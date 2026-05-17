#!/usr/bin/env python3
"""
Eigenvector Stability of Braided Field in Noisy Environment

This script computes the eigenvector decomposition of the braided field
transfer matrix and analyzes stability under various noise conditions.
This is relevant for compression - if information is encoded in transfer
characteristics, we need to know if those characteristics are stable.
"""

import numpy as np
import cmath
import hashlib
import json
import zlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
RECEIPT_PATH = ROOT / "4-Infrastructure" / "hardware" / "noise_stability_sim_receipt.json"
PLOT_PATH = ROOT / "4-Infrastructure" / "hardware" / "eigenvalue_trajectory.png"

@dataclass
class NoiseEnvironment:
    """Parameters for the noisy environment."""
    thermal_noise: float  # Temperature-dependent noise
    quantum_noise: float   # Quantum fluctuations
    disorder_strength: float  # Structural disorder
    correlation_length: float  # Noise correlation length

class BraidedFieldMatrix:
    """Linear system representation of braided field for eigenvector analysis."""

    def __init__(self, num_particles: int = 4):
        self.num_particles = num_particles
        # Transfer matrix representing the system
        self.matrix = np.eye(num_particles, dtype=complex)
        self.eigenvalues = None
        self.eigenvectors = None

    def apply_hamiltonian_component(self, component_type: str, weight: float):
        """Apply a Hamiltonian component to the transfer matrix."""
        # Component-specific matrix modifications
        if component_type == 'photon':
            # Photon: diagonal phase shifts
            for i in range(self.num_particles):
                self.matrix[i, i] *= cmath.exp(1j * weight * 0.1)
        elif component_type == 'electron':
            # Electron: off-diagonal coupling
            for i in range(self.num_particles - 1):
                self.matrix[i, i+1] += weight * 0.05 * cmath.exp(1j * np.pi/4)
                self.matrix[i+1, i] += weight * 0.05 * cmath.exp(-1j * np.pi/4)
        elif component_type == 'phonon':
            # Phonon: stronger coupling with phase
            for i in range(self.num_particles - 1):
                self.matrix[i, i+1] += weight * 0.1 * cmath.exp(1j * np.pi/2)
                self.matrix[i+1, i] += weight * 0.1 * cmath.exp(-1j * np.pi/2)
        elif component_type == 'interaction':
            # Interaction: global coupling
            for i in range(self.num_particles):
                for j in range(self.num_particles):
                    if i != j:
                        self.matrix[i, j] += weight * 0.02 * cmath.exp(1j * np.pi)

    def add_noise(self, noise_env: NoiseEnvironment, gain: float = 0.01):
        """Add noise to the transfer matrix."""
        n = self.num_particles

        # Thermal noise: random perturbations
        thermal_perturbation = np.random.normal(0, noise_env.thermal_noise, (n, n)) + \
                              1j * np.random.normal(0, noise_env.thermal_noise, (n, n))

        # Quantum noise: coherent perturbations
        quantum_perturbation = np.random.normal(0, noise_env.quantum_noise, (n, n)) * \
                             np.exp(1j * np.random.uniform(0, 2*np.pi, (n, n)))

        # Disorder: diagonal variations
        disorder = np.random.normal(0, noise_env.disorder_strength, n)
        disorder_matrix = np.diag(disorder)

        # Combine noise sources
        total_noise = thermal_perturbation + quantum_perturbation + disorder_matrix
        self.matrix += total_noise * gain

    def compute_eigendecomposition(self):
        """Compute eigenvalues and eigenvectors."""
        self.eigenvalues, self.eigenvectors = np.linalg.eig(self.matrix)
        return self.eigenvalues, self.eigenvectors

    def spectral_radius(self) -> float:
        """Compute spectral radius (max eigenvalue magnitude)."""
        if self.eigenvalues is None:
            self.compute_eigendecomposition()
        return max(abs(ev) for ev in self.eigenvalues)

    def condition_number(self) -> float:
        """Compute condition number (stability metric)."""
        if self.eigenvalues is None:
            self.compute_eigendecomposition()
        magnitudes = [abs(ev) for ev in self.eigenvalues]
        return max(magnitudes) / (min(magnitudes) + 1e-10)

    def stability_margin(self) -> float:
        """Compute stability margin (distance to instability)."""
        if self.eigenvalues is None:
            self.compute_eigendecomposition()
        # Stability margin = minimum distance of eigenvalues from unit circle
        margin = min(abs(abs(ev) - 1.0) for ev in self.eigenvalues)
        return margin

    def dominant_eigenvector(self) -> np.ndarray:
        """Get the eigenvector corresponding to the dominant eigenvalue."""
        if self.eigenvalues is None:
            self.compute_eigendecomposition()
        idx = np.argmax(abs(self.eigenvalues))
        return self.eigenvectors[:, idx]

