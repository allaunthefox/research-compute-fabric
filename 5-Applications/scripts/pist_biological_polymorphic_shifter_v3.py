#!/usr/bin/env python3
"""
PIST Biological Polymorphic Shifter v3.0
=========================================
Hyperdimensional biological manifold compressor where every encoding modality
is a polymorphic shifter that transforms manifold state. ANY combination with
ANY combination is allowed as long as it increases fitness (compression × computation × stability).

Synthetic DNA Alphabets:
  Hachimoji (8-letter), AEGIS (12+ letter), Hydrophobic Pairs, Shape-Complementary Pairs
  Backbone XNAs: PNA, LNA, TNA, GNA, HNA, CeNA, FANA, Morpholino, Spiegelmer

RNA Processing:
  Transcription, Translation (codon→peptide), Splicing, Editing, Interference (siRNA, miRNA, piRNA)
  lncRNA regulation, Riboswitches, Ribozymes

Prion/Epigenetic:
  Self-propagating conformational shift, Histone modification, DNA methylation, Chromatin remodeling

Neuronal Encoding:
  Spike timing, STDP plasticity, Rate coding, Burst coding, Oscillatory phase coding

Mycelial/Fungal:
  Hyphal network routing, Spore dispersal, Symbiotic exchange, Quorum sensing

Cellular Automata:
  Wireworld, Game of Life, Rule 30, Rule 110 (as discrete state machine shifters)

n() Notation: Every shifter has an exponential amplification factor.
  n(shifter) = base^depth where depth = how many times the shifter has been applied.
  This represents combinatorial explosion of encoding capacity.

Usage:
  python3 pist_biological_polymorphic_shifter_v3.py
"""

import struct
import math
import json
import time
import random
import sys
from collections import Counter, defaultdict
from heapq import heappush, heappop
from itertools import product, combinations, chain
from functools import lru_cache
from copy import deepcopy

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

PHI = (1 + 5**0.5) / 2  # golden ratio ≈ 1.618
E = math.e
PI = math.pi

# Prime numbers for Galois field operations
GALOIS_PRIME = 251  # largest prime ≤ 255
GALOIS_PRIMITIVE = 86  # primitive element mod 251

# ── Synthetic Genetic Alphabets ─────────────────────────────────────────────
# Each letter maps to a bit pattern

HACHIMOJI_ALPHABET = {
    # Natural bases
    'A': 0b0000,  # Adenine
    'T': 0b0001,  # Thymine
    'C': 0b0010,  # Cytosine
    'G': 0b0011,  # Guanine
    # Synthetic bases
    'Z': 0b0100,  # 6-amino-5-nitropyridin-2-one (pairs with P)
    'P': 0b0101,  # 2-aminoimidazo[1,2-a][1,3,5]triazin-4(8H)-one (pairs with Z)
    'S': 0b0110,  # 3-methyl-6-amino-5-(1-propynyl)-pyrimidin-2-one (pairs with B)
    'B': 0b0111,  # 6-amino-9H-purin-2-ol (pairs with S)
}
# 8 letters = 3 bits per letter, 2.67x density vs binary

AEGIS_ALPHABET = {
    **HACHIMOJI_ALPHABET,
    'V': 0b1000,  # pairs with J
    'J': 0b1001,  # pairs with V
    'K': 0b1010,  # pairs with X
    'X': 0b1011,  # pairs with K
}
# 12 letters = ~3.58 bits per letter

ROMESBERG_ALPHABET = {
    'NaM': 0b00,    # naphthalene derivative
    '5SICS': 0b01,  # pairs with NaM (hydrophobic)
    'TPT3': 0b10,   # optimized partner for NaM
    'dNaM': 0b11,   # alternative NaM variant
}
# 4 hydrophobic letters = 2 bits per letter

HIRAO_ALPHABET = {
    'Ds': 0b00,   # 7-(2-thienyl)-imidazo[4,5-b]pyridine
    'Px': 0b01,   # 2-nitro-4-propynylpyrrole
    'Pa': 0b10,   # pyrrole-2-carbaldehyde (older)
    'dK': 0b11,   # alternative shape-complementary
}
# 4 shape-complementary letters = 2 bits per letter

