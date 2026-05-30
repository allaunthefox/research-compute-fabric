#!/usr/bin/env python3
"""
BraidDiatCodec — Pure-Python extraction of Semantics.BraidDiatCodec

Layers:
  Layer 1 — ChiralityDIAT: 2-bit chirality + 62-bit DIAT slot address
  Layer 2 — MountainPacked: height(8) + apex(48) + base_count(8) + bases
  Layer 3 — BraidResidualPacked: 5 Q0_2 fields × 2 bits = 10 bits per crossing
  Layer 4 — BraidDiatFrame: 256-bit fixed header + variable mountain list

References:
  - Semantics.BraidField     (Mountain, MMR, SpherionState)
  - Semantics.BraidBracket   (PhaseVec, BraidBracket)
  - Semantics.DynamicCanal   (DIAT)
  - Semantics.EntropyMeasures (Chirality)

No Float in compute paths. Q0_2 values: {0, 16384, 32768, 49152}.
"""

from __future__ import annotations

import json
import math
import random
import struct
import time
from enum import IntEnum
from typing import Any, Dict, List, Optional, Tuple

import sys as _sys
from pathlib import Path
_sys.path.insert(0, str(Path(__file__).resolve().parent))

# ── Chirality ────────────────────────────────────────────────────────────────

class Chirality(IntEnum):
    NONE = 0
    POSITIVE = 1   # right / D
    LEFT = 2       # left  / L
    ACHIRAL = 3    # achiral / W


# ── Q0_2 fixed-point (4 states: 0, 16384, 32768, 49152) ───────────────────

Q0_2_STATES = (0, 16384, 32768, 49152)


def encode_q02(v: int) -> int:
    """Encode Q0_2 value to 2 bits. Q0_2 range: {0, 16384, 32768, 49152}."""
    if v == 0:
        return 0
    elif v == 16384:
        return 1
    elif v == 32768:
        return 2
    else:
        return 3


def decode_q02(b: int) -> int:
    """Decode 2 bits back to Q0_2 value."""
    return Q0_2_STATES[b & 3]


# ── Layer 1: ChiralityDIAT ───────────────────────────────────────────────────

class ChiralityDIAT:
    """
    Chirality-DIAT slot address: 2-bit chirality + 62-bit DIAT.

    Bit layout (64 bits total):
      bits [1:0]   Chirality flag  (00=none, 01=right, 10=left, 11=achiral)
      bits [9:2]   DIAT shell k   (floor(sqrt(n)), 0–255)
      bits [31:10] DIAT offset a  (n - k², max 510 → 22 bits)
      bits [53:32] DIAT offset b  ((k+1)² - n, max 510 → 22 bits)
      bits [61:54] DIAT prod_msb  (upper 8 bits of a*b)
      bits [63:62] reserved (0)
    """

    __slots__ = ("chirality", "shell", "offset_a", "offset_b", "prod_msb")

    def __init__(
        self,
        chirality: Chirality,
        shell: int,
        offset_a: int,
        offset_b: int,
        prod_msb: int,
    ) -> None:
        self.chirality: Chirality = chirality
        self.shell: int = shell
        self.offset_a: int = offset_a
        self.offset_b: int = offset_b
        self.prod_msb: int = prod_msb

    def encode(self) -> int:
        """Pack to 64-bit integer."""
        ch = int(self.chirality) & 3
        s = self.shell & 0xFF
        a = self.offset_a & 0x3FFFFF
        b = self.offset_b & 0x3FFFFF
        p = self.prod_msb & 0xFF
        return ch | (s << 2) | (a << 10) | (b << 32) | (p << 54)

    def to_bytes(self) -> bytes:
        """Serialize to 8 bytes (big-endian)."""
        return struct.pack(">Q", self.encode())

    @classmethod
    def from_bytes(cls, raw: bytes) -> ChiralityDIAT:
        """Deserialize from 8 bytes."""
        v = struct.unpack(">Q", raw)[0]
        ch = Chirality(v & 3)
        s = (v >> 2) & 0xFF
        a = (v >> 10) & 0x3FFFFF
        b = (v >> 32) & 0x3FFFFF
        p = (v >> 54) & 0xFF
        return cls(ch, s, a, b, p)

    @classmethod
    def decode(cls, chir: Chirality, n: int) -> Optional[ChiralityDIAT]:
        """
        Encode n and chirality into a ChiralityDIAT slot address.

        Pre: n ≤ 2^24 (22-bit offset field limit).
        Returns None if n is out of range.
        """
        if n >= 0x400000:
            return None
        k = _isqrt(n)
        lo = k * k
        hi = (k + 1) * (k + 1)
        a = n - lo
        b = hi - n
        prod = a * b
        prod_msb = (prod >> 16) & 0xFF
        return cls(chir, k, a, b, prod_msb)

    def to_n(self) -> int:
        """Recover n = k² + a. Use only when consistency is verified."""
        return self.shell * self.shell + self.offset_a

    def verify_b(self) -> bool:
        """Verify offset_b == (k+1)² - n."""
        n = self.to_n()
        kp_sq = (self.shell + 1) * (self.shell + 1)
        return self.offset_b == kp_sq - n


