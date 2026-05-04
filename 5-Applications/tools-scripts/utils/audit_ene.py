#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK — PHASE 12: ENE PARALLELIZED AUDIT
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================

"""
5-Applications/tools-5-Applications/scripts/audit_ene.py — Parallelized ENE Filesystem Consistency Audit

Audits the ENE index against the live filesystem to confirm 100% consistency.
Uses ProcessPoolExecutor for parallel hash computation.

Can audit in two modes:
  1. INDEX_MODE: Verify every entry in ENE_INDEX.json exists on disk with
     matching hash and size.
  2. FULL_MODE: Walk the entire tree, compare against the index, and report
     files missing from either side.

Usage:
    python 5-Applications/tools-5-Applications/scripts/audit_ene.py                    # INDEX_MODE (default)
    python 5-Applications/tools-5-Applications/scripts/audit_ene.py --full             # FULL_MODE (bidirectional)
    python 5-Applications/tools-5-Applications/scripts/audit_ene.py --workers 16       # Override worker count
    python 5-Applications/tools-5-Applications/scripts/audit_ene.py --json report.json # Save JSON report
    python 5-Applications/tools-5-Applications/scripts/audit_ene.py --quiet            # Suppress progress output
"""

import hashlib
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = Path("/home/allaun/Research Stack")
INDEX_PATH = BASE_DIR / "ENE_INDEX.json"
GITIGNORE_PATH = BASE_DIR / ".gitignore"

WORKERS = os.cpu_count() or 8
CHUNK_SIZE = 65536

SELF_EXCLUSIONS = {"ENE_INDEX.json", "ENE_INDEX.sha256", ".gitignore", "substrate_index.db"}
DIR_EXCLUSIONS = {".git", "__pycache__", ".pytest_cache", ".venv-eng", ".venv-fem", "node_modules", "target"}


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

