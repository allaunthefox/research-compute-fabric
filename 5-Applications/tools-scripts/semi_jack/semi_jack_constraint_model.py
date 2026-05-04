#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
semi_jack_constraint_model.py — GeomTREE Semi-Jack structural constraint analyzer

Applies the full OSHA/ASME PALD/EN 12839 constraint envelope to the existing
merkle_tree.json geometry and reports every violation. Works at toy scale (22mm)
first — if it fails here, scaling up won't fix it.

Standards applied:
  ASME PALD-2009    — proof load 200% SWL, no permanent deformation
  ASME B30.1        — design-to-failure ≥ 3× SWL
  OSHA 1926.305     — firm foundation, never under load on jack alone
  OSHA 1910.244     — rated capacity marked, sufficient for load
  EN 12839          — jack stand requirements, 200% proof test
  FMCSA grade ops   — stability on 15° incline with full load

Usage:
    python 5-Applications/scripts/semi_jack_constraint_model.py
    python 5-Applications/scripts/semi_jack_constraint_model.py --radius 1.5 --swl 34335
    python 5-Applications/scripts/semi_jack_constraint_model.py --radius 1.5 --list-flaws
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── Standards-derived constraint constants ─────────────────────────────────────

# ASME PALD / EN 12839 — proof load multiplier (200% of SWL)
PROOF_LOAD_FACTOR = 2.0

# ASME B30.1 — minimum design-to-failure factor (3× SWL)
DESIGN_FAILURE_FACTOR = 3.0

# FMCSA 49 CFR 393 — maximum operating grade for stability check
MAX_GRADE_DEG = 15.0

# OSHA 1926.305 / ASME PALD — minimum base-to-height ratio for stability on level
MIN_BASE_HEIGHT_RATIO = 0.5

# ── Material envelopes ─────────────────────────────────────────────────────────
# All stresses in N/mm² (MPa)

# ── Test mass helpers ─────────────────────────────────────────────────────────

def block_load_N(l_mm: float, w_mm: float, h_mm: float, density_g_cm3: float) -> float:
    vol_cm3 = (l_mm * w_mm * h_mm) / 1000.0
    return (vol_cm3 * density_g_cm3 / 1000.0) * 9.81

def sphere_load_N(r_mm: float, density_g_cm3: float) -> float:
    vol_cm3 = (4/3 * math.pi * r_mm**3) / 1000.0
    return (vol_cm3 * density_g_cm3 / 1000.0) * 9.81

def cylinder_load_N(r_mm: float, h_mm: float, density_g_cm3: float) -> float:
    vol_cm3 = (math.pi * r_mm**2 * h_mm) / 1000.0
    return (vol_cm3 * density_g_cm3 / 1000.0) * 9.81

OSMIUM_DENSITY = 22.59  # g/cm³ — densest stable element, reference only

def osmium_brick_load_N(l_mm: float, w_mm: float, h_mm: float) -> float:
    return block_load_N(l_mm, w_mm, h_mm, OSMIUM_DENSITY)


# ── Lattice / honeycomb mass ───────────────────────────────────────────────────
# The test mass IS the same Merkle tree geometry — a lattice of tubular struts.
# Mass = sum of strut volumes × bulk material density.
# Fill factor = strut volume / bounding box volume (how hollow it is).

def lattice_mass_kg(
    nodes: Dict[int, "Node"],
    edges: List[Tuple[int, int]],
    tubule_radius_mm: float,
    bulk_density_g_cm3: float,
) -> Tuple[float, float, float]:
    """
    Returns (mass_kg, fill_factor, strut_vol_mm3).
    bulk_density_g_cm3 is the density of the strut material itself — any value.
    """
    strut_vol_mm3 = 0.0
    for p_id, c_id in edges:
        p, c = nodes[p_id], nodes[c_id]
        length = math.sqrt(
            (c.x - p.x)**2 + (c.y - p.y)**2 + (c.z - p.z)**2
        )
        strut_vol_mm3 += math.pi * tubule_radius_mm**2 * length

    # Bounding box of all nodes
    xs = [n.x for n in nodes.values()]
    ys = [n.y for n in nodes.values()]
    zs = [n.z for n in nodes.values()]
    bbox_vol_mm3 = (
        (max(xs) - min(xs) or 1.0) *
        (max(ys) - min(ys) or 1.0) *   # guard: planar Y=0 → use 1mm depth
        (max(zs) - min(zs) or 1.0)
    )

    fill_factor = strut_vol_mm3 / bbox_vol_mm3
    mass_kg = (strut_vol_mm3 / 1000.0) * bulk_density_g_cm3 / 1000.0
    return mass_kg, fill_factor, strut_vol_mm3


