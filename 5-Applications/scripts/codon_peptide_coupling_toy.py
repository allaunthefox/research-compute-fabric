#!/usr/bin/env python3
"""
Codon-Peptide Coupling Toy Run

This script couples:
  - codon RL over synonymous choices
  - codon → amino acid translation
  - amino-acid-implied peptide expert field
  - peptide scoring at the CDS level

Demonstrates the integration between CodonOTOM efficiency functional
and the PeptideMoE system at the peptide level.
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple, Dict
from dataclasses import dataclass
from collections import defaultdict

# ============================================================================
# Genetic Code (Simplified)
# ============================================================================

# Simplified genetic code mapping (codon → amino acid)
GENETIC_CODE = {
    # Phenylalanine (2-fold degenerate)
    'UUU': 'F', 'UUC': 'F',
    # Leucine (6-fold degenerate)
    'UUA': 'L', 'UUG': 'L', 'CUU': 'L', 'CUC': 'L', 'CUA': 'L', 'CUG': 'L',
    # Isoleucine (3-fold degenerate)
    'AUU': 'I', 'AUC': 'I', 'AUA': 'I',
    # Methionine (1-fold degenerate - start)
    'AUG': 'M',
    # Valine (4-fold degenerate)
    'GUU': 'V', 'GUC': 'V', 'GUA': 'V', 'GUG': 'V',
    # Serine (6-fold degenerate)
    'UCU': 'S', 'UCC': 'S', 'UCA': 'S', 'UCG': 'S', 'AGU': 'S', 'AGC': 'S',
    # Proline (4-fold degenerate)
    'CCU': 'P', 'CCC': 'P', 'CCA': 'P', 'CCG': 'P',
    # Threonine (4-fold degenerate)
    'ACU': 'T', 'ACC': 'T', 'ACA': 'T', 'ACG': 'T',
    # Alanine (4-fold degenerate)
    'GCU': 'A', 'GCC': 'A', 'GCA': 'A', 'GCG': 'A',
    # Tyrosine (2-fold degenerate)
    'UAU': 'Y', 'UAC': 'Y',
    # Histidine (2-fold degenerate)
    'CAU': 'H', 'CAC': 'H',
    # Glutamine (2-fold degenerate)
    'CAA': 'Q', 'CAG': 'Q',
    # Asparagine (2-fold degenerate)
    'AAU': 'N', 'AAC': 'N',
    # Lysine (2-fold degenerate)
    'AAA': 'K', 'AAG': 'K',
    # Aspartic acid (2-fold degenerate)
    'GAU': 'D', 'GAC': 'D',
    # Glutamic acid (2-fold degenerate)
    'GAA': 'E', 'GAG': 'E',
    # Cysteine (2-fold degenerate)
    'UGU': 'C', 'UGC': 'C',
    # Tryptophan (1-fold degenerate)
    'UGG': 'W',
    # Arginine (6-fold degenerate)
    'CGU': 'R', 'CGC': 'R', 'CGA': 'R', 'CGG': 'R', 'AGA': 'R', 'AGG': 'R',
    # Glycine (4-fold degenerate)
    'GGU': 'G', 'GGC': 'G', 'GGA': 'G', 'GGG': 'G',
    # Stop codons (3-fold)
    'UAA': '*', 'UAG': '*', 'UGA': '*'
}

# Degeneracy mapping (number of codons per amino acid)
DEGENERACY = {
    'F': 2, 'L': 6, 'I': 3, 'M': 1, 'V': 4, 'S': 6, 'P': 4, 'T': 4, 'A': 4,
    'Y': 2, 'H': 2, 'Q': 2, 'N': 2, 'K': 2, 'D': 2, 'E': 2, 'C': 2, 'W': 1,
    'R': 6, 'G': 4, '*': 3
}

# ============================================================================
# Codon Efficiency Functional (CodonOTOM)
# ============================================================================

@dataclass
class CodonFeatures:
    """Local feature signals for a codon."""
    rho: float   # triplet consistency [0,1]
    q: float     # conservation [0,1]
    tau: float   # translation efficiency [0,1]
    H: float     # entropy [0,1]
    eps: float   # mutation penalty [0,1]

@dataclass
class CodonWeights:
    """Weight parameters for codon efficiency."""
    w_rho: float
    w_q: float
    w_tau: float
    w_H: float
    w_eps: float
    lambda_: float
    C0: float

def phi_codon(w: CodonWeights, f: CodonFeatures, codon: str) -> float:
    """
    Codon efficiency functional Φ_codon(c).
    
    Φ_codon(c) = (w_ρ·ρ̂ + w_q·q̂ + w_τ·τ̂ - w_H·Ĥ - w_ε·ε̂) / (ln 64 + λ ln d(c) + C_0)
    """
    aa = GENETIC_CODE.get(codon, 'X')
    d = DEGENERACY.get(aa, 1)
    
    numerator = (
        w.w_rho * f.rho +
        w.w_q * f.q +
        w.w_tau * f.tau -
        w.w_H * f.H -
        w.w_eps * f.eps
    )
    
    denominator = np.log(64) + w.lambda_ * np.log(d) + w.C0
    
    return numerator / denominator

# ============================================================================
# Peptide-Level Properties (Simplified PeptideMoE)
# ============================================================================

@dataclass
class PeptideState:
    """Simplified peptide state for toy run."""
    sequence: str  # amino acid sequence
    structural_coherence: float  # [0,1]
    free_energy: float  # kcal/mol

def peptide_efficiency(peptide: PeptideState, c0: float = 1.0) -> float:
    """
    Peptide efficiency (simplified from PeptideMoE).
    
    Φ_peptide = structural_coherence / (free_energy + c0)
    """
    return peptide.structural_coherence / (peptide.free_energy + c0)

# ============================================================================
# Codon RL over Synonymous Choices
# ============================================================================

def get_synonymous_codons(codon: str) -> List[str]:
    """Get all synonymous codons for a given codon."""
    aa = GENETIC_CODE.get(codon, 'X')
    if aa == 'X':
        return [codon]
    return [c for c, a in GENETIC_CODE.items() if a == aa]

def codon_rl_step(current_codon: str, w: CodonWeights, f: CodonFeatures) -> Tuple[str, float]:
    """
    RL step: select best synonymous codon based on Φ_codon.
    
    Returns: (best_codon, delta_efficiency)
    """
    current_phi = phi_codon(w, f, current_codon)
    
    synonymous = get_synonymous_codons(current_codon)
    best_codon = current_codon
    best_phi = current_phi
    
    for codon in synonymous:
        phi = phi_codon(w, f, codon)
        if phi > best_phi:
            best_codon = codon
            best_phi = phi
    
    delta_phi = best_phi - current_phi
    return best_codon, delta_phi

# ============================================================================
# Amino Acid → Peptide Expert Field
# ============================================================================

def amino_acid_to_expert_field(aa: str) -> Dict[str, float]:
    """
    Map amino acid to simplified expert field properties.
    
    This represents the amino-acid-implied peptide expert field
    that influences peptide-level properties.
    """
    # Simplified physicochemical properties
    properties = {
        'hydrophobicity': 0.0,
        'charge': 0.0,
        'size': 0.0,
        'flexibility': 0.0
    }
    
    # Hydrophobicity (Kyte-Doolittle scale, normalized)
    hydrophobicity = {
        'I': 0.9, 'V': 0.8, 'L': 0.8, 'F': 0.7, 'C': 0.6,
        'M': 0.5, 'A': 0.4, 'G': 0.3, 'T': 0.2, 'S': 0.2,
        'W': 0.2, 'Y': 0.1, 'P': 0.0, 'H': 0.0, 'E': -0.1,
        'Q': -0.1, 'D': -0.2, 'N': -0.2, 'K': -0.3, 'R': -0.3
    }
    
    # Charge at pH 7
    charge = {
        'R': 1.0, 'K': 1.0, 'H': 0.5, 'D': -1.0, 'E': -1.0,
        'C': 0.0, 'M': 0.0, 'F': 0.0, 'I': 0.0, 'L': 0.0,
        'V': 0.0, 'W': 0.0, 'Y': 0.0, 'A': 0.0, 'G': 0.0,
        'T': 0.0, 'S': 0.0, 'P': 0.0, 'Q': 0.0, 'N': 0.0
    }
    
    # Size (normalized)
    size = {
        'W': 1.0, 'R': 0.9, 'Y': 0.8, 'F': 0.8, 'K': 0.7,
        'E': 0.7, 'Q': 0.7, 'M': 0.6, 'H': 0.6, 'L': 0.6,
        'I': 0.6, 'D': 0.5, 'N': 0.5, 'T': 0.5, 'V': 0.5,
        'S': 0.4, 'C': 0.4, 'A': 0.3, 'G': 0.2, 'P': 0.5
    }
    
    # Flexibility (normalized)
    flexibility = {
        'G': 1.0, 'S': 0.9, 'A': 0.8, 'P': 0.7, 'D': 0.6,
        'N': 0.6, 'T': 0.5, 'K': 0.5, 'E': 0.5, 'Q': 0.5,
        'R': 0.4, 'H': 0.4, 'M': 0.4, 'L': 0.4, 'I': 0.3,
        'V': 0.3, 'F': 0.3, 'Y': 0.3, 'W': 0.2, 'C': 0.2
    }
    
    properties['hydrophobicity'] = hydrophobicity.get(aa, 0.0)
    properties['charge'] = charge.get(aa, 0.0)
    properties['size'] = size.get(aa, 0.0)
    properties['flexibility'] = flexibility.get(aa, 0.0)
    
    return properties

# ============================================================================
# CDS-Level Scoring
# ============================================================================

def cds_to_peptide(cds_sequence: str) -> str:
    """Translate CDS (codon sequence) to peptide."""
    peptide = []
    for i in range(0, len(cds_sequence), 3):
        codon = cds_sequence[i:i+3]
        aa = GENETIC_CODE.get(codon, 'X')
        if aa == '*':
            break  # Stop codon
        peptide.append(aa)
    return ''.join(peptide)

def compute_peptide_properties(peptide: str) -> PeptideState:
    """
    Compute peptide-level properties from amino acid sequence.
    
    This aggregates the amino acid expert fields to produce
    peptide-level structural_coherence and free_energy.
    """
    if not peptide:
        return PeptideState("", 0.0, 100.0)
    
    # Aggregate amino acid properties
    total_hydro = 0.0
    total_charge = 0.0
    total_size = 0.0
    total_flex = 0.0
    
    for aa in peptide:
        props = amino_acid_to_expert_field(aa)
        total_hydro += props['hydrophobicity']
        total_charge += props['charge']
        total_size += props['size']
        total_flex += props['flexibility']
    
    n = len(peptide)
    avg_hydro = total_hydro / n
    avg_charge = abs(total_charge) / n  # Magnitude of charge
    avg_size = total_size / n
    avg_flex = total_flex / n
    
    # Simplified peptide efficiency model
    # Structural coherence: higher with balanced hydrophobicity and flexibility
    structural_coherence = 0.5 * (1.0 - abs(avg_hydro)) + 0.3 * avg_flex + 0.2 * (1.0 - avg_charge)
    structural_coherence = np.clip(structural_coherence, 0.0, 1.0)
    
    # Free energy: higher with unbalanced properties
    free_energy = 10.0 + 5.0 * abs(avg_hydro) + 3.0 * avg_charge + 2.0 * avg_size
    
    return PeptideState(peptide, structural_coherence, free_energy)

# ============================================================================
# Toy Run
# ============================================================================

def run_toy_simulation():
    """Run toy simulation of codon RL coupling with peptide scoring."""
    
    print("=" * 70)
    print("CODON-PEPTIDE COUPLING TOY RUN")
    print("=" * 70)
    
    # Toy parameters
    w = CodonWeights(
        w_rho=0.3,
        w_q=0.25,
        w_tau=0.25,
        w_H=0.1,
        w_eps=0.1,
        lambda_=0.5,
        C0=1.0
    )
    
    # Initial CDS sequence (toy example)
    initial_cds = "AUGUUUUAACUUUGGAAAUU"  # MFLFGN (partial)
    
    print(f"\nInitial CDS: {initial_cds}")
    print(f"Initial peptide: {cds_to_peptide(initial_cds)}")
    
    # Compute initial peptide properties
    initial_peptide = compute_peptide_properties(cds_to_peptide(initial_cds))
    initial_peptide_phi = peptide_efficiency(initial_peptide)
    
    print(f"\nInitial peptide properties:")
    print(f"  Structural coherence: {initial_peptide.structural_coherence:.3f}")
    print(f"  Free energy: {initial_peptide.free_energy:.3f} kcal/mol")
    print(f"  Peptide efficiency: {initial_peptide_phi:.3f}")
    
    # Codon RL optimization
    print("\n" + "=" * 70)
    print("CODON RL OPTIMIZATION")
    print("=" * 70)
    
    optimized_cds = initial_cds
    total_delta_phi_codon = 0.0
    
    for i in range(0, len(initial_cds), 3):
        codon = initial_cds[i:i+3]
        if len(codon) < 3:
            break
        
        # Toy features (would be computed from actual data)
        f = CodonFeatures(
            rho=0.7,  # high triplet consistency
            q=0.6,    # moderate conservation
            tau=0.8,  # high translation efficiency
            H=0.3,    # low entropy
            eps=0.1   # low mutation penalty
        )
        
        best_codon, delta_phi = codon_rl_step(codon, w, f)
        
        if best_codon != codon:
            print(f"  Codon {i//3+1}: {codon} → {best_codon} (ΔΦ_codon = {delta_phi:+.4f})")
            optimized_cds = optimized_cds[:i] + best_codon + optimized_cds[i+3:]
            total_delta_phi_codon += delta_phi
        else:
            print(f"  Codon {i//3+1}: {codon} (already optimal)")
    
    print(f"\nTotal ΔΦ_codon improvement: {total_delta_phi_codon:+.4f}")
    
    # Compute optimized peptide properties
    optimized_peptide = compute_peptide_properties(cds_to_peptide(optimized_cds))
    optimized_peptide_phi = peptide_efficiency(optimized_peptide)
    
    print("\n" + "=" * 70)
    print("OPTIMIZED PEPTIDE PROPERTIES")
    print("=" * 70)
    
    print(f"\nOptimized CDS: {optimized_cds}")
    print(f"Optimized peptide: {cds_to_peptide(optimized_cds)}")
    print(f"\nOptimized peptide properties:")
    print(f"  Structural coherence: {optimized_peptide.structural_coherence:.3f}")
    print(f"  Free energy: {optimized_peptide.free_energy:.3f} kcal/mol")
    print(f"  Peptide efficiency: {optimized_peptide_phi:.3f}")
    
    # Compare
    peptide_delta_phi = optimized_peptide_phi - initial_peptide_phi
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    print(f"\nCodon-level improvement: ΔΦ_codon = {total_delta_phi_codon:+.4f}")
    print(f"Peptide-level improvement: ΔΦ_peptide = {peptide_delta_phi:+.4f}")
    
    if peptide_delta_phi > 0:
        print(f"\n✅ Codon optimization improved peptide efficiency by {peptide_delta_phi:.2%}")
    elif peptide_delta_phi < 0:
        print(f"\n⚠️  Codon optimization decreased peptide efficiency by {abs(peptide_delta_phi):.2%}")
    else:
        print(f"\n→ Codon optimization had no effect on peptide efficiency")
    
    return {
        'initial_cds': initial_cds,
        'optimized_cds': optimized_cds,
        'initial_peptide_phi': initial_peptide_phi,
        'optimized_peptide_phi': optimized_peptide_phi,
        'codon_delta_phi': total_delta_phi_codon,
        'peptide_delta_phi': peptide_delta_phi
    }

def visualize_results(results: Dict):
    """Visualize the toy run results."""
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Codon-Peptide Coupling Toy Run Results', fontsize=16)
    
    # Plot 1: Efficiency comparison
    ax1 = axes[0, 0]
    efficiencies = [results['initial_peptide_phi'], results['optimized_peptide_phi']]
    labels = ['Initial', 'Optimized']
    colors = ['lightcoral', 'lightblue']
    ax1.bar(labels, efficiencies, color=colors)
    ax1.set_ylabel('Peptide Efficiency Φ_peptide')
    ax1.set_title('Peptide Efficiency Comparison')
    ax1.set_ylim([0, max(efficiencies) * 1.2])
    for i, v in enumerate(efficiencies):
        ax1.text(i, v + 0.01, f'{v:.3f}', ha='center')
    
    # Plot 2: Delta efficiency
    ax2 = axes[0, 1]
    deltas = [results['codon_delta_phi'], results['peptide_delta_phi']]
    labels = ['Codon Level', 'Peptide Level']
    colors = ['green' if d > 0 else 'red' for d in deltas]
    ax2.bar(labels, deltas, color=colors)
    ax2.set_ylabel('ΔΦ')
    ax2.set_title('Efficiency Improvement')
    ax2.axhline(y=0, color='black', linestyle='--', linewidth=0.5)
    for i, v in enumerate(deltas):
        ax2.text(i, v + (0.01 if v > 0 else -0.02), f'{v:+.4f}', ha='center')
    
    # Plot 3: Codon optimization steps
    ax3 = axes[1, 0]
    initial_peptide = cds_to_peptide(results['initial_cds'])
    optimized_peptide = cds_to_peptide(results['optimized_cds'])
    
    # Show amino acid sequence
    ax3.text(0.5, 0.7, f'Initial: {initial_peptide}', ha='center', fontsize=12, 
             bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.5))
    ax3.text(0.5, 0.3, f'Optimized: {optimized_peptide}', ha='center', fontsize=12,
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
    ax3.set_xlim([0, 1])
    ax3.set_ylim([0, 1])
    ax3.axis('off')
    ax3.set_title('Amino Acid Sequences')
    
    # Plot 4: Coupling diagram
    ax4 = axes[1, 1]
    ax4.text(0.5, 0.8, 'Codon RL', ha='center', fontsize=10, fontweight='bold',
             bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))
    ax4.text(0.5, 0.6, '↓', ha='center', fontsize=20)
    ax4.text(0.5, 0.4, 'Codon → AA Translation', ha='center', fontsize=10, fontweight='bold',
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.7))
    ax4.text(0.5, 0.2, '↓', ha='center', fontsize=20)
    ax4.text(0.5, 0.0, 'Peptide Scoring', ha='center', fontsize=10, fontweight='bold',
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
    ax4.set_xlim([0, 1])
    ax4.set_ylim([-0.1, 0.9])
    ax4.axis('off')
    ax4.set_title('Coupling Flow')
    
    plt.tight_layout()
    
    # Save figure
    output_file = '/home/allaun/Documents/Research Stack/data/codon_peptide_coupling_toy.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\nVisualization saved to: {output_file}")
    
    plt.show()

if __name__ == "__main__":
    results = run_toy_simulation()
    visualize_results(results)
