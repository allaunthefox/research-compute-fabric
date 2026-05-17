#!/usr/bin/env python3
"""BraidStorm Sidon Crossing Anti-Alias Gate.

Assigns/validates Sidon labels for BraidStorm strand crossings.
Supports integer and modular address modes. Emits a FAMM receipt.
"""
from __future__ import annotations
import argparse, hashlib, json, math, random
from pathlib import Path
from typing import Any


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def pair_iter(n: int, allow_self: bool):
    for i in range(n):
        start = i if allow_self else i + 1
        for j in range(start, n):
            yield i, j


def address(a: int, b: int, mode: str, modulus: int | None) -> int:
    s = a + b
    if mode == "modular":
        if modulus is None:
            raise ValueError("modular mode requires modulus/address_budget")
        return s % modulus
    return s


def validate_labels(labels: list[int], mode: str = "integer", modulus: int | None = None, allow_self: bool = True) -> dict[str, Any]:
    seen: dict[int, tuple[int, int]] = {}
    collisions = []
    pairs = []
    for i, j in pair_iter(len(labels), allow_self):
        addr = address(labels[i], labels[j], mode, modulus)
        pair = {"i": i, "j": j, "a_i": labels[i], "a_j": labels[j], "address": addr}
        pairs.append(pair)
        if addr in seen:
            u, v = seen[addr]
            if {u, v} != {i, j}:
                collisions.append({
                    "address": addr,
                    "pair_a": {"i": u, "j": v, "labels": [labels[u], labels[v]]},
                    "pair_b": {"i": i, "j": j, "labels": [labels[i], labels[j]]},
                    "scar": "braidstorm_pair_address_alias",
                })
        else:
            seen[addr] = (i, j)
    return {"pairs": pairs, "collisions": collisions, "is_sidon_crossing_code": len(collisions) == 0}


def greedy_construct(m: int, budget: int, mode: str, allow_self: bool, seed: int = 0, max_restarts: int = 256) -> list[int]:
    """Heuristic constructor. Not a maximality proof."""
    rng = random.Random(seed)
    best: list[int] = []
    values = list(range(1, budget + 1)) if mode == "integer" else list(range(budget))
    modulus = budget if mode == "modular" else None

    for _ in range(max_restarts):
        rng.shuffle(values)
        labels: list[int] = []
        used_addrs: dict[int, tuple[int, int]] = {}
        for x in values:
            ok = True
            trial_addrs = []
            for idx, y in enumerate(labels):
                addr = address(x, y, mode, modulus)
                if addr in used_addrs or addr in trial_addrs:
                    ok = False
                    break
                trial_addrs.append(addr)
            if ok and allow_self:
                addr = address(x, x, mode, modulus)
                if addr in used_addrs or addr in trial_addrs:
                    ok = False
                else:
                    trial_addrs.append(addr)
            if ok:
                new_index = len(labels)
                for idx, y in enumerate(labels):
                    used_addrs[address(x, y, mode, modulus)] = (idx, new_index)
                if allow_self:
                    used_addrs[address(x, x, mode, modulus)] = (new_index, new_index)
                labels.append(x)
                if len(labels) >= m:
                    return sorted(labels)
        if len(labels) > len(best):
            best = sorted(labels)
    return best


def run(config: dict[str, Any]) -> dict[str, Any]:
    m = int(config.get("strand_count", len(config.get("labels", []))))
    budget = int(config.get("address_budget", max(1, m*m)))
    mode = config.get("address_mode", "integer")
    allow_self = bool(config.get("allow_self_crossings", True))
    seed = int(config.get("seed", 0))
    max_restarts = int(config.get("max_restarts", 256))

    labels = config.get("labels")
    constructed = False
    if labels is None:
        labels = greedy_construct(m, budget, mode, allow_self, seed=seed, max_restarts=max_restarts)
        constructed = True
    labels = [int(x) for x in labels]

    validation = validate_labels(labels, mode=mode, modulus=budget if mode == "modular" else None, allow_self=allow_self)
    collision_count = len(validation["collisions"])
    capacity_prior = math.sqrt(budget)
    slack = capacity_prior - len(labels)

    receipt = {
        "receipt_type": "famm_braidstorm_sidon_crossing_receipt",
        "schema_version": "0.1.0",
        "problem": "BraidStorm pairwise crossing anti-aliasing",
        "strand_count_requested": m,
        "strand_count_labeled": len(labels),
        "address_budget": budget,
        "address_mode": mode,
        "allow_self_crossings": allow_self,
        "constructed_by_runner": constructed,
        "labels": labels,
        "capacity": {
            "theodorus_sqrt_budget": capacity_prior,
            "slack_vs_sqrt_budget": slack,
            "capacity_prior_only": True,
        },
        "validation": validation,
        "famm": {
            "residual_collision_count": collision_count,
            "scar_class": "PASS_ZERO_ALIAS" if collision_count == 0 and len(labels) == m else "ALIAS_OR_PARTIAL_SCAR",
            "coarsening_agent": None if collision_count == 0 and len(labels) == m else {
                "type": "braidstorm_sidon_address_alias_or_partial_assignment",
                "action": "coarsen_or_downweight_this_label_basin",
                "reason": "pair-address aliases exist or target strand count was not reached",
            }
        },
        "nuvmap": {
            "label_hash": sha256_json(labels),
            "pair_address_hash": sha256_json(validation["pairs"]),
            "collision_hash": sha256_json(validation["collisions"]),
        },
        "no_drift_boundary": "This receipt verifies pair-crossing address uniqueness for a chosen label set. It does not prove optimality, maximality, or BraidStorm convergence.",
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
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {out}")
    print(f"Requested strands: {receipt['strand_count_requested']}")
    print(f"Labeled strands: {receipt['strand_count_labeled']}")
    print(f"Collision count: {receipt['famm']['residual_collision_count']}")
    print(f"Scar class: {receipt['famm']['scar_class']}")
    print(f"Receipt hash: {receipt['receipt_hash']}")

if __name__ == "__main__":
    main()
