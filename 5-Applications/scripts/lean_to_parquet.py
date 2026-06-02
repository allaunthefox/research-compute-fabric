#!/usr/bin/env python3
"""
Lean-to-Parquet Dataset Generator
Transforms the Sovereign Informatic Manifold (Lean 4) into a columnar format
suitable for Spiking Neural Network (SNN) training.

Includes Apache 2.0 attribution and ENE-schema'd metadata.
"""

import os
import json
import hashlib
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime

from shim.utils.datetime_utils import utc_now

# ═══════════════════════════════════════════════════════════════════════════
# §0  Configuration & Metadata
# ═══════════════════════════════════════════════════════════════════════════

RESEARCH_STACK_ROOT = Path("/home/allaun/Research Stack")
LEAN_SRC_ROOT = RESEARCH_STACK_ROOT / "0-Core-Formalism/lean/Semantics/Semantics"
OUTPUT_DIR = RESEARCH_STACK_ROOT / "shared-data/data/datasets"
OUTPUT_FILE = OUTPUT_DIR / "sovereign_manifold_v1.parquet"

ATTRIBUTION = {
    "source": "Sovereign Informatic Manifold",
    "license": "Apache 2.0",
    "owner": "Lost Frog Research",
    "timestamp": utc_now()
}

# ═══════════════════════════════════════════════════════════════════════════
# §1  Extraction Logic
# ═══════════════════════════════════════════════════════════════════════════

def extract_lean_metadata(content: str) -> dict:
    """Extracts docstrings and basic stats from Lean source."""
    docstring = ""
    if "/-" in content:
        start = content.find("/-")
        end = content.find("-/", start)
        if end != -1:
            docstring = content[start+2:end].strip()
    
    return {
        "docstring": docstring,
        "logic_density": content.count("def ") + content.count("theorem ") + content.count("lemma "),
        "token_count": len(content.split())
    }

def gather_manifold_data():
    """Traverses the Semantics directory and gathers data rows."""
    rows = []
    
    if not LEAN_SRC_ROOT.exists():
        print(f"[ERROR] Source root does not exist: {LEAN_SRC_ROOT}")
        return []

    for lean_file in LEAN_SRC_ROOT.rglob("*.lean"):
        try:
            with open(lean_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            meta = extract_lean_metadata(content)
            module_path = str(lean_file.relative_to(LEAN_SRC_ROOT))
            
            rows.append({
                "module_path": module_path,
                "content": content,
                "docstring": meta["docstring"],
                "logic_density": meta["logic_density"],
                "token_count": meta["token_count"],
                "hash": hashlib.sha256(content.encode()).hexdigest(),
                "attribution": json.dumps(ATTRIBUTION)
            })
            print(f"[OK] Ingested: {module_path}")
            
        except Exception as e:
            print(f"[WARN] Failed to process {lean_file}: {e}")
            
    return rows

# ═══════════════════════════════════════════════════════════════════════════
# §2  Parquet Serialization
# ═══════════════════════════════════════════════════════════════════════════

def write_parquet(rows):
    """Writes the gathered data to a Parquet file."""
    if not rows:
        print("[ERROR] No data rows to write.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Define Schema
    fields = [
        pa.field('module_path', pa.string()),
        pa.field('content', pa.string()),
        pa.field('docstring', pa.string()),
        pa.field('logic_density', pa.int32()),
        pa.field('token_count', pa.int32()),
        pa.field('hash', pa.string()),
        pa.field('attribution', pa.string())
    ]
    schema = pa.schema(fields)

    # Convert rows to arrays
    data = {k: [r[k] for r in rows] for k in rows[0].keys()}
    table = pa.Table.from_pydict(data, schema=schema)

    # Write to file
    pq.write_table(table, OUTPUT_FILE)
    print(f"\n[SUCCESS] Parquet dataset created at: {OUTPUT_FILE}")
    print(f"[INFO] Total Manifold Modules: {len(rows)}")

if __name__ == "__main__":
    print("[INIT] Launching Lean-to-Parquet pipeline...")
    manifold_rows = gather_manifold_data()
    write_parquet(manifold_rows)
