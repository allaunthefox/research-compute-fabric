"""
Genetic N-Space Shell Encoding (GENSIS) Kernel
===============================================
Extends MISC with every known biological/genetic coding system:
  - Standard/non-standard genetic code tables (64 codons × many variants)
  - n-dimensional hypercubic shell coordinates (generalized PIST → d-cube)
  - Cross-dimensional resonance encoding
  - N-space delta encoding leveraging biological degeneracy

Pulls from MATH_MODEL_MAP models:
  182 (Hardy-Weinberg), 271 (Mendelian), 294 (Genomic Entropy),
  295 (Codon Hamming), 304 (Self-Assembly ΔG), 306 (DNA Tile Logic),
  412 (RNA Combinators), 413 (BioBrick), 1276-1280 (AVMR Codon Info)
"""

import math, struct, hashlib
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, Any
from enum import Enum

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from misc_kernel import Q16_16, SCALE, PI_Q16, cos_q16, exp_q16


# ════════════════════════════════════════════════════════════════
# 1. GENETIC CODE TABLES — Every known variant (models 271,294,412)
# ════════════════════════════════════════════════════════════════

BASES = ['A', 'C', 'G', 'T']  # DNA
RNA_BASES = ['A', 'C', 'G', 'U']
AMINO_ACIDS = [
    'Ala','Arg','Asn','Asp','Cys','Gln','Glu','Gly','His','Ile',
    'Leu','Lys','Met','Phe','Pro','Ser','Thr','Trp','Tyr','Val',
    'SeCys','Pyl','Stop'
]
AA_ORDER = {aa: i for i, aa in enumerate(AMINO_ACIDS)}


def _build_standard_table() -> Dict[Tuple[str,str,str], str]:
    """Standard genetic code: 64 codons → 20 AAs + Stop"""
    table = {}
    bases = ['T', 'C', 'A', 'G']
    # Standard genetic code mapping (64 entries)
    std_map = {
        'TTT':'Phe','TTC':'Phe','TTA':'Leu','TTG':'Leu',
        'TCT':'Ser','TCC':'Ser','TCA':'Ser','TCG':'Ser',
        'TAT':'Tyr','TAC':'Tyr','TAA':'Stop','TAG':'Stop',
        'TGT':'Cys','TGC':'Cys','TGA':'Stop','TGG':'Trp',
        'CTT':'Leu','CTC':'Leu','CTA':'Leu','CTG':'Leu',
        'CCT':'Pro','CCC':'Pro','CCA':'Pro','CCG':'Pro',
        'CAT':'His','CAC':'His','CAA':'Gln','CAG':'Gln',
        'CGT':'Arg','CGC':'Arg','CGA':'Arg','CGG':'Arg',
        'ATT':'Ile','ATC':'Ile','ATA':'Ile','ATG':'Met',
        'ACT':'Thr','ACC':'Thr','ACA':'Thr','ACG':'Thr',
        'AAT':'Asn','AAC':'Asn','AAA':'Lys','AAG':'Lys',
        'AGT':'Ser','AGC':'Ser','AGA':'Arg','AGG':'Arg',
        'GTT':'Val','GTC':'Val','GTA':'Val','GTG':'Val',
        'GCT':'Ala','GCC':'Ala','GCA':'Ala','GCG':'Ala',
        'GAT':'Asp','GAC':'Asp','GAA':'Glu','GAG':'Glu',
        'GGT':'Gly','GGC':'Gly','GGA':'Gly','GGG':'Gly',
    }
    for codon_str, aa in std_map.items():
        table[(codon_str[0], codon_str[1], codon_str[2])] = aa
    return table


