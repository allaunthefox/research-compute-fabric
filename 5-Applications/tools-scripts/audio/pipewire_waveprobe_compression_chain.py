#!/usr/bin/env python3
from __future__ import annotations

# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================

# [WARDEN BOUNDARY ENFORCEMENT INJECTED]
import sys
import os
try:
    from io_harness_compat import spawn_isolated_process, fetch_network_resource
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from io_harness_compat import spawn_isolated_process, fetch_network_resource

"""
PipeWire -> compression -> waveprobe test harness.

Captures a short WAV from PipeWire or loads an existing WAV, chunks the PCM
payload, then runs:

  1. ENE compression routing / MI scoring
  2. unified_canal_pipeline waveprobe scoring

The goal is not to replace the eventual HDL path. The goal is to measure what
happens when the existing compression logic is inserted into the host-side audio
front end.
"""

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
# import subprocess (REMOVED BY WARDEN)
import sys
import time
import wave
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from math_harness_compat import xp, AnyArray
import zlib


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ene_mi_signal import MISignal, extract_mi_features  # noqa: E402
from scripts.pipewire_dsp_workloads import (  # noqa: E402
    apply_dsp_workload,
    available_workloads,
)


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module {module_name} from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


UCP = _load_module(
    "unified_canal_pipeline",
    REPO_ROOT / "hutter" / "unified_canal_pipeline.py",
)

METHOD_SPECS: Dict[str, Dict[str, float | str]] = {
    "order0": {
        "encode_kind": "order0",
        "centroid_norm": 0.80,
        "transient_norm": 0.85,
        "flatness_norm": 0.92,
        "zcr_norm": 0.85,
        "low_band": 0.18,
        "mid_band": 0.34,
        "high_band": 0.80,
        "complexity": 0.08,
        "memory": 0.04,
    },
    "zlib_fast": {
        "encode_kind": "zlib_fast",
        "centroid_norm": 0.30,
        "transient_norm": 0.30,
        "flatness_norm": 0.26,
        "zcr_norm": 0.28,
        "low_band": 0.72,
        "mid_band": 0.42,
        "high_band": 0.12,
        "complexity": 0.18,
        "memory": 0.12,
    },
    "zlib": {
        "encode_kind": "zlib",
        "centroid_norm": 0.25,
        "transient_norm": 0.25,
        "flatness_norm": 0.20,
        "zcr_norm": 0.25,
        "low_band": 0.75,
        "mid_band": 0.45,
        "high_band": 0.10,
        "complexity": 0.36,
        "memory": 0.28,
    },
    "gzip": {
        "encode_kind": "gzip",
        "centroid_norm": 0.28,
        "transient_norm": 0.28,
        "flatness_norm": 0.24,
        "zcr_norm": 0.27,
        "low_band": 0.70,
        "mid_band": 0.48,
        "high_band": 0.14,
        "complexity": 0.34,
        "memory": 0.22,
    },
    "bz2": {
        "encode_kind": "bz2",
        "centroid_norm": 0.40,
        "transient_norm": 0.38,
        "flatness_norm": 0.30,
        "zcr_norm": 0.32,
        "low_band": 0.60,
        "mid_band": 0.62,
        "high_band": 0.18,
        "complexity": 0.58,
        "memory": 0.52,
    },
    "brotli": {
        "encode_kind": "brotli",
        "centroid_norm": 0.22,
        "transient_norm": 0.20,
        "flatness_norm": 0.16,
        "zcr_norm": 0.20,
        "low_band": 0.78,
        "mid_band": 0.55,
        "high_band": 0.08,
        "complexity": 0.54,
        "memory": 0.48,
    },
    "zstd": {
        "encode_kind": "zstd",
        "centroid_norm": 0.24,
        "transient_norm": 0.24,
        "flatness_norm": 0.18,
        "zcr_norm": 0.22,
        "low_band": 0.74,
        "mid_band": 0.58,
        "high_band": 0.10,
        "complexity": 0.30,
        "memory": 0.24,
    },
    "lzma": {
        "encode_kind": "lzma",
        "centroid_norm": 0.45,
        "transient_norm": 0.45,
        "flatness_norm": 0.30,
        "zcr_norm": 0.35,
        "low_band": 0.55,
        "mid_band": 0.70,
        "high_band": 0.20,
        "complexity": 0.82,
        "memory": 0.86,
    },
}

METHOD_PROFILES: Dict[str, Tuple[str, ...]] = {
    "baseline": ("order0", "zlib", "lzma"),
    "expanded": (
        "order0",
        "zlib_fast",
        "zlib",
        "gzip",
        "bz2",
        "brotli",
        "zstd",
        "lzma",
    ),
}


def available_method_profiles() -> Tuple[str, ...]:
    return tuple(METHOD_PROFILES.keys())


def _select_hybrid_dsp_workload(
    dsp_metrics: Dict[str, float],
    waveprobe_metrics: Dict[str, float],
) -> str:
    """
    Hybrid DSP workload selector using branch prediction principles.
    
    Selects optimal DSP workload based on audio characteristics:
    - Spectral-dominant audio → spectral_focus (FFT-based enhancement)
    - Transient-dominant audio → transient_edge (edge detection)
    - Balanced audio → hybrid (combined spectral + transient)
    - Simple audio → raw (no transform, fastest path)
    
    This reduces QUBO solve energy by pre-processing with optimal transforms.
    """
    from scripts.pipewire_dsp_workloads import (
        WORKLOAD_RAW,
        WORKLOAD_SPECTRAL_FOCUS,
        WORKLOAD_TRANSIENT_EDGE,
        WORKLOAD_HYBRID,
    )
    
    # Branch prediction: order conditions by likelihood
    spectral_centroid = dsp_metrics.get("spectral_centroid_hz", 0.0)
    spectral_flatness = dsp_metrics.get("spectral_flatness", 0.0)
    transient_ratio = dsp_metrics.get("transient_ratio", 0.0)
    band_energy_high = dsp_metrics.get("band_energy_high", 0.0)
    band_energy_mid = dsp_metrics.get("band_energy_mid", 0.0)
    wave_heat = waveprobe_metrics.get("heat", 0.0)
    
    # Spectral-dominant: high centroid, low flatness
    is_spectral_dominant = spectral_centroid > 2000.0 and spectral_flatness < 0.4
    
    # Transient-dominant: high transient ratio, high band energy
    is_transient_dominant = transient_ratio > 3.0 and band_energy_high > 0.4
    
    # Balanced: mid-band dominant, moderate flatness
    is_balanced = band_energy_mid > 0.4 and spectral_flatness > 0.3
    
    # Simple: low wave heat, low complexity
    is_simple = wave_heat < 0.2 and spectral_centroid < 1000.0
    
    if is_spectral_dominant:
        return WORKLOAD_SPECTRAL_FOCUS
    elif is_transient_dominant:
        return WORKLOAD_TRANSIENT_EDGE
    elif is_balanced:
        return WORKLOAD_HYBRID
    elif is_simple:
        return WORKLOAD_RAW
    else:
        return WORKLOAD_HYBRID  # Default to hybrid for unknown patterns