def noise_stability_analysis(gain: float = 0.01, label: str = "micro"):
    """Analyze eigenvector stability under various noise conditions."""
    print(f"=== Eigenvector Stability Analysis in Noisy Environment ({label}, gain={gain}) ===\n")

    # Test different noise levels
    noise_levels = [
        ("Low noise", NoiseEnvironment(0.01, 0.01, 0.01, 1.0)),
        ("Medium noise", NoiseEnvironment(0.05, 0.05, 0.05, 1.0)),
        ("High noise", NoiseEnvironment(0.1, 0.1, 0.1, 1.0)),
        ("Extreme noise", NoiseEnvironment(0.2, 0.2, 0.2, 1.0)),
    ]

    print("Stability metrics vs noise level:")
    print("-" * 70)
    print(f"{'Noise Level':<15} {'Spectral Radius':<15} {'Condition #':<12} {'Stability Margin':<15}")
    print("-" * 70)

    results = []

    for name, noise_env in noise_levels:
        # Create braided field with Hamiltonian components
        bf = BraidedFieldMatrix(num_particles=4)

        # Apply standard Hamiltonian components
        bf.apply_hamiltonian_component('photon', weight=1.0)
        bf.apply_hamiltonian_component('electron', weight=1.0)
        bf.apply_hamiltonian_component('phonon', weight=1.0)
        bf.apply_hamiltonian_component('interaction', weight=1.0)

        # Add noise
        bf.add_noise(noise_env, gain=gain)

        # Compute stability metrics
        spectral_radius = bf.spectral_radius()
        condition_num = bf.condition_number()
        stability_margin = bf.stability_margin()

        print(f"{name:<15} {spectral_radius:<15.4f} {condition_num:<12.4f} {stability_margin:<15.4f}")

        results.append({
            "name": name,
            "gain": gain,
            "spectral_radius": float(spectral_radius),
            "condition_number": float(condition_num),
            "stability_margin": float(stability_margin),
            "eigenvalues": [
                {
                    "real": float(ev.real),
                    "imag": float(ev.imag),
                    "magnitude": float(abs(ev)),
                    "phase": float(cmath.phase(ev)),
                }
                for ev in bf.eigenvalues
            ],
        })

    print()

    # Analyze eigenvalue distribution
    print("Eigenvalue distribution (high noise case):")
    high_noise_eigenvalues = [
        complex(row["real"], row["imag"]) for row in results[-1]["eigenvalues"]
    ]
    for i, ev in enumerate(high_noise_eigenvalues):
        print(f"  λ_{i}: {ev:.4f} (magnitude: {abs(ev):.4f}, phase: {cmath.phase(ev):.4f} rad)")

    return {
        "label": label,
        "gain": gain,
        "rows": results,
    }

def eigenvector_persistence(gain: float = 0.01, label: str = "micro"):
    """Test if eigenvectors persist under repeated noise."""
    print(f"\n=== Eigenvector Persistence Under Repeated Noise ({label}, gain={gain}) ===\n")

    bf = BraidedFieldMatrix(num_particles=4)

    # Apply standard Hamiltonian components
    bf.apply_hamiltonian_component('photon', weight=1.0)
    bf.apply_hamiltonian_component('electron', weight=1.0)
    bf.apply_hamiltonian_component('phonon', weight=1.0)
    bf.apply_hamiltonian_component('interaction', weight=1.0)

    # Get initial eigenvector
    bf.compute_eigendecomposition()
    initial_eigenvector = bf.dominant_eigenvector()

    print(f"Initial dominant eigenvector: {initial_eigenvector}")

    noise_env = NoiseEnvironment(0.05, 0.05, 0.05, 1.0)

    # Apply noise multiple times and track eigenvector similarity
    similarities = []

    for i in range(10):
        bf.add_noise(noise_env, gain=gain)
        bf.compute_eigendecomposition()
        current_eigenvector = bf.dominant_eigenvector()

        # Compute similarity (cosine of angle between vectors)
        similarity = abs(np.vdot(initial_eigenvector, current_eigenvector)) / \
                    (np.linalg.norm(initial_eigenvector) * np.linalg.norm(current_eigenvector))
        similarities.append(similarity)

        print(f"  Noise iteration {i}: similarity = {similarity:.4f}")

    print(f"\nAverage similarity: {np.mean(similarities):.4f}")
    print(f"Similarity degradation: {similarities[0] - similarities[-1]:.4f}")

    return {
        "label": label,
        "gain": gain,
        "similarities": [float(x) for x in similarities],
        "average_similarity": float(np.mean(similarities)),
        "similarity_degradation": float(similarities[0] - similarities[-1]),
    }

