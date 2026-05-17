#!/usr/bin/env python3
"""Byte-stream row-group ingest for Bitcoin/Ethereum corpus mirrors.

This script does not parse consensus data. It treats a source as an ordered byte
stream, shards it into deterministic row groups, writes a small JSON index for
each shard, and optionally streams both payload and index directly to a Google
Drive rclone remote.

The format is "parquet-style" in the operational sense: partitioned datasets,
row groups, schema sidecars, and ordered shard manifests. It intentionally avoids
new dependencies; true Parquet can be added later as an extraction/export target.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO


REPO = Path(__file__).resolve().parents[2]
DATA_DIR = REPO / "shared-data/data/blockchain_corpus"
ARTIFACT_DIR = REPO / "shared-data/artifacts/blockchain_corpus"
SOURCE_MANIFEST = DATA_DIR / "blockchain_gdrive_stream_sources.json"
DEFAULT_DESTINATION = "Gdrive:topological_storage/research-stack/blockchain-corpus/seed-2026-05-10"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def run(cmd: list[str], input_bytes: bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def rclone_available(remote: str) -> tuple[bool, str]:
    proc = run(["rclone", "lsf", remote])
    message = (proc.stderr or proc.stdout).decode(errors="replace").strip()
    return proc.returncode == 0, message


def rcat(remote_path: str, payload: bytes) -> tuple[bool, str]:
    proc = run(["rclone", "rcat", remote_path], input_bytes=payload)
    message = (proc.stderr or proc.stdout).decode(errors="replace").strip()
    return proc.returncode == 0, message


def read_source(path: str) -> BinaryIO:
    if path == "-":
        return sys.stdin.buffer
    return Path(path).expanduser().open("rb")


def shard_remote_prefix(destination: str, chain: str, stream_kind: str, run_id: str) -> str:
    return f"{destination.rstrip('/')}/chain={chain}/stream={stream_kind}/run={run_id}"


def shard_name(chain: str, stream_kind: str, run_id: str, shard_index: int, suffix: str) -> str:
    return f"{chain}_{stream_kind}_{run_id}_shard_{shard_index:06d}.{suffix}"


def write_local(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def emit_payload(
    *,
    payload: bytes,
    index_payload: bytes,
    local_dir: Path,
    remote_prefix: str,
    payload_name: str,
    index_name: str,
    execute: bool,
    keep_local_payloads: bool,
) -> dict:
    local_payload = local_dir / "payload" / payload_name
    local_index = local_dir / "index" / index_name
    write_local(local_index, index_payload)
    if keep_local_payloads:
        write_local(local_payload, payload)

    result = {
        "payload_local_path": str(local_payload.relative_to(REPO)) if keep_local_payloads else None,
        "index_local_path": str(local_index.relative_to(REPO)),
        "payload_drive_path": f"{remote_prefix}/payload/{payload_name}",
        "index_drive_path": f"{remote_prefix}/index/{index_name}",
        "payload_upload": "HOLD_DRY_RUN_ONLY",
        "index_upload": "HOLD_DRY_RUN_ONLY",
    }
    if execute:
        payload_ok, payload_msg = rcat(result["payload_drive_path"], payload)
        index_ok, index_msg = rcat(result["index_drive_path"], index_payload)
        result["payload_upload"] = "ADMIT_GDRIVE_PAYLOAD" if payload_ok else "QUARANTINE_RCLONE_FAILED"
        result["index_upload"] = "ADMIT_GDRIVE_INDEX" if index_ok else "QUARANTINE_RCLONE_FAILED"
        result["payload_upload_message"] = payload_msg
        result["index_upload_message"] = index_msg
    return result


def stream_ingest(args: argparse.Namespace) -> dict:
    manifest = load_json(args.sources)
    destination = args.destination or manifest.get("default_drive_destination", DEFAULT_DESTINATION)
    shard_bytes = args.shard_bytes or int(manifest.get("default_shard_bytes", 64 * 1024 * 1024))
    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    remote_prefix = shard_remote_prefix(destination, args.chain, args.stream_kind, run_id)
    local_dir = ARTIFACT_DIR / args.chain / args.stream_kind / run_id

    remote_root = destination.split("/", 1)[0]
    remote_ok, remote_message = rclone_available(remote_root)
    if args.execute and not remote_ok:
        return {
            "schema": "blockchain_gdrive_stream_ingest_receipt_v0",
            "created_utc": now_iso(),
            "decision": "QUARANTINE_NO_GDRIVE_REMOTE",
            "destination": destination,
            "remote_check": remote_message,
        }

    shard_records = []
    total_bytes = 0
    stream_hash = hashlib.sha256()

    with read_source(args.source) as source:
        shard_index = 0
        while True:
            chunk = source.read(shard_bytes)
            if not chunk:
                break

            payload_hash = sha256_bytes(chunk)
            stream_hash.update(chunk)
            payload_name = shard_name(args.chain, args.stream_kind, run_id, shard_index, "bin")
            index_name = shard_name(args.chain, args.stream_kind, run_id, shard_index, "index.json")
            record = {
                "schema": "blockchain_row_group_index_v0",
                "chain": args.chain,
                "stream_kind": args.stream_kind,
                "run_id": run_id,
                "shard_index": shard_index,
                "offset_start": total_bytes,
                "byte_count": len(chunk),
                "payload_sha256": payload_hash,
                "payload_name": payload_name,
                "encoding": "raw-bytes",
                "columns": [
                    "chain",
                    "stream_kind",
                    "run_id",
                    "shard_index",
                    "offset_start",
                    "byte_count",
                    "payload_sha256",
                    "payload_name"
                ]
            }
            index_payload = json.dumps(record, indent=2, sort_keys=True).encode() + b"\n"
            emit_result = emit_payload(
                payload=chunk,
                index_payload=index_payload,
                local_dir=local_dir,
                remote_prefix=remote_prefix,
                payload_name=payload_name,
                index_name=index_name,
                execute=args.execute,
                keep_local_payloads=args.keep_local_payloads,
            )
            record.update(emit_result)
            shard_records.append(record)
            total_bytes += len(chunk)
            shard_index += 1

            if args.max_shards is not None and shard_index >= args.max_shards:
                break

    ordered_hash_input = "".join(item["payload_sha256"] for item in shard_records).encode()
    ordered_shard_hash = sha256_bytes(ordered_hash_input)
    decision = "ADMIT_STREAM_TO_GDRIVE" if args.execute else "HOLD_DRY_RUN_ONLY"
    if args.max_shards is not None:
        decision = "ADMIT_PARTIAL_STREAM_TO_GDRIVE" if args.execute else "HOLD_PARTIAL_DRY_RUN_ONLY"

    receipt = {
        "schema": "blockchain_gdrive_stream_ingest_receipt_v0",
        "created_utc": now_iso(),
        "claim_boundary": "Byte-stream row-group ingest. This receipt proves only ordered bytes seen by this run and optional Drive upload status; it does not prove complete Bitcoin/Ethereum corpus coverage.",
        "source_manifest": str(args.sources.relative_to(REPO)),
        "chain": args.chain,
        "stream_kind": args.stream_kind,
        "source": args.source,
        "destination": destination,
        "remote_prefix": remote_prefix,
        "run_id": run_id,
        "execute": args.execute,
        "keep_local_payloads": args.keep_local_payloads,
        "shard_bytes": shard_bytes,
        "max_shards": args.max_shards,
        "remote_check": "PASS" if remote_ok else remote_message,
        "summary": {
            "shard_count": len(shard_records),
            "total_bytes": total_bytes,
            "stream_sha256": stream_hash.hexdigest(),
            "ordered_shard_hash": ordered_shard_hash,
        },
        "shards": shard_records,
        "decision": decision,
    }
    receipt_path = DATA_DIR / f"blockchain_gdrive_stream_ingest_receipt_{args.chain}_{args.stream_kind}_{run_id}.json"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    receipt["receipt_path"] = str(receipt_path.relative_to(REPO))

    if args.execute:
        remote_receipt = f"{remote_prefix}/receipts/{receipt_path.name}"
        ok, message = rcat(remote_receipt, receipt_path.read_bytes())
        receipt["receipt_upload"] = {
            "drive_path": remote_receipt,
            "ok": ok,
            "message": message,
        }
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")

    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, default=SOURCE_MANIFEST)
    parser.add_argument("--chain", choices=["bitcoin", "ethereum"], required=True)
    parser.add_argument("--stream-kind", required=True)
    parser.add_argument("--source", default="-", help="source file path or '-' for stdin")
    parser.add_argument("--destination", default=None)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--shard-bytes", type=int, default=None)
    parser.add_argument("--max-shards", type=int, default=None)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument(
        "--keep-local-payloads",
        action="store_true",
        help="Keep local payload shard bytes after upload/dry-run. Indexes and receipts are always kept.",
    )
    args = parser.parse_args()

    receipt = stream_ingest(args)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if not str(receipt.get("decision", "")).startswith("QUARANTINE") else 2


if __name__ == "__main__":
    sys.exit(main())
