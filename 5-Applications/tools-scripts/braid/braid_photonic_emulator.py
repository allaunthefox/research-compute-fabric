#!/usr/bin/env python3
"""
braid_photonic_emulator.py
Photonic emulation bridge for the Braid-Neuromorphic Genetic Ladder.

Maps integer-shell braid events to a Simphony photonic circuit netlist.
Each event becomes a Mach-Zehnder Interferometer (MZI) stage:
    y-branch splitter -> phase-shifted arm + reference arm -> y-branch combiner
The phase shift encodes timing_phase, and the arm-length difference encodes
polarity/interaction.  The resulting S21 spectrum gives a continuous-domain
view of the standing-wave field and genetic ladder topology.

Requires:  simphony, sax, jax, matplotlib, numpy
Run with:  source .venv-simphony/bin/activate && python 5-Applications/tools-5-Applications/scripts/braid_photonic_emulator.py
"""

from __future__ import annotations

import math
import json
import argparse
import functools
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import sax
from jax import config

config.update("jax_enable_x64", True)

from simphony.libraries import siepic

# ---------------------------------------------------------------------------
# Braid logic (mirrors braid_field_builder.py)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Braid logic (mirrors braid_field_builder.py)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BraidEventParams:
    """Single source of truth for every magic number in compute_event.
    Factored per 5-Applications/tools-scripts/formula_optimization/braid_event_delta_gcl.py"""
    decay_base:        float = 0.5    # tail/echo geometric decay base
    tail_depth:        int   = 3      # tail_weights has 3 entries
    echo_depth:        int   = 2      # Fm uses decay^1, Fp uses decay^2
    phase_tanh_coef:   float = 2.0    # tanh contribution to phase
    phase_tanh_scale:  float = 64.0   # interaction scale inside tanh
    phase_clip_range:  int   = 3      # = phase_linear_coef (the redundancy)

    @property
    def tail_weights(self) -> dict[int, float]:
        return {k: -(self.decay_base ** (k - 1)) for k in range(1, self.tail_depth + 1)}

    @property
    def echo_coefs(self) -> tuple[float, float]:
        # (Fm uses ^1, Fp uses ^2)
        return (self.decay_base ** 1, self.decay_base ** 2)

    @property
    def phase_linear_coef(self) -> int:
        return self.phase_clip_range


# Canonical Fc table reframed via sign × magnitude
_PURINES   = {"A", "G"}
_CANONICAL = {"A", "T"}      # full magnitude (1.0)
_WOBBLE    = {"G", "C"}      # half magnitude (0.5)


def _Fc_canonical(et: str) -> float:
    sign = +1.0 if et in _PURINES else -1.0
    magnitude = 1.0 if et in _CANONICAL else 0.5
    return sign * magnitude


def shell_state(n: int):
    k = int(math.isqrt(n))
    a = n - k * k
    b = (k + 1) * (k + 1) - n
    return {"n": n, "k": k, "a": a, "b": b, "width": 2 * k + 1}


def classify_event(s: dict):
    k, n = s["k"], s["n"]
    if n == k * k:
        return "A"
    if n == k * k + k:
        return "G"
    if n == k * k + k + 1:
        return "C"
    if n == (k + 1) * (k + 1) - 1:
        return "T"
    return None


def compute_event(n: int, params: BraidEventParams = BraidEventParams()):
    s = shell_state(n)
    et = classify_event(s)
    if et is None:
        return None
    a, b, k = s["a"], s["b"], s["k"]
    mass = a * b
    polarity = a - b
    shell_width = 2 * k + 1

    # Standing-wave echo (anti-causal tail approximation)
    echo = 0.0
    for tail, weight in params.tail_weights.items():
        if n - tail >= 0:
            prev = shell_state(n - tail)
            prev_et = classify_event(prev)
            if prev_et is not None:
                echo += weight * prev["a"] * prev["b"]

    # Field channels
    cm, cp = params.echo_coefs
    Fm = mass + cm * echo
    Fp = polarity + cp * echo
    Fc = _Fc_canonical(et)

    interaction = mass * Fm + polarity * Fp + Fc
    
    R = params.phase_clip_range
    phase = max(-R, min(R, round(
        params.phase_linear_coef * polarity / shell_width 
        + params.phase_tanh_coef * math.tanh(interaction / params.phase_tanh_scale)
    )))
    index_bit = 1 if interaction > 0 else 0

    return {
        "n": n,
        "k": k,
        "et": et,
        "mass": mass,
        "polarity": polarity,
        "shell_width": shell_width,
        "echo": echo,
        "Fm": Fm,
        "Fp": Fp,
        "Fc": Fc,
        "interaction": interaction,
        "phase": int(phase),
        "index_bit": index_bit,
    }


# ---------------------------------------------------------------------------
# Photonic model wrappers
# ---------------------------------------------------------------------------

def _phase_waveguide(wl: float = 1.55, length: float = 0.0, phase: float = 0.0):
    """Ideal waveguide with an additional phase shift."""
    wg = siepic.waveguide(wl=wl, length=length)
    j = complex(0, 1)
    rot = cmath.exp(j * phase)
    wg_rot = {}
    for (p1, p2), val in wg.items():
        if (p1 == "o0" and p2 == "o1") or (p1 == "o1" and p2 == "o0"):
            wg_rot[(p1, p2)] = val * rot
        else:
            wg_rot[(p1, p2)] = val
    return wg_rot


