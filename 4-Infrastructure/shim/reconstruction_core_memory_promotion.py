#!/usr/bin/env python3
"""Promote the reconstruction-core ladder into project memory.

This writes a compact memory pointer, not a private Codex memory entry. It
follows the local OpenClaw/ENE memory-write rule: hashes, receipt paths, lawful
statuses, claim boundaries, and next-action pointers only.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "stack_memory_promotions"
MEMORY = OUT_DIR / "reconstruction_core_ladder_memory.json"
RECEIPT = OUT_DIR / "reconstruction_core_ladder_memory_receipt.json"
SUMMARY = OUT_DIR / "reconstruction_core_ladder_memory.md"

SOURCE_RECEIPTS = [
    REPO / "shared-data/data/enwiki9_logogram_targeter/enwiki9_logogram_targeter_receipt.json",
    REPO / "shared-data/data/enwiki9_logogram_xml_dict_probe/enwiki9_logogram_xml_dict_probe_receipt.json",
    REPO / "shared-data/data/enwiki9_logogram_receipt_aggregation_probe/enwiki9_logogram_receipt_aggregation_probe_receipt.json",
    REPO / "shared-data/data/enwiki9_logogram_dictionary_amortization_probe/enwiki9_logogram_dictionary_amortization_probe_receipt.json",
    REPO / "shared-data/data/enwiki9_logogram_canonical_baseline_probe/enwiki9_logogram_canonical_baseline_probe_receipt.json",
    REPO / "shared-data/data/language_surface_ambiguity_negative_control/language_surface_ambiguity_negative_control_receipt.json",
    REPO / "shared-data/data/foundation_forward_equation_compiler/foundation_forward_equation_compiler_receipt.json",
    REPO / "shared-data/data/buoyancy_added_mass_mobius/buoyancy_added_mass_mobius_receipt.json",
    REPO / "shared-data/data/mass_number_transform_registry/mass_number_transform_registry_receipt.json",
    REPO / "shared-data/data/cross_domain_kernel_adapters/cross_domain_kernel_adapter_registry_receipt.json",
    REPO / "shared-data/data/magnetic_derivative_kernels/magnetic_derivative_kernel_receipt.json",
    REPO / "shared-data/data/solids_physics_kernels/solids_physics_kernel_receipt.json",
    REPO / "shared-data/data/cross_domain_easy_wins/cross_domain_easy_wins_route_map_receipt.json",
]

SOURCE_DOCS = [
    REPO / "6-Documentation/docs/specs/DECODER_FACING_RECONSTRUCTION_CORE.md",
    REPO / "6-Documentation/docs/specs/LAW_GATED_RECONSTRUCTION_CORE_SHIFT.md",
    REPO / "6-Documentation/docs/specs/RECONSTRUCTION_CORE_MATH_REVIEW_2026_05_09.md",
    REPO / "6-Documentation/docs/specs/FORWARD_FOUNDATION_EQUATION_COMPILER.md",
    REPO / "6-Documentation/docs/safety/ANGRYSPHINX_ADAPTIVE_SHELL_DEFENSE.md",
    REPO / "0-Core-Formalism/otom/docs/safety/ANGRYSPHINX_ADAPTIVE_SHELL_DEFENSE.md",
]


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_hash(path: Path) -> str | None:
    return sha256_bytes(path.read_bytes()) if path.exists() else None


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def source_ref(path: Path) -> dict[str, Any]:
    return {
        "path": rel(path),
        "exists": path.exists(),
        "sha256": file_hash(path),
    }


def build_memory() -> dict[str, Any]:
    return {
        "schema": "stack_memory_pointer_v1",
        "memory_key": "reconstruction_core_ladder_2026_05_09",
        "memory_kind": "receipt_backed_project_memory",
        "settlement_state": "FORMING",
        "lawful_status": "HOLD_TOP_LEVEL",
        "claim_boundary": (
            "Project-memory pointer only. This records the current reconstruction-core "
            "evidence ladder and guardrails; it is not a Hutter/LTCB result, not a "
            "canonical enwik9 result, and not a compression benchmark claim."
        ),
        "canonical_statement": (
            "The reconstruction-core ladder has replay-valid fixtures, a positive "
            "core-delta gate, a positive packet-delta gate, and one noncanonical "
            "global-positive fixture under dictionary amortization. Top-level "
            "promotion remains HOLD until canonical enwik9, baseline comparison, "
            "control filters, and full accounting pass. Godel's Gauntlet is the "
            "promotion/quarantine gate that blocks self-handwave; Buffalo-style "
            "same-surface language instances require typed replay or residuals. "
            "The forward-foundation compiler blocks backward theorem-label trust: "
            "external equation names route only as hints until they compile from F0 "
            "with closure, residual accounting, and receipts. The v5 canonical "
            "baseline probe freezes the codec and adds provenance plus baseline "
            "gates; the available local input remains a fixture and currently "
            "lands at HOLD_GLOBAL. The Mass Number transform registry records "
            "reusable exact algebraic kernels for ratio, pair, blend, reflection, "
            "binary-choice, and Mobius-load families as MN plus a small opcode; "
            "analytic entropy remains HOLD until precision and error policy are "
            "receipted. Cross-domain compression is adapter-gated kernel reuse: "
            "same algebraic skeleton does not imply same domain law, and couch "
            "contact topology or seismic horizon inference stay HOLD until their "
            "adapters close with replay, residuals, and receipts. Magnetic "
            "derivative kernels currently admit only exact local scalar/vector "
            "fixtures; Maxwell, MHD, gauge, material, and measurement claims stay "
            "HOLD until unit, boundary, source, and residual receipts exist. "
            "Solids physics currently admits local linear-elastic algebra fixtures "
            "and MN pair/boundary adapters; wave, plasticity, fracture, anisotropy, "
            "geometry, and material-model claims stay HOLD until their adapters "
            "close. The easy-wins route map ranks the next low-cost domains for "
            "exact local-algebra probes, with nonlinear, field, geometry, and "
            "measurement claims held until receipted."
        ),
        "gate_ladder": [
            {"gate": "G0_exact_replay", "status": "PASS_FIXTURE"},
            {"gate": "G1_delta_core_positive", "status": "PASS_FIXTURE"},
            {"gate": "G2_delta_packet_positive", "status": "PASS_FIXTURE"},
            {"gate": "G3_delta_global_positive", "status": "ADMIT_FIXTURE_NONCANONICAL_ONLY"},
            {"gate": "G4_canonical_enwik9_slice", "status": "HOLD"},
            {"gate": "G5_baseline_comparison", "status": "HOLD"},
            {"gate": "G6_corpus_scale_hutter_accounting", "status": "HOLD"},
        ],
        "guardrails": [
            {
                "name": "Godels_Gauntlet",
                "role": "promotion_quarantine_gate",
                "rule": "the stack may propose and defend, but may not promote itself without receipts",
            },
            {
                "name": "Buffalo_surface_collision",
                "role": "same_surface_role_guardrail",
                "rule": "same visible token is not same atom unless role, position, case, and replay order are preserved or residualized",
            },
            {
                "name": "flown_by_cancellation",
                "role": "invalid_derivation_guardrail",
                "rule": "correct output is not proof of a lawful operator",
            },
            {
                "name": "Mass_Number_opcode_registry",
                "role": "symbolic_compression_kernel",
                "rule": "exact pair/ratio/blend/reflection families may compress to MN plus opcode; analytic transforms stay HOLD until error policy is receipted",
            },
            {
                "name": "Cross_domain_adapter_gate",
                "role": "analogy_to_law_boundary",
                "rule": "shared kernels may be reused across domains only through adapters with replay, residual policy, and closure receipts",
            },
            {
                "name": "Magnetic_derivative_gate",
                "role": "field_equation_boundary",
                "rule": "local derivative and cross-product fixtures may be accepted, but Maxwell/MHD/material claims stay HOLD until units, boundaries, sources, and residuals are receipted",
            },
            {
                "name": "Solids_physics_gate",
                "role": "material_law_boundary",
                "rule": "local linear-elastic fixtures may be accepted, but wave, plasticity, fracture, anisotropy, geometry, and material claims stay HOLD until receipted",
            },
            {
                "name": "Easy_wins_route_map",
                "role": "probe_queue",
                "rule": "prioritize exact local algebra in circuits, thermal, acoustics, probability, two-body, chemistry, optics, statistics, biology, and contact routes",
            },
        ],
        "source_receipts": [source_ref(path) for path in SOURCE_RECEIPTS],
        "source_docs": [source_ref(path) for path in SOURCE_DOCS],
        "next_action_pointer": "Find or construct canonical enwik9, verify size/checksum, then run frozen v5 on canonical slices.",
        "memory_write_rule": "write only hashes, receipt paths, lawful statuses, claim boundaries, and next-action pointers; never raw secrets",
    }


def build_receipt(memory: dict[str, Any]) -> dict[str, Any]:
    memory_hash = sha256_bytes(stable_json(memory).encode("utf-8"))
    receipt = {
        "schema": "stack_memory_promotion_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "memory_key": memory["memory_key"],
        "memory_path": rel(MEMORY),
        "memory_hash": memory_hash,
        "source_receipt_paths": [item["path"] for item in memory["source_receipts"]],
        "source_doc_paths": [item["path"] for item in memory["source_docs"]],
        "lawful_status": memory["lawful_status"],
        "claim_boundary": memory["claim_boundary"],
        "next_action_pointer": memory["next_action_pointer"],
        "decision": "PROMOTE_TO_PROJECT_MEMORY",
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(memory: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# Reconstruction Core Ladder Memory",
        "",
        f"Memory key: `{memory['memory_key']}`  ",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        memory["claim_boundary"],
        "",
        "## Canonical Statement",
        "",
        memory["canonical_statement"],
        "",
        "## Gate Ladder",
        "",
        "| Gate | Status |",
        "|---|---|",
    ]
    for gate in memory["gate_ladder"]:
        lines.append(f"| `{gate['gate']}` | `{gate['status']}` |")
    lines.extend(["", "## Guardrails", "", "| Name | Role | Rule |", "|---|---|---|"])
    for guardrail in memory["guardrails"]:
        lines.append(f"| `{guardrail['name']}` | `{guardrail['role']}` | {guardrail['rule']} |")
    lines.extend(["", "## Next Action", "", memory["next_action_pointer"]])
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    memory = build_memory()
    receipt = build_receipt(memory)
    MEMORY.write_text(json.dumps(memory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(memory, receipt)
    print(
        json.dumps(
            {
                "memory": rel(MEMORY),
                "summary": rel(SUMMARY),
                "receipt": rel(RECEIPT),
                "receipt_hash": receipt["receipt_hash"],
                "decision": receipt["decision"],
                "lawful_status": memory["lawful_status"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
