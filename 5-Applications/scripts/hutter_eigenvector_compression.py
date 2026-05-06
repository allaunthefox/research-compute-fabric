#!/usr/bin/env python3
"""
Hutter Prize Eigenvector Compression Test

Load enwik9 data, compute eigenvectors, and test compression through TSM/FAMM.
"""

import sys
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import eigsh
from pathlib import Path
from collections import Counter

# Add TSM to path
sys.path.insert(0, str(Path(__file__).parent))
from topological_state_machine import (
    TopologicalStateMachine, NibbleSwitch, ManifoldPoint,
    TopologicalInvariants, FAMMCache
)

HUTTER_DATA = Path("/home/allaun/Documents/Research Stack/shared-data/data/hutter_archive/enwik9")
OUTPUT_DIR = Path("/home/allaun/Documents/Research Stack/3-Mathematical-Models/hutter_eigenvector")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_hutter_data(max_bytes: int = None):
    """Load Hutter Prize data."""
    file_size = HUTTER_DATA.stat().st_size
    if max_bytes is None:
        max_bytes = file_size
    print(f"Loading Hutter Prize data (max {max_bytes:,} bytes of {file_size:,} total)...")
    with open(HUTTER_DATA, "rb") as f:
        data = f.read(max_bytes)
    print(f"  → Loaded {len(data):,} bytes")
    return data

def build_byte_adjacency(data: bytes, window_size: int = 4):
    """
    Build adjacency matrix from byte co-occurrence.

    Two bytes are connected if they appear within window_size bytes of each other.
    """
    print(f"Building byte adjacency matrix (window={window_size})...")

    # Count byte co-occurrences
    cooccurrence = Counter()
    byte_counts = Counter(data)

    for i in range(len(data) - window_size):
        window = data[i:i+window_size]
        for j in range(len(window)):
            for k in range(j+1, len(window)):
                pair = (window[j], window[k])
                cooccurrence[pair] += 1

    # Build sparse adjacency matrix (256x256 for all possible bytes)
    n = 256
    row_indices = []
    col_indices = []
    data_values = []

    for (b1, b2), count in cooccurrence.items():
        if count > 0:
            row_indices.append(b1)
            col_indices.append(b2)
            # Normalize by byte frequencies
            norm = count / (byte_counts[b1] * byte_counts[b2] + 1)
            data_values.append(norm)

    adj = csr_matrix((data_values, (row_indices, col_indices)), shape=(n, n))
    print(f"  → Matrix shape: {adj.shape}")
    print(f"  → Non-zero entries: {adj.nnz}")
    print(f"  → Unique bytes: {len(byte_counts)}")

    return adj, byte_counts

def compute_eigenvectors(adj_matrix, n_eigenvectors=5):
    """Find principal eigenvectors."""
    print(f"Computing {n_eigenvectors} eigenvectors...")
    eigenvalues, eigenvectors = eigsh(adj_matrix, k=n_eigenvectors, which='LM')
    print(f"  → Found {len(eigenvalues)} eigenvalues")
    return eigenvalues, eigenvectors

def byte_to_nibble(byte_val: int, eigenvalue: float, magnitude: float):
    """Convert byte to nibble switch with eigenmass."""
    # Map byte to domain (0-3)
    domain = byte_val & 0x3
    # Map byte to control (0-3)
    control = (byte_val >> 6) & 0x3
    # Magnitude determines polarity
    polarity = 1 if magnitude > 0.01 else -1

    return NibbleSwitch.from_parts(control, domain, polarity)

