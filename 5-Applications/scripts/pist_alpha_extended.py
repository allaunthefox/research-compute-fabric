#!/usr/bin/env python3
"""
PIST Alpha Branch — Extended Manifold Encoding and Basis Adaptation
===================================================================
Experimental basis selection and coordinate encoding methods isolated
from the stable branch. All features are opt-in and formally unverified.

Methods implemented:
  - Constraint block encoding (simultaneous shell-level constraints)
  - Basis exchange via compatibility screening (ranked pool intersection)
  - Basis fusion via set intersection and bilinear operators
  - Composite manifold coordinates (tree × surface × torus × shell)
  - Programmable decoder architecture (data as instruction stream)
  - Substrate-independent basis extraction (remappable symbol sets)

This module imports from pist_biological_polymorphic_shifter_v3_complete
but does NOT modify it.
"""

import sys
import math
import random
import hashlib
from collections import Counter
from functools import lru_cache

sys.path.insert(0, '/home/allaun/Desktop')
from pist_biological_polymorphic_shifter_v3_complete import (
    Shifter, ManifoldState, pist_encode, pist_mass, pist_mirror,
    intrinsic_load, _pist_coords_from_bytes, _bytes_from_pist_coords,
    NExponent, Compressor, PHI
)


# ═══════════════════════════════════════════════════════════════════════
# CONSTRAINT BLOCK ENCODING
# ═══════════════════════════════════════════════════════════════════════

class ConstraintBlock:
    """Simultaneous constraint block for a single PIST shell.

    Captures all constraints on a shell at once rather than sequentially.
    The decoder resolves constraints to linear positions after the full
    block is received.
    """

    def __init__(self, shell_k, max_basis_dim=16):
        self.k = shell_k
        self.t_range = 2 * shell_k + 1
        self.constraints = {}  # t -> {byte_val, probability, mass}
        self.basis = None      # populated at block close
        self.max_basis_dim = max_basis_dim

    def add_constraint(self, t, byte_val, confidence=1.0):
        """Add a simultaneous constraint at position t on this shell."""
        mass = pist_mass(self.k, t)
        self.constraints[t] = {
            'byte': byte_val,
            'confidence': confidence,
            'mass': mass,
            'mirror_t': 2 * self.k + 1 - t,
        }

    def close_block(self):
        """Finalize the block: extract basis from constraint distribution."""
        if not self.constraints:
            self.basis = [0] * self.max_basis_dim
            return

        # Histogram from constrained bytes
        hist = Counter(c['byte'] for c in self.constraints.values())
        indexed = [(b, f) for b, f in hist.items()]
        indexed.sort(key=lambda x: x[1], reverse=True)
        self.basis = [b for b, _ in indexed[:self.max_basis_dim]]
        while len(self.basis) < self.max_basis_dim:
            self.basis.append(0)

    def to_bytes(self):
        """Serialize block for transmission."""
        self.close_block()
        result = bytearray()
        result.append(self.k & 0xFF)
        result.append(len(self.constraints) & 0xFF)
        result.append(self.max_basis_dim & 0xFF)
        result.extend(self.basis)
        for t, c in sorted(self.constraints.items()):
            result.append(t & 0xFF)
            result.append(c['byte'] & 0xFF)
            result.append(int(c['confidence'] * 255) & 0xFF)
        return bytes(result)

    @classmethod
    def from_bytes(cls, data):
        """Deserialize block."""
        k = data[0]
        n_constraints = data[1]
        basis_dim = data[2]
        basis = list(data[3:3 + basis_dim])
        block = cls(k, max_basis_dim=basis_dim)
        block.basis = basis
        ptr = 3 + basis_dim
        for _ in range(n_constraints):
            if ptr + 2 >= len(data):
                break
            t = data[ptr]
            byte_val = data[ptr + 1]
            confidence = data[ptr + 2] / 255.0
            block.add_constraint(t, byte_val, confidence)
            ptr += 3
        return block


# ═══════════════════════════════════════════════════════════════════════
# BASIS EXPANSION AND REDUCTION
# ═══════════════════════════════════════════════════════════════════════

class BasisExpansion:
    """Expand data into high-dimensional PIST shell, etch basis, refold.

    From data unfolding onto a high-k PIST shell, compute an AVMR basis
    across the surface, then refold by tracing out (removing) non-basis
    dimensions.
    """

    EXPANSION_K = 255  # Shell for dimensional expansion

    @classmethod
    def unfold(cls, data):
        """Map each byte to a point on the expansion shell surface."""
        coords = []
        for i, b in enumerate(data):
            rng = random.Random(int(hashlib.sha256(bytes([b, i & 0xFF])).hexdigest(), 16))
            t = rng.randint(0, 2 * cls.EXPANSION_K)
            coords.append((cls.EXPANSION_K, t, b))
        return coords

    @classmethod
    def etch_basis(cls, coords, dim=16):
        """Extract dominant directions from unfolded surface."""
        hist = Counter(c[2] for c in coords)
        indexed = [(b, f) for b, f in hist.items()]
        indexed.sort(key=lambda x: x[1], reverse=True)
        basis = [b for b, _ in indexed[:dim]]
        while len(basis) < dim:
            basis.append(0)
        return basis

    @classmethod
    def refold(cls, coords, basis):
        """Trace out non-basis dimensions."""
        basis_set = set(basis)
        reduced = [(k, t, b) for k, t, b in coords if b in basis_set]
        return reduced


# ═══════════════════════════════════════════════════════════════════════
# MUTUAL SIMULATION FOR SHARED BASIS
# ═══════════════════════════════════════════════════════════════════════

