#!/usr/bin/env python3
"""
Pulsar Chandelier Model — Genus-3 Topology + Superfluid Vortex Dynamics

Physical basis:
- Two-component neutron star: rigid crust + superfluid interior
- Angular momentum conserved globally, redistributed between components
- Vortices in superfluid carry quantized circulation
- When vortex tension exceeds pinning strength: unpinning avalanche = "flash"
- Magnetic dipole braking provides slow damping
- Genus-3 surface embeds the vortex array topology
- Blue/red shift from relativistic rotational beaming

No "up/down" — only torsional direction (angular momentum axis).
"Depth" = proximity to vortex cluster center = higher energy density.

References:
[1] Manchester, R. 2017, "Millisecond Pulsars, their Evolution and Applications"
[2] Liu et al. 2023, "On the Spin Period Distribution of Millisecond Pulsars"
[3] Alpar et al. 1984, "Glitches in Pulsar Spin"
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import json
import os
from datetime import datetime

# ─── Physical Constants (scaled) ─────────────────────────────────────────────
G = 1.0          # Gravitational constant (scaled)
C = 10.0         # Speed of light (scaled so v < C always)
H_BAR = 0.1      # Reduced Planck constant (scaled)
M_STAR = 100.0   # Stellar mass (scaled)
R_STAR = 5.0     # Stellar radius (scaled)
I_CRUST = 50.0   # Crust moment of inertia
I_SF = 100.0     # Superfluid moment of inertia
K_DIPOLE = 0.001 # Magnetic dipole braking coefficient
T_PIN = 2.5      # Critical vortex pinning tension (flash threshold)
ETA_VISC = 0.01  # Crust-superfluid coupling viscosity
N_VORTICES = 512 # Number of vortices in superfluid

# ─── Genus-3 Surface Parametrization ─────────────────────────────────────────
def genus3_surface(u, v, R=3.0, r=1.0, p=0.6):
    """
    Parametric genus-3 surface (3-lobed torus).
    u, v in [0, 2π].
    Genus = number of holes = 3.
    """
    rho = R + r * np.cos(v) + p * np.cos(3 * u)
    x = rho * np.cos(u)
    y = rho * np.sin(u)
    z = r * np.sin(v) + 0.3 * np.sin(3 * u)
    return x, y, z


def genus3_normal(u, v, R=3.0, r=1.0, p=0.6, h=1e-5):
    """Compute unit normal vector at surface point (u,v)."""
    # Central difference for partial derivatives
    xp, yp, zp = genus3_surface(u + h, v, R, r, p)
    xm, ym, zm = genus3_surface(u - h, v, R, r, p)
    xu = (xp - xm) / (2 * h)
    yu = (yp - ym) / (2 * h)
    zu = (zp - zm) / (2 * h)
    
    xp, yp, zp = genus3_surface(u, v + h, R, r, p)
    xm, ym, zm = genus3_surface(u, v - h, R, r, p)
    xv = (xp - xm) / (2 * h)
    yv = (yp - ym) / (2 * h)
    zv = (zp - zm) / (2 * h)
    
    # Cross product
    nx = yu * zv - zu * yv
    ny = zu * xv - xu * zv
    nz = xu * yv - yu * xv
    n = np.sqrt(nx**2 + ny**2 + nz**2)
    return np.array([nx, ny, nz]) / n


def genus3_mesh(n_u=120, n_v=60):
    """Generate meshgrid for genus-3 surface."""
    u = np.linspace(0, 2*np.pi, n_u)
    v = np.linspace(0, 2*np.pi, n_v)
    U, V = np.meshgrid(u, v)
    X, Y, Z = genus3_surface(U, V)
    return X, Y, Z, U, V


# ─── Torsional Curvature ("Depth" Measure) ──────────────────────────────────
def torsional_depth(u, v):
    """
    Measure of local 'depth' = torsional curvature concentration.
    Higher where lobes pinch / vortices cluster.
    Peaks near the three lobe centers (u = 0, 2π/3, 4π/3).
    """
    # Three lobe centers
    d0 = np.minimum(np.abs(u - 0), np.abs(u - 2*np.pi))
    d1 = np.abs(u - 2*np.pi/3)
    d2 = np.abs(u - 4*np.pi/3)
    d_min = np.minimum(np.minimum(d0, d1), d2)
    
    # Depth = inverse distance to nearest lobe center, modulated by v
    depth = 3.0 / (1.0 + 5.0 * d_min) * (1.0 + 0.3 * np.cos(v))
    return depth


# ─── Vortex Class ────────────────────────────────────────────────────────────
class Vortex:
    """A quantized vortex line in the superfluid."""
    
    def __init__(self, u, v, circulation=1.0):
        self.u = u % (2 * np.pi)
        self.v = v % (2 * np.pi)
        self.circulation = circulation  # Quantized: n * h/m
        self.tension = 0.0              # Local pinning tension
        self.pinned = True              # Pinned to crustal nuclei
        self.age = 0
        
    def position(self):
        x, y, z = genus3_surface(self.u, self.v)
        return np.array([x, y, z])
    
    def move(self, du, dv, dt):
        """Advect vortex on surface (toroidal + poloidal drift)."""
        # Vortices drift with local superfluid velocity
        self.u = (self.u + du * dt) % (2 * np.pi)
        self.v = (self.v + dv * dt) % (2 * np.pi)
        self.age += dt
        
    def compute_tension(self, omega_sf, local_depth):
        """
        Tension = Magnus force + pinning + vortex-vortex interaction.
        Flash occurs when tension exceeds critical.
        """
        # Magnus force ~ ρ_s × (v_sf - v_crust) × κ
        magnus = abs(omega_sf) * self.circulation * (1.0 + 0.5 * local_depth)
        
        # Vortex-vortex repulsion (simplified: proportional to local density)
        # Computed externally and passed as part of local_depth
        repulsion = 0.3 * local_depth ** 2
        
        self.tension = magnus + repulsion
        return self.tension


# ─── Two-Component Pulsar Model ──────────────────────────────────────────────
class PulsarChandelier:
    """
    Two-component pulsar: crust + superfluid.
    Angular momentum conserved. Energy tracked.
    """
    
    def __init__(self, n_vortices=N_VORTICES):
        self.omega_crust = 2.0 * np.pi * 2.1   # Initial: 2.1 Hz (disco pulse!)
        self.omega_sf = self.omega_crust * 1.001  # Superfluid slightly ahead (vortex creep)
        self.I_crust = I_CRUST
        self.I_sf = I_SF
        
        # Total angular momentum (conserved!)
        self.L_total = self.I_crust * self.omega_crust + self.I_sf * self.omega_sf
        
        # Vortex array
        self.vortices = []
        self._init_vortices(n_vortices)
        
        # State tracking
        self.time = 0.0
        self.dt = 0.01
        self.flashes = []       # (time, energy_released, n_unpinned)
        self.history = {
            't': [],
            'omega_crust': [],
            'omega_sf': [],
            'E_rot': [],
            'E_mag': [],
            'L_total': [],
            'n_pinned': [],
            'tension_max': [],
            'flash_count': []
        }
        
        # Phase transition counters
        self.tier_boundaries = [1.5, 2.5, 4.0]  # Tension thresholds for tier flashes
        self.tier_flash_count = [0, 0, 0]
        
    def _init_vortices(self, n):
        """Initialize vortices uniformly, then let them cluster."""
        # Start with some clustering near lobe centers
        for i in range(n):
            if np.random.rand() < 0.4:
                # Cluster near one of three lobe centers
                lobe = np.random.choice(3)
                u_center = lobe * 2 * np.pi / 3
                u = u_center + np.random.normal(0, 0.3)
                v = np.pi + np.random.normal(0, 0.5)
            else:
                u = np.random.uniform(0, 2*np.pi)
                v = np.random.uniform(0, 2*np.pi)
            self.vortices.append(Vortex(u, v, circulation=H_BAR * (1 + np.random.poisson(0.5))))
    
    @property
    def omega_crust(self):
        return self._omega_crust
    
    @omega_crust.setter
    def omega_crust(self, val):
        self._omega_crust = val
    
    @property
    def omega_sf(self):
        return self._omega_sf
    
    @omega_sf.setter
    def omega_sf(self, val):
        self._omega_sf = val
        
    def rotational_energy(self):
        return 0.5 * self.I_crust * self.omega_crust**2 + 0.5 * self.I_sf * self.omega_sf**2
    
    def magnetic_energy(self):
        """Dipole magnetic energy ~ B² ~ ω² (simplified braking model)."""
        return 0.1 * self.omega_crust**2
    
    def total_energy(self):
        return self.rotational_energy() + self.magnetic_energy()
    
    def check_angular_momentum(self):
        """Verify L is conserved (debug check)."""
        L_now = self.I_crust * self.omega_crust + self.I_sf * self.omega_sf
        deviation = abs(L_now - self.L_total)
        return deviation < 1e-3, deviation
    
    def vortex_cluster_density(self):
        """Compute local vortex density on a grid for tension calculation."""
        n_grid = 48
        u_grid = np.linspace(0, 2*np.pi, n_grid)
        v_grid = np.linspace(0, 2*np.pi, n_grid)
        density = np.zeros((n_grid, n_grid))
        
        for vtx in self.vortices:
            iu = int((vtx.u / (2*np.pi)) * n_grid) % n_grid
            iv = int((vtx.v / (2*np.pi)) * n_grid) % n_grid
            density[iu, iv] += vtx.circulation
            
        # Smooth
        from scipy.ndimage import gaussian_filter
        density = gaussian_filter(density, sigma=1.5, mode='wrap')
        return u_grid, v_grid, density
    
    def step(self):
        """One integration step."""
        dt = self.dt
        
        # 1. Magnetic dipole braking on crust: dω/dt = -K·ω³/I
        braking = -K_DIPOLE * self.omega_crust**3 / self.I_crust
        self.omega_crust += braking * dt
        
        # 2. Vortex creep: superfluid tries to spin down slower than crust
        # Vortices slowly move outward, transferring angular momentum
        delta_omega = self.omega_sf - self.omega_crust
        coupling = ETA_VISC * delta_omega
        
        # 3. Update vortex positions (drift with superfluid)
        u_grid, v_grid, density = self.vortex_cluster_density()
        
        n_unpinned = 0
        flash_energy = 0.0
        
        for vtx in self.vortices:
            # Local depth and density
            iu = int((vtx.u / (2*np.pi)) * len(u_grid)) % len(u_grid)
            iv = int((vtx.v / (2*np.pi)) * len(v_grid)) % len(v_grid)
            local_depth = torsional_depth(vtx.u, vtx.v)
            local_density = density[iu, iv]
            
            # Compute tension
            tension = vtx.compute_tension(self.omega_sf, local_depth + 0.1 * local_density)
            
            # Vortex drift velocity (radial outward + azimuthal)
            # Outward drift: vortices move to larger u where density is lower
            du = 0.05 * self.omega_sf + 0.02 * np.sin(3 * vtx.u)
            dv = 0.01 * np.cos(vtx.v) * local_depth
            
            if vtx.pinned:
                # Check for unpinning (flash condition)
                if tension > T_PIN:
                    vtx.pinned = False
                    n_unpinned += 1
                    # Unpinning releases energy: vortex sudden motion
                    flash_energy += 0.5 * vtx.circulation * tension**2
                    # Sudden angular momentum transfer: superfluid → crust
                    # Small glitch: ~0.1% of local vortex angular momentum
                    dL = vtx.circulation * self.omega_sf * 0.01
                    self.omega_crust += dL / self.I_crust
                    self.omega_sf -= dL / self.I_sf
                else:
                    # Pinned vortices don't move (coupled to crust)
                    du *= 0.1
                    dv *= 0.1
            
            vtx.move(du, dv, dt)
        
        # 4. Recouple superfluid to crust (viscous relaxation)
        self.omega_sf -= coupling * dt / self.I_sf
        self.omega_crust += coupling * dt / self.I_crust
        
        # 5. Enforce angular momentum conservation exactly
        L_now = self.I_crust * self.omega_crust + self.I_sf * self.omega_sf
        delta_L = self.L_total - L_now
        # Distribute correction: same dω to both preserves L most naturally
        domega = delta_L / (self.I_crust + self.I_sf)
        self.omega_crust += domega
        self.omega_sf += domega
        
        # 6. Record flash
        if n_unpinned > 0:
            self.flashes.append((self.time, flash_energy, n_unpinned))
            # Count tier flashes
            for idx, threshold in enumerate(self.tier_boundaries):
                if flash_energy > threshold:
                    self.tier_flash_count[idx] += 1
        
        # 7. Record history
        self.history['t'].append(self.time)
        self.history['omega_crust'].append(self.omega_crust)
        self.history['omega_sf'].append(self.omega_sf)
        self.history['E_rot'].append(self.rotational_energy())
        self.history['E_mag'].append(self.magnetic_energy())
        self.history['L_total'].append(self.L_total)
        self.history['n_pinned'].append(sum(1 for v in self.vortices if v.pinned))
        self.history['tension_max'].append(max(v.tension for v in self.vortices))
        self.history['flash_count'].append(len(self.flashes))
        
        self.time += dt
        
    def run(self, t_max=100.0):
        """Run simulation."""
        n_steps = int(t_max / self.dt)
        for i in range(n_steps):
            self.step()
            if i % 1000 == 0:
                L_ok, L_dev = self.check_angular_momentum()
                print(f"  t={self.time:.2f}, ω_crust={self.omega_crust:.4f}, "
                      f"flashes={len(self.flashes)}, L_dev={L_dev:.2e}")
        
        print(f"\nSimulation complete.")
        print(f"  Total flashes: {len(self.flashes)}")
        print(f"  Final ω_crust: {self.omega_crust:.4f} rad/s ({self.omega_crust/(2*np.pi):.4f} Hz)")
        print(f"  Angular momentum conserved: {self.check_angular_momentum()}")
        print(f"  Energy change: {self.history['E_rot'][-1] - self.history['E_rot'][0]:.4f}")
        print(f"  Tier flash counts: {self.tier_flash_count}")


# ─── Visualization ───────────────────────────────────────────────────────────
def visualize(pulsar, out_dir="/home/allaun/Documents/Research Stack/out"):
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Main figure: 3D genus-3 surface with vortices colored by Doppler shift
    fig = plt.figure(figsize=(18, 12))
    
    # ── Panel A: 3D Surface with Vortices ──────────────────────────────────
    ax1 = fig.add_subplot(2, 3, 1, projection='3d')
    X, Y, Z, U, V = genus3_mesh(n_u=80, n_v=40)
    
    # Surface colored by torsional depth (the "basin")
    depth_map = torsional_depth(U, V)
    surf = ax1.plot_surface(X, Y, Z, facecolors=plt.cm.RdYlBu_r(depth_map / depth_map.max()),
                            alpha=0.4, rstride=2, cstride=2, linewidth=0.1)
    
    # Vortex positions with Doppler shift coloring
    # Blue shift = approaching (high ω, near rotation axis)
    # Red shift = receding
    vtx_pos = np.array([v.position() for v in pulsar.vortices])
    vtx_tensions = np.array([v.tension for v in pulsar.vortices])
    
    # Doppler factor from rotational velocity
    # v_phi = ω × r_perp, blueshift when moving toward observer (+x direction)
    if len(vtx_pos) > 0:
        r_perp = np.sqrt(vtx_pos[:, 1]**2 + vtx_pos[:, 2]**2)
        v_phi = pulsar.omega_crust * r_perp
        # Simplified Doppler: project onto x-axis (observer at +x)
        doppler = v_phi * np.sign(vtx_pos[:, 1]) / C  # β = v/c
        doppler = np.clip(doppler, -0.3, 0.3)
        
        scatter = ax1.scatter(vtx_pos[:, 0], vtx_pos[:, 1], vtx_pos[:, 2],
                              c=doppler, cmap='RdBu_r', s=20 + 80 * vtx_tensions / T_PIN,
                              alpha=0.9, edgecolors='black', linewidth=0.3)
        plt.colorbar(scatter, ax=ax1, shrink=0.5, label='Doppler shift β=v/c')
    
    ax1.set_title('Genus-3 Surface: Vortices (color=Doppler, size=tension)')
    ax1.set_xlabel('X')
    ax1.set_ylabel('Y')
    ax1.set_zlabel('Z')
    
    # ── Panel B: ω vs Time ─────────────────────────────────────────────────
    ax2 = fig.add_subplot(2, 3, 2)
    t = np.array(pulsar.history['t'])
    ax2.plot(t, np.array(pulsar.history['omega_crust']) / (2*np.pi), 'b-', label='Crust ω', linewidth=1)
    ax2.plot(t, np.array(pulsar.history['omega_sf']) / (2*np.pi), 'r--', label='Superfluid ω', linewidth=1, alpha=0.7)
    
    # Mark flash events
    for flash_time, flash_energy, n_unpinned in pulsar.flashes:
        ax2.axvline(flash_time, color='orange', alpha=0.3, linewidth=0.5)
    ax2.set_xlabel('Time')
    ax2.set_ylabel('Spin frequency (Hz)')
    ax2.set_title('Rotational Evolution (2.1 Hz → slower)')
    ax2.legend()
    ax2.set_yscale('log')
    
    # ── Panel C: Energy Budget ─────────────────────────────────────────────
    ax3 = fig.add_subplot(2, 3, 3)
    E_rot = np.array(pulsar.history['E_rot'])
    E_mag = np.array(pulsar.history['E_mag'])
    ax3.plot(t, E_rot, 'g-', label='Rotational E')
    ax3.plot(t, E_mag, 'm-', label='Magnetic E')
    ax3.plot(t, E_rot + E_mag, 'k--', label='Total E', linewidth=1.5)
    ax3.set_xlabel('Time')
    ax3.set_ylabel('Energy')
    ax3.set_title('Energy Conservation')
    ax3.legend()
    
    # ── Panel D: Angular Momentum (should be flat!) ────────────────────────
    ax4 = fig.add_subplot(2, 3, 4)
    L = np.array(pulsar.history['L_total'])
    ax4.plot(t, L, 'k-', linewidth=1.5)
    ax4.set_xlabel('Time')
    ax4.set_ylabel('Angular Momentum')
    ax4.set_title(f'L Conservation (deviation: {np.std(L):.2e})')
    
    # ── Panel E: Tension Distribution / Phase Transitions ──────────────────
    ax5 = fig.add_subplot(2, 3, 5)
    tensions = [v.tension for v in pulsar.vortices]
    ax5.hist(tensions, bins=50, color='steelblue', edgecolor='black', alpha=0.7)
    for threshold in pulsar.tier_boundaries:
        ax5.axvline(threshold, color='red', linestyle='--', label=f'Tier {threshold}')
    ax5.set_xlabel('Vortex Tension')
    ax5.set_ylabel('Count')
    ax5.set_title('Final Tension Distribution')
    ax5.set_yscale('log')
    
    # ── Panel F: Flash Events Timeline ─────────────────────────────────────
    ax6 = fig.add_subplot(2, 3, 6)
    if pulsar.flashes:
        flash_times = [f[0] for f in pulsar.flashes]
        flash_energies = [f[1] for f in pulsar.flashes]
        flash_counts = [f[2] for f in pulsar.flashes]
        
        colors = []
        for e in flash_energies:
            if e > pulsar.tier_boundaries[2]:
                colors.append('red')
            elif e > pulsar.tier_boundaries[1]:
                colors.append('orange')
            elif e > pulsar.tier_boundaries[0]:
                colors.append('yellow')
            else:
                colors.append('lightblue')
        
        ax6.scatter(flash_times, flash_energies, c=colors, s=[20 + 5*c for c in flash_counts],
                   alpha=0.7, edgecolors='black', linewidth=0.5)
        ax6.set_xlabel('Time')
        ax6.set_ylabel('Flash Energy')
        ax6.set_title('Phase Transition Flashes')
        ax6.set_yscale('log')
    else:
        ax6.text(0.5, 0.5, 'No flashes', ha='center', va='center', transform=ax6.transAxes)
    
    plt.tight_layout()
    out_path = os.path.join(out_dir, f"pulsar_chandelier_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved visualization to {out_path}")
    
    # 2. Second figure: Vortex trajectory movie frame (static for now)
    fig2, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # Parametric plot: u-v space showing vortex clustering
    for idx, (ax, lobe_name, u_center) in enumerate(zip(axes, 
                                                          ['Lobe 1 (u=0)', 'Lobe 2 (u=2π/3)', 'Lobe 3 (u=4π/3)'],
                                                          [0, 2*np.pi/3, 4*np.pi/3])):
        u_vals = [v.u for v in pulsar.vortices]
        v_vals = [v.v for v in pulsar.vortices]
        tensions = [v.tension for v in pulsar.vortices]
        
        # Wrap u around lobe center
        u_wrapped = [(u - u_center + np.pi) % (2*np.pi) - np.pi for u in u_vals]
        
        scatter = ax.scatter(u_wrapped, v_vals, c=tensions, cmap='hot', s=30,
                            alpha=0.7, vmin=0, vmax=max(tensions) * 0.8)
        ax.set_xlim(-np.pi, np.pi)
        ax.set_ylim(0, 2*np.pi)
        ax.set_xlabel('Δu (relative to lobe)')
        ax.set_ylabel('v (poloidal)')
        ax.set_title(lobe_name)
        plt.colorbar(scatter, ax=ax, shrink=0.6, label='Tension')
    
    plt.tight_layout()
    out_path2 = os.path.join(out_dir, f"pulsar_chandelier_uv_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
    plt.savefig(out_path2, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved UV-space visualization to {out_path2}")
    
    return out_path, out_path2


# ─── Export Data ─────────────────────────────────────────────────────────────
def export_data(pulsar, out_dir="/home/allaun/Documents/Research Stack/out"):
    """Export simulation data as JSON for further analysis."""
    os.makedirs(out_dir, exist_ok=True)
    
    data = {
        'metadata': {
            'model': 'PulsarChandelier',
            'topology': 'genus-3',
            'n_vortices': len(pulsar.vortices),
            't_max': pulsar.time,
            'dt': pulsar.dt,
            'constants': {
                'I_crust': I_CRUST,
                'I_sf': I_SF,
                'K_dipole': K_DIPOLE,
                'T_pin': T_PIN,
                'eta_visc': ETA_VISC
            }
        },
        'history': {
            k: [float(x) for x in v] for k, v in pulsar.history.items()
        },
        'flashes': [
            {'time': float(t), 'energy': float(e), 'n_unpinned': int(n)}
            for t, e, n in pulsar.flashes
        ],
        'final_state': {
            'omega_crust_hz': float(pulsar.omega_crust / (2*np.pi)),
            'omega_sf_hz': float(pulsar.omega_sf / (2*np.pi)),
            'L_total': float(pulsar.L_total),
            'E_total': float(pulsar.total_energy()),
            'n_pinned': sum(1 for v in pulsar.vortices if v.pinned),
            'tier_flash_counts': pulsar.tier_flash_count
        }
    }
    
    out_path = os.path.join(out_dir, f"pulsar_chandelier_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(out_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Exported data to {out_path}")
    return out_path


# ─── Main ────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 60)
    print("PULSAR CHANDELIER MODEL")
    print("Genus-3 topology + superfluid vortex dynamics")
    print("=" * 60)
    
    pulsar = PulsarChandelier(n_vortices=N_VORTICES)
    print(f"\nInitial state:")
    print(f"  Crust spin: {pulsar.omega_crust/(2*np.pi):.2f} Hz")
    print(f"  Superfluid spin: {pulsar.omega_sf/(2*np.pi):.2f} Hz")
    print(f"  Total angular momentum: {pulsar.L_total:.2f}")
    print(f"  Vortices: {len(pulsar.vortices)}")
    print(f"  Flash thresholds (tiers): {pulsar.tier_boundaries}")
    
    print("\nRunning simulation...")
    pulsar.run(t_max=50.0)
    
    print("\nGenerating visualizations...")
    img1, img2 = visualize(pulsar)
    
    print("\nExporting data...")
    data_path = export_data(pulsar)
    
    print("\n" + "=" * 60)
    print("DONE")
    print(f"  Images: {img1}, {img2}")
    print(f"  Data: {data_path}")
    print("=" * 60)
