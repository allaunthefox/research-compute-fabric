#!/usr/bin/env python3
"""Build an aggregate accounting receipt for blockchain corpus streaming.

This is an accounting surface only. It records source inventories, completed
transfer receipts, and optional remote object counts. It does not decode chain
semantics or claim complete cryptocurrency coverage beyond the listed source
objects.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def rclone_count(remote: str, suffix: str | None = None) -> int | None:
    try:
        proc = subprocess.run(
            ["rclone", "lsf", remote, "--recursive"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=90,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    lines = [
        line
        for line in proc.stdout.splitlines()
        if line and not line.endswith("/") and not line.startswith("receipts/") and "/receipts/" not in line
    ]
    if suffix:
        lines = [line for line in lines if line.endswith(suffix)]
    return len(lines)


def summarize_inventory(path: pathlib.Path) -> dict[str, Any]:
    doc = load_json(path)
    objects = doc.get("objects", [])
    payload_object_count = sum(1 for item in objects if not str(item.get("key", "")).endswith("/"))
    parquet_object_count = sum(1 for item in objects if str(item.get("key", "")).endswith(".parquet"))
    total_bytes = doc.get("total_listed_bytes")
    if total_bytes is None:
        total_bytes = doc.get("total_listed_bytes_known")
    return {
        "chain": doc.get("chain"),
        "claim_boundary": doc.get("claim_boundary"),
        "dataset": doc.get("dataset"),
        "decision": doc.get("decision"),
        "directory_url": doc.get("directory_url"),
        "inventory": str(path),
        "inventory_hash": doc.get("inventory_hash"),
        "object_count": doc.get("object_count"),
        "payload_object_count": payload_object_count,
        "parquet_object_count": parquet_object_count,
        "prefix": doc.get("prefix"),
        "table": doc.get("table"),
        "total_listed_bytes": total_bytes,
    }


def summarize_transfer(path: pathlib.Path) -> dict[str, Any]:
    doc = load_json(path)
    summary = doc.get("summary", {})
    return {
        "chain": doc.get("chain"),
        "dataset": doc.get("dataset"),
        "decision": doc.get("decision"),
        "receipt": str(path),
        "receipt_hash": doc.get("receipt_hash"),
        "table": doc.get("table"),
        "quarantine_count": summary.get("quarantine_count"),
        "selected_object_count": summary.get("selected_object_count"),
        "size_mismatch_count": summary.get("size_mismatch_count"),
        "successful_or_dry_run_count": summary.get("successful_or_dry_run_count"),
        "total_observed_bytes": summary.get("total_observed_bytes"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="shared-data/data/blockchain_corpus")
    parser.add_argument("--destination", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--include-remote-counts", action="store_true")
    parser.add_argument("--running", action="append", default=[])
    args = parser.parse_args()

    data_dir = pathlib.Path(args.data_dir)
    aws_full_inventories = [
        summarize_inventory(path)
        for path in sorted(data_dir.glob("aws_public_blockchain_*_blocks_inventory_full.json"))
    ]
    bounded_inventories = [
        summarize_inventory(path)
        for path in sorted(data_dir.glob("blockchair_*_blocks_inventory_first100.json"))
    ]
    inventories = aws_full_inventories + bounded_inventories
    transfers = []
    for path in sorted(data_dir.glob("*transfer*receipt.json")):
        doc = load_json(path)
        summary = doc.get("summary", {})
        if not doc.get("dataset") or not doc.get("chain") or "selected_object_count" not in summary:
            continue
        transfers.append(summarize_transfer(path))

    inventory_by_key = {
        (entry["dataset"], entry["chain"], entry["table"]): entry for entry in inventories
    }
    transferred_by_key: dict[tuple[Any, Any, Any], int] = {}
    quarantined_by_key: dict[tuple[Any, Any, Any], int] = {}
    bytes_by_key: dict[tuple[Any, Any, Any], int] = {}
    for entry in transfers:
        key = (entry["dataset"], entry["chain"], entry["table"])
        transferred_by_key[key] = transferred_by_key.get(key, 0) + int(entry.get("successful_or_dry_run_count") or 0)
        quarantined_by_key[key] = quarantined_by_key.get(key, 0) + int(entry.get("quarantine_count") or 0)
        bytes_by_key[key] = bytes_by_key.get(key, 0) + int(entry.get("total_observed_bytes") or 0)

    chains = []
    for key, inv in sorted(inventory_by_key.items(), key=lambda item: str(item[0])):
        remote = f"{args.destination}/{inv['dataset']}/{inv['chain']}/{inv['table']}"
        entry = {
            **inv,
            "completed_transfer_objects": transferred_by_key.get(key, 0),
            "completed_transfer_bytes": bytes_by_key.get(key, 0),
            "completed_quarantine_objects": quarantined_by_key.get(key, 0),
            "remote_parquet_count": rclone_count(remote) if args.include_remote_counts else None,
            "remote_payload_count": rclone_count(remote, None) if args.include_remote_counts else None,
            "remote_prefix": remote,
        }
        chains.append(entry)

    all_transfer_totals = {
        "quarantine_objects": sum(int(entry.get("quarantine_count") or 0) for entry in transfers),
        "selected_objects": sum(int(entry.get("selected_object_count") or 0) for entry in transfers),
        "size_mismatch_objects": sum(int(entry.get("size_mismatch_count") or 0) for entry in transfers),
        "successful_or_dry_run_objects": sum(int(entry.get("successful_or_dry_run_count") or 0) for entry in transfers),
        "total_observed_bytes": sum(int(entry.get("total_observed_bytes") or 0) for entry in transfers),
    }

    decision = "ADMIT_BLOCKCHAIN_CORPUS_ACCOUNTING"
    if args.running:
        decision = "ADMIT_BLOCKCHAIN_CORPUS_ACCOUNTING_WITH_RUNNING_TRANSFERS"

    receipt = {
        "claim_boundary": (
            "Full accounting receipt for currently listed public blockchain corpus sources. "
            "This records inventory coverage, transfer receipts, remote counts when requested, "
            "and running transfer labels. It does not prove decoded chain semantics, price/market "
            "coverage, private dataset coverage, or compression results."
        ),
        "created_utc": utc_now(),
        "decision": decision,
        "destination": args.destination,
        "aws_full_inventoried_chain_table_count": len(aws_full_inventories),
        "bounded_inventoried_chain_table_count": len(bounded_inventories),
        "inventoried_chain_table_count": len(inventories),
        "running_transfers": args.running,
        "schema": "blockchain_full_account_receipt_v0",
        "source_inventories": chains,
        "transfer_receipts": transfers,
        "totals": {
            "all_transfer_receipts": all_transfer_totals,
            "completed_quarantine_objects": sum(entry["completed_quarantine_objects"] for entry in chains),
            "completed_transfer_bytes": sum(entry["completed_transfer_bytes"] for entry in chains),
            "completed_transfer_objects": sum(entry["completed_transfer_objects"] for entry in chains),
            "inventoried_objects": sum(int(entry.get("object_count") or 0) for entry in chains),
            "inventoried_payload_objects": sum(int(entry.get("payload_object_count") or 0) for entry in chains),
            "inventoried_parquet_objects": sum(int(entry.get("parquet_object_count") or 0) for entry in chains),
            "inventoried_total_listed_bytes": sum(int(entry.get("total_listed_bytes") or 0) for entry in chains),
        },
    }
    receipt["receipt_hash"] = sha256_json(receipt)

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"decision": receipt["decision"], "out": str(out), "receipt_hash": receipt["receipt_hash"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