def information_capacity_analysis(gain: float = 0.01, label: str = "micro"):
    """Analyze information capacity under noise using eigenvalue spectrum."""
    print(f"\n=== Information Capacity Analysis ({label}, gain={gain}) ===\n")

    bf = BraidedFieldMatrix(num_particles=4)

    # Apply standard Hamiltonian components
    bf.apply_hamiltonian_component('photon', weight=1.0)
    bf.apply_hamiltonian_component('electron', weight=1.0)
    bf.apply_hamiltonian_component('phonon', weight=1.0)
    bf.apply_hamiltonian_component('interaction', weight=1.0)

    print("Information capacity vs noise level:")
    print("-" * 60)
    print(f"{'Noise Level':<15} {'Spectral Entropy':<20} {'Effective Rank':<15}")
    print("-" * 60)

    noise_levels = [0.0, 0.02, 0.05, 0.1, 0.2]
    rows = []

    for noise_level in noise_levels:
        bf_temp = BraidedFieldMatrix(num_particles=4)
        bf_temp.matrix = bf.matrix.copy()

        if noise_level > 0:
            noise_env = NoiseEnvironment(noise_level, noise_level, noise_level, 1.0)
            bf_temp.add_noise(noise_env, gain=gain)

        bf_temp.compute_eigendecomposition()

        # Compute spectral entropy (information measure)
        eigenvalue_mags = np.array([abs(ev) for ev in bf_temp.eigenvalues])
        eigenvalue_mags = eigenvalue_mags / np.sum(eigenvalue_mags)  # Normalize
        spectral_entropy = -np.sum(eigenvalue_mags * np.log(eigenvalue_mags + 1e-10))

        # Compute effective rank (number of significant eigenvalues)
        effective_rank = np.sum(eigenvalue_mags > 0.1)

        print(f"{noise_level:<15.2f} {spectral_entropy:<20.4f} {effective_rank:<15.0f}")
        rows.append({
            "noise_level": float(noise_level),
            "spectral_entropy": float(spectral_entropy),
            "effective_rank": int(effective_rank),
        })

    return {
        "label": label,
        "gain": gain,
        "rows": rows,
    }

