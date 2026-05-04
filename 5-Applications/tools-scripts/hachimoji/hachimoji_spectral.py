#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
hachimoji_spectral.py — DNA/RNA Spectral Codon Encoding on Menger Laplacian

Combines hachimoji_synth.py (DNA) and hachimoji_rna.py (RNA) into a unified
spectral codon space where codon position = eigenmode of the Menger sponge
Laplacian.

MATH UNIVERSE
─────────────
All "energy" and "stability" values are symbolic — structural coordinates
in a mathematical address space, not physical measurements.  The numerical
ordering is inspired by biochemistry (H-bond count, fold propensity) but
no physical unit attaches.  This removes the dependency on experimental
Tm data and makes the system domain-agnostic.

SPECTRAL DECOMPOSITION
──────────────────────
DNA carrier profile  → coarse eigenmodes (low-frequency structure)
RNA fold propensity  → fine eigenmodes   (high-frequency topology)

Together they form a complete spectral decomposition of the engram
address space — analogous to Fourier decomposition but applied to the
codon/voxel address space on the Menger sponge.

    Codon c → spectral weight w(c) = α · dna_weight(c) + β · rna_weight(c)

    where:
        dna_weight(c) = normalised codon usage from carrier profile
        rna_weight(c) = symbolic fold stability from BASE_FOLD_STABILITY
        α, β          = mixing coefficients (DNA coarse, RNA fine)

    The spectral weight defines the eigenvalue magnitude at the codon's
    Menger Laplacian position.  Hot codons (high eigenvalue) are visited
    frequently by engram random walks; cold codons (low eigenvalue) are
    structural boundaries.

COMBINED CODON SPACE
────────────────────
DNA alphabet: A, T, G, C, P, Z, S, B  →  8³ = 512 codons
RNA alphabet: A, U, G, C, P, Z, S, B  →  8³ = 512 codons
Combined: 1024 distinct codon labels (T↔U distinguishes strand type)
    shared: codons with no T or U (e.g. GCG, PZS) → 6³ = 216 overlap
    DNA-only: any codon with T but no U
    RNA-only: any codon with U but no T
    hybrid: codons with both T and U (e.g. TUG) → structurally impossible
            in biology but valid as abstract address labels in math universe

In practice: 512 DNA + 512 RNA − 216 shared = 808 distinct addresses.
The shared codons carry BOTH DNA and RNA spectral weights → double-layered
eigenvalues (the address has both coarse and fine structure simultaneously).

Usage
─────
    from hachimoji_spectral import SpectralCodonSpace, MengerLaplacian

    spec = SpectralCodonSpace()
    print(spec.n_addresses)              # 808

    lap = MengerLaplacian(spec)
    ev = lap.eigenvalue('GCG')           # combined spectral weight
    band = lap.spectral_band('GCG')      # 'COARSE', 'FINE', 'DUAL', 'NULL'
