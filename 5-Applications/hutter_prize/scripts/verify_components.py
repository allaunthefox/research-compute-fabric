#!/usr/bin/env python3
"""Verify tracked files against a SHA-256 lock manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", required=True, help="Path to the JSON lock manifest.")
    parser.add_argument(
        "--root",
        default=".",
        help="Root directory used to resolve component paths from the lock file.",
    )
    parser.add_argument(
        "--file",
        action="append",
        default=[],
        help="Extra file to verify directly by path. If omitted, verify every locked component.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    lock_path = Path(args.lock).resolve()
    root = Path(args.root).resolve()

    data = json.loads(lock_path.read_text(encoding="utf-8"))
    locked = {entry["path"]: entry["sha256"] for entry in data["components"]}

    if args.file:
        targets = []
        for item in args.file:
            path = Path(item).resolve()
            try:
                rel = path.relative_to(root)
            except ValueError:
                rel = path.relative_to(lock_path.parent)
            targets.append((str(rel), path))
    else:
        targets = [(rel_path, root / rel_path) for rel_path in locked]

    failures = []
    for rel_path, full_path in targets:
        expected = locked.get(rel_path)
        if expected is None:
            failures.append(f"{rel_path}: not present in lock manifest")
            continue
        if not full_path.is_file():
            failures.append(f"{rel_path}: file missing")
            continue
        actual = sha256_file(full_path)
        if actual != expected:
            failures.append(
                f"{rel_path}: sha256 mismatch (expected {expected}, got {actual})"
            )

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1

    print("All tracked component hashes match the lock manifest.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
