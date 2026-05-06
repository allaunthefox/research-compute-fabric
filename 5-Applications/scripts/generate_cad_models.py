#!/usr/bin/env python3
"""
Generate 3D CAD models (.scad files) for visualizing PIST manifolds.

These are NOT the full manifolds — they are 3D slices through the
pathological structures, making them human-visualizable. The full
9+ dimensional address cannot be embedded in 3D, but these slices
provide geometric intuition.
"""

import math
import os

OUTDIR = "/home/allaun/Desktop/cad_models"
os.makedirs(OUTDIR, exist_ok=True)

PHI = (1 + math.sqrt(5)) / 2


def write_scad(filename, content):
    path = os.path.join(OUTDIR, filename)
    with open(path, 'w') as f:
        f.write(content)
    print(f"Wrote {path}")


def scad_header(title):
    return f"// {title}\n// 3D slice of PIST pathological manifold\n\n"


# ═══════════════════════════════════════════════════════════════════════
# MODEL 1: PIST SHELLS AS CONCENTRIC POLYGONS
# ═══════════════════════════════════════════════════════════════════════

def generate_pist_shells():
    """PIST shells visualized as concentric polygonal rings.
    Shell k has 2k+1 positions arranged as vertices of a regular polygon."""

    scad = scad_header("PIST Shells: Concentric Polygonal Rings")
    scad += "// Each shell k is a regular (2k+1)-gon with radius k\n"
    scad += "// Inner shells: dense, low curvature\n"
    scad += "// Outer shells: sparse, high curvature\n\n"

    max_shell = 12  # shells 0 through 12

    for k in range(max_shell + 1):
        n_points = 2 * k + 1 if k > 0 else 1
        radius = k * 5  # mm

        scad += f"// Shell k={k}, capacity={n_points}, radius={radius}mm\n"

        if k == 0:
            scad += f"translate([0, 0, {k * 2}]) sphere(r=2, $fn=32);\n"
        else:
            points = []
            for t in range(n_points):
                angle = 2 * math.pi * t / n_points
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                points.append(f"[{x:.2f}, {y:.2f}, {k * 2}]")

            scad += f"// Vertices at positions t=0..{n_points-1}\n"
            for t in range(n_points):
                angle = 2 * math.pi * t / n_points
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                scad += f"translate([{x:.2f}, {y:.2f}, {k * 2}]) "
                scad += f"sphere(r=1.5, $fn=16);\n"

            # Draw polygon ring
            scad += f"\n// Polygon ring for shell k={k}\n"
            scad += f"linear_extrude(height=0.5, center=true) "
            scad += f"polygon(points=[{', '.join(points)}]);\n"

        scad += "\n"

    # Mirror connections (involution axis)
    scad += "// Mirror involution connections between shells\n"
    for k in range(1, max_shell + 1):
        n_points = 2 * k + 1
        radius = k * 5
        t_mirror = k  # center position
        angle = 2 * math.pi * t_mirror / n_points
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        scad += f"// Shell {k}: mirror axis at t={t_mirror}\n"
        scad += f"color([1, 0, 0, 0.3]) translate([{x:.2f}, {y:.2f}, {k * 2}]) "
        scad += f"cylinder(h=5, r=0.5, center=true, $fn=8);\n"

    return scad


# ═══════════════════════════════════════════════════════════════════════
# MODEL 2: MENGER SPONGE (3D FRACTAL)
# ═══════════════════════════════════════════════════════════════════════