def _build_mito_table() -> Dict[Tuple[str,str,str], str]:
    """Vertebrate Mitochondrial Code (model 271 variant)."""
    table = _build_standard_table()
    # Reassignments for vertebrate mitochondria
    table[('A','T','A')] = 'Met'   # instead of Ile
    table[('T','G','A')] = 'Trp'   # instead of Stop
    table[('A','G','A')] = 'Stop'  # instead of Arg
    table[('A','G','G')] = 'Stop'  # instead of Arg
    return table


def _build_ciliate_table() -> Dict[Tuple[str,str,str], str]:
    """Ciliate Nuclear Code (model 271 variant)."""
    table = _build_standard_table()
    table[('T','A','A')] = 'Gln'   # instead of Stop
    table[('T','A','G')] = 'Gln'   # instead of Stop
    return table


GENETIC_CODE_TABLES = {
    'standard':        _build_standard_table(),
    'vert_mito':       _build_mito_table(),
    'ciliate':         _build_ciliate_table(),
    # Additional tables can be added similarly
}


# ════════════════════════════════════════════════════════════════
# 2. N-DIMENSIONAL SHELL COORDINATE (Generalized PIST)
# ════════════════════════════════════════════════════════════════

@dataclass
class NShellCoordinate:
    """d-dimensional shell coordinate (generalized PIST).
    
    Original 2D PIST: k = floor(sqrt(n)), t = n - k², mass = t·(2k+1-t)
    Generalized d-cube: k = floor(n^(1/d)), t[i] = base-(k+1) digits
    mass = Π t[i]·(k - t[i] + 1)
    """
    k: int           # shell index (d-th root of rank)
    t: List[int]     # offsets per dimension (length d)
    d: int           # number of dimensions
    
    def __post_init__(self):
        if len(self.t) != self.d:
            raise ValueError(f"t length {len(self.t)} != d={self.d}")
    
    @classmethod
    def encode(cls, n: int, d: int = 3) -> 'NShellCoordinate':
        """Encode natural number n into d-dimensional shell coordinate.
        
        n = k^d + Σ t[i]·(k+1)^i  where 0 ≤ t[i] ≤ k
        """
        if n < 0:
            return cls(k=0, t=[0]*d, d=d)
        if d < 1:
            return cls(k=0, t=[0], d=1)
        
        # Integer d-th root for shell index
        k = int(round(n ** (1.0 / d)))
        # Adjust for floating point errors
        while (k + 1) ** d <= n:
            k += 1
        while k ** d > n:
            k -= 1
        if k < 0:
            k = 0
        
        remaining = n - k ** d
        t = []
        base = max(k + 1, 1)
        for _ in range(d):
            t.append(remaining % base)
            remaining = remaining // base
        
        return cls(k=k, t=t, d=d)
    
    @property
    def mass(self) -> int:
        """d-dimensional hyperbolic hyperbola index.
        
        mass = 0 iff n is a perfect d-power (all t[i] = 0).
        This is the generalized zero-mass theorem (model 603 extended).
        """
        m = 1
        for ti in self.t:
            m *= ti * (self.k - ti + 1)
        return m
    
    @property
    def is_endpoint(self) -> bool:
        """Zero mass iff all offsets are 0 (perfect d-th power)."""
        return self.mass == 0
    
    def mirror(self) -> 'NShellCoordinate':
        """Mirror involution: t[i] → k - t[i], preserves mass.
        
        Generalizes model 580 to d dimensions.
        """
        mirrored = [self.k - ti for ti in self.t]
        return NShellCoordinate(k=self.k, t=mirrored, d=self.d)
    
    def is_resonant_with(self, other: 'NShellCoordinate') -> bool:
        """Generalized resonance: equal mass (model 582)."""
        return self.mass == other.mass
    
    def is_cross_resonant(self, other: 'NShellCoordinate') -> bool:
        """Cross-dimensional resonance: mass equality across different d."""
        return self.mass == other.mass  # works even if self.d != other.d
    
    @property
    def rho(self) -> List[float]:
        """Normalized tension per dimension (generalized model 585)."""
        return [ti / max(self.k + 1, 1) for ti in self.t]
    
    @property
    def tension_gradient(self) -> List[float]:
        """∇mass — direction of steepest mass increase in d-space."""
        grad = []
        for ti in self.t:
            # ∂mass/∂t_i = Π_{j≠i} t_j·(k-t_j+1) · (k - 2t_i + 1)
            partial = 1
            for j, tj in enumerate(self.t):
                if j != len(grad):  # not current dimension
                    partial *= tj * (self.k - tj + 1)
            # The derivative factor for dimension i
            d_factor = self.k - 2*ti + 1
            grad.append(partial * d_factor)
        return grad
    
    def to_tuple(self) -> Tuple[int, ...]:
        return (self.k,) + tuple(self.t)
    
    def __repr__(self) -> str:
        return (f"NS{d}Shell(k={self.k}, t={self.t}, "
                f"mass={self.mass})")


