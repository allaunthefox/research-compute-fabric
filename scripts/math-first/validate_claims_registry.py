#!/usr/bin/env python3
"""Validate ``claims.yaml`` against the claims-registry JSON Schema.

Usage:
    scripts/math-first/validate_claims_registry.py [PATH]

When no PATH is provided, the registry at the repo root (``claims.yaml``) is
validated. The script enforces:

  * the YAML parses and conforms to
    ``shared-data/schemas/claims-registry.schema.json``;
  * every ``id`` is unique across the registry;
  * every repo-relative path referenced from ``lean``, ``review_receipts``,
    and ``sources`` resolves to a tracked file on disk (external citations
    that do not look like repo paths -- e.g. ``http`` URLs, ``arXiv:...`` --
    are skipped).

Exit code:
    0  registry valid.
    1  registry invalid (schema, duplicate id, or missing referenced file).
    2  schema malformed, dependencies missing, or registry file not found.

See ``docs/math-first-tooling.md`` for the math-first tooling contract.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "shared-data" / "schemas" / "claims-registry.schema.json"
DEFAULT_REGISTRY = REPO_ROOT / "claims.yaml"

# Anything matching one of these prefixes is treated as an external citation
# rather than a repo-relative path, and is therefore not required to resolve
# to a file on disk.
_EXTERNAL_PREFIXES = ("http://", "https://", "arXiv:", "arxiv:", "doi:", "DOI:")
_EXTERNAL_RE = re.compile(r"^[A-Za-z]+:")


def _load_schema(schema_path: Path) -> dict[str, Any]:
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        print(
            "error: jsonschema>=4.18 is required (Draft 2020-12). "
            "Install via `uv pip install jsonschema>=4.21 PyYAML`.",
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

    Draft202012Validator.check_schema(schema)
    return schema


def _load_registry(registry_path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        print(
            "error: PyYAML is required. Install via `uv pip install PyYAML`.",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc

    try:
        text = registry_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"error: registry not found at {registry_path}", file=sys.stderr)
        raise SystemExit(2)

    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        print(f"error: registry {registry_path} did not parse as a mapping", file=sys.stderr)
        raise SystemExit(1)
    return data


def _is_external(reference: str) -> bool:
    if reference.startswith(_EXTERNAL_PREFIXES):
        return True
    return bool(_EXTERNAL_RE.match(reference))


def _check_path(reference: str) -> tuple[bool, str]:
    if _is_external(reference):
        return True, ""
    if reference.startswith("/"):
        return False, "must be repo-relative (no leading '/')"
    candidate = REPO_ROOT / reference
    if not candidate.exists():
        return False, f"path does not exist on disk: {reference}"
    return True, ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=DEFAULT_REGISTRY,
        help=f"Registry file to validate (default: {DEFAULT_REGISTRY.relative_to(REPO_ROOT)}).",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=SCHEMA_PATH,
        help=f"Path to the JSON Schema (default: {SCHEMA_PATH.relative_to(REPO_ROOT)}).",
    )
    args = parser.parse_args(argv)

    schema = _load_schema(args.schema)
    registry = _load_registry(args.path)

    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(registry), key=lambda e: list(e.absolute_path))
    if errors:
        print(f"FAIL {args.path}")
        for err in errors:
            location = "/".join(str(p) for p in err.absolute_path) or "<root>"
            print(f"  - {location}: {err.message}")
        return 1

    failures: list[str] = []
    seen_ids: dict[str, int] = {}
    for index, entry in enumerate(registry.get("claims", [])):
        cid = entry.get("id", f"<index {index}>")
        if cid in seen_ids:
            failures.append(
                f"duplicate id '{cid}' (also defined at index {seen_ids[cid]})"
            )
        seen_ids[cid] = index

        for key in ("lean",):
            value = entry.get(key)
            if not value:
                continue
            # Lean entries may be either a file path or a theorem symbol; only
            # validate the file path form, which contains a `/` or ends in `.lean`.
            if "/" in value or value.endswith(".lean"):
                ok, msg = _check_path(value)
                if not ok:
                    failures.append(f"claim '{cid}': {key}: {msg}")

        for key in ("review_receipts", "sources"):
            for value in entry.get(key, []) or []:
                ok, msg = _check_path(value)
                if not ok:
                    failures.append(f"claim '{cid}': {key}: {msg}")

    if failures:
        print(f"FAIL {args.path}")
        for line in failures:
            print(f"  - {line}")
        return 1

    print(f"OK   {args.path} ({len(registry.get('claims', []))} claim(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
