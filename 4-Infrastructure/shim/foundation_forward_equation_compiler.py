#!/usr/bin/env python3
"""Emit the forward-foundation equation compiler contract.

This is a receipt-bearing contract, not a proof engine. It records the local
rule that theorem names, expert labels, citations, and logogram names are
routing hints only. A trusted equation atom must compile forward from the
foundation kernel and carry closure, residual, budget, and receipt evidence.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "foundation_forward_equation_compiler"
KERNEL = OUT_DIR / "foundation_kernel_f0.json"
ATOMS = OUT_DIR / "foundation_equation_atoms.json"
RECEIPT = OUT_DIR / "foundation_forward_equation_compiler_receipt.json"
SUMMARY = OUT_DIR / "foundation_forward_equation_compiler.md"

SOURCE_DOCS = [
    REPO / "6-Documentation/docs/specs/DECODER_FACING_RECONSTRUCTION_CORE.md",
    REPO / "6-Documentation/docs/specs/OMINDIRECTION_LOGOGRAM_DESIGN_AND_COMPILER.md",
    REPO / "6-Documentation/docs/specs/GCCL_ENCODING_CONTRACT.md",
    REPO / "shared-data/data/stack_memory_promotions/reconstruction_core_ladder_memory_receipt.json",
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


def hash_obj(obj: Any) -> str:
    return sha256_bytes(stable_json(obj).encode("utf-8"))


def build_kernel() -> dict[str, Any]:
    return {
        "schema": "foundation_kernel_f0_v1",
        "kernel_id": "F0_forward_foundation_kernel",
        "claim_boundary": (
            "Forward compiler foundation only. This is not a proof that derived "
            "equations are true and not a benchmark claim. Human theorem labels, "
            "citations, expert names, and logogram names are routing hints only."
        ),
        "canonical_rule": "No backward trust chain. Only forward admissible generation.",
        "origin_metadata_doctrine": {
            "canonical_statement": "Origin may inspire. Only closure admits.",
            "joke_boundary": "No vibes-to-axioms pipeline without a receipt.",
            "rule": (
                "Human origin, era context, institution, biography, altered-state suspicion, "
                "aesthetic elegance, and theorem labels are metadata only. They may route a "
                "candidate, but they cannot promote it."
            ),
            "careful_nonclaim": (
                "This does not claim that unusual historical, cultural, or personal origins "
                "invalidate an equation. It only says origin stories are not receipts."
            ),
            "metadata_fields": {
                "human_origin": "metadata_only",
                "era_context": "metadata_only",
                "institutional_prestige": "metadata_only",
                "theorem_label": "routing_hint_only",
                "aesthetic_elegance": "routing_hint_only",
                "accepted_result": "hold_until_forward_receipted",
                "formal_closure": "admission_candidate",
            },
        },
        "foundation_set": [
            {
                "symbol": "O4",
                "name": "four_primitives",
                "meaning": "field, shear, packet, spectral",
            },
            {
                "symbol": "SD",
                "name": "dimensional_shell",
                "meaning": "projection plus residual plus closure shell",
            },
            {
                "symbol": "MN",
                "name": "mass_number",
                "meaning": "metric weight and admissibility pressure",
            },
            {
                "symbol": "gamma_star",
                "name": "geodesic_projection",
                "meaning": "shortest lawful projection path under declared costs",
            },
            {
                "symbol": "H_dV",
                "name": "information_horizon",
                "meaning": "entropy and Underverse boundary",
            },
            {
                "symbol": "Omega",
                "name": "torsion_shear_event_correction",
                "meaning": "deformation and event-order accounting",
            },
            {
                "symbol": "Lambda",
                "name": "logogram_substitution",
                "meaning": "callable abstraction atom",
            },
            {
                "symbol": "A",
                "name": "admission_gate",
                "meaning": "ACCEPT, HOLD, or QUARANTINE decision",
            },
        ],
        "shell_equation": {
            "id": "SD_no_infinity_shell",
            "display": "SD = L4(O4) + L3(Rg3) + chi0 + U4 + E_HD + U_under",
            "terms": {
                "SD": "source object in its full domain dimension",
                "O4": "visible four-primitive projection",
                "Rg3": "genus-3 residual shadow",
                "chi0": "closure witness",
                "U4": "unseen but promotable reserve",
                "E_HD": "high-dimensional projection energy tax",
                "U_under": "Underverse lane for forbidden, failed, entropy-bound, or non-promotable residue",
            },
        },
        "admission_equation": {
            "id": "forward_equation_acceptance",
            "display": "ACCEPT(E) iff receipt_recomputes(E) and chi0(E)=0 and residual_declared(E) and B(E)<B_max and E_HD_paid(E)",
            "fail_lanes": ["HOLD", "QUARANTINE", "U_under", "NaN0"],
        },
        "pass_add_pause_subtract": {
            "PASS": "verify byte-exact or payload-exact replay plus hashes",
            "ADD": "add deterministic core, residual, receipt, protocol, dictionary, and energy costs",
            "PAUSE": "zero-delta logical event fence; wall-clock time is metadata only",
            "SUBTRACT": "compute deltas after costs are sealed",
        },
    }


def equation_atom(
    *,
    equation_id: str,
    semantic_key: str,
    canonical_equation: str,
    parent_equations: list[str],
    transform_rule: str,
    projection: dict[str, Any],
    domain_laws: list[str],
    decision: str,
    residual_policy: str,
) -> dict[str, Any]:
    identity = {
        "equation_id": equation_id,
        "semantic_key": semantic_key,
        "canonical_equation": canonical_equation,
    }
    identity["equation_hash"] = hash_obj(identity)
    dependency_hash = hash_obj(
        {
            "source_kernel": "F0_forward_foundation_kernel",
            "parent_equations": parent_equations,
            "transform_rule": transform_rule,
        }
    )
    receipt_payload = {
        "identity": identity,
        "dependency_hash": dependency_hash,
        "projection": projection,
        "domain_laws": domain_laws,
        "decision": decision,
        "residual_policy": residual_policy,
    }
    return {
        "identity": identity,
        "foundation": {
            "source_kernel": "F0_forward_foundation_kernel",
            "parent_equations": parent_equations,
            "transform_rule": transform_rule,
            "dependency_hash": dependency_hash,
        },
        "projection": projection,
        "admissibility": {
            "domain_laws": domain_laws,
            "dimensional_scaling": "declared_or_hold",
            "energy_budget": "E_HD_must_be_paid_or_hold",
            "information_budget": "H_dV_boundary_must_be_declared_or_hold",
            "closure_status": "closed_only_if_chi0_zero",
            "residual_policy": residual_policy,
        },
        "receipt": {
            "source_hash": "F0",
            "equation_hash": identity["equation_hash"],
            "dependency_hash": dependency_hash,
            "receipt_hash": hash_obj(receipt_payload),
            "decision": decision,
        },
    }


def build_atoms() -> dict[str, Any]:
    atoms = [
        equation_atom(
            equation_id="F1_dimensional_shell",
            semantic_key="foundation.shell.no_infinity",
            canonical_equation="SD = L4(O4) + L3(Rg3) + chi0 + U4 + E_HD + U_under",
            parent_equations=["F0_forward_foundation_kernel"],
            transform_rule="declare_shell_terms",
            projection={
                "O4": "visible_projection",
                "Rg3": "bounded_residual_shadow",
                "chi0": "closure_witness",
                "U4": "promotable_reserve",
                "E_HD": "projection_energy_tax",
                "Underverse": "non_promotable_entropy_lane",
            },
            domain_laws=["no_silent_infinity", "residual_declared", "closure_required_for_accept"],
            decision="ACCEPT_CONTRACT",
            residual_policy="all non-closed material routes to U_under, HOLD, QUARANTINE, or NaN0",
        ),
        equation_atom(
            equation_id="F2_mass_number_metric",
            semantic_key="foundation.mass_number.metric_pressure",
            canonical_equation="MN -> g_MN",
            parent_equations=["F1_dimensional_shell"],
            transform_rule="derive_metric_pressure_from_mass_number",
            projection={
                "O4": "metric-visible pressure",
                "Rg3": "unclosed metric residual",
                "chi0": "metric closure witness",
                "U4": "candidate metric reserves",
                "E_HD": "metric projection cost",
                "Underverse": "metric category errors",
            },
            domain_laws=["mass_is_not_distance_until_admissibility_closure", "category_errors_hold"],
            decision="ACCEPT_CONTRACT",
            residual_policy="raw mass-number divergence must carry typed residuals until closed",
        ),
        equation_atom(
            equation_id="F3_geodesic_projection",
            semantic_key="foundation.geodesic.shortest_lawful_path",
            canonical_equation="gamma_star = argmin(path_cost + E_HD + H_dV_cost)",
            parent_equations=["F2_mass_number_metric"],
            transform_rule="select_shortest_lawful_projection_path",
            projection={
                "O4": "selected visible path",
                "Rg3": "path shadow residual",
                "chi0": "path closure witness",
                "U4": "unselected lawful alternates",
                "E_HD": "path projection energy",
                "Underverse": "forbidden or entropy-bound paths",
            },
            domain_laws=["costs_declared", "forbidden_paths_do_not_promote", "event_order_preserved"],
            decision="ACCEPT_CONTRACT",
            residual_policy="unselected or forbidden route material remains residual or Underverse",
        ),
        equation_atom(
            equation_id="F4_logogram_abstraction",
            semantic_key="foundation.logogram.callable_atom",
            canonical_equation="O4 + Rg3 -> Lambda -> D_lambda(theta) + r -> chi0",
            parent_equations=["F3_geodesic_projection"],
            transform_rule="promote_repeated_lawful_structure_to_callable_atom",
            projection={
                "O4": "visible callable surface",
                "Rg3": "abstraction residual",
                "chi0": "rehydration closure witness",
                "U4": "future promotable motifs",
                "E_HD": "abstraction and replay cost",
                "Underverse": "same-surface collisions and invalid cancellations",
            },
            domain_laws=["payload_not_glyph", "same_surface_not_same_atom", "correct_output_not_operator_proof"],
            decision="ACCEPT_CONTRACT",
            residual_policy="payload, orientation, placement, role, and replay order must be preserved or residualized",
        ),
        equation_atom(
            equation_id="F5_admission_gate",
            semantic_key="foundation.admission.accept_hold_quarantine",
            canonical_equation="A(E) = ACCEPT iff receipt_recomputes and chi0=0 and residual_declared and B<B_max and E_HD_paid",
            parent_equations=["F4_logogram_abstraction"],
            transform_rule="apply_godel_gauntlet",
            projection={
                "O4": "accepted interface state",
                "Rg3": "declared residual state",
                "chi0": "zero closure defect",
                "U4": "deferred admissible reserve",
                "E_HD": "paid projection cost",
                "Underverse": "failed, forbidden, or overclaim lane",
            },
            domain_laws=["no_backward_trust_chain", "forward_receipt_required", "timestamps_metadata_only"],
            decision="ACCEPT_CONTRACT",
            residual_policy="anything not compiled and receipted from F0 stays HOLD or routes to quarantine lanes",
        ),
    ]
    return {
        "schema": "foundation_equation_atoms_v1",
        "kernel_id": "F0_forward_foundation_kernel",
        "atoms": atoms,
        "atom_count": len(atoms),
        "decision": "ACCEPT_CONTRACT_HOLD_RESULTS",
        "claim_boundary": (
            "These atoms define the forward compiler contract. They do not promote "
            "external equations, theorem labels, citations, or benchmark claims."
        ),
    }


def build_receipt(kernel: dict[str, Any], atoms: dict[str, Any]) -> dict[str, Any]:
    kernel_hash = hash_obj(kernel)
    atoms_hash = hash_obj(atoms)
    pass_gate = {
        "gate": "PASS",
        "kernel_hash": kernel_hash,
        "atoms_hash": atoms_hash,
        "source_docs": [source_ref(path) for path in SOURCE_DOCS],
        "exact_replay": True,
        "clock_participates_in_hash": False,
    }
    add_gate = {
        "gate": "ADD",
        "foundation_symbol_count": len(kernel["foundation_set"]),
        "equation_atom_count": atoms["atom_count"],
        "source_doc_count": len(SOURCE_DOCS),
    }
    state_before_pause = hash_obj({"pass": pass_gate, "add": add_gate})
    pause_gate = {
        "gate": "PAUSE",
        "event_index": 3,
        "delta_bytes": 0,
        "state_root_before": state_before_pause,
        "state_root_after": state_before_pause,
        "clock_participates_in_hash": False,
    }
    subtract_gate = {
        "gate": "SUBTRACT",
        "trusted_backward_labels": 0,
        "trusted_forward_contract_atoms": atoms["atom_count"],
        "uncompiled_equation_default": "HOLD",
    }
    receipt = {
        "schema": "foundation_forward_equation_compiler_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "kernel_path": rel(KERNEL),
        "kernel_hash": kernel_hash,
        "atoms_path": rel(ATOMS),
        "atoms_hash": atoms_hash,
        "gates": [pass_gate, add_gate, pause_gate, subtract_gate],
        "source_docs": [source_ref(path) for path in SOURCE_DOCS],
        "decision": "ACCEPT_CONTRACT_HOLD_RESULTS",
        "claim_boundary": kernel["claim_boundary"],
        "canonical_statement": kernel["canonical_rule"],
        "origin_metadata_doctrine": kernel["origin_metadata_doctrine"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(kernel: dict[str, Any], atoms: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# Foundation Forward Equation Compiler",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        kernel["claim_boundary"],
        "",
        "## Canonical Rule",
        "",
        "```text",
        kernel["canonical_rule"],
        "```",
        "",
        "## Origin Metadata Doctrine",
        "",
        kernel["origin_metadata_doctrine"]["careful_nonclaim"],
        "",
        "```text",
        kernel["origin_metadata_doctrine"]["canonical_statement"],
        kernel["origin_metadata_doctrine"]["joke_boundary"],
        "```",
        "",
        kernel["origin_metadata_doctrine"]["rule"],
        "",
        "## Foundation Set",
        "",
        "| Symbol | Name | Meaning |",
        "|---|---|---|",
    ]
    for item in kernel["foundation_set"]:
        lines.append(f"| `{item['symbol']}` | `{item['name']}` | {item['meaning']} |")
    lines.extend(
        [
            "",
            "## Shell Equation",
            "",
            "```text",
            kernel["shell_equation"]["display"],
            "```",
            "",
            "## Forward Atoms",
            "",
            "| Equation | Decision | Rule |",
            "|---|---|---|",
        ]
    )
    for atom in atoms["atoms"]:
        lines.append(
            f"| `{atom['identity']['equation_id']}` | `{atom['receipt']['decision']}` | "
            f"{atom['foundation']['transform_rule']} |"
        )
    lines.extend(
        [
            "",
            "## Gate Loop",
            "",
            "```text",
            "PASS -> ADD -> PAUSE -> SUBTRACT => ACCEPT_CONTRACT/HOLD_RESULTS",
            "```",
            "",
            "Anything that cannot compile forward from `F0_forward_foundation_kernel` remains `HOLD`, `QUARANTINE`, `U_under`, or `NaN0`.",
        ]
    )
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    kernel = build_kernel()
    atoms = build_atoms()
    receipt = build_receipt(kernel, atoms)
    KERNEL.write_text(json.dumps(kernel, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    ATOMS.write_text(json.dumps(atoms, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(kernel, atoms, receipt)
    print(
        json.dumps(
            {
                "kernel": rel(KERNEL),
                "atoms": rel(ATOMS),
                "receipt": rel(RECEIPT),
                "summary": rel(SUMMARY),
                "receipt_hash": receipt["receipt_hash"],
                "decision": receipt["decision"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