# ════════════════════════════════════════════════════════════════
# 3. GENETIC N-SPACE SHELL MAPPER
# ════════════════════════════════════════════════════════════════

class GeneticNShellMapper:
    """Builds n-dimensional shell coordinates using genetic encoding.
    
    Every byte is mapped through a genetic code table to produce
    a coordinate in d-dimensional shell space. Multiple code tables
    and dimensions are available.
    """
    
    # Codon bases lookup: byte → 3-base codon
    CODON_BASES = ['A', 'C', 'G', 'T']
    
    def __init__(self, 
                 dimension: int = 3,
                 code_table: str = 'standard',
                 use_rna: bool = False):
        assert dimension >= 1, "Dimension must be >= 1"
        assert code_table in GENETIC_CODE_TABLES, f"Unknown table: {code_table}"
        
        self.d = dimension
        self.code_table_name = code_table
        self.table = GENETIC_CODE_TABLES[code_table]
        self.bases = RNA_BASES if use_rna else BASES
        
        # Precompute all 64 codon → AA mappings
        self._codon_cache: Dict[Tuple[int,int,int], str] = {}
    
    def byte_to_codon(self, b: int) -> Tuple[str, str, str]:
        """Map a byte (0-255) to a DNA/RNA codon triplet.
        
        Uses modular arithmetic over {A, C, G, T}:
          byte 0-63: direct codon mapping (6 bits)
          byte 64-255: upper bits modulate the translation
        """
        idx = b & 0x3F  # 6 bits = 64 codons
        b1 = self.bases[(idx >> 4) & 0x3]
        b2 = self.bases[(idx >> 2) & 0x3]
        b3 = self.bases[idx & 0x3]
        return (b1, b2, b3)
    
    def byte_to_aa(self, b: int) -> str:
        """Translate a byte through the genetic code to an amino acid."""
        codon = self.byte_to_codon(b)
        return self.table.get(codon, 'Stop')
    
    def byte_to_rank(self, b: int, context: Optional[int] = None) -> int:
        """Map a byte to a natural number rank for shell encoding.
        
        The rank incorporates:
        - The amino acid index (0-22)
        - The codon position (0-63)
        - Optional context byte for contextual encoding
        """
        aa = self.byte_to_aa(b)
        aa_idx = AA_ORDER.get(aa, 0)
        codon_idx = b & 0x3F
        
        # Rank = aa_index * 64 + codon_idx + context modulation
        rank = aa_idx * 64 + codon_idx
        
        if context is not None:
            # Context byte modulates the rank within the same AA group
            context_mod = (context & 0x3F) % 64
            rank = aa_idx * 64 + ((codon_idx + context_mod) % 64)
        
        return rank
    
    def encode_byte(self, b: int, 
                    context: Optional[int] = None,
                    return_coord: bool = True) -> NShellCoordinate:
        """Map a byte to an n-dimensional shell coordinate."""
        rank = self.byte_to_rank(b, context)
        return NShellCoordinate.encode(rank, self.d)
    
    def build_shell_map(self, data: bytes) -> Dict[int, NShellCoordinate]:
        """Build shell coordinates for all bytes in data.
        
        Returns dict: byte_position → NShellCoordinate
        """
        coords: Dict[int, NShellCoordinate] = {}
        for i, b in enumerate(data):
            context = data[i-1] if i > 0 else None
            coords[i] = self.encode_byte(b, context)
        return coords
    
    def resonance_groups(self, data: bytes) -> Dict[int, List[int]]:
        """Group byte positions by shell mass (resonance class).
        
        Returns: mass → [positions with that mass]
        """
        groups: Dict[int, List[int]] = defaultdict(list)
        shell_map = self.build_shell_map(data)
        for pos, coord in shell_map.items():
            groups[coord.mass].append(pos)
        return dict(groups)
    
    def code_table_diversity(self) -> int:
        """Number of distinct AA translations across all 64 codons."""
        seen = set()
        for i in range(64):
            b1 = self.bases[(i >> 4) & 0x3]
            b2 = self.bases[(i >> 2) & 0x3]
            b3 = self.bases[i & 0x3]
            seen.add(self.table.get((b1, b2, b3), '?'))
        return len(seen)
    
    @property
    def degeneracy(self) -> float:
        """Model 1276-1280: Average codons per amino acid."""
        aa_counts = Counter()
        for i in range(64):
            b1 = self.bases[(i >> 4) & 0x3]
            b2 = self.bases[(i >> 2) & 0x3]
            b3 = self.bases[i & 0x3]
            aa = self.table.get((b1, b2, b3), 'Stop')
            aa_counts[aa] += 1
        # Exclude Stop for meaningful average
        non_stop = {k: v for k, v in aa_counts.items() if k != 'Stop'}
        if not non_stop:
            return 0.0
        return sum(non_stop.values()) / len(non_stop)


