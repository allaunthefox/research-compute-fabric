#!/usr/bin/env python3
"""Virtual-only polaron-polariton braid field probe.

This is a numerical toy model for equation scouting. It does not model a
specific material stack and does not touch hardware. The goal is to test whether
charge-lattice dressing, light-matter coupling, and braid phase can be expressed
as a stable multi-lane encoding candidate.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "4-Infrastructure" / "hardware" / "polaron_polariton_braid_probe_receipt.json"


@dataclass(frozen=True)
class BraidFieldCase:
    name: str
    photon_energy: float
    exciton_energy: float
    phonon_energy: float
    photon_exciton_coupling: float
    electron_phonon_coupling: float
    polaron_drag: float
    braid_theta: float
    local_disorder: float


def hamiltonian(case: BraidFieldCase, disorder: np.ndarray | None = None) -> np.ndarray:
    """Four-mode Hermitian toy Hamiltonian.

    Basis:
      0 photon mode
      1 exciton / charge mode
      2 phonon / lattice distortion mode
      3 residual dressed cloud mode
    """
    diag = np.array(
        [
            case.photon_energy,
            case.exciton_energy,
            case.phonon_energy,
            case.exciton_energy - case.polaron_drag,
        ],
        dtype=np.float64,
    )
    if disorder is not None:
        diag = diag + disorder

    h = np.diag(diag).astype(np.complex128)
    omega = 0.5 * case.photon_exciton_coupling
    g = case.electron_phonon_coupling
    drag = case.polaron_drag
    phase = np.exp(1j * case.braid_theta)

    h[0, 1] = omega
    h[1, 0] = np.conj(h[0, 1])
    h[1, 2] = g
    h[2, 1] = np.conj(h[1, 2])
    h[1, 3] = drag
    h[3, 1] = np.conj(h[1, 3])

    # Braided light-lattice sideband: phase-bearing path, not a physical claim.
    h[0, 2] = 0.25 * math.sqrt(max(omega * omega + g * g, 0.0)) * phase
    h[2, 0] = np.conj(h[0, 2])
    h[0, 3] = 0.15 * drag * np.conj(phase)
    h[3, 0] = np.conj(h[0, 3])
    return h


def braid_operator(theta: float) -> np.ndarray:
    """Exchange operator with anyon-like phase on a two-lane subspace."""
    return np.array([[0.0, np.exp(1j * theta)], [1.0, 0.0]], dtype=np.complex128)


def spectral_gap(evals: np.ndarray) -> float:
    diffs = np.diff(np.sort(np.real(evals)))
    return float(np.min(np.abs(diffs)))


def participation_entropy(vec: np.ndarray) -> float:
    weights = np.abs(vec) ** 2
    weights = weights / max(float(np.sum(weights)), 1e-12)
    return float(-np.sum(weights * np.log2(np.maximum(weights, 1e-12))))


def diagnostics(case: BraidFieldCase, seed: int = 0, trials: int = 64) -> dict:
    base = hamiltonian(case)
    evals, evecs = np.linalg.eigh(base)
    gap = spectral_gap(evals)
    ground_entropy = participation_entropy(evecs[:, 0])
    braid = braid_operator(case.braid_theta)
    braid_unitarity_error = float(np.linalg.norm(braid.conj().T @ braid - np.eye(2)))

    rng = np.random.default_rng(seed)
    shifts = []
    phase_errors = []
    for _ in range(trials):
        disorder = rng.normal(0.0, case.local_disorder, size=4)
        perturbed = hamiltonian(case, disorder=disorder)
        pevals = np.linalg.eigvalsh(perturbed)
        shifts.append(float(np.linalg.norm(np.sort(np.real(pevals)) - np.sort(np.real(evals)))))
        perturbed_theta = case.braid_theta + float(rng.normal(0.0, case.local_disorder))
        phase_errors.append(abs(np.angle(np.exp(1j * perturbed_theta) / np.exp(1j * case.braid_theta))))

    mean_shift = float(np.mean(shifts))
    phase_std = float(np.std(phase_errors))
    robustness_proxy = float((gap / (gap + mean_shift + 1e-12)) * math.exp(-phase_std))
    return {
        "case": asdict(case),
        "eigenvalues": [float(x) for x in np.real(evals)],
        "spectral_gap": gap,
        "ground_participation_entropy": ground_entropy,
        "braid_unitarity_error": braid_unitarity_error,
        "mean_disorder_eigen_shift": mean_shift,
        "braid_phase_error_std": phase_std,
        "topological_robustness_proxy": robustness_proxy,
        "admissible": bool(gap > 0.02 and robustness_proxy > 0.55 and braid_unitarity_error < 1e-9),
    }


def sweep(seed: int = 20260507, count: int = 256) -> list[dict]:
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(count):
        case = BraidFieldCase(
            name=f"random-{i:03d}",
            photon_energy=float(rng.uniform(0.8, 1.25)),
            exciton_energy=float(rng.uniform(0.85, 1.2)),
            phonon_energy=float(rng.uniform(0.05, 0.35)),
            photon_exciton_coupling=float(rng.uniform(0.03, 0.9)),
            electron_phonon_coupling=float(rng.uniform(0.01, 0.75)),
            polaron_drag=float(rng.uniform(0.005, 0.45)),
            braid_theta=float(rng.uniform(0.0, 2.0 * math.pi)),
            local_disorder=float(rng.uniform(0.001, 0.08)),
        )
        rows.append(diagnostics(case, seed=seed + i))
    return rows


def main() -> None:
    canonical_cases = [
        BraidFieldCase("balanced-braid", 1.0, 1.0, 0.16, 0.55, 0.22, 0.12, math.pi / 3.0, 0.01),
        BraidFieldCase("polaron-heavy", 1.04, 0.96, 0.11, 0.28, 0.62, 0.38, math.pi / 2.0, 0.02),
        BraidFieldCase("polariton-clean", 1.0, 1.02, 0.2, 0.82, 0.08, 0.04, math.pi / 4.0, 0.006),
        BraidFieldCase("disorder-fray", 1.0, 1.0, 0.13, 0.35, 0.28, 0.2, 2.8, 0.075),
        BraidFieldCase("gap-collapse", 1.0, 1.01, 0.95, 0.04, 0.03, 0.02, 5.2, 0.04),
    ]
    canonical = [diagnostics(case, seed=20260507 + i) for i, case in enumerate(canonical_cases)]
    rows = sweep()
    admissible_count = sum(1 for row in rows if row["admissible"])
    best = sorted(rows, key=lambda row: row["topological_robustness_proxy"], reverse=True)[:8]
    worst_gap = sorted(rows, key=lambda row: row["spectral_gap"])[:8]

    equations = {
        "total_hamiltonian": "H_total = H_photon + H_electron + H_phonon + H_interactions",
        "polaron_term": "H_e-ph = sum_kq g_q c^dagger_{k+q} c_k (a_q + a^dagger_{-q})",
        "polariton_term": "H_pol = [[E_c(k)-i gamma_c/2, Omega_R/2], [Omega_R/2, E_x-i gamma_x/2]]",
        "braid_exchange": "B_i psi(...,x_i,x_{i+1},...) = exp(i theta) psi(...,x_{i+1},x_i,...)",
        "project_lane": "BraidedPolaronPolaritonLane = charge_lattice_dressing * light_matter_branch * exp(i theta_braid) + residual_repair",
    }
    receipt = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "lawful": True,
        "mode": "virtual_only",
        "source_note": "No hardware programming, RF emission, JTAG, serial flashing, board access, or material claim. Numerical toy model only.",
        "equations": equations,
        "basis": ["photon", "exciton_charge", "phonon_lattice_distortion", "residual_dressed_cloud"],
        "canonical_cases": canonical,
        "random_sweep": {
            "seed": 20260507,
            "count": len(rows),
            "admissible_count": admissible_count,
            "admissible_ratio": admissible_count / len(rows),
            "best_robustness": best,
            "worst_gap": worst_gap,
        },
        "claim_boundary": "This scouts a topological polaron-polariton braid-field equation candidate only. It does not prove topological protection, device feasibility, material existence, or compression advantage.",
    }
    encoded = json.dumps(receipt, indent=2, sort_keys=True).encode("utf-8")
    receipt["receipt_hash_preimage_sha256"] = hashlib.sha256(encoded).hexdigest()
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
