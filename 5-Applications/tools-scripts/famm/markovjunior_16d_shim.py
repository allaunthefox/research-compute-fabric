#!/usr/bin/env python3
"""MarkovJunior 16D PIST Rewrite Shim.

Projects MarkovJunior-style rewrite rules into 16D FAMM/PIST/NUVMAP anchors.

This runner does not execute the full MarkovJunior XML language. It is a shim:
rules and optional constraints are mapped into 16D route objects, hashes, and
receipts so later tools can use them as PIST/Delta-DAG inputs.
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


def norm_hash(value: Any, scale: float = 1.0) -> float:
    h = hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).digest()
    n = int.from_bytes(h[:8], "big")
    return (n / float((1 << 64) - 1)) * scale


def pattern_mass(pattern: str) -> float:
    if not pattern:
        return 0.0
    non_wild = sum(1 for ch in pattern if ch != "*")
    return non_wild / max(1, len(pattern))


def delta_mass(left: str, right: str) -> float:
    n = max(len(left), len(right), 1)
    changed = 0
    for i in range(n):
        l = left[i] if i < len(left) else ""
        r = right[i] if i < len(right) else ""
        if r != "*" and l != r:
            changed += 1
    return changed / n


def chirality_score(value: str) -> float:
    mapping = {
        "left": 0.25,
        "right": 0.75,
        "neutral": 0.5,
        "clockwise": 0.8,
        "counterclockwise": 0.2,
    }
    return float(mapping.get(str(value).lower(), 0.5))


def rule_anchor(rule: dict[str, Any], constraints: dict[str, Any], index: int, total: int) -> dict[str, Any]:
    left = str(rule.get("left", ""))
    right = str(rule.get("right", ""))
    weight = float(rule.get("weight", 1.0))
    obs = constraints.get("observations", [])

    pm = pattern_mass(left)
    dm = delta_mass(left, right)
    wc = left.count("*") / max(1, len(left))
    obs_pressure = min(1.0, sum(float(o.get("weight", 1.0)) for o in obs) / max(1, len(obs) or 1))
    rule_order_pressure = 1.0 - (index / max(1, total - 1)) if total > 1 else 1.0
    route_cost = min(1.0, (len(left) + len(right)) / 64.0)
    receipt_strength = 1.0 if left and right else 0.25
    scar = 0.0 if left and right and len(left) == len(right) else 0.35
    residual = 0.0 if len(left) == len(right) else abs(len(left) - len(right)) / max(len(left), len(right), 1)
    invariant_overlap = 1.0 - min(1.0, dm * 0.5 + scar * 0.5)

    vector = [
        norm_hash({"left": left, "right": right, "id": rule.get("id")}),
        min(1.0, float(rule.get("dimensions", 2)) / 16.0),
        pm,
        dm,
        rule_order_pressure,
        obs_pressure,
        chirality_score(rule.get("chirality", "neutral")),
        min(1.0, pm + dm),
        norm_hash({"recurrence": left + "->" + right}),
        dm,
        scar,
        residual,
        invariant_overlap,
        route_cost,
        receipt_strength,
        wc,
    ]

    payload = {
        "id": rule.get("id", f"rule_{index}"),
        "left": left,
        "right": right,
        "node": rule.get("node", "exists"),
        "weight": weight,
        "orientation": rule.get("orientation", "axis_aligned"),
        "chirality": rule.get("chirality", "neutral"),
        "metrics": {
            "pattern_mass": pm,
            "delta_mass": dm,
            "wildcard_fraction": wc,
            "constraint_pressure": obs_pressure,
            "scar": scar,
            "residual": residual,
            "invariant_overlap": invariant_overlap,
            "route_cost": route_cost,
            "receipt_strength": receipt_strength,
        },
        "vector16": vector,
        "rule_hash": sha256_json(rule),
    }
    payload["anchor_hash"] = sha256_json(payload)
    return payload


def run(config: dict[str, Any]) -> dict[str, Any]:
    rules = config.get("rules", [])
    constraints = config.get("constraints", {})
    anchors = [rule_anchor(rule, constraints, i, len(rules)) for i, rule in enumerate(rules)]

    source = config.get("source", {})
    grid = config.get("grid", {})
    projection = config.get("projection", {})

    nuvmap = {
        "projection": projection.get("nuvmap_projection", "frontier"),
        "grid_hash": sha256_json(grid),
        "constraints_hash": sha256_json(constraints),
        "rule_anchor_hashes": [a["anchor_hash"] for a in anchors],
        "dag_node_seed": sha256_json({
            "grid": grid,
            "constraints": constraints,
            "anchors": [a["anchor_hash"] for a in anchors],
        }),
    }

    receipt = {
        "receipt_type": "famm_markovjunior_16d_shim_receipt",
        "schema_version": "0.1.0",
        "source": source,
        "grid": grid,
        "constraints": constraints,
        "projection": projection,
        "rules": rules,
        "anchors": anchors,
        "nuvmap": nuvmap,
        "pist_transition_form": "X_{t+1}=Pi_adm[PIST_r(X_t)+Delta_MJ(r_t,m_t)]",
        "no_drift_boundary": (
            "This shim projects MarkovJunior-style rewrite rules into 16D FAMM/PIST anchors. "
            "It does not execute full MarkovJunior XML semantics or prove generated artifacts correct."
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
    print(f"Rules projected: {len(receipt['anchors'])}")
    print(f"NUVMAP DAG seed: {receipt['nuvmap']['dag_node_seed']}")
    print(f"Receipt hash: {receipt['receipt_hash']}")


if __name__ == "__main__":
    main()
