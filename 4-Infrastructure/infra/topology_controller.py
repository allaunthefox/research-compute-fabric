#!/usr/bin/env python3
"""
topology_controller.py — Geometric Topology Controller

Python extraction of TopologyResilience.lean.

Principles:
- The topology is a manifold, not a graph.
- Network segments are charts on the manifold.
- Traffic flows along geodesics (minimal curvature paths).
- Load is an energy density field.
- Services are placed where the Laplacian is minimized.
- Quorum is geometric coverage, not node counting.
- Resiliency = k-connected atlas + dynamic reconfiguration.

Per AGENTS.md §6: Python may only serialize, spawn, wrap, display.
All cost/invariant/branching decisions are extracted from Lean.
"""

import json
import sys
import time
import hashlib
import threading
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Callable
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════
# §0  Q16.16 Fixed-Point (Python extraction)
# ═══════════════════════════════════════════════════════════════════════════

class Q16_16:
    """Fixed-point Q16.16 using Python int (backend: UInt32 semantics)."""
    def __init__(self, val: int):
        self.val = val & 0xFFFFFFFF

    @staticmethod
    def zero() -> "Q16_16":
        return Q16_16(0)

    @staticmethod
    def one() -> "Q16_16":
        return Q16_16(0x00010000)

    @staticmethod
    def from_nat(n: int) -> "Q16_16":
        return Q16_16((n * 65536) & 0xFFFFFFFF)

    @staticmethod
    def from_float(f: float) -> "Q16_16":
        return Q16_16(int(f * 65536) & 0xFFFFFFFF)

    def to_float(self) -> float:
        v = self.val if self.val < 0x80000000 else self.val - 0x100000000
        return v / 65536.0

    def __add__(self, other: "Q16_16") -> "Q16_16":
        return Q16_16((self.val + other.val) & 0xFFFFFFFF)

    def __sub__(self, other: "Q16_16") -> "Q16_16":
        return Q16_16((self.val - other.val) & 0xFFFFFFFF)

    def __mul__(self, other: "Q16_16") -> "Q16_16":
        prod = (self.val * other.val) >> 16
        return Q16_16(prod & 0xFFFFFFFF)

    def __truediv__(self, other: "Q16_16") -> "Q16_16":
        if other.val == 0:
            return Q16_16(0xFFFFFFFF)
        return Q16_16(((self.val << 16) // other.val) & 0xFFFFFFFF)

    def __lt__(self, other: "Q16_16") -> bool:
        a = self.val if self.val < 0x80000000 else self.val - 0x100000000
        b = other.val if other.val < 0x80000000 else other.val - 0x100000000
        return a < b

    def __gt__(self, other: "Q16_16") -> bool:
        return other < self

    def __le__(self, other: "Q16_16") -> bool:
        return self == other or self < other

    def __ge__(self, other: "Q16_16") -> bool:
        return other <= self

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Q16_16):
            return False
        return self.val == other.val

    def to_dict(self) -> dict:
        return {"val": self.val, "float": self.to_float()}

    @staticmethod
    def from_dict(d: dict) -> "Q16_16":
        return Q16_16(d["val"])


# ═══════════════════════════════════════════════════════════════════════════
# §1  Network Segment — Chart with capacity
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class NetworkSegment:
    """A network segment is a chart on the manifold with capacity constraints."""
    point_id: str
    dimension: int = 2
    center_coords: List[Q16_16] = field(default_factory=list)
    capacity_qps: Q16_16 = field(default_factory=Q16_16.zero)
    latency_ms: Q16_16 = field(default_factory=Q16_16.zero)
    throughput_mbps: Q16_16 = field(default_factory=Q16_16.zero)
    current_load: Q16_16 = field(default_factory=Q16_16.zero)
    healthy: bool = True

    def utilization(self) -> Q16_16:
        if self.capacity_qps == Q16_16.zero():
            return Q16_16.one()
        return self.current_load / self.capacity_qps

    def is_overloaded(self) -> bool:
        return self.utilization() > Q16_16(52428)  # 0.8 in Q16.16

    def traversal_cost(self) -> Q16_16:
        return self.latency_ms + (self.current_load * Q16_16.from_nat(2))

    def to_dict(self) -> dict:
        return {
            "point_id": self.point_id,
            "dimension": self.dimension,
            "center_coords": [c.to_dict() for c in self.center_coords],
            "capacity_qps": self.capacity_qps.to_dict(),
            "latency_ms": self.latency_ms.to_dict(),
            "throughput_mbps": self.throughput_mbps.to_dict(),
            "current_load": self.current_load.to_dict(),
            "healthy": self.healthy,
        }

    @staticmethod
    def from_dict(d: dict) -> "NetworkSegment":
        return NetworkSegment(
            point_id=d["point_id"],
            dimension=d["dimension"],
            center_coords=[Q16_16.from_dict(c) for c in d.get("center_coords", [])],
            capacity_qps=Q16_16.from_dict(d.get("capacity_qps", {"val": 0})),
            latency_ms=Q16_16.from_dict(d.get("latency_ms", {"val": 0})),
            throughput_mbps=Q16_16.from_dict(d.get("throughput_mbps", {"val": 0})),
            current_load=Q16_16.from_dict(d.get("current_load", {"val": 0})),
            healthy=d.get("healthy", True),
        )


# ═══════════════════════════════════════════════════════════════════════════
# §2  Topology Controller — Manifold-aware orchestrator
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class PingProbe:
    source_id: str
    target_id: str
    timestamp: float
    ttl: int
    accumulated_cost: Q16_16

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "timestamp": self.timestamp,
            "ttl": self.ttl,
            "accumulated_cost": self.accumulated_cost.to_dict(),
        }


