#!/usr/bin/env python3
"""Combined holographic encoding + Menger-style carving via threshold-band exclusion.

Instead of removing coordinates (Menger), the beam superposition B(x, r)
carves voids by threshold-band non-activation: at each point, only structures
whose lambda-band matches the local B value materialize.  Everything else is
"void" at that point.

This gives a scaffold where multiple structures share coordinates but separate
in lambda-space.  The expansion-space cost is lambda-separation, not
coordinate-buffer volume.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "holographic_carving"
REGISTRY = OUT_DIR / "holographic_carving_registry.json"
RECEIPT = OUT_DIR / "holographic_carving_receipt.json"
SUMMARY = OUT_DIR / "holographic_carving.md"
TIDDLER = (
    REPO
    / "6-Documentation"
    / "tiddlywiki-local"
    / "wiki"
    / "tiddlers"
    / "Holographic Carving.tid"
)

SOURCE_REFS = [
    REPO
    / "0-Core-Formalism"
    / "lean"
    / "Semantics"
    / "Semantics"
    / "LogogramRotationLoop.lean",
    REPO
    / "0-Core-Formalism"
    / "lean"
    / "Semantics"
    / "Semantics"
    / "ThresholdVector.lean",
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
# Core types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ThresholdBand:
    lower: float
    upper: float


@dataclass(frozen=True)
class ProjectionLayer:
    angle: float
    encoding: dict[str, float]  # phi vector
    band: ThresholdBand
    label: str


@dataclass(frozen=True)
class CarvingVoxel:
    """A point in the volume: what materializes depends on B(x)."""
    x: float
    y: float
    z: float
    B: float
    active_structures: dict[str, bool]


# ---------------------------------------------------------------------------
# Carving engine
# ---------------------------------------------------------------------------


def band_contains(B: float, band: ThresholdBand) -> bool:
    return band.lower <= B <= band.upper


def integrate_beam(layers: list[ProjectionLayer], weights: dict[str, float]) -> float:
    """Compute B = sum alpha_i * phi_i over all layers."""
    total = 0.0
    for layer in layers:
        for comp, val in layer.encoding.items():
            total += weights.get(comp, 0.0) * val
    weight_sum = sum(weights.values())
    return total / weight_sum if weight_sum > 0 else 0.0


def resolve_voxel(
    B: float,
    layers: list[ProjectionLayer],
    critical_threshold: float,
) -> dict[str, bool]:
    """At a point with total activation B, which structures materialize?"""
    critical = B >= critical_threshold
    return {
        layer.label: (critical and band_contains(B, layer.band))
        for layer in layers
    }


def carve_volume(
    layers: list[ProjectionLayer],
    weights: dict[str, float],
    critical_threshold: float,
    resolution: int = 4,
) -> list[CarvingVoxel]:
    """Evaluate B(x) over a 3D grid, producing active/void at each voxel."""
    voxels = []
    B_beam = integrate_beam(layers, weights)
    for i in range(resolution):
        for j in range(resolution):
            for k in range(resolution):
                x = i / (resolution - 1) if resolution > 1 else 0.5
                y = j / (resolution - 1) if resolution > 1 else 0.5
                z = k / (resolution - 1) if resolution > 1 else 0.5
                # In the combined model, B varies across the volume.
                # For this probe, we modulate B by position to show
                # spatial variation in threshold-band activation.
                B_local = B_beam * (1.0 - 0.3 * ((x - 0.5) ** 2 + (y - 0.5) ** 2 + (z - 0.5) ** 2) / 0.75)
                active = resolve_voxel(B_local, layers, critical_threshold)
                voxels.append(CarvingVoxel(x, y, z, round(B_local, 4), active))
    return voxels


def count_active_voxels(voxels: list[CarvingVoxel], structure_label: str) -> int:
    return sum(1 for v in voxels if v.active_structures.get(structure_label, False))


def count_void_voxels(voxels: list[CarvingVoxel]) -> int:
    return sum(1 for v in voxels if not any(v.active_structures.values()))


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

LOW_BAND = ThresholdBand(0.0, 0.35)
MID_BAND = ThresholdBand(0.35, 0.65)
HIGH_BAND = ThresholdBand(0.65, 1.0)

DEFAULT_WEIGHTS = {
    "density_gradient": 0.20,
    "spectral_drift": 0.20,
    "coupling": 0.20,
    "scar_pressure": 0.15,
    "topology_persistence": 0.10,
    "deposited_energy": 0.15,
}

DEFAULT_CRITICAL = 0.5


def single_structure_scenario() -> dict[str, Any]:
    """Baseline: one beam, one structure (pre-holographic)."""
    layers = [
        ProjectionLayer(
            angle=0.0,
            encoding={"density_gradient": 1.0, "spectral_drift": 0.0,
                       "coupling": 0.0, "scar_pressure": 0.0,
                       "topology_persistence": 0.0, "deposited_energy": 0.0},
            band=LOW_BAND,
            label="single_structure",
        )
    ]
    B_beam = integrate_beam(layers, DEFAULT_WEIGHTS)
    voxels = carve_volume(layers, DEFAULT_WEIGHTS, DEFAULT_CRITICAL, resolution=4)
    return {
        "scenario_id": "single_structure_baseline",
        "n_layers": len(layers),
        "n_structures": 1,
        "B_beam": round(B_beam, 4),
        "total_voxels": len(voxels),
        "active_voxels": {
            "single_structure": count_active_voxels(voxels, "single_structure"),
        },
        "void_voxels": count_void_voxels(voxels),
        "packing_efficiency": round(count_active_voxels(voxels, "single_structure") / len(voxels), 4),
    }


def three_structure_scenario() -> dict[str, Any]:
    """Three structures in one beam, separated by threshold bands."""
    layers = [
        ProjectionLayer(
            angle=0.0,
            encoding={"density_gradient": 0.5, "spectral_drift": 0.0,
                       "coupling": 0.0, "scar_pressure": 0.0,
                       "topology_persistence": 0.0, "deposited_energy": 0.0},
            band=LOW_BAND,
            label="density_scaffold",
        ),
        ProjectionLayer(
            angle=0.333,
            encoding={"density_gradient": 0.0, "spectral_drift": 1.0,
                       "coupling": 0.0, "scar_pressure": 0.0,
                       "topology_persistence": 0.0, "deposited_energy": 0.0},
            band=MID_BAND,
            label="spectral_filament",
        ),
        ProjectionLayer(
            angle=0.667,
            encoding={"density_gradient": 0.0, "spectral_drift": 0.0,
                       "coupling": 0.0, "scar_pressure": 0.0,
                       "topology_persistence": 1.0, "deposited_energy": 1.0},
            band=HIGH_BAND,
            label="topology_web",
        ),
    ]
    B_beam = integrate_beam(layers, DEFAULT_WEIGHTS)
    voxels = carve_volume(layers, DEFAULT_WEIGHTS, DEFAULT_CRITICAL, resolution=4)
    active_counts = {
        label: count_active_voxels(voxels, label)
        for label in ["density_scaffold", "spectral_filament", "topology_web"]
    }
    total_active = sum(active_counts.values())
    return {
        "scenario_id": "three_structure_holographic",
        "n_layers": len(layers),
        "n_structures": 3,
        "B_beam": round(B_beam, 4),
        "total_voxels": len(voxels),
        "active_voxels": active_counts,
        "total_active_voxels": total_active,
        "void_voxels": count_void_voxels(voxels),
        "packing_efficiency": round(total_active / len(voxels), 4),
        "structures_per_beam": 3,
    }


def carving_void_scenario() -> dict[str, Any]:
    """Menger-like carving: structures create voids in each other's bands."""
    layers = [
        ProjectionLayer(
            angle=0.0,
            encoding={"density_gradient": 0.8, "spectral_drift": 0.0,
                       "coupling": 0.0, "scar_pressure": 0.0,
                       "topology_persistence": 0.0, "deposited_energy": 0.0},
            band=LOW_BAND,
            label="scaffold",
        ),
        ProjectionLayer(
            angle=0.5,
            encoding={"density_gradient": 0.0, "spectral_drift": 0.0,
                       "coupling": 0.0, "scar_pressure": 0.0,
                       "topology_persistence": 0.0, "deposited_energy": 1.0},
            band=HIGH_BAND,
            label="energy_void",
        ),
    ]
    B_beam = integrate_beam(layers, DEFAULT_WEIGHTS)
    voxels = carve_volume(layers, DEFAULT_WEIGHTS, DEFAULT_CRITICAL, resolution=6)
    scaffold_active = count_active_voxels(voxels, "scaffold")
    void_active = count_active_voxels(voxels, "energy_void")
    void_count = count_void_voxels(voxels)
    return {
        "scenario_id": "carving_void",
        "n_layers": len(layers),
        "n_structures": 2,
        "B_beam": round(B_beam, 4),
        "total_voxels": len(voxels),
        "active_voxels": {
            "scaffold": scaffold_active,
            "energy_void": void_active,
        },
        "void_voxels": void_count,
        "scaffold_void_ratio": round(scaffold_active / void_count, 4) if void_count else -1,
        "packing_efficiency": round((scaffold_active + void_active) / len(voxels), 4),
    }