def resolve_method_profile(profile: str) -> List[str]:
    if profile not in METHOD_PROFILES:
        raise ValueError(
            f"Unknown method profile {profile!r}; expected one of {available_method_profiles()}"
        )
    return list(METHOD_PROFILES[profile])


def _encode_bpb(method: str, data: bytes) -> float:
    if not data:
        return 0.0
    if method == "none":
        return 8.0
    if method == "order0":
        counts = [0] * 256
        for b in data:
            counts[b] += 1
        entropy = 0.0
        n = len(data)
        for c in counts:
            if c > 0:
                p = c / n
                entropy -= p * math.log2(p)
        return entropy
    if method == "zlib_fast":
        return len(zlib.compress(data, 1)) * 8 / len(data)
    if method == "zlib":
        return len(zlib.compress(data, 9)) * 8 / len(data)
    if method == "gzip":
        import gzip

        return len(gzip.compress(data, compresslevel=6, mtime=0)) * 8 / len(data)
    if method == "bz2":
        import bz2

        return len(bz2.compress(data, compresslevel=9)) * 8 / len(data)
    if method == "brotli":
        import brotli

        return len(brotli.compress(data, quality=6, lgwin=20)) * 8 / len(data)
    if method == "zstd":
        import zstandard as zstd

        compressor = zstd.ZstdCompressor(level=5)
        return len(compressor.compress(data)) * 8 / len(data)
    if method == "lzma":
        import lzma

        return len(lzma.compress(data, preset=6)) * 8 / len(data)
    return 8.0


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _normalize_qubo_features(
    dsp_metrics: Dict[str, float],
    waveprobe_metrics: Dict[str, float],
    sample_rate_hz: int,
) -> Dict[str, float]:
    nyquist = max(sample_rate_hz / 2.0, 1.0)
    centroid_norm = _clamp01(dsp_metrics.get("spectral_centroid_hz", 0.0) / nyquist)
    transient_norm = _clamp01(dsp_metrics.get("transient_ratio", 0.0) / 4.0)
    flatness_norm = _clamp01(dsp_metrics.get("spectral_flatness", 0.0))
    zcr_norm = _clamp01(dsp_metrics.get("zero_crossing_rate", 0.0))
    low_band = _clamp01(dsp_metrics.get("band_energy_low", 0.0))
    mid_band = _clamp01(dsp_metrics.get("band_energy_mid", 0.0))
    high_band = _clamp01(dsp_metrics.get("band_energy_high", 0.0))
    wave_heat = _clamp01(waveprobe_metrics.get("heat", 0.0))
    wave_comp = _clamp01(waveprobe_metrics.get("compression_sensitivity", 0.0) / 32.0)
    wave_aniso = _clamp01(waveprobe_metrics.get("anisotropy", 0.0) / 8.0)
    return {
        "centroid_norm": centroid_norm,
        "transient_norm": transient_norm,
        "flatness_norm": flatness_norm,
        "zcr_norm": zcr_norm,
        "low_band": low_band,
        "mid_band": mid_band,
        "high_band": high_band,
        "wave_heat": wave_heat,
        "wave_comp": wave_comp,
        "wave_aniso": wave_aniso,
    }


def _build_qubo_candidates(
    methods: List[str],
    features: Dict[str, float],
) -> List[Dict[str, float | str]]:
    feature_weights = {
        "centroid_norm": 0.16,
        "transient_norm": 0.18,
        "flatness_norm": 0.18,
        "zcr_norm": 0.10,
        "low_band": 0.12,
        "mid_band": 0.10,
        "high_band": 0.16,
    }

    candidates: List[Dict[str, float | str]] = []
    wave_pressure = (
        0.5 * features["wave_heat"]
        + 0.3 * features["wave_comp"]
        + 0.2 * features["wave_aniso"]
    )
    for method in methods:
        target = METHOD_SPECS[method]
        mismatch = 0.0
        for key, weight in feature_weights.items():
            mismatch += weight * abs(features[key] - float(target[key]))
        routing_cost = _clamp01(
            0.65 * float(target["complexity"]) + 0.35 * wave_pressure
        )
        memory_cost = _clamp01(
            0.55 * float(target["memory"])
            + 0.25 * features["flatness_norm"]
            + 0.20 * features["mid_band"]
        )
        candidates.append(
            {
                "method": method,
                "e": _clamp01(mismatch),
                "r": routing_cost,
                "m": memory_cost,
            }
        )
    return candidates


def _build_one_hot_qubo_matrix(
    candidates: List[Dict[str, float | str]],
    penalty: float,
    lambda_e: float = 0.50,
    lambda_r: float = 0.30,
    lambda_m: float = 0.20,
) -> Tuple[AnyArray, List[float]]:
    n = len(candidates)
    q = xp.zeros((n, n), dtype=float)
    costs: List[float] = []
    for i, candidate in enumerate(candidates):
        c_i = (
            lambda_e * float(candidate["e"])
            + lambda_r * float(candidate["r"])
            + lambda_m * float(candidate["m"])
        )
        costs.append(c_i)
        q[i, i] = c_i - penalty
    for i in range(n):
        for j in range(i + 1, n):
            q[i, j] = 2.0 * penalty
    return q, costs


def _qubo_energy(q: AnyArray, bits: AnyArray) -> float:
    return float(bits @ q @ bits)


def _one_hot_bits(n: int, active_index: int) -> AnyArray:
    bits = xp.zeros(n, dtype=float)
    bits[active_index] = 1.0
    return bits


def _solve_qubo_exact(q: AnyArray) -> Dict[str, Any]:
    n = int(q.shape[0])
    best_bits: List[int] | None = None
    best_energy = float("inf")
    evaluated_states = 0
    for state in range(1, 1 << n):
        bits = xp.array([(state >> i) & 1 for i in range(n)], dtype=float)
        energy = _qubo_energy(q, bits)
        evaluated_states += 1
        if energy < best_energy:
            best_energy = energy
            best_bits = bits.astype(int).tolist()
    if best_bits is None:
        raise RuntimeError("QUBO solve failed to produce a state")
    active = [idx for idx, bit in enumerate(best_bits) if bit]
    return {
        "solution_bits": best_bits,
        "active_indices": active,
        "energy": best_energy,
        "constraint_satisfied": sum(best_bits) == 1,
        "evaluated_states": evaluated_states,
    }