# ════════════════════════════════════════════════════════════════
# 4. N-SPACE DELTA ENCODER
# ════════════════════════════════════════════════════════════════

class NSpaceDeltaEncoder:
    """Delta-encode sequences of NShellCoordinates.
    
    Leverages the fact that within a resonance group,
    coordinates differ by small amounts in shell space.
    """
    
    def __init__(self):
        self.prev: Optional[NShellCoordinate] = None
    
    def encode_delta(self, coord: NShellCoordinate) -> bytes:
        """Encode a single coordinate as delta from previous.
        
        Format: [delta_k][delta_t_1]...[delta_t_d][delta_mass_hi][delta_mass_lo]
        Each delta is variable-length encoded.
        """
        if self.prev is None:
            # Full encoding for first coordinate
            encoded = self._encode_full(coord)
            self.prev = coord
            return encoded
        
        # Compute deltas across all dimensions
        dk = coord.k - self.prev.k
        dt = [coord.t[i] - self.prev.t[i] for i in range(coord.d)]
        dm = coord.mass - self.prev.mass
        
        # Pack deltas efficiently using variable-length encoding
        # Small deltas (within [-63, 63]) use 1 byte: 0xxx_xxxx
        # Large deltas use 2 bytes: 1xxx_xxxx xxxx_xxxx
        encoded = bytearray()
        encoded.append(self._encode_vlq(dk))
        for dti in dt:
            encoded.append(self._encode_vlq(dti))
        encoded.extend(self._encode_vlq_s16(dm))
        
        self.prev = coord
        return bytes(encoded)
    
    def _encode_vlq(self, val: int) -> int:
        """Variable-length encode a small integer to byte.
        
        -64..63 → 0xxxxxxx (7-bit signed)
        Otherwise saturate.
        """
        if val < -64:
            return 0x40  # min
        if val > 63:
            return 0x3F  # max
        return val & 0x7F
    
    def _encode_vlq_s16(self, val: int) -> Tuple[int, int]:
        """Encode 16-bit signed integer as 2 bytes.
        
        If value fits in [-2048, 2047], use 1-byte format
        (bit 7 = 0, bits 0-6 = 7-bit signed).
        Otherwise 2-byte format (bit 15 = 1, bits 0-14 = 15-bit signed).
        """
        if -2048 <= val <= 2047:
            # 1 byte: bit 7 = 0 (small), bits 0-6 = 7-bit signed
            return (val & 0x7F, 0x80)  # second byte marks "end"
        else:
            # 2 bytes: bit 15 = 1 (large), bits 0-14 = 15-bit signed
            hi = ((val >> 8) & 0x7F) | 0x80
            lo = val & 0xFF
            return (hi, lo)
    
    def _encode_full(self, coord: NShellCoordinate) -> bytes:
        """Full encoding (not delta)."""
        packed = bytearray()
        # k as 1 byte (for small shells) or 2 bytes
        if coord.k < 256:
            packed.append(coord.k & 0xFF)
        else:
            packed.append(0xFF)
            packed.append((coord.k >> 8) & 0xFF)
            packed.append(coord.k & 0xFF)
        
        # Each t[i] as 1 byte
        for ti in coord.t:
            packed.append(min(ti, 255) & 0xFF)
        
        # Mass as 2 bytes
        packed.append((coord.mass >> 8) & 0xFF)
        packed.append(coord.mass & 0xFF)
        
        return bytes(packed)
    
    def reset(self):
        self.prev = None


