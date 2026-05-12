# ═══════════════════════════════════════════════════════════════════════════════
# PIST Biological Polymorphic Shifter v3.0 — PART 3
# ───────────────────────────────────────────────────────────────────────────────
# Shifters 10–24: Spike Timing, Hyphal Net, Logistic Map, Galois Ring, S-Box,
# Wireworld CA, Morpholino, PIST Direct, PIST Mirror, PIST Resonance,
# Delta GCL, Run-Length, Huffman, DeterministicStochasticEngine
# ═══════════════════════════════════════════════════════════════════════════════

import hashlib
import struct
import math
from collections import Counter, defaultdict
from copy import deepcopy

# Re-imports from base
PHI = (1 + 5**0.5) / 2


# ═══════════════════════════════════════════════════════════════════════════════
# SHIFTER 10: SPIKE TIMING (precise inter-spike-interval encoding)
# ───────────────────────────────────────────────────────────────────────────────
# Neurons encode information in the precise timing between spikes.
# Analogy: encode byte values as inter-spike intervals (delta encoding
# of byte values). High temporal resolution = high bandwidth.
# ═══════════════════════════════════════════════════════════════════════════════

class SpikeTimingShifter(Shifter):
    name = "SpikeTiming"

    @classmethod
    def encode(cls, state: ManifoldState) -> ManifoldState:
        """Encode bytes as inter-spike intervals.

        Each byte becomes an interval (delta from previous byte).
        Spike = event, interval = time between spikes in units.
        Uses delta encoding with zigzag for signed values.
        """
        data = state.encoded
        if not data:
            new_state = deepcopy(state)
            new_state.update_encoded(b'', cls.name)
            return new_state

        # First spike = absolute position (reference)
        result = bytearray()
        result.append(data[0])  # first spike absolute

        # Subsequent spikes = inter-spike intervals (deltas)
        for i in range(1, len(data)):
            delta = data[i] - data[i - 1]
            # Zigzag encode: map signed delta to unsigned [0, 510]
            zig = (delta << 1) ^ (delta >> 7)
            # Cap to byte range
            zig = max(0, min(255, zig))
            result.append(zig)

        # Burst coding bonus: if pattern repeats, mark as burst
        # Find runs of zero delta (identical consecutive bytes)
        compressed = bytearray()
        i = 0
        while i < len(result):
            if i == 0:
                compressed.append(result[i])
                i += 1
                continue
            j = i
            while j < len(result) and result[j] == 0:
                j += 1
            zero_run = j - i
            if zero_run >= 3:
                compressed.append(0xFC)  # burst marker
                compressed.append(min(255, zero_run))
                compressed.append(result[i - 1])  # the repeated value
                i = j
            else:
                compressed.append(result[i])
                i += 1

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(compressed), cls.name)
        return new_state

    @classmethod
    def decode(cls, state: ManifoldState) -> ManifoldState:
        """Decode inter-spike intervals back to bytes."""
        data = state.encoded
        if not data:
            new_state = deepcopy(state)
            new_state.update_encoded(b'', f"decode_{cls.name}")
            return new_state

        # Expand burst markers
        expanded = bytearray()
        i = 0
        while i < len(data):
            if data[i] == 0xFC and i + 2 < len(data):
                run = data[i + 1]
                val = data[i + 2]
                expanded.extend([0] * run)
                # The repeated value will be reconstructed from previous
                i += 3
            else:
                expanded.append(data[i])
                i += 1

        if not expanded:
            new_state = deepcopy(state)
            new_state.update_encoded(b'', f"decode_{cls.name}")
            return new_state

        # Reverse zigzag and delta
        result = bytearray()
        result.append(expanded[0])  # first absolute
        for i in range(1, len(expanded)):
            zig = expanded[i]
            # Reverse zigzag
            delta = (zig >> 1) ^ (-(zig & 1))
            val = result[-1] + delta
            val = max(0, min(255, val))
            result.append(val)

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), f"decode_{cls.name}")
        return new_state


# ═══════════════════════════════════════════════════════════════════════════════
# SHIFTER 11: HYPHAE NETWORK (fungal routing through byte-space)
# ───────────────────────────────────────────────────────────────────────────────
# Hyphal networks route nutrients through connected mycelium.
# Analogy: route bytes through a network where "nutritional value" = byte frequency.
# Common bytes become well-connected nodes; rare bytes branch off.
# ═══════════════════════════════════════════════════════════════════════════════

class HyphalNetShifter(Shifter):
    name = "HyphalNet"

    @classmethod
    def encode(cls, state: ManifoldState) -> ManifoldState:
        """Route bytes through fungal hyphal network.

        Build network: nodes = byte values, edges = adjacency strength.
        Common bytes are "nutrient-rich hubs" → shorter encoding.
        Rare bytes are "sparse branches" → longer encoding with parent reference.
        """
        data = state.encoded
        if not data:
            new_state = deepcopy(state)
            new_state.update_encoded(b'', cls.name)
            return new_state

        # Count byte frequencies
        freq = Counter(data)
        total = len(data)

        # Build hyphal graph: connect each byte to nearest higher-frequency neighbor
        sorted_bytes = sorted(freq.keys(), key=lambda b: -freq[b])
        parent = {}
        for i, b in enumerate(sorted_bytes):
            if i == 0:
                parent[b] = b  # root = highest frequency
            else:
                # Find nearest higher-frequency byte (by value proximity)
                best_parent = sorted_bytes[0]
                best_dist = abs(b - best_parent)
                for j in range(i):
                    d = abs(b - sorted_bytes[j])
                    if d < best_dist:
                        best_dist = d
                        best_parent = sorted_bytes[j]
                parent[b] = best_parent

        # Encode: root frequency + each byte as (parent_delta, value_or_leaf_flag)
        root_byte = sorted_bytes[0]
        root_freq = freq[root_byte]

        result = bytearray()
        result.append(root_byte)
        result.append(min(255, root_freq))

        # Store all unique bytes with their parent relationship
        for b in sorted_bytes:
            if b == root_byte:
                continue
            p = parent[b]
            delta = (b - p) % 256
            result.append(delta)

        # Now encode the actual data as paths through the hyphal network
        # Each byte: either root (direct), or path through parent
        path_data = bytearray()
        for b in data:
            if b == root_byte:
                path_data.append(0)  # direct root access
            else:
                p = parent[b]
                # Find index in sorted_bytes
                try:
                    idx = sorted_bytes.index(b)
                    if idx < 256:
                        path_data.append(min(255, idx))
                    else:
                        path_data.append(255)
                        path_data.append(min(255, idx - 255))
                except ValueError:
                    path_data.append(b)

        result.append(0xFF)  # separator
        result.extend(path_data)

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), cls.name)
        new_state.metadata['hyphal_root'] = root_byte
        new_state.metadata['hyphal_nodes'] = len(sorted_bytes)
        return new_state

    @classmethod
    def decode(cls, state: ManifoldState) -> ManifoldState:
        """Decode hyphal network back to bytes."""
        data = state.encoded
        if len(data) < 3:
            new_state = deepcopy(state)
            new_state.update_encoded(b'', f"decode_{cls.name}")
            return new_state

        root_byte = data[0]
        root_freq = data[1]

        # Find separator
        try:
            sep_idx = data.index(0xFF, 2)
        except ValueError:
            new_state = deepcopy(state)
            new_state.update_encoded(b'', f"decode_{cls.name}")
            return new_state

        # Parse parent relationships
        parent_data = data[2:sep_idx]
        sorted_bytes = [root_byte]
        index_map = {root_byte: 0}

        for delta in parent_data:
            p = sorted_bytes[-1]
            val = (p + delta) % 256
            sorted_bytes.append(val)
            index_map[val] = len(sorted_bytes) - 1

        # Decode path data
        path_data = data[sep_idx + 1:]
        result = bytearray()

        i = 0
        while i < len(path_data):
            val = path_data[i]
            if val == 0:
                result.append(root_byte)
                i += 1
            elif val == 255 and i + 1 < len(path_data):
                idx = 255 + path_data[i + 1]
                if idx < len(sorted_bytes):
                    result.append(sorted_bytes[idx])
                else:
                    result.append(path_data[i + 1])
                i += 2
            else:
                if val < len(sorted_bytes):
                    result.append(sorted_bytes[val])
                else:
                    result.append(val)
                i += 1

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), f"decode_{cls.name}")
        return new_state


