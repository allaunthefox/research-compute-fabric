#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Evaluate a daily scoreboard CSV and output a binary GO/NO-GO decision.

Usage:
    python3 5-Applications/scripts/evaluate_daily_scoreboard.py \
        validate \
        --csv data_baselines/daily_go_no_go_scoreboard_template.csv \
        --schema schemas/daily_go_no_go_scoreboard_row.schema.json \
        --out 5-Applications/out/daily_go_no_go_schema_validation.json

  python3 5-Applications/scripts/evaluate_daily_scoreboard.py \
        evaluate \
    --csv data_baselines/daily_go_no_go_scoreboard_template.csv \
        --schema schemas/daily_go_no_go_scoreboard_row.schema.json \
    --out 5-Applications/out/daily_go_no_go_result.json

Exit codes:
  0 -> GO
  3 -> NO-GO
  1 -> validation/runtime error
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List, Tuple

from jsonschema import Draft202012Validator

VALID_STATUS = {"PASS", "FAIL", "NA", "UNKNOWN"}
REQUIRED_COLUMNS = [
    "date_utc",
    "run_id",
    "gate_id",
    "category",
    "required",
    "is_killswitch",
    "threshold",
    "observed",
    "status",
    "evidence",
    "notes",
]


def parse_bool(value: str, field: str, row_num: int) -> bool:
    normalized = (value or "").strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    raise ValueError(f"Row {row_num}: invalid boolean for {field}: {value!r}")


def load_rows(csv_path: Path) -> List[Dict[str, str]]:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []
        missing = [c for c in REQUIRED_COLUMNS if c not in columns]
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")

        rows = list(reader)

    if not rows:
        raise ValueError("CSV has no data rows")

    return rows


def load_schema(schema_path: Path) -> Dict[str, object]:
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    return json.loads(schema_path.read_text(encoding="utf-8"))


def to_schema_row(row: Dict[str, str], row_num: int) -> Dict[str, object]:
    """Coerce CSV string values into schema types for direct JSON Schema validation."""
    return {
        "date_utc": (row.get("date_utc") or "").strip(),
        "run_id": (row.get("run_id") or "").strip(),
        "gate_id": (row.get("gate_id") or "").strip(),
        "category": (row.get("category") or "").strip(),
        "required": parse_bool(row.get("required", ""), "required", row_num),
        "is_killswitch": parse_bool(row.get("is_killswitch", ""), "is_killswitch", row_num),
        "threshold": (row.get("threshold") or "").strip(),
        "observed": (row.get("observed") or "").strip(),
        "status": (row.get("status") or "").strip().upper(),
        "evidence": (row.get("evidence") or "").strip(),
        "notes": (row.get("notes") or "").strip(),
    }


def validate_rows_against_schema(
    rows: List[Dict[str, str]], schema: Dict[str, object]
) -> Tuple[List[Dict[str, object]], List[str]]:
    validator = Draft202012Validator(schema)
    typed_rows: List[Dict[str, object]] = []
    errors: List[str] = []

    for idx, row in enumerate(rows, start=2):
        try:
            typed = to_schema_row(row, idx)
        except ValueError as exc:
            errors.append(str(exc))
            continue

        row_errors = sorted(validator.iter_errors(typed), key=lambda e: list(e.path))
        for err in row_errors:
            field = ".".join([str(p) for p in err.path]) if err.path else "<row>"
            errors.append(f"Row {idx}: {field}: {err.message}")

        typed_rows.append(typed)

    return typed_rows, errors


