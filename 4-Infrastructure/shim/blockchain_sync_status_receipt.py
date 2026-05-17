#!/usr/bin/env python3
"""Emit blockchain acquisition status receipts for Bitcoin/Geth sync lanes."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
DATA_DIR = REPO / "shared-data/data/blockchain_corpus"
DEFAULT_DESTINATION = "Gdrive:topological_storage/research-stack/blockchain-corpus/seed-2026-05-10/status"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def run(cmd: list[str], timeout: int = 20, input_bytes: bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def parse_json_or_error(proc: subprocess.CompletedProcess) -> dict:
    stdout = proc.stdout.decode(errors="replace").strip()
    stderr = proc.stderr.decode(errors="replace").strip()
    if proc.returncode != 0:
        return {
            "ok": False,
            "returncode": proc.returncode,
            "stdout": stdout,
            "stderr": stderr,
        }
    try:
        return {"ok": True, "data": json.loads(stdout)}
    except json.JSONDecodeError:
        return {"ok": True, "stdout": stdout, "stderr": stderr}


def bitcoin_status(conf: str) -> dict:
    proc = run(["bitcoin-cli", f"-conf={conf}", "getblockchaininfo"])
    result = parse_json_or_error(proc)
    if not result.get("ok"):
        result["decision"] = "HOLD_BITCOIN_RPC_UNAVAILABLE"
        return result
    data = result.get("data", {})
    result["decision"] = (
        "ADMIT_BITCOIN_PRUNED_LIVE_SYNC"
        if data.get("pruned")
        else "ADMIT_BITCOIN_FULL_NODE_SYNC"
    )
    result["claim_boundary"] = (
        "Pruned Bitcoin node can support live/head/header pattern receipts, "
        "but not full historical block-body corpus export."
        if data.get("pruned")
        else "Non-pruned Bitcoin node may support historical block-body corpus export after sync."
    )
    return result


def geth_status() -> dict:
    expr = (
        "JSON.stringify({"
        "syncing: eth.syncing,"
        "blockNumber: eth.blockNumber,"
        "peerCount: net.peerCount,"
        "txIndexRemainingBlocks: (eth.syncing && eth.syncing.txIndexRemainingBlocks) || null,"
        "txIndexFinishedBlocks: (eth.syncing && eth.syncing.txIndexFinishedBlocks) || null"
        "})"
    )
    proc = run(["geth", "attach", "--exec", expr])
    stdout = proc.stdout.decode(errors="replace").strip()
    stderr = proc.stderr.decode(errors="replace").strip()
    if proc.returncode != 0:
        return {
            "ok": False,
            "returncode": proc.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "decision": "HOLD_GETH_IPC_UNAVAILABLE",
        }
    try:
        data = json.loads(json.loads(stdout))
    except Exception:
        return {
            "ok": False,
            "stdout": stdout,
            "stderr": stderr,
            "decision": "QUARANTINE_GETH_STATUS_PARSE_FAILED",
        }
    decision = "ADMIT_GETH_RUNNING_WAITING_FOR_PEERS"
    if data.get("peerCount", 0) > 0:
        decision = "ADMIT_GETH_SYNCING"
    if data.get("syncing") is False and data.get("blockNumber", 0) > 0:
        decision = "ADMIT_GETH_SYNCED_OR_NEAR_HEAD"
    return {
        "ok": True,
        "data": data,
        "decision": decision,
        "claim_boundary": "Geth execution-history acquisition status only; full state/archive corpus requires separate state-history/archive receipt.",
    }


def rcat(remote_path: str, payload: bytes) -> tuple[bool, str]:
    proc = run(["rclone", "rcat", remote_path], input_bytes=payload, timeout=60)
    message = (proc.stderr or proc.stdout).decode(errors="replace").strip()
    return proc.returncode == 0, message


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bitcoin-conf", default=str(Path.home() / ".bitcoin/bitcoin.conf"))
    parser.add_argument("--destination", default=DEFAULT_DESTINATION)
    parser.add_argument("--upload", action="store_true")
    args = parser.parse_args()

    created = now_iso()
    safe_stamp = created.replace(":", "").replace("-", "")
    receipt = {
        "schema": "blockchain_sync_status_receipt_v0",
        "created_utc": created,
        "bitcoin": bitcoin_status(args.bitcoin_conf),
        "ethereum": geth_status(),
        "decision": "ADMIT_PROGRESSIVE_ACQUISITION_STATUS",
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"blockchain_sync_status_receipt_{safe_stamp}.json"
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    receipt["receipt_path"] = str(path.relative_to(REPO))

    if args.upload:
        remote_path = f"{args.destination.rstrip('/')}/{path.name}"
        ok, message = rcat(remote_path, path.read_bytes())
        receipt["drive_upload"] = {
            "drive_path": remote_path,
            "ok": ok,
            "message": message,
        }
        path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")

    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
