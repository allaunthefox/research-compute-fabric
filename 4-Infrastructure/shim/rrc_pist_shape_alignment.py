#!/usr/bin/env python3
"""RRC/PIST shape-alignment calibration pass.

Phase 2.2 bridge:

    PIST exact/proxy label  = structural/spectral morphology
    RRC shape label         = semantic/domain routing class

A mismatch is not automatically an error. For the current RRC equation corpus,
PIST often detects `LogogramProjection` because the input surface is an equation
name/logogram, while RRC supplies the semantic routing class such as
`CognitiveLoadField` or `SignalShapedRouteCompiler`.

This script annotates receipt-density records with a `shape_alignment` object and
turns known-compatible structural/semantic divergences into an explicit
`structural_semantic_label_divergence` warning instead of a raw
`pist_shape_disagreement` warning.

It does not promote claims. Every record remains `promotion = not_promoted`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_IN = ROOT / "shared-data/rrc_receipt_density_backfill.json"
DEFAULT_OUT = ROOT / "shared-data/rrc_receipt_density_backfill.json"

RRC_SEMANTIC_SHAPES = {
    "CognitiveLoadField",
    "SignalShapedRouteCompiler",
    "ProjectableGeometryTopology",
    "CadForceProbeReceipt",
    "LogogramProjection",
}

COMPATIBLE_STRUCTURAL_LABELS = {
    "LogogramProjection",
}

ALIGNMENT_SCORES = {
    "aligned_exact": 1.0,
    "aligned_proxy": 0.86,
    "compatible_structural_projection": 0.72,
    "missing_prediction": 0.0,
    "alignment_warning": 0.35,
}


def stable_hash(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def determine_alignment(record: dict[str, Any]) -> dict[str, Any]:
    rrc_shape = record.get("rrc_shape")
    shape_prediction = record.get("shape_prediction", {}) or {}
    proxy = shape_prediction.get("proxy_pred")
    exact = shape_prediction.get("exact_pred")

    if not proxy and not exact:
        status = "missing_prediction"
        reason = "No PIST proxy/exact classifier label is present for this record."
    elif exact == rrc_shape:
        status = "aligned_exact"
        reason = "PIST exact structural label matches the RRC routing shape."
    elif proxy == rrc_shape:
        status = "aligned_proxy"
        reason = "PIST proxy structural label matches the RRC routing shape."
    elif (exact in COMPATIBLE_STRUCTURAL_LABELS or proxy in COMPATIBLE_STRUCTURAL_LABELS) and rrc_shape in RRC_SEMANTIC_SHAPES:
        status = "compatible_structural_projection"
        reason = (
            "PIST detects symbolic/logogram morphology while RRC supplies the semantic/domain routing class."
        )
    else:
        status = "alignment_warning"
        reason = "PIST structural label and RRC semantic shape are not in the current compatibility map."

    return {
        "alignment_version": "rrc-pist-shape-alignment-v1",
        "alignment_status": status,
        "alignment_confidence": ALIGNMENT_SCORES[status],
        "rrc_shape": rrc_shape,
        "pist_proxy_label": proxy,
        "pist_exact_label": exact,
        "label_space_model": "PIST=morphology; RRC=semantic routing",
        "reason": reason,
        "promotion": "not_promoted",
    }


def rewrite_warnings(warnings: list[str], alignment: dict[str, Any]) -> list[str]:
    out = [warning for warning in warnings if warning != "pist_shape_disagreement"]
    status = alignment["alignment_status"]
    if status == "compatible_structural_projection":
        out.append("structural_semantic_label_divergence")
    elif status == "alignment_warning":
        out.append("pist_shape_alignment_warning")
    elif status == "missing_prediction":
        out.append("missing_pist_prediction")
    return sorted(set(out))


def update_hash(record: dict[str, Any]) -> str:
    payload = {
        "equation_id": record.get("equation_id"),
        "rrc_shape": record.get("rrc_shape"),
        "receipt_density": record.get("receipt_density"),
        "confidence": record.get("confidence"),
        "shape_prediction": record.get("shape_prediction"),
        "shape_alignment": record.get("shape_alignment"),
        "warnings": record.get("warnings"),
        "promotion": "not_promoted",
        "source": record.get("source"),
    }
    return stable_hash(payload)


def align_payload(payload: dict[str, Any]) -> dict[str, Any]:
    records = payload.get("records", [])
    if not isinstance(records, list):
        raise ValueError("input JSON must contain a records array")

    aligned_records: list[dict[str, Any]] = []
    alignment_counts: Counter[str] = Counter()
    warning_counts: Counter[str] = Counter()

    for record in records:
        if not isinstance(record, dict):
            continue
        updated = dict(record)
        updated["promotion"] = "not_promoted"
        alignment = determine_alignment(updated)
        updated["shape_alignment"] = alignment
        updated["warnings"] = rewrite_warnings(list(updated.get("warnings", [])), alignment)
        updated["receipt_hash"] = update_hash(updated)
        alignment_counts[alignment["alignment_status"]] += 1
        warning_counts.update(updated["warnings"])
        aligned_records.append(updated)

    summary = dict(payload.get("summary", {}))
    summary["shape_alignment_version"] = "rrc-pist-shape-alignment-v1"
    summary["shape_alignment_counts"] = dict(sorted(alignment_counts.items()))
    summary["warning_counts"] = dict(sorted(warning_counts.items()))
    summary["promotion_policy"] = "no automatic promotion; shape alignment calibrates label spaces only"

    out = dict(payload)
    out["summary"] = summary
    out["records"] = aligned_records
    out["shape_alignment_claim_boundary"] = {
        "means": "PIST structural morphology and RRC semantic routing labels have been calibrated",
        "does_not_mean": "mathematical proof or claim promotion",
        "promotion_policy": "not_promoted for every record",
    }
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Align RRC semantic labels with PIST structural labels.")
    parser.add_argument("--input", type=Path, default=DEFAULT_IN)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--fail-on-raw-disagreement", action="store_true")
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    aligned = align_payload(payload)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(aligned, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = aligned["summary"]
    print(json.dumps({
        "records": summary.get("records"),
        "shape_alignment_counts": summary.get("shape_alignment_counts"),
        "warning_counts": summary.get("warning_counts"),
        "promotion_policy": summary.get("promotion_policy"),
    }, indent=2, sort_keys=True))
    print(f"Wrote aligned receipt-density JSON: {args.out}")

    if args.fail_on_raw_disagreement and summary.get("warning_counts", {}).get("pist_shape_disagreement", 0):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
