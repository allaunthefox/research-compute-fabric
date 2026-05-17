#!/usr/bin/env python3
"""Distill the T16 transit-search pipeline into an equation-mining prior.

The source paper is an astronomy result, not an equation-discovery result.  This
runner records the transferable method shape: large uniform preprocessing,
cheap candidate extraction, diagnostic feature expansion, regime-specific
classifiers, automated vetting, and expensive confirmation only for survivors.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
RECEIPT = SHIM / "t16_candidate_pipeline_equation_prior_receipt.json"
CURRICULUM = SHIM / "t16_candidate_pipeline_equation_prior_curriculum.jsonl"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_receipt() -> dict[str, Any]:
    bridge = {
        "source": {
            "arxiv": "2604.18579",
            "title": (
                "The T16 Planet Hunt: 10,000 New Planet Candidates from TESS "
                "Cycle 1 and the Confirmation of a Hot Jupiter Around TIC 183374187"
            ),
            "doi": "10.48550/arXiv.2604.18579",
            "related_doi": "10.3847/1538-4365/ae5b6c",
            "source_claim": "large-scale machine-learning-assisted transit search",
        },
        "observed_source_shape": {
            "input_count": 83_717_159,
            "target_count": 54_401_549,
            "candidate_count": 11_554,
            "new_candidate_count": 10_091,
            "single_transit_count": 411,
            "validated_example": "TIC 183374187 radial-velocity confirmation",
        },
        "transferable_pipeline": [
            "uniform_detrending_and_systematics_correction",
            "cheap_linear_search_for_candidate_events",
            "fold_candidate_over_period_grid",
            "extract_harmonic_alias_features",
            "train_regime_specific_random_forest_classifiers",
            "drop_low_importance_or_noisy_features",
            "apply_probability_thresholds",
            "graph_vet_local_contamination",
            "prune_overpopulated_systematic_bins",
            "run_fast_physical_model_fit",
            "run_image_or_context_residual_check",
            "reserve_expensive_confirmation_for_survivors",
            "record_injection_recovery_as_future_completeness_gate",
        ],
        "equation_adaptation": {
            "equation_trace": (
                "sequence of symbolic, numeric, unit, residual, and proof-state "
                "observations extracted from an equation candidate"
            ),
            "detrending": (
                "remove notation-specific, source-specific, and formatting-specific "
                "systematics before scoring mathematical signal"
            ),
            "candidate_event": (
                "localized invariant, residual collapse, dimensional consistency, "
                "operator match, or compression-gain hint"
            ),
            "period_grid_analogue": (
                "probe aliases such as scale, reciprocal, dual, Fourier, log, "
                "normalization, and dimensional rescaling variants"
            ),
            "harmonic_features": [
                "primary_score",
                "half_scale_score",
                "double_scale_score",
                "triple_scale_score",
                "inverse_candidate_score",
                "delta_loss",
                "residual_ratio",
                "symbolic_depth",
                "unit_consistency",
                "domain_context",
            ],
            "regime_split": [
                "small_closed_form_equations",
                "high_dimensional_symbolic_systems",
                "noisy_empirical_fits",
                "compression_route_equations",
                "physics_or_hardware_control_equations",
            ],
            "confirmation": [
                "Lean_or_symbolic_check",
                "numeric_reproduction",
                "unit_and_dimension_check",
                "held_out_data_check",
                "exact_decode_hash_for_Hutter_use",
            ],
        },
        "equation_prior": {
            "score": (
                "priority = cheap_signal_score + alias_consistency + context_support "
                "- contamination_risk - systematic_bin_penalty - confirmation_cost"
            ),
            "promote_if": [
                "candidate_survives_regime_classifier",
                "local_contamination_or_duplicate_source_is_resolved",
                "systematic_alias_bin_is_not_overpopulated",
                "expensive_validator_confirms_the_claim",
                "Hutter_use_has_exact_decode_hash_and_measured_bytes",
            ],
            "fail_closed_if": [
                "source_context_is_unverified",
                "candidate_only_exists_after_notation_detrending",
                "alias_family_is_overpopulated_without_independent_support",
                "classifier_probability_replaces_proof",
                "manual_or_expensive_validator_rejects_candidate",
            ],
        },
        "claim_boundary": (
            "This receipt extracts a candidate-search method from an astronomy "
            "pipeline. It is not evidence that transit-search features prove "
            "equations, compression gains, or physical laws."
        ),
    }
    bridge["receipt_hash"] = sha256_text(stable_json(bridge))
    return bridge


def write_curriculum(receipt: dict[str, Any]) -> None:
    rows = [
        {
            "task": "map_transit_pipeline_to_equation_pipeline",
            "input": "uniformly detrended light curves plus transit candidate vetting",
            "target": "uniform equation traces plus proof/receipt candidate vetting",
        },
        {
            "task": "separate_candidate_score_from_proof",
            "input": "random forest probability and BLS/CETRA features",
            "target": "equation priority only, never a proof substitute",
        },
        {
            "task": "define_expensive_confirmation_boundary",
            "input": "radial velocity and MCMC follow-up",
            "target": "Lean/numeric/unit/Hutter exact-receipt validation",
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
        "candidate_count": receipt["observed_source_shape"]["candidate_count"],
        "transferable_stage_count": len(receipt["transferable_pipeline"]),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
