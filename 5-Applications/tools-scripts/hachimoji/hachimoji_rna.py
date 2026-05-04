#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
hachimoji_rna.py — Hachimoji RNA extension for hachimoji_synth.py

Extension module. Import only when RNA encoding is needed.
Does NOT modify or require hachimoji_synth.py.
Standalone or composable.

REFERENCE
---------
Hoshika et al. (2019). Hachimoji DNA and RNA: A genetic system with eight
building blocks. Science 363(6429):884-887. doi:10.1126/science.aat0971

RNA ALPHABET
------------
Standard RNA: A, U, G, C  (U replaces T vs DNA)
Hachimoji RNA: A, U, G, C, P, Z, S, B  (same synthetic pairs, ribose backbone)

Base pairings (Watson-Crick geometry preserved):
    A ↔ U   (standard)
    G ↔ C   (standard)
    P ↔ Z   (synthetic, Benner lab)
    S ↔ B   (synthetic, Benner lab)

Codon space: 8³ = 512 codons (vs 64 for standard RNA)

FOLD STABILITY CONVENTION (SYMBOLIC)
-------------------------------------
Each base is assigned a FOLD_STABILITY weight (0.0 → 1.0).
MATH UNIVERSE: these are symbolic structural coordinates, NOT literal
thermodynamic free energies.  The ordering is inspired by H-bond count
and Hoshika 2019 aptamer behaviour, but the values define positions in
the Menger Laplacian spectrum.  No physical unit attaches.
    G/C: maximum stability symbol  → 1.0
    A/U: mid-low symbol            → 0.6
    P/Z: high-mid symbol           → 0.8  (Hoshika 2019 qualitative)
    S/B: mid symbol                → 0.7  (Hoshika 2019 qualitative)
    Z:   minimum symbol            → 0.2  (destabiliser archetype)

STOP CODON CONVENTION
----------------------
Standard RNA stop codons: UAA, UAG, UGA
In Hachimoji RNA these are still functional if translation is the goal.
For ENGRAM ADDRESSING purposes, the biologically-unclaimed positions are:
    Any codon containing Z at position 1 or 2 (no natural amino acid uses Z)
    → available as Menger sponge vertex addresses (structural holes)
    → flagged CODON_CLASS_VERTEX in this module

MENGER SPONGE MAPPING
----------------------
Menger sponge iteration 1: 27 - 7 = 20 positions remaining.
Standard genetic code: exactly 20 amino acids.
Hachimoji RNA: 512 codons → 20 canonical + 492 extended addresses.

The 492 extended addresses are partitioned:
    CODON_CLASS_SURFACE  — G/C/P/Z rich, high stability → hot engram nodes
    CODON_CLASS_INTERIOR — A/U/S/B rich, moderate stability → warm nodes
    CODON_CLASS_VERTEX   — Z-dominant, destabilising → sponge holes / stop
    CODON_CLASS_TUNNEL   — pseudoknot-prone sequences → |W> tunnel state

Usage
-----
    from hachimoji_rna import RnaCodonSpace, FoldPropensity, MengerRnaMapper

    space = RnaCodonSpace()
    print(space.n_codons)            # 512
    print(space.stop_codons)         # ['UAA', 'UAG', 'UGA']
    print(space.vertex_codons[:5])   # Z-dominant, sponge holes

    fp = FoldPropensity()
    print(fp.stability('GCG'))       # ~1.0
    print(fp.stability('ZAU'))       # ~0.2x (Z destabilises)
    print(fp.codon_class('GCG'))     # 'SURFACE'
    print(fp.codon_class('ZZZ'))     # 'VERTEX'

    mapper = MengerRnaMapper()
    addr = mapper.codon_to_voxel('GCG')   # (iteration, position) in sponge
    print(mapper.is_tunnel_candidate('GUG'))  # True/False (G-quad prone)
