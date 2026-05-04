#!/usr/bin/env python3
"""
Validation harness for pulsar_marble_jar_multiscale.py

This does not validate the model against real data. It validates the *internal
physics-shaped invariants* that the model claims to preserve:

1. Time scales are separated: cruise years, glitch seconds, recovery days.
2. Lag can accumulate before glitches.
3. Glitches spin up the crust and spin down the superfluid reservoir.
4. Internal glitch events approximately conserve angular momentum.
5. Torsion rises as accessible phase volume contracts.
6. Genus-3 route weights actually participate and drift.
7. Outputs are written in a machine-readable report.

If this harness fails, the model remains HOLD and should not feed downstream
forest-map weighting except as a scar/bug record.
"""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any, Dict, List

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "scripts" / "pulsar_marble_jar_multiscale.py"
OUTDIR = ROOT / "research-stack" / "models" / "pulsar_marble_jar_multiscale_outputs"
VALIDATION_PATH = OUTDIR / "pulsar_marble_jar_multiscale_validation.json"


def load_model_module():
    spec = importlib.util.spec_from_file_location("pulsar_marble_jar_multiscale", MODEL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load model from {MODEL_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def finite(name: str, arr: np.ndarray) -> Dict[str, Any]:
    ok = bool(np.all(np.isfinite(arr)))
    return {"name": name, "ok": ok, "min": float(np.nanmin(arr)), "max": float(np.nanmax(arr))}


def pass_fail(name: str, ok: bool, detail: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return {"name": name, "ok": bool(ok), "detail": detail or {}}


def validate() -> Dict[str, Any]:
    module = load_model_module()

    # Keep runtime short enough for local checks, but long enough to trigger events.
    traces, glitches = module.simulate(total_years=250_000.0, cruise_dt_years=0.25, seed=7)
    module.plot_outputs(traces, glitches, OUTDIR)
    report = module.write_outputs(traces, glitches, OUTDIR)

    checks: List[Dict[str, Any]] = []

    # 1. Basic numeric sanity.
    for key in [
        "time_years", "omega_c", "omega_s", "lag", "L_residual", "doppler",
        "vortex_count_proxy", "torsion_proxy", "accessible_phase_proxy",
        "route_open_field", "route_closed_field", "route_return_sheet",
    ]:
        checks.append(finite(key, traces[key]))

    # 2. Time scales separated.
    rise_times = np.array([g.rise_time_seconds for g in glitches], dtype=float)
    recovery_days = np.array([g.recovery_time_days for g in glitches], dtype=float)
    wait_years = np.diff(np.array([g.time_years for g in glitches], dtype=float)) if len(glitches) > 1 else np.array([])

    checks.append(pass_fail(
        "timescale_separation_glitch_rise_seconds",
        len(rise_times) > 0 and float(np.max(rise_times)) < 600.0 and float(np.min(rise_times)) > 0.0,
        {"min_seconds": float(np.min(rise_times)) if len(rise_times) else None, "max_seconds": float(np.max(rise_times)) if len(rise_times) else None},
    ))
    checks.append(pass_fail(
        "timescale_separation_recovery_days",
        len(recovery_days) > 0 and float(np.max(recovery_days)) < 365.0 and float(np.min(recovery_days)) > 0.0,
        {"min_days": float(np.min(recovery_days)) if len(recovery_days) else None, "max_days": float(np.max(recovery_days)) if len(recovery_days) else None},
    ))
    checks.append(pass_fail(
        "timescale_separation_wait_years",
        len(wait_years) == 0 or float(np.median(wait_years)) > 0.25,
        {"median_wait_years": float(np.median(wait_years)) if len(wait_years) else None, "glitch_count": len(glitches)},
    ))

    # 3. Glitch direction: crust spin-up, superfluid spin-down, lag reduction.
    positive_spin_jumps = [g for g in glitches if g.fractional_spin_jump > 0 and g.omega_s_after < g.omega_s_before and g.lag_after < g.lag_before]
    checks.append(pass_fail(
        "glitch_direction_crust_up_superfluid_down_lag_reduced",
        len(glitches) > 0 and len(positive_spin_jumps) == len(glitches),
        {"glitch_count": len(glitches), "passing_glitches": len(positive_spin_jumps)},
    ))

    # 4. Internal angular momentum conservation during glitches.
    residuals = np.array([abs(g.angular_momentum_residual) for g in glitches], dtype=float)
    checks.append(pass_fail(
        "internal_glitch_angular_momentum_conservation",
        len(residuals) > 0 and float(np.max(residuals)) < 1e-10,
        {"max_internal_residual": float(np.max(residuals)) if len(residuals) else None},
    ))

    # 5. Torsion/phase-volume relationship should be anticorrelated in broad trace.
    torsion = traces["torsion_proxy"]
    phase = traces["accessible_phase_proxy"]
    corr = float(np.corrcoef(torsion, phase)[0, 1]) if len(torsion) > 3 else 0.0
    checks.append(pass_fail(
        "torsion_phase_volume_anticorrelation",
        corr < -0.10,
        {"correlation": corr},
    ))

    # 6. Route weights remain normalized and drift.
    route_sum = traces["route_open_field"] + traces["route_closed_field"] + traces["route_return_sheet"]
    route_drift = float(
        abs(traces["route_open_field"][-1] - traces["route_open_field"][0])
        + abs(traces["route_closed_field"][-1] - traces["route_closed_field"][0])
        + abs(traces["route_return_sheet"][-1] - traces["route_return_sheet"][0])
    )
    checks.append(pass_fail(
        "genus3_route_weights_normalized",
        bool(np.max(np.abs(route_sum - 1.0)) < 1e-8),
        {"max_deviation": float(np.max(np.abs(route_sum - 1.0)))},
    ))
    checks.append(pass_fail(
        "genus3_route_weights_drift_after_events",
        len(glitches) > 0 and route_drift > 1e-4,
        {"route_drift_l1": route_drift},
    ))

    # 7. Fractional spin jumps are in a plausible small-glitch envelope for a sketch.
    jump_sizes = np.array([g.fractional_spin_jump for g in glitches], dtype=float)
    checks.append(pass_fail(
        "fractional_spin_jump_small_not_explosive",
        len(jump_sizes) > 0 and float(np.max(jump_sizes)) < 1e-3 and float(np.min(jump_sizes)) > 0.0,
        {"min_jump": float(np.min(jump_sizes)) if len(jump_sizes) else None, "max_jump": float(np.max(jump_sizes)) if len(jump_sizes) else None},
    ))

    ok = all(c["ok"] for c in checks)
    validation = {
        "validation_id": "pulsar_marble_jar_multiscale_validation_v0",
        "status": "PASS" if ok else "HOLD_FAIL",
        "model_report_summary": report.get("summary", {}),
        "check_count": len(checks),
        "passed_count": sum(1 for c in checks if c["ok"]),
        "failed": [c for c in checks if not c["ok"]],
        "checks": checks,
        "rule": "Passing this harness validates internal invariants only. It does not validate the model against observed pulsars.",
    }
    OUTDIR.mkdir(parents=True, exist_ok=True)
    VALIDATION_PATH.write_text(json.dumps(validation, indent=2), encoding="utf-8")
    return validation


def main() -> None:
    validation = validate()
    print(json.dumps({
        "status": validation["status"],
        "passed_count": validation["passed_count"],
        "check_count": validation["check_count"],
        "failed": validation["failed"],
        "validation_path": str(VALIDATION_PATH),
    }, indent=2))
    if validation["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