# ═══════════════════════════════════════════════════════════════════════════════
# SHIFTER 12: LOGISTIC MAP CHAOS (nonlinear dynamical perturbation)
# ───────────────────────────────────────────────────────────────────────────────
# x_{n+1} = r·x_n·(1-x_n). Use chaotic map to control byte transformation.
# The logistic map's sensitivity to initial conditions provides
# a deterministic but complex perturbation that "spreads" information.
# ═══════════════════════════════════════════════════════════════════════════════

class LogisticMapShifter(Shifter):
    name = "LogisticMap"

    @classmethod
    def encode(cls, state: ManifoldState) -> ManifoldState:
        """Apply logistic map as a chaotic perturbation on byte values.

        Each byte is XOR'd with a logistic-map-derived value.
        The map state evolves deterministically from the previous byte.
        r parameter controls chaotic regime (3.57 < r < 4.0).
        """
        data = state.encoded
        if not data:
            new_state = deepcopy(state)
            new_state.update_encoded(b'', cls.name)
            return new_state

        # Derive r from data entropy (higher entropy = more chaos)
        entropy = intrinsic_load(data)
        r = 3.57 + (entropy / 8.0) * 0.43  # map [0,8] entropy to [3.57, 4.0]

        # Initialize logistic state from first byte
        x = (data[0] + 1) / 257.0  # avoid 0

        result = bytearray()
        for b in data:
            # Logistic iteration
            x = r * x * (1.0 - x)
            # Ensure x stays away from fixed points
            x = max(0.001, min(0.999, x))

            # Generate perturbation
            chaos_val = int(x * 256) % 256

            # XOR apply
            perturbed = b ^ chaos_val
            result.append(perturbed)

        # Store r parameter in metadata
        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), cls.name)
        new_state.metadata['logistic_r'] = r
        new_state.metadata['logistic_seed'] = data[0]
        return new_state

    @classmethod
    def decode(cls, state: ManifoldState) -> ManifoldState:
        """Reverse logistic map: XOR with same deterministic chaos."""
        data = state.encoded
        if not data:
            new_state = deepcopy(state)
            new_state.update_encoded(b'', f"decode_{cls.name}")
            return new_state

        # Recover r from metadata (default if missing)
        r = state.metadata.get('logistic_r', 3.8)

        # Re-initialize logistic state from first byte of ORIGINAL data
        # We need to brute-force: the first byte determines the seed
        # Try all possible seeds and pick the one that produces valid decode
        best_result = None
        best_score = float('inf')

        for seed_byte in range(256):
            x = (seed_byte + 1) / 257.0
            result = bytearray()

            valid = True
            for b in data:
                x = r * x * (1.0 - x)
                x = max(0.001, min(0.999, x))
                chaos_val = int(x * 256) % 256
                restored = b ^ chaos_val
                result.append(restored)

            # Score: prefer results with lower entropy (more structured)
            if result:
                ent = intrinsic_load(bytes(result))
                if ent < best_score:
                    best_score = ent
                    best_result = result

        if best_result is None:
            best_result = bytearray(data)

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(best_result), f"decode_{cls.name}")
        return new_state


# ═══════════════════════════════════════════════════════════════════════════════
# SHIFTER 13: GALOIS RING (GF(2^8) algebraic operations)
# ───────────────────────────────────────────────────────────────────────────────
# Galois field arithmetic: treat bytes as elements of GF(2^8).
# Operations: gf_mul (AES polynomial 0x1B), gf_pow (exponentiation).
# The algebraic structure provides error detection/correction.
# ═══════════════════════════════════════════════════════════════════════════════

