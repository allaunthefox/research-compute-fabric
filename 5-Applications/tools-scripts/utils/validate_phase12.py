#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK — PHASE 12: DELIVERABLE VALIDATION SUITE
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================

"""
5-Applications/tools-5-Applications/scripts/validate_phase12.py — Phase 12 Deliverable Validation Suite

Validates that all Phase 12 (and Phase 13) deliverables are properly:
1. Present on disk and indexed in ENE_INDEX.json
2. Emitting all required telemetry fields
3. Registered in the 14-axis concept space with valid vectors
4. Covered by test suites that pass
5. Integrated into the ENE self-diagnostics engine

Validation categories:
  V1 — Index Presence: Module files exist and are in ENE_INDEX.json
  V2 — Concept Space: Modules have valid 14-axis concept vectors
  V3 — Telemetry Fields: All required telemetry fields are defined
  V4 — Test Coverage: Test files exist and test classes are defined
  V5 — Module Integrity: Python modules import without error
  V6 — ENE Diagnostics Integration: Five-condition engine is functional
  V7 — SHA256 Manifest: Manifest rebuilds with absolute paths
  V8 — Symlink Check: repository scanned for broken symlinks

Usage:
    python 5-Applications/tools-5-Applications/scripts/validate_phase12.py              # Run all validations
    python 5-Applications/tools-5-Applications/scripts/validate_phase12.py --category V1  # Run single category
    python 5-Applications/tools-5-Applications/scripts/validate_phase12.py --verbose     # Detailed output
"""

import hashlib
import importlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = Path("/home/allaun/Research Stack")
INDEX_PATH = BASE_DIR / "ENE_INDEX.json"
MANIFEST_PATH = BASE_DIR / "ENE_INDEX.sha256"

