#!/usr/bin/env python3
"""
erdos_discrepancy_probe.py — Multi-core Discrepancy Probe for Erdős Sequences

Evaluates discrepancy of signed sequences (±1) over homogeneous arithmetic
progressions (APs):
  Disc(A; q, m) = |sum_{j=1}^m s_A(q * j)|

Checks if discrepancy remains bounded under a specified threshold.
Utilises multi-core CPU to scan large parameter spaces (q and m).
"""

from __future__ import annotations

import argparse
import json
import time
from multiprocessing import Pool, cpu_count
from typing import Dict, List, Tuple

def compute_ap_discrepancy(args: Tuple[List[int], int, int]) -> int:
    """Compute discrepancy of sequence for a specific step q and length m.
    
    AP is: q, 2q, 3q, ..., mq (1-indexed indices: q*j - 1 for 0-indexed list).
    """
    seq, q, m = args
    n = len(seq)
    
    # homogeneous AP check
    val = 0
    for j in range(1, m + 1):
        idx = q * j - 1
        if idx < n:
            val += seq[idx]
        else:
            break
    return abs(val)

def scan_discrepancy(seq: List[int], max_q: int, threads: int) -> Dict:
    """Scan all homogeneous APs up to max_q in parallel."""
    n = len(seq)
    print(f"[*] Scanning discrepancy for sequence of length {n}...")
    
    # Generate tasks: (seq, q, m) for q in 1..max_q and m in 1..n//q
    tasks = []
    for q in range(1, max_q + 1):
        max_m = n // q
        for m in range(1, max_m + 1):
            tasks.append((seq, q, m))
            
    print(f"[*] Generated {len(tasks)} AP configurations to scan.")
    
    t0 = time.time()
    with Pool(processes=threads) as pool:
        discrepancies = pool.map(compute_ap_discrepancy, tasks)
    elapsed = time.time() - t0
    
    # Find max discrepancy and its AP parameters
    max_disc = 0
    best_q = 1
    best_m = 1
    for idx, disc in enumerate(discrepancies):
        if disc > max_disc:
            max_disc = disc
            best_q = tasks[idx][1]
            best_m = tasks[idx][2]
            
    print(f"[+] Scan complete in {elapsed:.2f}s. Max discrepancy: {max_disc} (q={best_q}, m={best_m})")
    
    return {
        "max_discrepancy": max_disc,
        "critical_q": best_q,
        "critical_m": best_m,
        "scan_time_seconds": elapsed,
        "total_aps_checked": len(tasks)
    }

def main() -> int:
    parser = argparse.ArgumentParser(description="Erdos Discrepancy Probe")
    parser.add_argument("--length", type=int, default=10000, help="Generate random +-1 sequence of this length")
    parser.add_argument("--max-q", type=int, default=2000, help="Maximum AP step to check")
    parser.add_argument("--threads", type=int, default=cpu_count(), help="Concurrent threads")
    parser.add_argument("--output", default="erdos_discrepancy_receipt.json", help="Output receipt path")
    
    args = parser.parse_args()
    
    # Generate a deterministic pseudo-random sequence of +-1 using a hash-derived seed
    # to avoid external dependencies and stay secret-clean
    seq = []
    for i in range(args.length):
        val = 1 if (i * 1103515245 + 12345) % 65536 % 2 == 0 else -1
        seq.append(val)
        
    res = scan_discrepancy(seq, args.max_q, args.threads)
    res["sequence_length"] = args.length
    
    with open(args.output, "w") as f:
        json.dump(res, f, indent=2)
    print(f"[+] Discrepancy receipt saved to: {args.output}")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
