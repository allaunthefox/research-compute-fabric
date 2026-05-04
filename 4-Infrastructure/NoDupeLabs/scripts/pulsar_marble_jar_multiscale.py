#!/usr/bin/env python3
"""
Pulsar Marble-Jar Multiscale Simulation

Candidate Research Stack model v0.1

Purpose
-------
Fixes the earlier human-timeframe error. A pulsar model cannot honestly use one
arbitrary dt for spin-down, vortex creep, glitch rise, and post-glitch recovery.
Those processes live on wildly separated clocks.

This script uses an event-driven multiscale loop:

    cruise phase   : years to centuries per step
    glitch phase   : milliseconds to seconds per substep
    recovery phase : seconds to days per substep

Physical grammar
----------------
    crustal lattice / charged component        -> rigid outer jar / basin rim
    neutron superfluid vortex reservoir        -> marbles / chandelier filaments
    vortex creep                               -> slow grinding of marbles in jar
    pinning threshold                          -> stored torsion / stress limit
    unpinning avalanche                        -> flash / phase transition
    magnetic dipole braking                    -> slow external energy bleed
    glitch spin-up                             -> angular momentum redistribution
    Doppler beaming                            -> blue/red shift trace
    three route weights                        -> genus-3 reduced circulation channels

Authority boundary
------------------
This is a simulation sketch, not proof and not an empirical fit. It is designed
to emit traces and invariants for later audit.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np

# Exact SI anchors where applicable.
C = 299_792_458.0
H = 6.62607015e-34
YEAR_S = 365.25 * 24.0 * 3600.0
DAY_S = 24.0 * 3600.0

# Reference measured seed. Keep uncertainty/audit outside this sketch.
M_N = 1.67492749804e-27
KAPPA = H / (2.0 * M_N)  # neutron superfluid circulation quantum proxy, m^2/s


@dataclass
class GlitchEvent:
    index: int
    time_years: float
    rise_time_seconds: float
    recovery_time_days: float
    omega_c_before: float
    omega_c_after: float
    omega_s_before: float
    omega_s_after: float
    lag_before: float
    lag_after: float
    fractional_spin_jump: float
    released_fraction: float
    unpinned_macro_vortices: int
    real_vortex_flux_proxy: float
    flash_energy_proxy: float
    angular_momentum_residual: float
    doppler_before: float
    doppler_after: float
    route_open_field: float
    route_closed_field: float
    route_return_sheet: float


@dataclass
class RouteState:
    """Genus-3 reduced circulation abstraction: three noncontractible channels."""

    open_field: float = 0.34
    closed_field: float = 0.33
    return_sheet: float = 0.33

    def array(self) -> np.ndarray:
        v = np.array([self.open_field, self.closed_field, self.return_sheet], dtype=float)
        v = np.maximum(v, 1e-12)
        return v / v.sum()

    def drift(self, released_fraction: float, rng: np.random.Generator) -> "RouteState":
        weights = self.array()
        # Large avalanches bias the return-sheet/reconnection-like route.
        kick = np.array([0.00, -0.015, 0.025]) * min(1.0, released_fraction / 0.10)
        noise = rng.normal(0.0, 0.010 + 0.025 * min(1.0, released_fraction / 0.10), size=3)
        updated = np.maximum(weights + kick + noise, 1e-6)
        updated /= updated.sum()
        return RouteState(float(updated[0]), float(updated[1]), float(updated[2]))


def doppler_factor(omega: float, radius_m: float, theta_obs_rad: float) -> float:
    """Rotational Doppler/beaming proxy D = 1/(gamma(1-beta cos theta))."""
    beta = min(0.85, abs(omega * radius_m) / C)
    gamma = 1.0 / math.sqrt(max(1e-14, 1.0 - beta * beta))
    return 1.0 / (gamma * (1.0 - beta * math.cos(theta_obs_rad)))


def vortex_count_proxy(omega_s: float, radius_m: float) -> float:
    """Feynman relation integrated over a circular cross-section."""
    area = math.pi * radius_m * radius_m
    return 2.0 * omega_s * area / KAPPA


def magnetic_dipole_spin_down(omega_c: float, tau_years: float, omega_ref: float) -> float:
    """
    Scaled braking law dΩ/dt = -Ω_ref/tau * (Ω/Ω_ref)^3.

    This preserves the Ω^3 dipole-braking shape without pretending we fitted B,
    inclination, radius, and moment of inertia from data.
    Returns rad/s per year.
    """
    return -(omega_ref / tau_years) * (omega_c / omega_ref) ** 3


def route_entropy(route: RouteState) -> float:
    w = route.array()
    return -float(np.sum(w * np.log(w + 1e-12)))


def simulate(
    total_years: float = 250_000.0,
    cruise_dt_years: float = 0.25,
    seed: int = 7,
) -> Tuple[Dict[str, np.ndarray], List[GlitchEvent]]:
    """
    Event-driven multiscale simulation.

    Cruise clock uses years. Glitch and recovery use internal seconds/days-scale
    maps rather than forcing the whole run through tiny timesteps.
    """
    rng = np.random.default_rng(seed)

    # Pulsar-shaped reference values.
    radius_m = 12_000.0
    theta_obs = math.radians(35.0)
    omega_ref = 2.0 * math.pi * 11.2  # rad/s, Vela-like order

    # Two-component moments of inertia in normalized total units.
    I_total = 1.0
    I_c = 0.12
    I_s = I_total - I_c

    omega_c = omega_ref
    omega_s = omega_ref * (1.0 + 4.5e-4)

    # Long clocks.
    spin_down_tau_years = 1.0e6
    creep_tau_years = 75.0

    # Pinning/glitch settings.
    lag_crit = 0.0200                # rad/s
    lag_jitter = 0.0012              # disorder in pinning substrate
    release_fraction_base = 0.020    # typical fractional release of lag
    release_fraction_max = 0.20

    # Vortex coarse-graining. One macro-vortex stands for many real vortices.
    macro_vortices = 1024

    route = RouteState()
    glitches: List[GlitchEvent] = []

    # Downsampled traces; one row per cruise step plus event discontinuities.
    rows: List[Dict[str, float]] = []

    time_years = 0.0
    event_index = 0
    L_expected = I_c * omega_c + I_s * omega_s

    def append_row(kind: str) -> None:
        lag = omega_s - omega_c
        entropy = route_entropy(route)
        phase_volume = math.exp(-75.0 * abs(lag)) * (entropy / math.log(3.0))
        torsion_proxy = abs(lag) * (1.0 + 3.0 * (1.0 - entropy / math.log(3.0)))
        vortex_count = vortex_count_proxy(omega_s, radius_m)
        L_total = I_c * omega_c + I_s * omega_s
        w = route.array()
        rows.append({
            "time_years": time_years,
            "kind": float({"cruise": 0, "pre_glitch": 1, "post_glitch": 2, "recovery": 3}.get(kind, -1)),
            "omega_c": omega_c,
            "omega_s": omega_s,
            "frequency_c_hz": omega_c / (2.0 * math.pi),
            "frequency_s_hz": omega_s / (2.0 * math.pi),
            "lag": lag,
            "L_total": L_total,
            "L_expected": L_expected,
            "L_residual": L_total - L_expected,
            "doppler": doppler_factor(omega_c, radius_m, theta_obs),
            "vortex_count_proxy": vortex_count,
            "torsion_proxy": torsion_proxy,
            "accessible_phase_proxy": phase_volume,
            "route_open_field": w[0],
            "route_closed_field": w[1],
            "route_return_sheet": w[2],
        })

    append_row("cruise")

    while time_years < total_years:
        lag = omega_s - omega_c

        # ---- Cruise phase: years-scale integration ----
        d_omega_ext = magnetic_dipole_spin_down(omega_c, spin_down_tau_years, omega_ref)

        # Vortex creep / mutual friction: slow internal coupling. The sign here
        # transfers angular momentum from superfluid to crust when Ω_s > Ω_c.
        route_weights = route.array()
        route_coupling = 0.70 * route_weights[0] + 0.45 * route_weights[1] + 1.20 * route_weights[2]
        N_creep = route_coupling * lag / creep_tau_years

        domega_c_dt = d_omega_ext + (I_s / I_total) * N_creep
        domega_s_dt = -(I_c / I_total) * N_creep

        omega_c += domega_c_dt * cruise_dt_years
        omega_s += domega_s_dt * cruise_dt_years
        L_expected += I_c * d_omega_ext * cruise_dt_years
        time_years += cruise_dt_years

        # Disorder-jittered pinning threshold.
        threshold = lag_crit + lag_jitter * math.sin(2.0 * math.pi * time_years / 81.0) + rng.normal(0.0, 0.00025)
        threshold = max(0.010, threshold)

        if (omega_s - omega_c) >= threshold:
            append_row("pre_glitch")

            before_c = omega_c
            before_s = omega_s
            before_lag = before_s - before_c
            before_L = I_c * before_c + I_s * before_s
            before_doppler = doppler_factor(before_c, radius_m, theta_obs)

            # ---- Glitch phase: seconds-scale event map ----
            excess = max(0.0, before_lag - threshold)
            release_fraction = release_fraction_base * (1.0 + excess / max(1e-9, lag_crit))
            release_fraction *= (0.70 * route_weights[0] + 0.55 * route_weights[1] + 1.35 * route_weights[2])
            release_fraction = float(np.clip(release_fraction, 0.004, release_fraction_max))

            # Event duration is fast: seconds to minutes, larger avalanches run longer.
            rise_time_seconds = float(0.06 + 42.0 * release_fraction + rng.lognormal(mean=-0.3, sigma=0.35))
            recovery_time_days = float(0.15 + 18.0 * release_fraction + rng.lognormal(mean=0.6, sigma=0.45))

            delta_lag = release_fraction * before_lag

            # Conservation over the internal event:
            # I_c ΔΩ_c + I_s ΔΩ_s = 0
            # ΔΩ_c - ΔΩ_s = delta_lag
            delta_omega_c = (I_s / I_total) * delta_lag
            delta_omega_s = -(I_c / I_total) * delta_lag

            omega_c += delta_omega_c
            omega_s += delta_omega_s

            after_lag = omega_s - omega_c
            after_L = I_c * omega_c + I_s * omega_s
            angular_residual = after_L - before_L
            after_doppler = doppler_factor(omega_c, radius_m, theta_obs)

            # Vortex-count proxy and macro-vortex event size.
            vortex_before = vortex_count_proxy(before_s, radius_m)
            vortex_after = vortex_count_proxy(omega_s, radius_m)
            real_flux_proxy = abs(vortex_before - vortex_after)
            fraction_of_reservoir = min(1.0, real_flux_proxy / max(1e-9, vortex_before))
            unpinned_macro = max(1, int(round(macro_vortices * fraction_of_reservoir)))

            # Flash-energy proxy: rotational energy exchange in normalized inertia units.
            flash_energy = (
                0.5 * I_s * (before_s * before_s - omega_s * omega_s)
                + 0.5 * I_c * (omega_c * omega_c - before_c * before_c)
            )

            event = GlitchEvent(
                index=event_index,
                time_years=time_years,
                rise_time_seconds=rise_time_seconds,
                recovery_time_days=recovery_time_days,
                omega_c_before=before_c,
                omega_c_after=omega_c,
                omega_s_before=before_s,
                omega_s_after=omega_s,
                lag_before=before_lag,
                lag_after=after_lag,
                fractional_spin_jump=delta_omega_c / before_c,
                released_fraction=release_fraction,
                unpinned_macro_vortices=unpinned_macro,
                real_vortex_flux_proxy=real_flux_proxy,
                flash_energy_proxy=flash_energy,
                angular_momentum_residual=angular_residual,
                doppler_before=before_doppler,
                doppler_after=after_doppler,
                route_open_field=float(route_weights[0]),
                route_closed_field=float(route_weights[1]),
                route_return_sheet=float(route_weights[2]),
            )
            glitches.append(event)
            event_index += 1
            append_row("post_glitch")

            # ---- Recovery phase: seconds-to-days-scale map ----
            # We do not integrate every second in the long run; instead we apply a
            # small relaxation correction and advance the physical clock by days.
            rec_years = recovery_time_days / 365.25
            rec_coupling = min(0.15, 0.02 + 0.12 * release_fraction)
            rec_transfer = rec_coupling * (omega_s - omega_c)
            omega_c += (I_s / I_total) * rec_transfer
            omega_s -= (I_c / I_total) * rec_transfer
            time_years += rec_years

            route = route.drift(release_fraction, rng)
            append_row("recovery")
        else:
            append_row("cruise")

    # Convert row dicts to arrays.
    keys = list(rows[0].keys())
    traces = {k: np.array([r[k] for r in rows], dtype=float) for k in keys}
    return traces, glitches


def plot_outputs(traces: Dict[str, np.ndarray], glitches: List[GlitchEvent], outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    t = traces["time_years"]
    glitch_times = [g.time_years for g in glitches]

    plt.figure(figsize=(12, 5))
    plt.plot(t, traces["frequency_c_hz"], label="crust / charged component")
    plt.plot(t, traces["frequency_s_hz"], label="superfluid reservoir", alpha=0.70)
    for gt in glitch_times:
        plt.axvline(gt, alpha=0.18, linewidth=0.6)
    plt.title("Multiscale pulsar spin-down with event-driven glitch flashes")
    plt.xlabel("physical time (years)")
    plt.ylabel("frequency proxy (Hz)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(outdir / "multiscale_spin_down.png", dpi=180)
    plt.close()

    plt.figure(figsize=(12, 5))
    plt.plot(t, traces["lag"], label="lag Ω_s - Ω_c")
    plt.plot(t, traces["torsion_proxy"], label="torsion proxy", alpha=0.82)
    plt.plot(t, traces["accessible_phase_proxy"], label="accessible phase volume proxy", alpha=0.82)
    for gt in glitch_times:
        plt.axvline(gt, alpha=0.18, linewidth=0.6)
    plt.title("Slow lag accumulation, torsion growth, and phase-volume contraction")
    plt.xlabel("physical time (years)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(outdir / "multiscale_lag_torsion_phase.png", dpi=180)
    plt.close()

    plt.figure(figsize=(12, 5))
    plt.plot(t, traces["L_residual"], label="angular momentum residual")
    for gt in glitch_times:
        plt.axvline(gt, alpha=0.18, linewidth=0.6)
    plt.title("Conservation audit: internal glitches should not create angular momentum")
    plt.xlabel("physical time (years)")
    plt.ylabel("L_total - integrated external torque")
    plt.legend()
    plt.tight_layout()
    plt.savefig(outdir / "multiscale_angular_momentum_residual.png", dpi=180)
    plt.close()

    plt.figure(figsize=(12, 5))
    plt.plot(t, traces["route_open_field"], label="cycle 1: open-field route")
    plt.plot(t, traces["route_closed_field"], label="cycle 2: closed-field route")
    plt.plot(t, traces["route_return_sheet"], label="cycle 3: return-sheet route")
    for gt in glitch_times:
        plt.axvline(gt, alpha=0.18, linewidth=0.6)
    plt.title("Genus-3 route weights drift after avalanche events")
    plt.xlabel("physical time (years)")
    plt.ylabel("route weight")
    plt.legend()
    plt.tight_layout()
    plt.savefig(outdir / "multiscale_genus3_routes.png", dpi=180)
    plt.close()

    plt.figure(figsize=(12, 5))
    plt.plot(t, traces["doppler"], label="Doppler / beaming factor")
    vortex_norm = traces["vortex_count_proxy"] / max(1e-12, np.max(traces["vortex_count_proxy"]))
    plt.plot(t, vortex_norm, label="vortex count proxy normalized", alpha=0.82)
    for gt in glitch_times:
        plt.axvline(gt, alpha=0.18, linewidth=0.6)
    plt.title("Blue/red-shift proxy and vortex reservoir trace")
    plt.xlabel("physical time (years)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(outdir / "multiscale_doppler_vortex.png", dpi=180)
    plt.close()

    if glitches:
        sizes = np.array([g.fractional_spin_jump for g in glitches])
        waits = np.diff(np.array([g.time_years for g in glitches])) if len(glitches) > 1 else np.array([])
        plt.figure(figsize=(10, 5))
        plt.scatter([g.time_years for g in glitches], sizes, s=22)
        plt.yscale("log")
        plt.title("Glitch sizes over physical time")
        plt.xlabel("physical time (years)")
        plt.ylabel("fractional crust spin jump ΔΩ_c/Ω_c")
        plt.tight_layout()
        plt.savefig(outdir / "multiscale_glitch_sizes.png", dpi=180)
        plt.close()

        if len(waits) > 0:
            plt.figure(figsize=(10, 5))
            plt.hist(waits, bins=min(30, max(5, len(waits) // 2)))
            plt.title("Inter-glitch waiting-time distribution")
            plt.xlabel("years")
            plt.ylabel("count")
            plt.tight_layout()
            plt.savefig(outdir / "multiscale_waiting_times.png", dpi=180)
            plt.close()


def write_outputs(traces: Dict[str, np.ndarray], glitches: List[GlitchEvent], outdir: Path) -> Dict[str, object]:
    outdir.mkdir(parents=True, exist_ok=True)
    glitch_times = np.array([g.time_years for g in glitches], dtype=float)
    waits = np.diff(glitch_times) if len(glitch_times) > 1 else np.array([])

    report = {
        "model_id": "pulsar_marble_jar_multiscale_v0",
        "status": "HOLD",
        "proof_status": "simulation_sketch_not_proof",
        "timeframe_fix": "Cruise uses physical years; glitch rise uses seconds; recovery uses days. No arbitrary single dt controls all regimes.",
        "rule": "No canonical vertical in n-space. Descent is increasing torsion, decreasing accessible phase volume, and loss of available free energy.",
        "constants": {
            "c_exact_SI_m_s": C,
            "h_exact_SI_J_s": H,
            "m_n_measured_reference_kg": M_N,
            "kappa_proxy_h_over_2mn_m2_s": KAPPA,
        },
        "summary": {
            "trace_rows": int(len(traces["time_years"])),
            "simulated_years": float(traces["time_years"][-1]),
            "glitch_count": len(glitches),
            "mean_wait_years": float(np.mean(waits)) if len(waits) else None,
            "median_wait_years": float(np.median(waits)) if len(waits) else None,
            "initial_crust_frequency_hz": float(traces["frequency_c_hz"][0]),
            "final_crust_frequency_hz": float(traces["frequency_c_hz"][-1]),
            "max_lag_rad_s": float(np.max(traces["lag"])),
            "max_torsion_proxy": float(np.max(traces["torsion_proxy"])),
            "min_accessible_phase_proxy": float(np.min(traces["accessible_phase_proxy"])),
            "max_abs_angular_momentum_residual": float(np.max(np.abs(traces["L_residual"]))),
            "max_doppler_factor": float(np.max(traces["doppler"])),
            "max_fractional_spin_jump": float(max([g.fractional_spin_jump for g in glitches], default=0.0)),
        },
        "glitches": [asdict(g) for g in glitches],
        "outputs": [
            str(outdir / "multiscale_spin_down.png"),
            str(outdir / "multiscale_lag_torsion_phase.png"),
            str(outdir / "multiscale_angular_momentum_residual.png"),
            str(outdir / "multiscale_genus3_routes.png"),
            str(outdir / "multiscale_doppler_vortex.png"),
            str(outdir / "multiscale_glitch_sizes.png"),
            str(outdir / "multiscale_waiting_times.png"),
            str(outdir / "pulsar_marble_jar_multiscale_report.json"),
            str(outdir / "pulsar_marble_jar_multiscale_traces.csv"),
        ],
        "acceptance_tests": {
            "lag_accumulates_between_glitches": "inspect lag sawtooth in multiscale_lag_torsion_phase.png",
            "glitch_spinup_occurs": "glitch log should show positive fractional_spin_jump",
            "internal_event_conserves_angular_momentum": "angular_momentum_residual should remain bounded near numerical/event-map tolerance",
            "route_weights_change_after_events": "multiscale_genus3_routes.png should show event-linked drift",
            "time_scales_are_separated": "report includes years for cruise, seconds for rise, days for recovery",
        },
        "next_gate": "Compare trace classes against real pulsar glitch phenomenology; keep HOLD until validated against data/literature.",
    }

    (outdir / "pulsar_marble_jar_multiscale_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    names = list(traces.keys())
    matrix = np.column_stack([traces[name] for name in names])
    np.savetxt(outdir / "pulsar_marble_jar_multiscale_traces.csv", matrix, delimiter=",", header=",".join(names), comments="")
    return report


def main() -> None:
    outdir = Path("research-stack/models/pulsar_marble_jar_multiscale_outputs")
    traces, glitches = simulate()
    plot_outputs(traces, glitches, outdir)
    report = write_outputs(traces, glitches, outdir)
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
