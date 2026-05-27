#!/usr/bin/env python3
"""Regression tests for pist_receipt_density_injector.py.

These tests are intentionally dependency-light and can run with plain Python:

    python3 4-Infrastructure/shim/test_pist_receipt_density_injector.py

They protect the Phase 2.1 anti-drift boundaries:

* Markdown table noise is not treated as equations.
* Receipt density and confidence are bounded.
* Every generated record is explicitly not promoted.
* Unsafe RDS table identifiers are rejected before SQL construction.
* RDS writes remain opt-in; default runs produce JSON only.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pist_receipt_density_injector as inj


SAMPLE_RRC = """# RRC Equation Projection

## Sample Projections

| Equation | RRC shape | Status | Top axes |
|---|---|---|---|
| `bandwidth_adjusted_threshold` | `CognitiveLoadField` | `CANDIDATE` | `projection_declared, negative_control_strength, witness_declared, scale_band_declared` |
| `source_domain` | `SignalShapedRouteCompiler` | `CANDIDATE` | `projection_declared, shape_closure, witness_declared, scale_band_declared` |
"""


SAMPLE_PIST = {
    "predictions": [
        {
            "equation": "Equation",
            "ground_truth": "RRC shape",
            "proxy_pred": "LogogramProjection",
            "exact_pred": "LogogramProjection",
        },
        {
            "equation": "---",
            "ground_truth": "---",
            "proxy_pred": "LogogramProjection",
            "exact_pred": "LogogramProjection",
        },
        {
            "equation": "bandwidth_adjusted_threshold",
            "ground_truth": "CognitiveLoadField",
            "proxy_pred": "CognitiveLoadField",
            "exact_pred": "CognitiveLoadField",
            "matrix_hash": "mhash001",
            "canonical_hash": "chash001",
            "spectral_gap": 0.5,
            "rank_estimate": 8,
            "laplacian_zero_count": 1,
            "crossing_density": 0.25,
            "strand_entropy": 3.0,
        },
        {
            "equation": "source_domain",
            "ground_truth": "SignalShapedRouteCompiler",
            "proxy_pred": "LogogramProjection",
            "exact_pred": "LogogramProjection",
            "matrix_hash": "mhash002",
            "canonical_hash": "chash002",
            "spectral_gap": 0.25,
            "rank_estimate": 7,
            "laplacian_zero_count": 1,
            "crossing_density": 0.125,
            "strand_entropy": 2.5,
        },
    ]
}


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_table_noise_filtering() -> None:
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "rrc.md"
        path.write_text(SAMPLE_RRC, encoding="utf-8")
        rows = inj.parse_rrc_table(path)
        assert_true(len(rows) == 2, f"expected 2 real rows, got {len(rows)}")
        assert_true(all(r.equation_id not in {"Equation", "---"} for r in rows), "table noise leaked into rows")


def test_pist_noise_filtering() -> None:
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "pist.json"
        path.write_text(json.dumps(SAMPLE_PIST), encoding="utf-8")
        preds = inj.load_pist_predictions(path)
        assert_true(set(preds) == {"bandwidth_adjusted_threshold", "source_domain"}, f"unexpected predictions: {set(preds)}")


def test_record_bounds_and_no_promotion() -> None:
    with tempfile.TemporaryDirectory() as td:
        rrc = Path(td) / "rrc.md"
        pist = Path(td) / "pist.json"
        rrc.write_text(SAMPLE_RRC, encoding="utf-8")
        pist.write_text(json.dumps(SAMPLE_PIST), encoding="utf-8")
        rows = inj.parse_rrc_table(rrc)
        preds = inj.load_pist_predictions(pist)
        records = [inj.build_record(row, preds.get(row.equation_id)) for row in rows]
        assert_true(len(records) == 2, "expected 2 records")
        for record in records:
            assert_true(0.0 <= record.receipt_density <= 1.0, f"density out of range: {record}")
            assert_true(0.0 <= record.confidence <= 1.0, f"confidence out of range: {record}")
            assert_true(record.promotion == "not_promoted", "promotion boundary violated")
            assert_true(record.receipt_hash, "missing receipt hash")


def test_shape_disagreement_warning() -> None:
    row = inj.RRCEquationRow(
        equation_id="source_domain",
        rrc_shape="SignalShapedRouteCompiler",
        status="CANDIDATE",
        top_axes=["projection_declared", "shape_closure"],
    )
    pred = SAMPLE_PIST["predictions"][-1]
    record = inj.build_record(row, pred)
    assert_true("pist_shape_disagreement" in record.warnings, "expected disagreement warning")


def test_table_identifier_validation() -> None:
    assert_true(inj.split_qualified_table("ene.rrc_receipt_density") == ("ene", "rrc_receipt_density"), "valid table rejected")
    bad_tables = [
        "ene.bad;drop table x",
        "ene.rrc receipt density",
        "ene..rrc_receipt_density",
        "ene.rrc_receipt_density where 1=1",
    ]
    for table in bad_tables:
        try:
            inj.split_qualified_table(table)
        except ValueError:
            pass
        else:
            raise AssertionError(f"unsafe table accepted: {table}")


def test_default_main_does_not_write_rds() -> None:
    with tempfile.TemporaryDirectory() as td:
        rrc = Path(td) / "rrc.md"
        pist = Path(td) / "pist.json"
        out = Path(td) / "out.json"
        rrc.write_text(SAMPLE_RRC, encoding="utf-8")
        pist.write_text(json.dumps(SAMPLE_PIST), encoding="utf-8")
        code = inj.main(["--rrc-file", str(rrc), "--pist-report", str(pist), "--out", str(out)])
        assert_true(code == 0, f"main returned {code}")
        payload = json.loads(out.read_text(encoding="utf-8"))
        assert_true(payload["summary"]["rds_write"]["enabled"] is False, "RDS write should be disabled by default")
        assert_true(payload["summary"]["records"] == 2, "unexpected record count")


def run_all() -> None:
    tests = [
        test_table_noise_filtering,
        test_pist_noise_filtering,
        test_record_bounds_and_no_promotion,
        test_shape_disagreement_warning,
        test_table_identifier_validation,
        test_default_main_does_not_write_rds,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")


if __name__ == "__main__":
    run_all()
