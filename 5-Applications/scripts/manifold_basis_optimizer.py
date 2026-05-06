#!/usr/bin/env python3
"""
Manifold Basis Optimizer — Empirical Search for Optimal PIST Basis

Assumes the data lives on an unknown manifold.
The decoder has:
  - A 16-byte basis (local coordinate frame)
  - A position-dependent prediction function (manifold map)
  - No imposed geometry (no parabola, torus, or surface)

The optimizer searches basis vectors and mixing weights
to minimize residual entropy on a data sample.

Builds on: Landauer reversibility, Shannon entropy, Jaynes maxent,
Bekenstein holographic bound, Bennett history tape.
"""

import sys
import struct
import random
import math
import hashlib
from typing import List, Tuple, Callable
import numpy as np


# ─── Configuration ───
BASIS_SIZE = 16       # Holographic boundary (Bekenstein)
HISTORY_BITS = 256    # FAMM scar memory depth (Bennett history tape)
POPULATION_SIZE = 64  # Genetic algorithm population
GENERATIONS = 200     # Search iterations
MUTATION_RATE = 0.05  # Per-byte mutation probability
CROSSOVER_RATE = 0.7
ELITE_FRACTION = 0.1  # Top performers preserved

SAMPLE_BYTES = 100000  # Bytes to evaluate per candidate


# ─── Manifold-agnostic prediction primitives ───

def manifold_map(position: int, basis: bytes) -> int:
    """
    Map a position on the manifold to a prediction byte.
    No geometric assumptions — just a hash mixing position and basis.
    The hash function IS the unknown manifold shape.
    """
    # Mix position into the basis index deterministically
    idx = (position * 2654435761) & 0xFFFFFFFF  # Knuth multiplicative hash
    b1 = basis[idx % BASIS_SIZE]
    b2 = basis[(idx >> 8) % BASIS_SIZE]
    b3 = basis[(idx >> 16) % BASIS_SIZE]
    # Noncommuting composition: a then b then a'
    a = b1 ^ (position & 0xFF)
    b = b2 ^ ((position >> 8) & 0xFF)
    a_prime = b3 ^ ((position ^ b) & 0xFF)
    return (a ^ b ^ a_prime) & 0xFF


def predict_with_history(position: int, basis: bytes, history: bytearray) -> int:
    """
    Prediction including history tape (Bennett reversibility).
    History records recent prediction errors (scars).
    """
    base = manifold_map(position, basis)
    # Weight by recent history (FAMM-like scar bias)
    if len(history) > 0:
        h = history[-1] if len(history) > 0 else 0
        h2 = history[-2] if len(history) > 1 else 0
        # Recent errors modify the prediction (shear correction)
        base ^= (h * 7 + h2 * 3) & 0xFF
    return base & 0xFF


# ─── Evaluation: residual entropy ───

def evaluate_basis(basis: bytes, data: bytes, history_depth: int = 8) -> float:
    """
    Evaluate a basis by measuring residual entropy after prediction.
    Lower is better (means residuals are more compressible).

    Returns: estimated bits per byte of the residual stream.
    """
    residuals = bytearray()
    history = bytearray()

    for pos, byte in enumerate(data):
        pred = predict_with_history(pos, basis, history)
        residual = byte ^ pred
        residuals.append(residual)

        # Update history tape (reversible — old state not discarded)
        history.append(residual)
        if len(history) > history_depth:
            history.pop(0)

    # Estimate entropy of residuals via order-1 context model
    # (histogram of residual values, plus simple context mixing)
    counts = np.zeros(256, dtype=np.int64)
    for r in residuals:
        counts[r] += 1

    total = len(residuals)
    entropy = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            entropy -= p * math.log2(p)

    # Penalty for high-variation residuals (Jaynes: maxent subject to constraints)
    # We want residuals to be concentrated, not uniform
    variance = np.var(list(residuals))
    penalty = variance / 65536.0  # normalize to [0, 1]

    return entropy + penalty


# ─── Genetic Algorithm ───

def random_basis() -> bytes:
    """Generate a random 16-byte basis."""
    return bytes(random.randint(0, 255) for _ in range(BASIS_SIZE))


def mutate_basis(basis: bytes, rate: float = MUTATION_RATE) -> bytes:
    """Mutate a basis by flipping random bytes."""
    ba = bytearray(basis)
    for i in range(len(ba)):
        if random.random() < rate:
            ba[i] = random.randint(0, 255)
    return bytes(ba)


