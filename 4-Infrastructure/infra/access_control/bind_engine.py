"""
bind_engine.py — Minimal Python Loader for the Lean Bind Server

The single primitive of the reengineered stack:

    bind(left, right, metric_kind, history=None) -> BindResult

All invariant checks, conservation laws, and cost evaluations are delegated
to the compiled Lean `bindserver` executable. Python only handles:

  1. Trajectory history (n-local topology)
  2. Metric pre-computation from history
  3. JSON serialization / subprocess I/O
  4. Result wrapping

This ensures the physical semantics (Standard Model invariants, lawful loss,
bind bridge equations) are enforced by the formally-typed Lean layer.
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import threading
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

# =============================================================================
# Primitive Types
# =============================================================================

@dataclass(frozen=True)
class Metric:
    cost: int = 0
    tensor: str = "identity"
    torsion: int = 0
    reference: str = "euclidean_baseline"
    history_len: int = 0

    @staticmethod
    def euclidean() -> Metric:
        return Metric()


@dataclass(frozen=True)
class Witness:
    left_invariant: str
    right_invariant: str
    conserved: bool
    trace_hash: str


@dataclass(frozen=True)
class BindResult:
    left: Any
    right: Any
    metric: Metric
    cost: int
    witness: Witness
    lawful: bool


# =============================================================================
# Lean Server Subprocess Wrapper
# =============================================================================

class _LeanServer:
    """Singleton wrapper around the compiled Lean bindserver executable."""

    _instance: Optional[_LeanServer] = None
    _lock = threading.Lock()

    def __new__(cls) -> _LeanServer:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._proc: Optional[subprocess.Popen] = None
                cls._instance._available = False
                cls._instance._start()
            return cls._instance

    def _find_binary(self) -> Optional[Path]:
        # Try project-relative path first
        candidates = [
            Path(__file__).resolve().parents[2] / "tools" / "lean" / "Semantics" / ".lake" / "build" / "bin" / "bindserver",
            Path(os.getcwd()) / "tools" / "lean" / "Semantics" / ".lake" / "build" / "bin" / "bindserver",
        ]
        for c in candidates:
            if c.exists() and c.is_file():
                return c
        return None

    def _start(self) -> None:
        binary = self._find_binary()
        if binary is None:
            print("[bind_engine] Lean bindserver not found; falling back to pure Python.", file=sys.stderr)
            return
        try:
            self._proc = subprocess.Popen(
                [str(binary)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            self._available = True
        except Exception as e:
            print(f"[bind_engine] Failed to start bindserver: {e}", file=sys.stderr)

    def call(self, request: Dict[str, Any]) -> Dict[str, Any]:
        if not self._available or self._proc is None or self._proc.poll() is not None:
            raise RuntimeError("Lean bindserver is not available")
        line = json.dumps(request, separators=(",", ":")) + "\n"
        self._proc.stdin.write(line)  # type: ignore[union-attr]
        self._proc.stdin.flush()      # type: ignore[union-attr]
        resp_line = self._proc.stdout.readline()  # type: ignore[union-attr]
        if not resp_line:
            raise RuntimeError("bindserver returned empty response (crashed?)")
        return json.loads(resp_line)

    def close(self) -> None:
        if self._proc is not None:
            self._proc.stdin.close()
            self._proc.wait(timeout=2)





# =============================================================================
# Universal Bind Engine
# =============================================================================

class BindEngine:
    """
    Runtime engine for the Cambrian collapse.

    Maintains a history of binds so that metrics become n-local automatically.
    All lawfulness and cost computation is delegated to the Lean bindserver.
    """

    def __init__(self, max_history: int = 64):
        self.history: deque[BindResult] = deque(maxlen=max_history)
        self._server = _LeanServer()

    def bind(
        self,
        left: Any,
        right: Any,
        metric_kind: str,
        invariant_left: Callable[[Any], str] = lambda x: str(hash(str(x))),
        invariant_right: Callable[[Any], str] = lambda x: str(hash(str(x))),
        custom_cost: Optional[Callable[[Any, Any, Metric], float]] = None,
        use_history: bool = True,
    ) -> BindResult:
        # Python shim does not compute metrics or invariants.
        # All cost/invariant logic is delegated to the Lean bindserver.
        metric = Metric(
            cost=0,
            tensor=metric_kind,
            torsion=0,
            reference="euclidean_baseline",
            history_len=len(self.history),
        )

        if not self._server._available:
            raise RuntimeError("Lean bindserver is not available. Pure Python fallback is forbidden by Functional Collapse axioms. Please build the Lean engine.")

        # Delegate to Lean bindserver for cost/metric computation
        request = {
            "metricKind": metric_kind,
            "left": left,
            "right": right,
            "useHistory": use_history and metric_kind in ("riemannian", "geometric", "control"),
            "historyLen": metric.history_len,
            "historyCost": metric.cost,
            "historyTorsion": metric.torsion,
        }
        resp = self._server.call(request)
        if "error" in resp:
            raise RuntimeError(f"bindserver error: {resp['error']}")

        # All invariants come from Lean bindserver. Python shim does not
        # compute invariants, lawful checks, or trace hashes.
        inv_l = resp["leftInvariant"]
        inv_r = resp["rightInvariant"]
        is_lawful = resp["lawful"]
        trace_hash = resp["traceHash"]

        witness = Witness(
            left_invariant=inv_l,
            right_invariant=inv_r,
            conserved=is_lawful,
            trace_hash=trace_hash,
        )
        result = BindResult(
            left=left,
            right=right,
            metric=Metric(
                cost=resp["cost"],
                tensor=resp["metricTensor"],
                torsion=resp["metricTorsion"],
                reference=metric.reference,
                history_len=resp["metricHistoryLen"],
            ),
            cost=resp["cost"],
            witness=witness,
            lawful=is_lawful,
        )
        self.history.append(result)
        return result



    def nlocal_metric(self, base_tensor: str = "riemannian") -> Metric:
        # TODO(lean-port): delegate history→metric computation to bindserver
        return Metric(
            cost=0,
            tensor=base_tensor,
            torsion=0,
            reference="nlocal_delegated",
            history_len=len(self.history),
        )

    def last(self, n: int = 1) -> List[BindResult]:
        return list(self.history)[-n:]


# =============================================================================
# Convenience Constructors (the collapsed MATH_MODEL_MAP instances)
# =============================================================================

def informational_bind(
    current: Dict[str, float],
    optimal: Dict[str, float],
    engine: Optional[BindEngine] = None,
) -> BindResult:
    eng = engine or BindEngine()
    return eng.bind(
        left=current,
        right=optimal,
        metric_kind="informational",
        invariant_left=lambda d: f"sum={sum(d.values()):.6f}",
        invariant_right=lambda d: f"sum={sum(d.values()):.6f}",
        use_history=False,
    )


def geometric_bind(
    state_a: Dict[str, Any],
    state_b: Dict[str, Any],
    engine: Optional[BindEngine] = None,
) -> BindResult:
    eng = engine or BindEngine()
    return eng.bind(
        left=state_a,
        right=state_b,
        metric_kind="geometric",
        invariant_left=lambda d: str(d.get("kind", "unknown")),
        invariant_right=lambda d: str(d.get("kind", "unknown")),
        use_history=True,
    )


def thermodynamic_bind(
    current: Dict[str, float],
    equilibrium: Dict[str, float],
    engine: Optional[BindEngine] = None,
) -> BindResult:
    eng = engine or BindEngine()
    return eng.bind(
        left=current,
        right=equilibrium,
        metric_kind="thermodynamic",
        invariant_left=lambda d: f"E={d.get('energy', 0.0):.6f}",
        invariant_right=lambda d: f"E={d.get('energy', 0.0):.6f}",
        use_history=False,
    )


def physical_bind(
    inputs: Dict[str, Any],
    outputs: Dict[str, Any],
    engine: Optional[BindEngine] = None,
) -> BindResult:
    """Physical particle interaction binding — delegated to Lean."""
    eng = engine or BindEngine()
    return eng.bind(
        left=inputs,
        right=outputs,
        metric_kind="physical",
        use_history=False,
    )


def control_bind(
    observation: Dict[str, float],
    setpoint: Dict[str, float],
    engine: Optional[BindEngine] = None,
) -> BindResult:
    eng = engine or BindEngine()
    return eng.bind(
        left=observation,
        right=setpoint,
        metric_kind="control",
        invariant_left=lambda d: f"mode={d.get('mode', 'none')}",
        invariant_right=lambda d: f"mode={d.get('mode', 'none')}",
        use_history=True,
    )


# =============================================================================
# Example usage
# =============================================================================

if __name__ == "__main__":
    # Example 1: physical bind (e- + e+ -> γ + γ)
    engine = BindEngine()
    result = physical_bind(
        inputs={"particles": [
            {"kind": "electron", "quantities": {"charge": -1, "leptonNumber": 1, "mass": 1}},
            {"kind": "positron", "quantities": {"charge": 1, "leptonNumber": -1, "mass": 1}},
        ]},
        outputs={"particles": [
            {"kind": "photon", "quantities": {"charge": 0, "leptonNumber": 0}},
            {"kind": "photon", "quantities": {"charge": 0, "leptonNumber": 0}},
        ]},
        engine=engine,
    )
    print(f"Physical bind: lawful={result.lawful}, cost={result.cost:.6f}")

    # Example 2: bad physical bind (charge not conserved)
    bad = physical_bind(
        inputs={"particles": [
            {"kind": "electron", "quantities": {"charge": -1, "leptonNumber": 1, "mass": 1}},
        ]},
        outputs={"particles": [
            {"kind": "photon", "quantities": {"charge": 0, "leptonNumber": 0}},
            {"kind": "photon", "quantities": {"charge": 0, "leptonNumber": 0}},
        ]},
        engine=BindEngine(),
    )
    print(f"Bad physical bind: lawful={bad.lawful}, cost={bad.cost:.6f}")

    # Example 3: geometric bind with history (n-local)
    geo_engine = BindEngine()
    for i in range(5):
        r = geometric_bind(
            state_a={"kind": "mu_seed", "state_vector": [0.1 * i, 0.2 * i]},
            state_b={"kind": "mu_seed", "state_vector": [0.1 * (i + 1), 0.2 * (i + 1)]},
            engine=geo_engine,
        )
    print(f"Last geometric bind: metric.tensor={r.metric.tensor}, torsion={r.metric.torsion:.6f}, history_len={r.metric.history_len}")
