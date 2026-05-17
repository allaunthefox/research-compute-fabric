#!/usr/bin/env python3
"""Genus-3 residual boat for the Standard Model 12-to-4 reduction.

This probes the user's "boat in the math sea" idea as a concrete stabilizer:
the exact 12D residual lane is partitioned into three handle vectors.  The boat
is lawful only if the three handles add back to the original residual exactly.

This is a compression/topology control object, not a physical claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
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
OUT = (
    REPO
    / "4-Infrastructure"
    / "hardware"
    / "standard_model_genus3_residual_boat_receipt.json"
)

HANDLES = ("packet_local", "shear_torsion", "spectral_field")

HANDLE_MAP = {
    "packet_local": {
        "fermion_quark_sector",
        "fermion_lepton_sector",
        "yukawa_mass_coupling",
        "charged_current_ckm",
        "ghost_gaugefix_sector",
    },
    "shear_torsion": {
        "nonabelian_self_interaction",
        "electroweak_charged_w",
        "derivative_kinetic_flow",
    },
    "spectral_field": {
        "su3_gluon_field",
        "electroweak_neutral_za",
        "higgs_goldstone_scalar",
        "scalar_potential",
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


def vector_json(vector: dict[str, Fraction]) -> dict[str, dict[str, Any]]:
    return {key: fraction_json(value) for key, value in sorted(vector.items())}


def signed_l1(vector: dict[str, Fraction]) -> Fraction:
    return sum((abs(value) for value in vector.values()), Fraction(0))


def signed_l2_float(vector: dict[str, Fraction]) -> float:
    return math.sqrt(sum(float(value) ** 2 for value in vector.values()))


def positive_mass(vector: dict[str, Fraction]) -> Fraction:
    return sum((value for value in vector.values() if value > 0), Fraction(0))


def negative_mass_abs(vector: dict[str, Fraction]) -> Fraction:
    return sum((-value for value in vector.values() if value < 0), Fraction(0))


def ranked_abs_vector(vector: dict[str, Fraction], limit: int = 6) -> list[dict[str, Any]]:
    ranked = sorted(vector.items(), key=lambda item: abs(item[1]), reverse=True)
    return [
        {
            "axis": key,
            "value": fraction_json(value),
            "absolute": fraction_json(abs(value)),
        }
        for key, value in ranked[:limit]
    ]


def validate_handle_map(residual_axes: set[str]) -> list[str]:
    errors: list[str] = []
    assigned: set[str] = set()
    for handle, axes in HANDLE_MAP.items():
        unknown = sorted(axes - residual_axes)
        if unknown:
            errors.append(f"{handle} has unknown axes: {unknown}")
        overlap = sorted(assigned & axes)
        if overlap:
            errors.append(f"{handle} overlaps previous handles: {overlap}")
        assigned |= axes
    missing = sorted(residual_axes - assigned)
    if missing:
        errors.append(f"unassigned residual axes: {missing}")
    return errors


def handle_vectors(residual: dict[str, Fraction]) -> dict[str, dict[str, Fraction]]:
    vectors: dict[str, dict[str, Fraction]] = {}
    for handle, axes in HANDLE_MAP.items():
        vectors[handle] = {
            axis: residual[axis]
            for axis in sorted(axes)
        }
    return vectors


def sum_handle_vectors(vectors: dict[str, dict[str, Fraction]], axes: list[str]) -> dict[str, Fraction]:
    summed = {axis: Fraction(0) for axis in axes}
    for vector in vectors.values():
        for axis, value in vector.items():
            summed[axis] += value
    return summed


def handle_summary(handle: str, vector: dict[str, Fraction]) -> dict[str, Any]:
    signed_sum = sum(vector.values(), Fraction(0))
    l1 = signed_l1(vector)
    pos = positive_mass(vector)
    neg = negative_mass_abs(vector)
    return {
        "handle": handle,
        "axis_count": len(vector),
        "signed_sum": fraction_json(signed_sum),
        "positive_mass": fraction_json(pos),
        "negative_mass_abs": fraction_json(neg),
        "l1": fraction_json(l1),
        "l2": signed_l2_float(vector),
        "dominant_axes": ranked_abs_vector(vector, limit=4),
        "interpretation": {
            "packet_local": "localized fermion, witness, ghost, and coupling residual channel",
            "shear_torsion": "interaction-gradient, derivative-flow, and W-spine residual channel",
            "spectral_field": "field-density, neutral gauge, scalar, and mode residual channel",
        }[handle],
    }


def build_receipt() -> dict[str, Any]:
    reduction = load_json(REDUCTION_RECEIPT)
    residual = vector_from_json(reduction["residual_lane_12d"]["residual"])
    axes = sorted(residual)
    errors = validate_handle_map(set(axes))
    if errors:
        raise ValueError("; ".join(errors))

    vectors = handle_vectors(residual)
    summed = sum_handle_vectors(vectors, axes)
    closure_delta = {
        axis: summed[axis] - residual[axis]
        for axis in axes
    }
    handle_rollups = {
        handle: handle_summary(handle, vectors[handle])
        for handle in HANDLES
    }
    residual_l1 = signed_l1(residual)
    handle_l1_sum = sum(
        (parse_fraction_json(handle_rollups[handle]["l1"]) for handle in HANDLES),
        Fraction(0),
    )
    signed_total = sum(residual.values(), Fraction(0))
    max_handle_l1 = max(
        parse_fraction_json(handle_rollups[handle]["l1"])
        for handle in HANDLES
    )
    boat_freeboard = residual_l1 - max_handle_l1

    receipt = {
        "schema": "standard_model_genus3_residual_boat_receipt_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "surface_id": "standard_model_genus3_residual_boat",
        "source": {
            "reduction_receipt": str(REDUCTION_RECEIPT.relative_to(REPO)),
            "reduction_stable_hash_sha256": reduction.get("stable_reduction_hash_sha256"),
            "residual_l1": reduction["residual_lane_12d"]["residual_l1"],
        },
        "boat_model": {
            "name": "genus3_residual_boat",
            "sea": "the 12D residual correction field after 4D primitive projection",
            "hull": "bounded residual envelope measured by residual L1",
            "keel": "the 4D primitive vector from the 12-to-4 reduction",
            "ballast": "signed handle sums; total must remain zero to avoid drift",
            "handles": {
                handle: sorted(axes)
                for handle, axes in HANDLE_MAP.items()
            },
        },
        "keel_4d": reduction["visible_reduced_4d"],
        "handle_vectors": {
            handle: vector_json(vector)
            for handle, vector in vectors.items()
        },
        "handle_rollups": handle_rollups,
        "closure": {
            "three_handles_sum_to_residual": all(value == 0 for value in closure_delta.values()),
            "closure_l1_error": fraction_json(signed_l1(closure_delta)),
            "closure_delta": vector_json(closure_delta),
        },
        "bounded_boat_metrics": {
            "hull_capacity_l1": fraction_json(residual_l1),
            "handle_l1_sum": fraction_json(handle_l1_sum),
            "max_handle_l1": fraction_json(max_handle_l1),
            "freeboard_l1": fraction_json(boat_freeboard),
            "signed_total": fraction_json(signed_total),
            "zero_drift": signed_total == 0,
            "dominant_handle": max(
                HANDLES,
                key=lambda handle: parse_fraction_json(handle_rollups[handle]["l1"]),
            ),
            "bounded": (
                all(value == 0 for value in closure_delta.values())
                and signed_total == 0
                and handle_l1_sum == residual_l1
                and boat_freeboard >= 0
            ),
        },
        "claim_boundary": (
            "This tests a genus-3 residual carrier for a symbolic compression "
            "residual. It is not a physical universe topology, cosmological "
            "claim, Standard Model result, or empirical statement."
        ),
        "lawful": True,
    }

    stable_preimage = stable_json({
        "schema": receipt["schema"],
        "surface_id": receipt["surface_id"],
        "source": receipt["source"],
        "boat_model": receipt["boat_model"],
        "keel_4d": receipt["keel_4d"],
        "handle_vectors": receipt["handle_vectors"],
        "handle_rollups": receipt["handle_rollups"],
        "closure": receipt["closure"],
        "bounded_boat_metrics": receipt["bounded_boat_metrics"],
        "claim_boundary": receipt["claim_boundary"],
        "lawful": receipt["lawful"],
    }).encode("utf-8")
    receipt["stable_boat_hash_sha256"] = sha256_bytes(stable_preimage)
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
        "stable_boat_hash_sha256": receipt["stable_boat_hash_sha256"],
        "receipt_hash_preimage_sha256": receipt["receipt_hash_preimage_sha256"],
        "bounded": receipt["bounded_boat_metrics"]["bounded"],
        "zero_drift": receipt["bounded_boat_metrics"]["zero_drift"],
        "dominant_handle": receipt["bounded_boat_metrics"]["dominant_handle"],
        "hull_capacity_l1": receipt["bounded_boat_metrics"]["hull_capacity_l1"],
        "handle_l1": {
            handle: receipt["handle_rollups"][handle]["l1"]
            for handle in HANDLES
        },
        "closure": receipt["closure"]["three_handles_sum_to_residual"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