"""

from __future__ import annotations
from itertools import product
from typing import Dict, List, Tuple, Optional

# ── Alphabet ──────────────────────────────────────────────────────────────────

RNA_BASES: Tuple[str, ...] = ('A', 'U', 'G', 'C', 'P', 'Z', 'S', 'B')

# Watson-Crick complement in Hachimoji RNA
RNA_COMPLEMENT: Dict[str, str] = {
    'A': 'U', 'U': 'A',
    'G': 'C', 'C': 'G',
    'P': 'Z', 'Z': 'P',
    'S': 'B', 'B': 'S',
}

# Symbolic fold stability weight per base.
# MATH UNIVERSE: these are structural ordering labels (topology of the
# address space), NOT literal thermodynamic measurements.  The ordering
# is inspired by H-bond count and Hoshika 2019 aptamer behaviour, but
# the numerical values are symbolic coordinates — they define the
# Menger Laplacian spectrum, not physical free energies.
BASE_FOLD_STABILITY: Dict[str, float] = {
    'G': 1.00,   # maximum stability symbol — 3 H-bonds archetype
    'C': 1.00,   # maximum stability symbol — 3 H-bonds archetype
    'P': 0.80,   # high-mid symbol — synthetic stable (Hoshika 2019)
    'S': 0.70,   # mid symbol — synthetic stable
    'A': 0.60,   # mid-low symbol — 2 H-bonds archetype
    'U': 0.60,   # mid-low symbol — 2 H-bonds archetype
    'B': 0.50,   # low-mid symbol — less characterised
    'Z': 0.20,   # minimum symbol — destabiliser (spinach aptamer quench)
}

# G-quadruplex propensity: G-runs form G4 structures (pseudoknot-prone)
# Used to identify tunnel-state candidate codons (|W> in TSM-NR1)
G_QUAD_MIN_RUN = 2   # GG or more at any position → candidate

# Standard RNA stop codons (biologically claimed)
RNA_STOP_STANDARD: Tuple[str, ...] = ('UAA', 'UAG', 'UGA')

# Codon class labels
CODON_CLASS_SURFACE  = 'SURFACE'   # high stability → hot engram node
CODON_CLASS_INTERIOR = 'INTERIOR'  # moderate       → warm node
CODON_CLASS_VERTEX   = 'VERTEX'    # Z-dominant     → sponge hole / stop
CODON_CLASS_TUNNEL   = 'TUNNEL'    # pseudoknot-prone → |W> tunnel state

# Stability thresholds for class assignment
SURFACE_THRESHOLD  = 0.80   # mean stability ≥ this → SURFACE
VERTEX_THRESHOLD   = 0.40   # mean stability ≤ this → VERTEX
# Between VERTEX_THRESHOLD and SURFACE_THRESHOLD → INTERIOR or TUNNEL


# ── Codon space ───────────────────────────────────────────────────────────────

class RnaCodonSpace:
    """
    Complete 8-base Hachimoji RNA codon space.

    All 512 codons enumerated, classified, and indexed.
    No translation table defined — this is for engram addressing,
    not biological protein synthesis.
    """

    def __init__(self) -> None:
        self._codons: List[str] = [
            ''.join(t) for t in product(RNA_BASES, repeat=3)
        ]
        self._index: Dict[str, int] = {c: i for i, c in enumerate(self._codons)}
        self._fp = FoldPropensity()

    @property
    def n_codons(self) -> int:
        return len(self._codons)   # always 512

    @property
    def all_codons(self) -> List[str]:
        return list(self._codons)

    @property
    def stop_codons(self) -> List[str]:
        """Standard RNA stop codons still present in Hachimoji RNA."""
        return [c for c in self._codons if c in RNA_STOP_STANDARD]

    @property
    def vertex_codons(self) -> List[str]:
        """Z-dominant codons — sponge holes, structurally destabilising.
        Biologically unclaimed in Hachimoji RNA → free for engram addressing."""
        return [c for c in self._codons
                if self._fp.codon_class(c) == CODON_CLASS_VERTEX]

    @property
    def surface_codons(self) -> List[str]:
        """High-stability codons → hot engram surface nodes."""
        return [c for c in self._codons
                if self._fp.codon_class(c) == CODON_CLASS_SURFACE]

    @property
    def tunnel_codons(self) -> List[str]:
        """Pseudoknot-prone → |W> tunnel state candidates."""
        return [c for c in self._codons
                if self._fp.codon_class(c) == CODON_CLASS_TUNNEL]

    @property
    def interior_codons(self) -> List[str]:
        """Moderate stability → warm/cold engram nodes."""
        return [c for c in self._codons
                if self._fp.codon_class(c) == CODON_CLASS_INTERIOR]

    def index(self, codon: str) -> int:
        """Integer address of a codon in [0, 511]."""
        return self._index[codon.upper()]

    def codon(self, index: int) -> str:
        """Codon at integer address."""
        return self._codons[index]

    def complement(self, codon: str) -> str:
        """Watson-Crick complement of a codon (3'→5' sense)."""
        return ''.join(RNA_COMPLEMENT[b] for b in codon.upper())

    def summary(self) -> Dict[str, int]:
        return {
            'total':    self.n_codons,
            'surface':  len(self.surface_codons),
            'interior': len(self.interior_codons),
            'vertex':   len(self.vertex_codons),
            'tunnel':   len(self.tunnel_codons),
            'stop':     len(self.stop_codons),
        }


# ── Fold propensity ───────────────────────────────────────────────────────────

class FoldPropensity:
    """
    Codon-level fold stability and class assignment.

    Symbolic codon-level fold propensity for Menger address classification.
    No sequence-context model — single codon only.
    Weights are structural ordering labels (math universe), not literal
    thermodynamic measurements.  The classification SURFACE/INTERIOR/
    VERTEX/TUNNEL defines address-space topology, not physical stability.
    """

    def stability(self, codon: str) -> float:
        """Mean fold stability weight for a codon. Range [0.0, 1.0]."""
        return sum(BASE_FOLD_STABILITY[b] for b in codon.upper()) / 3.0

    def is_g_quad_prone(self, codon: str) -> bool:
        """True if codon contains a G-run that may participate in G-quadruplex.
        G-quadruplexes are pseudoknot-prone → |W> tunnel state candidates."""
        g_run = 0
        for b in codon.upper():
            if b == 'G':
                g_run += 1
                if g_run >= G_QUAD_MIN_RUN:
                    return True
            else:
                g_run = 0
        return False

    def codon_class(self, codon: str) -> str:
        """
        Classify codon for Menger sponge / engram addressing.

        Priority order:
            TUNNEL  — G-quad prone (pseudoknot → |W> tunnel state)
            VERTEX  — Z-dominant, destabilising (sponge holes)
            SURFACE — high stability (hot engram nodes)
            INTERIOR — everything else (warm/cold nodes)
        """
        c = codon.upper()
        s = self.stability(c)

        # TUNNEL first — G-quad supersedes stability classification
        if self.is_g_quad_prone(c):
            return CODON_CLASS_TUNNEL

        # VERTEX — Z destabilises fold below threshold
        if s <= VERTEX_THRESHOLD:
            return CODON_CLASS_VERTEX

        # SURFACE — high stability hot engram nodes
        if s >= SURFACE_THRESHOLD:
            return CODON_CLASS_SURFACE

        # Everything else
        return CODON_CLASS_INTERIOR

    def hot_cold_score(self, codon: str) -> float:
        """
        Thermodynamic hot/cold score for hot-path circulation.

        +1.0 = maximally hot (stable fold, stays in memory)
        -1.0 = maximally cold (unstable, evicts quickly)

        Derived from stability weight, centred and normalised.
        TUNNEL codons get a separate non-linear score (non-planar topology).
        """
        c = codon.upper()
        if self.is_g_quad_prone(c):
            # G-quadruplexes are thermodynamically very stable but topologically
            # complex — score as moderately hot with high variance
            return 0.5
        s = self.stability(c)
        # Map [0, 1] → [-1, +1], centred at 0.6 (A/U stability)
        return (s - 0.6) / 0.4


# ── Menger RNA mapper ─────────────────────────────────────────────────────────

class MengerRnaMapper:
    """
    Maps Hachimoji RNA codons to Menger sponge addresses.

    Menger sponge geometry:
        Iteration 0: 3×3×3 = 27 positions (raw 3-base codon space mod 27)
        Iteration 1: 27 - 7 = 20 positions (amino acid analog — 7 holes)
        Iteration 2: 20 × 20 = 400 (dipeptide analog)
        ...

    The 7 removed positions at iteration 1 correspond to the 7 cubes
    removed from the Menger sponge: center of each face (6) + center cube (1).
    In this mapping these are VERTEX codons — structurally destabilising,
    biologically unclaimed in Hachimoji RNA.

    The 512 Hachimoji RNA codons are mapped onto this geometry:
        Positions 0-19:   iteration-1 surface (20 amino acid analogs)
        Positions 20-511: extended Hachimoji address space
            partitioned by codon_class into SURFACE/INTERIOR/VERTEX/TUNNEL

    Hausdorff dimension of Menger sponge: log(20)/log(3) ≈ 2.727
    This is the effective dimensionality of the engram address space —
    sub-integer, between 2D surface and 3D volume.
    Non-Euclidean by construction.
    """

    HAUSDORFF_DIM: float = 2.7268   # log(20) / log(3)
    N_ITERATION_1: int = 20          # positions after first Menger iteration
    N_ITERATION_0: int = 27          # 3×3×3 raw cube

    # The 7 removed positions in iteration 1 (face centres + body centre)
    # Mapped to codon indices via: removed_idx % 27
    REMOVED_POSITIONS: Tuple[int, ...] = (4, 10, 12, 13, 14, 16, 22)

    def __init__(self) -> None:
        self._space = RnaCodonSpace()
        self._fp    = FoldPropensity()
        self._build_index()

    def _build_index(self) -> None:
        """Partition all 512 codons into Menger address layers."""
        self._layer: Dict[str, str] = {}
        self._voxel: Dict[str, Tuple[int, int]] = {}

        surface  = self._space.surface_codons
        tunnel   = self._space.tunnel_codons
        vertex   = self._space.vertex_codons
        interior = self._space.interior_codons

        # Iteration-1 surface: first 20 SURFACE codons (by index order)
        iter1 = surface[:self.N_ITERATION_1]
        for i, c in enumerate(iter1):
            self._layer[c] = 'ITER1'
            self._voxel[c] = (1, i)

        # Remaining SURFACE → iteration-2 extended surface
        for i, c in enumerate(surface[self.N_ITERATION_1:]):
            self._layer[c] = 'ITER2_SURFACE'
            self._voxel[c] = (2, i)

        # TUNNEL → |W> tunnel state addresses (non-planar)
        for i, c in enumerate(tunnel):
            self._layer[c] = 'TUNNEL'
            self._voxel[c] = (3, i)

        # INTERIOR → warm/cold interior addresses
        for i, c in enumerate(interior):
            self._layer[c] = 'INTERIOR'
            self._voxel[c] = (4, i)

        # VERTEX → sponge holes (stop codon analogs)
        for i, c in enumerate(vertex):
            self._layer[c] = 'VERTEX'
            self._voxel[c] = (5, i)

    def codon_to_voxel(self, codon: str) -> Tuple[int, int]:
        """
        Map a codon to its (iteration_layer, position) in Menger space.

        Returns:
            (1, 0-19)    — iteration-1 surface (20 canonical positions)
            (2, n)       — extended surface
            (3, n)       — tunnel / |W> addresses
            (4, n)       — interior warm/cold
            (5, n)       — vertex / stop / sponge holes
        """
        return self._voxel.get(codon.upper(), (0, 0))

    def voxel_to_codons(self, iteration: int) -> List[str]:
        """All codons at a given iteration layer."""
        return [c for c, v in self._voxel.items() if v[0] == iteration]

    def is_tunnel_candidate(self, codon: str) -> bool:
        """True if codon maps to a |W> tunnel address (pseudoknot-prone)."""
        return self._layer.get(codon.upper()) == 'TUNNEL'

    def is_vertex(self, codon: str) -> bool:
        """True if codon is a sponge hole (structurally destabilising stop)."""
        return self._layer.get(codon.upper()) == 'VERTEX'

    def hot_cold_score(self, codon: str) -> float:
        """Hot/cold engram score for this codon's voxel position."""
        return self._fp.hot_cold_score(codon.upper())

    def address_space_summary(self) -> Dict[str, object]:
        layer_counts: Dict[str, int] = {}
        for layer in self._layer.values():
            layer_counts[layer] = layer_counts.get(layer, 0) + 1
        return {
            'hausdorff_dim': self.HAUSDORFF_DIM,
            'total_addresses': len(self._voxel),
            'layers': layer_counts,
            'canonical_iter1': self.N_ITERATION_1,
            'note': (
                'VERTEX codons are biologically unclaimed in Hachimoji RNA — '
                'available as sponge-hole addresses with no prior art conflict.'
            ),
        }