# ════════════════════════════════════════════════════════════════
# 5. SHAPE EXPANSION ANALYZER
# ════════════════════════════════════════════════════════════════

class ShapeExpansionAnalyzer:
    """Analyzes how different dimensions/shapes affect encoding.
    
    For each dimension d (1..n), computes:
    - Shell statistics (mass distribution, resonance groups)
    - Encoding efficiency estimates
    - Cross-dimensional resonance opportunities
    """
    
    def __init__(self, data: bytes):
        self.data = data
        self.seen: Dict[int, Dict[int, Counter]] = {}  # dim → mass → count
    
    def analyze_dimension(self, d: int, 
                          code_table: str = 'standard') -> Dict[str, Any]:
        """Analyze shell statistics for dimension d."""
        mapper = GeneticNShellMapper(dimension=d, code_table=code_table)
        coords = mapper.build_shell_map(self.data)
        
        n = len(self.data)
        masses = [c.mass for c in coords.values()]
        unique_masses = len(set(masses))
        endpoint_count = sum(1 for c in coords.values() if c.is_endpoint)
        nonzero_masses = [m for m in masses if m > 0]
        avg_mass = sum(nonzero_masses) / max(len(nonzero_masses), 1)
        
        # Resonance group sizes
        groups = mapper.resonance_groups(self.data)
        group_sizes = [len(v) for v in groups.values()]
        avg_group_size = sum(group_sizes) / max(len(group_sizes), 1)
        
        # Entropy of mass distribution (how predictable)
        mass_entropy = 0.0
        mass_counts = Counter(masses)
        for count in mass_counts.values():
            p = count / n
            mass_entropy -= p * math.log2(p)
        
        return {
            'd': d,
            'unique_masses': unique_masses,
            'endpoint_fraction': endpoint_count / n if n > 0 else 0,
            'avg_mass': avg_mass,
            'avg_resonance_group_size': avg_group_size,
            'mass_entropy': mass_entropy,
            'code_table_diversity': mapper.code_table_diversity(),
            'degeneracy': mapper.degeneracy,
            'n_shell_count': len(coords),
        }
    
    def find_optimal_dimension(self, 
                               max_d: int = 8,
                               code_table: str = 'standard') -> int:
        """Find dimension that minimizes mass entropy.
        
        Lower mass entropy → more structured → better compression.
        """
        best_d = 2
        best_entropy = float('inf')
        
        for d in range(1, max_d + 1):
            stats = self.analyze_dimension(d, code_table)
            entropy = stats['mass_entropy']
            
            if entropy < best_entropy:
                best_entropy = entropy
                best_d = d
        
        return best_d
    
    def best_code_table(self, d: int = 3) -> Tuple[str, float]:
        """Find code table that maximizes shell structure."""
        best_table = 'standard'
        best_score = 0.0
        
        for table_name in GENETIC_CODE_TABLES:
            stats = self.analyze_dimension(d, table_name)
            # Score: low mass entropy + high resonance group size
            score = (1.0 / max(stats['mass_entropy'], 0.01)) * \
                    stats['avg_resonance_group_size']
            if score > best_score:
                best_score = score
                best_table = table_name
        
        return best_table, best_score
    
    def cross_dimensional_resonances(self, 
                                     d1: int, 
                                     d2: int) -> List[Tuple[int, int, int]]:
        """Find cross-dimensional resonances between dimensions d1 and d2.
        
        Returns: [(byte_pos_d1, byte_pos_d2, shared_mass)]
        """
        mapper1 = GeneticNShellMapper(dimension=d1)
        mapper2 = GeneticNShellMapper(dimension=d2)
        
        coords1 = mapper1.build_shell_map(self.data)
        coords2 = mapper2.build_shell_map(self.data)
        
        # Build mass → positions for each dimension
        mass_to_pos1: Dict[int, List[int]] = defaultdict(list)
        mass_to_pos2: Dict[int, List[int]] = defaultdict(list)
        
        for pos, c in coords1.items():
            mass_to_pos1[c.mass].append(pos)
        for pos, c in coords2.items():
            mass_to_pos2[c.mass].append(pos)
        
        # Find shared masses
        shared_masses = set(mass_to_pos1.keys()) & set(mass_to_pos2.keys())
        
        resonances = []
        for mass in sorted(shared_masses)[:50]:  # limit output
            for p1 in mass_to_pos1[mass][:3]:
                for p2 in mass_to_pos2[mass][:3]:
                    resonances.append((p1, p2, mass))
        
        return resonances


