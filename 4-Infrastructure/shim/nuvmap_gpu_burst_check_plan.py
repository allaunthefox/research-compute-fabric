#!/usr/bin/env python3
"""Emit a bounded GPU-burst check plan for NUVMAP probe validation.

The plan is intended for a short rented GPU session. It avoids wallets, mining,
public-chain writes, and long-lived services. The output is a receipt/checklist
for replaying local fixtures, checking CPU/GPU parity, and collecting bounded
waveprobe/metaprobe evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
DEFAULT_OUT = REPO / "shared-data/data/blockchain_corpus/nuvmap_gpu_burst_check_plan_receipt.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def build_receipt(max_hours: float) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema": "nuvmap_gpu_burst_check_plan_v0",
        "created_utc": now_iso(),
        "claim_boundary": (
            "GPU rental execution plan only. This is not crypto mining, not a blockchain mainnet, "
            "not a token launch, not a compression result, and not a hardware acceleration claim until "
            "the listed receipts are produced."
        ),
        "timebox_hours": max_hours,
        "forbidden_inputs": [
            "wallet private keys",
            "exchange credentials",
            "mainnet transaction signing material",
            "unbounded copyrighted payload mirrors",
        ],
        "required_outputs": [
            "environment_receipt.json",
            "cpu_gpu_parity_receipt.json",
            "waveprobe_batch_receipt.json",
            "metaprobe_batch_receipt.json",
            "negative_controls_receipt.json",
            "cost_and_shutdown_receipt.json",
        ],
        "burst_phases": [
            {
                "phase": "P0_ENVIRONMENT_SNAPSHOT",
                "target_minutes": 10,
                "checks": [
                    "nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv",
                    "python -c 'import torch; print(torch.cuda.is_available())' if torch is installed",
                    "git rev-parse HEAD and git status --short for provenance",
                ],
                "decision": "ADMIT_ENVIRONMENT_IF_GPU_VISIBLE",
            },
            {
                "phase": "P1_FIXTURE_REPLAY",
                "target_minutes": 25,
                "checks": [
                    "Verify NUVMAP fixture block hash and merkle roots.",
                    "Replay blockchain_l3_self_scan_scheduler_receipt as first policy input.",
                    "Reject any fixture with missing source hashes.",
                ],
                "decision": "ADMIT_FIXTURE_REPLAY_OR_HOLD",
            },
            {
                "phase": "P2_CPU_GPU_PARITY",
                "target_minutes": 35,
                "checks": [
                    "Run the same wave/vector kernel on CPU and GPU.",
                    "Compare Q16.16 or declared float tolerance residuals.",
                    "Emit max_abs_error, mean_abs_error, and mismatch examples.",
                ],
                "decision": "ADMIT_GPU_WITNESS_ONLY_IF_PARITY_BOUNDED",
            },
            {
                "phase": "P3_WAVEPROBE_BATCH",
                "target_minutes": 45,
                "checks": [
                    "Run bounded byte-window/eigen/density probes over sampled blockchain shards.",
                    "Store only feature hashes and summaries unless payload admission exists.",
                    "Emit route candidates as HOLD until negative controls pass.",
                ],
                "decision": "ADMIT_WAVEPROBE_BATCH_HOLD_PROMOTION",
            },
            {
                "phase": "P4_METAPROBE_AND_CONTROLS",
                "target_minutes": 45,
                "checks": [
                    "Run metaprobe route selection over waveprobe outputs.",
                    "Run shuffled window, shuffled chain label, and random-byte controls.",
                    "Require controls before any Hutter/logogram feedback promotion.",
                ],
                "decision": "ADMIT_METAPROBE_IF_CONTROLS_BOUND_SIGNAL",
            },
            {
                "phase": "P5_COST_AND_SHUTDOWN",
                "target_minutes": 20,
                "checks": [
                    "Write final receipt bundle.",
                    "Sync receipts and small summaries to Drive.",
                    "Record instance type, wall time, estimated cost, and shutdown confirmation.",
                ],
                "decision": "ADMIT_BURST_COMPLETE_ONLY_WITH_SHUTDOWN_RECEIPT",
            },
        ],
        "promotion_gates": {
            "hardware_witness": "GPU visible plus CPU/GPU parity receipt, not just code execution.",
            "compression_feedback": "HOLD until byte-exact baseline matrix exists.",
            "nuvmap_chain": "HOLD until local fixture block replay and verifier exist.",
        },
        "decision": "ADMIT_GPU_BURST_PLAN_HOLD_EXECUTION",
    }
    payload["receipt_hash"] = sha256_text(stable_json({k: v for k, v in payload.items() if k != "receipt_hash"}))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hours", type=float, default=3.0)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    receipt = build_receipt(args.hours)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": receipt["decision"], "out": rel(args.out), "receipt_hash": receipt["receipt_hash"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
