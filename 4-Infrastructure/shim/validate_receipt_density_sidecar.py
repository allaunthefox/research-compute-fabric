#!/usr/bin/env python3
"""Validate the RRC receipt-density sidecar table.

Readback validator for Phase 2.1. Uses the shared rds_connect.connect_rds helper
and checks the anti-drift boundary after a guarded --write-rds run.

Default table: ene.rrc_receipt_density
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SHIM_DIR = Path(__file__).resolve().parent
if str(SHIM_DIR) not in sys.path:
    sys.path.insert(0, str(SHIM_DIR))

DEFAULT_RDS_TABLE = "ene.rrc_receipt_density"
_ALLOWED_TABLES = {"ene.rrc_receipt_density", "public.rrc_receipt_density"}


def table_name(table: str) -> str:
    """Return a known-safe qualified table name.

    This validator intentionally accepts only known sidecar table names. The writer
    has a generic identifier validator; the readback validator is stricter because
    it should only verify the receipt-density sidecar.
    """
    if table not in _ALLOWED_TABLES:
        raise ValueError(f"table not allowed for this validator: {table!r}")
    schema, name = table.split(".", 1)
    for ident in (schema, name):
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", ident):
            raise ValueError(f"unsafe identifier: {ident!r}")
    return f'"{schema}"."{name}"'


def connect(connect_timeout: int | None):
    try:
        from rds_connect import connect_rds
    except ImportError as exc:
        raise RuntimeError("rds_connect.py is required for sidecar validation") from exc
    overrides: dict[str, Any] = {}
    if connect_timeout is not None:
        overrides["connect_timeout"] = connect_timeout
    return connect_rds(**overrides)


def validate_table(conn: Any, table: str) -> dict[str, Any]:
    full = table_name(table)
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT
              COUNT(*) AS total,
              SUM(CASE WHEN promotion != 'not_promoted' THEN 1 ELSE 0 END) AS promoted_rows,
              SUM(CASE WHEN receipt_density IS NULL THEN 1 ELSE 0 END) AS null_density_rows,
              SUM(CASE WHEN receipt_density < 0 OR receipt_density > 1 THEN 1 ELSE 0 END) AS out_of_range_density_rows,
              SUM(CASE WHEN confidence IS NULL THEN 1 ELSE 0 END) AS null_confidence_rows,
              SUM(CASE WHEN confidence < 0 OR confidence > 1 THEN 1 ELSE 0 END) AS out_of_range_confidence_rows,
              SUM(CASE WHEN receipt_density_hash IS NULL OR receipt_density_hash = '' THEN 1 ELSE 0 END) AS missing_hash_rows,
              SUM(CASE WHEN receipt_density_source IS NULL OR receipt_density_source = '' THEN 1 ELSE 0 END) AS missing_source_rows,
              SUM(CASE WHEN receipt_density_status NOT IN ('CANDIDATE', 'HOLD') THEN 1 ELSE 0 END) AS bad_status_rows
            FROM {full}
            """
        )
        row = cur.fetchone()
        keys = [
            "total",
            "promoted_rows",
            "null_density_rows",
            "out_of_range_density_rows",
            "null_confidence_rows",
            "out_of_range_confidence_rows",
            "missing_hash_rows",
            "missing_source_rows",
            "bad_status_rows",
        ]
        summary = {k: int(v or 0) for k, v in zip(keys, row)}

        cur.execute(
            f"""
            SELECT rrc_shape, COUNT(*), AVG(receipt_density)
            FROM {full}
            GROUP BY rrc_shape
            ORDER BY rrc_shape
            """
        )
        by_shape = [
            {
                "rrc_shape": shape,
                "count": int(count),
                "mean_receipt_density": round(float(avg), 6) if avg is not None else None,
            }
            for shape, count, avg in cur.fetchall()
        ]

    errors: list[str] = []
    if summary["total"] <= 0:
        errors.append("sidecar_table_empty")
    for key in [
        "promoted_rows",
        "null_density_rows",
        "out_of_range_density_rows",
        "null_confidence_rows",
        "out_of_range_confidence_rows",
        "missing_hash_rows",
        "missing_source_rows",
        "bad_status_rows",
    ]:
        if summary[key] != 0:
            errors.append(key)

    return {
        "table": table,
        "valid": len(errors) == 0,
        "errors": errors,
        "summary": summary,
        "by_shape": by_shape,
        "promotion_policy": "all rows must remain not_promoted",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the RRC receipt-density sidecar table.")
    parser.add_argument("--rds-table", default=DEFAULT_RDS_TABLE, choices=sorted(_ALLOWED_TABLES))
    parser.add_argument("--connect-timeout", type=int, default=10)
    parser.add_argument("--out", type=Path, default=None, help="Optional JSON report output path.")
    args = parser.parse_args(argv)

    conn = connect(args.connect_timeout)
    try:
        result = validate_table(conn, args.rds_table)
    finally:
        conn.close()

    print(json.dumps(result, indent=2, sort_keys=True))
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
