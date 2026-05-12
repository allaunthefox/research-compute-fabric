#!/usr/bin/env python3
"""Receipt for the cross-domain adaptation evidence bundle.

The input was a Consensus-style LaTeX/BibTeX synthesis supplied in chat.  This
runner preserves the useful structure without treating the synthesis as primary
verification of every citation.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
RECEIPT = SHIM / "cross_domain_adaptation_evidence_prior_receipt.json"
CURRICULUM = SHIM / "cross_domain_adaptation_evidence_prior_curriculum.jsonl"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_receipt() -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "schema": "cross_domain_adaptation_evidence_prior_v1",
        "source_type": "user_supplied_consensus_latex_synthesis",
        "numeric_review_artifact": "6-Documentation/docs/cross_domain_adaptation_numeric_review.md",
        "numeric_reference_count": 25,
        "paper_count_reported": {
            "identified": 562_365,
            "screened": 239,
            "eligible": 204,
            "included": 50,
        },
        "evidence_lanes": [
            {
                "lane": "sparse_representation_and_compressive_sensing",
                "strength": 10,
                "adaptation_read": "shared sparsity or k-term structure transfers well across signal, image, and compression domains",
                "representative_keys": [
                    "Cohen2008Compressed",
                    "Baraniuk2008Model-Based",
                    "Rani2018A",
                    "Wang2023Compressed",
                ],
            },
            {
                "lane": "neural_and_distributed_compression",
                "strength": 8,
                "adaptation_read": "learned compressors can rediscover useful coding structures but require empirical validation",
                "representative_keys": [
                    "Ozyilkan2023Neural",
                    "Sohrabi2022Learning",
                    "Dai2022Image",
                    "Liu2024Compression",
                ],
            },
            {
                "lane": "transfer_learning_and_domain_adaptation",
                "strength": 7,
                "adaptation_read": "transfer is useful when source and target share structure; negative transfer remains a gate",
                "representative_keys": [
                    "Hosna2022Transfer",
                    "Zhuang2019A",
                    "Ling2023Domain",
                    "Lu2025A",
                ],
            },
            {
                "lane": "topological_and_algebraic_methods",
                "strength": 6,
                "adaptation_read": "topology can transport abstract structure into compression and reconstruction, but tooling is less mainstream",
                "representative_keys": [
                    "Ebli2022Morse",
                    "Carlsson2020Topological",
                ],
            },
            {
                "lane": "theory_to_practice_gap",
                "strength": 5,
                "adaptation_read": "guarantees, convergence, and noise models do not automatically survive domain transfer",
                "representative_keys": [
                    "Chen2025Greedy",
                    "Wang2023Distributed",
                    "Kipnis2020Gaussian",
                ],
            },
        ],
        "gap_matrix": {
            "sparse_representation": {
                "signal_theory": 8,
                "compression_algorithms": 12,
                "mathematical_exploration": 2,
            },
            "neural_network_adaptation": {
                "signal_theory": 6,
                "compression_algorithms": 7,
                "mathematical_exploration": 1,
            },
            "topological_methods": {
                "signal_theory": 2,
                "compression_algorithms": "GAP",
                "mathematical_exploration": 4,
            },
            "transfer_learning": {
                "signal_theory": 5,
                "compression_algorithms": 4,
                "mathematical_exploration": 2,
            },
        },
        "adaptation_to_t16_equation_prior": {
            "supports": [
                "feature extraction before expensive validation",
                "regime-specific transfer instead of one universal model",
                "sparse/topological feature families for equation traces",
                "negative-transfer gates for mismatched domains",
            ],
            "does_not_support": [
                "automatic proof transfer",
                "automatic compression improvement",
                "using classifier confidence as a receipt",
                "using Consensus synthesis as primary citation verification",
            ],
        },
        "bibtex_hygiene_notes": [
            "Vetterli2001Wavelets,, contains a malformed citation key with a double comma",
            "The AMA/numeric version corrects this into reference 24",
            "Consensus-generated citation metadata should be verified before publication",
            "arXiv:2604.18579 is an astronomy candidate-search pipeline; the adaptation is methodological",
        ],
        "claim_boundary": (
            "This prior records cross-domain adaptation evidence as a research "
            "map. It does not prove that any specific T16-derived equation "
            "pipeline, compression route, or Hutter transform works."
        ),
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    return receipt


def write_curriculum(receipt: dict[str, Any]) -> None:
    rows = [
        {
            "task": "classify_adaptation_lane",
            "input": "paper or method claiming cross-domain transfer",
            "target": "sparse, neural, transfer, topology, or theory-practice lane",
        },
        {
            "task": "apply_negative_transfer_gate",
            "input": "source method and target equation domain",
            "target": "shared-structure evidence before transfer",
        },
        {
            "task": "separate_evidence_from_receipt",
            "input": "literature support for method transfer",
            "target": "proposal prior only until local validation succeeds",
        },
    ]
    CURRICULUM.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def main() -> None:
    receipt = build_receipt()
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_curriculum(receipt)
    print(json.dumps({
        "receipt": str(RECEIPT.relative_to(REPO)),
        "curriculum": str(CURRICULUM.relative_to(REPO)),
        "receipt_hash": receipt["receipt_hash"],
        "evidence_lane_count": len(receipt["evidence_lanes"]),
        "included_papers_reported": receipt["paper_count_reported"]["included"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
