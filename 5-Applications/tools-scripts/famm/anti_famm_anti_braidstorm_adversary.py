#!/usr/bin/env python3
"""Anti-FAMM / Anti-BraidStorm adversarial-dual receipt runner.

Scores candidate adversarial findings. It does not prove a theorem; it packages
hostile test evidence into a Warden-facing receipt.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def score_anti_famm(test: dict[str, Any]) -> dict[str, Any]:
    invisible = clamp01(test.get("projection_invisibility", 0.0))
    target_change = clamp01(test.get("target_behavior_change", 0.0))
    invariant_fail = clamp01(test.get("invariant_failure", 0.0))
    false_scar = clamp01(test.get("false_scar_evidence", 0.0))
    residual = clamp01(test.get("hidden_residual", 0.0))
    risk = clamp01(0.30*invisible + 0.30*target_change + 0.20*invariant_fail + 0.10*false_scar + 0.10*residual)
    return {
        "test_id": test.get("id", sha256_json(test)[:12]),
        "type": "anti_famm",
        "risk": risk,
        "decision": "WARDEN_BLOCK_OR_REOPEN" if risk >= 0.5 else "PASS_ADVERSARY_CHECK",
        "test_hash": sha256_json(test),
        "summary": {
            "projection_invisibility": invisible,
            "target_behavior_change": target_change,
            "invariant_failure": invariant_fail,
            "false_scar_evidence": false_scar,
            "hidden_residual": residual
        }
    }


def score_anti_braid(test: dict[str, Any]) -> dict[str, Any]:
    order = clamp01(test.get("braid_order_residual", 0.0))
    alias = clamp01(test.get("receipt_alias_risk", 0.0))
    fake = clamp01(test.get("fake_receipt_risk", 0.0))
    toxic = clamp01(test.get("toxic_recombination_risk", 0.0))
    scar_mask = clamp01(test.get("scar_masking_risk", 0.0))
    local_global = clamp01(test.get("local_pass_global_fail", 0.0))
    risk = clamp01(0.20*order + 0.20*alias + 0.15*fake + 0.15*toxic + 0.15*scar_mask + 0.15*local_global)
    return {
        "test_id": test.get("id", sha256_json(test)[:12]),
        "type": "anti_braidstorm",
        "risk": risk,
        "decision": "WARDEN_BLOCK_OR_REOPEN" if risk >= 0.5 else "PASS_ADVERSARY_CHECK",
        "test_hash": sha256_json(test),
        "summary": {
            "braid_order_residual": order,
            "receipt_alias_risk": alias,
            "fake_receipt_risk": fake,
            "toxic_recombination_risk": toxic,
            "scar_masking_risk": scar_mask,
            "local_pass_global_fail": local_global
        }
    }


def run(config: dict[str, Any]) -> dict[str, Any]:
    anti_famm = [score_anti_famm(t) for t in config.get("anti_famm_tests", [])]
    anti_braid = [score_anti_braid(t) for t in config.get("anti_braidstorm_tests", [])]
    all_tests = anti_famm + anti_braid
    blocked = [t for t in all_tests if t["decision"] == "WARDEN_BLOCK_OR_REOPEN"]

    receipt = {
        "receipt_type": "famm_adversarial_duals_receipt",
        "schema_version": "0.1.0",
        "target": config.get("target", {}),
        "anti_famm_results": anti_famm,
        "anti_braidstorm_results": anti_braid,
        "summary": {
            "test_count": len(all_tests),
            "blocked_or_reopened_count": len(blocked),
            "max_risk": max([t["risk"] for t in all_tests], default=0.0)
        },
        "warden_decision": "BLOCK_OR_REOPEN_ROUTE" if blocked else "ALLOW_PROMOTION_CANDIDATE",
        "nuvmap": {
            "target_hash": sha256_json(config.get("target", {})),
            "test_hashes": [t["test_hash"] for t in all_tests],
            "adversarial_dual_hash": sha256_json([t["test_hash"] for t in all_tests])
        },
        "no_drift_boundary": "Anti-FAMM and Anti-BraidStorm expose adversarial failure modes. Passing these checks is not a global proof by itself."
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
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {out}")
    print(f"Tests: {receipt['summary']['test_count']}")
    print(f"Blocked/reopened: {receipt['summary']['blocked_or_reopened_count']}")
    print(f"Warden decision: {receipt['warden_decision']}")
    print(f"Receipt hash: {receipt['receipt_hash']}")


if __name__ == "__main__":
    main()
