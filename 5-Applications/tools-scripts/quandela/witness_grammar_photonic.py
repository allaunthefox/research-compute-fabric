#!/usr/bin/env python3
"""
witness_grammar_photonic.py
============================

Photonic encoding of the FNWH-Burgers Witness-Grammar 3-mode toy
S(x) = sin(x) + 0.3·sin(2x) + 0.1·sin(3x).

Goal
----
Empirically measure the complexity metric Ω[u] = ½ Σ n²|a_n|² on a real
linear-optical sampler (local SLOS first; cloud `sim:slos` optional), then
compare to the closed-form Ω so the empirical-vs-analytical gap is honest and
visible.

Honest scope
------------
What this script demonstrates:
  ✓ The 3-mode spectral state encodes cleanly into a 3-mode photonic circuit.
  ✓ Ω can be reconstructed from photon-counting statistics within shot noise.
  ✓ The circuit unitary admits independent verification (analytical vs computed).

What this script does NOT do:
  ✗ Solve the regularized Burgers PDE.
  ✗ Prove EffectiveViscosity(Ω) > 0, prove WitnessScalar boundedness, or
    prove any of the candidate formal targets in mathholes_ene_brief.md.
  ✗ Establish anything about Navier-Stokes regularity.
  ✗ Validate the FNWH framework — we are working *inside* it and reporting
    what the photons say. External meaning is for an outside reviewer.

References
----------
- 6-Documentation/docs/specs/BurgersHarmonicPeelingVerification.md
- shared-data/data/ingested/chatgpt/mathholes_ene_brief.md  (claim quarantine)
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path

import perceval as pcvl
from perceval.components import BS
from perceval.algorithm import Sampler


# =============================================================================
# 1. Witness Grammar — the test field
# =============================================================================

# S(x) = sin(x) + 0.3*sin(2x) + 0.1*sin(3x)  per BurgersHarmonicPeelingVerification.md
WITNESS_AMPS: dict[int, float] = {1: 1.0, 2: 0.3, 3: 0.1}


def omega_analytical(amps: dict[int, float]) -> float:
    """Ω[u] = ½ Σ n² |a_n|²  (closed form from the spec)."""
    return 0.5 * sum(n * n * a * a for n, a in amps.items())


# =============================================================================
# 2. State-prep circuit  (3-mode amplitude encoding via BS tree)
# =============================================================================
#
# Perceval BS convention (Rx, default):
#   U = [[ cos(θ/2),  i·sin(θ/2)],
#        [ i·sin(θ/2), cos(θ/2) ]]
#
# Single photon in mode 0 → amplitude cos(θ/2) in mode 0, i·sin(θ/2) in mode 1.
# Phases don't enter Ω since Ω only sees |a_n|².
#
# To prepare normalised amplitudes (b₁, b₂, b₃) on 3 modes from |1,0,0⟩:
#   BS₁ on modes (0,1):  cos(θ₁/2) = b₁,  sin(θ₁/2) = √(b₂² + b₃²)
#   BS₂ on modes (1,2):  cos(θ₂/2) = b₂ / √(b₂² + b₃²)


def normalised_amps(amps: dict[int, float]) -> dict[int, float]:
    norm = math.sqrt(sum(a * a for a in amps.values()))
    return {n: a / norm for n, a in amps.items()}


def build_state_prep_circuit(amps: dict[int, float]) -> tuple[pcvl.Circuit, dict]:
    """3-mode circuit: |1,0,0⟩ → b₁|1,0,0⟩ + (i)b₂|0,1,0⟩ + (-)b₃|0,0,1⟩."""
    b = normalised_amps(amps)
    b1, b2, b3 = b[1], b[2], b[3]

    rem = math.sqrt(b2 * b2 + b3 * b3)
    theta1 = 2.0 * math.acos(b1)             # BS₁ on (0,1)
    theta2 = 2.0 * math.acos(b2 / rem) if rem > 0 else 0.0   # BS₂ on (1,2)

    circuit = pcvl.Circuit(3, name="WitnessGrammarPrep")
    circuit.add((0, 1), BS(theta=theta1))
    circuit.add((1, 2), BS(theta=theta2))

    meta = {
        "normalised_amps": b,
        "theta1_rad": theta1,
        "theta2_rad": theta2,
        "norm_squared": sum(a * a for a in amps.values()),
    }
    return circuit, meta


# =============================================================================
# 3. Independent verification of the circuit unitary  (analytic vs computed)
# =============================================================================

def verify_unitary(circuit: pcvl.Circuit, amps: dict[int, float]) -> dict:
    """Check that U|1,0,0⟩ has the |amplitude|² spectrum we asked for."""
    U = circuit.compute_unitary()
    # Column 0 of U is the image of |1,0,0⟩
    col0 = U[:, 0]
    p_predicted = [abs(c) ** 2 for c in col0]
    b = normalised_amps(amps)
    p_target = [b[1] ** 2, b[2] ** 2, b[3] ** 2]

    return {
        "unitary_column_0_amplitudes": [complex(c).__repr__() for c in col0],
        "predicted_mode_probabilities": p_predicted,
        "target_mode_probabilities": p_target,
        "max_abs_error": max(abs(p - q) for p, q in zip(p_predicted, p_target)),
        "passes": all(math.isclose(p, q, abs_tol=1e-12) for p, q in zip(p_predicted, p_target)),
    }


# =============================================================================
# 4. Run on local SLOS simulator  (no network, no token, no credit)
# =============================================================================

def run_slos(circuit: pcvl.Circuit, n_shots: int = 100_000, backend: str = "SLOS") -> dict:
    """Sample 1-photon outcomes from the circuit using Perceval's local SLOS."""
    processor = pcvl.Processor(backend, circuit)
    processor.with_input(pcvl.BasicState([1, 0, 0]))

    sampler = Sampler(processor)
    samples = sampler.samples(n_shots)["results"]

    counts = {0: 0, 1: 0, 2: 0}
    for s in samples:
        for mode in range(3):
            if s[mode] == 1:
                counts[mode] += 1
    total = sum(counts.values())
    return {
        "backend": backend,
        "n_shots": n_shots,
        "counts": counts,
        "total_detected": total,
        "empirical_probabilities": {m: c / total for m, c in counts.items()},
    }


