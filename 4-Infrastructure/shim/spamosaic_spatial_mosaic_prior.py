#!/usr/bin/env python3
"""Distill SpaMosaic into a bounded route prior for fragmented observations.

SpaMosaic integrates partially overlapping spatial multi-omics datasets into a
shared latent atlas using contrastive learning and spatial graph structure. For
the compressor, the useful shape is not biological atlas construction itself:
it is mosaic integration of incomplete route observations, batch correction,
spatial-neighbor constraints, and missing-lane imputation that remains only a
proposal until exact residual repair closes the byte stream.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
OUT = SHIM / "spamosaic_spatial_mosaic_prior_receipt.json"
CURRICULUM_OUT = SHIM / "spamosaic_spatial_mosaic_prior_curriculum.jsonl"

GENERATED_AT = "2026-05-08T00:00:00+00:00"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


SOURCE_EVIDENCE = {
    "news": {
        "title": "AI tool unifies fragmented cell maps into spatial atlases across tissues",
        "source": "Phys.org / Northwestern University",
        "published_date": "2026-05-07",
        "url": "https://phys.org/news/2026-05-ai-tool-fragmented-cell-spatial.html",
    },
    "primary_paper": {
        "title": "Mosaic integration of spatial multi-omics with SpaMosaic",
        "authors": "Xuhua Yan et al.",
        "journal": "Nature Genetics",
        "published_date": "2026-04-24",
        "doi": "10.1038/s41588-026-02573-3",
        "url": "https://www.nature.com/articles/s41588-026-02573-3",
    },
    "observed_core_claims": [
        "mosaic_datasets_measure_only_partially_overlapping_modalities",
        "contrastive_learning_learns_cross_dataset_similarities_and_differences",
        "graph_neural_networks_use_spatial_neighbor_relationships",
        "shared_latent_space_is_modality_agnostic_and_batch_corrected",
        "method_identifies_coherent_spatial_domains",
        "method_imputes_missing_molecular_layers",
        "imputation_reliability_requires_further_testing",
        "framework_scales_to_large_spatial_sections",
    ],
}


MOSAIC_ROUTE_OPERATORS = [
    {
        "id": "partial_modality_observation",
        "source_shape": "each tissue slice measures only some omics layers",
        "route_mapping": "each corpus slice or route probe observes only some transform features",
        "claim_boundary": "observation is incomplete until exact residual closes bytes",
    },
    {
        "id": "contrastive_alignment",
        "source_shape": "learn similarities and differences across fragmented datasets",
        "route_mapping": "align route observations across slices without collapsing distinct byte states",
        "claim_boundary": "alignment is a proposal feature, not proof of equivalence",
    },
    {
        "id": "spatial_graph_constraint",
        "source_shape": "neighboring cells constrain spatial domain inference",
        "route_mapping": "neighbor spans constrain route-family continuity and sidecar locality",
        "claim_boundary": "graph smoothness cannot override decode hash",
    },
    {
        "id": "batch_effect_correction",
        "source_shape": "remove technical processing differences while preserving biology",
        "route_mapping": "normalize route-observation artifacts while preserving exact byte authority",
        "claim_boundary": "correction must emit residual for every byte-affecting change",
    },
    {
        "id": "missing_lane_imputation",
        "source_shape": "predict unmeasured molecular layers",
        "route_mapping": "predict missing tokenbook / sidecar / witness lanes before exact repair",
        "claim_boundary": "imputed lane is sketch-only unless residual repair restores bytes",
    },
]


EQUATIONS = [
    {
        "id": "SM0_mosaic_observation",
        "equation": "O_s = (slice_s, observed_lanes_s, missing_lanes_s, spatial_graph_s)",
        "meaning": "Each route observation is a partial lane measurement over a local graph.",
    },
    {
        "id": "SM1_shared_latent_chart",
        "equation": "z_s = Align_contrastive(O_s, batch_id_s, graph_s)",
        "meaning": "Map fragmented observations into a shared chart while retaining batch provenance.",
    },
    {
        "id": "SM2_batch_corrected_not_byte_corrected",
        "equation": "batch_correct(z_s) != byte_correct(source_s)",
        "meaning": "Removing observation artifacts is not the same as proving byte rehydration.",
    },
    {
        "id": "SM3_missing_lane_prediction",
        "equation": "imputed_lane_l = Predict(z_s, graph_s, modality_l)",
        "meaning": "Missing route lanes can be proposed from nearby observations.",
    },
    {
        "id": "SM4_exact_closure",
        "equation": "promote iff hash(decode(imputed_lanes + exact_residuals)) == source_hash",
        "meaning": "Imputation closes only through exact residual repair and hash.",
    },
    {
        "id": "SM5_lower_bound",
        "equation": "LB = mosaic_header + graph_receipt + batch_receipt + imputation_receipt + residual_floor",
        "meaning": "All atlas/witness costs must be charged before route promotion.",
    },
]


def build_receipt() -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "schema": "spamosaic_spatial_mosaic_prior_v1",
        "generated_at": GENERATED_AT,
        "source_evidence": SOURCE_EVIDENCE,
        "primary_decision": {
            "name": "use_mosaic_integration_as_fragmented_route_observation_prior",
            "statement": (
                "Use SpaMosaic's shape as a prior for aligning incomplete route "
                "observations across slices, correcting observation artifacts, "
                "and proposing missing lanes. Treat every imputed lane as sketch "
                "data until exact residual repair and rehydration hash close."
            ),
        },
        "mosaic_route_operators": MOSAIC_ROUTE_OPERATORS,
        "equations": EQUATIONS,
        "candidate_dd_state_extension": [
            "mosaic_observation_id",
            "observed_lane_set",
            "missing_lane_set",
            "spatial_neighbor_graph_id",
            "contrastive_alignment_id",
            "batch_id",
            "batch_correction_receipt_id",
            "shared_latent_chart_id",
            "spatial_domain_id",
            "imputed_lane_id",
            "imputation_confidence",
            "imputation_reliability_status",
            "exact_residual_lane_id",
            "mosaic_lower_bound_bytes",
            "byte_rehydration_hash",
        ],
        "candidate_dd_edges": [
            "open_mosaic_route_observation",
            "record_observed_and_missing_lanes",
            "build_spatial_neighbor_graph",
            "align_observations_contrastively",
            "correct_batch_effect_with_receipt",
            "identify_route_spatial_domain",
            "predict_missing_route_lane",
            "emit_exact_residual_for_imputed_lane",
            "verify_mosaic_rehydration_hash",
            "reject_imputation_without_exact_repair",
        ],
        "lower_bound": [
            "mosaic_header_bytes",
            "spatial_graph_receipt_floor",
            "contrastive_alignment_receipt_floor",
            "batch_correction_receipt_floor",
            "imputed_lane_receipt_floor",
            "exact_residual_lane_floor",
        ],
        "promotion_rule": [
            "mosaic_layer_only_aligns_or_proposes_route_lanes",
            "batch_correction_is_receipted_and_byte_preserving_or_residualized",
            "spatial_graph_smoothness_does_not_override_byte_hash",
            "missing_lane_imputation_carries_exact_residual_repair",
            "imputation_reliability_status_is_recorded",
            "decoded_hash_matches_source",
            "measured_total_bytes_beat_incumbent_under_ratio_schema",
        ],
        "failure_rule": [
            "imputed_lane_without_exact_residual -> not_promoted",
            "batch_correction_changes_bytes_without_residual -> invalid_receipt",
            "spatial_domain_match_without_byte_hash -> diagnostic_only",
            "mosaic_header_larger_than_byte_gain -> prune",
            "unbounded_neighbor_graph_or_alignment -> NaN0",
        ],
        "claim_boundary": (
            "This prior imports SpaMosaic's fragmented-observation integration "
            "shape. It is not evidence that biological atlas methods compress "
            "text bytes, and it does not promote routes without exact decode, "
            "hash, byte count, and explicit ratio schema."
        ),
    }
    preimage = {key: value for key, value in receipt.items() if key != "receipt_hash"}
    receipt["receipt_hash"] = sha256_text(stable_json(preimage))
    return receipt


def curriculum_lines(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    for item in receipt["mosaic_route_operators"]:
        lines.append({"type": "mosaic_route_operator", **item})
    for item in receipt["equations"]:
        lines.append({"type": "equation", **item})
    for rule in receipt["promotion_rule"]:
        lines.append({"type": "promotion_rule", "rule": rule})
    for rule in receipt["failure_rule"]:
        lines.append({"type": "failure_rule", "rule": rule})
    return lines


def main() -> None:
    receipt = build_receipt()
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = curriculum_lines(receipt)
    CURRICULUM_OUT.write_text(
        "".join(json.dumps(line, sort_keys=True) + "\n" for line in lines),
        encoding="utf-8",
    )
    print(json.dumps({
        "receipt": rel(OUT),
        "curriculum": rel(CURRICULUM_OUT),
        "receipt_hash": receipt["receipt_hash"],
        "curriculum_records": len(lines),
        "decision": receipt["primary_decision"]["name"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
