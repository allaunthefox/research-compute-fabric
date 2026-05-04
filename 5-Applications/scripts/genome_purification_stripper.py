#!/usr/bin/env python3
"""
Genome Purification: Stripping the Bad Parts
Auditing C.fa based on RGFlow Lawfulness.
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

def strip_bad_parts(input_fa: Path, output_fa: Path):
    print(f"Opening Target Genome: {input_fa.name}")
    with open(input_fa, 'r') as f:
        lines = f.readlines()
        seq = "".join(l.strip() for l in lines if not l.startswith(">"))
    
    print(f"Original Sequence Length: {len(seq)} symbols")
    
    detector = BlindDetector()
    window_size = 5000
    stride = 2500
    
    purified_seq = []
    bad_parts_count = 0
    total_parts = 0
    
    print("Initiating Informatic Stripping Sweep...")
    
    for i in range(0, len(seq) - window_size + 1, stride):
        window = seq[i : i + window_size]
        total_parts += 1
        
        state = detector.calculate_window_state(window)
        (lawful_now, lawful_under_flow, _, _, _, _, _, rg_depth, attractor_id, _) = \
            detector.adaptation_eq.evaluate_state(state)
        
        # WE ONLY KEEP THE LAWFUL CORE
        if lawful_under_flow and rg_depth > 8:
            # We append the first 'stride' part to avoid overlap redundancy
            purified_seq.append(window[:stride])
        else:
            bad_parts_count += 1
            if bad_parts_count < 5:
                print(f"Stripped Bad Part at Locus {i}nd (Sigma: {state.sigma_q:.2f}, Depth: {rg_depth})")

    final_seq = "".join(purified_seq)
    
    print(f"\n--- PURIFICATION SUMMARY ---")
    print(f"Total Regions Scanned: {total_parts}")
    print(f"Bad Parts Stripped:    {bad_parts_count}")
    print(f"Lawful Parts Restored: {len(purified_seq)}")
    print(f"Purified Array Length: {len(final_seq)} symbols")
    print(f"Purification Ratio:    {len(seq) / (len(final_seq)+1e-9):.2f}x")
    
    with open(output_file, 'w') as f:
        f.write(">Purified_Sovereign_Genome\n")
        # Format as 80-char lines
        for i in range(0, len(final_seq), 80):
            f.write(final_seq[i:i+80] + "\n")
            
    print(f"\nPurified Genome saved to {output_fa}")

if __name__ == "__main__":
    input_file = Path("/home/allaun/Documents/Research Stack/data/benchmarks/killer_criterion/C.fa")
    output_file = Path("/home/allaun/Documents/Research Stack/data/benchmarks/killer_criterion/C_purified.fa")
    
    if input_file.exists():
        strip_bad_parts(input_file, output_file)
    else:
        print("Error: Target genome not found.")
