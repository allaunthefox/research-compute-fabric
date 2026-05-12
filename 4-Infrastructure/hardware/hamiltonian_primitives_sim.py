#!/usr/bin/env python3
"""
Braided Field Simulation with Hamiltonian Component Primitives

This script applies the 4 Hamiltonian components (photon, electron, phonon, interaction)
to the braided field system, exploring how each term affects the polaron-polariton state.
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
RECEIPT_PATH = ROOT / "4-Infrastructure" / "hardware" / "hamiltonian_primitives_sim_receipt.json"
PLOT_PATH = ROOT / "4-Infrastructure" / "hardware" / "hamiltonian_phase_energy.png"

@dataclass
class HamiltonianComponent:
    """One of the 4 Hamiltonian components."""
    name: str  # 'photon', 'electron', 'phonon', 'interaction'
    energy_coeff: float
    phase_coupling: float
    mass_renormalization: float

class HamiltonianPrimitives:
    """The 4 Hamiltonian components from the multi-body system."""

    def __init__(self):
        # Based on the Hamiltonian: H_total = H_photon + H_electron + H_phonon + H_interactions
        self.components = {
            'photon': HamiltonianComponent('photon', 1.0, 0.0, 0.0),
            'electron': HamiltonianComponent('electron', 0.5, np.pi/4, 0.1),
            'phonon': HamiltonianComponent('phonon', 0.3, np.pi/2, 0.5),
            'interaction': HamiltonianComponent('interaction', 0.2, np.pi, 1.0),
        }

    def get_component(self, name: str) -> HamiltonianComponent:
        return self.components[name]

    def all_components(self) -> List[HamiltonianComponent]:
        return list(self.components.values())

class BraidedFieldWithHamiltonian:
    """Braided field that accepts Hamiltonian component perturbations."""

    def __init__(self, num_particles: int = 4):
        self.particles = []
        self.braiding_history = []
        self.hamiltonian_perturbations = []
        self.magnetic_field = 0.0

        # Initialize polaron-polaritons
        for i in range(num_particles):
            angle = 2 * np.pi * i / num_particles
            self.particles.append({
                'photon_component': 1.0 + 0j,
                'electron_component': 1.0 + 0j,
                'phonon_component': 0.5 + 0j,
                'position': (np.cos(angle), np.sin(angle)),
                'statistics_parameter': np.pi/4,
                'effective_mass': 1.0
            })

    def apply_hamiltonian_component(self, component: HamiltonianComponent):
        """Apply a Hamiltonian component perturbation to the field."""
        self.hamiltonian_perturbations.append(component)

        # Apply component-specific effects
        for p in self.particles:
            # Phase coupling based on component
            p['statistics_parameter'] += component.phase_coupling * 0.1

            # Mass renormalization (especially for phonon)
            p['effective_mass'] += component.mass_renormalization * 0.1

            # Component-specific energy effects
            if component.name == 'photon':
                p['photon_component'] *= cmath.exp(1j * component.phase_coupling)
            elif component.name == 'electron':
                p['electron_component'] *= cmath.exp(1j * component.phase_coupling)
            elif component.name == 'phonon':
                p['phonon_component'] *= cmath.exp(1j * component.phase_coupling)
            elif component.name == 'interaction':
                # Interaction affects all components
                phase = component.phase_coupling
                p['photon_component'] *= cmath.exp(1j * phase)
                p['electron_component'] *= cmath.exp(1j * phase)
                p['phonon_component'] *= cmath.exp(1j * phase)

        # Record perturbation
        self.braiding_history.append({
            'type': 'hamiltonian',
            'component': component.name,
            'phase_shift': component.phase_coupling,
            'energy': component.energy_coeff
        })

    def apply_braiding(self, i: int, j: int, phase_shift: float):
        """Apply a standard braiding operation."""
        if i >= len(self.particles) or j >= len(self.particles):
            raise IndexError("Particle index out of range")

        # Swap particles
        self.particles[i], self.particles[j] = self.particles[j], self.particles[i]

        # Apply phase shift
        for p in [self.particles[i], self.particles[j]]:
            p['statistics_parameter'] += phase_shift
            p['photon_component'] *= cmath.exp(1j * phase_shift)
            p['electron_component'] *= cmath.exp(1j * phase_shift)
            p['phonon_component'] *= cmath.exp(1j * phase_shift)

        # Record braiding
        self.braiding_history.append({
            'type': 'braid',
            'i': i,
            'j': j,
            'phase_shift': phase_shift
        })

    def total_wavefunction(self) -> complex:
        """Compute total wavefunction from all particles."""
        psi = 0j
        for p in self.particles:
            psi += (p['photon_component'] +
                   p['electron_component'] +
                   p['phonon_component'])
        return psi

    def total_energy(self) -> float:
        """Compute total energy from Hamiltonian components."""
        total = 0.0
        for pert in self.hamiltonian_perturbations:
            total += pert.energy_coeff
        return total

    def effective_mass(self) -> float:
        """Compute average effective mass."""
        return np.mean([p['effective_mass'] for p in self.particles])

    def topological_invariant(self) -> float:
        """Compute topological invariant from braiding history."""
        total = 0.0
        for op in self.braiding_history:
            if op['type'] == 'braid':
                total += op['phase_shift']
            elif op['type'] == 'hamiltonian':
                total += op['phase_shift'] * 0.5  # Hamiltonian perturbations contribute half
        return total

    def is_protection_candidate(self) -> bool:
        """Local candidate gate; not a proof of topological protection."""
        return self.topological_invariant() != 0 and self.magnetic_field > 0

def simulate_hamiltonian_components():
    """Simulate applying each Hamiltonian component individually."""
    print("=== Braided Field with Hamiltonian Component Primitives ===\n")

    primitives = HamiltonianPrimitives()
    field = BraidedFieldWithHamiltonian(num_particles=4)

    print(f"Initial state:")
    print(f"  Particles: {len(field.particles)}")
    print(f"  Wavefunction: {field.total_wavefunction():.4f}")
    print(f"  Energy: {field.total_energy():.4f}")
    print(f"  Effective mass: {field.effective_mass():.4f}")
    print(f"  Topological invariant: {field.topological_invariant():.4f}\n")

    # Apply each Hamiltonian component
    print("Applying Hamiltonian components individually:")
    component_rows = []

    for component in primitives.all_components():
        field.apply_hamiltonian_component(component)
        row = {
            "component": component.name,
            "energy_coeff": component.energy_coeff,
            "phase_coupling": component.phase_coupling,
            "mass_renormalization": component.mass_renormalization,
            "wavefunction": f"{field.total_wavefunction():.4f}",
            "total_energy": field.total_energy(),
            "effective_mass": field.effective_mass(),
            "invariant": field.topological_invariant(),
        }
        component_rows.append(row)
        print(f"  {component.name.capitalize()} component:")
        print(f"    Energy coeff: {component.energy_coeff:.4f}")
        print(f"    Phase coupling: {component.phase_coupling:.4f} rad")
        print(f"    Mass renorm: {component.mass_renormalization:.4f}")
        print(f"    Wavefunction: {field.total_wavefunction():.4f}")
        print(f"    Total energy: {field.total_energy():.4f}")
        print(f"    Effective mass: {field.effective_mass():.4f}")
        print(f"    Invariant: {field.topological_invariant():.4f}\n")

    # Apply magnetic field
    field.magnetic_field = 1.0
    print(f"Applied magnetic field: {field.magnetic_field}")
    print(f"Protection candidate: {field.is_protection_candidate()}\n")

    print(f"Final topological invariant: {field.topological_invariant():.4f}")
    print(f"Total operations: {len(field.braiding_history)}")
    return {
        "components": component_rows,
        "magnetic_field": field.magnetic_field,
        "protection_candidate": field.is_protection_candidate(),
        "final_topological_invariant": field.topological_invariant(),
        "total_operations": len(field.braiding_history),
    }

def simulate_hamiltonian_braiding_sequence():
    """Simulate alternating Hamiltonian components and braiding operations."""
    print("\n=== Hamiltonian-Braiding Sequence Simulation ===\n")

    primitives = HamiltonianPrimitives()
    field = BraidedFieldWithHamiltonian(num_particles=4)

    sequence = [
        ('hamiltonian', 'photon'),
        ('braid', (0, 1, np.pi/4)),
        ('hamiltonian', 'electron'),
        ('braid', (1, 2, np.pi/3)),
        ('hamiltonian', 'phonon'),
        ('braid', (2, 3, np.pi/5)),
        ('hamiltonian', 'interaction'),
        ('braid', (0, 3, np.pi/2)),
    ]

    print(f"Initial wavefunction: {field.total_wavefunction():.4f}")
    print(f"Initial invariant: {field.topological_invariant():.4f}\n")
    rows = []

    for op_type, data in sequence:
        if op_type == 'hamiltonian':
            component = primitives.get_component(data)
            field.apply_hamiltonian_component(component)
            rows.append({
                "type": "hamiltonian",
                "component": data,
                "wavefunction": f"{field.total_wavefunction():.4f}",
                "energy": field.total_energy(),
                "invariant": field.topological_invariant(),
            })
            print(f"Hamiltonian component {data}:")
            print(f"  Wavefunction: {field.total_wavefunction():.4f}")
            print(f"  Energy: {field.total_energy():.4f}")
            print(f"  Invariant: {field.topological_invariant():.4f}")
        elif op_type == 'braid':
            i, j, phase = data
            field.apply_braiding(i, j, phase)
            rows.append({
                "type": "braid",
                "i": i,
                "j": j,
                "phase": phase,
                "wavefunction": f"{field.total_wavefunction():.4f}",
                "invariant": field.topological_invariant(),
            })
            print(f"Braid ({i},{j}) with phase {phase:.4f}:")
            print(f"  Wavefunction: {field.total_wavefunction():.4f}")
            print(f"  Invariant: {field.topological_invariant():.4f}")
        print()

    field.magnetic_field = 1.0
    print(f"Applied magnetic field: {field.magnetic_field}")
    print(f"Protection candidate: {field.is_protection_candidate()}")
    print(f"Final invariant: {field.topological_invariant():.4f}")
    return {
        "sequence": rows,
        "magnetic_field": field.magnetic_field,
        "protection_candidate": field.is_protection_candidate(),
        "final_topological_invariant": field.topological_invariant(),
    }

def plot_hamiltonian_phase_space():
    """Visualize Hamiltonian components in phase-energy space."""
    print("\n=== Hamiltonian Component Phase-Energy Space ===\n")

    primitives = HamiltonianPrimitives()
    components = primitives.all_components()

    # Extract data
    names = [c.name for c in components]
    phases = [c.phase_coupling for c in components]
    energies = [c.energy_coeff for c in components]
    masses = [c.mass_renormalization for c in components]

    # Create scatter plot
    fig, ax = plt.subplots(figsize=(10, 8))

    # Plot each component
    for name, phase, energy, mass in zip(names, phases, energies, masses):
        ax.scatter(phase, energy, s=mass*200, alpha=0.6, label=f'{name} (mass={mass})')
        ax.annotate(name, (phase, energy), xytext=(10, 10),
                   textcoords='offset points', fontsize=10)

    ax.set_xlabel('Phase Coupling (radians)')
    ax.set_ylabel('Energy Coefficient')
    ax.set_title('Hamiltonian Components in Phase-Energy Space')
    ax.grid(True, alpha=0.3)
    ax.legend()

    plt.tight_layout()
    plt.savefig(PLOT_PATH, dpi=150)
    print(f"Hamiltonian phase-energy plot saved to {PLOT_PATH}")
    return {
        "plot_path": str(PLOT_PATH),
        "component_count": len(components),
    }

def simulate_hamiltonian_encoding():
    """Simulate encoding information using Hamiltonian components."""
    print("\n=== Information Encoding with Hamiltonian Components ===\n")

    primitives = HamiltonianPrimitives()
    field = BraidedFieldWithHamiltonian(num_particles=4)

    # Encode information using component sequence
    sequence = ['photon', 'electron', 'phonon', 'interaction']

    print(f"Encoding sequence: {' -> '.join(sequence)}")
    print(f"Initial wavefunction: {field.total_wavefunction():.4f}")
    print(f"Initial invariant: {field.topological_invariant():.4f}\n")
    rows = []

    for component_name in sequence:
        component = primitives.get_component(component_name)
        field.apply_hamiltonian_component(component)
        rows.append({
            "component": component_name,
            "wavefunction": f"{field.total_wavefunction():.4f}",
            "energy": field.total_energy(),
            "invariant": field.topological_invariant(),
        })
        print(f"Encoded {component_name}:")
        print(f"  Wavefunction: {field.total_wavefunction():.4f}")
        print(f"  Energy: {field.total_energy():.4f}")
        print(f"  Invariant: {field.topological_invariant():.4f}")

    # Apply magnetic field to lock topology
    field.magnetic_field = 1.0
    print(f"\nApplied magnetic field: {field.magnetic_field}")
    print(f"Protection candidate: {field.is_protection_candidate()}")

    # The invariant encodes the sequence information
    final_invariant = field.topological_invariant()
    expected_invariant = sum(c.phase_coupling * 0.5 for c in primitives.all_components())
    print(f"\nFinal topological invariant: {final_invariant:.4f}")
    print(f"Expected invariant (sum of phase contributions): {expected_invariant:.4f}")

    print("\nThe Hamiltonian component sequence is represented in the accumulated invariant.")
    print("This demonstrates a candidate reduced-equation control surface for")
    print("virtual polaron-polariton braid-field simulations.")
    return {
        "sequence": sequence,
        "rows": rows,
        "magnetic_field": field.magnetic_field,
        "protection_candidate": field.is_protection_candidate(),
        "final_topological_invariant": final_invariant,
        "expected_invariant": expected_invariant,
        "invariant_matches_expected": abs(final_invariant - expected_invariant) < 1e-9,
    }

if __name__ == "__main__":
    component_summary = simulate_hamiltonian_components()
    sequence_summary = simulate_hamiltonian_braiding_sequence()
    plot_summary = plot_hamiltonian_phase_space()
    encoding_summary = simulate_hamiltonian_encoding()

    receipt = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "lawful": True,
        "mode": "virtual_only",
        "source_note": "No hardware programming, RF emission, JTAG, serial flashing, board access, or material claim. Python reduced-equation toy simulation only.",
        "reduced_equation_set": [
            "H_photon",
            "H_electron",
            "H_phonon",
            "H_interactions",
        ],
        "component_summary": component_summary,
        "sequence_summary": sequence_summary,
        "plot_summary": plot_summary,
        "encoding_summary": encoding_summary,
        "claim_boundary": "This simulation records a candidate reduced-Hamiltonian braid-field control model. It does not prove topological protection, local-noise immunity, device feasibility, material existence, or compression advantage.",
    }
    encoded = json.dumps(receipt, indent=2, sort_keys=True).encode("utf-8")
    receipt["receipt_hash_preimage_sha256"] = hashlib.sha256(encoded).hexdigest()
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("\n=== Simulation Complete ===")
    print("The 4 Hamiltonian components (photon, electron, phonon, interaction)")
    print("were applied as a virtual reduced-equation control surface.")
    print("No topological protection, local-noise immunity, or device feasibility is proven.")
    print(f"Receipt written to {RECEIPT_PATH}")
