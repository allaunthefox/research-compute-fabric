#!/usr/bin/env python3
"""
Braided Field Simulation: Polaron-Polariton Topological Quantum Mechanics

This script simulates the braided field concept combining:
- Polaron: charge dragging physical distortion
- Polariton: light coupled with matter
- Anyon braiding in 2D with complex phase shifts
"""

import numpy as np
import cmath
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
RECEIPT_PATH = ROOT / "4-Infrastructure" / "hardware" / "braided_field_sim_receipt.json"
PLOT_PATH = ROOT / "4-Infrastructure" / "hardware" / "braiding_phase_space.png"

@dataclass
class Quasiparticle:
    """A quasiparticle in 2D space with position and phase."""
    position: Tuple[float, float]
    phase: float
    particle_type: int  # 0 = photon-like, 1 = electron-like, 2 = phonon-like

@dataclass
class Braiding:
    """A braiding operation that swaps two quasiparticles."""
    i: int  # index of first particle
    j: int  # index of second particle
    phase_shift: float  # complex phase shift e^(iθ)

class Hamiltonian:
    """Multi-body Hamiltonian for polaron-polariton system."""

    def __init__(self):
        self.photon_energy_coeff = 1.0
        self.electron_energy_coeff = 0.5
        self.phonon_energy_coeff = 0.3
        self.interaction_coeff = 0.2

    def photon_energy(self, psi: complex) -> float:
        return self.photon_energy_coeff * abs(psi)**2

    def electron_energy(self, psi: complex) -> float:
        return self.electron_energy_coeff * abs(psi)**2

    def phonon_energy(self, psi: complex) -> float:
        return self.phonon_energy_coeff * abs(psi)**2

    def interaction_energy(self, psi: complex) -> float:
        return self.interaction_coeff * abs(psi)**4

    def total_energy(self, psi: complex) -> float:
        return (self.photon_energy(psi) +
                self.electron_energy(psi) +
                self.phonon_energy(psi) +
                self.interaction_energy(psi))

class BraidedField:
    """A braided field state containing multiple quasiparticles."""

    def __init__(self, particles: List[Quasiparticle], hamiltonian: Hamiltonian):
        self.particles = particles
        self.braiding_history: List[Braiding] = []
        self.hamiltonian = hamiltonian
        self.magnetic_field = 0.0

    def apply_braiding(self, i: int, j: int, phase_shift: float):
        """Apply a braiding operation to swap particles i and j."""
        if i >= len(self.particles) or j >= len(self.particles):
            raise IndexError("Particle index out of range")

        # Swap particles and apply phase shift
        self.particles[i], self.particles[j] = self.particles[j], self.particles[i]

        # Apply phase shift to both particles
        self.particles[i].phase += phase_shift
        self.particles[j].phase += phase_shift

        # Record the braiding operation
        self.braiding_history.append(Braiding(i, j, phase_shift))

    def topological_invariant(self) -> float:
        """Compute the topological invariant from braiding history."""
        return sum(b.phase_shift for b in self.braiding_history)

    def total_wavefunction(self) -> complex:
        """Compute the total wavefunction of the field."""
        psi = 0j
        for p in self.particles:
            psi += cmath.exp(1j * p.phase)
        return psi

    def total_energy(self) -> float:
        """Compute the total energy of the field."""
        psi = self.total_wavefunction()
        return self.hamiltonian.total_energy(psi)

    def is_protection_candidate(self) -> bool:
        """Check the local candidate gate; this is not a proof of protection."""
        invariant = self.topological_invariant()
        return invariant != 0 and self.magnetic_field > 0

class PolaronPolariton:
    """A topological polaron-polariton quasiparticle."""

    def __init__(self, position: Tuple[float, float], statistics_param: float):
        self.photon_component = 1.0 + 0j
        self.electron_component = 1.0 + 0j
        self.phonon_component = 0.5 + 0j
        self.position = position
        self.statistics_parameter = statistics_param  # θ in [0, 2π)

    def wavefunction(self) -> complex:
        """Combined wavefunction for polaron-polariton."""
        return (self.photon_component +
                self.electron_component +
                self.phonon_component)

    def effective_mass(self) -> float:
        """Effective mass renormalized by phonon coupling."""
        return 1.0 + abs(self.phonon_component) * 0.5

    def braid(self, other: 'PolaronPolariton') -> Tuple['PolaronPolariton', 'PolaronPolariton']:
        """Braid two polaron-polaritons with phase shift."""
        phase = cmath.exp(1j * self.statistics_parameter)

        pp1 = PolaronPolariton(self.position, self.statistics_parameter)
        pp1.photon_component = self.photon_component * phase
        pp1.electron_component = self.electron_component * phase
        pp1.phonon_component = self.phonon_component * phase

        pp2 = PolaronPolariton(other.position, other.statistics_parameter)
        pp2.photon_component = other.photon_component * phase
        pp2.electron_component = other.electron_component * phase
        pp2.phonon_component = other.phonon_component * phase

        return pp1, pp2

