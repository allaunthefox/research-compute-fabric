"""Example real adapter: compression / prediction universe.
Maps predicted vs actual coding cost into bounded coordinates.
"""
from __future__ import annotations
from typing import Mapping, Sequence
from pbacs_core import Adapter, ControlState, StepTrace


class CompressionAdapter(Adapter):
    def __init__(self) -> None:
        self._modes = ("BYPASS", "DELTA", "RICH")

    def initial_state(self):
        # x = [internal expected coding regime]
        return [0.5]

    def modes(self):
        return self._modes

    def target_state(self, raw: Mapping[str, float], history: Sequence[StepTrace]):
        # External target: actual coding burden normalized into [0,1]
        actual = max(0.0, min(1.0, raw["actual_bpb"]))
        return [actual]

    def update_projection_context(self, x_t, z_t, raw: Mapping[str, float], history: Sequence[StepTrace]):
        psi = max(0.0, min(1.0, x_t[0]))
        phi = max(0.0, min(1.0, z_t[0]))
        predicted = max(0.0, min(1.0, raw["predicted_bpb"]))
        actual = phi
        # prediction mismatch and state lag
        pred_err = abs(actual - predicted)
        delta = abs(phi - psi)
        prev_delta = history[-1].projections["u_delta"] if history else 0.0
        delta_dot = max(0.0, delta - prev_delta)
        prev_phi = history[-1].z_t[0] if history else phi
        prev2_phi = history[-2].z_t[0] if len(history) >= 2 else prev_phi
        gamma = abs(phi - 2.0 * prev_phi + prev2_phi)
        tau = min(1.0, 0.65 * pred_err + 0.35 * gamma)
        # productively structured disorder: better when redundancy is high and instability is low
        redundancy = max(0.0, min(1.0, raw["redundancy"]))
        chi = max(0.0, min(1.0, redundancy * (1.0 - tau)))
        gain = max(0.0, min(1.0, raw["compression_gain"]))
        cost = max(0.0, min(1.0, 0.5 * raw["latency_cost"] + 0.5 * pred_err))
        bias = max(0.0, min(1.0, raw["model_reliability"]))
        phi_margin = max(0.0, min(1.0, 0.5 * (1.0 - tau) + 0.3 * bias + 0.2 * gain))
        return {
            "u_phi": phi_margin,
            "u_delta": delta,
            "u_delta_dot": delta_dot,
            "u_gamma": max(0.0, min(1.0, gamma)),
            "u_tau": tau,
            "u_chi": chi,
            "u_gain": gain,
            "u_cost": cost,
            "u_bias": bias,
            "u_pacing": max(delta, pred_err),
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
            return (("HALT", "BYPASS"),)
        if state == ControlState.HOLD:
            return (("HOLD", "DELTA"), ("HOLD", "BYPASS"))
        if state == ControlState.DMT:
            return (("DMT", "RICH"),)
        return (("COMMIT", "BYPASS"), ("COMMIT", "DELTA"), ("COMMIT", "RICH"))
