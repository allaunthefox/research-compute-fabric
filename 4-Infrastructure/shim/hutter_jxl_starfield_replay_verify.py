#!/usr/bin/env python3
"""Byte-window replay verification for JPEG-XL starfield eigenprobe.

Reads the first-sweep receipt, extracts source_window_hints from density
neighborhoods, and verifies each claimed SHA-256 against the actual fixture
bytes. Produces a replay receipt satisfying Next Fixture Gate requirement #6.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

from shim.utils import sha256_bytes

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "shared-data" / "data" / "stack_solidification" / "hutter_jxl_starfield"
RECEIPT_PATH = OUT_DIR / "hutter_jxl_starfield_enwik8_first_sweep_receipt.json"
REPLAY_RECEIPT_PATH = OUT_DIR / "hutter_jxl_starfield_enwik8_first_sweep_replay_receipt.json"

PROTOCOL = "hutter_jxl_starfield_eigenprobe_first_sweep_v1"
REPLAY_PROTOCOL = "hutter_jxl_starfield_eigenprobe_first_sweep_replay_v1"



def extract_all_hints(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    seen: set[tuple[int, int]] = set()
    hints: list[dict[str, Any]] = []

    for neighborhood in receipt.get("suggested_neighborhoods", []):
        for hint in neighborhood.get("source_window_hints", []):
            key = (hint["byte_start"], hint["byte_end"])
            if key not in seen:
                seen.add(key)
                hints.append(hint)

    return hints


def verify_hints(
    hints: list[dict[str, Any]],
    data: bytes,
) -> dict[str, Any]:
    verified: list[dict[str, Any]] = []
    mismatches: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for hint in hints:
        start = hint["byte_start"]
        end = hint["byte_end"]
        claimed = hint["sha256"]
        window_id = hint["window_id"]

        if end > len(data):
            errors.append({
                "window_id": window_id,
                "byte_start": start,
                "byte_end": end,
                "error": "byte_range_exceeds_fixture_length",
                "fixture_length": len(data),
            })
            continue

        actual = sha256_bytes(data[start:end])
        entry = {
            "window_id": window_id,
            "byte_start": start,
            "byte_end": end,
            "claimed_sha256": claimed,
            "actual_sha256": actual,
        }
        if actual == claimed:
            verified.append(entry)
        else:
            mismatches.append(entry)

    return {
        "total_hints": len(hints),
        "verified_count": len(verified),
        "mismatch_count": len(mismatches),
        "error_count": len(errors),
        "verified": verified,
        "mismatches": mismatches,
        "errors": errors,
    }


def decide_replay(results: dict[str, Any]) -> dict[str, Any]:
    if results["error_count"] > 0:
        return {
            "decision": "QUARANTINE_REPLAY_BOUNDARY_ERROR",
            "reason": f"{results['error_count']} hints referenced bytes beyond fixture boundary",
        }
    if results["mismatch_count"] > 0:
        return {
            "decision": "QUARANTINE_REPLAY_MISMATCH",
            "reason": f"{results['mismatch_count']} hints had SHA-256 mismatches with fixture bytes",
        }
    if results["verified_count"] == 0:
        return {
            "decision": "HOLD_NO_HINTS_TO_VERIFY",
            "reason": "no source_window_hints found in receipt to verify",
        }
    return {
        "decision": "REPLAY_VERIFIED",
        "reason": f"all {results['verified_count']} unique byte-window hints matched fixture SHA-256",
    }


def main() -> None:
    if not RECEIPT_PATH.exists():
        print(f"ERROR: receipt not found at {RECEIPT_PATH}", file=sys.stderr)
        sys.exit(1)

    with RECEIPT_PATH.open("r", encoding="utf-8") as f:
        receipt = json.load(f)

    fixture_path = Path(receipt["fixture"]["source_path"])
    if not fixture_path.exists():
        print(f"ERROR: fixture not found at {fixture_path}", file=sys.stderr)
        sys.exit(1)

    slice_len = receipt["fixture"]["slice_byte_length"]
    with fixture_path.open("rb") as f:
        data = f.read(slice_len)

    hints = extract_all_hints(receipt)
    results = verify_hints(hints, data)
    gate = decide_replay(results)

    replay_receipt = {
        "protocol": REPLAY_PROTOCOL,
        "parent_protocol": PROTOCOL,
        "parent_receipt": str(RECEIPT_PATH),
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "fixture": {
            "source_path": str(fixture_path),
            "slice_byte_length": slice_len,
            "slice_sha256": receipt["fixture"]["slice_sha256"],
        },
        "replay": results,
        "gate": gate,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPLAY_RECEIPT_PATH.write_text(
        json.dumps(replay_receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "replay_receipt": str(REPLAY_RECEIPT_PATH),
        "decision": gate["decision"],
        "total_hints": results["total_hints"],
        "verified": results["verified_count"],
        "mismatches": results["mismatch_count"],
        "errors": results["error_count"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