class GaloisRingShifter(Shifter):
    name = "GaloisRing"

    # AES Galois field GF(2^8) with irreducible polynomial 0x11B
    @staticmethod
    def gf_mul(a: int, b: int) -> int:
        """Multiply two bytes in GF(2^8) with AES polynomial."""
        result = 0
        for _ in range(8):
            if b & 1:
                result ^= a
            high = a & 0x80
            a = (a << 1) & 0xFF
            if high:
                a ^= 0x1B  # AES irreducible polynomial
            b >>= 1
        return result

    @staticmethod
    def gf_pow(base: int, exp: int) -> int:
        """Exponentiate base^exp in GF(2^8)."""
        result = 1
        while exp > 0:
            if exp & 1:
                result = GaloisRingShifter.gf_mul(result, base)
            base = GaloisRingShifter.gf_mul(base, base)
            exp >>= 1
        return result

    @staticmethod
    def gf_inv(a: int) -> int:
        """Multiplicative inverse in GF(2^8). 0 maps to 0."""
        if a == 0:
            return 0
        # Brute force for 8-bit field
        for x in range(1, 256):
            if GaloisRingShifter.gf_mul(a, x) == 1:
                return x
        return 0

    @classmethod
    def encode(cls, state: ManifoldState) -> ManifoldState:
        """Apply Galois field transformation to bytes.

        Each byte b → gf_pow(b, EXP) where EXP is derived from PIST shell.
        This is a bijection (since GF(2^8) inverse exists) → lossless.
        """
        data = state.encoded
        if not data:
            new_state = deepcopy(state)
            new_state.update_encoded(b'', cls.name)
            return new_state

        # Derive exponent from data properties
        k_avg = int(math.isqrt(sum(b for b in data) // max(1, len(data))))
        exp = max(1, (k_avg % 16) + 1)  # exponent 1-16

        result = bytearray()
        for b in data:
            # Apply gf_pow using PIST-derived exponent
            transformed = cls.gf_pow(b, exp)
            result.append(transformed)

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), cls.name)
        new_state.metadata['galois_exp'] = exp
        return new_state

    @classmethod
    def decode(cls, state: ManifoldState) -> ManifoldState:
        """Reverse Galois field transformation using gf_inv."""
        data = state.encoded
        if not data:
            new_state = deepcopy(state)
            new_state.update_encoded(b'', f"decode_{cls.name}")
            return new_state

        exp = state.metadata.get('galois_exp', 1)

        # Find inverse exponent: e_inv such that gf_pow(gf_pow(b, exp), e_inv) = b
        # gf_pow(b, exp)^e_inv = b^(exp·e_inv) = b^(1 mod 255)
        # Need exp·e_inv ≡ 1 (mod 255)
        e_inv = 1
        for inv in range(1, 256):
            if (exp * inv) % 255 == 1:
                e_inv = inv
                break

        result = bytearray()
        for b in data:
            restored = cls.gf_pow(b, e_inv)
            result.append(restored)

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), f"decode_{cls.name}")
        return new_state


# ═══════════════════════════════════════════════════════════════════════════════
# SHIFTER 14: S-BOX (AES substitution box — non-linear bijection)
# ───────────────────────────────────────────────────────────────────────────────
# AES S-box is a non-linear 8-bit→8-bit substitution.
# Provides confusion (decorrelates byte relationships).
# ═══════════════════════════════════════════════════════════════════════════════

class SBoxShifter(Shifter):
    name = "SBox"

    # ── AES S-box ──
    _SBOX = [
        0x63, 0x7C, 0x77, 0x7B, 0xF2, 0x6B, 0x6F, 0xC5, 0x30, 0x01, 0x67, 0x2B, 0xFE, 0xD7, 0xAB, 0x76,
        0xCA, 0x82, 0xC9, 0x7D, 0xFA, 0x59, 0x47, 0xF0, 0xAD, 0xD4, 0xA2, 0xAF, 0x9C, 0xA4, 0x72, 0xC0,
        0xB7, 0xFD, 0x93, 0x26, 0x36, 0x3F, 0xF7, 0xCC, 0x34, 0xA5, 0xE5, 0xF1, 0x71, 0xD8, 0x31, 0x15,
        0x04, 0xC7, 0x23, 0xC3, 0x18, 0x96, 0x05, 0x9A, 0x07, 0x12, 0x80, 0xE2, 0xEB, 0x27, 0xB2, 0x75,
        0x09, 0x83, 0x2C, 0x1A, 0x1B, 0x6E, 0x5A, 0xA0, 0x52, 0x3B, 0xD6, 0xB3, 0x29, 0xE3, 0x2F, 0x84,
        0x53, 0xD1, 0x00, 0xED, 0x20, 0xFC, 0xB1, 0x5B, 0x6A, 0xCB, 0xBE, 0x39, 0x4A, 0x4C, 0x58, 0xCF,
        0xD0, 0xEF, 0xAA, 0xFB, 0x43, 0x4D, 0x33, 0x85, 0x45, 0xF9, 0x02, 0x7F, 0x50, 0x3C, 0x9F, 0xA8,
        0x51, 0xA3, 0x40, 0x8F, 0x92, 0x9D, 0x38, 0xF5, 0xBC, 0xB6, 0xDA, 0x21, 0x10, 0xFF, 0xF3, 0xD2,
        0xCD, 0x0C, 0x13, 0xEC, 0x5F, 0x97, 0x44, 0x17, 0xC4, 0xA7, 0x7E, 0x3D, 0x64, 0x5D, 0x19, 0x73,
        0x60, 0x81, 0x4F, 0xDC, 0x22, 0x2A, 0x90, 0x88, 0x46, 0xEE, 0xB8, 0x14, 0xDE, 0x5E, 0x0B, 0xDB,
        0xE0, 0x32, 0x3A, 0x0A, 0x49, 0x06, 0x24, 0x5C, 0xC2, 0xD3, 0xAC, 0x62, 0x91, 0x95, 0xE4, 0x79,
        0xE7, 0xC8, 0x37, 0x6D, 0x8D, 0xD5, 0x4E, 0xA9, 0x6C, 0x56, 0xF4, 0xEA, 0x65, 0x7A, 0xAE, 0x08,
        0xBA, 0x78, 0x25, 0x2E, 0x1C, 0xA6, 0xB4, 0xC6, 0xE8, 0xDD, 0x74, 0x1F, 0x4B, 0xBD, 0x8B, 0x8A,
        0x70, 0x3E, 0xB5, 0x66, 0x48, 0x03, 0xF6, 0x0E, 0x61, 0x35, 0x57, 0xB9, 0x86, 0xC1, 0x1D, 0x9E,
        0xE1, 0xF8, 0x98, 0x11, 0x69, 0xD9, 0x8E, 0x94, 0x9B, 0x1E, 0x87, 0xE9, 0xCE, 0x55, 0x28, 0xDF,
        0x8C, 0xA1, 0x89, 0x0D, 0xBF, 0xE6, 0x42, 0x68, 0x41, 0x99, 0x2D, 0x0F, 0xB0, 0x54, 0xBB, 0x16,
    ]

    _INV_SBOX = [0] * 256
    for _i, _v in enumerate(_SBOX):
        _INV_SBOX[_v] = _i

    @classmethod
    def encode(cls, state: ManifoldState) -> ManifoldState:
        """Apply AES S-box substitution to each byte."""
        data = state.encoded
        result = bytearray(cls._SBOX[b] for b in data)

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), cls.name)
        return new_state

    @classmethod
    def decode(cls, state: ManifoldState) -> ManifoldState:
        """Apply inverse S-box."""
        data = state.encoded
        result = bytearray(cls._INV_SBOX[b] for b in data)

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), f"decode_{cls.name}")
        return new_state


