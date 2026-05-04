#!/usr/bin/env python3
"""
bt20_bootstrap.py — Geometric Reader for BT20 Machine

Pulls 20 'Principal Axioms' from the 1GB Truth Baseline and converts
them into initial mu-seeds (neurons) for the tuning machine.
"""

import sqlite3
import json
import os
import hashlib
from pathlib import Path
from typing import List, Dict

DB_PATH = "/home/allaun/.tardy_mmr.db"
SEED_OUTPUT = Path.home() / ".gemini/antigravity/scratch/bt20_initial_seeds.json"

def get_principal_axioms(db_path: str, count: int = 20) -> List[Dict]:
    """Samples the 1GB sweep for high-saturation axioms."""
    conn = sqlite3.connect(db_path)
    # Sample axioms with regional basin roots (top-level truths)
    cursor = conn.execute(
        "SELECT payload FROM mmr WHERE leaf_type = 'AXIOM' ORDER BY RANDOM() LIMIT ?",
        (count,)
    )
    results = []
    for row in cursor:
        results.append(json.loads(row[0]))
    conn.close()
    return results

def axiom_to_mu_seed(axiom: Dict, index: int) -> Dict:
    """
    Encodes an Axiom into a 32-bit mu-seed structure (simplified for simulation).
    Pattern: GEFI-PRIM-1 (Encode primitive).
    """
    # Use the root hash to derive the 'Activation' and 'Transform'
    root_hash = axiom.get("batch_root_hash", "0" * 64)
    hash_bytes = bytes.fromhex(root_hash)
    
    # 10 bits Delta P from first 10 bits of hash
    delta_p = int.from_bytes(hash_bytes[:2], 'big') & 0x3FF
    # Gamma (Transform mode) - 5 bits
    gamma = hash_bytes[2] & 0x1F
    # Activation state - 4 bits
    activation = hash_bytes[3] & 0xF
    # Confidence - derived from batch member count
    member_count = axiom.get("member_count", 0)
    confidence = min(15, member_count // 64)
    
    # Pack into word (simulated)
    word = delta_p
    word |= (1 << 10) # Region: INTERIOR
    word |= (gamma << 14)
    word |= (activation << 19)
    word |= (confidence << 27)
    
    return {
        "neuron_id": index,
        "mu_seed": word,
        "gamma": gamma,
        "activation": float(activation),
        "confidence": confidence / 15.0,
        "anchor": root_hash[:8],
        "axiom_ref": f"record_{index}"
    }

def bootstrap():
    print(f"[*] Reading Truth Baseline from {DB_PATH}...")
    if not os.path.exists(DB_PATH):
        print(f"[!] Error: DB not found at {DB_PATH}")
        return

    axioms = get_principal_axioms(DB_PATH, 20)
    print(f"[*] Sampled {len(axioms)} axioms from the 1 million record pool.")

    seeds = []
    for i, axiom in enumerate(axioms):
        seed = axiom_to_mu_seed(axiom, i)
        seeds.append(seed)

    # Save to scratch
    os.makedirs(SEED_OUTPUT.parent, exist_ok=True)
    with open(SEED_OUTPUT, 'w') as f:
        json.dump(seeds, f, indent=4)
    
    print(f"[✅] BT20 Machine Bootstrapped. 20 neurons initialized in {SEED_OUTPUT}")

if __name__ == "__main__":
    bootstrap()
