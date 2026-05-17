#!/usr/bin/env python3
"""Dry-run H200 burst optimizer scaffold for finance LUT compression.

This does not require H200 hardware. It prepares the corpus/codebook search
surface and emits receipt-backed candidate summaries for later GPU rental.
"""

from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path
from typing import Any

import finance_claim_lut_harness as harness


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"


def load_bundle_receipt(path: Path) -> dict[str, Any]:
    if path.is_dir():
        path = path / "finance_claim_lut_harness_receipt.json"
    return json.loads(path.read_text(encoding="utf-8"))


def candidate_summary(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = []
    for sample in receipt.get("samples", []):
        metrics = sample["metrics"]
        best_known = min(
            value
            for value in [
                metrics.get("combined_fcl1_fcs1_bytes"),
                metrics.get("zlib_canonical_bytes"),
                metrics.get("cbor", {}).get("bytes"),
                metrics.get("messagepack", {}).get("bytes"),
                metrics.get("protobuf_dynamic", {}).get("bytes"),
            ]
            if isinstance(value, int)
        )
        candidates.append(
            {
                "sample_id": sample["id"],
                "current_fcl1_fcs1_bytes": metrics["combined_fcl1_fcs1_bytes"],
                "best_known_baseline_bytes": best_known,
                "target": "reduce FCS1 literal overhead and improve enum/value clustering",
                "promote": False,
                "reason": "dry-run only; no GPU search performed",
            }
        )
    return candidates


def run(args: argparse.Namespace) -> dict[str, Any]:
    receipt = load_bundle_receipt(args.corpus)
    candidates = candidate_summary(receipt)
    rejected = [
        {"name": "provider_live_job", "reason": "requires explicit rental, budget, and environment receipt"},
        {"name": "decoder_requires_gpu", "reason": "violates compact deterministic decoder boundary"},
        {"name": "compression_claim_from_tiny_corpus", "reason": "corpus still too small for competitive claim"},
    ]
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "candidate_lut_summary.json").write_text(json.dumps(candidates, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out_dir / "rejected_candidates.json").write_text(json.dumps(rejected, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    dry_run_receipt = {
        "schema": "h200_encode_runner_receipt_v1",
        "mode": "dry_run",
        "corpus": harness.repo_path(args.corpus),
        "out_dir": harness.repo_path(out_dir),
        "sample_count": len(receipt.get("samples", [])),
        "candidate_count": len(candidates),
        "rejected_count": len(rejected),
        "environment": {"python": platform.python_version(), "platform": platform.platform(), "gpu_required": False},
        "next_live_gate": "rent H200 only after local bundle, Netcup baseline, and noisy simulator receipts are lawful",
        "lawful": len(candidates) > 0 and all(not item["promote"] for item in candidates),
        "claim_boundary": "dry-run optimizer scaffold only; no H200 hardware used and no improved compression claim made",
    }
    (out_dir / "h200_encode_runner_receipt.json").write_text(json.dumps(dry_run_receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return dry_run_receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, default=SHIM / "finance_claim_remote_bundle")
    parser.add_argument("--out-dir", type=Path, default=SHIM / "h200_encode_dry_run")
    args = parser.parse_args()
    print(json.dumps(run(args), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
