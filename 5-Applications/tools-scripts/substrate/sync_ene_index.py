#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK — PHASE 12: ENE INDEX SYNCHRONIZATION
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================

"""
5-Applications/tools-5-Applications/scripts/sync_ene_index.py — ENE Index Builder and Synchronizer

Replaces the legacy version in tools/scratch/. This production-grade script:

1. Walks the entire repository tree, respecting .gitignore and standard exclusions
2. Computes SHA-256 hashes and file sizes in parallel
3. Builds ENE_INDEX.json with extended metadata for Phase 12 modules:
   - concept_axes: 14-axis concept space coordinates for thermal/stress/aging modules
   - telemetry_fields: list of emitted telemetry keys per module
   - module_classification: thermal | stress | aging | dispatch | diagnostics
4. Rebuilds ENE_INDEX.sha256 with absolute paths (sorted, deterministic)
5. Optionally runs a post-sync audit to confirm 100% consistency

Usage:
    python 5-Applications/tools-5-Applications/scripts/sync_ene_index.py              # Build index + manifest
    python 5-Applications/tools-5-Applications/scripts/sync_ene_index.py --audit      # Build + post-sync audit
    python 5-Applications/tools-5-Applications/scripts/sync_ene_index.py --dry-run    # Show what would change
    python 5-Applications/tools-5-Applications/scripts/sync_ene_index.py --validate   # Build + run Phase 12 validation
"""

import hashlib
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = Path("/home/allaun/Research Stack")
INDEX_PATH = BASE_DIR / "ENE_INDEX.json"
MANIFEST_PATH = BASE_DIR / "ENE_INDEX.sha256"
GITIGNORE_PATH = BASE_DIR / ".gitignore"

WORKERS = os.cpu_count() or 8
CHUNK_SIZE = 65536  # 64KB read chunks

# Files excluded from indexing (self-referential + transient)
SELF_EXCLUSIONS = {
    "ENE_INDEX.json",
    "ENE_INDEX.sha256",
    ".gitignore",
    "substrate_index.db",
    # Heartbeat/telemetry files rewritten by live daemons — would always
    # race against the audit step and produce spurious hash mismatches.
    "SHADOW_AUDIT.json",
    "5-Applications/tools-5-Applications/scripts/daemon_health.json",
    "5-Applications/tools-5-Applications/scripts/shadow_telemetry.json",
    "0-Core-Formalism/core/ui/telemetry.json",
}

# Directories excluded from walk
DIR_EXCLUSIONS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".venv-eng",
    ".venv-fem",
    "node_modules",
    "target",
}

# Force-include paths that are gitignored but critical for ENE routing
FORCE_INCLUDE_PREFIXES = (
    "pbacs/",
    "0-Core-Formalism/core/hw/diat_sqrt_table.mem",
    "0-Core-Formalism/core/hw/diat",
)

# ---------------------------------------------------------------------------
# Phase 12 Module Registry — 14-Axis Concept Space
# ---------------------------------------------------------------------------

# The 14 concept axes:
#   [0]  thermal_awareness    — temperature sensing and headroom calculation
#   [1]  stress_accumulation  — cumulative informatic stress modeling
#   [2]  hardware_aging       — wear, MTBF, silicon degradation tracking
#   [3]  load_balancing       — dispatch decisions with multi-factor scoring
#   [4]  autonomous_rest      — closed-loop thermal pause/resume protocol
#   [5]  bit_flip_modeling    — Arrhenius-based error rate estimation
#   [6]  electromigration     — current-driven degradation modeling
#   [7]  fatigue_accumulation — cycle-based wear accumulation
#   [8]  cooling_capacity     — passive/active thermal dissipation rating
#   [9]  workload_intensity   — computational load classification
#   [10] entropy_production   — Shannon entropy of workload distribution
#   [11] mtbf_prediction     — mean-time-between-failure forecasting
#   [12] silicon_health       — transistor-level degradation estimation
#   [13] flame_mode          — emergency dispatch under thermal constraint