# =============================================================================
# ADAPTIVE SCALE PROPOSAL REFINEMENT
# =============================================================================
# Inspired by the wavelength-detection concept from:
#   "Resonance MCMC" by Zachary Lafer (github.com/zman007-save/resonance-mcmc)
#   Principle: Detect characteristic spatial scales from accepted move history
#   and bias proposals toward those scales for faster mode discovery.
#
# Adaptation: Applied to discrete one-hot QUBO instead of continuous space.
#   - Track accepted index-space distances
#   - Detect median characteristic distance
#   - Bias proposals toward that distance and its harmonics
# =============================================================================

from dataclasses import dataclass, field


@dataclass
class AdaptiveProposalState:
    """Track proposal statistics for adaptive scale detection in QUBO annealing."""

    # History of accepted jump distances (in index space)
    accepted_distances: List[int] = field(default_factory=list)
    # History window size for median estimation
    window_size: int = 20
    # Minimum samples before adaptation activates
    min_samples: int = 5

    def observe_accepted_move(self, from_index: int, to_index: int):
        """Record an accepted move distance."""
        distance = abs(to_index - from_index)
        self.accepted_distances.append(distance)
        if len(self.accepted_distances) > self.window_size:
            self.accepted_distances.pop(0)

    def detect_scale(self) -> Optional[int]:
        """Detect characteristic jump scale from history using median.

        Returns None if insufficient samples.
        """
        if len(self.accepted_distances) < self.min_samples:
            return None
        return int(xp.median(xp.array(self.accepted_distances)))

    def get_scale_multiplier(self, current_index: int, candidate_index: int) -> float:
        """Compute proposal weight multiplier based on scale alignment.

        Returns 1.0 for neutral, >1.0 to favor, <1.0 to disfavor.
        """
        scale = self.detect_scale()
        if scale is None:
            return 1.0

        distance = abs(candidate_index - current_index)
        if distance == 0:
            return 0.5  # Disfavor staying in place

        # Check alignment with scale and its harmonics
        harmonic_boost = 0.0
        for harmonic in [1, 2, 3]:
            target_dist = scale * harmonic
            # Gaussian-like falloff around target
            diff = abs(distance - target_dist) / max(target_dist * 0.3, 1.0)
            boost = float(xp.exp(-diff ** 2))
            harmonic_boost = max(harmonic_boost, boost)

        # Return multiplier: 1.0 to 2.0
        return 1.0 + harmonic_boost


def _guided_initial_index(unary_costs: List[float]) -> int:
    return min(range(len(unary_costs)), key=lambda idx: unary_costs[idx])


def _weighted_candidate_indices(
    unary_costs: List[float],
    exclude_index: int,
    guidance: str,
    active_index: int = 0,
    adaptive_state: Optional[AdaptiveProposalState] = None,
) -> Tuple[AnyArray, AnyArray]:
    indices = xp.array([idx for idx in range(len(unary_costs)) if idx != exclude_index], dtype=int)
    if indices.size == 0:
        return indices, xp.array([], dtype=float)

    # Base weights from guidance strategy
    if guidance == "unguided":
        base_weights = xp.ones(indices.size, dtype=float)
    elif guidance == "adaptive_scale":
        # Use adaptive scale bias only (no cost weighting)
        base_weights = xp.ones(indices.size, dtype=float)
    else:
        # Cost-weighted ("dsp_guided" or default)
        max_cost = max(unary_costs)
        min_cost = min(unary_costs)
        spread = max(max_cost - min_cost, 1e-6)
        base_weights = xp.array(
            [1.0 + (max_cost - unary_costs[idx]) / spread for idx in indices],
            dtype=float,
        )

    # Apply adaptive scale multipliers if state provided
    if adaptive_state is not None:
        multipliers = xp.array([
            adaptive_state.get_scale_multiplier(active_index, int(idx))
            for idx in indices
        ], dtype=float)
        base_weights = base_weights * multipliers

    # Normalize
    weights = base_weights / xp.sum(base_weights)
    return indices, weights


def _solve_qubo_anneal(
    q: AnyArray,
    unary_costs: List[float],
    seed: int,
    steps: int,
    temp_start: float,
    temp_end: float,
    guidance: str,
) -> Dict[str, Any]:
    n = int(q.shape[0])
    rng = xp.random.default_rng(seed)
    safe_temp_start = max(float(temp_start), 1e-6)
    safe_temp_end = max(float(temp_end), 1e-6)
    if guidance == "dsp_guided":
        initial_index = _guided_initial_index(unary_costs)
    else:
        initial_index = int(rng.integers(0, n))
    current_bits = _one_hot_bits(n, initial_index)
    current_energy = _qubo_energy(q, current_bits)
    best_bits = current_bits.copy()
    best_energy = current_energy
    accepted_moves = 0
    improved_moves = 0

    # Initialize adaptive scale detection if enabled
    use_adaptive = guidance in ("adaptive_scale", "dsp_guided_adaptive")
    adaptive_state = AdaptiveProposalState(window_size=min(30, steps)) if use_adaptive else None

    for step in range(max(1, steps)):
        if steps <= 1:
            temperature = safe_temp_end
        else:
            alpha = step / (steps - 1)
            temperature = safe_temp_start * (
                (safe_temp_end / safe_temp_start) ** alpha
            )

        proposal_bits = current_bits.copy()
        active_indices = xp.flatnonzero(proposal_bits > 0.5)
        active_index = int(active_indices[0]) if active_indices.size else initial_index
        weighted_indices, weights = _weighted_candidate_indices(
            unary_costs,
            active_index,
            guidance=guidance,
            active_index=active_index,
            adaptive_state=adaptive_state,
        )
        if weighted_indices.size:
            target_index = int(rng.choice(weighted_indices, p=weights))
            proposal_bits[active_index] = 0.0
            proposal_bits[target_index] = 1.0
        else:
            flip_index = int(rng.integers(0, n))
            proposal_bits[flip_index] = 1.0 - proposal_bits[flip_index]

        proposal_energy = _qubo_energy(q, proposal_bits)
        delta = proposal_energy - current_energy
        if delta <= 0.0:
            accept = True
        else:
            accept = bool(rng.random() < math.exp(-delta / max(temperature, 1e-9)))

        if accept:
            accepted_moves += 1
            if delta < 0.0:
                improved_moves += 1
            # Record accepted move for adaptive scale detection
            if adaptive_state is not None and weighted_indices.size:
                adaptive_state.observe_accepted_move(active_index, target_index)
            current_bits = proposal_bits
            current_energy = proposal_energy
            if int(xp.sum(current_bits)) == 1 and current_energy < best_energy:
                best_bits = current_bits.copy()
                best_energy = current_energy

    best_bits_list = best_bits.astype(int).tolist()
    active = [idx for idx, bit in enumerate(best_bits_list) if bit]
    # Get final detected scale for diagnostics
    final_scale = adaptive_state.detect_scale() if adaptive_state else None

    return {
        "solution_bits": best_bits_list,
        "active_indices": active,
        "energy": best_energy,
        "constraint_satisfied": sum(best_bits_list) == 1,
        "seed": seed,
        "steps": max(1, steps),
        "accepted_moves": accepted_moves,
        "improved_moves": improved_moves,
        "accepted_ratio": accepted_moves / max(1, steps),
        "initial_index": initial_index,
        "initial_energy": _qubo_energy(q, _one_hot_bits(n, initial_index)),
        "guidance": guidance,
        "adaptive_scale": final_scale,
    }


