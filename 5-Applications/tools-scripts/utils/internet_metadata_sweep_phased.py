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
import hashlib
import zlib
import base64
# import subprocess (REMOVED BY WARDEN)
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
DAG_PATH = ROOT / "Research Documents" / "resonant_stack_v5.dag.json"
EXTERNAL_JSON = ROOT / "graph_os_metadata_external.json"
METADATA_REPORT = ROOT / "metadata_report.json"
FOAM_NODE_ID = "4161b3d4ac0e39900753c492e436b98f06a80dc437f59cc30a902c5e59cf846e"

def get_utc_now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def encode_capsule(data: dict) -> str:
    raw = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    compressed = zlib.compress(raw, level=9)
    return base64.urlsafe_b64encode(compressed).decode("ascii").rstrip("=")

def decode_capsule(capsule: str) -> dict:
    missing_padding = (-len(capsule)) % 4
    padding = '=' * missing_padding
    decoded_bytes = base64.urlsafe_b64decode(capsule + padding)
    decompressed_bytes = zlib.decompress(decoded_bytes)
    return json.loads(decompressed_bytes.decode('utf-8'))

def run_sweep(sources_path, limit=10):
    print(f"[*] Running metadata sweep on {sources_path} (limit={limit})...")
    token = os.environ.get("OMNITOKEN")
    if not token:
        print("[!] OMNITOKEN environment variable not set. Skipping live sweep.")
        return False
    
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "omnitoken_soliton_ping.py"),
        "--sources", str(sources_path),
        "--limit", str(limit)
    ]
    env = os.environ.copy()
    result = subprocess.run(cmd, env=env)
    return result.returncode == 0

def update_dag_and_foam():
    print("[*] Updating DAG and spraying the foam...")
    if not DAG_PATH.exists():
        print(f"[!] DAG file not found: {DAG_PATH}")
        return

    dag = json.loads(DAG_PATH.read_text(encoding="utf-8"))
    
    # 1. Extract new patterns from EXTERNAL_JSON
    if not EXTERNAL_JSON.exists():
        print("[!] No external metadata found to append.")
        return

    external_data = json.loads(EXTERNAL_JSON.read_text(encoding="utf-8"))
    new_headers = []
    
    for entry in external_data:
        node_id = entry.get("id") or entry.get("@id")
        if not node_id: continue
        
        if node_id in dag["dag_nodes"]:
            print(f"[-] Node {node_id} already in DAG. Skipping.")
            continue
            
        print(f"[+] Appending node {node_id} to HyperDAG.")
        
        # Initialize Kernel
        from TSM_COMPILER import TSM_Kernel
        kernel = TSM_Kernel(substrate="silicon")
        
        # Format for DAG
        metadata_payload = entry.get("metadata", entry)
        manifold_id = kernel.absorb(node_id, metadata_payload, external=True)
        capsule = kernel.manifold[node_id]["blob"]
        
        node_entry = {
            "tier": 2, # PLASMA default for external
            "tier_name": entry.get("tier", "PLASMA"),
            "equation_version": dag.get("equation_version", "Σ-EQ-ALL-01"),
            "ruleset_version": dag.get("ruleset_version", "Σ-RULESET-03"),
            "signature": dag.get("signature", "ML-DSA-BULK"),
            "tags": entry.get("tags", ["external_discovery"]),
            "compute_weight": 1.0,
            "meta_capsule": capsule,
            "meta_capsule_hash": hashlib.sha256(capsule.encode("utf-8")).hexdigest(),
            "parent": FOAM_NODE_ID,
            "timestamp": datetime.now().timestamp()
        }
        dag["dag_nodes"][node_id] = node_entry
        
        # Track for foam spray
        module = metadata_payload.get("module") or metadata_payload.get("@type") or "UNKNOWN"
        new_headers.append(f"discovery_{module}_{node_id[:8]}")

    if not new_headers:
        print("[*] No new nodes to append.")
        return

    # 2. Spray the Foam (Update PANSUBSTRATE_ALL_COMPUTES)
    if FOAM_NODE_ID in dag["dag_nodes"]:
        foam_node = dag["dag_nodes"][FOAM_NODE_ID]
        foam_meta = decode_capsule(foam_node["meta_capsule"])
        
        if "layers" not in foam_meta:
            foam_meta["layers"] = []
            
        for h in new_headers:
            if h not in foam_meta["layers"]:
                foam_meta["layers"].append(h)
        
        print(f"[*] Sprayed foam with {len(new_headers)} new metadata headers.")
        
        # Re-encode foam node
        new_capsule = encode_capsule(foam_meta)
        foam_node["meta_capsule"] = new_capsule
        foam_node["meta_capsule_hash"] = hashlib.sha256(new_capsule.encode("utf-8")).hexdigest()
        foam_node["timestamp"] = datetime.now().timestamp()

    # 3. Finalize DAG
    dag["node_count"] = len(dag["dag_nodes"])
    dag["compute_metrics"]["actions"] = len(dag["dag_nodes"])
    dag["compute_metrics"]["energy"] = round(sum(v["compute_weight"] for v in dag["dag_nodes"].values()), 1)
    dag["root_hash"] = hashlib.sha256(
        json.dumps(dag["dag_nodes"], sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    
    DAG_PATH.write_text(json.dumps(dag, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"[+] HyperDAG updated: {DAG_PATH}")

    # 4. Sync metadata_report.json
    print("[*] Syncing metadata_report.json...")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "extract_metadata.py")])

def main():
    sources_path = ROOT / "sources.txt"
    if not sources_path.exists():
        print(f"[!] Sources file not found: {sources_path}")
        return

    # Phase 1: Sweep
    if run_sweep(sources_path, limit=20):
        # Phase 2: Append and Spray
        update_dag_and_foam()
    else:
        print("[!] Sweep failed or returned no results.")

if __name__ == "__main__":
    main()
