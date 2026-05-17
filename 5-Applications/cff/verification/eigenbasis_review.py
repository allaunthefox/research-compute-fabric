#!/usr/bin/env python3
"""
Eigenbasis Review of the Full Physics Constraint Graph

Reviews all 773 equations through the lens of eigenvectors of the symmetrized
constraint adjacency matrix. The eigenvectors define the "natural storage modes"
of the physics knowledge graph — equations that co-locate in eigenvector space
are structurally related regardless of domain assignment.

Outputs:
  1. Spectral gap analysis (which eigenvalues dominate)
  2. Eigenvector coherence clusters (equations that co-locate)
  3. Chiral reclassification under spectral projection
  4. Equations that shift domain/layer under eigenbasis
  5. Topologically isolated equations (zero spectral connectivity)
"""

import sys
sys.path.insert(0, "/home/allaun")

import json
import sqlite3
import numpy as np
from typing import Dict, List, Tuple, Set
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class EigenEquation:
    eq_id: int
    name: str
    domain: str
    layer: int
    eigenvector_idx: int
    eigenvector_coordinate: float
    eigenvalue: float
    spectral_mass: float    # |coordinate| * |eigenvalue|
    chiral_old: str
    chiral_new: str
    shifted: bool


def load_graph(db_path: str):
    """Load full constraint graph including all chain edges and any direct edges."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    edges = []
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='invariant_chains'")
    if cur.fetchone():
        for (a, b) in [("layer1_eq_id","layer2_eq_id"),("layer2_eq_id","layer3_eq_id"),("layer3_eq_id","layer4_eq_id")]:
            cur.execute(f"SELECT DISTINCT {a} src, {b} dst FROM invariant_chains WHERE {a} IS NOT NULL AND {b} IS NOT NULL AND {a}!=0 AND {b}!=0")
            for r in cur.fetchall():
                edges.append((int(r["src"]), int(r["dst"])))

    edges = list(set(edges))

    all_ids = set()
    for s, d in edges:
        all_ids.add(s); all_ids.add(d)
    node_ids = sorted(all_ids)

    # Equation metadata
    cur.execute("""
        SELECT e.id, e.title, d.name as domain, d.ontological_layer
        FROM equations e JOIN domains d ON e.domain_id=d.id
        ORDER BY e.id
    """)
    eq_meta = {}
    for r in cur.fetchall():
        eq_meta[r["id"]] = {
            "title": r["title"],
            "domain": r["domain"],
            "layer": r["ontological_layer"] or 0,
        }

    # Existing chiral
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chiral_eigenmass'")
    old_chiral = {}
    if cur.fetchone():
        cur.execute("SELECT equation_id, chiral_state, chiral_residual FROM chiral_eigenmass")
        for r in cur.fetchall():
            old_chiral[r["equation_id"]] = {
                "state": r["chiral_state"],
                "residual": r["chiral_residual"],
            }

    conn.close()
    return edges, node_ids, eq_meta, old_chiral


def build_adjacency(edges, node_ids):
    """Build symmetrized adjacency matrix."""
    node_map = {eid: i for i, eid in enumerate(node_ids)}
    n = len(node_ids)
    A = np.zeros((n, n), dtype=np.float64)

    for src, dst in edges:
        if src in node_map and dst in node_map:
            i, j = node_map[src], node_map[dst]
            A[i, j] += 1.0

    S = (A + A.T) / 2.0
    return A, S, node_map


def compute_eigen(S):
    """Compute eigen-decomposition, sorted by descending abs eigenvalue."""
    e_vals, e_vecs = np.linalg.eigh(S)
    # Sort by descending absolute eigenvalue
    order = np.argsort(-np.abs(e_vals))
    e_vals = e_vals[order]
    e_vecs = e_vecs[:, order]
    return e_vals, e_vecs


def compute_spectral_mass(e_vals, e_vecs):
    """Compute spectral mass per node per eigenmode."""
    n_modes = len(e_vals)
    masses = np.zeros((len(e_vecs), n_modes))
    for k in range(n_modes):
        masses[:, k] = np.abs(e_vecs[:, k]) * np.abs(e_vals[k])
    return masses


def classify_chiral_from_spectral(node_idx, e_vals, e_vecs, masses):
    """
    Classify chiral state from spectral properties.

    In eigenbasis terms:
      - A node is "achiral_stable" if it has high spectral mass concentrated
        in a few dominant modes and low across-mode dispersion.
      - "left_handed_mass_bias" if its forward (AMVR) projection dominates
      - "right_handed_vector_bias" if its reverse (AVMR) projection dominates
      - "chiral_scarred" if spectral mass is anomalously low or dispersed
    """
    total_mass = masses[node_idx].sum()
    if total_mass < 1e-12:
        return "chiral_scarred", 1.0

    # Concentration: what fraction in top 3 modes?
    top3 = np.sort(masses[node_idx])[-3:].sum()
    concentration = top3 / total_mass

    # Participation ratio (inverse of IPR = how many modes participate)
    if total_mass > 0:
        m_norm = masses[node_idx] / total_mass
        ipr = (m_norm ** 2).sum()
        participation = 1.0 / ipr if ipr > 0 else float('inf')
    else:
        participation = 0

    total_modes = len(e_vals)
    pr_ratio = participation / total_modes

    # Chiral residual = 1 - concentration * pr_ratio (clamped)
    chiral_residual = 1.0 - min(1.0, concentration * min(1.0, pr_ratio))

    if concentration > 0.7 and pr_ratio < 0.3:
        state = "achiral_stable"
    elif concentration < 0.3:
        state = "chiral_scarred"
    elif masses[node_idx, :len(e_vals)//2].sum() > masses[node_idx, len(e_vals)//2:].sum():
        state = "left_handed_mass_bias"  # positive-half modes dominate
    else:
        state = "right_handed_vector_bias"  # negative-half modes dominate

    return state, chiral_residual


def detect_shifts(node_ids, eq_meta, old_chiral, e_vals, e_vecs, masses):
    """Detect equations whose classification shifts under eigenbasis."""
    shifts = []
    for i, eid in enumerate(node_ids):
        state_new, res_new = classify_chiral_from_spectral(i, e_vals, e_vecs, masses)
        meta = eq_meta.get(eid, {"title": f"Eq_{eid}", "domain": "Unknown", "layer": 0})
        old = old_chiral.get(eid, {"state": "unknown", "residual": 0.0})

        shifted = (state_new != old["state"])

        best_mode = np.argmax(masses[i])
        coordinate = e_vecs[i, best_mode]

        shifts.append(EigenEquation(
            eq_id=eid,
            name=meta["title"],
            domain=meta["domain"],
            layer=meta["layer"],
            eigenvector_idx=best_mode,
            eigenvector_coordinate=float(coordinate),
            eigenvalue=float(e_vals[best_mode]),
            spectral_mass=float(masses[i].sum()),
            chiral_old=old["state"],
            chiral_new=state_new,
            shifted=shifted,
        ))

    return shifts


def find_spectral_clusters(e_vecs, node_ids, eq_meta, top_modes=5):
    """Find equations that cluster together in eigenvector space."""
    clusters = defaultdict(list)
    for i, eid in enumerate(node_ids):
        coords = e_vecs[i, :top_modes]
        label = eid % 100  # simplistic, good enough for review
        for k in range(top_modes):
            key = (k, round(coords[k] * 100))
            clusters[key].append(eid)
    return clusters


def find_isolated(node_ids, mass_matrix, threshold=1e-6):
    """Find equations with near-zero spectral connectivity."""
    isolated = []
    for i, eid in enumerate(node_ids):
        if mass_matrix[i].sum() < threshold:
            isolated.append(eid)
    return isolated


def run_eigenbasis_review(db_path: str) -> dict:
    print("Loading graph...")
    edges, node_ids, eq_meta, old_chiral = load_graph(db_path)
    print(f"  {len(edges)} edges, {len(node_ids)} nodes")

    A, S, node_map = build_adjacency(edges, node_ids)
    print(f"  Adjacency: {A.sum():.0f} total edges, {np.count_nonzero(A)} directed connections")

    print("Computing eigen-decomposition...")
    e_vals, e_vecs = compute_eigen(S)

    # Spectral gap
    gaps = np.diff(np.abs(e_vals))
    max_gap_idx = np.argmax(np.abs(gaps))
    print(f"  {len(e_vals)} eigenvalues, range=[{e_vals[0]:.3f}, {e_vals[-1]:.3f}]")
    print(f"  Max spectral gap at index {max_gap_idx}: {gaps[max_gap_idx]:.3f}")

    masses = compute_spectral_mass(e_vals, e_vecs)

    print("Detecting shifts...")
    eq_shifts = detect_shifts(node_ids, eq_meta, old_chiral, e_vals, e_vecs, masses)

    shifted = [eq for eq in eq_shifts if eq.shifted]
    not_found = [eq for eq in eq_shifts if eq.chiral_old == "unknown"]
    isolated = find_isolated(node_ids, masses)

    print(f"  Shifts: {len(shifted)} equations changed classification")
    print(f"  New (not in old chiral): {len(not_found)} equations")
    print(f"  Isolated (near-zero spectral mass): {len(isolated)} equations")

    clusters = find_spectral_clusters(e_vecs, node_ids, eq_meta)

    # Build report
    report = {
        "num_nodes": len(node_ids),
        "num_edges": len(edges),
        "num_eigenvalues": len(e_vals),
        "eigenvalue_range": [float(e_vals[0]), float(e_vals[-1])],
        "spectral_gap_max_idx": int(max_gap_idx),
        "spectral_gap_max_value": float(gaps[max_gap_idx]),
        "num_shifted": len(shifted),
        "num_new_equations": len(not_found),
        "num_isolated": len(isolated),
        "shifted_equations": [
            {
                "eq_id": eq.eq_id,
                "name": eq.name[:80],
                "domain": eq.domain,
                "layer": eq.layer,
                "chiral_old": eq.chiral_old,
                "chiral_new": eq.chiral_new,
                "dominant_mode": eq.eigenvector_idx,
                "spectral_mass": round(eq.spectral_mass, 6),
                "eigenvalue": round(float(eq.eigenvalue), 4),
            }
            for eq in sorted(shifted, key=lambda x: -x.spectral_mass)
        ],
        "new_equations": [
            {
                "eq_id": eq.eq_id,
                "name": eq.name[:80],
                "domain": eq.domain,
                "chiral_new": eq.chiral_new,
                "spectral_mass": round(eq.spectral_mass, 6),
            }
            for eq in sorted(not_found, key=lambda x: -x.spectral_mass)
        ],
        "isolated_equations": [
            {
                "eq_id": eid,
                "name": eq_meta.get(eid, {"title": f"Eq_{eid}"})["title"][:80],
                "domain": eq_meta.get(eid, {"domain": "Unknown"})["domain"],
            }
            for eid in sorted(isolated)
        ],
        "top_eigenmodes": [
            {
                "mode": k,
                "eigenvalue": round(float(e_vals[k]), 4),
                "num_nodes_below_threshold": int((np.abs(e_vecs[:, k]) > 0.01).sum()),
                "top_nodes": [
                    {
                        "eq_id": node_ids[i],
                        "name": eq_meta.get(node_ids[i], {"title": f"Eq_{node_ids[i]}"})["title"][:60],
                        "coordinate": round(float(e_vecs[i, k]), 6),
                    }
                    for i in np.argsort(-np.abs(e_vecs[:, k]))[:10]
                ],
            }
            for k in range(min(5, len(e_vals)))
        ],
    }

    return report


def print_report(report: dict):
    """Print human-readable eigenbasis review."""
    print()
    print("=" * 70)
    print("EIGENBASIS REVIEW — Constraint Graph Spectral Analysis")
    print("=" * 70)
    print(f"  Nodes: {report['num_nodes']}")
    print(f"  Edges: {report['num_edges']}")
    print(f"  Eigenvalues: {report['num_eigenvalues']}")
    print(f"  Range: [{report['eigenvalue_range'][0]:.3f}, {report['eigenvalue_range'][1]:.3f}]")
    print(f"  Max spectral gap: {report['spectral_gap_max_value']:.3f} (mode {report['spectral_gap_max_idx']})")
    print()

    print(f"  Shifted classifications: {report['num_shifted']}")
    print(f"  New equations (not in chiral_eigenmass): {report['num_new_equations']}")
    print(f"  Topologically isolated: {report['num_isolated']}")
    print()

    if report["shifted_equations"]:
        print("--- SHIFTED EQUATIONS ---")
        print(f"  {'ID':>5} {'Name':60s} {'Old':20s} {'New':20s} {'Mass':>10s}")
        print(f"  {'-'*5} {'-'*60} {'-'*20} {'-'*20} {'-'*10}")
        for eq in report["shifted_equations"]:
            print(f"  {eq['eq_id']:>5} {eq['name'][:60]:60s} {eq['chiral_old']:20s} {eq['chiral_new']:20s} {eq['spectral_mass']:10.6f}")
        print()

    if report["new_equations"]:
        print("--- NEW EQUATIONS (not in old chiral) ---")
        for eq in report["new_equations"][:15]:
            print(f"  #{eq['eq_id']:>4} {eq['chiral_new']:25s} {eq['name'][:70]}")
        if len(report["new_equations"]) > 15:
            print(f"  ... and {len(report['new_equations']) - 15} more")
        print()

    if report["isolated_equations"]:
        print("--- ISOLATED EQUATIONS (near-zero spectral mass) ---")
        for eq in report["isolated_equations"][:10]:
            print(f"  #{eq['eq_id']:>4} {eq['domain']:25s} {eq['name'][:60]}")
        print()

    print("--- TOP EIGENMODES ---")
    for mode in report["top_eigenmodes"]:
        print(f"  Mode {mode['mode']}: λ = {mode['eigenvalue']:.4f}  ({mode['num_nodes_below_threshold']} nodes |coord| > 0.01)")
        for n in mode["top_nodes"][:5]:
            print(f"    #{n['eq_id']:>4} coord={n['coordinate']:+8.4f}  {n['name']}")
        print()


if __name__ == "__main__":
    db_path = "/home/allaun/physics_equations.db"
    report = run_eigenbasis_review(db_path)
    print_report(report)

    # Save to file
    with open("/home/allaun/cff/eigenbasis_review.json", "w") as f:
        json.dump(report, f, indent=2, sort_keys=True, default=str)
    print("Report saved to /home/allaun/cff/eigenbasis_review.json")
