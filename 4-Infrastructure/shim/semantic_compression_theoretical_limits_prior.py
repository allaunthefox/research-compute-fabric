#!/usr/bin/env python3
"""Semantic compression theoretical-limits prior.

This records the user's pasted Consensus thread as a route/evaluator prior.
It is not a semantic-compression proof and it does not relax byte-exact
promotion.  The practical extraction is a set of limit coordinates that can
shape DD pruning, receipts, and evaluator fields.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


DEFAULT_RECEIPT = Path(
    "4-Infrastructure/shim/semantic_compression_theoretical_limits_prior_receipt.json"
)
DEFAULT_CURRICULUM = Path(
    "4-Infrastructure/shim/semantic_compression_theoretical_limits_prior_curriculum.jsonl"
)


CONSENSUS_SOURCE_SUMMARY = {
    "thread_title": "Semantic Compression Theoretical Limits",
    "prompt": "unified math models of theoretical limits in semantic compression",
    "mode": "Deep",
    "search_count": 21,
    "citation_graph_uses": 1,
    "retrieved_count_reported": 2_777_471,
    "eligible_count_reported": 1_500,
    "included_count_reported": 50,
    "consensus_meter": {
        "question": "Are there unified mathematical models that define the theoretical limits of semantic compression?",
        "n": 9,
        "yes_percent": 100,
    },
    "claim_boundary": (
        "Consensus thread is a source-bundle prior. It supplies theoretical-limit "
        "coordinates and citations, not local compression evidence."
    ),
}


LIMIT_FAMILIES = [
    {
        "id": "semantic_information_bounds",
        "source_examples": [
            "Information-theoretic limits on compression of semantic information",
            "A Mathematical Theory of Semantic Communication",
            "Semantic Information Theory and Applications",
        ],
        "useful_shape": (
            "model a semantic source with conditional independence, Bayesian or "
            "probabilistic structure, and derive lower/upper rate bounds"
        ),
        "dd_use": "bound semantic-sidecar claims and require explicit semantic source model IDs",
        "receipt_fields": [
            "semantic_source_model_id",
            "conditional_independence_receipt",
            "semantic_entropy_bound_bits",
            "side_information_policy",
        ],
        "failure_mode": "semantic bound claimed without an explicit source model or local byte receipt",
    },
    {
        "id": "semantic_rate_distortion",
        "source_examples": [
            "Semantic Rate-Distortion Theory with Applications",
            "A Rate-Distortion Framework for Characterizing Semantic Information",
            "Semantic Compression with Side Information: A Rate-Distortion Perspective",
            "Fundamental Limitation of Semantic Communications: Neural Estimation for Rate-Distortion",
        ],
        "useful_shape": (
            "define a semantic distortion variable, estimate or bound the semantic "
            "rate-distortion function, and compare rate against task outcome"
        ),
        "dd_use": "treat semantic distortion as a diagnostic constraint, never as byte promotion",
        "receipt_fields": [
            "semantic_distortion_metric_id",
            "rate_distortion_estimator_id",
            "side_information_bits",
            "task_success_metric",
        ],
        "failure_mode": "semantic distortion score improves while decoded bytes do not match",
    },
    {
        "id": "rate_distortion_perception_bottleneck",
        "source_examples": [
            "Rate-Distortion-Perception Trade-Off in Information Theory, Generative Models, and Intelligent Communications",
            "Semantic Communication via Rate Distortion Perception Bottleneck",
            "Rate-Distortion-Perception Theory for Semantic Communication",
        ],
        "useful_shape": (
            "perceptual constraints may require extra rate; bottleneck objective "
            "balances task/perception/bit distortion"
        ),
        "dd_use": "charge perceptual or semantic witness bytes explicitly in the route budget",
        "receipt_fields": [
            "perception_constraint_id",
            "bottleneck_lambda",
            "extra_rate_for_perception_bits",
            "diagnostic_quality_score",
        ],
        "failure_mode": "perception quality hides sidecar or witness debt",
    },
    {
        "id": "information_bottleneck_and_ordered_latents",
        "source_examples": [
            "Efficient compression in color naming and its evolution",
            "Information-Ordered Bottlenecks for Adaptive Semantic Compression",
            "Ordered embeddings and intrinsic dimensionalities with information-ordered bottlenecks",
            "Adversarial Information Bottleneck",
        ],
        "useful_shape": (
            "compress observations while preserving task-relevant variables; order "
            "latent coordinates by marginal information or robustness"
        ),
        "dd_use": "rank route features and prune low-information sidecar lanes",
        "receipt_fields": [
            "bottleneck_variable_id",
            "relevance_variable_id",
            "marginal_information_gain",
            "robustness_receipt_id",
        ],
        "failure_mode": "latent relevance score treated as an exact rehydration witness",
    },
    {
        "id": "geometric_algebraic_error_subspaces",
        "source_examples": [
            "Geometry is All You Need: A Unified Taxonomy of Matrix and Tensor Factorization for Compression of Generative Language Models",
            "A General Error-Theoretical Analysis Framework for Constructing Compression Strategies",
            "Bridging Information-Theoretic and Geometric Compression in Language Models",
        ],
        "useful_shape": (
            "parameter/data compression can be expressed through intrinsic dimension, "
            "factorization geometry, or error subspace shape"
        ),
        "dd_use": "use geometry as route-feature coordinates and error-budget priors",
        "receipt_fields": [
            "intrinsic_dimension_estimate",
            "factorization_family_id",
            "error_subspace_shape_id",
            "layerwise_budget_vector",
        ],
        "failure_mode": "geometric compactness confused with source-byte compression",
    },
    {
        "id": "llm_understanding_compression_link",
        "source_examples": [
            "Lossless data compression by large models",
            "Semantic Compression with Large Language Models",
            "Language Modeling Is Compression",
            "Fundamental Limits of Prompt Compression: A Rate-Distortion Framework for Black-Box Language Models",
        ],
        "useful_shape": (
            "large learned models can improve compression by prediction/understanding, "
            "but introduce hallucination, context compression, and compute costs"
        ),
        "dd_use": "allow LLM routes as proposal/predictor engines with strict byte rehydration checks",
        "receipt_fields": [
            "model_id",
            "prompt_compression_ratio",
            "hallucination_guard_id",
            "context_rehydration_hash",
            "compute_budget_ms",
        ],
        "failure_mode": "LLM reconstruction is semantically plausible but byte-invalid",
    },
    {
        "id": "synonymity_and_semantic_arithmetic_coding",
        "source_examples": [
            "Semantic Arithmetic Coding Using Synonymous Mappings",
            "The Semantic Relations in LLMs: An Information-theoretic Compression Approach",
            "Preserving quality of information by using semantic relationships",
        ],
        "useful_shape": (
            "synonym or semantic-equivalence classes can reduce semantic code length "
            "when the equivalence relation is explicit"
        ),
        "dd_use": "map synonym classes to tokenbook proposals and residualize exact lexical choice",
        "receipt_fields": [
            "semantic_equivalence_class_id",
            "synonym_map_hash",
            "lexical_residual_bytes",
            "equivalence_ambiguity_count",
        ],
        "failure_mode": "semantic equivalence discards lexical bytes without residual repair",
    },
    {
        "id": "resource_constrained_semantic_limits",
        "source_examples": [
            "Compression Ratio Allocation for Probabilistic Semantic Communication With RSMA",
            "A Joint Communication and Computation Design for Probabilistic Semantic Communications",
            "Semantic Rate Distortion and Posterior Design: Compute Constraints, Multimodality, and Strategic Inference",
            "Semantic Communication with Side Information: A Rate-Distortion Perspective",
        ],
        "useful_shape": (
            "rate, compute, memory, side information, and multi-user allocation all "
            "change the achievable semantic limit"
        ),
        "dd_use": "make runtime, memory, sidecar, and witness budgets first-class route constraints",
        "receipt_fields": [
            "byte_budget",
            "compute_budget_ms",
            "memory_budget_bytes",
            "side_information_bytes",
            "allocation_policy_id",
        ],
        "failure_mode": "semantic route appears efficient only by ignoring compute or side-information cost",
    },
    {
        "id": "ambiguity_multimodality_and_generalization_gap",
        "source_examples": [
            "Compression Beyond Pixels: Semantic Compression with Multimodal Foundation Models",
            "Can Image Compression Rely on CLIP?",
            "Semantic Rate Distortion and Posterior Design: Compute Constraints, Multimodality, and Strategic Inference",
            "On the Fundamental Limits of LLMs at Scale",
        ],
        "useful_shape": (
            "ambiguity, polysemy, multimodality, hallucination, and retrieval fragility "
            "limit transfer from theoretical semantic rates to real systems"
        ),
        "dd_use": "force ambiguity packets and multimodal claim boundaries before promotion",
        "receipt_fields": [
            "ambiguity_class_id",
            "polysemy_count",
            "modality_set",
            "retrieval_fragility_score",
            "generalization_scope",
        ],
        "failure_mode": "semantic limit validated on narrow data is applied to a broader corpus slice",
    },
]


THEORETICAL_RECEIPT_RULES = {
    "ratio_schema": "source_bytes / compressed_total_bytes",
    "semantic_limit_status": "diagnostic unless byte_rehydration_hash matches",
    "promotion_rule": (
        "promote iff semantic-limit machinery only proposes, bounds, or budgets "
        "routes; exact residual lanes restore source bytes; decoded hash matches; "
        "and measured total bytes beat incumbent under explicit ratio_schema"
    ),
    "failure_rule": (
        "semantic entropy, rate-distortion, bottleneck, perceptual quality, LLM "
        "understanding, or synonymity without byte-exact restoration is diagnostic only"
    ),
}


def stable_hash(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_receipt() -> dict[str, Any]:
    source_hash = stable_hash(CONSENSUS_SOURCE_SUMMARY)
    receipt: dict[str, Any] = {
        "schema": "semantic_compression_theoretical_limits_prior_v1",
        "generated_at": "2026-05-08T00:00:00+00:00",
        "source_summary": CONSENSUS_SOURCE_SUMMARY,
        "source_summary_hash": source_hash,
        "claim_boundary": (
            "Theoretical semantic-compression models define proposal and budget "
            "surfaces. They do not establish local byte compression unless the "
            "route has a local encode/decode/hash/byte-count receipt."
        ),
        "limit_families": LIMIT_FAMILIES,
        "theoretical_receipt_rules": THEORETICAL_RECEIPT_RULES,
        "dd_state_extension": [
            "semantic_source_model_id",
            "semantic_entropy_bound_bits",
            "semantic_distortion_metric_id",
            "rate_distortion_estimator_id",
            "bottleneck_variable_id",
            "marginal_information_gain",
            "intrinsic_dimension_estimate",
            "error_subspace_shape_id",
            "semantic_equivalence_class_id",
            "lexical_residual_bytes",
            "side_information_bytes",
            "compute_budget_ms",
            "ambiguity_class_id",
            "byte_rehydration_hash",
        ],
        "candidate_dd_edges": [
            "choose_semantic_source_model",
            "estimate_semantic_entropy_bound",
            "estimate_semantic_rate_distortion",
            "apply_information_bottleneck_rank",
            "emit_geometric_error_subspace",
            "propose_llm_predictor_route",
            "emit_synonym_class_tokenbook",
            "charge_side_information_budget",
            "record_ambiguity_packet",
            "emit_exact_residual_lane",
            "verify_byte_rehydration_hash",
            "reject_semantic_only_promotion",
        ],
    }
    receipt["receipt_hash"] = stable_hash(receipt)
    return receipt


def curriculum_records(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    system = (
        "You are a semantic-compression limit router. Treat theory as a "
        "budget/proposal surface and byte-exact receipts as promotion authority."
    )
    records: list[dict[str, Any]] = []
    for family in receipt["limit_families"]:
        records.append(
            {
                "messages": [
                    {"role": "system", "content": system},
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "task": "route_semantic_compression_limit_family",
                                "family_id": family["id"],
                                "useful_shape": family["useful_shape"],
                                "dd_use": family["dd_use"],
                            },
                            ensure_ascii=False,
                        ),
                    },
                    {
                        "role": "assistant",
                        "content": json.dumps(
                            {
                                "selected": True,
                                "receipt_fields": family["receipt_fields"],
                                "failure_mode": family["failure_mode"],
                                "claim_boundary": "semantic-limit-prior-only",
                                "promotion_authority": "local encode/decode/hash/byte-count receipt",
                            },
                            ensure_ascii=False,
                        ),
                    },
                ]
            }
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--curriculum", type=Path, default=DEFAULT_CURRICULUM)
    args = parser.parse_args()

    receipt = build_receipt()
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with args.curriculum.open("w", encoding="utf-8") as handle:
        for record in curriculum_records(receipt):
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
