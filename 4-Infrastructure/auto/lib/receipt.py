#!/usr/bin/env python3
"""Receipt schema for the infra controller — hash-chained JSONL + optional S3 upload."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "infra_controller_receipt_v1"
VERSION = "1.0.0"
LOG_PATH = Path.home() / ".cache" / "infra-controller.jsonl"


def sha256(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha256(data).hexdigest()


def read_chain() -> tuple[int, str]:
    """Return (last_tick, last_hash) from existing log, or (0, '') if none."""
    if not LOG_PATH.exists():
        return 0, ""
    last_tick = 0
    last_hash = ""
    try:
        with open(LOG_PATH) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    last_tick = entry.get("tick", last_tick)
                    last_hash = entry.get("receipt_hash", last_hash)
                except json.JSONDecodeError:
                    pass
    except OSError:
        pass
    return last_tick, last_hash


def build_receipt(
    tick: int,
    parent_hash: str,
    observation: dict[str, Any],
    decision: dict[str, Any],
    action_result: dict[str, Any],
) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "schema": SCHEMA,
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "tick": tick,
        "parent_hash": parent_hash,
        "observation": observation,
        "decision": decision,
        "action_result": action_result,
        "claim_boundary": "infra-controller-observe-decide-act",
    }
    preimage = {
        k: v for k, v in receipt.items()
        if k not in ("generated_at_utc", "receipt_hash")
    }
    receipt["receipt_hash"] = sha256(json.dumps(preimage, sort_keys=True))
    return receipt


def write_receipt(receipt: dict[str, Any]) -> None:
    """Append receipt to local JSONL hash-chain log."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as fh:
        fh.write(json.dumps(receipt) + "\n")
