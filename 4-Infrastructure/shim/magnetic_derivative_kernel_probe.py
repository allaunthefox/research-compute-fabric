#!/usr/bin/env python3
"""Receipt-backed magnetic derivative kernel probe.

This probe adds a small magnetic-domain route surface for the cross-domain
kernel library. It admits only exact local algebra/vector fixtures and keeps
field-equation, gauge, boundary, and material-model claims in HOLD.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "magnetic_derivative_kernels"
REGISTRY = OUT_DIR / "magnetic_derivative_kernel_registry.json"
RECEIPT = OUT_DIR / "magnetic_derivative_kernel_receipt.json"
SUMMARY = OUT_DIR / "magnetic_derivative_kernel.md"

SOURCE_REFS = [
    REPO / "shared-data/data/mass_number_transform_registry/mass_number_transform_registry_receipt.json",
    REPO / "shared-data/data/cross_domain_kernel_adapters/cross_domain_kernel_adapter_registry_receipt.json",
]


Vector = tuple[Fraction, Fraction, Fraction]


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


def frac_payload(value: Fraction | Vector) -> Any:
    if isinstance(value, tuple):
        return [frac_payload(item) for item in value]
    return {"numerator": value.numerator, "denominator": value.denominator, "decimal": float(value)}


def mn(a: Fraction, b: Fraction) -> Fraction:
    return (a - b) / (a + b)


def magnetic_pressure(B: Fraction, mu: Fraction) -> Fraction:
    return B * B / (2 * mu)


def d_magnetic_pressure_dB(B: Fraction, mu: Fraction) -> Fraction:
    return B / mu


def scalar_dipole_force(moment: Fraction, dBdx: Fraction) -> Fraction:
    return moment * dBdx


def cross(a: Vector, b: Vector) -> Vector:
    ax, ay, az = a
    bx, by, bz = b
    return ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx


def lorentz_magnetic_force(charge: Fraction, velocity: Vector, B: Vector) -> Vector:
    vxB = cross(velocity, B)
    return tuple(charge * item for item in vxB)  # type: ignore[return-value]


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
    magnetic_role: str,
    compressed_form: str,
    expanded_form: str,
    checks: list[dict[str, Any]],
    decision: str,
    residual_policy: str,
) -> dict[str, Any]:
    item = {
        "entry_id": entry_id,
        "kernel_opcode": kernel_opcode,
        "magnetic_role": magnetic_role,
        "compressed_form": compressed_form,
        "expanded_form": expanded_form,
        "checks": checks,
        "all_checks_pass": all(check.get("pass", False) for check in checks) if checks else None,
        "decision": decision,
        "residual_policy": residual_policy,
        "claim_boundary": "magnetic route fixture only; not a Maxwell solver or material model",
    }
    item["entry_hash"] = hash_obj({k: v for k, v in item.items() if k != "entry_hash"})
    return item


def build_registry() -> dict[str, Any]:
    B = Fraction(3)
    mu = Fraction(2)
    moment = Fraction(5)
    dBdx = Fraction(7, 3)
    charge = Fraction(2)
    velocity: Vector = (Fraction(1), Fraction(2), Fraction(3))
    field: Vector = (Fraction(5), Fraction(-1), Fraction(4))
    mu1 = Fraction(3)
    mu2 = Fraction(8)

    entries = [
        entry(
            entry_id="magnetic_pressure_derivative",
            kernel_opcode="DERIV_QUADRATIC",
            magnetic_role="local derivative of magnetic pressure density with respect to field magnitude",
            compressed_form="d/dB [B^2/(2*mu)] = B/mu",
            expanded_form="P_B = B^2/(2*mu)",
            checks=[
                check_equal(
                    "dP_dB_B3_mu2",
                    d_magnetic_pressure_dB(B, mu),
                    (magnetic_pressure(B + Fraction(1), mu) - magnetic_pressure(B - Fraction(1), mu)) / 2,
                )
            ],
            decision="ACCEPT_DERIVATIVE_FIXTURE",
            residual_policy="scalar uniform-mu fixture only; spatial fields require gradient, units, geometry, and boundary receipts",
        ),
        entry(
            entry_id="scalar_dipole_gradient_force",
            kernel_opcode="DERIV_LINEAR",
            magnetic_role="one-dimensional projection of dipole force from potential gradient",
            compressed_form="F_x = m * dB/dx",
            expanded_form="U = -m*B(x); F_x = -dU/dx",
            checks=[check_equal("dipole_force_m5_dBdx7_3", scalar_dipole_force(moment, dBdx), Fraction(35, 3))],
            decision="ACCEPT_DERIVATIVE_FIXTURE",
            residual_policy="1D aligned-dipole fixture only; vector dipole orientation and material response require adapter receipts",
        ),
        entry(
            entry_id="lorentz_magnetic_cross_product",
            kernel_opcode="CROSS_PRODUCT",
            magnetic_role="magnetic part of Lorentz force as a vector cross-product kernel",
            compressed_form="F_B = q * cross(v,B)",
            expanded_form="F = q*(v x B)",
            checks=[
                check_equal(
                    "lorentz_q2_v123_B5neg14",
                    lorentz_magnetic_force(charge, velocity, field),
                    (Fraction(22), Fraction(22), Fraction(-22)),
                )
            ],
            decision="ACCEPT_VECTOR_FIXTURE",
            residual_policy="magnetic-only vector fixture; electric field term, relativistic conventions, and units remain adapter data",
        ),
        entry(
            entry_id="permeability_boundary_contrast",
            kernel_opcode="MN_REFLECT",
            magnetic_role="two-permeability boundary contrast candidate",
            compressed_form="Gamma_mu = MN(mu2,mu1)",
            expanded_form="Gamma_mu = (mu2-mu1)/(mu2+mu1)",
            checks=[check_equal("mn_mu8_3", mn(mu2, mu1), Fraction(5, 11))],
            decision="ACCEPT_KERNEL_ADAPTER",
            residual_policy="exact contrast only; electromagnetic boundary conditions, orientation, and sign convention still require domain receipt",
        ),
        entry(
            entry_id="alfven_speed_route",
            kernel_opcode="ANALYTIC_SQRT_RATIO",
            magnetic_role="MHD speed route with square-root denominator",
            compressed_form="v_A = B / sqrt(mu*rho)",
            expanded_form="Alfven speed candidate",
            checks=[],
            decision="HOLD_ANALYTIC_ADAPTER",
            residual_policy="requires square-root precision, units, density/permeability source, and MHD assumptions",
        ),
        entry(
            entry_id="faraday_time_derivative",
            kernel_opcode="CURL_TIME_DERIVATIVE",
            magnetic_role="field equation route for induction",
            compressed_form="curl(E) = -dB/dt",
            expanded_form="Faraday induction law candidate",
            checks=[],
            decision="HOLD_FIELD_EQUATION",
            residual_policy="requires orientation, gauge/sign convention, boundary conditions, discretization, and source receipt",
        ),
        entry(
            entry_id="ampere_current_derivative",
            kernel_opcode="CURL_SOURCE_ADAPTER",
            magnetic_role="field equation route for current source",
            compressed_form="curl(B) -> mu*J plus displacement-current policy",
            expanded_form="Ampere-Maxwell route candidate",
            checks=[],
            decision="HOLD_FIELD_EQUATION",
            residual_policy="requires unit system, displacement-current policy, material model, boundary conditions, and source receipt",
        ),
        entry(
            entry_id="magnetic_susceptibility_contrast",
            kernel_opcode="MN",
            magnetic_role="bounded contrast over two susceptibilities or magnetizations",
            compressed_form="MN(chi2,chi1) or MN(M2,M1)",
            expanded_form="relative contrast between magnetic response lanes",
            checks=[],
            decision="HOLD_MATERIAL_ADAPTER",
            residual_policy="requires material law, linearity range, hysteresis policy, and measurement receipt",
        ),
    ]
    return {
        "schema": "magnetic_derivative_kernel_registry_v1",
        "claim_boundary": (
            "Magnetic derivative route registry only. Exact scalar/vector algebra "
            "fixtures may be accepted, but Maxwell/MHD/material claims stay HOLD "
            "until units, gauge/sign conventions, boundary conditions, source data, "
            "and residual policies are receipted."
        ),
        "canonical_statement": (
            "Magnetic equations expose reusable derivative, contrast, and cross-product "
            "kernels, but field truth lives behind adapter closure."
        ),
        "entries": entries,
        "entry_count": len(entries),
        "status_counts": {
            status: sum(1 for item in entries if item["decision"] == status)
            for status in sorted({item["decision"] for item in entries})
        },
    }


def build_receipt(registry: dict[str, Any]) -> dict[str, Any]:
    accepted_statuses = {"ACCEPT_DERIVATIVE_FIXTURE", "ACCEPT_VECTOR_FIXTURE", "ACCEPT_KERNEL_ADAPTER"}
    accepted_checks_pass = all(
        item["all_checks_pass"] is True
        for item in registry["entries"]
        if item["decision"] in accepted_statuses
    )
    receipt = {
        "schema": "magnetic_derivative_kernel_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "registry_path": rel(REGISTRY),
        "registry_hash": hash_obj(registry),
        "source_refs": [source_ref(path) for path in SOURCE_REFS],
        "entry_count": registry["entry_count"],
        "status_counts": registry["status_counts"],
        "accepted_checks_pass": accepted_checks_pass,
        "decision": "HOLD_MAGNETIC_DOMAIN_WITH_ACCEPTED_FIXTURES" if accepted_checks_pass else "HOLD_DIAGNOSTIC",
        "claim_boundary": registry["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(registry: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# Magnetic Derivative Kernel Probe",
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
            f"`{item['decision']}` | {item['magnetic_role']} |"
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
