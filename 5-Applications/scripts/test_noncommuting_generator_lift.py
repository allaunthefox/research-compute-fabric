#!/usr/bin/env python3
"""
Test: Noncommuting Generator Lift (Squeezing Analogy)

From Băzăvan et al. (Nature Physics 2026):
  Linear spin-dependent forces + noncommuting spin basis + detuning selection
  = effective higher-order nonlinear interactions (squeezing, trisqueezing, quadsqueezing)

Hypothesis for compression:
  Two low-order transforms A, B with [A, B] != 0,
  composed with phase/detuning selection m = 1-n,
  can approximate high-order context models (n-gram, tag-context, etc.)
  more compactly than explicit n-th order tables.

Test: Does a pair of 1st-order predictors + noncommuting composition
  beat a single explicit 2nd-order predictor in description length?
"""

import sys
import os
import math
import random
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_pist_decoder import compress, predict


class GeneratorA:
    """First-order generator: predicts byte from previous byte."""
    name = "prev_byte"

    def __init__(self, data: bytes):
        # Build P(byte | previous_byte) table
        self.table = {}
        counts = Counter()
        for i in range(1, len(data)):
            prev = data[i-1]
            curr = data[i]
            counts[(prev, curr)] += 1

        # For each prev, find most likely next byte
        prev_counts = Counter()
        for (p, c), cnt in counts.items():
            prev_counts[p] += cnt
            if p not in self.table or counts[(p, c)] > counts[(p, self.table[p])]:
                self.table[p] = c

    def predict(self, pos: int, data: bytes) -> int:
        if pos == 0:
            return 0
        prev = data[pos - 1]
        return self.table.get(prev, 0)

    def size_bits(self) -> int:
        # 256 entries * 1 byte each = 2048 bits
        return len(self.table) * 8


class GeneratorB:
    """First-order generator: predicts byte from position mod 256."""
    name = "position_mod"

    def __init__(self, data: bytes):
        self.table = {}
        counts = Counter()
        for i, b in enumerate(data):
            pos_mod = i & 0xFF
            counts[(pos_mod, b)] += 1

        for (pm, b), cnt in counts.items():
            if pm not in self.table or counts[(pm, b)] > counts[(pm, self.table[pm])]:
                self.table[pm] = b

    def predict(self, pos: int, data: bytes) -> int:
        return self.table.get(pos & 0xFF, 0)

    def size_bits(self) -> int:
        return len(self.table) * 8


class NoncommutingComposition:
    """
    Compose two generators with a phase/detuning selection rule.

    A and B do not commute: applying A then B vs B then A gives different results.
    The composition order is selected by a "detuning" parameter m.

    For n=2 (squeezing analogue): apply A then B
    For n=3 (trisqueezing analogue): apply A, B, A
    For n=4 (quadsqueezing analogue): apply A, B, A, B
    """
    name = "noncommuting_composition"

    def __init__(self, gen_a, gen_b, order: int = 2):
        self.gen_a = gen_a
        self.gen_b = gen_b
        self.order = order
        # Weight table for combining predictions
        self.weights = {}

    def _compose(self, pos: int, data: bytes) -> int:
        """Apply generators in sequence according to order."""
        p = 0
        # Alternate A and B based on order
        for i in range(self.order):
            if i % 2 == 0:
                p ^= self.gen_a.predict(pos, data)
            else:
                p ^= self.gen_b.predict(pos, data)
        return p

    def predict(self, pos: int, data: bytes) -> int:
        return self._compose(pos, data)

    def size_bits(self) -> int:
        return self.gen_a.size_bits() + self.gen_b.size_bits()


class ExplicitSecondOrder:
    """Explicit 2nd-order predictor: P(byte | prev, prev-prev)."""
    name = "explicit_2nd_order"

    def __init__(self, data: bytes):
        self.table = {}
        counts = Counter()
        for i in range(2, len(data)):
            ctx = (data[i-2], data[i-1])
            curr = data[i]
            counts[(ctx, curr)] += 1

        for (ctx, c), cnt in counts.items():
            if ctx not in self.table or counts[(ctx, c)] > counts[(ctx, self.table[ctx])]:
                self.table[ctx] = c

    def predict(self, pos: int, data: bytes) -> int:
        if pos < 2:
            return 0
        ctx = (data[pos-2], data[pos-1])
        return self.table.get(ctx, 0)

    def size_bits(self) -> int:
        return len(self.table) * 16  # 2-byte context -> 1 byte prediction