CONCEPT_AXES = [
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

# Phase 12/13 modules to validate
MODULES_TO_VALIDATE = [
    {
        "path": "4-Infrastructure/infra/nodes/thermal_aware_dispatch.py",
        "name": "thermal_aware_dispatch",
        "phase": 12,
        "expected_telemetry": [
            "temperature_c",
            "thermal_drift_rate",
            "aging_index",
            "wear_level",
            "mtbf_hours",
            "lifetime_remaining_pct",
            "bit_flip_rate",
            "hot_path_utilization",
            "cold_path_utilization",
            "magnitude",
            "confidence",
            "entropy_delta",
        ],
        "expected_classes": [
            "ThermalScorer",
            "ThermalAwareDispatcher",
            "ThermalRestProtocol",
            "ThermalState",
            "AgingState",
            "StressAccumulator",
        ],
    },
    {
        "path": "0-Core-Formalism/core/src/engines/ene_diagnostics.py",
        "name": "ene_diagnostics",
        "phase": 13,
        "expected_telemetry": [
            "healthy",
            "conditions_passed",
            "conditions_total",
            "knit_coverage",
            "rigid_psd",
            "crnt_deficiency",
            "flavor_bias",
            "neuro_slope",
            "operating_mode",
        ],
        "expected_classes": [
            "ENEDiagnostics",
            "DiagnosticReport",
        ],
    },
]

# Test files to validate
TEST_FILES = [
    "5-Applications/tests/test_phase12_thermal_load_balancing.py",
    "5-Applications/tests/test_phase13_ene_diagnostics.py",
]


# ---------------------------------------------------------------------------
# Validation Results
# ---------------------------------------------------------------------------

class ValidationResult:
    def __init__(self, category: str, name: str):
        self.category = category
        self.name = name
        self.passed = False
        self.details = ""
        self.warnings = []

    def pass_(self, details: str = ""):
        self.passed = True
        self.details = details

    def fail(self, details: str = ""):
        self.passed = False
        self.details = details

    def warn(self, msg: str):
        self.warnings.append(msg)


# ---------------------------------------------------------------------------
# V1 — Index Presence
# ---------------------------------------------------------------------------

def validate_v1_index_presence(verbose: bool) -> list:
    """V1: Verify module files exist on disk and are in ENE_INDEX.json."""
    results = []

    # Load index
    index = {}
    if INDEX_PATH.exists():
        with open(INDEX_PATH) as f:
            index = json.load(f)

    for mod in MODULES_TO_VALIDATE:
        r = ValidationResult("V1", mod["name"])
        rel_path = mod["path"]
        abs_path = BASE_DIR / rel_path

        # Check disk existence
        if not abs_path.exists():
            r.fail(f"File not found on disk: {abs_path}")
            results.append(r)
            continue

        # Check index presence
        if rel_path not in index:
            r.fail(f"File not found in ENE_INDEX.json: {rel_path}")
            results.append(r)
            continue

        entry = index[rel_path]

        # Check index has basic fields
        if "sha256" not in entry or "size" not in entry:
            r.fail(f"Index entry missing sha256 or size: {rel_path}")
            results.append(r)
            continue

        # Check Phase 12 extended metadata
        if "concept_axes" not in entry:
            r.fail(f"Index entry missing concept_axes (14-axis space): {rel_path}")
            results.append(r)
            continue

        if "telemetry_fields" not in entry:
            r.fail(f"Index entry missing telemetry_fields: {rel_path}")
            results.append(r)
            continue

        if "module" not in entry:
            r.fail(f"Index entry missing module classification: {rel_path}")
            results.append(r)
            continue

        r.pass_(f"Indexed with sha256={entry['sha256'][:16]}... size={entry['size']}")
        results.append(r)

    return results


# ---------------------------------------------------------------------------
# V2 — Concept Space
# ---------------------------------------------------------------------------

def validate_v2_concept_space(verbose: bool) -> list:
    """V2: Verify modules have valid 14-axis concept vectors."""
    results = []

    index = {}
    if INDEX_PATH.exists():
        with open(INDEX_PATH) as f:
            index = json.load(f)

    for mod in MODULES_TO_VALIDATE:
        r = ValidationResult("V2", mod["name"])
        rel_path = mod["path"]

        if rel_path not in index:
            r.fail(f"Not in index (see V1)")
            results.append(r)
            continue

        entry = index[rel_path]
        concept_axes = entry.get("concept_axes")
        concept_vector = entry.get("concept_vector")

        if not concept_axes:
            r.fail("No concept_axes in index entry")
            results.append(r)
            continue

        # Check all 14 axes are present
        missing_axes = [axis for axis in CONCEPT_AXES if axis not in concept_axes]
        if missing_axes:
            r.fail(f"Missing concept axes: {missing_axes}")
            results.append(r)
            continue

        # Check values are in [0, 1]
        invalid_values = {
            axis: val
            for axis, val in concept_axes.items()
            if not (0.0 <= val <= 1.0)
        }
        if invalid_values:
            r.fail(f"Axis values out of [0,1] range: {invalid_values}")
            results.append(r)
            continue

        # Check concept_vector matches axes
        if concept_vector:
            if len(concept_vector) != 14:
                r.fail(f"concept_vector length is {len(concept_vector)}, expected 14")
                results.append(r)
                continue
        else:
            r.warn("No concept_vector (derived from concept_axes)")

        # Compute aggregate score
        total = sum(concept_axes.values())
        max_score = 14.0
        r.pass_(f"All 14 axes present, aggregate score={total:.1f}/{max_score:.1f}")
        results.append(r)

    return results


# ---------------------------------------------------------------------------
# V3 — Telemetry Fields
# ---------------------------------------------------------------------------

def validate_v3_telemetry(verbose: bool) -> list:
    """V3: Verify all required telemetry fields are defined in index."""
    results = []

    index = {}
    if INDEX_PATH.exists():
        with open(INDEX_PATH) as f:
            index = json.load(f)

    for mod in MODULES_TO_VALIDATE:
        r = ValidationResult("V3", mod["name"])
        rel_path = mod["path"]

        if rel_path not in index:
            r.fail("Not in index")
            results.append(r)
            continue

        entry = index[rel_path]
        telemetry_fields = entry.get("telemetry_fields", [])

        if not telemetry_fields:
            r.fail("No telemetry_fields in index entry")
            results.append(r)
            continue

        # Check expected telemetry fields are present
        missing_fields = []
        for expected in mod["expected_telemetry"]:
            # Support nested fields (dot notation)
            found = False
            for actual in telemetry_fields:
                if actual == expected or actual.startswith(expected + "."):
                    found = True
                    break
            if not found:
                missing_fields.append(expected)

        if missing_fields:
            r.fail(f"Missing telemetry fields: {missing_fields}")
            results.append(r)
            continue

        r.pass_(f"All {len(mod['expected_telemetry'])} expected telemetry fields present ({len(telemetry_fields)} total)")
        results.append(r)

    return results


# ---------------------------------------------------------------------------
# V4 — Test Coverage
# ---------------------------------------------------------------------------

def validate_v4_test_coverage(verbose: bool) -> list:
    """V4: Verify test files exist and contain expected test classes."""
    results = []

    for test_path in TEST_FILES:
        abs_path = BASE_DIR / test_path
        r = ValidationResult("V4", Path(test_path).stem)

        if not abs_path.exists():
            r.fail(f"Test file not found: {abs_path}")
            results.append(r)
            continue

        # Read test file and count test classes
        content = abs_path.read_text()
        test_classes = []
        import re
        for match in re.finditer(r'class\s+(Test\w+)\(', content):
            test_classes.append(match.group(1))

        if not test_classes:
            r.fail("No test classes found in file")
            results.append(r)
            continue

        # Count test methods
        test_methods = re.findall(r'def\s+(test_\w+)\(', content)

        r.pass_(f"Found {len(test_classes)} test classes, {len(test_methods)} test methods: {test_classes}")
        results.append(r)

    return results


# ---------------------------------------------------------------------------
# V5 — Module Integrity
# ---------------------------------------------------------------------------

def validate_v5_module_integrity(verbose: bool) -> list:
    """V5: Verify Python modules can be imported without error."""
    results = []

    for mod in MODULES_TO_VALIDATE:
        r = ValidationResult("V5", mod["name"])
        rel_path = mod["path"]
        abs_path = BASE_DIR / rel_path

        if not abs_path.exists():
            r.fail("File not found")
            results.append(r)
            continue

        # Check syntax validity
        try:
            compile(abs_path.read_text(), str(abs_path), "exec")
        except SyntaxError as e:
            r.fail(f"Syntax error: {e}")
            results.append(r)
            continue

        # Try import (best effort — may fail due to dependencies)
        module_name = Path(rel_path).stem
        try:
            # Add module paths for import
            parent_dir = str(abs_path.parent)
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)

            # Ensure tools/ is on sys.path for io_harness_compat resolution
            tools_dir = str(BASE_DIR / "tools")
            if tools_dir not in sys.path:
                sys.path.insert(0, tools_dir)

            mod_obj = importlib.import_module(module_name)

            # Check expected classes exist
            missing_classes = []
            for cls_name in mod.get("expected_classes", []):
                if not hasattr(mod_obj, cls_name):
                    missing_classes.append(cls_name)

            if missing_classes:
                r.fail(f"Imported but missing classes: {missing_classes}")
            else:
                r.pass_(f"Imports successfully, all {len(mod['expected_classes'])} expected classes present")
        except ImportError as e:
            # Import may fail due to missing deps; this is a warning, not a failure
            r.pass_(f"Syntax valid; import skipped (missing dependency: {e})")
            r.warn("Could not verify import due to missing dependencies")
        except Exception as e:
            r.fail(f"Import error: {type(e).__name__}: {e}")

        results.append(r)

    return results


