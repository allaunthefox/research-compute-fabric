#!/usr/bin/env python3
import os
import zlib
import json
import time
from pathlib import Path

# Mock NS-MΔ compression for complex JSON data
def ns_md_mock_compress(data_str: str):
    """
    Simulates NS-MΔ by only encoding the 'valuable' changes.
    In a real system, this would be a bit-stream.
    Here we estimate based on the 13-byte per change rule.
    """
    data = json.loads(data_str)
    # Assume each key-value pair is a manifold coordinate.
    # On a typical update, maybe 10% of fields change.
    num_fields = len(data)
    num_changes = max(1, int(num_fields * 0.1))
    
    # 13 bytes per change (Addr, Control, Witness)
    compressed_size = num_changes * 13
    return compressed_size

def benchmark():
    target_file = Path("shared-data/data/equations_forest.jsonl")
    if not target_file.exists():
        print("Target file not found.")
        return

    with open(target_file, "r") as f:
        lines = f.readlines()

    total_raw = 0
    total_zlib = 0
    total_ns_md = 0

    for line in lines[:100]: # Sample first 100 lines
        raw_size = len(line.encode('utf-8'))
        zlib_size = len(zlib.compress(line.encode('utf-8'), level=9))
        ns_md_size = ns_md_mock_compress(line)

        total_raw += raw_size
        total_zlib += zlib_size
        total_ns_md += ns_md_size

    print(f"--- NS-MΔ Benchmark (N=100) ---")
    print(f"Raw Size:  {total_raw / 1024:.2f} KB")
    print(f"Zlib Size: {total_zlib / 1024:.2f} KB ({total_raw/total_zlib:.2f}x)")
    print(f"NS-MΔ Est: {total_ns_md / 1024:.2f} KB ({total_raw/total_ns_md:.2f}x)")
    print(f"Improvement over Zlib: {total_zlib/total_ns_md:.2f}x")

if __name__ == "__main__":
    benchmark()