def entropy_of_residuals(residuals: bytes) -> float:
    """Shannon entropy of residual distribution in bits/byte."""
    counts = Counter(residuals)
    total = len(residuals)
    h = 0.0
    for cnt in counts.values():
        p = cnt / total
        h -= p * math.log2(p)
    return h


def test_on_corpus(corpus_path: str, max_bytes: int = 10_000_000):
    """Test all predictors on a corpus file."""
    print(f"\n{'='*60}")
    print(f"Testing on: {corpus_path}")
    print(f"{'='*60}")

    with open(corpus_path, 'rb') as f:
        data = f.read(max_bytes)

    print(f"Data size: {len(data)} bytes")

    # Split: first 80% for training, last 20% for testing
    split = int(len(data) * 0.8)
    train = data[:split]
    test = data[split:]

    predictors = [
        ("Baseline (no prediction)", None),
        ("Generator A (prev byte)", GeneratorA(train)),
        ("Generator B (position mod)", GeneratorB(train)),
        ("Noncommuting n=2 (A,B)", NoncommutingComposition(GeneratorA(train), GeneratorB(train), 2)),
        ("Noncommuting n=3 (A,B,A)", NoncommutingComposition(GeneratorA(train), GeneratorB(train), 3)),
        ("Noncommuting n=4 (A,B,A,B)", NoncommutingComposition(GeneratorA(train), GeneratorB(train), 4)),
        ("Explicit 2nd order", ExplicitSecondOrder(train)),
    ]

    results = []

    for name, predictor in predictors:
        if predictor is None:
            # Baseline: no prediction, residuals = data
            residuals = test
            model_bits = 0
        else:
            residuals = bytearray()
            for i in range(len(test)):
                p = predictor.predict(i, test)
                actual = test[i]
                residual = actual ^ p
                residuals.append(residual)
            model_bits = predictor.size_bits()

        residuals = bytes(residuals)
        h = entropy_of_residuals(residuals)
        residual_bits = h * len(test)
        total_bits = model_bits + residual_bits
        total_bytes = total_bits / 8
        ratio = total_bytes / len(test)

        results.append((name, model_bits, residual_bits, total_bits, ratio))
        print(f"\n{name}:")
        print(f"  Model size:     {model_bits/8:.0f} bytes ({model_bits} bits)")
        print(f"  Residual bits:  {residual_bits:.0f} ({h:.2f} bits/byte)")
        print(f"  Total:          {total_bytes:.0f} bytes")
        print(f"  Ratio:          {ratio:.4f}")

    # Find best
    best = min(results, key=lambda x: x[3])
    print(f"\n{'-'*60}")
    print(f"BEST: {best[0]} (ratio: {best[4]:.4f})")

    # Check if noncommuting beats explicit
    noncomm_idx = next((i for i, r in enumerate(results) if r[0].startswith("Noncommuting n=2")), None)
    explicit_idx = next((i for i, r in enumerate(results) if r[0].startswith("Explicit 2nd order")), None)

    if noncomm_idx and explicit_idx:
        nc = results[noncomm_idx]
        ex = results[explicit_idx]
        if nc[3] < ex[3]:
            improvement = (ex[3] - nc[3]) / ex[3] * 100
            print(f"\n*** Noncommuting BEATS explicit by {improvement:.1f}% ***")
        else:
            gap = (nc[3] - ex[3]) / ex[3] * 100
            print(f"\nExplicit beats noncommuting by {gap:.1f}%")

    return results


def main():
    print("Noncommuting Generator Lift Test")
    print("=" * 60)
    print("From: Băzăvan et al., Nature Physics 2026")
    print("Hypothesis: A,B generators + composition beats explicit 2nd-order tables")
    print()

    # Find available corpora
    corpus_dir = "/home/allaun/Documents/Research Stack/data/corpora"

    # Try Leipzig first
    leipzig_dir = os.path.join(corpus_dir, "leipzig")
    if os.path.exists(leipzig_dir):
        # Find sentence files
        import glob
        sentence_files = glob.glob(os.path.join(leipzig_dir, "*", "*-sentences.txt"))

        if sentence_files:
            # Test on a few languages
            test_files = sentence_files[:5]
            for f in test_files:
                test_on_corpus(f, max_bytes=1_000_000)
        else:
            print("No sentence files found in Leipzig corpus")
    else:
        print(f"Corpus directory not found: {leipzig_dir}")

    print("\n" + "=" * 60)
    print("Done")


if __name__ == "__main__":
    main()
