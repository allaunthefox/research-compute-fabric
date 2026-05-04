#!/usr/bin/env python3
"""
Master Manifold Dataset Merger
Unifies the Sovereign research, Global Mathlib, and Addons into a single high-performance Parquet file.
"""

import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path

DATA_DIR = Path("/home/allaun/Documents/Research Stack/data/datasets")
OUTPUT_FILE = DATA_DIR / "master_sovereign_manifold.parquet"

def merge():
    files = [
        DATA_DIR / "mathlib4_complete.parquet",
        DATA_DIR / "lean4_addons_complete.parquet",
        DATA_DIR / "sovereign_manifold_v1.parquet"
    ]
    
    tables = []
    for f in files:
        if f.exists():
            print(f"[MERGE] Loading {f.name}...")
            tables.append(pq.read_table(f))
        else:
            print(f"[WARN] File {f.name} missing. Skipping.")

    if not tables:
        return

    # Master Schema: unified across all sources
    # Note: Omnibus includes everything, so we could just use that,
    # but the user might want this curated triple.
    
    print("[MERGE] Unifying columns...")
    # We'll project to a common set of columns: module_path, content, provenance
    projected = []
    for i, t in enumerate(tables):
        # Determine source
        src = ["mathlib", "addons", "sovereign"][i]
        
        # content column is common
        content = t.column("content")
        
        # Determine path column (might be module_name or module_path)
        path_col = "module_path" if "module_path" in t.column_names else "module_name"
        path = t.column(path_col)
        
        # Create new table with common schema
        new_t = pa.table([
            path,
            content,
            pa.array([src] * len(t), pa.string())
        ], names=["path", "content", "source"])
        projected.append(new_t)

    master_table = pa.concat_tables(projected)
    pq.write_table(master_table, OUTPUT_FILE, compression='zstd')
    print(f"\n[SUCCESS] Master Sovereign Manifold created: {OUTPUT_FILE}")
    print(f"[INFO] Total Modules: {len(master_table)}")

if __name__ == "__main__":
    merge()
