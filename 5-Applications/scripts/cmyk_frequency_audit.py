#!/usr/bin/env python3
"""
CMYK Frequency Audit: Testing the Color Problem
RGFlow on Chromodynamic Frequency Packets.
"""

import sys
import numpy as np
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "4-Infrastructure"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "0-Core-Formalism"))

from scripts.rgflow_blind_detector import BlindDetector

logging.basicConfig(level=logging.ERROR)

def run_cmyk_audit():
    print("--- CMYK FREQUENCY INFORMATIC AUDIT ---")
    
    # 1. Formal CMYK Constants (from lean)
    base_freqs = {"C": 600, "M": 1200, "Y": 1800, "K": 2400}
    delta_freq = 20
    
    def generate_packet(nibbles, jitter=0):
        # nibbles: list of 4 values [0-15]
        packet = []
        for i, (ch, base) in enumerate(base_freqs.items()):
            packet.append(base + delta_freq * nibbles[i] + jitter)
        return np.array(packet)

    detector = BlindDetector()
    
    # 2. Test Cases
    test_cases = [
        ("LAWFUL (Pure)", [1, 10, 3, 15], 0),
        ("LAWFUL (Pure 2)", [8, 8, 8, 8], 0),
        ("SABOTAGED (Jitter +5)", [1, 10, 3, 15], 5),
        ("SABOTAGED (Noise)", [1, 10, 3, 15], 17),
    ]
    
    for label, nibbles, jitter in test_cases:
        packet = generate_packet(nibbles, jitter)
        print(f"\nAuditing {label}: {packet}")
        
        # Mapping Frequency to Informatic State
        # We look for the "Resonance" at 20Hz increments
        # Jitter breaks the resonance.
        
        # 1. Mutation (mu): distance from lawful bins
        offsets = [(f - base_freqs[ch]) % delta_freq for f, ch in zip(packet, base_freqs.keys())]
        error = np.mean(offsets)
        mu_q = (error / delta_freq) * 1.5
        
        # 2. Sigma (Connectance): Inverse of Error
        sigma_q = 2.0 - mu_q
        
        state = detector.calculate_window_state('ACGT'*100) # Template
        state.sigma_q = float(sigma_q)
        state.mu_q = float(mu_q)
        
        (lawful_now, lawful_under_flow, _, _, _, _, _, depth, _, _) = \
            detector.adaptation_eq.evaluate_state(state)
            
        print(f"  Informatic Sigma: {sigma_q:.4f}")
        print(f"  Manifold Depth:   {depth}/10")
        
        if lawful_under_flow and depth >= 10:
            print(f"  [+] RESULT: LAWFUL CHROMODYNAMICS")
        else:
            print(f"  [!] RESULT: CHROMATIC SABOTAGE DETECTED")

    print("\n--- AUDIT COMPLETE ---")

if __name__ == "__main__":
    run_cmyk_audit()
