#!/usr/bin/env python3
"""Force-like sector model under the 12D/4D/genus-3 residual regime.

This is an accounting model over the extracted Standard Model term-family graph:

* 12D source plane: visible symbolic term-family axes
* 4D primitive keel: field / shear / packet / spectral projection
* genus-3 residual boat: packet_local / shear_torsion / spectral_field handles

It does not model physical forces from first principles.  It asks how the
force-like sectors already present in the extracted equation grammar distribute
through the current compression regime.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
REDUCTION_RECEIPT = (
    REPO
    / "4-Infrastructure"
    / "hardware"
    / "standard_model_12_to_4_reduction_receipt.json"
)
BOAT_RECEIPT = (
    REPO
    / "4-Infrastructure"
    / "hardware"
    / "standard_model_genus3_residual_boat_receipt.json"
)
OUT = (
    REPO
    / "4-Infrastructure"
    / "hardware"
    / "standard_model_force_regime_model_receipt.json"
)

PRIMITIVES = ("field", "shear", "packet", "spectral")
HANDLES = ("packet_local", "shear_torsion", "spectral_field")

FORCE_SECTORS = {
    "strong_color": {
        "axes": ("su3_gluon_field", "nonabelian_self_interaction"),
        "meaning": "color gauge field plus nonabelian self-interaction grammar",
        "claim_boundary": "symbolic strong-sector proxy, not QCD dynamics",
    },
    "electroweak_charged": {
        "axes": ("electroweak_charged_w", "charged_current_ckm"),
        "meaning": "charged W and CKM current grammar",
        "claim_boundary": "symbolic charged weak proxy, not a weak-interaction calculation",
    },
    "electroweak_neutral": {
        "axes": ("electroweak_neutral_za",),
        "meaning": "neutral Z/A electroweak grammar visible in the equation wall",
        "claim_boundary": "symbolic neutral electroweak proxy; photon/Z separation is not performed",
    },
    "scalar_mass_yukawa": {
        "axes": ("higgs_goldstone_scalar", "scalar_potential", "yukawa_mass_coupling"),
        "meaning": "Higgs/Goldstone, scalar potential, and Yukawa/mass grammar",
        "claim_boundary": "symbolic scalar/mass-generation proxy, not Higgs-sector phenomenology",
    },
    "matter_current": {
        "axes": ("fermion_quark_sector", "fermion_lepton_sector"),
        "meaning": "fermion current matter grammar",
        "claim_boundary": "symbolic matter-current proxy, not a particle-spectrum model",
    },
    "gauge_fixing_ghost": {
        "axes": ("ghost_gaugefix_sector",),
        "meaning": "gauge-fixing and ghost grammar",
        "claim_boundary": "symbolic bookkeeping sector, not a physical force",
    },
    "kinetic_derivative": {
        "axes": ("derivative_kinetic_flow",),
        "meaning": "derivative and kinetic-flow grammar",
        "claim_boundary": "symbolic propagation/flow proxy, not a standalone force",
    },
    "gravity_external_slot": {
        "axes": (),
        "meaning": "reserved external slot because gravity is not part of this Standard Model source extraction",
        "claim_boundary": "no gravity force is inferred from the source equation wall",
    },
}


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fraction_str(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def fraction_json(value: Fraction) -> dict[str, Any]:
    return {
        "fraction": fraction_str(value),
        "numerator": value.numerator,
        "denominator": value.denominator,
        "decimal": float(value),
    }


def parse_fraction_json(item: dict[str, Any]) -> Fraction:
    return Fraction(int(item["numerator"]), int(item["denominator"]))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def vector_from_json(items: dict[str, dict[str, Any]]) -> dict[str, Fraction]:
    return {key: parse_fraction_json(value) for key, value in items.items()}


def projection_from_json(items: dict[str, dict[str, dict[str, Any]]]) -> dict[str, dict[str, Fraction]]:
    return {
        axis: {
            primitive: parse_fraction_json(weight)
            for primitive, weight in row.items()
        }
        for axis, row in items.items()
    }


def vector_json(vector: dict[str, Fraction]) -> dict[str, dict[str, Any]]:
    return {key: fraction_json(value) for key, value in sorted(vector.items())}


def signed_l1(vector: dict[str, Fraction]) -> Fraction:
    return sum((abs(value) for value in vector.values()), Fraction(0))


def sector_primitive_vector(
    axes: tuple[str, ...],
    centroid: dict[str, Fraction],
    projection: dict[str, dict[str, Fraction]],
) -> dict[str, Fraction]:
    vector = {primitive: Fraction(0) for primitive in PRIMITIVES}
    for axis in axes:
        for primitive, weight in projection[axis].items():
            vector[primitive] += centroid[axis] * weight
    return vector


def sector_handle_vector(
    axes: tuple[str, ...],
    handle_vectors: dict[str, dict[str, Fraction]],
) -> dict[str, Fraction]:
    vector = {handle: Fraction(0) for handle in HANDLES}
    for handle, residuals in handle_vectors.items():
        for axis in axes:
            vector[handle] += residuals.get(axis, Fraction(0))
    return vector


def dominant(vector: dict[str, Fraction]) -> dict[str, Any]:
    if not vector:
        return {"axis": None, "value": fraction_json(Fraction(0))}
    key, value = max(vector.items(), key=lambda item: abs(item[1]))
    return {"axis": key, "value": fraction_json(value)}


def build_receipt() -> dict[str, Any]:
    reduction = load_json(REDUCTION_RECEIPT)
    boat = load_json(BOAT_RECEIPT)
    centroid = vector_from_json(reduction["visible_centroid_12d"])
    projection = projection_from_json(reduction["projection_matrix_12_to_4"])
    handle_vectors = {
        handle: vector_from_json(vector)
        for handle, vector in boat["handle_vectors"].items()
    }

    sectors: dict[str, Any] = {}
    total_sector_mass = Fraction(0)
    total_primitive = {primitive: Fraction(0) for primitive in PRIMITIVES}
    total_handles = {handle: Fraction(0) for handle in HANDLES}

    for sector, spec in FORCE_SECTORS.items():
        axes = tuple(spec["axes"])
        centroid_mass = sum((centroid[axis] for axis in axes), Fraction(0))
        primitive_vector = sector_primitive_vector(axes, centroid, projection) if axes else {
            primitive: Fraction(0) for primitive in PRIMITIVES
        }
        handle_vector = sector_handle_vector(axes, handle_vectors) if axes else {
            handle: Fraction(0) for handle in HANDLES
        }
        total_sector_mass += centroid_mass
        for primitive in PRIMITIVES:
            total_primitive[primitive] += primitive_vector[primitive]
        for handle in HANDLES:
            total_handles[handle] += handle_vector[handle]
        sectors[sector] = {
            "axes": axes,
            "meaning": spec["meaning"],
            "centroid_mass": fraction_json(centroid_mass),
            "primitive_vector": vector_json(primitive_vector),
            "dominant_primitive": dominant(primitive_vector),
            "residual_handle_vector": vector_json(handle_vector),
            "residual_handle_l1": fraction_json(signed_l1(handle_vector)),
            "dominant_residual_handle": dominant(handle_vector),
            "claim_boundary": spec["claim_boundary"],
        }

    primitive_target = vector_from_json(reduction["visible_reduced_4d"])
    primitive_delta = {
        primitive: total_primitive[primitive] - primitive_target[primitive]
        for primitive in PRIMITIVES
    }
    residual_target = vector_from_json(reduction["residual_lane_12d"]["residual"])
    residual_total_by_handle = {
        handle: sum(handle_vectors[handle].values(), Fraction(0))
        for handle in HANDLES
    }
    handle_delta = {
        handle: total_handles[handle] - residual_total_by_handle[handle]
        for handle in HANDLES
    }

    receipt = {
        "schema": "standard_model_force_regime_model_receipt_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "surface_id": "standard_model_force_regime_model",
        "source": {
            "reduction_receipt": str(REDUCTION_RECEIPT.relative_to(REPO)),
            "reduction_stable_hash_sha256": reduction.get("stable_reduction_hash_sha256"),
            "boat_receipt": str(BOAT_RECEIPT.relative_to(REPO)),
            "boat_stable_hash_sha256": boat.get("stable_boat_hash_sha256"),
        },
        "regime": {
            "source_plane": "12D symbolic term-family axes",
            "primitive_keel": "4D field/shear/packet/spectral projection",
            "residual_boat": "genus-3 packet/shear/spectral-field handle carrier",
            "force_model": "force-like sectors are grouped from the visible Standard Model term grammar",
        },
        "force_like_sectors": sectors,
        "closure": {
            "sector_centroid_total": fraction_json(total_sector_mass),
            "sector_centroid_total_matches_one": total_sector_mass == 1,
            "primitive_total_from_sectors": vector_json(total_primitive),
            "primitive_target": vector_json(primitive_target),
            "primitive_delta": vector_json(primitive_delta),
            "primitive_delta_l1": fraction_json(signed_l1(primitive_delta)),
            "handle_total_from_sectors": vector_json(total_handles),
            "handle_signed_sum_target": vector_json(residual_total_by_handle),
            "handle_delta": vector_json(handle_delta),
            "handle_delta_l1": fraction_json(signed_l1(handle_delta)),
            "residual_l1_target": reduction["residual_lane_12d"]["residual_l1"],
            "residual_l1_from_axes": fraction_json(signed_l1(residual_target)),
            "closed": (
                total_sector_mass == 1
                and all(value == 0 for value in primitive_delta.values())
                and all(value == 0 for value in handle_delta.values())
            ),
        },
        "claim_boundary": (
            "This models how force-like symbolic sectors distribute through the "
            "current compression regime. It is not a numerical force law, "
            "cosmology, QFT calculation, gravity model, or empirical claim."
        ),
        "lawful": True,
    }

    stable_preimage = stable_json({
        "schema": receipt["schema"],
        "surface_id": receipt["surface_id"],
        "source": receipt["source"],
        "regime": receipt["regime"],
        "force_like_sectors": receipt["force_like_sectors"],
        "closure": receipt["closure"],
        "claim_boundary": receipt["claim_boundary"],
        "lawful": receipt["lawful"],
    }).encode("utf-8")
    receipt["stable_force_regime_hash_sha256"] = sha256_bytes(stable_preimage)
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
        "stable_force_regime_hash_sha256": receipt["stable_force_regime_hash_sha256"],
        "receipt_hash_preimage_sha256": receipt["receipt_hash_preimage_sha256"],
        "closed": receipt["closure"]["closed"],
        "sector_count": len(receipt["force_like_sectors"]),
        "force_like_sectors": {
            sector: {
                "centroid_mass": data["centroid_mass"],
                "dominant_primitive": data["dominant_primitive"],
                "dominant_residual_handle": data["dominant_residual_handle"],
            }
            for sector, data in receipt["force_like_sectors"].items()
        },
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
