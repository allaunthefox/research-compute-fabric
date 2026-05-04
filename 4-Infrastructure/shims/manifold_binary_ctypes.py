#!/usr/bin/env python3
"""
Manifold Binary Serialization — Python ctypes bindings
Loads C structs directly from binary blobs without parsing.

Usage:
    from manifold_binary_ctypes import ManifoldSerializer, ManifoldHeader
    ser = ManifoldSerializer("/path/to/manifold.bin")
    print(f"Shells: {ser.header.num_shells}, Points: {ser.header.num_points}")
    ser.validate_quaternions()
    ser.apply_sieve(threshold=0.3)
    ser.compute_famm()
"""

import ctypes
import struct
from pathlib import Path
from typing import Optional, List, Tuple
import numpy as np


# ═══════════════════════════════════════════════════════════════════════════
# C struct mirrors (must match manifold_binary.h exactly)
# ═══════════════════════════════════════════════════════════════════════════

class ManifoldHeader(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("magic", ctypes.c_uint32),         # 0x4D414E49
        ("version", ctypes.c_uint16),       # 1
        ("flags", ctypes.c_uint16),         # bitmask
        ("timestamp_ns", ctypes.c_uint64),
        ("num_shells", ctypes.c_uint32),
        ("num_points", ctypes.c_uint32),
        ("num_edges", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32),
    ]

    @property
    def has_famm(self) -> bool:
        return bool(self.flags & 0x4)


class Q16_16(ctypes.c_int32):
    """Fixed-point Q16.16: 1.0 = 65536"""
    SCALE = 1 << 16

    @classmethod
    def from_float(cls, f: float) -> int:
        return int(f * cls.SCALE)

    @classmethod
    def to_float(cls, v: int) -> float:
        return v / cls.SCALE


class QuaternionPoint(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("w", ctypes.c_int32),
        ("x", ctypes.c_int32),
        ("y", ctypes.c_int32),
        ("z", ctypes.c_int32),
        ("layer", ctypes.c_uint32),
        ("flags", ctypes.c_uint32),
    ]

    def to_numpy(self) -> np.ndarray:
        return np.array([
            Q16_16.to_float(self.w),
            Q16_16.to_float(self.x),
            Q16_16.to_float(self.y),
            Q16_16.to_float(self.z),
        ], dtype=np.float32)

    @property
    def is_alive(self) -> bool:
        return bool(self.flags & 1)

    @property
    def is_pruned(self) -> bool:
        return bool(self.flags & 2)


class PistShell(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("k", ctypes.c_int32),
        ("t", ctypes.c_int32),
        ("mass", ctypes.c_int32),
        ("a", ctypes.c_int32),
        ("b", ctypes.c_int32),
        ("shell_id", ctypes.c_uint32),
        ("phase", ctypes.c_int32),
    ]

    @property
    def phase_float(self) -> float:
        return Q16_16.to_float(self.phase)


class BraidEdge(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("from_idx", ctypes.c_uint32),
        ("to_idx", ctypes.c_uint32),
        ("weight", ctypes.c_int32),
        ("alignment", ctypes.c_int32),
        ("braid_id", ctypes.c_uint32),
    ]

    @property
    def weight_float(self) -> float:
        return Q16_16.to_float(self.weight)


class FammNode(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("torsional_stress", ctypes.c_int32),
        ("interlocking_energy", ctypes.c_int32),
        ("laplacian_energy", ctypes.c_int32),
        ("total_frustration", ctypes.c_int32),
        ("cognitive_load", ctypes.c_int32),
        ("decision", ctypes.c_uint8),
        ("topology", ctypes.c_uint8),
        ("reserved", ctypes.c_uint16),
    ]

    TOPOLOGY_NAMES = ["relational", "semantic", "topological", "minimal"]
    DECISION_NAMES = ["EXECUTE", "DEFER", "THROTTLE"]

    @property
    def frustration(self) -> float:
        return Q16_16.to_float(self.total_frustration)

    @property
    def topology_name(self) -> str:
        return self.TOPOLOGY_NAMES[self.topology] if self.topology < 4 else "unknown"

    @property
    def decision_name(self) -> str:
        return self.DECISION_NAMES[self.decision] if self.decision < 3 else "unknown"


