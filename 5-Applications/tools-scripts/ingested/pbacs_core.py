"""PBACS Root Spec v1 - minimal reference implementation.
Domain-agnostic core runtime with hysteretic gate, projection family,
and stable convex update law.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, Iterable, List, Mapping, MutableMapping, Sequence, Tuple

Scalar = float
State = Sequence[Scalar]
Mode = str
Action = str


class ControlState(str, Enum):
    COMMIT = "COMMIT"
    HOLD = "HOLD"
    HALT = "HALT"
    DMT = "DMT"


@dataclass(frozen=True)
class RootConfig:
    weights: Mapping[str, Scalar]
    polarities: Mapping[str, int]
    entry_thresholds: Mapping[str, Scalar]
    exit_thresholds: Mapping[str, Scalar]
    engram_length_min_ms: Scalar = 500.0
    engram_length_max_ms: Scalar = 700.0
    alpha0: Scalar = 0.25
    beta: Scalar = 0.0

    def validate(self) -> None:
        if not self.weights:
            raise ValueError("weights must be non-empty")
        total = sum(self.weights.values())
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"weights must sum to 1.0, got {total}")
        for k, w in self.weights.items():
            if w < 0:
                raise ValueError(f"weight {k} must be non-negative")
        for k, p in self.polarities.items():
            if p not in (-1, 1):
                raise ValueError(f"polarity {k} must be -1 or 1")
        for name in self.entry_thresholds:
            lo = self.exit_thresholds.get(name)
            hi = self.entry_thresholds[name]
            if lo is None or not (0.0 <= lo < hi <= 1.0):
                raise ValueError(f"invalid hysteresis band for {name}")
        if not (0.0 <= self.alpha0 <= 1.0):
            raise ValueError("alpha0 must be in [0,1]")
        if self.engram_length_min_ms > self.engram_length_max_ms:
            raise ValueError("invalid engramLength bounds")


@dataclass
class StepTrace:
    t: int
    raw: Mapping[str, Scalar]
    x_t: List[Scalar]
    z_t: List[Scalar]
    projections: Dict[str, Scalar]
    score: Scalar
    control_state: ControlState
    action: Action
    mode: Mode
    alpha_t: Scalar
    engram_length_ms: Scalar
    x_next: List[Scalar]


class Adapter:
    """Universe Adapter Spec v1 interface."""

    def initial_state(self) -> List[Scalar]:
        raise NotImplementedError

    def modes(self) -> Sequence[Mode]:
        raise NotImplementedError

    def target_state(self, raw: Mapping[str, Scalar], history: Sequence[StepTrace]) -> List[Scalar]:
        raise NotImplementedError

    def update_projection_context(
        self, x_t: Sequence[Scalar], z_t: Sequence[Scalar], raw: Mapping[str, Scalar], history: Sequence[StepTrace]
    ) -> Mapping[str, Scalar]:
        raise NotImplementedError

    def projections(self) -> Mapping[str, Callable[[Mapping[str, Scalar]], Scalar]]:
        raise NotImplementedError

    def admissible(self, state: ControlState) -> Sequence[Tuple[Action, Mode]]:
        raise NotImplementedError

    def tie_break(self, candidates: Sequence[Tuple[Action, Mode]]) -> Tuple[Action, Mode]:
        return sorted(candidates)[0]


class PBACS:
    def __init__(self, config: RootConfig, adapter: Adapter):
        config.validate()
        self.cfg = config
        self.adapter = adapter
        self.history: List[StepTrace] = []
        self.x_t = list(adapter.initial_state())
        self.state = ControlState.COMMIT

    @staticmethod
    def _clamp01(x: Scalar) -> Scalar:
        return min(1.0, max(0.0, float(x)))

    def _project(self, context: Mapping[str, Scalar]) -> Dict[str, Scalar]:
        out: Dict[str, Scalar] = {}
        for name, fn in self.adapter.projections().items():
            out[name] = self._clamp01(fn(context))
        return out

    def _score(self, projections: Mapping[str, Scalar]) -> Scalar:
        total = 0.0
        for name, weight in self.cfg.weights.items():
            p = self.cfg.polarities.get(name, 1)
            total += p * weight * projections[name]
        return total

    def _next_control_state(self, p: Mapping[str, Scalar]) -> ControlState:
        enter = self.cfg.entry_thresholds
        leave = self.cfg.exit_thresholds
        # Priority order for entry.
        if p.get("u_tau", 0.0) >= enter["halt_tau"]:
            return ControlState.HALT
        if p.get("u_chi", 0.0) * p.get("u_gamma", 0.0) >= enter["dmt_product"]:
            return ControlState.DMT
        if p.get("u_delta_dot", 0.0) >= enter["hold_delta_dot"] and p.get("u_delta", 0.0) >= enter["hold_delta"]:
            return ControlState.HOLD
        # Hysteretic exit conditions.
        if self.state == ControlState.HALT and p.get("u_tau", 0.0) > leave["halt_tau"]:
            return ControlState.HALT
        if self.state == ControlState.DMT and p.get("u_chi", 0.0) * p.get("u_gamma", 0.0) > leave["dmt_product"]:
            return ControlState.DMT
        if self.state == ControlState.HOLD and (
            p.get("u_delta_dot", 0.0) > leave["hold_delta_dot"] and p.get("u_delta", 0.0) > leave["hold_delta"]
        ):
            return ControlState.HOLD
        return ControlState.COMMIT

    def _engram_length_ms(self, p: Mapping[str, Scalar]) -> Scalar:
        r_t = self._clamp01(p.get("u_pacing", p.get("u_delta", 0.0)))
        return self.cfg.engram_length_min_ms + (self.cfg.engram_length_max_ms - self.cfg.engram_length_min_ms) * r_t

    def _alpha(self, engram_length_ms: Scalar) -> Scalar:
        raw = self.cfg.alpha0 / (1.0 + self.cfg.beta * engram_length_ms)
        return self._clamp01(raw)

    def _update(self, z_t: Sequence[Scalar], alpha_t: Scalar) -> List[Scalar]:
        if len(self.x_t) != len(z_t):
            raise ValueError("state and target dimensions must match")
        x_next = []
        for x_i, z_i in zip(self.x_t, z_t):
            x_next.append(self._clamp01((1.0 - alpha_t) * x_i + alpha_t * z_i))
        return x_next

    def step(self, raw: Mapping[str, Scalar]) -> StepTrace:
        z_t = list(self.adapter.target_state(raw, self.history))
        context = dict(self.adapter.update_projection_context(self.x_t, z_t, raw, self.history))
        projections = self._project(context)
        self.state = self._next_control_state(projections)
        admissible = list(self.adapter.admissible(self.state))
        if not admissible:
            raise ValueError(f"no admissible actions for state {self.state}")
        # Domain-agnostic: same score for all admissible candidates unless adapter encodes mode-aware context.
        score = self._score(projections)
        best = self.adapter.tie_break(admissible)
        engram_length_ms = self._engram_length_ms(projections)
        alpha_t = self._alpha(engram_length_ms)
        x_next = self._update(z_t, alpha_t)
        trace = StepTrace(
            t=len(self.history), raw=dict(raw), x_t=list(self.x_t), z_t=z_t,
            projections=projections, score=score, control_state=self.state,
            action=best[0], mode=best[1], alpha_t=alpha_t, engram_length_ms=engram_length_ms, x_next=x_next,
        )
        self.history.append(trace)
        self.x_t = x_next
        return trace
