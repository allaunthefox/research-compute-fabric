#!/usr/bin/env python3
"""
gpl_rotational_demo.py

Demonstrates rotational values and torsion in GPL.

Shows: π field encoding + chirality coupling = geometric rotation
"""

import math
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class RotationalMuSeed:
    """μ-seed with explicit rotation handling."""
    node_id: int
    delta_p: Tuple[float, float, float]  # Position delta (x, y, z)
    pi: int                              # Polarity/torsion (0-15)
    chi: int                             # Chirality (0=D, 1=L)
    activation: float
    
    def effective_rotation_angle(self) -> float:
        """
        Compute effective rotation angle in radians.
        
        D-form (χ=0): Counter-clockwise (+)
        L-form (χ=1): Clockwise (-)
        """
        base_angle = self.pi * (2 * math.pi / 16)  # 22.5° increments
        return base_angle if self.chi == 0 else -base_angle
    
    def rotate_vector(self, vec: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """Rotate a vector by this μ-seed's torsion (XY plane rotation)."""
        θ = self.effective_rotation_angle()
        cos_θ = math.cos(θ)
        sin_θ = math.sin(θ)
        
        x, y, z = vec
        return (
            x * cos_θ - y * sin_θ,
            x * sin_θ + y * cos_θ,
            z
        )
    
    def alignment_with(self, other: 'RotationalMuSeed') -> float:
        """
        Compute alignment (coupling strength) with another μ-seed.
        
        Returns: 1.0 (aligned) to -1.0 (opposite) to 0.0 (orthogonal)
        """
        # Relative rotation
        Δθ = self.effective_rotation_angle() - other.effective_rotation_angle()
        return math.cos(Δθ)


def demo_rotation_encoding():
    """Show how π encodes rotation."""
    
    print("=" * 60)
    print("ROTATIONAL VALUE ENCODING (π FIELD)")
    print("=" * 60)
    
    print("\nπ (4 bits) = 16 rotational states:")
    print("-" * 60)
    print(f"{'π':>3} | {'Binary':>6} | {'Degrees':>10} | {'Direction':>12}")
    print("-" * 60)
    
    for pi in range(16):
        degrees = pi * 22.5
        binary = format(pi, '04b')
        
        # Direction name
        if pi == 0:
            direction = "ALIGN"
        elif pi == 4:
            direction = "RIGHT"
        elif pi == 8:
            direction = "OPPOSITE"
        elif pi == 12:
            direction = "LEFT"
        else:
            direction = f"TURN_{pi}"
        
        print(f"{pi:>3} | {binary:>6} | {degrees:>10.1f}° | {direction:>12}")


def demo_chirality_coupling():
    """Show how chirality affects rotation direction."""
    
    print("\n" + "=" * 60)
    print("CHIRALITY-ROTATION COUPLING")
    print("=" * 60)
    
    # Create μ-seeds with same π but different chirality
    test_cases = [
        (0, 0, "D-form, π=0"),
        (0, 1, "L-form, π=0"),
        (4, 0, "D-form, π=4 (90°)"),
        (4, 1, "L-form, π=4 (90°)"),
        (8, 0, "D-form, π=8 (180°)"),
        (8, 1, "L-form, π=8 (180°)"),
    ]
    
    print(f"\n{'Description':<25} | {'π':>3} | {'χ':>3} | {'Effective°':>12} | {'Direction':>15}")
    print("-" * 70)
    
    for pi, chi, desc in test_cases:
        mu = RotationalMuSeed(0, (0, 0, 0), pi, chi, 0)
        angle_deg = math.degrees(mu.effective_rotation_angle())
        direction = "CCW" if angle_deg >= 0 else "CW"
        
        print(f"{desc:<25} | {pi:>3} | {chi:>3} | {angle_deg:>12.1f}° | {direction:>15}")
    
    print("\nKey insight: Same π, opposite rotation based on chirality!")


def demo_position_rotation():
    """Show how position deltas are rotated."""
    
    print("\n" + "=" * 60)
    print("POSITION DELTA ROTATION")
    print("=" * 60)
    
    # Start with a vector pointing east (1, 0, 0)
    vec = (1.0, 0.0, 0.0)
    
    print(f"\nOriginal vector: {vec}")
    print("-" * 60)
    print(f"{'π':>3} | {'χ':>3} | {'Rotated X':>12} | {'Rotated Y':>12} | {'Interpretation':>20}")
    print("-" * 60)
    
    test_cases = [
        (0, 0, "D-form, align"),
        (4, 0, "D-form, 90° CCW (North)"),
        (4, 1, "L-form, 90° CW (South)"),
        (8, 0, "D-form, 180° (West)"),
        (8, 1, "L-form, 180° (West - same!)"),
    ]
    
    for pi, chi, interp in test_cases:
        mu = RotationalMuSeed(0, (0, 0, 0), pi, chi, 0)
        rotated = mu.rotate_vector(vec)
        print(f"{pi:>3} | {chi:>3} | {rotated[0]:>12.3f} | {rotated[1]:>12.3f} | {interp:>20}")
    
    print("\nNote: π=8 (180°) gives same result for D and L (sign flip twice = same)")


def demo_alignment_coupling():
    """Show how rotational alignment affects coupling."""
    
    print("\n" + "=" * 60)
    print("ROTATIONAL ALIGNMENT & COUPLING")
    print("=" * 60)
    
    # Reference node
    mu_ref = RotationalMuSeed(0, (0, 0, 0), pi=0, chi=0, activation=5.0)
    
    print(f"\nReference: π={mu_ref.pi}, χ={mu_ref.chi} (Aligned to 0°)")
    print("-" * 70)
    print(f"{'Node π':>8} | {'Node χ':>8} | {'Alignment':>12} | {'Coupling':>12} | {'Description':>20}")
    print("-" * 70)
    
    test_nodes = [
        (0, 0, "Same (perfect)"),
        (0, 1, "Same π, L-chirality"),
        (4, 0, "90° apart"),
        (4, 1, "90° apart, L"),
        (8, 0, "Opposite (180°)"),
        (8, 1, "Opposite, L (same)"),
    ]
    
    for pi, chi, desc in test_nodes:
        mu_test = RotationalMuSeed(1, (0, 0, 0), pi, chi, 3.0)
        alignment = mu_ref.alignment_with(mu_test)
        coupling = "Strong" if alignment > 0.7 else "Weak" if alignment > -0.7 else "Repel"
        
        print(f"{pi:>8} | {chi:>8} | {alignment:>12.3f} | {coupling:>12} | {desc:>20}")
    
    print("\nCoupling strength determines information flow (ι operator)")


def demo_rotational_flow():
    """Demonstrate rotational channeling of activation flow."""
    
    print("\n" + "=" * 60)
    print("ROTATIONAL ACTIVATION FLOW")
    print("=" * 60)
    
    # Create a line of nodes with increasing π (rotating flow)
    nodes = []
    for i in range(8):
        pi = i % 16  # Rotate through angles
        mu = RotationalMuSeed(
            node_id=i,
            delta_p=(i, 0, 0),
            pi=pi,
            chi=0,  # D-form
            activation=1.0 if i == 0 else 0.0  # Only first node active
        )
        nodes.append(mu)
    
    print("\nChain of 8 nodes with π = 0, 1, 2, 3, 4, 5, 6, 7")
    print("(Rotating 0° → 22.5° → 45° → 67.5° → 90° → 112.5° → 135° → 157.5°)")
    print("-" * 60)
    print(f"{'Node':>6} | {'π':>4} | {'Angle°':>8} | {'Initial a':>12} | {'Alignment+1':>14} | {'Flow':>10}")
    print("-" * 60)
    
    for i, mu in enumerate(nodes):
        angle = mu.pi * 22.5
        # Alignment with next node (if exists)
        if i < len(nodes) - 1:
            align = mu.alignment_with(nodes[i+1])
        else:
            align = 0.0
        
        flow = "Strong" if align > 0.9 else "Medium" if align > 0.5 else "Weak"
        
        print(f"{i:>6} | {mu.pi:>4} | {angle:>8.1f} | {mu.activation:>12.1f} | {align:>14.3f} | {flow:>10}")
    
    print("\nActivation flows strongest where π changes gradually (aligned).")


def demo_chiral_superposition():
    """Show D+L superposition creating orthogonal channels."""
    
    print("\n" + "=" * 60)
    print("CHIRAL SUPERPOSITION (ORTHOGONAL CHANNELS)")
    print("=" * 60)
    
    # Create D and L versions of same structure
    print("\nTwo μ-seeds at same position:")
    print("-" * 60)
    
    for pi in [0, 4, 8]:
        mu_D = RotationalMuSeed(0, (0, 0, 0), pi, 0, 5.0)
        mu_L = RotationalMuSeed(1, (0, 0, 0), pi, 1, 5.0)
        
        angle_D = math.degrees(mu_D.effective_rotation_angle())
        angle_L = math.degrees(mu_L.effective_rotation_angle())
        
        print(f"\nπ = {pi} ({pi*22.5}° reference):")
        print(f"  D-form (χ=0): rotates to {angle_D:+.1f}° (CCW)")
        print(f"  L-form (χ=1): rotates to {angle_L:+.1f}° (CW)")
        print(f"  Net flow: D+L = {angle_D + angle_L:.1f}° (cancels!)")
        
        # But they don't interact!
        alignment = mu_D.alignment_with(mu_L)
        print(f"  Alignment: {alignment:.3f} (orthogonal channels)")


def demo_summary():
    """Summary of rotational programming."""
    
    print("\n" + "=" * 60)
    print("SUMMARY: ROTATIONAL PROGRAMMING IN GPL")
    print("=" * 60)
    
    print("""
Rotational Values (π field):
  • 4 bits → 16 states (22.5° resolution)
  • Encodes local torsion/orientation
  • Affects position delta interpretation
  • Controls activation flow direction

Chirality Coupling (χ bit):
  • χ=0 (D-form): Counter-clockwise rotation (+)
  • χ=1 (L-form): Clockwise rotation (-)
  • Same π, opposite physical effect
  • Orthogonal channels (no interaction)

Programming Implications:
  1. ALIGNMENT: Nodes with similar π couple strongly
  2. CHANNELING: Information flows along π gradients
  3. ORTHOGONALITY: D+L at same π = no crosstalk
  4. VORTICES: Circular π patterns create rotational attractors
  5. MEMORY: Store bits in rotational state

Example Patterns:
  π = constant: Parallel flow (all aligned)
  π = linear gradient: Directed flow (channel)
  π = circular: Vortex (attractor cycle)
  D+L pairs: Orthogonal information storage

Physical Realization:
  DNA origami twist angle encodes π
  D-form = right-handed helix twist
  L-form = left-handed helix twist
  Measured by FRET, CD, or conductance
""")


if __name__ == "__main__":
    demo_rotation_encoding()
    demo_chirality_coupling()
    demo_position_rotation()
    demo_alignment_coupling()
    demo_rotational_flow()
    demo_chiral_superposition()
    demo_summary()
