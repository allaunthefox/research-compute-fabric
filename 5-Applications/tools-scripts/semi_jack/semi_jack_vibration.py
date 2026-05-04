#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
semi_jack_vibration.py — Vibration matrix analysis for Semi-Jack geometry

Assembles the global stiffness K, geometric stiffness K_geo (from atmospheric
pressure), and mass matrix M for a 3D pin-jointed truss.

Atmospheric pressure contribution:
  Each strut acts as a cylinder under external pressure P_atm.
  Net compressive axial force = P_atm × A_cross_section.
  This modifies K via the geometric (stress-stiffening) matrix K_geo.
  Under compression K_geo is negative → reduces effective stiffness → lowers ω.

Eigenvalue problem:
  (K + K_geo) u = ω² M u
  Natural frequencies: f_n = ω_n / (2π)

Boundary conditions:
  Leaf nodes (no children) = fixed to ground (zero displacement).
  Root + internal nodes = free.

Usage:
    .venv-eng/bin/python 5-Applications/scripts/semi_jack_vibration.py
    .venv-eng/bin/python 5-Applications/scripts/semi_jack_vibration.py --json 5-Applications/out/sovereign_jenga/quantum_annealed/merkle_tree_nspace.json
    .venv-eng/bin/python 5-Applications/scripts/semi_jack_vibration.py --no-atm   # vacuum comparison
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import List, Set, Tuple

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from math_harness_compat import xp, AnyArray
from scipy.linalg import eigh

# ── Physical constants ─────────────────────────────────────────────────────────

ATM_PRESSURE_PA   = 101_325.0   # Pa — standard atmosphere (ISO 2533)
G_MS2             = 9.80665     # m/s² — standard gravity

# ── Material: SLS PA12 (SI units throughout) ──────────────────────────────────

E_PA12_PA         = 1_700e6     # Young's modulus, Pa
RHO_PA12_KG_M3    = 1_010.0     # density, kg/m³


# ── Geometry loader ────────────────────────────────────────────────────────────

def load_geometry(path: Path):
    data = json.loads(path.read_text())
    nodes = {n["id"]: n for n in data["nodes"]}
    edges = [(e[0], e[1]) for e in data["edges"]]

    # Identify leaf nodes (appear only as children, never as parents)
    parents = {e[0] for e in edges}
    all_ids  = set(nodes.keys())
    leaves   = all_ids - parents

    return nodes, edges, leaves


# ── Element matrices (3-DOF pin-jointed truss element) ────────────────────────
# DOFs per node: [ux, uy, uz].  Element connects node i (DOFs 0-2) to j (DOFs 3-5).

def direction_cosines(ni: dict, nj: dict) -> Tuple[float, float, float, float]:
    dx = (nj["x"] - ni["x"]) * 1e-3   # mm → m
    dy = (nj["y"] - ni["y"]) * 1e-3
    dz = (nj["z"] - ni["z"]) * 1e-3
    L  = math.sqrt(dx**2 + dy**2 + dz**2)
    if L < 1e-12:
        return 0.0, 0.0, 0.0, 0.0
    return dx/L, dy/L, dz/L, L


def element_stiffness(
    ni: dict, nj: dict, radius_m: float
) -> Tuple[AnyArray, float, float]:
    """
    6×6 elastic stiffness matrix in global coords.
    Returns (k_global, L_m, A_m2).
    """
    lx, ly, lz, L = direction_cosines(ni, nj)
    if L < 1e-12:
        return xp.zeros((6,6)), 0.0, 0.0

    A = math.pi * radius_m**2
    EA_over_L = E_PA12_PA * A / L

    # Direction cosine vector
    d = xp.array([lx, ly, lz])

    # Local-to-global: k = EA/L * [d; -d] ⊗ [d; -d]
    dext = xp.concatenate([d, -d])
    k_global = EA_over_L * xp.outer(dext, dext)
    return k_global, L, A


def element_geo_stiffness(
    ni: dict, nj: dict, radius_m: float, axial_force_N: float
) -> AnyArray:
    """
    6×6 geometric stiffness matrix for axial pre-load P.
    For a truss element: k_geo = P/L * [I -I; -I I] projected onto
    the transverse plane (perpendicular to strut axis).
    Negative P (compression) → negative k_geo → softens structure.
    """
    lx, ly, lz, L = direction_cosines(ni, nj)
    if L < 1e-12:
        return xp.zeros((6,6))

    d = xp.array([lx, ly, lz])
    I3 = xp.eye(3)
    # Transverse projector: I - d⊗d
    Pt = I3 - xp.outer(d, d)

    k_geo_3 = (axial_force_N / L) * Pt
    k_geo = xp.zeros((6, 6))
    k_geo[0:3, 0:3] =  k_geo_3
    k_geo[3:6, 3:6] =  k_geo_3
    k_geo[0:3, 3:6] = -k_geo_3
    k_geo[3:6, 0:3] = -k_geo_3
    return k_geo