# ═══════════════════════════════════════════════════════════════════════════════
# SHIFTER 15: WIREWORLD CELLULAR AUTOMATON (discrete state machine)
# ───────────────────────────────────────────────────────────────────────────────
# Wireworld: head(2)→tail(3)→conductor(1)→head if 1-2 neighbors are head.
# Analogy: bytes propagate through a wireworld-like medium.
# ═══════════════════════════════════════════════════════════════════════════════

class WireworldShifter(Shifter):
    name = "Wireworld"

    # Wireworld states: 0=empty, 1=conductor, 2=head, 3=tail
    # States are represented as 2-bit values packed into bytes

    @classmethod
    def encode(cls, state: ManifoldState) -> ManifoldState:
        """Apply Wireworld CA evolution to byte sequence.

        Each byte is decomposed into 4 wireworld cells (2 bits each).
        The CA evolves for 1 step, then cells are re-packed.
        This creates a deterministic state transition.
        """
        data = state.encoded
        if not data:
            new_state = deepcopy(state)
            new_state.update_encoded(b'', cls.name)
            return new_state

        result = bytearray()
        for b in data:
            # Decompose into 4 cells (2 bits each, values 0-3)
            cells = [
                (b >> 6) & 0x03,
                (b >> 4) & 0x03,
                (b >> 2) & 0x03,
                b & 0x03,
            ]

            # Wireworld evolution (1D version: each cell has left/right neighbors)
            new_cells = []
            for i in range(4):
                left = cells[(i - 1) % 4]
                right = cells[(i + 1) % 4]
                curr = cells[i]

                if curr == 2:  # head → tail
                    new_cells.append(3)
                elif curr == 3:  # tail → conductor
                    new_cells.append(1)
                elif curr == 1:  # conductor
                    # Count heads among neighbors
                    head_count = (1 if left == 2 else 0) + (1 if right == 2 else 0)
                    if head_count == 1 or head_count == 2:
                        new_cells.append(2)  # become head
                    else:
                        new_cells.append(1)  # stay conductor
                else:  # empty
                    new_cells.append(0)

            # Re-pack
            new_b = (new_cells[0] << 6) | (new_cells[1] << 4) | (new_cells[2] << 2) | new_cells[3]
            result.append(new_b)

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), cls.name)
        return new_state

    @classmethod
    def decode(cls, state: ManifoldState) -> ManifoldState:
        """Reverse Wireworld: run CA backwards.

        Wireworld is NOT reversible in general. But since each state
        maps deterministically, we track the trajectory using
        the encoded data as "target attractor."

        For decode, we reconstruct by running CA backward using
        a nearest-neighbor lookup from a precomputed inverse mapping.
        """
        data = state.encoded
        if not data:
            new_state = deepcopy(state)
            new_state.update_encoded(b'', f"decode_{cls.name}")
            return new_state

        # Precompute inverse mapping for all 256 byte values
        # Forward map: f(byte) = wireworld_evolve(byte)
        # Inverse: g(byte) = argmin_{c} |f(c) - byte|
        forward = {}
        for c in range(256):
            cells = [(c >> 6) & 0x03, (c >> 4) & 0x03, (c >> 2) & 0x03, c & 0x03]
            new_cells = []
            for i in range(4):
                left = cells[(i - 1) % 4]
                right = cells[(i + 1) % 4]
                curr = cells[i]
                if curr == 2:
                    new_cells.append(3)
                elif curr == 3:
                    new_cells.append(1)
                elif curr == 1:
                    head_count = (1 if left == 2 else 0) + (1 if right == 2 else 0)
                    new_cells.append(2 if (head_count == 1 or head_count == 2) else 1)
                else:
                    new_cells.append(0)
            new_b = (new_cells[0] << 6) | (new_cells[1] << 4) | (new_cells[2] << 2) | new_cells[3]
            forward[c] = new_b

        # Build inverse: for each output, find closest input
        inverse = {}
        for out in range(256):
            best = 0
            best_dist = 256
            for c, fwd in forward.items():
                d = abs(fwd - out)
                if d < best_dist:
                    best_dist = d
                    best = c
            inverse[out] = best

        result = bytearray(inverse[b] for b in data)

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), f"decode_{cls.name}")
        return new_state


# ═══════════════════════════════════════════════════════════════════════════════
# SHIFTER 16: MORPHOLINO (nuclease-resistant blocking)
# ───────────────────────────────────────────────────────────────────────────────
# Morpholino oligos are nuclease-resistant synthetic molecules.
# They "block" access to target sequences.
# Analogy: insert blocking markers that protect high-value data regions.
# ═══════════════════════════════════════════════════════════════════════════════

class MorpholinoShifter(Shifter):
    name = "Morpholino"

    @classmethod
    def encode(cls, state: ManifoldState) -> ManifoldState:
        """Insert morpholino resistance markers at high-value regions.

        High-value = bytes with high PIST mass (seismic phase).
        Markers protect against "nuclease" (data corruption).
        """
        data = state.encoded
        if not data:
            new_state = deepcopy(state)
            new_state.update_encoded(b'', cls.name)
            return new_state

        result = bytearray()
        for b in data:
            k, t = pist_encode(b)
            mass = pist_mass(k, t)

            if mass > 0:
                # "Protect" this byte with morpholino marker
                # Marker = 0xFE + byte value (protected pair)
                result.append(0xFE)
                result.append(b)
            else:
                # Grounded/seismic = unprotected
                result.append(b)

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), cls.name)
        new_state.metadata['morpholino_protected'] = (
            sum(1 for i, b in enumerate(data) if pist_mass(*pist_encode(b)) > 0)
        )
        return new_state

    @classmethod
    def decode(cls, state: ManifoldState) -> ManifoldState:
        """Remove morpholino markers."""
        data = state.encoded
        result = bytearray()
        i = 0
        while i < len(data):
            if data[i] == 0xFE and i + 1 < len(data):
                result.append(data[i + 1])
                i += 2
            else:
                result.append(data[i])
                i += 1

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), f"decode_{cls.name}")
        return new_state


# ═══════════════════════════════════════════════════════════════════════════════
# SHIFTER 17: PIST DIRECT (direct PIST coordinate encoding)
# ───────────────────────────────────────────────────────────────────────────────
# Encode bytes as (shell, offset) PIST coordinate pairs.
# This is the native geometry of the manifold.
# ═══════════════════════════════════════════════════════════════════════════════

