#!/usr/bin/env python3
"""Index Φ-scaling results across transfold documents.

The goal is a receipt-backed map, not proof promotion. It records where the
Φ-scaling equations and related transfold implementations live, and marks what
each file contributes.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]

FILES = [
    {
        "path": "0-Core-Formalism/lean/Semantics/SIGNAL_ANALYSIS_GENETIC_IMPLICATIONS.md",
        "role": "primary_analysis_document",
        "patterns": ["P ∝ S^{1/2}", "lambda_phi^{1.44042}", "DeltaE_eff", "Testable Predictions"],
    },
    {
        "path": "3-Mathematical-Models/recursive_branch_cut_self_similarity.md",
        "role": "source_model_recursive_branch_cut",
        "patterns": ["Φ²", "D_f", "DNA", "branch-cut"],
    },
    {
        "path": "6-Documentation/docs/speculative-materials/HierarchicalFieldBinding.md",
        "role": "source_model_hierarchical_field_binding",
        "patterns": ["E_binding", "State space compression", "RG flow", "Genes are bound states"],
    },
    {
        "path": "0-Core-Formalism/lean/Semantics/EvolutionaryTransfold.lean",
        "role": "ltee_transfold_implementation",
        "patterns": ["power law", "Q16_16.sqrt", "LTEE"],
    },
    {
        "path": "0-Core-Formalism/lean/Semantics/EvolutionaryTransfoldExpanded.lean",
        "role": "multi_species_transfold_implementation",
        "patterns": ["generation", "ploidy", "environment", "multiple organisms"],
    },
    {
        "path": "0-Core-Formalism/lean/Semantics/UrbanAdaptationTransfold.lean",
        "role": "urban_adaptation_transfold_implementation",
        "patterns": ["urban", "plasticity", "selection", "habitat"],
    },
    {
        "path": "0-Core-Formalism/lean/Semantics/TransfoldEquation.lean",
        "role": "enhanced_transfold_implementation",
        "patterns": ["Q16_16.sqrt", "hyperbolicPhase", "transfoldMechanicalToQuantum"],
    },
    {
        "path": "0-Core-Formalism/lean/Semantics/TransfoldEquationBaseline.lean",
        "role": "baseline_transfold_implementation",
        "patterns": ["Q16_16.sqrt", "transfoldDiscreteToQuantum", "TQFT"],
    },
    {
        "path": "0-Core-Formalism/lean/Semantics/TRANSFOLD_COMPARISON.md",
        "role": "comparison_document",
        "patterns": ["Five versions", "Invariant Root", "Mechanics Receipt Need"],
    },
]


def line_hits(path: Path, patterns: list[str]) -> dict[str, list[dict[str, Any]]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    hits: dict[str, list[dict[str, Any]]] = {}
    for pattern in patterns:
        pattern_hits: list[dict[str, Any]] = []
        needle = pattern.lower()
        for idx, line in enumerate(lines, start=1):
            if needle in line.lower():
                pattern_hits.append({"line": idx, "text": line.strip()[:220]})
        hits[pattern] = pattern_hits[:8]
    return hits


def classify_status(hits: dict[str, list[dict[str, Any]]]) -> str:
    present = sum(1 for values in hits.values() if values)
    if present == len(hits):
        return "anchored"
    if present:
        return "partial"
    return "missing_patterns"


def stable_hash(payload: dict[str, Any]) -> str:
    stable = {k: v for k, v in payload.items() if k != "receipt_hash"}
    encoded = json.dumps(stable, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def main() -> None:
    entries: list[dict[str, Any]] = []
    for item in FILES:
        path = REPO / item["path"]
        exists = path.exists()
        hits = line_hits(path, item["patterns"]) if exists else {}
        entries.append(
            {
                "path": item["path"],
                "role": item["role"],
                "exists": exists,
                "status": classify_status(hits) if exists else "missing_file",
                "patterns": item["patterns"],
                "hits": hits,
            }
        )

    receipt: dict[str, Any] = {
        "runner": "phi_scaling_transfold_results_index.py",
        "purpose": "receipt-backed map of Φ-scaling and transfold result locations",
        "core_equation": (
            "P proportional to S^(1/2) * lambda_phi^(1.44042) "
            "* exp(-gamma * DeltaE_eff/kT)"
        ),
        "entries": entries,
        "summary": {
            "file_count": len(entries),
            "existing_count": sum(1 for entry in entries if entry["exists"]),
            "anchored_count": sum(1 for entry in entries if entry["status"] == "anchored"),
            "partial_count": sum(1 for entry in entries if entry["status"] == "partial"),
            "missing_file_count": sum(1 for entry in entries if entry["status"] == "missing_file"),
        },
        "claim_boundary": (
            "This index records locations and equation surfaces. It does not prove "
            "the Phi hypothesis, genetic scaling, physical universality, or any "
            "compression result."
        ),
    }
    receipt["receipt_hash"] = stable_hash(receipt)

    out = Path(__file__).with_name("phi_scaling_transfold_results_index_receipt.json")
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt["summary"], indent=2, sort_keys=True))
    print(f"receipt: {out}")
    print(f"receipt_hash: {receipt['receipt_hash']}")


if __name__ == "__main__":
    main()