# ---------------------------------------------------------------------------
# Registry and receipt
# ---------------------------------------------------------------------------


def build_registry() -> dict[str, Any]:
    scenarios = [
        single_structure_scenario(),
        three_structure_scenario(),
        carving_void_scenario(),
    ]
    return {
        "schema": "holographic_carving_registry_v1",
        "source_refs": [source_ref(path) for path in SOURCE_REFS],
        "claim_boundary": (
            "Combined holographic encoding + Menger-style carving demo. "
            "The beam superposition carries multiple structures; threshold-band "
            "filtering determines which materialize at each voxel. "
            "Does not claim physical printing fidelity without dose-calibration."
        ),
        "canonical_statement": (
            "Voids are not removed coordinates. "
            "Voids are un-activated threshold bands at a given boundary point."
        ),
        "superposition_equation": "B(x) = sum_i alpha_i * phi_i(x)",
        "carving_rule": "structure S materializes at x iff B(x) in band(S) AND B(x) >= critical",
        "void_rule": "point x is void iff B(x) < critical OR B(x) not in any structure's band",
        "critical_threshold": DEFAULT_CRITICAL,
        "default_weights": DEFAULT_WEIGHTS,
        "scenarios": scenarios,
        "aggregates": {
            "scenario_count": len(scenarios),
            "total_structures": sum(s["n_structures"] for s in scenarios),
            "total_active_voxels": sum(s.get("total_active_voxels", s.get("active_voxels", {}).get(list(s["active_voxels"].keys())[0], 0)) for s in scenarios),
        },
    }