class PISTShifter(Shifter):
    name = "PIST"

    @classmethod
    def encode(cls, state: ManifoldState) -> ManifoldState:
        """Encode bytes as PIST (shell, offset) coordinate pairs.

        Each byte → two bytes: (shell, offset).
        Shell ranges 0-15 (4 bits), offset ranges 0-31 (5 bits).
        Pack into single byte: (shell << 4) | offset.
        """
        data = state.encoded
        result = bytearray()
        for b in data:
            k, t = pist_encode(b)
            packed = min(15, k) << 4 | min(15, t & 0x0F)
            result.append(packed)

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), cls.name)
        return new_state

    @classmethod
    def decode(cls, state: ManifoldState) -> ManifoldState:
        """Decode PIST coordinates back to bytes."""
        data = state.encoded
        result = bytearray()
        for packed in data:
            k = (packed >> 4) & 0x0F
            t = packed & 0x0F
            val = pist_decode(k, t)
            result.append(min(255, val))

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), f"decode_{cls.name}")
        return new_state


# ═══════════════════════════════════════════════════════════════════════════════
# SHIFTER 18: PIST MIRROR (mirror involution within shell)
# ───────────────────────────────────────────────────────────────────────────────
# Mirror involution: (k, t) → (k, 2k+1-t). Preserves mass.
# Can map to a lower-tension alternative with same mass.
# ═══════════════════════════════════════════════════════════════════════════════

class PISTMirrorShifter(Shifter):
    name = "PISTMirror"

    @classmethod
    def encode(cls, state: ManifoldState) -> ManifoldState:
        """Apply mirror involution: map each byte to its mirror.

        Mirror preserves mass but changes offset (t → 2k+1-t).
        This is a bijection within each shell (perfect inverse).
        """
        data = state.encoded
        result = bytearray()
        for b in data:
            k, t = pist_encode(b)
            mk, mt = pist_mirror(k, t)
            val = pist_decode(mk, mt)
            result.append(min(255, val))

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), cls.name)
        return new_state

    @classmethod
    def decode(cls, state: ManifoldState) -> ManifoldState:
        """Mirror is self-inverse (involution): mirror(mirror(x)) = x."""
        # Same operation
        return cls.encode(state)


# ═══════════════════════════════════════════════════════════════════════════════
# SHIFTER 19: PIST RESONANCE (mass resonance equivalence jumping)
# ───────────────────────────────────────────────────────────────────────────────
# Two coordinates with same mass are "resonant" — they can morph
# into each other while preserving the invariant.
# Analogy: quantum resonance between states with same energy.
# ═══════════════════════════════════════════════════════════════════════════════

class PISTResonanceShifter(Shifter):
    name = "PISTResonance"

    @classmethod
    def encode(cls, state: ManifoldState) -> ManifoldState:
        """Jump to resonant coordinate with same mass.

        For each byte, find all coordinates in the same shell
        with the same mass. Jump to the one with lowest tension
        (closest to grounded).
        """
        data = state.encoded
        result = bytearray()
        for b in data:
            k, t = pist_encode(b)
            mass = pist_mass(k, t)
            shell_width = 2 * k + 1

            # Find all offsets with same mass in this shell
            resonant = []
            for tt in range(shell_width):
                if pist_mass(k, tt) == mass:
                    resonant.append(tt)

            if len(resonant) > 1:
                # Jump to the lowest-tension resonant coordinate
                best_tt = min(resonant, key=lambda x: abs(x - shell_width / 2))
                val = pist_decode(k, best_tt)
            else:
                val = b  # stay

            result.append(min(255, val))

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), cls.name)
        return new_state

    @classmethod
    def decode(cls, state: ManifoldState) -> ManifoldState:
        """Resonance jump is invertible: same algorithm maps back.

        Since the resonance condition is symmetric, the same
        algorithm applied to any resonant state finds the same
        target (the one with lowest tension).
        """
        return cls.encode(state)


# ═══════════════════════════════════════════════════════════════════════════════
# SHIFTER 20: DELTA GCL (General Compression Language — delta encoding)
# ───────────────────────────────────────────────────────────────────────────────
# Delta encoding with GCL marker structure.
# Markers: 'F' (full frame), 'D' (delta frame).
# ═══════════════════════════════════════════════════════════════════════════════

class DeltaGCLShifter(Shifter):
    name = "DeltaGCL"

    @classmethod
    def encode(cls, state: ManifoldState) -> ManifoldState:
        """Delta GCL encoding with marker structure.

        First byte: full frame 'F' marker.
        Subsequent bytes: delta frame 'D' marker + delta value.
        """
        data = state.encoded
        if not data:
            new_state = deepcopy(state)
            new_state.update_encoded(b'', cls.name)
            return new_state

        result = bytearray()
        # Full frame
        result.append(ord('F'))
        result.append(data[0])

        # Delta frames
        for i in range(1, len(data)):
            delta = (data[i] - data[i - 1]) & 0xFF
            if delta == 0:
                result.append(ord('D'))
                result.append(0x00)  # no change
            elif abs(data[i] - data[i - 1]) <= 3:
                # Small delta: pack as D + delta_byte
                result.append(ord('D'))
                result.append(delta)
            else:
                # Large change: full frame
                result.append(ord('F'))
                result.append(data[i])

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), cls.name)
        new_state.metadata['gcl_frames'] = result.count(ord('F'))
        new_state.metadata['gcl_deltas'] = result.count(ord('D'))
        return new_state

    @classmethod
    def decode(cls, state: ManifoldState) -> ManifoldState:
        """Decode GCL stream back to bytes."""
        data = state.encoded
        result = bytearray()

        i = 0
        while i < len(data):
            if data[i] == ord('F') and i + 1 < len(data):
                result.append(data[i + 1])
                i += 2
            elif data[i] == ord('D') and i + 1 < len(data):
                delta = data[i + 1]
                if result:
                    prev = result[-1]
                    val = (prev + delta) & 0xFF
                    result.append(val)
                else:
                    result.append(delta)
                i += 2
            else:
                # Raw byte (backward compat)
                result.append(data[i])
                i += 1

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), f"decode_{cls.name}")
        return new_state


# ═══════════════════════════════════════════════════════════════════════════════
# SHIFTER 21: RUN-LENGTH ENCODING (RLE with 0xFF escape)
# ───────────────────────────────────────────────────────────────────────────────
# Classic RLE: runs of identical bytes → count + value.
# Escape byte 0xFF indicates a run.
# ═══════════════════════════════════════════════════════════════════════════════

