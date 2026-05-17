#!/usr/bin/env python3
"""Inventory public blockchain dataset object stores without cloud CLIs."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
DATA_DIR = REPO / "shared-data/data/blockchain_corpus"
S3_NS = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def fetch(url: str, timeout: int) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "ResearchStackBlockchainInventory/0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()


def s3_list_url(bucket_url: str, prefix: str, max_keys: int, token: str | None = None) -> str:
    params = {
        "list-type": "2",
        "prefix": prefix,
        "max-keys": str(max_keys),
    }
    if token:
        params["continuation-token"] = token
    return f"{bucket_url.rstrip('/')}/?{urllib.parse.urlencode(params)}"


def text_or_none(node: ET.Element, path: str) -> str | None:
    found = node.find(path, S3_NS)
    return found.text if found is not None else None


def list_s3_objects(bucket_url: str, prefix: str, max_objects: int, request_max_keys: int, timeout: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    token = None
    request_count = 0
    truncated = False
    next_token = None
    while len(objects) < max_objects:
        url = s3_list_url(bucket_url, prefix, min(request_max_keys, max_objects - len(objects)), token)
        payload = fetch(url, timeout)
        root = ET.fromstring(payload)
        request_count += 1
        truncated = (text_or_none(root, "s3:IsTruncated") or "").lower() == "true"
        next_token = text_or_none(root, "s3:NextContinuationToken")
        for item in root.findall("s3:Contents", S3_NS):
            key = text_or_none(item, "s3:Key")
            if not key:
                continue
            objects.append(
                {
                    "key": key,
                    "url": f"{bucket_url.rstrip('/')}/{urllib.parse.quote(key)}",
                    "last_modified": text_or_none(item, "s3:LastModified"),
                    "etag": (text_or_none(item, "s3:ETag") or "").strip('"'),
                    "size": int(text_or_none(item, "s3:Size") or 0),
                    "storage_class": text_or_none(item, "s3:StorageClass"),
                }
            )
            if len(objects) >= max_objects:
                break
        if not truncated or not next_token:
            break
        token = next_token
    meta = {
        "request_count": request_count,
        "is_truncated_after_inventory": truncated,
        "next_continuation_token_present": bool(next_token),
    }
    return objects, meta


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=["aws-public-blockchain"], default="aws-public-blockchain")
    parser.add_argument("--bucket-url", default="https://aws-public-blockchain.s3.amazonaws.com")
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--chain", required=True)
    parser.add_argument("--table", required=True)
    parser.add_argument("--max-objects", type=int, default=100)
    parser.add_argument("--request-max-keys", type=int, default=1000)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    objects, meta = list_s3_objects(
        args.bucket_url,
        args.prefix,
        args.max_objects,
        args.request_max_keys,
        args.timeout,
    )
    total_size = sum(item["size"] for item in objects)
    receipt = {
        "schema": "blockchain_public_dataset_inventory_v0",
        "created_utc": now_iso(),
        "claim_boundary": "Public dataset object inventory only. This proves listed object metadata retrieved from the source endpoint during this run; it does not prove full dataset coverage, parquet schema correctness, or decoded chain semantics.",
        "dataset": args.dataset,
        "bucket_url": args.bucket_url,
        "prefix": args.prefix,
        "chain": args.chain,
        "table": args.table,
        "max_objects": args.max_objects,
        "object_count": len(objects),
        "total_listed_bytes": total_size,
        "list_meta": meta,
        "objects": objects,
        "decision": "ADMIT_PUBLIC_DATASET_INVENTORY" if objects else "HOLD_EMPTY_PUBLIC_DATASET_INVENTORY",
    }
    receipt["inventory_hash"] = sha256_text(stable_json({k: v for k, v in receipt.items() if k != "inventory_hash"}))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if objects else 1


if __name__ == "__main__":
    sys.exit(main())