def _candidate_cost_rows(
    candidates: List[Dict[str, float | str]],
    unary_costs: List[float],
) -> List[Dict[str, float | str]]:
    return [
        {
            "method": str(candidate["method"]),
            "e": float(candidate["e"]),
            "r": float(candidate["r"]),
            "m": float(candidate["m"]),
            "unary_cost": unary_costs[idx],
        }
        for idx, candidate in enumerate(candidates)
    ]


def _run_qubo_method_search(
    methods: List[str],
    dsp_metrics: Dict[str, float],
    waveprobe_metrics: Dict[str, float],
    sample_rate_hz: int,
    solver: str,
    seed: int,
    anneal_steps: int,
    anneal_temp_start: float,
    anneal_temp_end: float,
    anneal_guidance: str,
    benchmark_guidance_ablation: bool,
    collect_exact_reference: bool,
) -> Dict[str, Any]:
    features = _normalize_qubo_features(
        dsp_metrics=dsp_metrics,
        waveprobe_metrics=waveprobe_metrics,
        sample_rate_hz=sample_rate_hz,
    )
    candidates = _build_qubo_candidates(methods, features)
    penalty = 1.25
    q, unary_costs = _build_one_hot_qubo_matrix(candidates, penalty=penalty)
    candidate_costs = _candidate_cost_rows(candidates, unary_costs)

    exact_reference_available = collect_exact_reference or solver == "exact"
    exact_solution: Dict[str, Any] | None = None
    exact_solve_time_ms: float | None = None
    exact_method: str | None = None
    if exact_reference_available:
        exact_start = time.perf_counter()
        exact_solution = _solve_qubo_exact(q)
        exact_solve_time_ms = (time.perf_counter() - exact_start) * 1000.0
        exact_index = (
            exact_solution["active_indices"][0]
            if exact_solution["active_indices"]
            else _guided_initial_index(unary_costs)
        )
        exact_method = str(candidates[exact_index]["method"])

    if solver == "anneal":
        solve_start = time.perf_counter()
        solved = _solve_qubo_anneal(
            q=q,
            unary_costs=unary_costs,
            seed=seed,
            steps=anneal_steps,
            temp_start=anneal_temp_start,
            temp_end=anneal_temp_end,
            guidance=anneal_guidance,
        )
        solve_time_ms = (time.perf_counter() - solve_start) * 1000.0
        active_index = solved["active_indices"][0] if solved["active_indices"] else _guided_initial_index(unary_costs)
        selected_method = str(candidates[active_index]["method"])
        initial_index = int(solved["initial_index"])
        initial_method = str(candidates[initial_index]["method"])
        benchmark = {
            "exact_reference_method": exact_method,
            "exact_reference_energy": (
                exact_solution["energy"] if exact_solution is not None else None
            ),
            "exact_reference_solve_time_ms": exact_solve_time_ms,
            "exact_reference_evaluated_states": (
                exact_solution["evaluated_states"] if exact_solution is not None else None
            ),
            "exact_match": (
                selected_method == exact_method if exact_method is not None else None
            ),
            "energy_gap_vs_exact": (
                solved["energy"] - exact_solution["energy"]
                if exact_solution is not None
                else None
            ),
        }
        guidance_benchmark: Dict[str, Any] | None = None
        if benchmark_guidance_ablation:
            alt_guidance = "unguided" if anneal_guidance == "dsp_guided" else "dsp_guided"
            alt_start = time.perf_counter()
            alt_solved = _solve_qubo_anneal(
                q=q,
                unary_costs=unary_costs,
                seed=seed,
                steps=anneal_steps,
                temp_start=anneal_temp_start,
                temp_end=anneal_temp_end,
                guidance=alt_guidance,
            )
            alt_solve_time_ms = (time.perf_counter() - alt_start) * 1000.0
            alt_index = (
                alt_solved["active_indices"][0]
                if alt_solved["active_indices"]
                else _guided_initial_index(unary_costs)
            )
            alt_method = str(candidates[alt_index]["method"])
            guidance_benchmark = {
                "alternative_guidance": alt_guidance,
                "selected_method": alt_method,
                "energy": alt_solved["energy"],
                "exact_match": alt_method == exact_method if exact_method is not None else None,
                "energy_gap_vs_exact": (
                    alt_solved["energy"] - exact_solution["energy"]
                    if exact_solution is not None
                    else None
                ),
                "solve_time_ms": alt_solve_time_ms,
                "accepted_ratio": alt_solved["accepted_ratio"],
                "initial_method": str(candidates[int(alt_solved["initial_index"])]["method"]),
            }
        solver_stats = {
            "steps": solved["steps"],
            "accepted_moves": solved["accepted_moves"],
            "improved_moves": solved["improved_moves"],
            "accepted_ratio": solved["accepted_ratio"],
            "initial_method": initial_method,
            "initial_energy": solved["initial_energy"],
            "seed": solved["seed"],
            "guidance": solved["guidance"],
        }
        solver_name = "simulated_annealing"
    else:
        solve_start = time.perf_counter()
        solved = _solve_qubo_exact(q)
        solve_time_ms = (time.perf_counter() - solve_start) * 1000.0
        active_index = solved["active_indices"][0] if solved["active_indices"] else _guided_initial_index(unary_costs)
        selected_method = str(candidates[active_index]["method"])
        benchmark = {
            "exact_reference_method": exact_method,
            "exact_reference_energy": (
                exact_solution["energy"] if exact_solution is not None else solved["energy"]
            ),
            "exact_reference_solve_time_ms": exact_solve_time_ms,
            "exact_reference_evaluated_states": (
                exact_solution["evaluated_states"] if exact_solution is not None else solved["evaluated_states"]
            ),
            "exact_match": True,
            "energy_gap_vs_exact": 0.0,
        }
        solver_stats = {
            "steps": solved["evaluated_states"],
            "accepted_moves": solved["evaluated_states"],
            "improved_moves": solved["evaluated_states"],
            "accepted_ratio": 1.0,
            "initial_method": exact_method,
            "initial_energy": exact_solution["energy"],
            "seed": seed,
            "guidance": "n/a",
        }
        guidance_benchmark = None
        solver_name = "exact_one_hot_enumeration"

    return {
        "triggered": True,
        "solver": solver_name,
        "selected_method": selected_method,
        "selected_index": active_index,
        "energy": solved["energy"],
        "solution_bits": solved["solution_bits"],
        "constraint_satisfied": solved["constraint_satisfied"],
        "solve_time_ms": solve_time_ms,
        "penalty": penalty,
        "features": features,
        "candidate_costs": candidate_costs,
        "matrix_upper_triangular": [
            [float(q[i, j]) for j in range(i, q.shape[1])]
            for i in range(q.shape[0])
        ],
        "benchmark": benchmark,
        "solver_stats": solver_stats,
        "guidance_benchmark": guidance_benchmark,
    }


