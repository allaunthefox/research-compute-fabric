#!/usr/bin/env python3
"""Receipt-weighted network topology model profile.

This probe keeps the original convergence weights as the raw hypothesis profile
and derives a conservative receipt-weighted profile.  It does not validate the
network topology theory; it begins the reweighting pass by downweighting model
charts that still have coefficient, provenance, prediction, or operational-risk
debt in the Underverse ledger.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
DATABASE = REPO / "shared-data" / "network_topology_database.json"
UNDERVERSE_RECEIPT = (
    REPO / "shared-data" / "data" / "underverse_variant_accounting" / "underverse_variant_accounting_receipt.json"
)
OUT_DIR = REPO / "shared-data" / "data" / "network_topology_model_reweighting"
RECEIPT = OUT_DIR / "network_topology_model_reweighting_receipt.json"
SUMMARY = OUT_DIR / "network_topology_model_reweighting.md"
TIDDLER = REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers" / "Network Topology Model Reweighting.tid"

REWEIGHT_RULES = {
    "hft_infrastructure": {
        "receipt_multiplier": 0.55,
        "reason": "high signal-speed relevance but overweighted by unreceipted ultimate-validation language",
        "decision": "HOLD_COEFFICIENT_RECEIPT_DEBT",
    },
    "public_internet_map": {
        "receipt_multiplier": 1.20,
        "reason": "closest to directly observed topology evidence in the current profile",
        "decision": "KEEP_OBSERVED_PRIOR_HIGH",
    },
    "soliton_wave_analysis": {
        "receipt_multiplier": 0.70,
        "reason": "useful physics chart, but equation adapter and negative controls remain unclosed",
        "decision": "HOLD_ANALOGY_ADAPTER",
    },
    "slime_mold_physics": {
        "receipt_multiplier": 0.80,
        "reason": "useful pathfinding prior, but cross-domain biological adapter remains fixture-grade",
        "decision": "HOLD_ANALOGY_ADAPTER",
    },
    "civic_design_mathematics": {
        "receipt_multiplier": 0.85,
        "reason": "established network heuristics, but local coefficient receipts are missing",
        "decision": "HOLD_COEFFICIENT_RECEIPT_DEBT",
    },
    "regional_infrastructure": {
        "receipt_multiplier": 0.90,
        "reason": "high-resolution observed infrastructure fixtures are useful but still need source receipts",
        "decision": "HOLD_PROVENANCE",
    },
    "subway_underground": {
        "receipt_multiplier": 0.85,
        "reason": "observed engineered-network analogue with remaining adapter and dataset debt",
        "decision": "HOLD_ANALOGY_ADAPTER",
    },
    "major_consumer_nodes": {
        "receipt_multiplier": 0.70,
        "reason": "demand-pressure prior, but entity, power, and causality receipts are incomplete",
        "decision": "HOLD_TOPOLOGY_PREDICTION_VALIDATION",
    },
    "backhaul_providers": {
        "receipt_multiplier": 0.70,
        "reason": "prediction-heavy layer; keep as route hint until outcome receipts close",
        "decision": "HOLD_TOPOLOGY_PREDICTION_VALIDATION",
    },
}


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_obj(obj: Any) -> str:
    return sha256_bytes(stable_json(obj).encode("utf-8"))


def file_hash(path: Path) -> str | None:
    return sha256_bytes(path.read_bytes()) if path.exists() else None


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_profile() -> dict[str, Any]:
    database = read_json(DATABASE)
    weights = database["fundamental_equation_data"]["methodology_weights"]
    adjusted = {}
    for name, raw in weights.items():
        rule = REWEIGHT_RULES[name]
        adjusted[name] = raw["weight"] * rule["receipt_multiplier"]
    adjusted_sum = sum(adjusted.values())

    methods = []
    for name, raw in weights.items():
        rule = REWEIGHT_RULES[name]
        normalized = adjusted[name] / adjusted_sum
        methods.append(
            {
                "methodology": name,
                "raw_weight": raw["weight"],
                "alignment_score": raw["alignment_score"],
                "raw_validation_status": raw["validation_status"],
                "receipt_multiplier": rule["receipt_multiplier"],
                "receipt_reweighted_weight": round(normalized, 6),
                "weight_delta": round(normalized - raw["weight"], 6),
                "decision": rule["decision"],
                "reason": rule["reason"],
            }
        )
    weighted_alignment = sum(item["receipt_reweighted_weight"] * item["alignment_score"] for item in methods)
    profile = {
        "schema": "network_topology_model_reweighting_profile_v1",
        "profile_name": "receipt_reweighted_v1",
        "raw_database": rel(DATABASE),
        "raw_database_sha256": file_hash(DATABASE),
        "underverse_receipt": rel(UNDERVERSE_RECEIPT),
        "underverse_receipt_sha256": file_hash(UNDERVERSE_RECEIPT),
        "reweight_rule": "receipt_reweighted_weight = normalize(raw_weight * receipt_multiplier)",
        "claim_boundary": (
            "Reweighting profile only. This does not validate the topology theory, "
            "admit predicted network nodes, or operationalize fiber/DAS inference. "
            "It starts a conservative weighting pass that treats unreceipted "
            "equation, coefficient, analogy, prediction, and privacy-risk surfaces "
            "as HOLD or QUARANTINE lanes."
        ),
        "methods": methods,
        "aggregates": {
            "method_count": len(methods),
            "raw_weight_sum": round(sum(item["raw_weight"] for item in methods), 6),
            "receipt_reweighted_sum": round(sum(item["receipt_reweighted_weight"] for item in methods), 6),
            "raw_methodology_convergence": database["metadata"].get("methodology_convergence"),
            "receipt_weighted_alignment": round(weighted_alignment, 6),
            "largest_gain": max(methods, key=lambda item: item["weight_delta"])["methodology"],
            "largest_drop": min(methods, key=lambda item: item["weight_delta"])["methodology"],
        },
        "decision": "ADMIT_REWEIGHTING_PROFILE_AS_HOLD_ACCOUNTING",
    }
    profile["profile_hash"] = hash_obj({k: v for k, v in profile.items() if k != "profile_hash"})
    return profile


def build_receipt(profile: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "network_topology_model_reweighting_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "profile_hash": profile["profile_hash"],
        "profile_name": profile["profile_name"],
        "aggregates": profile["aggregates"],
        "decision": profile["decision"],
        "claim_boundary": profile["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(profile: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# Network Topology Model Reweighting",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`  ",
        f"Profile hash: `{profile['profile_hash']}`",
        "",
        profile["claim_boundary"],
        "",
        "## Rule",
        "",
        f"`{profile['reweight_rule']}`",
        "",
        "## Aggregates",
        "",
        f"- Raw convergence: `{profile['aggregates']['raw_methodology_convergence']}`",
        f"- Receipt-weighted alignment: `{profile['aggregates']['receipt_weighted_alignment']}`",
        f"- Largest gain: `{profile['aggregates']['largest_gain']}`",
        f"- Largest drop: `{profile['aggregates']['largest_drop']}`",
        "",
        "## Method Weights",
        "",
        "| Method | Raw | Multiplier | Reweighted | Delta | Decision |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for item in profile["methods"]:
        lines.append(
            f"| {item['methodology']} | {item['raw_weight']:.6f} | {item['receipt_multiplier']:.2f} | "
            f"{item['receipt_reweighted_weight']:.6f} | {item['weight_delta']:+.6f} | {item['decision']} |"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
        ]
    )
    for item in profile["methods"]:
        lines.append(f"- `{item['methodology']}`: {item['reason']}")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tiddler(profile: dict[str, Any], receipt: dict[str, Any]) -> None:
    text = [
        "title: Network Topology Model Reweighting",
        "tags: NetworkTopology Underverse Receipt HOLD",
        "type: text/vnd.tiddlywiki",
        "",
        "! Network Topology Model Reweighting",
        "",
        f"Decision: `{receipt['decision']}`",
        "",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        f"Profile hash: `{profile['profile_hash']}`",
        "",
        "!! Rule",
        "",
        f"`{profile['reweight_rule']}`",
        "",
        "!! Method Weights",
        "",
        "| Method | Raw | Multiplier | Reweighted | Delta | Decision |h",
    ]
    for item in profile["methods"]:
        text.append(
            f"| {item['methodology']} | {item['raw_weight']:.6f} | {item['receipt_multiplier']:.2f} | "
            f"{item['receipt_reweighted_weight']:.6f} | {item['weight_delta']:+.6f} | {item['decision']} |"
        )
    text.extend(
        [
            "",
            "!! Claim Boundary",
            "",
            profile["claim_boundary"],
            "",
            "!! Links",
            "",
            f"* Receipt: `{rel(RECEIPT)}`",
            f"* Summary: `{rel(SUMMARY)}`",
            f"* Database: `{rel(DATABASE)}`",
            f"* Underverse receipt: `{rel(UNDERVERSE_RECEIPT)}`",
        ]
    )
    TIDDLER.write_text("\n".join(text) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    profile = build_profile()
    receipt = build_receipt(profile)
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT_DIR / "network_topology_model_reweighting_profile.json").write_text(
        json.dumps(profile, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_summary(profile, receipt)
    write_tiddler(profile, receipt)
    print(
        json.dumps(
            {
                "receipt": rel(RECEIPT),
                "receipt_hash": receipt["receipt_hash"],
                "profile_hash": profile["profile_hash"],
                "aggregates": profile["aggregates"],
                "summary": rel(SUMMARY),
                "tiddler": rel(TIDDLER),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