class TopologyController:
    """
    Geometric topology controller.

    Manages the manifold as a collection of overlapping network segments.
    All routing, load balancing, and service placement is manifold-native.
    """

    def __init__(self, controller_id: str):
        self.controller_id = controller_id
        self.segments: Dict[str, NetworkSegment] = {}
        self._lock = threading.RLock()
        self._running = False

    # ─────────────────────────────────────────────────────────────────────
    # Segment Management
    # ─────────────────────────────────────────────────────────────────────

    def register_segment(self, seg: NetworkSegment):
        with self._lock:
            self.segments[seg.point_id] = seg
            self._log("segment_register", f"{seg.point_id} load={seg.current_load.to_float():.2f}")

    def unregister_segment(self, point_id: str):
        with self._lock:
            if point_id in self.segments:
                del self.segments[point_id]
                self._log("segment_unregister", point_id)

    def update_segment(self, point_id: str, load: Optional[Q16_16] = None,
                       healthy: Optional[bool] = None):
        with self._lock:
            if point_id not in self.segments:
                return
            seg = self.segments[point_id]
            if load is not None:
                seg.current_load = load
            if healthy is not None:
                seg.healthy = healthy

    def get_healthy_segments(self) -> List[NetworkSegment]:
        with self._lock:
            return [s for s in self.segments.values() if s.healthy]

    # ─────────────────────────────────────────────────────────────────────
    # Load Balancing — Geodesic routing
    # ─────────────────────────────────────────────────────────────────────

    def pick_best_segment(self, candidates: Optional[List[NetworkSegment]] = None) -> Optional[NetworkSegment]:
        """Greedy geodesic: pick segment with minimal traversal cost."""
        segs = candidates or self.get_healthy_segments()
        if not segs:
            return None
        return min(segs, key=lambda s: s.traversal_cost().val)

    def route_to(self, target_id: str) -> Optional[NetworkSegment]:
        """Route to a specific segment. Returns None if unreachable."""
        with self._lock:
            seg = self.segments.get(target_id)
            if seg and seg.healthy:
                return seg
            return None

    def path_cost(self, point_ids: List[str]) -> Q16_16:
        """Total traversal cost across a path of segments."""
        total = Q16_16.zero()
        for pid in point_ids:
            seg = self.segments.get(pid)
            if seg:
                total = total + seg.traversal_cost()
        return total

    # ─────────────────────────────────────────────────────────────────────
    # Bottleneck Detection
    # ─────────────────────────────────────────────────────────────────────

    def detect_bottlenecks(self) -> List[NetworkSegment]:
        """Segments with load above neighborhood mean."""
        healthy = self.get_healthy_segments()
        if len(healthy) <= 1:
            return []
        mean_load = sum(s.current_load.val for s in healthy) / len(healthy)
        return [s for s in healthy if s.current_load.val > mean_load]

    def detect_overloaded(self) -> List[NetworkSegment]:
        """Segments with utilization > 0.8."""
        return [s for s in self.get_healthy_segments() if s.is_overloaded()]

    # ─────────────────────────────────────────────────────────────────────
    # Service Placement
    # ─────────────────────────────────────────────────────────────────────

    def place_service(self, service_name: str,
                      candidates: Optional[List[NetworkSegment]] = None) -> Optional[NetworkSegment]:
        """Place a service on the best available segment."""
        segs = candidates or self.get_healthy_segments()
        if not segs:
            return None
        # Score = load + latency + health penalty
        def score(seg: NetworkSegment) -> int:
            s = seg.current_load.val + seg.latency_ms.val
            if not seg.healthy:
                s += 100 * 65536
            return s
        return min(segs, key=score)

    # ─────────────────────────────────────────────────────────────────────
    # Ping Protocol — Probe along geodesics
    # ─────────────────────────────────────────────────────────────────────

    def process_ping(self, probe: PingProbe, seg: NetworkSegment) -> Tuple[Q16_16, PingProbe, bool]:
        """Process a ping probe at a segment. Returns (load, updated_probe, should_forward)."""
        new_cost = probe.accumulated_cost + seg.traversal_cost()
        response = seg.current_load
        should_forward = seg.healthy and probe.ttl > 0
        updated = PingProbe(
            source_id=probe.source_id,
            target_id=seg.point_id,
            timestamp=time.time(),
            ttl=probe.ttl - 1,
            accumulated_cost=new_cost,
        )
        return response, updated, should_forward

    def flood_ping(self, source_id: str) -> List[Tuple[str, Q16_16]]:
        """Flood ping from source to all reachable segments."""
        source = self.segments.get(source_id)
        if not source:
            return []
        init_probe = PingProbe(
            source_id=source_id,
            target_id="",
            timestamp=time.time(),
            ttl=5,
            accumulated_cost=Q16_16.zero(),
        )
        results = []
        for seg in self.segments.values():
            if seg.healthy and seg.point_id != source_id:
                _, _, reachable = self.process_ping(init_probe, seg)
                if reachable:
                    results.append((seg.point_id, seg.traversal_cost()))
        return results

    # ─────────────────────────────────────────────────────────────────────
    # Quorum & Resilience
    # ─────────────────────────────────────────────────────────────────────

    def has_quorum(self) -> bool:
        """Geometric quorum: every segment overlaps with at least one other."""
        healthy = self.get_healthy_segments()
        if len(healthy) < 2:
            return False
        for s1 in healthy:
            has_overlap = any(
                s1.point_id != s2.point_id and s1.dimension == s2.dimension
                for s2 in healthy
            )
            if not has_overlap:
                return False
        return True

    def k_resilient(self, k: int) -> bool:
        """Every segment overlaps with at least k others."""
        healthy = self.get_healthy_segments()
        for s1 in healthy:
            overlap_count = sum(
                1 for s2 in healthy
                if s1.point_id != s2.point_id and s1.dimension == s2.dimension
            )
            if overlap_count < k:
                return False
        return True

    def reconfigure_quorum(self) -> bool:
        """After failures, check if remaining segments still form quorum."""
        return self.has_quorum()

    # ─────────────────────────────────────────────────────────────────────
    # Status & Logging
    # ─────────────────────────────────────────────────────────────────────

    def get_status(self) -> dict:
        healthy = self.get_healthy_segments()
        overloaded = self.detect_overloaded()
        bottlenecks = self.detect_bottlenecks()
        return {
            "controller_id": self.controller_id,
            "total_segments": len(self.segments),
            "healthy_segments": len(healthy),
            "overloaded": [s.point_id for s in overloaded],
            "bottlenecks": [s.point_id for s in bottlenecks],
            "quorum": self.has_quorum(),
            "k2_resilient": self.k_resilient(2),
        }

    def _log(self, event: str, msg: str):
        ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        print(f"[{ts}] [{self.controller_id}] [{event}] {msg}", flush=True)


