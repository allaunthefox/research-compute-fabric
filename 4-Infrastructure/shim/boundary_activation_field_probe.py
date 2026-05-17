#!/usr/bin/env python3
"""Receipt-bearing probe for the boundary activation field B(x, r).

A boundary is not where a system ends. A boundary is where accumulated encoded
states become physically active.  B(x, r) is the boundary activation field at
location x and observer/interaction scale r.

  B(x, r) = f(del_rho, delta_lambda, eta, R_del, beta_k, E_deposit)

where:
  del_rho       = density gradient
  delta_lambda  = hyper-eigen regime transition
  eta           = medium coupling
  R_del         = boundary residual / scar pressure
  beta_k        = topology persistence
  E_deposit     = cumulative deposited energy

When the superposition of encoded regime components crosses the critical
threshold, the boundary enters an active physical regime (fire, shock, plasma,
fracture, turbulence, filamentation).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "boundary_activation_field"
REGISTRY = OUT_DIR / "boundary_activation_field_registry.json"
RECEIPT = OUT_DIR / "boundary_activation_field_receipt.json"
SUMMARY = OUT_DIR / "boundary_activation_field.md"
TIDDLER = (
    REPO
    / "6-Documentation"
    / "tiddlywiki-local"
    / "wiki"
    / "tiddlers"
    / "Boundary Activation Field.tid"
)

SOURCE_REFS = [
    REPO
    / "0-Core-Formalism"
    / "lean"
    / "Semantics"
    / "Semantics"
    / "ThresholdVector.lean",
    REPO
    / "0-Core-Formalism"
    / "lean"
    / "Semantics"
    / "Semantics"
    / "BoundaryDynamics.lean",
    REPO
    / "shared-data"
    / "data"
    / "observer_chart_projection_guardrail"
    / "observer_chart_projection_guardrail_receipt.json",
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


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DensityGradient:
    """nabla_rho — the density gradient at the boundary."""

    magnitude: float  # [0, 1] normalized
    direction: str  # "inward" | "outward" | "tangential"


@dataclass(frozen=True)
class HyperEigenTransition:
    """delta_lambda — hyper-eigenvalue regime transition indicator."""

    spectral_drift: float  # how far the dominant eigenmode has drifted [0, 1]
    regime_switch_active: bool


@dataclass(frozen=True)
class MediumCoupling:
    """eta — how strongly the boundary couples to the surrounding medium."""

    coefficient: float  # coupling coefficient [0, 1]
    atmosphere_participating: bool  # does the medium carry away energy?


@dataclass(frozen=True)
class BoundaryResidual:
    """R_del — accumulated residual / scar pressure at the boundary."""

    scar_pressure: float  # accumulated scar energy density [0, 1]
    residual_growth_rate: float  # how fast residuals are growing [0, 1]


@dataclass(frozen=True)
class TopologyPersistence:
    """beta_k — topology persistence across scale changes."""

    betti_connected: int  # number of connected components
    betti_loops: int  # number of tunnels / loops
    betti_cavities: int  # number of enclosed cavities
    persistence_ratio: float  # fraction of topology that survives scale change [0, 1]


@dataclass(frozen=True)
class DepositedEnergy:
    """E_deposit — cumulative energy deposited at the boundary."""

    total: float  # total deposited energy [0, 1] normalized
    deposition_rate: float  # rate of energy deposition [0, 1]


@dataclass(frozen=True)
class BoundaryActivationState:
    """Complete set of encoded regime components at a boundary point."""

    density_gradient: DensityGradient
    hyper_eigen: HyperEigenTransition
    medium_coupling: MediumCoupling
    boundary_residual: BoundaryResidual
    topology: TopologyPersistence
    deposited_energy: DepositedEnergy

    # Observer / scale metadata
    location_label: str  # human-readable location
    scale: float  # observation scale in arbitrary units

    def component_vector(self) -> dict[str, float]:
        """Extract the phi_i component vector for superposition computation."""
        return {
            "density_gradient": self.density_gradient.magnitude,
            "spectral_drift": self.hyper_eigen.spectral_drift,
            "coupling": self.medium_coupling.coefficient,
            "scar_pressure": self.boundary_residual.scar_pressure,
            "topology_persistence": self.topology.persistence_ratio,
            "deposited_energy": self.deposited_energy.total,
        }


@dataclass(frozen=True)
class ActivationWeights:
    """Superposition weights for each encoded regime component."""

    density_gradient: float = 0.15
    spectral_drift: float = 0.20
    coupling: float = 0.25
    scar_pressure: float = 0.15
    topology_persistence: float = 0.10
    deposited_energy: float = 0.15

    def total_weight(self) -> float:
        return (
            self.density_gradient
            + self.spectral_drift
            + self.coupling
            + self.scar_pressure
            + self.topology_persistence
            + self.deposited_energy
        )


@dataclass(frozen=True)
class ThresholdVector:
    """Regime transition thresholds (analogue of Theta_i in the Lean model)."""

    density_gradient: float = 0.35  # gradient -> fracture
    spectral_drift: float = 0.50  # spectral -> mode switch
    coupling: float = 0.67  # coupling -> ignition
    scar_pressure: float = 0.50  # scar -> boundary instability
    topology_persistence: float = 0.33  # persistence -> percolation
    deposited_energy: float = 0.50  # energy -> thermal regime


# ---------------------------------------------------------------------------
# Boundary activation computation
# ---------------------------------------------------------------------------


def compute_total_activation(
    state: BoundaryActivationState,
    weights: ActivationWeights | None = None,
) -> float:
    """Compute B = sum alpha_i * phi_i, the total boundary activation.

    This is the superposition of encoded regime components.  When B exceeds
    the critical threshold, the boundary enters an active physical regime.
    """
    if weights is None:
        weights = ActivationWeights()
    phi = state.component_vector()
    total = (
        weights.density_gradient * phi["density_gradient"]
        + weights.spectral_drift * phi["spectral_drift"]
        + weights.coupling * phi["coupling"]
        + weights.scar_pressure * phi["scar_pressure"]
        + weights.topology_persistence * phi["topology_persistence"]
        + weights.deposited_energy * phi["deposited_energy"]
    )
    # Normalize by total weight to keep B in [0, 1]
    norm = weights.total_weight()
    return total / norm if norm > 0 else 0.0


CRITICAL_ACTIVATION_THRESHOLD = 0.5


def is_critically_activated(total_activation: float) -> bool:
    """Check whether B exceeds the critical threshold Theta_c."""
    return total_activation > CRITICAL_ACTIVATION_THRESHOLD


def count_thresholds_crossed(
    state: BoundaryActivationState,
    thresholds: ThresholdVector | None = None,
) -> dict[str, bool]:
    """Determine which individual component thresholds are crossed."""
    if thresholds is None:
        thresholds = ThresholdVector()
    phi = state.component_vector()
    return {
        "density_gradient": phi["density_gradient"] > thresholds.density_gradient,
        "spectral_drift": phi["spectral_drift"] > thresholds.spectral_drift,
        "coupling": phi["coupling"] > thresholds.coupling,
        "scar_pressure": phi["scar_pressure"] > thresholds.scar_pressure,
        "topology_persistence": phi["topology_persistence"]
        > thresholds.topology_persistence,
        "deposited_energy": phi["deposited_energy"] > thresholds.deposited_energy,
    }


def classify_boundary_activation(
    state: BoundaryActivationState,
    thresholds: ThresholdVector | None = None,
    weights: ActivationWeights | None = None,
) -> str:
    """Classify the boundary into an activation regime.

    Returns one of: latent, smooth, turbulent, percolating, switching,
    diverging, active, critical
    """
    B = compute_total_activation(state, weights)
    if not is_critically_activated(B):
        return "latent"

    crossed = count_thresholds_crossed(state, thresholds)
    count = sum(1 for v in crossed.values() if v)

    if count >= 4:
        return "critical"
    elif count >= 3:
        return "active"
    elif crossed.get("deposited_energy", False):
        return "diverging"
    elif crossed.get("spectral_drift", False):
        return "switching"
    elif crossed.get("coupling", False):
        return "turbulent"
    elif crossed.get("topology_persistence", False):
        return "percolating"
    elif crossed.get("density_gradient", False):
        return "smooth"
    else:
        return "latent"


# ---------------------------------------------------------------------------
# Canonical scenario builders
# ---------------------------------------------------------------------------


def zero_activation_state(label: str = "void interior") -> BoundaryActivationState:
    return BoundaryActivationState(
        density_gradient=DensityGradient(0.0, "tangential"),
        hyper_eigen=HyperEigenTransition(0.0, False),
        medium_coupling=MediumCoupling(0.0, False),
        boundary_residual=BoundaryResidual(0.0, 0.0),
        topology=TopologyPersistence(0, 0, 0, 0.0),
        deposited_energy=DepositedEnergy(0.0, 0.0),
        location_label=label,
        scale=1.0,
    )


def wall_fracture_scenario(label: str = "wall fracture") -> BoundaryActivationState:
    return BoundaryActivationState(
        density_gradient=DensityGradient(0.8, "outward"),
        hyper_eigen=HyperEigenTransition(0.2, False),
        medium_coupling=MediumCoupling(0.1, False),
        boundary_residual=BoundaryResidual(0.6, 0.4),
        topology=TopologyPersistence(3, 1, 0, 0.5),
        deposited_energy=DepositedEnergy(0.3, 0.7),
        location_label=label,
        scale=0.1,
    )


def atmospheric_ignition_scenario(
    label: str = "atmospheric ignition",
) -> BoundaryActivationState:
    return BoundaryActivationState(
        density_gradient=DensityGradient(0.9, "outward"),
        hyper_eigen=HyperEigenTransition(0.6, True),
        medium_coupling=MediumCoupling(0.9, True),
        boundary_residual=BoundaryResidual(0.4, 0.3),
        topology=TopologyPersistence(5, 2, 0, 0.7),
        deposited_energy=DepositedEnergy(0.8, 0.9),
        location_label=label,
        scale=0.05,
    )


def cosmic_filament_scenario(
    label: str = "cosmic filament wall",
) -> BoundaryActivationState:
    return BoundaryActivationState(
        density_gradient=DensityGradient(0.6, "inward"),
        hyper_eigen=HyperEigenTransition(0.4, False),
        medium_coupling=MediumCoupling(0.3, False),
        boundary_residual=BoundaryResidual(0.5, 0.2),
        topology=TopologyPersistence(200, 45, 12, 0.85),
        deposited_energy=DepositedEnergy(0.7, 0.05),
        location_label=label,
        scale=100.0,
    )


def hulk_punch_scenario(
    label: str = "hulk punch fracture",
) -> BoundaryActivationState:
    return BoundaryActivationState(
        density_gradient=DensityGradient(1.0, "outward"),
        hyper_eigen=HyperEigenTransition(0.7, True),
        medium_coupling=MediumCoupling(0.8, True),
        boundary_residual=BoundaryResidual(0.9, 0.9),
        topology=TopologyPersistence(50, 10, 3, 0.4),
        deposited_energy=DepositedEnergy(1.0, 1.0),
        location_label=label,
        scale=0.01,
    )


# ---------------------------------------------------------------------------
# Registry and receipt
# ---------------------------------------------------------------------------


def build_scenario_record(
    index: int,
    scenario_id: str,
    state: BoundaryActivationState,
    weights: ActivationWeights | None = None,
    thresholds: ThresholdVector | None = None,
) -> dict[str, Any]:
    if weights is None:
        weights = ActivationWeights()
    if thresholds is None:
        thresholds = ThresholdVector()

    B = compute_total_activation(state, weights)
    verdict = classify_boundary_activation(state, thresholds, weights)
    crossed = count_thresholds_crossed(state, thresholds)

    record = {
        "index": index,
        "scenario_id": scenario_id,
        "location_label": state.location_label,
        "scale": state.scale,
        "component_vector": state.component_vector(),
        "weights": asdict(weights),
        "thresholds": asdict(thresholds),
        "total_activation_B": round(B, 6),
        "critical_threshold": CRITICAL_ACTIVATION_THRESHOLD,
        "is_critical": is_critically_activated(B),
        "thresholds_crossed": crossed,
        "thresholds_crossed_count": sum(1 for v in crossed.values() if v),
        "activation_verdict": verdict,
        "density_gradient": {
            "magnitude": state.density_gradient.magnitude,
            "direction": state.density_gradient.direction,
        },
        "hyper_eigen": {
            "spectral_drift": state.hyper_eigen.spectral_drift,
            "regime_switch_active": state.hyper_eigen.regime_switch_active,
        },
        "medium_coupling": {
            "coefficient": state.medium_coupling.coefficient,
            "atmosphere_participating": state.medium_coupling.atmosphere_participating,
        },
        "boundary_residual": {
            "scar_pressure": state.boundary_residual.scar_pressure,
            "residual_growth_rate": state.boundary_residual.residual_growth_rate,
        },
        "topology": {
            "betti_connected": state.topology.betti_connected,
            "betti_loops": state.topology.betti_loops,
            "betti_cavities": state.topology.betti_cavities,
            "persistence_ratio": state.topology.persistence_ratio,
        },
        "deposited_energy": {
            "total": state.deposited_energy.total,
            "deposition_rate": state.deposited_energy.deposition_rate,
        },
    }
    record["record_hash"] = hash_obj({k: v for k, v in record.items() if k != "record_hash"})
    return record


_DEFAULT_WEIGHTS = ActivationWeights()
_DEFAULT_THRESHOLDS = ThresholdVector()

SCENARIOS: list[tuple[str, BoundaryActivationState]] = [
    ("zero_activation", zero_activation_state()),
    ("wall_fracture", wall_fracture_scenario()),
    ("atmospheric_ignition", atmospheric_ignition_scenario()),
    ("cosmic_filament", cosmic_filament_scenario()),
    ("hulk_punch", hulk_punch_scenario()),
]


def build_registry() -> dict[str, Any]:
    scenario_records = [
        build_scenario_record(
            i,
            sid,
            state,
            _DEFAULT_WEIGHTS,
            _DEFAULT_THRESHOLDS,
        )
        for i, (sid, state) in enumerate(SCENARIOS)
    ]

    return {
        "schema": "boundary_activation_field_registry_v1",
        "source_refs": [source_ref(path) for path in SOURCE_REFS],
        "claim_boundary": (
            "Boundary activation field B(x, r) model only. Classifies boundary "
            "regimes based on the weighted superposition of six encoded regime "
            "components: density gradient, hyper-eigen spectral drift, medium "
            "coupling, scar pressure, topology persistence, and deposited "
            "energy. Does not claim full cosmological or material-science "
            "predictive power without calibration to domain-specific data."
        ),
        "canonical_statement": (
            "A boundary is not where a system ends. A boundary is where "
            "accumulated encoded states become physically active."
        ),
        "superposition_equation": "B(x, r) = sum_i alpha_i * phi_i(x, r)",
        "critical_condition": "B > Theta_c => boundary enters active physical regime",
        "critical_threshold": CRITICAL_ACTIVATION_THRESHOLD,
        "default_weights": asdict(_DEFAULT_WEIGHTS),
        "default_thresholds": asdict(_DEFAULT_THRESHOLDS),
        "regime_map": {
            "latent": "no threshold crossed, boundary inactive",
            "smooth": "density gradient regime, elastic/smooth transition",
            "turbulent": "coupling regime, atmospheric ignition boundary",
            "percolating": "topology regime, filament/web connectivity",
            "switching": "spectral regime, eigenmode transition",
            "diverging": "energy regime, thermal/divergence front",
            "active": "3+ thresholds crossed, full boundary activation",
            "critical": "4+ thresholds crossed, topology-tear regime",
        },
        "scenarios": scenario_records,
        "aggregates": {
            "scenario_count": len(scenario_records),
            "activation_verdicts": {
                r["activation_verdict"]: sum(
                    1 for s in scenario_records if s["activation_verdict"] == r["activation_verdict"]
                )
                for r in scenario_records
            },
            "critical_count": sum(1 for s in scenario_records if s["is_critical"]),
        },
    }


def build_receipt(registry: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "boundary_activation_field_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "registry": rel(REGISTRY),
        "registry_hash": hash_obj(registry),
        "aggregates": registry["aggregates"],
        "decision": "ADMIT_BOUNDARY_ACTIVATION_FIELD",
        "claim_boundary": registry["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json(
            {k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}
        ).encode("utf-8")
    )
    return receipt


def write_summary(registry: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# Boundary Activation Field",
        "",
        f"Decision: `{receipt['decision']}`",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        registry["claim_boundary"],
        "",
        "## Canonical Statement",
        "",
        registry["canonical_statement"],
        "",
        "## Equations",
        "",
        f"- Superposition: `{registry['superposition_equation']}`",
        f"- Critical condition: `{registry['critical_condition']}`",
        f"- Theta_c = {registry['critical_threshold']}",
        "",
        "## Regime Map",
        "",
    ]
    for regime, description in registry["regime_map"].items():
        lines.append(f"- `{regime}`: {description}")
    lines.extend(
        [
            "",
            "## Scenarios",
            "",
            "| Scenario | Location | B | Critical | Thresholds Crossed | Verdict |",
            "|---|---|---|---|---|---|",
        ]
    )
    for s in registry["scenarios"]:
        lines.append(
            f"| `{s['scenario_id']}` | {s['location_label']} | "
            f"{s['total_activation_B']} | {s['is_critical']} | "
            f"{s['thresholds_crossed_count']} | `{s['activation_verdict']}` |"
        )
    lines.extend(
        [
            "",
            "## Aggregates",
            "",
            f"- Scenario count: {registry['aggregates']['scenario_count']}",
            f"- Critical count: {registry['aggregates']['critical_count']}",
            f"- Verdicts: {registry['aggregates']['activation_verdicts']}",
            "",
            "## Source Refs",
            "",
        ]
    )
    for source in registry["source_refs"]:
        lines.append(f"- `{source['path']}` exists: `{source['exists']}`")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tiddler(receipt: dict[str, Any]) -> None:
    text = f"""created: 20260512000000000
