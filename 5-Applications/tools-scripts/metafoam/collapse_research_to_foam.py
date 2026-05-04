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
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTERNAL_JSON = ROOT / "graph_os_metadata_external.json"

def get_file_hash(filepath):
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def collapse():
    print("[*] Collapsing research files into Graph OS metadata foam...")
    
    research_files = []
    # add_*.py -> Tier 3 (FOAM) - Speculative additions
    for f in ROOT.glob("add_*.py"):
        research_files.append((f, "Tier 3 (FOAM)", "DISCOVERY_ADDITION", ["discovery", "addition"]))
    
    # KDA_*.py -> Tier 2 (PLASMA) - Dynamic simulation/logic
    for f in ROOT.glob("KDA_*.py"):
        research_files.append((f, "Tier 2 (PLASMA)", "KDA_SIMULATION", ["kda", "simulation", "logic"]))
    
    # simulate_spyvsspy_cdr.py -> Tier 2 (PLASMA) - Counter-Intelligence Simulation
    for f in (ROOT / "scripts").glob("simulate_spyvsspy_cdr.py"):
        research_files.append((f, "Tier 2 (PLASMA)", "COUNTER_INTEL_SIM", ["cdr", "forensics", "privacy"]))

    # zec_accumulation_algorithm.py -> Tier 2 (PLASMA) - Finance Simulation
    for f in (ROOT / "scripts").glob("zec_accumulation_algorithm.py"):
        research_files.append((f, "Tier 2 (PLASMA)", "FINANCE_SIM", ["zcash", "zec", "accumulation", "alpha"]))

    # z_bridge_protocol.py -> Tier 2 (PLASMA) - Bridge Protocol
    for f in (ROOT / "scripts").glob("z_bridge_protocol.py"):
        research_files.append((f, "Tier 2 (PLASMA)", "BRIDGE_PROTOCOL", ["zcash", "zec", "bridge", "privacy"]))

    # quantum_asic_miner.py -> Tier 2 (PLASMA) - Mining Simulation
    for f in (ROOT / "scripts").glob("quantum_asic_miner.py"):
        research_files.append((f, "Tier 2 (PLASMA)", "MINING_SIM", ["btc", "asic", "emulator", "gpgpu"]))

    # generate_z_address_native.py -> Tier 2 (PLASMA) - Address Generation

    for f in (ROOT / "scripts").glob("generate_z_address_via_logic_signal_substrate.py"):
        research_files.append((f, "Tier 2 (PLASMA)", "ADDRESS_GEN", ["zcash", "zec", "logic_signal_substrate", "address"]))

    # .logic_signal_substrate files -> Tier 1 (CRYSTALLINE) - Verified structure
    for f in ROOT.glob("*.logic_signal_substrate"):
        research_files.append((f, "Tier 1 (CRYSTALLINE)", "TSM_STRUCTURE", ["logic_signal_substrate", "structure"]))

    # zec_acquisition_result.json -> Tier 1 (CRYSTALLINE) - Financial Artifacts
    for f in ROOT.glob("zec_acquisition_result.json"):
        research_files.append((f, "Tier 1 (CRYSTALLINE)", "FINANCIAL_ARTIFACT", ["zcash", "zec", "acquisition", "result"]))

    # z_bridge_state.json -> Tier 1 (CRYSTALLINE) - Bridge State
    for f in ROOT.glob("z_bridge_state.json"):
        research_files.append((f, "Tier 1 (CRYSTALLINE)", "BRIDGE_STATE", ["zcash", "zec", "bridge", "state"]))

    # .logic_signal_substrate.json files -> Tier 1 (CRYSTALLINE) - Governance Templates
    for f in ROOT.glob("*.logic_signal_substrate.json"):
        research_files.append((f, "Tier 1 (CRYSTALLINE)", "GOVERNANCE_TEMPLATE", ["logic_signal_substrate", "template", "json"]))

    # .sterile files -> Tier 1 (CRYSTALLINE) - Disarmed Artifacts
    for f in ROOT.glob("*.sterile"):
        research_files.append((f, "Tier 1 (CRYSTALLINE)", "STERILE_ARTIFACT", ["sterile", "cdr", "disarmed"]))

    if not EXTERNAL_JSON.exists():
        existing = []
    else:
        with open(EXTERNAL_JSON, 'r') as f:
            content = f.read().strip()
            if not content:
                existing = []
            else:
                existing = json.loads(content)
            
    existing_ids = {e.get('id') for e in existing}
    added = 0
    
    for filepath, tier, module, tags in research_files:
        file_id = f"research_{filepath.name}"
        if file_id in existing_ids:
            continue
            
        file_hash = get_file_hash(filepath)
        
        # Read raw content to collapse it into the foam
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"[!] Error reading {filepath.name}: {e}")
            continue

        entry = {
            "id": file_id,
            "tier": tier,
            "module": module,
            "tags": tags + [filepath.suffix[1:]],
            "metadata": {
                "filename": filepath.name,
                "hash": file_hash,
                "raw_content": content,
                "purpose": "Research component absorbed into foam",
                "axis": "STRUC/MANI"
            }
        }
        existing.append(entry)
        added += 1
        
    with open(EXTERNAL_JSON, 'w') as f:
        json.dump(existing, f, indent=2)
        
    print(f"[+] Absorbed {added} research files into metadata foam.")
    
    # Rebuild DB
    print("[*] Rebuilding Graph OS metadata database...")
    subprocess.run([sys.executable, f"{ROOT}/scripts/build_graph_os_metadata_db.py"],
                   check=True)

if __name__ == "__main__":
    collapse()