def validate_and_score(rows: List[Dict[str, str]]) -> Tuple[Dict[str, object], List[str]]:
    errors: List[str] = []
    evaluated: List[Dict[str, object]] = []

    run_ids = set()
    dates = set()

    for idx, row in enumerate(rows, start=2):
        gate_id = (row.get("gate_id") or "").strip()
        category = (row.get("category") or "").strip()
        status = (row.get("status") or "").strip().upper()

        try:
            required = parse_bool(row.get("required", ""), "required", idx)
            is_killswitch = parse_bool(row.get("is_killswitch", ""), "is_killswitch", idx)
        except ValueError as exc:
            errors.append(str(exc))
            continue

        if not gate_id:
            errors.append(f"Row {idx}: gate_id is empty")
        if not category:
            errors.append(f"Row {idx}: category is empty")
        if status not in VALID_STATUS:
            errors.append(f"Row {idx}: invalid status {status!r}")

        if category == "killswitch" and not is_killswitch:
            errors.append(f"Row {idx}: category killswitch requires is_killswitch=true")

        run_ids.add((row.get("run_id") or "").strip())
        dates.add((row.get("date_utc") or "").strip())

        evaluated.append(
            {
                "row": idx,
                "gate_id": gate_id,
                "category": category,
                "required": required,
                "is_killswitch": is_killswitch,
                "status": status,
                "threshold": (row.get("threshold") or "").strip(),
                "observed": (row.get("observed") or "").strip(),
                "evidence": (row.get("evidence") or "").strip(),
                "notes": (row.get("notes") or "").strip(),
            }
        )

    if len(run_ids) != 1:
        errors.append(f"CSV must contain exactly one run_id, found {len(run_ids)}")
    if len(dates) != 1:
        errors.append(f"CSV must contain exactly one date_utc, found {len(dates)}")

    required_rows = [r for r in evaluated if r["required"]]
    killswitch_rows = [r for r in evaluated if r["is_killswitch"]]

    required_failures = [
        r for r in required_rows if r["status"] != "PASS"
    ]
    killswitch_failures = [
        r for r in killswitch_rows if r["status"] == "FAIL"
    ]

    all_required_pass = len(required_failures) == 0
    all_killswitch_pass = len(killswitch_failures) == 0
    final_decision = "GO" if (all_required_pass and all_killswitch_pass) else "NO-GO"

    by_category: Dict[str, Dict[str, int]] = {}
    for r in evaluated:
        category = r["category"] or "unknown"
        by_category.setdefault(category, {"PASS": 0, "FAIL": 0, "NA": 0, "UNKNOWN": 0})
        by_category[category][r["status"]] = by_category[category].get(r["status"], 0) + 1

    result = {
        "date_utc": next(iter(dates), ""),
        "run_id": next(iter(run_ids), ""),
        "final_decision": final_decision,
        "summary": {
            "total_gates": len(evaluated),
            "required_gates": len(required_rows),
            "killswitch_gates": len(killswitch_rows),
            "required_failures": len(required_failures),
            "killswitch_failures": len(killswitch_failures),
            "all_required_pass": all_required_pass,
            "all_killswitch_pass": all_killswitch_pass,
            "status_counts_by_category": by_category,
        },
        "failures": {
            "required": [
                {
                    "gate_id": r["gate_id"],
                    "category": r["category"],
                    "status": r["status"],
                    "threshold": r["threshold"],
                    "observed": r["observed"],
                    "evidence": r["evidence"],
                }
                for r in required_failures
            ],
            "killswitch": [
                {
                    "gate_id": r["gate_id"],
                    "category": r["category"],
                    "status": r["status"],
                    "threshold": r["threshold"],
                    "observed": r["observed"],
                    "evidence": r["evidence"],
                }
                for r in killswitch_failures
            ],
        },
    }

    return result, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate/evaluate daily GO/NO-GO scoreboard CSV")
    subparsers = parser.add_subparsers(dest="command")

    validate_parser = subparsers.add_parser("validate", help="Validate CSV rows against JSON schema")
    validate_parser.add_argument("--csv", required=True, help="Path to scoreboard CSV")
    validate_parser.add_argument("--schema", required=True, help="Path to row JSON schema")
    validate_parser.add_argument("--out", required=True, help="Path to output JSON validation result")

    evaluate_parser = subparsers.add_parser("evaluate", help="Validate schema, then score GO/NO-GO")
    evaluate_parser.add_argument("--csv", required=True, help="Path to scoreboard CSV")
    evaluate_parser.add_argument("--schema", required=True, help="Path to row JSON schema")
    evaluate_parser.add_argument("--out", required=True, help="Path to output JSON result")

    args = parser.parse_args()

    if not args.command:
        parser.error("A command is required: 'validate' or 'evaluate'.")

    csv_path = Path(args.csv)
    schema_path = Path(args.schema)
    out_path = Path(args.out)

    try:
        rows = load_rows(csv_path)
        schema = load_schema(schema_path)
        _, schema_errors = validate_rows_against_schema(rows, schema)
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1

    if schema_errors:
        payload = {
            "final_decision": "NO-GO",
            "phase": "schema_validation",
            "validation_errors": schema_errors,
        }
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print("NO-GO")
        print("Schema validation errors:")
        for err in schema_errors:
            print(f"- {err}")
        return 1

    if args.command == "validate":
        payload = {
            "final_decision": "GO",
            "phase": "schema_validation",
            "validated_rows": len(rows),
            "csv": str(csv_path),
            "schema": str(schema_path),
        }
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print("GO")
        print(f"Schema validation passed. Result written to: {out_path}")
        return 0

    result, errors = validate_and_score(rows)

    if errors:
        payload = {
            "final_decision": "NO-GO",
            "phase": "scoring_validation",
            "validation_errors": errors,
        }
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print("NO-GO")
        print("Validation errors:")
        for err in errors:
            print(f"- {err}")
        return 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(result["final_decision"])
    print(f"Result written to: {out_path}")

    if result["final_decision"] == "GO":
        return 0
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
