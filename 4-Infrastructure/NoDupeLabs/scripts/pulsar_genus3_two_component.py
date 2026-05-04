#!/usr/bin/env python3
"""
Pulsar Genus-3 Two-Component Simulation

Candidate Research Stack model:

    no canonical vertical in n-space
    "down" = increasing torsion / decreasing accessible phase volume / decreasing free energy

This script models a two-component pulsar-like system:

    crust / charged component:          Ω_c
    neutron superfluid component:       Ω_s
    external magnetic dipole braking:   N_ext = -K Ω_c^n
    internal coupling / creep:          N_int
    glitch flash:                       vortex-unpinning avalanche when lag crosses threshold
    genus-3 route weights:              three circulation channels that redistribute avalanche flow
    Doppler beaming trace:              D = 1 / (γ(1 - β cos θ_obs))

It is not proof. It is an executable sketch that emits invariants and traces.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np

# SI anchors used only for scale-aware proxies.
H = 6.62607015e-34          # exact SI Planck constant, J s
M_N = 1.67492749804e-27     # neutron mass, kg; measured reference seed
C = 299_792_458.0           # exact SI speed of light, m/s
KAPPA = H / (2.0 * M_N)     # neutron superfluid circulation quantum proxy, m^2/s


@dataclass
class GlitchEvent:
    step: int
    time: float
    lag_before: float
    lag_after: float
    delta_omega_c: float
    delta_omega_s: float
    delta_L_internal: float
    flash_energy_proxy: float
    vortex_flux_proxy: float
    route_open_field: float
    route_closed_field: float
    route_return_sheet: float
    doppler_before: float
    doppler_after: float


@dataclass
class RouteState:
    """Three independent circulation channels: reduced genus-3 abstraction."""

    open_field: float = 0.34
    closed_field: float = 0.33
    return_sheet: float = 0.33

    def normalized(self) -> "RouteState":
        values = np.array([self.open_field, self.closed_field, self.return_sheet], dtype=float)
        values = np.maximum(values, 1e-9)
        values = values / values.sum()
        return RouteState(float(values[0]), float(values[1]), float(values[2]))

    def as_array(self) -> np.ndarray:
        n = self.normalized()
        return np.array([n.open_field, n.closed_field, n.return_sheet], dtype=float)

    def drift_after_event(self, lag: float, rng: np.random.Generator) -> "RouteState":
        """
        Event history slightly reweights circulation channels.

        This is FAMM-like behavior in miniature: a successful release route becomes
        marginally easier next time, but noise prevents fake determinism.
        """
        base = self.as_array()
        stress = min(1.0, max(0.0, lag / 0.02))
        perturb = rng.normal(0.0, 0.015 + 0.025 * stress, size=3)
        # Return sheet gets extra weight under high lag: reconnection-like route.
        perturb[2] += 0.02 * stress
        values = np.maximum(base + perturb, 1e-5)
        values = values / values.sum()
        return RouteState(float(values[0]), float(values[1]), float(values[2]))


def doppler_factor(omega: float, radius: float, theta_obs: float) -> float:
    """Special-relativistic rotational Doppler/beaming proxy."""
    beta = min(0.85, abs(omega * radius) / C)
    gamma = 1.0 / math.sqrt(max(1e-12, 1.0 - beta * beta))
    return 1.0 / (gamma * (1.0 - beta * math.cos(theta_obs)))


def vortex_count_proxy(omega_s: float, radius: float) -> float:
    """Feynman vortex density relation n_v = 2 Ω_s / κ, integrated over area."""
    area = math.pi * radius * radius
    return 2.0 * omega_s * area / KAPPA


def simulate(
    steps: int = 30_000,
    dt: float = 0.02,
    seed: int = 42,
) -> Tuple[Dict[str, np.ndarray], List[GlitchEvent]]:
    """
    Two-component spin evolution.

    Equations:
        I_c dΩ_c/dt = N_ext + N_int
        I_s dΩ_s/dt = -N_int
        d/dt(I_c Ω_c + I_s Ω_s) = N_ext

    Internal glitch window approximately conserves angular momentum:
        I_c ΔΩ_c + I_s ΔΩ_s ≈ 0
    """
    rng = np.random.default_rng(seed)

    # Dimensionless but pulsar-shaped parameters.
    I_total = 1.0
    I_c = 0.12
    I_s = I_total - I_c

    # Vela-like order-of-magnitude rotation frequency in rad/s: 11.2 Hz * 2π.
    omega_c = 2.0 * math.pi * 11.2
    omega_s = omega_c * (1.0 + 4.0e-4)

    # External braking is deliberately small; lag builds slowly.
    K_brake = 1.1e-10
    braking_index = 3.0

    # Creep/mutual friction and glitch threshold.
    creep_coeff = 1.8e-5
    omega_crit_base = 0.018
    avalanche_fraction_base = 0.11
    avalanche_width = 0.0028

    # Emission radius proxy: neutron star radius order.
    radius = 12_000.0
    theta_obs = math.radians(35.0)

    routes = RouteState()
    glitches: List[GlitchEvent] = []

    t = np.zeros(steps)
    omega_c_trace = np.zeros(steps)
    omega_s_trace = np.zeros(steps)
    lag_trace = np.zeros(steps)
    L_total_trace = np.zeros(steps)
    L_expected_trace = np.zeros(steps)
    N_ext_trace = np.zeros(steps)
    N_int_trace = np.zeros(steps)
    doppler_trace = np.zeros(steps)
    vortex_trace = np.zeros(steps)
    torsion_trace = np.zeros(steps)
    accessible_phase_trace = np.zeros(steps)
    route_trace = np.zeros((steps, 3))

    L_expected = I_c * omega_c + I_s * omega_s
    previous_lag = omega_s - omega_c

    for step in range(steps):
        time = step * dt
        lag = omega_s - omega_c
        route_weights = routes.as_array()

        # Magnetic dipole braking: N_ext = -K Ω_c^n.
        N_ext = -K_brake * (omega_c ** braking_index)

        # Smooth mutual friction / creep tries to reduce lag.
        # Route weights bias the effective creep channel.
        route_coupling = 0.75 * route_weights[0] + 0.45 * route_weights[1] + 1.10 * route_weights[2]
        N_int = creep_coeff * route_coupling * lag

        # Integrate pre-glitch continuous evolution.
        domega_c = (N_ext + N_int) / I_c
        domega_s = -N_int / I_s
        omega_c += domega_c * dt
        omega_s += domega_s * dt
        L_expected += N_ext * dt

        # Threshold fluctuates weakly, representing disorder in pinning landscape.
        omega_crit = omega_crit_base * (1.0 + 0.08 * math.sin(0.003 * step) + 0.02 * rng.normal())
        lag_after_creep = omega_s - omega_c

        if lag_after_creep >= omega_crit:
            before_c = omega_c
            before_s = omega_s
            before_lag = lag_after_creep
            before_L = I_c * before_c + I_s * before_s
            doppler_before = doppler_factor(before_c, radius, theta_obs)

            # Avalanche fraction depends on excess lag and genus-route distribution.
            excess = max(0.0, before_lag - omega_crit)
            route_release_gain = 0.80 * route_weights[0] + 0.55 * route_weights[1] + 1.35 * route_weights[2]
            frac = avalanche_fraction_base * route_release_gain * (1.0 + excess / avalanche_width)
            frac = float(np.clip(frac, 0.035, 0.38))

            # Reduce the differential lag by transferring angular momentum from superfluid to crust.
            delta_lag = frac * before_lag
            # Conservation: I_c ΔΩ_c + I_s ΔΩ_s = 0 and ΔΩ_c - ΔΩ_s = delta_lag.
            delta_omega_c = (I_s / (I_c + I_s)) * delta_lag
            delta_omega_s = -(I_c / (I_c + I_s)) * delta_lag

            omega_c += delta_omega_c
            omega_s += delta_omega_s

            after_lag = omega_s - omega_c
            after_L = I_c * omega_c + I_s * omega_s
            delta_L_internal = after_L - before_L
            doppler_after = doppler_factor(omega_c, radius, theta_obs)

            vortex_before = vortex_count_proxy(before_s, radius)
            vortex_after = vortex_count_proxy(omega_s, radius)
            vortex_flux = abs(vortex_before - vortex_after)

            flash_energy_proxy = 0.5 * I_s * (before_s ** 2 - omega_s ** 2) + 0.5 * I_c * (omega_c ** 2 - before_c ** 2)

            glitches.append(
                GlitchEvent(
                    step=step,
                    time=time,
                    lag_before=before_lag,
                    lag_after=after_lag,
                    delta_omega_c=delta_omega_c,
                    delta_omega_s=delta_omega_s,
                    delta_L_internal=delta_L_internal,
                    flash_energy_proxy=flash_energy_proxy,
                    vortex_flux_proxy=vortex_flux,
                    route_open_field=float(route_weights[0]),
                    route_closed_field=float(route_weights[1]),
                    route_return_sheet=float(route_weights[2]),
                    doppler_before=doppler_before,
                    doppler_after=doppler_after,
                )
            )

            routes = routes.drift_after_event(before_lag, rng)

        # Traces.
        lag = omega_s - omega_c
        L_total = I_c * omega_c + I_s * omega_s
        D = doppler_factor(omega_c, radius, theta_obs)
        Nv = vortex_count_proxy(omega_s, radius)

        # Torsion proxy: lag strain plus route circulation imbalance.
        route_entropy = -float(np.sum(route_weights * np.log(route_weights + 1e-12)))
        max_entropy = math.log(3.0)
        route_imbalance = 1.0 - route_entropy / max_entropy
        torsion = abs(lag) * (1.0 + 3.0 * route_imbalance)

        # Accessible phase volume proxy shrinks as lag/torsion stress rises.
        accessible_phase = math.exp(-70.0 * abs(lag)) * (route_entropy / max_entropy)

        t[step] = time
        omega_c_trace[step] = omega_c
        omega_s_trace[step] = omega_s
        lag_trace[step] = lag
        L_total_trace[step] = L_total
        L_expected_trace[step] = L_expected
        N_ext_trace[step] = N_ext
        N_int_trace[step] = N_int
        doppler_trace[step] = D
        vortex_trace[step] = Nv
        torsion_trace[step] = torsion
        accessible_phase_trace[step] = accessible_phase
        route_trace[step] = routes.as_array()
        previous_lag = lag

    traces = {
        "t": t,
        "omega_c": omega_c_trace,
        "omega_s": omega_s_trace,
        "lag": lag_trace,
        "L_total": L_total_trace,
        "L_expected": L_expected_trace,
        "N_ext": N_ext_trace,
        "N_int": N_int_trace,
        "doppler": doppler_trace,
        "vortex_count": vortex_trace,
        "torsion": torsion_trace,
        "accessible_phase": accessible_phase_trace,
        "route_open_field": route_trace[:, 0],
        "route_closed_field": route_trace[:, 1],
        "route_return_sheet": route_trace[:, 2],
    }
    return traces, glitches


def plot_outputs(traces: Dict[str, np.ndarray], glitches: List[GlitchEvent], outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    t = traces["t"]
    glitch_times = [g.time for g in glitches]

    plt.figure(figsize=(11, 5))
    plt.plot(t, traces["omega_c"] / (2.0 * math.pi), label="crust / charged component frequency Hz")
    plt.plot(t, traces["omega_s"] / (2.0 * math.pi), label="superfluid frequency Hz", alpha=0.78)
    for gt in glitch_times:
        plt.axvline(gt, alpha=0.25, linewidth=0.8)
    plt.title("Two-component pulsar spin traces with glitch flashes")
    plt.xlabel("model time")
    plt.ylabel("frequency proxy Hz")
    plt.legend()
    plt.tight_layout()
    plt.savefig(outdir / "pulsar_spin_traces.png", dpi=180)
    plt.close()

    plt.figure(figsize=(11, 5))
    plt.plot(t, traces["lag"], label="lag Ω_s - Ω_c")
    plt.plot(t, traces["torsion"], label="torsion proxy", alpha=0.82)
    plt.plot(t, traces["accessible_phase"], label="accessible phase volume proxy", alpha=0.82)
    for gt in glitch_times:
        plt.axvline(gt, alpha=0.25, linewidth=0.8)
    plt.title("Lag builds, torsion rises, accessible phase volume contracts")
    plt.xlabel("model time")
    plt.legend()
    plt.tight_layout()
    plt.savefig(outdir / "pulsar_lag_torsion_phase.png", dpi=180)
    plt.close()

    plt.figure(figsize=(11, 5))
    residual = traces["L_total"] - traces["L_expected"]
    plt.plot(t, residual, label="angular momentum residual L_total - integrated external torque")
    for gt in glitch_times:
        plt.axvline(gt, alpha=0.25, linewidth=0.8)
    plt.title("Conservation check: internal glitches should preserve angular momentum")
    plt.xlabel("model time")
    plt.ylabel("residual")
    plt.legend()
    plt.tight_layout()
    plt.savefig(outdir / "pulsar_angular_momentum_residual.png", dpi=180)
    plt.close()

    plt.figure(figsize=(11, 5))
    plt.plot(t, traces["route_open_field"], label="cycle 1: open field route")
    plt.plot(t, traces["route_closed_field"], label="cycle 2: closed field route")
    plt.plot(t, traces["route_return_sheet"], label="cycle 3: return sheet route")
    for gt in glitch_times:
        plt.axvline(gt, alpha=0.25, linewidth=0.8)
    plt.title("Genus-3 route weights drift after avalanche events")
    plt.xlabel("model time")
    plt.ylabel("route weight")
    plt.legend()
    plt.tight_layout()
    plt.savefig(outdir / "pulsar_genus3_route_weights.png", dpi=180)
    plt.close()

    plt.figure(figsize=(11, 5))
    plt.plot(t, traces["doppler"], label="Doppler / beaming factor")
    plt.plot(t, traces["vortex_count"] / np.max(traces["vortex_count"]), label="vortex count proxy normalized", alpha=0.82)
    for gt in glitch_times:
        plt.axvline(gt, alpha=0.25, linewidth=0.8)
    plt.title("Blue/red shift proxy and superfluid vortex count proxy")
    plt.xlabel("model time")
    plt.legend()
    plt.tight_layout()
    plt.savefig(outdir / "pulsar_doppler_vortex_proxy.png", dpi=180)
    plt.close()


def write_outputs(traces: Dict[str, np.ndarray], glitches: List[GlitchEvent], outdir: Path) -> Dict[str, object]:
    outdir.mkdir(parents=True, exist_ok=True)
    residual = traces["L_total"] - traces["L_expected"]
    report = {
        "model_id": "pulsar_genus3_two_component_v0",
        "status": "HOLD",
        "proof_status": "simulation_sketch_not_proof",
        "rule": "No canonical vertical in n-space: descent is modeled as increasing torsion and decreasing accessible phase volume.",
        "constants": {
            "h_exact_SI": H,
            "c_exact_SI": C,
            "m_n_measured_reference": M_N,
            "kappa_proxy_h_over_2mn": KAPPA,
        },
        "summary": {
            "steps": int(len(traces["t"])),
            "glitch_count": len(glitches),
            "initial_crust_frequency_hz": float(traces["omega_c"][0] / (2.0 * math.pi)),
            "final_crust_frequency_hz": float(traces["omega_c"][-1] / (2.0 * math.pi)),
            "max_lag": float(np.max(traces["lag"])),
            "max_torsion_proxy": float(np.max(traces["torsion"])),
            "min_accessible_phase_proxy": float(np.min(traces["accessible_phase"])),
            "max_angular_momentum_residual_abs": float(np.max(np.abs(residual))),
            "max_doppler_factor": float(np.max(traces["doppler"])),
        },
        "glitches": [asdict(g) for g in glitches],
        "outputs": [
            str(outdir / "pulsar_spin_traces.png"),
            str(outdir / "pulsar_lag_torsion_phase.png"),
            str(outdir / "pulsar_angular_momentum_residual.png"),
            str(outdir / "pulsar_genus3_route_weights.png"),
            str(outdir / "pulsar_doppler_vortex_proxy.png"),
            str(outdir / "pulsar_genus3_report.json"),
        ],
        "next_gate": "Compare qualitative traces against literature-aligned glitch features; do not use as proof or solar-system validation.",
    }
    (outdir / "pulsar_genus3_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Compact CSV for spreadsheet/Neo4j/forest-map ingestion.
    csv_path = outdir / "pulsar_genus3_traces.csv"
    names = [
        "t", "omega_c", "omega_s", "lag", "L_total", "L_expected", "N_ext", "N_int",
        "doppler", "vortex_count", "torsion", "accessible_phase",
        "route_open_field", "route_closed_field", "route_return_sheet",
    ]
    matrix = np.column_stack([traces[name] for name in names])
    header = ",".join(names)
    np.savetxt(csv_path, matrix, delimiter=",", header=header, comments="")
    report["outputs"].append(str(csv_path))
    return report


def main() -> None:
    outdir = Path("research-stack/models/pulsar_genus3_outputs")
    traces, glitches = simulate()
    plot_outputs(traces, glitches, outdir)
    report = write_outputs(traces, glitches, outdir)
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