MATERIALS = {
    "SLS_PA12": {
        "label": "SLS Nylon PA12 (no fiber)",
        "compressive_yield_MPa": 70.0,    # no permanent deformation under proof load
        "compressive_ult_MPa":  95.0,     # failure threshold (must exceed 3× SWL stress)
        "tensile_yield_MPa":    48.0,
        "shear_yield_MPa":      30.0,     # ~0.6 × tensile yield (von Mises)
        "density_g_cm3":         1.01,
    },
    "SLS_PA12_GF": {
        "label": "SLS Nylon PA12 + 30% glass fiber",
        "compressive_yield_MPa": 120.0,
        "compressive_ult_MPa":  160.0,
        "tensile_yield_MPa":     90.0,
        "shear_yield_MPa":       52.0,
        "density_g_cm3":          1.30,
    },
    "PLA": {
        "label": "FDM PLA (prototype only)",
        "compressive_yield_MPa": 50.0,
        "compressive_ult_MPa":   65.0,
        "tensile_yield_MPa":     37.0,
        "shear_yield_MPa":       22.0,
        "density_g_cm3":          1.24,
    },
    "AL6061_T6": {
        "label": "Aluminum 6061-T6 (original JSON material)",
        "compressive_yield_MPa": 276.0,
        "compressive_ult_MPa":   310.0,
        "tensile_yield_MPa":     276.0,
        "shear_yield_MPa":       165.0,
        "density_g_cm3":           2.70,
    },
}

# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class Node:
    id: int
    x: float
    y: float
    z: float
    force_N: float          # nominal load at this node (from JSON)
    children: List[int] = field(default_factory=list)
    parent: Optional[int] = None

@dataclass
class EdgeResult:
    parent_id: int
    child_id: int
    length_mm: float
    branch_angle_deg: float     # angle from vertical (load axis)
    axial_force_N: float        # component along branch axis
    lateral_force_N: float      # component perpendicular (lateral shear)
    cross_section_mm2: float
    axial_stress_MPa: float
    shear_stress_MPa: float
    von_mises_MPa: float
    proof_ok: bool              # survives 200% SWL without yield
    failure_ok: bool            # fails at or above 300% SWL
    is_planar: bool             # Y-coordinate delta is zero (planarity flag)

@dataclass
class GeometryFlaw:
    severity: str               # CRITICAL / WARNING / INFO
    location: str
    description: str
    value: float
    limit: float
    unit: str

# ── Geometry loader ────────────────────────────────────────────────────────────

def load_tree(path: Path) -> Tuple[Dict[int, Node], List[Tuple[int, int]]]:
    data = json.loads(path.read_text())
    nodes: Dict[int, Node] = {}
    for n in data["nodes"]:
        nodes[n["id"]] = Node(
            id=n["id"], x=n["x"], y=n["y"], z=n["z"],
            force_N=n.get("F", 0.0)
        )
    edges = [(e[0], e[1]) for e in data["edges"]]
    for p, c in edges:
        nodes[p].children.append(c)
        nodes[c].parent = p
    return nodes, edges

# ── Constraint analysis ────────────────────────────────────────────────────────