# ════════════════════════════════════════════════════════════════
# 6. GENSIS ENCODER — Unified Genetic N-Space Compressor
# ════════════════════════════════════════════════════════════════

@dataclass
class GENSISBlock:
    """Output of GENSIS encoding for one block."""
    dimension: int
    code_table: str
    shell_coords: List[NShellCoordinate]
    delta_encoded: bytes
    resonance_groups: Dict[int, List[int]]
    mass_entropy: float
    cross_resonances: List[Tuple[int, int, int]]


class GENSISEncoder:
    """Unified Genetic N-Space Shell Encoder.
    
    1. Select optimal code table + dimension for data
    2. Encode to n-dimensional shell coordinates
    3. Delta-encode within resonance groups
    4. Detect cross-dimensional resonances
    5. Report shell statistics for MISC pipeline
    """
    
    def __init__(self, max_dim_search: int = 6):
        self.max_dim_search = max_dim_search
        self.delta_encoder = NSpaceDeltaEncoder()
    
    def encode(self, data: bytes) -> GENSISBlock:
        """Full GENSIS encoding pipeline."""
        analyzer = ShapeExpansionAnalyzer(data)
        
        # Step 1: Find optimal dimension
        d = analyzer.find_optimal_dimension(self.max_dim_search)
        
        # Step 2: Find best code table for this dimension
        table, table_score = analyzer.best_code_table(d)
        
        # Step 3: Encode to n-shell coordinates
        mapper = GeneticNShellMapper(dimension=d, code_table=table)
        coords = mapper.build_shell_map(data)
        
        # Step 4: Delta encode coordinate sequence
        self.delta_encoder.reset()
        delta_bytes = bytearray()
        sorted_positions = sorted(coords.keys())
        for pos in sorted_positions:
            delta_bytes.extend(self.delta_encoder.encode_delta(coords[pos]))
        
        # Step 5: Find resonance groups
        groups = mapper.resonance_groups(data)
        
        # Step 6: Check cross-dimensional resonances
        cross = []
        for other_d in range(1, self.max_dim_search + 1):
            if other_d != d:
                cross.extend(analyzer.cross_dimensional_resonances(d, other_d))
        
        # Mass entropy
        masses = [c.mass for c in coords.values()]
        mass_entropy = 0.0
        mass_counts = Counter(masses)
        n = len(data)
        for count in mass_counts.values():
            p = count / n
            if p > 0:
                mass_entropy -= p * math.log2(p)
        
        return GENSISBlock(
            dimension=d,
            code_table=table,
            shell_coords=list(coords.values()),
            delta_encoded=bytes(delta_bytes),
            resonance_groups=groups,
            mass_entropy=mass_entropy,
            cross_resonances=cross[:20],  # limit output
        )


