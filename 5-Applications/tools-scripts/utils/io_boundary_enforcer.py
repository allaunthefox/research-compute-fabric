#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import os
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

# Exclude unnecessary directories
EXCLUDE_DIRS = ['vendor', 'CATEGORY', 'tests', 'memory', 'out', '.git', '.secrets', 'archive']

def should_process(filepath: Path) -> bool:
    for ex in EXCLUDE_DIRS:
        if ex in filepath.parts:
            return False
    return filepath.suffix == '.py'

def inject_harness(filepath: Path):
    content = filepath.read_text(encoding='utf-8')
    if 'io_harness_compat' in content:
        return # Already processed

    # Find the depth of this file
    depth = len(filepath.relative_to(ROOT_DIR).parts) - 1
    dots = '..' + ('/..' * (depth - 1)) if depth > 0 else '.'
    
    inject_imports = f"""
# [WARDEN BOUNDARY ENFORCEMENT INJECTED]
import sys
import os
try:
    from io_harness_compat import spawn_isolated_process, fetch_network_resource
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '{dots}')))
    from io_harness_compat import spawn_isolated_process, fetch_network_resource
"""
    
    # Very unsafe substitutions, but prove the bounds
    # For now, we only FLAG the violations and inject the preamble, which sets up manual isolation
    # or overrides via module patching.
    
    content = re.sub(r'^(import subprocess)$', r'# \1 (REMOVED BY WARDEN)', content, flags=re.MULTILINE)
    content = re.sub(r'^(import requests)$', r'# \1 (REMOVED BY WARDEN)', content, flags=re.MULTILINE)
    
    modified = inject_imports + "\n" + content
    filepath.write_text(modified, encoding='utf-8')
    print(f"[BOUNDED] {filepath.relative_to(ROOT_DIR)}")

def main():
    count = 0
    for root, _, files in os.walk(ROOT_DIR):
        for f in files:
            path = Path(root) / f
            if should_process(path):
                content = path.read_text(encoding='utf-8', errors='ignore')
                if re.search(r'^(import|from)\s+(requests|urllib|subprocess|aiohttp)', content, flags=re.MULTILINE):
                    inject_harness(path)
                    count += 1
    print(f"Total files bounded: {count}")

if __name__ == "__main__":
    main()
