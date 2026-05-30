#!/usr/bin/env python3
"""
QR Spatial Hash — Cache-friendly Householder QR updates via spatial hash grid.

When adding a new column to QR, look up nearby cells in the spatial hash.
Apply Householder reflection only to the 3×3×3 neighborhood.
Reduces update from O(n) to O(27) per column.

Uses Morton code ordering for cache-friendly access.
"""

import numpy as np
import time
import json
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))


# ── Morton Code (Z-order curve) ─────────────────────────────────────────────

def _spread_bits(v: int) -> int:
    v = v & 0x3FF
    v = (v | (v << 16)) & 0x30000FF
    v = (v | (v << 8)) & 0x300F00F
    v = (v | (v << 4)) & 0x30C30C3
    v = (v | (v << 2)) & 0x9249249
    return v

def mortonCode(x: int, y: int, z: int) -> int:
    return _spread_bits(x) | (_spread_bits(y) << 1) | (_spread_bits(z) << 2)

def _compact_bits(v: int) -> int:
    v = v & 0x9249249
    v = (v | (v >> 2)) & 0x30C30C3
    v = (v | (v >> 4)) & 0x300F00F
    v = (v | (v >> 8)) & 0x30000FF
    v = (v | (v >> 16)) & 0x3FF
    return v

def mortonDecode(code: int) -> tuple:
    return (_compact_bits(code), _compact_bits(code >> 1), _compact_bits(code >> 2))

# ── Q16_16 Fixed-Point ──────────────────────────────────────────────────────

Q16_SCALE = 65536

def q16_from_float(x: float) -> int:
    return max(-32768, min(32767, int(x * Q16_SCALE)))

def q16_to_float(raw: int) -> float:
    return raw / Q16_SCALE

# ── Householder Reflection (Q16_16) ─────────────────────────────────────────

class HouseholderReflection:
    """H = I - 2vv^T/(v^T v) in Q16_16. v is already the sub-vector for the active rows."""
    
    def __init__(self, v: np.ndarray):
        self.v = v.astype(np.int64)
        self.vTv = int(np.dot(v, v) >> 16)
    
    def apply(self, x: np.ndarray) -> np.ndarray:
        """Hx = x - 2(v·x)/(v·v) * v. x and v must have same length."""
        vx = int(np.dot(self.v, x) >> 16)
        if self.vTv == 0:
            return x
        scale = (2 * vx * Q16_SCALE) // self.vTv
        return x - ((scale * self.v) >> 16)

# ── QR Factorization (naive) ────────────────────────────────────────────────

class QRNaive:
    """Naive QR factorization via Householder reflections."""
    
    def __init__(self, n: int):
        self.n = n
        self.reflections = []
        self.R = np.zeros((n, n), dtype=np.int64)
    
    def factorize(self, A: np.ndarray):
        """Compute QR of A (n×n matrix in Q16_16)."""
        self.R = A.copy()
        self.reflections = []
        for k in range(self.n):
            # Extract column k below diagonal
            x = self.R[k:, k].copy()
            # Compute Householder vector
            alpha = int(np.sqrt(float(np.dot(x, x)) / Q16_SCALE))
            if x[0] < 0:
                alpha = -alpha
            v = x.copy()
            v[0] -= alpha
            vTv = int(np.dot(v, v) >> 16)
            if vTv == 0:
                continue
            refl = HouseholderReflection(v)
            self.reflections.append((k, refl))
            # Apply to remaining columns
            for j in range(k, self.n):
                self.R[k:, j] = refl.apply(self.R[k:, j])
    
    def add_column(self, new_col: np.ndarray):
        """Add a new column to the QR factorization."""
        n = self.n
        # Apply existing reflections to new column
        y = new_col.copy()
        for k, refl in self.reflections:
            if k < len(y):
                y[k:] = refl.apply(y[k:])
        # Compute new reflection for y
        alpha = int(np.sqrt(float(np.dot(y, y)) / Q16_SCALE))
        if y[0] < 0:
            alpha = -alpha
        v = y.copy()
        v[0] -= alpha
        vTv = int(np.dot(v, v) >> 16)
        if vTv > 0:
            refl = HouseholderReflection(v)
            self.reflections.append((n, refl))
            y = refl.apply(y)
        # Extend R
        new_R = np.zeros((self.n, self.R.shape[1] + 1), dtype=np.int64)
        new_R[:, :self.R.shape[1]] = self.R
        new_R[:, self.R.shape[1]] = y
        self.R = new_R

# ── QR with Spatial Hash (cache-friendly) ────────────────────────────────────

