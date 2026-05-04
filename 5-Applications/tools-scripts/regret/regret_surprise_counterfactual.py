#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Regret, surprise, and counterfactual mechanics for the legal OmniToken action bot.

These mechanisms answer three questions that the compliance front layer alone
cannot answer:

1. **Surprise**: how far did this candidate deviate from what we expected?
2. **Regret**: did our decision cost us (or save us) relative to the best
   alternative we could have taken?
3. **Counterfactual**: what would have happened if we had chosen differently?

The market simulation lane uses these to tune entry/exit thresholds.
The compliance lane uses them to tune *refusal* thresholds — when the bot
chooses *not* to act, it should still learn whether that refusal was correct.

Design principles (from BEHAVIORAL_FORMALISM and MARKET_SIMULATION_REGRET_COMPRESSION_BRIDGE):
- Every decision emits a predicted value and a realized value
- Surprise = log(1 + |predicted - realized|) — bounded, doesn't blow up
- Regret = max(0, best_alternative - chosen) — standard external regret
- Counterfactuals enumerate the actions we didn't take and estimate their value
- Threshold adaptation learns from missed opportunities vs bad actions
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


# ── Surprise ─────────────────────────────────────────────────────────────────

def log_surprise(predicted: float, actual: float) -> float:
    """Log-scaled surprise: 0 = no surprise, higher = more deviation.

    Uses log(1 + |delta|) to prevent outlier blowup.
    """
    return math.log1p(abs(actual - predicted))


# ── Regret ───────────────────────────────────────────────────────────────────

@dataclass
class RegretRecord:
    """A single decision and its regret outcome."""
    candidate_id: str
    decision: str  # prepare_submit | hold_for_review | freeze_and_escalate | block_submit
    expected_value: float
    realized_value: float
    best_alternative_value: float
    surprise: float
    timestamp_utc: str

    @property
    def decision_regret(self) -> float:
        """Opportunity cost vs the best alternative we didn't take."""
        return max(0.0, self.best_alternative_value - self.realized_value)

    @property
    def is_missed_opportunity(self) -> bool:
        """We blocked/held but the alternative would have been profitable."""
        return (
            self.decision in ("block_submit", "hold_for_review", "freeze_and_escalate")
            and self.best_alternative_value > self.realized_value
        )

    @property
    def is_bad_action(self) -> bool:
        """We acted and the alternative would have been better."""
        return self.decision == "prepare_submit" and self.best_alternative_value > self.realized_value


def compute_regret(
    chosen_value: float,
    alternative_values: Sequence[float],
) -> Tuple[float, float]:
    """Return (regret, best_alternative_value).

    Standard external-regret: max(0, best_alt - chosen).
    """
    if not alternative_values:
        return 0.0, 0.0
    best_alt = max(alternative_values)
    return max(0.0, best_alt - chosen_value), best_alt


# ── Counterfactual Analysis ──────────────────────────────────────────────────

@dataclass
class CounterfactualScenario:
    """One alternative action we didn't take, with estimated outcomes."""
    alternative_action: str
    estimated_value: float
    estimated_risk: float
    rationale: str


