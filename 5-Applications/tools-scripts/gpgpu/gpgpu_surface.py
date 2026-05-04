#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""GPGPU surface abstraction for quantitative modeling.

This module provides a single compute surface that can run on:
1) CuPy (GPU)
2) NumPy (CPU vectorized)
3) Pure Python fallback
"""

from __future__ import annotations

import importlib
import importlib.util
import math
from typing import Any, Iterable, List

# ── NE geometry scaffold (geometry-rip branch) ────────────────────────────────
# Fixes EUCLIDEAN_ASSUMPTION_AUDIT finding #2 (HIGH): z-scores on log-normal
# quantities (gas fees, spreads) assume Gaussian on an unbounded line.
# Fix: log-transform before z-scoring to match the actual log-normal distribution.
_USE_NE_GEOMETRY = False


class GPGPUSurface:
    def __init__(self) -> None:
        self.backend = "python"
        self.xp: Any = None
        if importlib.util.find_spec("cupy") is not None:
            try:
                cp = importlib.import_module("cupy")
                self.xp = cp
                self.backend = "cupy"
                return
            except (ImportError, AttributeError):
                pass

        if importlib.util.find_spec("numpy") is not None:
            try:
                np = importlib.import_module("numpy")
                self.xp = np
                self.backend = "numpy"
                return
            except (ImportError, AttributeError):
                pass

    def to_array(self, values: Iterable[float]) -> Any:
        vals = list(values)
        if self.backend in ("cupy", "numpy"):
            return self.xp.asarray(vals, dtype=float)
        return vals

    def to_list(self, arr: Any) -> List[float]:
        if self.backend == "cupy":
            return [float(x) for x in self.xp.asnumpy(arr).tolist()]
        if self.backend == "numpy":
            return [float(x) for x in arr.tolist()]
        return [float(x) for x in arr]

    def mean(self, values: Iterable[float]) -> float:
        vals = list(values)
        if not vals:
            return 0.0
        if self.backend in ("cupy", "numpy"):
            arr = self.to_array(vals)
            return float(self.xp.mean(arr))
        return sum(vals) / len(vals)

    def std(self, values: Iterable[float]) -> float:
        vals = list(values)
        if len(vals) < 2:
            return 0.0
        if self.backend in ("cupy", "numpy"):
            arr = self.to_array(vals)
            return float(self.xp.std(arr))
        mu = self.mean(vals)
        var = sum((x - mu) ** 2 for x in vals) / len(vals)
        return math.sqrt(var)

    def zscores(self, values: Iterable[float]) -> List[float]:
        vals = list(values)
        if not vals:
            return []
        sigma = self.std(vals)
        if sigma == 0:
            return [0.0 for _ in vals]
        mu = self.mean(vals)
        if self.backend in ("cupy", "numpy"):
            arr = self.to_array(vals)
            out = (arr - mu) / sigma
            return self.to_list(out)
        return [(x - mu) / sigma for x in vals]

    def log_zscores(self, values: Iterable[float], eps: float = 1e-9) -> List[float]:
        """NE path: z-score on log-transformed values (AUDIT FINDING #2 fix).

        Gas fees and spreads are log-normally distributed. z-scoring log(x)
        instead of x correctly treats multiplicative deviations as equal in
        magnitude (e.g., 2× above mean == 0.5× below mean).
        Use when _USE_NE_GEOMETRY is True.
        """
        log_vals = [math.log(max(eps, float(x))) for x in values]
        return self.zscores(log_vals)

    def sigmoid(self, x: float) -> float:
        if self.backend in ("cupy", "numpy"):
            return float(1.0 / (1.0 + self.xp.exp(-x)))
        return 1.0 / (1.0 + math.exp(-x))

    def softmax(self, values: Iterable[float], temperature: float = 1.0) -> List[float]:
        vals = list(values)
        if not vals:
            return []
        t = max(1e-6, float(temperature))
        mx = max(vals)

        if self.backend in ("cupy", "numpy"):
            arr = self.to_array(vals)
            exps = self.xp.exp((arr - mx) / t)
            denom = float(self.xp.sum(exps))
            if denom == 0.0:
                return [1.0 / len(vals)] * len(vals)
            probs = exps / denom
            return self.to_list(probs)

        exps_py = [math.exp((x - mx) / t) for x in vals]
        denom_py = sum(exps_py)
        if denom_py == 0.0:
            return [1.0 / len(vals)] * len(vals)
        return [x / denom_py for x in exps_py]


def get_surface() -> GPGPUSurface:
    return GPGPUSurface()