PHASE12_MODULES = {
    "4-Infrastructure/infra/nodes/thermal_aware_dispatch.py": {
        "module": "thermal_aware_dispatch",
        "classification": "dispatch",
        "concept_axes": {
            "thermal_awareness": 1.0,
            "stress_accumulation": 0.8,
            "hardware_aging": 0.9,
            "load_balancing": 1.0,
            "autonomous_rest": 1.0,
            "bit_flip_modeling": 0.7,
            "electromigration": 0.3,
            "fatigue_accumulation": 0.6,
            "cooling_capacity": 0.5,
            "workload_intensity": 0.9,
            "entropy_production": 0.4,
            "mtbf_prediction": 0.8,
            "silicon_health": 0.7,
            "flame_mode": 1.0,
        },
        "telemetry_fields": [
            "magnitude",
            "confidence",
            "entropy_delta",
            "error_rates.hash",
            "error_rates.log",
            "temperature_c",
            "thermal_drift_rate",
            "aging_index",
            "wear_level",
            "mtbf_hours",
            "lifetime_remaining_pct",
            "bit_flip_rate",
            "hot_path_utilization",
            "cold_path_utilization",
        ],
        "phase": 12,
    },
    "0-Core-Formalism/core/src/engines/ene_diagnostics.py": {
        "module": "ene_diagnostics",
        "classification": "diagnostics",
        "concept_axes": {
            "thermal_awareness": 0.2,
            "stress_accumulation": 0.5,
            "hardware_aging": 0.1,
            "load_balancing": 0.3,
            "autonomous_rest": 0.1,
            "bit_flip_modeling": 0.1,
            "electromigration": 0.1,
            "fatigue_accumulation": 0.2,
            "cooling_capacity": 0.1,
            "workload_intensity": 0.3,
            "entropy_production": 0.4,
            "mtbf_prediction": 0.1,
            "silicon_health": 0.1,
            "flame_mode": 0.4,
        },
        "telemetry_fields": [
            "healthy",
            "conditions_passed",
            "conditions_total",
            "knit_coverage",
            "rigid_psd",
            "crnt_deficiency",
            "flavor_bias",
            "neuro_slope",
            "operating_mode",
            "n_points",
        ],
        "phase": 13,
    },
    "5-Applications/tests/test_phase12_thermal_load_balancing.py": {
        "module": "test_phase12_thermal_load_balancing",
        "classification": "test",
        "concept_axes": {
            "thermal_awareness": 1.0,
            "stress_accumulation": 0.8,
            "hardware_aging": 0.9,
            "load_balancing": 1.0,
            "autonomous_rest": 1.0,
            "bit_flip_modeling": 0.7,
            "electromigration": 0.3,
            "fatigue_accumulation": 0.6,
            "cooling_capacity": 0.5,
            "workload_intensity": 0.9,
            "entropy_production": 0.4,
            "mtbf_prediction": 0.8,
            "silicon_health": 0.7,
            "flame_mode": 1.0,
        },
        "telemetry_fields": [
            "thermal_score",
            "aging_index",
            "stress_magnitude",
            "bit_flip_rate",
            "lifetime_remaining_pct",
            "thermal_drift_rate",
        ],
        "phase": 12,
    },
    "5-Applications/tests/test_phase13_ene_diagnostics.py": {
        "module": "test_phase13_ene_diagnostics",
        "classification": "test",
        "concept_axes": {
            "thermal_awareness": 0.2,
            "stress_accumulation": 0.5,
            "hardware_aging": 0.1,
            "load_balancing": 0.3,
            "autonomous_rest": 0.1,
            "bit_flip_modeling": 0.1,
            "electromigration": 0.1,
            "fatigue_accumulation": 0.2,
            "cooling_capacity": 0.1,
            "workload_intensity": 0.3,
            "entropy_production": 0.4,
            "mtbf_prediction": 0.1,
            "silicon_health": 0.1,
            "flame_mode": 0.4,
        },
        "telemetry_fields": [
            "rigid_stress_matrix_psd",
            "knit_hamiltonian_path_exists",
            "crnt_deficiency",
            "flavor_bias",
            "neuro_gradient_slope",
        ],
        "phase": 13,
    },
}