# ═══════════════════════════════════════════════════════════════════════════
# Serializer: mmap-style zero-copy deserialization
# ═══════════════════════════════════════════════════════════════════════════

class ManifoldSerializer:
    MAGIC = 0x4D414E49
    VERSION = 1
    HEADER_SIZE = 32  # bytes

    def __init__(self, path: Optional[str] = None):
        self.header: Optional[ManifoldHeader] = None
        self.shells: ctypes.Array = None
        self.points: ctypes.Array = None
        self.edges: ctypes.Array = None
        self.famm_nodes: ctypes.Array = None
        self._buffer: Optional[bytes] = None

        if path:
            self.load(path)

    def load(self, path: str) -> None:
        """Load binary manifold from file (zero-copy via memoryview)."""
        data = Path(path).read_bytes()
        self._buffer = data
        self._parse(data)

    def _parse(self, data: bytes) -> None:
        if len(data) < self.HEADER_SIZE:
            raise ValueError("Buffer too small for header")

        # Parse header directly from bytes (no struct.unpack for the struct)
        self.header = ManifoldHeader.from_buffer_copy(data)

        if self.header.magic != self.MAGIC:
            raise ValueError(f"Bad magic: 0x{self.header.magic:08X} (expected 0x{self.MAGIC:08X})")
        if self.header.version != self.VERSION:
            raise ValueError(f"Bad version: {self.header.version}")

        offset = self.HEADER_SIZE

        # Shells
        if self.header.num_shells > 0:
            shell_size = ctypes.sizeof(PistShell)
            self.shells = (PistShell * self.header.num_shells).from_buffer_copy(
                data, offset
            )
            offset += shell_size * self.header.num_shells

        # Points
        if self.header.num_points > 0:
            point_size = ctypes.sizeof(QuaternionPoint)
            self.points = (QuaternionPoint * self.header.num_points).from_buffer_copy(
                data, offset
            )
            offset += point_size * self.header.num_points

        # Edges
        if self.header.num_edges > 0:
            edge_size = ctypes.sizeof(BraidEdge)
            self.edges = (BraidEdge * self.header.num_edges).from_buffer_copy(
                data, offset
            )
            offset += edge_size * self.header.num_edges

        # FAMM nodes
        if self.header.has_famm and self.header.num_points > 0:
            famm_size = ctypes.sizeof(FammNode)
            self.famm_nodes = (FammNode * self.header.num_points).from_buffer_copy(
                data, offset
            )
            offset += famm_size * self.header.num_points

    def save(self, path: str) -> int:
        """Serialize current state to binary file. Returns bytes written."""
        buf = self.to_bytes()
        Path(path).write_bytes(buf)
        return len(buf)

    def to_bytes(self) -> bytes:
        """Serialize to bytes buffer."""
        # Reconstruct contiguous buffer
        parts = [bytes(self.header)]
        if self.shells:
            parts.append(bytes(self.shells))
        if self.points:
            parts.append(bytes(self.points))
        if self.edges:
            parts.append(bytes(self.edges))
        if self.famm_nodes:
            parts.append(bytes(self.famm_nodes))
        return b"".join(parts)

    # ─────────────────────────────────────────────────────────────────
    # High-level operations
    # ─────────────────────────────────────────────────────────────────

    def validate_quaternions(self, tolerance: float = 0.01) -> int:
        """Verify all points lie on S³ (unit quaternion). Returns error count."""
        if not self.points:
            return 0
        errors = 0
        for p in self.points:
            w = Q16_16.to_float(p.w)
            x = Q16_16.to_float(p.x)
            y = Q16_16.to_float(p.y)
            z = Q16_16.to_float(p.z)
            norm = (w*w + x*x + y*y + z*z) ** 0.5
            if abs(norm - 1.0) > tolerance:
                errors += 1
        return errors

    def apply_sieve(self, threshold: float = 0.3) -> int:
        """Quaternion sieve: counter-rotation band-pass filter.
        Returns number of alive points."""
        if not self.points:
            return 0
        alive = 0
        for p in self.points:
            x = Q16_16.to_float(p.x)
            y = Q16_16.to_float(p.y)
            phase = np.arctan2(y, x)
            alignment = abs(np.sin(2.0 * phase))
            if alignment >= threshold:
                p.flags |= 1  # alive
                alive += 1
            else:
                p.flags &= ~1  # dead
        return alive

    def compute_famm(self) -> None:
        """Compute FAMM frustration and scheduling decisions in-place."""
        if not self.famm_nodes or not self.points:
            return
        for fn in self.famm_nodes:
            phi = (Q16_16.to_float(fn.torsional_stress)
                   + Q16_16.to_float(fn.interlocking_energy)
                   + Q16_16.to_float(fn.laplacian_energy))
            fn.total_frustration = Q16_16.from_float(phi)

            if phi < 0.25:
                fn.decision = 0
            elif phi < 0.5:
                fn.decision = 1
            else:
                fn.decision = 2

            load = Q16_16.to_float(fn.cognitive_load)
            if load < 0.25:
                fn.topology = 0
            elif load < 0.50:
                fn.topology = 1
            elif load < 0.75:
                fn.topology = 2
            else:
                fn.topology = 3

    def to_numpy_points(self) -> np.ndarray:
        """Return all quaternion points as Nx4 float32 array."""
        if not self.points:
            return np.zeros((0, 4), dtype=np.float32)
        arr = np.zeros((len(self.points), 4), dtype=np.float32)
        for i, p in enumerate(self.points):
            arr[i] = [Q16_16.to_float(p.w), Q16_16.to_float(p.x),
                      Q16_16.to_float(p.y), Q16_16.to_float(p.z)]
        return arr

    def to_numpy_edges(self) -> np.ndarray:
        """Return edges as Nx3 array [from, to, weight_float]."""
        if not self.edges:
            return np.zeros((0, 3), dtype=np.float32)
        arr = np.zeros((len(self.edges), 3), dtype=np.float32)
        for i, e in enumerate(self.edges):
            arr[i] = [e.from_idx, e.to_idx, Q16_16.to_float(e.weight)]
        return arr

    def __repr__(self) -> str:
        parts = [
            f"ManifoldSerializer(magic=0x{self.MAGIC:08X}",
            f"shells={self.header.num_shells if self.header else 0}",
            f"points={self.header.num_points if self.header else 0}",
            f"edges={self.header.num_edges if self.header else 0}",
            f"famm={self.header.has_famm if self.header else False})",
        ]
        return ", ".join(parts)