def build_receipt(registry: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "holographic_carving_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "registry": rel(REGISTRY),
        "registry_hash": hash_obj(registry),
        "aggregates": registry["aggregates"],
        "decision": "ADMIT_HOLOGRAPHIC_CARVING_MODEL",
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
        "# Holographic Carving — Combined Encoding + Threshold-Band Carving",
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
        f"- Carving rule: `{registry['carving_rule']}`",
        f"- Void rule: `{registry['void_rule']}`",
        f"- Critical threshold = {registry['critical_threshold']}",
        "",
        "## Scenarios",
        "",
        "| Scenario | Structures | B_beam | Voxels | Active | Void | Efficiency |",
        "|---|---|---|---|---|---|---|",
    ]
    for s in registry["scenarios"]:
        active = s.get("total_active_voxels", list(s["active_voxels"].values())[0])
        lines.append(
            f"| `{s['scenario_id']}` | {s['n_structures']} | {s['B_beam']} | "
            f"{s['total_voxels']} | {active} | {s['void_voxels']} | {s['packing_efficiency']} |"
        )
    lines.extend(
        [
            "",
            "## Active Voxel Detail",
            "",
        ]
    )
    for s in registry["scenarios"]:
        lines.append(f"### {s['scenario_id']}")
        for label, count in s.get("active_voxels", {}).items():
            ratio = round(count / s["total_voxels"], 3)
            lines.append(f"- `{label}`: {count} / {s['total_voxels']} voxels ({ratio})")
    lines.extend(
        [
            "",
            "## Aggregates",
            "",
            f"- Scenario count: {registry['aggregates']['scenario_count']}",
            f"- Total structures: {registry['aggregates']['total_structures']}",
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
tags: ResearchStack Encoding HolographicCarving Receipt
title: Holographic Carving
type: text/vnd.tiddlywiki

! Holographic Carving — Encoding + Threshold-Band Carving

Durable runner:

```
4-Infrastructure/shim/holographic_carving_probe.py
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

Voids are not removed coordinates. Voids are un-activated threshold bands at a given boundary point.

!! Links

* [[LogogramRotationLoop (Lean formalization)|LogogramRotationLoop.lean]]
* [[ThresholdVector (Lean formalization)|ThresholdVector.lean]]
* [[Boundary Activation Field]]
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