def _capture_with_pipewire(
    output_wav: Path,
    duration_s: float,
    rate: int,
    channels: int,
    fmt: str,
    latency: str,
    target: str | None,
) -> None:
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    sample_count = max(1, int(duration_s * rate))
    cmd = [
        "pw-record",
        "--container",
        "wav",
        "--rate",
        str(rate),
        "--channels",
        str(channels),
        "--format",
        fmt,
        "--latency",
        latency,
        "--sample-count",
        str(sample_count),
    ]
    if target:
        cmd.extend(["--target", target])
    cmd.append(str(output_wav))
    subprocess.run(cmd, check=True)


def _read_wav_pcm(path: Path) -> Dict[str, Any]:
    with wave.open(str(path), "rb") as wf:
        params = {
            "channels": wf.getnchannels(),
            "sample_width_bytes": wf.getsampwidth(),
            "sample_rate_hz": wf.getframerate(),
            "n_frames": wf.getnframes(),
            "duration_s": wf.getnframes() / max(wf.getframerate(), 1),
        }
        frames = wf.readframes(wf.getnframes())
    return {"params": params, "pcm_bytes": frames}


def _build_audio_dag(
    pcm_bytes: bytes,
    chunk_size: int,
    stride: int,
    max_states: int,
) -> Dict[str, Any]:
    ts = datetime.now(timezone.utc)
    chunks = UCP.chunk_corpus(pcm_bytes, chunk_size=chunk_size, stride=stride)
    dag: Dict[str, Any] = {}
    for offset, chunk_bytes in chunks[:max_states]:
        sha = UCP.compute_sha256(chunk_bytes)
        state_id = f"audio_capture:{offset:08x}:{sha[:16]}"
        dag[state_id] = UCP.CorpusState(
            sha256=sha,
            timestamp=ts,
            release_id="audio_capture",
            chunk_offset=offset,
            chunk_bytes=chunk_bytes,
        )
    return dag


