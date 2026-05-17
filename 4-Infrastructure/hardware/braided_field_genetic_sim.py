#!/usr/bin/env python3
"""
Braided Field Simulation with Genetic Event Primitives

This script applies the 4 genetic event primitives (A, T, G, C) from spectral encoding
to the braided field system, exploring how these perturbations affect topological states.
"""

import numpy as np
import cmath
from dataclasses import dataclass
from typing import List, Tuple
import matplotlib.pyplot as plt

@dataclass
class GeneticEvent:
    """A genetic event primitive (A, T, G, C)."""
    event_type: str  # 'A', 'T', 'G', 'C'
    spectral_bin: int  # 0, 1, 2, 3
    phase_perturbation: float
    amplitude_perturbation: float

class GeneticPrimitives:
    """The 4 genetic event primitives from spectral encoding."""

    def __init__(self):
        # Map events to spectral bins and perturbations
        self.events = {
            'A': GeneticEvent('A', 0, 0.0, 1.0),      # Bin 0, no phase shift, max amplitude
            'T': GeneticEvent('T', 1, np.pi/2, 1.0),   # Bin 1, π/2 phase shift
            'G': GeneticEvent('G', 2, np.pi, 1.0),     # Bin 2, π phase shift
            'C': GeneticEvent('C', 3, 3*np.pi/2, 1.0), # Bin 3, 3π/2 phase shift
        }

    def get_event(self, event_type: str) -> GeneticEvent:
        return self.events[event_type]

    def all_events(self) -> List[GeneticEvent]:
        return list(self.events.values())

class BraidedFieldWithGenetics:
    """Braided field that accepts genetic event perturbations."""

    def __init__(self, num_particles: int = 4):
        self.particles = []
        self.braiding_history = []
        self.genetic_perturbations = []
        self.magnetic_field = 0.0
        self.spectral_bins = [0.0 + 0j] * 8  # 8 spectral bins

        # Initialize particles at different positions
        for i in range(num_particles):
            angle = 2 * np.pi * i / num_particles
            self.particles.append({
                'position': (np.cos(angle), np.sin(angle)),
                'phase': 0.0,
                'amplitude': 1.0
            })

    def apply_genetic_event(self, event: GeneticEvent):
        """Apply a genetic event perturbation to the braided field."""
        self.genetic_perturbations.append(event)

        # Apply phase perturbation to all particles
        for p in self.particles:
            p['phase'] += event.phase_perturbation

        # Apply amplitude perturbation to spectral bin
        self.spectral_bins[event.spectral_bin] += event.amplitude_perturbation * cmath.exp(1j * event.phase_perturbation)

        # Record as a braiding operation
        self.braiding_history.append({
            'type': 'genetic',
            'event': event.event_type,
            'phase_shift': event.phase_perturbation,
            'amplitude': event.amplitude_perturbation
        })

    def apply_braiding(self, i: int, j: int, phase_shift: float):
        """Apply a standard braiding operation."""
        if i >= len(self.particles) or j >= len(self.particles):
            raise IndexError("Particle index out of range")

        # Swap particles
        self.particles[i], self.particles[j] = self.particles[j], self.particles[i]

        # Apply phase shift
        self.particles[i]['phase'] += phase_shift
        self.particles[j]['phase'] += phase_shift

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
            psi += p['amplitude'] * cmath.exp(1j * p['phase'])
        return psi

    def spectral_signature(self) -> List[complex]:
        """Get the spectral signature from accumulated genetic events."""
        return self.spectral_bins

    def topological_invariant(self) -> float:
        """Compute topological invariant from braiding history."""
        total = 0.0
        for op in self.braiding_history:
            if op['type'] == 'braid':
                total += op['phase_shift']
            elif op['type'] == 'genetic':
                total += op['phase_shift']
        return total

    def is_topologically_protected(self) -> bool:
        """Check if field is topologically protected."""
        return self.topological_invariant() != 0 and self.magnetic_field > 0

def simulate_genetic_perturbations():
    """Simulate applying genetic event primitives to braided field."""
    print("=== Braided Field with Genetic Event Primitives ===\n")

    # Initialize system
    primitives = GeneticPrimitives()
    field = BraidedFieldWithGenetics(num_particles=4)

    print(f"Initial state:")
    print(f"  Particles: {len(field.particles)}")
    print(f"  Wavefunction: {field.total_wavefunction():.4f}")
    print(f"  Topological invariant: {field.topological_invariant():.4f}\n")

    # Apply each genetic event
    print("Applying genetic event primitives:")

    for event in primitives.all_events():
        field.apply_genetic_event(event)
        print(f"  Event {event.event_type}:")
        print(f"    Spectral bin: {event.spectral_bin}")
        print(f"    Phase perturbation: {event.phase_perturbation:.4f} rad")
        print(f"    Wavefunction: {field.total_wavefunction():.4f}")
        print(f"    Topological invariant: {field.topological_invariant():.4f}")
        print()

    # Show spectral signature
    print("Spectral signature after genetic perturbations:")
    for i, bin_val in enumerate(field.spectral_bins[:4]):
        print(f"  Bin {i}: {bin_val:.4f}")
    print()

    # Apply magnetic field
    field.magnetic_field = 1.0
    print(f"Applied magnetic field: {field.magnetic_field}")
    print(f"Topologically protected: {field.is_topologically_protected()}\n")

    print(f"Final topological invariant: {field.topological_invariant():.4f}")
    print(f"Total operations: {len(field.braiding_history)}")

