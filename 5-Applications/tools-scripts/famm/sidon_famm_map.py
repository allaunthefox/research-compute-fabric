#!/usr/bin/env python3
"""Sidon FAMM Map receipt runner.

Computes pair-sum uniqueness, collision scars, candidate-addition admissibility,
Theodorus capacity pressure, and a compact FAMM receipt.

This is a verifier/router, not a proof of maximality.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def pair_sums(values: list[int]) -> list[dict[str, Any]]:
    out = []
    for i, a in enumerate(values):
        for j, b in enumerate(values[i:], start=i):
            out.append({"i": i, "j": j, "a": a, "b": b, "sum": a + b})
    return out


def find_collisions(pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[int, dict[str, Any]] = {}
    collisions = []
    for p in pairs:
        s = int(p["sum"])
        if s in seen:
            q = seen[s]
            same_unordered = {p["i"], p["j"]} == {q["i"], q["j"]}
            if not same_unordered:
                collisions.append({
                    "sum_address": s,
                    "pair_a": {"i": q["i"], "j": q["j"], "values": [q["a"], q["b"]]},
                    "pair_b": {"i": p["i"], "j": p["j"], "values": [p["a"], p["b"]]},
                    "trivial_collision": False,
                    "scar": "nontrivial_pair_sum_collision",
                })
        else:
            seen[s] = p
    return collisions


def candidate_gate(values: list[int], candidate: int) -> dict[str, Any]:
    current = pair_sums(values)
    current_sums = {p["sum"] for p in current}
    new_sums = [{"a": candidate, "b": x, "sum": candidate + x} for x in values]
    new_sums.append({"a": candidate, "b": candidate, "sum": 2 * candidate})

    external = [p for p in new_sums if p["sum"] in current_sums]
    internal_count = len(new_sums) - len({p["sum"] for p in new_sums})
    admissible = len(external) == 0 and internal_count == 0
    return {
        "candidate": candidate,
        "admissible": admissible,
        "new_sums": new_sums,
        "external_collisions": external,
        "internal_duplicate_count": internal_count,
    }


def additive_energy_ordered(values: list[int]) -> int:
    counts: dict[int, int] = {}
    for a in values:
        for b in values:
            counts[a + b] = counts.get(a + b, 0) + 1
    return sum(c * c for c in counts.values())


def run(config: dict[str, Any]) -> dict[str, Any]:
    values = list(map(int, config["set"]))
    pairs = pair_sums(values)
    collisions = find_collisions(pairs)
    m = len(values)
    e_plus = additive_energy_ordered(values)
    omega = e_plus - (2 * m * m - m)
    is_sidon = len(collisions) == 0 and omega == 0

    capacity_N = config.get("capacity_N")
    capacity = None
    if capacity_N is not None:
        capacity_N = int(capacity_N)
        capacity = {
            "N": capacity_N,
            "theodorus_shell_sqrt_N": math.sqrt(capacity_N),
            "occupied": m,
            "slack": math.sqrt(capacity_N) - m,
        }

    candidate_receipt = None
    if "candidate" in config:
        candidate_receipt = candidate_gate(values, int(config["candidate"]))

    famm = {
        "sidon_collision_count": len(collisions),
        "additive_energy_ordered": e_plus,
        "omega_sidon": omega,
        "scar_class": "PASS_ZERO_SCAR" if is_sidon else "COLLISION_SCAR",
        "coarsening_agent": None if is_sidon else {
            "type": "sidon_collision_coarsener",
            "action": "downweight_or_merge_collision_basin",
            "reason": "nontrivial pair-sum collision or additive energy excess",
        },
        "capacity": capacity,
        "candidate_gate": candidate_receipt,
        "semantic_mass_lanes": {
            "collision": len(collisions),
            "additive_energy_excess": omega,
            "capacity_pressure": None if capacity is None else -capacity["slack"],
            "residual": 0 if is_sidon else len(collisions) + max(0, omega),
        },
    }

    receipt = {
        "receipt_type": "famm_sidon_map_receipt",
        "schema_version": "0.1.0",
        "set": values,
        "is_sidon": is_sidon,
        "pair_sums": pairs,
        "collisions": collisions,
        "famm": famm,
        "no_drift_boundary": (
            "This receipt verifies Sidon pair-sum uniqueness and maps failures to FAMM scars. "
            "It does not prove maximality or physical realization."
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
    print(f"Sidon: {receipt['is_sidon']}")
    print(f"Collision count: {receipt['famm']['sidon_collision_count']}")
    print(f"Omega Sidon: {receipt['famm']['omega_sidon']}")
    if receipt["famm"]["candidate_gate"] is not None:
        print(f"Candidate admissible: {receipt['famm']['candidate_gate']['admissible']}")
    print(f"Receipt hash: {receipt['receipt_hash']}")


if __name__ == "__main__":
    main()
