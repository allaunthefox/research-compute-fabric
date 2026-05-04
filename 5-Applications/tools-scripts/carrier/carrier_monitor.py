#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
CarrierState Standing Wave Monitor for Hyperfluid Causal Pressure Model

Detects perturbations in the causal pressure dynamics via a self-reinforcing
standing wave (carrier_state) that locks onto baseline and fires when the hyperfluid
is disturbed beyond recovery threshold.

The "woman in the box" trick: a stable reference state that remains invisible
until the model deviates significantly, at which point the carrier_state becomes
manifest as an anomaly signal.
"""

import json
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class CarrierStateState:
    """Standing wave state in causal pressure space."""
    amplitude: float  # Current carrier_state amplitude (0.0 = no disturbance)
    phase: float      # Phase offset (0.0 = synchronized with baseline)
    coherence: float  # Coherence with baseline (1.0 = perfect lock)
    decay_rate: float # Exponential decay if undisturbed


def gaussian_kernel(x: float, sigma: float = 1.0) -> float:
    """Smooth kernel for baseline estimation."""
    import math
    return math.exp(-(x * x) / (2 * sigma * sigma)) / (sigma * math.sqrt(2 * math.pi))


def build_standing_wave_baseline(
    pressures: List[float],
    window: int = 12,
    sigma: float = 2.0,
) -> List[float]:
    """Compute reference baseline using Gaussian-weighted kernel smoothing.
    
    This is the 'woman in the box' — the invisible reference state.
    Returns smoothed baseline at each point.
    """
    if not pressures or window < 1:
        return pressures
    
    baseline = []
    for i in range(len(pressures)):
        # Gaussian-weighted average over window
        weights = []
        values = []
        for j in range(max(0, i - window), min(len(pressures), i + window + 1)):
            dist = abs(j - i)
            w = gaussian_kernel(dist, sigma)
            weights.append(w)
            values.append(pressures[j])
        
        if weights:
            total_w = sum(weights)
            avg = sum(v * w for v, w in zip(values, weights)) / total_w
            baseline.append(avg)
        else:
            baseline.append(0.0)
    
    return baseline


def compute_carrier_state_state(
    observed: float,
    baseline: float,
    prev_carrier_state: Optional[CarrierStateState],
    recovery_threshold: float = 0.15,
) -> CarrierStateState:
    """Update carrier_state state based on perturbation.
    
    The carrier_state is a self-reinforcing standing wave that:
    - Grows if perturbation exceeds threshold (disturbance locked)
    - Decays exponentially if undisturbed (coherence restored)
    - Remains stable once manifest
    
    Args:
        observed: Current causal pressure
        baseline: Expected (smoothed) baseline
        prev_carrier_state: Previous carrier_state state
        recovery_threshold: Deviation beyond which carrier_state manifests
    
    Returns:
        Updated CarrierStateState
    """
    if prev_carrier_state is None:
        prev_carrier_state = CarrierStateState(amplitude=0.0, phase=0.0, coherence=1.0, decay_rate=0.95)
    
    # Perturbation: signed deviation from baseline
    perturbation = observed - baseline
    
    # CarrierState growth/decay logic
    if abs(perturbation) > recovery_threshold:
        # Disturbance detected: carrier_state amplitude grows
        new_amplitude = min(1.0, prev_carrier_state.amplitude + 0.15 * abs(perturbation))
        new_coherence = max(0.0, prev_carrier_state.coherence - 0.10)
        phase_shift = 0.1 * perturbation  # Phase locks to disturbance
    else:
        # No disturbance: carrier_state decays exponentially toward rest
        new_amplitude = prev_carrier_state.amplitude * prev_carrier_state.decay_rate
        new_coherence = min(1.0, prev_carrier_state.coherence + 0.05)
        phase_shift = -0.05 * prev_carrier_state.phase  # Phase damps to 0
    
    new_phase = prev_carrier_state.phase + phase_shift
    
    return CarrierStateState(
        amplitude=new_amplitude,
        phase=new_phase,
        coherence=new_coherence,
        decay_rate=0.95,
    )


def compute_carrier_state_energy(state: CarrierStateState) -> float:
    """Energy of the carrier_state (0.0 = at rest, 1.0 = fully manifest).
    
    Energy = amplitude² + phase² + (1 - coherence)²
    """
    return state.amplitude**2 + state.phase**2 + (1.0 - state.coherence)**2


def carrier_state_rank_anomalies(
    predictions: List[Dict[str, Any]],
    recovery_threshold: float = 0.15,
) -> List[Dict[str, Any]]:
    """Rank predictions by carrier_state energy (anomaly score).
    
    Args:
        predictions: List of prediction dicts from backtest
        recovery_threshold: Threshold for perturbation detection
    
    Returns:
        Predictions augmented with carrier_state fields, sorted by anomaly energy
    """
    pressures = [float(p.get("expected_delta_pressure_horizon", 0.0) or 0.0) for p in predictions]
    
    baseline = build_standing_wave_baseline(pressures, window=12, sigma=2.0)
    
    carrier_state = None
    augmented = []
    
    for i, pred in enumerate(predictions):
        obs = pressures[i]
        base = baseline[i]
        
        carrier_state = compute_carrier_state_state(obs, base, carrier_state, recovery_threshold)
        energy = compute_carrier_state_energy(carrier_state)
        
        aug_pred = dict(pred)
        aug_pred["carrier_state_amplitude"] = round(carrier_state.amplitude, 8)
        aug_pred["carrier_state_phase"] = round(carrier_state.phase, 8)
        aug_pred["carrier_state_coherence"] = round(carrier_state.coherence, 8)
        aug_pred["carrier_state_energy"] = round(energy, 8)
        aug_pred["baseline_pressure"] = round(base, 8)
        aug_pred["perturbation"] = round(obs - base, 8)
        
        augmented.append(aug_pred)
    
    augmented.sort(key=lambda p: float(p.get("carrier_state_energy", 0.0)), reverse=True)
    
    return augmented


def carrier_state_summary(augmented_predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Summary statistics of carrier_state states across predictions."""
    if not augmented_predictions:
        return {}
    
    energies = [float(p.get("carrier_state_energy", 0.0) or 0.0) for p in augmented_predictions]
    amplitudes = [float(p.get("carrier_state_amplitude", 0.0) or 0.0) for p in augmented_predictions]
    coherences = [float(p.get("carrier_state_coherence", 0.0) or 0.0) for p in augmented_predictions]
    
    # Count "manifest" carrier_states (energy > 0.1)
    manifest_count = sum(1 for e in energies if e > 0.1)
    
    # Identify clusters of high energy (regime changes)
    high_energy_indices = [i for i, e in enumerate(energies) if e > 0.2]
    clusters = []
    if high_energy_indices:
        current_cluster = [high_energy_indices[0]]
        for idx in high_energy_indices[1:]:
            if idx - current_cluster[-1] <= 3:
                current_cluster.append(idx)
            else:
                clusters.append(current_cluster)
                current_cluster = [idx]
        clusters.append(current_cluster)
    
    return {
        "total_predictions": len(augmented_predictions),
        "manifest_carrier_states": manifest_count,
        "carrier_state_energy_stats": {
            "mean": round(statistics.fmean(energies), 8) if energies else 0.0,
            "median": round(statistics.median(energies), 8) if energies else 0.0,
            "max": round(max(energies), 8) if energies else 0.0,
            "pstdev": round(statistics.pstdev(energies), 8) if len(energies) > 1 else 0.0,
        },
        "coherence_stats": {
            "mean": round(statistics.fmean(coherences), 8) if coherences else 0.0,
            "min": round(min(coherences), 8) if coherences else 0.0,
        },
        "anomaly_clusters": [
            {
                "start_idx": cluster[0],
                "end_idx": cluster[-1],
                "size": len(cluster),
                "peak_energy": round(max(energies[i] for i in cluster), 8),
            }
            for cluster in clusters
        ],
        "interpretation": (
            f"{manifest_count}/{len(augmented_predictions)} predictions show carrier_state manifestation. "
            f"Mean coherence {round(statistics.fmean(coherences), 3)}. "
            f"{len(clusters)} anomaly cluster(s) detected."
        ),
    }


