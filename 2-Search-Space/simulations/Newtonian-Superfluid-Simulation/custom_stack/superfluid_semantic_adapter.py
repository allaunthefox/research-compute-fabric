"""
Semantic-mass adapter for the Newtonian Superfluid Simulation.

This module separates the particle-force simulation from the custom ontology stack.
It exports finite, auditable state summaries that can be consumed by:

- WebGPU / Three.js renderers
- JSON-LD graph exporters
- Lean/Wasm bridge prototypes
- FAMM / Inverted FAMM route-memory modules

Boundary:
    These values are dimensionless semantic/diagnostic metrics. They are not SI mass.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Tuple

import numpy as np

Array = np.ndarray

Q16_ONE = 1 << 16


@dataclass(frozen=True)
class SuperfluidParams:
    """Simulation constants matching the repository's force model."""

    box_size: float = 50.0
    dt: float = 0.04
    k_gravity: float = 100.0
    k_repel: float = 100.0
    softening: float = 1.2
    r_max: float = 10.0
    damping: float = 0.95
    max_vel: float = 12.0


@dataclass(frozen=True)
class SemanticMassState:
    """Dimensionless state exported to the ontology/wiki/render stack."""

    node_id: int
    particle_count: int
    mass_number: float
    semantic_density: float
    torsion: float
    kinetic_pressure: float
    basin_strength: float
    receipt_coverage: float
    gate: str

    def to_json_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_q16_dict(self) -> Dict[str, int]:
        return {
            "node_id": int(self.node_id),
            "mass_number_q16": float_to_q16(self.mass_number),
            "semantic_density_q16": float_to_q16(self.semantic_density),
            "torsion_q16": float_to_q16(self.torsion),
            "kinetic_pressure_q16": float_to_q16(self.kinetic_pressure),
            "basin_strength_q16": float_to_q16(self.basin_strength),
            "receipt_coverage_q16": float_to_q16(self.receipt_coverage),
            "gate_scope": 1 if self.gate == "V_scope" else 0,
        }


def clamp01(x: float) -> float:
    if not np.isfinite(x):
        return 0.0
    return float(max(0.0, min(1.0, x)))


def float_to_q16(x: float) -> int:
    """Convert a [0, 1] float-like metric to unsigned Q16.16 integer form."""

    return int(round(clamp01(x) * Q16_ONE))


def initialize_state(n_particles: int, params: SuperfluidParams, seed: int | None = None) -> Tuple[Array, Array]:
    rng = np.random.default_rng(seed)
    pos = rng.random((n_particles, 2), dtype=np.float64) * params.box_size
    vel = np.zeros((n_particles, 2), dtype=np.float64)
    return pos, vel


def compute_forces(pos: Array, params: SuperfluidParams) -> Array:
    """Vectorized local attraction/repulsion force field.

    Force law:
        attraction ~ +k_gravity / (r^2 + softening)
        repulsion  ~ -k_repel / (r^4 + 0.1)

    The diagonal self-force is masked out.
    """

    delta = pos[None, :, :] - pos[:, None, :]
    dist_sq = np.sum(delta * delta, axis=2)
    dist = np.sqrt(dist_sq) + 1.0e-9

    mask = (dist > 1.0e-8) & (dist < params.r_max)
    direction = delta / dist[:, :, None]

    f_grav = params.k_gravity / (dist_sq + params.softening)
    f_repel = -params.k_repel / ((dist_sq * dist_sq) + 0.1)
    scalar = np.where(mask, f_grav + f_repel, 0.0)

    return np.sum(direction * scalar[:, :, None], axis=1)


def step_superfluid(pos: Array, vel: Array, params: SuperfluidParams) -> Tuple[Array, Array, Array]:
    """Advance one finite simulation step and return pos, vel, forces."""

    forces = compute_forces(pos, params)
    vel = vel * params.damping + forces * params.dt

    speed = np.linalg.norm(vel, axis=1, keepdims=True)
    safe_speed = np.maximum(speed, 1.0e-9)
    vel = np.where(speed > params.max_vel, vel * (params.max_vel / safe_speed), vel)
    pos = pos + vel * params.dt

    for d in range(2):
        out_min = pos[:, d] < 0.0
        out_max = pos[:, d] > params.box_size
        if np.any(out_min):
            pos[out_min, d] = 0.0
            vel[out_min, d] = -vel[out_min, d] * 0.5
        if np.any(out_max):
            pos[out_max, d] = params.box_size
            vel[out_max, d] = -vel[out_max, d] * 0.5

    return pos, vel, forces