# Collection of all known synthetic DNA letters
ALL_SYNTHETIC_BASES = {
    # Natural
    'A', 'T', 'C', 'G', 'U',
    # Hachimoji
    'Z', 'P', 'S', 'B',
    # AEGIS extended
    'V', 'J', 'K', 'X',
    'isoC', 'isoG',
    # Romesberg hydrophobic
    'NaM', '5SICS', 'TPT3', 'dNaM',
    # Hirao shape-complementary
    'Ds', 'Px', 'Pa', 'dK',
}

BASE_PAIRS = {
    # Natural Watson-Crick
    'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C', 'U': 'A',
    # Hachimoji
    'Z': 'P', 'P': 'Z', 'S': 'B', 'B': 'S',
    # AEGIS
    'V': 'J', 'J': 'V', 'K': 'X', 'X': 'K',
    'isoC': 'isoG', 'isoG': 'isoC',
    # Romesberg hydrophobic
    'NaM': '5SICS', '5SICS': 'NaM', 'TPT3': 'dNaM', 'dNaM': 'TPT3',
    # Hirao shape
    'Ds': 'Px', 'Px': 'Ds', 'Pa': 'dK', 'dK': 'Pa',
}

# ── Codon Table (Natural + Expanded) ───────────────────────────────────────
STANDARD_CODON_TABLE = {
    'UUU': 'F', 'UUC': 'F', 'UUA': 'L', 'UUG': 'L',
    'CUU': 'L', 'CUC': 'L', 'CUA': 'L', 'CUG': 'L',
    'AUU': 'I', 'AUC': 'I', 'AUA': 'I', 'AUG': 'M',
    'GUU': 'V', 'GUC': 'V', 'GUA': 'V', 'GUG': 'V',
    'UCU': 'S', 'UCC': 'S', 'UCA': 'S', 'UCG': 'S',
    'CCU': 'P', 'CCC': 'P', 'CCA': 'P', 'CCG': 'P',
    'ACU': 'T', 'ACC': 'T', 'ACA': 'T', 'ACG': 'T',
    'GCU': 'A', 'GCC': 'A', 'GCA': 'A', 'GCG': 'A',
    'UAU': 'Y', 'UAC': 'Y', 'UAA': '*', 'UAG': '*',
    'CAU': 'H', 'CAC': 'H', 'CAA': 'Q', 'CAG': 'Q',
    'AAU': 'N', 'AAC': 'N', 'AAA': 'K', 'AAG': 'K',
    'GAU': 'D', 'GAC': 'D', 'GAA': 'E', 'GAG': 'E',
    'UGU': 'C', 'UGC': 'C', 'UGA': '*', 'UGG': 'W',
    'CGU': 'R', 'CGC': 'R', 'CGA': 'R', 'CGG': 'R',
    'AGU': 'S', 'AGC': 'S', 'AGA': 'R', 'AGG': 'R',
    'GGU': 'G', 'GGC': 'G', 'GGA': 'G', 'GGG': 'G',
}

# Reverse: amino acid → codons
AMINO_CODONS = defaultdict(list)
for codon, aa in STANDARD_CODON_TABLE.items():
    AMINO_CODONS[aa].append(codon)

AMINO_ACIDS = list(set(STANDARD_CODON_TABLE.values()))

# ═══════════════════════════════════════════════════════════════════════════════
# n() EXPONENTIAL AMPLIFICATION SYSTEM
# ───────────────────────────────────────────────────────────────────────────────
# n(shifter, depth) = base^depth where:
#   - base = information capacity of the shifter (bits per symbol)
#   - depth = how many nested/recursive applications of the shifter
#   - n() represents the combinatorial explosion factor
# ═══════════════════════════════════════════════════════════════════════════════