def generate_menger_sponge():
    """Menger sponge: recursive cube removal.
    We model depth=3 with explicit cube placement."""

    scad = scad_header("Menger Sponge: Recursive Cube Removal")
    scad += "// Iteration 0: solid cube\n"
    scad += "// Iteration 1: 20 subcubes (remove center + 6 face centers)\n"
    scad += "// Iteration 2: 400 subcubes\n"
    scad += "// Iteration 3: 8000 subcubes (visualized as simplified)\n\n"

    def menger_cubes(level, x, y, z, size):
        """Generate cube placements for Menger sponge at given level."""
        if level == 0:
            return [(x, y, z, size)]

        cubes = []
        new_size = size / 3.0
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    # Skip center cube and face centers
                    removed = (
                        (i == 1 and j == 1) or  # center of xy face
                        (i == 1 and k == 1) or  # center of xz face
                        (j == 1 and k == 1) or  # center of yz face
                        (i == 1 and j == 1 and k == 1)  # very center
                    )
                    if not removed:
                        cubes.extend(menger_cubes(
                            level - 1,
                            x + i * new_size,
                            y + j * new_size,
                            z + k * new_size,
                            new_size
                        ))
        return cubes

    # Generate level 3 (simplified: only render centers of level-2 cubes)
    scad += "// Level 3 Menger sponge (simplified for visibility)\n"
    scad += "module sponge_cube(x, y, z, s) {\n"
    scad += "  translate([x, y, z]) cube([s, s, s], center=true);\n"
    scad += "}\n\n"

    # For practical rendering, show a single level-2 sponge
    # and label subcubes with their indices
    scad += "// Level 2 sponge with subcube indices labeled\n"
    scad += "difference() {\n"
    scad += "  cube([90, 90, 90], center=true);\n"
    # Remove 7 holes (center + 6 faces)
    centers = [
        (30, 0, 0), (-30, 0, 0), (0, 30, 0), (0, -30, 0), (0, 0, 30), (0, 0, -30),
        (0, 0, 0)
    ]
    for cx, cy, cz in centers:
        scad += f"  translate([{cx}, {cy}, {cz}]) cube([30.1, 30.1, 30.1], center=true);\n"
    scad += "}\n\n"

    # Add annotations for valid subcubes
    scad += "// Valid subcubes (remaining after removal)\n"
    scad += "color([0.2, 0.6, 0.9]) {\n"
    idx = 0
    for i in range(3):
        for j in range(3):
            for k in range(3):
                removed = (
                    (i == 1 and j == 1) or
                    (i == 1 and k == 1) or
                    (j == 1 and k == 1) or
                    (i == 1 and j == 1 and k == 1)
                )
                if not removed:
                    x = (i - 1) * 30
                    y = (j - 1) * 30
                    z = (k - 1) * 30
                    scad += f"  translate([{x}, {y}, {z}]) "
                    scad += f"cube([28, 28, 28], center=true); // subcube {idx}\n"
                    idx += 1
    scad += "}\n"

    return scad


# ═══════════════════════════════════════════════════════════════════════
# MODEL 3: GABRIEL'S HORN (SURFACE OF REVOLUTION)
# ═══════════════════════════════════════════════════════════════════════

def generate_gabriels_horn():
    """Gabriel's horn: y = 1/x rotated around x-axis.
    Truncated at x=256, visualized as a hollow horn."""

    scad = scad_header("Gabriel's Horn: y = 1/x Surface of Revolution")
    scad += "// Finite volume, infinite surface area\n"
    scad += "// Visualized as hollow shell (the byte container surface)\n\n"

    scad += "// Generate horn profile as a polygon\n"
    scad += "// Then rotate_extrude to create the surface\n\n"

    scad += "module horn_profile() {\n"
    scad += "  points = [\n"

    # Generate profile points: (x, y) where y = 1/x
    points = []
    for n in range(1, 257, 4):  # sample every 4 units
        x = n / 20.0  # scale to ~13mm wide
        y = 40.0 / n  # scale to start at 40mm, thin to 0.15mm
        points.append((x, y))
        scad += f"    [{x:.3f}, {y:.3f}],\n"

    # Close the polygon
    scad += f"    [{points[-1][0]:.3f}, 0],\n"
    scad += "    [0.05, 0]\n"
    scad += "  ];\n"
    scad += "  polygon(points);\n"
    scad += "}\n\n"

    scad += "// Thick-walled horn (byte positions on surface)\n"
    scad += "difference() {\n"
    scad += "  rotate_extrude($fn=64) horn_profile();\n"
    scad += "  scale([0.95, 0.95, 0.95]) rotate_extrude($fn=64) horn_profile();\n"
    scad += "}\n\n"

    # Add position markers along the horn
    scad += "// Byte position markers (sample every 32 positions)\n"
    scad += "color([1, 0.5, 0]) {\n"
    for n in range(1, 257, 32):
        x = n / 20.0
        y = 40.0 / n
        angle = (n * PHI) % (2 * math.pi)
        mx = x
        my = y * math.cos(angle)
        mz = y * math.sin(angle)
        scad += f"  translate([{mx:.2f}, {my:.2f}, {mz:.2f}]) "
        scad += f"sphere(r=0.8, $fn=8); // n={n}\n"
    scad += "}\n"

    return scad


