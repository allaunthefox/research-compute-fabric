#!/usr/bin/env python3
"""Term-family eigen probe for the full Standard Model Lagrangian wall.

The source image is a compact Standard Model Lagrangian expansion. A physical
eigenvector would require an explicit operator, basis, gauge fixing, background,
renormalization scale, and boundary conditions. This probe instead builds a
receipt-bearing feature operator from visible term families and computes the
principal eigenvector of that coupling/interaction matrix.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "4-Infrastructure" / "hardware" / "standard_model_lagrangian_eigen_probe_receipt.json"
PHI = (1.0 + math.sqrt(5.0)) / 2.0


NODES = [
    "su3_gluon_field",
    "nonabelian_self_interaction",
    "electroweak_charged_w",
    "electroweak_neutral_za",
    "higgs_goldstone_scalar",
    "scalar_potential",
    "fermion_quark_sector",
    "fermion_lepton_sector",
    "yukawa_mass_coupling",
    "charged_current_ckm",
    "ghost_gaugefix_sector",
    "derivative_kinetic_flow",
]


# Manual term-family observations from the visible Lagrangian wall. These are
# not physical coupling constants; they are a compact feature grammar for the
# printed expansion.
OBSERVATIONS: list[tuple[str, str, float, str]] = [
    ("su3_gluon_field", "nonabelian_self_interaction", 8.0, "G kinetic, g_s f GGG, and g_s^2 f f GGGG terms"),
    ("su3_gluon_field", "derivative_kinetic_flow", 5.0, "partial_mu G partial^mu G and derivative gluon terms"),
    ("electroweak_charged_w", "nonabelian_self_interaction", 7.0, "W+ W- cubic and quartic gauge self terms"),
    ("electroweak_charged_w", "electroweak_neutral_za", 9.0, "A/Z with W+ W- mixing and c_w/s_w factors"),
    ("electroweak_neutral_za", "derivative_kinetic_flow", 6.0, "Z/A derivative kinetic and mixed derivative terms"),
    ("electroweak_charged_w", "derivative_kinetic_flow", 6.0, "W derivative kinetic and cross-derivative terms"),
    ("higgs_goldstone_scalar", "scalar_potential", 9.0, "H, phi0, phi+, phi- quartic and mass-potential terms"),
    ("higgs_goldstone_scalar", "electroweak_charged_w", 8.0, "W W H, W phi derivative, W W scalar terms"),
    ("higgs_goldstone_scalar", "electroweak_neutral_za", 7.0, "Z Z H, A/Z scalar derivative and scalar couplings"),
    ("higgs_goldstone_scalar", "derivative_kinetic_flow", 5.0, "scalar derivative kinetic terms"),
    ("fermion_quark_sector", "electroweak_charged_w", 6.0, "W charged quark currents"),
    ("fermion_lepton_sector", "electroweak_charged_w", 5.0, "W charged lepton/neutrino currents"),
    ("fermion_quark_sector", "electroweak_neutral_za", 6.0, "A/Z quark neutral currents"),
    ("fermion_lepton_sector", "electroweak_neutral_za", 5.0, "A/Z lepton neutral currents"),
    ("fermion_quark_sector", "yukawa_mass_coupling", 7.0, "m_u, m_d, H, phi Yukawa-like terms"),
    ("fermion_lepton_sector", "yukawa_mass_coupling", 5.0, "m_e, m_nu, H, phi Yukawa-like terms"),
    ("charged_current_ckm", "fermion_quark_sector", 6.0, "C_lambda k charged current quark mixing"),
    ("charged_current_ckm", "electroweak_charged_w", 5.0, "W+/- CKM charged current coupling"),
    ("ghost_gaugefix_sector", "electroweak_charged_w", 5.0, "X+/X- ghosts coupled to W"),
    ("ghost_gaugefix_sector", "electroweak_neutral_za", 4.0, "X0/Y ghosts and neutral gauge couplings"),
    ("ghost_gaugefix_sector", "higgs_goldstone_scalar", 4.0, "ghost-Higgs/Goldstone terms"),
    ("ghost_gaugefix_sector", "derivative_kinetic_flow", 4.0, "ghost kinetic derivative terms"),
    ("yukawa_mass_coupling", "higgs_goldstone_scalar", 8.0, "H and phi insertions into fermion mass terms"),
    ("scalar_potential", "electroweak_charged_w", 3.0, "scalar-gauge mass-generated W couplings"),
    ("scalar_potential", "electroweak_neutral_za", 3.0, "scalar-gauge mass-generated Z/A couplings"),
]


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_matrix(phi_mode: str) -> list[list[float]]:
    index = {name: pos for pos, name in enumerate(NODES)}
    size = len(NODES)
    matrix = [[0.0 for _ in range(size)] for _ in range(size)]
    for left, right, weight, _note in OBSERVATIONS:
        i = index[left]
        j = index[right]
        if phi_mode == "none":
            adjusted = weight
        elif phi_mode == "sector_scale":
            adjusted = weight * (PHI if "higgs" in left or "higgs" in right or "scalar" in left or "scalar" in right else 1.0)
        elif phi_mode == "omni":
            adjusted = weight * (PHI ** (((i + j) % 5) / 4.0))
        else:
            raise ValueError(f"unknown phi mode: {phi_mode}")
        matrix[i][j] += adjusted
        matrix[j][i] += adjusted
    # Diagonal mass/self weights keep each sector visible in the operator.
    for i, name in enumerate(NODES):
        base = 1.0 + sum(matrix[i]) / 20.0
        if phi_mode == "omni":
            base *= PHI ** ((i % 3) / 3.0)
        matrix[i][i] = base
    return matrix


def matvec(matrix: list[list[float]], vector: list[float]) -> list[float]:
    return [sum(row[j] * vector[j] for j in range(len(vector))) for row in matrix]


def norm(vector: list[float]) -> float:
    return math.sqrt(sum(value * value for value in vector))


def principal_eigen(matrix: list[list[float]], iterations: int = 256) -> dict[str, Any]:
    size = len(matrix)
    vector = [1.0 / math.sqrt(size) for _ in range(size)]
    eigenvalue = 0.0
    for _ in range(iterations):
        nxt = matvec(matrix, vector)
        nrm = norm(nxt)
        if nrm == 0.0:
            break
        vector = [value / nrm for value in nxt]
        av = matvec(matrix, vector)
        eigenvalue = sum(vector[i] * av[i] for i in range(size))
    residual_vec = [matvec(matrix, vector)[i] - eigenvalue * vector[i] for i in range(size)]
    return {
        "eigenvalue": eigenvalue,
        "vector": vector,
        "residual_norm": norm(residual_vec),
        "iterations": iterations,
    }


def summarize_vector(vector: list[float]) -> list[dict[str, float | str]]:
    entries = [
        {"node": node, "component": vector[i], "abs_component": abs(vector[i])}
        for i, node in enumerate(NODES)
    ]
    return sorted(entries, key=lambda item: float(item["abs_component"]), reverse=True)


def spectral_gap_proxy(matrix: list[list[float]], principal: list[float], eigenvalue: float) -> float:
    """Crude deflation-based gap proxy for this receipt."""
    size = len(matrix)
    deflated = [
        [
            matrix[i][j] - eigenvalue * principal[i] * principal[j]
            for j in range(size)
        ]
        for i in range(size)
    ]
    second = principal_eigen(deflated, iterations=128)["eigenvalue"]
    return eigenvalue - abs(float(second))


def mode_result(phi_mode: str) -> dict[str, Any]:
    matrix = build_matrix(phi_mode)
    principal = principal_eigen(matrix)
    entries = summarize_vector(principal["vector"])
    gap = spectral_gap_proxy(matrix, principal["vector"], float(principal["eigenvalue"]))
    matrix_hash = sha256_bytes(stable_json(matrix).encode("utf-8"))
    vector_hash = sha256_bytes(stable_json(entries).encode("utf-8"))
    return {
        "phi_mode": phi_mode,
        "matrix_hash_sha256": matrix_hash,
        "vector_hash_sha256": vector_hash,
        "principal_eigenvalue": principal["eigenvalue"],
        "residual_norm": principal["residual_norm"],
        "spectral_gap_proxy": gap,
        "dominant_components": entries,
        "claim_boundary": (
            "Eigenvector is from a hand-extracted term-family feature matrix, "
            "not from the physical Standard Model Hamiltonian or propagator."
        ),
    }


def build_receipt() -> dict[str, Any]:
    modes = [mode_result(mode) for mode in ("none", "sector_scale", "omni")]
    receipt = {
        "schema": "standard_model_lagrangian_term_eigen_probe_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "surface_id": "standard_model_lagrangian_wall_eigen_probe",
        "source": {
            "description": "User-provided image of expanded Standard Model Lagrangian.",
            "visible_term_families": NODES,
            "observation_count": len(OBSERVATIONS),
            "observations": [
                {"left": left, "right": right, "weight": weight, "note": note}
                for left, right, weight, note in OBSERVATIONS
            ],
        },
        "phi": PHI,
        "modes": modes,
        "lawful": True,
        "claim_boundary": (
            "This probe computes eigenvectors of a term-family interaction matrix "
            "derived from the visible Lagrangian wall. It does not compute particle "
            "mass eigenstates, CKM/PMNS eigenvectors, beta functions, vacuum states, "
            "or a physical spectrum."
        ),
    }
    stable_preimage = stable_json({
        "schema": receipt["schema"],
        "surface_id": receipt["surface_id"],
        "source": receipt["source"],
        "phi": receipt["phi"],
        "modes": receipt["modes"],
        "lawful": receipt["lawful"],
        "claim_boundary": receipt["claim_boundary"],
    }).encode("utf-8")
    receipt["stable_probe_hash_sha256"] = sha256_bytes(stable_preimage)
    receipt["receipt_hash_preimage_sha256"] = sha256_bytes(stable_json(receipt).encode("utf-8"))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    receipt = build_receipt()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "lawful": receipt["lawful"],
        "stable_probe_hash_sha256": receipt["stable_probe_hash_sha256"],
        "receipt_hash_preimage_sha256": receipt["receipt_hash_preimage_sha256"],
        "modes": [
            {
                "phi_mode": mode["phi_mode"],
                "principal_eigenvalue": mode["principal_eigenvalue"],
                "residual_norm": mode["residual_norm"],
                "spectral_gap_proxy": mode["spectral_gap_proxy"],
                "top_component": mode["dominant_components"][0],
            }
            for mode in receipt["modes"]
        ],
        "out": str(args.out.relative_to(REPO)) if args.out.is_relative_to(REPO) else str(args.out),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
