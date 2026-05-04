#!/usr/bin/env python3
"""
Pulsar Marble-Jar Model — Multiscale Event-Driven Simulation

Physical basis:
  A neutron star = 10^57 neutrons (marbles) in a superfluid (jar).
  Vortices are pinned to crustal nuclei. Mutual friction drains rotation.
  Individual unpinning events are invisible; collectively they spin-down the star.
  When pinning fails catastrophically: glitch = phase-transition flash.

Timescales:
  Cruise (years)    : magnetic braking + vortex creep
  Glitch (seconds)  : avalanche, angular momentum transfer
  Recovery (days)   : vortices repin, crust relaxes

Units:
  Time      : years (cruise) / seconds (glitch)
  Frequency : Hz
  Energy    : 10^33 J (one "unit")
  Inertia   : 10^38 kg m^2

No "up/down" — only torsional direction (rotation axis).
Genus-3 surface embeds the vortex array topology.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import json
import os
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Tuple
from scipy.ndimage import gaussian_filter

# ─── Physical Constants (realistic, scaled) ──────────────────────────────────
YEAR_TO_SEC = 3.154e7
SEC_TO_YEAR = 1.0 / YEAR_TO_SEC

I_CRUST = 0.6        # Crust moment of inertia (fraction of total)
I_SF = 1.0           # Superfluid moment of inertia
I_TOTAL = I_CRUST + I_SF

B_FIELD = 1e12       # Surface B-field in Gauss (scaled)
R_STAR = 1.0         # Radius in 10 km units

TAU_CHAR = 1e6       # Characteristic spin-down age (years)
TAU_RECOVERY = 30.0  # Post-glitch recovery time (days)
TAU_CREEP = 500.0    # Vortex creep coupling timescale (years)

T_PIN_BASE = 1.0     # Base pinning threshold
T_PIN_WIDTH = 0.2    # Distribution width (some pins weaker)
GLITCH_DF = 0.05     # Fraction of pinned vortices that unpin in a glitch

# ─── Genus-3 Surface (unchanged topology) ────────────────────────────────────
def genus3_surface(u, v, R=3.0, r=1.0, p=0.6):
    rho = R + r * np.cos(v) + p * np.cos(3 * u)
    x = rho * np.cos(u)
    y = rho * np.sin(u)
    z = r * np.sin(v) + 0.3 * np.sin(3 * u)
    return x, y, z


def torsional_depth(u, v):
    """Local 'depth' = torsional curvature concentration. Higher near lobe centers."""
    d0 = np.minimum(np.abs(u - 0), np.abs(u - 2*np.pi))
    d1 = np.abs(u - 2*np.pi/3)
    d2 = np.abs(u - 4*np.pi/3)
    d_min = np.minimum(np.minimum(d0, d1), d2)
    depth = 3.0 / (1.0 + 5.0 * d_min) * (1.0 + 0.3 * np.cos(v))
    return depth


def genus3_mesh(n_u=80, n_v=40):
    u = np.linspace(0, 2*np.pi, n_u)
    v = np.linspace(0, 2*np.pi, n_v)
    U, V = np.meshgrid(u, v)
    X, Y, Z = genus3_surface(U, V)
    return X, Y, Z, U, V


# ─── Vortex ──────────────────────────────────────────────────────────────────
@dataclass
class Vortex:
    u: float
    v: float
    circulation: float = 1.0
    pinned: bool = True
    tension: float = 0.0
    unpin_age: float = 0.0       # When did it last unpin?
    repin_time: float = 0.0      # How long until it repins?
    
    def pos(self):
        x, y, z = genus3_surface(self.u, self.v)
        return np.array([x, y, z])


# ─── Flash Event ─────────────────────────────────────────────────────────────
@dataclass
class Flash:
    time_yr: float       # Time in years
    time_sec: float      # Time within glitch in seconds
    energy: float        # Flash energy released
    n_unpinned: int      # How many vortices unpin
    delta_omega_hz: float  # Glitch size (spin-up)
    recovery_time_days: float
    tier: int            # Which tier boundary crossed


# ─── Pulsar Marble-Jar Model ─────────────────────────────────────────────────
class PulsarMarbleJar:
    """Event-driven multiscale pulsar simulation."""
    
    def __init__(self, n_vortices=512, f0_hz=10.0):
        # Two-component rotation
        self.f_crust = f0_hz          # Crust spin frequency (Hz)
        self.f_sf = f0_hz * 1.0001   # Superfluid slightly ahead (vortex creep lag)
        self.omega_crust = 2 * np.pi * self.f_crust
        self.omega_sf = 2 * np.pi * self.f_sf
        
        # Conserved angular momentum (in units where I_total = 1)
        self.L_total = I_CRUST * self.omega_crust + I_SF * self.omega_sf
        
        # Vortex array
        self.vortices: List[Vortex] = []
        self._init_vortices(n_vortices)
        
        # State
        self.time_yr = 0.0
        self.in_glitch = False
        self.glitch_start_time_yr = 0.0
        self.glitch_clock_sec = 0.0
        self.recovery_clock_days = 0.0
        
        # Events
        self.flashes: List[Flash] = []
        
        # History (cruise sampling)
        self.history = {
            't_yr': [],
            'f_crust_hz': [],
            'f_sf_hz': [],
            'E_rot': [],
            'L_total': [],
            'n_pinned': [],
            'tension_max': [],
            'flash_count': [],
            'phase': []    # 'cruise', 'glitch', 'recovery'
        }
        
        # Tier boundaries for flash classification
        self.tier_thresholds = [0.5, 1.0, 2.0]  # Energy thresholds
        
        # Cruise sampling interval
        self.cruise_sample_interval = 100.0  # years
        self.last_sample_time = -self.cruise_sample_interval
        
    def _init_vortices(self, n):
        """Initialize vortices with clustering near lobe centers."""
        for i in range(n):
            if np.random.rand() < 0.35:
                lobe = np.random.choice(3)
                u_c = lobe * 2 * np.pi / 3
                u = u_c + np.random.normal(0, 0.25)
                v = np.pi + np.random.normal(0, 0.4)
            else:
                u = np.random.uniform(0, 2*np.pi)
                v = np.random.uniform(0, 2*np.pi)
            
            # Each vortex has slightly different pinning strength
            pin_variation = np.random.normal(0, T_PIN_WIDTH)
            
            self.vortices.append(Vortex(
                u=u % (2*np.pi),
                v=v % (2*np.pi),
                circulation=1.0 + 0.5 * np.random.poisson(0.3),
                pinned=True,
                tension=0.0,
                repin_time=np.inf
            ))
    
    def _vortex_density_grid(self, n_grid=32):
        """Compute smoothed vortex density on toroidal grid."""
        density = np.zeros((n_grid, n_grid))
        for v in self.vortices:
            iu = int((v.u / (2*np.pi)) * n_grid) % n_grid
            iv = int((v.v / (2*np.pi)) * n_grid) % n_grid
            density[iu, iv] += v.circulation
        density = gaussian_filter(density, sigma=1.2, mode='wrap')
        return density
    
    def _update_vortex_tensions(self):
        """Compute tension on each vortex from Magnus force and local density."""
        density = self._vortex_density_grid()
        n_grid = density.shape[0]
        
        max_tension = 0.0
        for v in self.vortices:
            iu = int((v.u / (2*np.pi)) * n_grid) % n_grid
            iv = int((v.v / (2*np.pi)) * n_grid) % n_grid
            local_depth = torsional_depth(v.u, v.v)
            local_rho = density[iu, iv]
            
            # Magnus force: F_M ~ ρ_s κ × (v_sf - v_crust)
            # Simplified: tension proportional to differential rotation and local depth
            delta_omega = abs(self.omega_sf - self.omega_crust)
            magnus = delta_omega * v.circulation * (1.0 + 0.8 * local_depth)
            repulsion = 0.2 * local_rho ** 1.5
            v.tension = magnus + repulsion
            max_tension = max(max_tension, v.tension)
        
        return max_tension
    
    def _enforce_L_conservation(self):
        """Hard correct to ensure L is exactly conserved."""
        L_now = I_CRUST * self.omega_crust + I_SF * self.omega_sf
        delta_L = self.L_total - L_now
        domega = delta_L / I_TOTAL
        self.omega_crust += domega
        self.omega_sf += domega
        self.f_crust = self.omega_crust / (2 * np.pi)
        self.f_sf = self.omega_sf / (2 * np.pi)
    
    # ── Cruise Phase (years) ────────────────────────────────────────────────
    def cruise_step(self, dt_yr):
        """Integrate spin-down between glitches. Large timestep in years."""
        dt = dt_yr
        
        # 1. Magnetic dipole braking: dΩ/dt = -Ω / τ_char * (Ω/Ω_0)^2
        # Characteristic age τ_char ~ 10^6 yr for canonical pulsar
        braking = -self.omega_crust / (TAU_CHAR * YEAR_TO_SEC) * (self.omega_crust / (2*np.pi*10))**2
        braking *= YEAR_TO_SEC  # convert to rad/s per year
        self.omega_crust += braking * dt
        
        # 2. Vortex creep: superfluid slowly couples to crust
        # Mutual friction torque transfers angular momentum over τ_creep
        delta_omega = self.omega_sf - self.omega_crust
        coupling = delta_omega / TAU_CREEP
        self.omega_sf -= coupling * dt * (I_CRUST / I_SF)
        self.omega_crust += coupling * dt
        
        # 3. Vortices slowly drift (creep motion)
        for v in self.vortices:
            if v.pinned:
                # Pinned vortices barely move — thermal creep
                du = 0.001 * np.sin(3*v.u) * dt / TAU_CREEP
                dv = 0.0005 * np.cos(v.v) * dt / TAU_CREEP
            else:
                # Unpinned vortices move with superfluid
                du = 0.1 * self.omega_sf * dt * SEC_TO_YEAR
                dv = 0.02 * dt * SEC_TO_YEAR
                # Check repin
                v.unpin_age += dt * YEAR_TO_SEC
                if v.unpin_age > v.repin_time:
                    v.pinned = True
                    v.unpin_age = 0
            
            v.u = (v.u + du) % (2*np.pi)
            v.v = (v.v + dv) % (2*np.pi)
        
        self._enforce_L_conservation()
        self.time_yr += dt
        
        # 4. Check for glitch trigger
        max_tension = self._update_vortex_tensions()
        if max_tension > T_PIN_BASE and not self.in_glitch:
            # Enter glitch phase
            self.in_glitch = True
            self.glitch_start_time_yr = self.time_yr
            self.glitch_clock_sec = 0.0
            return True  # signal: glitch triggered
        
        # 5. Sample history
        if self.time_yr - self.last_sample_time >= self.cruise_sample_interval:
            self._record_history('cruise')
            self.last_sample_time = self.time_yr
        
        return False
    
    # ── Glitch Phase (seconds) ──────────────────────────────────────────────
    def glitch_step(self, dt_sec):
        """Resolve glitch dynamics at second-scale resolution."""
        dt = dt_sec
        self.glitch_clock_sec += dt
        
        # Count how many vortices exceed threshold
        triggered = [v for v in self.vortices if v.pinned and v.tension > T_PIN_BASE]
        
        if len(triggered) > 0 and self.glitch_clock_sec < 10.0:
            # Avalanche: unpin a fraction of triggered vortices
            n_to_unpin = max(1, int(GLITCH_DF * len(triggered)))
            np.random.shuffle(triggered)
            unpinned = triggered[:n_to_unpin]
            
            # Each unpinned vortex transfers angular momentum from sf → crust
            # Real glitch: ΔΩ/Ω ~ 10^-8 to 10^-6
            # Each simulated vortex = ~10^14 real vortices
            total_dL = 0.0
            for v in unpinned:
                v.pinned = False
                v.unpin_age = 0.0
                v.repin_time = np.random.exponential(TAU_RECOVERY * 24 * 3600)  # seconds
                # Small angular momentum transfer per vortex
                dL = v.circulation * self.omega_sf * 1e-6 * I_SF
                total_dL += dL
            
            # Apply transfer
            self.omega_crust += total_dL / I_CRUST
            self.omega_sf -= total_dL / I_SF
            
            # Flash energy: rotational energy change + thermal dissipation
            E_flash = 0.5 * total_dL * (self.omega_crust - self.omega_sf)
            
            # Classify tier
            tier = sum(1 for th in self.tier_thresholds if E_flash > th)
            
            # Record flash
            self.flashes.append(Flash(
                time_yr=self.time_yr + self.glitch_clock_sec * SEC_TO_YEAR,
                time_sec=self.glitch_clock_sec,
                energy=E_flash,
                n_unpinned=len(unpinned),
                delta_omega_hz=total_dL / (2*np.pi * I_CRUST),
                recovery_time_days=TAU_RECOVERY,
                tier=tier
            ))
            
            # Update tensions after redistribution
            self._update_vortex_tensions()
        
        # Vortices move rapidly during glitch
        for v in self.vortices:
            if not v.pinned:
                du = 0.5 * self.omega_sf * dt
                dv = 0.1 * np.sin(v.v) * dt
                v.u = (v.u + du) % (2*np.pi)
                v.v = (v.v + dv) % (2*np.pi)
        
        self._enforce_L_conservation()
        
        # End glitch after a few seconds
        if self.glitch_clock_sec > 5.0:
            self.in_glitch = False
            self.recovery_clock_days = 0.0
            return True  # signal: glitch ended, enter recovery
        
        return False
    
    # ── Recovery Phase (days) ───────────────────────────────────────────────
    def recovery_step(self, dt_days):
        """Post-glitch relaxation. Vortices slowly repin."""
        self.recovery_clock_days += dt_days
        
        # During recovery, crust and superfluid re-equilibrate
        delta_omega = self.omega_sf - self.omega_crust
        # Recovery follows exponential relaxation with timescale τ_recovery
        relax_rate = dt_days / TAU_RECOVERY
        self.omega_crust += delta_omega * relax_rate * (I_SF / I_TOTAL)
        self.omega_sf -= delta_omega * relax_rate * (I_CRUST / I_TOTAL)
        
        # Repin vortices whose time is up
        for v in self.vortices:
            if not v.pinned:
                v.unpin_age += dt_days * 24 * 3600
                if v.unpin_age > v.repin_time:
                    v.pinned = True
                    v.unpin_age = 0
        
        self._enforce_L_conservation()
        self.time_yr += dt_days / 365.25
        
        # End recovery
        if self.recovery_clock_days > TAU_RECOVERY:
            return True  # signal: back to cruise
        
        return False
    
    def _record_history(self, phase):
        """Record state to history buffer."""
        self.history['t_yr'].append(self.time_yr)
        self.history['f_crust_hz'].append(self.f_crust)
        self.history['f_sf_hz'].append(self.f_sf)
        E_rot = 0.5 * I_CRUST * self.omega_crust**2 + 0.5 * I_SF * self.omega_sf**2
        self.history['E_rot'].append(E_rot)
        self.history['L_total'].append(self.L_total)
        self.history['n_pinned'].append(sum(1 for v in self.vortices if v.pinned))
        self.history['tension_max'].append(max(v.tension for v in self.vortices))
        self.history['flash_count'].append(len(self.flashes))
        self.history['phase'].append(phase)
    
    # ── Main Run Loop ───────────────────────────────────────────────────────
    def run(self, t_max_yr=2e6):
        """Run full multiscale simulation."""
        print(f"Starting multiscale simulation: 0 → {t_max_yr:.1e} years")
        print(f"Initial f_crust = {self.f_crust:.2f} Hz")
        print(f"Characteristic age = {TAU_CHAR:.1e} years")
        print(f"Vortices: {len(self.vortices)}")
        
        next_print = 0.0
        
        while self.time_yr < t_max_yr:
            if not self.in_glitch:
                # Cruise or recovery
                if self.recovery_clock_days > 0:
                    # In recovery
                    done = self.recovery_step(dt_days=1.0)
                    if done:
                        self.recovery_clock_days = 0.0
                else:
                    # In cruise
                    glitch_triggered = self.cruise_step(dt_yr=10.0)
                    if glitch_triggered:
                        print(f"  GLITCH TRIGGERED at t = {self.time_yr:.2e} yr")
                        print(f"    Max tension = {max(v.tension for v in self.vortices):.3f}")
            else:
                # In glitch — resolve at second scale
                done = self.glitch_step(dt_sec=0.1)
                if done:
                    print(f"    Glitch resolved: Δf = {self.flashes[-1].delta_omega_hz:.2e} Hz")
                    print(f"    {self.flashes[-1].n_unpinned} vortices unpinned")
            
            # Progress print
            if self.time_yr >= next_print:
                phase = 'GLITCH' if self.in_glitch else ('RECOVERY' if self.recovery_clock_days > 0 else 'CRUISE')
                print(f"  t={self.time_yr:.2e} yr | f={self.f_crust:.4f} Hz | "
                      f"flashes={len(self.flashes)} | phase={phase}")
                next_print += t_max_yr / 20
        
        # Final sample
        self._record_history('end')
        
        print(f"\n{'='*60}")
        print("SIMULATION COMPLETE")
        print(f"  Total time: {self.time_yr:.2e} years")
        print(f"  Final f_crust: {self.f_crust:.4f} Hz")
        print(f"  Total flashes: {len(self.flashes)}")
        print(f"  Final L deviation: {abs(I_CRUST*self.omega_crust + I_SF*self.omega_sf - self.L_total):.2e}")
        
        if self.flashes:
            sizes = [f.delta_omega_hz for f in self.flashes]
            print(f"  Glitch sizes: min={min(sizes):.2e}, max={max(sizes):.2e} Hz")
            intervals = np.diff([f.time_yr for f in self.flashes])
            if len(intervals) > 0:
                print(f"  Inter-glitch: mean={np.mean(intervals):.2e}, med={np.median(intervals):.2e} yr")


# ─── Visualization ───────────────────────────────────────────────────────────
def visualize(model, out_dir="/home/allaun/Documents/Research Stack/out"):
    os.makedirs(out_dir, exist_ok=True)
    
    fig = plt.figure(figsize=(18, 14))
    
    # ── Panel A: Spin-down curve (log-log) ─────────────────────────────────
    ax1 = fig.add_subplot(3, 3, 1)
    t = np.array(model.history['t_yr'])
    f = np.array(model.history['f_crust_hz'])
    ax1.loglog(t + 1, f, 'b-', linewidth=1, label='Crust spin')
    ax1.loglog(t + 1, np.array(model.history['f_sf_hz']), 'r--', alpha=0.5, linewidth=0.8, label='Superfluid')
    
    # Mark glitches
    for flash in model.flashes:
        ax1.axvline(flash.time_yr + 1, color='orange', alpha=0.4, linewidth=0.8)
    
    # Reference: pure dipole braking f ∝ t^(-1/2)
    t_ref = np.logspace(0, np.log10(t.max()+1), 50)
    f_ref = model.f_crust * (t_ref / (t_ref[0] + 1e3)) ** (-0.5)
    ax1.loglog(t_ref, f_ref, 'g:', alpha=0.5, label='∝ t^(-1/2) dipole')
    
    ax1.set_xlabel('Time (years)')
    ax1.set_ylabel('Spin frequency (Hz)')
    ax1.set_title('Spin-down over megayears')
    ax1.legend()
    ax1.set_ylim(bottom=0.1)
    
    # ── Panel B: Glitch sizes histogram ────────────────────────────────────
    ax2 = fig.add_subplot(3, 3, 2)
    if model.flashes:
        sizes = [f.delta_omega_hz for f in model.flashes]
        ax2.hist(np.log10(sizes), bins=20, color='steelblue', edgecolor='black', alpha=0.7)
        ax2.set_xlabel('log₁₀(Δf) [Hz]')
        ax2.set_ylabel('Count')
        ax2.set_title(f'Glitch size distribution (n={len(sizes)})')
    else:
        ax2.text(0.5, 0.5, 'No glitches', ha='center', va='center', transform=ax2.transAxes)
    
    # ── Panel C: Inter-glitch intervals ────────────────────────────────────
    ax3 = fig.add_subplot(3, 3, 3)
    if len(model.flashes) > 1:
        intervals = np.diff([f.time_yr for f in model.flashes])
        ax3.hist(np.log10(intervals + 1), bins=20, color='forestgreen', edgecolor='black', alpha=0.7)
        ax3.set_xlabel('log₁₀(Δt) [years]')
        ax3.set_ylabel('Count')
        ax3.set_title('Inter-glitch waiting times')
    else:
        ax3.text(0.5, 0.5, 'Need >1 glitch', ha='center', va='center', transform=ax3.transAxes)
    
    # ── Panel D: Energy budget over time ───────────────────────────────────
    ax4 = fig.add_subplot(3, 3, 4)
    E_rot = np.array(model.history['E_rot'])
    ax4.semilogy(t + 1, E_rot, 'k-', linewidth=1.5, label='Rotational E')
    # Approximate radiated energy = integral of braking torque
    # E_dot = I Ω dΩ/dt ≈ -I Ω² / τ_char
    E_rad = E_rot[0] * (1 - (f / model.history['f_crust_hz'][0])**2)
    ax4.semilogy(t + 1, E_rot[0] - E_rad, 'm--', alpha=0.5, label='Radiated away')
    ax4.set_xlabel('Time (years)')
    ax4.set_ylabel('Energy')
    ax4.set_title('Energy budget')
    ax4.legend()
    
    # ── Panel E: Angular momentum ──────────────────────────────────────────
    ax5 = fig.add_subplot(3, 3, 5)
    L = np.array(model.history['L_total'])
    ax5.plot(t, L, 'k-', linewidth=1.5)
    ax5.set_xlabel('Time (years)')
    ax5.set_ylabel('Angular momentum')
    ax5.set_title(f'L conserved (σ={np.std(L):.2e})')
    
    # ── Panel F: Vortex tension over time ──────────────────────────────────
    ax6 = fig.add_subplot(3, 3, 6)
    ax6.semilogy(t + 1, model.history['tension_max'], 'purple', linewidth=1)
    ax6.axhline(T_PIN_BASE, color='red', linestyle='--', label='Pin threshold')
    ax6.set_xlabel('Time (years)')
    ax6.set_ylabel('Max tension')
    ax6.set_title('Peak vortex tension')
    ax6.legend()
    
    # ── Panel G: 3D Genus-3 with final vortex state ────────────────────────
    ax7 = fig.add_subplot(3, 3, 7, projection='3d')
    X, Y, Z, U, V = genus3_mesh(n_u=60, n_v=30)
    depth_map = torsional_depth(U, V)
    ax7.plot_surface(X, Y, Z, facecolors=plt.cm.RdYlBu_r(depth_map / depth_map.max()),
                     alpha=0.3, rstride=2, cstride=2, linewidth=0.1)
    
    vtx_pos = np.array([v.pos() for v in model.vortices])
    tensions = np.array([v.tension for v in model.vortices])
    pinned = np.array([v.pinned for v in model.vortices])
    
    if len(vtx_pos) > 0:
        # Color by tension, shape by pinned status
        scatter = ax7.scatter(vtx_pos[:, 0], vtx_pos[:, 1], vtx_pos[:, 2],
                              c=tensions, cmap='hot', s=20 + 60*tensions/T_PIN_BASE,
                              alpha=0.8, edgecolors='black', linewidth=0.2)
        plt.colorbar(scatter, ax=ax7, shrink=0.5, label='Tension')
    
    ax7.set_title('Final vortex array on genus-3')
    
    # ── Panel H: Pinned vs unpinned over time ──────────────────────────────
    ax8 = fig.add_subplot(3, 3, 8)
    ax8.plot(t, np.array(model.history['n_pinned']), 'b-', label='Pinned')
    ax8.plot(t, len(model.vortices) - np.array(model.history['n_pinned']), 'r--', label='Unpinned')
    ax8.set_xlabel('Time (years)')
    ax8.set_ylabel('Count')
    ax8.set_title('Vortex pinning state')
    ax8.legend()
    
    # ── Panel I: Flash timeline with tiers ─────────────────────────────────
    ax9 = fig.add_subplot(3, 3, 9)
    if model.flashes:
        ft = [f.time_yr for f in model.flashes]
        fe = [f.energy for f in model.flashes]
        fc = [f.n_unpinned for f in model.flashes]
        tiers = [f.tier for f in model.flashes]
        
        colors = ['lightblue', 'yellow', 'orange', 'red']
        c_list = [colors[min(t, 3)] for t in tiers]
        
        ax9.scatter(ft, fe, c=c_list, s=[20 + 5*c for c in fc],
                   alpha=0.7, edgecolors='black', linewidth=0.5)
        ax9.set_xlabel('Time (years)')
        ax9.set_ylabel('Flash energy')
        ax9.set_title('Phase transition flashes')
        ax9.set_yscale('log')
    else:
        ax9.text(0.5, 0.5, 'No flashes', ha='center', va='center', transform=ax9.transAxes)
    
    plt.tight_layout()
    out_path = os.path.join(out_dir, f"marble_jar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {out_path}")
    
    # Second figure: Zoomed glitch detail (if any glitches)
    if model.flashes:
        fig2, axes = plt.subplots(2, 3, figsize=(15, 8))
        
        for idx, ax in enumerate(axes.flat):
            if idx >= min(6, len(model.flashes)):
                ax.axis('off')
                continue
            
            flash = model.flashes[idx]
            # Mock detailed profile: exponential recovery
            t_g = np.linspace(0, TAU_RECOVERY, 200)
            delta_f = flash.delta_omega_hz * np.exp(-t_g / TAU_RECOVERY)
            
            ax.plot(t_g, delta_f * 1e6, 'b-', linewidth=1.5)
            ax.axvline(flash.time_sec / 86400, color='red', linestyle='--', alpha=0.5, label='Glitch')
            ax.set_xlabel('Days after glitch')
            ax.set_ylabel('Δf (μHz)')
            ax.set_title(f'Glitch {idx+1}: t={flash.time_yr:.2e} yr, tier={flash.tier}')
            ax.set_yscale('log')
        
        plt.tight_layout()
        out_path2 = os.path.join(out_dir, f"marble_jar_glitchdetail_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        plt.savefig(out_path2, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"Saved: {out_path2}")
        return out_path, out_path2
    
    return out_path, None


# ─── Export ──────────────────────────────────────────────────────────────────
def export_data(model, out_dir="/home/allaun/Documents/Research Stack/out"):
    os.makedirs(out_dir, exist_ok=True)
    
    data = {
        'metadata': {
            'model': 'PulsarMarbleJarMultiscale',
            'topology': 'genus-3',
            'n_vortices': len(model.vortices),
            't_max_yr': model.time_yr,
            'parameters': {
                'I_crust': I_CRUST,
                'I_sf': I_SF,
                'tau_char': TAU_CHAR,
                'tau_creep': TAU_CREEP,
                'tau_recovery': TAU_RECOVERY,
                'T_pin_base': T_PIN_BASE,
                'glitch_df': GLITCH_DF
            }
        },
        'history': {k: [float(x) if isinstance(x, (int, float, np.floating)) else x 
                        for x in v] 
                    for k, v in model.history.items()},
        'flashes': [
            {'time_yr': f.time_yr, 'time_sec': f.time_sec,
             'energy': f.energy, 'n_unpinned': f.n_unpinned,
             'delta_omega_hz': f.delta_omega_hz,
             'tier': f.tier}
            for f in model.flashes
        ],
        'final_state': {
            'f_crust_hz': model.f_crust,
            'f_sf_hz': model.f_sf,
            'L_total': model.L_total,
            'n_pinned': sum(1 for v in model.vortices if v.pinned),
            'n_flashes': len(model.flashes)
        }
    }
    
    out_path = os.path.join(out_dir, f"marble_jar_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(out_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Exported: {out_path}")
    return out_path


# ─── Main ────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 70)
    print("PULSAR MARBLE-JAR MODEL (Multiscale)")
    print("Cruise: years  |  Glitch: seconds  |  Recovery: days")
    print("=" * 70)
    
    model = PulsarMarbleJar(n_vortices=512, f0_hz=10.0)
    model.run(t_max_yr=2e6)
    
    print("\nGenerating visualizations...")
    paths = visualize(model)
    
    print("\nExporting data...")
    export_data(model)
    
    print("\n" + "=" * 70)
    print("ALL DONE")
    print("=" * 70)