def analyze_edge(
    parent: Node, child: Node,
    swl_N: float,
    tubule_radius_mm: float,
    material: dict,
    root_force_N: float = 45000.0,
) -> EdgeResult:
    dx = child.x - parent.x
    dy = child.y - parent.y
    dz = child.z - parent.z
    length = math.sqrt(dx**2 + dy**2 + dz**2)

    # Branch angle from vertical (Z axis is load axis, z goes negative downward)
    horiz = math.sqrt(dx**2 + dy**2)
    vert  = abs(dz)
    branch_angle_deg = math.degrees(math.atan2(horiz, vert)) if vert > 1e-9 else 90.0

    # Scale branch force to specified SWL.
    # Use child's fraction of the ROOT load (not just parent), so stress
    # decreases correctly at deeper levels of the tree.
    branch_force = swl_N * (child.force_N / max(root_force_N, 1e-9))

    # Axial (along branch) and lateral (perpendicular) components
    angle_rad = math.radians(branch_angle_deg)
    axial_force   = branch_force / max(math.cos(angle_rad), 1e-6)  # actual strut force
    lateral_force = axial_force * math.sin(angle_rad)               # lateral component

    # Cross-section
    area_mm2 = math.pi * tubule_radius_mm**2

    # Stresses (N/mm² = MPa)
    axial_stress  = axial_force   / area_mm2
    shear_stress  = lateral_force / area_mm2
    von_mises     = math.sqrt(axial_stress**2 + 3 * shear_stress**2)

    # ASME PALD / EN 12839: proof load = 2× SWL — no permanent deformation
    proof_stress  = von_mises * PROOF_LOAD_FACTOR
    proof_ok      = proof_stress <= material["compressive_yield_MPa"]

    # ASME B30.1: failure must not occur below 3× SWL
    failure_stress = von_mises * DESIGN_FAILURE_FACTOR
    failure_ok     = failure_stress <= material["compressive_ult_MPa"]

    is_planar = abs(dy) < 1e-6 and abs(child.y) < 1e-6

    return EdgeResult(
        parent_id=parent.id,
        child_id=child.id,
        length_mm=length,
        branch_angle_deg=branch_angle_deg,
        axial_force_N=axial_force,
        lateral_force_N=lateral_force,
        cross_section_mm2=area_mm2,
        axial_stress_MPa=axial_stress,
        shear_stress_MPa=shear_stress,
        von_mises_MPa=von_mises,
        proof_ok=proof_ok,
        failure_ok=failure_ok,
        is_planar=is_planar,
    )


def check_global_geometry(nodes: Dict[int, Node], swl_N: float) -> List[GeometryFlaw]:
    flaws: List[GeometryFlaw] = []

    # Find root (no parent) and leaves (no children)
    root   = next(n for n in nodes.values() if n.parent is None)
    leaves = [n for n in nodes.values() if not n.children]

    # ── Flaw 1: Planarity check ──────────────────────────────────────────────
    all_y = [n.y for n in nodes.values()]
    y_span = max(all_y) - min(all_y)
    if y_span < 1e-6:
        flaws.append(GeometryFlaw(
            severity="CRITICAL",
            location="ALL NODES",
            description=(
                "Structure is entirely planar (Y=0 for all nodes). "
                "Zero resistance to any lateral force in the Y direction. "
                "A 15° grade tilt in the Y plane produces unconstrained rotation. "
                "Fix: rotate alternating branch levels by 90° in Y, "
                "or use pentagonal (5-way) branching in 3D."
            ),
            value=y_span,
            limit=1.0,   # at minimum, leaves must span some Y distance
            unit="mm Y-span",
        ))

    # ── Flaw 2: Base-to-height ratio (stability on level) ───────────────────
    xs = [n.x for n in leaves]
    ys = [n.y for n in leaves]
    base_span_x = max(xs) - min(xs) if xs else 0.0
    base_span_y = max(ys) - min(ys) if ys else 0.0
    base_span   = math.sqrt(base_span_x**2 + base_span_y**2)   # diagonal
    total_height = abs(root.z - min(n.z for n in nodes.values()))

    ratio = base_span / max(total_height, 1e-9)
    if ratio < MIN_BASE_HEIGHT_RATIO:
        flaws.append(GeometryFlaw(
            severity="CRITICAL",
            location="ROOT↔LEAVES",
            description=(
                f"Base/height ratio {ratio:.3f} < {MIN_BASE_HEIGHT_RATIO} (ASME PALD / OSHA 1926.305). "
                "Structure tips under lateral load. "
                f"Base span: {base_span:.1f}mm, height: {total_height:.1f}mm. "
                "Fix: widen leaf node spread or reduce height."
            ),
            value=ratio,
            limit=MIN_BASE_HEIGHT_RATIO,
            unit="base/height",
        ))

    # ── Flaw 3: 15° grade stability (FMCSA, OSHA field ops) ─────────────────
    # Under 15° tilt, CG must remain over base polygon
    # Simple check: CG horizontal shift = height × tan(15°)
    cg_shift = total_height * math.tan(math.radians(MAX_GRADE_DEG))
    half_base_x = base_span_x / 2.0
    if cg_shift > half_base_x:
        flaws.append(GeometryFlaw(
            severity="CRITICAL",
            location="STABILITY@15°",
            description=(
                f"On a {MAX_GRADE_DEG}° grade the CG shifts {cg_shift:.1f}mm horizontally "
                f"but X half-base is only {half_base_x:.1f}mm. "
                "Structure tips before reaching operating grade. "
                "Fix: increase base span or reduce height."
            ),
            value=cg_shift,
            limit=half_base_x,
            unit="mm CG shift vs half-base",
        ))

    # ── Flaw 4: Binary vs pentagonal branching ───────────────────────────────
    max_children = max(len(n.children) for n in nodes.values())
    if max_children <= 2:
        flaws.append(GeometryFlaw(
            severity="WARNING",
            location="BRANCHING FACTOR",
            description=(
                f"Maximum branching factor = {max_children} (binary). "
                "Patent spec calls for pentagonal (5-way) branching. "
                "Binary branching concentrates 50% of load at each parent node; "
                "pentagonal distributes 20% per branch, reducing peak node stress by ~2.5×. "
                "At toy scale this is acceptable for geometry validation but must be "
                "upgraded before load testing."
            ),
            value=float(max_children),
            limit=5.0,
            unit="branches/node",
        ))

    # ── Flaw 5: Root force vs SWL ────────────────────────────────────────────
    root_force = root.force_N
    if abs(root_force - swl_N) / max(swl_N, 1e-9) > 0.05:
        flaws.append(GeometryFlaw(
            severity="WARNING",
            location=f"ROOT NODE {root.id}",
            description=(
                f"Root force in JSON ({root_force:.0f}N = {root_force/9.81:.0f}kg) "
                f"does not match specified SWL ({swl_N:.0f}N = {swl_N/9.81:.0f}kg). "
                "Constraint analysis uses specified SWL; JSON force is noted as mismatch."
            ),
            value=root_force,
            limit=swl_N,
            unit="N root force",
        ))

    # ── Flaw 6: No leaf pad geometry ─────────────────────────────────────────
    flaws.append(GeometryFlaw(
        severity="INFO",
        location="LEAF NODES",
        description=(
            f"{len(leaves)} leaf nodes are dimensionless points. "
            "OSHA 1926.305(b): jack must sit on firm foundation — "
            "requires a base pad geometry. "
            "At toy scale: minimum pad area = load / allowable_bearing_pressure. "
            "For SLS PA12 on printed surface: ~2× tubule area minimum. "
            "Fix: add cap geometry to leaf nodes in STL output."
        ),
        value=0.0,
        limit=1.0,
        unit="pad area defined",
    ))

    return flaws