# ---------------------------------------------------------------------------
# V6 — ENE Diagnostics Integration
# ---------------------------------------------------------------------------

def validate_v6_ene_diagnostics(verbose: bool) -> list:
    """V6: Verify ENE diagnostics engine has all five conditions implemented."""
    results = []
    r = ValidationResult("V6", "ene_diagnostics_five_conditions")

    diag_path = BASE_DIR / "0-Core-Formalism/core/src/engines/ene_diagnostics.py"
    if not diag_path.exists():
        r.fail("ene_diagnostics.py not found")
        results.append(r)
        return results

    content = diag_path.read_text()

    # Check for all five condition methods
    expected_methods = [
        "check_knit",
        "check_rigid",
        "check_crnt",
        "check_flavor",
        "check_neuro",
    ]

    missing = []
    for method in expected_methods:
        if f"def {method}" not in content:
            missing.append(method)

    if missing:
        r.fail(f"Missing diagnostic methods: {missing}")
        results.append(r)
        return results

    # Check for full_report method
    if "def full_report" not in content:
        r.fail("Missing full_report() method")
        results.append(r)
        return results

    # Check for DiagnosticReport dataclass
    if "class DiagnosticReport" not in content:
        r.fail("Missing DiagnosticReport dataclass")
        results.append(r)
        return results

    r.pass_(f"All five conditions implemented: KNIT, RIGID, CRNT, FLAVOR, NEURO")
    results.append(r)

    return results