# Ordered list of concept axes for vector representation
CONCEPT_AXIS_ORDER = [
    "thermal_awareness",
    "stress_accumulation",
    "hardware_aging",
    "load_balancing",
    "autonomous_rest",
    "bit_flip_modeling",
    "electromigration",
    "fatigue_accumulation",
    "cooling_capacity",
    "workload_intensity",
    "entropy_production",
    "mtbf_prediction",
    "silicon_health",
    "flame_mode",
]


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class FileEntry:
    """Single file entry for the ENE index."""
    sha256: str
    size: int
    modified: float
    # Phase 12 extended metadata (optional, populated for known modules)
    module: Optional[str] = None
    classification: Optional[str] = None
    concept_axes: Optional[dict] = None
    concept_vector: Optional[list] = None
    telemetry_fields: Optional[list] = None
    phase: Optional[int] = None

    def to_dict(self) -> dict:
        d = {"sha256": self.sha256, "size": self.size, "modified": self.modified}
        if self.module is not None:
            d["module"] = self.module
        if self.classification is not None:
            d["classification"] = self.classification
        if self.concept_axes is not None:
            d["concept_axes"] = self.concept_axes
        if self.concept_vector is not None:
            d["concept_vector"] = self.concept_vector
        if self.telemetry_fields is not None:
            d["telemetry_fields"] = self.telemetry_fields
        if self.phase is not None:
            d["phase"] = self.phase
        return d


# ---------------------------------------------------------------------------
# Core hashing
# ---------------------------------------------------------------------------