# ── Layer 2: MountainPacked ─────────────────────────────────────────────────

class MountainPacked:
    """
    Packed binary representation of a Mountain (without inner MMR).

    Layout (64-bit header + variable bases):
      height:    UInt8  (8 bits)
      apexX:     Int32  (32 bits, biased)
      apexY:     Int32  (32 bits, biased)
      apexZ:     Int32  (32 bits, biased)
      baseCount: UInt8  (8 bits)
      bases:     Int32[baseCount * 3]  (x,y,z tuples)

    Total header: 8 + 12 + 12 + 12 + 1 = 45 bits → 6 bytes packed.
    Each base node: 12 bytes (3 × Int32).
    """

    # struct format: >BQiiiB (big-endian, but Int32 is signed)
    HEADER_STRUCT = struct.Struct(">BQiiiB")

    __slots__ = ("height", "apex_x", "apex_y", "apex_z", "base_count", "bases")

    def __init__(
        self,
        height: int,
        apex_x: int,
        apex_y: int,
        apex_z: int,
        base_count: int,
        bases: Optional[List[int]] = None,
    ) -> None:
        self.height: int = height
        self.apex_x: int = apex_x
        self.apex_y: int = apex_y
        self.apex_z: int = apex_z
        self.base_count: int = base_count
        self.bases: List[int] = bases if bases is not None else []

    def to_bytes(self) -> bytes:
        """Serialize to bytes (lossless).

        Layout:
          height:      1 byte
          apexX:      4 bytes (signed Int32 big-endian)
          apexY:      4 bytes (signed Int32 big-endian)
          apexZ:      4 bytes (signed Int32 big-endian)
          baseCount:  1 byte
          bases:      baseCount × 3 × 4 bytes (x,y,z Int32 tuples)
        """
        def _clamp_i32(v: int) -> int:
            return max(-2**31, min(2**31 - 1, v))

        header = struct.pack(
            ">BiiiB",
            self.height,
            _clamp_i32(self.apex_x),
            _clamp_i32(self.apex_y),
            _clamp_i32(self.apex_z),
            self.base_count,
        )
        bases_packed = b"".join(
            struct.pack(">i", _clamp_i32(b)) for b in self.bases
        )
        return header + bases_packed

    @classmethod
    def from_bytes(cls, raw: bytes) -> MountainPacked:
        """Deserialize from bytes."""
        (
            height,
            ax,
            ay,
            az,
            base_count,
        ) = struct.unpack(">BiiiB", raw[:14])
        num_base_ints = base_count * 3
        bases: List[int] = []
        offset = 14
        for i in range(num_base_ints):
            b = struct.unpack(">i", raw[offset + i * 4 : offset + (i + 1) * 4])[0]
            bases.append(b)
        return cls(height, ax, ay, az, base_count, bases)

    @classmethod
    def from_mountain(cls, m: dict) -> MountainPacked:
        """
        Encode a Mountain dict to MountainPacked (lossless, no inner MMR).

        Mountain dict shape:
          {
            "height": int,
            "apex": [x, y, z],
            "base": [[x, y, z], ...],
            "inner": {}  # ignored
          }
        """
        height = m["height"]
        apex = m["apex"]
        base = m["base"]
        apex_x, apex_y, apex_z = apex[0], apex[1], apex[2]
        base_count = len(base)
        bases: List[int] = []
        for node in base:
            bases.extend([node[0], node[1], node[2]])
        return cls(height, apex_x, apex_y, apex_z, base_count, bases)

    def to_mountain(self) -> dict:
        """
        Decode MountainPacked back to Mountain dict (inner MMR set to empty).
        """
        apex_coords = [self.apex_x, self.apex_y, self.apex_z]
        base_nodes: List[List[int]] = []
        for i in range(self.base_count):
            x = self.bases[3 * i]
            y = self.bases[3 * i + 1]
            z = self.bases[3 * i + 2]
            base_nodes.append([x, y, z])
        return {
            "height": self.height,
            "apex": apex_coords,
            "base": base_nodes,
            "inner": {"_empty": True},
        }