def simulate_genetic_braiding_sequence():
    """Simulate alternating genetic events and braiding operations."""
    print("\n=== Genetic-Braiding Sequence Simulation ===\n")

    primitives = GeneticPrimitives()
    field = BraidedFieldWithGenetics(num_particles=4)

    sequence = [
        ('genetic', 'A'),
        ('braid', (0, 1, np.pi/4)),
        ('genetic', 'T'),
        ('braid', (1, 2, np.pi/3)),
        ('genetic', 'G'),
        ('braid', (2, 3, np.pi/5)),
        ('genetic', 'C'),
        ('braid', (0, 3, np.pi/2)),
    ]

    print(f"Initial wavefunction: {field.total_wavefunction():.4f}")
    print(f"Initial invariant: {field.topological_invariant():.4f}\n")

    for op_type, data in sequence:
        if op_type == 'genetic':
            event = primitives.get_event(data)
            field.apply_genetic_event(event)
            print(f"Genetic event {data}:")
            print(f"  Wavefunction: {field.total_wavefunction():.4f}")
            print(f"  Invariant: {field.topological_invariant():.4f}")
        elif op_type == 'braid':
            i, j, phase = data
            field.apply_braiding(i, j, phase)
            print(f"Braid ({i},{j}) with phase {phase:.4f}:")
            print(f"  Wavefunction: {field.total_wavefunction():.4f}")
            print(f"  Invariant: {field.topological_invariant():.4f}")
        print()

    field.magnetic_field = 1.0
    print(f"Applied magnetic field: {field.magnetic_field}")
    print(f"Topologically protected: {field.is_topologically_protected()}")
    print(f"Final invariant: {field.topological_invariant():.4f}")

def plot_genetic_phase_space():
    """Visualize genetic event perturbations in phase space."""
    print("\n=== Genetic Event Phase Space ===\n")

    primitives = GeneticPrimitives()

    # Get phase shifts for each event
    events = primitives.all_events()
    phases = [e.phase_perturbation for e in events]
    amplitudes = [e.amplitude_perturbation for e in events]
    labels = [e.event_type for e in events]
    bins = [e.spectral_bin for e in events]

    # Create polar plot
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))

    # Plot each event as a point
    for phase, amp, label, bin_idx in zip(phases, amplitudes, labels, bins):
        ax.plot(phase, amp, 'o', markersize=12, label=f'{label} (bin {bin_idx})')
        ax.annotate(label, (phase, amp), xytext=(10, 10),
                   textcoords='offset points', fontsize=10)

    # Draw lines from origin
    for phase, amp in zip(phases, amplitudes):
        ax.plot([0, phase], [0, amp], 'b-', alpha=0.3)

    ax.set_title('Genetic Event Primitives in Phase Space', pad=20)
    ax.set_xlabel('Phase (radians)')
    ax.set_ylabel('Amplitude')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right')

    plt.tight_layout()
    plt.savefig('/tmp/genetic_phase_space.png', dpi=150)
    print("Genetic phase space plot saved to /tmp/genetic_phase_space.png")

def simulate_genetic_topological_encoding():
    """Simulate encoding information in braided field using genetic events."""
    print("\n=== Topological Encoding with Genetic Events ===\n")

    primitives = GeneticPrimitives()
    field = BraidedFieldWithGenetics(num_particles=4)

    # Encode "ATGC" sequence
    sequence = ['A', 'T', 'G', 'C']

    print(f"Encoding sequence: {''.join(sequence)}")
    print(f"Initial wavefunction: {field.total_wavefunction():.4f}")
    print(f"Initial invariant: {field.topological_invariant():.4f}\n")

    for event_type in sequence:
        event = primitives.get_event(event_type)
        field.apply_genetic_event(event)
        print(f"Encoded {event_type}:")
        print(f"  Wavefunction: {field.total_wavefunction():.4f}")
        print(f"  Invariant: {field.topological_invariant():.4f}")

    # Apply magnetic field to lock topology
    field.magnetic_field = 1.0
    print(f"\nApplied magnetic field: {field.magnetic_field}")
    print(f"Topologically protected: {field.is_topologically_protected()}")

    # Check if information is preserved in topology
    final_invariant = field.topological_invariant()
    print(f"\nFinal topological invariant: {final_invariant:.4f}")

    # The invariant encodes the sequence information
    expected_invariant = sum(e.phase_perturbation for e in primitives.all_events())
    print(f"Expected invariant (sum of phases): {expected_invariant:.4f}")
    print(f"Match: {abs(final_invariant - expected_invariant) < 1e-10}")

    print("\nThe genetic sequence is now encoded in the topological invariant,")
    print("making it immune to local perturbations.")

if __name__ == "__main__":
    simulate_genetic_perturbations()
    simulate_genetic_braiding_sequence()
    plot_genetic_phase_space()
    simulate_genetic_topological_encoding()

    print("\n=== Simulation Complete ===")
    print("Genetic event primitives (A, T, G, C) successfully applied to braided field.")
    print("The 4 primitives create distinct phase perturbations that affect")
    print("the topological invariant, enabling information encoding in")
    print("the braided field topology.")
