#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
semi_jack_geometry_search.py — n-space geometry search for the Semi-Jack

A "perfect mass in n-space" is the geometry where stress is perfectly
uniform across every node in the Merkle tree — the attractor state where
no node is over-loaded and none is under-utilised. Every strut operates
at the same fraction of its capacity simultaneously.

The parameter space (n-space) for a depth-D tree:
    branch_angle[0..D-1]    — angle from vertical per level (degrees)
    az_offset[0..D-1]       — azimuthal rotation between levels (degrees)
    branching_factor        — children per node (2..6)
    tubule_radius           — strut cross-section radius (mm)

Total: 2D + 2 dimensions.  Default D=4 → 10D search space.

Fitness = stress_variance across all edges + constraint penalties.
Perfect geometry → fitness = 0.

Parallel iteration: each worker evaluates one candidate independently.
The main loop keeps the top-K survivors, perturbs them, and re-evaluates.
No shared state between workers — pure function evaluation.

Usage:
    python 5-Applications/scripts/semi_jack_geometry_search.py
    python 5-Applications/scripts/semi_jack_geometry_search.py --depth 4 --pop 64 --iters 50
    python 5-Applications/scripts/semi_jack_geometry_search.py --depth 4 --workers 8 --out best.json
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── Constants (mirror constraint_model) ───────────────────────────────────────

PROOF_LOAD_FACTOR   = 2.0
DESIGN_FAIL_FACTOR  = 3.0

# Default material: SLS PA12 (strut structural limits)
MAT_YIELD_MPA = 70.0
MAT_ULT_MPA   = 95.0

# Search space bounds
ANGLE_MIN, ANGLE_MAX     = 5.0,  60.0   # branch angle from vertical (deg)
AZ_MIN,    AZ_MAX        = 0.0, 180.0   # azimuthal offset (deg)
BF_MIN,    BF_MAX        = 2,    6      # branching factor
RADIUS_MIN, RADIUS_MAX   = 0.3,  5.0   # tubule radius (mm)

# ── Parametric tree geometry ───────────────────────────────────────────────────

@dataclass
class GNode:
    id:       int
    x:        float
    y:        float
    z:        float
    load_frac: float          # fraction of root SWL at this node
    parent:   Optional[int]  = None
    depth:    int            = 0

@dataclass
class Candidate:
    branch_angles:  List[float]   # one per depth level
    az_offsets:     List[float]   # azimuthal rotation per level (deg)
    branching_factor: int
    tubule_radius:  float
    fitness:        float = float("inf")
    nodes:          List[GNode]  = field(default_factory=list)
    edges:          List[Tuple[int,int]] = field(default_factory=list)


def generate_tree(
    depth:           int,
    branch_angles:   List[float],
    az_offsets:      List[float],
    branching_factor: int,
    height_per_level: float = 6.0,   # mm per level
) -> Tuple[List[GNode], List[Tuple[int,int]]]:
    """
    Build a rooted tree in 3D.
    - Root at (0, 0, 0).
    - At each level, children are placed symmetrically around the parent,
      at branch_angle[level] from vertical, spaced evenly in azimuth,
      with az_offsets[level] rotating the whole fan at that level.
    - load_frac halves (for binary) or divides by branching_factor at each step.
    """
    nodes: List[GNode] = [GNode(id=0, x=0.0, y=0.0, z=0.0, load_frac=1.0, depth=0)]
    edges: List[Tuple[int,int]] = []
    node_id = 1

    current_level = [0]   # indices of nodes at current depth

    for lv in range(depth):
        angle_deg = branch_angles[min(lv, len(branch_angles)-1)]
        angle_rad = math.radians(angle_deg)
        az_base   = az_offsets[min(lv, len(az_offsets)-1)]
        next_level = []

        for pid in current_level:
            parent = nodes[pid]
            child_frac = parent.load_frac / branching_factor
            step_z = height_per_level * math.cos(angle_rad)
            step_r = height_per_level * math.sin(angle_rad)

            for k in range(branching_factor):
                az_deg = az_base + k * (360.0 / branching_factor)
                az_rad = math.radians(az_deg)
                cx = parent.x + step_r * math.cos(az_rad)
                cy = parent.y + step_r * math.sin(az_rad)
                cz = parent.z - step_z      # growing downward

                child = GNode(
                    id=node_id,
                    x=cx, y=cy, z=cz,
                    load_frac=child_frac,
                    parent=pid,
                    depth=lv+1,
                )
                nodes.append(child)
                edges.append((pid, node_id))
                next_level.append(node_id)
                node_id += 1

        current_level = next_level

    return nodes, edges