# ═══════════════════════════════════════════════════════════════════════════
# Builder: Construct manifold from Python data
# ═══════════════════════════════════════════════════════════════════════════

class ManifoldBuilder:
    """Build a ManifoldBlock from Python data, then serialize."""

    def __init__(self):
        self.header = ManifoldHeader()
        self.header.magic = ManifoldSerializer.MAGIC
        self.header.version = ManifoldSerializer.VERSION
        self.header.flags = 0x4  # has_famm
        self.header.timestamp_ns = 0  # caller sets
        self.shells: List[PistShell] = []
        self.points: List[QuaternionPoint] = []
        self.edges: List[BraidEdge] = []
        self.famm_nodes: List[FammNode] = []

    def add_shell(self, k: int, t: int, mass: int, a: int, b: int,
                  phase: float = 0.0) -> PistShell:
        s = PistShell(k=k, t=t, mass=mass, a=a, b=b,
                      shell_id=len(self.shells),
                      phase=Q16_16.from_float(phase))
        self.shells.append(s)
        return s

    def add_point(self, w: float, x: float, y: float, z: float,
                  layer: int = 0, normalize: bool = True) -> QuaternionPoint:
        if normalize:
            norm = (w*w + x*x + y*y + z*z) ** 0.5
            w, x, y, z = w/norm, x/norm, y/norm, z/norm
        p = QuaternionPoint(
            w=Q16_16.from_float(w), x=Q16_16.from_float(x),
            y=Q16_16.from_float(y), z=Q16_16.from_float(z),
            layer=layer, flags=0)
        self.points.append(p)
        return p

    def add_edge(self, from_idx: int, to_idx: int,
                 weight: float = 1.0, alignment: float = 0.0,
                 braid_id: int = 0) -> BraidEdge:
        e = BraidEdge(from_idx=from_idx, to_idx=to_idx,
                      weight=Q16_16.from_float(weight),
                      alignment=Q16_16.from_float(alignment),
                      braid_id=braid_id)
        self.edges.append(e)
        return e

    def add_famm_node(self, torsional_stress: float = 0.0,
                      interlocking_energy: float = 0.0,
                      laplacian_energy: float = 0.0,
                      cognitive_load: float = 0.0) -> FammNode:
        fn = FammNode(
            torsional_stress=Q16_16.from_float(torsional_stress),
            interlocking_energy=Q16_16.from_float(interlocking_energy),
            laplacian_energy=Q16_16.from_float(laplacian_energy),
            total_frustration=Q16_16.from_float(0.0),
            cognitive_load=Q16_16.from_float(cognitive_load),
            decision=0, topology=0, reserved=0)
        self.famm_nodes.append(fn)
        return fn

    def build(self) -> ManifoldSerializer:
        """Finalize and return a ManifoldSerializer ready for save()."""
        ser = ManifoldSerializer()
        self.header.num_shells = len(self.shells)
        self.header.num_points = len(self.points)
        self.header.num_edges = len(self.edges)

        ser.header = self.header
        if self.shells:
            ser.shells = (PistShell * len(self.shells))(*self.shells)
        if self.points:
            ser.points = (QuaternionPoint * len(self.points))(*self.points)
        if self.edges:
            ser.edges = (BraidEdge * len(self.edges))(*self.edges)
        if self.famm_nodes:
            ser.famm_nodes = (FammNode * len(self.famm_nodes))(*self.famm_nodes)
        return ser


