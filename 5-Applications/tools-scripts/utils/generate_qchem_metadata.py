# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================

# [WARDEN BOUNDARY ENFORCEMENT INJECTED]
import sys
import os
try:
    from io_harness_compat import spawn_isolated_process, fetch_network_resource
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from io_harness_compat import spawn_isolated_process, fetch_network_resource

import json
import hashlib
from pathlib import Path
# import subprocess (REMOVED BY WARDEN)

BASE_DIR = Path(__file__).parent.parent.resolve()
DATA_FILE = BASE_DIR / "hqw_atomic_combinations.json"
MANIFEST_BIN = BASE_DIR / "scripts" / "file_manifest_builder.py"
MANIFEST_OUT = BASE_DIR / "hqw_atomic_combinations.manifest.json"
METADATA_OUT = BASE_DIR / "hqw_materials_metadata.jsonl"
CHUNK_STORE = BASE_DIR / "hqw_chunks"

def sha256_text(text):
    return hashlib.sha256(text.encode()).hexdigest()

def generate_metadata():
    print(f"[*] Reading {DATA_FILE}...")
    with open(DATA_FILE, 'r') as f:
        combinations = json.load(f)
    
    print(f"[*] Generating per-combination metadata...")
    with open(METADATA_OUT, 'w') as f:
        for comb in combinations:
            # Hash the formula + register_bits as a unique key for the combination
            # This follows the 'valence as register' metadata requirement
            data_str = json.dumps(comb, sort_keys=True)
            digest = sha256_text(data_str)
            comb['sha256'] = digest
            f.write(json.dumps(comb) + "\n")
    
    print(f"[+] Metadata saved to {METADATA_OUT}")

def generate_manifest():
    print(f"[*] Building file-level manifest using file_manifest_builder.py...")
    cmd = [
        "python3", str(MANIFEST_BIN), "build",
        "--input", str(DATA_FILE),
        "--manifest-out", str(MANIFEST_OUT),
        "--chunk-store", str(CHUNK_STORE)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"[+] Manifest saved to {MANIFEST_OUT}")
        print(f"[*] Chunk store created in {CHUNK_STORE}")
    else:
        print(f"[!] Manifest build failed: {result.stderr}")

if __name__ == "__main__":
    if not DATA_FILE.exists():
        print(f"[!] Error: {DATA_FILE} not found. Run the HQW simulation first.")
    else:
        generate_metadata()
        generate_manifest()