# ═══════════════════════════════════════════════════════════════════════
# MODEL 4: HYPERTORUS SLICE (3D PROJECTION)
# ═══════════════════════════════════════════════════════════════════════

def generate_hypertorus_slice():
    """Hypertorus: take a 3D slice (two angles + one radius).
    This is not the full 4D torus but a visualizable projection."""

    scad = scad_header("Hypertorus: 3D Slice of 4D Structure")
    scad += "// Full hypertorus has 3 angular coordinates\n"
    scad += "// This model shows a 3D slice: theta, phi, with R=3, r=1\n"
    scad += "// The psi angle is represented by color/phase\n\n"

    R = 30.0  # major radius
    r = 10.0  # minor radius

    scad += f"// Major radius R = {R}mm, minor radius r = {r}mm\n"
    scad += "// Points colored by psi angle (the third, unseen dimension)\n\n"

    scad += "module torus_point(theta, phi, psi, R, r) {\n"
    scad += "  x = (R + r * cos(phi)) * cos(theta);\n"
    scad += "  y = (R + r * cos(phi)) * sin(theta);\n"
    scad += "  z = r * sin(phi);\n"
    scad += "  // Color by psi: [red=sin(psi), green=cos(psi), blue=0.5]\n"
    scad += "  color([0.5 + 0.5*sin(psi), 0.5 + 0.5*cos(psi), 0.5])\n"
    scad += "    translate([x, y, z]) sphere(r=1.5, $fn=8);\n"
    scad += "}\n\n"

    scad += "// Sample points using irrational rotations by PHI\n"
    for n in range(64):
        theta = (n * PHI) % (2 * math.pi)
        phi = (n * PHI * PHI) % (2 * math.pi)
        psi = (n * PHI * PHI * PHI) % (2 * math.pi)
        scad += f"torus_point({theta:.4f}, {phi:.4f}, {psi:.4f}, {R}, {r});\n"

    # Add the torus skeleton
    scad += "\n// Torus skeleton (major circle)\n"
    scad += f"color([0.3, 0.3, 0.3]) rotate_extrude($fn=64) "
    scad += f"translate([{R}, 0, 0]) circle(r={r}, $fn=32);\n"

    return scad


# ═══════════════════════════════════════════════════════════════════════
# MODEL 5: COMPOSITE PATHOLOGICAL MANIFOLD (3D SLICE)
# ═══════════════════════════════════════════════════════════════════════

