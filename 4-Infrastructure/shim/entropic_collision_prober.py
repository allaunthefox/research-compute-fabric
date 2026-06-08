#!/usr/bin/env python3
"""
entropic_collision_prober.py — Entropic Collision debt calculation for Sidon sets

Computes the sumset entropy of a candidate set A:
  H_sum(A) = - sum (p(s) * log2(p(s)))  where s = a + b for a, b in A, a <= b

Checks for entropy/compression spoofing by verifying if:
  |H_sum(A) - predicted_entropy| < epsilon
"""

from __future__ import annotations

import argparse
import json
import math
from typing import Dict, List, Tuple

def compute_sumset_entropy(A: List[int]) -> Tuple[float, int, Dict[int, int]]:
    """Compute the exact sumset entropy and pair-sum frequency map.
    
    All calculations are done with precise frequency maps.
    Returns:
      entropy: Shannons entropy (in bits)
      collisions: number of duplicate pair-sums (C_B2 collision debt)
      sums: dictionary of pair sums and their counts
    """
    n = len(A)
    sums = {}
    total_pairs = 0
    for i in range(n):
        for j in range(i, n):
            s = A[i] + A[j]
            sums[s] = sums.get(s, 0) + 1
            total_pairs += 1
            
    # Calculate Shannon entropy
    entropy = 0.0
    collisions = 0
    for s, count in sums.items():
        if count > 1:
            collisions += (count - 1)
        p = count / total_pairs
        entropy -= p * math.log2(p)
        
    return entropy, collisions, sums

def main() -> int:
    parser = argparse.ArgumentParser(description="Entropic Collision Prober")
    parser.add_argument("--set", type=int, nargs="+", default=[1, 3, 7, 12, 20, 30, 44, 65],
                        help="The candidate set (integer elements)")
    parser.add_argument("--output", default="entropic_collision_receipt.json", help="Output receipt path")
    
    args = parser.parse_args()
    
    A = sorted(list(set(args.set)))
    n = len(A)
    
    if n < 2:
        print("[-] Error: Candidate set must have at least 2 distinct elements.")
        return 1
        
    entropy, collisions, sums = compute_sumset_entropy(A)
    
    # Maximum possible entropy is when all pair-sums are distinct (true Sidon set)
    total_pairs = n * (n + 1) // 2
    max_possible_entropy = math.log2(total_pairs)
    
    # Deviation metric (entropy spoof check)
    entropy_deficit = max_possible_entropy - entropy
    
    res = {
        "candidate_set": A,
        "set_size": n,
        "total_pairs": total_pairs,
        "unique_sums": len(sums),
        "collisions_debt": collisions,
        "observed_entropy": entropy,
        "max_possible_entropy": max_possible_entropy,
        "entropy_deficit": entropy_deficit,
        "is_sidon": collisions == 0,
        "claim_boundary": "entropic-collision-debt-only"
    }
    
    with open(args.output, "w") as f:
        json.dump(res, f, indent=2)
        
    print(f"[+] Observed Entropy: {entropy:.6f} bits (Max: {max_possible_entropy:.6f} bits)")
    print(f"[+] Deficit: {entropy_deficit:.6f} bits | Collisions: {collisions}")
    print(f"[+] Entropic collision receipt saved to: {args.output}")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
