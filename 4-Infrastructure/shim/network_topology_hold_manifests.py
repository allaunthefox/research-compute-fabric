#!/usr/bin/env python3
"""Create HOLD manifests for network topology coefficients and predictions."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
DB = REPO / "shared-data" / "network_topology_database.json"
OUT_DIR = REPO / "shared-data" / "data" / "stack_solidification"
COEFF_OUT = OUT_DIR / "network_topology_coefficient_calibration_manifest.json"
PRED_OUT = OUT_DIR / "network_topology_prediction_hold_registry.json"
DOC = REPO / "6-Documentation" / "docs" / "network_topology_hold_manifests_2026-05-09.md"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def coeff_rows(db: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    raw = db.get("fundamental_equation_data", {}).get("methodology_weights", {})
    reweighted = (
        db.get("fundamental_equation_data", {})
        .get("receipt_reweighted_methodology_weights", {})
        .get("methodology_weights", {})
    )
    for key, item in sorted(raw.items()):
        receipt = reweighted.get(key, {})
        rows.append(
            {
                "methodology": key,
                "raw_weight": item.get("weight"),
                "alignment_score": item.get("alignment_score"),
                "validation_status_label": item.get("validation_status"),
                "receipt_multiplier": receipt.get("receipt_multiplier"),
                "receipt_reweighted_weight": receipt.get("receipt_reweighted_weight"),
                "decision": receipt.get("decision"),
                "status": "HOLD_CALIBRATION",
                "closure_gate": [
                    "source dataset receipt exists",
                    "calibration target and loss function are declared",
                    "sensitivity sweep passes",
                    "negative control shows coefficient is not arbitrary fit",
                ],
            }
        )
    return rows


def prediction_rows(db: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for item in db.get("predicted_network_nodes", []):
        rows.append(
            {
                "prediction_id": f"node::{item.get('provider')}::{item.get('location')}",
                "kind": "predicted_network_node",
                "provider": item.get("provider"),
                "location": item.get("location"),
                "prediction_reason": item.get("prediction_reason"),
                "confidence": item.get("confidence"),
                "validation_status_label": item.get("validation_status"),
                "validation_score": item.get("validation_score"),
                "status": "HOLD_PREDICTION_VALIDATION",
                "closure_gate": [
                    "pre-registration timestamp and immutable hash exist",
                    "public/independent observation source is named",
                    "outcome comparison receipt exists",
                    "false-positive and null-baseline comparison are recorded",
                ],
            }
        )
    for item in db.get("novel_network_paths", []):
        rows.append(
            {
                "prediction_id": f"path::{item.get('source')}::{item.get('destination')}",
                "kind": "novel_network_path",
                "source": item.get("source"),
                "destination": item.get("destination"),
                "prediction_confidence": item.get("prediction_confidence"),
                "path_quality": item.get("path_quality"),
                "novelty_status_label": item.get("novelty_status"),
                "status": "HOLD_PREDICTION_VALIDATION",
                "closure_gate": [
                    "pre-registration timestamp and immutable hash exist",
                    "independent topology/source map is named",
                    "outcome comparison receipt exists",
                    "known-connection baseline comparison is recorded",
                ],
            }
        )
    return rows


def build_doc(coeff: dict[str, Any], pred: dict[str, Any]) -> str:
    lines = [
        "# Network Topology HOLD Manifests",
        "",
        "**Date:** 2026-05-09",
        "",
        "These manifests separate hypothesis weights and predictions from calibrated or validated claims.",
        "",
        "## Coefficient Calibration",
        "",
        f"- Rows: `{coeff['summary']['row_count']}`",
        f"- Status: `{coeff['summary']['status']}`",
        f"- Receipt: `{COEFF_OUT.relative_to(REPO)}`",
        "",
        "| Methodology | Raw Weight | Receipt Weight | Decision |",
        "| --- | ---: | ---: | --- |",
    ]
    for row in coeff["rows"]:
        lines.append(
            f"| `{row['methodology']}` | {row['raw_weight']} | {row['receipt_reweighted_weight']} | `{row['decision']}` |"
        )
    lines.extend(
        [
            "",
            "## Prediction HOLD Registry",
            "",
            f"- Rows: `{pred['summary']['row_count']}`",
            f"- Status: `{pred['summary']['status']}`",
            f"- Receipt: `{PRED_OUT.relative_to(REPO)}`",
            "",
            "| Prediction | Kind | Status |",
            "| --- | --- | --- |",
        ]
    )
    for row in pred["rows"]:
        lines.append(f"| `{row['prediction_id']}` | `{row['kind']}` | `{row['status']}` |")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "These rows are accounting and validation queues. They do not calibrate coefficients or validate topology predictions.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    db = load_json(DB)
    now = datetime.now(timezone.utc).isoformat()
    coeff = {
        "schema": "network_topology_coefficient_calibration_manifest_v1",
        "created_utc": now,
        "source_database": str(DB.relative_to(REPO)),
        "claim_boundary": "Coefficient HOLD manifest only. Raw and receipt-reweighted weights remain hypothesis/accounting surfaces until calibration gates close.",
        "summary": {"row_count": len(coeff_rows(db)), "status": "HOLD_CALIBRATION"},
        "rows": coeff_rows(db),
    }
    pred = {
        "schema": "network_topology_prediction_hold_registry_v1",
        "created_utc": now,
        "source_database": str(DB.relative_to(REPO)),
        "claim_boundary": "Prediction HOLD registry only. Entries are not validated claims until pre-registration and independent outcome receipts close.",
        "summary": {"row_count": len(prediction_rows(db)), "status": "HOLD_PREDICTION_VALIDATION"},
        "rows": prediction_rows(db),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    COEFF_OUT.write_text(json.dumps(coeff, indent=2, sort_keys=True), encoding="utf-8")
    PRED_OUT.write_text(json.dumps(pred, indent=2, sort_keys=True), encoding="utf-8")
    DOC.write_text(build_doc(coeff, pred), encoding="utf-8")
    print(json.dumps({"coefficient_manifest": str(COEFF_OUT.relative_to(REPO)), "prediction_registry": str(PRED_OUT.relative_to(REPO)), "doc": str(DOC.relative_to(REPO))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
