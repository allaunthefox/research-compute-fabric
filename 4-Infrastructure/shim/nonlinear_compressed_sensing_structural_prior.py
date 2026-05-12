#!/usr/bin/env python3
"""Receipt for nonlinear compressed sensing as a structural transfer prior."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
RECEIPT = SHIM / "nonlinear_compressed_sensing_structural_prior_receipt.json"
CURRICULUM = SHIM / "nonlinear_compressed_sensing_structural_prior_curriculum.jsonl"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_receipt() -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "schema": "nonlinear_compressed_sensing_structural_prior_v1",
        "source_type": "user_supplied_consensus_bibtex_and_meter",
        "consensus_meter": {
            "claim": (
                "Compressed sensing ideas extend beyond linear sparse recovery, "
                "but only under specific structural and regularity conditions."
            ),
            "n": 7,
            "yes_percent": 86,
            "yes_papers": 6,
            "no_percent": 14,
            "no_papers": 1,
            "yes_citations_total": 354,
            "no_citations_total": 8,
            "yes_average_year": 2014,
            "no_average_year": 2019,
        },
        "structural_conditions": [
            "low_dimensional_structure",
            "sparsity_or_structured_sparsity",
            "RIP_or_generalized_RIP_like_condition",
            "Lipschitz_measurement_map_or_Lipschitz_generator",
            "stable_Jacobian_or_local_regular_measurement_operator",
            "distinct_parameters_relative_to_operator_correlation",
            "bounded_noise_and_quantization_model",
            "sample_complexity_scales_with_intrinsic_dimension",
        ],
        "nonlinear_model_lanes": [
            {
                "lane": "mildly_nonlinear_observations",
                "core_condition": "nonlinear map is Lipschitz and satisfies generalized RIP-like regularity",
                "guarantee_shape": "iterative hard thresholding can stably recover sparse or structured signals",
                "representative_keys": ["Blumensath2012Compressed"],
            },
            {
                "lane": "quasi_linear_compressed_sensing",
                "core_condition": "measurements can be represented as A(x)=F(x)x with F Lipschitz",
                "guarantee_shape": "generalized RIP-like conditions give identifiability and greedy convergence",
                "representative_keys": ["Ehler2013Quasi-linear"],
            },
            {
                "lane": "separable_nonlinear_inverse_problems",
                "core_condition": "parameters are sufficiently distinct relative to operator correlation",
                "guarantee_shape": "sparse recovery can survive deterministic non-RIP operators in special structure",
                "representative_keys": ["Bernstein2019Sparse"],
            },
            {
                "lane": "nonlinear_generative_compressed_sensing",
                "core_condition": "Lipschitz generative prior and sample complexity tied to latent dimension",
                "guarantee_shape": "uniform recovery for nonlinear/quantized/single-index measurements",
                "representative_keys": ["Chen2023A", "Dhar2018Modeling"],
            },
        ],
        "rich_low_dimensional_structures": [
            {
                "model_type": "structured_sparsity_hierarchies",
                "core_idea": "blocks, trees, multilevel support",
                "cs_style_guarantee": "fewer measurements under model-based RIP or restricted amplification",
                "representative_keys": ["Baraniuk2008Model-Based", "Duarte2011Structured", "Eisert2021Hierarchical"],
            },
            {
                "model_type": "manifolds",
                "core_idea": "signals lie on low-dimensional nonlinear families",
                "cs_style_guarantee": "random linear maps can embed manifolds stably with recovery/parameter bounds",
                "representative_keys": ["Eftekhari2013New", "Wakin2010Manifold-Based"],
            },
            {
                "model_type": "temporal_dynamic_models",
                "core_idea": "autoregressive or state-space structure with spatial and temporal sparsity",
                "cs_style_guarantee": "near-optimal sampling can extend to dependent dynamic data",
                "representative_keys": ["Kazemipour2018Compressed"],
            },
            {
                "model_type": "generative_learned_priors",
                "core_idea": "deep/domain-specific generator plus sparse deviations",
                "cs_style_guarantee": "larger signal classes recoverable than plain sparsity when generator assumptions hold",
                "representative_keys": ["Dhar2018Modeling", "Chen2023A"],
            },
        ],
        "equation_pipeline_implication": {
            "useful_for": [
                "equation traces with intrinsic low-dimensional structure",
                "manifold-like parameter families",
                "structured residual or witness lanes",
                "hierarchical route priors",
                "generative proposal models with explicit residual checks",
            ],
            "gate": (
                "Nonlinear CS-style transfer is admissible only after the route "
                "declares its structure class and regularity condition."
            ),
            "reject_if": [
                "nonlinear map lacks Lipschitz or local regularity bound",
                "intrinsic dimension is unknown or unbounded",
                "generator prior hides payload or proof work",
                "operator correlations make parameters indistinct",
                "classifier or reconstruction score replaces receipt",
            ],
        },
        "hutter_implication": {
            "route_state_additions": [
                "cs_structure_class",
                "intrinsic_dimension_estimate",
                "regularity_witness_id",
                "operator_correlation_bound",
                "generator_prior_id",
                "sparse_deviation_lane_id",
                "residual_rehydration_hash",
            ],
            "promotion_boundary": (
                "No nonlinear sparse route promotes without exact residual repair, "
                "decoded hash match, measured bytes, and counted regularity witness."
            ),
        },
        "bibliography_keys": [
            "Ahmed2022Sparse",
            "Baraniuk2008Model-Based",
            "Bernstein2019Sparse",
            "Blumensath2012Compressed",
            "Chen2023A",
            "Dhar2018Modeling",
            "Duarte2011Structured",
            "Eftekhari2013New",
            "Ehler2013Quasi-linear",
            "Eisert2021Hierarchical",
            "Ibanez2019Some",
            "Kazemipour2018Compressed",
            "Kolleck2017On",
            "Lee2016Unified",
            "Qi2013Low-Dimensional",
            "Rani2018A",
            "Romero2015Compressive",
            "Wakin2010Manifold-Based",
            "Wang2023Compressed",
        ],
        "claim_boundary": (
            "This prior says nonlinear compressed sensing can guide route and "
            "equation candidate design under explicit structure and regularity. "
            "It does not prove any Hutter compression result or validate an "
            "unbounded nonlinear manifold route."
        ),
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    return receipt


def write_curriculum(receipt: dict[str, Any]) -> None:
    rows = [
        {
            "task": "classify_nonlinear_cs_lane",
            "input": "candidate nonlinear equation or route",
            "target": "mildly nonlinear, quasi-linear, separable inverse, generative, manifold, or hierarchy lane",
        },
        {
            "task": "require_regular_structure",
            "input": "nonlinear recovery claim",
            "target": "explicit regularity, intrinsic dimension, and correlation bounds",
        },
        {
            "task": "block_unbounded_nonlinear_routes",
            "input": "manifold or generator compression proposal",
            "target": "fail closed unless exact residual and byte receipt exist",
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
        "model_lane_count": len(receipt["nonlinear_model_lanes"]),
        "structure_count": len(receipt["rich_low_dimensional_structures"]),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
