#!/usr/bin/env python3
"""Distill "make illegal states unrepresentable" into DD route-state guards.

The source article's useful extraction is finite-state API discipline: expose
only legal transitions, and use type/state markers to prevent invalid builder
paths. For the bounded route compiler, invalid route combinations should be
unrepresentable when possible, and otherwise fail closed at the boundary.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
OUT = SHIM / "illegal_state_unrepresentable_route_prior_receipt.json"
CURRICULUM_OUT = SHIM / "illegal_state_unrepresentable_route_prior_curriculum.jsonl"

GENERATED_AT = "2026-05-08T00:00:00+00:00"
SOURCE_URL = "https://blog.frankel.ch/illegal-state-unrepresentable/"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


SOURCE_EVIDENCE = {
    "title": "Making illegal state unrepresentable",
    "author": "Nicolas Frankel",
    "published_date": "2026-04-19",
    "source_url": SOURCE_URL,
    "observed_core_claims": [
        "builder_pattern_can_be_read_as_finite_state_machine",
        "illegal_transitions_should_not_be_exposed_to_api_users",
        "static_typing_can_reject_nonexistent_transitions_at_compile_time",
        "dynamic_typing_requires_runtime_validation_or_external_type_checker",
        "naive_state_classes_can_create_combinatorial_growth",
        "phantom_or_generic_state_markers_reduce_growth_for_common_transitions",
        "opaque_constructors_help_hide_invalid_direct_construction",
    ],
}


STATE_DISCIPLINES = [
    {
        "id": "runtime_validation_only",
        "local_meaning": "route object can be built in invalid shape and rejected later",
        "use_when": "dynamic/plugin boundaries where static types are unavailable",
        "risk": "invalid states consume evaluator time and can leak into receipts",
        "verdict": "boundary_fallback_only",
    },
    {
        "id": "state_specific_builder",
        "local_meaning": "each route state exposes only legal next DD edges",
        "use_when": "small finite route machines with few compatibility dimensions",
        "risk": "class/edge explosion as route constraints multiply",
        "verdict": "good_for_small_closed_fsm",
    },
    {
        "id": "phantom_state_marker",
        "local_meaning": "carry compile-time or schema-time route state without serializing payload",
        "use_when": "shared transitions should preserve route family while specific edges are constrained",
        "risk": "marker must not become an uncounted witness channel",
        "verdict": "preferred_for_route_api_shape",
    },
    {
        "id": "opaque_route_constructor",
        "local_meaning": "force route construction through legal transition functions",
        "use_when": "receipts or config matrices should not be hand-assembled into invalid states",
        "risk": "bypass paths must be audited at JSON/plugin boundaries",
        "verdict": "preferred_for_receipt_objects",
    },
]


EQUATIONS = [
    {
        "id": "ISR0_route_fsm",
        "equation": "RouteFSM = (States, LegalEdges, start, terminals)",
        "meaning": "Transform tuning is an explicit finite-state route builder.",
    },
    {
        "id": "ISR1_transition_totality",
        "equation": "edge(s, a) is constructible iff a in LegalEdges(s)",
        "meaning": "An illegal DD edge should not be callable from the current route state.",
    },
    {
        "id": "ISR2_phantom_state",
        "equation": "RouteBuilder[S] carries S at type/schema time and erases S at payload time",
        "meaning": "State markers constrain transitions without becoming hidden compressed data.",
    },
    {
        "id": "ISR3_common_transition",
        "equation": "common_edge: RouteBuilder[S] -> RouteBuilder[S]",
        "meaning": "Shared legal edges preserve state and avoid duplicated boilerplate.",
    },
    {
        "id": "ISR4_specific_transition",
        "equation": "specific_edge: RouteBuilder[S_a] -> RouteBuilder[S_b]",
        "meaning": "Compatibility-changing route choices move to a new explicit state class.",
    },
    {
        "id": "ISR5_boundary_validation",
        "equation": "external_json_route valid iff reconstruct(RouteFSM, json).state != invalid",
        "meaning": "Typed interiors still need fail-closed validation at untyped plugin/file boundaries.",
    },
]


def build_receipt() -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "schema": "illegal_state_unrepresentable_route_prior_v1",
        "generated_at": GENERATED_AT,
        "source_evidence": SOURCE_EVIDENCE,
        "primary_decision": {
            "name": "make_invalid_route_states_unrepresentable",
            "statement": (
                "Represent route construction as a finite-state builder where "
                "only legal DD edges are exposed from each state. Use phantom "
                "or schema-time state markers for common transitions, and keep "
                "runtime validation at external JSON/plugin boundaries."
            ),
        },
        "state_disciplines": STATE_DISCIPLINES,
        "equations": EQUATIONS,
        "candidate_dd_state_extension": [
            "route_state_type_id",
            "legal_edge_set_id",
            "phantom_marker_id",
            "opaque_constructor_status",
            "transition_witness_id",
            "compile_time_rejected_edge_count",
            "runtime_rejected_edge_count",
            "json_boundary_validation_status",
            "state_marker_payload_bytes",
            "invalid_state_nan0_flag",
            "byte_rehydration_hash",
        ],
        "candidate_dd_edges": [
            "open_typed_route_builder",
            "expose_only_legal_edges",
            "apply_common_transition_preserving_state",
            "apply_specific_transition_changing_state",
            "erase_phantom_marker_from_payload",
            "validate_external_route_json",
            "reject_unrepresentable_transition",
            "fail_closed_on_invalid_route_state",
        ],
        "lower_bound": [
            "state_marker_header_bytes",
            "transition_witness_floor",
            "json_boundary_validation_floor",
            "exact_residual_lane_floor",
        ],
        "promotion_rule": [
            "route_builder_exposes_only_legal_transitions",
            "phantom_or_schema_markers_are_not_payload_channels",
            "opaque_constructors_prevent_direct_invalid_receipts",
            "external_json_or_plugin_routes_validate_against_fsm",
            "invalid_states_fail_closed_before_evaluation",
            "decoded_hash_matches_source",
            "measured_total_bytes_beat_incumbent_under_ratio_schema",
        ],
        "failure_rule": [
            "illegal_transition_constructible -> invalid_api_surface",
            "phantom_marker_serialized_as_hidden_payload -> invalid_receipt",
            "state_class_growth_becomes_combinatorial -> refactor_to_marker_matrix",
            "external_route_json_bypasses_validation -> fail_closed",
            "runtime_rejection_after_expensive_eval -> prune_or_move_gate_earlier",
        ],
        "claim_boundary": (
            "This prior constrains route-state representation. It is not a "
            "compression result and does not replace exact decode/hash/byte-count "
            "promotion receipts."
        ),
    }
    preimage = {key: value for key, value in receipt.items() if key != "receipt_hash"}
    receipt["receipt_hash"] = sha256_text(stable_json(preimage))
    return receipt


def curriculum_lines(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    for item in receipt["state_disciplines"]:
        lines.append({"type": "state_discipline", **item})
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
