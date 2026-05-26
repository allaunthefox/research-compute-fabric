#!/usr/bin/env python3
"""pist-trace-decompose — PIST spectral decomposition of a Lean proof trace.

Analyzes the transition matrix from ProofTraceReceipt v1,
builds spectral features (eigenvalues, gap, rank, density),
and classifies the trace by tactic family distribution.

Usage:
    python3 pist_trace_decompose.py trace.json [--out report.json]
"""

import json
import math
import os
import sys
from collections import Counter, defaultdict

FEATURE_NAMES = [
    "n_steps",
    "n_unique_goal_states",
    "transition_density",
    "spectral_gap", 
    "laplacian_zero_count",
    "rank_estimate",
    "avg_delta_goal_count",
    "avg_delta_hypothesis",
    "avg_delta_symbol",
    "tactic_family_entropy",
    "verified_ratio",
    "total_elapsed",
]


def build_transition_matrix(steps: list[dict]) -> tuple[list[list[int]], list[str]]:
    """Build adjacency matrix from goal-state hash transitions."""
    hashes = []
    for s in steps:
        bh = s.get("before_goal_hash", "")
        if bh:
            hashes.append(bh)
    if steps:
        ah = steps[-1].get("after_goal_hash", "")
        if ah:
            hashes.append(ah)
    
    unique = list(dict.fromkeys(hashes))
    h2i = {h: i for i, h in enumerate(unique)}
    n = len(unique)
    if n == 0:
        return [[0]], ["_empty"]
    
    matrix = [[0] * n for _ in range(n)]
    for s in steps:
        bh = s.get("before_goal_hash", "")
        ah = s.get("after_goal_hash", "")
        if bh in h2i and ah in h2i:
            matrix[h2i[bh]][h2i[ah]] += 1
    
    return matrix, unique


def symmetrize(matrix: list[list[int]]) -> list[list[float]]:
    n = len(matrix)
    if n == 0:
        return []
    sym = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            sym[i][j] = (matrix[i][j] + matrix[j][i]) / 2.0
    return sym


def laplacian(matrix: list[list[float]]) -> list[list[float]]:
    n = len(matrix)
    if n == 0:
        return []
    lap = [[0.0] * n for _ in range(n)]
    for i in range(n):
        deg = sum(matrix[i])
        for j in range(n):
            if i == j:
                lap[i][j] = deg
            else:
                lap[i][j] = -matrix[i][j]
    return lap


def power_iteration(matrix: list[list[float]], max_iter: int = 100) -> tuple[float, list[float]]:
    """Estimate the largest eigenvalue using power iteration."""
    n = len(matrix)
    if n == 0:
        return 0.0, [0.0] * n
    v = [1.0 / math.sqrt(n)] * n
    for _ in range(max_iter):
        v_new = [sum(matrix[i][j] * v[j] for j in range(n)) for i in range(n)]
        norm = math.sqrt(sum(x * x for x in v_new))
        if norm < 1e-12:
            return 0.0, v
        v = [x / norm for x in v_new]
        # Check convergence
        if all(abs(v_new[i] - v[i]) < 1e-6 for i in range(n)):
            break
    # Rayleigh quotient
    num = sum(v[i] * sum(matrix[i][j] * v[j] for j in range(n)) for i in range(n))
    den = sum(v[i] * v[i] for i in range(n))
    return num / den if den > 0 else 0.0, v


def spectral_analysis(matrix: list[list[int]]) -> dict:
    """Compute spectral features from the transition matrix."""
    n = len(matrix)
    if n == 0:
        return {"error": "empty_matrix"}
    
    sym = symmetrize(matrix)
    lap = laplacian(sym)
    
    # Largest eigenvalue via power iteration (symmetric matrix)
    eig_max, _ = power_iteration(sym)
    
    # Spectral gap: difference between largest and 2nd largest
    # (approximate by shifting the matrix and re-running)
    shift = [[sym[i][j] for j in range(n)] for i in range(n)]
    for i in range(n):
        shift[i][i] -= 0.9 * eig_max  # shift by 90% of largest
    eig_shift, _ = power_iteration(shift)
    eig_second_approx = 0.9 * eig_max + eig_shift
    
    gap = eig_max - eig_second_approx if eig_second_approx < eig_max else eig_max
    
    # Laplacian eigenvalues (power iteration on -lap for smallest)
    lap_max, _ = power_iteration(lap)
    
    # Rank estimate: count rows with non-zero sum
    row_sums = [sum(row) for row in matrix]
    rank_est = sum(1 for s in row_sums if s > 0)
    
    # Zero-mode proxy: count near-zero rows
    zero_rows = sum(1 for s in row_sums if s == 0)
    
    # Frobenius norm
    frob_norm = math.sqrt(sum(sum(cell * cell for cell in row) for row in matrix))
    
    # Trace
    trace = sum(matrix[i][i] for i in range(n))
    
    return {
        "n_states": n,
        "eigenvalue_max": round(eig_max, 6),
        "spectral_gap": round(gap, 6),
        "laplacian_eigenvalue_max": round(lap_max, 6),
        "rank_estimate": rank_est,
        "zero_rows": zero_rows,
        "frobenius_norm": round(frob_norm, 6),
        "trace": trace,
        "density": sum(row_sums) / max(n * n, 1) if n > 0 else 0,
    }