def _ybranch(wl: float = 1.55):
    return siepic.y_branch(wl=wl)


# ---------------------------------------------------------------------------
# Photonic netlist builder
# ---------------------------------------------------------------------------

def build_mzi_ladder_netlist(events: list[dict]):
    """
    Build a cascade of MZIs, one per event.
    Each MZI:  y-split_i -> wgA_i -> y-comb_i
                         -> wgB_i ->
    """
    instances: dict[str, callable] = {}
    connections: dict[str, str] = {}

    for i, ev in enumerate(events):
        # Map braid features to photonic parameters
        base_length = 50e-6  # 50 µm base arm
        delta_length = ev["polarity"] * 2e-6  # ±2 µm per polarity unit
        phase_rad = math.radians(ev["phase"] * 15.0)  # ±3 -> ±45°

        split_name = f"split_{i}"
        comb_name = f"comb_{i}"
        wgA_name = f"wgA_{i}"
        wgB_name = f"wgB_{i}"

        instances[split_name] = functools.partial(_ybranch)
        instances[comb_name] = functools.partial(_ybranch)
        instances[wgA_name] = functools.partial(_phase_waveguide, length=base_length + delta_length, phase=phase_rad)
        instances[wgB_name] = functools.partial(_phase_waveguide, length=base_length - delta_length, phase=0.0)

        # Internal MZI wiring
        connections[f"{split_name},port_2"] = f"{wgA_name},o0"
        connections[f"{split_name},port_3"] = f"{wgB_name},o0"
        connections[f"{wgA_name},o1"] = f"{comb_name},port_2"
        connections[f"{wgB_name},o1"] = f"{comb_name},port_3"

        # Chain to next stage
        if i + 1 < len(events):
            connections[f"{comb_name},port_1"] = f"split_{i+1},port_1"

    ports = {"in": "split_0,port_1", "out": f"comb_{len(events)-1},port_1"}

    return {"instances": instances, "connections": connections, "ports": ports}


# ---------------------------------------------------------------------------
# Simulation runner
# ---------------------------------------------------------------------------

def run_photonic_simulation(events: list[dict], wl_start: float = 1.50, wl_stop: float = 1.60, points: int = 1001):
    netlist = build_mzi_ladder_netlist(events)
    circuit, info = sax.circuit(netlist, models={})
    wl = np.linspace(wl_start, wl_stop, points)
    s_params = circuit(wl=wl)
    s21 = s_params[("in", "out")]
    transmission = np.abs(s21) ** 2
    return wl, transmission, events


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Photonic emulation of the Braid-Neuromorphic Genetic Ladder")
    parser.add_argument("--start", type=int, default=1, help="Start integer n")
    parser.add_argument("--stop", type=int, default=200, help="Stop integer n (inclusive)")
    parser.add_argument("--csv", type=str, default="braid_photonic_emulation.csv", help="Output CSV path")
    parser.add_argument("--png", type=str, default="braid_photonic_emulation.png", help="Output plot path")
    parser.add_argument("--json", type=str, default="braid_photonic_netlist.json", help="Output netlist JSON")
    args = parser.parse_args()

    events = [ev for n in range(args.start, args.stop + 1) if (ev := compute_event(n)) is not None]
    print(f"Computed {len(events)} axial events for n={args.start}..{args.stop}")

    if not events:
        print("No events to simulate.")
        return

    print("Building photonic MZI ladder netlist ...")
    wl, transmission, events = run_photonic_simulation(events)
    print(f"Simulated {len(wl)} wavelength points.")

    # CSV export (one row per event with center-wavelength transmission)
    out_csv = Path(args.csv)
    with out_csv.open("w") as f:
        f.write("n,k,event,mass,polarity,interaction,phase,index_bit,wl_um,transmission_dB\n")
        center_idx = len(wl) // 2
        for ev in events:
            t = transmission[center_idx]
            t_db = 10.0 * math.log10(max(1e-12, t))
            f.write(
                f"{ev['n']},{ev['k']},{ev['et']},"
                f"{ev['mass']},{ev['polarity']},{ev['interaction']:.6f},"
                f"{ev['phase']},{ev['index_bit']},"
                f"{wl[center_idx]:.6f},{t_db:.6f}\n"
            )
    print(f"Wrote CSV: {out_csv.resolve()}")

    # Plot
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(wl, 10 * np.log10(np.maximum(1e-12, transmission)), label="S21 (dB)")
    ax.set_xlabel("Wavelength (µm)")
    ax.set_ylabel("Transmission (dB)")
    ax.set_title("Braid-Neuromorphic Genetic Ladder — Photonic MZI Emulation")
    ax.legend()
    ax.grid(True)
    fig.tight_layout()
    out_png = Path(args.png)
    fig.savefig(out_png, dpi=150)
    print(f"Wrote plot: {out_png.resolve()}")

    # Netlist JSON (metadata only)
    netlist = build_mzi_ladder_netlist(events)
    out_json = Path(args.json)
    with out_json.open("w") as f:
        json.dump(
            {
                "instances": list(netlist["instances"].keys()),
                "connections": netlist["connections"],
                "ports": netlist["ports"],
                "event_count": len(events),
            },
            f,
            indent=2,
        )
    print(f"Wrote netlist JSON: {out_json.resolve()}")


if __name__ == "__main__":
    import cmath
    main()
