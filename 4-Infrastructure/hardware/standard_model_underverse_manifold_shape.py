#!/usr/bin/env python3
"""Manifold coordinate shape from visible/underverse Standard Model graph probes.

This builds a compact coordinate chart from:
- exact rational visible centroid
- exact underverse signed mirror
- targeted Q(phi) centroid displacement
- eigenvector sector axes
- complement residual mass
- antihydrogen gravity residual envelope as an external measured coordinate

It is a symbolic/compression manifold, not a physical spacetime manifold.
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

from standard_model_lagrangian_eigen_probe import NODES
from standard_model_lagrangian_exact_average import QPhi, fraction_str


REPO = Path(__file__).resolve().parents[2]
AVERAGE = REPO / "4-Infrastructure" / "hardware" / "standard_model_lagrangian_exact_average_receipt.json"
CLOSURE = REPO / "4-Infrastructure" / "hardware" / "standard_model_lagrangian_underverse_closure_receipt.json"
EIGEN = REPO / "4-Infrastructure" / "hardware" / "standard_model_lagrangian_eigen_probe_receipt.json"
OUT = REPO / "4-Infrastructure" / "hardware" / "standard_model_underverse_manifold_shape_receipt.json"
PHI = (1.0 + math.sqrt(5.0)) / 2.0


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_hash(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def frac_from_json(obj: dict[str, Any]) -> Fraction:
    return Fraction(int(obj["numerator"]), int(obj["denominator"]))


def fraction_json(value: Fraction) -> dict[str, Any]:
    return {
        "fraction": fraction_str(value),
        "numerator": value.numerator,
        "denominator": value.denominator,
        "decimal": float(value),
    }


def qphi_from_json(obj: dict[str, Any]) -> QPhi:
    return QPhi(Fraction(obj["a"]), Fraction(obj["b"]))


def load_receipts() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    return (
        json.loads(AVERAGE.read_text(encoding="utf-8")),
        json.loads(CLOSURE.read_text(encoding="utf-8")),
        json.loads(EIGEN.read_text(encoding="utf-8")),
    )


def visible_centroid(avg: dict[str, Any]) -> dict[str, Fraction]:
    return {
        item["node"]: frac_from_json(item["centroid_component"])
        for item in avg["rational_average"]["centroid_components"]
    }


def qphi_centroid(avg: dict[str, Any]) -> dict[str, QPhi]:
    return {
        item["node"]: qphi_from_json(item["centroid_component_qphi"])
        for item in avg["qphi_targeted_average"]["centroid_components_qphi"]
    }


def qphi_rational_delta(qphi: dict[str, QPhi], rational: dict[str, Fraction]) -> dict[str, QPhi]:
    return {
        node: qphi[node] - QPhi(rational[node], Fraction(0))
        for node in NODES
    }


def vector_norm(values: list[float]) -> float:
    return math.sqrt(sum(value * value for value in values))


def build_shape() -> dict[str, Any]:
    avg, closure, eigen = load_receipts()
    rational = visible_centroid(avg)
    mirror = {node: -value for node, value in rational.items()}
    closure_sum = {node: rational[node] + mirror[node] for node in NODES}
    qphi = qphi_centroid(avg)
    delta = qphi_rational_delta(qphi, rational)
    delta_values = [value.approx() for value in delta.values()]
    rational_values = [float(rational[node]) for node in NODES]
    mirror_values = [float(mirror[node]) for node in NODES]

    no_phi = next(mode for mode in eigen["modes"] if mode["phi_mode"] == "none")
    sector_phi = next(mode for mode in eigen["modes"] if mode["phi_mode"] == "sector_scale")
    omni_phi = next(mode for mode in eigen["modes"] if mode["phi_mode"] == "omni")
    top6_residual = frac_from_json(avg["rational_average"]["compressed_top_k"]["residual_mass"])

    # ALPHA-g 2023 central residual as external measurement coordinate:
    # a_hbar = (0.75 +/- sqrt(0.13^2 + 0.16^2)) g.
    antihydrogen_residual = -0.25
    antihydrogen_sigma = math.sqrt(0.13 * 0.13 + 0.16 * 0.16)
    antihydrogen_z = antihydrogen_residual / antihydrogen_sigma

    coordinates = {
        "visible_norm_l2": vector_norm(rational_values),
        "underverse_mirror_norm_l2": vector_norm(mirror_values),
        "signed_closure_norm_l1": sum(abs(float(value)) for value in closure_sum.values()),
        "signed_closure_exact_zero": all(value == 0 for value in closure_sum.values()),
        "qphi_delta_norm_l2": vector_norm(delta_values),
        "top6_residual_mass": fraction_json(top6_residual),
        "eigen_gap_no_phi": no_phi["spectral_gap_proxy"],
        "eigen_gap_sector_phi": sector_phi["spectral_gap_proxy"],
        "eigen_gap_omni_phi": omni_phi["spectral_gap_proxy"],
        "sector_phi_gap_lift": sector_phi["spectral_gap_proxy"] - no_phi["spectral_gap_proxy"],
        "omni_phi_gap_lift": omni_phi["spectral_gap_proxy"] - no_phi["spectral_gap_proxy"],
        "antihydrogen_gravity_residual_g": antihydrogen_residual,
        "antihydrogen_gravity_sigma_g": antihydrogen_sigma,
        "antihydrogen_gravity_z_score": antihydrogen_z,
    }

    dominant_axes = [
        {
            "axis": "visible_centroid",
            "node": max(rational, key=lambda node: rational[node]),
            "value": fraction_json(max(rational.values())),
        },
        {
            "axis": "underverse_mirror",
            "node": min(mirror, key=lambda node: mirror[node]),
            "value": fraction_json(min(mirror.values())),
        },
        {
            "axis": "qphi_delta",
            "node": max(delta, key=lambda node: delta[node].approx()),
            "value_qphi": delta[max(delta, key=lambda node: delta[node].approx())].as_json(),
        },
        {
            "axis": "eigen_no_phi",
            "node": no_phi["dominant_components"][0]["node"],
            "value": no_phi["dominant_components"][0]["component"],
        },
        {
            "axis": "eigen_sector_phi",
            "node": sector_phi["dominant_components"][0]["node"],
            "value": sector_phi["dominant_components"][0]["component"],
        },
    ]

    return {
        "schema": "standard_model_underverse_manifold_shape_v1",
        "coordinate_system": {
            "description": "Symbolic compression manifold chart from visible graph, underverse mirror, phi displacement, residual mass, eigen axes, and antihydrogen residual envelope.",
            "nodes": NODES,
            "basis": [
                "visible rational centroid",
                "signed underverse mirror",
                "targeted Q(phi) displacement",
                "top-k residual mass",
                "term-family eigen axes",
                "external antihydrogen gravity residual coordinate",
            ],
        },
        "coordinates": coordinates,
        "dominant_axes": dominant_axes,
        "closure_inputs": {
            "average_receipt": str(AVERAGE.relative_to(REPO)),
            "average_hash": file_hash(AVERAGE),
            "closure_receipt": str(CLOSURE.relative_to(REPO)),
            "closure_hash": file_hash(CLOSURE),
            "eigen_receipt": str(EIGEN.relative_to(REPO)),
            "eigen_hash": file_hash(EIGEN),
            "closure_exact": {
                "complement_edge_closed": closure["complement_closure"]["edge_closure"]["closed_exactly"],
                "annihilation_edge_closed": closure["annihilation_closure"]["edge_closure"]["closed_exactly"],
                "annihilation_centroid_closed": closure["annihilation_closure"]["centroid_closure"]["closed_exactly"],
                "qphi_annihilation_closed": closure["qphi_annihilation_closure"]["closed_exactly"],
            },
        },
        "claim_boundary": (
            "This is a symbolic/compression manifold chart. The antihydrogen residual "
            "coordinate is an experimental uncertainty-envelope coordinate, not a "
            "claim of physical divergence. The manifold is not a spacetime model."
        ),
    }


def build_receipt() -> dict[str, Any]:
    shape = build_shape()
    receipt = {
        "schema": "standard_model_underverse_manifold_shape_receipt_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "surface_id": "standard_model_underverse_manifold_shape",
        "shape": shape,
        "lawful": True,
        "claim_boundary": shape["claim_boundary"],
    }
    stable_preimage = stable_json({
        "schema": receipt["schema"],
        "surface_id": receipt["surface_id"],
        "shape": receipt["shape"],
        "lawful": receipt["lawful"],
        "claim_boundary": receipt["claim_boundary"],
    }).encode("utf-8")
    receipt["stable_shape_hash_sha256"] = sha256_bytes(stable_preimage)
    receipt["receipt_hash_preimage_sha256"] = sha256_bytes(stable_json(receipt).encode("utf-8"))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    receipt = build_receipt()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    coords = receipt["shape"]["coordinates"]
    print(json.dumps({
        "lawful": receipt["lawful"],
        "signed_closure_exact_zero": coords["signed_closure_exact_zero"],
        "visible_norm_l2": coords["visible_norm_l2"],
        "qphi_delta_norm_l2": coords["qphi_delta_norm_l2"],
        "top6_residual_mass": coords["top6_residual_mass"],
        "antihydrogen_gravity_z_score": coords["antihydrogen_gravity_z_score"],
        "dominant_axes": receipt["shape"]["dominant_axes"],
        "stable_shape_hash_sha256": receipt["stable_shape_hash_sha256"],
        "receipt_hash_preimage_sha256": receipt["receipt_hash_preimage_sha256"],
        "out": str(args.out.relative_to(REPO)) if args.out.is_relative_to(REPO) else str(args.out),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
