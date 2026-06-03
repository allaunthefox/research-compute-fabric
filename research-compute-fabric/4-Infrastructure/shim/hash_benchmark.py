#!/usr/bin/env python3
"""
Hash Function Benchmark: Hilbert vs Morton vs xxHash

Benchmarks three spatial hashing strategies across multiple grid sizes and
access pattern traces.  Measures cache hit rate, lookup latency (p50/p99),
spatial locality preservation, and simulated memory bandwidth.

Output:
  - CSV:  /home/allaun/Research Stack/shared-data/artifacts/hash_benchmark.csv
  - JSON: /home/allaun/Research Stack/shared-data/artifacts/hash_benchmark.json
"""

import csv
import hashlib
import json
import math
import os
import random
import time
from collections import OrderedDict
from pathlib import Path
from typing import Dict, List, Tuple

import xxhash

# ──────────────────────────────────────────────────────────────────────
# 1.  HASH FUNCTIONS
# ──────────────────────────────────────────────────────────────────────

def _part1by1(n: int) -> int:
    """Spread bits of a 16-bit integer so every bit is separated by a zero."""
    n &= 0x0000FFFF
    n = (n | (n << 8)) & 0x00FF00FF
    n = (n | (n << 4)) & 0x0F0F0F0F
    n = (n | (n << 2)) & 0x33333333
    n = (n | (n << 1)) & 0x55555555
    return n

def _unpart1by1(n: int) -> int:
    n &= 0x55555555
    n = (n | (n >> 1)) & 0x33333333
    n = (n | (n >> 2)) & 0x0F0F0F0F
    n = (n | (n >> 4)) & 0x00FF00FF
    n = (n | (n >> 8)) & 0x0000FFFF
    return n

# ---------- Morton code ----------

def morton_encode_2d(x: int, y: int) -> int:
    return _part1by1(x) | (_part1by1(y) << 1)

def morton_decode_2d(n: int) -> Tuple[int, int]:
    return _unpart1by1(n), _unpart1by1(n >> 1)

def morton_encode_3d(x: int, y: int, z: int) -> int:
    def spread(v):
        v &= 0x000003FF
        v = (v | (v << 16)) & 0xFF0000FF
        v = (v | (v <<  8)) & 0x0300F00F
        v = (v | (v <<  4)) & 0x30C30C30
        v = (v | (v <<  2)) & 0x92492492
        return v
    return spread(x) | (spread(y) << 1) | (spread(z) << 2)

def morton_decode_3d(n: int) -> Tuple[int, int, int]:
    def compact(v):
        v &= 0x92492492
        v = (v | (v >>  2)) & 0x30C30C30
        v = (v | (v >>  4)) & 0x0300F00F
        v = (v | (v >>  8)) & 0xFF0000FF
        v = (v | (v >> 16)) & 0x000003FF
        return v
    return compact(n), compact(n >> 1), compact(n >> 2)

# ---------- Hilbert curve ----------

def _hilbert_index_to_point_2d(n: int, d: int) -> Tuple[int, int]:
    """Convert Hilbert index *n* to 2D point for order *d* (side = 2^d)."""
    x = y = 0
    s = 1 << (d - 1)
    for _ in range(d):
        rx = (n >> 1) & 1
        ry = (n ^ rx) & 1
        if ry == 0:
            if rx == 1:
                x = s - 1 - x
                y = s - 1 - y
            x, y = y, x
        x += s * rx
        y += s * ry
        n >>= 2
        s >>= 1
    return x, y

def _hilbert_point_to_index_2d(x: int, y: int, d: int) -> int:
    """Convert 2D point to Hilbert index for order *d*."""
    n = 0
    s = 1 << (d - 1)
    for _ in range(d):
        rx = 1 if (x & s) else 0
        ry = 1 if (y & s) else 0
        n += s * s * ((3 * rx) ^ ry)
        if ry == 0:
            if rx == 1:
                x = s - 1 - x
                y = s - 1 - y
            x, y = y, x
        x -= s * rx
        y -= s * ry
        s >>= 1
    return n