# ═══════════════════════════════════════════════════════════════════════════
# Demo
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import time

    builder = ManifoldBuilder()
    builder.header.timestamp_ns = int(time.time_ns())

    # Generate PIST shells (32×16 grid)
    resolution = 32
    for k in range(resolution):
        for t in range(resolution // 2):
            mass = (k + 1) * (t + 1)
            a = int(mass ** 0.5) or 1
            b = mass // a
            theta = 2 * np.pi * k / resolution
            phi = np.pi * t / resolution
            builder.add_shell(k, t, mass, a, b, phase=theta)

            # Quaternion from spherical coordinates
            w = np.cos(theta/2) * np.cos(phi/2)
            x = np.sin(theta/2) * np.cos(phi/2)
            y = np.sin(theta/2) * np.sin(phi/2)
            z = np.cos(theta/2) * np.sin(phi/2)
            builder.add_point(w, x, y, z, layer=k)

            # Add FAMM node with synthetic stress
            builder.add_famm_node(
                torsional_stress=0.1 + 0.05 * np.sin(theta),
                interlocking_energy=0.05 + 0.02 * np.cos(phi),
                laplacian_energy=0.03,
                cognitive_load=0.2 + 0.1 * np.sin(theta * 2)
            )

    # Connect nearest neighbors as braid edges
    num_pts = len(builder.points)
    for i in range(num_pts - 1):
        builder.add_edge(i, i + 1, weight=0.8, braid_id=i % 4)

    ser = builder.build()
    print(ser)

    path = "/tmp/test_manifold.bin"
    nbytes = ser.save(path)
    print(f"Serialized {nbytes} bytes to {path}")

    # Roundtrip
    ser2 = ManifoldSerializer(path)
    print(f"Loaded: {ser2}")
    print(f"Validation errors: {ser2.validate_quaternions()}")
    alive = ser2.apply_sieve(threshold=0.3)
    print(f"Alive after sieve: {alive} / {ser2.header.num_points}")
    ser2.compute_famm()
    if ser2.famm_nodes:
        print(f"Sample FAMM: Φ={ser2.famm_nodes[0].frustration:.3f}, "
              f"decision={ser2.famm_nodes[0].decision_name}, "
              f"topology={ser2.famm_nodes[0].topology_name}")