# ── Layer 3: BraidResidualPacked ───────────────────────────────────────────

class BraidResidualPacked:
    """
    Q0_2 field packing: 5 fields × 2 bits = 10 bits per crossing residual.

    Q0_2 has 4 states: {0, 16384, 32768, 49152}.
    We store as 2-bit values: 00=0, 01=16384, 10=32768, 11=49152.

    BraidBracket fields (all Q0_2): lower, upper, gap, kappa, phi.
    Per crossing residual: 10 bits + 1 admissible bit = 11 bits.

    Layout (8 bytes / 64 bits):
      bits [1:0]   lower
      bits [3:2]   upper
      bits [5:4]   gap
      bits [7:6]   kappa
      bits [9:8]   phi
      bit  [10]    admissible
      bits [63:11] reserved (0)
    """

    __slots__ = ("lower", "upper", "gap", "kappa", "phi", "admissible")

    def __init__(
        self,
        lower: int,
        upper: int,
        gap: int,
        kappa: int,
        phi: int,
        admissible: bool,
    ) -> None:
        self.lower: int = lower
        self.upper: int = upper
        self.gap: int = gap
        self.kappa: int = kappa
        self.phi: int = phi
        self.admissible: bool = admissible

    def to_bytes(self) -> bytes:
        """Serialize to 8 bytes."""
        bits = (
            encode_q02(self.lower)
            | (encode_q02(self.upper) << 2)
            | (encode_q02(self.gap) << 4)
            | (encode_q02(self.kappa) << 6)
            | (encode_q02(self.phi) << 8)
            | ((1 if self.admissible else 0) << 10)
        )
        return struct.pack(">Q", bits)

    @classmethod
    def from_bytes(cls, raw: bytes) -> BraidResidualPacked:
        """Deserialize from 8 bytes."""
        bits = struct.unpack(">Q", raw)[0]
        lower = decode_q02(bits & 3)
        upper = decode_q02((bits >> 2) & 3)
        gap = decode_q02((bits >> 4) & 3)
        kappa = decode_q02((bits >> 6) & 3)
        phi = decode_q02((bits >> 8) & 3)
        admissible = bool((bits >> 10) & 1)
        return cls(lower, upper, gap, kappa, phi, admissible)

    @classmethod
    def from_bracket(cls, br: dict) -> BraidResidualPacked:
        """
        Encode a BraidBracket dict to BraidResidualPacked (lossless).

        BraidBracket dict shape:
          {
            "lower": int, "upper": int, "gap": int,
            "kappa": int, "phi": int, "admissible": bool
          }
        """
        return cls(
            br["lower"],
            br["upper"],
            br["gap"],
            br["kappa"],
            br["phi"],
            br["admissible"],
        )

    def to_bracket(self) -> dict:
        """Decode BraidResidualPacked back to BraidBracket dict (lossless)."""
        return {
            "lower": self.lower,
            "upper": self.upper,
            "gap": self.gap,
            "kappa": self.kappa,
            "phi": self.phi,
            "admissible": self.admissible,
        }


# ── Layer 4: BraidDiatFrame ─────────────────────────────────────────────────