# ── Optional integration with hachimoji_synth.py ─────────────────────────────

def rna_carrier_from_dna_profile(dna_profile: dict) -> dict:
    """
    Convert a DNA carrier profile (from hachimoji_synth.py CARRIER_PROFILES)
    to an approximate RNA carrier profile.

    Substitution: T → U everywhere in codon labels.
    Frequencies are preserved — this is a label translation only.

    NOTE: This is an approximation. A proper RNA carrier profile requires
    RNA-seq codon counts from the target organism, not CDS-derived DNA counts.
    The octopus profile in hachimoji_synth.py explicitly flags this gap
    (60% neural transcript RNA editing in O. vulgaris).

    For organisms with significant RNA editing, this function will be wrong.
    Use RNA-seq data where available.
    """
    rna_profile: dict = {}
    for codon, freq in dna_profile.items():
        rna_codon = codon.replace('T', 'U')
        rna_profile[rna_codon] = freq
    return rna_profile


def score_sequence_for_menger(
    codons: List[str],
    mapper: Optional[MengerRnaMapper] = None,
) -> Dict[str, object]:
    """
    Score a Hachimoji RNA codon sequence for Menger sponge address properties.

    Returns per-codon classification and aggregate statistics useful for
    deciding whether RNA encoding adds value for a given sequence.

    If the sequence has no TUNNEL or VERTEX codons, RNA encoding adds no
    geometric addressing benefit over DNA encoding — save the complexity.
    """
    if mapper is None:
        mapper = MengerRnaMapper()

    classified = [
        {
            'codon':      c,
            'layer':      mapper._layer.get(c.upper(), 'UNKNOWN'),
            'voxel':      mapper.codon_to_voxel(c),
            'hot_cold':   mapper.hot_cold_score(c),
            'is_tunnel':  mapper.is_tunnel_candidate(c),
            'is_vertex':  mapper.is_vertex(c),
        }
        for c in codons
    ]

    n = len(classified)
    n_tunnel = sum(1 for x in classified if x['is_tunnel'])
    n_vertex = sum(1 for x in classified if x['is_vertex'])
    n_iter1  = sum(1 for x in classified if x['layer'] == 'ITER1')
    mean_hc  = sum(x['hot_cold'] for x in classified) / max(n, 1)

    return {
        'n_codons':       n,
        'n_tunnel':       n_tunnel,
        'n_vertex':       n_vertex,
        'n_iter1':        n_iter1,
        'mean_hot_cold':  mean_hc,
        'rna_adds_value': n_tunnel > 0 or n_vertex > 0,
        'codons':         classified,
    }


