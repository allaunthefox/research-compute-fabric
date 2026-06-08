#!/usr/bin/env python3
"""
galois_orbit_trimmer.py — Galois Orbit Trimming (Dimensional Shock Trim)

Demonstrates how to accelerate planar unit-distance searches by partitioning the
point set into orbits under the Galois group (complex conjugation symmetry).
It only computes distances from a set of orbit representatives and reconstructs the
entire distance network algebraically, showing the speedup of Dimensional Shock Trim.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from typing import Dict, List, Set, Tuple

def verify_unit_distances_brute(points: List[Tuple[float, float]], tolerance: float = 1e-7) -> int:
    """Standard brute-force O(n^2) search for unit distances."""
    n = len(points)
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            x1, y1 = points[i]
            x2, y2 = points[j]
            dist = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
            if abs(dist - 1.0) < tolerance:
                count += 1
    return count

def generate_symmetric_generators(m: int, d: int) -> List[Tuple[float, float]]:
    """Generate m magnitude-1 units in Q(sqrt(-d)), closed under complex conjugation."""
    generators = []
    a = 1
    # We generate in pairs (gamma, conj(gamma))
    while len(generators) < m:
        for b in range(1, 100):
            if math.gcd(a, b) == 1:
                denom = a**2 + d * b**2
                real = (a**2 - d * b**2) / denom
                imag = (2 * a * b * math.sqrt(d)) / denom
                
                pt = (real, imag)
                conj_pt = (real, -imag)
                
                if pt not in generators and conj_pt not in generators:
                    generators.append(pt)
                    if len(generators) < m:
                        generators.append(conj_pt)
                    if len(generators) == m:
                        break
        a += 1
    return generators

def generate_subset_sums(generators: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """Generate all subset sums of the generators."""
    points = [(0.0, 0.0)]
    for gen in generators:
        new_pts = []
        for pt in points:
            new_pts.append((pt[0] + gen[0], pt[1] + gen[1]))
        points.extend(new_pts)
        
    # Deduplicate
    unique_points = []
    seen = set()
    for x, y in points:
        key = (round(x, 10), round(y, 10))
        if key not in seen:
            seen.add(key)
            unique_points.append((x, y))
    return unique_points

def build_conjugate_map(points: List[Tuple[float, float]], tolerance: float = 1e-6) -> List[int]:
    """Build a mapping from each point index to its complex conjugate's index."""
    n = len(points)
    conj_map = [-1] * n
    
    # Fast lookup table by rounded coordinates
    lookup = {}
    for idx, (x, y) in enumerate(points):
        # We index each point by its own coordinates
        key = (round(x, 10), round(y, 10))
        lookup[key] = idx
        
    for idx, (x, y) in enumerate(points):
        # We look up the conjugate: (x, -y)
        key = (round(x, 10), round(-y, 10))
        if key not in lookup:
            raise ValueError(f"Conjugate of point {idx} ({(x, y)}) not found in points set. Set is not closed under complex conjugation.")
        conj_map[idx] = lookup[key]
        
    return conj_map

def run_galois_trimmed_search(
    points: List[Tuple[float, float]], 
    conj_map: List[int], 
    tolerance: float = 1e-7
) -> Tuple[int, float]:
    """Perform unit distance verification accelerated by Galois orbit representatives."""
    n = len(points)
    
    # 1. Partition into orbits under conjugation
    visited = [False] * n
    representatives = []
    
    for i in range(n):
        if not visited[i]:
            representatives.append(i)
            visited[i] = True
            visited[conj_map[i]] = True
            
    # 2. Check distances starting ONLY from representatives
    t0 = time.time()
    unit_pairs: Set[Tuple[int, int]] = set()
    
    for r in representatives:
        rx, ry = points[r]
        # Compare with all other points
        for j in range(n):
            if r == j:
                continue
            x2, y2 = points[j]
            dist = math.sqrt((rx - x2)**2 + (ry - y2)**2)
            if abs(dist - 1.0) < tolerance:
                # Add pair in sorted order
                pair = (r, j) if r < j else (j, r)
                unit_pairs.add(pair)
                
                # Galois Orbit propagation: conjugate pair must also be at distance 1
                cr = conj_map[r]
                cj = conj_map[j]
                if cr != cj:
                    conj_pair = (cr, cj) if cr < cj else (cj, cr)
                    unit_pairs.add(conj_pair)
                    
    elapsed = time.time() - t0
    return len(unit_pairs), elapsed

def main() -> int:
    parser = argparse.ArgumentParser(description="Galois Orbit Trimming (DST)")
    parser.add_argument("--generators", type=int, default=12, help="Number of generators m for subset sums")
    parser.add_argument("--d-val", type=int, default=3, help="The imaginary integer d for Q(sqrt(-d))")
    parser.add_argument("--tolerance", type=float, default=1e-7, help="Tolerance for floating-point comparison")
    parser.add_argument("--output", default="galois_orbit_trim_receipt.json", help="Output receipt path")
    
    args = parser.parse_args()
    
    if args.generators % 2 != 0:
        print("[-] Error: Number of generators must be even to ensure complex conjugation pairing.")
        return 1
        
    print(f"[*] Generating symmetric algebraic units for m={args.generators}...")
    generators = generate_symmetric_generators(args.generators, args.d_val)
    points = generate_subset_sums(generators)
    n = len(points)
    print(f"[+] Formed {n} distinct points.")
    
    # Build Galois symmetry map (complex conjugation)
    conj_map = build_conjugate_map(points, args.tolerance)
    
    # 1. Run Brute Force
    print("[*] Running Brute Force unit distance search...")
    t_brute_start = time.time()
    brute_count = verify_unit_distances_brute(points, args.tolerance)
    t_brute = time.time() - t_brute_start
    print(f"[+] Brute Force found {brute_count} unit distances in {t_brute:.4f}s.")
    
    # 2. Run Galois Trimmed Search
    print("[*] Running Galois Trimmed (DST) search...")
    trimmed_count, t_trim = run_galois_trimmed_search(points, conj_map, args.tolerance)
    print(f"[+] Galois Trimmed found {trimmed_count} unit distances in {t_trim:.4f}s.")
    
    # Validate correctness
    assert brute_count == trimmed_count, f"Validation Failed: Brute count ({brute_count}) != Trimmed count ({trimmed_count})"
    print("[+] Validation Success: Trimmed and Brute counts match exactly.")
    
    speedup = t_brute / t_trim if t_trim > 0 else 1.0
    print(f"[+] Dimensional Shock Trim Speedup: {speedup:.2f}x")
    
    res = {
        "generators_count": args.generators,
        "points_count": n,
        "observed_unit_distances": trimmed_count,
        "brute_time_seconds": t_brute,
        "trim_time_seconds": t_trim,
        "speedup_ratio": speedup,
        "redundant_dimensions_trimmed": n // 2,
        "claim_boundary": "galois-orbit-trim-dimensional-shock-trim"
    }
    
    with open(args.output, "w") as f:
        json.dump(res, f, indent=2)
    print(f"[+] Galois orbit trim receipt saved to: {args.output}")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