def compute_hash_file(abs_path: Path) -> Optional[tuple]:
    """Compute (sha256, size) for a file. Returns None on error."""
    sha256 = hashlib.sha256()
    try:
        stat = abs_path.stat()
        with open(abs_path, "rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                sha256.update(chunk)
        return (sha256.hexdigest(), stat.st_size)
    except (OSError, PermissionError):
        return None


# ---------------------------------------------------------------------------
# Gitignore
# ---------------------------------------------------------------------------

def load_gitignore_spec():
    try:
        import pathspec
        if GITIGNORE_PATH.exists():
            with open(GITIGNORE_PATH, "r") as f:
                return pathspec.PathSpec.from_lines("gitwildmatch", f)
    except ImportError:
        pass
    return None


def should_exclude(rel_path: str, spec) -> bool:
    if os.path.basename(rel_path) in SELF_EXCLUSIONS:
        return True
    if spec and spec.match_file(rel_path):
        return True
    return False


# ---------------------------------------------------------------------------
# Directory walk (for FULL mode)
# ---------------------------------------------------------------------------

def walk_files(spec):
    """Yield (abs_path, rel_path) for all indexable files on disk."""
    for root, dirs, filenames in os.walk(BASE_DIR):
        rel_root = os.path.relpath(root, BASE_DIR)
        if rel_root == ".":
            rel_root = ""

        dirs[:] = [
            d for d in dirs
            if d not in DIR_EXCLUSIONS
            and not (spec and spec.match_file(os.path.join(rel_root, d) + "/"))
        ]

        for fname in filenames:
            if rel_root:
                rel_path = os.path.join(rel_root, fname)
            else:
                rel_path = fname

            if should_exclude(rel_path, spec):
                continue

            abs_path = Path(root) / fname
            yield (abs_path, rel_path)


# ---------------------------------------------------------------------------
# Audit logic
# ---------------------------------------------------------------------------

def audit_index(index: dict, workers: int, quiet: bool) -> dict:
    """
    INDEX_MODE: Verify every entry in the index exists on disk with
    matching hash and size.
    """
    results = {
        "mode": "index",
        "total_indexed": len(index),
        "missing_from_disk": [],
        "hash_mismatch": [],
        "size_mismatch": [],
        "ok": 0,
        "errors": [],
    }

    files_to_check = []
    for rel_path in sorted(index.keys()):
        abs_path = BASE_DIR / rel_path
        if should_exclude(rel_path, None):
            continue
        files_to_check.append((abs_path, rel_path, index[rel_path]))

    if not quiet:
        print(f"  Checking {len(files_to_check)} indexed files against disk...")

    with ProcessPoolExecutor(max_workers=workers) as executor:
        future_to_info = {}
        for abs_path, rel_path, expected in files_to_check:
            future = executor.submit(compute_hash_file, abs_path)
            future_to_info[future] = (rel_path, expected)

        checked = 0
        total = len(files_to_check)
        for future in as_completed(future_to_info):
            rel_path, expected = future_to_info[future]
            result = future.result()
            checked += 1

            if not quiet and checked % 5000 == 0:
                print(f"  Progress: {checked}/{total} ({checked/total*100:.1f}%)")

            if result is None:
                results["missing_from_disk"].append(rel_path)
                continue

            actual_sha256, actual_size = result
            if actual_sha256 != expected["sha256"]:
                results["hash_mismatch"].append({
                    "path": rel_path,
                    "expected": expected["sha256"],
                    "actual": actual_sha256,
                })
            elif actual_size != expected["size"]:
                results["size_mismatch"].append({
                    "path": rel_path,
                    "expected": expected["size"],
                    "actual": actual_size,
                })
            else:
                results["ok"] += 1

    return results


def audit_full(index: dict, workers: int, quiet: bool) -> dict:
    """
    FULL_MODE: Bidirectional audit — check index entries exist on disk
    AND check disk files exist in index.
    """
    spec = load_gitignore_spec()
    results = {
        "mode": "full",
        "total_indexed": len(index),
        "missing_from_disk": [],
        "missing_from_index": [],
        "hash_mismatch": [],
        "size_mismatch": [],
        "ok": 0,
        "errors": [],
    }

    # Pass 1: Verify index entries against disk (same as INDEX_MODE)
    if not quiet:
        print("  Pass 1: Index -> Disk verification...")

    index_files_to_check = []
    for rel_path in sorted(index.keys()):
        abs_path = BASE_DIR / rel_path
        if should_exclude(rel_path, spec):
            continue
        index_files_to_check.append((abs_path, rel_path, index[rel_path]))

    indexed_set = set()
    with ProcessPoolExecutor(max_workers=workers) as executor:
        future_to_info = {}
        for abs_path, rel_path, expected in index_files_to_check:
            future = executor.submit(compute_hash_file, abs_path)
            future_to_info[future] = (rel_path, expected)

        for future in as_completed(future_to_info):
            rel_path, expected = future_to_info[future]
            result = future.result()

            if result is None:
                results["missing_from_disk"].append(rel_path)
                continue

            actual_sha256, actual_size = result
            if actual_sha256 != expected["sha256"]:
                results["hash_mismatch"].append({
                    "path": rel_path,
                    "expected": expected["sha256"],
                    "actual": actual_sha256,
                })
            elif actual_size != expected["size"]:
                results["size_mismatch"].append({
                    "path": rel_path,
                    "expected": expected["size"],
                    "actual": actual_size,
                })
            else:
                results["ok"] += 1
                indexed_set.add(rel_path)

    # Pass 2: Check disk files against index
    if not quiet:
        print("  Pass 2: Disk -> Index verification...")

    disk_files = list(walk_files(spec))
    if not quiet:
        print(f"  Found {len(disk_files)} files on disk.")

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {}
        for abs_path, rel_path in disk_files:
            future = executor.submit(compute_hash_file, abs_path)
            futures[future] = rel_path

        for future in as_completed(futures):
            rel_path = futures[future]
            result = future.result()

            if result is None:
                continue

            if rel_path not in index:
                results["missing_from_index"].append(rel_path)

    return results


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_report(results: dict):
    """Print human-readable audit report."""
    mode = results["mode"]
    print()
    print("=" * 60)
    print("  ENE FILESYSTEM CONSISTENCY AUDIT")
    print("=" * 60)
    print(f"  Mode: {mode.upper()}")
    print(f"  Total indexed: {results['total_indexed']}")
    print()

    total_checked = (
        results["ok"]
        + len(results["hash_mismatch"])
        + len(results["size_mismatch"])
        + len(results["missing_from_disk"])
    )

    print(f"  Files verified:    {total_checked}")
    print(f"  OK:                {results['ok']}")
    print(f"  Missing from disk: {len(results['missing_from_disk'])}")

    if mode == "full":
        print(f"  Missing from index:{len(results['missing_from_index'])}")

    print(f"  Hash mismatches:   {len(results['hash_mismatch'])}")
    print(f"  Size mismatches:   {len(results['size_mismatch'])}")
    print()

    consistency = (results["ok"] / max(total_checked, 1)) * 100
    print(f"  Consistency:       {consistency:.2f}%")
    print()

    if results["ok"] == total_checked and (mode == "index" or not results["missing_from_index"]):
        print("  RESULT: PASS — 100% filesystem consistency confirmed.")
    else:
        print("  RESULT: FAIL — Inconsistencies detected.")

        if results["missing_from_disk"]:
            print()
            print("  Missing from disk (first 20):")
            for p in results["missing_from_disk"][:20]:
                print(f"    - {p}")
            if len(results["missing_from_disk"]) > 20:
                print(f"    ... and {len(results['missing_from_disk']) - 20} more")

        if results["hash_mismatch"]:
            print()
            print("  Hash mismatches (first 10):")
            for item in results["hash_mismatch"][:10]:
                print(f"    - {item['path']}")

        if mode == "full" and results["missing_from_index"]:
            print()
            print("  Missing from index (first 20):")
            for p in results["missing_from_index"][:20]:
                print(f"    + {p}")
            if len(results["missing_from_index"]) > 20:
                print(f"    ... and {len(results['missing_from_index']) - 20} more")

    print("=" * 60)


def save_report(results: dict, path: Path):
    """Save audit results as JSON."""
    with open(path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"  Report saved to {path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(description="ENE Parallelized Filesystem Consistency Audit")
    parser.add_argument("--full", action="store_true", help="Full bidirectional audit (disk <-> index)")
    parser.add_argument("--workers", type=int, default=WORKERS, help=f"Parallel workers (default: {WORKERS})")
    parser.add_argument("--json", dest="json_report", type=str, default=None, help="Save JSON report to path")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress output")
    args = parser.parse_args()

    t0 = time.time()

    if not args.quiet:
        print(f"[*] ENE Audit — Loading index from {INDEX_PATH}...")

    if not INDEX_PATH.exists():
        print(f"[!] ERROR: Index not found at {INDEX_PATH}")
        print("    Run sync_ene_index.py first to build the index.")
        sys.exit(1)

    with open(INDEX_PATH, "r") as f:
        index = json.load(f)

    if not args.quiet:
        print(f"[*] Index loaded: {len(index)} entries")
        print(f"[*] Mode: {'FULL (bidirectional)' if args.full else 'INDEX (index->disk)'}")
        print(f"[*] Workers: {args.workers}")
        print()

    if args.full:
        results = audit_full(index, args.workers, args.quiet)
    else:
        results = audit_index(index, args.workers, args.quiet)

    elapsed = time.time() - t0
    results["duration_seconds"] = round(elapsed, 2)

    print_report(results)

    if args.json_report:
        save_report(results, Path(args.json_report))

    # Exit code: 0 = pass, 1 = fail
    total_checked = (
        results["ok"]
        + len(results["hash_mismatch"])
        + len(results["size_mismatch"])
        + len(results["missing_from_disk"])
    )
    if results["ok"] == total_checked and (not args.full or not results["missing_from_index"]):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
