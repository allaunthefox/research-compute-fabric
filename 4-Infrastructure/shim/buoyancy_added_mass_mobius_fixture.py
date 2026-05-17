#!/usr/bin/env python3
"""Emit a receipt for the buoyancy added-mass Mobius logogram fixture.

This records a small forward-derived physics atom:

    lambda_BAM(x, C) = g * alpha_C * x / (1 + kappa_C * x)

where x is the density Mass Number / Atwood contrast. The fixture checks
algebraic equivalence against the classical added-mass expression and records
the light-object boundedness correction as a claim boundary.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "buoyancy_added_mass_mobius"
ATOM = OUT_DIR / "buoyancy_added_mass_mobius_atom.json"
RECEIPT = OUT_DIR / "buoyancy_added_mass_mobius_receipt.json"
SUMMARY = OUT_DIR / "buoyancy_added_mass_mobius.md"

SOURCE_REFS = [
    REPO / "shared-data/data/foundation_forward_equation_compiler/foundation_forward_equation_compiler_receipt.json",
]


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_obj(obj: Any) -> str:
    return sha256_bytes(stable_json(obj).encode("utf-8"))


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def file_hash(path: Path) -> str | None:
    return sha256_bytes(path.read_bytes()) if path.exists() else None


def source_ref(path: Path) -> dict[str, Any]:
    return {"path": rel(path), "exists": path.exists(), "sha256": file_hash(path)}


def mass_number(rho_o: Fraction, rho_m: Fraction) -> Fraction:
    return (rho_o - rho_m) / (rho_o + rho_m)


def added_mass_a_over_g(rho_o: Fraction, rho_m: Fraction, c_shape: Fraction) -> Fraction:
    return (rho_o - rho_m) / (rho_o + c_shape * rho_m)


def alpha(c_shape: Fraction) -> Fraction:
    return Fraction(2, 1) / (Fraction(1, 1) + c_shape)


def kappa(c_shape: Fraction) -> Fraction:
    return (Fraction(1, 1) - c_shape) / (Fraction(1, 1) + c_shape)


def mobius_a_over_g(x: Fraction, c_shape: Fraction) -> Fraction:
    return alpha(c_shape) * x / (Fraction(1, 1) + kappa(c_shape) * x)


def inverse_mass_number(a_over_g: Fraction, c_shape: Fraction) -> Fraction:
    return a_over_g / (alpha(c_shape) - kappa(c_shape) * a_over_g)


def frac_payload(value: Fraction) -> dict[str, Any]:
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "decimal": float(value),
    }


def check_case(name: str, rho_ratio: Fraction, c_shape: Fraction) -> dict[str, Any]:
    rho_m = Fraction(1, 1)
    rho_o = rho_ratio * rho_m
    x = mass_number(rho_o, rho_m)
    direct = added_mass_a_over_g(rho_o, rho_m, c_shape)
    compressed = mobius_a_over_g(x, c_shape)
    inverted = inverse_mass_number(compressed, c_shape)
    return {
        "name": name,
        "rho_o_over_rho_m": frac_payload(rho_ratio),
        "C": frac_payload(c_shape),
        "MN_rho": frac_payload(x),
        "alpha_C": frac_payload(alpha(c_shape)),
        "kappa_C": frac_payload(kappa(c_shape)),
        "a_over_g_direct": frac_payload(direct),
        "a_over_g_mobius": frac_payload(compressed),
        "a_mps2_at_g_9_80665": float(compressed * Fraction(980665, 100000)),
        "inverse_MN_rho": frac_payload(inverted),
        "equivalence_pass": direct == compressed,
        "inverse_pass": inverted == x,
    }


def build_atom() -> dict[str, Any]:
    cases = [
        check_case("sphere_rho_ratio_2", Fraction(2, 1), Fraction(1, 2)),
        check_case("cylinder_perp_rho_ratio_2", Fraction(2, 1), Fraction(1, 1)),
        check_case("light_sphere_limit_probe", Fraction(0, 1), Fraction(1, 2)),
    ]
    identity = {
        "equation_id": "lambda_BAM_buoyancy_added_mass_mobius",
        "semantic_key": "fluid.early_time_buoyancy.added_mass.mobius",
        "canonical_equation": "a = g * alpha_C * MN_rho / (1 + kappa_C * MN_rho)",
        "expanded_equation": "a = g * (rho_o - rho_m) / (rho_o + C*rho_m)",
        "inverse_equation": "MN_rho = (a/g) / (alpha_C - kappa_C*(a/g))",
    }
    identity["equation_hash"] = hash_obj(identity)
    atom = {
        "schema": "forward_equation_fixture_atom_v1",
        "identity": identity,
        "foundation": {
            "source_kernel": "F0_forward_foundation_kernel",
            "parent_equations": [
                "F2_mass_number_metric",
                "F3_geodesic_projection",
                "F4_logogram_abstraction",
                "F5_admission_gate",
            ],
            "transform_rule": "density_contrast_plus_shape_load_to_mobius_projection",
            "dependency_hash": hash_obj(
                {
                    "source_kernel": "F0_forward_foundation_kernel",
                    "parents": ["F2", "F3", "F4", "F5"],
                    "rule": "density_contrast_plus_shape_load_to_mobius_projection",
                }
            ),
        },
        "projection": {
            "O4": ["MN_rho", "C", "g", "Gamma_shape"],
            "Rg3": ["drag", "vorticity", "boundary_effects"],
            "chi0": "0 only in early-time ideal added-mass regime",
            "U4": "later transient refinements",
            "E_HD": "C*rho_m carried-fluid inertia tax",
            "Underverse": "claims that ignore drag/vorticity/boundary domains or overstate boundedness",
        },
        "admissibility": {
            "domain_laws": [
                "early_time_before_drag_dominates",
                "added_mass_coefficient_declared",
                "density_contrast_uses_Atwood_form",
                "residual_lanes_declared",
                "bounded_by_g_only_for_heavier_sinking_branch_or_C_ge_1",
            ],
            "residual_policy": {
                "drag": "null only at early-time idealization; otherwise residual",
                "vorticity": "null only before shedding/circulation matters; otherwise residual",
                "boundary_effects": "null only for unbounded-domain approximation; otherwise residual",
            },
            "claim_boundary": (
                "Fixture-level algebraic compression of the classical added-mass "
                "early-time acceleration equation. This is not a new fluid theorem, "
                "not an experiment, and not a claim that |a| <= g for all density "
                "branches. For a light sphere in the ideal model, a/g tends to -2."
            ),
        },
        "checks": cases,
        "decision": "ACCEPT_FIXTURE_WITH_BOUND_CORRECTION",
    }
    receipt_payload = {
        "identity": atom["identity"],
        "foundation": atom["foundation"],
        "projection": atom["projection"],
        "checks": atom["checks"],
        "decision": atom["decision"],
    }
    atom["receipt"] = {
        "equation_hash": atom["identity"]["equation_hash"],
        "dependency_hash": atom["foundation"]["dependency_hash"],
        "receipt_hash": hash_obj(receipt_payload),
        "decision": atom["decision"],
    }
    return atom


def build_receipt(atom: dict[str, Any]) -> dict[str, Any]:
    all_checks_pass = all(item["equivalence_pass"] and item["inverse_pass"] for item in atom["checks"])
    receipt = {
        "schema": "buoyancy_added_mass_mobius_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "atom_path": rel(ATOM),
        "atom_hash": hash_obj(atom),
        "source_refs": [source_ref(path) for path in SOURCE_REFS],
        "all_equivalence_checks_pass": all_checks_pass,
        "decision": atom["decision"] if all_checks_pass else "HOLD_DIAGNOSTIC",
        "claim_boundary": atom["admissibility"]["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(atom: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# Buoyancy Added-Mass Mobius Fixture",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        receipt["claim_boundary"],
        "",
        "## Canonical Form",
        "",
        "```text",
        "MN_rho = (rho_o - rho_m) / (rho_o + rho_m)",
        "alpha_C = 2 / (1 + C)",
        "kappa_C = (1 - C) / (1 + C)",
        "lambda_BAM(MN_rho, C) = g * alpha_C * MN_rho / (1 + kappa_C * MN_rho)",
        "```",
        "",
        "Equivalent expanded form:",
        "",
        "```text",
        "a = g * (rho_o - rho_m) / (rho_o + C*rho_m)",
        "```",
        "",
        "Inverse:",
        "",
        "```text",
        "MN_rho = (a/g) / (alpha_C - kappa_C*(a/g))",
        "```",
        "",
        "## Checks",
        "",
        "| Case | C | MN_rho | a/g | a at g=9.80665 | Equivalence | Inverse |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in atom["checks"]:
        lines.append(
            f"| `{item['name']}` | {item['C']['decimal']:.6g} | "
            f"{item['MN_rho']['decimal']:.6g} | {item['a_over_g_mobius']['decimal']:.6g} | "
            f"{item['a_mps2_at_g_9_80665']:.6g} | {item['equivalence_pass']} | {item['inverse_pass']} |"
        )
    lines.extend(
        [
            "",
            "## Residual Lanes",
            "",
            "| Lane | Policy |",
            "|---|---|",
        ]
    )
    for lane, policy in atom["admissibility"]["residual_policy"].items():
        lines.append(f"| `{lane}` | {policy} |")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    atom = build_atom()
    receipt = build_receipt(atom)
    ATOM.write_text(json.dumps(atom, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(atom, receipt)
    print(
        json.dumps(
            {
                "atom": rel(ATOM),
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