class NExponent:
    """n() exponential amplification system for shifter encoding capacity."""

    SHIFTER_BASES = {
        # ── Synthetic DNA Alphabets ──
        'Hachimoji': 3.0,     # 8 letters ≈ 3 bits/letter → 2^3 = 8 states
        'AEGIS': 3.585,       # 12 letters ≈ 3.585 bits/letter
        'Romesberg': 2.0,     # 4 hydrophobic pairs ≈ 2 bits/letter
        'Hirao': 2.0,         # 4 shape-complementary ≈ 2 bits/letter
        'NaturalDNA': 2.0,    # 4 natural bases ≈ 2 bits/base
        'RNA': 2.0,           # 4 bases (AUCG) ≈ 2 bits/base

        # ── Backbone XNAs (same letters, different structural properties) ──
        'PNA': 2.0,           # Peptide backbone (neutral, tighter binding)
        'LNA': 2.0,           # Locked ribose (thermally stable)
        'TNA': 2.0,           # Threose backbone (pre-RNA)
        'GNA': 2.0,           # Glycol backbone (simpler)
        'HNA': 2.0,           # Hexitol backbone (RNA binding)
        'CeNA': 2.0,          # Cyclohexenyl backbone
        'FANA': 2.0,          # Fluoro-arabino (enzyme resistant)
        'Morpholino': 2.0,    # Morpholine ring (therapeutic)
        'Spiegelmer': 2.0,    # L-DNA mirror image (non-degradable)
        'Boranophosphate': 2.0,  # Borane backbone (nuclease resistant)
        'Phosphorothioate': 2.0, # Sulfur backbone (therapeutic)

        # ── RNA Processing ──
        'Transcription': 4.0,  # DNA→RNA (amplification)
        'Translation': 3.0,    # RNA→Peptide (codon→aa, 3:1 compression)
        'Splicing': 2.5,       # Intron removal (compression)
        'Editing': 2.0,        # Base editing (A→I, C→U)
        'miRNA': 3.0,          # MicroRNA regulation (gene silencing)
        'siRNA': 3.0,          # Small interfering RNA (targeted)
        'piRNA': 3.0,          # Piwi-interacting (transposon defense)
        'lncRNA': 2.5,         # Long non-coding (scaffold)
        'Riboswitch': 2.0,     # Metabolite-sensing RNA
        'Ribozyme': 2.0,       # Catalytic RNA
        'tRNA': 3.0,           # Transfer RNA (adaptor)
        'rRNA': 2.0,           # Ribosomal RNA (structural)

        # ── Prion/Epigenetic ──
        'Prion': 4.0,          # Self-propagating conformational (exponential!)
        'HistoneMod': 2.5,     # Histone acetylation/methylation
        'DNAmethylation': 2.0, # CpG methylation
        'Chromatin': 3.0,      # Chromatin remodeling (domain scale)
        'lncRNA_epi': 2.5,     # lncRNA-directed epigenetic modification

        # ── Neuronal Encoding ──
        'SpikeTiming': 4.0,    # Precise spike timing (high bandwidth)
        'STDP': 3.0,           # Spike-timing-dependent plasticity
        'RateCoding': 2.5,     # Firing rate encoding
        'BurstCoding': 3.5,    # Burst pattern encoding
        'PhaseCoding': 3.0,    # Oscillatory phase encoding
        'PopulationCoding': 4.0, # Population vector encoding
        'SynapticWeight': 3.0, # Weight-based memory
        'DendriticComp': 3.5,  # Dendritic computation

        # ── Mycelial/Fungal ──
        'HyphalNet': 3.5,      # Hyphal network routing
        'SporeDispersal': 3.0, # Spore-based information dispersal
        'Symbiotic': 2.5,      # Symbiotic exchange (mycorrhizal)
        'QuorumSensing': 2.0,  # Density-based signaling
        'FungalWave': 3.0,     # Calcium wave propagation
        'MycelialFusion': 3.5, # Hyphal anastomosis (network merging)

        # ── Chaotic Maps ──
        'LogisticMap': 2.5,    # x_{n+1} = r·x_n·(1-x_n)
        'HenonMap': 3.0,       # 2D chaotic attractor
        'Lorenz': 3.5,         # 3D chaotic system
        'ArnoldCat': 2.0,      # Torus automorphism (area-preserving)
        'ChuaCircuit': 3.5,    # Double scroll attractor
        'ChenMap': 3.0,        # Chen's hyperchaotic system

        # ── Galois Ring Algebra ──
        'GaloisRing': 4.0,     # GF(p^k) algebraic operations
        'SBox': 3.0,           # Substitution box (non-linear)
        'NLFSR': 2.5,          # Non-linear feedback shift register

        # ── Compressed Sensing ──
        'CompressedSensing': 4.0,  # Sub-Nyquist sampling
        'SparseRecovery': 3.5,     # L1 minimization

        # ── Cellular Automata ──
        'Wireworld': 2.0,      # Wireworld CA (electronics)
        'GameOfLife': 2.0,     # Conway's Game of Life
        'Rule30': 2.0,         # Rule 30 (chaotic)
        'Rule110': 2.0,        # Rule 110 (Turing complete)
        'ElementaryCA': 2.0,   # General elementary CA

        # ── PIST Geometry (base) ──
        'PIST': 2.5,           # PIST shell coordinates
        'PISTMirror': 2.0,     # Mirror involution
        'PISTResonance': 2.5,  # Mass resonance equivalence

        # ── Arithmetic ──
        'DeltaGCL': 2.0,       # Delta encoding
        'RunLength': 2.0,      # RLE
        'Huffman': 2.0,        # Huffman coding
        'ArithmeticCoding': 2.5, # Arithmetic coding
    }

    @staticmethod
    def n(shifter_name: str, depth: int = 1) -> float:
        """n(shifter) = base^depth. Exponential amplification factor."""
        base = NExponent.SHIFTER_BASES.get(shifter_name, 2.0)
        return base ** depth

    @staticmethod
    def n_combined(shifters: list, depths: list = None) -> float:
        """n(shifter1, shifter2, ...) = product of n(shifter_i).

        The combined exponential amplification is the product of all bases,
        representing the combinatorial explosion of nested encoding layers.
        """
        if depths is None:
            depths = [1] * len(shifters)
        combined = 1.0
        for name, depth in zip(shifters, depths):
            combined *= NExponent.n(name, depth)
        return combined

    @staticmethod
    def log_n(combined_factor: float) -> float:
        """log2 of n() factor — effective bits per symbol."""
        return math.log2(max(1.0, combined_factor))

    @staticmethod
    def format_n(shifter_name: str, depth: int = 1) -> str:
        """Format n(shifter) for display."""
        val = NExponent.n(shifter_name, depth)
        return f"n({shifter_name}) = {val:.3f} (base^{depth})"