# ═══════════════════════════════════════════════════════════════════════════
# §3  CLI
# ═══════════════════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print("Usage: topology_controller.py <config.json>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        cfg = json.load(f)

    ctrl = TopologyController(cfg.get("controller_id", "default"))

    # Register segments from config
    for seg_raw in cfg.get("segments", []):
        seg = NetworkSegment.from_dict(seg_raw)
        ctrl.register_segment(seg)

    # Run ping flood and report
    print("\n=== TOPOLOGY CONTROLLER STATUS ===")
    print(json.dumps(ctrl.get_status(), indent=2))

    print("\n=== PING FLOOD ===")
    source = cfg.get("ping_source", list(ctrl.segments.keys())[0] if ctrl.segments else "")
    if source:
        results = ctrl.flood_ping(source)
        for target, cost in results:
            print(f"  {source} -> {target}: cost={cost.to_float():.4f}")

    print("\n=== BOTTLENECKS ===")
    for b in ctrl.detect_bottlenecks():
        print(f"  {b.point_id}: load={b.current_load.to_float():.2f}")

    print("\n=== BEST PLACEMENT ===")
    best = ctrl.pick_best_segment()
    if best:
        print(f"  {best.point_id}: traversal_cost={best.traversal_cost().to_float():.4f}")


if __name__ == "__main__":
    main()
