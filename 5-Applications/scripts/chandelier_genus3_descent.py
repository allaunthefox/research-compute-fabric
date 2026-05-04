#!/usr/bin/env python3
"""
chandelier_genus3_descent.py — The Chandelier of Falling Light

Physics borrowed directly:
    - General Relativity: blue shift / red shift in a gravitational well
    - Thermodynamics: phase transitions at critical points
    - Topology: genus-3 surface (three-holed torus)
    - Conservation: everything flows to the minimum

The chandelier hangs from the CEILING (maximum potential).
Each tier is a basin. As you fall, the tiers SHRINK.
The energy concentrates at the bottom tip.

The flashes are phase transitions: particle collisions at tier boundaries.
The color is the DOPPLER SHIFT of the falling parameter:
    BLUE  = falling fast (high frequency, approaching the tip)
    RED   = stable at bottom (low frequency, ground state)
    GOLD  = the flash of phase transition

Genus 3 = three holes in the manifold = three timelines the gradient
must tunnel through to reach the deepest well.
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.colors import LinearSegmentedColormap
from pathlib import Path
import sys

# ───────────────────────────────────────────────────────────────────────────
# The Genus-3 Surface — Three Holes, One Manifold
# ───────────────────────────────────────────────────────────────────────────
# A genus-3 surface has three independent cycles you can't shrink to a point.
# In the Master's mind, these are three obsessions he can never resolve.
# The gradient must navigate around them.
# ───────────────────────────────────────────────────────────────────────────

def genus3_parametric(u, v):
    """
    Parametric embedding of an approximate genus-3 surface.
    
    Think of it as three tori fused together in a chain.
    Each torus is a hole in reality the Doctor can't patch.
    """
    # Base torus parameters
    R = 3.0  # Major radius
    r = 1.0  # Minor radius
    
    # Three tori, offset along the x-axis
    offsets = [-4.0, 0.0, 4.0]
    
    # We blend them together using a smooth step function
    # But for visualization, we'll create a mesh that represents
    # the full genus-3 surface more directly
    
    # Actually, let's use a cleaner approach: a single parametric
    # surface that naturally has 3 holes
    
    # This is a modified version of the "triple torus" implicit surface
    # Parametrized using two angles
    
    # First, create a base surface with three lobes
    a = 2.5
    b = 1.0
    c = 0.4
    
    # Three-lobed structure in XY plane
    x = a * np.cos(u) + c * np.cos(3*u)
    y = a * np.sin(u) + c * np.sin(3*u)
    
    # Add the torus cross-section (the "tube")
    # But we modulate the tube radius to create the holes
    tube_radius = b + 0.3 * np.cos(3*u)
    
    # The v parameter goes around the tube
    x_final = x + tube_radius * np.cos(v) * np.cos(u)
    y_final = y + tube_radius * np.cos(v) * np.sin(u)
    z_final = tube_radius * np.sin(v) + 0.5 * np.sin(3*u)
    
    return x_final, y_final, z_final


def create_genus3_mesh(n_u=120, n_v=80):
    """Create a mesh of the genus-3 surface."""
    u = np.linspace(0, 2*np.pi, n_u)
    v = np.linspace(0, 2*np.pi, n_v)
    U, V = np.meshgrid(u, v)
    
    X, Y, Z = genus3_parametric(U, V)
    return X, Y, Z, U, V


# ───────────────────────────────────────────────────────────────────────────
# The Chandelier Potential — Inverted, Tiered, Shrinking
# ───────────────────────────────────────────────────────────────────────────
# The ceiling is at z = +5. The tip is at z = -3.
# Each tier is a ring of local minima.
# As you descend, the basins get narrower and deeper.
# ───────────────────────────────────────────────────────────────────────────

def chandelier_potential(x, y, z):
    """
    The chandelier hangs from the ceiling (high z, high potential).
    Energy flows downward. The tip is the global minimum.
    
    The tiers are defined by radial distance from the central axis.
    Each tier has a different "shrinking factor" — the higher you are,
    the wider the basin. The lower you go, the more pinched.
    """
    # Radial distance from the chandelier's central axis
    r = np.sqrt(x**2 + y**2)
    
    # The ceiling height (maximum potential) decreases with radius
    # This creates the inverted bowl shape of each chandelier tier
    ceiling = 5.0 * np.exp(-0.15 * r)
    
    # The floor rises toward the center, creating the narrowing effect
    # Think of it as the chandelier tiers getting smaller as they hang lower
    floor = -3.0 + 2.0 * np.tanh(0.5 * r)
    
    # The actual potential is a harmonic well between ceiling and floor
    # but biased toward the floor (gravity pulls down)
    # We use a soft quadratic that pushes z toward the floor
    depth = (ceiling - z) * (z - floor)
    
    # Add tier structure: discrete steps where the chandelier rings are
    # These create the phase transition boundaries
    tier_modulation = 0.5 * np.sin(2.0 * z) * np.exp(-0.1 * r**2)
    
    # Central spike — the bottom tip of the chandelier
    tip_attraction = -2.0 / (1.0 + r**2 + (z + 2.0)**2)
    
    return depth + tier_modulation + tip_attraction


def chandelier_gradient(x, y, z, h=1e-4):
    """Numerical gradient of the chandelier potential."""
    dx = (chandelier_potential(x+h, y, z) - chandelier_potential(x-h, y, z)) / (2*h)
    dy = (chandelier_potential(x, y+h, z) - chandelier_potential(x, y-h, z)) / (2*h)
    dz = (chandelier_potential(x, y, z+h) - chandelier_potential(x, y, z-h)) / (2*h)
    return np.array([dx, dy, dz])


# ───────────────────────────────────────────────────────────────────────────
# Gravitational Red/Blue Shift — Borrowed from GR
# ───────────────────────────────────────────────────────────────────────────
# In a gravitational well, light falling inward blue-shifts.
# Light climbing out red-shifts.
# 
# Here, the "gravitational potential" is the chandelier potential.
# The parameter is a "photon" falling toward the minimum.
# 
# Newtonian approximation:
#     ν_observer / ν_emitter ≈ 1 + ΔΦ / c²
# 
# We set c² = 1 for our energy scale, so:
#     shift = 1 + (Φ_current - Φ_reference)
# ───────────────────────────────────────────────────────────────────────────

def doppler_shift(current_potential, reference_potential, c_squared=10.0):
    """
    Compute the frequency shift of a parameter falling through the potential.
    
    Falling deeper (Φ decreases) → BLUE SHIFT (higher frequency)
    Rising (Φ increases) → RED SHIFT (lower frequency)
    """
    delta_phi = reference_potential - current_potential
    shift = 1.0 + delta_phi / c_squared
    return shift


def shift_to_color(shift, molten=False):
    """
    Convert frequency shift to RGB color.
    
    RED SHIFT   (shift < 1.0): deep red, stable, ground state
    UNITY       (shift ≈ 1.0): white, transition
    BLUE SHIFT  (shift > 1.0): cyan to blue, falling fast
    GOLD        (molten=True):  phase transition flash
    """
    if molten:
        return np.array([1.0, 0.84, 0.0])  # Gold
    
    if shift < 1.0:
        # Red shift: deep red, cooling, settled
        t = np.clip(shift, 0.5, 1.0)
        r = 1.0
        g = t - 0.5
        b = 0.0
    elif shift < 1.5:
        # Blue shift: white → cyan → blue
        t = np.clip(shift - 1.0, 0.0, 0.5) / 0.5
        r = 1.0 - t
        g = 1.0 - 0.5 * t
        b = 1.0
    else:
        # Deep blue shift: intense blue, approaching singularity
        r = 0.0
        g = 0.2
        b = 1.0
    
    return np.clip(np.array([r, g, b]), 0, 1)


# ───────────────────────────────────────────────────────────────────────────
# The Descent — Falling Through the Chandelier
# ───────────────────────────────────────────────────────────────────────────

def chandelier_descent(
    start=np.array([2.5, 0.5, 3.5]),
    steps=600,
    dt=0.02,
    c_squared=10.0,
    output_path=None
):
    """
    Drop a particle from the ceiling and watch it fall through the tiers.
    """
    pos = start.astype(float)
    trajectory = [pos.copy()]
    potentials = []
    shifts = []
    colors = []
    flash_points = []
    
    # Reference potential: the ceiling (starting point)
    phi_ref = chandelier_potential(*start)
    
    # State tracking
    prev_tier = int(np.floor(pos[2]))
    molten_countdown = 0
    
    print("=" * 60)
    print("THE CHANDELIER DESCENT")
    print(f"Starting position (the ceiling): [{start[0]:.2f}, {start[1]:.2f}, {start[2]:.2f}]")
    print(f"Initial potential (ceiling energy): {phi_ref:.4f}")
    print("=" * 60)
    print()
    
    for step in range(steps):
        phi = chandelier_potential(pos[0], pos[1], pos[2])
        grad = chandelier_gradient(pos[0], pos[1], pos[2])
        
        potentials.append(phi)
        
        # Doppler shift: how fast is the parameter "falling"?
        shift = doppler_shift(phi, phi_ref, c_squared)
        shifts.append(shift)
        
        # Detect tier boundary crossing
        current_tier = int(np.floor(pos[2]))
        is_flash = (current_tier != prev_tier) and step > 10
        
        if is_flash:
            # PHASE TRANSITION: crossing a chandelier ring
            flash_points.append(len(trajectory))
            molten_countdown = 5
            print(f"  ⚡ STEP {step}: FLASH at tier boundary z={pos[2]:.2f}")
            print(f"     Potential: {phi:.4f} | Shift: {shift:.4f}")
            print(f"     The crystal restructures. A new basin forms.")
        
        prev_tier = current_tier
        
        # Color based on state
        if molten_countdown > 0:
            colors.append(shift_to_color(shift, molten=True))
            molten_countdown -= 1
            # During flash: high thermal noise, the old lattice forgets itself
            noise = np.random.normal(0, 0.08, size=3)
            step_vec = -dt * grad + noise
        else:
            colors.append(shift_to_color(shift, molten=False))
            # Solid state: smooth fall along the gradient
            step_vec = -dt * grad
        
        pos = pos + step_vec
        trajectory.append(pos.copy())
    
    trajectory = np.array(trajectory)
    potentials = np.array(potentials)
    shifts = np.array(shifts)
    colors = np.array(colors)
    
    # ── Visualization ──
    fig = plt.figure(figsize=(16, 10))
    fig.patch.set_facecolor('#050505')
    
    # MAIN PLOT: 3D Chandelier with descent path
    ax1 = fig.add_subplot(2, 2, 1, projection='3d')
    ax1.set_facecolor('#050505')
    
    # Draw the genus-3 surface as a translucent wireframe
    X, Y, Z, U, V = create_genus3_mesh(n_u=60, n_v=40)
    
    # Scale and position the surface to match the chandelier space
    X_s = X * 0.6
    Y_s = Y * 0.6
    Z_s = Z * 0.4 - 1.0
    
    # Compute potential on the surface for coloring
    surf_potential = chandelier_potential(X_s, Y_s, Z_s)
    
    ax1.plot_surface(X_s, Y_s, Z_s, facecolors=plt.cm.magma(
        (surf_potential - surf_potential.min()) / (surf_potential.max() - surf_potential.min() + 1e-8)
    ), alpha=0.25, rstride=2, cstride=2, linewidth=0, antialiased=True)
    
    # Plot the falling trajectory as glowing beads
    for i in range(len(trajectory) - 1):
        alpha = 0.3 + 0.7 * (i / len(trajectory))
        ax1.plot(trajectory[i:i+2, 0], trajectory[i:i+2, 1], trajectory[i:i+2, 2],
                color=colors[i], linewidth=2.0, alpha=alpha)
    
    # Mark flashes
    for fp in flash_points:
        ax1.scatter(*trajectory[fp], color='gold', s=80, marker='o', 
                   edgecolors='white', linewidths=1.0, alpha=1.0, zorder=10)
    
    # Mark start and end
    ax1.scatter(*trajectory[0], color='white', s=100, marker='^', 
               edgecolors='black', linewidths=1.5, zorder=10)
    ax1.scatter(*trajectory[-1], color='red', s=150, marker='*', 
               edgecolors='gold', linewidths=1.0, zorder=10)
    
    ax1.text(trajectory[0, 0], trajectory[0, 1], trajectory[0, 2] + 0.3, 
            'CEILING\n(max Φ)', color='white', fontsize=9, ha='center')
    ax1.text(trajectory[-1, 0], trajectory[-1, 1], trajectory[-1, 2] - 0.5, 
            'TIP\n(ground state)', color='gold', fontsize=9, ha='center')
    
    ax1.set_title('The Chandelier Manifold\n(Genus-3 surface + shrinking basins)',
                  color='white', fontsize=11, fontweight='bold')
    ax1.set_xlabel('X', color='white')
    ax1.set_ylabel('Y', color='white')
    ax1.set_zlabel('Z (height)', color='white')
    ax1.tick_params(colors='white')
    ax1.grid(False)
    
    # PLOT 2: Potential vs Time
    ax2 = fig.add_subplot(2, 2, 2)
    ax2.set_facecolor('#050505')
    
    time = np.arange(len(potentials))
    ax2.fill_between(time, potentials.min(), potentials, 
                     where=(shifts > 1.0), color='cyan', alpha=0.2, label='Blue shift (falling)')
    ax2.fill_between(time, potentials.min(), potentials, 
                     where=(shifts <= 1.0), color='red', alpha=0.2, label='Red shift (stable)')
    ax2.plot(time, potentials, color='white', linewidth=1.0)
    
    for fp in flash_points:
        ax2.axvline(x=fp, color='gold', linestyle='--', alpha=0.6, linewidth=1.0)
    
    ax2.set_title('Potential Energy vs Time\n(conservation drives descent)',
                  color='white', fontsize=11, fontweight='bold')
    ax2.set_xlabel('Step', color='white')
    ax2.set_ylabel('Φ (potential)', color='white')
    ax2.tick_params(colors='white')
    ax2.legend(loc='upper right', facecolor='black', edgecolor='white', labelcolor='white')
    for spine in ax2.spines.values():
        spine.set_color('white')
    
    # PLOT 3: Doppler Shift (Blue/Red)
    ax3 = fig.add_subplot(2, 2, 3)
    ax3.set_facecolor('#050505')
    
    ax3.fill_between(time, 0.5, shifts, where=(shifts > 1.0), color='cyan', alpha=0.4)
    ax3.fill_between(time, 0.5, shifts, where=(shifts <= 1.0), color='red', alpha=0.4)
    ax3.plot(time, shifts, color='white', linewidth=1.2)
    ax3.axhline(y=1.0, color='yellow', linestyle='--', alpha=0.5, label='Unity (no shift)')
    
    for fp in flash_points:
        ax3.axvline(x=fp, color='gold', linestyle='--', alpha=0.6)
    
    ax3.set_title('Gravitational Doppler Shift\n(BLUE = falling, RED = stable)',
                  color='white', fontsize=11, fontweight='bold')
    ax3.set_xlabel('Step', color='white')
    ax3.set_ylabel('ν/ν₀', color='white')
    ax3.tick_params(colors='white')
    ax3.legend(loc='upper right', facecolor='black', edgecolor='white', labelcolor='white')
    for spine in ax3.spines.values():
        spine.set_color('white')
    ax3.set_ylim(0.5, 1.5)
    
    # PLOT 4: The Chandelier Tiers (cross-section)
    ax4 = fig.add_subplot(2, 2, 4)
    ax4.set_facecolor('#050505')
    
    # Create a cross-section of the potential at y=0
    z_range = np.linspace(-4, 6, 200)
    r_range = np.linspace(0, 5, 200)
    Z_cross, R_cross = np.meshgrid(z_range, r_range)
    Phi_cross = chandelier_potential(R_cross, 0, Z_cross)
    
    im = ax4.imshow(Phi_cross, extent=[-4, 6, 0, 5], origin='lower',
                    cmap='magma', aspect='auto', vmin=-3, vmax=5)
    
    # Overlay the trajectory projected onto the r-z plane
    r_traj = np.sqrt(trajectory[:, 0]**2 + trajectory[:, 1]**2)
    for i in range(len(trajectory) - 1):
        ax4.plot(trajectory[i:i+2, 2], r_traj[i:i+2], 
                color=colors[i], linewidth=2.5, alpha=0.7)
    
    # Mark flashes
    for fp in flash_points:
        ax4.scatter(trajectory[fp, 2], r_traj[fp], color='gold', s=60, zorder=10)
    
    ax4.set_title('Chandelier Cross-Section\n(radial distance vs height)',
                  color='white', fontsize=11, fontweight='bold')
    ax4.set_xlabel('Z (height)', color='white')
    ax4.set_ylabel('r (radial distance)', color='white')
    ax4.tick_params(colors='white')
    for spine in ax4.spines.values():
        spine.set_color('white')
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, facecolor='#050505')
        print(f"\n💾 Saved to: {output_path}")
    else:
        default_path = "/home/allaun/Documents/Research Stack/out/chandelier_genus3_descent.png"
        Path(default_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(default_path, dpi=150, facecolor='#050505')
        print(f"\n💾 Saved to: {default_path}")
    
    plt.close()
    
    # Summary
    final_phi = potentials[-1]
    print(f"\n{'='*60}")
    print("DESCENT COMPLETE")
    print(f"{'='*60}")
    print(f"Final position:     [{trajectory[-1, 0]:.4f}, {trajectory[-1, 1]:.4f}, {trajectory[-1, 2]:.4f}]")
    print(f"Final potential:    {final_phi:.4f}")
    print(f"Total energy drop:  {phi_ref - final_phi:.4f}")
    print(f"Phase transitions:  {len(flash_points)}")
    print(f"Max blue shift:     {shifts.max():.4f}")
    print(f"Final red shift:    {shifts[-1]:.4f}")
    print(f"\nThe parameter fell from the ceiling to the tip.")
    print(f"The chandelier collected the energy at its point.")
    print(f"Torsion increased. The manifold found its ground state.")
    
    return trajectory, potentials, shifts, flash_points


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Chandelier Genus-3 Descent")
    parser.add_argument("--steps", type=int, default=600, help="Number of steps")
    parser.add_argument("--dt", type=float, default=0.02, help="Step size")
    parser.add_argument("--output", type=str, default=None, help="Output PNG path")
    args = parser.parse_args()
    
    chandelier_descent(
        steps=args.steps,
        dt=args.dt,
        output_path=args.output
    )
