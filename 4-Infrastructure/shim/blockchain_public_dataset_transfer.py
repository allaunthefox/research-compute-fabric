#!/usr/bin/env python3
"""Transfer inventoried public blockchain objects to Google Drive.

The script reads an inventory emitted by blockchain_public_dataset_inventory.py,
downloads each listed object, streams it to an rclone destination, and emits a
receipt with source metadata plus observed SHA-256 hashes. It is intentionally
object-preserving for Parquet snapshots: the payload object is the row group
container, while the receipt is the replay surface.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
DATA_DIR = REPO / "shared-data/data/blockchain_corpus"
DEFAULT_DESTINATION = "Gdrive:topological_storage/research-stack/blockchain-corpus/seed-2026-05-10/public-datasets"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def run(cmd: list[str], input_bytes: bytes | None = None, timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def rcat(remote_path: str, payload: bytes, timeout: int) -> tuple[bool, str]:
    proc = run(["rclone", "rcat", remote_path], input_bytes=payload, timeout=timeout)
    message = (proc.stderr or proc.stdout).decode(errors="replace").strip()
    return proc.returncode == 0, message


def copyto(local_path: Path, remote_path: str, timeout: int) -> tuple[bool, str]:
    proc = run(["rclone", "copyto", str(local_path), remote_path], timeout=timeout)
    message = (proc.stderr or proc.stdout).decode(errors="replace").strip()
    return proc.returncode == 0, message


def fetch_object_to_file(url: str, target: Path, timeout: int) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "ResearchStackBlockchainTransfer/0"})
    h = hashlib.sha256()
    with urllib.request.urlopen(req, timeout=timeout) as response:
        with target.open("wb") as handle:
            byte_count = 0
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                h.update(chunk)
                handle.write(chunk)
                byte_count += len(chunk)
    return byte_count, h.hexdigest()


def safe_remote_key(key: str) -> str:
    return key.strip("/").replace("//", "/")


def transfer_one(index: int, item: dict[str, Any], remote_prefix: str, args: argparse.Namespace) -> dict[str, Any]:
    source_url = item["url"]
    key = safe_remote_key(item["key"])
    if key.endswith("/"):
        return {
            "object_index": index,
            "source_key": item.get("key"),
            "source_url": source_url,
            "source_size": item.get("size"),
            "source_etag": item.get("etag"),
            "drive_path": f"{remote_prefix}/{key}",
            "upload_status": "ADMIT_SKIPPED_DIRECTORY_MARKER",
            "upload_message": "Directory marker skipped so object payloads can occupy the prefix.",
            "size_matches_inventory": None if item.get("size") is None else item.get("size") in {0, "0"},
        }
    remote_path = f"{remote_prefix}/{key}"
    try:
        with tempfile.TemporaryDirectory(prefix="rs_blockchain_transfer_") as tmpdir:
            local_path = Path(tmpdir) / Path(key).name
            byte_count, observed_hash = fetch_object_to_file(source_url, local_path, args.timeout)
            upload_ok, upload_message = (False, "HOLD_DRY_RUN_ONLY")
            if args.execute:
                upload_ok, upload_message = copyto(local_path, remote_path, args.upload_timeout)
        status = "ADMIT_TRANSFERRED_TO_GDRIVE" if upload_ok else ("HOLD_DRY_RUN_ONLY" if not args.execute else "QUARANTINE_UPLOAD_FAILED")
        size_matches = None if item.get("size") is None else byte_count == item.get("size")
        return {
            "object_index": index,
            "source_key": item.get("key"),
            "source_url": source_url,
            "source_size": item.get("size"),
            "source_etag": item.get("etag"),
            "observed_byte_count": byte_count,
            "observed_sha256": observed_hash,
            "drive_path": remote_path,
            "upload_status": status,
            "upload_message": upload_message,
            "size_matches_inventory": size_matches,
        }
    except Exception as exc:  # noqa: BLE001 - receipt every per-object failure.
        return {
            "object_index": index,
            "source_key": item.get("key"),
            "source_url": source_url,
            "upload_status": "QUARANTINE_TRANSFER_EXCEPTION",
            "error": str(exc),
        }


def transfer(args: argparse.Namespace) -> dict[str, Any]:
    inventory = json.loads(args.inventory.read_text())
    all_objects = inventory.get("objects", [])
    objects = all_objects[args.start_index :]
    if args.max_objects is not None:
        objects = objects[: args.max_objects]
    remote_prefix = f"{args.destination.rstrip('/')}/{inventory.get('dataset', 'dataset')}/{inventory.get('chain', 'chain')}/{inventory.get('table', 'table')}"

    records: list[dict[str, Any]] = []
    if args.workers <= 1:
        for index, item in enumerate(objects):
            record = transfer_one(index, item, remote_prefix, args)
            records.append(record)
            if str(record.get("upload_status", "")).startswith("QUARANTINE") and not args.keep_going:
                break
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(transfer_one, index, item, remote_prefix, args): index
                for index, item in enumerate(objects)
            }
            for future in as_completed(futures):
                record = future.result()
                records.append(record)
                if str(record.get("upload_status", "")).startswith("QUARANTINE") and not args.keep_going:
                    break
        records.sort(key=lambda record: int(record.get("object_index", 0)))

    total_bytes = sum(record.get("observed_byte_count", 0) for record in records)
    ok_count = sum(
        1
        for record in records
        if record.get("upload_status") in {"ADMIT_TRANSFERRED_TO_GDRIVE", "HOLD_DRY_RUN_ONLY"}
    )

    receipt = {
        "schema": "blockchain_public_dataset_transfer_receipt_v0",
        "created_utc": now_iso(),
        "claim_boundary": "Public dataset object transfer receipt only. This proves bytes fetched from listed URLs and optional Drive upload status; it does not prove full dataset coverage, Parquet decoding, or chain semantics.",
        "inventory": str(args.inventory.relative_to(REPO)) if args.inventory.is_relative_to(REPO) else str(args.inventory),
        "inventory_hash": inventory.get("inventory_hash"),
        "dataset": inventory.get("dataset"),
        "chain": inventory.get("chain"),
        "table": inventory.get("table"),
        "source_prefix": inventory.get("prefix"),
        "destination": args.destination,
        "remote_prefix": remote_prefix,
        "execute": args.execute,
        "selection": {
            "inventory_object_count": len(all_objects),
            "start_index": args.start_index,
            "max_objects": args.max_objects,
            "workers": args.workers,
        },
        "summary": {
            "selected_object_count": len(objects),
            "successful_or_dry_run_count": ok_count,
            "total_observed_bytes": total_bytes,
            "size_mismatch_count": sum(1 for record in records if record.get("size_matches_inventory") is False),
            "size_unknown_count": sum(1 for record in records if record.get("size_matches_inventory") is None),
            "skipped_directory_marker_count": sum(1 for record in records if record.get("upload_status") == "ADMIT_SKIPPED_DIRECTORY_MARKER"),
            "quarantine_count": sum(1 for record in records if str(record.get("upload_status", "")).startswith("QUARANTINE")),
        },
        "objects": records,
    }
    decision = "ADMIT_PUBLIC_DATASET_TRANSFER_TO_GDRIVE" if args.execute else "HOLD_PUBLIC_DATASET_TRANSFER_DRY_RUN"
    if receipt["summary"]["quarantine_count"]:
        decision = "QUARANTINE_PUBLIC_DATASET_TRANSFER_PARTIAL"
    receipt["decision"] = decision
    receipt["receipt_hash"] = sha256_text(stable_json({k: v for k, v in receipt.items() if k != "receipt_hash"}))

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = args.out or DATA_DIR / f"blockchain_public_dataset_transfer_receipt_{inventory.get('chain', 'chain')}_{inventory.get('table', 'table')}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    receipt["receipt_path"] = str(out.relative_to(REPO)) if out.is_relative_to(REPO) else str(out)

    if args.execute:
        receipt_remote = f"{remote_prefix}/receipts/{out.name}"
        ok, message = rcat(receipt_remote, out.read_bytes(), args.upload_timeout)
        receipt["receipt_upload"] = {
            "drive_path": receipt_remote,
            "ok": ok,
            "message": message,
        }
        out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--destination", default=DEFAULT_DESTINATION)
    parser.add_argument("--max-objects", type=int, default=None)
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--upload-timeout", type=int, default=600)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--keep-going", action="store_true")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    receipt = transfer(args)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if not str(receipt.get("decision", "")).startswith("QUARANTINE") else 2


if __name__ == "__main__":
    sys.exit(main())
