#!/usr/bin/env python3
"""Semantic topology compression regimes for metaprobe/LLM tuning.

The regimes are intentionally blunt:

* beautiful: stable topological folding across compatible semantic basins
* ugly: asymmetric pruning that preserves statistical structure but drops context
* horrible: manifold tearing / singularity where bindings become incompatible

The output is a training prior and receipt taxonomy, not a proof of semantic
geometry. Lean can later formalize the predicates and destruction rules.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REGIMES = [
    {
        "id": "beautiful_topological_folding",
        "label": "beautiful",
        "condition": "shared_invariant_high and torsion_low and round_trip_loss_low",
        "operation": "fold compatible semantic basins into a dense shared coordinate",
        "payload": ["shared_invariant", "fold_map", "torsion", "round_trip_loss", "receipt_hash"],
        "failure_mode": "false_friend_fold",
        "lean_predicate_hint": "StableFold(a,b) := invariant_overlap a b >= tau ∧ torsion a b <= eps",
    },
    {
        "id": "ugly_asymmetric_pruning",
        "label": "ugly",
        "condition": "statistical_structure_high and indexical_structure_discarded and quality_delta_bounded",
        "operation": "shear off low-information or indexical volume while preserving routing basin",
        "payload": ["retained_terms", "dropped_context", "distortion", "quality_delta", "source_boundary"],
        "failure_mode": "nuance_collapse",
        "lean_predicate_hint": "AdmissiblePrune(x,y) := preserves_basin x y ∧ distortion x y <= budget",
    },
    {
        "id": "horrible_manifold_tearing",
        "label": "horrible",
        "condition": "torsion_high or contradiction_high or round_trip_loss_unbounded",
        "operation": "mark incompatible bindings as torn; isolate detached semantic mass instead of merging",
        "payload": ["contradiction_witness", "tear_boundary", "detached_mass_id", "origin_block", "repair_rule"],
        "failure_mode": "semantic_singularity",
        "lean_predicate_hint": "TornBinding(a,b) := torsion a b > max_torsion ∨ contradiction a b",
    },
]


def chat_record(system: str, prompt: dict[str, Any], answer: dict[str, Any]) -> dict[str, Any]:
    return {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            {"role": "assistant", "content": json.dumps(answer, ensure_ascii=False)},
        ]
    }


def curriculum_records(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    system = "You are a semantic topology compression router. Classify regimes and emit receipt boundaries."
    records: list[dict[str, Any]] = []
    for regime in receipt["regimes"]:
        records.append(
            chat_record(
                system,
                {
                    "task": "classify_semantic_compression_regime",
                    "regime": regime["label"],
                    "condition": regime["condition"],
                    "operation": regime["operation"],
                    "instruction": "Return how this regime should route a compressed semantic binding.",
                },
                {
                    "selected": True,
                    "regime_id": regime["id"],
                    "operation": regime["operation"],
                    "claim_boundary": "semantic-topology-prior-only",
                    "receipt_payload": regime["payload"],
                    "failure_mode": regime["failure_mode"],
                    "lean_predicate_hint": regime["lean_predicate_hint"],
                },
            )
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, default=Path("4-Infrastructure/shim/semantic_topology_compression_regimes_receipt.json"))
    parser.add_argument("--curriculum", type=Path, default=Path("4-Infrastructure/shim/semantic_topology_compression_regimes_curriculum.jsonl"))
    args = parser.parse_args()

    receipt = {
        "schema": "semantic_topology_compression_regimes_v1",
        "claim_boundary": "Compression regimes classify folding/pruning/tearing decisions; Lean or metaprobe receipts are required for local claims.",
        "regimes": REGIMES,
        "lawful": True,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with args.curriculum.open("w", encoding="utf-8") as handle:
        for record in curriculum_records(receipt):
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
