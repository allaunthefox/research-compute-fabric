#!/usr/bin/env python3
"""
V4 Minimal Cotranslational Simulator

Implements the minimal V4 simulator with:
- Exposed prefix (Eₜ)
- Pause field (P(t))
- Contact probability term (Πᵢⱼ(t))
- Transient bias field (Bₖ(t))

Based on V4 Full Cotranslational Codon-Peptide Equation Set
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class ExpertType(Enum):
    HELIX = "helix"
    SHEET = "sheet"
    LOOP = "loop"


@dataclass
class Codon:
    """Represents a codon with its properties"""
    index: int
    nucleotides: str
    amino_acid: str
    translation_speed: float  # v(c)
    folding_delay: float  # τ(c) = 1/v(c)
    structural_bias: Dict[ExpertType, float]  # bₖ(c)
    bias_lifetime: float  # τ_b(c)


@dataclass
class Residue:
    """Represents a single amino acid residue"""
    index: int
    amino_acid: str
    position_3d: np.ndarray  # 3D coordinates
    translation_time: float  # Tₘ


@dataclass
class Expert:
    """Represents an MoE expert"""
    type: ExpertType
    logit: float  # zₖ
    advice: np.ndarray  # Advice vector


class V4CotranslationalSimulator:
    """
    Minimal V4 Cotranslational Simulator
    
    Implements:
    - Time-indexed translation state (Tₘ, m(t), Sₜ)
    - Ribosome pausing field (p(cᵢ), P(t))
    - Nascent-chain exposure window (Eₜ)
    - Contact formation kinetics (Πᵢⱼ(t), χᵢⱼ(t))
    - Transient codon bias (Bₖ(t))
    """
    
    def __init__(
        self,
        sequence: List[Codon],
        exposed_length: int = 10,  # L_exp
        alpha_p: float = 1.0,  # pause speed coefficient
        beta_p: float = 0.1,  # pause rarity coefficient
        kappa_p: float = 1.0,  # pause accessibility coefficient
        kappa_e: float = 1.0,  # exposure accessibility coefficient
        sigma_d: float = 1.0,  # spatial scale
        sigma_g: float = 1.0,  # geometric scale
        eta: float = 0.1,  # energy sensitivity
    ):
        self.sequence = sequence
        self.exposed_length = exposed_length
        
        # Parameters
        self.alpha_p = alpha_p
        self.beta_p = beta_p
        self.kappa_p = kappa_p
        self.kappa_e = kappa_e
        self.sigma_d = sigma_d
        self.sigma_g = sigma_g
        self.eta = eta
        
        # State
        self.time = 0.0
        self.translated_residues: List[Residue] = []
        self.expert_logits: Dict[ExpertType, float] = {
            ExpertType.HELIX: 0.0,
            ExpertType.SHEET: 0.0,
            ExpertType.LOOP: 0.0
        }
        
        # Precompute cumulative translation times
        self.cumulative_times = self._compute_cumulative_times()
    
    def _compute_cumulative_times(self) -> List[float]:
        """Compute Tₘ = Σ_{i=1}^{m} 1/v(cᵢ)"""
        times = []
        total = 0.0
        for codon in self.sequence:
            total += codon.folding_delay  # τ(c) = 1/v(c)
            times.append(total)
        return times
    
    def pause_intensity(self, codon: Codon) -> float:
        """Compute pause intensity p(cᵢ) = αₚ/v(cᵢ) + βₚ·σ_rare(cᵢ)"""
        # For simplicity, assume σ_rare = 0 for now
        return self.alpha_p / codon.translation_speed
    
    def pause_field(self, t: float) -> float:
        """Compute local pause field P(t) = p(c_{m(t)})"""
        m = self.visible_prefix_length(t)
        if m == 0:
            return 0.0
        codon = self.sequence[m - 1]
        return self.pause_intensity(codon)
    
    def visible_prefix_length(self, t: float) -> int:
        """Compute m(t) = max{m : Tₘ ≤ t}"""
        m = 0
        for i, T in enumerate(self.cumulative_times):
            if T <= t:
                m = i + 1
            else:
                break
        return m
    
    def exposed_segment(self, t: float) -> List[Residue]:
        """Compute exposed segment Eₜ = (a_{m(t)-L_exp+1}, ..., a_{m(t)})"""
        m = self.visible_prefix_length(t)
        start = max(0, m - self.exposed_length)
        return self.translated_residues[start:m]
    
    def kinetic_accessibility(self, i: int, j: int, t: float) -> float:
        """Compute χᵢⱼ(t) = (1 - e^{-κₚ P(t)}) (1 - e^{-κₑ τ_exp(i,j,t)})"""
        P = self.pause_field(t)
        tau_exp = self.exposure_time(i, j, t)
        
        pause_factor = 1 - np.exp(-self.kappa_p * P)
        exposure_factor = 1 - np.exp(-self.kappa_e * tau_exp)
        
        return pause_factor * exposure_factor
    
    def exposure_time(self, i: int, j: int, t: float) -> float:
        """Compute time both residues have been exposed together"""
        # Simplified: assume exposure time is proportional to time since translation
        if i >= len(self.translated_residues) or j >= len(self.translated_residues):
            return 0.0
        
        T_i = self.cumulative_times[i]
        T_j = self.cumulative_times[j]
        T_max = max(T_i, T_j)
        
        return max(0.0, t - T_max)
    
    def contact_probability(self, i: int, j: int, t: float) -> float:
        """Compute Πᵢⱼ(t) = 1_{i,j∈Eₜ}·exp(-dᵢⱼ²/2σ_d²)·exp(-Δᵢⱼ_geom²/2σ_g²)·χᵢⱼ(t)"""
        E = self.exposed_segment(t)
        exposed_indices = {r.index for r in E}
        
        if i not in exposed_indices or j not in exposed_indices:
            return 0.0
        
        if i >= len(self.translated_residues) or j >= len(self.translated_residues):
            return 0.0
        
        # Spatial separation
        d_ij = np.linalg.norm(
            self.translated_residues[i].position_3d - 
            self.translated_residues[j].position_3d
        )
        
        # Geometric compatibility (simplified as 1 for now)
        Delta_ij_geom = 1.0
        
        # Kinetic accessibility
        chi_ij = self.kinetic_accessibility(i, j, t)
        
        spatial_factor = np.exp(-d_ij**2 / (2 * self.sigma_d**2))
        geometric_factor = np.exp(-Delta_ij_geom**2 / (2 * self.sigma_g**2))
        
        return spatial_factor * geometric_factor * chi_ij
    
    def transient_bias(self, expert_type: ExpertType, t: float, window_size: int = 5) -> float:
        """Compute Bₖ(t) = Σ_{i∈Wₜ} bₖ(cᵢ)·exp(-(t-Tᵢ)/τ_b(cᵢ))"""
        m = self.visible_prefix_length(t)
        W = list(range(max(0, m - window_size), m))
        
        B = 0.0
        for i in W:
            codon = self.sequence[i]
            T_i = self.cumulative_times[i]
            tau_b = codon.bias_lifetime
            
            bias = codon.structural_bias.get(expert_type, 0.0)
            decay = np.exp(-(t - T_i) / tau_b)
            
            B += bias * decay
        
        return B
    
    def expert_weights(self, t: float) -> Dict[ExpertType, float]:
        """Compute gₖ(t) ∝ exp(zₖ(t) + Bₖ(t) + Dₖ(t) - ηEₖ(Θₜ))"""
        weights = {}
        
        for expert_type in ExpertType:
            z = self.expert_logits[expert_type]
            B = self.transient_bias(expert_type, t)
            D = self.delay_bias(t, expert_type)
            E = self.expert_energy_incompatibility(expert_type, t)
            
            logit = z + B + D - self.eta * E
            weights[expert_type] = np.exp(logit)
        
        # Normalize
        total = sum(weights.values())
        if total > 0:
            for expert_type in weights:
                weights[expert_type] /= total
        
        return weights
    
    def delay_bias(self, t: float, expert_type: ExpertType) -> float:
        """Compute Dₖ(t) based on pause field"""
        P = self.pause_field(t)
        
        # Simplified: different experts respond differently to pause
        if expert_type == ExpertType.HELIX:
            return -0.5 * P  # helix formation decreases with pause
        elif expert_type == ExpertType.SHEET:
            return -0.3 * P  # sheet formation decreases with pause
        else:  # LOOP
            return 0.8 * P  # loop formation increases with pause
    
    def expert_energy_incompatibility(self, expert_type: ExpertType, t: float) -> float:
        """Compute Eₖ(Θₜ) - simplified as 0 for minimal simulator"""
        return 0.0
    
    def step(self, dt: float = 0.1):
        """Advance simulation by dt"""
        self.time += dt
        
        # Translate new residues
        m = self.visible_prefix_length(self.time)
        while len(self.translated_residues) < m:
            i = len(self.translated_residues)
            codon = self.sequence[i]
            
            # Create new residue with random 3D position
            position = np.random.randn(3)  # Simplified
            residue = Residue(
                index=i,
                amino_acid=codon.amino_acid,
                position_3d=position,
                translation_time=self.cumulative_times[i]
            )
            self.translated_residues.append(residue)
        
        # Update expert logits based on RL (simplified)
        weights = self.expert_weights(self.time)
        for expert_type in ExpertType:
            # Simple RL update: increase logit for high-weight experts
            if weights[expert_type] > 0.5:
                self.expert_logits[expert_type] += 0.01 * dt
    
    def get_contact_average(self, t: float) -> float:
        """Compute average contact probability Π̄(t)"""
        E = self.exposed_segment(t)
        n = len(E)
        
        if n < 2:
            return 0.0
        
        total = 0.0
        count = 0
        for i in range(n):
            for j in range(i + 1, n):
                total += self.contact_probability(E[i].index, E[j].index, t)
                count += 1
        
        if count == 0:
            return 0.0
        
        return total / count
    
    def get_cds_score(self, t: float, alpha: float = 0.5, beta: float = 0.3, chi: float = 0.2) -> float:
        """Compute Φ_CDS(v4)(t) = α·Φ̄_codon + β·Φ_peptide(Θₜ,t) + χ·Π̄(t)"""
        m = self.visible_prefix_length(t)
        
        # Average codon fitness (simplified as 1.0)
        Phi_codon_avg = 1.0
        
        # Peptide efficiency (simplified as 1.0 / (1 + pause))
        P = self.pause_field(t)
        Phi_peptide = 1.0 / (1.0 + P)
        
        # Average contact probability
        Pi_avg = self.get_contact_average(t)
        
        return alpha * Phi_codon_avg + beta * Phi_peptide + chi * Pi_avg


def create_test_sequence() -> List[Codon]:
    """Create a test sequence for simulation"""
    amino_acids = ["A", "R", "N", "D", "C", "Q", "E", "G", "H", "I"]
    
    sequence = []
    for i in range(20):
        aa = amino_acids[i % len(amino_acids)]
        
        # Vary translation speed to test pause effects
        if i % 3 == 0:
            speed = 0.5  # Slow codon
        elif i % 3 == 1:
            speed = 1.0  # Medium codon
        else:
            speed = 2.0  # Fast codon
        
        codon = Codon(
            index=i,
            nucleotides=f"ABC",  # Simplified
            amino_acid=aa,
            translation_speed=speed,
            folding_delay=1.0 / speed,
            structural_bias={
                ExpertType.HELIX: np.random.randn() * 0.1,
                ExpertType.SHEET: np.random.randn() * 0.1,
                ExpertType.LOOP: np.random.randn() * 0.1
            },
            bias_lifetime=1.0
        )
        sequence.append(codon)
    
    return sequence


def run_simulation():
    """Run the V4 simulation"""
    print("=" * 70)
    print("V4 COTRANSLATIONAL SIMULATOR")
    print("=" * 70)
    
    # Create test sequence
    sequence = create_test_sequence()
    print(f"\nCreated test sequence with {len(sequence)} codons")
    
    # Initialize simulator
    sim = V4CotranslationalSimulator(sequence, exposed_length=5)
    
    # Run simulation
    print("\nRunning simulation...")
    print(f"{'Time':>8} | {'Translated':>10} | {'Exposed':>7} | {'Pause':>6} | {'Contact':>7} | {'Score':>6}")
    print("-" * 70)
    
    t = 0.0
    dt = 0.5
    max_time = 10.0
    
    results = []
    
    while t < max_time:
        sim.step(dt)
        
        m = sim.visible_prefix_length(t)
        E = sim.exposed_segment(t)
        P = sim.pause_field(t)
        Pi = sim.get_contact_average(t)
        score = sim.get_cds_score(t)
        
        print(f"{t:8.2f} | {m:10d} | {len(E):7d} | {P:6.3f} | {Pi:7.3f} | {score:6.3f}")
        
        results.append({
            "time": t,
            "translated": m,
            "exposed": len(E),
            "pause": P,
            "contact": Pi,
            "score": score
        })
        
        t += dt
    
    print("\n" + "=" * 70)
    print("SIMULATION COMPLETE")
    print("=" * 70)
    
    # Summary statistics
    final_score = results[-1]["score"]
    avg_pause = np.mean([r["pause"] for r in results])
    avg_contact = np.mean([r["contact"] for r in results])
    
    print(f"\nFinal CDS Score: {final_score:.4f}")
    print(f"Average Pause Field: {avg_pause:.4f}")
    print(f"Average Contact Probability: {avg_contact:.4f}")
    
    print("\nKey V4 Features Demonstrated:")
    print("- Time-indexed translation: residues become available at different times")
    print("- Pause field: slow codons create stronger pauses")
    print("- Exposure window: only tail of chain is structurally active")
    print("- Contact kinetics: pause affects contact formation probability")
    print("- Transient bias: codon bias decays over time")
    
    return results


if __name__ == "__main__":
    results = run_simulation()
