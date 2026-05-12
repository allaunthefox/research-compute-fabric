#!/usr/bin/env python3
"""
Moldable Information Transfer using Braided Field Primitives

This script explores how the 4 Hamiltonian components can be used as "knobs"
to mold information transfer characteristics - making it flexible, adaptable,
and configurable without requiring physical field tests.
"""

import numpy as np
import cmath
from dataclasses import dataclass
from typing import List, Tuple, Dict
import matplotlib.pyplot as plt

@dataclass
class TransferPrimitive:
    """A primitive that molds information transfer characteristics."""
    name: str
    phase_coupling: float
    energy_modulation: float
    bandwidth_factor: float
    noise_resistance: float

class MoldableTransfer:
    """Information transfer system with moldable characteristics."""

    def __init__(self):
        # The 4 Hamiltonian components as transfer primitives
        self.primitives = {
            'photon': TransferPrimitive('photon', 0.0, 1.0, 1.0, 0.1),
            'electron': TransferPrimitive('electron', np.pi/4, 0.8, 0.9, 0.3),
            'phonon': TransferPrimitive('phonon', np.pi/2, 0.6, 0.7, 0.6),
            'interaction': TransferPrimitive('interaction', np.pi, 0.4, 0.5, 0.9),
        }
        self.transfer_state = {
            'phase': 0.0,
            'energy': 1.0,
            'bandwidth': 1.0,
            'noise_resistance': 0.2,
            'signal': 1.0 + 0j
        }
        self.history = []

    def apply_primitive(self, primitive_name: str, weight: float = 1.0):
        """Apply a primitive to mold transfer characteristics."""
        prim = self.primitives[primitive_name]

        # Mold the transfer state based on primitive characteristics
        self.transfer_state['phase'] += prim.phase_coupling * weight
        self.transfer_state['energy'] *= (1.0 + prim.energy_modulation * weight * 0.1)
        self.transfer_state['bandwidth'] *= prim.bandwidth_factor ** weight
        self.transfer_state['noise_resistance'] += prim.noise_resistance * weight * 0.1

        # Apply phase to signal
        phase_shift = prim.phase_coupling * weight
        self.transfer_state['signal'] *= cmath.exp(1j * phase_shift)

        # Record the operation
        self.history.append({
            'primitive': primitive_name,
            'weight': weight,
            'phase_coupling': prim.phase_coupling * weight,
            'energy_mod': prim.energy_modulation * weight,
            'bandwidth': self.transfer_state['bandwidth'],
            'noise_resistance': self.transfer_state['noise_resistance']
        })

    def get_transfer_characteristics(self) -> Dict[str, float]:
        """Get current transfer characteristics."""
        return {
            'phase': self.transfer_state['phase'],
            'energy': self.transfer_state['energy'],
            'bandwidth': self.transfer_state['bandwidth'],
            'noise_resistance': self.transfer_state['noise_resistance'],
            'signal_magnitude': abs(self.transfer_state['signal']),
            'signal_phase': cmath.phase(self.transfer_state['signal'])
        }

    def reset(self):
        """Reset transfer state to initial."""
        self.transfer_state = {
            'phase': 0.0,
            'energy': 1.0,
            'bandwidth': 1.0,
            'noise_resistance': 0.2,
            'signal': 1.0 + 0j
        }
        self.history = []

def explore_moldable_profiles():
    """Explore different transfer profiles by applying primitives in different ways."""
    print("=== Moldable Information Transfer Profiles ===\n")

    # Profile 1: High bandwidth, low noise resistance
    print("Profile 1: High Bandwidth (photon-heavy)")
    mt = MoldableTransfer()
    mt.apply_primitive('photon', weight=2.0)
    mt.apply_primitive('electron', weight=0.5)
    chars = mt.get_transfer_characteristics()
    print(f"  Bandwidth: {chars['bandwidth']:.4f}")
    print(f"  Noise resistance: {chars['noise_resistance']:.4f}")
    print(f"  Signal magnitude: {chars['signal_magnitude']:.4f}\n")

    # Profile 2: High noise resistance, lower bandwidth
    print("Profile 2: Noise Resistant (phonon-heavy)")
    mt = MoldableTransfer()
    mt.apply_primitive('phonon', weight=2.0)
    mt.apply_primitive('interaction', weight=1.0)
    chars = mt.get_transfer_characteristics()
    print(f"  Bandwidth: {chars['bandwidth']:.4f}")
    print(f"  Noise resistance: {chars['noise_resistance']:.4f}")
    print(f"  Signal magnitude: {chars['signal_magnitude']:.4f}\n")

    # Profile 3: Balanced
    print("Profile 3: Balanced (equal mix)")
    mt = MoldableTransfer()
    for prim in ['photon', 'electron', 'phonon', 'interaction']:
        mt.apply_primitive(prim, weight=1.0)
    chars = mt.get_transfer_characteristics()
    print(f"  Bandwidth: {chars['bandwidth']:.4f}")
    print(f"  Noise resistance: {chars['noise_resistance']:.4f}")
    print(f"  Signal magnitude: {chars['signal_magnitude']:.4f}\n")