def simulate_braiding_sequence():
    """Simulate a sequence of braiding operations."""
    print("=== Braided Field Simulation ===\n")

    # Create quasiparticles
    particles = [
        Quasiparticle((0.0, 0.0), 0.0, 0),  # photon-like at origin
        Quasiparticle((1.0, 0.0), 0.0, 1),  # electron-like at (1,0)
        Quasiparticle((0.5, 1.0), 0.0, 2),  # phonon-like at (0.5,1)
    ]

    hamiltonian = Hamiltonian()
    field = BraidedField(particles, hamiltonian)

    print(f"Initial state: {len(particles)} quasiparticles")
    print(f"Initial wavefunction: {field.total_wavefunction():.4f}")
    print(f"Initial energy: {field.total_energy():.4f}")
    print(f"Topological invariant: {field.topological_invariant():.4f}\n")

    # Apply braiding operations
    print("Applying braiding operations:")

    # Braid 0 and 1 with phase shift π/2
    field.apply_braiding(0, 1, np.pi/2)
    print(f"  Braid (0,1) with phase π/2")
    print(f"  Wavefunction: {field.total_wavefunction():.4f}")
    print(f"  Energy: {field.total_energy():.4f}")
    print(f"  Invariant: {field.topological_invariant():.4f}\n")

    # Braid 1 and 2 with phase shift π/3
    field.apply_braiding(1, 2, np.pi/3)
    print(f"  Braid (1,2) with phase π/3")
    print(f"  Wavefunction: {field.total_wavefunction():.4f}")
    print(f"  Energy: {field.total_energy():.4f}")
    print(f"  Invariant: {field.topological_invariant():.4f}\n")

    # Braid 0 and 2 with phase shift π/4
    field.apply_braiding(0, 2, np.pi/4)
    print(f"  Braid (0,2) with phase π/4")
    print(f"  Wavefunction: {field.total_wavefunction():.4f}")
    print(f"  Energy: {field.total_energy():.4f}")
    print(f"  Invariant: {field.topological_invariant():.4f}\n")

    # Apply magnetic field to enable topological protection
    field.magnetic_field = 1.0
    print(f"Applied magnetic field: {field.magnetic_field}")
    print(f"Protection candidate: {field.is_protection_candidate()}\n")

    print(f"Final topological invariant: {field.topological_invariant():.4f}")
    print(f"Total braiding operations: {len(field.braiding_history)}")
    return {
        "initial_wavefunction": "3.0000+0.0000j",
        "final_wavefunction": f"{field.total_wavefunction():.4f}",
        "final_energy": field.total_energy(),
        "topological_invariant": field.topological_invariant(),
        "braiding_operations": len(field.braiding_history),
        "magnetic_field": field.magnetic_field,
        "protection_candidate": field.is_protection_candidate(),
    }