# ═══════════════════════════════════════════════════════════════════════════════
# PIST GEOMETRY (base coordinate system)
# ═══════════════════════════════════════════════════════════════════════════════

def pist_encode(n: int) -> tuple:
    """Encode n into (shell, offset). Byte range 0-255 → shells 0-15."""
    k = int(math.isqrt(n))
    t = n - k * k
    return (k, t)

def pist_decode(k: int, t: int) -> int:
    """Decode PIST coordinates back to integer."""
    return k * k + t

def pist_mass(k: int, t: int) -> int:
    """PIST mass = t·(2k+1-t). Zero at perfect squares (grounded)."""
    return t * (2 * k + 1 - t)

def pist_mirror(k: int, t: int) -> tuple:
    """Mirror involution preserves mass within shell."""
    return (k, 2 * k + 1 - t)

def pist_normalized_tension(k: int, t: int) -> float:
    """ρ = t/(2k+1) ∈ [0,1)."""
    width = 2 * k + 1
    return t / width if width > 0 else 0.0

def pist_phase_str(k: int, t: int) -> str:
    """Phase classification."""
    return 'grounded' if pist_mass(k, t) == 0 else 'seismic'

def intrinsic_load(data: bytes) -> float:
    """L_I Shannon entropy in bits per byte."""
    if not data:
        return 0.0
    c = Counter(data)
    n = len(data)
    return -sum((cnt / n) * math.log2(cnt / n) for cnt in c.values())


# ═══════════════════════════════════════════════════════════════════════════════
# SHIFTER BASE CLASS — Any encoding modality
# ───────────────────────────────────────────────────────────────────────────────
# A shifter takes manifold state as input and returns transformed manifold state.
# Each shifter has:
#   - encode(state) → transformed state (compression/encoding pass)
#   - decode(state) → inverse (reconstruction pass)
#   - fitness(state) → compression_ratio × computation_metric × stability
#   - n_factor → exponential amplification factor (via NExponent)
# ═══════════════════════════════════════════════════════════════════════════════

