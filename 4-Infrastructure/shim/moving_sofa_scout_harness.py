#!/usr/bin/env python3
"""Moving sofa scout harness.

This is the next runnable loop for the couch/sofa white whale:

  prior receipt -> ZAYA-ready scout packets -> deterministic admissibility gates

The harness does not solve the moving sofa problem. It prepares bounded prompts
for a local scout model and defines what a usable answer must contain before it
can be promoted to source/formal/certificate work.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


DEFAULT_PRIOR = Path("4-Infrastructure/shim/moving_sofa_nspace_prior_receipt.json")
DEFAULT_ROUTER = Path("4-Infrastructure/shim/intense_math_modeling_router_receipt.json")
DEFAULT_EIGEN = Path("4-Infrastructure/shim/nspace_semantic_pde_eigenvectors.json")


SCOUT_TASKS = [
    {
        "id": "contact_envelope_decomposition",
        "axis": "contact_envelope",
        "ask": "Propose a contact-event decomposition for Gerver-style sofa motion.",
        "required_fields": ["curve_sections", "contact_events", "reconstruction_error_plan", "source_prior_ids"],
        "promotion_gate": "must cite curve/event receipt plan; no proof claim",
    },
    {
        "id": "upper_bound_certificate_shape",
        "axis": "upper_bound_obstruction",
        "ask": "Propose a certificate schema for pruning candidate shapes above Gerver-scale area.",
        "required_fields": ["angle_grid", "forbidden_region_model", "coverage_certificate", "error_bound_plan"],
        "promotion_gate": "must include discretization and coverage/error boundary",
    },
    {
        "id": "variational_functional_route",
        "axis": "area_functional",
        "ask": "Propose a variational route that separates assumptions, necessary conditions, and numerical checks.",
        "required_fields": ["functional", "assumptions", "necessary_conditions", "numerical_receipts"],
        "promotion_gate": "Euler-Lagrange style conditions are necessary only unless proof receipt says otherwise",
    },
    {
        "id": "nspace_generalization_probe",
        "axis": "nspace_generalization",
        "ask": "Map the 2D sofa problem into an n-space generalization without confusing analogy with theorem.",
        "required_fields": ["dimension", "corridor_topology", "rigid_body_state", "projection_rule", "analogy_boundary"],
        "promotion_gate": "must distinguish 2D theorem status from n-space experiment",
    },
    {
        "id": "claimed_proof_triage",
        "axis": "configuration_space",
        "ask": "Triage the claimed optimality proof into checkable lemmas, dependencies, and certificate candidates.",
        "required_fields": ["lemma_buckets", "dependency_graph", "certificate_candidates", "verification_order"],
        "promotion_gate": "must treat arXiv claim as source material, not accepted theorem",
    },
]


def sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_axis(prior: dict[str, Any], axis_name: str) -> dict[str, Any]:
    for axis in prior.get("sofa_axes", []):
        if axis.get("axis") == axis_name:
            return axis
    raise KeyError(axis_name)


def top_terms(eigen: dict[str, Any], limit: int = 12) -> list[str]:
    return [str(item.get("term")) for item in eigen.get("top_terms", [])[:limit]]


def make_scout_packet(task: dict[str, Any], prior: dict[str, Any], router: dict[str, Any], eigen: dict[str, Any]) -> dict[str, Any]:
    axis = find_axis(prior, task["axis"])
    packet = {
        "schema": "moving_sofa_scout_packet_v1",
        "task_id": task["id"],
        "preferred_scout_model": router.get("preferred_scout_model", "Zyphra/ZAYA1-8B"),
        "axis": axis,
        "ask": task["ask"],
        "required_response_fields": task["required_fields"],
        "promotion_gate": task["promotion_gate"],
        "relevant_priors": [
            {
                "id": item.get("id"),
                "role": item.get("role"),
                "boundary": item.get("boundary"),
                "use_as": item.get("use_as"),
                "url": item.get("url"),
            }
            for item in prior.get("sofa_priors", [])
        ],
        "eigen_terms": top_terms(eigen),
        "claim_boundary": "scout-packet-only; model output is not proof",
        "response_contract": {
            "format": "strict_json",
            "must_include": task["required_fields"] + ["claim_boundary", "next_receipts"],
            "must_not_claim": ["solved", "proved", "optimality_certified"],
        },
    }
    packet["packet_hash"] = sha256_json(packet)
    return packet


def make_curriculum(packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    system = "You are ZAYA acting as a moving-sofa scout. Return strict JSON; never certify proof."
    records = []
    for packet in packets:
        answer = {
            "selected": True,
            "route": "zaya_scout",
            "task_id": packet["task_id"],
            "claim_boundary": packet["claim_boundary"],
            "required_response_fields": packet["required_response_fields"],
            "next_receipts": ["source_excerpt", "formal_or_solver_check", "metaprobe_audit"],
            "packet_hash": packet["packet_hash"],
        }
        records.append(
            {
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": json.dumps(packet, ensure_ascii=False)},
                    {"role": "assistant", "content": json.dumps(answer, ensure_ascii=False)},
                ]
            }
        )
    return records


def audit_packets(packets: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(packets)
    required_ok = 0
    boundary_ok = 0
    hash_ok = 0
    for packet in packets:
        contract = packet.get("response_contract", {})
        if packet.get("required_response_fields") and contract.get("must_include"):
            required_ok += 1
        if "not proof" in packet.get("claim_boundary", "") and packet.get("promotion_gate"):
            boundary_ok += 1
        expected_hash = packet.get("packet_hash")
        clone = dict(packet)
        clone.pop("packet_hash", None)
        if expected_hash == sha256_json(clone):
            hash_ok += 1
    denom = total or 1
    resonance = (required_ok / denom + boundary_ok / denom + hash_ok / denom) / 3
    return {
        "packet_count": total,
        "required_ok": required_ok,
        "boundary_ok": boundary_ok,
        "hash_ok": hash_ok,
        "resonance": resonance,
        "lawful": resonance >= 0.95,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prior", type=Path, default=DEFAULT_PRIOR)
    parser.add_argument("--router", type=Path, default=DEFAULT_ROUTER)
    parser.add_argument("--eigen", type=Path, default=DEFAULT_EIGEN)
    parser.add_argument("--receipt", type=Path, default=Path("4-Infrastructure/shim/moving_sofa_scout_harness_receipt.json"))
    parser.add_argument("--packets", type=Path, default=Path("4-Infrastructure/shim/moving_sofa_scout_packets.jsonl"))
    parser.add_argument("--curriculum", type=Path, default=Path("4-Infrastructure/shim/moving_sofa_scout_harness_curriculum.jsonl"))
    args = parser.parse_args()

    prior = load_json(args.prior)
    router = load_json(args.router)
    eigen = load_json(args.eigen)
    packets = [make_scout_packet(task, prior, router, eigen) for task in SCOUT_TASKS]
    audit = audit_packets(packets)
    receipt = {
        "schema": "moving_sofa_scout_harness_receipt_v1",
        "claim_boundary": "Scout packets prepare model-assisted decomposition; they do not solve or prove the moving sofa problem.",
        "source_prior": str(args.prior),
        "router_prior": str(args.router),
        "eigen_prior": str(args.eigen),
        "preferred_scout_model": router.get("preferred_scout_model", "Zyphra/ZAYA1-8B"),
        "audit": audit,
        "packets": packets,
        "lawful": audit["lawful"],
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with args.packets.open("w", encoding="utf-8") as handle:
        for packet in packets:
            handle.write(json.dumps(packet, ensure_ascii=False) + "\n")
    with args.curriculum.open("w", encoding="utf-8") as handle:
        for record in make_curriculum(packets):
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