def compute_hash(file_path: Path) -> Optional[tuple]:
    """
    Compute SHA-256 hash, size, and mtime for a file.
    Returns (sha256_hex, size, mtime) or None on error.
    """
    sha256 = hashlib.sha256()
    try:
        stat = file_path.stat()
        with open(file_path, "rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                sha256.update(chunk)
        return (sha256.hexdigest(), stat.st_size, stat.st_mtime)
    except (OSError, PermissionError):
        return None


# ---------------------------------------------------------------------------
# Gitignore handling
# ---------------------------------------------------------------------------

def load_gitignore_spec():
    """Load .gitignore patterns using pathspec if available, else simple parser."""
    if not GITIGNORE_PATH.exists():
        return None
    try:
        import pathspec
        with open(GITIGNORE_PATH, "r") as f:
            return pathspec.PathSpec.from_lines("gitwildmatch", f)
    except ImportError:
        # Fallback: return None, rely on DIR_EXCLUSIONS only
        return None


def should_exclude(rel_path: str, spec) -> bool:
    """Determine if a relative path should be excluded from indexing."""
    # Force-include critical paths even if gitignored
    for prefix in FORCE_INCLUDE_PREFIXES:
        if rel_path.startswith(prefix):
            # Still respect self-exclusions and dir exclusions
            basename = os.path.basename(rel_path)
            if basename in SELF_EXCLUSIONS or rel_path in SELF_EXCLUSIONS:
                return True
            return False

    # Self-exclusions
    basename = os.path.basename(rel_path)
    if basename in SELF_EXCLUSIONS:
        return True
    if rel_path in SELF_EXCLUSIONS:
        return True

    # Gitignore spec
    if spec and spec.match_file(rel_path):
        return True

    return False


# ---------------------------------------------------------------------------
# Directory walk
# ---------------------------------------------------------------------------

def _walk_tree(base_rel: str, real_root: Path, files: list, spec, visited: set):
    """Recursive helper that follows directory symlinks inside BASE_DIR."""
    for root, dirs, filenames in os.walk(real_root, followlinks=True):
        rel_root = os.path.relpath(root, BASE_DIR)
        if rel_root == ".":
            rel_root = ""

        # Determine the logical path prefix (for symlink aliases)
        if base_rel and rel_root.startswith(str(real_root.relative_to(BASE_DIR))):
            logical_root = base_rel + rel_root[len(str(real_root.relative_to(BASE_DIR))):]
        elif base_rel:
            logical_root = base_rel
        else:
            logical_root = rel_root

        # Remove excluded directories (unless force-included)
        def _keep_dir(d: str) -> bool:
            if d in DIR_EXCLUSIONS:
                return False
            rel_dir = os.path.join(rel_root, d) + "/"
            # Force-include critical directories
            for prefix in FORCE_INCLUDE_PREFIXES:
                if rel_dir.startswith(prefix) or prefix.startswith(rel_dir):
                    return True
            if spec and spec.match_file(rel_dir):
                return False
            return True

        dirs[:] = [d for d in dirs if _keep_dir(d)]

        for fname in filenames:
            abs_path = Path(root) / fname
            if logical_root:
                log_path = os.path.join(logical_root, fname)
            else:
                log_path = fname

            if should_exclude(log_path, spec):
                continue

            # Resolve symlink loops
            real_path = abs_path.resolve()
            key = (str(real_path), log_path)
            if key in visited:
                continue
            visited.add(key)
            files.append((abs_path, log_path))


def collect_files():
    """
    Walk BASE_DIR and return list of (abs_path, rel_path) tuples
    for all indexable files, including directory symlinks.
    """
    spec = load_gitignore_spec()
    files = []
    visited = set()

    _walk_tree("", BASE_DIR, files, spec, visited)

    # Explicitly handle top-level directory symlinks (os.walk doesn't follow them)
    for entry in BASE_DIR.iterdir():
        if entry.is_symlink() and entry.is_dir():
            target = entry.resolve()
            # Only follow symlinks that point inside BASE_DIR
            if str(target).startswith(str(BASE_DIR) + os.sep):
                link_name = entry.name
                _walk_tree(link_name, target, files, spec, visited)

    return files


# ---------------------------------------------------------------------------
# Parallel hash computation
# ---------------------------------------------------------------------------

def hash_files_parallel(files: list, workers: int = WORKERS) -> dict:
    """
    Hash files in parallel using ProcessPoolExecutor.
    Returns dict of {rel_path: FileEntry}.
    """
    index = {}
    abs_paths = [abs_path for abs_path, _ in files]

    with ProcessPoolExecutor(max_workers=workers) as executor:
        future_to_info = {}
        for i, abs_path in enumerate(abs_paths):
            future = executor.submit(compute_hash, abs_path)
            future_to_info[future] = i

        for future in as_completed(future_to_info):
            idx = future_to_info[future]
            abs_path, rel_path = files[idx]
            result = future.result()

            if result is None:
                continue

            sha256_hex, size, mtime = result
            entry = FileEntry(sha256=sha256_hex, size=size, modified=mtime)

            # Enrich with Phase 12 module metadata if applicable
            if rel_path in PHASE12_MODULES:
                mod = PHASE12_MODULES[rel_path]
                entry.module = mod["module"]
                entry.classification = mod["classification"]
                entry.concept_axes = mod["concept_axes"]
                entry.concept_vector = [
                    mod["concept_axes"].get(axis, 0.0)
                    for axis in CONCEPT_AXIS_ORDER
                ]
                entry.telemetry_fields = mod["telemetry_fields"]
                entry.phase = mod["phase"]

            index[rel_path] = entry

    return index


# ---------------------------------------------------------------------------
# Index serialization
# ---------------------------------------------------------------------------

def save_index(index: dict):
    """Save ENE_INDEX.json with sorted keys for deterministic output."""
    output = {}
    for rel_path in sorted(index.keys()):
        output[rel_path] = index[rel_path].to_dict()

    with open(INDEX_PATH, "w") as f:
        json.dump(output, f, indent=2, sort_keys=False)

    return output


def _sanitize_manifest_path(abs_path: str) -> str:
    """Sanitize a path for safe inclusion in the line-based manifest.

    Replaces newlines with spaces and strips leading/trailing whitespace
    so the manifest parser can always split on '  ' reliably.
    """
    return " ".join(abs_path.split())


def save_manifest(index: dict):
    """
    Rebuild ENE_INDEX.sha256 with absolute paths.
    Format: <sha256>  <absolute_path>
    Sorted by path for deterministic output.

    Paths containing newlines or other whitespace are sanitized so that
    every manifest line cleanly splits into exactly two fields.
    """
    lines = []
    for rel_path in sorted(index.keys()):
        sha256_hex = index[rel_path].sha256
        abs_path = _sanitize_manifest_path(str(BASE_DIR / rel_path))
        lines.append(f"{sha256_hex}  {abs_path}")

    with open(MANIFEST_PATH, "w") as f:
        f.write("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# Audit (post-sync verification)
# ---------------------------------------------------------------------------

def run_audit(index: dict, spec=None) -> dict:
    """
    Run a parallelized audit: verify every indexed file exists on disk
    with matching hash and size.
    Returns audit results dict.
    """
    results = {
        "missing_from_disk": [],
        "hash_mismatch": [],
        "size_mismatch": [],
        "ok": 0,
        "errors": [],
    }

    files_to_check = []
    for rel_path in sorted(index.keys()):
        abs_path = BASE_DIR / rel_path
        if should_exclude(rel_path, spec):
            continue
        files_to_check.append((abs_path, rel_path, index[rel_path]))

    with ProcessPoolExecutor(max_workers=WORKERS) as executor:
        future_to_path = {}
        for abs_path, rel_path, expected_entry in files_to_check:
            future = executor.submit(compute_hash, abs_path)
            future_to_path[future] = (rel_path, expected_entry)

        for future in as_completed(future_to_path):
            rel_path, expected = future_to_path[future]
            result = future.result()

            if result is None:
                results["missing_from_disk"].append(rel_path)
                continue

            actual_sha256, actual_size, _ = result

            exp_sha = expected.get("sha256", expected.get("hash", ""))
            exp_sz = expected.get("size", 0)

            if actual_sha256 != exp_sha:
                results["hash_mismatch"].append({
                    "path": rel_path,
                    "expected": exp_sha,
                    "actual": actual_sha256,
                })
            elif actual_size != exp_sz:
                results["size_mismatch"].append({
                    "path": rel_path,
                    "expected": exp_sz,
                    "actual": actual_size,
                })
            else:
                results["ok"] += 1

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(description="ENE Index Builder and Synchronizer")
    parser.add_argument("--audit", action="store_true", help="Run post-sync audit")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing")
    parser.add_argument("--validate", action="store_true", help="Run Phase 12 validation after sync")
    parser.add_argument("--workers", type=int, default=WORKERS, help=f"Number of parallel workers (default: {WORKERS})")
    args = parser.parse_args()

    print(f"[*] ENE Index Sync — Phase 12")
    print(f"[*] Base directory: {BASE_DIR}")
    print(f"[*] Workers: {args.workers}")
    print()

    # Phase 1: Collect files
    t0 = time.time()
    print(f"[1/4] Collecting files from repository tree...")
    files = collect_files()
    print(f"     Found {len(files)} files to index.")

    # Phase 2: Compute hashes in parallel
    print(f"[2/4] Computing SHA-256 hashes ({args.workers} workers)...")
    index = hash_files_parallel(files, workers=args.workers)
    print(f"     Indexed {len(index)} files.")

    # Phase 3: Save index and manifest
    if args.dry_run:
        print()
        print("[DRY RUN] Would save:")
        print(f"  - {INDEX_PATH} ({len(index)} entries)")
        print(f"  - {MANIFEST_PATH} ({len(index)} lines)")
        # Show Phase 12 module entries
        print()
        print("Phase 12/13 modules that would be enriched:")
        for rel_path, mod in PHASE12_MODULES.items():
            if rel_path in index:
                print(f"  + {rel_path} [{mod['classification']}] axes={sum(mod['concept_axes'].values()):.1f}/14.0")
        return

    print(f"[3/4] Saving index and manifest...")
    output = save_index(index)
    save_manifest(index)
    print(f"     Wrote {INDEX_PATH} ({os.path.getsize(INDEX_PATH) / 1024 / 1024:.1f} MB)")
    print(f"     Wrote {MANIFEST_PATH} ({os.path.getsize(MANIFEST_PATH) / 1024 / 1024:.1f} MB)")

    # Phase 4: Optional audit
    if args.audit:
        print()
        print(f"[4/4] Running post-sync audit...")
        spec = load_gitignore_spec()
        audit_results = run_audit(output, spec)

        total_checked = audit_results["ok"] + len(audit_results["hash_mismatch"]) + len(audit_results["size_mismatch"]) + len(audit_results["missing_from_disk"])
        print(f"     Files checked: {total_checked}")
        print(f"     OK: {audit_results['ok']}")
        print(f"     Missing from disk: {len(audit_results['missing_from_disk'])}")
        print(f"     Hash mismatches: {len(audit_results['hash_mismatch'])}")
        print(f"     Size mismatches: {len(audit_results['size_mismatch'])}")

        consistency_pct = (audit_results["ok"] / max(total_checked, 1)) * 100
        print(f"     Consistency: {consistency_pct:.2f}%")

        if audit_results["ok"] == total_checked:
            print("     PASS: 100% filesystem consistency confirmed.")
        else:
            print("     WARN: Inconsistencies detected. Review audit results above.")

    # Optional validation
    if args.validate:
        print()
        print(f"[*] Launching Phase 12 validation suite...")
        validate_script = BASE_DIR / "tools" / "scripts" / "validate_phase12.py"
        if validate_script.exists():
            import subprocess
            result = subprocess.run(
                [sys.executable, str(validate_script)],
                capture_output=False,
                cwd=str(BASE_DIR),
            )
            if result.returncode != 0:
                print(f"[!] Phase 12 validation exited with code {result.returncode}")
        else:
            print(f"[!] Validation script not found at {validate_script}")

    elapsed = time.time() - t0
    print()
    print(f"[*] Sync complete in {elapsed:.2f} seconds.")
    print(f"[*] Total files indexed: {len(index)}")


if __name__ == "__main__":
    main()
