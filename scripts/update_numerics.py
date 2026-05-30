#!/usr/bin/env python3
"""
update_numerics.py — Systematically update modules to use Q16_16Numerics

This script:
1. Finds all .lean files using Q16_16.sqrt/sin/cos
2. Adds import Semantics.Q16_16Numerics if missing
3. Updates function calls to use rigorous versions

Usage:
    python3 update_numerics.py [--dry-run]
"""

import os
import re
from pathlib import Path

SEMASNTICS_DIR = Path("/home/allaun/Research Stack/0-Core-Formalism/lean/Semantics/Semantics")

# Functions to update
FUNCTION_UPDATES = {
    'Q16_16.sqrt': 'Semantics.Q16_16Numerics.sqrt',
    'Q16_16.sin': 'Semantics.Q16_16Numerics.sin',
    'Q16_16.cos': 'Semantics.Q16_16Numerics.cos',
    'Q16_16.expNeg': 'Semantics.Q16_16Numerics.expNeg',
    'Q16_16.exp': 'Semantics.Q16_16Numerics.exp',
    'Q16_16.ln': 'Semantics.Q16_16Numerics.ln',
    'Q16_16.log2': 'Semantics.Q16_16Numerics.log2',
    'Q16_16.tan': 'Semantics.Q16_16Numerics.tan',
    'Q16_16.asin': 'Semantics.Q16_16Numerics.asin',
    'Q16_16.acos': 'Semantics.Q16_16Numerics.acos',
    'Q16_16.atan': 'Semantics.Q16_16Numerics.atan',
    'Q16_16.atan2': 'Semantics.Q16_16Numerics.atan2',
    'Q16_16.sinh': 'Semantics.Q16_16Numerics.sinh',
    'Q16_16.cosh': 'Semantics.Q16_16Numerics.cosh',
    'Q16_16.tanh': 'Semantics.Q16_16Numerics.tanh',
}

# Files to skip (already updated or have issues)
SKIP_FILES = [
    'Q16_16Numerics.lean',
    'FixedPoint.lean',
    'EntropyMeasures.lean',  # Has pre-existing errors with pow
]

def needs_update(filepath):
    """Check if a file needs updating."""
    if any(skip in str(filepath) for skip in SKIP_FILES):
        return False
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check if already has import
    if 'import Semantics.Q16_16Numerics' in content:
        return False
    
    # Check if uses any functions we're updating
    for func in FUNCTION_UPDATES.keys():
        if func in content:
            return True
    
    return False

def add_import(content):
    """Add Q16_16Numerics import after last existing import."""
    lines = content.split('\n')
    last_import_idx = -1
    
    for i, line in enumerate(lines):
        if line.startswith('import '):
            last_import_idx = i
    
    if last_import_idx >= 0:
        lines.insert(last_import_idx + 1, 'import Semantics.Q16_16Numerics')
    
    return '\n'.join(lines)

def update_functions(content):
    """Update function calls to use rigorous versions."""
    for old_func, new_func in FUNCTION_UPDATES.items():
        # Only update if not already qualified
        content = content.replace(old_func, new_func)
    
    return content

def process_file(filepath, dry_run=False):
    """Process a single file."""
    with open(filepath, 'r') as f:
        original = f.read()
    
    updated = original
    updated = add_import(updated)
    updated = update_functions(updated)
    
    if updated != original:
        changes = []
        if 'import Semantics.Q16_16Numerics' in updated and 'import Semantics.Q16_16Numerics' not in original:
            changes.append('added import')
        
        for old_func in FUNCTION_UPDATES.keys():
            if old_func in original and old_func not in updated:
                changes.append(f'updated {old_func}')
        
        if not dry_run:
            with open(filepath, 'w') as f:
                f.write(updated)
        
        return True, changes
    return False, []

def main():
    dry_run = '--dry-run' in sys.argv
    
    print("=" * 70)
    print("Q16_16Numerics MIGRATION REPORT")
    print("=" * 70)
    
    files_to_update = []
    for filepath in SEMASNTICS_DIR.rglob("*.lean"):
        if needs_update(filepath):
            files_to_update.append(filepath)
    
    print(f"\nFiles needing update: {len(files_to_update)}")
    
    updated_count = 0
    for filepath in sorted(files_to_update):
        rel_path = filepath.relative_to(SEMASNTICS_DIR.parent)
        updated, changes = process_file(filepath, dry_run)
        if updated:
            updated_count += 1
            print(f"\n  {'[DRY RUN] ' if dry_run else ''}Updated: {rel_path}")
            for change in changes:
                print(f"    - {change}")
    
    print(f"\n{'=' * 70}")
    print(f"Total files updated: {updated_count}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print("=" * 70)

if __name__ == "__main__":
    import sys
    main()
