#!/usr/bin/env python3
"""Exact average/compressed centroid for the Standard Model Lagrangian wall.

This uses the same visible term-family extraction as
standard_model_lagrangian_eigen_probe.py, but computes exact rational averages
and a targeted phi average in Q(phi), where phi^2 = phi + 1.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any

from standard_model_lagrangian_eigen_probe import NODES, OBSERVATIONS


REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "4-Infrastructure" / "hardware" / "standard_model_lagrangian_exact_average_receipt.json"
PHI_FLOAT = (1.0 + math.sqrt(5.0)) / 2.0


GROUPS = {
    "gauge": {
        "su3_gluon_field",
        "nonabelian_self_interaction",
        "electroweak_charged_w",
        "electroweak_neutral_za",
    },
    "scalar": {"higgs_goldstone_scalar", "scalar_potential"},
    "fermion": {
        "fermion_quark_sector",
        "fermion_lepton_sector",
        "yukawa_mass_coupling",
        "charged_current_ckm",
    },
    "ghost": {"ghost_gaugefix_sector"},
    "derivative": {"derivative_kinetic_flow"},
}


@dataclass(frozen=True)
class QPhi:
    """Exact a + b phi element with phi^2 = phi + 1."""

    a: Fraction = Fraction(0)
    b: Fraction = Fraction(0)

    def __add__(self, other: QPhi) -> QPhi:
        return QPhi(self.a + other.a, self.b + other.b)

    def __sub__(self, other: QPhi) -> QPhi:
        return QPhi(self.a - other.a, self.b - other.b)

    def __mul__(self, other: QPhi) -> QPhi:
        # (a + bφ)(c + dφ) = ac + (ad+bc)φ + bdφ²
        # φ² = φ + 1
        return QPhi(
            self.a * other.a + self.b * other.b,
            self.a * other.b + self.b * other.a + self.b * other.b,
        )

    def inv(self) -> QPhi:
        # conjugate of c+dφ is c+d-dφ because φ' = 1-φ
        norm = self.a * self.a + self.a * self.b - self.b * self.b
        if norm == 0:
            raise ZeroDivisionError("QPhi element has zero norm")
        return QPhi((self.a + self.b) / norm, -self.b / norm)

    def __truediv__(self, other: QPhi) -> QPhi:
        return self * other.inv()

    def approx(self) -> float:
        return float(self.a) + float(self.b) * PHI_FLOAT

    def as_json(self) -> dict[str, Any]:
        return {
            "a": fraction_str(self.a),
            "b": fraction_str(self.b),
            "form": f"({fraction_str(self.a)}) + ({fraction_str(self.b)})*phi",
            "approx": self.approx(),
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


def is_scalar_touched(left: str, right: str) -> bool:
    fields = (left, right)
    return any("higgs" in field or "scalar" in field for field in fields)


def exact_rational_average() -> dict[str, Any]:
    weights = [Fraction(int(weight)) for _left, _right, weight, _note in OBSERVATIONS]
    total_edge_weight = sum(weights, Fraction(0))
    observation_count = Fraction(len(OBSERVATIONS))
    strengths = {node: Fraction(0) for node in NODES}
    for left, right, weight, _note in OBSERVATIONS:
        w = Fraction(int(weight))
        strengths[left] += w
        strengths[right] += w
    total_incident_weight = sum(strengths.values(), Fraction(0))
    centroid = {
        node: strengths[node] / total_incident_weight
        for node in NODES
    }
    grouped = {}
    for group, nodes in GROUPS.items():
        grouped[group] = sum((centroid[node] for node in nodes), Fraction(0))
    ranked = sorted(
        [
            {
                "node": node,
                "incident_weight": fraction_json(strengths[node]),
                "centroid_component": fraction_json(centroid[node]),
            }
            for node in NODES
        ],
        key=lambda item: item["centroid_component"]["decimal"],
        reverse=True,
    )
    top_k = 6
    top_nodes = ranked[:top_k]
    residual_mass = Fraction(1) - sum(Fraction(item["centroid_component"]["numerator"], item["centroid_component"]["denominator"]) for item in top_nodes)
    return {
        "schema": "exact_rational_term_family_average_v1",
        "observation_count": len(OBSERVATIONS),
        "total_edge_weight": fraction_json(total_edge_weight),
        "average_edge_weight": fraction_json(total_edge_weight / observation_count),
        "total_incident_weight": fraction_json(total_incident_weight),
        "centroid_components": ranked,
        "group_centroid": {
            group: fraction_json(value)
            for group, value in sorted(grouped.items(), key=lambda item: float(item[1]), reverse=True)
        },
        "compressed_top_k": {
            "k": top_k,
            "top_nodes": top_nodes,
            "residual_mass": fraction_json(residual_mass),
            "claim_boundary": "Top-k centroid is a lossy compressed summary unless the residual node list is retained.",
        },
    }


def phi_targeted_average() -> dict[str, Any]:
    strengths = {node: QPhi() for node in NODES}
    total = QPhi()
    for left, right, weight, _note in OBSERVATIONS:
        w = Fraction(int(weight))
        q_weight = QPhi(Fraction(0), w) if is_scalar_touched(left, right) else QPhi(w, Fraction(0))
        strengths[left] = strengths[left] + q_weight
        strengths[right] = strengths[right] + q_weight
        total = total + q_weight + q_weight
    centroid = {node: strengths[node] / total for node in NODES}
    grouped = {}
    for group, nodes in GROUPS.items():
        value = QPhi()
        for node in nodes:
            value = value + centroid[node]
        grouped[group] = value
    ranked = sorted(
        [
            {
                "node": node,
                "incident_weight_qphi": strengths[node].as_json(),
                "centroid_component_qphi": centroid[node].as_json(),
            }
            for node in NODES
        ],
        key=lambda item: item["centroid_component_qphi"]["approx"],
        reverse=True,
    )
    return {
        "schema": "exact_qphi_targeted_average_v1",
        "total_incident_weight_qphi": total.as_json(),
        "centroid_components_qphi": ranked,
        "group_centroid_qphi": {
            group: value.as_json()
            for group, value in sorted(grouped.items(), key=lambda item: item[1].approx(), reverse=True)
        },
        "claim_boundary": "Q(phi) average is exact for targeted scalar-sector phi weighting only; omni fractional phi powers are intentionally excluded from exact mode.",
    }


def build_receipt() -> dict[str, Any]:
    rational = exact_rational_average()
    qphi = phi_targeted_average()
    receipt = {
        "schema": "standard_model_lagrangian_exact_average_receipt_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "surface_id": "standard_model_lagrangian_exact_average",
        "source": {
            "basis": "manual term-family extraction from standard_model_lagrangian_eigen_probe.py",
            "node_count": len(NODES),
            "observation_count": len(OBSERVATIONS),
            "nodes": NODES,
        },
        "rational_average": rational,
        "qphi_targeted_average": qphi,
        "lawful": True,
        "claim_boundary": (
            "This is an exact average over the extracted term-family graph, not an "
            "average of the physical Standard Model action, fields, amplitudes, "
            "mass spectrum, or path integral."
        ),
    }
    stable_preimage = stable_json({
        "schema": receipt["schema"],
        "surface_id": receipt["surface_id"],
        "source": receipt["source"],
        "rational_average": receipt["rational_average"],
        "qphi_targeted_average": receipt["qphi_targeted_average"],
        "lawful": receipt["lawful"],
        "claim_boundary": receipt["claim_boundary"],
    }).encode("utf-8")
    receipt["stable_average_hash_sha256"] = sha256_bytes(stable_preimage)
    receipt["receipt_hash_preimage_sha256"] = sha256_bytes(stable_json(receipt).encode("utf-8"))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    receipt = build_receipt()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    rational = receipt["rational_average"]
    qphi = receipt["qphi_targeted_average"]
    print(json.dumps({
        "lawful": receipt["lawful"],
        "stable_average_hash_sha256": receipt["stable_average_hash_sha256"],
        "receipt_hash_preimage_sha256": receipt["receipt_hash_preimage_sha256"],
        "average_edge_weight": rational["average_edge_weight"],
        "top_rational_component": rational["centroid_components"][0],
        "top_group": next(iter(rational["group_centroid"].items())),
        "top_qphi_component": qphi["centroid_components_qphi"][0],
        "top_qphi_group": next(iter(qphi["group_centroid_qphi"].items())),
        "out": str(args.out.relative_to(REPO)) if args.out.is_relative_to(REPO) else str(args.out),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
