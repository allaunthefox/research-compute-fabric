"""Example real adapter: market watcher universe.
Maps a small OHLCV-like feature stream into bounded coordinates.
"""
from __future__ import annotations
from typing import Dict, Mapping, Sequence, Tuple
from pbacs_core import Adapter, ControlState, StepTrace


class MarketAdapter(Adapter):
    def __init__(self) -> None:
        self._modes = ("OBSERVE", "DEFENSIVE", "AGGRESSIVE")

    def initial_state(self):
        # x = [internal regime alignment]
        return [0.5]

    def modes(self):
        return self._modes

    def target_state(self, raw: Mapping[str, float], history: Sequence[StepTrace]):
        # External regime target: scaled trend impulse in [0,1]
        price_move = raw["return_1"]
        vol = raw["volatility"]
        z = 0.5 + 0.5 * max(-1.0, min(1.0, price_move / max(1e-9, vol + 1e-9)))
        return [max(0.0, min(1.0, z))]

    def update_projection_context(self, x_t, z_t, raw: Mapping[str, float], history: Sequence[StepTrace]):
        psi = x_t[0]
        phi = z_t[0]
        delta = abs(phi - psi)
        prev_delta = history[-1].projections["u_delta"] if history else 0.0
        delta_dot = max(0.0, delta - prev_delta)
        prev_phi = history[-1].z_t[0] if history else phi
        prev2_phi = history[-2].z_t[0] if len(history) >= 2 else prev_phi
        gamma = abs(phi - 2.0 * prev_phi + prev2_phi)
        tau = min(1.0, 0.5 * delta + 0.5 * gamma)
        chi = raw["volume_imbalance"] * (1.0 - raw["spread"])
        gain = raw["signal_strength"]
        cost = 0.5 * raw["spread"] + 0.5 * raw["volatility"]
        bias = raw["historical_reliability"]
        phi_margin = max(0.0, min(1.0, (0.6 * (1.0 - tau) + 0.4 * bias)))
        return {
            "u_phi": phi_margin,
            "u_delta": delta,
            "u_delta_dot": delta_dot,
            "u_gamma": max(0.0, min(1.0, gamma)),
            "u_tau": tau,
            "u_chi": max(0.0, min(1.0, chi)),
            "u_gain": max(0.0, min(1.0, gain)),
            "u_cost": max(0.0, min(1.0, cost)),
            "u_bias": max(0.0, min(1.0, bias)),
            "u_pacing": delta,
        }

    def projections(self):
        return {
            "u_phi": lambda c: c["u_phi"],
            "u_delta": lambda c: c["u_delta"],
            "u_delta_dot": lambda c: c["u_delta_dot"],
            "u_gamma": lambda c: c["u_gamma"],
            "u_tau": lambda c: c["u_tau"],
            "u_chi": lambda c: c["u_chi"],
            "u_gain": lambda c: c["u_gain"],
            "u_cost": lambda c: c["u_cost"],
            "u_bias": lambda c: c["u_bias"],
            "u_pacing": lambda c: c["u_pacing"],
        }

    def admissible(self, state: ControlState):
        if state == ControlState.HALT:
            return (("HALT", "OBSERVE"),)
        if state == ControlState.HOLD:
            return (("HOLD", "DEFENSIVE"), ("HOLD", "OBSERVE"))
        if state == ControlState.DMT:
            return (("DMT", "DEFENSIVE"),)
        return (("COMMIT", "OBSERVE"), ("COMMIT", "DEFENSIVE"), ("COMMIT", "AGGRESSIVE"))
