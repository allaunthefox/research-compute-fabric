#!/usr/bin/env python3
"""Guided virtual-connectome reconfiguration runner.

This is the non-autonomous middle stage: it takes a guarded retune candidate,
recomputes the projection/residual geometry in a sandboxed receipt, and decides
whether the change is ready for a route trial, should stay diagnostic, or must
fail closed.

It deliberately does not rewrite the canonical Standard Model projection.
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
W_GUARD_RECEIPT = (
    REPO
    / "4-Infrastructure"
    / "hardware"
    / "standard_model_w_conservation_guard_receipt.json"
)
OUT = (
    REPO
    / "4-Infrastructure"
    / "hardware"
    / "standard_model_connectome_reconfiguration_receipt.json"
)

PRIMITIVES = ("field", "shear", "packet", "spectral")


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


def projection_from_json(items: dict[str, dict[str, dict[str, Any]]]) -> dict[str, dict[str, Fraction]]:
    return {
        axis: {
            primitive: parse_fraction_json(weight)
            for primitive, weight in row.items()
        }
        for axis, row in items.items()
    }


def projection_json(projection: dict[str, dict[str, Fraction]]) -> dict[str, dict[str, dict[str, Any]]]:
    return {
        axis: {
            primitive: fraction_json(weight)
            for primitive, weight in sorted(row.items())
            if weight
        }
        for axis, row in sorted(projection.items())
    }


def signed_l1(vector: dict[str, Fraction]) -> Fraction:
    return sum((abs(value) for value in vector.values()), Fraction(0))


def project_12_to_4(
    centroid: dict[str, Fraction],
    projection: dict[str, dict[str, Fraction]],
) -> dict[str, Fraction]:
    reduced = {primitive: Fraction(0) for primitive in PRIMITIVES}
    for axis, mass in centroid.items():
        for primitive, weight in projection[axis].items():
            reduced[primitive] += mass * weight
    return reduced


def lift_4_to_12(
    reduced: dict[str, Fraction],
    projection: dict[str, dict[str, Fraction]],
) -> dict[str, Fraction]:
    support_weight_sum = {primitive: Fraction(0) for primitive in PRIMITIVES}
    for row in projection.values():
        for primitive, weight in row.items():
            support_weight_sum[primitive] += weight

    lifted = {axis: Fraction(0) for axis in projection}
    for axis, row in projection.items():
        for primitive, weight in row.items():
            if support_weight_sum[primitive]:
                lifted[axis] += reduced[primitive] * weight / support_weight_sum[primitive]
    return lifted


def evaluate_projection(
    centroid: dict[str, Fraction],
    projection: dict[str, dict[str, Fraction]],
) -> dict[str, Any]:
    reduced = project_12_to_4(centroid, projection)
    lifted = lift_4_to_12(reduced, projection)
    residual = {
        axis: centroid[axis] - lifted[axis]
        for axis in centroid
    }
    rehydrated_delta = {
        axis: lifted[axis] + residual[axis] - centroid[axis]
        for axis in centroid
    }
    return {
        "reduced_4d": reduced,
        "lifted_12d": lifted,
        "residual_12d": residual,
        "residual_l1": signed_l1(residual),
        "rehydrated_delta": rehydrated_delta,
        "rehydrated_delta_l1": signed_l1(rehydrated_delta),
        "exact_rehydration": signed_l1(rehydrated_delta) == 0,
    }


def row_from_guard_json(row: dict[str, dict[str, Any]]) -> dict[str, Fraction]:
    return {
        primitive: parse_fraction_json(value)
        for primitive, value in row.items()
    }


def row_support(row: dict[str, Fraction]) -> tuple[str, ...]:
    return tuple(sorted(row))


def row_cost(row: dict[str, Fraction]) -> int:
    """Tiny metadata proxy: primitive count plus denominator complexity."""
    return len(row) + sum(value.denominator for value in row.values())


def residual_pressure_by_handle(
    residual: dict[str, Fraction],
    boat: dict[str, Any],
) -> dict[str, Fraction]:
    pressure = {handle: Fraction(0) for handle in boat["handle_vectors"]}
    for handle, vector in boat["handle_vectors"].items():
        for axis in vector:
            pressure[handle] += abs(residual[axis])
    return pressure


def ranked_fraction_map(values: dict[str, Fraction]) -> list[dict[str, Any]]:
    return [
        {"axis": key, "value": fraction_json(value)}
        for key, value in sorted(values.items(), key=lambda item: abs(item[1]), reverse=True)
    ]


def ranked_abs_vector(vector: dict[str, Fraction], limit: int = 8) -> list[dict[str, Any]]:
    return [
        {
            "axis": key,
            "value": fraction_json(value),
            "absolute": fraction_json(abs(value)),
        }
        for key, value in sorted(vector.items(), key=lambda item: abs(item[1]), reverse=True)[:limit]
    ]


def decide(
    guard_passes: bool,
    exact_rehydration: bool,
    residual_improvement: Fraction,
    support_preserved: bool,
    metadata_cost_proxy: int,
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if not exact_rehydration:
        return "nan0_fail_closed", ["exact rehydration failed"]
    if residual_improvement <= 0:
        return "diagnostic_only", ["candidate does not improve residual_l1"]
    if not guard_passes:
        return "diagnostic_only", ["guard did not pass"]
    if not support_preserved:
        return "diagnostic_only", ["candidate changes primitive support"]
    reasons.append("guard passed")
    reasons.append("exact rehydration remained closed")
    reasons.append("residual_l1 improved")
    reasons.append("primitive support preserved")
    reasons.append(f"metadata_cost_proxy={metadata_cost_proxy} is recorded but not byte-priced")
    return "hold_for_route_trial", reasons


def build_receipt() -> dict[str, Any]:
    reduction = load_json(REDUCTION_RECEIPT)
    boat = load_json(BOAT_RECEIPT)
    guard = load_json(W_GUARD_RECEIPT)

    centroid = vector_from_json(reduction["visible_centroid_12d"])
    baseline_projection = projection_from_json(reduction["projection_matrix_12_to_4"])
    guarded = guard["candidate_classification"]["best_support_preserving_candidate"]
    axis = guarded["axis"]
    candidate_row = row_from_guard_json(guarded["candidate_row"])
    baseline_row = baseline_projection[axis]

    trial_projection = {
        key: dict(value)
        for key, value in baseline_projection.items()
    }
    trial_projection[axis] = candidate_row

    baseline_eval = evaluate_projection(centroid, baseline_projection)
    trial_eval = evaluate_projection(centroid, trial_projection)
    residual_improvement = baseline_eval["residual_l1"] - trial_eval["residual_l1"]
    support_preserved = row_support(baseline_row) == row_support(candidate_row)
    metadata_cost_proxy = row_cost(candidate_row) - row_cost(baseline_row)
    decision, reasons = decide(
        guard_passes=bool(guarded["passes_guard"]),
        exact_rehydration=bool(trial_eval["exact_rehydration"]),
        residual_improvement=residual_improvement,
        support_preserved=support_preserved,
        metadata_cost_proxy=metadata_cost_proxy,
    )
    residual_delta = {
        key: trial_eval["residual_12d"][key] - baseline_eval["residual_12d"][key]
        for key in centroid
    }
    baseline_handle_pressure = residual_pressure_by_handle(baseline_eval["residual_12d"], boat)
    trial_handle_pressure = residual_pressure_by_handle(trial_eval["residual_12d"], boat)
    handle_pressure_delta = {
        handle: trial_handle_pressure[handle] - baseline_handle_pressure[handle]
        for handle in baseline_handle_pressure
    }

    receipt = {
        "schema": "standard_model_connectome_reconfiguration_receipt_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "surface_id": "standard_model_connectome_reconfiguration",
        "source": {
            "reduction_receipt": str(REDUCTION_RECEIPT.relative_to(REPO)),
            "reduction_stable_hash_sha256": reduction.get("stable_reduction_hash_sha256"),
            "boat_receipt": str(BOAT_RECEIPT.relative_to(REPO)),
            "boat_stable_hash_sha256": boat.get("stable_boat_hash_sha256"),
            "w_guard_receipt": str(W_GUARD_RECEIPT.relative_to(REPO)),
            "w_guard_stable_hash_sha256": guard.get("stable_w_conservation_guard_hash_sha256"),
        },
        "reconfiguration_scope": {
            "mode": "guided_local_retune",
            "autonomy_level": "human_gated_candidate_generation",
            "canonical_projection_rewritten": False,
            "axis": axis,
        },
        "candidate": {
            "axis": axis,
            "baseline_row": {
                primitive: fraction_json(value)
                for primitive, value in sorted(baseline_row.items())
            },
            "candidate_row": {
                primitive: fraction_json(value)
                for primitive, value in sorted(candidate_row.items())
            },
            "guard_status": guarded["status"],
            "guard_reasons": guarded["reasons"],
            "support_preserved": support_preserved,
            "metadata_cost_proxy_delta": metadata_cost_proxy,
        },
        "baseline": {
            "residual_l1": fraction_json(baseline_eval["residual_l1"]),
            "reduced_4d": vector_json(baseline_eval["reduced_4d"]),
            "top_residual_axes": ranked_abs_vector(baseline_eval["residual_12d"]),
            "handle_pressure": ranked_fraction_map(baseline_handle_pressure),
        },
        "trial": {
            "residual_l1": fraction_json(trial_eval["residual_l1"]),
            "residual_l1_improvement": fraction_json(residual_improvement),
            "residual_l1_improvement_ratio": fraction_json(
                residual_improvement / baseline_eval["residual_l1"]
                if baseline_eval["residual_l1"]
                else Fraction(0)
            ),
            "reduced_4d": vector_json(trial_eval["reduced_4d"]),
            "top_residual_axes": ranked_abs_vector(trial_eval["residual_12d"]),
            "residual_delta_top_axes": ranked_abs_vector(residual_delta),
            "handle_pressure": ranked_fraction_map(trial_handle_pressure),
            "handle_pressure_delta": ranked_fraction_map(handle_pressure_delta),
            "exact_rehydration": trial_eval["exact_rehydration"],
            "rehydrated_delta_l1": fraction_json(trial_eval["rehydrated_delta_l1"]),
        },
        "decision": {
            "status": decision,
            "reasons": reasons,
            "next_required_actions": [
                "do not rewrite canonical projection yet",
                "run downstream residual-accounting and force-regime probes against the trial projection",
                "price projection-row metadata before compression promotion",
                "promote only if exact receipt boundary and objective both improve",
            ],
        },
        "claim_boundary": (
            "This is a guided virtual-connectome reconfiguration receipt. It "
            "tests a local symbolic projection retune without claiming autonomous "
            "metatyping, physical Standard Model correction, or compression proof."
        ),
        "lawful": True,
    }
    stable_preimage = stable_json({
        "schema": receipt["schema"],
        "surface_id": receipt["surface_id"],
        "source": receipt["source"],
        "reconfiguration_scope": receipt["reconfiguration_scope"],
        "candidate": receipt["candidate"],
        "baseline": receipt["baseline"],
        "trial": receipt["trial"],
        "decision": receipt["decision"],
        "claim_boundary": receipt["claim_boundary"],
        "lawful": receipt["lawful"],
    }).encode("utf-8")
    receipt["stable_connectome_reconfiguration_hash_sha256"] = sha256_bytes(stable_preimage)
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
        "stable_connectome_reconfiguration_hash_sha256": receipt["stable_connectome_reconfiguration_hash_sha256"],
        "receipt_hash_preimage_sha256": receipt["receipt_hash_preimage_sha256"],
        "axis": receipt["candidate"]["axis"],
        "decision": receipt["decision"],
        "baseline_residual_l1": receipt["baseline"]["residual_l1"],
        "trial_residual_l1": receipt["trial"]["residual_l1"],
        "residual_l1_improvement": receipt["trial"]["residual_l1_improvement"],
        "residual_l1_improvement_ratio": receipt["trial"]["residual_l1_improvement_ratio"],
        "exact_rehydration": receipt["trial"]["exact_rehydration"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
