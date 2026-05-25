# PTOS: LAYER=INFRA / DOMAIN=AUTOMATION / CONDITION=ALPHA
"""
Q16_16 fixed-point arithmetic for deterministic compute across all substrates.
All thresholds and metric values are stored as Q16_16 integers.
One = 0x00010000 = 65536. Float is forbidden in compute paths.
"""
from __future__ import annotations

Q16_ONE: int = 0x00010000
Q16_HALF: int = 0x00008000


def to_q16(value: float) -> int:
    """Convert a float to Q16_16. Only allowed at the external boundary."""
    return int(round(value * Q16_ONE))


def from_q16(value: int) -> float:
    """Convert Q16_16 back to float. Only for display, never in compute."""
    return value / Q16_ONE


def ratio_q16(numerator: float, denominator: float) -> int:
    """Compute Q16_16 ratio of two floats, clamped to [0, 1]."""
    if denominator == 0:
        return 0
    r = numerator / denominator
    r = max(0.0, min(1.0, r))
    return int(r * Q16_ONE)