def element_mass(
    ni: dict, nj: dict, radius_m: float
) -> AnyArray:
    """
    6×6 consistent mass matrix in global coords.
    m = ρAL/6 * [2I I; I 2I]  (consistent formulation for truss)
    """
    _, L, A = element_stiffness(ni, nj, radius_m)
    if L < 1e-12:
        return xp.zeros((6,6))

    m_total = RHO_PA12_KG_M3 * A * L
    I3 = xp.eye(3)
    m = xp.zeros((6, 6))
    m[0:3, 0:3] = 2/6 * m_total * I3
    m[3:6, 3:6] = 2/6 * m_total * I3
    m[0:3, 3:6] = 1/6 * m_total * I3
    m[3:6, 0:3] = 1/6 * m_total * I3
    return m


# ── Global assembly ────────────────────────────────────────────────────────────

def assemble(
    nodes:     dict,
    edges:     List[Tuple[int,int]],
    leaves:    Set[int],
    radius_mm: float,
    swl_N:     float,
    with_atm:  bool,
) -> Tuple[AnyArray, AnyArray, List[int], dict]:
    """
    Assemble global K, K_geo, M.
    Returns (K_total, M, free_dofs, diagnostics).
    """
    node_ids  = sorted(nodes.keys())
    id_to_idx = {nid: i for i, nid in enumerate(node_ids)}
    n_nodes   = len(node_ids)
    n_dofs    = n_nodes * 3

    radius_m  = radius_mm * 1e-3
    A_m2      = math.pi * radius_m**2

    # Atmospheric pressure compressive force on each strut end
    # F_atm = P_atm × A_cross  (acts inward = compression = negative)
    atm_force_N = -ATM_PRESSURE_PA * A_m2 if with_atm else 0.0

    K = xp.zeros((n_dofs, n_dofs))
    M = xp.zeros((n_dofs, n_dofs))

    diag = {
        "atm_force_per_strut_N": abs(atm_force_N),
        "n_struts": len(edges),
        "radius_mm": radius_mm,
        "A_mm2": A_m2 * 1e6,
    }

    # Identify root (no parent in edge list)
    child_ids = {e[1] for e in edges}
    root_id   = next(nid for nid in node_ids if nid not in child_ids)

    # Root force distribution: each direct child carries swl_N * load_frac
    root_force = nodes[root_id].get("F", swl_N)

    for p_id, c_id in edges:
        ni = nodes[p_id]
        nj = nodes[c_id]

        k_el, L_m, _area = element_stiffness(ni, nj, radius_m)

        # Structural axial force in strut (from applied SWL)
        child_F   = nj.get("F", 0.0)
        frac      = child_F / max(root_force, 1e-9)
        strut_V   = swl_N * frac                       # vertical component
        lx, ly, lz, _L = direction_cosines(ni, nj)
        cos_ang   = abs(lz) if L_m > 1e-12 else 1.0
        strut_axial = strut_V / max(cos_ang, 1e-6)     # along strut axis

        # Atmospheric compressive pre-load
        total_axial_N = -strut_axial + atm_force_N   # compression = negative

        k_geo = element_geo_stiffness(ni, nj, radius_m, total_axial_N)
        m_el  = element_mass(ni, nj, radius_m)

        # DOF indices
        ri = id_to_idx[p_id] * 3
        rj = id_to_idx[c_id] * 3
        idx = [ri, ri+1, ri+2, rj, rj+1, rj+2]

        for a, ga in enumerate(idx):
            for b, gb in enumerate(idx):
                K[ga, gb] += k_el[a, b] + k_geo[a, b]
                M[ga, gb] += m_el[a, b]

    # ── Boundary conditions: fix leaf nodes ───────────────────────────────────
    fixed_dofs: Set[int] = set()
    for leaf_id in leaves:
        base = id_to_idx[leaf_id] * 3
        fixed_dofs.update([base, base+1, base+2])

    all_dofs  = list(range(n_dofs))
    free_dofs = [d for d in all_dofs if d not in fixed_dofs]

    return K, M, free_dofs, diag


# ── Eigenvalue solve ───────────────────────────────────────────────────────────

def natural_frequencies(
    K: AnyArray,
    M: AnyArray,
    free_dofs: List[int],
    n_modes: int = 10,
) -> AnyArray:
    """
    Solve generalised eigenvalue problem on free DOFs.
    Returns natural frequencies in Hz.
    """
    Kf = K[xp.ix_(free_dofs, free_dofs)]
    Mf = M[xp.ix_(free_dofs, free_dofs)]

    if Kf.shape[0] == 0:
        return xp.array([])

    # Regularise: add small diagonal to M to avoid singularity
    Mf += xp.eye(Mf.shape[0]) * 1e-18

    n_req = min(n_modes, Kf.shape[0] - 1)
    if n_req < 1:
        return xp.array([])

    try:
        # eigh for symmetric matrices → real eigenvalues
        eigenvalues, _ = eigh(Kf, Mf, subset_by_index=[0, n_req-1])
        # ω² = eigenvalue, clip negatives (rigid-body / numerical noise)
        omega2 = xp.clip(eigenvalues, 0, None)
        return xp.sqrt(omega2) / (2 * math.pi)   # Hz
    except Exception as e:
        print(f"  [eigensolve warning] {e}", file=sys.stderr)
        return xp.array([])