# ── Stress calculation ─────────────────────────────────────────────────────────

ATM_PRESSURE_PA = 101_325.0   # Pa — standard atmosphere

def edge_von_mises(
    parent: GNode, child: GNode,
    swl_N: float, radius_mm: float,
    with_atm: bool = True,
) -> float:
    """
    Von Mises stress (MPa) in one strut.
    Includes atmospheric pressure as additional axial compression when with_atm=True.
    ATM adds: P_atm × A / A = P_atm (MPa) directly to axial stress.
    """
    dx = child.x - parent.x
    dy = child.y - parent.y
    dz = child.z - parent.z
    length = math.sqrt(dx**2 + dy**2 + dz**2)
    if length < 1e-9:
        return 0.0

    horiz = math.sqrt(dx**2 + dy**2)
    vert  = abs(dz)
    angle_rad = math.atan2(horiz, max(vert, 1e-9))

    branch_force = swl_N * child.load_frac
    axial   = branch_force / max(math.cos(angle_rad), 1e-6)
    lateral = axial * math.sin(angle_rad)

    area = math.pi * radius_mm**2
    sa   = axial   / area
    ss   = lateral / area

    # Atmospheric pressure adds uniform compressive stress on all strut faces
    atm_stress = (ATM_PRESSURE_PA * 1e-6) if with_atm else 0.0  # Pa → MPa
    sa_total   = sa + atm_stress

    return math.sqrt(sa_total**2 + 3 * ss**2)


# ── Fitness function ───────────────────────────────────────────────────────────

def fitness(
    nodes:    List[GNode],
    edges:    List[Tuple[int,int]],
    radius:   float,
    swl_N:    float,
    with_atm: bool = True,
) -> Tuple[float, List[float]]:
    """
    Fitness = variance of normalised stresses + heavy penalties.

    Perfect geometry: all stresses equal → variance = 0.
    Constraint penalties:
      - proof stress > yield  → +1000 per violating edge
      - fail stress < ult     → +1000 per edge that fails too early
      - base/height ratio     → +500 if unstable
      - planarity             → +500 if all Y ≈ 0
    """
    node_map = {n.id: n for n in nodes}
    stresses: List[float] = []

    proof_violations = 0
    fail_violations  = 0

    for p_id, c_id in edges:
        p = node_map[p_id]
        c = node_map[c_id]
        vm = edge_von_mises(p, c, swl_N, radius, with_atm)
        stresses.append(vm)

        if vm * PROOF_LOAD_FACTOR  > MAT_YIELD_MPA: proof_violations += 1
        if vm * DESIGN_FAIL_FACTOR > MAT_ULT_MPA:   fail_violations  += 1

    if not stresses:
        return float("inf"), []

    # Normalise stresses to [0,1] relative to yield
    norm = [s / max(MAT_YIELD_MPA, 1e-9) for s in stresses]
    mean = sum(norm) / len(norm)
    variance = sum((s - mean)**2 for s in norm) / len(norm)

    # Penalties
    penalty = 0.0
    penalty += 1000.0 * proof_violations
    penalty += 1000.0 * fail_violations

    # Stability: base span vs height
    ys = [n.y for n in nodes]
    xs = [n.x for n in nodes]
    y_span = max(ys) - min(ys)
    x_span = max(xs) - min(xs)
    base   = math.sqrt(x_span**2 + y_span**2)
    height = abs(min(n.z for n in nodes) - max(n.z for n in nodes))
    if height > 1e-9 and base / height < 0.5:
        penalty += 500.0 * (0.5 - base/height)

    # Planarity: all Y ≈ 0 → add heavy penalty
    if y_span < 1e-3:
        penalty += 500.0

    return variance + penalty, stresses


# ── Worker (runs in separate process) ─────────────────────────────────────────

