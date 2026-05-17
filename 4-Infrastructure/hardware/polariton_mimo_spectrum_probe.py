#!/usr/bin/env python3
"""Virtual-only polariton MIMO spectrum probe.

This is an equation and simulation harness, not a hardware driver. It explores
whether polariton-style coupled-mode equations can act as a multi-spectrum MIMO
encoding law for the existing spectral encoder direction.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "4-Infrastructure" / "hardware" / "polariton_mimo_spectrum_probe_receipt.json"


@dataclass(frozen=True)
class SweepCase:
    name: str
    detuning: float
    rabi: float
    loss: float
    cross_coupling: float
    torsion: float
    snr_db: float


def polariton_branches(e_cavity: np.ndarray, e_exciton: float, rabi: float) -> tuple[np.ndarray, np.ndarray]:
    """Lower/upper polariton branches from a two-level coupled oscillator."""
    delta = e_cavity - e_exciton
    root = np.sqrt(delta * delta + rabi * rabi)
    lower = 0.5 * (e_cavity + e_exciton - root)
    upper = 0.5 * (e_cavity + e_exciton + root)
    return lower, upper


def hopfield_photon_fraction(e_cavity: np.ndarray, e_exciton: float, rabi: float) -> np.ndarray:
    """Photon-like fraction for the lower polariton branch."""
    delta = e_cavity - e_exciton
    return 0.5 * (1.0 - delta / np.sqrt(delta * delta + rabi * rabi))


def dft_matrix(n: int) -> np.ndarray:
    idx = np.arange(n)
    omega = np.exp(-2j * np.pi / n)
    return omega ** (np.outer(idx, idx)) / np.sqrt(n)


def mimo_channel(case: SweepCase, bins: int = 8, tx: int = 4, rx: int = 4) -> np.ndarray:
    """Build a compact polariton-weighted MIMO channel tensor H[f, rx, tx]."""
    k = np.linspace(-1.0, 1.0, bins)
    e_cavity = 1.0 + case.detuning + 0.18 * k * k
    e_exciton = 1.0
    lower, upper = polariton_branches(e_cavity, e_exciton, case.rabi)
    photon = hopfield_photon_fraction(e_cavity, e_exciton, case.rabi)
    exciton = 1.0 - photon

    # Spectral mixer: DFT gives orthogonal carriers; torsion rotates their phase.
    carrier = dft_matrix(max(rx, tx))[:rx, :tx]
    lane_phase = np.exp(1j * (case.torsion * np.arange(bins)))
    h = np.zeros((bins, rx, tx), dtype=np.complex128)
    for i in range(bins):
        branch_gap = upper[i] - lower[i]
        q_weight = photon[i] / (case.loss + 0.03 + abs(branch_gap))
        coherent = q_weight * lane_phase[i] * carrier
        # Crosstalk term is deliberately ugly: rank-one leakage plus lane parity.
        leakage = case.cross_coupling * exciton[i] * np.outer(
            np.exp(1j * np.arange(rx) * (i + 1) * 0.37),
            np.exp(-1j * np.arange(tx) * (i + 1) * 0.23),
        )
        h[i] = coherent + leakage
    return h


def capacity_bits_per_use(h: np.ndarray, snr_db: float) -> float:
    snr = 10 ** (snr_db / 10.0)
    tx = h.shape[-1]
    total = 0.0
    for hf in h:
        gram = hf @ hf.conj().T
        eye = np.eye(gram.shape[0], dtype=np.complex128)
        total += float(np.real(np.log2(np.linalg.det(eye + (snr / tx) * gram))))
    return total / h.shape[0]


def diagnostics(case: SweepCase) -> dict:
    h = mimo_channel(case)
    singular_values = np.array([np.linalg.svd(hf, compute_uv=False) for hf in h])
    min_sv = float(np.min(singular_values))
    max_sv = float(np.max(singular_values))
    condition = float(max_sv / max(min_sv, 1e-12))
    lane_power = np.sum(np.abs(h) ** 2, axis=(1, 2))
    lane_spread = float(np.std(lane_power) / max(float(np.mean(lane_power)), 1e-12))
    offdiag_energy = 0.0
    diag_energy = 0.0
    for hf in h:
        gram = hf.conj().T @ hf
        diag_energy += float(np.sum(np.abs(np.diag(gram))))
        offdiag_energy += float(np.sum(np.abs(gram - np.diag(np.diag(gram)))))
    crosstalk_ratio = offdiag_energy / max(diag_energy, 1e-12)
    return {
        "case": asdict(case),
        "capacity_bits_per_use": capacity_bits_per_use(h, case.snr_db),
        "condition_number": condition,
        "min_singular_value": min_sv,
        "max_singular_value": max_sv,
        "lane_power_spread": lane_spread,
        "crosstalk_ratio": crosstalk_ratio,
        "separable": bool(condition < 80.0 and crosstalk_ratio < 1.25 and min_sv > 1e-3),
    }


def random_sweep(seed: int = 20260507, count: int = 360) -> list[dict]:
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(count):
        case = SweepCase(
            name=f"random-{i:03d}",
            detuning=float(rng.uniform(-0.65, 0.65)),
            rabi=float(rng.uniform(0.05, 1.4)),
            loss=float(rng.uniform(0.005, 0.35)),
            cross_coupling=float(rng.uniform(0.0, 1.2)),
            torsion=float(rng.uniform(0.0, 2.0 * math.pi)),
            snr_db=float(rng.uniform(6.0, 32.0)),
        )
        rows.append(diagnostics(case))
    return rows


def main() -> None:
    canonical_cases = [
        SweepCase("orthogonal-low-loss", 0.0, 0.72, 0.02, 0.02, math.pi / 4.0, 24.0),
        SweepCase("detuned-high-rabi", -0.42, 1.1, 0.04, 0.12, math.pi / 2.0, 24.0),
        SweepCase("crosstalk-horror", 0.18, 0.22, 0.08, 0.95, 2.7, 18.0),
        SweepCase("lossy-collapse", 0.52, 0.09, 0.31, 0.45, 5.1, 18.0),
        SweepCase("torsion-scrambler", -0.08, 0.83, 0.03, 0.31, 2.0 * math.pi / 3.0, 30.0),
    ]
    canonical = [diagnostics(case) for case in canonical_cases]
    sweep = random_sweep()
    best = sorted(sweep, key=lambda row: row["capacity_bits_per_use"], reverse=True)[:8]
    worst_condition = sorted(sweep, key=lambda row: row["condition_number"], reverse=True)[:8]
    separable_count = sum(1 for row in sweep if row["separable"])

    equations = {
        "polariton_coupled_mode": "H_pol(k) = [[E_c(k)-i gamma_c/2, Omega_R/2], [Omega_R/2, E_x-i gamma_x/2]]",
        "polariton_branches": "E_pm(k) = (E_c(k)+E_x)/2 +/- 1/2 sqrt((E_c(k)-E_x)^2 + Omega_R^2)",
        "mimo_channel": "y_f = H_f x_f + n_f",
        "svd_separation": "H_f = U_f Sigma_f V_f^H",
        "capacity": "C = mean_f log2 det(I + rho/N_t H_f H_f^H)",
        "polariton_mimo_lane": "PolaritonLane_f := polariton_branch_weight_f * braid_phase_f * carrier_f + residual_crosstalk_f",
    }

    receipt = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "lawful": True,
        "mode": "virtual_only",
        "source_note": "No hardware programming, RF emission, JTAG, serial flashing, or board access. Numerical equation probe only.",
        "name_boundary": "Polariton is the normalized term for this probe: coupled light-matter mode equations used as a virtual multi-spectrum MIMO encoding candidate.",
        "equations": equations,
        "canonical_cases": canonical,
        "random_sweep": {
            "seed": 20260507,
            "count": len(sweep),
            "separable_count": separable_count,
            "separable_ratio": separable_count / len(sweep),
            "best_capacity": best,
            "worst_condition": worst_condition,
        },
        "claim_boundary": "Equation candidate and virtual stress probe only; not a physical polariton device, RF modem, ESP32 test, or hardware-safe implementation.",
    }
    encoded = json.dumps(receipt, indent=2, sort_keys=True).encode("utf-8")
    receipt["receipt_hash_preimage_sha256"] = hashlib.sha256(encoded).hexdigest()
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
