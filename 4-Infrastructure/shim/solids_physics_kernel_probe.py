#!/usr/bin/env python3
"""Receipt-backed solids-physics kernel probe.

This probe adds a small solids-domain route surface. It admits exact local
linear-elastic algebra fixtures and keeps anisotropy, plasticity, fracture,
wave-speed square roots, geometry, and boundary-value claims in HOLD.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "solids_physics_kernels"
REGISTRY = OUT_DIR / "solids_physics_kernel_registry.json"
RECEIPT = OUT_DIR / "solids_physics_kernel_receipt.json"
SUMMARY = OUT_DIR / "solids_physics_kernel.md"

SOURCE_REFS = [
    REPO / "shared-data/data/mass_number_transform_registry/mass_number_transform_registry_receipt.json",
    REPO / "shared-data/data/cross_domain_kernel_adapters/cross_domain_kernel_adapter_registry_receipt.json",
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


def frac_payload(value: Fraction | tuple[Fraction, ...]) -> Any:
    if isinstance(value, tuple):
        return [frac_payload(item) for item in value]
    return {"numerator": value.numerator, "denominator": value.denominator, "decimal": float(value)}


def mn(a: Fraction, b: Fraction) -> Fraction:
    return (a - b) / (a + b)


def hooke_stress(E: Fraction, strain: Fraction) -> Fraction:
    return E * strain


def elastic_energy_from_strain(E: Fraction, strain: Fraction) -> Fraction:
    return E * strain * strain / 2


def elastic_energy_from_stress(stress: Fraction, E: Fraction) -> Fraction:
    return stress * stress / (2 * E)


def d_energy_d_strain(E: Fraction, strain: Fraction) -> Fraction:
    return E * strain


def isotropic_shear_modulus(E: Fraction, nu: Fraction) -> Fraction:
    return E / (2 * (1 + nu))


def isotropic_bulk_modulus(E: Fraction, nu: Fraction) -> Fraction:
    return E / (3 * (1 - 2 * nu))


def harmonic_equal_thickness_modulus(E1: Fraction, E2: Fraction) -> Fraction:
    return 2 * E1 * E2 / (E1 + E2)


def harmonic_from_mn(total: Fraction, x: Fraction) -> Fraction:
    return total * (1 - x * x) / 2


def check_equal(name: str, compressed: Any, direct: Any) -> dict[str, Any]:
    return {
        "name": name,
        "compressed": frac_payload(compressed),
        "direct": frac_payload(direct),
        "pass": compressed == direct,
    }


def entry(
    *,
    entry_id: str,
    kernel_opcode: str,
    solids_role: str,
    compressed_form: str,
    expanded_form: str,
    checks: list[dict[str, Any]],
    decision: str,
    residual_policy: str,
) -> dict[str, Any]:
    item = {
        "entry_id": entry_id,
        "kernel_opcode": kernel_opcode,
        "solids_role": solids_role,
        "compressed_form": compressed_form,
        "expanded_form": expanded_form,
        "checks": checks,
        "all_checks_pass": all(check.get("pass", False) for check in checks) if checks else None,
        "decision": decision,
        "residual_policy": residual_policy,
        "claim_boundary": "solids route fixture only; not a finite-element solver or material model",
    }
    item["entry_hash"] = hash_obj({k: v for k, v in item.items() if k != "entry_hash"})
    return item


def build_registry() -> dict[str, Any]:
    E = Fraction(12)
    strain = Fraction(1, 4)
    stress = hooke_stress(E, strain)
    nu = Fraction(1, 4)
    E1 = Fraction(5)
    E2 = Fraction(3)
    total = E1 + E2
    x = mn(E1, E2)

    entries = [
        entry(
            entry_id="hooke_1d_stress",
            kernel_opcode="LINEAR_MAP",
            solids_role="one-dimensional linear elastic stress-strain map",
            compressed_form="sigma = E*epsilon",
            expanded_form="Hooke 1D linear elasticity",
            checks=[check_equal("sigma_E12_eps1_4", stress, Fraction(3))],
            decision="ACCEPT_LINEAR_ELASTIC_FIXTURE",
            residual_policy="small-strain 1D fixture only; tensor strain, boundary conditions, and material range require receipts",
        ),
        entry(
            entry_id="elastic_energy_density",
            kernel_opcode="DERIV_QUADRATIC",
            solids_role="quadratic elastic energy and conjugate stress derivative",
            compressed_form="U = E*epsilon^2/2; dU/depsilon = sigma",
            expanded_form="U = sigma*epsilon/2 = sigma^2/(2E)",
            checks=[
                check_equal("energy_strain_vs_stress", elastic_energy_from_strain(E, strain), elastic_energy_from_stress(stress, E)),
                check_equal("dU_deps_equals_sigma", d_energy_d_strain(E, strain), stress),
            ],
            decision="ACCEPT_DERIVATIVE_FIXTURE",
            residual_policy="linear-elastic scalar fixture only; path dependence and plastic work stay residualized",
        ),
        entry(
            entry_id="isotropic_moduli_transform",
            kernel_opcode="RATIONAL_MATERIAL_TRANSFORM",
            solids_role="Young/Poisson to shear and bulk modulus transform",
            compressed_form="G=E/(2*(1+nu)); K=E/(3*(1-2*nu))",
            expanded_form="isotropic linear elastic moduli relations",
            checks=[
                check_equal("G_E12_nu1_4", isotropic_shear_modulus(E, nu), Fraction(24, 5)),
                check_equal("K_E12_nu1_4", isotropic_bulk_modulus(E, nu), Fraction(8)),
            ],
            decision="ACCEPT_ISOTROPIC_FIXTURE",
            residual_policy="isotropic linear-elastic fixture only; anisotropy and near-incompressibility require domain receipts",
        ),
        entry(
            entry_id="equal_thickness_series_modulus",
            kernel_opcode="MN_PAIR_HARMONIC",
            solids_role="two-layer equal-thickness series effective modulus",
            compressed_form="E_eff = S/2*(1-MN(E1,E2)^2)",
            expanded_form="E_eff = 2*E1*E2/(E1+E2)",
            checks=[check_equal("series_E5_3", harmonic_from_mn(total, x), harmonic_equal_thickness_modulus(E1, E2))],
            decision="ACCEPT_KERNEL_ADAPTER",
            residual_policy="equal-thickness 1D series fixture only; laminate orientation, shear coupling, and boundary conditions require receipts",
        ),
        entry(
            entry_id="elastic_impedance_contrast",
            kernel_opcode="MN_REFLECT",
            solids_role="elastic/acoustic impedance contrast candidate at a solid boundary",
            compressed_form="Gamma_Z = MN(Z2,Z1)",
            expanded_form="Gamma_Z = (Z2-Z1)/(Z2+Z1)",
            checks=[check_equal("solid_impedance_mn_9_4", mn(Fraction(9), Fraction(4)), Fraction(5, 13))],
            decision="ACCEPT_KERNEL_ADAPTER",
            residual_policy="contrast identity only; wave mode, incidence angle, attenuation, and boundary conditions require receipts",
        ),
        entry(
            entry_id="longitudinal_wave_speed_route",
            kernel_opcode="ANALYTIC_SQRT_RATIO",
            solids_role="elastic wave-speed route",
            compressed_form="c = sqrt(E/rho) or tensor generalization",
            expanded_form="wave speed candidate",
            checks=[],
            decision="HOLD_ANALYTIC_ADAPTER",
            residual_policy="requires square-root precision, density/source receipts, mode convention, and material assumptions",
        ),
        entry(
            entry_id="von_mises_yield_route",
            kernel_opcode="STRESS_INVARIANT",
            solids_role="distortional-energy yield criterion route",
            compressed_form="sigma_vm = invariant(stress deviator)",
            expanded_form="von Mises candidate",
            checks=[],
            decision="HOLD_PLASTICITY_ADAPTER",
            residual_policy="requires tensor convention, yield surface, hardening law, loading path, and experimental/source receipt",
        ),
        entry(
            entry_id="fracture_toughness_route",
            kernel_opcode="ANALYTIC_SQRT_GEOMETRY",
            solids_role="crack-tip stress intensity route",
            compressed_form="K = Y*sigma*sqrt(pi*a)",
            expanded_form="linear elastic fracture mechanics candidate",
            checks=[],
            decision="HOLD_FRACTURE_ADAPTER",
            residual_policy="requires crack geometry, plane stress/strain convention, units, boundary conditions, and source receipt",
        ),
        entry(
            entry_id="anisotropic_stiffness_tensor_route",
            kernel_opcode="TENSOR_CONSTITUTIVE_ADAPTER",
            solids_role="anisotropic stiffness/compliance tensor route",
            compressed_form="sigma_ij = C_ijkl*epsilon_kl",
            expanded_form="anisotropic Hooke law candidate",
            checks=[],
            decision="HOLD_TENSOR_ADAPTER",
            residual_policy="requires tensor index convention, symmetry class, units, material source, and closure receipt",
        ),
    ]
    return {
        "schema": "solids_physics_kernel_registry_v1",
        "claim_boundary": (
            "Solids-physics route registry only. Exact local linear-elastic algebra "
            "fixtures may be accepted, but anisotropic, plasticity, fracture, wave, "
            "geometry, boundary-value, and material-model claims stay HOLD until "
            "source data, units, conventions, and residual policies are receipted."
        ),
        "canonical_statement": (
            "Solids physics exposes reusable linear maps, quadratic derivative "
            "kernels, rational modulus transforms, and MN boundary contrasts; "
            "material truth lives behind adapter closure."
        ),
        "entries": entries,
        "entry_count": len(entries),
        "status_counts": {
            status: sum(1 for item in entries if item["decision"] == status)
            for status in sorted({item["decision"] for item in entries})
        },
    }


def build_receipt(registry: dict[str, Any]) -> dict[str, Any]:
    accepted_statuses = {
        "ACCEPT_LINEAR_ELASTIC_FIXTURE",
        "ACCEPT_DERIVATIVE_FIXTURE",
        "ACCEPT_ISOTROPIC_FIXTURE",
        "ACCEPT_KERNEL_ADAPTER",
    }
    accepted_checks_pass = all(
        item["all_checks_pass"] is True
        for item in registry["entries"]
        if item["decision"] in accepted_statuses
    )
    receipt = {
        "schema": "solids_physics_kernel_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "registry_path": rel(REGISTRY),
        "registry_hash": hash_obj(registry),
        "source_refs": [source_ref(path) for path in SOURCE_REFS],
        "entry_count": registry["entry_count"],
        "status_counts": registry["status_counts"],
        "accepted_checks_pass": accepted_checks_pass,
        "decision": "HOLD_SOLIDS_DOMAIN_WITH_ACCEPTED_FIXTURES" if accepted_checks_pass else "HOLD_DIAGNOSTIC",
        "claim_boundary": registry["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(registry: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# Solids Physics Kernel Probe",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        registry["claim_boundary"],
        "",
        "## Canonical Statement",
        "",
        registry["canonical_statement"],
        "",
        "## Entry Table",
        "",
        "| Entry | Kernel | Decision | Role |",
        "|---|---|---|---|",
    ]
    for item in registry["entries"]:
        lines.append(
            f"| `{item['entry_id']}` | `{item['kernel_opcode']}` | "
            f"`{item['decision']}` | {item['solids_role']} |"
        )
    lines.extend(["", "## Guardrail", "", registry["claim_boundary"]])
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    registry = build_registry()
    receipt = build_receipt(registry)
    REGISTRY.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(registry, receipt)
    print(
        json.dumps(
            {
                "registry": rel(REGISTRY),
                "receipt": rel(RECEIPT),
                "summary": rel(SUMMARY),
                "receipt_hash": receipt["receipt_hash"],
                "decision": receipt["decision"],
                "status_counts": registry["status_counts"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
