#!/usr/bin/env python3
"""
Killer Criterion: Synthetic Genome Generator
Creates 5 benchmark files to test RGFlow/Manifold detection.
"""

import os
import secrets
import random
import numpy as np
from pathlib import Path
import hashlib
from mpmath import mp

# Set precision for pi and e
mp.dps = 110000 # ~110k digits

def get_pi_digits(n):
    return str(mp.pi)[2:n+2]

def get_e_digits(n):
    return str(mp.e)[2:n+2]

def bits_to_dna(bits):
    mapping = {'00': 'A', '01': 'C', '10': 'G', '11': 'T'}
    res = []
    for i in range(0, len(bits), 2):
        res.append(mapping.get(bits[i:i+2], 'A'))
    return "".join(res)

def generate_benchmarks():
    out_dir = Path("/home/allaun/Documents/Research Stack/data/benchmarks/killer_criterion")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print("Generating Benchmark A: Pure Random...")
    # A: 1,000,000 random bits -> 500,000 DNA symbols
    bits_a = "".join(random.choice('01') for _ in range(1000000))
    with open(out_dir / "A.fa", "w") as f:
        f.write(">Random_Noise\n" + bits_to_dna(bits_a))

    print("Generating Benchmark B: Pure Repetitive...")
    # B: 1,000,000 'A' symbols
    with open(out_dir / "B.fa", "w") as f:
        f.write(">Trivial_Repetition\n" + "A" * 500000)

    print("Generating Benchmark C: Random + Planted Lawful Core + Random...")
    # C: 0-200k (Random), 200k-300k (Planted), 300k-500k (Random) [Scaled from 1M to 500k DNA]
    # (Using 500k DNA symbols total to match user's 1M bits request)
    flank_random_1 = "".join(random.choice('01') for _ in range(400000))
    flank_random_2 = "".join(random.choice('01') for _ in range(400000))
    
    # Planted Core (B): Pi + e + Checksum
    pi_digits = get_pi_digits(50000)
    e_digits = get_e_digits(40000)
    core_text = pi_digits + e_digits
    checksum = hashlib.sha256(core_text.encode()).hexdigest()
    core_combined = core_text + checksum
    
    # Map core_combined (text digits) to bits
    core_bits = "".join(format(ord(c), '08b') for c in core_combined)[:200000]
    
    total_bits_c = flank_random_1 + core_bits + flank_random_2
    dna_c = bits_to_dna(total_bits_c)
    with open(out_dir / "C.fa", "w") as f:
        f.write(">Planted_Lawful_Core\n" + dna_c)

    print("Generating Benchmark D: Mutated Version of C...")
    # 10% random substitutions in the core
    dna_c_list = list(dna_c)
    core_start = 200000 // 2
    core_end = (200000 + 200000) // 2 
    # Adjust for bit-to-DNA mapping (1M bits total -> 500k DNA)
    # Flank 1: 400k bits (200k DNA)
    # Core: 200k bits (100k DNA)
    # Flank 2: 400k bits (200k DNA)
    core_dna_start = 200000
    core_dna_end = 300000
    
    for i in range(core_dna_start, core_dna_end):
        if random.random() < 0.10: # 10% mutation
            dna_c_list[i] = random.choice('ACGT')
    
    with open(out_dir / "D.fa", "w") as f:
        f.write(">Mutated_Planted_Core\n" + "".join(dna_c_list))

    print("Generating Benchmark E: Shuffled Version of C...")
    dna_e_list = list(dna_c)
    random.shuffle(dna_e_list)
    with open(out_dir / "E.fa", "w") as f:
        f.write(">Shuffled_Lawful_Core\n" + "".join(dna_e_list))

    print("All benchmarks generated in " + str(out_dir))

if __name__ == "__main__":
    generate_benchmarks()
