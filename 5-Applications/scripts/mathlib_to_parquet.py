#!/usr/bin/env python3
"""
Mathlib4-to-Parquet Global Ingester
Transforms the entire Mathlib4 library into a columnar dataset for large-scale
Lean 4 training (LeanGPT / SNN).

License: Apache 2.0 (Lean Community)
"""

import os
import hashlib
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime

from shim.utils.datetime_utils import utc_now

# ═══════════════════════════════════════════════════════════════════════════
# §0  Configuration
# ═══════════════════════════════════════════════════════════════════════════

RESEARCH_STACK_ROOT = Path("/home/allaun/Research Stack")
MATHLIB_SRC_ROOT = RESEARCH_STACK_ROOT / "0-Core-Formalism/lean/Semantics/.lake/packages/mathlib/Mathlib"
OUTPUT_DIR = RESEARCH_STACK_ROOT / "shared-data/data/datasets"
OUTPUT_FILE = OUTPUT_DIR / "mathlib4_complete.parquet"

# ═══════════════════════════════════════════════════════════════════════════
# §1  Extraction Logic
# ═══════════════════════════════════════════════════════════════════════════

def get_mathlib_domain(file_path: Path) -> str:
    """Extracts the top-level math domain (e.g., 'Analysis')."""
    try:
        relative = file_path.relative_to(MATHLIB_SRC_ROOT)
        return relative.parts[0] if len(relative.parts) > 1 else "Core"
    except:
        return "Unknown"

def ingest_mathlib():
    """Gathers Mathlib files with progress tracking."""
    rows = []
    
    if not MATHLIB_SRC_ROOT.exists():
        print(f"[ERROR] Mathlib root not found: {MATHLIB_SRC_ROOT}")
        return []

    print(f"[INFO] Scanning Mathlib corpus at {MATHLIB_SRC_ROOT}...")
    lean_files = list(MATHLIB_SRC_ROOT.rglob("*.lean"))
    total_files = len(lean_files)
    print(f"[INFO] Found {total_files} Lean files.")

    for i, lean_file in enumerate(lean_files):
        try:
            with open(lean_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Module name (relative path without .lean)
            module_name = str(lean_file.relative_to(MATHLIB_SRC_ROOT)).replace("/", ".").replace(".lean", "")
            domain = get_mathlib_domain(lean_file)
            
            rows.append({
                "module_name": module_name,
                "domain": domain,
                "content": content,
                "token_count": len(content.split()),
                "hash": hashlib.sha256(content.encode()).hexdigest(),
                "extracted_at": utc_now()
            })
            
            if (i + 1) % 500 == 0:
                print(f"[PROGRESS] Ingested {i+1}/{total_files} files...")
                
        except Exception as e:
            print(f"[WARN] Failed to process {lean_file}: {e}")
            
    return rows

# ═══════════════════════════════════════════════════════════════════════════
# §2  Parquet Serialization
# ═══════════════════════════════════════════════════════════════════════════

def write_parquet(rows):
    """Writes to Parquet with Schema enforcement."""
    if not rows:
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    fields = [
        pa.field('module_name', pa.string()),
        pa.field('domain', pa.string()),
        pa.field('content', pa.string()),
        pa.field('token_count', pa.int32()),
        pa.field('hash', pa.string()),
        pa.field('extracted_at', pa.string())
    ]
    schema = pa.schema(fields)

    # Building table
    table = pa.Table.from_pylist(rows, schema=schema)

    # Writing with compression for such a large file
    pq.write_table(table, OUTPUT_FILE, compression='snappy')
    print(f"\n[SUCCESS] Global Mathlib4 Dataset created: {OUTPUT_FILE}")
    print(f"[INFO] Record count: {len(rows)}")

if __name__ == "__main__":
    data = ingest_mathlib()
    write_parquet(data)