modified: 20260512000000000
tags: ResearchStack Encoding BoundaryActivation Receipt
title: Boundary Activation Field
type: text/vnd.tiddlywiki

! Boundary Activation Field

Durable runner:

```
4-Infrastructure/shim/boundary_activation_field_probe.py
```

Receipt:

```
{rel(RECEIPT)}
```

Receipt hash:

```
{receipt['receipt_hash']}
```

!! Doctrine

A boundary is not where a system ends. A boundary is where accumulated encoded states become physically active.

```
latent    -> no threshold crossed, boundary inactive
smooth    -> density gradient regime, elastic/smooth transition
turbulent -> coupling regime, atmospheric ignition boundary
percolating -> topology regime, filament/web connectivity
switching -> spectral regime, eigenmode transition
diverging -> energy regime, thermal/divergence front
active    -> 3+ thresholds crossed, full boundary activation
critical  -> 4+ thresholds crossed, topology-tear regime
```

!! Links

* [[ThresholdVector (Lean formalization)|ThresholdVector.lean]]
* [[Observer Chart Projection Guardrail]]
* [[Boundary Dynamics]]
"""
    TIDDLER.write_text(text, encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    registry = build_registry()
    receipt = build_receipt(registry)
    REGISTRY.write_text(
        json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    RECEIPT.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_summary(registry, receipt)
    write_tiddler(receipt)
    print(
        json.dumps(
            {
                "registry": rel(REGISTRY),
                "receipt": rel(RECEIPT),
                "summary": rel(SUMMARY),
                "tiddler": rel(TIDDLER),
                "receipt_hash": receipt["receipt_hash"],
                "decision": receipt["decision"],
                "aggregates": registry["aggregates"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
