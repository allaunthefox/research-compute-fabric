#!/usr/bin/env python3
"""Capture the refinement that every route stage is a parallel domain bundle.

The local design correction is that a route stage should not be modeled as one
linear transform lane. Each stage processes parallel domains of the data type
currently under evaluation: bytes, tokens, structure, residuals, witnesses,
owners, runtime budgets, and closure state. Promotion happens only when all
domains synchronize back to exact bytes with bounded costs.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
OUT = SHIM / "parallel_stage_domain_route_prior_receipt.json"
CURRICULUM_OUT = SHIM / "parallel_stage_domain_route_prior_curriculum.jsonl"

GENERATED_AT = "2026-05-08T00:00:00+00:00"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


DOMAIN_AXES = [
    {
        "id": "byte_domain",
        "role": "source bytes and exact decoded output",
        "promotion_authority": True,
        "failure": "byte hash mismatch -> not promoted",
    },
    {
        "id": "token_domain",
        "role": "XML tokens, phrase tokens, dependency heads, semantic anchors",
        "promotion_authority": False,
        "failure": "token view without residual -> diagnostic only",
    },
    {
        "id": "structure_domain",
        "role": "records, attributes, graphs, folds, bundles, scaffolds",
        "promotion_authority": False,
        "failure": "structure changes decode reachability -> fail closed",
    },
    {
        "id": "residual_domain",
        "role": "exact repair lanes for all sketch, deletion, imputation, or projection losses",
        "promotion_authority": True,
        "failure": "missing residual for non-byte-exact domain -> NaN0",
    },
    {
        "id": "witness_domain",
        "role": "topology, shell, singular, cache, composition, phase, and route receipts",
        "promotion_authority": False,
        "failure": "witness bytes exceed remaining gain -> prune",
    },
    {
        "id": "owner_domain",
        "role": "deterministic owner, cache dependency, route-to-chart assignment",
        "promotion_authority": False,
        "failure": "broadcast or ambiguous owner without tie-break -> fail closed",
    },
    {
        "id": "budget_domain",
        "role": "byte, runtime, sidecar, witness, and evaluator capacity budgets",
        "promotion_authority": False,
        "failure": "domain budget hidden from lower bound -> invalid receipt",
    },
    {
        "id": "closure_domain",
        "role": "NaN0, chi0, shell closure, rank decrease, rehydration status",
        "promotion_authority": True,
        "failure": "closure does not converge -> NaN0",
    },
]


EQUATIONS = [
    {
        "id": "PSD0_stage_bundle",
        "equation": "Stage_t = {D_t^byte, D_t^token, D_t^structure, D_t^residual, D_t^witness, D_t^owner, D_t^budget, D_t^closure}",
        "meaning": "A route stage is a synchronized bundle of typed domains, not a single transform.",
    },
    {
        "id": "PSD1_parallel_transition",
        "equation": "Stage_{t+1} = parallel_map(f_i, D_t^i) with sync barriers at claim boundaries",
        "meaning": "Each domain advances with its own legal edge, then synchronizes before claims are compared.",
    },
    {
        "id": "PSD2_domain_contract",
        "equation": "contract_i = (input_type_i, output_type_i, witness_cost_i, residual_obligation_i)",
        "meaning": "Every domain edge declares what it consumes, emits, costs, and must repair.",
    },
    {
        "id": "PSD3_cross_domain_barrier",
        "equation": "barrier_ok iff all obligations_i are paid and no domain has nan0_flag",
        "meaning": "No domain can advance a promotion claim while another domain carries unpaid byte debt.",
    },
    {
        "id": "PSD4_stage_lower_bound",
        "equation": "LB_stage = sum_i header_i + witness_i + residual_floor_i + compute_floor_i",
        "meaning": "Lower bounds are summed across parallel domains before expensive evaluation.",
    },
    {
        "id": "PSD5_stage_promotion",
        "equation": "promote iff sync(Stage_T) and hash(decode(D_T^byte + D_T^residual)) == source_hash and bytes < incumbent",
        "meaning": "The stage bundle promotes only through exact bytes after all domains synchronize.",
    },
]


def build_receipt() -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "schema": "parallel_stage_domain_route_prior_v1",
        "generated_at": GENERATED_AT,
        "source_evidence": {
            "type": "local_design_refinement",
            "statement": "Each stage is parallel domains of the data type being processed.",
            "workspace_target": "Decision Diagram Compression Tuning Prior",
        },
        "primary_decision": {
            "name": "model_route_stage_as_parallel_domain_bundle",
            "statement": (
                "Represent each DD route stage as a typed parallel domain bundle. "
                "Domains may transform, propose, route, repair, witness, or bound "
                "different views of the current data type, but they must synchronize "
                "at claim boundaries and close through exact decoded bytes."
            ),
        },
        "domain_axes": DOMAIN_AXES,
        "equations": EQUATIONS,
        "candidate_dd_state_extension": [
            "stage_id",
            "stage_domain_vector_id",
            "active_data_type_id",
            "byte_domain_state_id",
            "token_domain_state_id",
            "structure_domain_state_id",
            "residual_domain_state_id",
            "witness_domain_state_id",
            "owner_domain_state_id",
            "budget_domain_state_id",
            "closure_domain_state_id",
            "domain_contract_hash",
            "cross_domain_barrier_status",
            "stage_lower_bound_bytes",
            "domain_nan0_bitmap",
            "byte_rehydration_hash",
        ],
        "candidate_dd_edges": [
            "open_parallel_stage_bundle",
            "advance_byte_domain",
            "advance_token_domain",
            "advance_structure_domain",
            "emit_domain_residual_obligation",
            "charge_domain_witness_cost",
            "assign_domain_owner",
            "sum_stage_lower_bound",
            "synchronize_stage_domains",
            "reject_unsynchronized_promotion",
            "close_stage_with_rehydration_hash",
        ],
        "promotion_rule": [
            "stage_domains_are_explicit_and_typed",
            "each_domain_edge_declares_cost_and_residual_obligation",
            "cross_domain_barrier_synchronizes_before_promotion",
            "all_non_byte_exact_domains_emit_exact_residual_repair",
            "domain_nan0_bitmap_is_zero",
            "decoded_hash_matches_source",
            "measured_total_bytes_beat_incumbent_under_ratio_schema",
        ],
        "failure_rule": [
            "linear_stage_hides_parallel_domain_debt -> invalid_receipt",
            "domain_advances_without_contract -> fail_closed",
            "token_or_structure_domain_claims_byte_authority -> diagnostic_only",
            "cross_domain_barrier_unsynchronized -> not_promoted",
            "domain_nan0_bitmap_nonzero -> fail_closed",
            "sum_domain_costs_exceeds_incumbent_margin -> prune",
        ],
        "claim_boundary": (
            "Parallel stage domains are a route representation discipline. They "
            "do not relax the proof surface: exact decoded bytes, source hash, "
            "measured total bytes, bounded costs, and explicit ratio schema remain "
            "the only promotion authority."
        ),
    }
    preimage = {key: value for key, value in receipt.items() if key != "receipt_hash"}
    receipt["receipt_hash"] = sha256_text(stable_json(preimage))
    return receipt


def curriculum_lines(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    for item in receipt["domain_axes"]:
        lines.append({"type": "domain_axis", **item})
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
