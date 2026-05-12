#!/usr/bin/env python3
"""Build a Tammes-focused adversarial route prior for Hutter work.

The prior combines three shapes:

* Tammes / spherical-code spacing: keep route candidates diverse by maximizing
  nearest-neighbor distance on a route feature manifold.
* Multimetal nanocrystal composition focusing: use staged scaffold decisions
  that collapse a large theoretical frontier into a smaller lawful frontier.
* Adversarial Conway-style tournament stress: hash rule/glyph candidates into
  hostile local-interaction tests before spending promotion evaluator budget.

This is a route-selection and stress-testing prior. It is not a compression
result and does not promote any Hutter route without exact byte receipts.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
OUT = SHIM / "tammes_focused_adversarial_hutter_prior_receipt.json"
CURRICULUM_OUT = SHIM / "tammes_focused_adversarial_hutter_prior_curriculum.jsonl"

GENERATED_AT = "2026-05-08T00:00:00+00:00"
HUTTER_ENWIK9_TARGET_BYTES = 109_685_197

SOURCE_RECEIPTS = {
    "hutter_equation_metastate_transfold": SHIM
    / "hutter_equation_metastate_transfold_receipt.json",
    "multimetal_nanocrystal_composition_focusing_prior": SHIM
    / "multimetal_nanocrystal_composition_focusing_prior_receipt.json",
    "projectable_geometry_topology_model": SHIM
    / "projectable_geometry_topology_model_receipt.json",
}


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def receipt_hash(path: Path, data: dict[str, Any]) -> str:
    for key in (
        "receipt_hash",
        "stable_topology_model_hash_sha256",
        "stable_shell_dd_hash_sha256",
    ):
        value = data.get(key)
        if isinstance(value, str):
            return value
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_receipt_records(receipts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        name: {
            "path": rel(SOURCE_RECEIPTS[name]),
            "schema": receipt.get("schema", "unknown"),
            "hash": receipt_hash(SOURCE_RECEIPTS[name], receipt),
        }
        for name, receipt in receipts.items()
    }


def source_evidence() -> dict[str, Any]:
    return {
        "tammes_problem": {
            "shape": "place N points on a sphere/manifold to maximize the minimum pairwise distance",
            "route_use": "diversify route candidates and avoid wasting evaluator time on near-duplicates",
            "reference_url": "https://mathworld.wolfram.com/SphericalCode.html",
            "claim_status": "standard_geometry_prior",
        },
        "multimetal_nanocrystal": {
            "title": "Researchers combine five metals to build a better nanocrystal",
            "source": "Phys.org / Stanford University",
            "published_date": "2026-05-07",
            "url": "https://phys.org/news/2026-05-combine-metals-nanocrystal.html",
            "primary_paper_doi": "10.1126/science.aea8044",
            "route_use": "composition focusing / staged decision tree for lawful frontier collapse",
            "claim_status": "verified_article_shape_not_byte_evidence",
        },
        "adversarial_conway_prompt": {
            "title": "Adversarial Conway: Example Matches",
            "source": "Reddit r/gameoflife",
            "url": "https://www.reddit.com/r/gameoflife/comments/1t71s3m/adversarial_conway_example_matches/",
            "observed_shape": "hashed contestant glyphs enter a tournament-like adversarial cellular-automaton arena",
            "route_use": "stress route rules under hostile local interactions before promotion",
            "claim_status": "community_prompt_not_peer_reviewed_source",
        },
    }


def route_embedding() -> dict[str, Any]:
    return {
        "route_point": [
            "transform_family_id",
            "tokenbook_policy_id",
            "residual_policy_id",
            "witness_budget_class",
            "decoder_cost_class",
            "locality_profile_id",
            "byte_gain_floor_class",
            "failure_signature_id",
            "adversarial_fragility_class",
            "composition_focus_score",
        ],
        "metric": (
            "d_route(i,j) = weighted distance over route_point fields, with "
            "hard separation for incompatible residual or decoder policies"
        ),
        "normalization": (
            "candidate coordinates are proposal features only; no coordinate "
            "is promotion evidence until exact bytes are measured"
        ),
    }


def equations() -> list[dict[str, str]]:
    return [
        {
            "id": "TFA0_route_embedding",
            "equation": "x_i = embed(route_i) in M_Hutter",
            "meaning": "Represent each candidate route as a point on the Hutter feature manifold.",
        },
        {
            "id": "TFA1_tammes_diversity",
            "equation": "D_Tammes(R) = min_{i != j} d_route(x_i, x_j)",
            "meaning": "Prefer route batches whose nearest candidates are still meaningfully separated.",
        },
        {
            "id": "TFA2_composition_focus",
            "equation": "F_focus = 1 - focused_frontier_size / theoretical_frontier_size",
            "meaning": "Reward staged constraints that collapse the legal frontier without losing decode reachability.",
        },
        {
            "id": "TFA3_decision_tree_attachment",
            "equation": "node_{t+1} = attach(argmin_l cost(l | scaffold_t), node_t)",
            "meaning": "Use nanocrystal-style staged attachment as a deterministic route decision tree.",
        },
        {
            "id": "TFA4_adversarial_fragility",
            "equation": "A_adv(route) = failed_stress_cases / total_stress_cases",
            "meaning": "Measure how often a route rule breaks under hostile local rewrite / automaton tests.",
        },
        {
            "id": "TFA5_priority_score",
            "equation": (
                "Priority = gain_floor + alpha*D_Tammes + beta*F_focus "
                "- residual_floor - witness_floor - decoder_floor - gamma*A_adv"
            ),
            "meaning": "Rank what to evaluate next; this score never promotes by itself.",
        },
        {
            "id": "TFA6_promotion",
            "equation": "promote iff decode(route_artifact) == source and bytes_total < incumbent",
            "meaning": "Promotion authority remains exact reconstruction and counted byte improvement.",
        },
    ]


def dd_state_extension() -> list[str]:
    return [
        "tammes_route_lattice_id",
        "route_feature_vector_id",
        "route_manifold_chart_id",
        "nearest_neighbor_distance_floor",
        "tammes_diversity_score",
        "composition_scaffold_id",
        "decision_tree_node_id",
        "attachment_order_receipt_id",
        "focused_frontier_size",
        "theoretical_frontier_size",
        "composition_focus_score",
        "adversarial_glyph_hash",
        "adversarial_arena_id",
        "stress_case_count",
        "failed_stress_case_count",
        "adversarial_fragility_score",
        "route_priority_score",
        "exact_residual_lane_id",
        "byte_rehydration_hash",
    ]


def dd_edges() -> list[str]:
    return [
        "embed_route_on_hutter_manifold",
        "compute_route_pair_distance",
        "maximize_nearest_neighbor_route_distance",
        "open_composition_scaffold_decision_tree",
        "attach_route_lane_by_focus_cost",
        "measure_frontier_collapse",
        "hash_route_glyph_for_adversarial_arena",
        "run_adversarial_conway_stress_cases",
        "penalize_adversarial_fragility",
        "rank_route_priority",
        "reject_near_duplicate_route",
        "emit_exact_residual_lane",
        "close_with_byte_rehydration_hash",
    ]


def promotion_rule() -> list[str]:
    return [
        "route_batch_has_tammes_separation_above_floor",
        "composition_scaffold_decision_tree_is_deterministic_or_receipted",
        "frontier_collapse_preserves_decode_reachability",
        "adversarial_stress_failures_are_zero_or_fail_closed_before_expensive_promotion",
        "all residual/witness/decoder/container costs are counted",
        "decoded_hash_matches_source_hash",
        "measured_total_bytes_beat_incumbent_under_explicit_ratio_schema",
    ]


def failure_rule() -> list[str]:
    return [
        "tammes_route_points_collapse_to_near_duplicates -> prune_batch",
        "decision_tree_attachment_ambiguous_without_tie_break -> fail_closed",
        "focused_frontier_loses_decode_reachability -> fail_closed",
        "adversarial_arena_generates_unbounded_rule_search -> NaN0",
        "stress_survivorship_used_as_byte_evidence -> diagnostic_only",
        "witness_or_stress_metadata_exceeds_byte_gain -> prune",
    ]


def current_hutter_context(receipts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    metastate = receipts["hutter_equation_metastate_transfold"]["current_best_metastate"]
    return {
        "current_route": metastate["transform_route"],
        "source_corpus_id": metastate["source_corpus_id"],
        "source_bytes": metastate["source_bytes"],
        "compressed_total_bytes": metastate["compressed_total_bytes"],
        "baseline_bytes": metastate["baseline_bytes"],
        "margin_vs_baseline_bytes": metastate["margin_vs_baseline_bytes"],
        "projected_enwik9_total_bytes": metastate["projected_enwik9_total_bytes"],
        "projected_gap_to_hard_target_bytes": metastate[
            "projected_gap_to_hard_target_bytes"
        ],
        "hard_target_bytes_enwik9": HUTTER_ENWIK9_TARGET_BYTES,
        "route_use": (
            "Use this prior to choose diverse, focused, adversarially stable "
            "payload-transform trials before adding more witness bytes."
        ),
    }


def build_receipt() -> dict[str, Any]:
    receipts = {name: load_json(path) for name, path in SOURCE_RECEIPTS.items()}
    receipt: dict[str, Any] = {
        "schema": "tammes_focused_adversarial_hutter_prior_v1",
        "generated_at": GENERATED_AT,
        "runner": rel(Path(__file__)),
        "source_evidence": source_evidence(),
        "source_receipts": source_receipt_records(receipts),
        "primary_decision": {
            "name": "tammes_focused_adversarial_route_lattice",
            "statement": (
                "Adapt Tammes spacing to the Hutter feature manifold, use "
                "nanocrystal-style staged decision trees to collapse route "
                "frontiers, and add adversarial Conway-style local-interaction "
                "stress before exact byte evaluation."
            ),
        },
        "route_embedding": route_embedding(),
        "equations": equations(),
        "candidate_dd_state_extension": dd_state_extension(),
        "candidate_dd_edges": dd_edges(),
        "promotion_rule": promotion_rule(),
        "failure_rule": failure_rule(),
        "current_hutter_context": current_hutter_context(receipts),
        "claim_boundary": (
            "This is a route-prior and evaluator-scheduling artifact. Tammes "
            "spacing, nanocrystal composition focusing, and adversarial Conway "
            "stress do not prove compression. Hutter promotion still requires "
            "exact decode, matching hashes, measured total bytes, explicit ratio "
            "schema, and counted residual/witness/decoder/container costs."
        ),
    }
    preimage = {key: value for key, value in receipt.items() if key != "receipt_hash"}
    receipt["receipt_hash"] = sha256_text(stable_json(preimage))
    return receipt


def curriculum_lines(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    for equation in receipt["equations"]:
        lines.append({"type": "equation", **equation})
    for edge in receipt["candidate_dd_edges"]:
        lines.append({"type": "dd_edge", "edge": edge})
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
    print(
        json.dumps(
            {
                "receipt": rel(OUT),
                "curriculum": rel(CURRICULUM_OUT),
                "receipt_hash": receipt["receipt_hash"],
                "equation_count": len(receipt["equations"]),
                "dd_edge_count": len(receipt["candidate_dd_edges"]),
                "current_route": receipt["current_hutter_context"]["current_route"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
