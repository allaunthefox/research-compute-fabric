#!/usr/bin/env python3
"""
Manifold Basis Optimizer v3 — Fast Statistical Context Model

Pre-computes data statistics once. Only the basis mixing weights evolve.
Uses a simple but effective model: for each context (prev byte),
learn empirical frequencies, then blend with basis-weighted prior.
"""

import sys
import random
import math
from typing import List, Tuple
import numpy as np


BASIS_SIZE = 16
POPULATION = 128
GENERATIONS = 100
MUTATION = 0.1
CROSSOVER = 0.8
ELITE = 0.15


def build_stats(data: bytes):
    """Build order-1 frequency tables from data."""
    # counts[context][next_byte]
    counts = np.zeros((256, 256), dtype=np.float64)
    prev = 0
    for b in data:
        counts[prev][b] += 1.0
        prev = b
    # Add small prior to avoid zeros
    counts += 0.1
    return counts


def evaluate_basis(basis: bytes, counts: np.ndarray, test_data: bytes) -> float:
    """
    Fast evaluation: blend empirical frequencies with basis prior.
    For each context, the predicted probability is:
        p(byte | context) = (count[context][byte] + w * basis_prior[byte]) / norm
    where w is a weight derived from the basis.
    """
    # Build basis prior: each basis byte votes for nearby values
    prior = np.ones(256, dtype=np.float64) * 0.1
    for b in basis:
        prior[b] += 1.0
        # Also boost neighbors (smooth prior)
        prior[(b + 1) & 0xFF] += 0.3
        prior[(b - 1) & 0xFF] += 0.3
    prior /= prior.sum()

    # Weight for blending
    w = 2.0  # Fixed blend weight

    total_bits = 0.0
    n = 0
    prev = test_data[0] if len(test_data) > 0 else 0

    for i in range(1, len(test_data)):
        ctx = prev
        actual = test_data[i]

        # Blend empirical counts with basis prior
        probs = counts[ctx] + w * prior
        probs /= probs.sum()

        p = probs[actual]
        if p < 1e-12:
            p = 1e-12
        total_bits += -math.log2(p)
        n += 1
        prev = actual

    return total_bits / max(1, n)


def random_basis() -> bytes:
    return bytes(random.randint(0, 255) for _ in range(BASIS_SIZE))


def mutate_basis(basis: bytes) -> bytes:
    ba = bytearray(basis)
    for i in range(len(ba)):
        if random.random() < MUTATION:
            ba[i] = random.randint(0, 255)
    return bytes(ba)


def crossover(a: bytes, b: bytes) -> Tuple[bytes, bytes]:
    if random.random() > CROSSOVER:
        return a, b
    pt = random.randint(1, BASIS_SIZE - 1)
    return a[:pt] + b[pt:], b[:pt] + a[pt:]


def optimize(data: bytes):
    # Precompute stats on training half
    split = len(data) // 2
    train = data[:split]
    test = data[split:]
    counts = build_stats(train)

    print(f"Data: {len(data)} bytes | Train: {len(train)} | Test: {len(test)}")
    print(f"Pop: {POPULATION}, Gens: {GENERATIONS}")
    print("-" * 60)

    # Seed population with heuristics
    pop = [random_basis() for _ in range(POPULATION)]
    freq = np.zeros(256, dtype=np.int64)
    for b in train:
        freq[b] += 1
    top = np.argsort(freq)[-BASIS_SIZE:]
    pop[0] = bytes(int(top[i]) for i in range(BASIS_SIZE))
    pop[1] = bytes(i * 17 for i in range(BASIS_SIZE))

    best_basis = pop[0]
    best_score = evaluate_basis(best_basis, counts, test)

    for gen in range(GENERATIONS):
        scores = []
        for basis in pop:
            s = evaluate_basis(basis, counts, test)
            scores.append((s, basis))
            if s < best_score:
                best_score = s
                best_basis = basis

        scores.sort(key=lambda x: x[0])
        avg = sum(s[0] for s in scores) / len(scores)

        if gen % 10 == 0 or gen == GENERATIONS - 1:
            print(f"Gen {gen:>3}: best={scores[0][0]:.4f} avg={avg:.4f} worst={scores[-1][0]:.4f}")

        # Elite + offspring
        elite_n = max(2, int(POPULATION * ELITE))
        new_pop = [scores[i][1] for i in range(elite_n)]

        while len(new_pop) < POPULATION:
            i1 = random.randint(0, len(scores) // 3)
            i2 = random.randint(0, len(scores) // 3)
            c1, c2 = crossover(scores[i1][1], scores[i2][1])
            new_pop.append(mutate_basis(c1))
            if len(new_pop) < POPULATION:
                new_pop.append(mutate_basis(c2))

        pop = new_pop

    print("-" * 60)
    print(f"Best entropy: {best_score:.4f} bits/byte")
    print(f"Best basis:   {best_basis.hex()}")
    print(f"Bytes:        {list(best_basis)}")
    print()
    print(f"Uniform baseline:  8.0000 bits/byte")
    print(f"Optimized:         {best_score:.4f} bits/byte")
    print(f"Gain:              {8.0 - best_score:.4f} bits/byte ({(8.0 - best_score)/8.0*100:.1f}%)")

    with open('optimized_basis_v3.bin', 'wb') as f:
        f.write(best_basis)
    print("Wrote optimized_basis_v3.bin")


def main():
    if len(sys.argv) < 2:
        print("Usage: python manifold_basis_optimizer_v3.py <file>  or  --synthetic")
        sys.exit(1)

    if sys.argv[1] == '--synthetic':
        print("Generating synthetic data...")
        np.random.seed(42)
        text = b"The quick brown fox jumps over the lazy dog. " * 1500
        pat = bytes([i % 256 for i in range(128)]) * 800
        noise = bytes(np.random.randint(0, 256, size=80000))
        d = bytearray(text + pat + noise)
        random.shuffle(d)
        data = bytes(d)
    else:
        with open(sys.argv[1], 'rb') as f:
            data = f.read(300000)
        print(f"Loaded {len(data)} bytes from {sys.argv[1]}")

    optimize(data)


if __name__ == "__main__":
    main()
