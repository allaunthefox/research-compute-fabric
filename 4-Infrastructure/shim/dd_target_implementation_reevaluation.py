#!/usr/bin/env python3
"""Re-evaluate DD compression targets against current implementation receipts.

This is a receipt-bearing target review.  It does not recompress data.  It
reads the local decision-diagram, topology, route-card, KV, citation, and
singular-chart receipts and classifies which configuration knobs are currently:

* promotion-backed by measured bytes,
* useful as pruning / control configuration, or
* still only proposal surface until an encode/decode/hash evaluator exists.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
OUT = SHIM / "dd_target_implementation_reevaluation_receipt.json"
CURRICULUM_OUT = SHIM / "dd_target_implementation_reevaluation_curriculum.jsonl"

GENERATED_AT = "2026-05-08T00:00:00+00:00"
HUTTER_ENWIK9_TARGET_BYTES = 109_685_197

RECEIPT_PATHS = {
    "dimensional_shell_dd_probe": SHIM / "dimensional_shell_dd_probe_receipt.json",
    "projectable_geometry_topology_model": SHIM
    / "projectable_geometry_topology_model_receipt.json",
    "alphaevolve_dd_experiment_card_runner": SHIM
    / "alphaevolve_dd_experiment_card_receipt.json",
    "non_euclidean_semantic_kv_prior": SHIM
    / "non_euclidean_semantic_kv_prior_receipt.json",
    "citation_math_function_distillation": SHIM
    / "citation_math_function_distillation_receipt.json",
    "singular_route_chart_equations": SHIM
    / "singular_route_chart_equations_receipt.json",
    "compression_ratio_rederivation": SHIM
    / "compression_ratio_rederivation_receipt.json",
}


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def receipt_hash(path: Path, data: dict[str, Any]) -> str:
    for key in (
        "stable_topology_model_hash_sha256",
        "stable_shell_dd_hash_sha256",
        "receipt_hash",
    ):
        value = data.get(key)
        if isinstance(value, str):
            return value
    return sha256_bytes(path.read_bytes())


def source_receipts(receipts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        name: {
            "path": rel(RECEIPT_PATHS[name]),
            "hash": receipt_hash(RECEIPT_PATHS[name], receipt),
            "schema": receipt.get("schema", "unknown"),
        }
        for name, receipt in receipts.items()
    }


def class_counts(cards: dict[str, Any]) -> dict[str, int]:
    counts = cards.get("class_counts")
    if isinstance(counts, dict):
        return {str(key): int(value) for key, value in counts.items()}
    derived: dict[str, int] = {}
    for card in cards.get("cards", []):
        cls = str(card.get("applicability_class", "unknown"))
        derived[cls] = derived.get(cls, 0) + 1
    return derived


def current_best(shell: dict[str, Any], topology: dict[str, Any]) -> dict[str, Any]:
    shell_best = shell["summary"]["best_shell_adjusted_overall"]
    topology_best = topology["best_approach"]["selected_route"]
    return {
        "slice": topology_best["slice"],
        "route": topology["best_approach"]["route"],
        "byte_transform": f"{topology_best['transform']} -> {topology_best['codec']}",
        "source_bytes": topology_best["source_bytes"],
        "raw_baseline_bytes": topology_best["raw_baseline_bytes"],
        "xml_bz2_bytes": topology_best["compressed_bytes"],
        "topology_or_shell_witness_bytes": topology_best["topology_witness_bytes"],
        "modeled_total_bytes": topology_best["modeled_total_bytes"],
        "modeled_ratio": topology_best["modeled_ratio"],
        "remaining_margin_vs_raw_baseline_bytes": topology_best[
            "gain_vs_raw_after_topology_bytes"
        ],
        "witness_budget_before_losing_raw_bytes": topology_best[
            "overhead_budget_before_losing_raw"
        ],
        "projected_enwik9_total_bytes": shell_best[
            "projected_enwik9_total_bytes"
        ],
        "projected_hutter_gap_bytes": shell_best[
            "hutter_target_gap_bytes_projected_enwik9"
        ],
        "rehydration_status": shell_best["shell_status"],
        "lawful": bool(topology_best["lawful"] and not shell_best["shell_status"]["nan0"]),
    }


def implementation_status(receipts: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    shell = receipts["dimensional_shell_dd_probe"]
    topology = receipts["projectable_geometry_topology_model"]
    cards = receipts["alphaevolve_dd_experiment_card_runner"]
    kv = receipts["non_euclidean_semantic_kv_prior"]
    citation = receipts["citation_math_function_distillation"]
    singular = receipts["singular_route_chart_equations"]
    ratio = receipts["compression_ratio_rederivation"]

    return [
        {
            "id": "dimensional_shell_dd_probe",
            "status": "implemented_receipt_over_existing_measurements",
            "promotion_authority": "measured route receipt inherited from reversible approach; shell only adds bounded witness",
            "evidence": {
                "route_count": shell["summary"]["route_count"],
                "promoted_route_count": shell["summary"]["promoted_route_count"],
                "lower_bound_pruned_count": shell["summary"][
                    "lower_bound_pruned_count"
                ],
                "nan0_route_count": shell["summary"]["nan0_route_count"],
                "shell_witness_bytes": shell["dd_policy"][
                    "shell_witness_bytes_per_non_raw_route"
                ],
            },
            "verdict": "promotable_when_margin_survives_witness",
        },
        {
            "id": "projectable_geometry_topology_model",
            "status": "implemented_topology_witness_model",
            "promotion_authority": "existing xml_token -> bz2 byte measurement plus 16-byte witness budget",
            "evidence": topology["best_approach"]["selected_route"],
            "verdict": "current_best_control_plane",
        },
        {
            "id": "alphaevolve_dd_experiment_card_runner",
            "status": "implemented_search_card_prior",
            "promotion_authority": "none until local candidate code runs through encode/decode/hash evaluator",
            "evidence": {
                "card_count": cards["card_count"],
                "class_counts": class_counts(cards),
                "full_program_collection": cards["validation"].get(
                    "full_program_collections", False
                ),
            },
            "verdict": "proposal_and_dashboard_surface",
        },
        {
            "id": "citation_math_function_distillation",
            "status": "implemented_operator_distillation",
            "promotion_authority": "none; this is the route compiler algebra",
            "evidence": {
                "primary_function": citation["primary_function"]["name"],
                "algebra_count": len(citation["dd_function_algebra"]),
                "function_group_count": len(citation["function_groups"]),
            },
            "verdict": "configuration_basis",
        },
        {
            "id": "singular_route_chart_equations",
            "status": "implemented_equation_group",
            "promotion_authority": "none unless a finite chart decodes and hashes exact bytes under measured byte count",
            "evidence": {
                "primary_function": singular["singular_route_chart"][
                    "primary_function"
                ],
                "equation_count": len(singular["equations"]),
                "dd_state_field_count": len(singular["dd_state_extension"]),
                "receipt_hash": singular["receipt_hash"],
            },
            "verdict": "fail_closed_chart_layer",
        },
        {
            "id": "non_euclidean_semantic_kv_prior",
            "status": "implemented_prior_and_watchlist",
            "promotion_authority": "none until byte-store / KV-cache routes have exact rehydration receipts",
            "evidence": {
                "prior_family_count": len(kv["prior_families"]),
                "priority_watch_items": [
                    item["id"] for item in kv["priority_watch_items"]
                ],
                "treefiddy_status": kv["local_treefiddy_status"]["status"],
            },
            "verdict": "proposal_surface_with_local_tree_bound",
        },
        {
            "id": "compression_ratio_rederivation",
            "status": "implemented_ratio_audit",
            "promotion_authority": "ratio schema only; byte counts remain terminal authority",
            "evidence": {
                "claim_boundary": ratio["claim_boundary"],
                "finance_claim_lut_lawful": ratio["finance_claim_lut"]["lawful"],
            },
            "verdict": "measurement_schema_guard",
        },
    ]


def configuration_axes(best: dict[str, Any]) -> list[dict[str, Any]]:
    remaining = int(best["remaining_margin_vs_raw_baseline_bytes"])
    budget = int(best["witness_budget_before_losing_raw_bytes"])
    return [
        {
            "id": "topology_witness_bytes",
            "current_setting": 16,
            "admissible_range_for_current_best_bytes": [0, budget],
            "target_role": "bounded closure/control witness",
            "reevaluation": "keep at 16 unless a new encoder earns more payload savings",
        },
        {
            "id": "operator_basis_B_R_F_T_A_E_V",
            "current_setting": "available_as_distilled_algebra",
            "target_role": "configure pruning, routing, folding, transport, allocation, repair, and verification",
            "reevaluation": "wire as evaluator stages; do not charge bytes unless an emitted receipt/witness is serialized",
        },
        {
            "id": "singular_route_chart",
            "current_setting": "available_not_wired_to_byte_evaluator",
            "target_role": "contain singular/ambiguous/unbounded route regions",
            "reevaluation": (
                "use on failing or ambiguous branches first; applying extra chart "
                f"bytes to the current best must stay under {remaining} bytes"
            ),
        },
        {
            "id": "tinyenc_encrypted_kv_envelope",
            "current_setting": "watch_item_only",
            "target_role": "future compressed/encrypted byte-store route",
            "reevaluation": "diagnostic until compressed bytes, query index overhead, and plaintext hash are receipted",
        },
        {
            "id": "treekv_treefiddy_spine",
            "current_setting": "local_treefiddy_found_prior_only",
            "target_role": "bounded tree route spine and owner/depth guard",
            "reevaluation": "proposal only until TreeKV merge preserves decode reachability and exact residual leaves",
        },
        {
            "id": "alphaevolve_route_population",
            "current_setting": "experiment_card_shape_only",
            "target_role": "candidate generator and analysed/program counters",
            "reevaluation": "feed candidates into the DD; never promote gallery score or novelty without local byte receipt",
        },
    ]


def admissibility_verdicts(best: dict[str, Any]) -> list[dict[str, Any]]:
    remaining = int(best["remaining_margin_vs_raw_baseline_bytes"])
    return [
        {
            "route_or_overlay": "xml_token -> topology_witness_16b -> bz2",
            "verdict": "promote_current_incumbent_for_small_slice",
            "reason": "measured route survives exact shell/topology witness and beats raw+bz2 by 1105 bytes",
        },
        {
            "route_or_overlay": "singular_chart_on_current_best",
            "verdict": "prune_unless_chart_bytes_are_paid_by_new_savings",
            "reason": f"any added chart receipt consumes the remaining {remaining}-byte margin",
        },
        {
            "route_or_overlay": "B/R/F/T/A/E/V operator basis",
            "verdict": "admissible_as_evaluator_configuration",
            "reason": "operators organize route search and receipts, but do not themselves add byte evidence",
        },
        {
            "route_or_overlay": "TreeKV + Tree Fiddy",
            "verdict": "diagnostic_until_encoder_exists",
            "reason": "local Tree Fiddy can bound tree depth, but no TreeKV byte route has been evaluated",
        },
        {
            "route_or_overlay": "TinyEnc-style encrypted KV store",
            "verdict": "diagnostic_until_store_receipt_exists",
            "reason": "encryption, query index, and compression overhead must all be counted with plaintext rehydration",
        },
        {
            "route_or_overlay": "AlphaEvolve route population",
            "verdict": "proposal_generator_only",
            "reason": "program and analysed counts are useful search controls, not compression evidence",
        },
    ]


def next_target(best: dict[str, Any]) -> dict[str, Any]:
    return {
        "target_name": "configurable_bounded_route_evaluator",
        "reframed_goal": "optimize route evaluation and pruning configuration before adding more serialized witness bytes",
        "why": (
            "The current best has only 1105 bytes of margin after the 16-byte "
            "witness. New knobs should reject bad branches cheaply or propose "
            "new byte-saving transforms; they should not be blindly appended to "
            "the incumbent route."
        ),
        "minimum_config_fields": [
            "slice_id",
            "candidate_route",
            "backend_codec",
            "topology_witness_bytes",
            "singular_chart_enabled",
            "singular_chart_bytes",
            "treefiddy_spine_enabled",
            "tinyenc_envelope_enabled",
            "ratio_schema",
            "incumbent_bytes",
            "lower_bound_bytes",
            "rehydration_hash",
        ],
        "first_safe_implementation_step": (
            "Add a configuration-matrix wrapper over existing receipts that "
            "computes lower bounds and prunes overlays whose witness/chart/KV "
            "cost would erase the incumbent margin before recompression."
        ),
        "first_real_compression_step": (
            "Evaluate one new payload-saving transform family at a time, starting "
            "with bounded corpus-resolution/fascicle or tokenbook variants, then "
            "charge any topology/singular/KV witness bytes in the terminal receipt."
        ),
        "hard_target_bytes_enwik9": HUTTER_ENWIK9_TARGET_BYTES,
        "diagnostic_target": "beat raw baseline per slice under explicit ratio_schema",
        "current_gap_to_hard_target_projected_enwik9_bytes": best[
            "projected_hutter_gap_bytes"
        ],
    }


def curriculum_lines(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    for item in receipt["implementation_status"]:
        lines.append(
            {
                "type": "implementation_status",
                "id": item["id"],
                "status": item["status"],
                "verdict": item["verdict"],
            }
        )
    for item in receipt["configuration_axes"]:
        lines.append(
            {
                "type": "configuration_axis",
                "id": item["id"],
                "current_setting": item["current_setting"],
                "reevaluation": item["reevaluation"],
            }
        )
    for item in receipt["admissibility_verdicts"]:
        lines.append(
            {
                "type": "admissibility_verdict",
                "id": item["route_or_overlay"],
                "verdict": item["verdict"],
                "reason": item["reason"],
            }
        )
    return lines


def build_receipt() -> dict[str, Any]:
    receipts = {name: load_json(path) for name, path in RECEIPT_PATHS.items()}
    best = current_best(
        receipts["dimensional_shell_dd_probe"],
        receipts["projectable_geometry_topology_model"],
    )
    receipt: dict[str, Any] = {
        "schema": "dd_target_implementation_reevaluation_v1",
        "generated_at": GENERATED_AT,
        "source_receipts": source_receipts(receipts),
        "current_target": {
            "primary_machine": "bounded_exact_route_compiler",
            "hard_target_bytes_enwik9": HUTTER_ENWIK9_TARGET_BYTES,
            "diagnostic_target": "beat raw baseline per slice under explicit ratio_schema",
            "proof_surface": [
                "exact decoded bytes",
                "rehydration hash",
                "measured compressed_total_bytes",
                "explicit ratio_schema",
                "bounded sidecar/witness/container/compute cost",
                "fail-closed NaN0 metadata holds",
            ],
        },
        "current_best_implemented_route": best,
        "implementation_status": implementation_status(receipts),
        "configuration_axes": configuration_axes(best),
        "admissibility_verdicts": admissibility_verdicts(best),
        "reevaluated_next_target": next_target(best),
        "claim_boundary": (
            "This is a target and implementation reevaluation over local receipts. "
            "It does not recompress data, prove optimality, or promote any route "
            "without an encode/decode/hash/byte-count receipt."
        ),
    }
    preimage = {key: value for key, value in receipt.items() if key != "receipt_hash"}
    receipt["receipt_hash"] = sha256_bytes(stable_json(preimage).encode("utf-8"))
    return receipt


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
        "line_count": len(lines),
        "current_best": receipt["current_best_implemented_route"]["route"],
        "next_target": receipt["reevaluated_next_target"]["target_name"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
