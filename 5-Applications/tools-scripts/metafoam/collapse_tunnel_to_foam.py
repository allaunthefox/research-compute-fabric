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

#!/usr/bin/env python3
import json
import os
# import subprocess (REMOVED BY WARDEN)
import sys
import hashlib
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "out" / "omnitoken_bridge" / "tunnel_cache"
EXTERNAL_JSON = ROOT / "graph_os_metadata_external.json"

def get_file_hash(filepath):
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def collapse_tunnel():
    print("[*] Collapsing tunnel cache into Graph OS metadata foam...")
    
    if not CACHE_DIR.exists():
        print("[!] tunnel cache directory not found.")
        return

    if not EXTERNAL_JSON.exists():
        existing = []
    else:
        with open(EXTERNAL_JSON, 'r') as f:
            content = f.read().strip()
            existing = json.loads(content) if content else []
            
    existing_ids = {e.get('id') for e in existing}
    added = 0
    
    for f in CACHE_DIR.iterdir():
        if not f.is_file():
            continue
            
        file_id = f"tunnel_{f.name}"
        if file_id in existing_ids:
            continue
            
        file_hash = get_file_hash(f)
        
        # For large files like .tar.gz, we store them as base64 or just metadata
        # Given the "collapse" requirement, we'll try to read content if reasonable
        # but for safety with .tar.gz (591MB), we'll cap the content ingestion or use a placeholder
        content_type = "text"
        raw_content = ""
        
        if f.suffix in ['.json', '.py', '.md', '.txt', '.html', '.csv']:
            try:
                with open(f, 'r', encoding='utf-8') as src:
                    raw_content = src.read()
            except Exception:
                content_type = "binary"
                raw_content = "[Binary data preserved in tunnel cache]"
        else:
            content_type = "binary"
            raw_content = f"[Binary/Large file: {f.suffix} - hash: {file_hash}]"

        entry = {
            "id": file_id,
            "tier": "Tier 3 (FOAM)",
            "module": "tunnel_INGRESS",
            "tags": ["tunnel", "transferred", f.suffix[1:] if f.suffix else "none"],
            "metadata": {
                "filename": f.name,
                "hash": file_hash,
                "content_type": content_type,
                "raw_content": raw_content,
                "purpose": "Transferred component collapsed into foam",
                "axis": "STRUC/MANI"
            }
        }
        existing.append(entry)
        added += 1
        
    with open(EXTERNAL_JSON, 'w') as f:
        json.dump(existing, f, indent=2)
        
    print(f"[+] Absorbed {added} tunnel files into metadata foam.")
    
    # Rebuild DB and DAG
    print("[*] Rebuilding Graph OS metadata database...")
    subprocess.run([sys.executable, f"{ROOT}/scripts/build_graph_os_metadata_db.py"],
                   check=True)
    print("[*] Finalizing HyperDAG update...")
    subprocess.run([sys.executable, f"{ROOT}/scripts/absorb_and_align_metadata.py"],
                   check=True)

if __name__ == "__main__":
    collapse_tunnel()
