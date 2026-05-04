#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
Shared market action policy surface.

This replaces older fixed-edge shorthand with explicit, bounded settings:

- entry improvement fraction
- max tolerated loss fraction
- expected slippage fraction
- adaptive activation pause when adverse reinforcement appears

The default posture is intentionally ordinary: no fixed magical edge is assumed.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass
class MarketActionPolicy:
    entry_improvement_fraction: float = 0.0
    max_loss_fraction: float = 0.05
    expected_slippage_fraction: float = 0.0025
    activation_pause_seconds: int = 60
    max_activation_pause_seconds: int = 300
    reinforcement_pause_multiplier: float = 3.0
    rationale: str = (
        "No fixed impossible-edge assumption; action must be mitigated explicitly."
    )

    @classmethod
    def from_env(cls, prefix: str = "MARKET_ACTION") -> "MarketActionPolicy":
        # Clamp all env-var params to sane ranges so misconfiguration
        # cannot invert buy logic, create tight-loop order floods, or
        # produce negative reference prices.
        activation_pause = max(1, _env_int(f"{prefix}_ACTIVATION_PAUSE_SECONDS", 60))
        max_activation_pause = max(
            activation_pause,
            _env_int(f"{prefix}_MAX_ACTIVATION_PAUSE_SECONDS", 300),
        )
        return cls(
            entry_improvement_fraction=max(0.0, min(0.50, _env_float(
                f"{prefix}_ENTRY_IMPROVEMENT_FRACTION", 0.0
            ))),
            max_loss_fraction=max(0.001, min(0.50, _env_float(
                f"{prefix}_MAX_LOSS_FRACTION", 0.05
            ))),
            expected_slippage_fraction=max(0.0, min(0.10, _env_float(
                f"{prefix}_EXPECTED_SLIPPAGE_FRACTION", 0.0025
            ))),
            activation_pause_seconds=activation_pause,
            max_activation_pause_seconds=max_activation_pause,
            reinforcement_pause_multiplier=max(1.0, _env_float(
                f"{prefix}_REINFORCEMENT_PAUSE_MULTIPLIER", 3.0
            )),
            rationale=os.getenv(
                f"{prefix}_RATIONALE",
                "No fixed impossible-edge assumption; action must be mitigated explicitly.",
            ),
        )

    def entry_reference_price(self, basis_price: float) -> float:
        return basis_price * (1.0 - self.entry_improvement_fraction)

    def loss_alert_price(self, basis_price: float) -> float:
        return basis_price * (1.0 - self.max_loss_fraction)

    def reinforcement_trigger_fraction(self) -> float:
        return max(
            self.entry_improvement_fraction + self.expected_slippage_fraction,
            self.expected_slippage_fraction * 2.0,
        )

    def gap_fraction(self, current_price: float, reference_price: float) -> float:
        if reference_price <= 0.0:
            return 0.0
        return max(0.0, (current_price - reference_price) / reference_price)

    def detects_loss_reinforcement(
        self,
        *,
        current_price: float,
        reference_price: float,
        last_price: Optional[float] = None,
        adverse_streak: int = 0,
    ) -> bool:
        gap = self.gap_fraction(current_price, reference_price)
        trending_worse = last_price is not None and current_price >= last_price
        materially_outside = gap >= self.reinforcement_trigger_fraction()
        repeated_adverse = adverse_streak >= 2 and gap > 0.0
        return materially_outside and (trending_worse or repeated_adverse)

    def activation_pause_for(
        self,
        *,
        loss_reinforcement: bool,
        adverse_streak: int = 0,
    ) -> int:
        if not loss_reinforcement:
            return self.activation_pause_seconds
        scaled = int(
            self.activation_pause_seconds
            * self.reinforcement_pause_multiplier
            * max(1.0, 1.0 + (0.5 * adverse_streak))
        )
        return min(self.max_activation_pause_seconds, max(self.activation_pause_seconds, scaled))

    def snapshot(self, market_price: float) -> Dict[str, Any]:
        return {
            "policy_mode": "risk_aware_action_policy",
            "market_price": round(market_price, 8),
            "entry_reference_price": round(self.entry_reference_price(market_price), 8),
            "entry_improvement_fraction": round(self.entry_improvement_fraction, 8),
            "entry_improvement_pct": round(self.entry_improvement_fraction * 100.0, 6),
            "max_loss_fraction": round(self.max_loss_fraction, 8),
            "max_loss_pct": round(self.max_loss_fraction * 100.0, 6),
            "loss_alert_price": round(self.loss_alert_price(market_price), 8),
            "expected_slippage_fraction": round(self.expected_slippage_fraction, 8),
            "expected_slippage_pct": round(
                self.expected_slippage_fraction * 100.0, 6
            ),
            "activation_pause_seconds": int(self.activation_pause_seconds),
            "max_activation_pause_seconds": int(self.max_activation_pause_seconds),
            "reinforcement_pause_multiplier": round(
                self.reinforcement_pause_multiplier, 6
            ),
            "reinforcement_trigger_fraction": round(
                self.reinforcement_trigger_fraction(), 8
            ),
            "reinforcement_trigger_pct": round(
                self.reinforcement_trigger_fraction() * 100.0, 6
            ),
            "rationale": self.rationale,
        }

    def brief(self) -> str:
        return (
            f"entry improvement {self.entry_improvement_fraction * 100.0:.2f}% | "
            f"max loss {self.max_loss_fraction * 100.0:.2f}% | "
            f"slippage {self.expected_slippage_fraction * 100.0:.2f}% | "
            f"pause {self.activation_pause_seconds}s->{self.max_activation_pause_seconds}s"
        )