def _hilbert_index_to_point_3d(n: int, d: int) -> Tuple[int, int, int]:
    """Convert Hilbert index to 3D point for order d."""
    x = y = z = 0
    s = 1 << (d - 1)
    for _ in range(d):
        rx = (n >> 2) & 1
        ry = (n >> 1) & 1
        rz = (n ^ rx ^ ry) & 1
        # inverse Gray code
        if rz == 0:
            if rx == 1:
                x = s - 1 - x
                y = s - 1 - y
            if ry == 1:
                z_temp = z
                z = s - 1 - y
                y = s - 1 - z_temp
            x, y, z = y, z, x
        else:
            if ry == 1:
                z_temp = z
                z = s - 1 - y
                y = s - 1 - z_temp
            if rx == 1:
                x = s - 1 - x
                y = s - 1 - y
            x, y, z = z, x, y
        x += s * rx
        y += s * ry
        z += s * rz
        n >>= 3
        s >>= 1
    return x, y, z

def _hilbert_point_to_index_3d(x: int, y: int, z: int, d: int) -> int:
    """Convert 3D point to Hilbert index for order d."""
    n = 0
    s = 1 << (d - 1)
    for _ in range(d):
        rx = 1 if (x & s) else 0
        ry = 1 if (y & s) else 0
        rz = 1 if (z & s) else 0
        n += s * s * s * ((7 * rx) ^ (3 * ry) ^ rz)
        if rz == 0:
            if ry == 1:
                z_temp = z
                z = s - 1 - y
                y = s - 1 - z_temp
            if rx == 1:
                x = s - 1 - x
                y = s - 1 - y
            x, y, z = y, z, x
        else:
            x, y, z = z, x, y
            if ry == 1:
                z_temp = z
                z = s - 1 - y
                y = s - 1 - z_temp
            if rx == 1:
                x = s - 1 - x
                y = s - 1 - y
        x -= s * rx
        y -= s * ry
        z -= s * rz
        s >>= 1
    return n

def hilbert_encode(x: int, y: int, z: int, order: int) -> int:
    return _hilbert_point_to_index_3d(x, y, z, order)

def hilbert_decode(n: int, order: int) -> Tuple[int, int, int]:
    return _hilbert_index_to_point_3d(n, order)

# ---------- xxHash wrapper ----------

def xxhash_encode(x: int, y: int, z: int, grid_size: int) -> int:
    """Hash 3D coordinates using xxHash, mapped into [0, grid_size^3)."""
    data = struct_pack_3ints(x, y, z)
    h = xxhash.xxh3_64(data).intdigest()
    return h % (grid_size ** 3)

def _struct_pack_3ints(x: int, y: int, z: int) -> bytes:
    return x.to_bytes(4, 'little') + y.to_bytes(4, 'little') + z.to_bytes(4, 'little')

# alias
struct_pack_3ints = _struct_pack_3ints

# ──────────────────────────────────────────────────────────────────────
# 2.  ACCESS PATTERN TRACES
# ──────────────────────────────────────────────────────────────────────

def trace_sequential(grid_size: int, n: int) -> List[Tuple[int, int, int]]:
    """Linear scan through the entire grid in row-major order."""
    coords = []
    for i in range(min(n, grid_size ** 3)):
        z = i // (grid_size * grid_size)
        rem = i % (grid_size * grid_size)
        y = rem // grid_size
        x = rem % grid_size
        coords.append((x, y, z))
    # tile if n > total cells
    while len(coords) < n:
        coords.extend(coords[:n - len(coords)])
    return coords[:n]

def trace_random(grid_size: int, n: int) -> List[Tuple[int, int, int]]:
    """Uniformly random coordinates."""
    rng = random.Random(42)
    return [(rng.randint(0, grid_size - 1),
             rng.randint(0, grid_size - 1),
             rng.randint(0, grid_size - 1)) for _ in range(n)]

def trace_spatial_locality(grid_size: int, n: int) -> List[Tuple[int, int, int]]:
    """Random walk with small steps — simulates spatial locality."""
    rng = random.Random(42)
    x, y, z = grid_size // 2, grid_size // 2, grid_size // 2
    coords = []
    for _ in range(n):
        coords.append((x, y, z))
        dx = rng.randint(-3, 3)
        dy = rng.randint(-3, 3)
        dz = rng.randint(-3, 3)
        x = max(0, min(grid_size - 1, x + dx))
        y = max(0, min(grid_size - 1, y + dy))
        z = max(0, min(grid_size - 1, z + dz))
    return coords