def flow_hutter_through_tsm(data: bytes, eigenvalues, eigenvectors, steps_per_cluster=50):
    """Flow Hutter data through TSM as hyperfluid with eigenmass."""
    print("\nFlowing Hutter data through TSM manifold...")

    cache_dir = OUTPUT_DIR / "tsm_cache"
    tsm = TopologicalStateMachine(cache_dir=cache_dir)

    flow_log = []

    # For each eigenvector cluster
    for cluster_idx in range(len(eigenvalues)):
        print(f"\n  Eigenvector Cluster {cluster_idx + 1}")
        print(f"    Eigenvalue: {eigenvalues[cluster_idx]:.6f}")

        # Get top bytes by eigenvector magnitude
        magnitudes = np.abs(eigenvectors[:, cluster_idx])
        top_bytes = np.argsort(magnitudes)[-100:][::-1]

        cluster_trajectory = []
        for step in range(steps_per_cluster):
            if step < len(top_bytes):
                byte_val = int(top_bytes[step])
                magnitude = float(magnitudes[byte_val])
                eigenvalue_q16 = int(eigenvalues[cluster_idx] * 65536) & 0xFFFF
                magnitude_q16 = int(magnitude * 65536) & 0xFFFF
                nib = byte_to_nibble(byte_val, eigenvalues[cluster_idx], magnitude)

                new_state = tsm.transition(nib.control, nib.domain, nib.polarity, eigenvalue_q16, magnitude_q16)
            else:
                # Autonomous flow
                nib = NibbleSwitch.from_parts(1, cluster_idx % 4, 1)
                new_state = tsm.transition(nib.control, nib.domain, nib.polarity)

            cluster_trajectory.append({
                "step": tsm.step,
                "byte": int(top_bytes[step]) if step < len(top_bytes) else None,
                "state": str(new_state),
                "curvature": new_state.curvature,
                "locus": hex(new_state.locus)
            })

            if (step + 1) % 10 == 0:
                print(f"      Step {step + 1}/{steps_per_cluster}: locus={new_state.locus:08x}, curvature={new_state.curvature}")

        flow_log.append({
            "cluster": cluster_idx + 1,
            "eigenvalue": float(eigenvalues[cluster_idx]),
            "trajectory": cluster_trajectory,
            "final_state": str(tsm.state),
            "final_curvature": tsm.state.curvature,
            "final_locus": hex(tsm.state.locus)
        })

    return tsm, flow_log

def main():
    print("=" * 70)
    print("  HUTTER PRIZE EIGENVECTOR COMPRESSION TEST")
    print("=" * 70)

    # Phase 1: Load data
    print("\n[1/5] Loading Hutter Prize data...")
    data = load_hutter_data()  # Full dataset

    # Phase 2: Build adjacency matrix
    print("\n[2/5] Building byte adjacency matrix...")
    adj, byte_counts = build_byte_adjacency(data, window_size=8)

    # Phase 3: Compute eigenvectors
    print("\n[3/5] Computing eigenvectors...")
    eigenvalues, eigenvectors = compute_eigenvectors(adj, n_eigenvectors=5)
    for i, (ev, vec) in enumerate(zip(eigenvalues, eigenvectors.T)):
        print(f"  Eigenvalue {i+1}: {ev:.6f}")

    # Phase 4: Flow through TSM
    print("\n[4/5] Flowing through TSM with eigenmass...")
    tsm, flow_log = flow_hutter_through_tsm(data, eigenvalues, eigenvectors, steps_per_cluster=30)

    # Phase 5: Analyze topology
    print("\n[5/5] Analyzing hyperfluid topology...")
    topo = tsm.topology.summary()
    print(f"  Total TSM steps: {tsm.step}")
    print(f"  Betti-0 (components): {topo['betti_0']}")
    print(f"  Betti-1 (loops): {topo['betti_1']}")
    print(f"  Euler characteristic: {topo['euler_characteristic']}")
    print(f"  Avg curvature: {topo['avg_curvature']:.4f}")

    # Save results
    print(f"\nSaving results to {OUTPUT_DIR}...")
    import json
    results = {
        "data_size_bytes": len(data),
        "eigenvalues": eigenvalues.tolist(),
        "flow_log": flow_log,
        "topology": topo,
        "tsm_final_state": str(tsm.state),
        "cache_stats": tsm.cache.get_stats()
    }

    output_path = OUTPUT_DIR / f"hutter_eigenvector_{tsm.step}_steps.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"  Output: {output_path}")

    # Compression analysis
    original_size = len(data)
    tsm_cache_size = tsm.cache.get_stats()["bank_size_mb"] * 1024 * 1024
    compression_ratio = original_size / tsm_cache_size if tsm_cache_size > 0 else 0

    print(f"\n{'='*70}")
    print("  COMPRESSION ANALYSIS")
    print(f"{'='*70}")
    print(f"  Original data size: {original_size:,} bytes ({original_size/1024/1024:.2f} MB)")
    print(f"  TSM/FAMM cache size: {tsm_cache_size:,} bytes ({tsm_cache_size/1024/1024:.2f} MB)")
    print(f"  Compression ratio: {compression_ratio:.2f}x")
    print(f"  TSM steps: {tsm.step}")
    print(f"  Topology loops: {topo['betti_1']}")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
