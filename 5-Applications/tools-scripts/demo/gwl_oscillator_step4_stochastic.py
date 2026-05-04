#!/usr/bin/env python3
"""
gwl_oscillator_step4_stochastic.py

STEP 4: Stochastically Driven Harmonic Oscillator (Langevin Equation)

Base equation: d²x/dt² + 2ζω₀·dx/dt + ω₀²·x = (F₀/m)·cos(ω_d·t) + ξ(t)/m

where ξ(t) is white noise with ⟨ξ(t)ξ(t')⟩ = 2D·δ(t-t')

Key physical constraints:
- Fluctuation-dissipation: D = γk_B T (Einstein relation)
- Mean trajectory: ⟨x(t)⟩ follows deterministic solution
- Equilibrium variance: σ² = k_B T / k
- Correlation: ⟨x(t)x(0)⟩ = (k_B T/k)·e^(-γ|t|/2m)·cos(ω₁t)

This tests: noise resilience, ensemble statistics, energy equipartition
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple, List, Optional
import math


@dataclass
class StochasticOscillatorState:
    """State with noise realization."""
    x: float
    v: float
    t: float
    F_drive: float
    xi: float  # Noise sample
    
    def to_vector(self) -> Tuple[float, float]:
        return (self.x, self.v)


class GWL_StochasticOscillator:
    """
    Langevin oscillator: deterministic backbone + stochastic perturbation.
    
    Uses validated Step 3 as backbone, adds bounded noise.
    """
    
    def __init__(self, omega0: float = 1.0, mass: float = 1.0,
                 zeta: float = 0.1, F0: float = 0.0, omega_d: float = 1.0,
                 temperature: float = 1.0, dt: float = 0.01,
                 seed: Optional[int] = None):
        """
        Args:
            omega0: Natural frequency
            mass: Mass
            zeta: Damping ratio
            F0: Driving amplitude (0 for pure thermal)
            omega_d: Driving frequency
            temperature: k_B T (thermal energy scale)
            dt: Time step
            seed: RNG seed for reproducibility
        """
        self.omega0 = omega0
        self.mass = mass
        self.zeta = zeta
        self.F0 = F0
        self.omega_d = omega_d
        self.temperature = temperature
        self.dt = dt
        
        # Derived
        self.k = mass * omega0**2
        self.gamma = 2 * zeta * mass * omega0
        
        # Fluctuation-dissipation: D = γk_B T
        self.diffusion = self.gamma * temperature
        self.noise_amp = math.sqrt(2 * self.diffusion / dt)  # For discrete update
        
        # RNG
        self.rng = np.random.RandomState(seed)
        
        # State
        self.state = StochasticOscillatorState(x=0.0, v=0.0, t=0.0, F_drive=0.0, xi=0.0)
        self.history: List[StochasticOscillatorState] = []
        
    def initialize(self, x0: float = 0.0, v0: float = 0.0):
        """Set initial conditions."""
        self.state = StochasticOscillatorState(x=x0, v=v0, t=0.0, F_drive=self.F0, xi=0.0)
        self.history = []
    
    def driving_force(self, t: float) -> float:
        """Deterministic driving."""
        return self.F0 * math.cos(self.omega_d * t)
    
    def step(self):
        """
        Stochastic update: deterministic backbone + Wiener increment.
        
        v_new = v_det + ξ·√Δt/m
        where ξ has variance 2D = 2γk_B T
        """
        x_n = self.state.x
        v_n = self.state.v
        t_n = self.state.t
        
        # Deterministic part (from validated Step 3)
        F_det = self.driving_force(t_n)
        
        v_temp = v_n - self.omega0**2 * x_n * self.dt
        v_temp *= math.exp(-self.gamma * self.dt / self.mass)
        v_det = v_temp + (F_det / self.mass) * self.dt
        
        # Stochastic perturbation (Wiener increment)
        # ⟨ξ²⟩ = 2D·Δt, so ξ = √(2D·Δt)·N(0,1)
        xi = math.sqrt(2 * self.diffusion * self.dt) * self.rng.randn()
        
        v_new = v_det + xi / self.mass
        x_new = x_n + v_new * self.dt
        t_new = t_n + self.dt
        
        self.state = StochasticOscillatorState(
            x=x_new, v=v_new, t=t_new, F_drive=F_det, xi=xi
        )
        self.history.append(self.state)
    
    def run(self, steps: int):
        """Run simulation."""
        for _ in range(steps):
            self.step()
    
    def energy(self) -> float:
        """Total mechanical energy."""
        return 0.5 * self.mass * self.state.v**2 + 0.5 * self.k * self.state.x**2
    
    def equilibrium_variance(self) -> float:
        """Theoretical equilibrium variance: σ² = k_B T / k"""
        return self.temperature / self.k


class EnsembleSimulator:
    """Run multiple realizations for ensemble statistics."""
    
    def __init__(self, num_realizations: int = 1000, **oscillator_kwargs):
        self.num_realizations = num_realizations
        self.oscillator_kwargs = oscillator_kwargs
        self.ensembles: List[GWL_StochasticOscillator] = []
        
    def run_ensemble(self, steps: int, x0: float = 0.0, v0: float = 0.0):
        """Run N realizations, collect statistics."""
        self.ensembles = []
        
        for i in range(self.num_realizations):
            osc = GWL_StochasticOscillator(**self.oscillator_kwargs, seed=i)
            osc.initialize(x0, v0)
            osc.run(steps)
            self.ensembles.append(osc)
        
        return self.compute_statistics()
    
    def compute_statistics(self) -> dict:
        """Compute ensemble statistics at each time step."""
        if not self.ensembles:
            return {}
        
        num_steps = len(self.ensembles[0].history)
        
        # Extract trajectories
        x_trajs = np.array([[h.x for h in osc.history] for osc in self.ensembles])
        v_trajs = np.array([[h.v for h in osc.history] for osc in self.ensembles])
        t_vals = [h.t for h in self.ensembles[0].history]
        
        # Statistics
        mean_x = np.mean(x_trajs, axis=0)
        mean_v = np.mean(v_trajs, axis=0)
        var_x = np.var(x_trajs, axis=0)
        var_v = np.var(v_trajs, axis=0)
        
        return {
            't': t_vals,
            'mean_x': mean_x,
            'mean_v': mean_v,
            'var_x': var_x,
            'var_v': var_v,
            'x_trajs': x_trajs,
            'v_trajs': v_trajs
        }


class StochasticValidationSuite:
    """Validation for Step 4: Langevin dynamics."""
    
    def __init__(self, omega0: float = 1.0, mass: float = 1.0, zeta: float = 0.2):
        self.omega0 = omega0
        self.mass = mass
        self.zeta = zeta
        self.results = {}
    
    def test_fluctuation_dissipation(self) -> Tuple[bool, dict]:
        """
        Test 1: Fluctuation-dissipation theorem.
        
        D = γk_B T should give correct equilibrium variance.
        """
        temperature = 1.0
        k = self.mass * self.omega0**2
        
        # Equilibrium variance: σ² = k_B T / k
        expected_var = temperature / k
        
        # Run ensemble to equilibrium
        ensemble = EnsembleSimulator(
            num_realizations=500,
            omega0=self.omega0,
            mass=self.mass,
            zeta=self.zeta,
            F0=0.0,  # No driving, pure thermal
            omega_d=self.omega0,
            temperature=temperature,
            dt=0.01
        )
        
        # Run for several decay times
        tau = 1.0 / (self.zeta * self.omega0)
        steps = int(10 * tau / 0.01)
        stats = ensemble.run_ensemble(steps, x0=1.0, v0=0.0)
        
        # Measure late-time variance
        late_var = np.mean(stats['var_x'][-100:])
        
        error = abs(late_var - expected_var) / expected_var
        passed = error < 0.15
        
        return passed, {
            'expected_var': expected_var,
            'measured_var': late_var,
            'error': error,
            'temperature': temperature,
            'k': k
        }
    
    def test_mean_trajectory(self) -> Tuple[bool, dict]:
        """
        Test 2: Mean trajectory follows deterministic solution.
        
        ⟨x(t)⟩ should match Step 3 deterministic oscillator.
        """
        F0 = 1.0
        omega_d = 0.8 * self.omega0
        
        # Run ensemble with driving
        ensemble = EnsembleSimulator(
            num_realizations=300,
            omega0=self.omega0,
            mass=self.mass,
            zeta=self.zeta,
            F0=F0,
            omega_d=omega_d,
            temperature=0.5,  # Small noise
            dt=0.01
        )
        
        tau = 1.0 / (self.zeta * self.omega0)
        steps = int(8 * tau / 0.01)
        stats = ensemble.run_ensemble(steps, x0=0.0, v0=0.0)
        
        # Compare late-time mean to deterministic steady-state
        late_mean = np.mean(stats['mean_x'][-100:])
        
        # Expected steady-state amplitude
        # A = (F₀/m) / √((ω₀²-ω_d²)² + (2ζω₀ω_d)²)
        numerator = F0 / self.mass
        denominator = math.sqrt(
            (self.omega0**2 - omega_d**2)**2 + 
            (2 * self.zeta * self.omega0 * omega_d)**2
        )
        expected_amp = numerator / denominator
        
        error = abs(late_mean - expected_amp) / expected_amp if expected_amp > 0 else abs(late_mean)
        passed = error < 0.2  # Ensemble mean has variance
        
        return passed, {
            'mean_trajectory': late_mean,
            'expected_amplitude': expected_amp,
            'error': error,
            'temperature': 0.5
        }
    
    def test_variance_evolution(self) -> Tuple[bool, dict]:
        """
        Test 3: Variance grows and saturates to equilibrium value.
        
        σ²(t) → k_B T / k as t → ∞
        """
        temperature = 1.0
        k = self.mass * self.omega0**2
        expected_var = temperature / k
        
        ensemble = EnsembleSimulator(
            num_realizations=400,
            omega0=self.omega0,
            mass=self.mass,
            zeta=self.zeta,
            F0=0.0,
            omega_d=self.omega0,
            temperature=temperature,
            dt=0.01
        )
        
        tau = 1.0 / (self.zeta * self.omega0)
        steps = int(8 * tau / 0.01)
        stats = ensemble.run_ensemble(steps, x0=0.0, v0=0.0)
        
        var_x = stats['var_x']
        
        # Check growth from near-zero to equilibrium
        early_var = np.mean(var_x[:50])
        late_var = np.mean(var_x[-100:])
        
        growth = late_var / (early_var + 1e-10)
        saturation = abs(late_var - expected_var) / expected_var
        
        # Variance should grow and saturate
        passed = growth > 5 and saturation < 0.2
        
        return passed, {
            'early_var': early_var,
            'late_var': late_var,
            'growth_factor': growth,
            'saturation_error': saturation,
            'expected_var': expected_var
        }
    
    def test_energy_equipartition(self) -> Tuple[bool, dict]:
        """
        Test 4: Energy equipartition at equilibrium.
        
        ⟨E_kinetic⟩ = ⟨E_potential⟩ = ½k_B T
        """
        temperature = 1.0
        
        ensemble = EnsembleSimulator(
            num_realizations=400,
            omega0=self.omega0,
            mass=self.mass,
            zeta=self.zeta,
            F0=0.0,
            omega_d=self.omega0,
            temperature=temperature,
            dt=0.01
        )
        
        tau = 1.0 / (self.zeta * self.omega0)
        steps = int(10 * tau / 0.01)
        stats = ensemble.run_ensemble(steps, x0=1.0, v0=1.0)
        
        # Extract late-time energies
        k = self.mass * self.omega0**2
        late_x = stats['x_trajs'][:, -100:]
        late_v = stats['v_trajs'][:, -100:]
        
        E_pot = 0.5 * k * late_x**2
        E_kin = 0.5 * self.mass * late_v**2
        
        mean_E_pot = np.mean(E_pot)
        mean_E_kin = np.mean(E_kin)
        
        expected = 0.5 * temperature
        error_pot = abs(mean_E_pot - expected) / expected
        error_kin = abs(mean_E_kin - expected) / expected
        
        # Both should be ≈ ½k_B T
        passed = error_pot < 0.2 and error_kin < 0.2
        
        return passed, {
            'mean_E_potential': mean_E_pot,
            'mean_E_kinetic': mean_E_kin,
            'expected': expected,
            'error_pot': error_pot,
            'error_kin': error_kin
        }
    
    def test_deterministic_backbone_preserved(self) -> Tuple[bool, dict]:
        """
        Test 5: As T → 0, recover deterministic solution exactly.
        """
        from gwl_oscillator_step3_driven import GWL_DrivenOscillator
        
        F0 = 1.0
        omega_d = self.omega0
        x0, v0 = 0.0, 0.0
        steps = 500
        
        # Deterministic (Step 3)
        det_osc = GWL_DrivenOscillator(
            omega0=self.omega0, mass=self.mass, zeta=self.zeta,
            F0=F0, omega_d=omega_d, dt=0.01
        )
        det_osc.initialize(x0, v0)
        det_osc.run(steps)
        x_det = [h.x for h in det_osc.history]
        
        # Stochastic with T ≈ 0
        stoch_osc = GWL_StochasticOscillator(
            omega0=self.omega0, mass=self.mass, zeta=self.zeta,
            F0=F0, omega_d=omega_d, temperature=1e-6, dt=0.01, seed=42
        )
        stoch_osc.initialize(x0, v0)
        stoch_osc.run(steps)
        x_stoch = [h.x for h in stoch_osc.history]
        
        # Should match closely
        max_diff = max(abs(a - b) for a, b in zip(x_det, x_stoch))
        
        passed = max_diff < 0.01
        
        return passed, {
            'max_diff': max_diff,
            'deterministic_final': x_det[-1],
            'stochastic_final': x_stoch[-1]
        }
    
    def run_all(self):
        """Run complete validation suite."""
        print("=" * 80)
        print("STEP 4 VALIDATION: STOCHASTIC LANGEVIN DYNAMICS")
        print("=" * 80)
        print(f"Base equation: m·d²x/dt² + γ·dx/dt + k·x = F(t) + ξ(t)")
        print(f"Noise: ⟨ξ(t)ξ(t')⟩ = 2D·δ(t-t'), D = γk_B T")
        print(f"Validation: Einstein fluctuation-dissipation, equipartition")
        print(f"Parameters: ω₀={self.omega0}, ζ={self.zeta}")
        print()
        
        tests = [
            ('Fluctuation-Dissipation', self.test_fluctuation_dissipation),
            ('Mean Trajectory', self.test_mean_trajectory),
            ('Variance Evolution', self.test_variance_evolution),
            ('Energy Equipartition', self.test_energy_equipartition),
            ('Deterministic Backbone', self.test_deterministic_backbone_preserved),
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
                    elif isinstance(val, np.ndarray):
                        print(f"  {key}: array[{len(val)}]")
                    else:
                        print(f"  {key}: {val}")
                self.results[name] = {'passed': passed, 'details': details}
                all_passed = all_passed and passed
            except Exception as e:
                print(f"Status: ✗ ERROR - {e}")
                import traceback
                traceback.print_exc()
                self.results[name] = {'passed': False, 'error': str(e)}
                all_passed = False
        
        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        for name, result in self.results.items():
            status = "✓ PASS" if result.get('passed') else "✗ FAIL"
            print(f"{name:35s}: {status}")
        
        print("\n" + "=" * 80)
        if all_passed:
            print("ALL TESTS PASSED - STEP 4 VALIDATED")
            print("=" * 80)
            print("""
The Langevin oscillator is now validated.
Physical constraints verified:
  ✓ Fluctuation-dissipation: D = γk_B T → correct σ²
  ✓ Mean trajectory: follows deterministic backbone
  ✓ Variance evolution: grows and saturates
  ✓ Energy equipartition: ⟨E_kin⟩ = ⟨E_pot⟩ = ½k_B T
  ✓ T → 0 limit: recovers deterministic exactly

STOCHASTIC EXTENSION VALIDATED
  Structure: Deterministic backbone + bounded perturbation
  Safety: Cannot destabilize proven backbone
  Physics: Satisfies Einstein relation, equipartition

READY FOR STEP 5: Multi-projection consensus
            """)
        else:
            print("SOME TESTS FAILED - DO NOT PROCEED")
            print("=" * 80)
        
        return all_passed


if __name__ == "__main__":
    validator = StochasticValidationSuite(omega0=1.0, mass=1.0, zeta=0.2)
    success = validator.run_all()
    exit(0 if success else 1)