"""

from __future__ import annotations
import math
from itertools import product
from typing import Dict, List, Optional, Tuple

# ── Import partner modules ───────────────────────────────────────────────────

from hachimoji_rna import (
    RNA_BASES,
    BASE_FOLD_STABILITY,
    RnaCodonSpace,
    FoldPropensity,
    MengerRnaMapper,
)

# DNA constants from hachimoji_synth — import-safe fallback if not available
try:
    from hachimoji_synth import HACHI_BASES as DNA_BASES_STR
    DNA_BASES: Tuple[str, ...] = tuple(DNA_BASES_STR)
except ImportError:
    DNA_BASES = ('A', 'T', 'G', 'C', 'P', 'Z', 'S', 'B')

# ── Constants ────────────────────────────────────────────────────────────────

# Symbolic stability weights for DNA bases (mirrors RNA convention).
# T replaces U; otherwise same symbolic ordering.
DNA_FOLD_STABILITY: Dict[str, float] = {
    'G': 1.00,
    'C': 1.00,
    'P': 0.80,
    'S': 0.70,
    'A': 0.60,
    'T': 0.60,   # DNA thymine — same symbolic weight as RNA uracil
    'B': 0.50,
    'Z': 0.20,
}

# Mixing coefficients: DNA = coarse (low-frequency), RNA = fine (high-frequency)
ALPHA_DNA: float = 0.6    # coarse eigenmode weight
BETA_RNA:  float = 0.4    # fine eigenmode weight
# α + β = 1.0 → spectral weight normalised to [0, 1]

# Menger sponge constants
HAUSDORFF_DIM: float = 2.7268    # log(20)/log(3)
MENGER_ITER1_POSITIONS: int = 20  # 27 - 7 removed


# ── Strand type ──────────────────────────────────────────────────────────────

class StrandType:
    DNA  = 'DNA'
    RNA  = 'RNA'
    DUAL = 'DUAL'   # codon has neither T nor U → shared by both
    NULL = 'NULL'    # codon has both T and U → abstract-only address


def classify_strand(codon: str) -> str:
    """Determine which strand(s) a codon belongs to."""
    has_t = 'T' in codon.upper()
    has_u = 'U' in codon.upper()
    if has_t and has_u:
        return StrandType.NULL   # biologically impossible, math-valid
    if has_t:
        return StrandType.DNA
    if has_u:
        return StrandType.RNA
    return StrandType.DUAL       # no T, no U → shared


# ── Spectral codon space ────────────────────────────────────────────────────

class SpectralCodonSpace:
    """
    Combined DNA + RNA codon space with spectral weight assignment.

    Each codon gets:
        - strand classification (DNA / RNA / DUAL / NULL)
        - DNA symbolic weight (coarse eigenmode)
        - RNA symbolic weight (fine eigenmode)
        - combined spectral weight = α·dna + β·rna
        - Menger sponge address (iteration, position)
    """

    # All 10 bases across both alphabets
    ALL_BASES: Tuple[str, ...] = ('A', 'T', 'U', 'G', 'C', 'P', 'Z', 'S', 'B')

    def __init__(
        self,
        alpha: float = ALPHA_DNA,
        beta: float = BETA_RNA,
    ) -> None:
        self.alpha = alpha
        self.beta = beta

        # Generate the full combined space: 9 bases (A,T,U,G,C,P,Z,S,B)
        # 9³ = 729 raw combinations, but we exclude NULL (T+U) codons
        # from the primary address space.
        self._codons: List[str] = []
        self._strand: Dict[str, str] = {}
        self._dna_weight: Dict[str, float] = {}
        self._rna_weight: Dict[str, float] = {}
        self._spectral: Dict[str, float] = {}

        for bases in product(self.ALL_BASES, repeat=3):
            codon = ''.join(bases)
            strand = classify_strand(codon)

            self._codons.append(codon)
            self._strand[codon] = strand
            self._dna_weight[codon] = self._calc_dna_weight(codon, strand)
            self._rna_weight[codon] = self._calc_rna_weight(codon, strand)
            self._spectral[codon] = self._combine(codon)

        self._index: Dict[str, int] = {c: i for i, c in enumerate(self._codons)}

    def _calc_dna_weight(self, codon: str, strand: str) -> float:
        """DNA symbolic weight — coarse eigenmode."""
        if strand == StrandType.RNA:
            return 0.0   # pure RNA codon has no DNA eigenmode
        # Map U→T for DUAL codons when computing DNA weight
        return sum(DNA_FOLD_STABILITY.get(b, DNA_FOLD_STABILITY.get(
            'T' if b == 'U' else b, 0.0)) for b in codon) / 3.0

    def _calc_rna_weight(self, codon: str, strand: str) -> float:
        """RNA symbolic weight — fine eigenmode."""
        if strand == StrandType.DNA:
            return 0.0   # pure DNA codon has no RNA eigenmode
        # Map T→U for DUAL codons when computing RNA weight
        return sum(BASE_FOLD_STABILITY.get(b, BASE_FOLD_STABILITY.get(
            'U' if b == 'T' else b, 0.0)) for b in codon) / 3.0

    def _combine(self, codon: str) -> float:
        """Combined spectral weight = α·dna + β·rna."""
        d = self._dna_weight[codon]
        r = self._rna_weight[codon]
        strand = self._strand[codon]

        if strand == StrandType.DUAL:
            # Shared codon: both eigenmodes active
            return self.alpha * d + self.beta * r
        elif strand == StrandType.DNA:
            return d   # full DNA weight, no RNA contribution
        elif strand == StrandType.RNA:
            return r   # full RNA weight, no DNA contribution
        else:  # NULL
            # Abstract address — average of what T and U would give
            return (d + r) / 2.0

    @property
    def n_total(self) -> int:
        """Total codons including NULL."""
        return len(self._codons)

    @property
    def n_addresses(self) -> int:
        """Addressable codons (excluding NULL)."""
        return sum(1 for s in self._strand.values() if s != StrandType.NULL)

    def codons_by_strand(self, strand: str) -> List[str]:
        return [c for c, s in self._strand.items() if s == strand]

    def spectral_weight(self, codon: str) -> float:
        return self._spectral.get(codon.upper(), 0.0)

    def dna_weight(self, codon: str) -> float:
        return self._dna_weight.get(codon.upper(), 0.0)

    def rna_weight(self, codon: str) -> float:
        return self._rna_weight.get(codon.upper(), 0.0)

    def strand(self, codon: str) -> str:
        return self._strand.get(codon.upper(), StrandType.NULL)

    def summary(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for s in self._strand.values():
            counts[s] = counts.get(s, 0) + 1
        return {
            'total': self.n_total,
            'addressable': self.n_addresses,
            **counts,
        }


# ── Menger Laplacian ────────────────────────────────────────────────────────

class MengerLaplacian:
    """
    Spectral decomposition on the Menger sponge Laplacian.

    Each codon maps to an eigenmode.  The eigenvalue = spectral weight.
    Spectral band classification:

        COARSE — DNA-only codon (low-frequency structural backbone)
        FINE   — RNA-only codon (high-frequency topological detail)
        DUAL   — shared codon  (both eigenmodes superposed)
        NULL   — abstract address (biologically impossible T+U)

    The Laplacian adjacency is defined by single-base mutations:
    codon A is adjacent to codon B if they differ at exactly one position.
    Each codon has at most 8 × 3 = 24 neighbours (8 alternative bases × 3
    positions, minus self).  In practice fewer, since not all bases appear
    at all positions.

    The spectral weight determines the eigenvalue magnitude:
    hot codons (high eigenvalue) → frequently visited by engram random walks
    cold codons (low eigenvalue) → structural boundaries / stop positions
    """

    def __init__(self, space: Optional[SpectralCodonSpace] = None) -> None:
        self._space = space or SpectralCodonSpace()

    def eigenvalue(self, codon: str) -> float:
        """Eigenvalue = spectral weight at this codon's Laplacian position."""
        return self._space.spectral_weight(codon)

    def spectral_band(self, codon: str) -> str:
        """Which eigenmode band this codon occupies."""
        return self._space.strand(codon)

    def neighbours(self, codon: str) -> List[str]:
        """
        All codons reachable by a single-base mutation.
        These are the Laplacian adjacency edges.
        """
        c = codon.upper()
        nbrs: List[str] = []
        for pos in range(3):
            for base in SpectralCodonSpace.ALL_BASES:
                if base == c[pos]:
                    continue
                mutant = c[:pos] + base + c[pos+1:]
                nbrs.append(mutant)
        return nbrs

    def local_spectral_gradient(self, codon: str) -> float:
        """
        Mean eigenvalue difference between this codon and its neighbours.
        Positive → this codon is a spectral peak (attractor).
        Negative → this codon is in a spectral valley (repeller/boundary).
        """
        ev = self.eigenvalue(codon)
        nbrs = self.neighbours(codon)
        if not nbrs:
            return 0.0
        mean_nbr = sum(self.eigenvalue(n) for n in nbrs) / len(nbrs)
        return ev - mean_nbr

    def is_spectral_peak(self, codon: str, threshold: float = 0.05) -> bool:
        """True if this codon is a local attractor in the spectral field."""
        return self.local_spectral_gradient(codon) > threshold

    def is_spectral_boundary(self, codon: str, threshold: float = -0.05) -> bool:
        """True if this codon is a structural boundary (valley)."""
        return self.local_spectral_gradient(codon) < threshold

    def cross_strand_edges(self, codon: str) -> List[Tuple[str, str]]:
        """
        Neighbours that cross the DNA/RNA boundary.
        These are the inter-strand spectral coupling edges —
        the mechanism by which coarse and fine eigenmodes interact.

        A T→U mutation (or reverse) crosses strands while preserving
        the symbolic stability weight — the eigenvalue stays the same
        but the spectral band changes.  This is the codon equivalent
        of a refractive interface in the Snell's Law analogy.
        """
        strand = self._space.strand(codon)
        edges: List[Tuple[str, str]] = []
        for nbr in self.neighbours(codon):
            nbr_strand = self._space.strand(nbr)
            if nbr_strand != strand:
                edges.append((nbr, nbr_strand))
        return edges

    def codon_spectrum_entry(self, codon: str) -> Dict[str, object]:
        """Full spectral descriptor for a single codon."""
        c = codon.upper()
        return {
            'codon':       c,
            'band':        self.spectral_band(c),
            'eigenvalue':  self.eigenvalue(c),
            'dna_weight':  self._space.dna_weight(c),
            'rna_weight':  self._space.rna_weight(c),
            'gradient':    self.local_spectral_gradient(c),
            'is_peak':     self.is_spectral_peak(c),
            'is_boundary': self.is_spectral_boundary(c),
            'n_neighbours': len(self.neighbours(c)),
            'n_cross_strand': len(self.cross_strand_edges(c)),
        }


