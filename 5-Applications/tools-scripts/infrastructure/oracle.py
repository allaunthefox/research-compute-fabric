#!/usr/bin/env python3
"""
Utility: oracle.py
------------------
The Sovereign Oracle: Informatic Retrieval & Inference Engine.
"""

import argparse
import hashlib
import json
import time
import struct
from bt20_fpga_bridge import MassArchivist

class SovereignOracle:
    def __init__(self, db_path="/home/allaun/.tardy_mmr.db"):
        self.archivist = MassArchivist(db_path=db_path)
        self.num_neurons = 20

    def seed_from_text(self, text):
        """ Hash keyword to a specific neuron index. """
        h = hashlib.sha256(text.encode()).hexdigest()
        idx = int(h[:2], 16) % self.num_neurons
        return idx

    def query(self, text):
        print(f"[>] Querying Sovereign Oracle: '{text}'...")
        neuron_id = self.seed_from_text(text)
        
        # 1. Seeding
        activation = 0xFFFF # MAX activation for the seed
        print(f"[*] Seeding Manifold -> Neuron {neuron_id}")
        if self.archivist.ser:
            self.archivist.ser.write(struct.pack(">BBH", 0x01, neuron_id, activation))
        
        # 2. Resonance (Trigger 100 epochs)
        print("[*] Initiating Informatic Resonance (100 Epochs)...")
        for _ in range(100):
            if self.archivist.ser:
                self.archivist.ser.write(bytes([0x03]))
            time.sleep(0.001)
            
        # 3. Retrieval (Poll Telemetry/Memory)
        phi = self.archivist.poll_telemetry()
        print(f"[+] Resonance Stabilized at Φss: {phi:.4f}")
        
        # 4. MMR Lookup
        return self.lookup_promotion(neuron_id)

    def lookup_promotion(self, neuron_id):
        import sqlite3
        conn = sqlite3.connect(self.archivist.db_path)
        cur = conn.cursor()
        cur.execute("SELECT payload FROM mmr WHERE leaf_type='AXIOM' AND payload LIKE ?", (f'%"neuron": {neuron_id}%',))
        match = cur.fetchone()
        conn.close()
        
        if match:
            return json.loads(match[0])
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("query", type=str, help="Search term for the Oracle")
    args = parser.parse_args()

    oracle = SovereignOracle()
    result = oracle.query(args.query)
    
    if result:
        print("\n=== ORACLE RESPONSE: PROMOTED AXIOM ===")
        print(json.dumps(result, indent=4))
    else:
        print("\n[!] ORACLE SILENT: No promoted axiom matches this informatic seed.")
