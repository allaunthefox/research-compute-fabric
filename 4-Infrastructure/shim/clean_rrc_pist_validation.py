#!/usr/bin/env python3
"""Clean shared-data/rrc_pist_exact_validation.json after regeneration.

The legacy validation script can accidentally include Markdown table artifacts such
as `Equation` and `---` as predictions. This cleaner removes those rows, rebuilds
the summary, and preserves classifier-backed predictions for the receipt-density
injector.

Usage:

    python3 4-Infrastructure/shim/clean_rrc_pist_validation.py

Optional paths:

    python3 4-Infrastructure/shim/clean_rrc_pist_validation.py \
      --input shared-data/rrc_pist_exact_validation.json \
      --out shared-data/rrc_pist_exact_validation.json
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT = ROOT / "shared-data/rrc_pist_exact_validation.json"
NOISE = {"", "---", "Equation", "RRC shape", "Status", "Top axes"}


def is_noise(pred: dict[str, Any]) -> bool:
    eq = str(pred.get("equation", ""))
    gt = str(pred.get("ground_truth", ""))
    proxy = str(pred.get("proxy_pred", ""))
    return (
        eq in NOISE
        or gt in NOISE
        or proxy in NOISE
        or bool(re.fullmatch(r"-+", eq))
        or bool(re.fullmatch(r"-+", gt))
    )


def accuracy(predictions: list[dict[str, Any]], key: str) -> float:
    if not predictions:
        return 0.0
    return sum(1 for pred in predictions if pred.get(key) == pred.get("ground_truth")) / len(predictions)


def per_class(predictions: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    classes = sorted({p.get("ground_truth") for p in predictions} | {p.get(key) for p in predictions})
    out: dict[str, dict[str, Any]] = {}
    for cls in classes:
        if cls is None:
            continue
        total = sum(1 for p in predictions if p.get("ground_truth") == cls)
        correct = sum(1 for p in predictions if p.get("ground_truth") == cls and p.get(key) == cls)
        out[str(cls)] = {"total": total, "correct": correct, "accuracy": correct / total if total else 0.0}
    return out


def zmp_distribution(predictions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    zmp_by_gt: dict[str, list[int]] = defaultdict(list)
    for pred in predictions:
        gt = str(pred.get("ground_truth", "unknown"))
        try:
            zmp = int(pred.get("zmp", 0))
        except Exception:
            zmp = 0
        zmp_by_gt[gt].append(zmp)
    return {
        gt: {"mean": sum(vals) / len(vals), "min": min(vals), "max": max(vals), "unique": len(set(vals))}
        for gt, vals in zmp_by_gt.items()
        if vals
    }


def clean_report(data: dict[str, Any]) -> dict[str, Any]:
    raw_predictions = data.get("predictions", [])
    predictions = [pred for pred in raw_predictions if isinstance(pred, dict) and not is_noise(pred)]
    dropped = len(raw_predictions) - len(predictions)

    matrix_hashes = Counter(str(p.get("matrix_hash", "")) for p in predictions if p.get("matrix_hash"))
    canonical_hashes = Counter(str(p.get("canonical_hash", "")) for p in predictions if p.get("canonical_hash"))
    errors = data.get("errors_detail", []) or []

    return {
        "summary": {
            "total_input_predictions_before_clean": len(raw_predictions),
            "markdown_noise_predictions_dropped": dropped,
            "total": len(predictions),
            "errors": len(errors),
            "unique_matrix_hashes": len(matrix_hashes),
            "unique_canonical_hashes": len(canonical_hashes),
            "proxy_accuracy": accuracy(predictions, "proxy_pred"),
            "exact_accuracy": accuracy(predictions, "exact_pred"),
            "matrix_hash_collisions": sum(1 for count in matrix_hashes.values() if count > 1),
            "canonical_hash_collisions": sum(1 for count in canonical_hashes.values() if count > 1),
            "filtered_markdown_noise": True,
            "promotion_policy": "not_promoted classifier diagnostics only",
        },
        "per_class_proxy": per_class(predictions, "proxy_pred"),
        "per_class_exact": per_class(predictions, "exact_pred"),
        "zmp_distribution": zmp_distribution(predictions),
        "errors_detail": errors,
        "predictions": predictions,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean RRC PIST validation JSON")
    parser.add_argument("--input", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--out", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--fail-if-empty", action="store_true")
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    cleaned = clean_report(data)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(cleaned, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(cleaned["summary"], indent=2, sort_keys=True))
    print(f"Wrote cleaned report: {args.out}")
    if args.fail_if_empty and cleaned["summary"]["total"] == 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
