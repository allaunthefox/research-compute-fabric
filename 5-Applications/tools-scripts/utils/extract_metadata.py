# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import json
import base64
import zlib
import os
import argparse
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from io_harness_compat import spawn_isolated_process


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_INPUT = os.path.join(PROJECT_ROOT, "Research Documents", "resonant_stack_v5.dag.json")


def decode_capsule(capsule: str) -> dict:
    missing_padding = (-len(capsule)) % 4
    padding = '=' * missing_padding
    decoded_bytes = base64.urlsafe_b64decode(capsule + padding)
    decompressed_bytes = zlib.decompress(decoded_bytes)
    return json.loads(decompressed_bytes.decode('utf-8'))

def extract_metadata(input_path):
    if not os.path.exists(input_path):
        print(f"File not found: {input_path}")
        return {}

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error reading file: {e}")
        return {}

    nodes = data.get('dag_nodes', {})
    if not isinstance(nodes, dict):
        print("Invalid input shape: 'dag_nodes' must be an object")
        return {}
    results = {}

    for node_id, node_data in nodes.items():
        capsule = node_data.get('meta_capsule')
        if not capsule:
            continue
        
        try:
            decoded_metadata = decode_capsule(capsule)
            results[node_id] = {
                "tier": node_data.get('tier_name'),
                "tags": node_data.get('tags'),
                "metadata": decoded_metadata
            }
        except (ValueError, zlib.error, json.JSONDecodeError) as e:
            results[node_id] = {"error": str(e), "capsule_head": capsule[:20] if capsule else None}

    return results


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Extract and decode node metadata capsules from a DAG JSON file.")
    p.add_argument("input", nargs="?", default=DEFAULT_INPUT, help="Path to resonant_stack DAG JSON.")
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    cli_input_path = args.input
    extracted_metadata = extract_metadata(cli_input_path)
    print(json.dumps(extracted_metadata, indent=2))

    # Write regenerated canonical metadata report.
    out_dir = os.path.join(PROJECT_ROOT, "out")
    os.makedirs(out_dir, exist_ok=True)
    regen_path = os.path.join(out_dir, "graph_os_decoded_metadata_regenerated.json")
    with open(regen_path, "w", encoding="utf-8") as f:
        json.dump(extracted_metadata, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"[+] Wrote canonical metadata: {regen_path}", file=sys.stderr)

    # Auto-sync metadata_report.json to canonical and verify alignment.
    sync_script = os.path.join(os.path.dirname(__file__), "sync_metadata_report.py")
    returncode, _, _ = spawn_isolated_process(
        [sys.executable, sync_script, "--sync"]
    )
    sys.exit(returncode)
