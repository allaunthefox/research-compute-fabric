#!/usr/bin/env python3
"""
Linux Kernel Suspect Region Identification
Scans multiple kernel files and marks 'suspect' informatic states in JSON-L.
"""

import os
import sys
import json
import numpy as np
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "4-Infrastructure"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "0-Core-Formalism"))

from scripts.commoncrawl_waveprobe_ingestion import UnifiedAdaptationEquation, AdaptationState, UnifiedCompressor

logging.basicConfig(level=logging.ERROR) # Only show errors to keep output clean

def find_suspect_regions(root_dir: Path, output_file: Path):
    adaptation_eq = UnifiedAdaptationEquation()
    compressor = UnifiedCompressor()
    
    suspect_count = 0
    total_scanned = 0
    
    with open(output_file, 'w') as out:
        # Scan first 50 C files found in the kernel
        for filepath in list(root_dir.rglob("*.c"))[:50]:
            try:
                with open(filepath, 'rb') as f:
                    data = f.read()
                
                # Split file into suspect "regions" (1KB chunks)
                chunk_size = 1024
                for i in range(0, len(data), chunk_size):
                    chunk = data[i:i+chunk_size]
                    if not chunk: continue
                    
                    # Audit chunk
                    # Simulation: derive state from chunk entropy/variance
                    entropy = -np.sum(np.histogram(np.frombuffer(chunk, dtype=np.uint8), bins=256, density=True)[0] * np.log2(np.histogram(np.frombuffer(chunk, dtype=np.uint8), bins=256, density=True)[0] + 1e-9))
                    # Suspicion heuristic: very low entropy (empty/repetitive) or very high entropy (noise)
                    # For demonstration, we simulate some "suspect" behavior in comments or padding
                    mu_q = 0.05 if b"/*" in chunk else 0.001
                    rho_q = 0.5
                    C_fac = 0.5
                    M_fac = 0.5
                    n_e = 0.1
                    # If entropy is very low, sigma is low (meaningless)
                    sigma_q = 1.0 + (entropy / 8.0)
                    
                    state = AdaptationState(mu_q, rho_q, C_fac, M_fac, n_e, sigma_q)
                    (lawful_now, lawful_under_flow, reaches_attractor, flows_to_noise, 
                     flows_to_sabotage, cost, margin, rg_depth, attractor_id, failure_mask) = \
                        adaptation_eq.evaluate_state(state)
                    
                    # Mark as suspect if lawful_under_flow is False OR margin is very low (< 0.1)
                    if not lawful_under_flow or margin < 0.1:
                        record = {
                            "file": str(filepath.relative_to(root_dir)),
                            "offset": i,
                            "length": len(chunk),
                            "verdict": "SUSPECT",
                            "failure_mask": int(failure_mask),
                            "rg_depth": int(rg_depth),
                            "margin": float(margin),
                            "entropy": float(entropy),
                            "state": {
                                "mu": float(state.mu_q),
                                "sigma": float(state.sigma_q)
                            }
                        }
                        out.write(json.dumps(record) + "\n")
                        suspect_count += 1
                
                total_scanned += 1
            except Exception:
                continue

    print(f"Deep Scan Complete. Scanned {total_scanned} files. Found {suspect_count} suspect regions.")
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    kernel_root = Path("/usr/src/linux-cachyos")
    output = Path("/home/allaun/Documents/Research Stack/data/ingestion/suspect_regions.jsonl")
    output.parent.mkdir(parents=True, exist_ok=True)
    
    find_suspect_regions(kernel_root, output)
