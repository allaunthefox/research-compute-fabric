#!/usr/bin/env python3
"""Batch spectral decomposition of Tier 2B trace matrices.

Reads all v2_canary_*.json files from proof_traces/, computes spectra,
and outputs vectors + report.
"""
import glob
import json
import math
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))
from pist_trace_decompose import spectral_analysis, FEATURE_NAMES

TRACE_DIR = os.path.join(os.path.dirname(__file__), "../..", "shared-data/proof_traces")
VECTORS_PATH = os.path.join(os.path.dirname(__file__), "../..", "shared-data/pist_trace_tier2b_vectors.jsonl")
REPORT_PATH = os.path.join(os.path.dirname(__file__), "../..", "shared-data/pist_trace_tier2b_report.json")


def power_iteration(matrix, max_iter=100):
    """Estimate largest eigenvalue via power iteration."""
    n = len(matrix)
    if n == 0:
        return 0.0
    v = [1.0 / math.sqrt(n)] * n
    for _ in range(max_iter):
        v_new = [sum(matrix[i][j] * v[j] for j in range(n)) for i in range(n)]
        norm = math.sqrt(sum(x * x for x in v_new))
        if norm < 1e-12:
            return 0.0
        v = [x / norm for x in v_new]
    num = sum(v[i] * sum(matrix[i][j] * v[j] for j in range(n)) for i in range(n))
    den = sum(v[i] * v[i] for i in range(n))
    return num / den if den > 0 else 0.0


def symmetrize(matrix):
    n = len(matrix)
    if n == 0:
        return []
    sym = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            sym[i][j] = (matrix[i][j] + matrix[j][i]) / 2.0
    return sym


def build_laplacian(sym):
    n = len(sym)
    if n == 0:
        return []
    lap = [[0.0] * n for _ in range(n)]
    for i in range(n):
        deg = sum(sym[i])
        for j in range(n):
            if i == j:
                lap[i][j] = deg
            else:
                lap[i][j] = -sym[i][j]
    return lap


def analyze_matrix(matrix):
    """Full spectral analysis of a transition matrix."""
    n = len(matrix)
    if n == 0 or len(matrix[0]) == 0:
        return {"error": "empty", "n_states": 0}

    sym = symmetrize(matrix)
    lap = build_laplacian(sym)

    sym_max = power_iteration(sym)
    lap_max = power_iteration(lap)

    # Estimate second eigenvalue via shifted power iteration
    shift = [[sym[i][j] for j in range(n)] for i in range(n)]
    for i in range(n):
        shift[i][i] -= 0.9 * sym_max
    shift_max = power_iteration(shift)
    sym_second = max(0, sym_max - shift_max)
    gap = sym_max - sym_second

    # Laplacian zero count
    lap_min = power_iteration([[-lap[i][j] for j in range(n)] for i in range(n)])
    lap_zero_count = sum(1 for i in range(n) if sum(lap[i]) < 1e-9)

    # Rank: count non-zero rows
    rank = sum(1 for row in matrix if sum(row) > 0)

    # Density
    total = sum(sum(row) for row in matrix)
    density = total / max(n * n, 1)

    # Frobenius norm
    frob = math.sqrt(sum(sum(cell * cell for cell in row) for row in matrix))

    return {
        "n_states": n,
        "eigenvalue_max": round(sym_max, 6),
        "spectral_gap": round(gap, 6),
        "laplacian_max": round(lap_max, 6),
        "laplacian_zero_count": lap_zero_count,
        "rank_estimate": rank,
        "density": round(density, 6),
        "frobenius_norm": round(frob, 6),
    }


def main():
    files = sorted(glob.glob(os.path.join(TRACE_DIR, "v2_canary_*.json")))
    print(f"Found {len(files)} trace files", flush=True)

    records = []
    for fpath in files:
        with open(fpath) as f:
            trace = json.load(f)

        name = trace.get("name", Path(fpath).stem)
        status = trace.get("status", "?")
        matrix = trace.get("transition_matrix", [])

        if not matrix or len(matrix) == 0:
            print(f"  {name:30s} SKIP (empty matrix)", flush=True)
            continue

        spectral = analyze_matrix(matrix)

        record = {
            "name": name,
            "proof_status": status,
            "trace_tags": trace.get("n_steps", 0),
            "unique_states": trace.get("n_unique", 0),
            "matrix_size": len(matrix),
            "rank": spectral.get("rank_estimate", 0),
            "spectral_gap": spectral.get("spectral_gap", 0),
            "laplacian_zero_count": spectral.get("laplacian_zero_count", 0),
            "density": spectral.get("density", 0),
            "eigenvalue_max": spectral.get("eigenvalue_max", 0),
            "symmetric_eigenvalues": [spectral.get("eigenvalue_max", 0)],
            "laplacian_eigenvalues": [spectral.get("laplacian_max", 0)],
            "frobenius_norm": spectral.get("frobenius_norm", 0),
        }
        records.append(record)

        print(f"  {name:30s} {status:10s} n={spectral['n_states']:2d} "
              f"rank={spectral['rank_estimate']:2d} gap={spectral['spectral_gap']:.4f} "
              f"lap0={spectral['laplacian_zero_count']:2d}", flush=True)

    n = len(records)
    if n == 0:
        print("No records to analyze", flush=True)
        return 1

    # ── Report ──
    print(f"\n{'='*60}", flush=True)
    print("TIER 2B SPECTRAL DECOMPOSITION REPORT", flush=True)
    print(f"{'='*60}", flush=True)

    sizes = [r["matrix_size"] for r in records]
    ranks = [r["rank"] for r in records]
    gaps = [r["spectral_gap"] for r in records]
    lap0s = [r["laplacian_zero_count"] for r in records]
    densities = [r["density"] for r in records]

    print(f"\nRecords: {n}", flush=True)
    print(f"Matrix size: mean={sum(sizes)/n:.1f} max={max(sizes)} varied={len(set(sizes))>1}", flush=True)
    print(f"Rank: mean={sum(ranks)/n:.2f} max={max(ranks)} varied={len(set(ranks))>1}", flush=True)
    print(f"Spectral gap: mean={sum(gaps)/n:.4f} varied={len(set(round(g,4) for g in gaps))}", flush=True)
    print(f"Laplacian zero count: varied={len(set(lap0s))} max={max(lap0s)}", flush=True)
    print(f"Density: mean={sum(densities)/n:.4f} varied={len(set(round(d,4) for d in densities))}", flush=True)

    # Verified vs failed
    for label in ["verified", "failed"]:
        subset = [r for r in records if r["proof_status"] == label]
        if subset:
            sg = [r["spectral_gap"] for r in subset]
            rk = [r["rank"] for r in subset]
            print(f"\n{label} (n={len(subset)}): gap={sum(sg)/len(sg):.4f} "
                  f"rank={sum(rk)/len(rk):.2f} density={sum(r['density'] for r in subset)/len(subset):.4f}",
                  flush=True)

    # Save vectors
    with open(VECTORS_PATH, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    print(f"\nVectors: {VECTORS_PATH}", flush=True)

    # Save report
    report = {
        "n": n,
        "avg_matrix_size": round(sum(sizes) / n, 1),
        "avg_rank": round(sum(ranks) / n, 2),
        "avg_spectral_gap": round(sum(gaps) / n, 4),
        "avg_density": round(sum(densities) / n, 4),
        "unique_gaps": len(set(round(g, 4) for g in gaps)),
        "unique_ranks": len(set(ranks)),
        "records": records,
    }
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Report: {REPORT_PATH}", flush=True)
    return 0


if __name__ == "__main__":
    main()
