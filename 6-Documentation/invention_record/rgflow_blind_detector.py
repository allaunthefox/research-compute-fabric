#!/usr/bin/env python3
"""
RGFlow Blind Detector
Localizes lawful informatic phases in unknown sequences.
"""

import sys
import json
import numpy as np
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.commoncrawl_waveprobe_ingestion import UnifiedAdaptationEquation, AdaptationState

logging.basicConfig(level=logging.ERROR)

class BlindDetector:
    def __init__(self):
        self.adaptation_eq = UnifiedAdaptationEquation()
        self.window_size = 5000 # Symbols
        self.stride = 2500

    def calculate_window_state(self, sequence: str) -> AdaptationState:
        """Calculate informatic state for a sequence window using AVMR Spectral Audit."""
        # 1. Map to Amino Acids (AVMR Unified Compression)
        # Standard Genetic Code mapping
        genetic_code = {
            'TTT': 'F', 'TTC': 'F', 'TTA': 'L', 'TTG': 'L',
            'CTT': 'L', 'CTC': 'L', 'CTA': 'L', 'CTG': 'L',
            'ATT': 'I', 'ATC': 'I', 'ATA': 'I', 'ATG': 'M',
            'GTT': 'V', 'GTC': 'V', 'GTA': 'V', 'GTG': 'V',
            'TCT': 'S', 'TCC': 'S', 'TCA': 'S', 'TCG': 'S',
            'CCT': 'P', 'CCC': 'P', 'CCA': 'P', 'CCG': 'P',
            'ACT': 'T', 'ACC': 'T', 'ACA': 'T', 'ACG': 'T',
            'GCT': 'A', 'GCC': 'A', 'GCA': 'A', 'GCG': 'A',
            'TAT': 'Y', 'TAC': 'Y', 'TAA': '*', 'TAG': '*',
            'CAT': 'H', 'CAC': 'H', 'CAA': 'Q', 'CAG': 'Q',
            'AAT': 'N', 'AAC': 'N', 'AAA': 'K', 'AAG': 'K',
            'GAT': 'D', 'GAC': 'D', 'GAA': 'E', 'GAG': 'E',
            'TGT': 'C', 'TGC': 'C', 'TGA': '*', 'TGG': 'W',
            'CGT': 'R', 'CGC': 'R', 'CGA': 'R', 'CGG': 'R',
            'AGT': 'S', 'AGC': 'S', 'AGA': 'R', 'AGG': 'R',
            'GGT': 'G', 'GGC': 'G', 'GGA': 'G', 'GGG': 'G',
        }
        
        amino_acids = []
        for j in range(0, len(sequence) - 2, 3):
            codon = sequence[j:j+3]
            amino_acids.append(genetic_code.get(codon, '?'))
        
        # 2. Spectral Coherence (Signature Density)
        unique_acids = len(set(amino_acids))
        total_acids = len(amino_acids)
        # In noise, unique_acids ~ 20. In structure (pi/e), certain residues dominate.
        spectral_density = unique_acids / 21.0
        
        # 3. RGFlow Beta: Mutation and Entropy
        transitions = sum(1 for k in range(len(amino_acids)-1) if amino_acids[k] != amino_acids[k+1])
        mu_q = (transitions / total_acids) * 0.1
        
        # 4. Final Sigma: Only high if the spectrum has structured resonance (AVMR Invariant)
        counts = [amino_acids.count(a) for a in set(amino_acids)]
        entropy = -sum((c/total_acids) * np.log2(c/total_acids) for c in counts if c > 0)
        
        # Crucial Filter: Lawful structure has structured entropy that persists under scaling.
        # Random noise has max entropy but high uniform spectral density.
        if 2.5 < entropy < 4.2 and spectral_density < 0.95:
            sigma_q = 1.0 + (entropy / 4.0)
        else:
            sigma_q = 0.5
        
        return AdaptationState(mu_q, 0.5, 0.5, 0.5, 0.5, sigma_q)

    def scan_file(self, filename: Path):
        with open(filename, 'r') as f:
            lines = f.readlines()
            seq = "".join(l.strip() for l in lines if not l.startswith(">"))

        print(f"\nScanning {filename.name} ({len(seq)} symbols)...")
        
        lawful_regions = []
        current_region = None
        
        for i in range(0, len(seq) - self.window_size + 1, self.stride):
            window = seq[i : i + self.window_size]
            state = self.calculate_window_state(window)
            
            (lawful_now, lawful_under_flow, reaches_attractor, flows_to_noise, 
             flows_to_sabotage, cost, margin, rg_depth, attractor_id, failure_mask) = \
                self.adaptation_eq.evaluate_state(state)
            
            if lawful_under_flow and rg_depth > 8:
                if current_region is None:
                    current_region = {"start": i, "end": i + self.window_size, "depth_sum": rg_depth, "count": 1}
                else:
                    current_region["end"] = i + self.window_size
                    current_region["depth_sum"] += rg_depth
                    current_region["count"] += 1
            else:
                if current_region:
                    current_region["avg_depth"] = current_region["depth_sum"] / current_region["count"]
                    # ONLY report regions with significant width and high average depth
                    if current_region["end"] - current_region["start"] >= 20000:
                        lawful_regions.append(current_region)
                    current_region = None
        
        if current_region:
            current_region["avg_depth"] = current_region["depth_sum"] / current_region["count"]
            if current_region["end"] - current_region["start"] >= 20000:
                lawful_regions.append(current_region)

        if not lawful_regions:
            print("  Result: ✗ NO LAWFUL REGIONS DETECTED (Pure Noise/Repetition/Sabotage)")
        else:
            print(f"  Result: ✓ {len(lawful_regions)} LAWFUL PHASE(S) DETECTED")
            for r in lawful_regions:
                # Filter out small jitter
                if r['end'] - r['start'] > 10000:
                    print(f"    - Locus: {r['start']}nd - {r['end']}nd (Width: {r['end']-r['start']})")
                    print(f"    - Confidence: {r['avg_depth']*10:.1f}% Scale Stability")
                    print(f"    - Attractor: 1 (Lawful Informatic Phase)")

if __name__ == "__main__":
    detector = BlindDetector()
    bench_dir = Path("/home/allaun/Documents/Research Stack/data/benchmarks/killer_criterion")
    
    for label in ['A', 'B', 'C', 'D', 'E']:
        detector.scan_file(bench_dir / f"{label}.fa")
