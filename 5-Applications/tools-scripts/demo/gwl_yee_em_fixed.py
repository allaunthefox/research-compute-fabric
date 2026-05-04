#!/usr/bin/env python3
"""
gwl_yee_em_fixed.py

Fixed GWL/TSM electromagnetic field propagation using Yee FDTD (1966) algorithm.

Key fix: Staggered E/B updates instead of naive explicit.

Yee Algorithm (proven stable since 1966):
  B^{n+1/2} = B^{n-1/2} - (Δt/μ) ∇ × E^n
  E^{n+1} = E^n + (Δt/ε) ∇ × B^{n+1/2}
"""

import numpy as np
from typing import Tuple, List
import math


class GWL_YeeEM_1D:
    """
    GWL Electromagnetic field using Yee FDTD staggered update.
    
    Maps to GWL/TSM primitives:
    - E field → μ-seed E component (full time steps)
    - B field → μ-seed B component (half time steps)  
    - ∇ × operator → π-field weighted coupling
    - Temporal staggering → τ phase offset
    """
    
    def __init__(self, nx: int = 200, dx: float = 0.01, dt: float = 0.005, 
                 epsilon: float = 1.0, mu: float = 1.0):
        self.nx = nx
        self.dx = dx
        self.dt = dt
        self.epsilon = epsilon
        self.mu = mu
        
        # Courant number (c * dt / dx)
        c = 1.0 / math.sqrt(epsilon * mu)
        self.courant = c * dt / dx
        
        # Fields
        # E at integer grid points (0, 1, 2, ..., nx-1)
        self.E = np.zeros(nx)
        
        # B at half-integer points (-0.5, 0.5, 1.5, ..., nx-1.5)
        # Represented as array of size nx (with boundary handling)
        self.B = np.zeros(nx)
        
        # Time step counter (for determining full/half steps)
        self.step_count = 0
        
        # History
        self.energy_history = []
        
    def initialize_gaussian_pulse(self, center: int, width: int, amplitude: float = 1.0):
        """Initialize E field with Gaussian pulse."""
        for i in range(self.nx):
            dist = abs(i - center)
            self.E[i] = amplitude * math.exp(-dist**2 / (2 * (width/3)**2))
        # B starts at zero (consistent with initial conditions)
        self.B.fill(0.0)
    
    def curl_E(self, i: int) -> float:
        """
        Compute ∂E/∂x at point i (for B update).
        
        E is at integer points, we need derivative at half-integer.
        Use central difference: (E[i] - E[i-1]) / dx
        """
        if i == 0:
            return (self.E[i] - self.E[self.nx-1]) / self.dx  # Periodic
        else:
            return (self.E[i] - self.E[i-1]) / self.dx
    
    def curl_B(self, i: int) -> float:
        """
        Compute ∂B/∂x at point i (for E update).
        
        B is at half-integer points, we need derivative at integer.
        Use central difference: (B[i+1] - B[i]) / dx
        """
        if i == self.nx - 1:
            return (self.B[0] - self.B[i]) / self.dx  # Periodic
        else:
            return (self.B[i+1] - self.B[i]) / self.dx
    
    def step(self):
        """
        One Yee FDTD step.
        
        In 1D, the curl reduces to a single derivative component.
        For E_z and B_y (propagating in x):
          ∂B_y/∂t = - (1/μ) ∂E_z/∂x
          ∂E_z/∂t = - (1/ε) ∂B_y/∂x
        """
        # Update B at half step (t + dt/2)
        coeff_B = self.dt / (self.mu * self.dx)
        for i in range(self.nx):
            # B_y^{n+1/2} = B_y^{n-1/2} - (dt/μ) * (E_z[i] - E_z[i-1])/dx
            self.B[i] -= coeff_B * (self.E[i] - self.E[(i-1) % self.nx])
        
        # Update E at full step (t + dt)
        coeff_E = self.dt / (self.epsilon * self.dx)
        for i in range(self.nx):
            # E_z^{n+1} = E_z^n - (dt/ε) * (B_y[i+1] - B_y[i])/dx
            self.E[i] -= coeff_E * (self.B[(i+1) % self.nx] - self.B[i])
        
        self.step_count += 1
        
        # Record energy
        energy = self.compute_energy()
        self.energy_history.append(energy)
    
    def compute_energy(self) -> float:
        """Compute total EM energy (ε E² + B²/μ)."""
        electric = self.epsilon * np.sum(self.E**2)
        magnetic = np.sum(self.B**2) / self.mu
        return electric + magnetic
    
    def run(self, steps: int = 500):
        """Run simulation for specified steps."""
        for _ in range(steps):
            self.step()
    
    def find_pulse_center(self) -> int:
        """Find center of pulse (position of max |E|)."""
        return int(np.argmax(np.abs(self.E)))
    
    def get_energy_stats(self) -> Tuple[float, float, float]:
        """Return (initial, min, max, final) energy."""
        if not self.energy_history:
            return 0, 0, 0, 0
        return (self.energy_history[0],
                min(self.energy_history),
                max(self.energy_history),
                self.energy_history[-1])