def adaptive_transfer_simulation():
    """Simulate adaptive information transfer using moldable primitives."""
    print("=== Adaptive Transfer Simulation ===\n")

    mt = MoldableTransfer()

    # Scenario: adapt to changing channel conditions
    scenarios = [
        ("Clean channel", {'photon': 2.0, 'electron': 0.5}),
        ("Noisy channel", {'phonon': 0.5, 'phonon': 2.0, 'interaction': 1.5}),
        ("Bandwidth-limited", {'electron': 1.5, 'phonon': 1.0}),
        ("High-latency", {'photon': 1.0, 'interaction': 2.0}),
    ]

    for scenario_name, weights in scenarios:
        mt.reset()
        print(f"Scenario: {scenario_name}")

        for prim, weight in weights.items():
            mt.apply_primitive(prim, weight)

        chars = mt.get_transfer_characteristics()
        print(f"  Applied: {weights}")
        print(f"  Result - Bandwidth: {chars['bandwidth']:.4f}, Noise resistance: {chars['noise_resistance']:.4f}")
        print(f"  Signal: {chars['signal_magnitude']:.4f} ∠{chars['signal_phase']:.4f} rad\n")

def continuous_molding_space():
    """Explore the continuous molding space of transfer characteristics."""
    print("=== Continuous Molding Space ===\n")

    mt = MoldableTransfer()

    # Explore the space by varying weights continuously
    photon_weights = np.linspace(0, 2, 5)
    phonon_weights = np.linspace(0, 2, 5)

    print("Molding space exploration (photon vs phonon weights):")
    print("Photon weight | Phonon weight | Bandwidth | Noise resistance")
    print("-" * 60)

    for pw in photon_weights:
        for phw in phonon_weights:
            mt.reset()
            mt.apply_primitive('photon', weight=pw)
            mt.apply_primitive('phonon', weight=phw)
            chars = mt.get_transfer_characteristics()
            print(f"{pw:10.2f} | {phw:12.2f} | {chars['bandwidth']:8.4f} | {chars['noise_resistance']:.4f}")

def information_encoding_with_molding():
    """Encode information by molding transfer characteristics."""
    print("\n=== Information Encoding via Transfer Molding ===\n")

    mt = MoldableTransfer()

    # Encode a message as a sequence of primitive applications
    message = "HELLO"

    # Map characters to primitive combinations
    encoding = {
        'H': {'photon': 1.0, 'electron': 0.5},
        'E': {'electron': 1.0, 'phonon': 0.5},
        'L': {'phonon': 1.0, 'interaction': 0.5},
        'O': {'photon': 0.5, 'interaction': 1.0},
    }

    print(f"Encoding message: {message}")
    print(f"Initial signal: {mt.transfer_state['signal']:.4f}\n")

    for char in message:
        weights = encoding[char]
        for prim, weight in weights.items():
            mt.apply_primitive(prim, weight)
        chars = mt.get_transfer_characteristics()
        print(f"Encoded '{char}':")
        print(f"  Signal: {chars['signal_magnitude']:.4f} ∠{chars['signal_phase']:.4f} rad")
        print(f"  Transfer state: phase={chars['phase']:.4f}, energy={chars['energy']:.4f}\n")

    print("The message is encoded in the transfer characteristics,")
    print("not in the signal values themselves - making it moldable")

def plot_molding_space():
    """Visualize the molding space of transfer characteristics."""
    print("\n=== Molding Space Visualization ===\n")

    # Generate samples
    photon_weights = np.linspace(0, 2, 20)
    phonon_weights = np.linspace(0, 2, 20)

    bandwidths = []
    noise_resistances = []

    for pw in photon_weights:
        for phw in phonon_weights:
            mt = MoldableTransfer()
            mt.apply_primitive('photon', weight=pw)
            mt.apply_primitive('phonon', weight=phw)
            chars = mt.get_transfer_characteristics()
            bandwidths.append(chars['bandwidth'])
            noise_resistances.append(chars['noise_resistance'])

    # Create scatter plot
    fig, ax = plt.subplots(figsize=(10, 8))
    scatter = ax.scatter(bandwidths, noise_resistances, c=range(len(bandwidths)),
                        cmap='viridis', alpha=0.6)
    ax.set_xlabel('Bandwidth Factor')
    ax.set_ylabel('Noise Resistance')
    ax.set_title('Molding Space: Bandwidth vs Noise Resistance')
    ax.grid(True, alpha=0.3)
    plt.colorbar(scatter, label='Configuration index')

    plt.tight_layout()
    plt.savefig('/tmp/molding_space.png', dpi=150)
    print("Molding space plot saved to /tmp/molding_space.png")

if __name__ == "__main__":
    explore_moldable_profiles()
    adaptive_transfer_simulation()
    continuous_molding_space()
    information_encoding_with_molding()
    plot_molding_space()

    print("\n=== Simulation Complete ===")
    print("The 4 Hamiltonian primitives can mold information transfer characteristics")
    print("without requiring physical field tests. By adjusting primitive weights,")
    print("we can adapt bandwidth, noise resistance, and signal properties continuously.")
