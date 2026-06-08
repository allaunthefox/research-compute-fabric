#!/usr/bin/env python3
"""
quandela_erdos_search.py — Photonic-guided search using Quandela Perceval SDK

Maps candidate Erdős configurations (discrepancy and distinct distance vectors)
to a 3-mode/6-mode linear optical circuit. Simulates photonic mode sampling
using the SLOS simulator to estimate spectral complexity and "shave off"
combinatorial search explosions.
"""

from __future__ import annotations

import argparse
import json
import time
from typing import Dict, List, Tuple, Optional
import numpy as np
import perceval as pcvl

# Q16.16 conversion
Q16_SCALE = 65536

class PhotonicErdosSearch:
    def __init__(self, M: int = 6, exhaust_modes: Tuple[int, ...] = (3, 4, 5)):
        self.M = M
        self.exhaust_modes = exhaust_modes

    def encode_vector(self, a: List[float]) -> Dict:
        """Normalize and map spectral vector to phase angles."""
        norm = float(np.linalg.norm(a))
        if norm < 1e-9:
            return {"theta": [0.0] * len(a), "norm": 0.0}
        theta = [float(np.pi * (x / norm)) for x in a]
        return {"theta": theta, "norm": norm}

    def sample_circuit(self, theta: List[float], norm: float, N_shots: int) -> Dict[str, float]:
        """Build and sample the linear-optical circuit using Perceval SLOS simulator."""
        if norm < 1e-9:
            return {str(i): 0.0 for i in range(self.M)}

        circuit = pcvl.Circuit(self.M)
        # PS (Phase Shifters) on encoded modes
        for i in range(min(len(theta), self.M)):
            circuit.add(i, pcvl.PS(theta[i]))

        # Mix modes via Beam Splitters (BS)
        for i in range(self.M - 1):
            circuit.add((i, i+1), pcvl.BS())

        # 1 photon in each of the first 3 modes, 0 elsewhere
        input_state = pcvl.BasicState([1, 1, 1] + [0] * (self.M - 3))

        processor = pcvl.Processor("SLOS", circuit)
        processor.with_input(input_state)

        sampler = pcvl.algorithm.Sampler(processor)
        res = sampler.sample_count(N_shots)

        hist = {str(i): 0.0 for i in range(self.M)}
        for state, count in res["results"].items():
            prob = count / N_shots
            for mode, photons in enumerate(state):
                hist[str(mode)] += photons * prob

        # Scale by total energy (norm^2)
        for k in hist:
            hist[k] *= (norm ** 2)

        return hist

    def compute_photonic_complexity(self, hist: Dict[str, float]) -> int:
        """Compute Omega complexity from exhaust modes (returned in Q16_16)."""
        omega_float = sum(hist.get(str(m), 0.0) for m in self.exhaust_modes)
        return int(omega_float * Q16_SCALE)

def optimize_erdos_vector(
    searcher: PhotonicErdosSearch,
    candidates: List[List[float]],
    N_shots: int
) -> Dict:
    """Evaluate candidate vectors and select the one with optimal photonic complexity."""
    best_vector = []
    min_complexity = float("inf")
    results = []

    for idx, cand in enumerate(candidates):
        encoding = searcher.encode_vector(cand)
        hist = searcher.sample_circuit(encoding["theta"], encoding["norm"], N_shots)
        complexity = searcher.compute_photonic_complexity(hist)
        
        results.append({
            "index": idx,
            "candidate": cand,
            "complexity_q16": complexity,
            "complexity_float": complexity / Q16_SCALE
        })
        
        if complexity < min_complexity:
            min_complexity = complexity
            best_vector = cand

    return {
        "best_candidate": best_vector,
        "min_complexity_q16": min_complexity,
        "results": results
    }

def main() -> int:
    parser = argparse.ArgumentParser(description="Quandela Erdos Search")
    parser.add_argument("--shots", type=int, default=1000, help="Number of sampler shots")
    parser.add_argument("--output", default="quandela_erdos_search_receipt.json", help="Output receipt path")
    
    args = parser.parse_args()
    
    # Generate test candidates representing diverse spectral vector configurations
    candidates = [
        [1.0, 0.3, 0.1],
        [0.8, 0.5, 0.2],
        [0.5, 0.5, 0.5],
        [0.1, 0.3, 1.0]
    ]
    
    print("[*] Initializing Perceval SLOS Photonic Search...")
    searcher = PhotonicErdosSearch()
    t0 = time.time()
    res = optimize_erdos_vector(searcher, candidates, args.shots)
    elapsed = time.time() - t0
    
    res["elapsed_seconds"] = elapsed
    res["shots"] = args.shots
    res["claim_boundary"] = "quandela-perceval-erdos-search-only"
    
    with open(args.output, "w") as f:
        json.dump(res, f, indent=2)
        
    print(f"[+] Photonic search complete in {elapsed:.2f}s.")
    print(f"[+] Optimal Candidate: {res['best_candidate']} (Complexity: {res['min_complexity_q16']/Q16_SCALE:.6f})")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