def generate_counterfactuals(
    candidate: Mapping[str, Any],
    chosen_action: str,
    front_layer: Mapping[str, Any],
) -> List[CounterfactualScenario]:
    """Bounded counterfactual alternatives for a candidate.

    For each action we *didn't* take, estimate what would have happened
    based on observable features and front-layer flags.

    Estimates are deliberately conservative — the bot should not
    fantasize about profits it cannot verify.
    """
    alternatives: List[CounterfactualScenario] = []
    economic_purpose = str(front_layer.get("economic_purpose", "unknown"))
    risk_flags = sum(
        1 for k in (
            "retail_disadvantage_flag",
            "manipulation_risk_flag",
            "wash_trading_risk_flag",
            "spoofing_pattern_flag",
            "user_order_targeting_flag",
        )
        if front_layer.get(k)
    )

    if chosen_action != "prepare_submit":
        # If risk flags are high, estimated value of submitting is low
        submit_value = 0.0 if risk_flags >= 2 else 0.3
        submit_risk = 0.8 if risk_flags >= 2 else 0.3
        alternatives.append(CounterfactualScenario(
            alternative_action="prepare_submit",
            estimated_value=submit_value,
            estimated_risk=submit_risk,
            rationale=(
                f"Submitting would expose the candidate to downstream markets; "
                f"{risk_flags} abuse risk flags present. "
                f"Economic purpose: {economic_purpose}."
            ),
        ))

    if chosen_action != "hold_for_review":
        hold_value = 0.5 if risk_flags == 0 else 0.2
        hold_risk = 0.1
        alternatives.append(CounterfactualScenario(
            alternative_action="hold_for_review",
            estimated_value=hold_value,
            estimated_risk=hold_risk,
            rationale=(
                "Holding for review defers the decision but preserves optionality; "
                "review cost is bounded and the candidate remains observable."
            ),
        ))

    if chosen_action != "freeze_and_escalate":
        freeze_value = 0.1 if risk_flags >= 3 else 0.0
        freeze_risk = 0.05
        alternatives.append(CounterfactualScenario(
            alternative_action="freeze_and_escalate",
            estimated_value=freeze_value,
            estimated_risk=freeze_risk,
            rationale=(
                "Freezing prevents any downstream harm but incurs escalation cost; "
                "only justified when risk flags are numerous or critical."
            ),
        ))

    if chosen_action != "block_submit":
        alternatives.append(CounterfactualScenario(
            alternative_action="block_submit",
            estimated_value=0.0,
            estimated_risk=0.0,
            rationale=(
                "Blocking eliminates risk but also eliminates any possible benefit; "
                "appropriate only when the candidate fails hard jurisdictional or "
                "asset-whitelist checks."
            ),
        ))

    return alternatives


# ── Adaptive Threshold Tuning from Counterfactual Regret ─────────────────────

@dataclass
class ThresholdState:
    """Tracks how action thresholds adapt based on regret signals."""

    # Mirrors MarketActionPolicy structure
    # RSC-1 follow-up: initialize above 0.0 so missed-opportunity decrements (-0.0001/event)
    # have room to operate. At 0.0 (the clamp floor), every missed-opportunity decrement is
    # silently discarded — the entry bar cannot self-loosen from baseline.
    # 0.005 = 0.5% improvement required initially; ≈50 missed-opp events to reach neutral.
    entry_improvement_fraction: float = 0.005
    max_loss_fraction: float = 0.05
    expected_slippage_fraction: float = 0.0025

    # Regret tracking
    total_regret: float = 0.0
    missed_opportunities: int = 0
    bad_actions: int = 0
    total_decisions: int = 0

    learning_rate: float = 0.01

    def update(self, record: RegretRecord) -> None:
        self.total_decisions += 1
        self.total_regret += record.decision_regret

        if record.is_missed_opportunity:
            self.missed_opportunities += 1
            # Too conservative: loosen loss tolerance, lower entry bar
            self.max_loss_fraction += self.learning_rate * record.decision_regret
            # RSC-1 fix: entry_improvement_fraction was never updated
            self.entry_improvement_fraction -= self.learning_rate * 0.01

        if record.is_bad_action:
            self.bad_actions += 1
            # Too aggressive: tighten loss tolerance, raise slippage expectation, raise entry bar
            self.max_loss_fraction -= self.learning_rate * record.decision_regret
            self.expected_slippage_fraction += self.learning_rate * 0.5
            # RSC-1 fix: entry_improvement_fraction was never updated
            self.entry_improvement_fraction += self.learning_rate * 0.01

        # Clamp to sane bounds.
        # RSC-B: once entry_improvement_fraction reaches 0.0, missed-opportunity
        # decrements (-0.0001/event) are silently absorbed. After ~50 missed-opp
        # events from the 0.005 baseline the threshold is fully loosened and the
        # learning signal is structurally saturated — the counter keeps incrementing
        # but threshold state no longer changes. This is intentional: the system
        # is already maximally permissive on entries. The saturation is observable
        # via missed_opportunities count vs the ~50-event horizon.
        self.max_loss_fraction = max(0.01, min(0.20, self.max_loss_fraction))
        self.expected_slippage_fraction = max(0.001, min(0.05, self.expected_slippage_fraction))
        self.entry_improvement_fraction = max(0.0, min(0.10, self.entry_improvement_fraction))

    def regret_rate(self) -> float:
        return self.total_regret / max(self.total_decisions, 1)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "entry_improvement_fraction": round(self.entry_improvement_fraction, 6),
            "max_loss_fraction": round(self.max_loss_fraction, 6),
            "expected_slippage_fraction": round(self.expected_slippage_fraction, 6),
            "total_regret": round(self.total_regret, 6),
            "regret_per_decision": round(self.regret_rate(), 6),
            "missed_opportunities": self.missed_opportunities,
            "bad_actions": self.bad_actions,
            "total_decisions": self.total_decisions,
            "learning_rate": self.learning_rate,
        }


