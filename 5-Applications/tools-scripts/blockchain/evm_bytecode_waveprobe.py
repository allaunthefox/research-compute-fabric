#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""EVM Bytecode Waveprobe — Structural classification of smart contract bytecode.

Adapts the Waveprobe v0.1 perturbation instrument (raw byte probes) to the
specific structure of EVM bytecode. Produces heat, torsion, and anisotropy
maps that classify contract regions as cold/warm/hot without requiring ABI
decoding or Solidity-level decompilation.

This module operates on raw deployed bytecode, not source code.

Usage:
    from scripts.evm_bytecode_waveprobe import EVMBytecodeWaveprobe

    probe = EVMBytecodeWaveprobe(bytecode_hex="0x6060...")
    result = probe.analyze()
    # result.heat_map, result.classification, result.aggregate

Compliance integration:
    The classification output feeds into the canal routing metric for
    gas-optimal path selection. The valve layer maps to the compliance
    front layer (see MEV_COMPLIANCE_BOUNDARY.md).

Conforms to Waveprobe v0.1 Implementation Contract.
"""

from __future__ import annotations

import hashlib
import json
import math
import struct
import zlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

# ── EVM Opcode Constants ─────────────────────────────────────────────────────

# Common opcodes for structural classification
STOP        = 0x00
ADD         = 0x01
MUL         = 0x02
SUB         = 0x03
JUMPDEST    = 0x5B
JUMP        = 0x56
JUMPI       = 0x57
PUSH1       = 0x60
PUSH32      = 0x7F
DUP1        = 0x80
DUP16       = 0x8F
SWAP1       = 0x90
SWAP16      = 0x9F
LOG0        = 0xA0
LOG4        = 0xA4
CALL        = 0xF1
CALLCODE    = 0xF2
RETURN      = 0xF3
DELEGATECALL = 0xF4
CREATE2     = 0xF5
STATICCALL  = 0xFA
REVERT      = 0xFD
SELFDESTRUCT = 0xFF

# Opcodes that carry inline data (PUSH1 through PUSH32)
PUSH_RANGE = range(PUSH1, PUSH32 + 1)

# High-heat opcodes — dynamic dispatch, external interaction
HIGH_HEAT_OPCODES = frozenset({
    CALL, CALLCODE, DELEGATECALL, STATICCALL,
    CREATE2, SELFDESTRUCT,
})

# Control flow opcodes
CONTROL_FLOW_OPCODES = frozenset({
    JUMP, JUMPI, JUMPDEST, RETURN, REVERT, STOP,
})

# Standard feature dimension for the waveprobe
FEATURE_DIM = 8

# Waveprobe chunk size (contract spec: 4096, but we adapt to bytecode length)
DEFAULT_CHUNK_SIZE = 4096

# Classification thresholds
HEAT_COLD_THRESHOLD = 0.05
HEAT_HOT_THRESHOLD = 0.25

EPSILON = 1e-9


# ── Feature Extraction ───────────────────────────────────────────────────────

def _byte_entropy(data: bytes) -> float:
    """Shannon entropy of byte distribution, normalized to [0, 1]."""
    if not data:
        return 0.0
    counts = [0] * 256
    for b in data:
        counts[b] += 1
    n = len(data)
    entropy = 0.0
    for c in counts:
        if c > 0:
            p = c / n
            entropy -= p * math.log2(p)
    return entropy / 8.0  # normalize to [0, 1]


def _opcode_density(data: bytes) -> float:
    """Fraction of bytes that are standalone opcodes (not PUSH data)."""
    if not data:
        return 0.0
    i = 0
    opcode_count = 0
    while i < len(data):
        b = data[i]
        opcode_count += 1
        if b in PUSH_RANGE:
            push_size = b - PUSH1 + 1
            i += 1 + push_size
        else:
            i += 1
    return min(1.0, opcode_count / max(1, len(data)))


def _high_heat_density(data: bytes) -> float:
    """Fraction of opcodes that are high-heat (CALL, DELEGATECALL, etc.)."""
    if not data:
        return 0.0
    i = 0
    total = 0
    hot = 0
    while i < len(data):
        b = data[i]
        total += 1
        if b in HIGH_HEAT_OPCODES:
            hot += 1
        if b in PUSH_RANGE:
            i += 1 + (b - PUSH1 + 1)
        else:
            i += 1
    return hot / max(1, total)


def _control_flow_density(data: bytes) -> float:
    """Fraction of opcodes that are control flow."""
    if not data:
        return 0.0
    i = 0
    total = 0
    cf = 0
    while i < len(data):
        b = data[i]
        total += 1
        if b in CONTROL_FLOW_OPCODES:
            cf += 1
        if b in PUSH_RANGE:
            i += 1 + (b - PUSH1 + 1)
        else:
            i += 1
    return cf / max(1, total)


def _push_data_ratio(data: bytes) -> float:
    """Fraction of bytes consumed by PUSH inline data."""
    if not data:
        return 0.0
    i = 0
    push_bytes = 0
    while i < len(data):
        b = data[i]
        if b in PUSH_RANGE:
            size = b - PUSH1 + 1
            push_bytes += size
            i += 1 + size
        else:
            i += 1
    return push_bytes / max(1, len(data))


def _jumpdest_spacing_cv(data: bytes) -> float:
    """Coefficient of variation of JUMPDEST spacing.

    Low CV = regular function dispatch table (cold).
    High CV = irregular control flow (warm/hot).
    """
    positions: list[int] = []
    i = 0
    while i < len(data):
        b = data[i]
        if b == JUMPDEST:
            positions.append(i)
        if b in PUSH_RANGE:
            i += 1 + (b - PUSH1 + 1)
        else:
            i += 1

    if len(positions) < 2:
        return 0.0

    spacings = [positions[j + 1] - positions[j] for j in range(len(positions) - 1)]
    mean_sp = sum(spacings) / len(spacings)
    if mean_sp < EPSILON:
        return 0.0
    var_sp = sum((s - mean_sp) ** 2 for s in spacings) / len(spacings)
    return math.sqrt(var_sp) / (mean_sp + EPSILON)


def _repetition_rate(data: bytes) -> float:
    """Adjacent byte repetition rate."""
    if len(data) < 2:
        return 0.0
    reps = sum(1 for i in range(1, len(data)) if data[i] == data[i - 1])
    return reps / (len(data) - 1)


def _compression_score(data: bytes) -> float:
    """Deterministic compression scalar using zlib (level 6).

    Returns compressed_size / original_size. Lower = more compressible.
    """
    if not data:
        return 1.0
    compressed = zlib.compress(data, level=6)
    return len(compressed) / len(data)


def extract_features(data: bytes) -> List[float]:
    """Extract 8-dimensional feature vector Φ(x) from EVM bytecode.

    Features are normalized to [0, 1] where possible.
    """
    return [
        _byte_entropy(data),           # f0: byte-level entropy
        _opcode_density(data),          # f1: opcode vs data ratio
        _high_heat_density(data),       # f2: CALL/DELEGATECALL density
        _control_flow_density(data),    # f3: JUMP/JUMPI/RETURN density
        _push_data_ratio(data),         # f4: inline PUSH data fraction
        _jumpdest_spacing_cv(data),     # f5: JUMPDEST spacing irregularity
        _repetition_rate(data),         # f6: adjacent byte repetition
        _compression_score(data),       # f7: zlib compression ratio
    ]


# ── Perturbation Families (EVM-adapted) ──────────────────────────────────────

def _deterministic_position(seed_hex: str, family_name: str, length: int,
                             validator=None) -> int:
    """Deterministic position selection per the waveprobe contract.

    Uses SHA-256 chaining to generate candidate indices.
    """
    family_seed = hashlib.sha256(
        (seed_hex + ":" + family_name).encode()
    ).digest()

    offset = 0
    while True:
        if offset + 4 > len(family_seed):
            family_seed = hashlib.sha256(family_seed).digest()
            offset = 0
        word = struct.unpack_from(">I", family_seed, offset)[0]
        offset += 4
        idx = word % length
        if validator is None or validator(idx):
            return idx


def _deterministic_positions(seed_hex: str, family_name: str, length: int,
                              count: int, window_start: int = 0,
                              window_end: Optional[int] = None) -> List[int]:
    """Select multiple distinct deterministic positions within a window."""
    if window_end is None:
        window_end = length - 1
    window_len = window_end - window_start + 1

    family_seed = hashlib.sha256(
        (seed_hex + ":" + family_name + ":multi").encode()
    ).digest()

    selected: list[int] = []
    offset = 0
    while len(selected) < count:
        if offset + 4 > len(family_seed):
            family_seed = hashlib.sha256(family_seed).digest()
            offset = 0
        word = struct.unpack_from(">I", family_seed, offset)[0]
        offset += 4
        idx = window_start + (word % window_len)
        if idx not in selected:
            selected.append(idx)

    return sorted(selected)


def probe_opcode_swap(data: bytes, seed_hex: str) -> Tuple[bytes, Dict[str, Any]]:
    """P1: Swap two adjacent opcodes (skip over PUSH data).

    EVM adaptation of adjacent_swap. We swap opcode positions only,
    not PUSH inline data.
    """
    # Build opcode position list (skipping PUSH data bytes)
    opcode_positions: list[int] = []
    i = 0
    while i < len(data):
        opcode_positions.append(i)
        b = data[i]
        if b in PUSH_RANGE:
            i += 1 + (b - PUSH1 + 1)
        else:
            i += 1

    if len(opcode_positions) < 2:
        return data, {"probe_family": "opcode_swap", "fallback_used": True,
                      "positions": [], "reason": "insufficient_opcodes"}

    # Find a valid adjacent pair
    k_idx = _deterministic_position(
        seed_hex, "opcode_swap", len(opcode_positions) - 1
    )
    pos_a = opcode_positions[k_idx]
    pos_b = opcode_positions[k_idx + 1]

    result = bytearray(data)
    result[pos_a], result[pos_b] = result[pos_b], result[pos_a]

    return bytes(result), {
        "probe_family": "opcode_swap",
        "fallback_used": False,
        "positions": [pos_a, pos_b],
        "original_bytes_hex": [f"{data[pos_a]:02x}", f"{data[pos_b]:02x}"],
        "new_bytes_hex": [f"{result[pos_a]:02x}", f"{result[pos_b]:02x}"],
    }


def probe_push_data_toggle(data: bytes, seed_hex: str) -> Tuple[bytes, Dict[str, Any]]:
    """P2: Toggle a PUSH data byte.

    EVM adaptation of whitespace_toggle. Flips the LSB of a PUSH inline
    data byte — the smallest meaningful perturbation to contract arguments.
    """
    # Find all PUSH data byte positions
    push_data_positions: list[int] = []
    i = 0
    while i < len(data):
        b = data[i]
        if b in PUSH_RANGE:
            size = b - PUSH1 + 1
            for j in range(1, size + 1):
                if i + j < len(data):
                    push_data_positions.append(i + j)
            i += 1 + size
        else:
            i += 1

    if not push_data_positions:
        # Fallback: flip LSB of a random position
        k = _deterministic_position(seed_hex, "push_data_toggle", len(data))
        result = bytearray(data)
        result[k] ^= 0x01
        return bytes(result), {
            "probe_family": "push_data_toggle",
            "fallback_used": True,
            "positions": [k],
        }

    k = push_data_positions[
        _deterministic_position(seed_hex, "push_data_toggle", len(push_data_positions))
    ]
    result = bytearray(data)
    result[k] ^= 0x01

    return bytes(result), {
        "probe_family": "push_data_toggle",
        "fallback_used": False,
        "positions": [k],
        "original_bytes_hex": [f"{data[k]:02x}"],
        "new_bytes_hex": [f"{result[k]:02x}"],
    }


def probe_opcode_variant_flip(data: bytes, seed_hex: str) -> Tuple[bytes, Dict[str, Any]]:
    """P3: Flip opcode variant (e.g., PUSH1↔PUSH2, DUP1↔DUP2).

    EVM adaptation of ascii_case_flip. Tests width sensitivity of the
    instruction encoding.
    """
    # Find opcode positions that have a "flip partner"
    flippable: list[int] = []
    i = 0
    while i < len(data):
        b = data[i]
        # DUP family: DUP1-DUP16
        if DUP1 <= b <= DUP16:
            flippable.append(i)
        # SWAP family: SWAP1-SWAP16
        elif SWAP1 <= b <= SWAP16:
            flippable.append(i)
        # LOG family: LOG0-LOG4
        elif LOG0 <= b <= LOG4:
            flippable.append(i)

        if b in PUSH_RANGE:
            i += 1 + (b - PUSH1 + 1)
        else:
            i += 1

    if not flippable:
        # Fallback: XOR a byte with 0x01
        k = _deterministic_position(seed_hex, "opcode_variant_flip", len(data))
        result = bytearray(data)
        result[k] ^= 0x01
        return bytes(result), {
            "probe_family": "opcode_variant_flip",
            "fallback_used": True,
            "positions": [k],
        }

    k = flippable[
        _deterministic_position(seed_hex, "opcode_variant_flip", len(flippable))
    ]
    result = bytearray(data)
    b = result[k]

    # Toggle the LSB of the opcode within its family
    if b % 2 == 0:
        result[k] = b + 1
    else:
        result[k] = b - 1

    return bytes(result), {
        "probe_family": "opcode_variant_flip",
        "fallback_used": False,
        "positions": [k],
        "original_bytes_hex": [f"{data[k]:02x}"],
        "new_bytes_hex": [f"{result[k]:02x}"],
    }


def probe_push_arg_delete(data: bytes, seed_hex: str) -> Tuple[bytes, Dict[str, Any]]:
    """P4: Delete a PUSH argument and shift locally (length-preserving).

    EVM adaptation of local_delete_compensate. Removes a PUSH inline
    argument byte and shifts the local window to preserve chunk length.
    """
    # Find PUSH instructions with data
    push_positions: list[Tuple[int, int]] = []  # (opcode_pos, data_size)
    i = 0
    while i < len(data):
        b = data[i]
        if b in PUSH_RANGE:
            size = b - PUSH1 + 1
            if i + size < len(data):
                push_positions.append((i, size))
            i += 1 + size
        else:
            i += 1

    if not push_positions:
        return data, {"probe_family": "push_arg_delete", "fallback_used": True,
                      "positions": [], "reason": "no_push_instructions"}

    idx = _deterministic_position(seed_hex, "push_arg_delete", len(push_positions))
    opcode_pos, _data_size = push_positions[idx]
    delete_pos = opcode_pos + 1  # delete first data byte

    # Local window shift (radius 8)
    a = max(0, delete_pos - 8)
    b = min(len(data) - 1, delete_pos + 8)

    result = bytearray(data)
    # Shift left within window
    for j in range(delete_pos, b):
        result[j] = result[j + 1]
    result[b] = data[b]  # compensate

    return bytes(result), {
        "probe_family": "push_arg_delete",
        "fallback_used": False,
        "positions": [delete_pos],
        "window_start": a,
        "window_end": b,
        "support_type": "window_shift",
    }


def probe_modal_opcode_substitute(data: bytes, seed_hex: str) -> Tuple[bytes, Dict[str, Any]]:
    """P5: Replace opcode with the local modal opcode.

    EVM adaptation of modal_byte_substitute. Replaces an opcode with
    the most common opcode in its neighborhood.
    """
    # Build opcode positions
    opcode_positions: list[int] = []
    i = 0
    while i < len(data):
        opcode_positions.append(i)
        b = data[i]
        if b in PUSH_RANGE:
            i += 1 + (b - PUSH1 + 1)
        else:
            i += 1

    if len(opcode_positions) < 3:
        return data, {"probe_family": "modal_opcode_substitute", "fallback_used": True,
                      "positions": [], "reason": "insufficient_opcodes"}

    k_idx = _deterministic_position(
        seed_hex, "modal_opcode_substitute", len(opcode_positions)
    )
    center = opcode_positions[k_idx]

    # Neighborhood: 16 opcodes in each direction
    start_idx = max(0, k_idx - 16)
    end_idx = min(len(opcode_positions), k_idx + 17)
    neighborhood_positions = opcode_positions[start_idx:end_idx]

    # Count opcode frequencies in neighborhood
    freq: dict[int, int] = {}
    for pos in neighborhood_positions:
        op = data[pos]
        freq[op] = freq.get(op, 0) + 1

    # Modal byte (smallest value on tie)
    modal_byte = min(freq.keys(), key=lambda b: (-freq[b], b))

    result = bytearray(data)
    original = result[center]
    result[center] = modal_byte

    return bytes(result), {
        "probe_family": "modal_opcode_substitute",
        "fallback_used": False,
        "positions": [center],
        "original_bytes_hex": [f"{original:02x}"],
        "new_bytes_hex": [f"{modal_byte:02x}"],
        "substitution_changed": original != modal_byte,
    }


def probe_jumpdest_scramble(data: bytes, seed_hex: str) -> Tuple[bytes, Dict[str, Any]]:
    """P6: Rotate three JUMPDEST-adjacent values cyclically.

    EVM adaptation of local_motif_scramble. Permutes entries in a
    JUMPDEST dispatch table to measure router topology sensitivity.
    """
    # Find JUMPDEST positions
    jumpdest_positions: list[int] = []
    i = 0
    while i < len(data):
        if data[i] == JUMPDEST:
            jumpdest_positions.append(i)
        b = data[i]
        if b in PUSH_RANGE:
            i += 1 + (b - PUSH1 + 1)
        else:
            i += 1

    if len(jumpdest_positions) < 3:
        # Fallback to raw motif scramble on any 3 positions
        positions = _deterministic_positions(seed_hex, "jumpdest_scramble",
                                              len(data), 3)
        result = bytearray(data)
        p_i, p_j, p_l = positions
        result[p_i], result[p_j], result[p_l] = data[p_j], data[p_l], data[p_i]
        return bytes(result), {
            "probe_family": "jumpdest_scramble",
            "fallback_used": True,
            "positions": positions,
        }

    # Pick 3 JUMPDESTs
    if len(jumpdest_positions) == 3:
        selected = sorted(jumpdest_positions)
    else:
        selected = _deterministic_positions(
            seed_hex, "jumpdest_scramble",
            len(jumpdest_positions), 3
        )
        selected = sorted([jumpdest_positions[s] for s in selected])

    p_i, p_j, p_l = selected
    result = bytearray(data)
    # Rotate the byte AFTER each JUMPDEST (the instruction that follows)
    # This permutes what happens at each dispatch point
    ri = min(p_i + 1, len(data) - 1)
    rj = min(p_j + 1, len(data) - 1)
    rl = min(p_l + 1, len(data) - 1)
    result[ri], result[rj], result[rl] = data[rj], data[rl], data[ri]

    return bytes(result), {
        "probe_family": "jumpdest_scramble",
        "fallback_used": False,
        "positions": [ri, rj, rl],
        "jumpdest_positions": [p_i, p_j, p_l],
    }


# ── Probe Families Registry ─────────────────────────────────────────────────

PROBE_FAMILIES = [
    ("opcode_swap", probe_opcode_swap),
    ("push_data_toggle", probe_push_data_toggle),
    ("opcode_variant_flip", probe_opcode_variant_flip),
    ("push_arg_delete", probe_push_arg_delete),
    ("modal_opcode_substitute", probe_modal_opcode_substitute),
    ("jumpdest_scramble", probe_jumpdest_scramble),
]


# ── Aggregate Metrics ────────────────────────────────────────────────────────

def _l2_norm(vec: Sequence[float]) -> float:
    return math.sqrt(sum(v * v for v in vec))


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _covariance_matrix(vectors: List[List[float]]) -> List[List[float]]:
    """Sample covariance of displacement vectors."""
    m = len(vectors)
    d = len(vectors[0]) if vectors else 0
    if m < 2 or d == 0:
        return [[0.0] * d for _ in range(d)]

    means = [sum(v[j] for v in vectors) / m for j in range(d)]
    cov = [[0.0] * d for _ in range(d)]
    for i_dim in range(d):
        for j_dim in range(d):
            cov[i_dim][j_dim] = sum(
                (v[i_dim] - means[i_dim]) * (v[j_dim] - means[j_dim])
                for v in vectors
            ) / (m - 1)
    return cov


def _trace(matrix: List[List[float]]) -> float:
    return sum(matrix[i][i] for i in range(len(matrix)))


def _max_eigenvalue_power(matrix: List[List[float]], iterations: int = 50) -> float:
    """Estimate largest eigenvalue via power iteration."""
    d = len(matrix)
    if d == 0:
        return 0.0
    vec = [1.0 / math.sqrt(d)] * d
    for _ in range(iterations):
        new_vec = [sum(matrix[i][j] * vec[j] for j in range(d)) for i in range(d)]
        norm = _l2_norm(new_vec)
        if norm < EPSILON:
            return 0.0
        vec = [v / norm for v in new_vec]
    # Rayleigh quotient
    mv = [sum(matrix[i][j] * vec[j] for j in range(d)) for i in range(d)]
    return _dot(vec, mv)


# ── Main Analysis ────────────────────────────────────────────────────────────

@dataclass
class ChunkProbeResult:
    """Results for a single probe family on one chunk."""
    probe_family: str
    feature_displacement: List[float]
    feature_displacement_magnitude: float
    compression_displacement: float
    signed_compression_delta: float
    metadata: Dict[str, Any]


@dataclass
class ChunkAnalysis:
    """Full waveprobe analysis for one bytecode chunk."""
    chunk_offset: int
    chunk_length: int
    content_sha256: str
    base_features: List[float]
    base_compression: float
    probes: List[ChunkProbeResult]

    # Aggregates
    sensitivity: float = 0.0
    compression_sensitivity: float = 0.0
    compression_variance: float = 0.0
    anisotropy: float = 0.0
    heat: float = 0.0
    torsion: Optional[float] = None
    mean_response_direction: List[float] = field(default_factory=list)
    classification: str = "cold"   # cold | warm | hot


@dataclass
class EVMWaveprobeResult:
    """Complete waveprobe analysis of an EVM contract."""
    bytecode_sha256: str
    total_length: int
    chunk_count: int
    chunks: List[ChunkAnalysis]

    # Contract-level aggregates
    overall_heat: float = 0.0
    overall_classification: str = "cold"
    heat_map: List[float] = field(default_factory=list)
    classification_map: List[str] = field(default_factory=list)

    # Feature summary
    high_heat_region_count: int = 0
    warm_region_count: int = 0
    cold_region_count: int = 0


class EVMBytecodeWaveprobe:
    """EVM bytecode waveprobe instrument.

    Probes contract bytecode with 6 EVM-adapted perturbation families,
    measures structural response, and classifies regions.
    """

    def __init__(
        self,
        bytecode_hex: str = "",
        bytecode_raw: bytes = b"",
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        release_id: str = "evm-probe-v0.1",
    ):
        if bytecode_hex:
            clean = bytecode_hex.strip()
            if clean.startswith("0x") or clean.startswith("0X"):
                clean = clean[2:]
            self.bytecode = bytes.fromhex(clean)
        elif bytecode_raw:
            self.bytecode = bytecode_raw
        else:
            self.bytecode = b""

        self.chunk_size = chunk_size
        self.release_id = release_id

    def _chunk_bytecode(self) -> List[Tuple[int, bytes]]:
        """Split bytecode into overlapping chunks (stride = chunk_size // 2)."""
        data = self.bytecode
        if not data:
            return []

        stride = max(1, self.chunk_size // 2)
        chunks: list[Tuple[int, bytes]] = []

        offset = 0
        while offset < len(data):
            end = min(offset + self.chunk_size, len(data))
            chunk = data[offset:end]
            # Pad if needed to maintain chunk_size
            if len(chunk) < self.chunk_size:
                chunk = chunk + b"\x00" * (self.chunk_size - len(chunk))
            chunks.append((offset, chunk))
            offset += stride
            if end >= len(data):
                break

        return chunks

    def _probe_seed(self, chunk_offset: int, content_sha256: str) -> str:
        """Deterministic probe seed per the implementation contract."""
        raw = f"{self.release_id}:{chunk_offset}:{content_sha256}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def _analyze_chunk(self, chunk_offset: int, chunk_data: bytes) -> ChunkAnalysis:
        """Run all 6 probe families on a single chunk."""
        content_sha = hashlib.sha256(chunk_data).hexdigest()
        seed = self._probe_seed(chunk_offset, content_sha)

        base_features = extract_features(chunk_data)
        base_compression = _compression_score(chunk_data)

        probes: list[ChunkProbeResult] = []
        displacement_vectors: list[list[float]] = []

        for family_name, probe_fn in PROBE_FAMILIES:
            perturbed, metadata = probe_fn(chunk_data, seed)
            perturbed_features = extract_features(perturbed)
            perturbed_compression = _compression_score(perturbed)

            # Feature displacement vector
            disp_vec = [
                perturbed_features[j] - base_features[j]
                for j in range(len(base_features))
            ]
            disp_mag = _l2_norm(disp_vec)
            comp_disp = abs(perturbed_compression - base_compression)
            signed_comp = perturbed_compression - base_compression

            probes.append(ChunkProbeResult(
                probe_family=family_name,
                feature_displacement=disp_vec,
                feature_displacement_magnitude=disp_mag,
                compression_displacement=comp_disp,
                signed_compression_delta=signed_comp,
                metadata=metadata,
            ))
            displacement_vectors.append(disp_vec)

        # ── Aggregate metrics (per waveprobe contract) ───────────────────
        m = len(probes)

        # Sensitivity
        sensitivity = sum(p.feature_displacement_magnitude for p in probes) / m

        # Compression sensitivity
        comp_sens = sum(p.compression_displacement for p in probes) / m

        # Compression variance (sample variance)
        if m > 1:
            comp_var = sum(
                (p.compression_displacement - comp_sens) ** 2 for p in probes
            ) / (m - 1)
        else:
            comp_var = 0.0

        # Anisotropy
        cov = _covariance_matrix(displacement_vectors)
        tr = _trace(cov)
        lmax = _max_eigenvalue_power(cov)
        anisotropy = lmax / (tr + EPSILON)

        # Heat (frozen coefficients: alpha=0.5, beta=0.5)
        heat = comp_sens + 0.5 * comp_var + 0.5 * sensitivity

        # Mean response direction
        d = len(base_features)
        mean_dir = [
            sum(dv[j] for dv in displacement_vectors) / m
            for j in range(d)
        ]

        # Classification
        if heat >= HEAT_HOT_THRESHOLD:
            classification = "hot"
        elif heat >= HEAT_COLD_THRESHOLD:
            classification = "warm"
        else:
            classification = "cold"

        return ChunkAnalysis(
            chunk_offset=chunk_offset,
            chunk_length=len(chunk_data),
            content_sha256=content_sha,
            base_features=base_features,
            base_compression=base_compression,
            probes=probes,
            sensitivity=sensitivity,
            compression_sensitivity=comp_sens,
            compression_variance=comp_var,
            anisotropy=anisotropy,
            heat=heat,
            mean_response_direction=mean_dir,
            classification=classification,
        )

    def analyze(self) -> EVMWaveprobeResult:
        """Run the full waveprobe analysis on the contract bytecode."""
        bytecode_sha = hashlib.sha256(self.bytecode).hexdigest()
        chunks = self._chunk_bytecode()

        chunk_results: list[ChunkAnalysis] = []
        for offset, chunk_data in chunks:
            chunk_results.append(self._analyze_chunk(offset, chunk_data))

        # Contract-level aggregates
        heat_map = [c.heat for c in chunk_results]
        classification_map = [c.classification for c in chunk_results]

        hot_count = sum(1 for c in classification_map if c == "hot")
        warm_count = sum(1 for c in classification_map if c == "warm")
        cold_count = sum(1 for c in classification_map if c == "cold")

        overall_heat = sum(heat_map) / max(1, len(heat_map))

        if hot_count > 0:
            overall_class = "hot"
        elif warm_count > len(chunk_results) * 0.3:
            overall_class = "warm"
        else:
            overall_class = "cold"

        return EVMWaveprobeResult(
            bytecode_sha256=bytecode_sha,
            total_length=len(self.bytecode),
            chunk_count=len(chunk_results),
            chunks=chunk_results,
            overall_heat=overall_heat,
            overall_classification=overall_class,
            heat_map=heat_map,
            classification_map=classification_map,
            high_heat_region_count=hot_count,
            warm_region_count=warm_count,
            cold_region_count=cold_count,
        )

    def to_json(self, result: Optional[EVMWaveprobeResult] = None) -> str:
        """Serialize analysis result to JSON."""
        if result is None:
            result = self.analyze()

        def _chunk_to_dict(c: ChunkAnalysis) -> Dict[str, Any]:
            return {
                "chunk_offset": c.chunk_offset,
                "chunk_length": c.chunk_length,
                "content_sha256": c.content_sha256,
                "base_features": [round(f, 8) for f in c.base_features],
                "base_compression": round(c.base_compression, 8),
                "classification": c.classification,
                "aggregate": {
                    "sensitivity": round(c.sensitivity, 8),
                    "compression_sensitivity": round(c.compression_sensitivity, 8),
                    "compression_variance": round(c.compression_variance, 8),
                    "anisotropy": round(c.anisotropy, 8),
                    "heat": round(c.heat, 8),
                    "torsion": round(c.torsion, 8) if c.torsion is not None else None,
                },
                "probes": [
                    {
                        "probe_family": p.probe_family,
                        "feature_displacement_magnitude": round(p.feature_displacement_magnitude, 8),
                        "compression_displacement": round(p.compression_displacement, 8),
                    }
                    for p in c.probes
                ],
            }

        return json.dumps({
            "waveprobe_version": "0.1-evm",
            "release_id": self.release_id,
            "bytecode_sha256": result.bytecode_sha256,
            "total_length": result.total_length,
            "chunk_count": result.chunk_count,
            "overall_heat": round(result.overall_heat, 8),
            "overall_classification": result.overall_classification,
            "high_heat_region_count": result.high_heat_region_count,
            "warm_region_count": result.warm_region_count,
            "cold_region_count": result.cold_region_count,
            "heat_map": [round(h, 6) for h in result.heat_map],
            "classification_map": result.classification_map,
            "chunks": [_chunk_to_dict(c) for c in result.chunks],
        }, indent=2)


# ── CLI ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="EVM Bytecode Waveprobe — structural classification of smart contracts"
    )
    parser.add_argument("bytecode", nargs="?",
                        help="Hex-encoded bytecode (0x-prefixed or raw hex)")
    parser.add_argument("--file", help="Read bytecode from file (hex-encoded)")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE,
                        help=f"Chunk size for analysis (default {DEFAULT_CHUNK_SIZE})")
    parser.add_argument("--summary", action="store_true",
                        help="Print summary only (no per-chunk details)")
    parser.add_argument("--json", action="store_true",
                        help="Output full JSON analysis")

    args = parser.parse_args()

    bytecode_hex = ""
    if args.file:
        bytecode_hex = open(args.file).read().strip()
    elif args.bytecode:
        bytecode_hex = args.bytecode
    else:
        print("Usage: evm_bytecode_waveprobe.py <bytecode_hex> | --file <path>")
        sys.exit(1)

    probe = EVMBytecodeWaveprobe(
        bytecode_hex=bytecode_hex,
        chunk_size=args.chunk_size,
    )
    result = probe.analyze()

    if args.json:
        print(probe.to_json(result))
    elif args.summary:
        print(f"Contract: {result.bytecode_sha256[:16]}...")
        print(f"Length:   {result.total_length} bytes")
        print(f"Chunks:   {result.chunk_count}")
        print(f"Heat:     {result.overall_heat:.6f}")
        print(f"Class:    {result.overall_classification}")
        print(f"  Cold:   {result.cold_region_count}")
        print(f"  Warm:   {result.warm_region_count}")
        print(f"  Hot:    {result.high_heat_region_count}")
    else:
        print(f"Contract: {result.bytecode_sha256[:16]}...")
        print(f"Length:   {result.total_length} bytes  |  Chunks: {result.chunk_count}")
        print(f"Overall:  {result.overall_classification.upper()} (heat={result.overall_heat:.6f})")
        print()
        for i, chunk in enumerate(result.chunks):
            icon = {"cold": "🧊", "warm": "🌡️", "hot": "🔥"}.get(chunk.classification, "?")
            print(f"  [{i:3d}] offset={chunk.chunk_offset:6d}  "
                  f"heat={chunk.heat:.6f}  "
                  f"aniso={chunk.anisotropy:.4f}  "
                  f"{icon} {chunk.classification}")
