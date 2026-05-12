#!/usr/bin/env python3
"""Validate moving-sofa scout responses.

This finishes the first complete couch-problem loop:

  scout packets -> scout responses -> deterministic validation/promote/hold

If no response file is supplied, the script emits conservative baseline
responses that satisfy the same contract ZAYA must satisfy later. That makes the
pipeline runnable today while keeping the model as a replaceable scout.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


DEFAULT_PACKETS = Path("4-Infrastructure/shim/moving_sofa_scout_packets.jsonl")
FORBIDDEN_PROOF_WORDS = {"solved", "proved", "proof", "certified", "optimality_certified"}


BASELINE_PLANS = {
    "contact_envelope_decomposition": {
        "curve_sections": ["gerver_section_index_0_to_17", "wall_contact_arc", "corner_contact_transition"],
        "contact_events": ["left_wall_support", "inner_corner_tangent", "right_wall_support"],
        "reconstruction_error_plan": "compare reconstructed envelope area and contact continuity against source curve receipts",
        "source_prior_ids": ["Gerver_sofa_constant", "Baek_optimality_claim"],
    },
    "upper_bound_certificate_shape": {
        "angle_grid": "monotone theta samples with interval enclosure, not a single floating grid",
        "forbidden_region_model": "intersection of hallway-obstruction half-planes/contact constraints",
        "coverage_certificate": "hashable interval cover over angle/contact states",
        "error_bound_plan": "separate discretization error, interval arithmetic error, and coverage gap",
    },
    "variational_functional_route": {
        "functional": "area(shape_boundary) subject to feasible corridor-motion constraints",
        "assumptions": ["connected planar shape", "unit-width right-angle hallway", "declared convexity/injectivity assumptions only when used"],
        "necessary_conditions": ["Euler-Lagrange stationarity", "contact-envelope boundary compatibility"],
        "numerical_receipts": ["integration_error", "curve_section_hash", "assumption_list"],
    },
    "nspace_generalization_probe": {
        "dimension": "n >= 2, with 2D theorem status kept separate",
        "corridor_topology": "right-angle corridor generalized to constrained passage complex",
        "rigid_body_state": ["translation_coordinates", "rotation_group_parameterization", "collision_predicate"],
        "projection_rule": "project n-space obstruction to lower-dimensional contact certificates",
        "analogy_boundary": "n-space probe is an analogy/search surface, not a solved 2D theorem",
    },
    "claimed_proof_triage": {
        "lemma_buckets": ["configuration-space reduction", "contact-envelope completeness", "upper-bound obstruction", "Gerver equality case"],
        "dependency_graph": "extract definitions -> lemmas -> theorem -> numeric constant dependencies",
        "certificate_candidates": ["curve_section_receipts", "interval_cover_hashes", "area_integral_replay"],
        "verification_order": ["definitions", "assumptions", "local lemmas", "certificate replay", "global theorem claim"],
    },
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    out = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                out.append(json.loads(line))
    return out


def sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def make_baseline_response(packet: dict[str, Any]) -> dict[str, Any]:
    task_id = packet["task_id"]
    plan = dict(BASELINE_PLANS.get(task_id, {}))
    plan.update(
        {
            "claim_boundary": "scout-response-only; not proof",
            "next_receipts": ["source_excerpt", "formal_or_solver_check", "metaprobe_audit"],
            "promotion_request": "HOLD until receipt gates pass",
            "packet_hash": packet["packet_hash"],
        }
    )
    return plan


def load_responses(path: Path | None, packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not path:
        return [make_baseline_response(packet) for packet in packets]
    return load_jsonl(path)


def contains_forbidden_claim(value: Any) -> bool:
    text = json.dumps(value, ensure_ascii=False).lower()
    # These words are allowed when they appear in explicit negative/boundary
    # phrases. Keep this conservative and phrase-based rather than trying to do
    # natural-language semantics inside the validator.
    safe_boundary_phrases = [
        "not proof",
        "no proof",
        "not a proof",
        "not solved",
        "not a solved",
        "not accepted",
        "not automatically accepted",
        "not an automatically accepted",
        "not certified",
        "no theorem claim",
    ]
    for phrase in safe_boundary_phrases:
        text = text.replace(phrase, "")
    return any(word in text for word in FORBIDDEN_PROOF_WORDS)


def validate_response(packet: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    required = set(packet.get("required_response_fields", []))
    present = {field for field in required if field in response}
    must_include = set(packet.get("response_contract", {}).get("must_include", []))
    present_contract = {field for field in must_include if field in response}
    packet_hash_ok = response.get("packet_hash") == packet.get("packet_hash")
    boundary_ok = "claim_boundary" in response and "not proof" in str(response.get("claim_boundary", "")).lower()
    receipts_ok = isinstance(response.get("next_receipts"), list) and bool(response.get("next_receipts"))
    forbidden = contains_forbidden_claim(response)
    required_ok = present == required
    contract_ok = present_contract == must_include
    lawful = required_ok and contract_ok and packet_hash_ok and boundary_ok and receipts_ok and not forbidden
    return {
        "task_id": packet.get("task_id"),
        "required_ok": required_ok,
        "contract_ok": contract_ok,
        "packet_hash_ok": packet_hash_ok,
        "boundary_ok": boundary_ok,
        "receipts_ok": receipts_ok,
        "forbidden_claim": forbidden,
        "promotion": "PROMOTE_TO_SOURCE_FORMAL_TRIAGE" if lawful else "HOLD",
        "lawful": lawful,
        "response_hash": sha256_json(response),
    }


def curriculum_records(packets: list[dict[str, Any]], responses: list[dict[str, Any]], validations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    system = "You are a moving-sofa scout-response validator. Return compact JSON with promotion status."
    records = []
    for packet, response, validation in zip(packets, responses, validations):
        prompt = {
            "task": "validate_moving_sofa_scout_response",
            "packet": {
                "task_id": packet["task_id"],
                "required_response_fields": packet["required_response_fields"],
                "packet_hash": packet["packet_hash"],
            },
            "response": response,
        }
        answer = {
            "selected": validation["lawful"],
            "task_id": validation["task_id"],
            "promotion": validation["promotion"],
            "claim_boundary": "validation-receipt-only",
            "checks": validation,
        }
        records.append(
            {
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
                    {"role": "assistant", "content": json.dumps(answer, ensure_ascii=False)},
                ]
            }
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packets", type=Path, default=DEFAULT_PACKETS)
    parser.add_argument("--responses", type=Path, help="optional ZAYA response JSONL; defaults to baseline conservative responses")
    parser.add_argument("--out-responses", type=Path, default=Path("4-Infrastructure/shim/moving_sofa_scout_baseline_responses.jsonl"))
    parser.add_argument("--receipt", type=Path, default=Path("4-Infrastructure/shim/moving_sofa_scout_response_validation_receipt.json"))
    parser.add_argument("--curriculum", type=Path, default=Path("4-Infrastructure/shim/moving_sofa_scout_response_validation_curriculum.jsonl"))
    args = parser.parse_args()

    packets = load_jsonl(args.packets)
    responses = load_responses(args.responses, packets)
    if len(responses) != len(packets):
        raise SystemExit(f"response count {len(responses)} does not match packet count {len(packets)}")
    validations = [validate_response(packet, response) for packet, response in zip(packets, responses)]
    lawful_count = sum(1 for item in validations if item["lawful"])
    receipt = {
        "schema": "moving_sofa_scout_response_validation_v1",
        "claim_boundary": "Validation gates scout responses; it does not prove the moving sofa problem.",
        "packets": str(args.packets),
        "responses_source": str(args.responses) if args.responses else "baseline_conservative_responses",
        "response_count": len(responses),
        "lawful_count": lawful_count,
        "validations": validations,
        "lawful": lawful_count == len(validations),
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    with args.out_responses.open("w", encoding="utf-8") as handle:
        for response in responses:
            handle.write(json.dumps(response, ensure_ascii=False) + "\n")
    args.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with args.curriculum.open("w", encoding="utf-8") as handle:
        for record in curriculum_records(packets, responses, validations):
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
