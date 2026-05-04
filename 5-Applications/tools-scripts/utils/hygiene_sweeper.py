#!/usr/bin/env python3
import os
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
EXCLUDE_DIRS = ['vendor', 'CATEGORY', 'tests', 'memory', 'out', '.git', '.secrets', 'archive', '.venv-eng']

HEADER = """# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""

def should_process(filepath: Path) -> bool:
    for ex in EXCLUDE_DIRS:
        if ex in filepath.parts:
            return False
    return filepath.suffix == '.py'

def inject_company_ip(filepath: Path):
    content = filepath.read_text(encoding='utf-8')
    # Prevent double-stamping
    if "COPYRIGHT NO ONE EVERYWHERE LLC" in content:
        return 0

    # Handle python shebangs
    if content.startswith("#!"):
        lines = content.split('\n')
        modified = lines[0] + '\n' + HEADER + '\n'.join(lines[1:])
    else:
        modified = HEADER + content
        
    filepath.write_text(modified, encoding='utf-8')
    return 1

def main():
    count = 0
    for root, _, files in os.walk(ROOT_DIR):
        for f in files:
            path = Path(root) / f
            if should_process(path):
                count += inject_company_ip(path)
                
    print(f"[HYGIENE AUDIT] Corporate Identity Boundary Attached to {count} IP Endpoints.")

if __name__ == "__main__":
    main()