class ManifoldState:
    """
    The fundamental state of the biological manifold.
    Can be represented in multiple encoding regimes simultaneously.

    Attributes:
        raw_bytes: The original byte data
        pist_coords: List of (shell, offset, mass, tension) for each byte
        shifter_chain: List of (shifter_name, depth) applied so far
        encoded: Current encoded representation (bytes)
        n_factor: Combined n() exponential amplification factor
        fitness_score: Current fitness (compression × computation × stability)
        entropy: Current Shannon entropy of encoded state
        regime: Current encoding regime (e.g., 'hachimoji', 'prion', 'spike')
    """

    def __init__(self, data: bytes = None):
        self.raw_bytes = data or b''
        self.pist_coords = []
        self.shifter_chain = []
        self.encoded = data or b''
        self.n_factor = 1.0
        self.fitness_score = 0.0
        self.entropy = intrinsic_load(self.encoded)
        self.regime = 'raw'
        self.metadata = {}

        if data:
            self._compute_pist()

    def _compute_pist(self):
        """Compute PIST coordinates for all bytes."""
        self.pist_coords = []
        for b in self.raw_bytes:
            k, t = pist_encode(b)
            m = pist_mass(k, t)
            tens = pist_normalized_tension(k, t)
            self.pist_coords.append({
                'byte': b, 'shell': k, 'offset': t,
                'mass': m, 'tension': tens,
                'phase': 'grounded' if m == 0 else 'seismic'
            })

    def update_encoded(self, new_encoded: bytes, shifter_name: str, depth: int = 1):
        """Apply a shifter transformation and update state."""
        self.encoded = new_encoded
        self.shifter_chain.append((shifter_name, depth))
        self.entropy = intrinsic_load(new_encoded)

        # Update combined n() factor
        self.n_factor *= NExponent.n(shifter_name, depth)
        self.regime = shifter_name

    def compute_fitness(self) -> float:
        """
        fitness = compression_ratio × computation_efficiency × stability

        compression_ratio: raw_size / encoded_size
        computation_efficiency: 1.0 / (1.0 + entropy)  — lower entropy = more efficient
        stability: 1.0 - abs(0.5 - tension_variance)  — moderate tension = stable

        Returns a float in [0, ∞). Higher is better.
        """
        if not self.raw_bytes or not self.encoded:
            return 0.0

        # Compression ratio
        ratio = len(self.raw_bytes) / max(1, len(self.encoded))

        # Computation efficiency (inverse of entropy cost)
        comp_eff = 1.0 / (1.0 + self.entropy)

        # Stability: measure of PIST tension distribution
        if self.pist_coords:
            tensions = [c['tension'] for c in self.pist_coords]
            if tensions:
                mean_t = sum(tensions) / len(tensions)
                var_t = sum((t - mean_t)**2 for t in tensions) / len(tensions)
                # Ideal: moderate variance (not all grounded, not all seismic)
                stability = 1.0 - min(1.0, abs(0.25 - var_t) * 2)
            else:
                stability = 0.5
        else:
            stability = 0.5

        # n() amplification bonus
        n_bonus = math.log2(max(1.0, self.n_factor)) / 8.0  # normalize to [0, ~1]

        return ratio * comp_eff * (stability + 0.5 * n_bonus)


class Shifter:
    """
    Base class for all encoding shifters.
    A shifter transforms manifold state in some encoding regime.
    """

    name = "BaseShifter"

    @classmethod
    def encode(cls, state: ManifoldState) -> ManifoldState:
        """Encode the manifold state. Returns new state with encoded representation."""
        raise NotImplementedError

    @classmethod
    def decode(cls, state: ManifoldState) -> ManifoldState:
        """Inverse operation. Returns decoded state."""
        raise NotImplementedError

    @classmethod
    def n_factor(cls, depth: int = 1) -> float:
        """n(shifter) exponential amplification factor."""
        return NExponent.n(cls.name, depth)

    @staticmethod
    def chain(shifters: list, state: ManifoldState, direction: str = 'encode') -> ManifoldState:
        """
        Chain multiple shifters in sequence.
        ANY combination of ANY shifters is allowed.
        direction: 'encode' (compress) or 'decode' (reconstruct)
        """
        current = state
        if direction == 'encode':
            for shifter_cls in shifters:
                current = shifter_cls.encode(current)
        else:
            for shifter_cls in reversed(shifters):
                current = shifter_cls.decode(current)
        return current
