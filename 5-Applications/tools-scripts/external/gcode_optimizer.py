#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
gcode_optimizer.py — 14D canal-metric G-code path optimizer

Virtual extruder test harness. Runs multiple optimization strategies against
G-code input and reports canal metric + φ-coherence scores without hardware.

14D planning axes:
    Physical (5):   X, Y, Z, E (extrusion), F (feedrate)
    Planning (9):   η (viscosity), τ (thermal), A (acceleration),
                    overhang_angle, bridge_span, retraction_state,
                    layer_height, wall_proximity, ringing_risk

Strategies:
    baseline      — original G-code order
    canal         — nearest-neighbour by canal metric (greedy)
    phi_sorted    — sorted by φ-coherence bucket per layer
    thixotropic   — prefer previously-visited regions (lower η)
    random        — shuffled within layer (sanity check, expected worst)

Usage:
    python 5-Applications/scripts/gcode_optimizer.py --synthetic
    python 5-Applications/scripts/gcode_optimizer.py --input benchy.gcode
    python 5-Applications/scripts/gcode_optimizer.py --synthetic --strategies baseline,canal,phi
"""

from __future__ import annotations

import argparse
import math
import random
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── Constants ─────────────────────────────────────────────────────────────────

PHI = (1 + math.sqrt(5)) / 2          # 1.6180339887…
N_AXES = 18                         # Extended for Layer 7 (was 14)
_EPS = 1e-9


def clamp_unit(v: float) -> float:
    """Clamp value to [0, 1] range."""
    return max(0.0, min(1.0, v))

# Canal metric weighting — from HYPERFLUID_CANAL_MODEL.md
_LAMBDA_T = 0.15   # thixotropic decay rate (visit-count)
_LAMBDA_A = 0.30   # predictability (IoC) weight
_ETA_0    = 1.0    # base viscosity

# Physical axis indices
_AX_X, _AX_Y, _AX_Z, _AX_E, _AX_F = 0, 1, 2, 3, 4

# Planning axis indices (original 9)
_AX_ETA, _AX_TAU, _AX_ACC   = 5, 6, 7
_AX_OVH, _AX_BRG, _AX_RET   = 8, 9, 10
_AX_LYR, _AX_WLL, _AX_RNG   = 11, 12, 13

# Layer 7: Regime Drift / Structured Chaos extensions
_AX_CHI = 14                    # structured chaos ratio
_AX_PSI = 15                    # alignment state ψ (model adaptation)
_AX_PHI = 16                    # structural regime φ (target)
_AX_DELTA = 17                  # regime lag |φ - ψ|


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class GCodeMove:
    """One parsed G0/G1 command with current machine state after execution."""
    x: float
    y: float
    z: float
    e: float
    f: float
    is_travel: bool        # E == previous E (no extrusion)
    line_no: int
    raw: str


@dataclass
class Move14D:
    """GCodeMove expanded to 18D planning space (Layer 7 extended)."""
    move: GCodeMove
    vec: List[float] = field(default_factory=lambda: [0.0] * N_AXES)
    # Layer 7: Scroll/orientation state for path history
    scroll_id: int = 0
    twist_bit: int = 1          # +1 or -1 based on direction change
    bridge_candidate: bool = False  # True if this move is a potential bridge node


# ── G-code parser ─────────────────────────────────────────────────────────────

_G_RE = re.compile(
    r'G[01]\s*'
    r'(?:X(-?[\d.]+))?\s*'
    r'(?:Y(-?[\d.]+))?\s*'
    r'(?:Z(-?[\d.]+))?\s*'
    r'(?:E(-?[\d.]+))?\s*'
    r'(?:F(-?[\d.]+))?',
    re.IGNORECASE,
)


def parse_gcode(text: str) -> List[GCodeMove]:
    moves: List[GCodeMove] = []
    cx = cy = cz = ce = cf = 0.0
    prev_e = 0.0

    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith(';'):
            continue
        m = _G_RE.match(line)
        if not m:
            continue
        x_s, y_s, z_s, e_s, f_s = m.groups()
        if x_s is not None: cx = float(x_s)
        if y_s is not None: cy = float(y_s)
        if z_s is not None: cz = float(z_s)
        if e_s is not None: ce = float(e_s)
        if f_s is not None: cf = float(f_s)

        is_travel = (ce == prev_e)
        moves.append(GCodeMove(cx, cy, cz, ce, cf, is_travel, lineno, raw))
        prev_e = ce

    return moves


def emit_gcode(moves: List[GCodeMove]) -> str:
    """Re-emit G-code from a (possibly reordered) move list."""
    lines: List[str] = ["; gcode_optimizer output"]
    for mv in moves:
        lines.append(f"G1 X{mv.x:.3f} Y{mv.y:.3f} Z{mv.z:.3f} E{mv.e:.4f} F{mv.f:.0f}")
    return "\n".join(lines)


# ── 14D expander ──────────────────────────────────────────────────────────────

class Expander14D:
    """Convert a sequence of GCodeMoves to Move14D planning vectors."""

    def __init__(self, window: int = 8):
        self._window = window

    def expand(self, moves: List[GCodeMove]) -> List[Move14D]:
        out: List[Move14D] = []
        thermal_decay = []   # recent E-delta contributions
        f_history: List[float] = []
        z_layers: Dict[float, List[int]] = defaultdict(list)
        for i, mv in enumerate(moves):
            z_layers[round(mv.z, 3)].append(i)

        for i, mv in enumerate(moves):
            prev = moves[i - 1] if i > 0 else mv
            dx = mv.x - prev.x
            dy = mv.y - prev.y
            dz = mv.z - prev.z
            de = mv.e - prev.e
            df = mv.f - prev.f

            xy_len = math.hypot(dx, dy)
            xyz_len = math.sqrt(dx*dx + dy*dy + dz*dz) + _EPS

            # Axis 5: η — extrusion-pressure proxy (E-per-mm-travel)
            eta = abs(de) / (xy_len + _EPS) if xy_len > _EPS else 0.0

            # Axis 6: τ — thermal history (sum of recent |de| with exponential decay)
            thermal_decay = [v * 0.85 for v in thermal_decay[-self._window:]]
            thermal_decay.append(abs(de))
            tau = sum(thermal_decay)

            # Axis 7: A — acceleration proxy (|Δf| over window)
            f_history.append(mv.f)
            if len(f_history) > self._window:
                f_history.pop(0)
            accel = (max(f_history) - min(f_history)) / (max(f_history) + _EPS)

            # Axis 8: overhang_angle (0 = horizontal, 1 = vertical)
            overhang = abs(dz) / xyz_len

            # Axis 9: bridge_span — XY travel since last Z-layer move
            same_layer = z_layers.get(round(mv.z, 3), [])
            prev_same = max((j for j in same_layer if j < i), default=i)
            span_moves = i - prev_same
            bridge_span = min(1.0, span_moves / max(1, self._window))

            # Axis 10: retraction_state
            retraction = 1.0 if de < 0 else 0.0

            # Axis 11: layer_height
            layer_height = min(1.0, abs(dz) / 0.3)   # normalised to typical 0.3mm layer

            # Axis 12: wall_proximity (short XY moves with extrusion ≈ perimeter)
            wall_prox = 1.0 if (xy_len < 5.0 and de > 0) else 0.0

            # Axis 13: ringing_risk — variance of recent XY velocity
            recent_f = f_history[-4:] if len(f_history) >= 4 else f_history
            mean_f = sum(recent_f) / len(recent_f)
            ringing = math.sqrt(sum((v - mean_f)**2 for v in recent_f) / len(recent_f)) / (mean_f + _EPS)

            # Layer 7 Axes --------------------------------------------------
            # Axis 14: chi — structured chaos proxy
            # High when heat (traversal) dominates over congestion (A) and misalignment (τ)
            # Approximation: chi = eta_indicator * (1 - congestion_indicator)
            congestion = (bridge_span + overhang) / 2.0  # proxy for A
            misalign = tau / max(thermal_decay + [_EPS])  # proxy for τ
            chi = clamp_unit(eta * (1.0 - congestion) / (1.0 + misalign))

            # Axis 15: psi — adaptive alignment state (exponentially smoothed)
            # Track how well the path matches expected (via phi-coherence)
            # This is a running estimate; actual requires history
            psi = 0.5  # default neutral; updated per strategy

            # Axis 16: phi — structural regime (optimal configuration)
            # For gcode, this is the "ideal" path geometry given constraints
            # Approximation: high when layer-aligned, low when bridging/overhang
            phi = clamp_unit(1.0 - overhang - bridge_span * 0.5)

            # Axis 17: delta — regime lag |φ - ψ|
            delta = abs(phi - psi)

            vec = [
                mv.x, mv.y, mv.z, mv.e, mv.f,     # physical (0-4)
                eta, tau, accel,                    # material/thermal/accel (5-7)
                overhang, bridge_span, retraction,  # geometry (8-10)
                layer_height, wall_prox, ringing,   # quality (11-13)
                chi, psi, phi, delta,               # Layer 7 (14-17)
            ]

            # Compute scroll_id and twist_bit for path orientation memory
            scroll_id = int(mv.z * 10) + int(mv.x / 20)  # Z-layer + X-bucket
            twist_bit = 1 if (dx * dy >= 0) else -1 if (dx * dy < 0) else 1

            out.append(Move14D(move=mv, vec=vec, scroll_id=scroll_id, twist_bit=twist_bit))

        return out


# ── Canal metric ──────────────────────────────────────────────────────────────

class CanalMetric:
    """
    d(p1, p2) = ‖p2-p1‖₁₈ × η(p1) × (1+τ(p1)) × (1+λ_A·A(p1)) × (1+λ_χ·(1-χ))

    η is thixotropic: decreases with visit count for p1's voxel.
    χ is structured chaos: rewards productive disorder.
    """

    def __init__(self, grid_res: float = 5.0):
        self._grid_res = grid_res
        self._visit_counts: Dict[Tuple[int, int, int], int] = defaultdict(int)

    def _voxel(self, v: List[float]) -> Tuple[int, int, int]:
        return (
            int(v[_AX_X] / self._grid_res),
            int(v[_AX_Y] / self._grid_res),
            int(v[_AX_Z] * 10),   # finer Z resolution
        )

    def distance(self, a: Move14D, b: Move14D) -> float:
        # ‖Φ‖ — L2 over all 18 axes (normalised to [0,1] range per axis)
        # Updated norms for 18D space (14 original + 4 Layer 7)
        norms = [200, 200, 10, 50, 15000, 1, 5, 1, 1, 1, 1, 1, 1, 1,
                 1.0, 1.0, 1.0, 1.0]  # chi, psi, phi, delta are already [0,1]
        diff = [(a.vec[i] - b.vec[i]) / max(norms[i], _EPS) for i in range(N_AXES)]
        phi_norm = math.sqrt(sum(d*d for d in diff))

        vox = self._voxel(a.vec)
        visits = self._visit_counts[vox]
        eta = _ETA_0 * math.exp(-_LAMBDA_T * visits)

        tau = a.vec[_AX_TAU]
        accel = a.vec[_AX_ACC]
        chi = a.vec[_AX_CHI]

        # Layer 7: Modified canal cost with structured chaos χ
        # Only destructive chaos (1-χ) penalizes torsion and acceleration
        tau_eff = (1.0 - chi) * tau
        accel_eff = (1.0 - chi) * accel

        # Base cost
        base_cost = phi_norm * eta

        # Add torsion alignment bonus/penalty based on twist_bit match
        twist_alignment = 1.0
        if a.twist_bit == b.twist_bit and a.twist_bit != 0:
            twist_alignment = 0.9  # 10% discount for aligned scrolls

        return base_cost * (1 + tau_eff) * (1 + _LAMBDA_A * accel_eff) * twist_alignment

    def visit(self, m: Move14D) -> None:
        self._visit_counts[self._voxel(m.vec)] += 1

    def total_cost(self, path: List[Move14D], record_visits: bool = False) -> float:
        if len(path) < 2:
            return 0.0
        cost = 0.0
        for i in range(1, len(path)):
            cost += self.distance(path[i - 1], path[i])
            if record_visits:
                self.visit(path[i - 1])
        return cost


# ── φ-coherence gate ──────────────────────────────────────────────────────────

def phi_coherence_score(path: List[Move14D]) -> float:
    """
    Fraction of consecutive delta-vectors whose 18D amplitude ratio ≈ φ.

    Layer 7: Uses chi (structured chaos) to widen acceptance window when
    productive disorder is detected. High chi → more tolerance for variation.

    Uses the same per-axis normalization as CanalMetric.
    """
    if len(path) < 2:
        return 0.0

    # Updated normalization scales for 18D space
    norms = [200, 200, 10, 50, 15000, 1, 5, 1, 1, 1, 1, 1, 1, 1,
             1.0, 1.0, 1.0, 1.0]

    coherent = 0
    for i in range(1, len(path)):
        a, b = path[i - 1].vec, path[i].vec
        chi = a[_AX_CHI]  # structured chaos at this position

        delta = [abs(b[j] - a[j]) / max(norms[j], _EPS) for j in range(N_AXES)]
        # axis_0 = combined XY physical displacement (primary motion)
        axis0 = delta[_AX_X] + delta[_AX_Y] + _EPS
        rest_sum = sum(delta[2:])   # Z + E + F + all planning axes
        ratio = rest_sum / axis0

        # Layer 7: Dynamic tolerance based on chi
        # High chi → wider acceptance (structured chaos is productive)
        base_tolerance = 0.20
        chi_bonus = 0.10 * chi  # up to 10% extra tolerance
        tolerance = base_tolerance + chi_bonus

        if abs(ratio - PHI) / PHI < tolerance:
            coherent += 1

    return coherent / (len(path) - 1)


def is_bridge_node(a: Move14D, b: Move14D, c: Move14D, threshold: float = 10.0) -> bool:
    """Detect if b is a bridge state between a and c (dual-anchor constraint).

    A bridge exists when b is between two constraints that both 'reach' toward it.
    This is a simplified geometric check for 3D printing paths.
    """
    # Check if b is roughly between a and c in XY plane
    dx_ab = b.vec[_AX_X] - a.vec[_AX_X]
    dy_ab = b.vec[_AX_Y] - a.vec[_AX_Y]
    dx_bc = c.vec[_AX_X] - b.vec[_AX_X]
    dy_bc = c.vec[_AX_Y] - b.vec[_AX_Y]

    # Same Z-layer check
    if abs(b.vec[_AX_Z] - a.vec[_AX_Z]) > 0.05:
        return False
    if abs(c.vec[_AX_Z] - b.vec[_AX_Z]) > 0.05:
        return False

    # Direction reversal check (bridge spans typically reverse direction)
    dot_product = dx_ab * dx_bc + dy_ab * dy_bc
    if dot_product > 0:  # Same direction, not a bridge
        return False

    # Distance check (within threshold)
    dist_ab = math.hypot(dx_ab, dy_ab)
    dist_bc = math.hypot(dx_bc, dy_bc)
    if dist_ab > threshold or dist_bc > threshold:
        return False

    return True


# ── Strategies ────────────────────────────────────────────────────────────────

def _by_layer(moves: List[Move14D]) -> Dict[float, List[Move14D]]:
    layers: Dict[float, List[Move14D]] = defaultdict(list)
    for m in moves:
        layers[round(m.move.z, 3)].append(m)
    return layers


def _detect_and_mark_bridges(moves: List[Move14D]) -> None:
    """Mark bridge_candidate flag on moves that are potential bridge states."""
    if len(moves) < 3:
        return

    for i in range(1, len(moves) - 1):
        a, b, c = moves[i-1], moves[i], moves[i+1]
        if is_bridge_node(a, b, c):
            moves[i].bridge_candidate = True


def strategy_baseline(moves: List[Move14D]) -> List[Move14D]:
    return list(moves)


def strategy_canal(moves: List[Move14D]) -> List[Move14D]:
    """Greedy nearest-neighbour by canal metric, within each Z-layer."""
    metric = CanalMetric()
    result: List[Move14D] = []
    for z, layer in sorted(_by_layer(moves).items()):
        remaining = list(layer)
        if not remaining:
            continue
        cur = remaining.pop(0)
        result.append(cur)
        while remaining:
            costs = [(metric.distance(cur, nxt), i, nxt) for i, nxt in enumerate(remaining)]
            costs.sort(key=lambda t: t[0])
            _, best_i, best = costs[0]
            metric.visit(cur)
            result.append(best)
            remaining.pop(best_i)
            cur = best
    return result


def strategy_phi_sorted(moves: List[Move14D]) -> List[Move14D]:
    """Sort moves within each layer by φ-ratio bucket (closer to φ first)."""
    result: List[Move14D] = []
    for z, layer in sorted(_by_layer(moves).items()):
        def phi_err(m: Move14D) -> float:
            v = [abs(x) for x in m.vec]
            axis0 = v[_AX_X] + _EPS
            return abs(sum(v[1:]) / axis0 - PHI)
        result.extend(sorted(layer, key=phi_err))
    return result


def strategy_thixotropic(moves: List[Move14D]) -> List[Move14D]:
    """Prefer previously-visited voxels — emergent worn-path following."""
    metric = CanalMetric()
    # Warm-up pass: record visits in baseline order
    for m in moves:
        metric.visit(m)
    # Now re-sort within layers: lower canal distance from origin wins
    result: List[Move14D] = []
    for z, layer in sorted(_by_layer(moves).items()):
        if not layer:
            continue
        cur = layer[0]
        remaining = list(layer[1:])
        result.append(cur)
        while remaining:
            costs = [(metric.distance(cur, nxt), i, nxt) for i, nxt in enumerate(remaining)]
            costs.sort(key=lambda t: t[0])
            _, best_i, best = costs[0]
            result.append(best)
            remaining.pop(best_i)
            cur = best
    return result


def strategy_random(moves: List[Move14D], seed: int = 42) -> List[Move14D]:
    rng = random.Random(seed)
    result: List[Move14D] = []
    for z, layer in sorted(_by_layer(moves).items()):
        shuffled = list(layer)
        rng.shuffle(shuffled)
        result.extend(shuffled)
    return result


STRATEGIES = {
    "baseline":    strategy_baseline,
    "canal":       strategy_canal,
    "phi_sorted":  strategy_phi_sorted,
    "thixotropic": strategy_thixotropic,
    "random":      strategy_random,
}


# ── Virtual extruder metrics ──────────────────────────────────────────────────

@dataclass
class ExtruderMetrics:
    strategy: str
    canal_cost: float
    phi_coherence: float
    move_count: int
    travel_moves: int
    layer_count: int
    bridge_risk_mean: float
    ringing_risk_mean: float
    overhang_mean: float
    estimated_time_s: float    # Σ distance / feedrate
    # Layer 7 extensions
    chi_mean: float            # structured chaos (0-1, higher = more productive)
    regime_lag_mean: float    # |φ - ψ| alignment lag
    bridge_count: int          # detected bridge states
    scroll_alignment: float   # fraction of moves with consistent twist_bit


def score(name: str, path: List[Move14D]) -> ExtruderMetrics:
    metric = CanalMetric()
    cost = metric.total_cost(path, record_visits=False)
    phi = phi_coherence_score(path)

    # Layer 7: Detect and mark bridges
    _detect_and_mark_bridges(path)

    layers = len(set(round(m.move.z, 3) for m in path))
    travels = sum(1 for m in path if m.move.is_travel)

    bridge_risks  = [m.vec[_AX_BRG] for m in path]
    ringing_risks = [m.vec[_AX_RNG] for m in path]
    overhangs     = [m.vec[_AX_OVH] for m in path]

    br_mean  = sum(bridge_risks)  / max(len(bridge_risks), 1)
    rr_mean  = sum(ringing_risks) / max(len(ringing_risks), 1)
    ov_mean  = sum(overhangs)     / max(len(overhangs), 1)

    # Layer 7: Compute extended metrics
    chis = [m.vec[_AX_CHI] for m in path]
    chi_mean = sum(chis) / max(len(chis), 1)

    regime_lags = [m.vec[_AX_DELTA] for m in path]
    lag_mean = sum(regime_lags) / max(len(regime_lags), 1)

    bridge_count = sum(1 for m in path if m.bridge_candidate)

    # Scroll alignment: fraction of consecutive moves with same twist
    aligned_twists = 0
    total_twist_pairs = 0
    for i in range(1, len(path)):
        if path[i].twist_bit == path[i-1].twist_bit:
            aligned_twists += 1
        total_twist_pairs += 1
    scroll_align = aligned_twists / max(total_twist_pairs, 1)

    # Estimated time: Σ(XY distance / feedrate)
    t = 0.0
    for i in range(1, len(path)):
        a, b = path[i-1].move, path[i].move
        d = math.hypot(b.x - a.x, b.y - a.y, b.z - a.z)
        f = max(b.f, 100) / 60  # mm/s
        t += d / f

    return ExtruderMetrics(
        strategy=name,
        canal_cost=round(cost, 4),
        phi_coherence=round(phi, 4),
        move_count=len(path),
        travel_moves=travels,
        layer_count=layers,
        bridge_risk_mean=round(br_mean, 4),
        ringing_risk_mean=round(rr_mean, 4),
        overhang_mean=round(ov_mean, 4),
        estimated_time_s=round(t, 1),
        # Layer 7 metrics
        chi_mean=round(chi_mean, 4),
        regime_lag_mean=round(lag_mean, 4),
        bridge_count=bridge_count,
        scroll_alignment=round(scroll_align, 4),
    )


# ── Synthetic benchy-like G-code generator ────────────────────────────────────

def _synthetic_gcode(seed: int = 0) -> str:
    """
    Generate a minimal benchy-representative G-code sequence covering:
      - Hull curve (smooth XY arcs, multiple layers)
      - Stern bridge (XY travel over open space)
      - Chimney overhang (Z-increasing with decreasing support)
      - Porthole circles (small tight loops, high acceleration)
      - Roof (45° overhang)
    """
    rng = random.Random(seed)
    lines = ["; synthetic benchy-like gcode (gcode_optimizer test fixture)"]
    f_default = 3000

    def g1(x, y, z, e_delta, f=f_default, acc_e=None):
        nonlocal cur_e
        cur_e += e_delta
        return f"G1 X{x:.3f} Y{y:.3f} Z{z:.3f} E{cur_e:.4f} F{f}"

    cur_e = 0.0
    layer_heights = [round(0.2 * i, 2) for i in range(1, 16)]   # 15 layers

    # ── Hull curve: 3 layers of smooth ellipse ─────────────────────────────────
    for lz in layer_heights[:3]:
        n_pts = 36
        for i in range(n_pts):
            angle = 2 * math.pi * i / n_pts
            x = 80 + 40 * math.cos(angle)
            y = 40 + 20 * math.sin(angle)
            de = 0.04 + rng.gauss(0, 0.002)
            lines.append(g1(x, y, lz, de))

    # ── Stern bridge: unsupported XY span ──────────────────────────────────────
    lz = layer_heights[3]
    for x_step in range(20):
        x = 20 + x_step * 3
        y = 40
        de = 0.05 if x_step > 3 else 0.0   # first few are travel
        lines.append(g1(x, y, lz, de))

    # ── Chimney overhang: Z-increasing with shrinking XY radius ────────────────
    for li, lz in enumerate(layer_heights[4:10]):
        r = 8 - li * 1.0   # shrinking circle = overhang
        cx, cy = 60, 60
        for i in range(24):
            angle = 2 * math.pi * i / 24
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            de = 0.03
            lines.append(g1(x, y, lz, de))

    # ── Porthole circles: small tight loops, high ringing risk ─────────────────
    for lz in layer_heights[2:5]:
        for cx_off in [30, 50]:
            for i in range(16):
                angle = 2 * math.pi * i / 16
                x = cx_off + 3 * math.cos(angle)
                y = 25 + 3 * math.sin(angle)
                de = 0.015
                lines.append(g1(x, y, lz, de, f=5000))   # high-speed = ringing

    # ── Roof overhangs: 45° slope ──────────────────────────────────────────────
    for li, lz in enumerate(layer_heights[10:]):
        x_start = 30 + li * 2   # footprint shrinks = overhang
        for xi in range(20):
            x = x_start + xi * 1.5
            y = 40 + rng.gauss(0, 0.1)
            de = 0.045
            lines.append(g1(x, y, lz, de))

    return "\n".join(lines)


# ── Report ────────────────────────────────────────────────────────────────────

_COL_W = 14

def _row(label: str, *vals) -> str:
    return f"  {label:<22}" + "".join(f"{str(v):>{_COL_W}}" for v in vals)


def print_report(results: List[ExtruderMetrics]) -> None:
    strategies = [r.strategy for r in results]
    print()
    print("=" * (24 + _COL_W * len(results)))
    print("  18D VIRTUAL EXTRUDER REPORT (Layer 7 Extended)")
    print("=" * (24 + _COL_W * len(results)))
    print(_row("metric", *strategies))
    print("  " + "-" * (22 + _COL_W * len(results)))

    fields = [
        ("canal_cost",        "canal_cost",        "lower = better path"),
        ("phi_coherence",     "phi_coherence",      "higher = more φ-locked"),
        ("estimated_time_s",  "estimated_time_s",   "lower = faster print"),
        ("bridge_risk_mean",  "bridge_risk_mean",   "lower = safer bridges"),
        ("ringing_risk_mean", "ringing_risk_mean",  "lower = less vibration"),
        ("overhang_mean",     "overhang_mean",      "lower = better support"),
        ("travel_moves",      "travel_moves",       "lower = less stringing"),
        ("move_count",        "move_count",         ""),
        ("layer_count",       "layer_count",        ""),
        # Layer 7 metrics
        ("chi_mean",          "chi_mean",           "higher = productive chaos"),
        ("regime_lag_mean",   "regime_lag",         "lower = better aligned"),
        ("bridge_count",      "bridge_count",       "count of dual-anchor states"),
        ("scroll_alignment",  "scroll_alignment",   "higher = consistent path"),
    ]

    for attr, label, note in fields:
        vals = [getattr(r, attr) for r in results]
        note_str = f"  ← {note}" if note else ""
        print(_row(label, *vals) + note_str)

    print()

    # Rank by canal_cost
    ranked = sorted(results, key=lambda r: r.canal_cost)
    print("  Ranking by canal cost:")
    for i, r in enumerate(ranked, 1):
        delta = ""
        if i > 1:
            pct = (r.canal_cost - ranked[0].canal_cost) / max(ranked[0].canal_cost, _EPS) * 100
            delta = f"  (+{pct:.1f}%)"
        phi_pass = "φ-COHERENT" if r.phi_coherence >= 0.5 else "φ-WEAK"
        chi_tag = f" χ={r.chi_mean:.2f}" if r.chi_mean > 0.5 else ""
        print(f"    {i}. {r.strategy:<14} cost={r.canal_cost:<10} {phi_pass}{chi_tag}{delta}")

    print()

    # φ-commit gate
    best = ranked[0]
    if best.phi_coherence >= 0.5:
        print(f"  COMMIT GATE: PASS — '{best.strategy}' φ-coherence={best.phi_coherence}")
    else:
        alt = next((r for r in ranked if r.phi_coherence >= 0.5), None)
        if alt:
            print(f"  COMMIT GATE: best canal '{best.strategy}' fails φ-coherence.")
            print(f"               Fallback: '{alt.strategy}' (cost={alt.canal_cost}, φ={alt.phi_coherence})")
        else:
            print("  COMMIT GATE: ALL strategies below φ-coherence threshold.")

    print("=" * (24 + _COL_W * len(results)))
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="14D canal-metric G-code optimizer (virtual extruder)")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--input",     metavar="FILE",  help="Input G-code file")
    src.add_argument("--synthetic", action="store_true", help="Use built-in synthetic benchy fixture")
    ap.add_argument("--strategies", default="baseline,canal,phi_sorted,thixotropic,random",
                    help="Comma-separated list of strategies to run")
    ap.add_argument("--emit", metavar="DIR",
                    help="Emit optimized G-code files to DIR (one per strategy)")
    ap.add_argument("--telemetry", metavar="FILE",
                    help="Log voxel telemetry to JSONL file")
    ap.add_argument("--seed", type=int, default=0, help="RNG seed for synthetic/random")
    args = ap.parse_args()

    # Load G-code
    if args.synthetic:
        gcode_text = _synthetic_gcode(seed=args.seed)
        print(f"[gcode_optimizer] synthetic fixture: {len(gcode_text.splitlines())} lines")
    else:
        path = Path(args.input)
        if not path.exists():
            print(f"[gcode_optimizer] ERROR: file not found: {path}", file=sys.stderr)
            sys.exit(1)
        gcode_text = path.read_text()
        print(f"[gcode_optimizer] loaded: {path} ({len(gcode_text.splitlines())} lines)")

    # Parse → expand
    raw_moves = parse_gcode(gcode_text)
    if not raw_moves:
        print("[gcode_optimizer] ERROR: no G0/G1 moves found", file=sys.stderr)
        sys.exit(1)

    print(f"[gcode_optimizer] parsed {len(raw_moves)} moves, expanding to 18D (Layer 7)…")
    expander = Expander14D()
    moves_14d = expander.expand(raw_moves)

    # Run strategies
    strategy_names = [s.strip() for s in args.strategies.split(",") if s.strip()]
    unknown = [s for s in strategy_names if s not in STRATEGIES]
    if unknown:
        print(f"[gcode_optimizer] unknown strategies: {unknown}. Available: {list(STRATEGIES)}", file=sys.stderr)
        sys.exit(1)

    results: List[ExtruderMetrics] = []
    for name in strategy_names:
        print(f"[gcode_optimizer] running strategy: {name}…", end=" ", flush=True)
        fn = STRATEGIES[name]
        optimized = fn(moves_14d) if name != "random" else fn(moves_14d, seed=args.seed)
        metrics = score(name, optimized)
        results.append(metrics)
        print(f"canal={metrics.canal_cost}, φ={metrics.phi_coherence}, χ={metrics.chi_mean:.2f}")

        # Optionally emit G-code
        if args.emit:
            out_dir = Path(args.emit)
            out_dir.mkdir(parents=True, exist_ok=True)
            gcode_out = emit_gcode([m.move for m in optimized])
            out_path = out_dir / f"{name}.gcode"
            out_path.write_text(gcode_out)
            print(f"[gcode_optimizer]   → {out_path}")

        # Optionally log telemetry (Layer 7)
        if args.telemetry:
            import json
            telemetry_path = Path(args.telemetry)
            telemetry_path.parent.mkdir(parents=True, exist_ok=True)

            for i, m in enumerate(optimized):
                row = {
                    "strategy": name,
                    "move_idx": i,
                    "voxel_key": (m.scroll_id, int(m.vec[_AX_X]/5), int(m.vec[_AX_Y]/5)),
                    "x": round(m.vec[_AX_X], 3),
                    "y": round(m.vec[_AX_Y], 3),
                    "z": round(m.vec[_AX_Z], 3),
                    "chi": round(m.vec[_AX_CHI], 6),
                    "psi": round(m.vec[_AX_PSI], 6),
                    "phi": round(m.vec[_AX_PHI], 6),
                    "delta": round(m.vec[_AX_DELTA], 6),
                    "scroll_id": m.scroll_id,
                    "twist_bit": m.twist_bit,
                    "bridge_candidate": m.bridge_candidate,
                }
                with telemetry_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(row, sort_keys=True) + "\n")

    print_report(results)


if __name__ == "__main__":
    main()
