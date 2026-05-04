#!/usr/bin/env python3
"""
Chandelier + Genus-3 Descent Simulation

This is a candidate visualization/model for the Research Stack intuition:

    chandelier-shaped shrinking basin
    + genus-3 topology
    + damped descent
    + angular momentum / torsion growth
    + blue/red shift trace
    + flash events at phase transitions

It is not proof. It is a physics-shaped sketch that emits traces for later
Graph.lean / torsion / FAMM handling.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np


@dataclass
class FlashEvent:
    step: int
    time: float
    tier_from: int
    tier_to: int
    delta_energy: float
    radius: float
    shift_factor: float


def holes() -> np.ndarray:
    """Three topological handles/obstructions in the 2D chart."""
    return np.array([
        [1.35, 0.15],
        [-0.75, 1.10],
        [-0.80, -1.15],
    ], dtype=float)


def chandelier_potential(pos: np.ndarray) -> float:
    """
    Shrinking-basin potential.

    Existing equations being borrowed:
    - harmonic descent toward zero: V ~ r^2
    - tier barriers: Gaussian energy shells
    - genus-3 obstruction: three repulsive handles/holes
    - blue/red shift proxy later uses Δf/f ≈ -ΔΦ/c^2, rescaled
    """
    x, y = pos
    r = math.hypot(x, y) + 1e-9

    # The fundamental rest-at-zero tendency.
    bottom_well = 0.45 * r * r

    # Chandelier tiers: energy shells that must be crossed.
    tier_radii = [3.2, 2.25, 1.35, 0.62]
    tier_heights = [0.38, 0.32, 0.26, 0.18]
    tier_widths = [0.10, 0.09, 0.075, 0.06]
    tiers = 0.0
    for radius, height, width in zip(tier_radii, tier_heights, tier_widths):
        tiers += height * math.exp(-((r - radius) ** 2) / (2 * width * width))

    # Genus-3: three high-energy holes the descent must wind around.
    obstruction = 0.0
    for hx, hy in holes():
        d2 = (x - hx) ** 2 + (y - hy) ** 2
        obstruction += 0.30 * math.exp(-d2 / (2 * 0.22 * 0.22))

    # Weak 3-fold angular corrugation so the handles matter as routes, not just dots.
    theta = math.atan2(y, x)
    angular = 0.055 * math.sin(3.0 * theta + 1.7 / (r + 0.22)) * math.exp(-0.25 * r)

    return bottom_well + tiers + obstruction + angular


def numerical_gradient(f, pos: np.ndarray, eps: float = 1e-4) -> np.ndarray:
    grad = np.zeros_like(pos)
    for i in range(len(pos)):
        plus = pos.copy()
        minus = pos.copy()
        plus[i] += eps
        minus[i] -= eps
        grad[i] = (f(plus) - f(minus)) / (2 * eps)
    return grad


def tier_index(radius: float) -> int:
    """Discrete chandelier tiers; crossing them creates flash events."""
    if radius > 2.75:
        return 4
    if radius > 1.80:
        return 3
    if radius > 1.00:
        return 2
    if radius > 0.42:
        return 1
    return 0


def simulate(
    steps: int = 2400,
    dt: float = 0.018,
    damping: float = 0.065,
    torsion_drive: float = 0.075,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, List[FlashEvent]]:
    """
    Damped descent with a torsion term.

    Equation family:
        m x¨ + γ x˙ + ∇V(x) = torsion_drive * J x˙

    J rotates the velocity by 90 degrees. As the basin narrows, conservation-like
    angular behavior makes the path wind tighter around the bottom.
    """
    pos = np.array([3.75, 0.28], dtype=float)
    vel = np.array([-0.04, 0.34], dtype=float)

    traj = []
    energies = []
    torsions = []
    shifts = []
    flashes: List[FlashEvent] = []

    previous_tier = tier_index(np.linalg.norm(pos))
    previous_energy = chandelier_potential(pos) + 0.5 * float(np.dot(vel, vel))
    ceiling_energy = previous_energy

    for step in range(steps):
        r = float(np.linalg.norm(pos)) + 1e-9
        grad = numerical_gradient(chandelier_potential, pos)

        # Rotational/torsion drive. Stronger as radius shrinks.
        Jvel = np.array([-vel[1], vel[0]])
        torsion_scale = torsion_drive / (r + 0.18)
        acc = -grad - damping * vel + torsion_scale * Jvel

        vel = vel + acc * dt
        pos = pos + vel * dt

        kinetic = 0.5 * float(np.dot(vel, vel))
        potential = chandelier_potential(pos)
        energy = kinetic + potential

        # Angular velocity proxy: omega = (r x v)/r^2.
        angular_momentum_proxy = pos[0] * vel[1] - pos[1] * vel[0]
        omega = angular_momentum_proxy / (r * r)
        torsion = abs(omega) / (r + 0.12)

        # Blue/red shift proxy from potential drop. c is scaled to 1 for model-space.
        # Falling from ceiling -> shift_factor > 1 (blue). Relaxing/rising -> lower.
        delta_phi = ceiling_energy - potential
        shift_factor = max(0.05, 1.0 + 0.18 * delta_phi)

        current_tier = tier_index(float(np.linalg.norm(pos)))
        if current_tier != previous_tier:
            flashes.append(
                FlashEvent(
                    step=step,
                    time=step * dt,
                    tier_from=previous_tier,
                    tier_to=current_tier,
                    delta_energy=previous_energy - energy,
                    radius=float(np.linalg.norm(pos)),
                    shift_factor=shift_factor,
                )
            )
            previous_tier = current_tier

        previous_energy = energy
        traj.append(pos.copy())
        energies.append(energy)
        torsions.append(torsion)
        shifts.append(shift_factor)

    return np.array(traj), np.array(energies), np.array(torsions), np.array(shifts), flashes


def plot_outputs(traj: np.ndarray, energies: np.ndarray, torsions: np.ndarray, shifts: np.ndarray, flashes: List[FlashEvent], outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)

    xs = np.linspace(-4.2, 4.2, 340)
    ys = np.linspace(-4.2, 4.2, 340)
    X, Y = np.meshgrid(xs, ys)
    Z = np.vectorize(lambda x, y: chandelier_potential(np.array([x, y])))(X, Y)

    plt.figure(figsize=(9, 9))
    plt.contourf(X, Y, Z, levels=80, cmap="magma")
    plt.contour(X, Y, Z, levels=18, colors="white", alpha=0.18, linewidths=0.6)
    plt.plot(traj[:, 0], traj[:, 1], color="cyan", linewidth=1.5, alpha=0.9, label="descent path")
    for h in holes():
        circle = plt.Circle(tuple(h), 0.23, color="black", alpha=0.55)
        plt.gca().add_patch(circle)
    if flashes:
        fp = traj[[f.step for f in flashes if f.step < len(traj)]]
        plt.scatter(fp[:, 0], fp[:, 1], s=80, c="gold", edgecolors="white", label="phase flash")
    plt.title("Chandelier + Genus-3 Descent: shrinking basin with flash transitions")
    plt.xlabel("x chart")
    plt.ylabel("y chart")
    plt.axis("equal")
    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(outdir / "chandelier_genus3_descent_map.png", dpi=180)
    plt.close()

    plt.figure(figsize=(10, 4))
    plt.plot(energies, label="total energy")
    plt.plot(torsions / max(1e-9, np.max(torsions)), label="torsion normalized")
    plt.plot(shifts / max(1e-9, np.max(shifts)), label="blue/red shift proxy normalized")
    for f in flashes:
        plt.axvline(f.step, color="gold", alpha=0.28)
    plt.title("Energy descends; torsion and frequency-shift respond")
    plt.xlabel("step")
    plt.legend()
    plt.tight_layout()
    plt.savefig(outdir / "chandelier_genus3_traces.png", dpi=180)
    plt.close()


def main() -> None:
    outdir = Path("research-stack/models/chandelier_genus3_outputs")
    traj, energies, torsions, shifts, flashes = simulate()
    plot_outputs(traj, energies, torsions, shifts, flashes, outdir)

    report = {
        "model_id": "chandelier_genus3_descent_v0",
        "status": "HOLD",
        "proof_status": "simulation_sketch_not_proof",
        "rule": "TV imagery is not proof; this simulation tests whether the geometry intuition produces coherent traces.",
        "summary": {
            "steps": int(len(traj)),
            "initial_energy": float(energies[0]),
            "final_energy": float(energies[-1]),
            "max_torsion": float(np.max(torsions)),
            "final_torsion": float(torsions[-1]),
            "max_shift_factor": float(np.max(shifts)),
            "flash_count": len(flashes),
        },
        "flashes": [asdict(f) for f in flashes],
        "outputs": [
            str(outdir / "chandelier_genus3_descent_map.png"),
            str(outdir / "chandelier_genus3_traces.png"),
        ],
    }
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "chandelier_genus3_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
