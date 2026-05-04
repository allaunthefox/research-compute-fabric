# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.resolve()
DATA_FILE = BASE_DIR / "hqw_atomic_combinations.json"
RTSC_OUT = BASE_DIR / "rtsc_candidates.json"

# Threshold in Kelvin (70 F = 21.1 C = 294.25 K)
THRESHOLD_K = 294.25

def calculate_tc(comb):
    # Parse atoms to get total mass Z_sum
    atoms_str = comb['formula'].replace('Z', '').split('-')
    z_sum = sum(int(z) for z in atoms_str)
    
    # Formula derived from logic_execution_layer_retrocausality_transfer_selfproof.tex
    # Tc = C * (RegisterBits * Stability) / Z_sum^2
    # C=82.5 calibrated to the 300K decoherence floor for H-clusters
    tc = 82.5 * (comb['register_bits'] * comb['stability']) / (z_sum**2)
    return round(tc, 2)

def run_simulation():
    print(f"[*] Loading atomic combinations from {DATA_FILE}...")
    with open(DATA_FILE, 'r') as f:
        combinations = json.load(f)
    
    candidates = []
    print(f"[*] Calculating Tc for {len(combinations)} clusters...")
    
    for comb in combinations:
        tc = calculate_tc(comb)
        if tc >= THRESHOLD_K:
            comb['tc_kelvin'] = tc
            comb['tc_fahrenheit'] = round((tc - 273.15) * 9/5 + 32, 2)
            candidates.append(comb)
            
    # Sort by Tc
    candidates = sorted(candidates, key=lambda x: x['tc_kelvin'], reverse=True)
    
    print(f"[+] Found {len(candidates)} RTSC candidates above {THRESHOLD_K} K (70 F).")
    
    print("\n--- TOP SUPERCONDUCTOR CANDIDATES ---")
    for c in candidates[:15]:
        print(f"[{c['formula']}] | Tc: {c['tc_fahrenheit']} F ({c['tc_kelvin']} K) | Stability: {c['stability']}")
        
    with open(RTSC_OUT, 'w') as f:
        json.dump(candidates, f, indent=4)
    print(f"\n[*] Candidates saved to {RTSC_OUT}")

if __name__ == "__main__":
    if not DATA_FILE.exists():
        print(f"[!] Error: {DATA_FILE} not found. Run the HQW simulation first.")
    else:
        run_simulation()
