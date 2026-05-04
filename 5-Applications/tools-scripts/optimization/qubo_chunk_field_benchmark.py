#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
qubo_chunk_field_benchmark.py

Benchmark a solvable-but-slow dense QUBO instance against two search policies:

1. baseline simulated annealing with uniform variable proposals
2. chunk-field guided annealing that prioritizes high-energy-density chunks

This script is intentionally narrow. It does not claim to implement the full
waveprobe/phonon-graph hardware path. It tests one grounded hypothesis from the
matrix/operator thread: if we treat the QUBO surface as a field and rank chunks
by energy density, does that help a bounded stochastic solver reach the optimum
more often or earlier on a frustrating instance?
"""

from __future__ import annotations

import argparse
import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from math_harness_compat import xp, AnyArray


@dataclass
class RunStats:
    best_energy: float
    hit_optimum: bool
    first_hit_step: Optional[int]
    elapsed_s: float


def generate_dense_qubo(
    n: int,
    seed: int,
    density: float = 1.0,
    weight_scale: float = 1.0,
    bias_scale: float = 0.35,
) -> AnyArray:
    """Generate a dense frustrated symmetric QUBO matrix."""
    rng = xp.random.default_rng(seed)
    raw = rng.normal(0.0, weight_scale, size=(n, n))
    mask = rng.random((n, n)) < density
    raw *= mask
    raw = xp.triu(raw, 1)
    sym = raw + raw.T
    diag = rng.normal(0.0, bias_scale, size=n)
    xp.fill_diagonal(sym, diag)
    return sym.astype(xp.float64)


def energy(Q: AnyArray, x: AnyArray) -> float:
    return float(x @ Q @ x)


def exact_solve_qubo(Q: AnyArray, batch_size: int = 65536) -> Dict[str, object]:
    """
    Exact solver by batched brute force.
    Practical for n <= ~22 on a normal machine.
    """
    n = Q.shape[0]
    total = 1 << n
    best_energy = float("inf")
    best_state = None
    col_shifts = xp.arange(n, dtype=xp.uint64)

    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        vals = xp.arange(start, end, dtype=xp.uint64)
        bits = ((vals[:, None] >> col_shifts) & 1).astype(xp.float64)
        energies = xp.einsum("bi,ij,bj->b", bits, Q, bits, optimize=True)
        idx = int(xp.argmin(energies))
        e = float(energies[idx])
        if e < best_energy:
            best_energy = e
            best_state = bits[idx].astype(xp.int8)

    return {
        "best_energy": best_energy,
        "best_state": best_state.tolist() if best_state is not None else None,
    }


def build_chunk_index(n: int, chunk_size: int) -> List[AnyArray]:
    return [
        xp.arange(start, min(start + chunk_size, n), dtype=xp.int64)
        for start in range(0, n, chunk_size)
    ]


def chunk_static_density(Q: AnyArray, chunks: List[AnyArray]) -> AnyArray:
    scores = []
    for idxs in chunks:
        block = Q[xp.ix_(idxs, xp.arange(Q.shape[0]))]
        scores.append(float(xp.mean(block * block)))
    return xp.asarray(scores, dtype=xp.float64)


def run_baseline_sa(
    Q: AnyArray,
    optimum: float,
    steps: int,
    seed: int,
    temp_start: float,
    temp_end: float,
) -> RunStats:
    rng = xp.random.default_rng(seed)
    n = Q.shape[0]
    x = rng.integers(0, 2, size=n, dtype=xp.int8).astype(xp.float64)
    Qx = Q @ x
    current_energy = energy(Q, x)
    best_energy = current_energy
    first_hit_step = 0 if math.isclose(current_energy, optimum, abs_tol=1e-9) else None

    t0 = time.perf_counter()
    for step in range(steps):
        frac = step / max(steps - 1, 1)
        temp = temp_start * ((temp_end / temp_start) ** frac)
        i = int(rng.integers(0, n))
        d = 1.0 - 2.0 * x[i]
        delta = 2.0 * d * Qx[i] + Q[i, i]
        if delta < 0.0 or rng.random() < math.exp(-delta / max(temp, 1e-12)):
            x[i] = 1.0 - x[i]
            Qx += d * Q[:, i]
            current_energy += delta
            if current_energy < best_energy:
                best_energy = current_energy
            if first_hit_step is None and math.isclose(current_energy, optimum, abs_tol=1e-9):
                first_hit_step = step + 1
    elapsed = time.perf_counter() - t0
    return RunStats(
        best_energy=best_energy,
        hit_optimum=math.isclose(best_energy, optimum, abs_tol=1e-9),
        first_hit_step=first_hit_step,
        elapsed_s=elapsed,
    )


def run_chunk_guided_sa(
    Q: AnyArray,
    optimum: float,
    steps: int,
    seed: int,
    temp_start: float,
    temp_end: float,
    chunk_size: int,
    guided_prob: float,
    recompute_every: int,
) -> RunStats:
    rng = xp.random.default_rng(seed)
    n = Q.shape[0]
    chunks = build_chunk_index(n, chunk_size)
    static_density = chunk_static_density(Q, chunks)

    x = rng.integers(0, 2, size=n, dtype=xp.int8).astype(xp.float64)
    Qx = Q @ x
    current_energy = energy(Q, x)
    best_energy = current_energy
    first_hit_step = 0 if math.isclose(current_energy, optimum, abs_tol=1e-9) else None

    chunk_prob = xp.ones(len(chunks), dtype=xp.float64) / max(len(chunks), 1)
    t0 = time.perf_counter()
    for step in range(steps):
        if step % max(recompute_every, 1) == 0:
            local_flip_gain = xp.abs((1.0 - 2.0 * x) * Qx)
            dynamic = xp.asarray(
                [float(xp.mean(local_flip_gain[idxs])) for idxs in chunks],
                dtype=xp.float64,
            )
            chunk_score = static_density * (0.5 + dynamic)
            if xp.all(chunk_score <= 0.0):
                chunk_prob = xp.ones(len(chunks), dtype=xp.float64) / max(len(chunks), 1)
            else:
                chunk_prob = chunk_score / xp.sum(chunk_score)

        frac = step / max(steps - 1, 1)
        temp = temp_start * ((temp_end / temp_start) ** frac)

        if rng.random() < guided_prob:
            chunk_idx = int(rng.choice(len(chunks), p=chunk_prob))
            idxs = chunks[chunk_idx]
            local_flip_gain = xp.abs((1.0 - 2.0 * x[idxs]) * Qx[idxs]) + 1e-9
            var_prob = local_flip_gain / xp.sum(local_flip_gain)
            i = int(rng.choice(idxs, p=var_prob))
        else:
            i = int(rng.integers(0, n))

        d = 1.0 - 2.0 * x[i]
        delta = 2.0 * d * Qx[i] + Q[i, i]
        if delta < 0.0 or rng.random() < math.exp(-delta / max(temp, 1e-12)):
            x[i] = 1.0 - x[i]
            Qx += d * Q[:, i]
            current_energy += delta
            if current_energy < best_energy:
                best_energy = current_energy
            if first_hit_step is None and math.isclose(current_energy, optimum, abs_tol=1e-9):
                first_hit_step = step + 1
    elapsed = time.perf_counter() - t0
    return RunStats(
        best_energy=best_energy,
        hit_optimum=math.isclose(best_energy, optimum, abs_tol=1e-9),
        first_hit_step=first_hit_step,
        elapsed_s=elapsed,
    )


def summarize_runs(runs: List[RunStats], optimum: float) -> Dict[str, object]:
    hit_steps = [r.first_hit_step for r in runs if r.first_hit_step is not None]
    return {
        "trials": len(runs),
        "optimum_energy": optimum,
        "hit_rate": sum(r.hit_optimum for r in runs) / max(len(runs), 1),
        "avg_best_energy": float(xp.mean([r.best_energy for r in runs])),
        "median_best_energy": float(xp.median([r.best_energy for r in runs])),
        "avg_gap_to_optimum": float(xp.mean([r.best_energy - optimum for r in runs])),
        "median_first_hit_step": int(xp.median(hit_steps)) if hit_steps else None,
        "avg_elapsed_s": float(xp.mean([r.elapsed_s for r in runs])),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Benchmark chunk-field-guided SA on a dense QUBO")
    ap.add_argument("--n", type=int, default=20, help="QUBO variable count (exact solve grows as 2^n)")
    ap.add_argument("--seed", type=int, default=1337)
    ap.add_argument("--trials", type=int, default=48)
    ap.add_argument("--steps", type=int, default=6000)
    ap.add_argument("--chunk-size", type=int, default=4)
    ap.add_argument("--guided-prob", type=float, default=0.8)
    ap.add_argument("--recompute-every", type=int, default=32)
    ap.add_argument("--temp-start", type=float, default=3.0)
    ap.add_argument("--temp-end", type=float, default=0.02)
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("5-Applications/out/qubo_chunk_benchmark/spin_glass.json"),
    )
    args = ap.parse_args()

    if args.n > 24:
        raise SystemExit("Refusing exact solve above n=24 without a stronger backend.")

    Q = generate_dense_qubo(args.n, seed=args.seed)
    exact = exact_solve_qubo(Q)
    optimum = float(exact["best_energy"])

    baseline_runs: List[RunStats] = []
    guided_runs: List[RunStats] = []
    for trial in range(args.trials):
        trial_seed = args.seed + 1000 + trial
        baseline_runs.append(
            run_baseline_sa(
                Q=Q,
                optimum=optimum,
                steps=args.steps,
                seed=trial_seed,
                temp_start=args.temp_start,
                temp_end=args.temp_end,
            )
        )
        guided_runs.append(
            run_chunk_guided_sa(
                Q=Q,
                optimum=optimum,
                steps=args.steps,
                seed=trial_seed,
                temp_start=args.temp_start,
                temp_end=args.temp_end,
                chunk_size=args.chunk_size,
                guided_prob=args.guided_prob,
                recompute_every=args.recompute_every,
            )
        )

    result = {
        "schema_version": "qubo.chunk.field.benchmark.v1",
        "params": {
            "n": args.n,
            "seed": args.seed,
            "trials": args.trials,
            "steps": args.steps,
            "chunk_size": args.chunk_size,
            "guided_prob": args.guided_prob,
            "recompute_every": args.recompute_every,
            "temp_start": args.temp_start,
            "temp_end": args.temp_end,
        },
        "exact": exact,
        "baseline": summarize_runs(baseline_runs, optimum),
        "chunk_guided": summarize_runs(guided_runs, optimum),
    }
    result["delta"] = {
        "hit_rate_gain": result["chunk_guided"]["hit_rate"] - result["baseline"]["hit_rate"],
        "avg_gap_reduction": result["baseline"]["avg_gap_to_optimum"] - result["chunk_guided"]["avg_gap_to_optimum"],
        "median_first_hit_step_gain": (
            None
            if result["baseline"]["median_first_hit_step"] is None
            or result["chunk_guided"]["median_first_hit_step"] is None
            else result["baseline"]["median_first_hit_step"] - result["chunk_guided"]["median_first_hit_step"]
        ),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)

    print(json.dumps({
        "exact_best_energy": optimum,
        "baseline": result["baseline"],
        "chunk_guided": result["chunk_guided"],
        "delta": result["delta"],
        "out": str(args.out.resolve()),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