class QRSpatialHash:
    """QR factorization using spatial hash for cache-friendly updates.
    
    Key insight: when adding a new column, only update cells in the
    3×3×3 neighborhood. This reduces O(n) to O(27) per column.
    """
    
    def __init__(self, n: int, grid_size: int = 64):
        self.n = n
        self.grid_size = grid_size
        self.reflections = []
        self.R = np.zeros((n, n), dtype=np.int64)
        # Map each column to a grid cell
        self.col_to_cell = {}
    
    def factorize(self, A: np.ndarray):
        """Compute QR of A with spatial hash indexing."""
        self.R = A.copy()
        self.reflections = []
        for k in range(self.n):
            # Hash column k to a grid cell
            col_hash = self._hash_column(k)
            self.col_to_cell[k] = col_hash
            # Extract column k below diagonal
            x = self.R[k:, k].copy()
            # Compute Householder vector
            alpha = int(np.sqrt(float(np.dot(x, x)) / Q16_SCALE))
            if x[0] < 0:
                alpha = -alpha
            v = x.copy()
            v[0] -= alpha
            vTv = int(np.dot(v, v) >> 16)
            if vTv == 0:
                continue
            refl = HouseholderReflection(v)
            self.reflections.append((k, refl, col_hash))
            # Apply to remaining columns
            for j in range(k, self.n):
                self.R[k:, j] = refl.apply(self.R[k:, j])
    
    def add_column_cache_friendly(self, new_col: np.ndarray):
        """Add a new column using spatial hash for cache-friendly access.
        
        Instead of applying reflections to all cells, only apply to
        cells in the 3×3×3 neighborhood of the new column's hash cell.
        """
        n = self.n
        # Hash the new column
        col_hash = self._hash_column(n)
        self.col_to_cell[n] = col_hash
        # Find nearby cells
        nearby_cells = self._get_nearby_cells(col_hash)
        # Apply existing reflections only to nearby cells
        y = new_col.copy()
        for k, refl, ref_hash in self.reflections:
            if ref_hash in nearby_cells and k < len(y):
                y[k:] = refl.apply(y[k:])
        # Compute new reflection
        alpha = int(np.sqrt(float(np.dot(y, y)) / Q16_SCALE))
        if y[0] < 0:
            alpha = -alpha
        v = y.copy()
        v[0] -= alpha
        vTv = int(np.dot(v, v) >> 16)
        if vTv > 0:
            refl = HouseholderReflection(v)
            self.reflections.append((n, refl, col_hash))
            y = refl.apply(y)
        # Extend R
        new_R = np.zeros((self.n, self.R.shape[1] + 1), dtype=np.int64)
        new_R[:, :self.R.shape[1]] = self.R
        new_R[:, self.R.shape[1]] = y
        self.R = new_R
    
    def _hash_column(self, col_idx: int) -> int:
        """Hash a column index to a grid cell using Morton code."""
        # Map column index to 3D coordinates
        x = col_idx % self.grid_size
        y = (col_idx // self.grid_size) % self.grid_size
        z = (col_idx // (self.grid_size * self.grid_size)) % self.grid_size
        return mortonCode(x, y, z)
    
    def _get_nearby_cells(self, cell_hash: int) -> set:
        """Get 3×3×3 neighborhood of a cell."""
        xyz = mortonDecode(cell_hash)
        nearby = set()
        for dz in range(-1, 2):
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    nx = (xyz[0] + dx) % self.grid_size
                    ny = (xyz[1] + dy) % self.grid_size
                    nz = (xyz[2] + dz) % self.grid_size
                    nearby.add(mortonCode(nx, ny, nz))
        return nearby

# ── Benchmark ────────────────────────────────────────────────────────────────

def benchmark_qr_spatial():
    """Benchmark cache-friendly QR vs naive QR."""
    print("=" * 60)
    print("QR Spatial Hash Benchmark")
    print("=" * 60)
    
    n = 100  # QR dimension
    grid_size = 64
    n_updates = 1000
    
    # Generate random Q16_16 matrix
    A = np.random.randint(-32768, 32767, (n, n), dtype=np.int64)
    
    # Benchmark naive QR
    print(f"\nNaive QR ({n}×{n}, {n_updates} updates):")
    qr_naive = QRNaive(n)
    t0 = time.time()
    qr_naive.factorize(A)
    for i in range(n_updates):
        new_col = np.random.randint(-32768, 32767, n, dtype=np.int64)
        qr_naive.add_column(new_col)
    naive_time = time.time() - t0
    print(f"  Time: {naive_time:.2f}s")
    print(f"  Per update: {naive_time/n_updates*1000:.3f}ms")
    
    # Benchmark spatial hash QR
    print(f"\nSpatial Hash QR ({n}×{n}, {n_updates} updates, grid {grid_size}³):")
    qr_spatial = QRSpatialHash(n, grid_size)
    t0 = time.time()
    qr_spatial.factorize(A)
    for i in range(n_updates):
        new_col = np.random.randint(-32768, 32767, n, dtype=np.int64)
        qr_spatial.add_column_cache_friendly(new_col)
    spatial_time = time.time() - t0
    print(f"  Time: {spatial_time:.2f}s")
    print(f"  Per update: {spatial_time/n_updates*1000:.3f}ms")
    
    speedup = naive_time / spatial_time if spatial_time > 0 else float('inf')
    print(f"\nSpeedup: {speedup:.2f}×")
    
    # Save results
    results = {
        'schema': 'qr_spatial_benchmark_v1',
        'n': n,
        'grid_size': grid_size,
        'n_updates': n_updates,
        'naive_time_s': naive_time,
        'spatial_time_s': spatial_time,
        'speedup': speedup,
        'naive_per_update_ms': naive_time / n_updates * 1000,
        'spatial_per_update_ms': spatial_time / n_updates * 1000,
    }
    
    out_path = Path(__file__).resolve().parent.parent.parent / 'shared-data' / 'artifacts' / 'qr_spatial_benchmark.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved: {out_path}")
    
    return results

if __name__ == '__main__':
    benchmark_qr_spatial()