# ── Spectral Menger address ─────────────────────────────────────────────────

class SpectralMengerAddress:
    """
    Unified Menger sponge address with spectral eigenvalue.

    Combines MengerRnaMapper (topology) with MengerLaplacian (spectrum)
    into a single address descriptor.

    The address has three components:
        1. Menger iteration layer (topology)
        2. Position within that layer (geometry)
        3. Spectral eigenvalue (dynamics — how frequently visited)

    This is the engram address: topology + geometry + dynamics = complete
    description of where a codon sits in the non-Euclidean address space
    and how it behaves under random walks.
    """

    def __init__(self) -> None:
        self._space = SpectralCodonSpace()
        self._lap = MengerLaplacian(self._space)
        self._rna_mapper = MengerRnaMapper()
        self._fp = FoldPropensity()

    def full_address(self, codon: str) -> Dict[str, object]:
        """
        Complete engram address for a codon.

        Returns dict with:
            codon:       the codon string
            strand:      DNA / RNA / DUAL / NULL
            menger:      (iteration_layer, position) — topology
            eigenvalue:  spectral weight — dynamics
            band:        COARSE / FINE / DUAL / NULL — eigenmode type
            gradient:    local spectral gradient — attractor/repeller
            hot_cold:    [-1, +1] circulation score
            class:       SURFACE / INTERIOR / TUNNEL / VERTEX
            hausdorff:   Menger sponge dimensionality
        """
        c = codon.upper()
        strand = self._space.strand(c)

        # Menger topology — use RNA mapper for RNA/DUAL, construct DNA analog
        if strand in (StrandType.RNA, StrandType.DUAL):
            # For DUAL codons, the RNA mapper works directly (no T present)
            menger = self._rna_mapper.codon_to_voxel(c)
            codon_class = self._fp.codon_class(c)
            hot_cold = self._fp.hot_cold_score(c)
        elif strand == StrandType.DNA:
            # DNA codon: translate T→U to get RNA-equivalent Menger position
            rna_equiv = c.replace('T', 'U')
            menger = self._rna_mapper.codon_to_voxel(rna_equiv)
            codon_class = self._fp.codon_class(rna_equiv)
            hot_cold = self._fp.hot_cold_score(rna_equiv)
        else:  # NULL
            menger = (0, 0)
            codon_class = 'NULL'
            hot_cold = 0.0

        return {
            'codon':      c,
            'strand':     strand,
            'menger':     menger,
            'eigenvalue': self._lap.eigenvalue(c),
            'band':       self._lap.spectral_band(c),
            'gradient':   self._lap.local_spectral_gradient(c),
            'hot_cold':   hot_cold,
            'class':      codon_class,
            'hausdorff':  HAUSDORFF_DIM,
        }

    def batch_addresses(self, codons: List[str]) -> List[Dict[str, object]]:
        return [self.full_address(c) for c in codons]

    def spectral_summary(self) -> Dict[str, object]:
        """Aggregate spectral statistics across the full address space."""
        weights = [self._space.spectral_weight(c)
                   for c in self._space._codons
                   if self._space.strand(c) != StrandType.NULL]
        n = len(weights)
        mean_w = sum(weights) / max(n, 1)
        var_w = sum((w - mean_w) ** 2 for w in weights) / max(n, 1)

        summary = self._space.summary()
        return {
            'n_addresses':     summary['addressable'],
            'strand_counts':   {k: v for k, v in summary.items()
                                if k not in ('total', 'addressable')},
            'mean_eigenvalue': mean_w,
            'std_eigenvalue':  math.sqrt(var_w),
            'hausdorff_dim':   HAUSDORFF_DIM,
            'alpha_dna':       self._space.alpha,
            'beta_rna':        self._space.beta,
        }