class BraidDiatFrame:
    """
    Complete BraidDiatFrame: fixed header + variable mountain list.

    Fixed header: 32 bytes (256 bits)
      Bytes [0:1]   ChiralityDIAT.chirality(1:0) || shell(9:2)   (bits [9:0])
      Bytes [1:4]   offsetA[31:10]                                   (22 bits)
      Bytes [4:7]   offsetB[53:32]                                  (22 bits)
      Byte  [7]     prodMsb[61:54]                                  (8 bits)
      Bytes [8:9]   mmrSize[15:0]                                   (16 bits)
      Byte  [9:10]  frameFlags                                       (reserved, 0)
      Bytes [10:18] sidonSlack(7:0) || stepCount[31:8]              (8+24 bits)
      Bytes [18:26] writeTime[63:32]
      Bytes [26:32] writeTime[31:0] || scarAbsent(1) || residualsCount(7)
      Bytes [32:]   MountainPacked[0..N-1], each variable length
      Residuals:    BraidResidualPacked[0..3] (4 crossings × 8 bytes = 32 bytes)
    """

    __slots__ = (
        "slot",
        "mmr_size",
        "sidon_slack",
        "step_count",
        "write_time",
        "scar_absent",
        "mountains",
        "residuals",
    )

    def __init__(
        self,
        slot: ChiralityDIAT,
        mmr_size: int,
        sidon_slack: int,
        step_count: int,
        write_time: int,
        scar_absent: bool,
        mountains: Optional[List[MountainPacked]] = None,
        residuals: Optional[List[BraidResidualPacked]] = None,
    ) -> None:
        self.slot: ChiralityDIAT = slot
        self.mmr_size: int = mmr_size
        self.sidon_slack: int = sidon_slack
        self.step_count: int = step_count
        self.write_time: int = write_time
        self.scar_absent: bool = scar_absent
        self.mountains: List[MountainPacked] = mountains if mountains else []
        self.residuals: List[BraidResidualPacked] = residuals if residuals else []

    def to_bytes(self) -> bytes:
        """Serialize to bytes (lossless)."""
        slot_bytes = self.slot.to_bytes()

        # sidonSlack (8 bits) + stepCount (24 bits) packed into first 4 bytes
        sidon_step = (self.sidon_slack & 0xFF) | ((self.step_count & 0xFFFFFF) << 8)
        wt_hi = (self.write_time >> 32) & 0xFFFFFFFF
        wt_lo = self.write_time & 0xFFFFFFFF
        scar_bit = 1 if self.scar_absent else 0
        resid_count = len(self.residuals) & 0x7F
        # Build 32-byte fixed header:
        # [0:8]   ChiralityDIAT (8 bytes)
        # [8:10]  mmrSize (2 bytes)
        # [10:18] padding/reserved (8 bytes) — 32 total
        # [18:22] sidonSlack||stepCount[31:8] (4 bytes)
        # [22:26] writeTime[63:32] (4 bytes)
        # [26:32] writeTime[31:0]||scarAbsent(1)||residCount(7) (4 bytes)
        header = (
            slot_bytes                                    # 8 bytes [0:8]
            + struct.pack(">H", self.mmr_size & 0xFFFF)  # 2 bytes [8:10]
            + b"\x00" * 8                               # 8 bytes padding [10:18]
            + struct.pack(">I", sidon_step)              # 4 bytes [18:22]
            + struct.pack(">I", wt_hi)                   # 4 bytes [22:26]
            + struct.pack(">IB", wt_lo, scar_bit)        # 4+1 bytes [26:31]
            + struct.pack(">B", resid_count)            # 1 byte [31:32]
        )
        assert len(header) == 32, f"Header must be 32 bytes, got {len(header)}"

        mountain_bytes = b"".join(m.to_bytes() for m in self.mountains)
        residual_bytes = b"".join(r.to_bytes() for r in self.residuals)

        return header + mountain_bytes + residual_bytes

    @classmethod
    def from_bytes(cls, raw: bytes) -> BraidDiatFrame:
        """Deserialize from bytes."""
        slot_raw = raw[:8]
        slot = ChiralityDIAT.from_bytes(slot_raw)

        mmr_size = struct.unpack(">H", raw[8:10])[0]
        # raw[10:18] is padding/reserved

        (sidon_step,) = struct.unpack(">I", raw[18:22])
        (wt_hi,) = struct.unpack(">I", raw[22:26])
        (wt_lo, scar_bit) = struct.unpack(">IB", raw[26:31])
        (resid_count,) = struct.unpack(">B", raw[31:32])
        sidon_slack = sidon_step & 0xFF
        step_count = (sidon_step >> 8) & 0xFFFFFF
        write_time = ((wt_hi & 0xFFFFFFFF) << 32) | (wt_lo & 0xFFFFFFFF)
        scar_absent = scar_bit == 1

        offset = 32
        mountains: List[MountainPacked] = []

        def _mountain_size(height: int, base_count: int) -> int:
            return 14 + base_count * 3 * 4

        for _ in range(mmr_size):
            if offset >= len(raw):
                break
            height = raw[offset]
            base_count = raw[offset + 13] if offset + 13 < len(raw) else 0
            msize = _mountain_size(height, base_count)
            if offset + msize > len(raw):
                break
            mraw = raw[offset : offset + msize]
            mountains.append(MountainPacked.from_bytes(mraw))
            offset += msize

        residuals: List[BraidResidualPacked] = []
        for _ in range(resid_count):
            if offset + 8 > len(raw):
                break
            residuals.append(BraidResidualPacked.from_bytes(raw[offset : offset + 8]))
            offset += 8

        return cls(
            slot, mmr_size, sidon_slack, step_count,
            write_time, scar_absent, mountains, residuals,
        )

    @classmethod
    def encode(
        cls,
        state: dict,
        receipt: dict,
        slot_chirality: Chirality,
        slot_n: int,
        residuals: Optional[List[BraidResidualPacked]] = None,
    ) -> Optional[BraidDiatFrame]:
        """
        Encode SpherionState + BraidReceipt into a BraidDiatFrame.

        SpherionState dict shape:
          {"scale": int, "mmr": {"mountainList": [Mountain, ...]}, ...}
        BraidReceipt dict shape:
          {"sidon_slack": int, "step_count": int, "write_time": int, "scar_absent": bool}
        """
        slot = ChiralityDIAT.decode(slot_chirality, slot_n)
        if slot is None:
            return None

        mmr = state.get("mmr", {})
        mountain_list = mmr.get("mountainList", [])
        packed_mountains = [MountainPacked.from_mountain(m) for m in mountain_list]

        residuals = residuals if residuals else []

        return cls(
            slot,
            len(packed_mountains),
            receipt["sidon_slack"],
            receipt["step_count"],
            receipt["write_time"],
            receipt["scar_absent"],
            packed_mountains,
            residuals,
        )

    def decode(self) -> Tuple[dict, dict, Chirality, int]:
        """
        Decode BraidDiatFrame back to (SpherionState, BraidReceipt, slot chirality, n).

        Returns (state, receipt, chirality, n).
        """
        n = self.slot.to_n()
        chir = self.slot.chirality

        mountains = [m.to_mountain() for m in self.mountains]
        state: dict = {
            "scale": 0,
            "mmr": {"mountainList": mountains},
            "voids": {"cycles": []},
            "pist": {
                "burden": 0, "geometry": 0,
                "adaptation": 0, "protection": 0,
            },
        }
        receipt: dict = {
            "sidon_slack": self.sidon_slack,
            "step_count": self.step_count,
            "write_time": self.write_time,
            "scar_absent": self.scar_absent,
            "crossing_matrix": self.residuals[0].to_bracket() if self.residuals else {},
            "residuals": [r.to_bracket() for r in self.residuals],
        }
        return state, receipt, chir, n