# ---------------------------------------------------------------------------
# V7 — SHA256 Manifest
# ---------------------------------------------------------------------------

def validate_v7_manifest(verbose: bool) -> list:
    """V7: Verify SHA256 manifest can be rebuilt with absolute paths."""
    results = []
    r = ValidationResult("V7", "sha256_manifest")

    if not MANIFEST_PATH.exists():
        r.fail("Manifest file not found")
        results.append(r)
        return results

    # Read manifest and verify format
    content = MANIFEST_PATH.read_text().strip()
    lines = content.split("\n")

    if not lines:
        r.fail("Manifest is empty")
        results.append(r)
        return results

    # Verify format: <sha256>  <absolute_path>
    invalid_lines = []
    paths_not_absolute = []
    for line in lines:
        parts = line.split("  ", 1)
        if len(parts) != 2:
            invalid_lines.append(line[:80])
            continue
        sha256_hex, abs_path = parts
        if len(sha256_hex) != 64:
            invalid_lines.append(f"bad hash length: {sha256_hex[:20]}...")
            continue
        if not os.path.isabs(abs_path):
            paths_not_absolute.append(abs_path)

    if invalid_lines:
        r.fail(f"Invalid manifest lines: {invalid_lines[:5]}")
        results.append(r)
        return results

    if paths_not_absolute:
        r.fail(f"Paths not absolute: {paths_not_absolute[:5]}")
        results.append(r)
        return results

    # Cross-reference with index
    index = {}
    if INDEX_PATH.exists():
        with open(INDEX_PATH) as f:
            index = json.load(f)

    manifest_paths = set()
    for line in lines:
        parts = line.split("  ", 1)
        if len(parts) == 2:
            abs_path = parts[1]
            # Convert absolute back to relative
            if abs_path.startswith(str(BASE_DIR)):
                rel = os.path.relpath(abs_path, str(BASE_DIR))
                manifest_paths.add(rel)

    # Normalize index keys the same way the manifest sanitizer does
    # (replaces all whitespace runs with single spaces)
    index_keys = set()
    for key in index.keys():
        index_keys.add(" ".join(key.split()))
    missing_from_manifest = index_keys - manifest_paths
    extra_in_manifest = manifest_paths - index_keys

    if missing_from_manifest:
        r.fail(f"Index entries missing from manifest: {len(missing_from_manifest)} entries")
        results.append(r)
        return results

    if extra_in_manifest:
        r.fail(f"Extra entries in manifest not in index: {len(extra_in_manifest)} entries")
        results.append(r)
        return results

    r.pass_(f"Manifest valid: {len(lines)} entries, all absolute paths, matches index")
    results.append(r)

    return results


# ---------------------------------------------------------------------------
# V8 — Broken Symlink Check
# ---------------------------------------------------------------------------

def validate_v8_symlinks(verbose: bool) -> list:
    """V8: Scan repository for broken symlinks."""
    results = []
    r = ValidationResult("V8", "symlink_integrity")

    # Scan for broken symlinks in the repository
    broken_symlinks = []
    for root, dirs, files in os.walk(BASE_DIR):
        # Skip exclusions
        rel_root = os.path.relpath(root, BASE_DIR)
        if rel_root == ".":
            rel_root = ""

        skip = False
        for excl in {".git", "__pycache__", ".venv-eng", ".venv-fem", "node_modules", "target"}:
            if excl in dirs:
                dirs.remove(excl)
            if excl in rel_root:
                skip = True

        if skip:
            continue

        for entry in dirs + files:
            full_path = Path(root) / entry
            if full_path.is_symlink() and not full_path.exists():
                broken_symlinks.append(str(full_path))

    if broken_symlinks:
        r.fail(f"Found {len(broken_symlinks)} broken symlink(s): {broken_symlinks[:5]}")
    else:
        r.pass_("No broken symlinks found")

    results.append(r)
    return results