def run_chain(
    wav_path: Path,
    chunk_size: int,
    stride: int,
    max_states: int,
    low_mi_threshold: float,
    high_mi_threshold: float,
    dsp_workload: str,
    method_profile: str = "baseline",
    qubo_solver: str = "exact",
    qubo_anneal_steps: int = 32,
    qubo_anneal_temp_start: float = 0.50,
    qubo_anneal_temp_end: float = 0.05,
    qubo_anneal_guidance: str = "dsp_guided",
    qubo_benchmark_guidance_ablation: bool = False,
    qubo_collect_exact_reference: bool = True,
    hybrid_dsp_workload: bool = False,
) -> Dict[str, Any]:
    wav_data = _read_wav_pcm(wav_path)
    pcm_bytes = wav_data["pcm_bytes"]
    dag = _build_audio_dag(
        pcm_bytes=pcm_bytes,
        chunk_size=chunk_size,
        stride=stride,
        max_states=max_states,
    )
    if not dag:
        raise RuntimeError("No audio chunks available for analysis")

    analysis_dag: Dict[str, Any] = {}
    dsp_by_state: Dict[str, Dict[str, float]] = {}
    for state_id, state in dag.items():
        analysis_bytes, dsp_metrics = apply_dsp_workload(
            state.chunk_bytes,
            sample_width_bytes=wav_data["params"]["sample_width_bytes"],
            channels=wav_data["params"]["channels"],
            sample_rate_hz=wav_data["params"]["sample_rate_hz"],
            workload=dsp_workload,
        )
        analysis_sha = UCP.compute_sha256(analysis_bytes)
        analysis_dag[state_id] = UCP.CorpusState(
            sha256=analysis_sha,
            timestamp=state.timestamp,
            release_id=state.release_id,
            chunk_offset=state.chunk_offset,
            chunk_bytes=analysis_bytes,
        )
        dsp_by_state[state_id] = dsp_metrics

    mu, sigma = UCP.compute_feature_stats(analysis_dag)
    mi_signal = MISignal(
        low_mi_threshold=low_mi_threshold,
        high_mi_threshold=high_mi_threshold,
    )
    methods = resolve_method_profile(method_profile)

    per_chunk: List[Dict[str, Any]] = []
    method_counts: Dict[str, int] = {m: 0 for m in methods + ["none"]}
    qubo_method_counts: Dict[str, int] = {m: 0 for m in methods}
    dsp_workload_counts: Dict[str, int] = {}
    rich_chunks = 0
    cheap_chunks = 0
    qubo_invocations = 0
    qubo_method_overrides = 0
    qubo_exact_matches = 0
    wave_heat_total = 0.0
    wave_compsens_total = 0.0
    mi_actual_total = 0.0
    yield_total = 0.0
    dsp_centroid_total = 0.0
    dsp_flatness_total = 0.0
    dsp_transient_total = 0.0
    dsp_zcr_total = 0.0
    dsp_low_total = 0.0
    dsp_mid_total = 0.0
    dsp_high_total = 0.0
    qubo_solve_time_total = 0.0
    qubo_exact_solve_time_total = 0.0
    qubo_energy_gap_total = 0.0
    qubo_accepted_ratio_total = 0.0
    qubo_alt_exact_matches = 0
    qubo_alt_solve_time_total = 0.0
    qubo_alt_energy_gap_total = 0.0
    qubo_alt_accepted_ratio_total = 0.0

    for idx, (state_id, state) in enumerate(analysis_dag.items()):
        raw_state = dag[state_id]
        dsp_metrics = dsp_by_state[state_id]
        state_seed = int(
            hashlib.sha256(f"{state_id}:{dsp_workload}".encode("utf-8")).hexdigest()[:8],
            16,
        )
        wp = UCP.waveprobe(state.chunk_bytes, mu, sigma, seed=state_seed)
        
        # Hybrid DSP workload selection for energy efficiency
        if hybrid_dsp_workload:
            selected_workload = _select_hybrid_dsp_workload(dsp_metrics, wp)
            # Re-apply DSP with selected workload
            analysis_bytes, dsp_metrics = apply_dsp_workload(
                raw_state.chunk_bytes,
                sample_width_bytes=wav_data["params"]["sample_width_bytes"],
                channels=wav_data["params"]["channels"],
                sample_rate_hz=wav_data["params"]["sample_rate_hz"],
                workload=selected_workload,
            )
            analysis_sha = UCP.compute_sha256(analysis_bytes)
            analysis_dag[state_id] = UCP.CorpusState(
                sha256=analysis_sha,
                timestamp=state.timestamp,
                release_id=state.release_id,
                chunk_offset=state.chunk_offset,
                chunk_bytes=analysis_bytes,
            )
            dsp_by_state[state_id] = dsp_metrics
        else:
            selected_workload = dsp_workload
        
        # Track DSP workload selection
        dsp_workload_counts[selected_workload] = dsp_workload_counts.get(selected_workload, 0) + 1
        
        z = extract_mi_features(state.chunk_bytes)
        route = mi_signal.route(z, state.chunk_bytes, methods, _encode_bpb)
        qubo_result: Dict[str, Any] = {"triggered": False}

        selected_method = route["method"]
        selected_bpb = route["actual_bpb"]
        selected_mi = route["mi_actual"]
        if route["decision_class"] == "rich":
            qubo_result = _run_qubo_method_search(
                methods=methods,
                dsp_metrics=dsp_metrics,
                waveprobe_metrics=wp,
                sample_rate_hz=wav_data["params"]["sample_rate_hz"],
                solver=qubo_solver,
                seed=state_seed,
                anneal_steps=qubo_anneal_steps,
                anneal_temp_start=qubo_anneal_temp_start,
                anneal_temp_end=qubo_anneal_temp_end,
                anneal_guidance=qubo_anneal_guidance,
                benchmark_guidance_ablation=qubo_benchmark_guidance_ablation,
                collect_exact_reference=qubo_collect_exact_reference,
            )
            qubo_invocations += 1
            qubo_method = qubo_result["selected_method"]
            qubo_method_counts[qubo_method] = qubo_method_counts.get(qubo_method, 0) + 1
            if qubo_method != route["method"]:
                qubo_method_overrides += 1
            if qubo_result["benchmark"]["exact_match"] is True:
                qubo_exact_matches += 1
            qubo_solve_time_total += float(qubo_result["solve_time_ms"])
            if qubo_result["benchmark"]["exact_reference_solve_time_ms"] is not None:
                qubo_exact_solve_time_total += float(
                    qubo_result["benchmark"]["exact_reference_solve_time_ms"]
                )
            if qubo_result["benchmark"]["energy_gap_vs_exact"] is not None:
                qubo_energy_gap_total += float(
                    qubo_result["benchmark"]["energy_gap_vs_exact"]
                )
            qubo_accepted_ratio_total += float(
                qubo_result["solver_stats"]["accepted_ratio"]
            )
            alt_guidance = qubo_result.get("guidance_benchmark")
            if alt_guidance:
                if alt_guidance["exact_match"] is True:
                    qubo_alt_exact_matches += 1
                qubo_alt_solve_time_total += float(alt_guidance["solve_time_ms"])
                if alt_guidance["energy_gap_vs_exact"] is not None:
                    qubo_alt_energy_gap_total += float(alt_guidance["energy_gap_vs_exact"])
                qubo_alt_accepted_ratio_total += float(alt_guidance["accepted_ratio"])
            selected_method = qubo_method
            selected_bpb = _encode_bpb(selected_method, state.chunk_bytes)
            selected_mi = route["baseline_bpb"] - selected_bpb

        method = selected_method
        method_counts[method] = method_counts.get(method, 0) + 1
        if route["decision_class"] == "rich":
            rich_chunks += 1
        elif route["decision_class"] == "cheap":
            cheap_chunks += 1

        wave_heat_total += wp["heat"]
        wave_compsens_total += wp["compression_sensitivity"]
        mi_actual_total += selected_mi
        yield_total += route["structure_yield"]
        dsp_centroid_total += dsp_metrics.get("spectral_centroid_hz", 0.0)
        dsp_flatness_total += dsp_metrics.get("spectral_flatness", 0.0)
        dsp_transient_total += dsp_metrics.get("transient_ratio", 0.0)
        dsp_zcr_total += dsp_metrics.get("zero_crossing_rate", 0.0)
        dsp_low_total += dsp_metrics.get("band_energy_low", 0.0)
        dsp_mid_total += dsp_metrics.get("band_energy_mid", 0.0)
        dsp_high_total += dsp_metrics.get("band_energy_high", 0.0)

        per_chunk.append(
            {
                "state_id": state_id,
                "chunk_index": idx,
                "offset": raw_state.chunk_offset,
                "raw_sha256_prefix": raw_state.sha256[:16],
                "analysis_sha256_prefix": state.sha256[:16],
                "decision_class": route["decision_class"],
                "method": method,
                "mi_actual": selected_mi,
                "mi_predicted": route["mi_predicted"],
                "mi_surprise": route["mi_surprise"],
                "structure_yield": route["structure_yield"],
                "baseline_bpb": route["baseline_bpb"],
                "actual_bpb": selected_bpb,
                "mi_router_method": route["method"],
                "qubo_enabled": qubo_result["triggered"],
                "qubo_solver": qubo_result.get("solver"),
                "qubo_guidance": qubo_result.get("solver_stats", {}).get("guidance"),
                "qubo_selected_method": qubo_result.get("selected_method"),
                "qubo_energy": qubo_result.get("energy"),
                "qubo_solution_bits": qubo_result.get("solution_bits"),
                "qubo_constraint_satisfied": qubo_result.get("constraint_satisfied"),
                "qubo_solve_time_ms": qubo_result.get("solve_time_ms"),
                "qubo_candidate_costs": qubo_result.get("candidate_costs"),
                "qubo_features": qubo_result.get("features"),
                "qubo_initial_method": qubo_result.get("solver_stats", {}).get("initial_method"),
                "qubo_initial_energy": qubo_result.get("solver_stats", {}).get("initial_energy"),
                "qubo_steps": qubo_result.get("solver_stats", {}).get("steps"),
                "qubo_accepted_moves": qubo_result.get("solver_stats", {}).get("accepted_moves"),
                "qubo_improved_moves": qubo_result.get("solver_stats", {}).get("improved_moves"),
                "qubo_accepted_ratio": qubo_result.get("solver_stats", {}).get("accepted_ratio"),
                "qubo_seed": qubo_result.get("solver_stats", {}).get("seed"),
                "qubo_exact_reference_method": qubo_result.get("benchmark", {}).get("exact_reference_method"),
                "qubo_exact_reference_energy": qubo_result.get("benchmark", {}).get("exact_reference_energy"),
                "qubo_exact_reference_solve_time_ms": qubo_result.get("benchmark", {}).get("exact_reference_solve_time_ms"),
                "qubo_exact_match": qubo_result.get("benchmark", {}).get("exact_match"),
                "qubo_energy_gap_vs_exact": qubo_result.get("benchmark", {}).get("energy_gap_vs_exact"),
                "qubo_guidance_alternative": (
                    qubo_result.get("guidance_benchmark") or {}
                ).get("alternative_guidance"),
                "qubo_guidance_alternative_method": (
                    qubo_result.get("guidance_benchmark") or {}
                ).get("selected_method"),
                "qubo_guidance_alternative_exact_match": (
                    qubo_result.get("guidance_benchmark") or {}
                ).get("exact_match"),
                "qubo_guidance_alternative_energy_gap_vs_exact": (
                    qubo_result.get("guidance_benchmark") or {}
                ).get("energy_gap_vs_exact"),
                "qubo_guidance_alternative_solve_time_ms": (
                    qubo_result.get("guidance_benchmark") or {}
                ).get("solve_time_ms"),
                "qubo_guidance_alternative_accepted_ratio": (
                    qubo_result.get("guidance_benchmark") or {}
                ).get("accepted_ratio"),
                "waveprobe_sensitivity": wp["sensitivity"],
                "waveprobe_compression_sensitivity": wp["compression_sensitivity"],
                "waveprobe_anisotropy": wp["anisotropy"],
                "waveprobe_heat": wp["heat"],
                "dsp_workload": dsp_workload,
                "dsp_rms_ratio": dsp_metrics.get("rms_ratio", 1.0),
                "dsp_zero_crossing_rate": dsp_metrics.get("zero_crossing_rate", 0.0),
                "dsp_spectral_centroid_hz": dsp_metrics.get("spectral_centroid_hz", 0.0),
                "dsp_spectral_flatness": dsp_metrics.get("spectral_flatness", 0.0),
                "dsp_dominant_freq_hz": dsp_metrics.get("dominant_freq_hz", 0.0),
                "dsp_transient_ratio": dsp_metrics.get("transient_ratio", 0.0),
                "dsp_band_energy_low": dsp_metrics.get("band_energy_low", 0.0),
                "dsp_band_energy_mid": dsp_metrics.get("band_energy_mid", 0.0),
                "dsp_band_energy_high": dsp_metrics.get("band_energy_high", 0.0),
                "dsp_centroid_shift_hz": dsp_metrics.get("centroid_shift_hz", 0.0),
                "dsp_transient_shift": dsp_metrics.get("transient_shift", 0.0),
                "dsp_workload": selected_workload,
            }
        )

    n = len(per_chunk)
    per_chunk_sorted = sorted(
        per_chunk,
        key=lambda item: (
            item["mi_actual"],
            item["waveprobe_heat"],
            item["waveprobe_compression_sensitivity"],
        ),
        reverse=True,
    )

    return {
        "schema_version": "pipewire.waveprobe.compression.v1",
        "captured_wav": str(wav_path),
        "wav_params": wav_data["params"],
        "chunking": {
            "chunk_size_bytes": chunk_size,
            "stride_bytes": stride,
            "n_chunks": n,
        },
        "mi_router_config": {
            "low_mi_threshold": low_mi_threshold,
            "high_mi_threshold": high_mi_threshold,
        },
        "dsp_frontend": {
            "workload": dsp_workload,
        },
        "qubo_config": {
            "method_profile": method_profile,
            "n_methods": len(methods),
            "solver": qubo_solver,
            "anneal_steps": qubo_anneal_steps,
            "anneal_temp_start": qubo_anneal_temp_start,
            "anneal_temp_end": qubo_anneal_temp_end,
            "anneal_guidance": qubo_anneal_guidance,
            "benchmark_guidance_ablation": qubo_benchmark_guidance_ablation,
            "collect_exact_reference": qubo_collect_exact_reference,
        },
        "summary": {
            "avg_mi_actual": mi_actual_total / n,
            "avg_structure_yield": yield_total / n,
            "avg_waveprobe_heat": wave_heat_total / n,
            "avg_waveprobe_compression_sensitivity": wave_compsens_total / n,
            "avg_dsp_spectral_centroid_hz": dsp_centroid_total / n,
            "avg_dsp_spectral_flatness": dsp_flatness_total / n,
            "avg_dsp_transient_ratio": dsp_transient_total / n,
            "avg_dsp_zero_crossing_rate": dsp_zcr_total / n,
            "avg_dsp_band_energy_low": dsp_low_total / n,
            "avg_dsp_band_energy_mid": dsp_mid_total / n,
            "avg_dsp_band_energy_high": dsp_high_total / n,
            "rich_chunks": rich_chunks,
            "cheap_chunks": cheap_chunks,
            "qubo_invocations": qubo_invocations,
            "qubo_method_overrides": qubo_method_overrides,
            "qubo_exact_matches": qubo_exact_matches,
            "qubo_exact_match_rate": (
                qubo_exact_matches / qubo_invocations
                if qubo_invocations and (qubo_collect_exact_reference or qubo_solver == "exact")
                else None
            ),
            "avg_qubo_solve_time_ms": (
                qubo_solve_time_total / qubo_invocations if qubo_invocations else 0.0
            ),
            "avg_qubo_exact_reference_solve_time_ms": (
                qubo_exact_solve_time_total / qubo_invocations
                if qubo_invocations and (qubo_collect_exact_reference or qubo_solver == "exact")
                else None
            ),
            "avg_qubo_energy_gap_vs_exact": (
                qubo_energy_gap_total / qubo_invocations
                if qubo_invocations and (qubo_collect_exact_reference or qubo_solver == "exact")
                else None
            ),
            "avg_qubo_accepted_ratio": (
                qubo_accepted_ratio_total / qubo_invocations
                if qubo_invocations
                else 0.0
            ),
            "alt_guidance_exact_matches": qubo_alt_exact_matches,
            "alt_guidance_exact_match_rate": (
                qubo_alt_exact_matches / qubo_invocations
                if qubo_invocations
                and qubo_benchmark_guidance_ablation
                and (qubo_collect_exact_reference or qubo_solver == "exact")
                else None
            ),
            "avg_alt_guidance_solve_time_ms": (
                qubo_alt_solve_time_total / qubo_invocations
                if qubo_invocations and qubo_benchmark_guidance_ablation
                else None
            ),
            "avg_alt_guidance_energy_gap_vs_exact": (
                qubo_alt_energy_gap_total / qubo_invocations
                if qubo_invocations
                and qubo_benchmark_guidance_ablation
                and (qubo_collect_exact_reference or qubo_solver == "exact")
                else None
            ),
            "avg_alt_guidance_accepted_ratio": (
                qubo_alt_accepted_ratio_total / qubo_invocations
                if qubo_invocations and qubo_benchmark_guidance_ablation
                else None
            ),
            "method_counts": method_counts,
            "qubo_method_counts": qubo_method_counts,
            "dsp_workload_counts": dsp_workload_counts,
            "mi_signal_stats": mi_signal.get_stats(),
        },
        "top_chunks": per_chunk_sorted[:10],
        "chunks": per_chunk,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="PipeWire -> compression -> waveprobe chain harness"
    )
    parser.add_argument("--input-wav", type=Path, help="Analyze an existing WAV file")
    parser.add_argument(
        "--capture-seconds",
        type=float,
        default=2.0,
        help="Duration for PipeWire capture when --input-wav is omitted",
    )
    parser.add_argument("--rate", type=int, default=48000)
    parser.add_argument("--channels", type=int, default=1)
    parser.add_argument("--format", default="s16")
    parser.add_argument("--latency", default="50ms")
    parser.add_argument("--target", default=None, help="Optional PipeWire target node")
    parser.add_argument("--chunk-size-bytes", type=int, default=4096)
    parser.add_argument("--stride-bytes", type=int, default=2048)
    parser.add_argument("--max-states", type=int, default=128)
    parser.add_argument("--low-mi-threshold", type=float, default=0.5)
    parser.add_argument("--high-mi-threshold", type=float, default=3.0)
    parser.add_argument(
        "--dsp-workload",
        default="raw",
        choices=list(available_workloads()),
        help="DSP-like front-end transform applied before MI routing and waveprobe scoring",
    )
    parser.add_argument(
        "--method-profile",
        default="baseline",
        choices=list(available_method_profiles()),
        help="Compression method profile used for MI routing and QUBO search",
    )
    parser.add_argument(
        "--qubo-solver",
        default="exact",
        choices=("exact", "anneal"),
        help="QUBO solver used on rich chunks",
    )
    parser.add_argument(
        "--qubo-anneal-steps",
        type=int,
        default=32,
        help="Number of simulated annealing steps when --qubo-solver=anneal",
    )
    parser.add_argument(
        "--qubo-anneal-temp-start",
        type=float,
        default=0.50,
        help="Starting temperature for simulated annealing",
    )
    parser.add_argument(
        "--qubo-anneal-temp-end",
        type=float,
        default=0.05,
        help="Ending temperature for simulated annealing",
    )
    parser.add_argument(
        "--qubo-anneal-guidance",
        default="dsp_guided",
        choices=("dsp_guided", "unguided"),
        help="Proposal/init guidance mode for simulated annealing",
    )
    parser.add_argument(
        "--qubo-benchmark-guidance-ablation",
        action="store_true",
        help="Also run the opposite annealing guidance mode for side-by-side benchmarking",
    )
    parser.add_argument(
        "--skip-exact-reference",
        action="store_true",
        help="Skip exact-reference benchmarking on rich chunks to reduce end-to-end runtime",
    )
    parser.add_argument(
        "--hybrid-dsp-workload",
        action="store_true",
        help="Enable hybrid DSP workload selection for energy-efficient QUBO solves",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=REPO_ROOT / "out" / "pipewire_waveprobe_chain",
    )
    args = parser.parse_args()

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = args.out_dir / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.input_wav:
        wav_path = args.input_wav.resolve()
    else:
        wav_path = out_dir / "capture.wav"
        _capture_with_pipewire(
            output_wav=wav_path,
            duration_s=args.capture_seconds,
            rate=args.rate,
            channels=args.channels,
            fmt=args.format,
            latency=args.latency,
            target=args.target,
        )

    result = run_chain(
        wav_path=wav_path,
        chunk_size=args.chunk_size_bytes,
        stride=args.stride_bytes,
        max_states=args.max_states,
        low_mi_threshold=args.low_mi_threshold,
        high_mi_threshold=args.high_mi_threshold,
        dsp_workload=args.dsp_workload,
        method_profile=args.method_profile,
        qubo_solver=args.qubo_solver,
        qubo_anneal_steps=args.qubo_anneal_steps,
        qubo_anneal_temp_start=args.qubo_anneal_temp_start,
        qubo_anneal_temp_end=args.qubo_anneal_temp_end,
        qubo_anneal_guidance=args.qubo_anneal_guidance,
        qubo_benchmark_guidance_ablation=args.qubo_benchmark_guidance_ablation,
        qubo_collect_exact_reference=not args.skip_exact_reference,
        hybrid_dsp_workload=args.hybrid_dsp_workload,
    )

    result["run_id"] = run_id
    result["generated_utc"] = datetime.now(timezone.utc).isoformat()
    result["capture_mode"] = "file" if args.input_wav else "pipewire"

    json_path = out_dir / "summary.json"
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)

    print(json.dumps(result["summary"], indent=2))
    print(f"\n[+] Summary written to {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