def trace_temporal_locality(grid_size: int, n: int) -> List[Tuple[int, int, int]]:
    """Repeated access to a recent working set."""
    rng = random.Random(42)
    window = max(16, n // 20)
    recent: List[Tuple[int, int, int]] = []
    coords = []
    for i in range(n):
        if recent and rng.random() < 0.7:
            c = rng.choice(recent)
        else:
            c = (rng.randint(0, grid_size - 1),
                 rng.randint(0, grid_size - 1),
                 rng.randint(0, grid_size - 1))
        coords.append(c)
        recent.append(c)
        if len(recent) > window:
            recent.pop(0)
    return coords

TRACE_GENERATORS = {
    "sequential":      trace_sequential,
    "random":          trace_random,
    "spatial_locality": trace_spatial_locality,
    "temporal_locality": trace_temporal_locality,
}

# ──────────────────────────────────────────────────────────────────────
# 3.  SIMULATED CACHE
# ──────────────────────────────────────────────────────────────────────

class SimCache:
    """LRU set-associative cache simulation (3 levels: L1/L2/L3)."""

    def __init__(self, l1_lines=64, l2_lines=512, l3_lines=4096):
        self.l1 = OrderedDict()
        self.l2 = OrderedDict()
        self.l3 = OrderedDict()
        self.l1_cap = l1_lines
        self.l2_cap = l2_lines
        self.l3_cap = l3_lines
        self.hits = 0
        self.misses = 0

    def access(self, key: int) -> str:
        if key in self.l1:
            self.l1.move_to_end(key)
            self.hits += 1
            return "L1"
        if key in self.l2:
            self.l2.move_to_end(key)
            self.l1[key] = True
            if len(self.l1) > self.l1_cap:
                self.l1.popitem(last=False)
            self.hits += 1
            return "L2"
        if key in self.l3:
            self.l3.move_to_end(key)
            self.l2[key] = True
            if len(self.l2) > self.l2_cap:
                self.l2.popitem(last=False)
            self.l1[key] = True
            if len(self.l1) > self.l1_cap:
                self.l1.popitem(last=False)
            self.hits += 1
            return "L3"
        # miss
        self.l3[key] = True
        if len(self.l3) > self.l3_cap:
            self.l3.popitem(last=False)
        self.l2[key] = True
        if len(self.l2) > self.l2_cap:
            self.l2.popitem(last=False)
        self.l1[key] = True
        if len(self.l1) > self.l1_cap:
            self.l1.popitem(last=False)
        self.misses += 1
        return "MISS"

    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total else 0.0

    def reset(self):
        self.l1.clear(); self.l2.clear(); self.l3.clear()
        self.hits = 0; self.misses = 0

# ──────────────────────────────────────────────────────────────────────
# 4.  SPATIAL LOCALITY PRESERVATION METRIC
# ──────────────────────────────────────────────────────────────────────

def locality_preservation(coords: List[Tuple[int, int, int]],
                          hashes: List[int]) -> float:
    """
    Fraction of spatially-adjacent points (Manhattan dist <= 1) whose
    hash indices differ by at most grid_size (roughly one grid plane).
    """
    if len(coords) < 2:
        return 1.0
    adjacent = 0
    preserved = 0
    sample = min(len(coords), 2000)
    rng = random.Random(99)
    indices = rng.sample(range(len(coords)), sample)
    grid_size_approx = int(round(len(hashes) ** (1/3))) if len(hashes) > 0 else 64
    threshold = grid_size_approx  # one "row" in linearised grid
    for i in indices:
        for j in indices:
            if j <= i:
                continue
            cx, cy, cz = coords[i]
            dx, dy, dz = coords[j]
            manhattan = abs(cx - dx) + abs(cy - dy) + abs(cz - dz)
            if manhattan <= 1:
                adjacent += 1
                if abs(hashes[i] - hashes[j]) <= threshold:
                    preserved += 1
    return preserved / adjacent if adjacent > 0 else 1.0

# ──────────────────────────────────────────────────────────────────────
# 5.  BENCHMARK RUNNER
# ──────────────────────────────────────────────────────────────────────

def run_benchmark():
    grid_sizes = [16, 32, 64, 128, 256]
    trace_sizes = [1000, 10000, 100000, 1000000]
    results = []

    for gs in grid_sizes:
        order = int(math.log2(gs))
        for tn in trace_sizes:
            for tname, tgen in TRACE_GENERATORS.items():
                trace = tgen(gs, tn)
                for hname in ("hilbert", "morton", "xxhash"):
                    cache = SimCache()
                    latencies = []
                    hashes_out = []

                    t0 = time.perf_counter_ns()
                    for (x, y, z) in trace:
                        if hname == "hilbert":
                            h = hilbert_encode(x, y, z, order)
                        elif hname == "morton":
                            h = morton_encode_3d(x, y, z)
                        else:
                            h = xxhash_encode(x, y, z, gs)
                        hashes_out.append(h)
                        cache.access(h)
                        t1 = time.perf_counter_ns()
                        latencies.append(t1 - t0)
                        t0 = t1

                    # percentiles
                    latencies.sort()
                    n = len(latencies)
                    p50 = latencies[n // 2] / 1e3  # µs
                    p99 = latencies[int(n * 0.99)] / 1e3
                    total_ns = sum(latencies)
                    bandwidth = (tn * 12) / (total_ns / 1e9) / 1e6  # MB/s (12 bytes/coord)

                    loc = locality_preservation(trace, hashes_out)

                    row = OrderedDict(
                        grid_size=gs,
                        trace_size=tn,
                        trace_pattern=tname,
                        hash_function=hname,
                        cache_hit_rate=round(cache.hit_rate(), 6),
                        p50_latency_us=round(p50, 4),
                        p99_latency_us=round(p99, 4),
                        memory_bandwidth_mbs=round(bandwidth, 2),
                        locality_preservation=round(loc, 6),
                    )
                    results.append(row)
                    print(f"  gs={gs:>4d}  trace={tn:>7d}  {tname:<18s}  {hname:<8s}  "
                          f"hit={cache.hit_rate():.3f}  p50={p50:.2f}µs  p99={p99:.2f}µs  "
                          f"bw={bandwidth:.1f}MB/s  loc={loc:.3f}")

    return results


def write_outputs(results: List[OrderedDict]):
    base = Path("/home/allaun/Research Stack/shared-data/artifacts")
    base.mkdir(parents=True, exist_ok=True)

    # CSV
    csv_path = base / "hash_benchmark.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results)
    print(f"\nCSV  → {csv_path}")

    # JSON
    json_path = base / "hash_benchmark.json"
    payload = {
        "benchmark": "hash_function_comparison",
        "description": "Hilbert vs Morton vs xxHash spatial hashing benchmark",
        "grid_sizes": [16, 32, 64, 128, 256],
        "trace_sizes": [1000, 10000, 100000, 1000000],
        "hash_functions": ["hilbert", "morton", "xxhash"],
        "trace_patterns": ["sequential", "random", "spatial_locality", "temporal_locality"],
        "metrics": ["cache_hit_rate", "p50_latency_us", "p99_latency_us",
                     "memory_bandwidth_mbs", "locality_preservation"],
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "results": results,
    }
    with open(json_path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"JSON → {json_path}")


# ──────────────────────────────────────────────────────────────────────
# 6.  SUMMARY TABLE
# ──────────────────────────────────────────────────────────────────────

def print_summary(results: List[OrderedDict]):
    from itertools import groupby

    print("\n" + "=" * 90)
    print("AGGREGATE SUMMARY  (averaged across grid sizes and trace sizes)")
    print("=" * 90)
    print(f"{'Hash':<10s} {'Pattern':<20s} {'Avg Hit%':>9s} {'Avg p50µs':>10s} "
          f"{'Avg p99µs':>10s} {'Avg BW MB/s':>12s} {'Avg Loc':>8s}")
    print("-" * 90)

    key_fn = lambda r: (r["hash_function"], r["trace_pattern"])
    results_sorted = sorted(results, key=key_fn)
    for (hf, tp), group in groupby(results_sorted, key=key_fn):
        g = list(group)
        n = len(g)
        ah = sum(r["cache_hit_rate"] for r in g) / n
        ap50 = sum(r["p50_latency_us"] for r in g) / n
        ap99 = sum(r["p99_latency_us"] for r in g) / n
        abw = sum(r["memory_bandwidth_mbs"] for r in g) / n
        al = sum(r["locality_preservation"] for r in g) / n
        print(f"{hf:<10s} {tp:<20s} {ah*100:>8.2f}% {ap50:>10.2f} {ap99:>10.2f} "
              f"{abw:>12.1f} {al:>8.3f}")
    print("=" * 90)


# ──────────────────────────────────────────────────────────────────────
# 7.  MAIN
# ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Hash Function Benchmark: Hilbert vs Morton vs xxHash")
    print("=" * 90)
    results = run_benchmark()
    print_summary(results)
    write_outputs(results)
    print("\nDone.")
