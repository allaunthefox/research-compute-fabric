#!/usr/bin/env python3
"""
Eigenvector Hyperfluid through Topological State Machine

Flows eigenvector cluster data through the TSM as a hyperfluid compression
mechanism. Each eigenvector cluster becomes a "fluid packet" that navigates
the TSM manifold, with topological tracking of the flow.

Concept:
  - Eigenvector clusters → NibbleSwitch transitions
  - Cluster magnitude → Transition polarity
  - Cluster eigenvalue → Domain selection
  - Flow trajectory → Manifold topology evolution
"""

import sys
import json
import numpy as np
import sqlite3
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import eigsh
from pathlib import Path
from typing import Dict, List, Tuple
from collections import deque

# Add TSM to path
sys.path.insert(0, str(Path(__file__).parent))
from topological_state_machine import (
    TopologicalStateMachine, NibbleSwitch, ManifoldPoint,
    TopologicalInvariants, StateMachineCache
)

DB_PATH = "/dev/shm/physics_equations.db"
OUTPUT_DIR = Path("/home/allaun/Documents/Research Stack/3-Mathematical-Models/eigenvector_tsm")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_equations() -> List[Tuple[int, str, int, str]]:
    """Load all equations from database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT eq_number, title, domain_id, significance FROM equations ORDER BY eq_number")
    rows = cursor.fetchall()
    cursor.execute("SELECT id, name FROM domains")
    domains = {str(r[0]): r[1] for r in cursor.fetchall()}
    conn.close()
    return [(eq_num, title, domains.get(str(did), "Unknown"), desc or "")
            for eq_num, title, did, desc in rows]

def build_domain_adjacency(equations):
    """Build adjacency matrix based on domain co-occurrence."""
    n = len(equations)

    domain_to_eqs = {}
    for i, (_, _, domain_id, _) in enumerate(equations):
        if domain_id not in domain_to_eqs:
            domain_to_eqs[domain_id] = []
        domain_to_eqs[domain_id].append(i)

    row_indices = []
    col_indices = []
    data = []

    for domain_id, eq_indices in domain_to_eqs.items():
        for i in eq_indices:
            for j in eq_indices:
                if i != j:
                    row_indices.append(i)
                    col_indices.append(j)
                    data.append(1.0 / len(eq_indices))

    adj = csr_matrix((data, (row_indices, col_indices)), shape=(n, n))
    return adj, domain_to_eqs

def find_principal_eigenvectors(adj_matrix, n_eigenvectors=5):
    """Find principal eigenvectors."""
    eigenvalues, eigenvectors = eigsh(adj_matrix, k=n_eigenvectors, which='LM')
    return eigenvalues, eigenvectors

def assign_eigenvector_categories(equations, eigenvectors):
    """Assign each equation to its dominant eigenvector cluster."""
    n_eqs = len(equations)
    n_clusters = eigenvectors.shape[1]

    categories = []
    for i in range(n_eqs):
        magnitudes = np.abs(eigenvectors[i, :])
        dominant_cluster = int(np.argmax(magnitudes))
        dominant_magnitude = float(magnitudes[dominant_cluster])
        categories.append((dominant_cluster, dominant_magnitude))

    return categories

def eigenvector_to_nibble(cluster_idx, magnitude, eigenvalue):
    """
    Convert eigenvector cluster data to NibbleSwitch.

    Mapping:
      - cluster_idx (0-4) → domain (0-3) via modulo
      - magnitude → polarity (positive if > threshold)
      - eigenvalue → control state based on magnitude
    """
    # Map cluster to domain (5 clusters → 4 domains via modulo)
    domain = cluster_idx % 4

    # Magnitude determines polarity
    polarity = 1 if magnitude > 0.1 else -1

    # Eigenvalue determines control state
    # High eigenvalue = ACCEPT (1), Low eigenvalue = REJECT (0)
    control = 1 if eigenvalue > 0.95 else 0

    return NibbleSwitch.from_parts(control, domain, polarity)

def flow_eigenvectors_through_tsm(equations, categories, eigenvalues, steps_per_cluster=50):
    """
    Flow eigenvector data through TSM as hyperfluid.

    For each cluster, create a flow trajectory through the TSM manifold.
    The trajectory is driven by the cluster's eigenvector properties.
    """
    # Initialize TSM
    cache_dir = OUTPUT_DIR / "tsm_cache"
    tsm = TopologicalStateMachine(cache_dir=cache_dir)

    cluster_names = [
        "Electromagnetism & Circuits",
        "Condensed Matter & Superconductivity",
        "Quantum Mechanics & Particle Physics",
        "Materials Science & Engineering",
        "Cognitive & Semantic Systems"
    ]

    flow_log = []

    for cluster_idx in range(len(eigenvalues)):
        print(f"\n  Flowing Cluster {cluster_idx + 1}: {cluster_names[cluster_idx]}")
        print(f"    Eigenvalue: {eigenvalues[cluster_idx]:.6f}")

        # Get equations in this cluster
        cluster_eqs = [(eq, cat[1]) for eq, cat in zip(equations, categories) if cat[0] == cluster_idx]
        cluster_eqs.sort(key=lambda x: x[1], reverse=True)

        print(f"    Equations: {len(cluster_eqs)}")

        # Flow this cluster through TSM
        cluster_trajectory = []
        for step in range(steps_per_cluster):
            # Use top equations to drive transitions
            if step < len(cluster_eqs):
                eq, magnitude = cluster_eqs[step]
                eq_num, title, domain, desc = eq
                # Create nibble from eigenvector data
                nib = eigenvector_to_nibble(cluster_idx, magnitude, eigenvalues[cluster_idx])
            else:
                # Autonomous flow based on current TSM state
                nib = eigenvector_to_nibble(cluster_idx, 0.05, eigenvalues[cluster_idx])

            # Execute transition with eigenmass
            # Convert eigenvalue and magnitude to Q16_16
            eigenvalue_q16 = int(eigenvalues[cluster_idx] * 65536) & 0xFFFF
            magnitude_q16 = int(magnitude * 65536) & 0xFFFF
            new_state = tsm.transition(nib.control, nib.domain, nib.polarity, eigenvalue_q16, magnitude_q16)

            cluster_trajectory.append({
                "step": tsm.step,
                "nibble": str(nib),
                "state": str(new_state),
                "curvature": new_state.curvature,
                "locus": hex(new_state.locus)
            })

            if (step + 1) % 10 == 0:
                print(f"      Step {step + 1}/{steps_per_cluster}: locus={new_state.locus:08x}, curvature={new_state.curvature:.4f}")

        flow_log.append({
            "cluster": cluster_idx + 1,
            "name": cluster_names[cluster_idx],
            "eigenvalue": float(eigenvalues[cluster_idx]),
            "equation_count": len(cluster_eqs),
            "trajectory": cluster_trajectory,
            "final_state": str(tsm.state),
            "final_curvature": tsm.state.curvature,
            "final_locus": hex(tsm.state.locus)
        })

    return tsm, flow_log

def analyze_hyperfluid_topology(tsm, flow_log):
    """Analyze the topological structure of the hyperfluid flow."""
    topo = tsm.topology.summary()

    # Compute cluster-to-cluster transition statistics
    cluster_transitions = {}
    for i, cluster_data in enumerate(flow_log):
        if i < len(flow_log) - 1:
            from_cluster = cluster_data["cluster"]
            to_cluster = flow_log[i + 1]["cluster"]
            key = f"{from_cluster}→{to_cluster}"
            cluster_transitions[key] = cluster_transitions.get(key, 0) + 1

    return {
        "topology": topo,
        "cluster_transitions": cluster_transitions,
        "total_fluid_steps": sum(len(c["trajectory"]) for c in flow_log),
        "final_tsm_state": str(tsm.state)
    }

def main():
    print("=" * 70)
    print("  EIGENVECTOR HYPERFLID THROUGH TOPOLOGICAL STATE MACHINE")
    print("=" * 70)

    # Phase 1: Load eigenvector data
    print("\n[1/5] Loading equations and computing eigenvectors...")
    equations = load_equations()
    print(f"      → {len(equations)} equations loaded")

    adj, domain_to_eqs = build_domain_adjacency(equations)
    print(f"      → Adjacency matrix: {adj.shape}")

    eigenvalues, eigenvectors = find_principal_eigenvectors(adj, n_eigenvectors=5)
    print(f"      → {len(eigenvalues)} eigenvectors computed")

    categories = assign_eigenvector_categories(equations, eigenvectors)
    print(f"      → {len(categories)} equations categorized")

    # Phase 2: Initialize TSM
    print("\n[2/5] Initializing Topological State Machine...")
    cache_dir = OUTPUT_DIR / "tsm_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    print(f"      → Cache: {cache_dir}")

    # Phase 3: Flow eigenvectors as hyperfluid
    print("\n[3/5] Flowing eigenvectors through TSM manifold...")
    tsm, flow_log = flow_eigenvectors_through_tsm(
        equations, categories, eigenvalues, steps_per_cluster=30
    )

    # Phase 4: Analyze topology
    print("\n[4/5] Analyzing hyperfluid topology...")
    analysis = analyze_hyperfluid_topology(tsm, flow_log)
    print(f"      → Total fluid steps: {analysis['total_fluid_steps']}")
    print(f"      → Betti-0 (components): {analysis['topology']['betti_0']}")
    print(f"      → Betti-1 (loops): {analysis['topology']['betti_1']}")
    print(f"      → Euler characteristic: {analysis['topology']['euler_characteristic']}")
    print(f"      → Avg curvature: {analysis['topology']['avg_curvature']:.4f}")

    # Phase 5: Save results
    print("\n[5/5] Saving hyperfluid analysis...")

    results = {
        "metadata": {
            "equations_count": len(equations),
            "eigenvalues": eigenvalues.tolist(),
            "cluster_names": [
                "Electromagnetism & Circuits",
                "Condensed Matter & Superconductivity",
                "Quantum Mechanics & Particle Physics",
                "Materials Science & Engineering",
                "Cognitive & Semantic Systems"
            ]
        },
        "flow_log": flow_log,
        "topology_analysis": analysis,
        "tsm_final_state": tsm.self_reflect()
    }

    output_path = OUTPUT_DIR / f"eigenvector_hyperfluid_{tsm.step}_steps.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"      → Output: {output_path}")

    print(f"\n{'='*70}")
    print("  HYPERFLID FLOW COMPLETE")
    print(f"{'='*70}")
    print(f"  Total TSM steps: {tsm.step}")
    print(f"  Fluid clusters: {len(flow_log)}")
    print(f"  Final locus: {hex(tsm.state.locus)}")
    print(f"  Final curvature: {tsm.state.curvature:.4f}")
    print(f"  Topology loops: {analysis['topology']['betti_1']}")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
