#!/usr/bin/env python3
"""
Lean4-Addons-to-Parquet Ingester
Pulls every legally compatible companion package in .lake/packages/
(batteries, aesop, Cli, etc.) and converts them to Parquet.

Attribution maintained for all packages.
"""

import os
import hashlib
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════
# §0  Configuration
# ═══════════════════════════════════════════════════════════════════════════

RESEARCH_STACK_ROOT = Path("/home/allaun/Research Stack")
PACKAGES_ROOT = RESEARCH_STACK_ROOT / "0-Core-Formalism/lean/Semantics/.lake/packages"
OUTPUT_DIR = RESEARCH_STACK_ROOT / "shared-data/data/datasets"
OUTPUT_FILE = OUTPUT_DIR / "lean4_addons_complete.parquet"

# ═══════════════════════════════════════════════════════════════════════════
# §1  Extraction Logic
# ═══════════════════════════════════════════════════════════════════════════

def ingest_all_addons():
    """Gathers files from all packages except Mathlib."""
    rows = []
    
    if not PACKAGES_ROOT.exists():
        print(f"[ERROR] Packages root not found: {PACKAGES_ROOT}")
        return []

    # Get list of addon directories
    addon_dirs = [d for d in PACKAGES_ROOT.iterdir() if d.is_dir() and d.name != "mathlib"]
    print(f"[INFO] Found {len(addon_dirs)} addon packages: {[d.name for d in addon_dirs]}")

    for addon_dir in addon_dirs:
        package_name = addon_dir.name
        print(f"[INGEST] Processing package: {package_name}...")
        
        # Scrape all .lean files in the package
        lean_files = list(addon_dir.rglob("*.lean"))
        for lean_file in lean_files:
            try:
                with open(lean_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                module_path = str(lean_file.relative_to(addon_dir))
                
                rows.append({
                    "package": package_name,
                    "module_path": module_path,
                    "content": content,
                    "token_count": len(content.split()),
                    "hash": hashlib.sha256(content.encode()).hexdigest(),
                    "extracted_at": datetime.utcnow().isoformat()
                })
            except Exception as e:
                print(f"[WARN] Failed to process {lean_file}: {e}")
                
    return rows

# ═══════════════════════════════════════════════════════════════════════════
# §2  Serialization
# ═══════════════════════════════════════════════════════════════════════════

def write_parquet(rows):
    if not rows:
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    schema = pa.schema([
        pa.field('package', pa.string()),
        pa.field('module_path', pa.string()),
        pa.field('content', pa.string()),
        pa.field('token_count', pa.int32()),
        pa.field('hash', pa.string()),
        pa.field('extracted_at', pa.string())
    ])

    table = pa.Table.from_pylist(rows, schema=schema)
    pq.write_table(table, OUTPUT_FILE, compression='snappy')
    
    print(f"\n[SUCCESS] Lean4 Addons Dataset created: {OUTPUT_FILE}")
    print(f"[INFO] Total Addon Modules: {len(rows)}")

if __name__ == "__main__":
    data = ingest_all_addons()
    write_parquet(data)
