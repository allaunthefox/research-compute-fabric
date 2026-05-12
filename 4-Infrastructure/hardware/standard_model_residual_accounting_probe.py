#!/usr/bin/env python3
"""Fine-grain residual accounting for the Standard Model eigen probe.

This joins the existing 12D->4D reduction, genus-3 residual boat, and
force-regime receipts.  The goal is not to assign physical meaning to every
residual, but to make every remainder inspectable before it is treated as
noise, sidecar debt, signal, or a failure boundary.
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
FORCE_RECEIPT = (
    REPO
    / "4-Infrastructure"
    / "hardware"
    / "standard_model_force_regime_model_receipt.json"
)
OUT = (
    REPO
    / "4-Infrastructure"
    / "hardware"
    / "standard_model_residual_accounting_probe_receipt.json"
)

PRIMITIVES = ("field", "shear", "packet", "spectral")
HANDLES = ("packet_local", "shear_torsion", "spectral_field")


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


def find_handle(axis: str, handle_vectors: dict[str, dict[str, Fraction]]) -> str:
    for handle, vector in handle_vectors.items():
        if axis in vector:
            return handle
    raise KeyError(f"residual axis has no handle: {axis}")


def find_sector(axis: str, force_sectors: dict[str, Any]) -> str:
    for sector, data in force_sectors.items():
        if axis in data.get("axes", []):
            return sector
    return "unassigned"


def dominant_primitive(weights: dict[str, Fraction]) -> str:
    return max(weights.items(), key=lambda item: item[1])[0]


def residual_scale_class(abs_value: Fraction, residual_l1: Fraction) -> str:
    if residual_l1 == 0:
        return "zero"
    share = abs_value / residual_l1
    if share >= Fraction(1, 8):
        return "major_structured"
    if share >= Fraction(1, 16):
        return "secondary_structured"
    if share >= Fraction(1, 64):
        return "fine_grain_candidate"
    return "micro_residual"


def correction_direction(value: Fraction) -> str:
    if value > 0:
        return "under_lifted_axis_add_back"
    if value < 0:
        return "over_lifted_axis_subtract_back"
    return "exact_axis_no_residual"


def sum_by_axis_property(
    axis_rows: dict[str, dict[str, Any]],
    property_name: str,
) -> dict[str, Fraction]:
    totals: dict[str, Fraction] = {}
    for row in axis_rows.values():
        key = row[property_name]
        totals.setdefault(key, Fraction(0))
        totals[key] += parse_fraction_json(row["abs_residual"])
    return totals


def weighted_primitive_pressure(
    residual: dict[str, Fraction],
    projection: dict[str, dict[str, Fraction]],
) -> dict[str, Fraction]:
    pressure = {primitive: Fraction(0) for primitive in PRIMITIVES}
    for axis, value in residual.items():
        for primitive, weight in projection[axis].items():
            pressure[primitive] += abs(value) * weight
    return pressure


def ranked_fraction_map(values: dict[str, Fraction]) -> list[dict[str, Any]]:
    return [
        {"axis": key, "value": fraction_json(value)}
        for key, value in sorted(values.items(), key=lambda item: abs(item[1]), reverse=True)
    ]


def build_receipt() -> dict[str, Any]:
    reduction = load_json(REDUCTION_RECEIPT)
    boat = load_json(BOAT_RECEIPT)
    force = load_json(FORCE_RECEIPT)

    centroid = vector_from_json(reduction["visible_centroid_12d"])
    lifted = vector_from_json(reduction["canonical_lift_4d_to_12d"]["lifted_centroid_12d"])
    residual = vector_from_json(reduction["residual_lane_12d"]["residual"])
    projection = projection_from_json(reduction["projection_matrix_12_to_4"])
    residual_l1 = parse_fraction_json(reduction["residual_lane_12d"]["residual_l1"])
    handle_vectors = {
        handle: vector_from_json(vector)
        for handle, vector in boat["handle_vectors"].items()
    }
    force_sectors = force["force_like_sectors"]

    axis_rows: dict[str, dict[str, Any]] = {}
    positive_mass = Fraction(0)
    negative_mass = Fraction(0)

    for axis in sorted(residual):
        value = residual[axis]
        abs_value = abs(value)
        if value > 0:
            positive_mass += value
        elif value < 0:
            negative_mass += -value
        weights = projection[axis]
        handle = find_handle(axis, handle_vectors)
        sector = find_sector(axis, force_sectors)
        axis_rows[axis] = {
            "axis": axis,
            "centroid": fraction_json(centroid[axis]),
            "lifted_from_4d": fraction_json(lifted[axis]),
            "residual": fraction_json(value),
            "abs_residual": fraction_json(abs_value),
            "residual_l1_share": fraction_json(abs_value / residual_l1 if residual_l1 else Fraction(0)),
            "centroid_relative_residual": fraction_json(
                abs_value / centroid[axis] if centroid[axis] else Fraction(0)
            ),
            "correction_direction": correction_direction(value),
            "scale_class": residual_scale_class(abs_value, residual_l1),
            "handle": handle,
            "sector": sector,
            "dominant_primitive": dominant_primitive(weights),
            "primitive_weights": vector_json(weights),
        }

    handle_pressure = sum_by_axis_property(axis_rows, "handle")
    sector_pressure = sum_by_axis_property(axis_rows, "sector")
    primitive_pressure = weighted_primitive_pressure(residual, projection)
    rehydrated_delta = {
        axis: lifted[axis] + residual[axis] - centroid[axis]
        for axis in residual
    }
    major_axes = [
        axis_rows[axis]
        for axis in sorted(axis_rows, key=lambda key: parse_fraction_json(axis_rows[key]["abs_residual"]), reverse=True)
        if axis_rows[axis]["scale_class"] in {"major_structured", "secondary_structured"}
    ]

    receipt = {
        "schema": "standard_model_residual_accounting_probe_receipt_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "surface_id": "standard_model_residual_accounting_probe",
        "source": {
            "reduction_receipt": str(REDUCTION_RECEIPT.relative_to(REPO)),
            "reduction_stable_hash_sha256": reduction.get("stable_reduction_hash_sha256"),
            "boat_receipt": str(BOAT_RECEIPT.relative_to(REPO)),
            "boat_stable_hash_sha256": boat.get("stable_boat_hash_sha256"),
            "force_receipt": str(FORCE_RECEIPT.relative_to(REPO)),
            "force_stable_hash_sha256": force.get("stable_force_regime_hash_sha256"),
        },
        "accounting_law": {
            "standard": "unexplained != disposable; unexplained -> accounted",
            "equation": "V_12 = lift_4_to_12(O_4) + R_12",
            "residual_handles": "R_12 = R_packet_local + R_shear_torsion + R_spectral_field",
            "promotion_boundary": "residuals may guide compression or routing only after closure and exact rehydration checks",
        },
        "axis_accounting": axis_rows,
        "fine_grain_summary": {
            "residual_l1": fraction_json(residual_l1),
            "positive_residual_mass": fraction_json(positive_mass),
            "negative_residual_mass_abs": fraction_json(negative_mass),
            "signed_residual_sum": fraction_json(sum(residual.values(), Fraction(0))),
            "major_or_secondary_axis_count": len(major_axes),
            "major_or_secondary_axes": major_axes,
            "handle_pressure_ranked": ranked_fraction_map(handle_pressure),
            "sector_pressure_ranked": ranked_fraction_map(sector_pressure),
            "primitive_pressure_ranked": ranked_fraction_map(primitive_pressure),
            "dominant_residual_handle": ranked_fraction_map(handle_pressure)[0],
            "dominant_residual_sector": ranked_fraction_map(sector_pressure)[0],
            "dominant_residual_primitive_pressure": ranked_fraction_map(primitive_pressure)[0],
        },
        "closure": {
            "rehydrated_delta": vector_json(rehydrated_delta),
            "rehydrated_delta_l1": fraction_json(signed_l1(rehydrated_delta)),
            "exact_rehydration": signed_l1(rehydrated_delta) == 0,
            "residual_l1_matches_reduction": residual_l1 == signed_l1(residual),
            "handle_pressure_l1_matches_residual_l1": sum(handle_pressure.values(), Fraction(0)) == residual_l1,
            "sector_pressure_l1_matches_residual_l1": sum(sector_pressure.values(), Fraction(0)) == residual_l1,
        },
        "claim_boundary": (
            "This classifies symbolic residual structure from the local Standard "
            "Model Lagrangian eigen probe. It is not a physical Standard Model "
            "calculation, particle claim, force law, or empirical prediction."
        ),
        "lawful": True,
    }

    stable_preimage = stable_json({
        "schema": receipt["schema"],
        "surface_id": receipt["surface_id"],
        "source": receipt["source"],
        "accounting_law": receipt["accounting_law"],
        "axis_accounting": receipt["axis_accounting"],
        "fine_grain_summary": receipt["fine_grain_summary"],
        "closure": receipt["closure"],
        "claim_boundary": receipt["claim_boundary"],
        "lawful": receipt["lawful"],
    }).encode("utf-8")
    receipt["stable_residual_accounting_hash_sha256"] = sha256_bytes(stable_preimage)
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
        "stable_residual_accounting_hash_sha256": receipt["stable_residual_accounting_hash_sha256"],
        "receipt_hash_preimage_sha256": receipt["receipt_hash_preimage_sha256"],
        "exact_rehydration": receipt["closure"]["exact_rehydration"],
        "residual_l1": receipt["fine_grain_summary"]["residual_l1"],
        "dominant_residual_handle": receipt["fine_grain_summary"]["dominant_residual_handle"],
        "dominant_residual_sector": receipt["fine_grain_summary"]["dominant_residual_sector"],
        "dominant_residual_primitive_pressure": receipt["fine_grain_summary"]["dominant_residual_primitive_pressure"],
        "major_or_secondary_axes": [
            {
                "axis": row["axis"],
                "scale_class": row["scale_class"],
                "residual": row["residual"],
                "handle": row["handle"],
                "sector": row["sector"],
            }
            for row in receipt["fine_grain_summary"]["major_or_secondary_axes"]
        ],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