# ── Report ─────────────────────────────────────────────────────────────────────

def run(
    json_path: Path,
    radius_mm: float,
    swl_N:     float,
    n_modes:   int,
    with_atm:  bool,
):
    nodes, edges, leaves = load_geometry(json_path)
    print(f"\n  {'='*66}")
    print(f"  Semi-Jack Vibration Matrix Analysis")
    print(f"  {'='*66}")
    print(f"  Geometry : {json_path.name}")
    print(f"  Nodes    : {len(nodes)}  Edges: {len(edges)}  Leaves: {len(leaves)}")
    print(f"  Radius   : {radius_mm} mm   SWL: {swl_N:.1f} N ({swl_N/G_MS2:.2f} kg)")
    print(f"  Atm P    : {'101325 Pa (standard atmosphere)' if with_atm else 'OFF (vacuum)'}")
    print(f"  Material : SLS PA12  E={E_PA12_PA/1e6:.0f} MPa  ρ={RHO_PA12_KG_M3} kg/m³")
    print()

    K, M, free_dofs, diag = assemble(
        nodes, edges, leaves, radius_mm, swl_N, with_atm
    )

    print(f"  System size : {K.shape[0]} DOFs  ({len(free_dofs)} free after BCs)")
    print(f"  Strut area  : {diag['A_mm2']:.3f} mm²")
    if with_atm:
        print(f"  Atm load/strut: {diag['atm_force_per_strut_N']:.4f} N compressive")
    print()

    freqs = natural_frequencies(K, M, free_dofs, n_modes)

    if len(freqs) == 0:
        print("  No free DOFs — structure is fully constrained.")
        return freqs

    print(f"  NATURAL FREQUENCIES (first {len(freqs)} modes)")
    print(f"  {'-'*50}")
    for i, f in enumerate(freqs):
        label = ""
        if i == 0:  label = "  ← fundamental"
        if f < 20:  label += "  ⚠ near audible resonance"
        print(f"  Mode {i+1:3d}: {f:12.2f} Hz{label}")

    print()
    print(f"  Fundamental period : {1/freqs[0]*1000:.3f} ms" if freqs[0] > 0 else "")
    return freqs


def compare(json_path: Path, radius_mm: float, swl_N: float, n_modes: int):
    """Run with and without atmosphere, show delta."""
    print("\n  Running vacuum baseline...")
    f_vac = run(json_path, radius_mm, swl_N, n_modes, with_atm=False)

    print("\n  Running with standard atmosphere (101325 Pa)...")
    f_atm = run(json_path, radius_mm, swl_N, n_modes, with_atm=True)

    if len(f_vac) == 0 or len(f_atm) == 0:
        return

    n = min(len(f_vac), len(f_atm))
    print(f"\n  {'='*66}")
    print(f"  ATMOSPHERIC PRESSURE EFFECT ON VIBRATION MODES")
    print(f"  {'='*66}")
    print(f"  {'Mode':6s} {'Vacuum Hz':>12s} {'Atm Hz':>12s} {'Delta Hz':>12s} {'Delta %':>10s}")
    print(f"  {'-'*56}")
    for i in range(n):
        delta    = f_atm[i] - f_vac[i]
        delta_pc = 100.0 * delta / max(f_vac[i], 1e-9)
        flag = "  ↓ softened" if delta < -0.01 * f_vac[i] else ""
        print(
            f"  {i+1:6d} {f_vac[i]:12.2f} {f_atm[i]:12.2f} "
            f"{delta:12.2f} {delta_pc:10.3f}%{flag}"
        )
    print(f"  {'='*66}\n")


def main():
    ap = argparse.ArgumentParser(description="Semi-Jack vibration matrix analysis")
    ap.add_argument("--json",    default="5-Applications/out/sovereign_jenga/quantum_annealed/merkle_tree_nspace.json")
    ap.add_argument("--radius",  type=float, default=4.52,  help="Tubule radius mm")
    ap.add_argument("--swl",     type=float, default=104.0, help="SWL in Newtons")
    ap.add_argument("--modes",   type=int,   default=10,    help="Number of modes")
    ap.add_argument("--no-atm",  action="store_true",       help="Vacuum only (no atmosphere)")
    ap.add_argument("--no-compare", action="store_true",    help="Skip side-by-side comparison")
    args = ap.parse_args()

    path = Path(args.json)
    if not path.exists():
        path = Path(__file__).parent.parent / args.json
    if not path.exists():
        print(f"ERROR: {args.json} not found", file=sys.stderr)
        sys.exit(1)

    if args.no_atm:
        run(path, args.radius, args.swl, args.modes, with_atm=False)
    elif args.no_compare:
        run(path, args.radius, args.swl, args.modes, with_atm=True)
    else:
        compare(path, args.radius, args.swl, args.modes)


if __name__ == "__main__":
    main()