def pairwise_density(pos: Array, params: SuperfluidParams) -> float:
    """Fraction of local neighbor pairs within interaction range."""

    n = pos.shape[0]
    if n <= 1:
        return 0.0
    delta = pos[None, :, :] - pos[:, None, :]
    dist_sq = np.sum(delta * delta, axis=2)
    mask = (dist_sq > 1.0e-12) & (dist_sq < params.r_max * params.r_max)
    return clamp01(float(np.count_nonzero(mask)) / float(n * (n - 1)))


def angular_torsion(pos: Array, vel: Array, params: SuperfluidParams) -> float:
    """Dimensionless swirl/torsion proxy around the center of mass."""

    center = np.mean(pos, axis=0, keepdims=True)
    rel = pos - center
    radius = np.linalg.norm(rel, axis=1)
    speed = np.linalg.norm(vel, axis=1)
    cross_z = rel[:, 0] * vel[:, 1] - rel[:, 1] * vel[:, 0]
    denom = np.maximum(radius * speed, 1.0e-9)
    local_spin = np.abs(cross_z) / denom
    weighted = local_spin * np.tanh(speed / max(params.max_vel, 1.0e-9))
    return clamp01(float(np.mean(weighted)))


def kinetic_pressure(vel: Array, params: SuperfluidParams) -> float:
    speed = np.linalg.norm(vel, axis=1)
    return clamp01(float(np.mean(speed * speed) / max(params.max_vel * params.max_vel, 1.0e-9)))


def basin_strength_from_forces(forces: Array, params: SuperfluidParams) -> float:
    """Stable basins are low-force, low-residual regions in this first adapter."""

    force_mag = np.linalg.norm(forces, axis=1)
    force_scale = max(params.k_gravity / max(params.softening, 1.0e-9), 1.0e-9)
    normalized_force = clamp01(float(np.mean(force_mag) / force_scale))
    return clamp01(1.0 - normalized_force)


def summarize_semantic_state(
    node_id: int,
    pos: Array,
    vel: Array,
    forces: Array,
    params: SuperfluidParams,
    receipt_coverage: float = 0.25,
) -> SemanticMassState:
    density = pairwise_density(pos, params)
    torsion = angular_torsion(pos, vel, params)
    pressure = kinetic_pressure(vel, params)
    basin = basin_strength_from_forces(forces, params)

    # First-pass semantic mass: density carries the node, pressure activates it,
    # torsion discounts it when unresolved stress dominates.
    mass_number = clamp01(0.55 * density + 0.35 * pressure + 0.10 * basin - 0.15 * torsion)

    receipt_coverage = clamp01(receipt_coverage)
    gate = "V_scope" if receipt_coverage >= 1.0 else "U_scope"

    return SemanticMassState(
        node_id=node_id,
        particle_count=int(pos.shape[0]),
        mass_number=mass_number,
        semantic_density=density,
        torsion=torsion,
        kinetic_pressure=pressure,
        basin_strength=basin,
        receipt_coverage=receipt_coverage,
        gate=gate,
    )


def run_probe(
    n_particles: int = 350,
    steps: int = 200,
    seed: int | None = 7,
    params: SuperfluidParams | None = None,
) -> SemanticMassState:
    """Run a finite probe and return the final semantic summary."""

    params = params or SuperfluidParams()
    pos, vel = initialize_state(n_particles, params, seed=seed)
    forces = np.zeros_like(pos)
    for _ in range(steps):
        pos, vel, forces = step_superfluid(pos, vel, params)
    return summarize_semantic_state(1, pos, vel, forces, params)


if __name__ == "__main__":
    state = run_probe()
    print(state.to_json_dict())
    print(state.to_q16_dict())
