#!/usr/bin/env python3
"""Validate that a derived trinary VM program matches the declared baseline rules."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from derive_trinary_program import SCHEMA, derive_payload


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Original input file.")
    parser.add_argument("--program", required=True, help="Derived JSON program to validate.")
    parser.add_argument(
        "--report",
        help="Optional path to write a JSON validation receipt.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).resolve()
    program_path = Path(args.program).resolve()

    expected = derive_payload(input_path)
    actual = json.loads(program_path.read_text(encoding="utf-8"))

    failures: list[str] = []

    if actual.get("schema") != SCHEMA:
        failures.append(
            f"schema mismatch: expected {SCHEMA}, got {actual.get('schema')!r}"
        )

    for key in ("input_size_bytes", "input_sha256", "subregisters", "program"):
        if actual.get(key) != expected.get(key):
            failures.append(f"{key} mismatch")

    report = {
        "schema": "trinary_vm_validation_receipt_v1",
        "validated_utc": datetime.now(timezone.utc).isoformat(),
        "input_path": str(input_path),
        "input_sha256": sha256_file(input_path),
        "program_path": str(program_path),
        "program_sha256": sha256_file(program_path),
        "expected_schema": SCHEMA,
        "actual_schema": actual.get("schema"),
        "valid": not failures,
        "failures": failures,
    }

    if args.report:
        Path(args.report).resolve().write_text(
            json.dumps(report, indent=2) + "\n",
            encoding="utf-8",
        )

    if failures:
        print("Derived program validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        if args.report:
            print(f"Wrote validation receipt to {Path(args.report).resolve()}", file=sys.stderr)
        return 1

    print("Derived program matches the declared deterministic derivation rules.")
    if args.report:
        print(f"Wrote validation receipt to {Path(args.report).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
