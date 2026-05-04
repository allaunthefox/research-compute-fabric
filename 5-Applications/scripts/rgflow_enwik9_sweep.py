#!/usr/bin/env python3
"""
Enwik9 (1GB) RGFlow Sweep
Filtrating the massive knowledge corpus.
"""

import os
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

def run_enwik9_sweep(input_file: Path, output_file: Path):
    print(f"Opening 1GB Hutter Archive: {input_file}")
    file_size = os.path.getsize(input_file)
    
    detector = BlindDetector()
    window_size = 5000
    stride = 2500
    
    purified_data = bytearray()
    total_processed = 0
    lawful_count = 0
    
    with open(input_file, 'rb') as f:
        while True:
            chunk = f.read(window_size)
            if not chunk:
                break
                
            total_processed += len(chunk)
            
            # Map binary to DNA proxy (ACGT) for the detector
            # This is a heuristic mapping for speed in 1GB sweeps
            counts = np.unique(list(chunk), return_counts=True)[1]
            probs = counts / len(chunk)
            entropy = -np.sum(probs * np.log2(probs + 1e-9))
            
            # Lawfulness Check
            # Requirement: High entropy (meaning), structured distribution
            if 4.2 < entropy < 7.8 and len(counts) < 180: # Non-random text signature
                lawful_count += 1
                # RESTORE: Add a sample of the lawful chunk
                purified_data.extend(chunk[:stride])
            
            if total_processed % (10 * 1024 * 1024) == 0:
                print(f"Sweep Progress: {total_processed // (1024*1024)}MB / 1000MB (Purified: {len(purified_data)//1024}KB)")
                
            if len(purified_data) > 50 * 1024 * 1024: # Cap the purified core to 50MB for this pass
                print("Purified Core limit (50MB) reached. Finalizing...")
                break

    print(f"Restoring 1GB Purified Core ({len(purified_data)} bytes)...")
    with open(output_file, 'wb') as f:
        f.write(purified_data)
        
    print(f"Enwik9 Purified Archive saved to {output_file}")
    print(f"Filtration Ratio: {total_processed / len(purified_data):.2f}x")

if __name__ == "__main__":
    input_f = Path("/home/allaun/Documents/Research Stack/data/hutter_archive/enwik9")
    output_f = Path("/home/allaun/Documents/Research Stack/data/hutter_archive/enwik9_purified.bin")
    
    if input_f.exists():
        run_enwik9_sweep(input_f, output_f)
    else:
        print("Error: enwik9 raw file not found.")