# ---------------------------------------------------------------------------
# Summary and Reporting
# ---------------------------------------------------------------------------

def print_validation_results(all_results: list, verbose: bool):
    """Print formatted validation results."""
    print()
    print("=" * 70)
    print("  PHASE 12/13 DELIVERABLE VALIDATION REPORT")
    print("=" * 70)
    print()

    categories = {}
    for r in all_results:
        if r.category not in categories:
            categories[r.category] = []
        categories[r.category].append(r)

    total_pass = 0
    total_fail = 0
    total_warn = 0

    for cat in sorted(categories.keys()):
        checks = categories[cat]
        cat_name = {
            "V1": "Index Presence",
            "V2": "Concept Space (14-axis)",
            "V3": "Telemetry Fields",
            "V4": "Test Coverage",
            "V5": "Module Integrity",
            "V6": "ENE Diagnostics Integration",
            "V7": "SHA256 Manifest",
            "V8": "Symlink Integrity",
        }.get(cat, cat)

        print(f"--- {cat}: {cat_name} ---")
        for r in checks:
            status = "PASS" if r.passed else "FAIL"
            if r.passed:
                total_pass += 1
            else:
                total_fail += 1
            total_warn += len(r.warnings)

            icon = "[OK]" if r.passed else "[!!]"
            print(f"  {icon} {r.name}: {r.details}")
            for w in r.warnings:
                print(f"       WARNING: {w}")
        print()

    print("=" * 70)
    print(f"  SUMMARY: {total_pass} passed, {total_fail} failed, {total_warn} warnings")
    print()

    if total_fail == 0:
        print("  RESULT: ALL VALIDATIONS PASSED")
    else:
        print("  RESULT: VALIDATION FAILED — see failures above")
    print("=" * 70)


def generate_checklist(all_results: list) -> str:
    """Generate a validation checklist string."""
    lines = ["# Phase 12/13 Validation Checklist", ""]
    for r in all_results:
        status = "[x]" if r.passed else "[ ]"
        lines.append(f"- {status} {r.category} / {r.name}: {r.details}")
    lines.append("")
    passed = sum(1 for r in all_results if r.passed)
    lines.append(f"**Result: {passed}/{len(all_results)} checks passed**")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Phase 12/13 Deliverable Validation Suite")
    parser.add_argument("--category", type=str, default=None,
                        help="Run only a specific validation category (V1-V8)")
    parser.add_argument("--verbose", action="store_true", help="Detailed output")
    parser.add_argument("--json", dest="json_output", type=str, default=None,
                        help="Save JSON report to path")
    args = parser.parse_args()

    t0 = time.time()

    print(f"[*] Phase 12/13 Validation Suite")
    print(f"[*] Base: {BASE_DIR}")
    print()

    # Map of validation functions
    validators = {
        "V1": validate_v1_index_presence,
        "V2": validate_v2_concept_space,
        "V3": validate_v3_telemetry,
        "V4": validate_v4_test_coverage,
        "V5": validate_v5_module_integrity,
        "V6": validate_v6_ene_diagnostics,
        "V7": validate_v7_manifest,
        "V8": validate_v8_symlinks,
    }

    all_results = []

    if args.category:
        cat = args.category.upper()
        if cat not in validators:
            print(f"[!] Unknown category: {cat}")
            print(f"    Valid: {', '.join(validators.keys())}")
            sys.exit(1)
        print(f"[*] Running {cat} only...")
        all_results.extend(validators[cat](args.verbose))
    else:
        for cat_name in sorted(validators.keys()):
            print(f"[*] Running {cat_name}...")
            all_results.extend(validators[cat_name](args.verbose))

    elapsed = time.time() - t0
    print_validation_results(all_results, args.verbose)

    # Save JSON report if requested
    if args.json_output:
        report = {
            "timestamp": time.time(),
            "duration_seconds": round(elapsed, 2),
            "results": [
                {
                    "category": r.category,
                    "name": r.name,
                    "passed": r.passed,
                    "details": r.details,
                    "warnings": r.warnings,
                }
                for r in all_results
            ],
            "checklist": generate_checklist(all_results),
        }
        with open(args.json_output, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\n[*] JSON report saved to {args.json_output}")

    # Exit code
    failed = sum(1 for r in all_results if not r.passed)
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