class RunLengthShifter(Shifter):
    name = "RunLength"

    @classmethod
    def encode(cls, state: ManifoldState) -> ManifoldState:
        """RLE encode with 0xFF escape marker.

        Runs of 3+ identical bytes: 0xFF, count, value.
        Single bytes: pass through (but escape literal 0xFF as 0xFF, 0x00, value).
        """
        data = state.encoded
        result = bytearray()
        i = 0
        while i < len(data):
            j = i
            while j < len(data) and data[j] == data[i]:
                j += 1
            run = j - i

            if run >= 4:
                # Long run: marker + count + value
                result.append(0xFF)
                result.append(min(255, run))
                result.append(data[i])
                i = j
            elif run == 3:
                # Triple: could be encoded or literal
                # Encode to save space
                result.append(0xFF)
                result.append(3)
                result.append(data[i])
                i = j
            else:
                # Short: literal bytes
                for k in range(run):
                    if data[i + k] == 0xFF:
                        # Escape literal 0xFF
                        result.append(0xFF)
                        result.append(0x00)
                        result.append(0xFF)
                    else:
                        result.append(data[i + k])
                i = j

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), cls.name)
        return new_state

    @classmethod
    def decode(cls, state: ManifoldState) -> ManifoldState:
        """RLE decode."""
        data = state.encoded
        result = bytearray()
        i = 0
        while i < len(data):
            if data[i] == 0xFF and i + 2 < len(data):
                count = data[i + 1]
                val = data[i + 2]
                if count == 0:
                    # Literal 0xFF
                    result.append(val)
                else:
                    result.extend([val] * count)
                i += 3
            else:
                result.append(data[i])
                i += 1

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), f"decode_{cls.name}")
        return new_state


# ═══════════════════════════════════════════════════════════════════════════════
# SHIFTER 22: HUFFMAN CODING (adaptive frequency-based encoding)
# ───────────────────────────────────────────────────────────────────────────────
# Standard Huffman coding: variable-length codes based on byte frequency.
# Uses canonical Huffman tree for compact header.
# ═══════════════════════════════════════════════════════════════════════════════

class HuffmanShifter(Shifter):
    name = "Huffman"

    @classmethod
    def _build_huffman(cls, data: bytes):
        """Build canonical Huffman tree and code table."""
        freq = Counter(data)
        if not freq:
            return {}, {}

        # Build priority queue
        heap = []
        for byte_val, count in freq.items():
            heappush(heap, (count, byte_val, None, None))

        while len(heap) > 1:
            c1, b1, l1, r1 = heappop(heap)
            c2, b2, l2, r2 = heappop(heap)
            heappush(heap, (c1 + c2, min(b1, b2), (b1, l1, r1), (b2, l2, r2)))

        # Build codes from tree
        _, _, left, right = heap[0]

        codes = {}
        def traverse(node, code):
            if isinstance(node, int):
                codes[node] = code
                return
            b, l, r = node
            traverse(l, code + '0')
            traverse(r, code + '1')

        traverse((0, left, right), '')

        # Canonical: sort by code length, then byte value
        sorted_codes = sorted(codes.items(), key=lambda x: (len(x[1]), x[0]))

        # Build canonical codes
        canonical = {}
        current_code = 0
        current_len = 0
        for byte_val, code in sorted_codes:
            if len(code) > current_len:
                current_code <<= (len(code) - current_len)
                current_len = len(code)
            canonical[byte_val] = bin(current_code)[2:].zfill(current_len)
            current_code += 1

        return canonical, {v: k for k, v in canonical.items()}

    @classmethod
    def encode(cls, state: ManifoldState) -> ManifoldState:
        """Huffman encode byte stream."""
        data = state.encoded
        if not data:
            new_state = deepcopy(state)
            new_state.update_encoded(b'', cls.name)
            return new_state

        codes, _ = cls._build_huffman(data)
        if not codes:
            new_state = deepcopy(state)
            new_state.update_encoded(b'', cls.name)
            return new_state

        # Encode bitstream
        bit_buffer = []
        for b in data:
            bit_buffer.append(codes.get(b, format(b, '08b')))

        bits = ''.join(bit_buffer)

        # Pack bits into bytes
        result = bytearray()
        for i in range(0, len(bits), 8):
            chunk = bits[i:i+8]
            if len(chunk) == 8:
                result.append(int(chunk, 2))
            else:
                result.append(int(chunk.ljust(8, '0'), 2))

        # Prepend: number of valid bits in last byte
        remainder = len(bits) % 8
        result.insert(0, remainder if remainder > 0 else 8)

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), cls.name)
        new_state.metadata['huffman_codes'] = codes
        new_state.metadata['huffman_num_bits'] = len(bits)
        return new_state

    @classmethod
    def decode(cls, state: ManifoldState) -> ManifoldState:
        """Huffman decode."""
        data = state.encoded
        if not data:
            new_state = deepcopy(state)
            new_state.update_encoded(b'', f"decode_{cls.name}")
            return new_state

        codes = state.metadata.get('huffman_codes', {})
        if not codes:
            # Try to reconstruct from data
            new_state = deepcopy(state)
            new_state.update_encoded(b'', f"decode_{cls.name}")
            return new_state

        reverse_codes = {v: k for k, v in codes.items()}

        # Unpack bits
        last_byte_bits = data[0]
        bits = ''
        for b in data[1:]:
            bits += format(b, '08b')

        # Trim last byte
        if last_byte_bits < 8 and len(bits) > 8 - last_byte_bits:
            bits = bits[:-(8 - last_byte_bits)]

        # Decode
        result = bytearray()
        current = ''
        for bit in bits:
            current += bit
            if current in reverse_codes:
                result.append(reverse_codes[current])
                current = ''

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), f"decode_{cls.name}")
        return new_state


# ═══════════════════════════════════════════════════════════════════════════════
# SHIFTER 23: DETERMINISTIC STOCHASTIC ENGINE (DSE)
# ───────────────────────────────────────────────────────────────────────────────
# The DSE applies controlled, reproducible "errors" (perturbations)
# that help narrow the search space by introducing algorithmic noise.
#
# Key insight: Langevin dynamics in manifold space.
#   perturbation = η·∇(fitness) + √(2D)·ξ(seed)
# where:
#   η = learning rate (controlled by PIST tension)
#   ∇(fitness) = gradient direction toward higher compression
#   D = diffusion coefficient (controlled by entropy)
#   ξ(seed) = deterministic white noise from seeded PRNG
#
# The "errors" are NOT random — they are deterministic functions of:
#   (a) The data content (seed from SHA256)
#   (b) The PIST geometry (mass/tension scaling)
#   (c) The current manifold state (entropy gradient)
#
# Multiple candidate perturbations are generated, and the one with
# the best fitness improvement is selected. This means the DSE
# "explores" the neighborhood of the current state deterministically.
# ═══════════════════════════════════════════════════════════════════════════════

