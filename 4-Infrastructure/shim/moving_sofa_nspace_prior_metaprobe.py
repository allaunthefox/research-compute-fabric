#!/usr/bin/env python3
"""Moving sofa / couch problem n-space prior.

This is the user's white-whale geometry target. The receipt turns the problem
into a compression/search surface: configuration space, contact envelopes,
rotation schedules, obstruction certificates, and claimed proof boundaries.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SOFA_AXES = [
    {
        "axis": "configuration_space",
        "payload": ["x", "y", "theta", "hallway_constraint", "collision_free_path"],
        "router_use": "encode sofa motion as a low-dimensional path through constrained configuration space",
        "receipt_rule": "record corridor width, rotation angle schedule, contact state, and collision predicate",
    },
    {
        "axis": "contact_envelope",
        "payload": ["wall_contact", "corner_contact", "swept_boundary", "curve_section", "support_line"],
        "router_use": "compress feasible shapes by contact/event envelopes instead of dense grids",
        "receipt_rule": "record curve section IDs, tangency/contact events, and boundary reconstruction error",
    },
    {
        "axis": "area_functional",
        "payload": ["shape_boundary", "area_integral", "variation", "Euler_Lagrange_condition", "constraint_multiplier"],
        "router_use": "route variational approaches and Gerver-like optimality conditions",
        "receipt_rule": "record functional, assumptions, necessary conditions, and numerical integration error",
    },
    {
        "axis": "upper_bound_obstruction",
        "payload": ["angle_grid", "forbidden_region", "cover_certificate", "upper_bound", "computer_assistance"],
        "router_use": "construct obstruction certificates for pruning larger candidate shapes",
        "receipt_rule": "record discretization, interval bounds, certificate hash, and convergence/coverage claim",
    },
    {
        "axis": "neural_shape_scout",
        "payload": ["candidate_shape_latent", "movement_policy", "area_score", "constraint_loss", "counterexample_search"],
        "router_use": "use ZAYA/neural solvers as scouts for candidate decompositions and failure cases",
        "receipt_rule": "neural evidence never promotes without analytic/source/verifier certificate",
    },
    {
        "axis": "nspace_generalization",
        "payload": ["dimension", "corridor_topology", "rigid_body_state", "projection", "obstruction_family"],
        "router_use": "generalize couch problem into n-space topology/compression experiments",
        "receipt_rule": "record dimensional assumptions and distinguish 2D sofa theorem claims from n-space analogies",
    },
]


SOFA_PRIORS = [
    {
        "id": "Gerver_sofa_constant",
        "role": "best_known_classical_lower_bound_and_conjectured_optimum",
        "boundary": "classical-construction-prior",
        "use_as": "target_shape_and_contact_envelope_prior",
        "source": "Gerver construction, referenced across current sofa literature",
        "url": "https://www.math.ucdavis.edu/~romik/movingsofa/",
        "notes": "Area approximately 2.2195; boundary described by 18 curve sections in modern accounts.",
    },
    {
        "id": "Kallus_Romik_upper_bound",
        "role": "computer_assisted_upper_bound_prior",
        "boundary": "published/computer-assisted-prior",
        "use_as": "upper_bound_obstruction_certificate_axis",
        "source": "Improved upper bounds in the moving sofa problem",
        "url": "https://www.math.ucdavis.edu/~romik/data/uploads/papers/sofabounds.pdf",
        "notes": "Upper bound line around 2.37; useful for obstruction-certificate shape.",
    },
    {
        "id": "Baek_conditional_upper_bound",
        "role": "conditional_injectivity_upper_bound_prior",
        "boundary": "paper-prior-only",
        "use_as": "injectivity_condition_and_variational_upper_bound_axis",
        "source": "A Conditional Upper Bound for the Moving Sofa Problem",
        "url": "https://arxiv.org/abs/2406.10725",
        "notes": "Reports conditional upper bound 1 + pi^2/8 = 2.2337... under an injectivity condition including Gerver's sofa.",
    },
    {
        "id": "Deng_variational_solver",
        "role": "calculus_of_variations_necessary_condition_prior",
        "boundary": "paper-prior-only",
        "use_as": "area_functional_and_euler_lagrange_axis",
        "source": "Solving Moving Sofa Problem Using Calculus of Variations",
        "url": "https://arxiv.org/abs/2407.02587",
        "notes": "Derives variational necessary conditions and numerically recovers Gerver-scale area under assumptions.",
    },
    {
        "id": "Deep_learning_Gerver_evidence",
        "role": "neural_evidence_for_global_optimality_prior",
        "boundary": "evidence-prior-not-proof",
        "use_as": "neural_shape_scout_and_negative_control_axis",
        "source": "Deep Learning Evidence for Global Optimality of Gerver's Sofa",
        "url": "https://arxiv.org/abs/2407.11106",
        "notes": "Useful as scout/evidence shape; does not replace proof or obstruction certificate.",
    },
    {
        "id": "Baek_optimality_claim",
        "role": "claimed_resolution_of_moving_sofa_problem",
        "boundary": "arxiv-claimed-proof-prior-until-independent-verification",
        "use_as": "proof_structure_and_obstruction_certificate_target",
        "source": "Optimality of Gerver's Sofa",
        "url": "https://arxiv.org/abs/2411.19826",
        "notes": "Claims Gerver's 18-section construction attains maximum area 2.2195...; local pipeline should treat as source to inspect, not as automatically accepted theorem.",
    },
]


def chat_record(system: str, prompt: dict[str, Any], answer: dict[str, Any]) -> dict[str, Any]:
    return {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            {"role": "assistant", "content": json.dumps(answer, ensure_ascii=False)},
        ]
    }


def curriculum_records(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    system = "You are a moving-sofa n-space geometry router. Return compact JSON with proof boundaries."
    records: list[dict[str, Any]] = []
    for axis in receipt["sofa_axes"]:
        records.append(
            chat_record(
                system,
                {
                    "task": "route_moving_sofa_axis",
                    "axis": axis["axis"],
                    "payload": axis["payload"],
                    "instruction": "Use this axis to compress/search the couch problem.",
                },
                {
                    "selected": True,
                    "use_as": axis["router_use"],
                    "claim_boundary": "moving-sofa-coordinate-prior-only",
                    "surface_payload_hint": axis["axis"][:16].upper(),
                    "receipt_rule": axis["receipt_rule"],
                },
            )
        )
    for prior in receipt["sofa_priors"]:
        records.append(
            chat_record(
                system,
                {
                    "task": "use_moving_sofa_prior",
                    "prior": prior["id"],
                    "role": prior["role"],
                    "source": prior["source"],
                    "instruction": "Explain how this prior guides ZAYA/intense modeling without becoming proof.",
                },
                {
                    "selected": True,
                    "use_as": prior["use_as"],
                    "claim_boundary": prior["boundary"],
                    "metaprobe_rule": "Use for route/scout/certificate shape only; theorem status requires independent source/proof/formal or reproducible certificate receipts.",
                },
            )
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, default=Path("4-Infrastructure/shim/moving_sofa_nspace_prior_receipt.json"))
    parser.add_argument("--curriculum", type=Path, default=Path("4-Infrastructure/shim/moving_sofa_nspace_prior_curriculum.jsonl"))
    args = parser.parse_args()

    receipt = {
        "schema": "moving_sofa_nspace_prior_v1",
        "claim_boundary": "Moving sofa priors guide n-space search/compression; they do not certify a proof.",
        "white_whale": True,
        "sofa_axes": SOFA_AXES,
        "sofa_priors": SOFA_PRIORS,
        "lawful": True,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with args.curriculum.open("w", encoding="utf-8") as handle:
        for record in curriculum_records(receipt):
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
