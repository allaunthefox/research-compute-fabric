#!/usr/bin/env python3
"""
Strip all human-imposed categorization from the unified dataset.
Outputs a "math-raw" parquet containing only the equation text and a
128-bit UUID, with every tag, feature flag, domain, pattern, and provenance removed.

Input:  equations_unified_9pattern.parquet
Output: equations_math_raw.parquet
"""

import uuid
import pyarrow.parquet as pq
import pyarrow as pa
from datetime import datetime

BASE = "/home/allaun/Documents/Research Stack/3-Mathematical-Models/equations_parquet_tagged"
INPUT = f"{BASE}/equations_unified_9pattern.parquet"
OUTPUT = f"{BASE}/equations_math_raw.parquet"
SUMMARY = f"{BASE}/../math_raw_summary.json"

print("Loading unified dataset...")
table = pq.read_table(INPUT)
print(f"  Loaded {table.num_rows:,} rows with {len(table.column_names)} columns")

# ── Generate 128-bit UUIDs ──────────────────────────────────────────────────
n_rows = table.num_rows
uuids = [str(uuid.uuid4()).replace("-", "") for _ in range(n_rows)]
uuid_col = pa.array(uuids, pa.string())

# ── Columns to KEEP (math-raw only) ─────────────────────────────────────────
KEEP = ["equation", "refined_equation"]

# ── Verify all KEEP columns exist ─────────────────────────────────────────────
missing = [c for c in KEEP if c not in table.column_names]
if missing:
    print(f"  [!] Missing columns: {missing}")
    KEEP = [c for c in KEEP if c in table.column_names]

# ── Build stripped table with UUID ────────────────────────────────────────────
arrays = {"uuid": uuid_col}
for col in KEEP:
    arrays[col] = table.column(col)

raw_table = pa.table(arrays)
print(f"  Stripped to {len(raw_table.column_names)} columns: {raw_table.column_names}")

# ── Write math-raw parquet ──────────────────────────────────────────────────
print(f"\nWriting math-raw parquet to {OUTPUT}...")
pq.write_table(raw_table, OUTPUT, compression="zstd")
print(f"  Done. Size: {OUTPUT}")

# ── Summary ─────────────────────────────────────────────────────────────────
import json

n_eq = raw_table.num_rows
n_refined = sum(1 for v in raw_table.column("refined_equation") if v is not None and str(v) != "")

summary = {
    "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
    "total_equations": n_eq,
    "has_refined_text": n_refined,
    "columns": raw_table.column_names,
    "dropped_columns": [c for c in table.column_names if c not in ("uuid",) + tuple(KEEP)],
    "input_file": INPUT,
    "output_file": OUTPUT,
}

with open(SUMMARY, "w") as f:
    json.dump(summary, f, indent=2)
print(f"\nSummary written to {SUMMARY}")

print(f"\n{'='*50}")
print(f"  MATH-RAW DATASET COMPLETE")
print(f"  {n_eq:,} equations, {len(raw_table.column_names)} columns")
print(f"{'='*50}")