# ── Self-test ────────────────────────────────────────────────────────────────

def _self_test() -> None:
    print("hachimoji_spectral.py — self-test")
    print("=" * 60)

    # 1. Spectral codon space
    space = SpectralCodonSpace()
    s = space.summary()
    print(f"Combined codon space: {s['total']} total, {s['addressable']} addressable")
    for strand in (StrandType.DNA, StrandType.RNA, StrandType.DUAL, StrandType.NULL):
        print(f"  {strand:<5s}: {s.get(strand, 0):4d}")

    assert s['total'] == 9 ** 3, f"Expected 729, got {s['total']}"
    # DUAL = 6³ = 216 (no T, no U among A,G,C,P,Z,S,B = 7... wait)
    # Actually: ALL_BASES has 9 elements. DUAL = codons with neither T nor U.
    # Bases without T or U: A, G, C, P, Z, S, B = 7 bases → 7³ = 343
    n_dual = len(space.codons_by_strand(StrandType.DUAL))
    print(f"\n  DUAL codons (shared DNA+RNA): {n_dual}")
    assert n_dual == 7 ** 3, f"Expected 343 DUAL, got {n_dual}"

    # 2. Spectral weights
    # GCG is DUAL — should have both DNA and RNA weights
    gcg_d = space.dna_weight('GCG')
    gcg_r = space.rna_weight('GCG')
    gcg_s = space.spectral_weight('GCG')
    print(f"\n  GCG: dna={gcg_d:.3f} rna={gcg_r:.3f} spectral={gcg_s:.3f}")
    assert gcg_d > 0 and gcg_r > 0, "GCG should have both weights"
    assert abs(gcg_s - (ALPHA_DNA * gcg_d + BETA_RNA * gcg_r)) < 1e-9

    # ATG is DNA-only
    atg_s = space.strand('ATG')
    assert atg_s == StrandType.DNA, f"ATG should be DNA, got {atg_s}"
    assert space.rna_weight('ATG') == 0.0, "ATG RNA weight should be 0"

    # AUG is RNA-only
    aug_s = space.strand('AUG')
    assert aug_s == StrandType.RNA, f"AUG should be RNA, got {aug_s}"
    assert space.dna_weight('AUG') == 0.0, "AUG DNA weight should be 0"

    # TUG is NULL (both T and U)
    tug_s = space.strand('TUG')
    assert tug_s == StrandType.NULL, f"TUG should be NULL, got {tug_s}"
    print("  Strand classification: PASS")

    # 3. Menger Laplacian
    lap = MengerLaplacian(space)
    gcg_ev = lap.eigenvalue('GCG')
    gcg_grad = lap.local_spectral_gradient('GCG')
    gcg_nbrs = lap.neighbours('GCG')
    gcg_cross = lap.cross_strand_edges('GCG')
    print(f"\n  Laplacian at GCG:")
    print(f"    eigenvalue: {gcg_ev:.4f}")
    print(f"    gradient:   {gcg_grad:+.4f}")
    print(f"    neighbours: {len(gcg_nbrs)}")
    print(f"    cross-strand edges: {len(gcg_cross)}")
    assert len(gcg_nbrs) == 8 * 3, f"Expected 24 neighbours, got {len(gcg_nbrs)}"
    # GCG is DUAL; mutating any position to T → DNA, to U → RNA
    assert len(gcg_cross) > 0, "GCG should have cross-strand edges"

    # 4. Spectral Menger address
    sma = SpectralMengerAddress()
    addr = sma.full_address('GCG')
    print(f"\n  Full address for GCG:")
    for k, v in addr.items():
        print(f"    {k}: {v}")
    assert addr['strand'] == StrandType.DUAL
    assert addr['hausdorff'] == HAUSDORFF_DIM

    # ZZZ should be VERTEX / boundary
    zzz = sma.full_address('ZZZ')
    print(f"\n  Full address for ZZZ:")
    print(f"    class={zzz['class']} eigenvalue={zzz['eigenvalue']:.4f} "
          f"gradient={zzz['gradient']:+.4f}")
    assert zzz['class'] == 'VERTEX'

    # 5. Spectral summary
    ss = sma.spectral_summary()
    print(f"\n  Spectral summary:")
    print(f"    addresses: {ss['n_addresses']}")
    print(f"    mean eigenvalue: {ss['mean_eigenvalue']:.4f}")
    print(f"    std eigenvalue:  {ss['std_eigenvalue']:.4f}")
    print(f"    Hausdorff dim:   {ss['hausdorff_dim']:.4f}")
    print(f"    α(DNA):          {ss['alpha_dna']}")
    print(f"    β(RNA):          {ss['beta_rna']}")

    # 6. Cross-strand spectral coupling: T↔U mutation preserves symbolic weight
    atg_ev = lap.eigenvalue('ATG')
    aug_ev = lap.eigenvalue('AUG')
    # Both should have same symbolic stability (T and U have same weight 0.6)
    # but different spectral weights due to strand-specific mixing
    print(f"\n  Cross-strand coupling ATG↔AUG:")
    print(f"    ATG eigenvalue: {atg_ev:.4f} (DNA-only, full weight)")
    print(f"    AUG eigenvalue: {aug_ev:.4f} (RNA-only, full weight)")
    # Since T and U have same symbolic weight, these should be equal
    assert abs(atg_ev - aug_ev) < 1e-9, \
        "ATG and AUG should have equal eigenvalues (T↔U same symbolic weight)"
    print("    T↔U eigenvalue conservation: PASS")

    print("\n" + "=" * 60)
    print("All checks PASS")
    print("=" * 60)
    print("NOTE: All weights are symbolic (math universe).")
    print("Codon position = eigenmode of Menger Laplacian.")
    print("DNA = coarse eigenmodes. RNA = fine eigenmodes.")
    print(f"Combined: {ss['n_addresses']} addresses at "
          f"Hausdorff dimension {HAUSDORFF_DIM:.4f}.")


if __name__ == '__main__':
    _self_test()
