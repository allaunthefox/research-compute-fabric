#!/usr/bin/env python3
"""
Manifold Basis Optimizer v2 — Statistical Context Model

Learns from data statistics, not deterministic hashes.
Uses order-1 context (previous byte) to build empirical frequency tables.
Searches for the 16-byte basis that maximizes prediction accuracy.

Architecture: Landauer reversibility + Shannon entropy + Jaynes maxent
"""

import sys
import struct
import random
import math
from typing import List, Tuple
import numpy as np


# ─── Configuration ───
BASIS_SIZE = 16       # Holographic boundary
CONTEXT_ORDER = 1     # Use previous 1 byte as context
POPULATION_SIZE = 128
GENERATIONS = 300
MUTATION_RATE = 0.08
CROSSOVER_RATE = 0.8
ELITE_FRACTION = 0.15

SAMPLE_BYTES = 200000  # More data for statistical learning
MAX_CONTEXTS = 256     # One frequency table per previous byte value


class StatisticalPredictor:
    """
    Order-1 context model with basis-weighted mixing.
    For each context (previous byte), learns empirical frequencies
    of next bytes, weighted by the basis.
    """
    def __init__(self, basis: bytes):
        self.basis = basis
        # frequency[context][next_byte] = count
        self.freq = np.ones((MAX_CONTEXTS, 256), dtype=np.float64)
        # Total counts per context
        self.totals = np.ones(MAX_CONTEXTS, dtype=np.float64) * 256.0
        self.seen = 0

    def predict(self, context: int) -> Tuple[np.ndarray, float]:
        """
        Returns probability distribution over next bytes given context.
        Also returns estimated entropy of this distribution.
        """
        counts = self.freq[context]
        total = self.totals[context]
        probs = counts / total

        # Entropy of this distribution
        ent = 0.0
        for p in probs:
            if p > 1e-10:
                ent -= p * math.log2(p)

        return probs, ent

    def update(self, context: int, actual: int, weight: float = 1.0):
        """Update frequency table after seeing actual byte."""
        self.freq[context][actual] += weight
        self.totals[context] += weight
        self.seen += 1

    def train(self, data: bytes):
        """Build frequency tables from data."""
        prev = 0
        for i, byte in enumerate(data):
            self.update(prev, byte)
            # Mix in basis influence: basis bytes act as "virtual observations"
            b = self.basis[i % BASIS_SIZE]
            self.update(prev, b, weight=0.5)
            prev = byte

    def evaluate(self, data: bytes) -> float:
        """
        Evaluate predictor on held-out data.
        Returns average bits per byte (cross-entropy).
        """
        total_bits = 0.0
        prev = data[0] if len(data) > 0 else 0

        # Train on first half, test on second half
        split = len(data) // 2
        self.train(data[:split])

        prev = data[split] if split < len(data) else 0
        for i in range(split + 1, len(data)):
            probs, _ = self.predict(prev)
            actual = data[i]
            p = probs[actual]
            if p < 1e-10:
                p = 1e-10
            total_bits += -math.log2(p)
            prev = actual

        return total_bits / max(1, len(data) - split - 1)


def random_basis() -> bytes:
    return bytes(random.randint(0, 255) for _ in range(BASIS_SIZE))


def mutate_basis(basis: bytes, rate: float = MUTATION_RATE) -> bytes:
    ba = bytearray(basis)
    for i in range(len(ba)):
        if random.random() < rate:
            # Gaussian mutation around current value
            delta = int(random.gauss(0, 32))
            ba[i] = (ba[i] + delta) & 0xFF
    return bytes(ba)


def crossover_basis(a: bytes, b: bytes) -> Tuple[bytes, bytes]:
    if random.random() > CROSSOVER_RATE:
        return a, b
    point = random.randint(1, BASIS_SIZE - 1)
    # Blend rather than single-point: weighted average
    alpha = random.random()
    c1 = bytes(int((1-alpha)*x + alpha*y) & 0xFF for x, y in zip(a, b))
    c2 = bytes(int(alpha*x + (1-alpha)*y) & 0xFF for x, y in zip(a, b))
    return c1, c2


