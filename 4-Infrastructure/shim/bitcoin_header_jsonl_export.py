#!/usr/bin/env python3
"""Export Bitcoin active-chain headers as newline-delimited JSON.

This exporter is designed for pruned Bitcoin Core nodes. A pruned node cannot
serve every historical block body, but it can still expose active-chain header
metadata through the block index. That makes this lane useful for pattern
studies from genesis to the current validated height without claiming full
historical block-body coverage.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
DATA_DIR = REPO / "shared-data/data/blockchain_corpus"
DEFAULT_RPC_URL = "http://127.0.0.1:8332"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def load_rpc_auth(conf_path: Path) -> tuple[str, str]:
    rpcuser = ""
    rpcpassword = ""
    for raw_line in conf_path.expanduser().read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key == "rpcuser":
            rpcuser = value
        elif key == "rpcpassword":
            rpcpassword = value
    if not rpcuser or not rpcpassword:
        raise SystemExit(f"missing rpcuser/rpcpassword in {conf_path}")
    return rpcuser, rpcpassword


class BitcoinRpc:
    def __init__(self, url: str, rpcuser: str, rpcpassword: str, timeout: int) -> None:
        token = base64.b64encode(f"{rpcuser}:{rpcpassword}".encode()).decode()
        self.url = url
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
        }
        self.next_id = 1

    def call(self, method: str, params: list[Any] | None = None) -> Any:
        return self.batch([(method, params or [])])[0]

    def batch(self, calls: list[tuple[str, list[Any]]]) -> list[Any]:
        request_items = []
        ids: list[int] = []
        for method, params in calls:
            request_id = self.next_id
            self.next_id += 1
            ids.append(request_id)
            request_items.append(
                {
                    "jsonrpc": "1.0",
                    "id": request_id,
                    "method": method,
                    "params": params,
                }
            )
        payload = json.dumps(request_items).encode()
        req = urllib.request.Request(self.url, data=payload, headers=self.headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                response_payload = response.read()
        except urllib.error.URLError as exc:
            raise SystemExit(f"bitcoin rpc failed: {exc}") from exc

        decoded = json.loads(response_payload)
        by_id = {item["id"]: item for item in decoded}
        results = []
        for request_id in ids:
            item = by_id[request_id]
            if item.get("error"):
                raise SystemExit(f"bitcoin rpc error for id {request_id}: {item['error']}")
            results.append(item.get("result"))
        return results


def stable_json_line(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode() + b"\n"


def export_headers(args: argparse.Namespace) -> dict[str, Any]:
    rpcuser, rpcpassword = load_rpc_auth(args.bitcoin_conf)
    rpc = BitcoinRpc(args.rpc_url, rpcuser, rpcpassword, args.timeout)
    chain_info = rpc.call("getblockchaininfo")
    source_height = int(chain_info[args.height_source])
    end_height = source_height if args.end_height is None else min(args.end_height, source_height)
    start_height = args.start_height
    if args.max_heights is not None:
        end_height = min(end_height, start_height + args.max_heights - 1)
    if end_height < start_height:
        raise SystemExit("end height is before start height")

    created = now_iso()
    stream_hash = hashlib.sha256()
    record_count = 0
    first_hash = None
    last_hash = None
    started = time.time()

    for batch_start in range(start_height, end_height + 1, args.batch_size):
        batch_end = min(end_height, batch_start + args.batch_size - 1)
        heights = list(range(batch_start, batch_end + 1))
        hashes = rpc.batch([("getblockhash", [height]) for height in heights])
        headers = rpc.batch([("getblockheader", [block_hash, True]) for block_hash in hashes])

        for height, block_hash, header in zip(heights, hashes, headers, strict=True):
            record = {
                "schema": "bitcoin_header_jsonl_v0",
                "chain": "bitcoin",
                "height": height,
                "hash": block_hash,
                "confirmations": header.get("confirmations"),
                "version": header.get("version"),
                "versionHex": header.get("versionHex"),
                "merkleroot": header.get("merkleroot"),
                "time": header.get("time"),
                "mediantime": header.get("mediantime"),
                "nonce": header.get("nonce"),
                "bits": header.get("bits"),
                "difficulty": header.get("difficulty"),
                "chainwork": header.get("chainwork"),
                "nTx": header.get("nTx"),
                "previousblockhash": header.get("previousblockhash"),
                "nextblockhash": header.get("nextblockhash"),
            }
            line = stable_json_line(record)
            args.output.buffer.write(line)
            stream_hash.update(line)
            record_count += 1
            first_hash = first_hash or block_hash
            last_hash = block_hash

        if args.progress_every and record_count % args.progress_every < len(heights):
            print(
                f"exported={record_count} height={batch_end} elapsed_s={time.time() - started:.1f}",
                file=sys.stderr,
                flush=True,
            )

    args.output.flush()
    receipt = {
        "schema": "bitcoin_header_jsonl_export_receipt_v0",
        "created_utc": created,
        "claim_boundary": "Active-chain Bitcoin header JSONL export from local Bitcoin Core RPC. This proves header metadata coverage for the exported height interval, not full historical block-body coverage.",
        "bitcoin_conf": str(args.bitcoin_conf.expanduser()),
        "rpc_url": args.rpc_url,
        "height_source": args.height_source,
        "chain_info": {
            "chain": chain_info.get("chain"),
            "blocks": chain_info.get("blocks"),
            "headers": chain_info.get("headers"),
            "bestblockhash": chain_info.get("bestblockhash"),
            "verificationprogress": chain_info.get("verificationprogress"),
            "initialblockdownload": chain_info.get("initialblockdownload"),
            "pruned": chain_info.get("pruned"),
            "pruneheight": chain_info.get("pruneheight"),
        },
        "start_height": start_height,
        "end_height": end_height,
        "record_count": record_count,
        "first_hash": first_hash,
        "last_hash": last_hash,
        "jsonl_sha256": stream_hash.hexdigest(),
        "decision": "ADMIT_BITCOIN_HEADER_INTERVAL_EXPORT",
    }
    if args.receipt_path:
        args.receipt_path.parent.mkdir(parents=True, exist_ok=True)
        args.receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bitcoin-conf", type=Path, default=Path.home() / ".bitcoin/bitcoin.conf")
    parser.add_argument("--rpc-url", default=DEFAULT_RPC_URL)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--start-height", type=int, default=0)
    parser.add_argument("--end-height", type=int, default=None)
    parser.add_argument("--height-source", choices=["blocks", "headers"], default="blocks")
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--max-heights", type=int, default=None)
    parser.add_argument("--progress-every", type=int, default=10000)
    parser.add_argument("--receipt-path", type=Path, default=None)
    parser.add_argument("--output", type=argparse.FileType("w"), default=sys.stdout)
    args = parser.parse_args()

    if args.receipt_path is None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        args.receipt_path = DATA_DIR / f"bitcoin_header_jsonl_export_receipt_{stamp}.json"

    receipt = export_headers(args)
    print(json.dumps(receipt, indent=2, sort_keys=True), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
