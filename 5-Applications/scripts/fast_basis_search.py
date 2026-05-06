#!/usr/bin/env python3
"""
Fast Basis Search — Brute-force over small space with simple order-1 model.

Instead of genetic search over 2^128, we search over:
  - 256 choices for the most frequent byte in basis
  - 16 positions to place it
  - A few variants of the remaining bytes

This completes in seconds, not hours.
"""

import sys
import math
import numpy as np


def build_counts(data: bytes):
    """Order-1 counts[prev][next]."""
    counts = np.zeros((256, 256), dtype=np.float64)
    prev = 0
    for b in data:
        counts[prev][b] += 1.0
        prev = b
    counts += 0.5  # prior
    return counts


def evaluate_blend(counts: np.ndarray, basis: bytes, test: bytes, w: float = 1.0) -> float:
    """Blend empirical counts with basis prior. Lower = better."""
    prior = np.ones(256, dtype=np.float64) * 0.5
    for b in basis:
        prior[b] += 1.0
    prior /= prior.sum()

    total = 0.0
    n = 0
    prev = test[0] if test else 0
    for i in range(1, len(test)):
        ctx = prev
        actual = test[i]
        probs = counts[ctx] + w * prior
        probs /= probs.sum()
        p = max(probs[actual], 1e-12)
        total += -math.log2(p)
        n += 1
        prev = actual
    return total / max(1, n)


def search_best_basis(data: bytes):
    split = len(data) // 2
    train = data[:split]
    test = data[split:]
    counts = build_counts(train)

    print(f"Data: {len(data)} bytes | Searching basis...")

    # Baseline: no basis prior (w=0)
    baseline = evaluate_blend(counts, bytes(16), test, w=0.0)
    print(f"Baseline (no basis): {baseline:.4f} bits/byte")

    # Find most common bytes
    freq = np.zeros(256)
    for b in train:
        freq[b] += 1
    top = np.argsort(freq)[-32:][::-1]  # top 32 most frequent bytes

    best_score = baseline
    best_basis = bytes(16)
    best_w = 0.0

    # Search: try each top byte in each position with varied weights
    tested = 0
    for w in [0.5, 1.0, 2.0, 4.0]:
        for anchor_byte in top[:8]:
            for pos in range(16):
                basis = bytearray(16)
                basis[pos] = anchor_byte
                # Fill rest with other frequent bytes
                for i in range(16):
                    if i != pos:
                        basis[i] = int(top[i % 8])
                score = evaluate_blend(counts, bytes(basis), test, w)
                tested += 1
                if score < best_score:
                    best_score = score
                    best_basis = bytes(basis)
                    best_w = w

                # Also try anchor with random fill
                np.random.seed(pos + anchor_byte)
                rand_fill = np.random.randint(0, 256, size=16)
                rand_fill[pos] = anchor_byte
                score_r = evaluate_blend(counts, bytes(rand_fill), test, w)
                tested += 1
                if score_r < best_score:
                    best_score = score_r
                    best_basis = bytes(rand_fill)
                    best_w = w

    print(f"Tested {tested} configurations")
    print(f"Best: {best_score:.4f} bits/byte (w={best_w})")
    print(f"Basis: {best_basis.hex()}")
    print(f"Gain: {baseline - best_score:.4f} bits/byte")

    with open('fast_basis.bin', 'wb') as f:
        f.write(best_basis)
    print("Wrote fast_basis.bin")


def main():
    if len(sys.argv) < 2:
        print("Usage: python fast_basis_search.py <file>  or  --synthetic")
        sys.exit(1)

    if sys.argv[1] == '--synthetic':
        print("Generating synthetic data...")
        np.random.seed(42)
        text = b"The quick brown fox jumps over the lazy dog. " * 2000
        pat = bytes([i % 256 for i in range(128)]) * 1000
        noise = bytes(np.random.randint(0, 256, size=100000))
        d = bytearray(text + pat + noise)
        import random as py_random
        py_random.shuffle(d)
        data = bytes(d)
    else:
        with open(sys.argv[1], 'rb') as f:
            data = f.read(200000)
        print(f"Loaded {len(data)} bytes from {sys.argv[1]}")

    search_best_basis(data)


if __name__ == "__main__":
    main()