class MutualSimulation:
    """Encoder and decoder simulate each other's decision procedures to
    converge on a shared basis without explicit transmission.

    The equilibrium basis is the fixed point of mutual simulation.
    """

    SIMULATION_DEPTH = 3  # Iterations of mutual simulation

    @classmethod
    def negotiate_basis(cls, data_prefix, seed_basis, depth=None):
        """Iteratively refine basis via mutual simulation."""
        if depth is None:
            depth = cls.SIMULATION_DEPTH

        basis = list(seed_basis)
        for _ in range(depth):
            # Encoder simulates decoder: "given this basis, what would
            # the decoder's prediction residuals look like?"
            simulated_decoder_basis = cls._simulate_decoder(data_prefix, basis)
            # Decoder simulates encoder: "given the simulated decoder's
            # basis, what basis would the encoder have chosen?"
            basis = cls._simulate_encoder(data_prefix, simulated_decoder_basis)
        return basis

    @classmethod
    def _simulate_decoder(cls, prefix, encoder_basis):
        """Decoder builds its own basis from the prefix, then adjusts
        toward encoder's expected basis."""
        hist = Counter(prefix)
        indexed = [(b, f) for b, f in hist.items()]
        indexed.sort(key=lambda x: x[1], reverse=True)
        decoder_basis = [b for b, _ in indexed[:len(encoder_basis)]]
        while len(decoder_basis) < len(encoder_basis):
            decoder_basis.append(0)
        # Adjustment: move decoder basis toward encoder basis by 1/3
        adjusted = []
        for db, eb in zip(decoder_basis, encoder_basis):
            adjusted.append((2 * db + eb) // 3)
        return adjusted

    @classmethod
    def _simulate_encoder(cls, prefix, decoder_basis):
        """Encoder sees decoder's adjusted basis and re-optimizes."""
        # Encoder's re-optimization: blend decoder basis with prefix frequencies
        hist = Counter(prefix)
        indexed = [(b, f) for b, f in hist.items()]
        indexed.sort(key=lambda x: x[1], reverse=True)
        encoder_top = [b for b, _ in indexed[:len(decoder_basis)]]
        while len(encoder_top) < len(decoder_basis):
            encoder_top.append(0)
        # Blend: encoder gives 2/3 weight to its own preference
        blended = []
        for et, db in zip(encoder_top, decoder_basis):
            blended.append((2 * et + db) // 3)
        return blended


# ═══════════════════════════════════════════════════════════════════════
# ADAPTIVE PARAMETERS
# ═══════════════════════════════════════════════════════════════════════

class AdaptiveParameters:
    """Encoding parameters change based on PIST shell depth."""

    @classmethod
    def basis_dim_for_shell(cls, k):
        """Basis dimension increases with shell depth."""
        return min(4 + k // 32, 32)

    @classmethod
    def chiral_schedule_for_shell(cls, k):
        """Chirality schedule changes with shell depth."""
        if k < 64:
            return 'parity'
        elif k < 192:
            return 'shell_parity'
        else:
            return 'mass_threshold'

    @classmethod
    def confidence_threshold(cls, k):
        """Confidence threshold decreases with shell depth."""
        return max(0.5, 1.0 - k / 512.0)


# ═══════════════════════════════════════════════════════════════════════
# SUBSTRATE-INDEPENDENT BASIS EXTRACTION
# ═══════════════════════════════════════════════════════════════════════

class SubstrateIndependentBasis:
    """Substrate-independent basis extraction: any sufficiently complex
    pattern contains all computations. The qBasis isn't tied to byte-value
    space but to any isomorphism class.

    Here we provide a substrate mapping: the "bytes" can be remapped to
    any 256-element symbol set while preserving the O-AVMR structure.
    """

    SUBSTRATES = {
        'bytes': lambda x: x,
        'bit_parity': lambda x: sum(1 for c in bin(x).count('1')),
        'prime_residue': lambda x: x % 53,  # 53 is prime near 256/5
        'phi_scaled': lambda x: int((x * 1.618033988749894) % 256),
    }

    @classmethod
    def map_to_substrate(cls, data, substrate='bytes'):
        """Remap byte data to an alternative substrate."""
        fn = cls.SUBSTRATES.get(substrate, cls.SUBSTRATES['bytes'])
        return bytes(fn(b) & 0xFF for b in data)

    @classmethod
    def compute_isomorphic_basis(cls, data, substrate='bytes', dim=16):
        """Compute O-AVMR basis on a non-standard substrate."""
        mapped = cls.map_to_substrate(data, substrate)
        hist = Counter(mapped)
        indexed = [(b, f) for b, f in hist.items()]
        indexed.sort(key=lambda x: x[1], reverse=True)
        basis = [b for b, _ in indexed[:dim]]
        while len(basis) < dim:
            basis.append(0)
        return basis, mapped


# ═══════════════════════════════════════════════════════════════════════
# CONSTRAINT BLOCK SHIFTER (Alpha Branch Main Entry Point)
# ═══════════════════════════════════════════════════════════════════════

class ConstraintBlockShifter(Shifter):
    """Constraint block shifter: simultaneous shell-level encoding.

    Encode:
      1. Partition data into PIST shell blocks
      2. For each shell, build a ConstraintBlock
      3. Optionally: high-shell basis extraction and dimensional reduction
      4. Optionally: acausal basis negotiation
      5. Zone-adaptive parameters per shell depth
      6. Serialize blocks + metadata

    Decode:
      1. Read blocks
      2. Reconstruct basis per block
      3. Collapse constraints into linear sequence
      4. Apply inverse substrate mapping if used

    WARNING: Unverified. Use only in alpha exploration.
    """

    name = "constraint_block"
    description = "Constraint block encoding: simultaneous shell-level constraints (alpha)"

    # Feature flags for experimental methods
    # NOTE: high_shell_extraction and substrate_mapping are INTENTIONALLY
    # LOSSY. They drop data outside the dominant basis. Use only for
    # alpha exploration, not production compression.
    USE_HIGH_SHELL = True
    USE_ACAUSAL = True
    USE_ZONES = True
    USE_SUBSTRATE = False  # Experimental; no inverse mapping yet
    SUBSTRATE = 'bytes'

    @classmethod
    def _shells_from_data(cls, data):
        """Group bytes by their PIST shell k."""
        shells = {}
        for i, b in enumerate(data):
            k, t = pist_encode(i)
            if k not in shells:
                shells[k] = []
            shells[k].append((t, b, i))
        return shells

    @classmethod
    def encode(cls, state, **kwargs):
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)

        # Optional: remap to alternative substrate
        if cls.USE_SUBSTRATE and kwargs.get('substrate'):
            _, data = SubstrateIndependentBasis.compute_isomorphic_basis(
                data, kwargs.get('substrate'), dim=16
            )

        shells = cls._shells_from_data(data)
        blocks = []
        global_basis = None

        for k in sorted(shells.keys()):
            entries = shells[k]
            dim = AdaptiveParameters.basis_dim_for_shell(k) if cls.USE_ZONES else 16
            block = ConstraintBlock(k, max_basis_dim=dim)

            for t, b, original_pos in entries:
                conf = AdaptiveParameters.confidence_threshold(k) if cls.USE_ZONES else 1.0
                block.add_constraint(t, b, conf)

            block.close_block()

            # High-shell basis extraction for high-entropy shells
            if cls.USE_HIGH_SHELL and len(entries) > 32:
                coords = BasisExpansion.unfold(bytes(e[1] for e in entries))
                hs_basis = BasisExpansion.etch_basis(coords, dim=dim)
                reduced = BasisExpansion.refold(coords, hs_basis)
                block.basis = hs_basis
                block.constraints = {}
                for k2, t2, b2 in reduced:
                    block.add_constraint(t2, b2, 1.0)

            # Mutual simulation for shared basis across shells
            if cls.USE_ACAUSAL and global_basis is not None:
                prefix = bytes(e[1] for e in entries[:min(64, len(entries))])
                block.basis = MutualSimulation.negotiate_basis(
                    prefix, block.basis, depth=2
                )
            elif cls.USE_ACAUSAL:
                global_basis = list(block.basis)

            blocks.append(block)

        # Serialize
        result = bytearray()
        result.extend(len(blocks).to_bytes(2, 'big'))
        for block in blocks:
            block_bytes = block.to_bytes()
            result.extend(len(block_bytes).to_bytes(2, 'big'))
            result.extend(block_bytes)

        return state.update(bytes(result), cls.name,
                            {'n_shells': len(shells),
                             'n_blocks': len(blocks),
                             'alpha_features': {
                                 'high_shell': cls.USE_HIGH_SHELL,
                                 'acausal': cls.USE_ACAUSAL,
                                 'zones': cls.USE_ZONES,
                                 'substrate': cls.USE_SUBSTRATE,
                             }})

    @classmethod
    def decode(cls, state, **kwargs):
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)
        if len(data) < 2:
            return state.update(data, f"decode_{cls.name}")

        n_blocks = int.from_bytes(data[:2], 'big')
        ptr = 2
        blocks = []
        for _ in range(n_blocks):
            if ptr + 2 > len(data):
                break
            block_len = int.from_bytes(data[ptr:ptr + 2], 'big')
            ptr += 2
            if ptr + block_len > len(data):
                break
            block = ConstraintBlock.from_bytes(data[ptr:ptr + block_len])
            blocks.append(block)
            ptr += block_len

        # Collapse blocks into linear sequence
        result = bytearray()
        pos_map = {}
        for block in blocks:
            k = block.k
            for t, c in block.constraints.items():
                n = k * k + t
                pos_map[n] = c['byte']

        for i in range(max(pos_map.keys()) + 1) if pos_map else range(0):
            result.append(pos_map.get(i, 0))

        if cls.USE_SUBSTRATE and kwargs.get('substrate'):
            pass  # known limitation

        return state.update(bytes(result), f"decode_{cls.name}")


# ═══════════════════════════════════════════════════════════════════════
# STANDALONE TEST (does not touch stable branch)
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# ADAPTIVE BASIS SHIFTER — BASIS EXCHANGE VIA COMPATIBILITY SCREENING
# ═══════════════════════════════════════════════════════════════════════
#
# Basis selection via pool exchange and compatibility screening:
#   - Ranked basis pool construction (frequency-sorted vector sets)
#   - Memory buffer for prior transfers (redundancy prevention)
#   - Compatibility metric (inverse distance screening)
#   - Fitness screening (coverage improvement vs. resistance penalty)

class AdaptiveBasisShifter(Shifter):
    """Adaptive basis selection via pool exchange and compatibility screening.

    Core mechanisms:
      1. RANKED POOL: basis vectors sorted by frequency (fitness).
      2. MEMORY BUFFER: records prior transfers to prevent redundancy.
      3. COMPATIBILITY METRIC: inverse-distance match between donor
         vector and recipient basis.
      4. FITNESS SCREENING: new vector accepted only if coverage
         improvement exceeds resistance penalty.
    """

    name = "adaptive_basis"
    description = "Adaptive basis selection: pool exchange and compatibility screening"

    # ── Pool Parameters ──
    POOL_SIZE = 16           # basis slots per pool
    SHUFFLE_RATE = 0.3      # probability of pool exchange per block

    # ── Memory Buffer ──
    MEMORY_MAX = 64         # max memory entries (prior transfer records)
    MEMORY_MATCH_LEN = 4    # bytes of basis vector for memory identity

    # ── Compatibility Threshold ──
    COMPAT_THRESHOLD = 0.6   # compatibility score for successful transfer

    # ── Resistance Weight ──
    RESISTANCE_WEIGHT = 0.5  # how much existing basis resists new vectors

    @classmethod
    def _build_pool(cls, data):
        """Build a ranked pool of basis vectors.

        Each vector is a byte value with a fitness score (frequency).
        The pool is the transferable element that can be exchanged.
        """
        hist = Counter(data)
        vectors = [(b, f) for b, f in hist.items()]
        vectors.sort(key=lambda x: x[1], reverse=True)
        while len(vectors) < cls.POOL_SIZE:
            vectors.append((0, 0))
        return vectors[:cls.POOL_SIZE]

    @classmethod
    def _memory_match(cls, memory, candidate):
        """Memory buffer check: has this basis vector been transferred before?

        Returns True if candidate matches any memory entry (prevents
        redundant acquisition via known-sequence filtering).
        """
        c_bytes = candidate.to_bytes(1, 'big')
        for entry in memory:
            if entry[:cls.MEMORY_MATCH_LEN] == c_bytes[:cls.MEMORY_MATCH_LEN]:
                return True
        return False

    @classmethod
    def _compatibility_metric(cls, donor_vec, recipient_basis):
        """Compatibility: how well does the donor vector match recipient?

        Inverse byte-distance to nearest basis vector.
        """
        if not recipient_basis:
            return 0.0
        min_dist = min(abs(donor_vec - rb) for rb in recipient_basis if rb != 0)
        similarity = 1.0 - (min_dist / 256.0)
        return similarity

    @classmethod
    def _fitness_screen(cls, donor_vec, recipient_basis):
        """Fitness screening: does the new vector improve coverage?

        A new basis vector is accepted only if it increases overall
        coverage more than the resistance penalty.
        """
        if not recipient_basis:
            return True
        current_coverage = len(set(recipient_basis) - {0})
        new_coverage = len(set(recipient_basis + [donor_vec]) - {0})
        improvement = (new_coverage - current_coverage) / cls.POOL_SIZE
        penalty = cls.RESISTANCE_WEIGHT * (current_coverage / cls.POOL_SIZE)
        return improvement > penalty

    @classmethod
    def _exchange_vectors(cls, donor_pool, recipient_basis, memory):
        """Transfer compatible vectors from donor pool to recipient.

        Steps:
          1. Form donor pool (vector collection)
          2. Compatibility screening (recipient matching)
          3. Memory buffer check (redundancy rejection)
          4. Fitness integration (coverage acceptance)
          5. Memory acquisition (record successful transfer)
        """
        new_basis = list(recipient_basis)
        new_memory = list(memory)

        for vec, freq in donor_pool:
            if len(new_basis) >= cls.POOL_SIZE:
                break
            if freq == 0:
                continue

            compat = cls._compatibility_metric(vec, new_basis)
            if compat < cls.COMPAT_THRESHOLD:
                continue

            if cls._memory_match(new_memory, vec):
                continue

            if not cls._fitness_screen(vec, new_basis):
                continue

            new_basis.append(vec)
            new_memory.append(vec.to_bytes(1, 'big'))
            if len(new_memory) > cls.MEMORY_MAX:
                new_memory.pop(0)

        return new_basis[:cls.POOL_SIZE], new_memory

    @classmethod
    def encode(cls, state, **kwargs):
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)

        # Build local pool (recipient basis)
        recipient_pool = cls._build_pool(data)
        recipient_basis = [v for v, _ in recipient_pool[:cls.POOL_SIZE]]

        # Build donor pool from prefix (simulated external basis)
        prefix_len = min(64, len(data))
        donor_pool = cls._build_pool(data[:prefix_len])

        # Memory buffer: initialized from prior transfers
        memory = kwargs.get('memory_history', [])

        # Vector exchange
        new_basis, new_memory = cls._exchange_vectors(
            donor_pool, recipient_basis, memory
        )

        # Shuffle: probabilistic vector rearrangement (pool dynamics)
        rng = random.Random(int(hashlib.sha256(data[:16]).hexdigest(), 16))
        if rng.random() < cls.SHUFFLE_RATE:
            i, j = rng.sample(range(len(new_basis)), 2)
            new_basis[i], new_basis[j] = new_basis[j], new_basis[i]

        result = bytearray()
        result.append(len(new_basis))
        result.extend(new_basis)
        result.append(len(new_memory))
        for entry in new_memory[:cls.MEMORY_MAX]:
            result.extend(entry)

        seed = int(hashlib.sha256(bytes(new_basis)).hexdigest(), 16)
        rng2 = random.Random(seed)
        ks = bytearray(len(data))
        for i in range(len(data)):
            region = (i // max(1, len(data) // 256)) % 256
            base = new_basis[region % len(new_basis)] if new_basis else 0
            detail = rng2.randint(0, 63)
            ks[i] = (base ^ detail) & 0xFF

        for i, b in enumerate(data):
            result.append(b ^ ks[i])

        return state.update(bytes(result), cls.name,
                            {'pool_size': len(new_basis),
                             'memory_entries': len(new_memory),
                             'exchange_events': len(new_basis) - len(recipient_basis),
                             'shuffled': rng.random() < cls.SHUFFLE_RATE})

    @classmethod
    def decode(cls, state, **kwargs):
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)
        if len(data) < 2:
            return state.update(data, f"decode_{cls.name}")

        basis_len = data[0]
        offset = 1
        basis = list(data[offset:offset + basis_len])
        offset += basis_len

        n_memory = data[offset]
        offset += 1
        memory = []
        for _ in range(n_memory):
            if offset < len(data):
                memory.append(bytes([data[offset]]))
                offset += 1

        residuals = data[offset:]

        seed = int(hashlib.sha256(bytes(basis)).hexdigest(), 16)
        rng = random.Random(seed)
        ks = bytearray(len(residuals))
        for i in range(len(residuals)):
            region = (i // max(1, len(residuals) // 256)) % 256
            base = basis[region % len(basis)] if basis else 0
            detail = rng.randint(0, 63)
            ks[i] = (base ^ detail) & 0xFF

        result = bytearray()
        for i, b in enumerate(residuals):
            result.append(b ^ ks[i])

        return state.update(bytes(result), f"decode_{cls.name}")


# ═══════════════════════════════════════════════════════════════════════
# BASIS FUSION SHIFTER — SET INTERSECTION AND BILINEAR COMBINATION
# ═══════════════════════════════════════════════════════════════════════
#
# Mathematical model for combining two basis sets via a common
# substructure (intersection) and a bilinear operator on the non-intersecting
# arms.
#
# Structure:
#   Intersection = basis_A ∩ basis_B    (common directions)
#   Left         = basis_A \ intersection (A-specific directions)
#   Right        = basis_B \ intersection (B-specific directions)
#   Bridge       = Ψ(left, right)         (hybrid directions from fusion)
#
# Ψ (bridge operator) options:
#   hadamard : element-wise product  (a * b) % 256
#   xor      : bitwise XOR           (a ^ b)
#   wedge    : anti-symmetric pair   (a, b) as 2D subspace
#   tensor   : Kronecker product      (higher-dimensional, then truncate)

class BasisFusionShifter(Shifter):
    """Basis fusion: combine two basis sets via intersection and bridge operator.

    Takes two basis sets, extracts their intersection, and fuses the
    remaining arms via a bilinear operator to create a hybrid basis with
    higher representational capacity than either parent.
    """

    name = "basis_fusion"
    description = "Basis fusion: set intersection and bilinear combination of basis sets"

    # Bridge operators
    BRIDGE_OPS = {
        'hadamard': lambda a, b: ((a * b) & 0xFF),
        'xor':      lambda a, b: (a ^ b) & 0xFF,
        'wedge':    lambda a, b: ((a * 256 + b) & 0xFFFF) % 256,  # project 2D to 1D
        'tensor':   lambda a, b: ((a << 4) | (b & 0x0F)) & 0xFF,  # nibble-pair
        'mean':     lambda a, b: ((a + b) // 2) & 0xFF,
    }

    @classmethod
    def _extract_intersection(cls, basis_a, basis_b):
        """Intersection: common directions between two basis sets."""
        set_a = set(basis_a)
        set_b = set(basis_b)
        intersection = sorted(set_a & set_b)
        left = sorted(set_a - set_b)
        right = sorted(set_b - set_a)
        return intersection, left, right

    @classmethod
    def _fuse_bridge(cls, left, right, operator='hadamard', max_bridge=8):
        """Apply bridge operator to all pairs from left and right arms.

        Returns up to max_bridge unique hybrid vectors.
        """
        op = cls.BRIDGE_OPS.get(operator, cls.BRIDGE_OPS['hadamard'])
        hybrids = set()
        for a in left:
            for b in right:
                h = op(a, b)
                hybrids.add(h)
                if len(hybrids) >= max_bridge:
                    break
            if len(hybrids) >= max_bridge:
                break
        return sorted(hybrids)

    @classmethod
    def _build_fused_basis(cls, basis_a, basis_b, operator='hadamard', max_dim=16):
        """Construct fused basis: intersection + bridge + overflow from arms.

        Priority ordering:
          1. Intersection (common to both parents)
          2. Bridge (hybrid vectors — novel combination)
          3. Left overflow (A-specific, if room)
          4. Right overflow (B-specific, if room)
        """
        intersection, left, right = cls._extract_intersection(basis_a, basis_b)
        bridge = cls._fuse_bridge(left, right, operator, max_bridge=max_dim // 2)

        fused_basis = list(intersection)
        fused_basis.extend(bridge)

        # Fill remaining slots from left/right alternately
        alt = True
        for i in range(max_dim - len(fused_basis)):
            src = left if alt else right
            alt = not alt
            if i < len(src):
                fused_basis.append(src[i])
            elif i < len(left) + len(right):
                other = right if src is left else left
                idx = i - len(src)
                if idx < len(other):
                    fused_basis.append(other[idx])
            else:
                fused_basis.append(0)

        while len(fused_basis) < max_dim:
            fused_basis.append(0)

        return fused_basis[:max_dim], {
            'intersection': intersection,
            'left': left,
            'right': right,
            'bridge': bridge,
            'operator': operator,
        }

    @classmethod
    def _basis_from_data(cls, data, dim=16):
        """Extract a basis set from byte data."""
        hist = Counter(data)
        basis = [b for b, _ in hist.most_common(dim)]
        while len(basis) < dim:
            basis.append(0)
        return basis

    @classmethod
    def encode(cls, state, **kwargs):
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)

        # Basis A: from full data
        hist_a = Counter(data)
        basis_a = [b for b, _ in hist_a.most_common(16)]
        while len(basis_a) < 16:
            basis_a.append(0)

        # Basis B: from prefix (simulated external source)
        prefix_len = min(64, len(data))
        hist_b = Counter(data[:prefix_len])
        basis_b = [b for b, _ in hist_b.most_common(16)]
        while len(basis_b) < 16:
            basis_b.append(0)

        operator = kwargs.get('bridge_operator', 'hadamard')
        max_dim = kwargs.get('max_dim', 16)
        fused_basis, anatomy = cls._build_fused_basis(
            basis_a, basis_b, operator=operator, max_dim=max_dim
        )

        result = bytearray()
        result.append(len(basis_a))
        result.extend(basis_a)
        result.append(len(basis_b))
        result.extend(basis_b)
        result.append(len(fused_basis))
        result.extend(fused_basis)
        result.append(anatomy['operator'].encode()[0] if isinstance(anatomy['operator'], str) else ord('h'))

        seed = int(hashlib.sha256(bytes(fused_basis)).hexdigest(), 16)
        rng = random.Random(seed)
        ks = bytearray(len(data))
        for i in range(len(data)):
            region = (i // max(1, len(data) // 256)) % 256
            base = fused_basis[region % len(fused_basis)] if fused_basis else 0
            detail = rng.randint(0, 63)
            ks[i] = (base ^ detail) & 0xFF

        for i, b in enumerate(data):
            result.append(b ^ ks[i])

        return state.update(bytes(result), cls.name,
                            {'fusion_anatomy': anatomy,
                             'fused_dim': len(fused_basis),
                             'intersection_size': len(anatomy['intersection']),
                             'bridge_size': len(anatomy['bridge']),
                             'operator': operator})

    @classmethod
    def decode(cls, state, **kwargs):
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)
        if len(data) < 4:
            return state.update(data, f"decode_{cls.name}")

        ptr = 0
        len_a = data[ptr]; ptr += 1
        basis_a = list(data[ptr:ptr + len_a]); ptr += len_a
        len_b = data[ptr]; ptr += 1
        basis_b = list(data[ptr:ptr + len_b]); ptr += len_b
        len_tri = data[ptr]; ptr += 1
        tri_basis = list(data[ptr:ptr + len_tri]); ptr += len_tri
        _op_byte = data[ptr] if ptr < len(data) else ord('h'); ptr += 1

        residuals = data[ptr:]

        # Reconstruct keystream from tri-chiral basis
        seed = int(hashlib.sha256(bytes(tri_basis)).hexdigest(), 16)
        rng = random.Random(seed)
        ks = bytearray(len(residuals))
        for i in range(len(residuals)):
            region = (i // max(1, len(residuals) // 256)) % 256
            base = tri_basis[region % len(tri_basis)] if tri_basis else 0
            detail = rng.randint(0, 63)
            ks[i] = (base ^ detail) & 0xFF

        result = bytearray()
        for i, b in enumerate(residuals):
            result.append(b ^ ks[i])

        return state.update(bytes(result), f"decode_{cls.name}")


# ═══════════════════════════════════════════════════════════════════════
# COMPOSITE COORDINATE SHIFTER
# ═══════════════════════════════════════════════════════════════════════
#
# Encodes into a composite coordinate system with multiple geometric
# components derived from a single integer position:
#   - Tree address: recursive base-20 traversal
#   - Surface coordinates: 1/x surface of revolution mapping
#   - Toroidal angles: multi-periodic angular coordinates
#   - PIST shell: number-theoretic decomposition
#
# The address for byte position n is a structured tuple:
#   (tree_addr, surface_x_y_theta, torus_angles, pist_k_t)
#
# All coordinates are derived from n deterministically. No storage
# overhead for the geometric structure.

class CompositeCoordinateShifter(Shifter):
    """Composite coordinate system: tree × surface × torus × shell."""

    name = "composite_coordinate"
    description = "Composite coordinate system: tree, surface, torus, and shell encoding"

    # ── Menger Sponge ──
    SPONGE_LEVELS = 3  # recursion depth (each level: 20 valid sub-cubes from 27)

    # ── Gabriel's Horn ──
    HORN_MIN_X = 1.0   # x >= 1 for y = 1/x
    HORN_MAX_X = 256.0 # finite truncation

    # ── Hypertorus (4D: 3 angles + 2 radii) ──
    TORUS_MAJOR_R = 3.0  # R
    TORUS_MINOR_R = 1.0  # r

    @classmethod
    def _menger_sponge_node(cls, n, level=0):
        """Map position n to Menger sponge coordinates (level, subcube_index).

        At each level, the cube divides into 3x3x3 = 27 subcubes.
        The Menger sponge removes the center cube of each face and
        the very center: 27 - 7 = 20 valid subcubes per level.
        """
        if level >= cls.SPONGE_LEVELS:
            return (level, n % 20)

        # Which of the 20 valid subcubes does n fall into?
        subcube = n % 20
        remaining = n // 20
        return cls._menger_sponge_node(remaining, level + 1)

    @classmethod
    def _sponge_address(cls, n):
        """Full Menger sponge address as list of (level, subcube) tuples."""
        addr = []
        remaining = n
        for level in range(cls.SPONGE_LEVELS):
            subcube = remaining % 20
            addr.append((level, subcube))
            remaining //= 20
        return addr

    @classmethod
    def _gabriels_horn_surface(cls, n):
        """Map position to Gabriel's horn surface coordinates (x, y, theta).

        x ranges from HORN_MIN_X to HORN_MAX_X.
        y = 1/x (the horn radius at position x).
        theta is the azimuthal angle around the horn's axis.
        """
        # Distribute n across the horn's length
        x = cls.HORN_MIN_X + (n % 255) * (cls.HORN_MAX_X - cls.HORN_MIN_X) / 255.0
        y = 1.0 / x  # horn radius
        theta = (n * PHI) % (2 * math.pi)  # irrational rotation for uniform coverage
        return x, y, theta

    @classmethod
    def _hypertorus_angles(cls, n):
        """Map position to hypertorus angular coordinates (theta, phi, psi).

        A 4D torus has three independent angles. We derive them from n
        using irrational rotations to avoid periodic overlap.
        """
        theta = (n * PHI) % (2 * math.pi)
        phi = (n * PHI * PHI) % (2 * math.pi)
        psi = (n * PHI * PHI * PHI) % (2 * math.pi)
        return theta, phi, psi

    @classmethod
    def _composite_address(cls, n):
        """Full address: (tree_addr, surface_coords, torus_angles, pist_coords).

        A structured tuple derived from a single scalar n. All coordinates
        are deterministic functions of n.
        """
        tree = cls._sponge_address(n)
        horn_x, horn_y, horn_theta = cls._gabriels_horn_surface(n)
        torus_theta, torus_phi, torus_psi = cls._hypertorus_angles(n)
        pist_k, pist_t = pist_encode(n)
        return {
            'sponge': tree,
            'horn': (horn_x, horn_y, horn_theta),
            'torus': (torus_theta, torus_phi, torus_psi),
            'pist': (pist_k, pist_t),
            'linear': n,
        }

    @classmethod
    def _composite_keystream(cls, data, seed_basis):
        """Generate keystream from composite coordinate traversal.

        Each byte's keystream value is a function of its position's
        composite coordinates. Tree depth, surface curvature, and torus
        angles all modulate the output.
        """
        seed = int(hashlib.sha256(bytes(seed_basis)).hexdigest(), 16)
        rng = random.Random(seed)
        ks = bytearray(len(data))

        for i in range(len(data)):
            addr = cls._composite_address(i)
            sponge_level = addr['sponge'][0][0] if addr['sponge'] else 0
            sponge_sub = addr['sponge'][0][1] if addr['sponge'] else 0
            horn_x, horn_y, horn_theta = addr['horn']
            torus_theta, torus_phi, torus_psi = addr['torus']
            pist_k, pist_t = addr['pist']

            sponge_mod = (sponge_level * 32 + sponge_sub * 4) & 0xFF
            horn_mod = int((horn_theta / (2 * math.pi)) * 255) & 0xFF
            torus_mod = int(
                (math.sin(torus_theta) + math.cos(torus_phi) + math.sin(torus_psi)) * 64
            ) & 0xFF

            mass = pist_mass(pist_k, pist_t)
            pist_mod = (mass * 8) & 0xFF

            base = seed_basis[i % len(seed_basis)] if seed_basis else 128
            detail = rng.randint(0, 31)
            ks[i] = (base ^ sponge_mod ^ horn_mod ^ torus_mod ^ pist_mod ^ detail) & 0xFF

        return ks

    @classmethod
    def encode(cls, state, **kwargs):
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)

        # Basis from data histogram
        hist = Counter(data)
        basis = [b for b, _ in hist.most_common(16)]
        while len(basis) < 16:
            basis.append(0)

        # Keystream from composite coordinates
        ks = cls._composite_keystream(data, basis)

        result = bytearray()
        result.extend(basis)
        for i, b in enumerate(data):
            result.append(b ^ ks[i])

        n_positions = len(data)
        sponge_depths = Counter()
        horn_ys = []
        for i in range(n_positions):
            addr = cls._composite_address(i)
            if addr['sponge']:
                sponge_depths[addr['sponge'][0][0]] += 1
            horn_ys.append(addr['horn'][1])

        return state.update(bytes(result), cls.name,
                            {'basis_dim': len(basis),
                             'sponge_levels': dict(sponge_depths),
                             'horn_y_range': (min(horn_ys), max(horn_ys)),
                             'n_positions': n_positions,
                             'manifold_dims': 9})

    @classmethod
    def decode(cls, state, **kwargs):
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)
        if len(data) < 16:
            return state.update(data, f"decode_{cls.name}")

        basis = list(data[:16])
        residuals = data[16:]

        ks = cls._composite_keystream(residuals, basis)

        result = bytearray()
        for i, b in enumerate(residuals):
            result.append(b ^ ks[i])

        return state.update(bytes(result), f"decode_{cls.name}")


# ═══════════════════════════════════════════════════════════════════════
# PROGRAMMABLE DECODER SHIFTER — DATA AS INSTRUCTION STREAM
# ═══════════════════════════════════════════════════════════════════════
#
# During decompression, each byte is interpreted as an instruction
# that traverses the PIST manifold and mutates decoder state. The
# decoded output is computed rather than directly stored.
#
# Architecture:
#   - Data byte = instruction opcode
#   - PIST (k,t) = instruction address
#   - ManifoldState.metadata = decoder registers
#   - Basis vectors = arithmetic operands
#
# The decoder is a register machine where the compressed stream
# serves as the instruction sequence.

class ProgrammableDecoderShifter(Shifter):
    """Programmable decoder: data interpreted as instruction stream."""

    name = "programmable_decoder"
    description = "Programmable decoder: data as instruction stream for manifold traversal"

    # ── CPU Registers (stored in ManifoldState.metadata) ──
    REGISTERS = ['acc', 'pc', 'sp', 'flags', 'entropy', 'depth']

    # ── Instruction Set (each data byte is an instruction) ──
    # Opcodes derived from byte value mod 8
    OPCODES = {
        0: 'NOOP',     # No operation
        1: 'LOAD',     # Load basis[acc] into acc
        2: 'STORE',    # Store acc into spacer memory
        3: 'ADD',      # Add projected coefficient to acc
        4: 'XOR',      # XOR with mirror LUT prediction
        5: 'BRANCH',   # If mass > threshold, skip next n instructions
        6: 'FUSE',     # Fuse current basis with parent's basis
        7: 'HALT',     # Stop processing, emit acc
    }

    @classmethod
    def _decode_instruction(cls, byte_val, pos):
        """Decode a data byte into (opcode, operand, PIST coordinates)."""
        k, t = pist_encode(pos)
        opcode = byte_val % 8
        operand = (byte_val // 8) & 0x1F  # 5-bit operand
        mass = pist_mass(k, t)
        mirror_pos = k * k + (2 * k + 1 - t) if k > 0 else 0
        return {
            'opcode': cls.OPCODES.get(opcode, 'NOOP'),
            'operand': operand,
            'k': k, 't': t,
            'mass': mass,
            'mirrored': mirror_pos,
        }

    @classmethod
    def _execute(cls, instr, state, basis, stack):
        """Execute one instruction, mutating state (registers)."""
        regs = state.metadata.get('programmable_decoder', {}).get('registers', {
            'acc': 0, 'pc': 0, 'sp': 0, 'flags': 0, 'entropy': 0.0, 'depth': 0
        })
        op = instr['opcode']
        operand = instr['operand']
        k, t = instr['k'], instr['t']
        mass = instr['mass']

        if op == 'NOOP':
            pass

        elif op == 'LOAD':
            # Load basis vector at index operand
            idx = operand % max(len(basis), 1)
            regs['acc'] = basis[idx] if basis else 0

        elif op == 'STORE':
            # Push acc onto data stack
            stack.append(bytes([regs['acc'] & 0xFF]))
            if len(stack) > 64:
                stack.pop(0)

        elif op == 'ADD':
            # Add projected coefficient: mass * operand / 256
            coeff = (mass * operand) // 256
            regs['acc'] = (regs['acc'] + coeff) & 0xFF

        elif op == 'XOR':
            # XOR with mirror LUT prediction
            mirror_pos = instr['mirrored']
            mk, mt = pist_encode(mirror_pos)
            mmass = pist_mass(mk, mt)
            prediction = (mmass * 4 + (mk & 1) * 16) & 0xFF
            regs['acc'] = (regs['acc'] ^ prediction ^ operand) & 0xFF

        elif op == 'BRANCH':
            # Conditional skip: if mass > threshold, skip operand bytes
            threshold = operand * 8
            if mass > threshold:
                regs['pc'] = regs.get('pc', 0) + operand
                regs['flags'] = 1  # branch taken
            else:
                regs['flags'] = 0

        elif op == 'FUSE':
            # Perform fusion bridge between current basis and a
            # "parent" basis derived from operand
            parent_seed = operand * 7 + 13
            parent_basis = [(b + parent_seed) & 0xFF for b in basis]
            if basis and parent_basis:
                spine = list(set(basis) & set(parent_basis))
                bridge = [(a ^ b) & 0xFF for a in basis[:4] for b in parent_basis[:4]]
                new_basis = (spine + bridge)[:16]
                basis[:] = new_basis + [0] * (16 - len(new_basis))

        elif op == 'HALT':
            # Emit accumulator and pause
            regs['flags'] = 2  # halt signal

        # Update entropy register
        regs['entropy'] = (regs['entropy'] * 0.9 + (mass / 1000.0) * 0.1)
        regs['depth'] = k
        regs['pc'] = regs.get('pc', 0) + 1

        return regs

    @classmethod
    def encode(cls, state, **kwargs):
        """Encode by compiling data into weird machine program.

        The "program" is the data itself — each byte is an instruction.
        The encoding is just the data + bootstrap basis prefix.
        """
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)

        # Bootstrap basis from data histogram
        hist = Counter(data)
        basis = [b for b, _ in hist.most_common(16)]
        while len(basis) < 16:
            basis.append(0)

        # The program IS the data — no transformation needed
        # The decoder computes during decompression
        result = bytearray()
        result.extend(basis)
        result.extend(data)

        return state.update(bytes(result), cls.name,
                            {'programmable_decoder': {
                                'basis': basis,
                                'program_length': len(data),
                            }})

    @classmethod
    def decode(cls, state, **kwargs):
        """Decode by executing the instruction stream.

        Each byte is fetched, decoded to (opcode, operand, PIST coord),
        and executed. The accumulator register collects output bytes.
        """
        data = bytes(state.encoded) if state.encoded else bytes(state.raw_bytes)
        if len(data) < 16:
            return state.update(data, f"decode_{cls.name}")

        basis = list(data[:16])
        program = data[16:]
        stack = []

        # Initialize registers
        machine_state = ManifoldState(b'')
        machine_state.metadata['programmable_decoder'] = {
            'registers': {'acc': 0, 'pc': 0, 'sp': 0, 'flags': 0, 'entropy': 0.0, 'depth': 0}
        }

        result = bytearray()
        for pos, b in enumerate(program):
            instr = cls._decode_instruction(b, pos)
            regs = cls._execute(instr, machine_state, basis, stack)
            machine_state.metadata['programmable_decoder']['registers'] = regs

            # HALT emits accumulator
            if regs['flags'] == 2:
                result.append(regs['acc'])
                regs['flags'] = 0  # resume

            # Normal execution: after each instruction, emit acc if PC even
            # This creates a computation-to-output mapping
            if regs['pc'] % 2 == 0 and regs['flags'] != 2:
                result.append(regs['acc'])

        return state.update(bytes(result), f"decode_{cls.name}")


def test_alpha():
    print("=" * 70)
    print("PIST Alpha Branch — Extended Manifold Encoding and Basis Adaptation")
    print("Unverified. Use only for concept exploration.")
    print("=" * 70)

    test_data = b"Hello, extended manifold encoding across PIST shells!"
    print(f"\nOriginal: {test_data}")

    state = ManifoldState(test_data)
    encoded = ConstraintBlockShifter.encode(state)
    meta = encoded.metadata.get('constraint_block', {})
    print(f"Encoded size: {len(encoded.encoded)} bytes")
    print(f"Shells: {meta.get('n_shells')}")
    print(f"Features: {meta.get('alpha_features')}")

    decoded = ConstraintBlockShifter.decode(encoded)
    result = bytes(decoded.encoded)
    print(f"Decoded: {result}")
    print(f"Roundtrip: {result == test_data}")

    # Test with larger data
    import random
    rng = random.Random(42)
    large = bytes(rng.randint(0, 255) for _ in range(500))
    s2 = ManifoldState(large)
    e2 = ConstraintBlockShifter.encode(s2)
    d2 = ConstraintBlockShifter.decode(e2)
    print(f"\nLarge roundtrip (500 bytes): {bytes(d2.encoded) == large}")

    # Test feature toggles
    print("\n--- Feature toggle tests ---")
    for high_shell, acausal, zones in [(False, False, False), (True, False, False),
                                       (False, True, False), (False, False, True),
                                       (True, True, True)]:
        ConstraintBlockShifter.USE_HIGH_SHELL = high_shell
        ConstraintBlockShifter.USE_ACAUSAL = acausal
        ConstraintBlockShifter.USE_ZONES = zones
        s = ManifoldState(test_data)
        enc = ConstraintBlockShifter.encode(s)
        dec = ConstraintBlockShifter.decode(enc)
        ok = bytes(dec.encoded) == test_data
        print(f"  high_shell={high_shell} acausal={acausal} zones={zones}: roundtrip={ok}")

    # Restore defaults
    ConstraintBlockShifter.USE_HIGH_SHELL = True
    ConstraintBlockShifter.USE_ACAUSAL = True
    ConstraintBlockShifter.USE_ZONES = True

    # ── Adaptive Basis Tests ──
    print("\n--- Adaptive basis tests ---")
    s = ManifoldState(test_data)
    enc = AdaptiveBasisShifter.encode(s)
    dec = AdaptiveBasisShifter.decode(enc)
    ok = bytes(dec.encoded) == test_data
    meta_ab = enc.metadata.get('adaptive_basis', {})
    print(f"  Basis exchange roundtrip: {ok}")
    print(f"  Pool size: {meta_ab.get('pool_size')}")
    print(f"  Memory entries: {meta_ab.get('memory_entries')}")
    print(f"  Exchange events: {meta_ab.get('exchange_events')}")

    # Basis exchange with memory history (simulated prior transfers)
    memory = [bytes([0x48]), bytes([0x65])]
    s2 = ManifoldState(test_data)
    enc2 = AdaptiveBasisShifter.encode(s2, memory_history=memory)
    meta2 = enc2.metadata.get('adaptive_basis', {})
    print(f"  Exchange with memory: events={meta2.get('exchange_events')}, entries={meta2.get('memory_entries')}")

    # Large data
    s3 = ManifoldState(large)
    enc3 = AdaptiveBasisShifter.encode(s3)
    dec3 = AdaptiveBasisShifter.decode(enc3)
    print(f"  Exchange large roundtrip: {bytes(dec3.encoded) == large}")

    # ── Basis Fusion Tests ──
    print("\n--- Basis fusion tests ---")
    for op in ['hadamard', 'xor', 'wedge', 'tensor', 'mean']:
        s = ManifoldState(test_data)
        enc = BasisFusionShifter.encode(s, bridge_operator=op)
        dec = BasisFusionShifter.decode(enc)
        ok = bytes(dec.encoded) == test_data
        meta = enc.metadata.get('basis_fusion', {})
        anat = meta.get('fusion_anatomy', {})
        print(f"  {op:10s}: roundtrip={ok}  intersection={len(anat.get('intersection', []))}  bridge={len(anat.get('bridge', []))}")

    # Large data
    s4 = ManifoldState(large)
    enc4 = BasisFusionShifter.encode(s4, bridge_operator='hadamard')
    dec4 = BasisFusionShifter.decode(enc4)
    print(f"  Fusion large roundtrip: {bytes(dec4.encoded) == large}")

    # Cross-substrate fusion
    basis_a, _ = SubstrateIndependentBasis.compute_isomorphic_basis(test_data, 'bytes', dim=16)
    basis_b, _ = SubstrateIndependentBasis.compute_isomorphic_basis(test_data, 'phi_scaled', dim=16)
    s5 = ManifoldState(test_data)
    enc5 = BasisFusionShifter.encode(s5, basis_a=basis_a, basis_b=basis_b, bridge_operator='xor')
    meta5 = enc5.metadata.get('basis_fusion', {})
    anat5 = meta5.get('fusion_anatomy', {})
    dec5 = BasisFusionShifter.decode(enc5)
    print(f"  Cross-substrate xor: roundtrip={bytes(dec5.encoded) == test_data}  "
          f"intersection={len(anat5.get('intersection', []))}  bridge={len(anat5.get('bridge', []))}")

    # ── Composite Coordinate Tests ──
    print("\n--- Composite coordinate tests ---")
    s = ManifoldState(test_data)
    enc = CompositeCoordinateShifter.encode(s)
    dec = CompositeCoordinateShifter.decode(enc)
    ok = bytes(dec.encoded) == test_data
    meta_cc = enc.metadata.get('composite_coordinate', {})
    print(f"  Composite roundtrip: {ok}")
    print(f"  Manifold dims: {meta_cc.get('manifold_dims')}")
    print(f"  Sponge levels: {meta_cc.get('sponge_levels')}")
    print(f"  Horn y range: {meta_cc.get('horn_y_range')}")

    # Large data
    s6 = ManifoldState(large)
    enc6 = CompositeCoordinateShifter.encode(s6)
    dec6 = CompositeCoordinateShifter.decode(enc6)
    print(f"  Composite large roundtrip: {bytes(dec6.encoded) == large}")

    # Show a sample composite address
    addr = CompositeCoordinateShifter._composite_address(42)
    print(f"\n  Sample address for n=42:")
    print(f"    tree: {addr['sponge']}")
    print(f"    surface: x={addr['horn'][0]:.4f}, y={addr['horn'][1]:.4f}, theta={addr['horn'][2]:.4f}")
    print(f"    torus: θ={addr['torus'][0]:.4f}, φ={addr['torus'][1]:.4f}, ψ={addr['torus'][2]:.4f}")
    print(f"    pist: k={addr['pist'][0]}, t={addr['pist'][1]}")

    # ── Programmable Decoder Tests ──
    print("\n--- Programmable decoder tests ---")
    s = ManifoldState(test_data)
    enc = ProgrammableDecoderShifter.encode(s)
    dec = ProgrammableDecoderShifter.decode(enc)
    print(f"  Decoder output: {bytes(dec.encoded)[:20]}...")
    print(f"  Program length: {enc.metadata.get('programmable_decoder', {}).get('program_length')}")
    print(f"  Note: programmable decoder is data-as-program, not direct compression")

    print("\n" + "=" * 70)
    print("Alpha branch test complete.")
    print("=" * 70)


if __name__ == '__main__':
    test_alpha()