def augment_report_with_carrier_state(
    report_path: Path,
    out_path: Optional[Path] = None,
    recovery_threshold: float = 0.15,
) -> Dict[str, Any]:
    """Load a causal pressure report, augment with carrier_state monitoring, save.
    
    Args:
        report_path: Path to hyperfluid_causal_report.json
        out_path: Optional path to save augmented report (default: insert _with_carrier_state)
        recovery_threshold: Perturbation threshold for carrier_state manifestation
    
    Returns:
        Augmented report dict
    """
    report = json.loads(report_path.read_text(encoding="utf-8"))
    
    chain_backtests = report.get("chain_backtests", {})
    
    for chain, backtest in chain_backtests.items():
        predictions_raw = backtest.get("predictions", [])
        if predictions_raw:
            augmented = carrier_state_rank_anomalies(predictions_raw, recovery_threshold)
            backtest["predictions_with_carrier_state"] = augmented
            backtest["carrier_state_summary"] = carrier_state_summary(augmented)
            
            # Top 5 anomalies
            backtest["top_anomalies"] = augmented[:5]
    
    if out_path is None:
        stem = report_path.stem
        out_path = report_path.parent / f"{stem}_with_carrier_state.json"
    
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    
    return report


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CarrierState standing wave monitor for hyperfluid causal pressure")
    parser.add_argument("--report", type=str, required=True, help="Path to hyperfluid_causal_report.json")
    parser.add_argument("--out", type=str, default=None, help="Output path (default: _with_carrier_state.json)")
    parser.add_argument("--recovery-threshold", type=float, default=0.15, help="Perturbation threshold for carrier_state manifestation")
    
    args = parser.parse_args()
    
    report_path = Path(args.report)
    out_path = Path(args.out) if args.out else None
    
    augmented_report = augment_report_with_carrier_state(
        report_path,
        out_path=out_path,
        recovery_threshold=float(args.recovery_threshold),
    )
    
    print(f"✓ CarrierState monitoring complete")
    print(f"  Report: {report_path}")
    print(f"  Output: {out_path or (report_path.parent / f'{report_path.stem}_with_carrier_state.json')}")
    
    # Print summary per chain
    for chain, backtest in augmented_report.get("chain_backtests", {}).items():
        summary = backtest.get("carrier_state_summary", {})
        print(f"\n  [{chain}]")
        print(f"    Manifest carrier_states: {summary.get('manifest_carrier_states', 0)}")
        print(f"    Mean coherence: {summary.get('coherence_stats', {}).get('mean', 0)}")
        print(f"    Anomaly clusters: {len(summary.get('anomaly_clusters', []))}")