def stochastic_crc_lane(stability: dict, persistence: dict, capacity: dict) -> dict:
    """Derive a deterministic CRC witness from the seeded stochastic micro-noise lane.

    This is not an error-correcting code by itself. It is a compact witness over
    the sampled noise response, suitable for detecting drift in a replayed probe.
    """
    payload = {
        "stability_rows": [
            {
                "name": row["name"],
                "spectral_radius_q": round(row["spectral_radius"], 8),
                "condition_number_q": round(row["condition_number"], 8),
                "stability_margin_q": round(row["stability_margin"], 8),
                "eigenvalue_magnitudes_q": [
                    round(ev["magnitude"], 8) for ev in row["eigenvalues"]
                ],
                "eigenvalue_phases_q": [
                    round(ev["phase"], 8) for ev in row["eigenvalues"]
                ],
            }
            for row in stability["rows"]
        ],
        "persistence_q": [round(x, 8) for x in persistence["similarities"]],
        "capacity_rows": [
            {
                "noise_level": row["noise_level"],
                "spectral_entropy_q": round(row["spectral_entropy"], 8),
                "effective_rank": row["effective_rank"],
            }
            for row in capacity["rows"]
        ],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    crc = zlib.crc32(encoded) & 0xFFFFFFFF
    return {
        "schema": "stochastic_crc_lane_v1",
        "source": "seeded micro-gain eigen/noise lane",
        "quantization": "round floating metrics to 8 decimal places before CRC32",
        "byte_length": len(encoded),
        "crc32_hex": f"{crc:08x}",
        "payload_sha256": hashlib.sha256(encoded).hexdigest(),
        "claim_boundary": "CRC witnesses replay drift in this seeded toy noise lane; it is not a proof of physical noise immunity or cryptographic integrity.",
    }

def plot_eigenvalue_trajectory(gain: float = 0.01, label: str = "micro"):
    """Plot eigenvalue trajectory under increasing noise."""
    print(f"\n=== Eigenvalue Trajectory Visualization ({label}, gain={gain}) ===\n")

    bf = BraidedFieldMatrix(num_particles=4)

    # Apply standard Hamiltonian components
    bf.apply_hamiltonian_component('photon', weight=1.0)
    bf.apply_hamiltonian_component('electron', weight=1.0)
    bf.apply_hamiltonian_component('phonon', weight=1.0)
    bf.apply_hamiltonian_component('interaction', weight=1.0)

    # Track eigenvalues under increasing noise
    noise_levels = np.linspace(0, 0.3, 30)
    eigenvalue_trajectories = [[] for _ in range(4)]

    for noise_level in noise_levels:
        bf_temp = BraidedFieldMatrix(num_particles=4)
        bf_temp.matrix = bf.matrix.copy()

        if noise_level > 0:
            noise_env = NoiseEnvironment(noise_level, noise_level, noise_level, 1.0)
            bf_temp.add_noise(noise_env, gain=gain)

        bf_temp.compute_eigendecomposition()

        for i, ev in enumerate(bf_temp.eigenvalues):
            eigenvalue_trajectories[i].append(ev)

    # Plot trajectories
    fig, ax = plt.subplots(figsize=(10, 8))

    colors = ['red', 'blue', 'green', 'orange']
    for i, trajectory in enumerate(eigenvalue_trajectories):
        real_parts = [ev.real for ev in trajectory]
        imag_parts = [ev.imag for ev in trajectory]
        ax.plot(real_parts, imag_parts, color=colors[i], linewidth=2,
                marker='o', markersize=3, label=f'λ_{i}')
        # Mark initial and final points
        ax.plot(real_parts[0], imag_parts[0], 's', color=colors[i], markersize=8)
        ax.plot(real_parts[-1], imag_parts[-1], '^', color=colors[i], markersize=8)

    # Draw unit circle
    theta = np.linspace(0, 2*np.pi, 100)
    ax.plot(np.cos(theta), np.sin(theta), 'k--', alpha=0.3, label='Unit circle')

    ax.set_xlabel('Re(λ)')
    ax.set_ylabel('Im(λ)')
    ax.set_title('Eigenvalue Trajectories Under Increasing Noise')
    ax.axhline(y=0, color='k', linestyle='-', alpha=0.1)
    ax.axvline(x=0, color='k', linestyle='-', alpha=0.1)
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.axis('equal')

    plt.tight_layout()
    plt.savefig(PLOT_PATH, dpi=150)
    print(f"Eigenvalue trajectory plot saved to {PLOT_PATH}")
    return {
        "label": label,
        "gain": gain,
        "plot_path": str(PLOT_PATH),
        "noise_levels": [float(x) for x in noise_levels],
    }

if __name__ == "__main__":
    # Set random seed for reproducibility
    np.random.seed(42)

    micro_stability = noise_stability_analysis(gain=0.01, label="micro")
    micro_persistence = eigenvector_persistence(gain=0.01, label="micro")
    micro_capacity = information_capacity_analysis(gain=0.01, label="micro")
    micro_stochastic_crc = stochastic_crc_lane(
        micro_stability,
        micro_persistence,
        micro_capacity,
    )
    trajectory = plot_eigenvalue_trajectory(gain=0.01, label="micro")

    direct_stability = noise_stability_analysis(gain=1.0, label="direct")
    direct_persistence = eigenvector_persistence(gain=1.0, label="direct")
    direct_capacity = information_capacity_analysis(gain=1.0, label="direct")

    receipt = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "lawful": True,
        "mode": "virtual_only",
        "source_note": "No hardware programming, RF emission, JTAG, serial flashing, board access, or material claim. Python eigenvector stability simulation only.",
        "noise_gain_boundary": "The original micro lane uses gain=0.01, so nominal extreme noise is intentionally small. Direct lane uses gain=1.0 to expose degradation.",
        "micro_gain": {
            "stability": micro_stability,
            "persistence": micro_persistence,
            "capacity": micro_capacity,
            "stochastic_crc": micro_stochastic_crc,
        },
        "direct_gain": {
            "stability": direct_stability,
            "persistence": direct_persistence,
            "capacity": direct_capacity,
        },
        "trajectory": trajectory,
        "claim_boundary": "This simulation records transfer-matrix eigen stability in a toy braided-field model. It does not prove topological protection, local-noise immunity, device feasibility, material existence, compression advantage, or Hutter Prize relevance.",
    }
    encoded = json.dumps(receipt, indent=2, sort_keys=True).encode("utf-8")
    receipt["receipt_hash_preimage_sha256"] = hashlib.sha256(encoded).hexdigest()
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("\n=== Analysis Complete ===")
    print("The eigenvector analysis shows:")
    print("1. Micro-gain noise can look almost invariant because gain=0.01")
    print("2. Direct-gain noise exposes actual degradation and mode drift")
    print("3. Eigenvectors should be treated as transfer-characteristic candidates")
    print("4. Eigenvalue trajectories show how the toy system evolves under noise")
    print("\nFor compression applications, this suggests that transfer characteristic")
    print("encoding is worth testing, but no compression advantage is claimed.")
    print(f"Receipt written to {RECEIPT_PATH}")