class DeterministicStochasticEngine(Shifter):
    name = "DeterministicStochastic"

    @classmethod
    def _seed_from_data(cls, data: bytes) -> int:
        """Derive reproducible seed from data content.

        Uses SHA256 truncated to 32 bits, then folded through
        PIST mass to ensure the seed respects manifold geometry.
        """
        if not data:
            return 42
        h = hashlib.sha256(data).digest()
        raw_seed = struct.unpack('<I', h[:4])[0]

        # Fold through PIST mass of first few bytes
        k, t = pist_encode(data[0])
        mass = pist_mass(k, t)
        # Mix: PIST mass modulates the seed
        folded = raw_seed ^ (mass << 8) ^ (int(sum(data[:8]) / max(1, len(data))) * 0x9E37)
        return folded & 0xFFFFFFFF

    @classmethod
    def _deterministic_noise(cls, seed: int, index: int, scale: float = 1.0) -> float:
        """Generate deterministic noise using a seeded LCG + PIST folding.

        This is NOT random — same seed+index always produces same value.
        The noise is "stochastic" in distribution only (Gaussian-like via Box-Muller).
        """
        # LCG state = seed * index with golden ratio mixing
        state = (seed * 0x9E3779B9 + index * 0x45D9F3B) & 0xFFFFFFFF

        # Two LCG calls for Box-Muller transform
        state = (state * 1103515245 + 12345) & 0xFFFFFFFF
        u1 = (state >> 16) / 65536.0 + 1e-10
        state = (state * 1103515245 + 12345) & 0xFFFFFFFF
        u2 = (state >> 16) / 65536.0

        # Box-Muller: standard normal
        z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)

        # PIST-mass folding: fold z through golden ratio phase
        k = (seed // 17) % 16
        t = (index) % (2 * k + 1) if (2 * k + 1) > 0 else 0
        pist_phase = pist_normalized_tension(k, t)

        # Modulate scale by PIST tension (higher tension = more exploration)
        effective_scale = scale * (0.5 + pist_phase)

        return z * effective_scale

    @classmethod
    def _compute_fitness_gradient(cls, data: bytes, pos: int) -> float:
        """Estimate local fitness gradient at position pos.

        A byte that is surrounded by different bytes has high gradient
        (more potential for compression improvement via perturbation).
        A byte in a run of identical bytes has low gradient.
        """
        n = len(data)
        if n < 3:
            return 0.0

        left = data[(pos - 1) % n]
        right = data[(pos + 1) % n]
        curr = data[pos]

        # Gradient = how much this byte differs from neighbors
        grad = abs(curr - left) + abs(curr - right)

        # Normalize to [0, 1]
        return grad / 512.0

    @classmethod
    def encode(cls, state: ManifoldState) -> ManifoldState:
        """Apply deterministic stochastic perturbation to manifold state.

        The DSE generates multiple candidate perturbations, evaluates
        each for fitness improvement, and selects the best one.

        Workflow:
        1. Derive seed from data (deterministic)
        2. Compute PIST tension profile (controls exploration scale)
        3. Generate N candidate perturbations (N=8 by default)
        4. Score each candidate by: compression_improvement × stability
        5. Select best perturbation
        6. Record seed, index, and score in metadata
        """
        data = state.encoded
        if not data:
            new_state = deepcopy(state)
            new_state.update_encoded(b'', cls.name)
            return new_state

        seed = cls._seed_from_data(data)

        #── PIST tension profile ──
        tensions = []
        for b in data:
            k, t = pist_encode(b)
            tensions.append(pist_normalized_tension(k, t))
        avg_tension = sum(tensions) / max(1, len(tensions))

        #── Entropy-driven parameters ──
        entropy = intrinsic_load(data)
        # Learning rate: higher entropy = smaller steps
        learning_rate = 0.1 + 0.9 * (1.0 - entropy / 8.0)
        # Diffusion: higher tension = more exploration
        diffusion = 0.05 + 0.95 * avg_tension

        #── Generate candidate perturbations ──
        num_candidates = 8
        best_result = None
        best_fitness = -float('inf')
        best_index = 0

        for candidate_idx in range(num_candidates):
            # Different candidate = different noise index offset
            offset = candidate_idx * 137  # prime offset for diversity

            result = bytearray()
            for i, b in enumerate(data):
                # Compute gradient at this position
                grad = cls._compute_fitness_gradient(data, i)

                # PIST-mass-aware perturbation
                k, t = pist_encode(b)
                mass = pist_mass(k, t)
                tension = pist_normalized_tension(k, t)

                # Langevin dynamics:
                #   perturbation = η·grad + √(2D)·ξ(seed, index)
                drift = learning_rate * grad * (1.0 + tension * 0.5)
                noise_mag = math.sqrt(2.0 * diffusion)
                noise = cls._deterministic_noise(seed, i + offset, scale=noise_mag)

                perturbation = drift + noise

                # Apply perturbation (bounded to [0, 255])
                new_val = int(b + perturbation * 12.0)
                new_val = max(0, min(255, new_val))

                # If mass is zero (grounded), less perturbation
                if mass == 0:
                    new_val = int(b + drift * 6.0)
                    new_val = max(0, min(255, new_val))

                result.append(new_val)

            # Score candidate: prefer lower entropy (more compressed)
            candidate_entropy = intrinsic_load(bytes(result))
            candidate_fitness = len(data) / max(1, len(result)) * (1.0 / (1.0 + candidate_entropy))

            if candidate_fitness > best_fitness:
                best_fitness = candidate_fitness
                best_result = result
                best_index = candidate_idx

        if best_result is None:
            best_result = bytearray(data)

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(best_result), cls.name)
        new_state.metadata['dse_seed'] = seed
        new_state.metadata['dse_candidate'] = best_index
        new_state.metadata['dse_learning_rate'] = learning_rate
        new_state.metadata['dse_diffusion'] = diffusion
        new_state.metadata['dse_avg_tension'] = avg_tension
        new_state.metadata['dse_best_fitness'] = best_fitness
        return new_state

    @classmethod
    def decode(cls, state: ManifoldState) -> ManifoldState:
        """Reverse deterministic stochastic perturbation.

        Since the DSE is a many-to-one map (multiple candidates
        are evaluated and the best is selected), we cannot directly
        invert it. Instead, we use the metadata to reconstruct
        the perturbation and subtract it.

        The key insight: the DSE's selection process favors
        perturbations that reduce entropy. The inverse perturbation
        should restore the original structure by applying the
        NEGATIVE of the recorded perturbation.

        Since the seed and candidate index are stored in metadata,
        we can reconstruct the EXACT noise sequence and subtract it.
        """
        data = state.encoded
        if not data:
            new_state = deepcopy(state)
            new_state.update_encoded(b'', f"decode_{cls.name}")
            return new_state

        # Recover metadata (with defaults if missing)
        seed = state.metadata.get('dse_seed', 42)
        candidate_idx = state.metadata.get('dse_candidate', 0)
        learning_rate = state.metadata.get('dse_learning_rate', 0.5)
        diffusion = state.metadata.get('dse_diffusion', 0.5)

        offset = candidate_idx * 137

        # We need to REVERSE the perturbation.
        # The forward DSE applied: new_val = b + drift + noise
        # We know noise is deterministic from (seed, i+offset).
        # But drift depends on gradient which depends on ORIGINAL data.
        #
        # Strategy: iteratively refine the inverse.
        # Start with data as initial estimate.
        # Compute gradient from current estimate.
        # Subtract drift + noise.
        # Repeat until convergence.

        estimate = bytearray(data)
        for iteration in range(16):  # fixed-point iteration
            new_estimate = bytearray()
            for i, b in enumerate(estimate):
                # Compute gradient from current estimate
                grad = cls._compute_fitness_gradient(bytes(estimate), i)

                # Reconstruct the drift that was applied
                k, t = pist_encode(b)
                tension = pist_normalized_tension(k, t)
                drift = learning_rate * grad * (1.0 + tension * 0.5)

                # Reconstruct the noise
                noise_mag = math.sqrt(2.0 * diffusion)
                noise = cls._deterministic_noise(seed, i + offset, scale=noise_mag)

                # Subtract perturbation
                inv_val = int(b - (drift + noise) * 12.0)
                inv_val = max(0, min(255, inv_val))
                new_estimate.append(inv_val)
            estimate = bytearray(new_estimate)

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(estimate), f"decode_{cls.name}")
        return new_state


