#!/usr/bin/env python3
"""Reduce the extracted Standard Model Lagrangian term axes from 12 to 4.

The input is the symbolic term-family centroid from
standard_model_lagrangian_exact_average.py.  This is a compression/control-plane
projection, not a physical reduction of the Standard Model.

The four target primitives are the local OTOM primitives:

* field    - value/density surface
* shear    - gradient, coupling, torsion, transformation
* packet   - localized event/witness/claim-like object
* spectral - eigenmode, covariance, resonance, residual spectrum

Because a 12 -> 4 projection is lossy, this runner also emits the exact 12D
residual lane required to rehydrate the symbolic centroid byte-for-byte at the
rational-coordinate level.
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
AVERAGE_RECEIPT = (
    REPO
    / "4-Infrastructure"
    / "hardware"
    / "standard_model_lagrangian_exact_average_receipt.json"
)
SIGNED_AXIS_RECEIPT = (
    REPO
    / "4-Infrastructure"
    / "hardware"
    / "standard_model_signed_axis_graph_receipt.json"
)
OUT = (
    REPO
    / "4-Infrastructure"
    / "hardware"
    / "standard_model_12_to_4_reduction_receipt.json"
)

PRIMITIVES = ("field", "shear", "packet", "spectral")

# Row-stochastic projection matrix from unreduced term-family axes to the four
# local primitives.  Rows intentionally sum to exactly 1.
PROJECTION: dict[str, dict[str, Fraction]] = {
    "su3_gluon_field": {
        "field": Fraction(1, 2),
        "spectral": Fraction(1, 2),
    },
    "nonabelian_self_interaction": {
        "shear": Fraction(1, 3),
        "spectral": Fraction(2, 3),
    },
    "electroweak_charged_w": {
        "field": Fraction(1, 3),
        "shear": Fraction(1, 3),
        "spectral": Fraction(1, 3),
    },
    "electroweak_neutral_za": {
        "field": Fraction(1, 2),
        "spectral": Fraction(1, 2),
    },
    "higgs_goldstone_scalar": {
        "field": Fraction(1, 2),
        "shear": Fraction(1, 2),
    },
    "scalar_potential": {
        "field": Fraction(1, 2),
        "spectral": Fraction(1, 2),
    },
    "fermion_quark_sector": {
        "field": Fraction(1, 3),
        "packet": Fraction(2, 3),
    },
    "fermion_lepton_sector": {
        "field": Fraction(1, 3),
        "packet": Fraction(2, 3),
    },
    "yukawa_mass_coupling": {
        "shear": Fraction(1, 4),
        "packet": Fraction(1, 2),
        "spectral": Fraction(1, 4),
    },
    "charged_current_ckm": {
        "shear": Fraction(1, 4),
        "packet": Fraction(1, 2),
        "spectral": Fraction(1, 4),
    },
    "ghost_gaugefix_sector": {
        "shear": Fraction(1, 2),
        "packet": Fraction(1, 2),
    },
    "derivative_kinetic_flow": {
        "shear": Fraction(2, 3),
        "spectral": Fraction(1, 3),
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


def centroid_from_average(receipt: dict[str, Any]) -> dict[str, Fraction]:
    centroid: dict[str, Fraction] = {}
    for item in receipt["rational_average"]["centroid_components"]:
        centroid[item["node"]] = parse_fraction_json(item["centroid_component"])
    return centroid


def projection_json() -> dict[str, dict[str, dict[str, Any]]]:
    return {
        node: {
            primitive: fraction_json(weight)
            for primitive, weight in weights.items()
        }
        for node, weights in PROJECTION.items()
    }


def validate_projection(nodes: list[str]) -> list[str]:
    errors: list[str] = []
    missing = sorted(set(nodes) - set(PROJECTION))
    extra = sorted(set(PROJECTION) - set(nodes))
    if missing:
        errors.append(f"missing projection rows: {missing}")
    if extra:
        errors.append(f"extra projection rows: {extra}")
    for node in nodes:
        row = PROJECTION.get(node, {})
        row_sum = sum(row.values(), Fraction(0))
        unknown = sorted(set(row) - set(PRIMITIVES))
        if row_sum != 1:
            errors.append(f"{node} projection row sums to {fraction_str(row_sum)}, not 1")
        if unknown:
            errors.append(f"{node} projection row has unknown primitives: {unknown}")
    return errors


def project_12_to_4(centroid: dict[str, Fraction]) -> dict[str, Fraction]:
    reduced = {primitive: Fraction(0) for primitive in PRIMITIVES}
    for node, mass in centroid.items():
        for primitive, weight in PROJECTION[node].items():
            reduced[primitive] += mass * weight
    return reduced


def lift_4_to_12(reduced: dict[str, Fraction]) -> dict[str, Fraction]:
    """A deterministic canonical lift from 4D to 12D.

    This lift distributes each primitive's mass back over all term axes that
    participated in that primitive, proportional to the same projection row
    weight.  It is deliberately not claimed to be the original graph.  The
    residual lane below is what makes exact rehydration possible.
    """

    support_weight_sum = {primitive: Fraction(0) for primitive in PRIMITIVES}
    for row in PROJECTION.values():
        for primitive, weight in row.items():
            support_weight_sum[primitive] += weight

    lifted = {node: Fraction(0) for node in PROJECTION}
    for node, row in PROJECTION.items():
        for primitive, weight in row.items():
            lifted[node] += reduced[primitive] * weight / support_weight_sum[primitive]
    return lifted


def signed_l1(vector: dict[str, Fraction]) -> Fraction:
    return sum((abs(value) for value in vector.values()), Fraction(0))


def vector_json(vector: dict[str, Fraction]) -> dict[str, dict[str, Any]]:
    return {
        key: fraction_json(value)
        for key, value in sorted(vector.items())
    }


def ranked_abs_vector(vector: dict[str, Fraction], limit: int = 8) -> list[dict[str, Any]]:
    ranked = sorted(vector.items(), key=lambda item: abs(item[1]), reverse=True)
    return [
        {
            "axis": key,
            "value": fraction_json(value),
            "absolute": fraction_json(abs(value)),
        }
        for key, value in ranked[:limit]
    ]


def build_receipt() -> dict[str, Any]:
    average = load_json(AVERAGE_RECEIPT)
    signed_axis = load_json(SIGNED_AXIS_RECEIPT) if SIGNED_AXIS_RECEIPT.exists() else {}
    nodes = average["source"]["nodes"]
    projection_errors = validate_projection(nodes)
    if projection_errors:
        raise ValueError("; ".join(projection_errors))

    centroid = centroid_from_average(average)
    reduced = project_12_to_4(centroid)
    reduced_mirror = {primitive: -value for primitive, value in reduced.items()}
    reduced_closure = {
        primitive: reduced[primitive] + reduced_mirror[primitive]
        for primitive in PRIMITIVES
    }

    lifted = lift_4_to_12(reduced)
    residual = {
        node: centroid[node] - lifted[node]
        for node in nodes
    }
    rehydrated = {
        node: lifted[node] + residual[node]
        for node in nodes
    }
    rehydration_delta = {
        node: rehydrated[node] - centroid[node]
        for node in nodes
    }

    residual_mirror = {node: -value for node, value in residual.items()}
    residual_closure = {
        node: residual[node] + residual_mirror[node]
        for node in nodes
    }

    reduced_total = sum(reduced.values(), Fraction(0))
    lifted_total = sum(lifted.values(), Fraction(0))
    centroid_total = sum(centroid.values(), Fraction(0))

    receipt = {
        "schema": "standard_model_12_to_4_reduction_receipt_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "surface_id": "standard_model_12_to_4_reduction",
        "source": {
            "average_receipt": str(AVERAGE_RECEIPT.relative_to(REPO)),
            "average_stable_hash_sha256": average.get("stable_average_hash_sha256"),
            "signed_axis_receipt": str(SIGNED_AXIS_RECEIPT.relative_to(REPO)),
            "signed_axis_stable_hash_sha256": signed_axis.get("stable_graph_hash_sha256"),
            "nodes": nodes,
        },
        "primitive_basis": {
            "field": "density/value surface coordinate",
            "shear": "gradient, coupling, torsion, and transformation coordinate",
            "packet": "localized event, witness, claim, or receipt coordinate",
            "spectral": "eigenmode, covariance, resonance, and residual-spectrum coordinate",
        },
        "projection_matrix_12_to_4": projection_json(),
        "projection_law": {
            "row_stochastic": True,
            "row_sum": "1",
            "meaning": (
                "Every unreduced term-family axis contributes all of its centroid "
                "mass into the four-primitives control basis."
            ),
        },
        "visible_centroid_12d": vector_json(centroid),
        "visible_reduced_4d": vector_json(reduced),
        "reduced_4d_total": fraction_json(reduced_total),
        "mirror_reduced_4d": vector_json(reduced_mirror),
        "mirror_closure_4d": {
            "closed": all(value == 0 for value in reduced_closure.values()),
            "l1_error": fraction_json(signed_l1(reduced_closure)),
            "components": vector_json(reduced_closure),
        },
        "canonical_lift_4d_to_12d": {
            "lift_rule": (
                "Distribute each primitive mass back over supporting term axes "
                "proportional to the projection row weight."
            ),
            "lifted_centroid_12d": vector_json(lifted),
            "lifted_total": fraction_json(lifted_total),
        },
        "residual_lane_12d": {
            "meaning": (
                "Exact rational sidecar required to reconstruct the original "
                "12-axis centroid after the lossy 12-to-4 projection."
            ),
            "residual": vector_json(residual),
            "residual_l1": fraction_json(signed_l1(residual)),
            "top_residual_axes": ranked_abs_vector(residual),
            "mirror_residual": vector_json(residual_mirror),
            "mirror_residual_closure": {
                "closed": all(value == 0 for value in residual_closure.values()),
                "l1_error": fraction_json(signed_l1(residual_closure)),
            },
        },
        "exact_rehydration": {
            "closed": all(value == 0 for value in rehydration_delta.values()),
            "l1_error": fraction_json(signed_l1(rehydration_delta)),
            "centroid_total": fraction_json(centroid_total),
            "rehydrated_total": fraction_json(sum(rehydrated.values(), Fraction(0))),
        },
        "claim_boundary": (
            "This is a symbolic compression projection over the extracted "
            "term-family graph. It is not a physical Standard Model reduction, "
            "renormalization result, hidden-particle claim, or new equation of "
            "motion."
        ),
        "lawful": True,
    }

    stable_preimage = stable_json({
        "schema": receipt["schema"],
        "surface_id": receipt["surface_id"],
        "source": receipt["source"],
        "primitive_basis": receipt["primitive_basis"],
        "projection_matrix_12_to_4": receipt["projection_matrix_12_to_4"],
        "projection_law": receipt["projection_law"],
        "visible_centroid_12d": receipt["visible_centroid_12d"],
        "visible_reduced_4d": receipt["visible_reduced_4d"],
        "mirror_closure_4d": receipt["mirror_closure_4d"],
        "canonical_lift_4d_to_12d": receipt["canonical_lift_4d_to_12d"],
        "residual_lane_12d": receipt["residual_lane_12d"],
        "exact_rehydration": receipt["exact_rehydration"],
        "claim_boundary": receipt["claim_boundary"],
        "lawful": receipt["lawful"],
    }).encode("utf-8")
    receipt["stable_reduction_hash_sha256"] = sha256_bytes(stable_preimage)
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
        "stable_reduction_hash_sha256": receipt["stable_reduction_hash_sha256"],
        "receipt_hash_preimage_sha256": receipt["receipt_hash_preimage_sha256"],
        "visible_reduced_4d": receipt["visible_reduced_4d"],
        "mirror_closure_4d": receipt["mirror_closure_4d"]["closed"],
        "residual_l1": receipt["residual_lane_12d"]["residual_l1"],
        "exact_rehydration": receipt["exact_rehydration"]["closed"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