# =============================================================================
# 5. Reconstruct Ω from empirical probabilities + report comparison
# =============================================================================

def reconstruct_omega(empirical_probs: dict[int, float], amps: dict[int, float]) -> float:
    """Ω̂ = ½ Σ n² · p̂_(n-1) · ‖a‖²  (un-normalise back to spec amplitudes)."""
    norm2 = sum(a * a for a in amps.values())
    return 0.5 * sum(
        n * n * empirical_probs[n - 1] * norm2 for n in sorted(amps)
    )


def shot_noise_envelope(empirical_probs: dict[int, float], amps: dict[int, float],
                        n_shots: int) -> dict:
    """1-σ multinomial shot-noise band on the reconstructed Ω."""
    norm2 = sum(a * a for a in amps.values())
    var_omega = 0.0
    for n in sorted(amps):
        p = empirical_probs[n - 1]
        # Var(p̂) = p(1-p)/N for multinomial with N trials
        var_p = p * (1.0 - p) / n_shots
        # Ω = ½ Σ n² p̂ · ‖a‖²  → Var(Ω) = Σ (½ n² ‖a‖²)² · Var(p̂_n)
        var_omega += (0.5 * n * n * norm2) ** 2 * var_p
    return {"sigma_omega": math.sqrt(var_omega)}


# =============================================================================
# 6. (Optional) Cloud sim:slos cross-check
# =============================================================================

def run_cloud_slos(circuit: pcvl.Circuit, n_shots: int = 1000) -> dict:
    """Submit the same circuit to cloud sim:slos via QUANDELA_API_KEY in .env."""
    env_file = Path(__file__).resolve().parents[3] / ".env"
    token = None
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("QUANDELA_API_KEY="):
                token = line.split("=", 1)[1].strip()
                break
    if not token:
        return {"skipped": True, "reason": "no QUANDELA_API_KEY in .env"}

    try:
        rp = pcvl.RemoteProcessor("sim:slos", token=token)
        # Note: max_shots_per_call is often required for remote backends
        rp.set_circuit(circuit)
        rp.min_detected_photons_filter(1)
        rp.with_input(pcvl.BasicState([1, 0, 0]))
        sampler = Sampler(rp, max_shots_per_call=n_shots)
        job = sampler.samples(n_shots)
        # Cloud jobs are async; .execute_async() pattern.  Try the simple sync path first.
        result = job if isinstance(job, dict) else job.execute_sync()
        samples = result["results"] if isinstance(result, dict) else result
        counts = {0: 0, 1: 0, 2: 0}
        for s in samples:
            for mode in range(3):
                if s[mode] == 1:
                    counts[mode] += 1
        total = sum(counts.values())
        return {
            "skipped": False,
            "platform": "sim:slos",
            "n_shots": n_shots,
            "counts": counts,
            "total_detected": total,
            "empirical_probabilities": {m: c / total for m, c in counts.items()},
        }
    except Exception as exc:
        return {"skipped": True, "reason": f"cloud submission failed: {type(exc).__name__}: {exc}"}