# ── Action Record Enrichment ────────────────────────────────────────────────

def enrich_action_with_regret_surprise_counterfactual(
    action: Dict[str, Any],
    candidate: Mapping[str, Any],
    predicted_value: float,
    realized_value: float,
    alternative_values: Sequence[float],
) -> Dict[str, Any]:
    """Add regret, surprise, and counterfactual fields to an action record.

    Called *after* compliance front layer produces its decision but
    *before* the action is written to the output log.
    """
    surprise = log_surprise(predicted_value, realized_value)
    counterfactuals = generate_counterfactuals(
        candidate,
        action.get("action", "hold_for_review"),
        action,
    )

    # RSC-A fix: best_alternative_value and best_alternative_action must come from
    # the same source.  Previously regret used external alternative_values while
    # best_alternative_action used internal counterfactual estimates — the two could
    # point to different scenarios.  Fix: derive alternative_values from counterfactuals
    # when available so both fields are consistent by construction.  External
    # alternative_values is kept as API fallback when no counterfactuals exist.
    cf_values = [cf.estimated_value for cf in counterfactuals]
    regret_values = cf_values if cf_values else list(alternative_values)
    regret, best_alt = compute_regret(realized_value, regret_values)

    enriched = dict(action)
    enriched["predicted_value"] = round(predicted_value, 6)
    enriched["realized_value"] = round(realized_value, 6)
    enriched["surprise"] = round(surprise, 6)
    enriched["regret"] = round(regret, 6)
    enriched["best_alternative_value"] = round(best_alt, 6)
    enriched["best_alternative_action"] = (
        max(counterfactuals, key=lambda c: c.estimated_value).alternative_action
        if counterfactuals
        else "none"
    )
    enriched["counterfactuals"] = [
        {
            "alternative_action": cf.alternative_action,
            "estimated_value": round(cf.estimated_value, 6),
            "estimated_risk": round(cf.estimated_risk, 6),
            "rationale": cf.rationale,
        }
        for cf in counterfactuals
    ]
    enriched["is_missed_opportunity"] = (
        action.get("action") in ("block_submit", "hold_for_review", "freeze_and_escalate")
        and best_alt > realized_value
    )
    enriched["is_bad_action"] = (
        action.get("action") == "prepare_submit"
        and best_alt > realized_value
    )
    return enriched


def surprise_regret_summary(actions: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Summary statistics for surprise and regret across a batch of actions."""
    surprises = [float(a.get("surprise", 0.0)) for a in actions]
    regrets = [float(a.get("regret", 0.0)) for a in actions]
    missed = sum(1 for a in actions if a.get("is_missed_opportunity"))
    bad = sum(1 for a in actions if a.get("is_bad_action"))

    def _pct(vals, p):
        if not vals:
            return 0.0
        s = sorted(vals)
        return s[min(int(len(s) * p), len(s) - 1)]

    n = max(len(actions), 1)
    return {
        "surprise_mean": round(sum(surprises) / n, 6),
        "surprise_median": round(_pct(surprises, 0.5), 6),
        "surprise_p90": round(_pct(surprises, 0.9), 6),
        "regret_mean": round(sum(regrets) / n, 6),
        "regret_median": round(_pct(regrets, 0.5), 6),
        "regret_p90": round(_pct(regrets, 0.9), 6),
        "missed_opportunities": missed,
        "bad_actions": bad,
        "missed_opportunity_rate": round(missed / n, 6),
        "bad_action_rate": round(bad / n, 6),
    }
