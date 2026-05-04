#!/usr/bin/env python3
"""
gwl_deterministic_em_demo.py

Demonstration of deterministic EM-like field propagation in GWL/TSM.

This validates the deterministic backbone before stochastic extensions.
"""

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class EMSeed:
    """μ-seed with electromagnetic field components."""
    x: float          # Position
    E: float          # Electric-like field
    B: float          # Magnetic-like field
    tau: int          # Temporal phase (0-15)
    pi: int           # Rotation/polarization (0-15)
    chi: int          # Chirality (0=D, 1=L)
    omega: float      # Frequency mode


class DeterministicEMField:
    """
    Deterministic EM-like field on TSM topology.
    
    Update law (no randomness):
        E_i(t+1) = E_i(t) + α * Σ_j w_ij * (B_j - B_i)
        B_i(t+1) = B_i(t) - β * Σ_j w_ij * (E_j - E_i)
        tau_i(t+1) = (tau_i + omega) % 16
    """
    
    def __init__(self, n_seeds: int = 100, alpha: float = 0.1, beta: float = 0.1):
        self.n = n_seeds
        self.alpha = alpha
        self.beta = beta
        self.seeds: List[EMSeed] = []
        self.history_E: List[List[float]] = []
        self.history_B: List[List[float]] = []
        self.history_energy: List[float] = []
        
        # Initialize linear topology (1D tape)
        for i in range(n_seeds):
            self.seeds.append(EMSeed(
                x=float(i),
                E=0.0,
                B=0.0,
                tau=0,
                pi=0,
                chi=0,
                omega=0.0
            ))
    
    def initialize_pulse(self, center: int, width: int, amplitude: float = 1.0, 
                         freq: float = 1.0):
        """Initialize a Gaussian pulse with given frequency."""
        for i in range(self.n):
            dist = abs(i - center)
            if dist < width:
                # Gaussian envelope
                envelope = amplitude * np.exp(-(dist**2) / (2 * (width/3)**2))
                self.seeds[i].E = envelope * np.cos(2 * np.pi * freq * i / self.n)
                self.seeds[i].B = envelope * np.sin(2 * np.pi * freq * i / self.n)
                self.seeds[i].omega = freq
    
    def coupling_weight(self, i: int, j: int) -> float:
        """
        Deterministic coupling weight.
        
        For 1D linear topology: only nearest neighbors couple.
        """
        if abs(i - j) == 1:  # Nearest neighbor
            return 1.0
        elif abs(i - j) == 2:  # Next-nearest (weaker)
            return 0.3
        return 0.0
    
    def step(self):
        """One deterministic evolution step."""
        new_E = np.zeros(self.n)
        new_B = np.zeros(self.n)
        new_tau = np.zeros(self.n, dtype=int)
        
        for i in range(self.n):
            # Coupling sum
            coupling_E = 0.0
            coupling_B = 0.0
            
            for j in range(max(0, i-2), min(self.n, i+3)):
                if i == j:
                    continue
                w = self.coupling_weight(i, j)
                coupling_E += w * (self.seeds[j].B - self.seeds[i].B)
                coupling_B += w * (self.seeds[j].E - self.seeds[i].E)
            
            # Deterministic update (NO RANDOMNESS)
            new_E[i] = self.seeds[i].E + self.alpha * coupling_E
            new_B[i] = self.seeds[i].B - self.beta * coupling_B
            
            # Temporal phase evolution
            new_tau[i] = (self.seeds[i].tau + int(self.seeds[i].omega * 16)) % 16
        
        # Apply updates
        for i in range(self.n):
            self.seeds[i].E = new_E[i]
            self.seeds[i].B = new_B[i]
            self.seeds[i].tau = new_tau[i]
        
        # Record history
        self.history_E.append([s.E for s in self.seeds])
        self.history_B.append([s.B for s in self.seeds])
        
        # Energy
        energy = sum(s.E**2 + s.B**2 for s in self.seeds)
        self.history_energy.append(energy)
    
    def run(self, steps: int = 200):
        """Run deterministic evolution."""
        for _ in range(steps):
            self.step()
    
    def test_1_stable_propagation(self) -> Tuple[bool, str]:
        """
        Test 1: Stable wave propagation.
        
        Energy should remain bounded, pulse should propagate.
        """
        self.initialize_pulse(center=25, width=10, amplitude=1.0, freq=2.0)
        initial_energy = sum(s.E**2 + s.B**2 for s in self.seeds)
        
        self.run(steps=100)
        
        final_energy = sum(s.E**2 + s.B**2 for s in self.seeds)
        energy_ratio = final_energy / initial_energy if initial_energy > 0 else 0
        
        # Check if pulse moved from initial position
        max_E_initial = max(abs(self.history_E[0][i]) for i in range(20, 30))
        max_E_final = max(abs(self.history_E[-1][i]) for i in range(40, 80))
        
        passed = (0.5 < energy_ratio < 2.0) and (max_E_final > 0.1 * max_E_initial)
        
        msg = f"Energy ratio: {energy_ratio:.3f}, Pulse propagated: {max_E_final > 0.1 * max_E_initial}"
        return passed, msg
    
    def test_2_frequency_separability(self) -> Tuple[bool, str]:
        """
        Test 2: Frequency separability.
        
        Two different frequencies should remain distinguishable.
        """
        # Initialize two pulses at different frequencies
        self.__init__(self.n, self.alpha, self.beta)  # Reset
        
        # Low frequency pulse
        for i in range(20, 40):
            dist = abs(i - 30)
            self.seeds[i].E = np.exp(-dist**2/20) * np.cos(2 * np.pi * 1.0 * i / 20)
            self.seeds[i].omega = 1.0
        
        # High frequency pulse
        for i in range(60, 80):
            dist = abs(i - 70)
            self.seeds[i].E = np.exp(-dist**2/20) * np.cos(2 * np.pi * 4.0 * i / 10)
            self.seeds[i].omega = 4.0
        
        self.run(steps=50)
        
        # FFT analysis
        signal_low = [self.history_E[t][30] for t in range(len(self.history_E))]
        signal_high = [self.history_E[t][70] for t in range(len(self.history_E))]
        
        if len(signal_low) > 10:
            fft_low = np.abs(np.fft.fft(signal_low))
            fft_high = np.abs(np.fft.fft(signal_high))
            
            peak_low = np.argmax(fft_low[:len(fft_low)//2])
            peak_high = np.argmax(fft_high[:len(fft_high)//2])
            
            separable = abs(peak_high - peak_low) > 2
            msg = f"Low freq peak: {peak_low}, High freq peak: {peak_high}"
            return separable, msg
        
        return False, "Insufficient data"
    
    def test_3_determinism(self) -> Tuple[bool, str]:
        """
        Test 3: Determinism.
        
        Same initial conditions → same evolution.
        """
        # Run 1
        self.__init__(self.n, self.alpha, self.beta)
        self.initialize_pulse(center=30, width=8, amplitude=1.0, freq=2.0)
        self.run(steps=50)
        final_E_1 = [s.E for s in self.seeds]
        
        # Run 2 (identical)
        self.__init__(self.n, self.alpha, self.beta)
        self.initialize_pulse(center=30, width=8, amplitude=1.0, freq=2.0)
        self.run(steps=50)
        final_E_2 = [s.E for s in self.seeds]
        
        # Compare
        diff = max(abs(a - b) for a, b in zip(final_E_1, final_E_2))
        passed = diff < 1e-10
        
        return passed, f"Max difference between runs: {diff:.2e}"
    
    def test_4_energy_conservation(self) -> Tuple[bool, str]:
        """
        Test 4: Energy conservation (bounded).
        
        Total field energy should not explode or vanish.
        """
        self.__init__(self.n, self.alpha, self.beta)
        self.initialize_pulse(center=50, width=15, amplitude=1.0, freq=1.5)
        
        initial_energy = self.history_energy[0] if self.history_energy else 1.0
        
        self.run(steps=100)
        
        energy_values = self.history_energy
        max_energy = max(energy_values)
        min_energy = min(energy_values)
        
        # Energy should stay within reasonable bounds
        ratio = max_energy / min_energy if min_energy > 0 else float('inf')
        passed = ratio < 10.0  # Less than 10x variation
        
        return passed, f"Energy variation ratio: {ratio:.3f}"
    
    def plot_evolution(self, title: str = "EM Field Evolution"):
        """Plot field evolution over time."""
        fig, axes = plt.subplots(3, 1, figsize=(12, 10))
        
        # Plot E field heatmap
        E_array = np.array(self.history_E)
        im1 = axes[0].imshow(E_array.T, aspect='auto', cmap='RdBu', 
                             extent=[0, len(self.history_E), 0, self.n])
        axes[0].set_ylabel('Position')
        axes[0].set_title(f'{title} - E Field')
        plt.colorbar(im1, ax=axes[0])
        
        # Plot B field heatmap
        B_array = np.array(self.history_B)
        im2 = axes[1].imshow(B_array.T, aspect='auto', cmap='RdBu',
                             extent=[0, len(self.history_B), 0, self.n])
        axes[1].set_ylabel('Position')
        axes[1].set_title('B Field')
        plt.colorbar(im2, ax=axes[1])
        
        # Plot energy
        axes[2].plot(self.history_energy)
        axes[2].set_xlabel('Time Step')
        axes[2].set_ylabel('Total Energy')
        axes[2].set_title('Energy Conservation')
        axes[2].grid(True)
        
        plt.tight_layout()
        return fig


def run_all_tests():
    """Run all four deterministic EM tests."""
    
    print("=" * 70)
    print("GWL DETERMINISTIC EM FIELD TESTS")
    print("=" * 70)
    
    field = DeterministicEMField(n_seeds=100, alpha=0.15, beta=0.15)
    
    # Test 1: Stable propagation
    print("\n[Test 1] Stable Wave Propagation")
    print("-" * 50)
    passed, msg = field.test_1_stable_propagation()
    status = "PASS" if passed else "FAIL"
    print(f"Status: {status}")
    print(f"Details: {msg}")
    
    # Test 2: Frequency separability
    print("\n[Test 2] Frequency Separability")
    print("-" * 50)
    passed, msg = field.test_2_frequency_separability()
    status = "PASS" if passed else "FAIL"
    print(f"Status: {status}")
    print(f"Details: {msg}")
    
    # Test 3: Determinism
    print("\n[Test 3] Determinism")
    print("-" * 50)
    passed, msg = field.test_3_determinism()
    status = "PASS" if passed else "FAIL"
    print(f"Status: {status}")
    print(f"Details: {msg}")
    
    # Test 4: Energy conservation
    print("\n[Test 4] Energy Conservation")
    print("-" * 50)
    passed, msg = field.test_4_energy_conservation()
    status = "PASS" if passed else "FAIL"
    print(f"Status: {status}")
    print(f"Details: {msg}")
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("""
These tests validate the deterministic backbone of GWL/TSM.

If all tests pass:
  - The system supports deterministic field propagation
  - Stochastic extensions can be safely added as perturbations
  - The EM spectrum is expressible

If any test fails:
  - The local update law needs refinement
  - Conservation constraints must be enforced
  - Do NOT add stochasticity to mask deterministic failures
    """)
    
    # Generate visualization
    field.__init__(n_seeds=100, alpha=0.15, beta=0.15)
    field.initialize_pulse(center=30, width=10, amplitude=1.0, freq=2.0)
    field.run(steps=150)
    
    try:
        fig = field.plot_evolution()
        plt.savefig('gwl_deterministic_em_evolution.png', dpi=150)
        print("\nVisualization saved to: gwl_deterministic_em_evolution.png")
    except Exception as e:
        print(f"\nPlotting skipped: {e}")


if __name__ == "__main__":
    run_all_tests()