# =============================================================================
# 7. Main
# =============================================================================

def main():
    out_dir = Path(__file__).resolve().parents[3] / "shared-data" / "artifacts" / "quandela_witness_grammar"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("WITNESS-GRAMMAR PHOTONIC ENCODING — local SLOS")
    print("=" * 72)
    print(f"Witness amplitudes: {WITNESS_AMPS}")
    print(f"Analytical Ω      : {omega_analytical(WITNESS_AMPS):.6f}")
    print()

    print("[1/4] building state-prep circuit")
    circuit, meta = build_state_prep_circuit(WITNESS_AMPS)
    print(f"      θ₁ = {meta['theta1_rad']:.6f} rad")
    print(f"      θ₂ = {meta['theta2_rad']:.6f} rad")
    print(f"      normalised amps: {meta['normalised_amps']}")
    print()

    print("[2/4] verifying unitary  (analytical vs computed)")
    ver = verify_unitary(circuit, WITNESS_AMPS)
    print(f"      target probs : {[f'{p:.6f}' for p in ver['target_mode_probabilities']]}")
    print(f"      computed     : {[f'{p:.6f}' for p in ver['predicted_mode_probabilities']]}")
    print(f"      max |error|  : {ver['max_abs_error']:.2e}  passes={ver['passes']}")
    print()

    print("[3/4] sampling local SLOS  (no network)")
    n_shots = 100_000
    slos = run_slos(circuit, n_shots=n_shots, backend="SLOS")
    print(f"      shots        : {slos['n_shots']}  detected={slos['total_detected']}")
    print(f"      empirical p̂ : {slos['empirical_probabilities']}")

    omega_hat = reconstruct_omega(slos["empirical_probabilities"], WITNESS_AMPS)
    sigma = shot_noise_envelope(slos["empirical_probabilities"], WITNESS_AMPS, n_shots)["sigma_omega"]
    omega_true = omega_analytical(WITNESS_AMPS)
    print(f"      Ω̂ (empirical): {omega_hat:.6f}  ± {sigma:.6f}  (1σ shot noise)")
    print(f"      Ω  (analytical): {omega_true:.6f}")
    print(f"      |Ω̂ − Ω| / σ : {abs(omega_hat - omega_true) / sigma:.3f}σ")
    print()

    print("[4/4] cross-check on cloud sim:slos  (uses QUANDELA_API_KEY if present)")
    cloud = run_cloud_slos(circuit, n_shots=1000)
    if cloud.get("skipped"):
        print(f"      skipped: {cloud['reason']}")
    else:
        omega_cloud = reconstruct_omega(cloud["empirical_probabilities"], WITNESS_AMPS)
        print(f"      cloud platform: {cloud['platform']}")
        print(f"      shots         : {cloud['n_shots']}  detected={cloud['total_detected']}")
        print(f"      empirical p̂  : {cloud['empirical_probabilities']}")
        print(f"      Ω̂ (cloud)   : {omega_cloud:.6f}")

    bundle = {
        "witness_amps": WITNESS_AMPS,
        "omega_analytical": omega_true,
        "circuit_meta": meta,
        "unitary_verification": ver,
        "local_slos": {**slos, "omega_empirical": omega_hat, "sigma_shot_noise": sigma,
                       "deviations_sigma": abs(omega_hat - omega_true) / sigma},
        "cloud_slos": cloud,
    }
    out_json = out_dir / "witness_grammar_photonic_bundle.json"
    out_json.write_text(json.dumps(bundle, indent=2, default=str))
    print(f"\nwrote bundle: {out_json}")


if __name__ == "__main__":
    main()