def evaluate_candidate(args_tuple) -> Tuple[float, dict]:
    """
    Top-level function (picklable) for ProcessPoolExecutor.
    Returns (fitness_score, serialisable candidate dict).
    """
    (branch_angles, az_offsets, branching_factor,
     tubule_radius, depth, height_per_level, swl_N, with_atm) = args_tuple

    nodes, edges = generate_tree(
        depth, branch_angles, az_offsets,
        branching_factor, height_per_level,
    )
    score, stresses = fitness(nodes, edges, tubule_radius, swl_N, with_atm)

    return score, {
        "branch_angles":    branch_angles,
        "az_offsets":       az_offsets,
        "branching_factor": branching_factor,
        "tubule_radius":    tubule_radius,
        "fitness":          score,
        "stress_mean_MPa":  sum(stresses)/len(stresses) if stresses else 0.0,
        "stress_var":       score,        # approximate — includes penalties
        "nodes": [
            {"id": n.id, "x": n.x, "y": n.y, "z": n.z,
             "load_frac": n.load_frac, "depth": n.depth}
            for n in nodes
        ],
        "edges": [[p, c] for p, c in edges],
    }


# ── Parameter sampling & perturbation ─────────────────────────────────────────

def random_params(depth: int, rng: random.Random) -> tuple:
    angles  = [rng.uniform(ANGLE_MIN, ANGLE_MAX)  for _ in range(depth)]
    az      = [rng.uniform(AZ_MIN,    AZ_MAX)     for _ in range(depth)]
    bf      = rng.randint(BF_MIN, BF_MAX)
    radius  = rng.uniform(RADIUS_MIN, RADIUS_MAX)
    return angles, az, bf, radius


def perturb(params: tuple, depth: int, rng: random.Random, scale: float = 0.15) -> tuple:
    angles, az, bf, radius = params
    new_angles = [
        max(ANGLE_MIN, min(ANGLE_MAX, a + rng.gauss(0, scale*(ANGLE_MAX-ANGLE_MIN))))
        for a in angles
    ]
    new_az = [
        (a + rng.gauss(0, scale*(AZ_MAX-AZ_MIN))) % 360.0
        for a in az
    ]
    new_bf = max(BF_MIN, min(BF_MAX, bf + rng.randint(-1, 1)))
    new_r  = max(RADIUS_MIN, min(RADIUS_MAX, radius + rng.gauss(0, scale*(RADIUS_MAX-RADIUS_MIN))))
    return new_angles, new_az, new_bf, new_r


# ── Main search loop ───────────────────────────────────────────────────────────

def search(
    depth:          int   = 4,
    population:     int   = 64,
    iterations:     int   = 40,
    survivors:      int   = 8,
    workers:        int   = 4,
    swl_N:          float = 104.0,
    height_per_level: float = 6.0,
    seed:           int   = 42,
    with_atm:       bool  = True,
) -> dict:
    rng = random.Random(seed)

    # Initial population
    pop: List[tuple] = [random_params(depth, rng) for _ in range(population)]

    best_score = float("inf")
    best_result = None

    for iteration in range(iterations):
        # Build args for workers
        work = [
            (p[0], p[1], p[2], p[3], depth, height_per_level, swl_N, with_atm)
            for p in pop
        ]

        results: List[Tuple[float, dict]] = []
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(evaluate_candidate, w): i for i, w in enumerate(work)}
            for fut in as_completed(futs):
                try:
                    results.append(fut.result())
                except Exception as e:
                    results.append((float("inf"), {}))

        results.sort(key=lambda r: r[0])

        iter_best = results[0][0]
        if iter_best < best_score:
            best_score  = iter_best
            best_result = results[0][1]

        print(
            f"  iter {iteration+1:3d}/{iterations}  "
            f"best={iter_best:.6f}  "
            f"pop_best={results[0][1].get('stress_mean_MPa', 0):.3f}MPa mean  "
            f"bf={results[0][1].get('branching_factor',0)}  "
            f"r={results[0][1].get('tubule_radius',0):.2f}mm  "
            f"angles={[round(a,1) for a in results[0][1].get('branch_angles',[])]}"
        )

        if best_score < 1e-6:
            print("  [converged]")
            break

        # Breed next generation from survivors
        survivors_params = []
        for score, res in results[:survivors]:
            if res:
                p = (
                    res["branch_angles"], res["az_offsets"],
                    res["branching_factor"], res["tubule_radius"],
                )
                survivors_params.append(p)

        pop = list(survivors_params)
        # Fill rest with perturbations of survivors
        while len(pop) < population:
            parent = rng.choice(survivors_params)
            pop.append(perturb(parent, depth, rng))

    return best_result or {}


# ── Output ─────────────────────────────────────────────────────────────────────

