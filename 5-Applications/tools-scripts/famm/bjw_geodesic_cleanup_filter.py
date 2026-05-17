#!/usr/bin/env python3
"""Builder-Judge-Warden Geodesic Cleanup Filter.

Scores candidate cleanup moves, accepts only Judge-pass / Warden-safe moves,
and emits a cleanup receipt.

This runner is intentionally generic: it evaluates provided candidate moves
rather than proving math by itself.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def move_score(move: dict[str, Any], weights: dict[str, float]) -> float:
    builder = move.get("builder", {})
    judge = move.get("judge", {})
    warden = move.get("warden", {})

    dc = float(builder.get("delta_complexity", 0.0))
    dr = float(builder.get("delta_residual", 0.0))
    scar = float(warden.get("penalty", 0.0))
    inv = 1.0 if judge.get("invariant_preserved", False) else 0.0
    proof = 1.0 if judge.get("receipt_pass", False) else 0.0

    return (
        float(weights.get("complexity", 1.0)) * dc
        + float(weights.get("residual", 1.0)) * dr
        + float(weights.get("scar", 1.0)) * scar
        - float(weights.get("invariant", 1.0)) * inv
        - float(weights.get("proof_burden", 0.5)) * proof
    )


def run(config: dict[str, Any]) -> dict[str, Any]:
    weights = config.get("weights", {})
    threshold = float(config.get("warden_threshold", 0.25))

    source_hash = sha256_json(config.get("source_object", config.get("source_description", "")))

    accepted = []
    rejected = []

    for move in sorted(config.get("candidate_moves", []), key=lambda m: move_score(m, weights)):
        judge = move.get("judge", {})
        warden = move.get("warden", {})
        score = move_score(move, weights)
        penalty = float(warden.get("penalty", 0.0))

        decision = (
            "ACCEPT"
            if judge.get("invariant_preserved", False)
            and judge.get("receipt_pass", False)
            and penalty <= threshold
            else "REJECT"
        )

        enriched = {
            **move,
            "cleanup_score": score,
            "decision": decision,
            "move_hash": sha256_json(move),
        }

        if decision == "ACCEPT":
            accepted.append(enriched)
        else:
            rejected.append(enriched)

    final_object = {
        "source_hash": source_hash,
        "accepted_move_hashes": [m["move_hash"] for m in accepted],
        "final_claim": config.get("final_claim", "cleaned object requires downstream exact verifier"),
    }
    final_hash = sha256_json(final_object)

    receipt = {
        "receipt_type": "famm_bjw_geodesic_cleanup_receipt",
        "schema_version": "0.1.0",
        "source_object_hash": source_hash,
        "source_description": config.get("source_description", ""),
        "accepted_geodesic": accepted,
        "rejected_moves": rejected,
        "final_object_hash": final_hash,
        "exact_receipt": {
            "judge_passed_all_accepted_moves": all(m["judge"].get("receipt_pass", False) for m in accepted),
            "warden_blocked_rejected_moves": len(rejected),
            "requires_downstream_exact_verifier": True,
        },
        "cleanup_metrics": {
            "candidate_count": len(config.get("candidate_moves", [])),
            "accepted_count": len(accepted),
            "rejected_count": len(rejected),
            "total_cleanup_score": sum(m["cleanup_score"] for m in accepted),
        },
        "no_drift_boundary": (
            "This filter ranks and accepts cleanup moves. It is not a proof generator. "
            "Downstream exact verification remains mandatory."
        ),
    }
    receipt["receipt_hash"] = sha256_json(receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    receipt = run(config)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")

    print(f"Wrote {out_path}")
    print(f"Accepted: {receipt['cleanup_metrics']['accepted_count']}")
    print(f"Rejected: {receipt['cleanup_metrics']['rejected_count']}")
    print(f"Final object hash: {receipt['final_object_hash']}")
    print(f"Receipt hash: {receipt['receipt_hash']}")


if __name__ == "__main__":
    main()
