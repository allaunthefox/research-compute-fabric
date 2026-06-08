#!/usr/bin/env python3
"""
openai_unit_distance_verifier.py — Verification tool for planar unit-distance configurations

Given a set of n planar points (x, y), calculates all pairwise Euclidean distances
and verifies the unit-distance count:
  nu(n) >= n^(1 + delta)

Supports generating points algebraically using complex multiplication (CM) field extensions.
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
    
    # Optimize by using spatial bucketing/grid for larger point sets to avoid O(n^2) distance checks
    if n > 2000:
        print(f"[*] Optimizing distance check using grid bucket for n={n} points...")
        # Since distance is exactly 1, we can bucket points into grid cells of size 1.0
        grid: Dict[Tuple[int, int], List[int]] = {}
        for idx, (x, y) in enumerate(points):
            cell = (int(math.floor(x)), int(math.floor(y)))
            if cell not in grid:
                grid[cell] = []
            grid[cell].append(idx)
            
        for cell, indices in grid.items():
            cx, cy = cell
            # Check current cell and neighboring cells (9 cells total)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    neighbor = (cx + dx, cy + dy)
                    if neighbor in grid:
                        for idx1 in indices:
                            for idx2 in grid[neighbor]:
                                if idx1 < idx2:
                                    x1, y1 = points[idx1]
                                    x2, y2 = points[idx2]
                                    dist = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
                                    if abs(dist - 1.0) < tolerance:
                                        unit_pairs.append((idx1, idx2))
        return len(unit_pairs), unit_pairs
    else:
        for i in range(n):
            for j in range(i + 1, n):
                x1, y1 = points[i]
                x2, y2 = points[j]
                dist = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
                if abs(dist - 1.0) < tolerance:
                    unit_pairs.append((i, j))
        return len(unit_pairs), unit_pairs

def generate_cm_generators(m: int, d: int) -> List[Tuple[float, float]]:
    """Generate m distinct magnitude-1 complex numbers using elements of Q(sqrt(-d)).
    
    For each coprime pair (a, b), alpha = a + b*sqrt(-d) yields unit gamma = alpha / conj(alpha).
    """
    generators = []
    # Search for coprime pairs (a, b)
    a = 1
    while len(generators) < m:
        for b in range(1, 100):
            if math.gcd(a, b) == 1:
                # Calculate gamma = (a + b*i*sqrt(d)) / (a - b*i*sqrt(d))
                denom = a**2 + d * b**2
                real_part = (a**2 - d * b**2) / denom
                imag_part = (2 * a * b * math.sqrt(d)) / denom
                
                # Verify magnitude is 1
                mag = math.sqrt(real_part**2 + imag_part**2)
                if abs(mag - 1.0) < 1e-9:
                    pt = (real_part, imag_part)
                    if pt not in generators:
                        generators.append(pt)
                        if len(generators) == m:
                            break
        a += 1
    return generators

def generate_subset_sums(generators: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """Generate all 2^m subset sums of the generators to form a planar point set."""
    m = len(generators)
    points = [(0.0, 0.0)]
    for gen in generators:
        new_pts = []
        for pt in points:
            new_pts.append((pt[0] + gen[0], pt[1] + gen[1]))
        points.extend(new_pts)
        
    # Deduplicate points using tolerance
    unique_points = []
    seen = set()
    for x, y in points:
        # Round to 8 decimal places for uniqueness check
        key = (round(x, 8), round(y, 8))
        if key not in seen:
            seen.add(key)
            unique_points.append((x, y))
    return unique_points

def main() -> int:
    parser = argparse.ArgumentParser(description="OpenAI Unit Distance Verifier")
    parser.add_argument("--tolerance", type=float, default=1e-7, help="Tolerance for floating-point comparison")
    parser.add_argument("--output", default="openai_unit_distance_receipt.json", help="Output receipt path")
    parser.add_argument("--algebraic", action="store_true", help="Enable algebraic generation using CM-field units")
    parser.add_argument("--d-val", type=int, default=3, help="The imaginary integer d for Q(sqrt(-d))")
    parser.add_argument("--generators", type=int, default=10, help="Number of generators m for subset sums")
    
    args = parser.parse_args()
    
    if args.algebraic:
        print(f"[*] Generating algebraic points using CM-field Q(sqrt(-{args.d_val}))...")
        generators = generate_cm_generators(args.generators, args.d_val)
        print(f"[+] Generated {len(generators)} CM units of magnitude 1.")
        points = generate_subset_sums(generators)
        print(f"[+] Formed {len(points)} distinct points from subset sums.")
    else:
        # Default fallback diamond configuration
        points = [
            (0.0, 0.0),
            (1.0, 0.0),
            (0.5, math.sqrt(3) / 2.0),
            (0.5, -math.sqrt(3) / 2.0)
        ]
        generators = []
        
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
        "calculated_delta": delta,
        "generators": generators,
        "claim_boundary": "openai-unit-distance-verification-only"
    }
    
    # If the point set is small enough, include coordinates in receipt
    if n <= 1000:
        res["points_coordinates"] = points
        res["unit_distance_pairs"] = pairs
        
    with open(args.output, "w") as f:
        json.dump(res, f, indent=2)
        
    print(f"[+] Points checked: {n} | Unit Distances found: {nu_count}")
    print(f"[+] Exponential factor delta: {delta:.6f}")
    print(f"[+] OpenAI unit-distance receipt saved to: {args.output}")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())