def to_merkle_json(result: dict, swl_N: float) -> dict:
    """Convert search result to merkle_tree.json-compatible format."""
    nodes_out = []
    for n in result.get("nodes", []):
        nodes_out.append({
            "id": n["id"],
            "x":  round(n["x"], 4),
            "y":  round(n["y"], 4),
            "z":  round(n["z"], 4),
            "F":  round(swl_N * n["load_frac"], 4),
        })
    return {
        "nodes": nodes_out,
        "edges": result.get("edges", []),
        "metadata": {
            "description": "Semi-Jack n-space geometry search result",
            "branch_angles":    result.get("branch_angles"),
            "az_offsets":       result.get("az_offsets"),
            "branching_factor": result.get("branching_factor"),
            "tubule_radius_mm": result.get("tubule_radius"),
            "fitness":          result.get("fitness"),
            "stress_mean_MPa":  result.get("stress_mean_MPa"),
            "swl_N":            swl_N,
            "material":         "SLS_PA12",
        }
    }


def main():
    ap = argparse.ArgumentParser(description="Semi-Jack n-space geometry search")
    ap.add_argument("--depth",   type=int,   default=4,    help="Tree depth (default 4)")
    ap.add_argument("--pop",     type=int,   default=64,   help="Population size (default 64)")
    ap.add_argument("--iters",   type=int,   default=40,   help="Iterations (default 40)")
    ap.add_argument("--survivors", type=int, default=8,    help="Survivors per iteration (default 8)")
    ap.add_argument("--workers", type=int,   default=4,    help="Parallel workers (default 4)")
    ap.add_argument("--swl",     type=float, default=104.0,
                    help="SWL in Newtons (default 104N = 22mm cube at water density)")
    ap.add_argument("--hlevel",  type=float, default=6.0,
                    help="Height per tree level in mm (default 6mm → 24mm total for depth=4)")
    ap.add_argument("--seed",    type=int,   default=42,   help="RNG seed")
    ap.add_argument("--no-atm",  action="store_true",
                    help="Search in vacuum (no atmospheric pressure). Default: include atm.")
    ap.add_argument("--out",     default="5-Applications/out/sovereign_jenga/quantum_annealed/merkle_tree_nspace.json",
                    help="Output JSON path")
    args = ap.parse_args()

    with_atm = not args.no_atm
    print(f"\n  Semi-Jack n-space geometry search")
    print(f"  depth={args.depth}  pop={args.pop}  iters={args.iters}")
    print(f"  workers={args.workers}  swl={args.swl}N ({args.swl/9.81:.2f}kg)")
    print(f"  atmosphere: {'101325 Pa (standard)' if with_atm else 'OFF (vacuum)'}")
    print(f"  search space: {2*args.depth + 2}D")
    print()

    best = search(
        depth=args.depth,
        population=args.pop,
        iterations=args.iters,
        survivors=args.survivors,
        workers=args.workers,
        swl_N=args.swl,
        height_per_level=args.hlevel,
        seed=args.seed,
        with_atm=with_atm,
    )

    if not best:
        print("ERROR: no result", file=sys.stderr)
        sys.exit(1)

    print(f"\n  BEST GEOMETRY FOUND")
    print(f"  fitness          : {best.get('fitness', '?'):.8f}")
    print(f"  branching factor : {best.get('branching_factor')}")
    print(f"  tubule radius    : {best.get('tubule_radius', 0):.3f} mm")
    print(f"  branch angles    : {[round(a,2) for a in best.get('branch_angles', [])]}")
    print(f"  az offsets       : {[round(a,2) for a in best.get('az_offsets', [])]}")
    print(f"  stress mean      : {best.get('stress_mean_MPa', 0):.3f} MPa")
    print(f"  nodes            : {len(best.get('nodes', []))}")
    print(f"  edges            : {len(best.get('edges', []))}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_json = to_merkle_json(best, args.swl)
    out_path.write_text(json.dumps(out_json, indent=2))
    print(f"\n  Saved → {out_path}")
    print(f"  Feed into constraint_model: ")
    print(f"    python 5-Applications/scripts/semi_jack_constraint_model.py \\")
    print(f"      --json {out_path} \\")
    print(f"      --radius {best.get('tubule_radius', 1.0):.3f} \\")
    print(f"      --swl {args.swl}")
    print()


if __name__ == "__main__":
    main()