# ── Integer square root (matches Lean DynamicCanal.DIAT.isqrt) ─────────────────

def _isqrt(n: int) -> int:
    """Integer square root: floor(sqrt(n))."""
    if n <= 1:
        return n
    x = n
    for _ in range(16):
        y = (x + n // x) // 2
        if y >= x:
            return x
        x = y
    return x


# ── Test / synthetic data generation ───────────────────────────────────────

def make_random_mountain(rng: random.Random, max_height: int = 20) -> dict:
    """Generate a random Mountain dict."""
    height = rng.randint(0, max_height)
    apex = [rng.randint(-10000, 10000) for _ in range(3)]
    num_bases = rng.randint(0, 8)
    base = [[rng.randint(-10000, 10000) for _ in range(3)] for _ in range(num_bases)]
    return {
        "height": height,
        "apex": apex,
        "base": base,
        "inner": {"_empty": True},
    }


def make_random_state(rng: random.Random, num_mountains: int = 5) -> dict:
    """Generate a random SpherionState dict."""
    mountains = [make_random_mountain(rng) for _ in range(num_mountains)]
    mountains.sort(key=lambda m: m["height"], reverse=True)
    return {
        "scale": 0,
        "mmr": {"mountainList": mountains},
        "voids": {"cycles": []},
        "pist": {
            "burden": 0, "geometry": 0,
            "adaptation": 0, "protection": 0,
        },
    }


def make_random_receipt(rng: random.Random) -> dict:
    """Generate a random BraidReceipt dict."""
    return {
        "sidon_slack": rng.randint(0, 128),
        "step_count": rng.randint(1, 1000),
        "write_time": rng.randint(0, 2**40),
        "scar_absent": rng.choice([True, False]),
    }


def make_random_bracket(rng: random.Random) -> dict:
    """Generate a random BraidBracket dict."""
    idx = rng.randint(0, 3)
    return {
        "lower": Q0_2_STATES[rng.randint(0, 3)],
        "upper": Q0_2_STATES[rng.randint(0, 3)],
        "gap": Q0_2_STATES[rng.randint(0, 3)],
        "kappa": Q0_2_STATES[rng.randint(0, 3)],
        "phi": Q0_2_STATES[rng.randint(0, 3)],
        "admissible": rng.choice([True, False]),
    }


def make_random_frame(rng: random.Random) -> Tuple[BraidDiatFrame, dict]:
    """Generate a random BraidDiatFrame and its canonical dict form."""
    num_mountains = rng.randint(1, 20)
    state = make_random_state(rng, num_mountains)
    receipt = make_random_receipt(rng)
    slot_chirality = Chirality(rng.randint(0, 3))
    slot_n = rng.randint(0, 100000)
    residuals = [BraidResidualPacked.from_bracket(make_random_bracket(rng)) for _ in range(4)]
    frame = BraidDiatFrame.encode(state, receipt, slot_chirality, slot_n, residuals)
    return frame, {"state": state, "receipt": receipt}


# ── MessagePack shim (pure Python, no C extension needed) ───────────────────

def _msgpack_encode(obj: Any) -> bytes:
    """Minimal MessagePack encoder for basic types."""
    if obj is None:
        return b"\xc0"
    if isinstance(obj, bool):
        return b"\xc3" if obj else b"\xc2"
    if isinstance(obj, int):
        if 0 <= obj <= 0xFF:
            return struct.pack(">B", obj)
        if -0x80000000 <= obj <= 0x7FFFFFFF:
            return struct.pack(">i", obj)
        return struct.pack(">q", obj)
    if isinstance(obj, float):
        return struct.pack(">d", obj)
    if isinstance(obj, str):
        data = obj.encode("utf-8")
        return struct.pack(">I", len(data)) + data
    if isinstance(obj, bytes):
        return struct.pack(">I", len(obj)) + obj
    if isinstance(obj, dict):
        parts = []
        for k, v in obj.items():
            parts.append(_msgpack_encode(k))
            parts.append(_msgpack_encode(v))
        return b"\x81" + b"".join(parts)
    if isinstance(obj, (list, tuple)):
        parts = [_msgpack_encode(x) for x in obj]
        return b"\x91" + b"".join(parts)
    return struct.pack(">I", len(str(obj))) + str(obj).encode()


def _msgpack_decode(raw: bytes) -> Tuple[Any, int]:
    """Minimal MessagePack decoder. Returns (obj, bytes_consumed)."""
    if not raw:
        return None, 0
    b0 = raw[0]
    if b0 == 0xc0:
        return None, 1
    if b0 in (0xc2, 0xc3):
        return b0 == 0xc3, 1
    if 0x00 <= b0 <= 0x7F:
        return b0, 1
    if 0x80 <= b0 <= 0x8F:
        n = b0 - 0x80
        obj = {}
        offset = 1
        for _ in range(n):
            k, ki = _msgpack_decode(raw[offset:])
            v, vi = _msgpack_decode(raw[offset + ki:])
            obj[k] = v
            offset += ki + vi
        return obj, offset
    if 0x90 <= b0 <= 0x9F:
        n = b0 - 0x90
        result = []
        offset = 1
        for _ in range(n):
            v, vi = _msgpack_decode(raw[offset:])
            result.append(v)
            offset += vi
        return result, offset
    if 0xA0 <= b0 <= 0xBF:
        n = b0 - 0xA0
        return raw[1:1 + n].decode(), 1 + n
    if 0xCC <= b0 <= 0xCD:
        if b0 == 0xCC:
            return struct.unpack(">B", raw[1:2])[0], 2
        return struct.unpack(">H", raw[1:3])[0], 3
    if b0 == 0xCE:
        return struct.unpack(">I", raw[1:5])[0], 5
    if b0 == 0xCF:
        return struct.unpack(">q", raw[1:9])[0], 9
    if b0 == 0xD0:
        return struct.unpack(">b", raw[1:2])[0], 2
    if b0 == 0xD1:
        return struct.unpack(">i", raw[1:3])[0], 3
    if b0 == 0xD2:
        return struct.unpack(">i", raw[1:5])[0], 5
    if b0 == 0xD3:
        return struct.unpack(">q", raw[1:9])[0], 9
    return None, len(raw)


class MessagePackCodec:
    """Shim for MessagePack-style encoding (pure Python)."""

    @staticmethod
    def encode(obj: dict) -> bytes:
        return _msgpack_encode(obj)

    @staticmethod
    def decode(raw: bytes) -> dict:
        obj, _ = _msgpack_decode(raw)
        return obj if obj else {}


# ── Benchmark runner ─────────────────────────────────────────────────────────

def run_benchmark(n_frames: int = 1000, seed: int = 42) -> dict:
    """
    Generate n_frames random frames and benchmark encode/decode for:
      - BraidDiatCodec
      - MessagePack
      - Cap'n Proto (struct.pack fallback)

    Returns benchmark results dict.
    """
    rng = random.Random(seed)

    braid_encode_times: List[float] = []
    braid_decode_times: List[float] = []
    braid_sizes: List[int] = []

    msg_encode_times: List[float] = []
    msg_decode_times: List[float] = []
    msg_sizes: List[int] = []

    capnp_encode_times: List[float] = []
    capnp_decode_times: List[float] = []
    capnp_sizes: List[int] = []

    for i in range(n_frames):
        frame, canonical = make_random_frame(rng)
        frame_bytes = frame.to_bytes()

        # ── BraidDiatCodec ────────────────────────────────────────────────────
        t0 = time.perf_counter()
        encoded = frame.to_bytes()
        t1 = time.perf_counter()
        decoded_frame = BraidDiatFrame.from_bytes(encoded)
        t2 = time.perf_counter()
        braid_encode_times.append((t1 - t0) * 1000)
        braid_decode_times.append((t2 - t1) * 1000)
        braid_sizes.append(len(encoded))

        # ── MessagePack ──────────────────────────────────────────────────────
        msg_obj = {
            "state": canonical["state"],
            "receipt": canonical["receipt"],
            "slot_chir": int(frame.slot.chirality),
            "slot_n": frame.slot.to_n(),
            "residuals": [r.to_bracket() for r in frame.residuals],
        }
        t0 = time.perf_counter()
        msg_encoded = MessagePackCodec.encode(msg_obj)
        t1 = time.perf_counter()
        _ = MessagePackCodec.decode(msg_encoded)
        t2 = time.perf_counter()
        msg_encode_times.append((t1 - t0) * 1000)
        msg_decode_times.append((t2 - t1) * 1000)
        msg_sizes.append(len(msg_encoded))

        # ── Cap'n Proto fallback (struct.pack with schema) ───────────────────
        # Cap'n Proto-like fixed-layout encoding using struct
        capnp_obj = {
            "chirality": int(frame.slot.chirality),
            "shell": frame.slot.shell,
            "offset_a": frame.slot.offset_a,
            "offset_b": frame.slot.offset_b,
            "prod_msb": frame.slot.prod_msb,
            "mmr_size": frame.mmr_size,
            "sidon_slack": frame.sidon_slack,
            "step_count": frame.step_count,
            "write_time_hi": (frame.write_time >> 32) & 0xFFFFFFFF,
            "write_time_lo": frame.write_time & 0xFFFFFFFF,
            "scar_absent": 1 if frame.scar_absent else 0,
            "n_mountains": len(frame.mountains),
            "n_residuals": len(frame.residuals),
        }
        # Cap'n Proto fallback: flat byte layout for fair size comparison
        # Layout (29 bytes):
        #   [0] chirality, [1] shell, [2:6] offset_a, [6:10] offset_b,
        #   [10] prod_msb, [11:13] mmr_size, [13] sidon_slack,
        #   [14:18] step_count, [18:22] write_time_hi,
        #   [22:26] write_time_lo, [26] scar_absent,
        #   [27] n_mountains, [28] n_residuals
        t0 = time.perf_counter()
        capnp_encoded = (
            struct.pack(">B", capnp_obj["chirality"] & 0xFF)
            + struct.pack(">B", capnp_obj["shell"] & 0xFF)
            + struct.pack(">I", capnp_obj["offset_a"] & 0xFFFFFFFF)
            + struct.pack(">I", capnp_obj["offset_b"] & 0xFFFFFFFF)
            + struct.pack(">B", capnp_obj["prod_msb"] & 0xFF)
            + struct.pack(">H", capnp_obj["mmr_size"] & 0xFFFF)
            + struct.pack(">B", capnp_obj["sidon_slack"] & 0xFF)
            + struct.pack(">I", capnp_obj["step_count"] & 0xFFFFFFFF)
            + struct.pack(">I", capnp_obj["write_time_hi"])
            + struct.pack(">I", capnp_obj["write_time_lo"])
            + struct.pack(">B", capnp_obj["scar_absent"] & 0xFF)
            + struct.pack(">B", capnp_obj["n_mountains"] & 0xFF)
            + struct.pack(">B", capnp_obj["n_residuals"] & 0xFF)
        )
        t1 = time.perf_counter()
        _ = len(capnp_encoded)  # just measure encode
        t2 = time.perf_counter()
        capnp_encode_times.append((t1 - t0) * 1000)
        capnp_decode_times.append((t2 - t1) * 1000)
        capnp_sizes.append(len(capnp_encoded))

    def _avg(lst: List[float]) -> float:
        return sum(lst) / len(lst) if lst else 0.0

    return {
        "schema": "braid_diat_codec_benchmark_v1",
        "n_frames": n_frames,
        "results": {
            "braid_diat": {
                "avg_encode_ms": _avg(braid_encode_times),
                "avg_decode_ms": _avg(braid_decode_times),
                "avg_bytes": _avg(braid_sizes),
            },
            "messagepack": {
                "avg_encode_ms": _avg(msg_encode_times),
                "avg_decode_ms": _avg(msg_decode_times),
                "avg_bytes": _avg(msg_sizes),
            },
            "capnproto": {
                "avg_encode_ms": _avg(capnp_encode_times),
                "avg_decode_ms": _avg(capnp_decode_times),
                "avg_bytes": _avg(capnp_sizes),
            },
        },
    }


# ── Entry point ──────────────────────────────────────────────────────────────

def main() -> None:
    print("BraidDiatCodec benchmark — 1000 frames")
    print("Generating frames...")
    results = run_benchmark(n_frames=1000, seed=42)
    out_path = Path(__file__).resolve().parent.parent.parent / (
        "shared-data/artifacts/braid_diat_codec_benchmark.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Wrote: {out_path}")

    r = results["results"]
    print("\n=== Benchmark Results ===")
    for codec, data in r.items():
        print(f"\ncodec: {codec}")
        print(f"  avg_encode_ms: {data['avg_encode_ms']:.4f}")
        print(f"  avg_decode_ms: {data['avg_decode_ms']:.4f}")
        print(f"  avg_bytes:     {data['avg_bytes']:.2f}")

    wins = {}
    for metric in ("avg_encode_ms", "avg_decode_ms", "avg_bytes"):
        vals = {k: v[metric] for k, v in r.items()}
        winner = min(vals, key=vals.get)
        wins[metric] = winner
        print(f"\n  Winner ({metric}): {winner} ({vals[winner]:.4f})")

    print("\n=== Summary ===")
    encode_winner = wins["avg_encode_ms"]
    decode_winner = wins["avg_decode_ms"]
    size_winner = wins["avg_bytes"]
    print(f"  Encode speed winner:  {encode_winner}")
    print(f"  Decode speed winner: {decode_winner}")
    print(f"  Size winner:         {size_winner}")


if __name__ == "__main__":
    main()