def optimize_basis(data: bytes) -> Tuple[bytes, float]:
    population = [random_basis() for _ in range(POPULATION_SIZE)]

    # Heuristic seeds
    freq = np.zeros(256, dtype=np.int64)
    for b in data[:50000]:
        freq[b] += 1
    top_bytes = np.argsort(freq)[-BASIS_SIZE:]
    population[0] = bytes(int(top_bytes[i]) for i in range(BASIS_SIZE))
    population[1] = bytes(b ^ 0xFF for b in population[0])  # complement
    population[2] = bytes(i * 17 for i in range(BASIS_SIZE))

    best_basis = None
    best_entropy = float('inf')

    print(f"Optimizing basis on {len(data)} bytes...")
    print(f"Population: {POPULATION_SIZE}, Generations: {GENERATIONS}")
    print("-" * 70)

    for gen in range(GENERATIONS):
        scores = []
        for basis in population:
            pred = StatisticalPredictor(basis)
            try:
                e = pred.evaluate(data)
            except Exception as ex:
                e = 10.0  # penalty for failure
            scores.append((e, basis))
            if e < best_entropy:
                best_entropy = e
                best_basis = basis

        scores.sort(key=lambda x: x[0])
        avg_e = sum(s[0] for s in scores) / len(scores)

        if gen % 30 == 0 or gen == GENERATIONS - 1:
            print(f"Gen {gen:>3}: best={scores[0][0]:.4f}  avg={avg_e:.4f}  "
                  f"worst={scores[-1][0]:.4f}")

        # Elite preservation
        elite_count = max(2, int(POPULATION_SIZE * ELITE_FRACTION))
        new_pop = [scores[i][1] for i in range(elite_count)]

        while len(new_pop) < POPULATION_SIZE:
            idx1 = random.randint(0, len(scores) // 3)
            idx2 = random.randint(0, len(scores) // 3)
            parent1 = scores[idx1][1]
            parent2 = scores[idx2][1]

            c1, c2 = crossover_basis(parent1, parent2)
            c1 = mutate_basis(c1)
            c2 = mutate_basis(c2)

            new_pop.append(c1)
            if len(new_pop) < POPULATION_SIZE:
                new_pop.append(c2)

        population = new_pop

    print("-" * 70)
    print(f"Best basis found (entropy = {best_entropy:.4f} bits/byte):")
    print(best_basis.hex())
    print(f"Basis bytes: {list(best_basis)}")

    return best_basis, best_entropy


def main():
    if len(sys.argv) < 2:
        print("Usage: python manifold_basis_optimizer_v2.py <data_file>")
        print("  Or:  python manifold_basis_optimizer_v2.py --synthetic")
        sys.exit(1)

    if sys.argv[1] == '--synthetic':
        print("Generating synthetic test data...")
        np.random.seed(42)
        text = b"The quick brown fox jumps over the lazy dog. " * 800
        pattern = bytes([i % 256 for i in range(128)]) * 400
        noise = bytes(np.random.randint(0, 256, size=50000))
        data = bytearray(text + pattern + noise)
        random.shuffle(data)
        data = bytes(data)
    else:
        with open(sys.argv[1], 'rb') as f:
            data = f.read(SAMPLE_BYTES)
        print(f"Loaded {len(data)} bytes from {sys.argv[1]}")

    best_basis, best_entropy = optimize_basis(data)

    # Baseline: uniform prediction (8 bits/byte)
    print()
    print(f"Uniform baseline:          8.0000 bits/byte")
    print(f"Optimized basis entropy:     {best_entropy:.4f} bits/byte")
    print(f"Improvement:                 {8.0 - best_entropy:.4f} bits/byte")
    print(f"Relative gain:               {(8.0 - best_entropy) / 8.0 * 100:.1f}%")

    with open('optimized_basis_v2.bin', 'wb') as f:
        f.write(best_basis)
    print()
    print("Wrote optimized_basis_v2.bin")


if __name__ == "__main__":
    main()