def simulate_polaron_polariton_braiding():
    """Simulate braiding of polaron-polaritons."""
    print("\n=== Polaron-Polariton Braiding Simulation ===\n")

    # Create two polaron-polaritons
    pp1 = PolaronPolariton((0.0, 0.0), np.pi/4)  # anyon with statistics parameter π/4
    pp2 = PolaronPolariton((1.0, 0.0), np.pi/4)

    print(f"Initial polaron-polaritons:")
    print(f"  PP1 wavefunction: {pp1.wavefunction():.4f}")
    print(f"  PP1 effective mass: {pp1.effective_mass():.4f}")
    print(f"  PP2 wavefunction: {pp2.wavefunction():.4f}")
    print(f"  PP2 effective mass: {pp2.effective_mass():.4f}\n")

    # Braid them
    print("Braiding the two polaron-polaritons...")
    pp1_braided, pp2_braided = pp1.braid(pp2)

    print(f"After braiding:")
    print(f"  PP1 wavefunction: {pp1_braided.wavefunction():.4f}")
    print(f"  PP1 effective mass: {pp1_braided.effective_mass():.4f}")
    print(f"  PP2 wavefunction: {pp2_braided.wavefunction():.4f}")
    print(f"  PP2 effective mass: {pp2_braided.effective_mass():.4f}\n")

    # Compute the phase shift
    phase_shift = cmath.exp(1j * pp1.statistics_parameter)
    print(f"Braiding phase shift: {phase_shift:.4f}")
    print(f"Phase shift magnitude: {abs(phase_shift):.4f}")
    print(f"Phase shift angle: {cmath.phase(phase_shift):.4f} rad")
    return {
        "initial_wavefunction": f"{pp1.wavefunction():.4f}",
        "braided_wavefunction": f"{pp1_braided.wavefunction():.4f}",
        "effective_mass": pp1_braided.effective_mass(),
        "phase_shift": f"{phase_shift:.4f}",
        "phase_shift_magnitude": abs(phase_shift),
        "phase_shift_angle_rad": cmath.phase(phase_shift),
    }

def plot_braiding_phase_space():
    """Visualize the braiding phase space."""
    print("\n=== Braiding Phase Space Visualization ===\n")

    # Generate phase shifts for different statistics parameters
    theta_values = np.linspace(0, 2*np.pi, 100)
    phase_shifts = [cmath.exp(1j * theta) for theta in theta_values]

    # Extract real and imaginary parts
    real_parts = [z.real for z in phase_shifts]
    imag_parts = [z.imag for z in phase_shifts]

    # Create plot
    plt.figure(figsize=(8, 8))
    plt.plot(real_parts, imag_parts, 'b-', linewidth=2, label='Phase shift unit circle')
    plt.axhline(y=0, color='k', linestyle='-', alpha=0.3)
    plt.axvline(x=0, color='k', linestyle='-', alpha=0.3)
    plt.xlabel('Re(e^(iθ))')
    plt.ylabel('Im(e^(iθ))')
    plt.title('Braiding Phase Shifts in Complex Plane')
    plt.grid(True, alpha=0.3)
    plt.axis('equal')
    plt.legend()

    # Mark special cases
    special_cases = [
        (0, 'Boson (θ=0)'),
        (np.pi, 'Fermion (θ=π)'),
        (np.pi/2, 'Semion (θ=π/2)'),
        (np.pi/4, 'θ=π/4'),
    ]

    for theta, label in special_cases:
        z = cmath.exp(1j * theta)
        plt.plot(z.real, z.imag, 'ro', markersize=8)
        plt.annotate(label, (z.real, z.imag), xytext=(10, 10),
                    textcoords='offset points', fontsize=9)

    plt.tight_layout()
    plt.savefig(PLOT_PATH, dpi=150)
    print(f"Phase space plot saved to {PLOT_PATH}")
    return {
        "plot_path": str(PLOT_PATH),
        "phase_samples": len(theta_values),
    }

if __name__ == "__main__":
    sequence_summary = simulate_braiding_sequence()
    polaron_polariton_summary = simulate_polaron_polariton_braiding()
    plot_summary = plot_braiding_phase_space()

    receipt = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "lawful": True,
        "mode": "virtual_only",
        "source_note": "No hardware programming, RF emission, JTAG, serial flashing, board access, or material claim. Python toy simulation only.",
        "sequence_summary": sequence_summary,
        "polaron_polariton_summary": polaron_polariton_summary,
        "plot_summary": plot_summary,
        "claim_boundary": "This simulation records a candidate braid-field control model. It does not prove topological protection, local-noise immunity, device feasibility, material existence, or compression advantage.",
    }
    encoded = json.dumps(receipt, indent=2, sort_keys=True).encode("utf-8")
    receipt["receipt_hash_preimage_sha256"] = hashlib.sha256(encoded).hexdigest()
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("\n=== Simulation Complete ===")
    print("The braided field combines light, charge, and vibration")
    print("into a virtual candidate braid-field control model.")
    print("No topological protection, local-noise immunity, or device feasibility is proven.")
    print(f"Receipt written to {RECEIPT_PATH}")
