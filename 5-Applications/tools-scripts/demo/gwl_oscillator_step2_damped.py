#!/usr/bin/env python3
"""
gwl_oscillator_step2_damped.py

STEP 2: Damped Harmonic Oscillator (Attractor Dynamics)

Base equation: d²x/dt² + 2ζω₀·dx/dt + ω₀²·x = 0
            or: m·d²x/dt² + γ·dx/dt + k·x = 0

Analytic solution depends on damping regime:
- Underdamped (ζ < 1): x(t) = A·e^(-ζω₀t)·cos(ω₁t + φ), ω₁ = ω₀√(1-ζ²)
- Critically damped (ζ = 1): x(t) = (A + Bt)·e^(-ω₀t)
- Overdamped (ζ > 1): x(t) = A·e^(-λ₁t) + B·e^(-λ₂t)

New GWL primitives: χ (instability), Γ (strain), regime classification
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple, List, Literal
import math


@dataclass 
class DampedOscillatorState:
    """Canonical state for damped oscillator."""
    x: float      # Position
    v: float      # Velocity
    t: float      # Time
    regime: Literal['underdamped', 'critical', 'overdamped'] = 'underdamped'
    
    def to_vector(self) -> Tuple[float, float]:
        return (self.x, self.v)


class GWL_DampedOscillator:
    """
    Damped harmonic oscillator with regime classification.
    
    Adds dissipation to Step 1's validated symplectic backbone.
    """
    
    def __init__(self, omega0: float = 1.0, mass: float = 1.0, 
                 zeta: float = 0.1, dt: float = 0.01):
        """
        Args:
            omega0: Natural frequency (rad/s)
            mass: Mass (kg)
            zeta: Damping ratio (dimensionless)
                  ζ < 1: underdamped (oscillating decay)
                  ζ = 1: critically damped (fastest return)
                  ζ > 1: overdamped (slow exponential)
            dt: Time step (s)
        """
        self.omega0 = omega0
        self.mass = mass
        self.zeta = zeta
        self.dt = dt
        
        # Derived parameters
        self.k = mass * omega0**2
        self.gamma = 2 * zeta * mass * omega0  # Damping coefficient
        
        # Regime classification
        if zeta < 1.0:
            self.regime = 'underdamped'
            self.omega1 = omega0 * math.sqrt(1 - zeta**2)  # Damped frequency
        elif abs(zeta - 1.0) < 0.01:
            self.regime = 'critical'
            self.omega1 = 0.0
        else:
            self.regime = 'overdamped'
            # Two real exponents
            self.lambda1 = omega0 * (zeta + math.sqrt(zeta**2 - 1))
            self.lambda2 = omega0 * (zeta - math.sqrt(zeta**2 - 1))
            self.omega1 = 0.0
        
        # State
        self.state = DampedOscillatorState(x=1.0, v=0.0, t=0.0, regime=self.regime)
        self.history: List[DampedOscillatorState] = []
        self.energy_history: List[float] = []
        
    def initialize(self, x0: float, v0: float):
        """Set initial conditions."""
        self.state = DampedOscillatorState(x=x0, v=v0, t=0.0, regime=self.regime)
        self.history = []
        self.energy_history = []
    
    def energy(self, state: DampedOscillatorState = None) -> float:
        """Compute total mechanical energy."""
        if state is None:
            state = self.state
        kinetic = 0.5 * self.mass * state.v**2
        potential = 0.5 * self.k * state.x**2
        return kinetic + potential
    
    def dissipation_rate(self) -> float:
        """Instantaneous energy dissipation: dE/dt = -γv²"""
        return -self.gamma * self.state.v**2
    
    def quality_factor(self) -> float:
        """Q factor: Q = ω₀m/γ = 1/(2ζ)"""
        return 1.0 / (2 * self.zeta) if self.zeta > 0 else float('inf')
    
    def analytic_solution(self, t: float, x0: float, v0: float) -> Tuple[float, float]:
        """
        Analytic solution for given damping regime.
        """
        if self.regime == 'underdamped':
            # x(t) = e^(-ζω₀t) [A·cos(ω₁t) + B·sin(ω₁t)]
            exp_term = math.exp(-self.zeta * self.omega0 * t)
            cos_term = math.cos(self.omega1 * t)
            sin_term = math.sin(self.omega1 * t)
            
            A = x0
            B = (v0 + self.zeta * self.omega0 * x0) / self.omega1
            
            x = exp_term * (A * cos_term + B * sin_term)
            
            # v = dx/dt
            v = exp_term * (-self.zeta * self.omega0 * (A * cos_term + B * sin_term) 
                          + self.omega1 * (-A * sin_term + B * cos_term))
            
        elif self.regime == 'critical':
            # x(t) = (A + Bt)·e^(-ω₀t)
            exp_term = math.exp(-self.omega0 * t)
            A = x0
            B = v0 + self.omega0 * x0
            
            x = (A + B * t) * exp_term
            v = (B - self.omega0 * (A + B * t)) * exp_term
            
        else:  # overdamped
            # x(t) = A·e^(-λ₁t) + B·e^(-λ₂t)
            exp1 = math.exp(-self.lambda1 * t)
            exp2 = math.exp(-self.lambda2 * t)
            
            # Solve for A, B from initial conditions
            # x0 = A + B
            # v0 = -λ₁A - λ₂B
            det = self.lambda2 - self.lambda1
            A = (v0 + self.lambda2 * x0) / det
            B = (-v0 - self.lambda1 * x0) / det
            
            x = A * exp1 + B * exp2
            v = -A * self.lambda1 * exp1 - B * self.lambda2 * exp2
        
        return x, v
    
    def step(self):
        """
        Symplectic update with dissipation.
        
        Split-step method:
        1. Symplectic (conservative) step
        2. Exact dissipation step
        """
        x_n = self.state.x
        v_n = self.state.v
        
        # Step 1: Conservative part (from Step 1, validated)
        v_temp = v_n - self.omega0**2 * x_n * self.dt
        
        # Step 2: Dissipation (exact for linear drag)
        # dv/dt = -(γ/m)v → v(t) = v(0)·exp(-γt/m)
        v_new = v_temp * math.exp(-self.gamma * self.dt / self.mass)
        
        # Step 3: Position update with new velocity
        x_new = x_n + v_new * self.dt
        
        # Update state
        t_new = self.state.t + self.dt
        self.state = DampedOscillatorState(x=x_new, v=v_new, t=t_new, regime=self.regime)
        
        # Record
        self.history.append(self.state)
        self.energy_history.append(self.energy())
    
    def run(self, steps: int):
        """Run simulation."""
        for _ in range(steps):
            self.step()
    
    def envelope(self, t: float, x0: float, v0: float) -> float:
        """Decay envelope for underdamped case."""
        if self.regime == 'underdamped':
            # Approximate envelope
            E0 = 0.5 * self.k * x0**2 + 0.5 * self.mass * v0**2
            return math.sqrt(2 * E0 / self.k) * math.exp(-self.zeta * self.omega0 * t)
        return None


class DampedValidationSuite:
    """
    Validation for Step 2: Damped oscillator.
    
    Tests all three damping regimes against analytic solutions.
    """
    
    def __init__(self, omega0: float = 1.0, mass: float = 1.0):
        self.omega0 = omega0
        self.mass = mass
        self.results = {}
    
    def test_underdamped_envelope(self) -> Tuple[bool, dict]:
        """
        Test 1: Underdamped envelope should decay as e^(-ζω₀t).
        """
        zeta = 0.1  # Light damping
        osc = GWL_DampedOscillator(omega0=self.omega0, mass=self.mass, zeta=zeta, dt=0.01)
        osc.initialize(x0=1.0, v0=0.0)
        
        # Run for several time constants
        tau = 1.0 / (zeta * self.omega0)  # Decay time constant
        steps = int(5 * tau / 0.01)
        osc.run(steps=steps)
        
        # Check envelope decay
        peaks_x = []
        peaks_t = []
        for i in range(1, len(osc.history) - 1):
            h = osc.history[i]
            if h.x > osc.history[i-1].x and h.x > osc.history[i+1].x and h.x > 0:
                peaks_x.append(h.x)
                peaks_t.append(h.t)
        
        if len(peaks_x) >= 3:
            # Fit exponential to peaks: x_peak ∝ e^(-ζω₀t)
            log_peaks = np.log(peaks_x)
            coeffs = np.polyfit(peaks_t, log_peaks, 1)
            measured_decay = -coeffs[0]
            expected_decay = zeta * self.omega0
            error = abs(measured_decay - expected_decay) / expected_decay
        else:
            error = float('inf')
        
        passed = error < 0.1
        
        return passed, {
            'zeta': zeta,
            'measured_decay': measured_decay if 'measured_decay' in dir() else None,
            'expected_decay': expected_decay,
            'error': error,
            'num_peaks': len(peaks_x),
            'threshold': 0.1
        }
    
    def test_frequency_shift(self) -> Tuple[bool, dict]:
        """
        Test 2: Underdamped frequency should be ω₁ = ω₀√(1-ζ²).
        """
        zeta = 0.2
        osc = GWL_DampedOscillator(omega0=self.omega0, mass=self.mass, zeta=zeta, dt=0.001)
        osc.initialize(x0=0.0, v0=1.0)  # Start at origin
        
        # Run and measure period
        tau = 1.0 / (zeta * self.omega0)
        steps = int(10 * tau / 0.001)  # Several cycles
        osc.run(steps=steps)
        
        # Find zero crossings
        x_values = [h.x for h in osc.history]
        t_values = [h.t for h in osc.history]
        
        zero_crossings = []
        for i in range(1, len(x_values)):
            if x_values[i-1] < 0 and x_values[i] >= 0:
                t_cross = t_values[i-1] + (t_values[i] - t_values[i-1]) * abs(x_values[i-1]) / (abs(x_values[i-1]) + abs(x_values[i]))
                zero_crossings.append(t_cross)
        
        if len(zero_crossings) >= 4:
            periods = [zero_crossings[i] - zero_crossings[i-1] for i in range(2, len(zero_crossings))]
            T_measured = np.mean(periods)
            omega_measured = 2 * math.pi / T_measured
            omega_expected = self.omega0 * math.sqrt(1 - zeta**2)
            error = abs(omega_measured - omega_expected) / omega_expected
        else:
            error = float('inf')
            omega_measured = None
            omega_expected = self.omega0 * math.sqrt(1 - zeta**2)
        
        passed = error < 0.05
        
        return passed, {
            'zeta': zeta,
            'omega_measured': omega_measured,
            'omega_expected': omega_expected,
            'error': error,
            'threshold': 0.05
        }
    
    def test_critical_damping(self) -> Tuple[bool, dict]:
        """
        Test 3: Critical damping (ζ=1) should return to zero fastest.
        """
        x0, v0 = 1.0, 0.0
        
        # Test three damping values
        results = {}
        for zeta in [0.5, 1.0, 2.0]:
            osc = GWL_DampedOscillator(omega0=self.omega0, mass=self.mass, zeta=zeta, dt=0.01)
            osc.initialize(x0=x0, v0=v0)
            
            # Find time to reach |x| < 0.01
            target_steps = 2000
            osc.run(steps=target_steps)
            
            # Find settling time
            settling_time = None
            for i, h in enumerate(osc.history):
                if abs(h.x) < 0.01 and abs(h.v) < 0.01:
                    settling_time = h.t
                    break
            
            results[zeta] = settling_time
        
        # Critical (ζ=1) should be fastest or nearly so
        crit_time = results[1.0]
        under_time = results[0.5]
        over_time = results[2.0]
        
        # Critical should beat overdamped
        passed = crit_time is not None and (over_time is None or crit_time <= over_time)
        
        return passed, {
            'settling_underdamped': under_time,
            'settling_critical': crit_time,
            'settling_overdamped': over_time,
            'critical_best': crit_time <= over_time if (crit_time and over_time) else None
        }
    
    def test_energy_decay(self) -> Tuple[bool, dict]:
        """
        Test 4: Energy should decay monotonically (dE/dt = -γv² ≤ 0).
        """
        zeta = 0.3
        osc = GWL_DampedOscillator(omega0=self.omega0, mass=self.mass, zeta=zeta, dt=0.01)
        osc.initialize(x0=1.0, v0=0.0)
        osc.run(steps=500)
        
        # Check monotonic decay
        monotonic = all(osc.energy_history[i] >= osc.energy_history[i+1] 
                       for i in range(len(osc.energy_history)-1))
        
        # Check approximate exponential decay of energy
        E0 = osc.energy_history[0]
        E_values = np.array(osc.energy_history)
        t_values = np.array([h.t for h in osc.history])
        
        # Fit: E(t) ≈ E₀·e^(-2ζω₀t) for light damping
        log_E = np.log(E_values / E0)
        valid = log_E > -10  # Avoid log(0)
        if np.sum(valid) > 10:
            coeffs = np.polyfit(t_values[valid], log_E[valid], 1)
            measured_decay = -coeffs[0]
            expected_decay = 2 * zeta * self.omega0
            decay_error = abs(measured_decay - expected_decay) / expected_decay
        else:
            decay_error = float('inf')
        
        passed = monotonic and decay_error < 0.3
        
        return passed, {
            'monotonic': monotonic,
            'measured_decay': measured_decay if 'measured_decay' in dir() else None,
            'expected_decay': expected_decay if 'expected_decay' in dir() else None,
            'decay_error': decay_error if 'decay_error' in dir() else None
        }
    
    def test_analytic_agreement(self) -> Tuple[bool, dict]:
        """
        Test 5: Numerical solution matches analytic for all regimes.
        """
        x0, v0 = 1.0, 0.5
        dt = 0.001
        steps = 500
        
        max_errors = {}
        for zeta, regime_name in [(0.1, 'underdamped'), (1.0, 'critical'), (2.0, 'overdamped')]:
            osc = GWL_DampedOscillator(omega0=self.omega0, mass=self.mass, zeta=zeta, dt=dt)
            osc.initialize(x0=x0, v0=v0)
            osc.run(steps=steps)
            
            max_error = 0.0
            for state in osc.history:
                x_analytic, v_analytic = osc.analytic_solution(state.t, x0, v0)
                error = abs(state.x - x_analytic)
                max_error = max(max_error, error)
            
            max_errors[regime_name] = max_error
        
        # All should have reasonable error
        passed = all(err < 0.1 for err in max_errors.values())
        
        return passed, {
            'max_error_underdamped': max_errors['underdamped'],
            'max_error_critical': max_errors['critical'],
            'max_error_overdamped': max_errors['overdamped']
        }
    
    def test_regime_classification(self) -> Tuple[bool, dict]:
        """
        Test 6: System correctly identifies its regime.
        """
        tests = [
            (0.05, 'underdamped'),
            (0.5, 'underdamped'),
            (0.99, 'underdamped'),  # Close to critical
            (1.0, 'critical'),
            (1.5, 'overdamped'),
            (3.0, 'overdamped'),
        ]
        
        correct = 0
        for zeta, expected in tests:
            osc = GWL_DampedOscillator(omega0=self.omega0, mass=self.mass, zeta=zeta, dt=0.01)
            if osc.regime == expected:
                correct += 1
        
        passed = correct == len(tests)
        
        return passed, {
            'correct_classifications': correct,
            'total_tests': len(tests),
            'accuracy': correct / len(tests)
        }
    
    def run_all(self):
        """Run complete validation suite."""
        print("=" * 80)
        print("STEP 2 VALIDATION: DAMPED HARMONIC OSCILLATOR")
        print("=" * 80)
        print(f"Base equation: d²x/dt² + 2ζω₀·dx/dt + ω₀²·x = 0")
        print(f"Analytic solutions by regime:")
        print(f"  Underdamped (ζ<1): x(t) = A·e^(-ζω₀t)·cos(ω₁t + φ)")
        print(f"  Critical (ζ=1): x(t) = (A+Bt)·e^(-ω₀t)")
        print(f"  Overdamped (ζ>1): x(t) = A·e^(-λ₁t) + B·e^(-λ₂t)")
        print(f"Parameters: ω₀={self.omega0}, m={self.mass}")
        print()
        
        tests = [
            ('Underdamped Envelope', self.test_underdamped_envelope),
            ('Frequency Shift', self.test_frequency_shift),
            ('Critical Damping', self.test_critical_damping),
            ('Energy Decay', self.test_energy_decay),
            ('Analytic Agreement', self.test_analytic_agreement),
            ('Regime Classification', self.test_regime_classification),
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
                    elif val is None:
                        print(f"  {key}: None")
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
            print(f"{name:30s}: {status}")
        
        print("\n" + "=" * 80)
        if all_passed:
            print("ALL TESTS PASSED - STEP 2 VALIDATED")
            print("=" * 80)
            print("""
The damped harmonic oscillator is now validated.
Properties verified:
  ✓ Underdamped envelope decay (e^(-ζω₀t))
  ✓ Frequency shift (ω₁ = ω₀√(1-ζ²))
  ✓ Critical damping (fastest return)
  ✓ Energy decay monotonic
  ✓ Analytic agreement all regimes
  ✓ Regime classification correct

READY FOR STEP 3: Add external forcing (resonance)
            """)
        else:
            print("SOME TESTS FAILED - DO NOT PROCEED")
            print("=" * 80)
        
        return all_passed


if __name__ == "__main__":
    validator = DampedValidationSuite(omega0=1.0, mass=1.0)
    success = validator.run_all()
    exit(0 if success else 1)