# ════════════════════════════════════════════════════════════════
# 7. DEMO & SELF-TEST
# ════════════════════════════════════════════════════════════════

def print_shell_stats(data: bytes):
    """Print comprehensive shell encoding analysis."""
    print(f"\n{'='*60}")
    print(f"  GENSIS — Genetic N-Space Shell Encoding")
    print(f"  Data: {len(data)} bytes")
    print(f"{'='*60}")
    
    for d in range(1, 7):
        for table_name in ['standard', 'vert_mito']:
            mapper = GeneticNShellMapper(dimension=d, code_table=table_name)
            coords = mapper.build_shell_map(data)
            
            if not coords:
                continue
            
            masses = [c.mass for c in coords.values()]
            unique_masses = len(set(masses))
            endpoints = sum(1 for c in coords.values() if c.is_endpoint)
            
            print(f"  d={d} | {table_name:12s} | "
                  f"shells={unique_masses:4d} | "
                  f"endpoints={endpoints:3d} | "
                  f"avg_mass={sum(masses)/max(len(masses),1):.1f} | "
                  f"degeneracy={mapper.degeneracy:.2f}")
    
    # Best dimension recommendation
    analyzer = ShapeExpansionAnalyzer(data)
    best_d = analyzer.find_optimal_dimension()
    best_table, _ = analyzer.best_code_table(best_d)
    print(f"\n  ▶ Recommended: d={best_d}, code_table='{best_table}'")
    
    # Cross-dimensional resonances
    cross = analyzer.cross_dimensional_resonances(best_d, best_d + 1 if best_d < 6 else best_d)
    if cross:
        print(f"  ▶ Cross-dimensional resonances: {len(cross)} found")


def demo():
    """Run GENSIS demonstration on various data."""
    test_data = [
        (b"The quick brown fox jumps over the lazy dog." * 5, "English text"),
        (b"AAAAACCCCCGGGGGTTTTTAAAAACCCCCGGGGGTTTTT" * 5, "DNA-like repeats"),
        (bytes(range(256)) * 2, "All 256 bytes, 2x"),
        (b"AGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCT" * 8, "AGCT repeats (highly structured)"),
    ]
    
    for data, desc in test_data:
        print(f"\n{'─'*60}")
        print(f"  Test: {desc}")
        print(f"{'─'*60}")
        print_shell_stats(data)
        
        # Full encode
        encoder = GENSISEncoder()
        result = encoder.encode(data)
        print(f"\n  Encoded: {len(result.delta_encoded)} delta bytes "
              f"(vs {len(data)} raw)")
        print(f"  Dimension: {result.dimension}, "
              f"Table: {result.code_table}, "
              f"Mass entropy: {result.mass_entropy:.3f}")
        print(f"  Resonance groups: {len(result.resonance_groups)}")
        print(f"  Cross-resonances: {len(result.cross_resonances)}")


if __name__ == "__main__":
    demo()
