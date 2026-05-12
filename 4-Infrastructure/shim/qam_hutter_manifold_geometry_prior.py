#!/usr/bin/env python3
"""Model the QAM Hutter equation as a constrained manifold geometry.

The useful local idea is that the I-axis byte objective and the Q-axis
exactness receipt are not two scores to average. They are coordinates on a
route manifold with a hard promotion submanifold: routes promote only when the
byte coordinate is below the incumbent and the receipt coordinate lies on the
exactness/closure locus.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SHIM = REPO / "4-Infrastructure" / "shim"
OUT = SHIM / "qam_hutter_manifold_geometry_prior_receipt.json"
CURRICULUM_OUT = SHIM / "qam_hutter_manifold_geometry_prior_curriculum.jsonl"

GENERATED_AT = "2026-05-08T00:00:00+00:00"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


MANIFOLD_OBJECTS = [
    {
        "id": "route_manifold",
        "symbol": "M_route",
        "definition": "space of legal transform routes with coordinates for bytes, witnesses, residuals, receipts, owners, and closure state",
        "compression_role": "search surface for Hutter-style exact routes",
    },
    {
        "id": "byte_coordinate_chart",
        "symbol": "I: M_route -> R",
        "definition": "I(r) = payload + sidecar + witness + container bytes",
        "compression_role": "objective coordinate minimized against the incumbent",
    },
    {
        "id": "exactness_constraint_chart",
        "symbol": "Q: M_route -> {0,1}",
        "definition": "Q(r)=1 iff decode/hash/receipt/NaN0 closure all pass",
        "compression_role": "hard constraint, not an optimizable soft score",
    },
    {
        "id": "promotion_submanifold",
        "symbol": "P = {r in M_route | I(r) < incumbent and Q(r)=1}",
        "definition": "verified route region eligible for incumbent replacement",
        "compression_role": "only region from which Hutter claims may be promoted",
    },
    {
        "id": "prune_halfspace",
        "symbol": "N = {r_prefix | LB_QAM(r_prefix) >= incumbent}",
        "definition": "lower-bound excluded route prefixes",
        "compression_role": "prevents expensive evaluation of routes that cannot win",
    },
    {
        "id": "nan0_boundary",
        "symbol": "partial M_NaN0",
        "definition": "fail-closed boundary where receipt, closure, or exactness is invalid",
        "compression_role": "absorbs invalid routes without recursive repair",
    },
]


EQUATIONS = [
    {
        "id": "QHM0_route_coordinate",
        "equation": "x_r = (I_payload, I_sidecar, I_witness, I_container, Q_hash, Q_merkle, Q_decode, Q_nan0)",
        "meaning": "A route point carries byte-mass coordinates and exactness receipt coordinates.",
    },
    {
        "id": "QHM1_byte_function",
        "equation": "I(r) = payload_bytes(r) + sidecar_bytes(r) + witness_bytes(r) + container_overhead(r)",
        "meaning": "The I coordinate is the measured byte objective.",
    },
    {
        "id": "QHM2_exactness_locus",
        "equation": "E = {r | decode(r)=source and H(decode(r))=source_hash and merkle(r)=route_key(r) and nan0(r)=0}",
        "meaning": "The exactness locus is a hard submanifold of valid route points.",
    },
    {
        "id": "QHM3_promotion_submanifold",
        "equation": "P = E cap {r | I(r) < incumbent_bytes}",
        "meaning": "Promotion requires exactness plus a strict byte win.",
    },
    {
        "id": "QHM4_prune_region",
        "equation": "Prune(prefix) iff LB_QAM(prefix) >= incumbent_bytes",
        "meaning": "Prefixes whose lower bound lies outside the winning halfspace are pruned.",
    },
    {
        "id": "QHM5_margin_budget",
        "equation": "witness_budget_remaining = incumbent_bytes - measured_payload_bytes - required_sidecar_bytes",
        "meaning": "Any new geometric, semantic, FPGA, or cache witness must fit inside measured savings.",
    },
    {
        "id": "QHM6_barrier_flow",
        "equation": "flow(r_t -> r_{t+1}) admissible iff Q remains closable and LB decreases or stays below incumbent",
        "meaning": "Search flow is allowed only while the exactness side can still close and the byte side can still win.",
    },
]


def build_receipt() -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "schema": "qam_hutter_manifold_geometry_prior_v1",
        "generated_at": GENERATED_AT,
        "source_evidence": {
            "type": "local_modeling_refinement",
            "statement": "Model the QAM Hutter Prize equations as manifold geometry.",
            "workspace_target": "Decision Diagram Compression Tuning Prior",
        },
        "primary_decision": {
            "name": "model_qam_hutter_as_constrained_route_manifold",
            "statement": (
                "Represent Hutter route tuning as a constrained manifold. The byte objective "
                "is an I-coordinate, exact rehydration and receipts form a Q-coordinate "
                "constraint, and promotion occurs only on the verified winning submanifold."
            ),
        },
        "manifold_objects": MANIFOLD_OBJECTS,
        "equations": EQUATIONS,
        "candidate_dd_state_extension": [
            "route_manifold_chart_id",
            "route_point_id",
            "i_payload_coordinate",
            "i_sidecar_coordinate",
            "i_witness_coordinate",
            "i_total_coordinate",
            "q_hash_coordinate",
            "q_merkle_coordinate",
            "q_decode_coordinate",
            "q_nan0_coordinate",
            "exactness_locus_status",
            "promotion_submanifold_status",
            "prune_halfspace_status",
            "margin_budget_bytes",
        ],
        "candidate_dd_edges": [
            "open_route_manifold_chart",
            "embed_route_as_qam_point",
            "compute_i_axis_byte_coordinate",
            "compute_q_axis_receipt_coordinate",
            "project_prefix_to_lower_bound_halfspace",
            "test_exactness_locus_membership",
            "test_promotion_submanifold_membership",
            "route_to_nan0_boundary",
            "promote_verified_winning_route",
        ],
        "promotion_rule": [
            "route_point_lies_on_exactness_locus",
            "i_axis_total_bytes_is_below_incumbent",
            "ratio_schema_is_explicit",
            "nan0_coordinate_is_zero",
            "witness_and_sidecar_mass_are_counted",
        ],
        "failure_rule": [
            "outside_exactness_locus -> not_promoted",
            "inside_exactness_locus_but_no_byte_win -> diagnostic_only",
            "lower_bound_outside_winning_halfspace -> prune",
            "nan0_coordinate_nonzero -> fail_closed",
            "hidden_payload_in_q_axis -> invalid_receipt",
        ],
        "implementation_implication": (
            "A configurable bounded route evaluator can treat each candidate as a point in "
            "M_route, cheaply reject prefixes outside the winning halfspace, and reserve "
            "expensive encode/decode/hash work for routes whose Q-coordinate can still close."
        ),
    }
    receipt["receipt_hash"] = sha256_text(stable_json(receipt))
    return receipt


def write_curriculum(receipt: dict[str, Any]) -> None:
    records = []
    for eq in receipt["equations"]:
        records.append(
            {
                "task": "derive_qam_hutter_manifold_equation",
                "equation_id": eq["id"],
                "prompt": f"Explain {eq['id']} for the bounded exact route compiler.",
                "completion": f"{eq['equation']} -- {eq['meaning']}",
            }
        )
    for obj in receipt["manifold_objects"]:
        records.append(
            {
                "task": "map_route_manifold_object",
                "object_id": obj["id"],
                "prompt": f"Map {obj['symbol']} into compression route evaluation.",
                "completion": obj["compression_role"],
            }
        )
    CURRICULUM_OUT.write_text(
        "".join(stable_json(record) + "\n" for record in records),
        encoding="utf-8",
    )


def main() -> int:
    receipt = build_receipt()
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    write_curriculum(receipt)
    print(json.dumps(
        {
            "receipt": rel(OUT),
            "curriculum": rel(CURRICULUM_OUT),
            "receipt_hash": receipt["receipt_hash"],
            "equation_count": len(receipt["equations"]),
            "manifold_object_count": len(receipt["manifold_objects"]),
        },
        indent=2,
        sort_keys=True,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
