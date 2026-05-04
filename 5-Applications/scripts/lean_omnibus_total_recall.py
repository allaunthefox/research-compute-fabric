#!/usr/bin/env python3
"""
Lean4 Omnibus "Total Recall" Ingester (Waveprobe Optimized)
Parallelized ingestion of EVERYTHING: Core Source, Trash Ghosts, and History.

Uses concurrent.futures for Waveprobe-style retrieval speed.
"""

import os
import hashlib
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ═══════════════════════════════════════════════════════════════════════════
# §0  Configuration
# ═══════════════════════════════════════════════════════════════════════════

HOME = Path("/home/allaun")
TOOLCHAIN_ROOT = HOME / ".elan/toolchains/leanprover--lean4---v4.30.0-rc2/src/lean"
TRASH_ROOT = HOME / ".local/share/Trash/files"
HISTORY_ROOT = HOME / ".4-Infrastructure/config/Windsurf - Next/User/History"
RESEARCH_STACK = HOME / "Research Stack"
OUTPUT_FILE = RESEARCH_STACK / "shared-data/data/datasets/lean4_omnibus_total_recall.parquet"

# ═══════════════════════════════════════════════════════════════════════════
# §1  Parallel Probe Logic
# ═══════════════════════════════════════════════════════════════════════════

def get_file_provenance(path: Path) -> str:
    if str(TOOLCHAIN_ROOT) in str(path): return "core_toolchain"
    if str(TRASH_ROOT) in str(path): return "trash_ghost"
    if str(HISTORY_ROOT) in str(path): return "editor_history"
    if str(RESEARCH_STACK) in str(path): return "active_research"
    return "orphaned_logic"

def process_single_file(file_path: Path):
    """Worker function for the Waveprobe thread pool."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        if not content.strip(): return None
        
        return {
            "path": str(file_path),
            "provenance": get_file_provenance(file_path),
            "content": content,
            "token_count": len(content.split()),
            "hash": hashlib.sha256(content.encode()).hexdigest(),
            "extracted_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        # print(f"[DEBUG] Skipping {file_path}: {e}")
        return None

def trigger_waveprobe():
    """Triggers parallel scans of the manifold substrate."""
    all_files = []
    
    print("[INFO] Triggering Waveprobe scans across all domains...")
    
    # 1. Scan core toolchain
    if TOOLCHAIN_ROOT.exists():
        all_files.extend(list(TOOLCHAIN_ROOT.rglob("*.lean")))
    
    # 2. Scan Trash
    if TRASH_ROOT.exists():
        all_files.extend(list(TRASH_ROOT.rglob("*.lean")))
        
    # 3. Scan Research Stack (Full backup)
    if RESEARCH_STACK.exists():
        all_files.extend(list(RESEARCH_STACK.rglob("*.lean")))
        
    # 4. Scan History (Esoteric capture)
    # Windsurf history folders contain files without .lean extensions but often are Lean code.
    # We include them if they are likely Lean or in the right sub-history.
    if HISTORY_ROOT.exists():
        # Capturing files in history that likely belong to Lean projects
        all_files.extend(list(HISTORY_ROOT.rglob("*.lean")))

    total_probes = len(all_files)
    print(f"[INFO] Waveprobe initialized. Targeted nodes: {total_probes}")

    results = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(process_single_file, f): f for f in all_files}
        
        count = 0
        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)
            count += 1
            if count % 1000 == 0:
                print(f"[WAVEPROBE] Probe status: {count}/{total_probes} successful hits.")

    return results

# ═══════════════════════════════════════════════════════════════════════════
# §2  Serialization
# ═══════════════════════════════════════════════════════════════════════════

def finalize_omnibus(rows):
    if not rows:
        print("[ERROR] No logic captured in the probe.")
        return

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    schema = pa.schema([
        pa.field('path', pa.string()),
        pa.field('provenance', pa.string()),
        pa.field('content', pa.string()),
        pa.field('token_count', pa.int32()),
        pa.field('hash', pa.string()),
        pa.field('extracted_at', pa.string())
    ])

    table = pa.Table.from_pylist(rows, schema=schema)
    pq.write_table(table, OUTPUT_FILE, compression='zstd') # ZSTD for ultimate compression
    
    print(f"\n[SUCCESS] Omnibus Total Recall completed: {OUTPUT_FILE}")
    print(f"[INFO] Manifold Logic Points: {len(rows)}")

if __name__ == "__main__":
    logic_rows = trigger_waveprobe()
    finalize_omnibus(logic_rows)