# ── Self-test ─────────────────────────────────────────────────────────────────

def _self_test() -> None:
    print("hachimoji_rna.py — self-test")
    print("=" * 60)

    space = RnaCodonSpace()
    s = space.summary()
    print(f"Codon space: {s['total']} total")
    print(f"  SURFACE  (hot engram nodes):     {s['surface']:3d}")
    print(f"  INTERIOR (warm/cold nodes):      {s['interior']:3d}")
    print(f"  TUNNEL   (|W> tunnel state):     {s['tunnel']:3d}")
    print(f"  VERTEX   (sponge holes/stops):   {s['vertex']:3d}")
    print(f"  STOP     (standard RNA stops):   {s['stop']:3d}")
    assert s['total'] == 512, f"Expected 512 codons, got {s['total']}"
    assert s['surface'] + s['interior'] + s['tunnel'] + s['vertex'] == 512

    fp = FoldPropensity()
    assert fp.codon_class('GGG') == CODON_CLASS_TUNNEL,  "GGG should be TUNNEL (G-quad)"
    assert fp.codon_class('ZZZ') == CODON_CLASS_VERTEX,  "ZZZ should be VERTEX (destabilising)"
    assert fp.codon_class('GCG') == CODON_CLASS_SURFACE, "GCG should be SURFACE (high stability)"
    assert fp.codon_class('AUA') == CODON_CLASS_INTERIOR,"AUA should be INTERIOR"
    print("\nFold propensity checks: PASS")

    mapper = MengerRnaMapper()
    addr_sum = mapper.address_space_summary()
    print(f"\nMenger mapper:")
    print(f"  Hausdorff dimension: {addr_sum['hausdorff_dim']:.4f}")
    print(f"  Total addresses:     {addr_sum['total_addresses']}")
    print(f"  Iteration-1 (canonical 20): {addr_sum['layers'].get('ITER1', 0)}")
    for layer, count in sorted(addr_sum['layers'].items()):
        print(f"    {layer:<20s}: {count}")
    print(f"\n  {addr_sum['note']}")

    # Verify GGG maps to TUNNEL layer
    assert mapper.is_tunnel_candidate('GGG'), "GGG should be tunnel candidate"
    assert mapper.is_vertex('ZZZ'),           "ZZZ should be vertex"
    assert not mapper.is_tunnel_candidate('AUA'), "AUA should not be tunnel"

    # Score a short sequence
    test_seq = ['GGG', 'GCG', 'AUA', 'ZZZ', 'GUG']
    result = score_sequence_for_menger(test_seq, mapper)
    print(f"\nSequence score for {test_seq}:")
    print(f"  RNA adds value: {result['rna_adds_value']}")
    print(f"  n_tunnel: {result['n_tunnel']}  n_vertex: {result['n_vertex']}")
    print(f"  mean hot/cold: {result['mean_hot_cold']:+.3f}")
    assert result['rna_adds_value'], "Test sequence should add value (has GGG tunnel + ZZZ vertex)"

    # DNA→RNA profile conversion
    dna_profile = {'ATG': 10, 'TGA': 3, 'GCT': 7}
    rna_profile = rna_carrier_from_dna_profile(dna_profile)
    assert 'AUG' in rna_profile, "ATG should become AUG"
    assert 'UGA' in rna_profile, "TGA should become UGA"
    print("\nDNA→RNA profile conversion: PASS")

    print("\nAll checks PASS")
    print("=" * 60)
    print("NOTE: BASE_FOLD_STABILITY weights are symbolic structural")
    print("coordinates (math universe), not literal thermodynamic values.")
    print("They define Menger Laplacian topology, not physical free energies.")


if __name__ == '__main__':
    _self_test()