def analyze_trace(trace: dict) -> dict:
    """Full spectral analysis of a proof trace."""
    steps = trace.get("steps", [])
    flexure_joints = trace.get("flexure_joints", [])
    
    n = len(steps)
    matrix, unique_hashes = build_transition_matrix(steps)
    spectral = spectral_analysis(matrix)
    
    # Tactic family distribution
    families = Counter(j.get("tactic_family", "?") for j in flexure_joints)
    n_families = len(families)
    if n_families > 0 and n > 0:
        probs = [f / n for f in families.values()]
        entropy = -sum(p * math.log2(p) for p in probs if p > 0)
    else:
        entropy = 0.0
    
    # Step delta stats
    goal_deltas = [abs(s.get("delta", {}).get("goal_count_delta", 0)) for s in steps if "delta" in s]
    hyp_deltas = [abs(s.get("delta", {}).get("hypothesis_delta", 0)) for s in steps if "delta" in s]
    sym_deltas = [abs(s.get("delta", {}).get("symbol_delta", 0)) for s in steps if "delta" in s]
    
    avg_gd = sum(goal_deltas) / max(len(goal_deltas), 1)
    avg_hd = sum(hyp_deltas) / max(len(hyp_deltas), 1)
    avg_sd = sum(sym_deltas) / max(len(sym_deltas), 1)
    
    # Result ratio
    successes = sum(1 for s in steps if s.get("result") == "success")
    
    # Flexure delta scores
    delta_scores = [j.get("delta_score", 0) for j in flexure_joints]
    
    feature_vector = [
        n,
        len(unique_hashes),
        spectral.get("density", 0),
        spectral.get("spectral_gap", 0),
        spectral.get("zero_rows", 0),
        spectral.get("rank_estimate", 0),
        avg_gd,
        avg_hd,
        avg_sd,
        round(entropy, 4),
        successes / max(n, 1),
        trace.get("total_elapsed_ms", 0),
    ]
    
    return {
        "trace_summary": {
            "theorem_name": trace.get("theorem_name", "?"),
            "status": trace.get("status", "?"),
            "n_steps": n,
            "n_unique_goal_states": len(unique_hashes),
            "n_flexure_joints": len(flexure_joints),
        },
        "spectral": spectral,
        "feature_vector": feature_vector,
        "feature_names": FEATURE_NAMES,
        "tactic_family_distribution": dict(families),
        "delta_stats": {
            "avg_goal_delta": round(avg_gd, 4),
            "avg_hypothesis_delta": round(avg_hd, 4),
            "avg_symbol_delta": round(avg_sd, 4),
            "max_delta_score": max(delta_scores) if delta_scores else 0,
        },
        "flexure_joints": flexure_joints,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 pist_trace_decompose.py trace.json [--out report.json]", file=sys.stderr)
        return 1
    
    trace_path = sys.argv[1]
    out_path = None
    for i, arg in enumerate(sys.argv):
        if arg == "--out" and i + 1 < len(sys.argv):
            out_path = sys.argv[i + 1]
    
    with open(trace_path) as f:
        trace = json.load(f)
    
    print(f"Analyzing trace: {trace.get('theorem_name', '?')}", flush=True)
    print(f"  Steps: {len(trace.get('steps', []))}", flush=True)
    print(f"  Status: {trace.get('status', '?')}", flush=True)
    
    result = analyze_trace(trace)
    
    ts = result["trace_summary"]
    sp = result["spectral"]
    print(f"\n  Unique goal states: {ts['n_unique_goal_states']}", flush=True)
    print(f"  Spectral gap: {sp.get('spectral_gap', 0):.4f}", flush=True)
    print(f"  Rank estimate: {sp.get('rank_estimate', 0)}", flush=True)
    print(f"  Density: {sp.get('density', 0):.4f}", flush=True)
    print(f"  Flexure joints: {ts['n_flexure_joints']}", flush=True)
    
    print(f"\n  Tactic families:", flush=True)
    for fam, count in sorted(result["tactic_family_distribution"].items(), key=lambda x: -x[1]):
        print(f"    {fam:20s}: {count:3d}", flush=True)
    
    print(f"\n  Delta stats:", flush=True)
    ds = result["delta_stats"]
    print(f"    Avg goal delta: {ds['avg_goal_delta']:.2f}", flush=True)
    print(f"    Max delta score: {ds['max_delta_score']}", flush=True)
    
    if out_path:
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nDecomposition: {out_path}", flush=True)
    
    return 0


if __name__ == "__main__":
    main()
