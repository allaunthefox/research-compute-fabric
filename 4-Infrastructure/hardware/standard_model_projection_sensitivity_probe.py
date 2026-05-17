#!/usr/bin/env python3
"""Projection sensitivity probe for the Standard Model residual geometry.

This tests whether the fine-grain residuals point to useful local retunes of
the 12D -> 4D projection matrix.  It searches bounded rational row-stochastic
rows for one axis at a time and reports candidate reductions in residual L1.

The probe is diagnostic.  It does not replace the canonical projection unless a
later route pays the header/receipt cost and preserves exact rehydration.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
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
ACCOUNTING_RECEIPT = (
    REPO
    / "4-Infrastructure"
    / "hardware"
    / "standard_model_residual_accounting_probe_receipt.json"
)
OUT = (
    REPO
    / "4-Infrastructure"
    / "hardware"
    / "standard_model_projection_sensitivity_probe_receipt.json"
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


def residual_for_projection(
    centroid: dict[str, Fraction],
    projection: dict[str, dict[str, Fraction]],
) -> dict[str, Fraction]:
    reduced = project_12_to_4(centroid, projection)
    lifted = lift_4_to_12(reduced, projection)
    return {axis: centroid[axis] - lifted[axis] for axis in centroid}


def candidate_rows(max_denominator: int) -> list[dict[str, Fraction]]:
    rows: dict[str, dict[str, Fraction]] = {}
    for denom in range(1, max_denominator + 1):
        for counts in itertools.product(range(denom + 1), repeat=len(PRIMITIVES)):
            if sum(counts) != denom:
                continue
            row = {
                primitive: Fraction(count, denom)
                for primitive, count in zip(PRIMITIVES, counts, strict=True)
                if count
            }
            if not row:
                continue
            key = stable_json({k: fraction_str(v) for k, v in row.items()})
            rows[key] = row
    return list(rows.values())


def support(row: dict[str, Fraction]) -> tuple[str, ...]:
    return tuple(primitive for primitive in PRIMITIVES if row.get(primitive, 0))


def row_distance(a: dict[str, Fraction], b: dict[str, Fraction]) -> Fraction:
    return sum((abs(a.get(p, 0) - b.get(p, 0)) for p in PRIMITIVES), Fraction(0))


def row_complexity(row: dict[str, Fraction]) -> int:
    return len(row) + sum(value.denominator for value in row.values())


def build_receipt(max_denominator: int, top_n: int) -> dict[str, Any]:
    reduction = load_json(REDUCTION_RECEIPT)
    accounting = load_json(ACCOUNTING_RECEIPT)
    centroid = vector_from_json(reduction["visible_centroid_12d"])
    baseline_projection = projection_from_json(reduction["projection_matrix_12_to_4"])
    baseline_residual = residual_for_projection(centroid, baseline_projection)
    baseline_l1 = signed_l1(baseline_residual)
    rows = candidate_rows(max_denominator)

    high_pressure_axes = [
        row["axis"]
        for row in accounting["fine_grain_summary"]["major_or_secondary_axes"]
    ]

    all_results: list[dict[str, Any]] = []
    best_by_axis: dict[str, dict[str, Any]] = {}

    for axis in high_pressure_axes:
        baseline_row = baseline_projection[axis]
        axis_results: list[dict[str, Any]] = []
        for candidate in rows:
            trial_projection = {
                key: dict(value)
                for key, value in baseline_projection.items()
            }
            trial_projection[axis] = candidate
            trial_residual = residual_for_projection(centroid, trial_projection)
            trial_l1 = signed_l1(trial_residual)
            improvement = baseline_l1 - trial_l1
            if improvement <= 0:
                continue
            result = {
                "axis": axis,
                "baseline_row": {
                    primitive: fraction_json(value)
                    for primitive, value in sorted(baseline_row.items())
                },
                "candidate_row": {
                    primitive: fraction_json(value)
                    for primitive, value in sorted(candidate.items())
                },
                "baseline_residual_l1": fraction_json(baseline_l1),
                "candidate_residual_l1": fraction_json(trial_l1),
                "residual_l1_improvement": fraction_json(improvement),
                "improvement_ratio_of_baseline": fraction_json(improvement / baseline_l1),
                "row_l1_distance": fraction_json(row_distance(baseline_row, candidate)),
                "baseline_support": support(baseline_row),
                "candidate_support": support(candidate),
                "support_changed": support(baseline_row) != support(candidate),
                "row_complexity": row_complexity(candidate),
                "candidate_axis_residual": fraction_json(trial_residual[axis]),
                "candidate_top_residual_axis": max(
                    trial_residual.items(),
                    key=lambda item: abs(item[1]),
                )[0],
            }
            axis_results.append(result)
            all_results.append(result)

        axis_results.sort(
            key=lambda item: (
                -parse_fraction_json(item["residual_l1_improvement"]),
                parse_fraction_json(item["row_l1_distance"]),
                item["row_complexity"],
            )
        )
        if axis_results:
            best_by_axis[axis] = axis_results[0]

    all_results.sort(
        key=lambda item: (
            -parse_fraction_json(item["residual_l1_improvement"]),
            parse_fraction_json(item["row_l1_distance"]),
            item["row_complexity"],
        )
    )
    top_results = all_results[:top_n]
    conservative_results = [
        result for result in all_results
        if not result["support_changed"]
    ][:top_n]

    receipt = {
        "schema": "standard_model_projection_sensitivity_probe_receipt_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "surface_id": "standard_model_projection_sensitivity_probe",
        "source": {
            "reduction_receipt": str(REDUCTION_RECEIPT.relative_to(REPO)),
            "reduction_stable_hash_sha256": reduction.get("stable_reduction_hash_sha256"),
            "accounting_receipt": str(ACCOUNTING_RECEIPT.relative_to(REPO)),
            "accounting_stable_hash_sha256": accounting.get("stable_residual_accounting_hash_sha256"),
        },
        "search_space": {
            "searched_axes": high_pressure_axes,
            "primitive_basis": PRIMITIVES,
            "max_denominator": max_denominator,
            "candidate_row_count": len(rows),
            "retune_scope": "one projection row changed at a time",
        },
        "baseline": {
            "projection_matrix_12_to_4": projection_json(baseline_projection),
            "residual_l1": fraction_json(baseline_l1),
        },
        "best_by_axis": best_by_axis,
        "top_single_row_retunes": top_results,
        "top_support_preserving_retunes": conservative_results,
        "diagnostic_summary": {
            "best_candidate": top_results[0] if top_results else None,
            "best_support_preserving_candidate": conservative_results[0] if conservative_results else None,
            "improving_candidate_count": len(all_results),
            "support_preserving_improving_candidate_count": len([
                result for result in all_results
                if not result["support_changed"]
            ]),
            "searched_axis_count": len(high_pressure_axes),
        },
        "claim_boundary": (
            "This is a bounded sensitivity search over symbolic projection rows. "
            "It proposes geometric retunes for compression/control experiments; "
            "it is not a physical Standard Model calculation or a replacement "
            "for exact residual receipts."
        ),
        "lawful": True,
    }

    stable_preimage = stable_json({
        "schema": receipt["schema"],
        "surface_id": receipt["surface_id"],
        "source": receipt["source"],
        "search_space": receipt["search_space"],
        "baseline": receipt["baseline"],
        "best_by_axis": receipt["best_by_axis"],
        "top_single_row_retunes": receipt["top_single_row_retunes"],
        "top_support_preserving_retunes": receipt["top_support_preserving_retunes"],
        "diagnostic_summary": receipt["diagnostic_summary"],
        "claim_boundary": receipt["claim_boundary"],
        "lawful": receipt["lawful"],
    }).encode("utf-8")
    receipt["stable_projection_sensitivity_hash_sha256"] = sha256_bytes(stable_preimage)
    receipt["receipt_hash_preimage_sha256"] = sha256_bytes(stable_json(receipt).encode("utf-8"))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-denominator", type=int, default=8)
    parser.add_argument("--top-n", type=int, default=12)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    receipt = build_receipt(args.max_denominator, args.top_n)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    best = receipt["diagnostic_summary"]["best_candidate"]
    conservative_best = receipt["diagnostic_summary"]["best_support_preserving_candidate"]
    print(json.dumps({
        "lawful": receipt["lawful"],
        "stable_projection_sensitivity_hash_sha256": receipt["stable_projection_sensitivity_hash_sha256"],
        "receipt_hash_preimage_sha256": receipt["receipt_hash_preimage_sha256"],
        "baseline_residual_l1": receipt["baseline"]["residual_l1"],
        "improving_candidate_count": receipt["diagnostic_summary"]["improving_candidate_count"],
        "support_preserving_improving_candidate_count": receipt["diagnostic_summary"]["support_preserving_improving_candidate_count"],
        "best_candidate": best,
        "best_support_preserving_candidate": conservative_best,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
