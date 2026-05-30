#!/usr/bin/env python3
"""
find_approximations.py — Find all modules with dangerous numerical approximations

This script scans the Lean codebase for:
  1. Uses of old expNeg/expLUT (4-entry lookup table)
  2. Linearized approximations (1-x for exp)
  3. Taylor approximations without error bounds
  4. Missing imports of Q16_16Numerics

Output: List of files and lines that need updating.
"""

import re
import os
from pathlib import Path

SEMASNTICS_DIR = Path("/home/allaun/Research Stack/0-Core-Formalism/lean/Semantics/Semantics")

# Patterns that indicate dangerous approximations
DANGEROUS_PATTERNS = [
    (r'Q16_16\.expNeg', "Old expNeg lookup table (4 entries)"),
    (r'expLUT', "Old expLUT lookup table"),
    (r'1 - x|1 - .*\.toInt', "Linearized exp approximation"),
    (r'Taylor.*cos.*1 - x.*x/2', "Cosine Taylor without error bounds"),
    (r'simplified.*sqrt', "Simplified sqrt"),
    (r'simplified.*exp', "Simplified exp"),
    (r'linearized', "Linearized approximation"),
]

# Patterns that are OK (using rigorous functions)
OK_PATTERNS = [
    (r'import Semantics\.Q16_16Numerics', "Has rigorous numerics import"),
    (r'Q16_16Numerics\.exp', "Using rigorous exp"),
    (r'Q16_16Numerics\.sqrt', "Using rigorous sqrt"),
    (r'Q16_16Numerics\.sin', "Using rigorous sin"),
    (r'Q16_16Numerics\.cos', "Using rigorous cos"),
]

def scan_file(filepath):
    """Scan a single file for approximation issues."""
    issues = []
    
    with open(filepath, 'r') as f:
        for i, line in enumerate(f, 1):
            for pattern, desc in DANGEROUS_PATTERNS:
                if re.search(pattern, line):
                    issues.append({
                        'file': str(filepath),
                        'line': i,
                        'code': line.strip(),
                        'issue': desc
                    })
    
    return issues

def main():
    all_issues = []
    
    for filepath in SEMASNTICS_DIR.rglob("*.lean"):
        issues = scan_file(filepath)
        all_issues.extend(issues)
    
    # Group by file
    by_file = {}
    for issue in all_issues:
        f = issue['file']
        if f not in by_file:
            by_file[f] = []
        by_file[f].append(issue)
    
    # Print report
    print("=" * 80)
    print("NUMERICAL APPROXIMATION AUDIT REPORT")
    print("=" * 80)
    print(f"\nTotal issues found: {len(all_issues)}")
    print(f"Files affected: {len(by_file)}")
    
    for filepath, issues in sorted(by_file.items()):
        rel_path = os.path.relpath(filepath, str(SEMASNTICS_DIR.parent))
        print(f"\n{'─' * 60}")
        print(f"File: {rel_path}")
        print(f"Issues: {len(issues)}")
        for issue in issues[:5]:  # Show first 5
            print(f"  Line {issue['line']}: {issue['issue']}")
            print(f"    {issue['code'][:80]}")
        if len(issues) > 5:
            print(f"  ... and {len(issues) - 5} more")
    
    # Priority ranking
    print(f"\n{'=' * 80}")
    print("PRIORITY RANKING (by impact on physics calculations)")
    print("=" * 80)
    
    priority_files = [
        "EntropyMeasures.lean",  # Has expLUT, many sqrt calls
        "DynamicCanal.lean",     # Uses expNeg
        "HCMMR/Kernels/FAMMScarMemory.lean",  # Uses expNeg
        "CrossModalCompression.lean",  # Uses expNeg
        "ImplicitShellLattice.lean",  # Uses sin/cos
        "UnitQuaternion.lean",   # Taylor approximations
        "Toybox/ObserverAngle.lean",  # Cosine approximation
    ]
    
    for i, fname in enumerate(priority_files, 1):
        matches = [f for f in by_file.keys() if fname in f]
        if matches:
            print(f"\n{i}. {fname} ({len(by_file[matches[0]])} issues)")

if __name__ == "__main__":
    main()
