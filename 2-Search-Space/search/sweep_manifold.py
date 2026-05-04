import numpy as np
import json
import os
import math
from pathlib import Path

# --- Configuration ---
LUT_PATH = "/home/allaun/Documents/Research Stack/data/swarm/adaptation_surface.bin"
INGEST_DIR = Path("/home/allaun/Documents/Research Stack/data/ingestion")
HARDENED_DIR = INGEST_DIR / "hardened"
LUT_DT = np.dtype([('lawful','u1'), ('dk','u1'), ('df','u1'), ('er','u1'), ('cost','u4')])

# Load LUT
try:
    ADAPTATION_SURFACE = np.fromfile(LUT_PATH, dtype=LUT_DT)
except Exception as e:
    print(f"Error loading LUT: {e}")
    exit(1)

def map_to_genome(item):
    """
    Maps IA metadata to 18-bit address (6 dims * 3 bits).
    Normalized to 0-7 range per dimension.
    """
    # 1. uBin (Mutation/Entropy): Inverse of metadata completeness
    # Max possible fields ~20. Map (20-count) to 0-7.
    metadata_count = len(item.keys())
    uBin = max(0, min(7, (20 - metadata_count) // 2))

    # 2. neBin (Population): Log of downloads
    downloads = int(item.get('downloads', 0))
    # Log2 mapping: 0-7 range for 1 to 100k downloads
    neBin = max(0, min(7, int(math.log2(downloads + 1) / 2)))

    # 3. sigBin (Fitness): Relevancy or index
    # We'll use the 'week' (trending) or just default to 4 for research seeds
    sigBin = 4 

    # 4. cBin (Connectance): Related identifiers count
    # IA often has 'identifier-access' or similar. 
    # Use length of 'identifier' as dummy connectance.
    cBin = max(0, min(7, len(item.get('identifier', '')) // 5))

    # 5. mBin (Modularity): Format count
    # Placeholder for multi-format records
    mBin = 3 

    # 6. xBin (Reserved/Noise)
    xBin = 0

    # Pack 18-bit address
    addr = (uBin & 0x7) | ((neBin & 0x7) << 3) | ((sigBin & 0x7) << 6) | \
           ((cBin & 0x7) << 9) | ((mBin & 0x7) << 12) | ((xBin & 0x7) << 15)
    return addr

def sweep():
    print(f"--- Initiating Manifold Hardening Sweep ---")
    total_found = 0
    total_kept = 0
    total_pruned = 0

    for fpath in INGEST_DIR.glob("ia_*.json"):
        print(f"Processing: {fpath.name}")
        with open(fpath, 'r') as f:
            data = json.load(f)
        
        # IA response structure: { 'response': { 'docs': [...] } }
        docs = data.get('response', {}).get('docs', [])
        hardened_docs = []
        
        for doc in docs:
            total_found += 1
            addr = map_to_genome(doc)
            state = ADAPTATION_SURFACE[addr]
            
            if state['lawful']:
                hardened_docs.append(doc)
                total_kept += 1
            else:
                total_pruned += 1
        
        # Save hardened version
        output_file = HARDENED_DIR / fpath.name
        with open(output_file, 'w') as f:
            json.dump({'docs': hardened_docs}, f, indent=2)
            
    print(f"\n--- Sweep Results ---")
    print(f"Total Records Analyzed: {total_found}")
    print(f"Total Lawful Records:   {total_kept}")
    print(f"Total Records Pruned:   {total_pruned}")
    if total_found > 0:
        print(f"Manifold Cleanliness:   {total_kept/total_found*100:.2f}%")

if __name__ == "__main__":
    sweep()