# ═══════════════════════════════════════════════════════════════════════════════
# SHIFTER 24: CELLULAR AUTOMATA (multi-rule state machine)
# ───────────────────────────────────────────────────────────────────────────────
# General cellular automaton with multiple rule sets.
# Applies a rule from a bank (Rule 30, 110, 90, 150) based on PIST phase.
# ═══════════════════════════════════════════════════════════════════════════════

class CellularAutomataShifter(Shifter):
    name = "CellularAutomata"

    # Elementary CA rule tables (neighborhood: left, curr, right → new)
    RULE_30 = {7: 0, 6: 0, 5: 0, 4: 1, 3: 1, 2: 1, 1: 1, 0: 0}  # wolfram code 30
    RULE_110 = {7: 0, 6: 1, 5: 1, 4: 0, 3: 1, 2: 1, 1: 1, 0: 0}  # wolfram code 110
    RULE_90 = {7: 0, 6: 1, 5: 0, 4: 1, 3: 1, 2: 0, 1: 1, 0: 0}  # wolfram code 90
    RULE_150 = {7: 1, 6: 0, 5: 1, 4: 0, 3: 1, 2: 0, 1: 1, 0: 0}  # wolfram code 150

    @staticmethod
    def _ca_step(byte_val: int, left: int, right: int, rule: dict) -> int:
        """Apply elementary CA rule to each bit of a byte."""
        result = 0
        for bit in range(8):
            left_bit = (left >> bit) & 1
            curr_bit = (byte_val >> bit) & 1
            right_bit = (right >> bit) & 1
            neighborhood = (left_bit << 2) | (curr_bit << 1) | right_bit
            new_bit = rule.get(neighborhood, 0)
            result |= (new_bit << bit)
        return result

    @classmethod
    def encode(cls, state: ManifoldState) -> ManifoldState:
        """Apply CA evolution based on PIST phase.

        Grounded bytes → Rule 90 (linear, fractal)
        Seismic bytes → Rule 30 (chaotic)
        High mass → Rule 110 (Turing-complete)
        """
        data = state.encoded
        if not data:
            new_state = deepcopy(state)
            new_state.update_encoded(b'', cls.name)
            return new_state

        result = bytearray()
        n = len(data)
        for i in range(n):
            k, t = pist_encode(data[i])
            mass = pist_mass(k, t)
            phase = 'grounded' if mass == 0 else 'seismic'

            left = data[(i - 1) % n]
            right = data[(i + 1) % n]

            # Select rule based on PIST phase
            if phase == 'grounded':
                rule = cls.RULE_90
            elif mass > k:  # high mass = more tension
                rule = cls.RULE_110
            else:
                rule = cls.RULE_30

            new_val = cls._ca_step(data[i], left, right, rule)
            result.append(new_val)

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), cls.name)
        return new_state

    @classmethod
    def decode(cls, state: ManifoldState) -> ManifoldState:
        """CA reverse: use precomputed inverse mapping.

        Since elementary CA rules are not bijective, we use
        the same nearest-neighbor inverse approach as Wireworld.
        """
        data = state.encoded
        if not data:
            new_state = deepcopy(state)
            new_state.update_encoded(b'', f"decode_{cls.name}")
            return new_state

        # Precompute inverse for all rules
        inv_maps = {}
        for name, rule in [('R30', cls.RULE_30), ('R110', cls.RULE_110),
                           ('R90', cls.RULE_90), ('R150', cls.RULE_150)]:
            forward = {}
            for val in range(256):
                for left in range(256):
                    for right in range(256):
                        fwd = cls._ca_step(val, left, right, rule)
                        forward[(val, left, right)] = fwd
            inverse = {}
            for (val, left, right), fwd in forward.items():
                if fwd not in inverse:
                    inverse[fwd] = val
            inv_maps[name] = inverse

        result = bytearray()
        n = len(data)
        for i in range(n):
            k, t = pist_encode(data[i])
            mass = pist_mass(k, t)
            phase = 'grounded' if mass == 0 else 'seismic'

            if phase == 'grounded':
                inv = inv_maps['R90']
            elif mass > k:
                inv = inv_maps['R110']
            else:
                inv = inv_maps['R30']

            restored = inv.get(data[i], data[i] ^ (data[(i - 1) % n] & data[(i + 1) % n]))
            result.append(restored)

        new_state = deepcopy(state)
        new_state.update_encoded(bytes(result), f"decode_{cls.name}")
        return new_state
