#!/usr/bin/env python3
"""Distill multimetallic nanocrystal composition focusing into a route prior.

The source result reports that adding more metals to Ru-based nanocrystal
synthesis can focus, rather than explode, the product distribution: a Cu/Ru
heterodimer scaffold and competitive reactivity guide later Co/Ni/Fe deposition
into a uniform five-metal structure. For the compressor, the useful shape is a
frontier-control prior: extra route components may reduce candidate entropy when
they are staged through a scaffold, incompatibility boundary, and ordered
attachment law. It is not compression evidence by itself.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
OUT = SHIM / "multimetal_nanocrystal_composition_focusing_prior_receipt.json"
CURRICULUM_OUT = SHIM / "multimetal_nanocrystal_composition_focusing_prior_curriculum.jsonl"

GENERATED_AT = "2026-05-08T00:00:00+00:00"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


SOURCE_EVIDENCE = {
    "news": {
        "title": "Researchers combine five metals to build a better nanocrystal",
        "source": "Phys.org / Stanford University",
        "published_date": "2026-05-07",
        "url": "https://phys.org/news/2026-05-combine-metals-nanocrystal.html",
    },
    "primary_paper": {
        "title": "Competitive reactivity drives size- and composition-focusing in multimetallic nanocrystals",
        "authors": "Jeesoo Yoon et al.",
        "journal": "Science",
        "published_date": "2026-05-07",
        "doi": "10.1126/science.aea8044",
        "url": "https://www.science.org/doi/10.1126/science.aea8044",
    },
    "observed_core_claims": [
        "five_metal_nanocrystals_can_be_more_uniform_than_two_or_three_metal_attempts",
        "31_theoretical_product_combinations_collapse_to_essentially_one_product",
        "copper_deposits_first_on_ruthenium_seed_but_does_not_mix_into_ruthenium",
        "copper_ruthenium_heterodimer_scaffold_guides_later_deposition",
        "cobalt_and_nickel_attach_to_affinity_regions_before_iron_envelopes_outer_layer",
        "competitive_reactivity_drives_size_and_composition_focusing",
        "five_metal_material_outperforms_standard_ruthenium_catalyst_for_ammonia_decomposition",
        "industrial_translation_remains_pending_outside_lab_conditions",
    ],
}


COMPOSITION_FOCUSING_OPERATORS = [
    {
        "id": "seed_route_core",
        "source_shape": "ruthenium seed provides a stable starting particle",
        "route_mapping": "start route search from a byte-exact incumbent or stable core transform",
        "claim_boundary": "seed stability is not a byte win without measured receipt",
    },
    {
        "id": "immiscible_scaffold_boundary",
        "source_shape": "copper attaches to ruthenium but remains a distinct domain",
        "route_mapping": "use incompatibility boundaries to prevent route lanes from merging too early",
        "claim_boundary": "boundary metadata must be bounded and cannot hide payload",
    },
    {
        "id": "competitive_reactivity_ordering",
        "source_shape": "metals reduce and attach in an order set by relative reactivity and affinity",
        "route_mapping": "order transform additions by observed compatibility and residual cost",
        "claim_boundary": "ordering is a pruning prior, not promotion evidence",
    },
    {
        "id": "composition_focusing",
        "source_shape": "more elements collapse the product distribution into a uniform particle",
        "route_mapping": "extra constraints can collapse a route frontier when each constraint is receipted",
        "claim_boundary": "frontier collapse must preserve exact decode reachability",
    },
    {
        "id": "outer_stability_shell",
        "source_shape": "iron-rich outer layer helps resist high-temperature sintering",
        "route_mapping": "add a final stability witness that guards repeated decode / perturbation churn",
        "claim_boundary": "stability witness is paid metadata and must fit byte margin",
    },
]


EQUATIONS = [
    {
        "id": "MCF0_route_seed",
        "equation": "R_0 = seed_route(source_slice, incumbent_receipt)",
        "meaning": "Begin from a verified route core rather than an unconstrained combinatorial soup.",
    },
    {
        "id": "MCF1_scaffold_boundary",
        "equation": "S = hetero_boundary(core_lane, anchor_lane) where merge(core, anchor) is forbidden",
        "meaning": "A deliberate non-merge boundary can become the scaffold for later legal attachments.",
    },
    {
        "id": "MCF2_ordered_attachment",
        "equation": "lane_{t+1} = attach(argmin_l reactivity_cost(l | S_t), S_t)",
        "meaning": "Attach the next route lane according to compatibility and residual-cost ordering.",
    },
    {
        "id": "MCF3_frontier_focusing",
        "equation": "|Frontier_{t+1}| < |Frontier_t| when every added constraint preserves decode reachability",
        "meaning": "Additional route components are useful only if they shrink legal states without losing exact decode paths.",
    },
    {
        "id": "MCF4_shell_stability",
        "equation": "stable_route iff churn_count <= churn_budget and n_minus_1_failures close or repair exactly",
        "meaning": "A final stability layer is a perturbation/churn guard, not hidden compressed data.",
    },
    {
        "id": "MCF5_promotion",
        "equation": "promote iff hash(decode(R_focused + exact_residuals)) == source_hash and bytes < incumbent",
        "meaning": "Composition focusing is admissible only after exact residual repair and measured byte win.",
    },
]


def build_receipt() -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "schema": "multimetal_nanocrystal_composition_focusing_prior_v1",
        "generated_at": GENERATED_AT,
        "source_evidence": SOURCE_EVIDENCE,
        "primary_decision": {
            "name": "use_composition_focusing_as_route_frontier_collapse_prior",
            "statement": (
                "Use multimetallic nanocrystal composition focusing as a prior "
                "for staged route construction: start from a stable seed, add "
                "an immiscible scaffold boundary, order lane additions by "
                "compatibility, and promote only if the focused frontier still "
                "decodes byte-exactly with all witness costs counted."
            ),
        },
        "composition_focusing_operators": COMPOSITION_FOCUSING_OPERATORS,
        "equations": EQUATIONS,
        "candidate_dd_state_extension": [
            "route_seed_id",
            "seed_incumbent_receipt_id",
            "component_lane_count",
            "candidate_component_set",
            "scaffold_anchor_lane_id",
            "immiscibility_boundary_id",
            "reactivity_order_id",
            "affinity_region_id",
            "attachment_step_index",
            "composition_focus_score",
            "focused_frontier_size",
            "theoretical_frontier_size",
            "outer_stability_shell_id",
            "decode_churn_count",
            "n_minus_1_stability_status",
            "exact_residual_lane_id",
            "byte_rehydration_hash",
        ],
        "candidate_dd_edges": [
            "open_seed_route_core",
            "emit_immiscible_scaffold_boundary",
            "rank_candidate_lanes_by_reactivity_cost",
            "attach_lane_to_affinity_region",
            "reject_premature_lane_merge",
            "measure_frontier_focusing",
            "emit_outer_stability_shell",
            "stress_decode_churn",
            "run_n_minus_1_route_stability_check",
            "close_focused_route_with_exact_residual",
        ],
        "lower_bound": [
            "seed_receipt_bytes",
            "scaffold_boundary_header_floor",
            "reactivity_order_receipt_floor",
            "attachment_sequence_floor",
            "stability_shell_receipt_floor",
            "exact_residual_lane_floor",
        ],
        "promotion_rule": [
            "route_components_are_staged_from_verified_seed",
            "immiscible_scaffold_boundary_is_bounded_and_not_payload",
            "attachment_order_is_deterministic_or_receipted",
            "frontier_focusing_preserves_decode_reachability",
            "outer_stability_shell_reduces_churn_without_hiding_bytes",
            "exact_residual_lanes_restore_source_bytes",
            "decoded_hash_matches_source",
            "measured_total_bytes_beat_incumbent_under_ratio_schema",
        ],
        "failure_rule": [
            "extra_components_increase_frontier_without_bound -> prune",
            "scaffold_boundary_hides_payload -> invalid_receipt",
            "attachment_order_ambiguous_without_tie_break -> fail_closed",
            "composition_focus_changes_decode_reachability -> fail_closed",
            "stability_shell_larger_than_byte_gain -> prune",
            "lab_catalyst_performance_used_as_byte_evidence -> diagnostic_only",
        ],
        "claim_boundary": (
            "This prior imports a staged self-organization and composition-focusing "
            "shape from multimetallic nanocrystal synthesis. It is not evidence "
            "that metals or catalysts compress text bytes; route promotion still "
            "requires exact decode, source hash, measured bytes, and explicit "
            "ratio schema."
        ),
    }
    preimage = {key: value for key, value in receipt.items() if key != "receipt_hash"}
    receipt["receipt_hash"] = sha256_text(stable_json(preimage))
    return receipt


def curriculum_lines(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    for item in receipt["composition_focusing_operators"]:
        lines.append({"type": "composition_focusing_operator", **item})
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
