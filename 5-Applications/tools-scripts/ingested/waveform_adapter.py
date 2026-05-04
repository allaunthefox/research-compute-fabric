"""Known-output waveform universe adapter.
Uses bounded scalar wave statistics to choose a basis and induce a field.
No domain assumptions beyond a fixed carrier dict.
"""
from __future__ import annotations
from typing import Mapping, Sequence
import math

from pbacs_core import Adapter, ControlState, StepTrace


class WaveformAdapter(Adapter):
    def __init__(self) -> None:
        self._modes = ("RAW", "SPECTRAL", "TRANSIENT", "HYBRID")

    def initial_state(self):
        # x = [alignment]
        return [0.5]

    def modes(self):
        return self._modes

    def target_state(self, raw: Mapping[str, float], history: Sequence[StepTrace]):
        # External target is a bounded combination of energy and confidence.
        energy = max(0.0, min(1.0, raw.get("energy", 0.0)))
        confidence = max(0.0, min(1.0, raw.get("confidence", 0.5)))
        z = max(0.0, min(1.0, 0.65 * energy + 0.35 * confidence))
        return [z]

    def basis_id(self, raw: Mapping[str, float]) -> str:
        centroid = raw.get("spectral_centroid", 0.0)
        flatness = raw.get("spectral_flatness", 0.0)
        transient = raw.get("transient_ratio", 0.0)
        low = raw.get("band_low", 0.0)
        mid = raw.get("band_mid", 0.0)
        high = raw.get("band_high", 0.0)
        if centroid > 0.70 and flatness < 0.45:
            return "SPECTRAL"
        if transient > 0.65 and high > 0.50:
            return "TRANSIENT"
        if mid > 0.40 and 0.25 <= flatness <= 0.75:
            return "HYBRID"
        if low < 0.05 and mid < 0.05 and high < 0.05:
            return "RAW"
        return "RAW"

    def update_projection_context(self, x_t, z_t, raw: Mapping[str, float], history: Sequence[StepTrace]):
        psi = x_t[0]
        phi = z_t[0]
        delta = abs(phi - psi)
        prev_delta = history[-1].projections["u_delta"] if history else 0.0
        delta_dot = max(0.0, delta - prev_delta)
        prev_phi = history[-1].z_t[0] if history else phi
        prev2_phi = history[-2].z_t[0] if len(history) >= 2 else prev_phi
        gamma = abs(phi - 2.0 * prev_phi + prev2_phi)

        basis = self.basis_id(raw)
        centroid = max(0.0, min(1.0, raw.get("spectral_centroid", 0.0)))
        flatness = max(0.0, min(1.0, raw.get("spectral_flatness", 0.0)))
        transient = max(0.0, min(1.0, raw.get("transient_ratio", 0.0)))
        coherence = max(0.0, min(1.0, raw.get("coherence", 0.5)))
        energy = max(0.0, min(1.0, raw.get("energy", 0.0)))
        confidence = max(0.0, min(1.0, raw.get("confidence", 0.5)))
        noise = max(0.0, min(1.0, raw.get("noise", 0.0)))

        # Basis-specific field shaping.
        if basis == "SPECTRAL":
            hazard = 0.25 * noise + 0.15 * transient + 0.10 * flatness
            gain = 0.70 * centroid + 0.30 * coherence
            chi = coherence * (1.0 - hazard)
        elif basis == "TRANSIENT":
            hazard = 0.20 * noise + 0.30 * transient + 0.15 * flatness
            gain = 0.65 * transient + 0.35 * confidence
            chi = confidence * (1.0 - hazard)
        elif basis == "HYBRID":
            hazard = 0.20 * noise + 0.20 * transient + 0.10 * flatness
            gain = 0.40 * centroid + 0.25 * transient + 0.35 * coherence
            chi = 0.5 * coherence + 0.5 * confidence
        else:  # RAW
            hazard = 0.10 * noise + 0.05 * transient + 0.05 * flatness
            gain = 0.50 * confidence + 0.50 * energy
            chi = confidence * (1.0 - hazard)

        tau = min(1.0, 0.50 * delta + 0.25 * gamma + 0.25 * hazard)
        cost = min(1.0, 0.40 * hazard + 0.30 * noise + 0.30 * flatness)
        bias = confidence
        phi_margin = max(0.0, min(1.0, 0.55 * (1.0 - tau) + 0.25 * bias + 0.20 * gain))
        accumulation_drive = max(0.0, min(1.0, 0.40 * hazard + 0.30 * tau + 0.30 * noise))
        return {
            "basis": basis,
            "u_phi": phi_margin,
            "u_delta": delta,
            "u_delta_dot": delta_dot,
            "u_gamma": max(0.0, min(1.0, gamma)),
            "u_tau": tau,
            "u_chi": max(0.0, min(1.0, chi)),
            "u_gain": max(0.0, min(1.0, gain)),
            "u_cost": max(0.0, min(1.0, cost)),
            "u_bias": max(0.0, min(1.0, bias)),
            "u_pacing": max(delta, hazard),
            "u_accum": accumulation_drive,
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
            return (("HALT", "RAW"),)
        if state == ControlState.HOLD:
            return (("HOLD", "HYBRID"), ("HOLD", "RAW"))
        if state == ControlState.DMT:
            return (("DMT", "TRANSIENT"),)
        return (("COMMIT", "RAW"), ("COMMIT", "SPECTRAL"), ("COMMIT", "TRANSIENT"), ("COMMIT", "HYBRID"))

    def tie_break(self, candidates):
        # Prefer the candidate matching the current basis when available.
        return sorted(candidates)[0]