def _root_force(nodes: Dict[int, Node]) -> float:
    root = next(n for n in nodes.values() if n.parent is None)
    return root.force_N


def find_minimum_radius(
    nodes: Dict[int, Node],
    edges: List[Tuple[int, int]],
    swl_N: float,
    material: dict,
) -> float:
    """Binary search for minimum tubule radius that passes all edge constraints."""
    rf = _root_force(nodes)
    lo, hi = 0.1, 50.0
    for _ in range(40):
        mid = (lo + hi) / 2.0
        all_ok = True
        for p_id, c_id in edges:
            r = analyze_edge(nodes[p_id], nodes[c_id], swl_N, mid, material, rf)
            if not r.proof_ok or not r.failure_ok:
                all_ok = False
                break
        if all_ok:
            hi = mid
        else:
            lo = mid
    return hi


# ── Report ─────────────────────────────────────────────────────────────────────

def print_report(
    nodes: Dict[int, Node],
    edges: List[Tuple[int, int]],
    swl_N: float,
    tubule_radius_mm: float,
    material_key: str,
):
    mat = MATERIALS[material_key]
    sep = "=" * 72
    print(f"\n{sep}")
    print("  SEMI-JACK CONSTRAINT MODEL — GeomTREE Structural Analysis")
    print(sep)
    print(f"  Material   : {mat['label']}")
    print(f"  SWL        : {swl_N:.0f} N  ({swl_N/9.81:.1f} kg)")
    print(f"  Proof load : {swl_N*PROOF_LOAD_FACTOR:.0f} N  ({swl_N*PROOF_LOAD_FACTOR/9.81:.1f} kg)  [ASME PALD 200%]")
    print(f"  Fail floor : {swl_N*DESIGN_FAILURE_FACTOR:.0f} N  ({swl_N*DESIGN_FAILURE_FACTOR/9.81:.1f} kg)  [ASME B30.1 300%]")
    print(f"  Tubule r   : {tubule_radius_mm:.2f} mm  (area {math.pi*tubule_radius_mm**2:.3f} mm²)")
    print(f"  Yield allow: {mat['compressive_yield_MPa']} MPa  (proof limit)")
    print(f"  Ult allow  : {mat['compressive_ult_MPa']} MPa  (failure floor)")
    print()

    # Global geometry flaws
    flaws = check_global_geometry(nodes, swl_N)
    print(f"  GEOMETRY FLAWS ({len(flaws)} found)")
    print(f"  {'-'*68}")
    for f in flaws:
        marker = {"CRITICAL": "✗", "WARNING": "△", "INFO": "·"}[f.severity]
        print(f"  {marker} [{f.severity:8s}] {f.location}")
        for line in f.description.split(". "):
            if line.strip():
                print(f"             {line.strip()}.")
        print(f"             Value: {f.value:.3f} {f.unit}  |  Limit: {f.limit:.3f} {f.unit}")
        print()

    # Per-edge analysis
    print(f"  EDGE STRESS ANALYSIS (r={tubule_radius_mm:.2f}mm)")
    print(f"  {'-'*68}")
    print(f"  {'Edge':8s} {'Len':6s} {'Angle':7s} {'Axial':8s} {'Shear':8s} {'vMises':8s} {'Proof':6s} {'Fail':5s} {'Planar':6s}")

    rf = _root_force(nodes)
    critical_edges = []
    planar_edges   = []
    for p_id, c_id in edges:
        r = analyze_edge(nodes[p_id], nodes[c_id], swl_N, tubule_radius_mm, mat, rf)
        proof_str = "OK" if r.proof_ok   else "FAIL"
        fail_str  = "OK" if r.failure_ok else "FAIL"
        planar_str = "YES" if r.is_planar else "no"
        flag = "  "
        if not r.proof_ok or not r.failure_ok:
            flag = "✗ "
            critical_edges.append((p_id, c_id, r))
        if r.is_planar:
            planar_edges.append((p_id, c_id))
        print(
            f"  {flag}{p_id:2d}→{c_id:2d}   "
            f"{r.length_mm:5.1f}mm  "
            f"{r.branch_angle_deg:5.1f}°   "
            f"{r.axial_stress_MPa:6.2f}MPa  "
            f"{r.shear_stress_MPa:6.2f}MPa  "
            f"{r.von_mises_MPa:6.2f}MPa  "
            f"{proof_str:6s}  "
            f"{fail_str:5s}  "
            f"{planar_str}"
        )

    # Minimum radius
    min_r = find_minimum_radius(nodes, edges, swl_N, mat)
    print()
    print(f"  MINIMUM TUBULE RADIUS TO PASS ALL CONSTRAINTS: {min_r:.3f} mm")
    print(f"  (at specified SWL={swl_N/9.81:.0f}kg, material={material_key})")
    print()

    # Summary
    n_crit    = sum(1 for f in flaws if f.severity == "CRITICAL")
    n_warn    = sum(1 for f in flaws if f.severity == "WARNING")
    n_planar  = len(planar_edges)
    n_fail    = len(critical_edges)
    print("  SUMMARY")
    print("  " + "-" * 68)
    print(f"  Critical geometry flaws : {n_crit}")
    print(f"  Warnings                : {n_warn}")
    print(f"  Planar edges            : {n_planar}/{len(edges)} (all Y=0 — zero Y-axis resistance)")
    print(f"  Stress failures         : {n_fail}/{len(edges)} edge(s) at r={tubule_radius_mm:.2f}mm")
    print(f"  Minimum safe radius     : {min_r:.3f} mm")

    if n_crit > 0:
        print()
        print(f"  VERDICT: FAILS CONSTRAINT ENVELOPE — {n_crit} critical flaw(s) must be resolved")
        print("           before this geometry is valid at ANY scale.")
    else:
        print()
        print(f"  VERDICT: Geometry passes envelope at r={tubule_radius_mm:.2f}mm with {material_key}.")
    print("=" * 72 + "\n")


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Semi-Jack GeomTREE constraint analyzer")
    ap.add_argument("--json",     default="5-Applications/out/sovereign_jenga/quantum_annealed/merkle_tree.json",
                    help="Path to merkle_tree.json")
    ap.add_argument("--swl",      type=float, default=34335.0,
                    help="Safe Working Load in Newtons (default: 34335 N = 3500 kg)")
    ap.add_argument("--radius",   type=float, default=1.0,
                    help="Tubule cross-section radius in mm (default: 1.0mm)")
    ap.add_argument("--material", default="SLS_PA12",
                    choices=list(MATERIALS.keys()),
                    help="Material key (default: SLS_PA12)")
    ap.add_argument("--toy-scale", action="store_true",
                    help="Scale SWL to toy proportions (area ratio from 22mm height to real 280mm)")
    ap.add_argument("--lattice-mass", nargs=2, type=float, metavar=("R", "D"),
                    help="Use the tree geometry itself as the test mass: "
                         "tubule radius R mm, bulk strut density D g/cm³. "
                         "SWL = weight of the lattice at that radius and density.")
    ap.add_argument("--osmium-brick", nargs=3, type=float, metavar=("L", "W", "H"),
                    help="Osmium block L×W×H mm as SWL (density=22.59 g/cm³)")
    ap.add_argument("--test-block", nargs=4, type=float, metavar=("L", "W", "H", "D"),
                    help="Block L×W×H mm at density D g/cm³ as SWL. "
                         "Use any density — mass/weight is what matters.")
    ap.add_argument("--test-sphere", nargs=2, type=float, metavar=("R", "D"),
                    help="Sphere radius R mm at density D g/cm³ as SWL.")
    ap.add_argument("--test-cylinder", nargs=3, type=float, metavar=("R", "H", "D"),
                    help="Cylinder radius R mm, height H mm, density D g/cm³ as SWL.")
    args = ap.parse_args()

    json_path = Path(args.json)
    if not json_path.exists():
        json_path = Path(__file__).parent.parent / args.json
    if not json_path.exists():
        print(f"ERROR: {args.json} not found", file=sys.stderr)
        sys.exit(1)

    nodes, edges = load_tree(json_path)

    swl = args.swl
    if args.lattice_mass:
        r_mm, density = args.lattice_mass
        mass_kg, fill, vol = lattice_mass_kg(nodes, edges, r_mm, density)
        swl = mass_kg * 9.81
        print(
            f"[lattice-mass] tree geometry as test mass:\n"
            f"               strut r={r_mm}mm  density={density} g/cm³\n"
            f"               strut vol={vol:.2f} mm³  fill factor={fill:.4f}\n"
            f"               mass={mass_kg:.6f} kg  load={swl:.6f} N"
        )
    elif args.test_block:
        l, w, h, d = args.test_block
        swl = block_load_N(l, w, h, d)
        print(f"[test-block]  {l:.1f}×{w:.1f}×{h:.1f}mm  density={d} g/cm³  "
              f"→ {swl/9.81:.4f} kg  {swl:.4f} N")
    elif args.test_sphere:
        r, d = args.test_sphere
        swl = sphere_load_N(r, d)
        print(f"[test-sphere] r={r:.1f}mm  density={d} g/cm³  "
              f"→ {swl/9.81:.4f} kg  {swl:.4f} N")
    elif args.test_cylinder:
        r, h, d = args.test_cylinder
        swl = cylinder_load_N(r, h, d)
        print(f"[test-cyl]    r={r:.1f}mm h={h:.1f}mm  density={d} g/cm³  "
              f"→ {swl/9.81:.4f} kg  {swl:.4f} N")
    elif args.osmium_brick:
        l_mm, w_mm, h_mm = args.osmium_brick
        swl = osmium_brick_load_N(l_mm, w_mm, h_mm)
        print(f"[osmium-brick] {l_mm:.0f}×{w_mm:.0f}×{h_mm:.0f}mm  "
              f"density={OSMIUM_DENSITY} g/cm³  "
              f"→ {swl/9.81:.4f} kg  {swl:.4f} N")
    elif args.toy_scale:
        # Scale SWL by linear scale squared: toy height 22mm vs real min 280mm
        scale = (22.0 / 280.0) ** 2
        swl = args.swl * scale
        print(f"[toy-scale] SWL scaled by {scale:.4f} → {swl:.1f} N ({swl/9.81:.2f} kg)")

    print_report(nodes, edges, swl, args.radius, args.material)

    # Material comparison
    print("  MATERIAL COMPARISON (minimum radius to pass at specified SWL)")
    print("  " + "-" * 50)
    for key, mat in MATERIALS.items():
        r = find_minimum_radius(nodes, edges, swl, mat)
        print(f"  {key:15s}: min radius = {r:.3f} mm  ({mat['label']})")
    print()


if __name__ == "__main__":
    main()
