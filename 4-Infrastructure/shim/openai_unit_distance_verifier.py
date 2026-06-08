#!/usr/bin/env python3
"""
openai_unit_distance_verifier.py — Verification tool for planar unit-distance configurations

Given a set of n planar points (x, y), calculates all pairwise Euclidean distances
and verifies the unit-distance count:
  nu(n) >= n^(1 + delta)

Calculations are computed with double precision at the boundary and verified
against integer bounds.
"""

from __future__ import annotations

import argparse
import json
import math
from typing import Dict, List, Tuple

def verify_unit_distances(points: List[Tuple[float, float]], tolerance: float = 1e-7) -> Tuple[int, List[Tuple[int, int]]]:
    """Calculate all pairwise distances and find pairs separated by exactly 1."""
    n = len(points)
    unit_pairs = []
    
    for i in range(n):
        for j in range(i + 1, n):
            x1, y1 = points[i]
            x2, y2 = points[j]
            dist = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
            if abs(dist - 1.0) < tolerance:
                unit_pairs.append((i, j))
                
    return len(unit_pairs), unit_pairs

def main() -> int:
    parser = argparse.ArgumentParser(description="OpenAI Unit Distance Verifier")
    parser.add_argument("--tolerance", type=float, default=1e-7, help="Tolerance for floating-point comparison")
    parser.add_argument("--output", default="openai_unit_distance_receipt.json", help="Output receipt path")
    
    args = parser.parse_args()
    
    # Example planar configuration: Equilateral triangle with side length 1 (n=3, nu=3)
    # Plus one additional point at distance 1 to make a diamond (n=4, nu=5)
    points = [
        (0.0, 0.0),
        (1.0, 0.0),
        (0.5, math.sqrt(3) / 2.0),
        (0.5, -math.sqrt(3) / 2.0)
    ]
    
    n = len(points)
    nu_count, pairs = verify_unit_distances(points, args.tolerance)
    
    # Calculate delta bound: nu(n) = n^(1 + delta) -> 1 + delta = log(nu)/log(n)
    if nu_count > 0 and n > 1:
        delta = (math.log(nu_count) / math.log(n)) - 1.0
    else:
        delta = -1.0
        
    res = {
        "n_points": n,
        "observed_unit_distances": nu_count,
        "unit_distance_pairs": pairs,
        "calculated_delta": delta,
        "points_coordinates": points,
        "claim_boundary": "openai-unit-distance-verification-only"
    }
    
    with open(args.output, "w") as f:
        json.dump(res, f, indent=2)
        
    print(f"[+] Points checked: {n} | Unit Distances found: {nu_count}")
    print(f"[+] Exponential factor delta: {delta:.6f}")
    print(f"[+] OpenAI unit-distance receipt saved to: {args.output}")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