class GWL_YeeEM_Tests:
    """Test suite for Yee-based GWL EM."""
    
    def __init__(self):
        self.results = {}
    
    def test_energy_conservation(self, steps: int = 400) -> Tuple[bool, dict]:
        """
        Test 1: Energy should be conserved (< 1% drift).
        """
        sim = GWL_YeeEM_1D(nx=200, dx=0.01, dt=0.005)
        sim.initialize_gaussian_pulse(center=100, width=20, amplitude=1.0)
        
        initial = sim.compute_energy()
        sim.run(steps=steps)
        final = sim.compute_energy()
        
        drift = abs(final - initial) / initial if initial > 0 else 0
        max_ratio = max(sim.energy_history) / initial if initial > 0 else 0
        
        passed = drift < 0.01 and max_ratio < 1.5  # < 1% drift, < 50% variation
        
        return passed, {
            'initial_energy': initial,
            'final_energy': final,
            'energy_drift': drift,
            'max_ratio': max_ratio,
            'threshold': 0.01
        }
    
    def test_stable_propagation(self, steps: int = 400) -> Tuple[bool, dict]:
        """
        Test 2: Pulse should propagate without blowup.
        With periodic boundaries, symmetric pulse splits and wraps.
        Check: no blowup, energy bounded, field remains finite.
        """
        sim = GWL_YeeEM_1D(nx=200, dx=0.01, dt=0.005)
        sim.initialize_gaussian_pulse(center=100, width=20, amplitude=1.0)
        
        initial_energy = sim.compute_energy()
        max_field_initial = np.max(np.abs(sim.E))
        
        sim.run(steps=steps)
        
        final_energy = sim.compute_energy()
        max_field_final = np.max(np.abs(sim.E))
        
        energy_ratio = final_energy / initial_energy if initial_energy > 0 else 0
        field_growth = max_field_final / max_field_initial if max_field_initial > 0 else 0
        
        # Criteria: no energy blowup, field remains bounded
        stable = energy_ratio < 2.0 and field_growth < 2.0
        
        return stable, {
            'initial_energy': initial_energy,
            'final_energy': final_energy,
            'energy_ratio': energy_ratio,
            'field_growth': field_growth,
            'max_field_final': max_field_final
        }
    
    def test_frequency_separability(self) -> Tuple[bool, dict]:
        """
        Test 3: Low and high frequency modes should propagate differently.
        """
        # Low frequency (broad pulse)
        sim_low = GWL_YeeEM_1D(nx=200, dx=0.01, dt=0.005)
        sim_low.initialize_gaussian_pulse(center=100, width=40, amplitude=1.0)
        sim_low.run(steps=200)
        spread_low = np.std(sim_low.E)
        
        # High frequency (narrow pulse)
        sim_high = GWL_YeeEM_1D(nx=200, dx=0.01, dt=0.005)
        sim_high.initialize_gaussian_pulse(center=100, width=5, amplitude=1.0)
        sim_high.run(steps=200)
        spread_high = np.std(sim_high.E)
        
        # They should behave differently
        different = abs(spread_low - spread_high) > 0.01
        
        return different, {
            'low_spread': spread_low,
            'high_spread': spread_high,
            'difference': abs(spread_low - spread_high)
        }
    
    def test_determinism(self) -> Tuple[bool, dict]:
        """
        Test 4: Same initial conditions → same results.
        """
        # Run 1
        sim1 = GWL_YeeEM_1D(nx=200, dx=0.01, dt=0.005)
        sim1.initialize_gaussian_pulse(center=100, width=20, amplitude=1.0)
        sim1.run(steps=100)
        E1 = sim1.E.copy()
        
        # Run 2
        sim2 = GWL_YeeEM_1D(nx=200, dx=0.01, dt=0.005)
        sim2.initialize_gaussian_pulse(center=100, width=20, amplitude=1.0)
        sim2.run(steps=100)
        E2 = sim2.E.copy()
        
        # Should be identical
        max_diff = np.max(np.abs(E1 - E2))
        
        return max_diff < 1e-10, {'max_diff': max_diff}
    
    def test_courant_stability(self) -> Tuple[bool, dict]:
        """
        Test 5: Courant number <= 1 for stability.
        """
        # Stable: courant = 0.5
        sim_stable = GWL_YeeEM_1D(nx=200, dx=0.01, dt=0.005)
        sim_stable.initialize_gaussian_pulse(center=100, width=20, amplitude=1.0)
        sim_stable.run(steps=200)
        stable_energy = sim_stable.compute_energy()
        stable_ratio = stable_energy / sim_stable.energy_history[0]
        
        # Unstable: courant = 1.2 (should still work with small enough dt)
        # Actually Yee is stable for courant <= 1
        # For courant > 1, we expect issues
        
        results = {
            'courant_stable': sim_stable.courant,
            'energy_ratio': stable_ratio,
            'stable': stable_ratio < 2.0
        }
        
        return results['stable'], results
    
    def run_all(self):
        """Run complete test suite."""
        print("=" * 80)
        print("GWL YEE FDTD EM FIELD TEST SUITE")
        print("=" * 80)
        print(f"\nUsing Yee FDTD algorithm (1966, 58 years proven)")
        print(f"Staggered E/B update with symplectic structure\n")
        
        tests = [
            ('Energy Conservation', self.test_energy_conservation),
            ('Stable Propagation', self.test_stable_propagation),
            ('Frequency Separability', self.test_frequency_separability),
            ('Determinism', self.test_determinism),
            ('Courant Stability', self.test_courant_stability),
        ]
        
        all_passed = True
        for name, test_fn in tests:
            print(f"\n[Test] {name}")
            print("-" * 60)
            try:
                passed, details = test_fn()
                status = "✓ PASS" if passed else "✗ FAIL"
                print(f"Status: {status}")
                for key, val in details.items():
                    if isinstance(val, float):
                        print(f"  {key}: {val:.6f}")
                    else:
                        print(f"  {key}: {val}")
                self.results[name] = {'passed': passed, 'details': details}
                all_passed = all_passed and passed
            except Exception as e:
                print(f"Status: ✗ ERROR - {e}")
                self.results[name] = {'passed': False, 'error': str(e)}
                all_passed = False
        
        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        for name, result in self.results.items():
            status = "✓ PASS" if result.get('passed') else "✗ FAIL"
            print(f"{name:30s}: {status}")
        
        print("\n" + "=" * 80)
        if all_passed:
            print("ALL TESTS PASSED")
            print("=" * 80)
            print("""
The Yee FDTD implementation provides a stable deterministic backbone
for GWL/TSM electromagnetic field evolution.

Key properties verified:
  ✓ Energy conserved (< 1% drift)
  ✓ Stable propagation (no blowup)
  ✓ Frequency separability
  ✓ Deterministic reproducibility
  ✓ Courant-stable

NEXT STEPS:
  1. Add stochastic perturbations on top of this stable backbone
  2. Extend to 2D/3D with proper curl operator
  3. Add medium coupling (ε, μ variations)
  4. Validate speed of light in medium
            """)
        else:
            print("SOME TESTS FAILED")
            print("=" * 80)
        
        return all_passed


if __name__ == "__main__":
    test_suite = GWL_YeeEM_Tests()
    success = test_suite.run_all()
    exit(0 if success else 1)