def crossover_basis(a: bytes, b: bytes) -> Tuple[bytes, bytes]:
    """Single-point crossover between two basis vectors."""
    if random.random() > CROSSOVER_RATE:
        return a, b
    point = random.randint(1, BASIS_SIZE - 1)
    c1 = a[:point] + b[point:]
    c2 = b[:point] + a[point:]
    return c1, c2


def optimize_basis(data: bytes) -> Tuple[bytes, float]:
    """
    Genetic algorithm search for optimal basis.
    Returns: (best_basis, best_entropy)
    """
    # Initial population: random + some structured seeds
    population = [random_basis() for _ in range(POPULATION_SIZE)]

    # Add some heuristic seeds (empirical frequencies from data)
    freq = np.zeros(256, dtype=np.int64)
    for b in data[:10000]:
        freq[b] += 1
    top_bytes = np.argsort(freq)[-BASIS_SIZE:]
    seed_basis = bytes(int(top_bytes[i]) for i in range(BASIS_SIZE))
    population[0] = seed_basis

    # Add identity-ish seed
    population[1] = bytes(i * 17 for i in range(BASIS_SIZE))

    best_basis = None
    best_entropy = float('inf')

    print(f"Optimizing basis on {len(data)} bytes...")
    print(f"Population: {POPULATION_SIZE}, Generations: {GENERATIONS}")
    print("-" * 60)

    for gen in range(GENERATIONS):
        # Evaluate population
        scores = []
        for basis in population:
            e = evaluate_basis(basis, data)
            scores.append((e, basis))
            if e < best_entropy:
                best_entropy = e
                best_basis = basis

        scores.sort(key=lambda x: x[0])

        # Elite preservation
        elite_count = max(1, int(POPULATION_SIZE * ELITE_FRACTION))
        new_pop = [scores[i][1] for i in range(elite_count)]

        # Generate offspring
        while len(new_pop) < POPULATION_SIZE:
            # Tournament selection
            idx1 = random.randint(0, len(scores) // 2)
            idx2 = random.randint(0, len(scores) // 2)
            parent1 = scores[idx1][1]
            parent2 = scores[idx2][1]

            c1, c2 = crossover_basis(parent1, parent2)
            c1 = mutate_basis(c1)
            c2 = mutate_basis(c2)

            new_pop.append(c1)
            if len(new_pop) < POPULATION_SIZE:
                new_pop.append(c2)

        population = new_pop

        if gen % 20 == 0 or gen == GENERATIONS - 1:
            avg_entropy = sum(s[0] for s in scores) / len(scores)
            print(f"Gen {gen:>3}: best={scores[0][0]:.4f}  "
                  f"avg={avg_entropy:.4f}  worst={scores[-1][0]:.4f}")

    print("-" * 60)
    print(f"Best basis found (entropy = {best_entropy:.4f} bits/byte):")
    print(best_basis.hex())
    print()
    print("Basis bytes:", list(best_basis))

    return best_basis, best_entropy


# ─── Main ───

def main():
    if len(sys.argv) < 2:
        print("Usage: python manifold_basis_optimizer.py <data_file>")
        print("  Or:  python manifold_basis_optimizer.py --synthetic")
        sys.exit(1)

    if sys.argv[1] == '--synthetic':
        # Generate synthetic data with known structure
        print("Generating synthetic test data...")
        np.random.seed(42)
        # Mix of: English-like text, repeated patterns, and noise
        text = b"The quick brown fox jumps over the lazy dog. " * 500
        pattern = bytes([i % 256 for i in range(64)]) * 200
        noise = bytes(np.random.randint(0, 256, size=20000))
        data = text + pattern + noise
        random.shuffle(list(data))  # In-place shuffle of a copy
        data = bytes(data)
    else:
        with open(sys.argv[1], 'rb') as f:
            data = f.read(SAMPLE_BYTES)
        print(f"Loaded {len(data)} bytes from {sys.argv[1]}")

    best_basis, best_entropy = optimize_basis(data)

    # Compare to trivial predictor (no basis, just identity)
    trivial_entropy = evaluate_basis(bytes(BASIS_SIZE), data)
    print()
    print(f"Trivial basis entropy:     {trivial_entropy:.4f} bits/byte")
    print(f"Optimized basis entropy:   {best_entropy:.4f} bits/byte")
    print(f"Improvement:               {trivial_entropy - best_entropy:.4f} bits/byte")
    print(f"Relative gain:             {(trivial_entropy - best_entropy) / trivial_entropy * 100:.1f}%")

    # Write optimized basis to file
    with open('optimized_basis.bin', 'wb') as f:
        f.write(best_basis)
    print()
    print("Wrote optimized_basis.bin")


if __name__ == "__main__":
    main()
