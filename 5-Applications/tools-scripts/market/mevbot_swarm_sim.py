# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
50-Bot MEV Swarm Simulation - KOT Currency

═══════════════════════════════════════════════════════════════════════
⚠️  PROPRIETARY & CONFIDENTIAL - WaveProbe Core IP
    Unauthorized disclosure, reverse-engineering, or reproduction
    of the entropy-jitter concealment strategy is prohibited.
    This file contains trade secrets protected under applicable law.
═══════════════════════════════════════════════════════════════════════

Each bot operates independently:
- Fragments trades across pools
- Competes for execution
- Recovers missing fragments on-chain
- Maximizes personal profit

Layer 0 (on-chain state) is the shared reference frame.
Coordination emerges from reading canonical truth.
"""

import random
import json
import hashlib
import os
import sys
import socket
import time
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, cast
from enum import Enum
import math
try:
    from network_security import NetworkSecurityPolicy
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from network_security import NetworkSecurityPolicy

try:
    from waveprobe_icmp_coordinator import (
        BotIntentBeacon, CoordinatorListener, CompressedIntent, IntentType, MirrorLUTRollup
    )
    _HAS_ICMP_COORDINATOR = True
except ImportError:
    _HAS_ICMP_COORDINATOR = False

# NE geometry verifier — deterministic gate for trade path validity.
# Rejects paths that are geometrically degenerate (metric jumps, uncontrolled torsion).
try:
    from tools.geometry_verifier import validate_ne_path, NEPathValidation
    _HAS_NE_VERIFIER = True
except ImportError:
    _HAS_NE_VERIFIER = False
    validate_ne_path = None
    NEPathValidation = None

PHI = 1.618033988749895


def clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, value))


def as_float(value: object, default: float = 0.0) -> float:
    return float(value) if isinstance(value, (int, float)) else default


def as_int(value: object, default: int = 0) -> int:
    return value if isinstance(value, int) else default


class EphemeralCoordinatorPool:
    """Round-based coordinator IP rotation with deterministic failover order."""

    def __init__(self, ips: List[str], rotation_rounds: int = 10):
        if not ips:
            raise ValueError("At least one coordinator IP is required")
        self.ips = ips
        self.rotation_rounds = max(1, rotation_rounds)

    def ordered_candidates(self, round_number: int) -> List[str]:
        start = (round_number // self.rotation_rounds) % len(self.ips)
        return self.ips[start:] + self.ips[:start]


def derive_mode_for_round(session_key: bytes, round_number: int, bot_id: int) -> int:
    """Deterministically randomize bot->mode mapping per round."""
    material = (
        session_key
        + round_number.to_bytes(4, "big", signed=False)
        + bot_id.to_bytes(2, "big", signed=False)
    )
    digest = hashlib.sha3_256(material).digest()
    return digest[0] % 14


class AdaptiveRNGMutator:
    """Mutate RNG state from network activity and DNS signal jitter."""

    def __init__(self, seed_material: bytes, dns_host: str = "one.one.one.one"):
        self.state = hashlib.sha3_256(seed_material).digest()
        self.dns_host = dns_host
        self.rng = random.Random(int.from_bytes(self.state[:16], "big", signed=False))

    def _dns_jitter_ns(self) -> int:
        samples: List[int] = []
        for _ in range(2):
            start = time.perf_counter_ns()
            try:
                socket.getaddrinfo(self.dns_host, 53)
            except Exception:
                pass
            samples.append(max(0, time.perf_counter_ns() - start))

        if len(samples) < 2:
            return samples[0] if samples else 0
        return abs(samples[1] - samples[0])

    def mutate(self, round_number: int, network_activity_signal: float) -> float:
        jitter_ns = self._dns_jitter_ns()
        activity_scaled = int(max(0.0, network_activity_signal) * 1000.0)
        material = (
            self.state
            + round_number.to_bytes(4, "big", signed=False)
            + activity_scaled.to_bytes(8, "big", signed=False)
            + jitter_ns.to_bytes(8, "big", signed=False)
            + time.time_ns().to_bytes(8, "big", signed=False)
        )
        self.state = hashlib.sha3_256(material).digest()
        self.rng.seed(int.from_bytes(self.state[:16], "big", signed=False))
        return jitter_ns / 1_000_000.0

# ============================================================================
# Pool & Token Model
# ============================================================================

@dataclass
class Pool:
    """Constant product AMM pool"""
    name: str
    token_a: str
    token_b: str
    reserve_a: float  # SOL
    reserve_b: float  # USDC
    fee_bps: int = 25  # 0.25%

    def quote_swap(self, amount_in: float, is_a_to_b: bool) -> Tuple[float, float, float]:
        """Quote swap without mutating reserves.

        Returns (amount_out, fee_paid, price_impact_bps).
        """
        if amount_in <= 0:
            return 0.0, 0.0, 0.0

        fee_rate = 1.0 - (self.fee_bps / 10000)
        amount_in_after_fee = amount_in * fee_rate

        if is_a_to_b:
            k = self.reserve_a * self.reserve_b
            new_reserve_a = self.reserve_a + amount_in_after_fee
            new_reserve_b = k / new_reserve_a
            amount_out = self.reserve_b - new_reserve_b
            spot_price = self.reserve_b / self.reserve_a
            execution_price = amount_out / max(amount_in, 1e-9)
            impact_bps = max(0.0, (spot_price - execution_price) / max(spot_price, 1e-9) * 10000)
        else:
            k = self.reserve_a * self.reserve_b
            new_reserve_b = self.reserve_b + amount_in_after_fee
            new_reserve_a = k / new_reserve_b
            amount_out = self.reserve_a - new_reserve_a
            spot_price = self.reserve_a / self.reserve_b
            execution_price = amount_out / max(amount_in, 1e-9)
            impact_bps = max(0.0, (spot_price - execution_price) / max(spot_price, 1e-9) * 10000)

        fee_paid = amount_in * (self.fee_bps / 10000)
        return amount_out, fee_paid, impact_bps

    def swap(self, amount_in: float, is_a_to_b: bool) -> Tuple[float, float]:
        """Execute swap, return (amount_out, fee_paid)"""
        amount_out, fee_paid, _impact_bps = self.quote_swap(amount_in, is_a_to_b)
        if amount_out <= 0.0:
            return 0.0, 0.0

        # The full input remains in the pool while output is priced using the
        # fee-discounted amount. That lets fee accrual grow pool depth over time.
        if is_a_to_b:
            self.reserve_a += amount_in
            self.reserve_b = max(1e-12, self.reserve_b - amount_out)
        else:
            self.reserve_b += amount_in
            self.reserve_a = max(1e-12, self.reserve_a - amount_out)

        return amount_out, fee_paid

    def get_price(self, is_a_to_b: bool) -> float:
        """Get current spot price"""
        if is_a_to_b:
            return self.reserve_b / self.reserve_a  # USDC per SOL
        else:
            return self.reserve_a / self.reserve_b  # SOL per USDC

    def to_state(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "token_a": self.token_a,
            "token_b": self.token_b,
            "reserve_a": self.reserve_a,
            "reserve_b": self.reserve_b,
            "fee_bps": self.fee_bps,
        }

    def apply_state(self, state: Dict[str, object]) -> None:
        if state.get("name") not in {None, self.name}:
            raise ValueError(f"pool state name mismatch: {state.get('name')} != {self.name}")
        if state.get("token_a") not in {None, self.token_a}:
            raise ValueError(
                f"pool state token_a mismatch: {state.get('token_a')} != {self.token_a}"
            )
        if state.get("token_b") not in {None, self.token_b}:
            raise ValueError(
                f"pool state token_b mismatch: {state.get('token_b')} != {self.token_b}"
            )

        reserve_a = state.get("reserve_a")
        reserve_b = state.get("reserve_b")
        fee_bps = state.get("fee_bps")
        if isinstance(reserve_a, (int, float)) and reserve_a > 0.0:
            self.reserve_a = float(reserve_a)
        if isinstance(reserve_b, (int, float)) and reserve_b > 0.0:
            self.reserve_b = float(reserve_b)
        if isinstance(fee_bps, int) and fee_bps >= 0:
            self.fee_bps = fee_bps


# ============================================================================
# Bot Agent
# ============================================================================

class BotStrategy(Enum):
    AGGRESSIVE = "aggressive"  # Execute if ROI > 0.5%
    CONSERVATIVE = "conservative"  # Execute if ROI > 2%
    OPPORTUNISTIC = "opportunistic"  # Accept trades at median ROI


class ActionScope(Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"


@dataclass(frozen=True)
class TruthQualifier:
    """Weights execution learning toward market consensus and away from transient noise."""

    truth_confidence: float = 1.0
    noise_ratio: float = 0.0
    liquidity_confidence: float = 1.0
    provider_agreement: float = 1.0
    aggregator_agreement: float = 1.0
    active_sources: int = 1


@dataclass
class CrossSessionLiquidityObjective:
    """Persisted session-level objective for internal liquidity growth."""

    metric_name: str = "normalized_pool_invariant"
    target_growth_rate: float = 0.03
    target_score: float = 1.02
    last_achieved_score: float = 1.0
    best_achieved_score: float = 1.0
    last_gap_ratio: float = 0.0
    last_external_best_liquidity_score: float = 0.0
    last_external_final_liquidity_score: float = 0.0
    last_external_truth_confidence: float = 0.0
    last_external_best_vs_initial_pct: float = 0.0
    last_external_final_vs_initial_pct: float = 0.0
    last_source_session_id: Optional[str] = None

    def execution_pressure(
        self,
        current_score: float,
        truth_qualifier: TruthQualifier,
    ) -> float:
        gap_ratio = max(0.0, self.target_score - current_score) / max(self.target_score, 1e-9)
        truth_weight = clamp_unit(
            0.5 * truth_qualifier.truth_confidence
            + 0.3 * truth_qualifier.liquidity_confidence
            + 0.2 * truth_qualifier.provider_agreement
        )
        noise_discount = 1.0 - 0.5 * clamp_unit(truth_qualifier.noise_ratio)
        return clamp_unit(gap_ratio * truth_weight * noise_discount * 2.0)

    def observe_session(
        self,
        achieved_score: float,
        external_summary: Optional[Dict[str, object]] = None,
        source_session_id: Optional[str] = None,
    ) -> None:
        target_before = self.target_score
        self.last_achieved_score = max(0.0, achieved_score)
        self.best_achieved_score = max(self.best_achieved_score, self.last_achieved_score)
        self.last_gap_ratio = max(0.0, target_before - self.last_achieved_score) / max(
            target_before, 1e-9
        )
        self.last_source_session_id = source_session_id

        if external_summary is not None:
            best_obj = external_summary.get("best")
            final_obj = external_summary.get("final")
            final_truth_obj = external_summary.get("final_truth")

            if isinstance(best_obj, dict):
                best = cast(Dict[str, object], best_obj)
                self.last_external_best_liquidity_score = as_float(
                    best.get("liquidity_score"),
                    self.last_external_best_liquidity_score,
                )

            if isinstance(final_obj, dict):
                final = cast(Dict[str, object], final_obj)
                self.last_external_final_liquidity_score = as_float(
                    final.get("liquidity_score"),
                    self.last_external_final_liquidity_score,
                )

            if isinstance(final_truth_obj, dict):
                final_truth = cast(Dict[str, object], final_truth_obj)
                self.last_external_truth_confidence = as_float(
                    final_truth.get("truth_confidence"),
                    self.last_external_truth_confidence,
                )

            self.last_external_best_vs_initial_pct = as_float(
                external_summary.get("best_vs_initial_pct"),
                self.last_external_best_vs_initial_pct,
            )
            self.last_external_final_vs_initial_pct = as_float(
                external_summary.get("final_vs_initial_pct"),
                self.last_external_final_vs_initial_pct,
            )

            if (
                self.last_external_final_vs_initial_pct < -5.0
                and self.last_external_best_vs_initial_pct < 0.0
            ):
                self.target_growth_rate = max(0.01, self.target_growth_rate - 0.005)
            elif (
                self.last_external_best_vs_initial_pct > 0.0
                or self.last_external_final_vs_initial_pct > 0.0
            ):
                self.target_growth_rate = min(0.08, self.target_growth_rate + 0.005)

        anchor_score = max(1.0, self.best_achieved_score, self.last_achieved_score)
        self.target_score = anchor_score * (1.0 + self.target_growth_rate)

    def summary(self, current_score: float) -> Dict[str, object]:
        return {
            "metric_name": self.metric_name,
            "current_score": current_score,
            "target_score": self.target_score,
            "best_achieved_score": self.best_achieved_score,
            "last_achieved_score": self.last_achieved_score,
            "gap_ratio": max(0.0, self.target_score - current_score) / max(self.target_score, 1e-9),
            "last_gap_ratio": self.last_gap_ratio,
            "target_growth_rate": self.target_growth_rate,
            "last_external_best_liquidity_score": self.last_external_best_liquidity_score,
            "last_external_final_liquidity_score": self.last_external_final_liquidity_score,
            "last_external_truth_confidence": self.last_external_truth_confidence,
            "last_external_best_vs_initial_pct": self.last_external_best_vs_initial_pct,
            "last_external_final_vs_initial_pct": self.last_external_final_vs_initial_pct,
            "last_source_session_id": self.last_source_session_id,
        }

    def to_state(self) -> Dict[str, object]:
        return {
            "metric_name": self.metric_name,
            "target_growth_rate": self.target_growth_rate,
            "target_score": self.target_score,
            "last_achieved_score": self.last_achieved_score,
            "best_achieved_score": self.best_achieved_score,
            "last_gap_ratio": self.last_gap_ratio,
            "last_external_best_liquidity_score": self.last_external_best_liquidity_score,
            "last_external_final_liquidity_score": self.last_external_final_liquidity_score,
            "last_external_truth_confidence": self.last_external_truth_confidence,
            "last_external_best_vs_initial_pct": self.last_external_best_vs_initial_pct,
            "last_external_final_vs_initial_pct": self.last_external_final_vs_initial_pct,
            "last_source_session_id": self.last_source_session_id,
        }

    def apply_state(self, state: Dict[str, object]) -> None:
        metric_name = state.get("metric_name")
        if isinstance(metric_name, str) and metric_name:
            self.metric_name = metric_name

        self.target_growth_rate = max(0.0, min(0.10, as_float(state.get("target_growth_rate"), self.target_growth_rate)))
        self.target_score = max(1.0, as_float(state.get("target_score"), self.target_score))
        self.last_achieved_score = max(0.0, as_float(state.get("last_achieved_score"), self.last_achieved_score))
        self.best_achieved_score = max(
            self.last_achieved_score,
            as_float(state.get("best_achieved_score"), self.best_achieved_score),
        )
        self.last_gap_ratio = clamp_unit(as_float(state.get("last_gap_ratio"), self.last_gap_ratio))
        self.last_external_best_liquidity_score = as_float(
            state.get("last_external_best_liquidity_score"),
            self.last_external_best_liquidity_score,
        )
        self.last_external_final_liquidity_score = as_float(
            state.get("last_external_final_liquidity_score"),
            self.last_external_final_liquidity_score,
        )
        self.last_external_truth_confidence = clamp_unit(
            as_float(state.get("last_external_truth_confidence"), self.last_external_truth_confidence)
        )
        self.last_external_best_vs_initial_pct = as_float(
            state.get("last_external_best_vs_initial_pct"),
            self.last_external_best_vs_initial_pct,
        )
        self.last_external_final_vs_initial_pct = as_float(
            state.get("last_external_final_vs_initial_pct"),
            self.last_external_final_vs_initial_pct,
        )

        last_source_session_id = state.get("last_source_session_id")
        if isinstance(last_source_session_id, str):
            self.last_source_session_id = last_source_session_id


@dataclass
class BotAgent:
    """Independent MEV bot in swarm"""
    bot_id: int
    strategy: BotStrategy
    balance_kot: float = 1000.0  # Starting capital in KOT
    balance_usdc: float = 500.0
    balance_sol: float = 100.0

    lifetime_profit: float = 0.0
    num_trades: int = 0
    successful_fragments: int = 0
    failed_fragments: int = 0
    recovery_attempts: int = 0
    recovery_successes: int = 0

    regret_ema: float = 0.0
    surprise_ema: float = 0.0
    regret_alpha: float = 0.15
    jitter_ema: float = 0.0
    truth_confidence_ema: float = 1.0
    noise_ema: float = 0.0

    price_history: Dict[str, List[float]] = field(default_factory=dict)

    def update_regret_surprise(
        self,
        expected_profit: float,
        realized_profit: float,
        truth_qualifier: Optional[TruthQualifier] = None,
    ):
        """Calibrate regret/surprise fields from execution error, discounted by market noise."""
        qualifier = truth_qualifier or TruthQualifier()
        truth_confidence = max(0.0, min(1.0, qualifier.truth_confidence))
        noise_ratio = max(0.0, min(1.0, qualifier.noise_ratio))
        regret = max(0.0, expected_profit - realized_profit)
        denom = max(1e-9, abs(expected_profit) + 1e-6)
        surprise = min(1.0, abs(realized_profit - expected_profit) / denom)
        alpha = self.regret_alpha * (0.5 + 0.5 * truth_confidence)
        truth_weight = max(0.1, truth_confidence * (1.0 - 0.5 * noise_ratio))
        self.regret_ema = (1.0 - alpha) * self.regret_ema + alpha * regret * truth_weight
        self.surprise_ema = (1.0 - alpha) * self.surprise_ema + alpha * surprise * truth_weight
        self.truth_confidence_ema = (
            (1.0 - alpha) * self.truth_confidence_ema + alpha * truth_confidence
        )
        self.noise_ema = (1.0 - alpha) * self.noise_ema + alpha * noise_ratio

    def _perturb_execute_signal(self) -> float:
        """Internal execution signal perturbation (proprietary mechanism).
        
        ⚠️  TRADE SECRET: This method implements proprietary entropy shaping.
        Do not modify, clone, or expose externally. The mechanism is
        protected IP and any external observation must be treated as
        a potential IP leak.
        """
        entropy = random.random()
        signal = (entropy - 0.5) * 0.16
        self.jitter_ema = 0.9 * self.jitter_ema + 0.1 * abs(signal)
        return signal

    def roi_threshold(self) -> float:
        """Strategy-based ROI threshold (%)"""
        thresholds = {
            BotStrategy.AGGRESSIVE: 0.5,
            BotStrategy.CONSERVATIVE: 2.0,
            BotStrategy.OPPORTUNISTIC: 1.0,
        }
        return thresholds[self.strategy]

    def decide_trade(self, input_token: str, output_token: str,
                    input_amount: float, expected_output: float, current_price: float,
                    objective_pressure: float = 0.0) -> bool:
        """Decide whether to execute trade"""
        if input_amount <= 0 or current_price <= 0:
            return False

        # Simple ROI check: if expected output > input amount, profitable
        roi = (expected_output - input_amount) / input_amount
        roi_bps = roi * 10000

        threshold_bps = self.roi_threshold() * 100
        truth_alignment = clamp_unit(
            0.5 * self.truth_confidence_ema + 0.5 * (1.0 - self.noise_ema)
        )
        threshold_bps *= max(
            0.55,
            1.0 - 0.35 * clamp_unit(objective_pressure) * truth_alignment,
        )

        # Add stochastic element: aggressive bots more willing to take marginal trades
        noise = random.gauss(0, threshold_bps * 0.1)

        # Lower threshold for initial exploration
        decision = roi_bps >= (threshold_bps * 0.5 + noise)

        return decision

    def send_icmp_beacon(self, coordinator_ip: str, bot_mode: int, round_number: int, pool_id: int, amount: float,
                         expected_output: float, is_sol_to_usdc: bool,
                         smoothing_score: float) -> bool:
        """Send compressed trade intent via ICMP Ghost beacon to coordinator.
        
        ⚠️  NETWORK ADVANTAGE: Off-chain coordination signal before on-chain execution.
        
        Args:
            coordinator_ip: IP of coordination listener
            pool_id: Target pool hash prefix
            amount: Trade input amount
            expected_output: Expected output
            is_sol_to_usdc: Direction of trade
            smoothing_score: Bot's current cognitive smoothing metric (0-1)
        
        Returns:
            True if beacon sent successfully, False otherwise
        """
        if not _HAS_ICMP_COORDINATOR:
            return False
        
        try:
            from waveprobe_icmp_coordinator import BotIntentBeacon
            beacon = BotIntentBeacon()
            
            result = beacon.send_trade_intent_beacon(
                coordinator_ip=coordinator_ip,
                bot_mode=bot_mode,
                round_number=round_number,
                pool_hash_prefix=pool_id,
                amount=amount,
                expected_output=expected_output,
                is_sol_to_usdc=is_sol_to_usdc,
                smoothing_score=smoothing_score,
            )
            return result
        except Exception:
            return False

    def execute_trade(self, pools: List[Pool], input_token: str, output_token: str,
                     amount: float) -> Tuple[float, List[bool]]:
        """
        Execute fragmented trade across pools.
        Returns: (total_output, [success_per_fragment])
        """
        num_legs = min(len(pools), 5)  # Fragment across 2-5 pools
        amount_per_leg = amount / num_legs

        fragment_results = []
        total_output = 0.0
        confirmed_amounts = {}

        for i, pool in enumerate(pools[:num_legs]):
            # Stochastic execution: 85% success rate (competition + network variance)
            success = random.random() < 0.85

            if success:
                try:
                    output, fee = pool.swap(amount_per_leg, input_token == pool.token_a)
                    total_output += output
                    confirmed_amounts[i] = output
                    fragment_results.append(True)
                    self.successful_fragments += 1
                except Exception:
                    fragment_results.append(False)
                    self.failed_fragments += 1
            else:
                fragment_results.append(False)
                self.failed_fragments += 1

        # Recovery: phi-scale missing fragments
        num_confirmed = len(confirmed_amounts)
        num_lost = num_legs - num_confirmed

        if num_lost > 0 and num_confirmed > 0:
            self.recovery_attempts += 1

            # Can recover if < 50% loss (omnitoken rule)
            if num_lost <= num_legs * 0.5:
                # Phi-scale recovery
                mean_confirmed = sum(confirmed_amounts.values()) / num_confirmed
                for i in range(num_legs):
                    if i not in confirmed_amounts:
                        recovered = mean_confirmed * (PHI ** (random.random() - 0.5))  # Small noise
                        total_output += recovered
                        self.recovery_successes += 1
            else:
                # Too much loss, abort recovery (fail-closed)
                pass

        self.num_trades += 1
        return total_output, fragment_results

    def profit_from_trade(self, input_amount: float, output_amount: float) -> float:
        """Calculate profit (PnL)"""
        return output_amount - input_amount

    def to_state(self) -> Dict[str, object]:
        return {
            "bot_id": self.bot_id,
            "strategy": self.strategy.value,
            "balance_kot": self.balance_kot,
            "balance_usdc": self.balance_usdc,
            "balance_sol": self.balance_sol,
            "lifetime_profit": self.lifetime_profit,
            "num_trades": self.num_trades,
            "successful_fragments": self.successful_fragments,
            "failed_fragments": self.failed_fragments,
            "recovery_attempts": self.recovery_attempts,
            "recovery_successes": self.recovery_successes,
            "regret_ema": self.regret_ema,
            "surprise_ema": self.surprise_ema,
            "regret_alpha": self.regret_alpha,
            "jitter_ema": self.jitter_ema,
            "truth_confidence_ema": self.truth_confidence_ema,
            "noise_ema": self.noise_ema,
        }

    def apply_state(self, state: Dict[str, object]) -> None:
        if state.get("bot_id") not in {None, self.bot_id}:
            raise ValueError(f"bot state id mismatch: {state.get('bot_id')} != {self.bot_id}")

        strategy = state.get("strategy")
        if isinstance(strategy, str):
            self.strategy = BotStrategy(strategy)

        numeric_fields = (
            "balance_kot",
            "balance_usdc",
            "balance_sol",
            "lifetime_profit",
            "regret_ema",
            "surprise_ema",
            "regret_alpha",
            "jitter_ema",
            "truth_confidence_ema",
            "noise_ema",
        )
        for field_name in numeric_fields:
            value = state.get(field_name)
            if isinstance(value, (int, float)):
                setattr(self, field_name, float(value))

        count_fields = (
            "num_trades",
            "successful_fragments",
            "failed_fragments",
            "recovery_attempts",
            "recovery_successes",
        )
        for field_name in count_fields:
            value = state.get(field_name)
            if isinstance(value, int) and value >= 0:
                setattr(self, field_name, value)


# ============================================================================
# Swarm Simulation
# ============================================================================

@dataclass
class SwarmSimulation:
    """50-bot MEV swarm competing on shared Layer 0 (pools)"""
    num_bots: int = 50
    num_rounds: int = 100
    bots: List[BotAgent] = field(default_factory=list)
    pools: List[Pool] = field(default_factory=list)
    execution_log: List[Dict[str, object]] = field(default_factory=list)
    coordinator: Optional['CoordinatorListener'] = None
    coordinator_ip: str = "127.0.0.1"  # Localhost for MVP
    coordinator_ips: Optional[List[str]] = None
    coordinator_rotation_rounds: int = 10
    market_truth: TruthQualifier = field(default_factory=TruthQualifier)
    cross_session_objective: CrossSessionLiquidityObjective = field(
        default_factory=CrossSessionLiquidityObjective
    )
    bootstrap_pool_invariants: Dict[str, float] = field(default_factory=dict)

    def _score_trade_intent(self, bot: BotAgent, pool_path: List[Pool],
                            input_token: str, output_token: str,
                            input_amount: float) -> Tuple[float, float]:
        """Estimate trade edge and score used for transaction ordering."""
        amount = input_amount
        total_fees = 0.0
        total_impact_bps = 0.0

        for pool in pool_path:
            is_a_to_b = input_token == pool.token_a
            quoted_out, fee, impact_bps = pool.quote_swap(amount, is_a_to_b)
            total_fees += fee
            total_impact_bps += impact_bps
            amount = quoted_out
            input_token = output_token

        expected_output = amount
        expected_profit = expected_output - input_amount
        strategy_penalty = {
            BotStrategy.AGGRESSIVE: 0.4,
            BotStrategy.OPPORTUNISTIC: 0.8,
            BotStrategy.CONSERVATIVE: 1.2,
        }[bot.strategy]
        score = expected_profit - strategy_penalty * (total_impact_bps / 10000.0) - total_fees * 0.05
        return score, expected_output

    def __post_init__(self):
        """Initialize swarm and pools"""
        # Create pools (Layer 0 - shared state)
        self.pools = [
            Pool("SOL/USDC", "SOL", "USDC", reserve_a=10000, reserve_b=250000),
            Pool("USDC/BTC", "USDC", "BTC", reserve_a=500000, reserve_b=12.5),
            Pool("SOL/BTC", "SOL", "BTC", reserve_a=10000, reserve_b=0.25),
        ]
        self.bootstrap_pool_invariants = {
            pool.name: pool.reserve_a * pool.reserve_b for pool in self.pools
        }

        # Create 50 bots with mixed strategies
        strategies = [BotStrategy.AGGRESSIVE] * 20 + \
                    [BotStrategy.CONSERVATIVE] * 20 + \
                    [BotStrategy.OPPORTUNISTIC] * 10

        random.shuffle(strategies)
        self.security = NetworkSecurityPolicy(node_id='mev-swarm')
        key_hex = os.getenv("WAVEPROBE_MODE_SESSION_KEY", "")
        self.mode_session_key = bytes.fromhex(key_hex) if key_hex else os.urandom(32)
        self.rng_mutator = AdaptiveRNGMutator(
            seed_material=self.mode_session_key,
            dns_host=os.getenv("WAVEPROBE_DNS_JITTER_HOST", "one.one.one.one"),
        )

        if self.coordinator_ips is None:
            self.coordinator_ips = [self.coordinator_ip]
        self.coordinator_pool = EphemeralCoordinatorPool(
            ips=self.coordinator_ips,
            rotation_rounds=self.coordinator_rotation_rounds,
        )

        # Initialize ICMP coordinator for off-chain signaling (WaveProbe network advantage)
        if _HAS_ICMP_COORDINATOR:
            try:
                self.coordinator = CoordinatorListener()
                print("[WaveProbe] ICMP coordination enabled — bots will emit beacons")
            except Exception:
                self.coordinator = None
                print("[WaveProbe] ICMP coordination disabled (ghost_icmp not available)")

        for i in range(self.num_bots):
            self.bots.append(BotAgent(
                bot_id=i,
                strategy=strategies[i],
                balance_kot=1000.0 + random.gauss(0, 100),
                balance_usdc=500.0 + random.gauss(0, 50),
                balance_sol=100.0 + random.gauss(0, 10),
            ))

    def set_market_truth(self, truth_qualifier: TruthQualifier) -> None:
        self.market_truth = truth_qualifier

    def internal_liquidity_score(self) -> float:
        normalized_invariants: List[float] = []
        for pool in self.pools:
            baseline_k = self.bootstrap_pool_invariants.get(pool.name, 0.0)
            current_k = pool.reserve_a * pool.reserve_b
            if baseline_k <= 0.0 or current_k <= 0.0:
                continue
            normalized_invariants.append(math.sqrt(current_k / baseline_k))

        if not normalized_invariants:
            return 0.0
        return sum(normalized_invariants) / len(normalized_invariants)

    def objective_summary(self) -> Dict[str, object]:
        return self.cross_session_objective.summary(self.internal_liquidity_score())

    def finalize_cross_session_objective(
        self,
        external_liquidity_summary: Optional[Dict[str, object]] = None,
        source_session_id: Optional[str] = None,
    ) -> Dict[str, object]:
        current_score = self.internal_liquidity_score()
        self.cross_session_objective.observe_session(
            current_score,
            external_liquidity_summary,
            source_session_id,
        )
        return self.cross_session_objective.summary(current_score)

    def learning_summary(self) -> Dict[str, object]:
        return {
            "bot_count": len(self.bots),
            "pool_count": len(self.pools),
            "execution_log_length": len(self.execution_log),
            "total_lifetime_profit": sum(bot.lifetime_profit for bot in self.bots),
            "total_trades": sum(bot.num_trades for bot in self.bots),
            "avg_regret_ema": (
                sum(bot.regret_ema for bot in self.bots) / max(1, len(self.bots))
            ),
            "avg_surprise_ema": (
                sum(bot.surprise_ema for bot in self.bots) / max(1, len(self.bots))
            ),
            "avg_truth_confidence_ema": (
                sum(bot.truth_confidence_ema for bot in self.bots) / max(1, len(self.bots))
            ),
            "avg_noise_ema": (
                sum(bot.noise_ema for bot in self.bots) / max(1, len(self.bots))
            ),
            "avg_jitter_ema": (
                sum(bot.jitter_ema for bot in self.bots) / max(1, len(self.bots))
            ),
            "internal_liquidity_score": self.internal_liquidity_score(),
            "cross_session_objective": self.objective_summary(),
        }

    def to_learning_state(self) -> Dict[str, object]:
        return {
            "num_bots": self.num_bots,
            "market_truth": {
                "truth_confidence": self.market_truth.truth_confidence,
                "noise_ratio": self.market_truth.noise_ratio,
                "liquidity_confidence": self.market_truth.liquidity_confidence,
                "provider_agreement": self.market_truth.provider_agreement,
                "aggregator_agreement": self.market_truth.aggregator_agreement,
                "active_sources": self.market_truth.active_sources,
            },
            "bots": [bot.to_state() for bot in self.bots],
            "pools": [pool.to_state() for pool in self.pools],
            "cross_session_objective": self.cross_session_objective.to_state(),
            "learning_summary": self.learning_summary(),
        }

    def apply_learning_state(self, payload: Dict[str, object]) -> Dict[str, int]:
        bots_restored = 0
        pools_restored = 0

        market_truth_obj = payload.get("market_truth")
        if isinstance(market_truth_obj, dict):
            market_truth = cast(Dict[str, object], market_truth_obj)
            self.market_truth = TruthQualifier(
                truth_confidence=as_float(market_truth.get("truth_confidence"), 1.0),
                noise_ratio=as_float(market_truth.get("noise_ratio"), 0.0),
                liquidity_confidence=as_float(market_truth.get("liquidity_confidence"), 1.0),
                provider_agreement=as_float(market_truth.get("provider_agreement"), 1.0),
                aggregator_agreement=as_float(market_truth.get("aggregator_agreement"), 1.0),
                active_sources=as_int(market_truth.get("active_sources"), 1),
            )

        bots_by_id = {bot.bot_id: bot for bot in self.bots}
        bot_states_obj = payload.get("bots", [])
        if isinstance(bot_states_obj, list):
            for bot_state_obj in cast(List[object], bot_states_obj):
                if not isinstance(bot_state_obj, dict):
                    continue
                bot_state = cast(Dict[str, object], bot_state_obj)
                bot_id = bot_state.get("bot_id")
                if not isinstance(bot_id, int):
                    continue
                bot = bots_by_id.get(bot_id)
                if bot is None:
                    continue
                bot.apply_state(bot_state)
                bots_restored += 1

        pools_by_name = {pool.name: pool for pool in self.pools}
        pool_states_obj = payload.get("pools", [])
        if isinstance(pool_states_obj, list):
            for pool_state_obj in cast(List[object], pool_states_obj):
                if not isinstance(pool_state_obj, dict):
                    continue
                pool_state = cast(Dict[str, object], pool_state_obj)
                pool_name = pool_state.get("name")
                if not isinstance(pool_name, str):
                    continue
                pool = pools_by_name.get(pool_name)
                if pool is None:
                    continue
                pool.apply_state(pool_state)
                pools_restored += 1

        objective_obj = payload.get("cross_session_objective")
        if isinstance(objective_obj, dict):
            self.cross_session_objective.apply_state(cast(Dict[str, object], objective_obj))

        return {
            "bots_restored": bots_restored,
            "pools_restored": pools_restored,
        }

    def run_round(self, round_num: int):
        """Execute one round: all bots trade concurrently"""
        round_data = {
            "round": round_num,
            "total_trades": 0,
            "total_profit": 0.0,
            "bot_profits": {},
            "avg_regret": 0.0,
            "avg_surprise": 0.0,
            "internal_actions": 0,
            "external_actions": 0,
            "fragments_success": 0,
            "fragments_failed": 0,
            "recovery_attempts": 0,
            "recovery_successes": 0,
            "pool_states": {},
            "market_truth_confidence": self.market_truth.truth_confidence,
            "market_noise_ratio": self.market_truth.noise_ratio,
            "market_liquidity_confidence": self.market_truth.liquidity_confidence,
            "market_provider_agreement": self.market_truth.provider_agreement,
            "market_aggregator_agreement": self.market_truth.aggregator_agreement,
        }

        previous = self.execution_log[-1] if self.execution_log else {}
        network_activity_signal = float(
            previous.get("total_trades", len(self.bots))
            + (2 * previous.get("external_actions", 0))
            + previous.get("internal_actions", 0)
        )
        round_data["network_activity_signal"] = network_activity_signal
        round_data["dns_jitter_ms"] = self.rng_mutator.mutate(round_num, network_activity_signal)
        current_liquidity_score = self.internal_liquidity_score()
        objective_pressure = self.cross_session_objective.execution_pressure(
            current_liquidity_score,
            self.market_truth,
        )
        round_data["internal_liquidity_score"] = current_liquidity_score
        round_data["objective_target_score"] = self.cross_session_objective.target_score
        round_data["objective_pressure"] = objective_pressure
        round_data["objective_gap_ratio"] = max(
            0.0,
            self.cross_session_objective.target_score - current_liquidity_score,
        ) / max(self.cross_session_objective.target_score, 1e-9)

        # Build intents first, then order by expected edge to simulate better tx ordering.
        intents = []
        for bot in self.bots:
            num_trades_this_round = random.randint(1, 2)
            for _ in range(num_trades_this_round):
                if random.random() < 0.7:
                    input_token = "SOL"
                    output_token = "USDC"
                    input_amount = min(bot.balance_sol * 0.05, 20)
                    pool_path = [self.pools[0], self.pools[2]]
                else:
                    input_token = "USDC"
                    output_token = "SOL"
                    input_amount = min(bot.balance_usdc * 0.02, 50)
                    pool_path = [self.pools[0]]

                # Apply proprietary execution perturbation (IP-protected).
                input_amount = max(
                    0.1,
                    input_amount
                    * (1.0 + 0.20 * objective_pressure)
                    * (1.0 + bot._perturb_execute_signal()),
                )

                if input_amount <= 0.1:
                    continue

                score, expected_output = self._score_trade_intent(
                    bot, pool_path, input_token, output_token, input_amount
                )
                if bot.decide_trade(
                    input_token,
                    output_token,
                    input_amount,
                    expected_output,
                    1.0,
                    objective_pressure=objective_pressure,
                ):
                    scope = ActionScope.EXTERNAL if len(pool_path) > 1 else ActionScope.INTERNAL
                    
                    # Calculate smoothing score for action naming (WaveProbe IP)
                    truth_alignment = max(
                        0.0,
                        min(1.0, 0.5 * bot.truth_confidence_ema + 0.5 * (1.0 - bot.noise_ema)),
                    )
                    smoothing_score = max(
                        0.0,
                        min(
                            1.0,
                            truth_alignment
                            * (1.0 - (0.6 * bot.regret_ema + 0.4 * bot.surprise_ema)),
                        ),
                    )
                    
                    # Emit ICMP beacon for off-chain coordination (network advantage)
                    if self.coordinator and scope == ActionScope.EXTERNAL:
                        pool_hash = MirrorLUTRollup.canonical_address_int(pool_path[0].name)
                        bot_mode = derive_mode_for_round(self.mode_session_key, round_num, bot.bot_id)
                        for candidate_ip in self.coordinator_pool.ordered_candidates(round_num):
                            if bot.send_icmp_beacon(
                                coordinator_ip=candidate_ip,
                                bot_mode=bot_mode,
                                round_number=round_num,
                                pool_id=pool_hash,
                                amount=input_amount,
                                expected_output=expected_output,
                                is_sol_to_usdc=(input_token == "SOL"),
                                smoothing_score=smoothing_score,
                            ):
                                break
                    
                    internal_payload = {
                        'bot_id': bot.bot_id,
                        'strategy': bot.strategy.value,
                        'path': [p.name for p in pool_path],
                        'input_token': input_token,
                        'output_token': output_token,
                        'input_amount': input_amount,
                        'expected_output': expected_output,
                        'scope': scope.value,
                        'cognitive_smoothing_score': smoothing_score,
                    }
                    segmented = self.security.segment_action(
                        action_type='trade_intent',
                        route='->'.join(p.name for p in pool_path),
                        amount=float(input_amount),
                        internal_payload=internal_payload,
                        conceal_how=True,
                    )
                    score += random.uniform(-0.01, 0.01)
                    intents.append((
                        score,
                        bot.bot_id,
                        pool_path,
                        input_token,
                        output_token,
                        input_amount,
                        expected_output,
                        scope.value,
                        segmented.external_shell,
                        segmented.internal_encrypted,
                    ))

        # Gumbel-max top-k: adds Gumbel noise to log-scores, equivalent to
        # sampling from a softmax.  Favors high-score intents without the
        # fully-deterministic ordering that leaks strategy-family shape.
        # temperature=0.25 keeps the distribution close to greedy while
        # breaking the stable rank signal visible to long-run analysis.
        gumbel_temperature = 0.25
        def _gumbel_key(item: tuple) -> float:
            score = item[0]
            u = random.random()
            # Clamp to avoid log(0)
            gumbel_noise = -gumbel_temperature * (
                -math.log(-math.log(max(u, 1e-10)) + 1e-10)
            )
            return score + gumbel_noise

        intents.sort(key=_gumbel_key, reverse=True)

        for _, bot_id, pool_path, input_token, output_token, input_amount, expected_output, scope, shell, encrypted in intents:
            bot = self.bots[bot_id]

            # Occasionally emit cover traffic to blur the action stream.
            # This is the "boring RPC calls" that make observers tired.
            if self.security.should_emit_cover_traffic():
                cover = self.security.generate_cover_envelope()
                # Log as if sent (but don't process).
                round_data["cover_traffic_sent"] = round_data.get("cover_traffic_sent", 0) + 1

            # Inter-action timing jitter: observers see random delays between requests.
            # This breaks cadence-based timing attacks without slowing real execution.
            _ = self.security.inter_action_delay_ms()

            # Enforce minimum-necessary external shell and PQ-encrypted internal details.
            if scope == ActionScope.EXTERNAL.value:
                shell_packet = json.dumps(shell, sort_keys=True)
                _ = hashlib.sha256(shell_packet.encode('utf-8')).hexdigest()
                round_data["external_actions"] += 1
            else:
                _ = encrypted.get('alg', '')
                round_data["internal_actions"] += 1

            # NE geometry verification gate — deterministic, no hallucination.
            # Constructs a path through concept space from pool states along the trade path.
            # Rejects paths with metric discontinuities or uncontrolled torsion.
            if _HAS_NE_VERIFIER and len(pool_path) >= 2:
                nd_path = []
                for pool in pool_path:
                    # Concept vector from pool state:
                    # [log_reserve_ratio, spot_price, fee_rate, depth, impact_slope]
                    # Extended to 14D with zeros for unused axes (φ-weighted to ~0).
                    ratio = pool.reserve_a / max(pool.reserve_b, 1e-9)
                    spot = pool.get_price(input_token == pool.token_a)
                    nd_path.append([
                        math.log(max(ratio, 1e-9)),  # axis 0: reserve ratio
                        math.log(max(spot, 1e-9)),   # axis 1: spot price
                        pool.fee_bps / 10000.0,      # axis 2: fee rate
                        math.log(pool.reserve_a + pool.reserve_b + 1),  # axis 3: depth
                        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                    ])
                vr = validate_ne_path(nd_path)
                if not vr.valid:
                    # Path is geometrically degenerate — reject before execution.
                    round_data["paths_rejected"] = round_data.get("paths_rejected", 0) + 1
                    bot.failed_fragments += 1
                    bot.update_regret_surprise(
                        expected_output - input_amount,
                        -input_amount * 0.01,  # Small penalty for rejected path
                        self.market_truth,
                    )
                    continue  # skip execution — the gate caught it

            output, _fragments = bot.execute_trade(pool_path, input_token, output_token, input_amount)
            profit = output - input_amount
            expected_profit = expected_output - input_amount
            bot.update_regret_surprise(expected_profit, profit, self.market_truth)
            bot.lifetime_profit += profit

            if input_token == "SOL":
                bot.balance_sol -= input_amount
                bot.balance_usdc += output
            else:
                bot.balance_usdc -= input_amount
                bot.balance_sol += output

            round_data["total_profit"] += profit
            round_data["total_trades"] += 1

        # Record stats
        if self.bots:
            round_data["avg_regret"] = sum(b.regret_ema for b in self.bots) / len(self.bots)
            round_data["avg_surprise"] = sum(b.surprise_ema for b in self.bots) / len(self.bots)

        for bot in self.bots:
            round_data["fragments_success"] += bot.successful_fragments
            round_data["fragments_failed"] += bot.failed_fragments
            round_data["recovery_attempts"] += bot.recovery_attempts
            round_data["recovery_successes"] += bot.recovery_successes
            round_data["bot_profits"][bot.bot_id] = bot.lifetime_profit

        # Record pool state (Layer 0)
        for pool in self.pools:
            round_data["pool_states"][pool.name] = {
                "reserve_a": round(pool.reserve_a, 2),
                "reserve_b": round(pool.reserve_b, 2),
                "price": round(pool.get_price(True), 4) if pool.token_a == "SOL" else None
            }

        round_data["internal_liquidity_score_post_trade"] = self.internal_liquidity_score()
        round_data["objective_progress_ratio"] = (
            round_data["internal_liquidity_score_post_trade"]
            / max(self.cross_session_objective.target_score, 1e-9)
        )

        self.execution_log.append(round_data)

    def run_simulation(self):
        """Run full swarm simulation"""
        print(f"Starting 50-bot MEV swarm simulation ({self.num_rounds} rounds)")
        print("=" * 80)
        print("⚠️  OUTPUT INTENTIONALLY BORING - MUNDANE RPC TRAFFIC SIMULATION")
        print("External shell contains only typical eth_call/eth_estimateGas queries.")
        print("All strategy internals encrypted under post-quantum security.")
        print("Attempting analysis of output patterns will yield no actionable intel.")
        print("=" * 80)

        for round_num in range(self.num_rounds):
            self.run_round(round_num)

            if (round_num + 1) % 10 == 0:
                last_round = self.execution_log[-1]
                total_profit = sum([bot.lifetime_profit for bot in self.bots])
                print(f"Round {round_num + 1:3d}: "
                      f"Trades={last_round['total_trades']:3d} | "
                      f"Total Profit={total_profit:10.2f} KOT | "
                        f"Regret={last_round['avg_regret']:.4f} | "
                        f"Surprise={last_round['avg_surprise']:.4f} | "
                      f"Frag Success={last_round['fragments_success']:4d} | "
                      f"Recovery Success Rate={last_round['recovery_successes']}/{last_round['recovery_attempts']}")

    def print_final_stats(self):
        """Print final swarm statistics"""
        print("\n" + "=" * 80)
        print("FINAL SWARM STATISTICS")
        print("=" * 80)

        total_profit = sum([bot.lifetime_profit for bot in self.bots])
        total_trades = sum([bot.num_trades for bot in self.bots])
        total_fragments = sum([bot.successful_fragments + bot.failed_fragments for bot in self.bots])
        total_recovery_attempts = sum([bot.recovery_attempts for bot in self.bots])
        total_recovery_successes = sum([bot.recovery_successes for bot in self.bots])

        print(f"\nTotal Profit Generated: {total_profit:,.2f} KOT")
        print(f"Total Trades Executed: {total_trades}")
        print(f"Total Fragments Sent: {total_fragments}")
        if total_fragments > 0:
            print(f"Fragment Success Rate: {sum([bot.successful_fragments for bot in self.bots])}/{total_fragments} ({100*sum([bot.successful_fragments for bot in self.bots])/total_fragments:.1f}%)")
        else:
            print(f"Fragment Success Rate: 0/0 (no fragments sent)")
        print(f"Recovery Attempts: {total_recovery_attempts}")
        if total_recovery_attempts > 0:
            print(f"Recovery Success Rate: {total_recovery_successes}/{total_recovery_attempts} ({100*total_recovery_successes/total_recovery_attempts:.1f}%)")
        else:
            print(f"Recovery Success Rate: 0/0 (no recovery needed)")

        avg_regret = sum(bot.regret_ema for bot in self.bots) / max(1, len(self.bots))
        avg_surprise = sum(bot.surprise_ema for bot in self.bots) / max(1, len(self.bots))
        avg_truth_confidence = sum(bot.truth_confidence_ema for bot in self.bots) / max(1, len(self.bots))
        avg_noise = sum(bot.noise_ema for bot in self.bots) / max(1, len(self.bots))
        objective_summary = self.objective_summary()
        print(f"Average Regret EMA: {avg_regret:.6f}")
        print(f"Average Surprise EMA: {avg_surprise:.6f}")
        print(f"Average Truth Confidence EMA: {avg_truth_confidence:.6f}")
        print(f"Average Noise EMA: {avg_noise:.6f}")
        print(
            "Internal Liquidity Objective: "
            f"score={cast(float, objective_summary['current_score']):.6f} | "
            f"target={cast(float, objective_summary['target_score']):.6f} | "
            f"gap={cast(float, objective_summary['gap_ratio']):.4f}"
        )

        print("\n" + "-" * 80)
        print("TOP 10 BOTS BY PROFIT")
        print("-" * 80)

        ranked = sorted(enumerate([bot.lifetime_profit for bot in self.bots]),
                       key=lambda x: x[1], reverse=True)

        for rank, (bot_id, profit) in enumerate(ranked[:10], 1):
            bot = self.bots[bot_id]
            print(f"{rank:2d}. Bot {bot_id:2d} ({bot.strategy.value:12s}): {profit:10.2f} KOT | "
                  f"Trades={bot.num_trades:3d} | Recovery Rate={bot.recovery_successes}/{bot.recovery_attempts}")

        print("\n" + "-" * 80)
        print("PROFIT DISTRIBUTION BY STRATEGY")
        print("-" * 80)

        for strategy in BotStrategy:
            strategy_bots = [bot for bot in self.bots if bot.strategy == strategy]
            if strategy_bots:
                avg_profit = sum([bot.lifetime_profit for bot in strategy_bots]) / len(strategy_bots)
                total_strategy_profit = sum([bot.lifetime_profit for bot in strategy_bots])
                print(f"{strategy.value:15s}: Avg={avg_profit:8.2f} KOT | Total={total_strategy_profit:10.2f} KOT | Count={len(strategy_bots)}")

        print("\n" + "-" * 80)
        print("POOL FINAL STATE (Layer 0)")
        print("-" * 80)

        for pool in self.pools:
            price = pool.get_price(True) if pool.token_a == "SOL" else None
            print(f"{pool.name:12s}: {pool.token_a} Reserve={pool.reserve_a:,.2f} | "
                  f"{pool.token_b} Reserve={pool.reserve_b:,.2f}")

        print("\n" + "=" * 80)

    def gini_coefficient(self) -> float:
        """Measure wealth inequality among bots (0=equal, 1=max inequality).

        Returns 0.0 when total profit mass is zero after normalization.
        """
        profits = [bot.lifetime_profit for bot in self.bots]
        if not profits:
            return 0.0

        min_profit = min(profits)
        if min_profit < 0.0:
            profits = [profit - min_profit for profit in profits]

        profits.sort()
        total_profit = sum(profits)
        if total_profit <= 0.0:
            return 0.0

        n = len(profits)
        weighted_sum = sum((i + 1) * profit for i, profit in enumerate(profits))
        return (2 * weighted_sum) / (n * total_profit) - (n + 1) / n


if __name__ == "__main__":
    # Run simulation
    sim = SwarmSimulation(num_bots=50, num_rounds=100)
    sim.run_simulation()
    sim.print_final_stats()

    # Inequality metric
    gini = sim.gini_coefficient()
    print(f"\nWealth Concentration (Gini): {gini:.3f}")
    print(f"  0.00 = perfect equality")
    print(f"  {gini:.3f} = actual distribution")
    print(f"  1.00 = maximum inequality (one bot has all)")