def generate_composite_slice():
    """A 3D slice showing the COMPOSITION of structures:
    PIST shells nested inside Menger sponge nodes on a Gabriel's horn.
    This is the most complex model — a true pathological visualization."""

    scad = scad_header("Composite Pathological Manifold: 3D Slice")
    scad += "// NOT the full 9D structure — a visualizable 3D projection\n"
    scad += "// Shows how PIST shells nest within sponge nodes on the horn\n\n"

    scad += "// The composite structure:\n"
    scad += "// - Gabriel's horn: backbone (x-axis curve)\n"
    scad += "// - Menger sponge nodes: attached at 8 sample points\n"
    scad += "// - PIST shells: inside each sponge node\n\n"

    # Sample points along the horn
    sample_positions = [16, 32, 64, 128, 192, 240]

    scad += "module sponge_node(x_pos, horn_radius) {\n"
    scad += "  // Small Menger-like cube cluster at this horn position\n"
    scad += "  translate([x_pos, 0, 0]) {\n"

    # 8 valid subcubes (from 2x2x2, no center removal)
    offsets = [
        (-1, -1, -1), (-1, -1, 1), (-1, 1, -1), (-1, 1, 1),
        (1, -1, -1), (1, -1, 1), (1, 1, -1), (1, 1, 1)
    ]
    for idx, (dx, dy, dz) in enumerate(offsets):
        scad += f"    translate([{dx*3}, {dy*3}, {dz*3}]) "
        scad += f"cube([4, 4, 4], center=true); // subcube {idx}\n"

    scad += "  }\n"
    scad += "}\n\n"

    scad += "// Horn backbone\n"
    scad += "color([0.2, 0.2, 0.4]) {\n"
    for i in range(len(sample_positions) - 1):
        x1 = sample_positions[i] / 5.0
        x2 = sample_positions[i+1] / 5.0
        y1 = 20.0 / sample_positions[i] if sample_positions[i] > 0 else 2
        y2 = 20.0 / sample_positions[i+1] if sample_positions[i+1] > 0 else 1
        scad += f"  hull() {{\n"
        scad += f"    translate([{x1:.1f}, 0, 0]) sphere(r={y1:.1f}, $fn=16);\n"
        scad += f"    translate([{x2:.1f}, 0, 0]) sphere(r={y2:.1f}, $fn=16);\n"
        scad += "  }\n"
    scad += "}\n\n"

    scad += "// Sponge nodes at sample positions\n"
    scad += "color([0.8, 0.4, 0.1]) {\n"
    for n in sample_positions:
        x = n / 5.0
        r = 20.0 / n if n > 0 else 2
        scad += f"  sponge_node({x:.1f}, {r:.1f}); // n={n}\n"
    scad += "}\n\n"

    # PIST shell inside each sponge node
    scad += "// PIST shell inside sponge node 0 (n=16, k=4)\n"
    scad += "color([0.1, 0.7, 0.3]) translate([3.2, 0, 0]) {\n"
    k = 4
    radius = k * 1.5
    for t in range(2*k + 1):
        angle = 2 * math.pi * t / (2*k + 1)
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        scad += f"  translate([{x:.1f}, {y:.1f}, 0]) "
        scad += f"sphere(r=0.5, $fn=8); // t={t}\n"
    scad += "}\n"

    return scad


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("Generating 3D CAD Models for PIST Manifolds")
    print(f"Output directory: {OUTDIR}")
    print("=" * 70)
    print()

    write_scad("pist_shells.scad", generate_pist_shells())
    write_scad("menger_sponge.scad", generate_menger_sponge())
    write_scad("gabriels_horn.scad", generate_gabriels_horn())
    write_scad("hypertorus_slice.scad", generate_hypertorus_slice())
    write_scad("composite_manifold.scad", generate_composite_slice())

    print()
    print("=" * 70)
    print("All models generated.")
    print()
    print("To view: install OpenSCAD (openscad.org)")
    print("  openscad pist_shells.scad &")
    print("  openscad menger_sponge.scad &")
    print("  openscad gabriels_horn.scad &")
    print("  openscad hypertorus_slice.scad &")
    print("  openscad composite_manifold.scad &")
    print()
    print("To export STL for 3D printing:")
    print("  openscad -o pist_shells.stl pist_shells.scad")
    print("=" * 70)


if __name__ == '__main__':
    main()
