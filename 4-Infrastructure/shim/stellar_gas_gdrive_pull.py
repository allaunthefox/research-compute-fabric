#!/usr/bin/env python3
"""Direct-to-Google-Drive seed puller for stellar gas observation routes.

The puller streams source payloads through rclone instead of writing observation
payloads into the repository. Local files are limited to source manifests and
receipts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


REPO = Path(__file__).resolve().parents[2]
SOURCE_PATH = REPO / "shared-data/data/stellar_gas_observation/stellar_gas_gdrive_sources.json"
SCHEMA_PATH = REPO / "shared-data/data/stellar_gas_observation/stellar_gas_observation_schema.json"
RECEIPT_DIR = REPO / "shared-data/data/stellar_gas_observation"


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


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
    if proc.returncode == 0:
        return True, proc.stdout.decode(errors="replace").strip()
    return False, proc.stderr.decode(errors="replace").strip()


def head_content_length(url: str, timeout: int) -> int | None:
    req = Request(url, method="HEAD", headers={"User-Agent": "ResearchStack-StellarGasPull/0"})
    try:
        with urlopen(req, timeout=timeout) as response:
            value = response.headers.get("Content-Length")
            return int(value) if value else None
    except Exception:
        return None


def fetch_bytes(url: str, timeout: int, max_bytes: int) -> tuple[bytes, str | None]:
    req = Request(url, headers={"User-Agent": "ResearchStack-StellarGasPull/0"})
    with urlopen(req, timeout=timeout) as response:
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise ValueError(f"payload exceeded max_bytes={max_bytes}")
            chunks.append(chunk)
        content_type = response.headers.get("Content-Type")
    return b"".join(chunks), content_type


def rcat(remote_path: str, payload: bytes) -> tuple[bool, str]:
    proc = run(["rclone", "rcat", remote_path], input_bytes=payload)
    if proc.returncode == 0:
        return True, proc.stdout.decode(errors="replace").strip()
    return False, proc.stderr.decode(errors="replace").strip()


def copy_local_to_drive(local_path: Path, remote_path: str) -> tuple[bool, str]:
    proc = run(["rclone", "copyto", str(local_path), remote_path, "--checksum"])
    if proc.returncode == 0:
        return True, proc.stdout.decode(errors="replace").strip()
    return False, proc.stderr.decode(errors="replace").strip()


def pull_source(source: dict, destination: str, max_bytes: int, timeout: int, execute: bool) -> dict:
    source_id = source["id"]
    output_name = source["output_name"]
    remote_path = f"{destination.rstrip('/')}/raw/{output_name}"
    result = {
        "id": source_id,
        "title": source.get("title"),
        "source_url": source["source_url"],
        "archive": source.get("archive"),
        "source_kind": source.get("source_kind"),
        "model_relevance": source.get("model_relevance", []),
        "drive_path": remote_path,
        "retrieved_at": now_iso(),
        "decision": "HOLD_ROUTE_ONLY",
        "byte_count": 0,
        "payload_sha256": None,
        "content_type": None,
        "notes": [],
    }

    if not source.get("pull_enabled", False):
        result["notes"].append(source.get("route_only_reason", "pull disabled by source manifest"))
        return result

    length = head_content_length(source["source_url"], timeout)
    result["head_content_length"] = length
    if length is not None and length > max_bytes:
        result["decision"] = "HOLD_OVERSIZE"
        result["notes"].append(f"content-length {length} exceeds max_bytes {max_bytes}")
        return result

    if not execute:
        result["decision"] = "DRY_RUN_READY"
        result["notes"].append("execute flag not set")
        return result

    try:
        payload, content_type = fetch_bytes(source["source_url"], timeout, max_bytes)
    except Exception as exc:
        result["decision"] = "QUARANTINE_FETCH_FAILED"
        result["notes"].append(str(exc))
        return result

    digest = hashlib.sha256(payload).hexdigest()
    ok, message = rcat(remote_path, payload)
    result.update(
        {
            "byte_count": len(payload),
            "payload_sha256": digest,
            "content_type": content_type,
            "rclone_message": message,
        }
    )
    result["decision"] = "ADMIT_GDRIVE_PAYLOAD" if ok else "QUARANTINE_RCLONE_FAILED"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, default=SOURCE_PATH)
    parser.add_argument("--schema", type=Path, default=SCHEMA_PATH)
    parser.add_argument("--destination", default=None)
    parser.add_argument("--max-bytes", type=int, default=None)
    parser.add_argument("--timeout", type=int, default=45)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    manifest = load_json(args.sources)
    destination = args.destination or manifest["default_drive_destination"]
    max_bytes = args.max_bytes or int(manifest.get("default_max_bytes", 20_000_000))
    receipt_path = RECEIPT_DIR / f"stellar_gas_gdrive_pull_receipt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    remote_root = destination.split("/", 1)[0]
    remote_ok, remote_message = rclone_available(remote_root)
    if not remote_ok:
        receipt = {
            "schema": "stellar_gas_gdrive_pull_receipt_v0",
            "created": now_iso(),
            "destination": destination,
            "decision": "QUARANTINE_NO_GDRIVE_REMOTE",
            "remote_check": remote_message,
        }
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
        print(json.dumps(receipt, indent=2))
        return 2

    results = [
        pull_source(source, destination, max_bytes, args.timeout, args.execute)
        for source in manifest["sources"]
    ]

    copied_control_files = []
    if args.execute:
        for local, name in [
            (args.sources, "stellar_gas_gdrive_sources.json"),
            (args.schema, "stellar_gas_observation_schema.json"),
        ]:
            remote_path = f"{destination.rstrip('/')}/control/{name}"
            ok, message = copy_local_to_drive(local, remote_path)
            copied_control_files.append(
                {
                    "local": str(local.relative_to(REPO)),
                    "drive_path": remote_path,
                    "ok": ok,
                    "message": message,
                }
            )

    admitted = [item for item in results if item["decision"] == "ADMIT_GDRIVE_PAYLOAD"]
    receipt = {
        "schema": "stellar_gas_gdrive_pull_receipt_v0",
        "created": now_iso(),
        "claim_boundary": "Direct-to-Google-Drive seed pull. Payloads are streamed to Drive; local repo stores only manifests and receipts. Heavy products remain route-only unless explicitly enabled.",
        "source_manifest": str(args.sources.relative_to(REPO)),
        "observation_schema": str(args.schema.relative_to(REPO)),
        "destination": destination,
        "execute": args.execute,
        "max_bytes": max_bytes,
        "remote_check": "PASS",
        "control_files": copied_control_files,
        "summary": {
            "source_count": len(results),
            "admitted_payload_count": len(admitted),
            "admitted_payload_bytes": sum(item["byte_count"] for item in admitted),
            "route_or_hold_count": len(results) - len(admitted),
        },
        "results": results,
        "decision": "ADMIT_SEED_PULL_TO_GDRIVE" if args.execute else "HOLD_DRY_RUN_ONLY",
    }

    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")

    if args.execute:
        remote_receipt = f"{destination.rstrip('/')}/receipts/{receipt_path.name}"
        ok, message = copy_local_to_drive(receipt_path, remote_receipt)
        receipt["receipt_upload"] = {
            "drive_path": remote_receipt,
            "ok": ok,
            "message": message,
        }
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")

    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
