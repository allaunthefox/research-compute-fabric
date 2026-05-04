#!/usr/bin/env python3
import pyarrow.parquet as pq
import pandas as pd

t = pq.read_table("3-Mathematical-Models/equations_parquet_tagged/equations_math_raw.parquet")
print("Columns:", t.column_names)
print("Rows:", t.num_rows)
print()
for col in t.column_names:
    print(f"  {col}: {t.column(col).null_count} nulls")
print()

df = t.to_pandas()
for i in range(5):
    raw = str(df.iloc[i]["equation"])[:100]
    refined = str(df.iloc[i]["refined_equation"])
    print(f"Row {i}:")
    print(f"  id:      {df.iloc[i]['equation_id']}")
    print(f"  raw:     {raw}...")
    print(f"  refined: {refined}")
    print(f"  source:  {df.iloc[i]['source']}")
    print()
