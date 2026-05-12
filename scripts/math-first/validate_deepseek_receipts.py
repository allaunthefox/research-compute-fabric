#!/usr/bin/env python3
"""Validate DeepSeek review receipts against the repo JSON Schema.

Usage:
    scripts/math-first/validate_deepseek_receipts.py [PATH ...]

When no PATH is provided, every tracked ``*.receipt.json`` under
``shared-data/artifacts/deepseek_review/`` is validated. Otherwise the named
paths are validated directly (files are checked as receipts; directories are
walked for ``*.receipt.json``).

Exit code:
    0  every receipt validates against
       ``shared-data/schemas/deepseek-review-receipt.schema.json``.
    1  one or more receipts failed schema validation.
    2  the schema itself is malformed or ``jsonschema`` is missing.

This script is the single source of truth shared by the pre-commit hook in
``.pre-commit-config.yaml`` and the ``math-check`` GitHub Actions workflow in
``.github/workflows/math-check.yml``. See ``docs/math-first-tooling.md`` for
the math-first tooling contract.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, Iterator

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "shared-data" / "schemas" / "deepseek-review-receipt.schema.json"
DEFAULT_ROOT = REPO_ROOT / "shared-data" / "artifacts" / "deepseek_review"
RECEIPT_SUFFIX = ".receipt.json"


def _iter_receipts(paths: Iterable[Path]) -> Iterator[Path]:
    for path in paths:
        if path.is_dir():
            yield from sorted(p for p in path.rglob(f"*{RECEIPT_SUFFIX}") if p.is_file())
        elif path.is_file():
            yield path
        else:
            print(f"warning: skipping missing path {path}", file=sys.stderr)


def _load_validator(schema_path: Path):
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError as exc:
        print(
            "error: jsonschema>=4.18 is required (Draft 2020-12). "
            "Install via `uv pip install jsonschema>=4.21 rfc3339-validator`.",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"error: schema not found at {schema_path}", file=sys.stderr)
        raise SystemExit(2)
    except json.JSONDecodeError as exc:
        print(f"error: schema {schema_path} is not valid JSON: {exc}", file=sys.stderr)
        raise SystemExit(2)

    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:  # noqa: BLE001 - surface schema errors verbatim
        print(f"error: schema {schema_path} is invalid: {exc}", file=sys.stderr)
        raise SystemExit(2)

    return Draft202012Validator(schema, format_checker=FormatChecker())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Receipt files or directories. Defaults to the tracked review artifact root.",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=SCHEMA_PATH,
        help=f"Path to the JSON Schema (default: {SCHEMA_PATH.relative_to(REPO_ROOT)}).",
    )
    args = parser.parse_args(argv)

    validator = _load_validator(args.schema)

    if args.paths:
        candidates = list(_iter_receipts(args.paths))
    elif DEFAULT_ROOT.exists():
        candidates = list(_iter_receipts([DEFAULT_ROOT]))
    else:
        candidates = []

    receipts = [p for p in candidates if p.name.endswith(RECEIPT_SUFFIX)]
    skipped = [p for p in candidates if not p.name.endswith(RECEIPT_SUFFIX)]
    for path in skipped:
        print(f"skip: {path} (not a *{RECEIPT_SUFFIX} file)")

    if not receipts:
        print("no DeepSeek review receipts to validate")
        return 0

    failed = 0
    for path in receipts:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"FAIL {path}: invalid JSON ({exc})")
            failed += 1
            continue

        errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
        if errors:
            print(f"FAIL {path}")
            for err in errors:
                location = "/".join(str(p) for p in err.absolute_path) or "<root>"
                print(f"  - {location}: {err.message}")
            failed += 1
        else:
            print(f"OK   {path}")

    if failed:
        print(f"\n{failed} receipt(s) failed validation", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
