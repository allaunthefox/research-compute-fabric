# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================

# [WARDEN BOUNDARY ENFORCEMENT INJECTED]
import sys
import os
try:
    from io_harness_compat import spawn_isolated_process, fetch_network_resource
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
    from io_harness_compat import spawn_isolated_process, fetch_network_resource

#!/usr/bin/env python3
"""
WaveProbe ICMP Coordinator — Off-chain swarm signaling via Jupiter Ghost ICMP

Bots send compressed trade intents via ICMP packets φ-locked to their mode.
Coordinator receives intents, aggregates strategies, coordinates execution.

Architecture:
  1. BotAgent.send_intent_beacon() → compress trade intent to 42 bytes
  2. JupiterGhostClient.send(mode=bot_id % 14, data=compressed_intent)
  3. CoordinatorListener.recv() → listen for incoming ghost packets
  4. Coordinator aggregates intents → coordinates MEV extraction order
  5. Bots receive coordination signal back on their mode → execute in consensus

⚠️  PROPRIETARY COORDINATION MECHANISM - WaveProbe Network Advantage
    This off-chain signaling layer provides trading edge via stealth coordination.
"""

import struct
import time
import hashlib
import hmac
import os
import shlex
# import subprocess (REMOVED BY WARDEN)
import statistics
import json
from collections import deque
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from waveprobe_nlut_sidecar import (
    BrownoutConservationCodon,
    DeterministicNLUTSidecar,
    NLUTSchema,
    RegretCooldownCodon,
    SurpriseDampeningCodon,
)


class IntentType(Enum):
    """Trade intent classification"""
    PROBE = 0x00           # Lightweight market observation (Phase 0)
    BID = 0x01             # Prepare to swap (Phase 1)
    EXECUTE = 0x02         # Execute now (Phase 2)
    ABORT = 0x03           # Cancel (on-chain recovery)
    COORDINATE = 0x04      # Swarm coordination signal


class MessageOTP:
    """Short-lived OTP tags for per-message authenticity.

    OTP here is an HMAC-based time-step token bound to payload header + mode.
    This prevents blind packet injection unless the sender shares OTP secret.
    """

    TAG_LEN = 8
    STEP_SECONDS = 5

    @staticmethod
    def _step(now: Optional[float] = None) -> int:
        return int(now if now is not None else time.time()) // MessageOTP.STEP_SECONDS

    @staticmethod
    def generate(
        header: bytes,
        otp_secret: bytes,
        mode: int,
        round_number: int,
        step: Optional[int] = None,
    ) -> bytes:
        if step is None:
            step = MessageOTP._step()
        material = (
            header
            + (mode & 0xFF).to_bytes(1, "big")
            + round_number.to_bytes(4, "big", signed=False)
            + step.to_bytes(8, "big", signed=False)
        )
        return hmac.new(otp_secret, material, hashlib.sha3_256).digest()[: MessageOTP.TAG_LEN]

    @staticmethod
    def verify(
        header: bytes,
        tag: bytes,
        otp_secret: bytes,
        mode: int,
        round_number: int,
        window: int = 1,
    ) -> bool:
        current = MessageOTP._step()
        for offset in range(-window, window + 1):
            expected = MessageOTP.generate(
                header,
                otp_secret,
                mode,
                round_number,
                step=current + offset,
            )
            if hmac.compare_digest(expected, tag):
                return True
        return False


class ReplayGuard:
    """Track recently seen packet keys and reject replays within a TTL window."""

    def __init__(self, ttl_seconds: int = 30, max_entries: int = 10000):
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._seen: Dict[bytes, float] = {}

    def _purge(self, now: float) -> None:
        expired = [k for k, ts in self._seen.items() if now - ts > self.ttl_seconds]
        for k in expired:
            self._seen.pop(k, None)

        # Hard cap to prevent unbounded growth under flood conditions.
        if len(self._seen) > self.max_entries:
            for key, _ in sorted(self._seen.items(), key=lambda kv: kv[1])[: len(self._seen) - self.max_entries]:
                self._seen.pop(key, None)

    def is_replay(self, key: bytes, now: Optional[float] = None) -> bool:
        now = now if now is not None else time.time()
        self._purge(now)
        if key in self._seen:
            return True
        self._seen[key] = now
        return False


@dataclass(frozen=True)
class RoundWindowPolicy:
    """Operator-tunable acceptance windows for round progression."""

    max_round_lag: int
    max_round_lead: int

    @staticmethod
    def from_env(profile_env: str = "WAVEPROBE_ROUND_POLICY_PROFILE") -> "RoundWindowPolicy":
        profile = os.getenv(profile_env, "balanced").strip().lower()
        profiles = {
            "strict": RoundWindowPolicy(max_round_lag=1, max_round_lead=2),
            "balanced": RoundWindowPolicy(max_round_lag=2, max_round_lead=8),
            "relaxed": RoundWindowPolicy(max_round_lag=4, max_round_lead=16),
        }
        if profile not in profiles:
            allowed = ", ".join(sorted(profiles))
            raise ValueError(f"Invalid {profile_env}: {profile!r}. Expected one of: {allowed}")
        policy = profiles[profile]

        lag_override = os.getenv("WAVEPROBE_MAX_ROUND_LAG")
        lead_override = os.getenv("WAVEPROBE_MAX_ROUND_LEAD")
        if lag_override is not None:
            try:
                policy = RoundWindowPolicy(max_round_lag=max(0, int(lag_override)), max_round_lead=policy.max_round_lead)
            except ValueError:
                raise ValueError(f"Invalid WAVEPROBE_MAX_ROUND_LAG: {lag_override!r}") from None
        if lead_override is not None:
            try:
                policy = RoundWindowPolicy(max_round_lag=policy.max_round_lag, max_round_lead=max(0, int(lead_override)))
            except ValueError:
                raise ValueError(f"Invalid WAVEPROBE_MAX_ROUND_LEAD: {lead_override!r}") from None
        return policy


@dataclass(frozen=True)
class RoundAdaptationLog:
    """Per-round adaptation telemetry for surprise/regret tracking."""

    round_number: int
    expected_output: float
    observed_output: float
    surprise: float
    chosen_utility: float
    best_counterfactual_utility: float
    regret: float
    shock: bool
    consensus_pool: int
    consensus_strength: int
    timestamp: float


class SurpriseRegretCollector:
    """Collect bounded round logs for adaptation metrics."""

    def __init__(self, max_logs: int = 2048, epsilon: float = 1e-9):
        self.max_logs = max_logs
        self.epsilon = epsilon
        self.round_logs: List[RoundAdaptationLog] = []

    def _trim(self) -> None:
        if len(self.round_logs) > self.max_logs:
            self.round_logs = self.round_logs[-self.max_logs :]

    def compute_surprise(self, expected_output: float, observed_output: float) -> float:
        denom = max(self.epsilon, abs(expected_output))
        return min(1.0, abs(observed_output - expected_output) / denom)

    def compute_regret(self, chosen_utility: float, best_counterfactual_utility: float) -> float:
        regret_raw = max(0.0, best_counterfactual_utility - chosen_utility)
        denom = max(self.epsilon, abs(best_counterfactual_utility))
        return regret_raw / denom

    def record_round(
        self,
        round_number: int,
        expected_output: float,
        observed_output: float,
        chosen_utility: float,
        best_counterfactual_utility: float,
        shock: bool = False,
        consensus_pool: int = 0,
        consensus_strength: int = 0,
    ) -> RoundAdaptationLog:
        surprise = self.compute_surprise(expected_output, observed_output)
        regret = self.compute_regret(chosen_utility, best_counterfactual_utility)
        log = RoundAdaptationLog(
            round_number=round_number,
            expected_output=expected_output,
            observed_output=observed_output,
            surprise=surprise,
            chosen_utility=chosen_utility,
            best_counterfactual_utility=best_counterfactual_utility,
            regret=regret,
            shock=shock,
            consensus_pool=consensus_pool,
            consensus_strength=consensus_strength,
            timestamp=time.time(),
        )
        self.round_logs.append(log)
        self._trim()
        return log

    def summary(self, last_n: Optional[int] = None) -> Dict[str, float]:
        logs = self.round_logs[-last_n:] if last_n else self.round_logs
        if not logs:
            return {
                "count": 0,
                "avg_surprise": 0.0,
                "avg_regret": 0.0,
                "shock_rate": 0.0,
            }

        count = len(logs)
        avg_surprise = sum(item.surprise for item in logs) / count
        avg_regret = sum(item.regret for item in logs) / count
        shock_rate = sum(1 for item in logs if item.shock) / count
        return {
            "count": float(count),
            "avg_surprise": avg_surprise,
            "avg_regret": avg_regret,
            "shock_rate": shock_rate,
        }


@dataclass(frozen=True)
class ShadowDecisionLog:
    """Per-round baseline-vs-codon shadow decision telemetry."""

    round_number: int
    baseline_action: int
    codon_action: int
    baseline_surprise: float
    codon_surprise: float
    surprise_delta: float
    baseline_regret: float
    codon_regret: float
    regret_delta: float
    shock: bool
    ndag_lag_rounds: int
    ndag_effective_round: int
    fallback_applied: bool
    fallback_tier: int
    fallback_action_id: Optional[int]
    level2_lock_active: bool
    recovery_half_life_surprise: Optional[float]
    recovery_half_life_regret: Optional[float]
    timestamp: float


@dataclass(frozen=True)
class HomeostasisAlertPolicy:
    """Thresholds used to flag degraded homeostasis in rolling summaries."""

    sign_stability_floor: float = 0.70
    shock_recovery_ratio_floor: float = 0.60
    median_half_life_ceiling: float = 8.0

    @staticmethod
    def _float_env(name: str, default: float) -> float:
        raw = os.getenv(name)
        if raw is None:
            return default
        try:
            return float(raw)
        except ValueError:
            return default

    @classmethod
    def from_env(cls) -> "HomeostasisAlertPolicy":
        return cls(
            sign_stability_floor=cls._float_env(
                "WAVEPROBE_HOMEOSTASIS_SIGN_STABILITY_FLOOR",
                cls.sign_stability_floor,
            ),
            shock_recovery_ratio_floor=cls._float_env(
                "WAVEPROBE_HOMEOSTASIS_SHOCK_RECOVERY_RATIO_FLOOR",
                cls.shock_recovery_ratio_floor,
            ),
            median_half_life_ceiling=cls._float_env(
                "WAVEPROBE_HOMEOSTASIS_MEDIAN_HALF_LIFE_CEILING",
                cls.median_half_life_ceiling,
            ),
        )


class ShadowDecisionMonitor:
    """Track baseline-vs-codon deltas and estimate rolling recovery half-life."""

    def __init__(self, max_logs: int = 2048):
        self.max_logs = max_logs
        self.logs: List[ShadowDecisionLog] = []

    def _trim(self) -> None:
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs :]

    @staticmethod
    def _sign_stability(values: List[float]) -> float:
        non_zero = [value for value in values if abs(value) > 1e-12]
        if len(non_zero) < 2:
            return 1.0
        same = 0
        total = 0
        for idx in range(1, len(non_zero)):
            total += 1
            if (non_zero[idx] > 0) == (non_zero[idx - 1] > 0):
                same += 1
        return float(same) / float(total) if total else 1.0

    @staticmethod
    def _shock_to_recovery_ratio(logs: List[ShadowDecisionLog], metric_getter) -> float:
        shock_indexes = [idx for idx, item in enumerate(logs) if item.shock]
        if not shock_indexes:
            return 0.0

        recovered = 0
        for shock_idx in shock_indexes:
            baseline = abs(metric_getter(logs[shock_idx]))
            if baseline <= 0.0:
                recovered += 1
                continue
            target = baseline * 0.5
            found = False
            for idx in range(shock_idx + 1, len(logs)):
                if abs(metric_getter(logs[idx])) <= target:
                    found = True
                    break
            if found:
                recovered += 1
        return float(recovered) / float(len(shock_indexes))

    @staticmethod
    def _half_life(
        logs: List[ShadowDecisionLog],
        metric_getter,
    ) -> Optional[float]:
        shock_idx = None
        for idx in range(len(logs) - 1, -1, -1):
            if logs[idx].shock:
                shock_idx = idx
                break
        if shock_idx is None:
            return None

        baseline = abs(metric_getter(logs[shock_idx]))
        if baseline <= 0.0:
            return 0.0
        target = baseline * 0.5
        start_round = logs[shock_idx].round_number

        for idx in range(shock_idx + 1, len(logs)):
            if abs(metric_getter(logs[idx])) <= target:
                return float(logs[idx].round_number - start_round)
        return None

    def record(
        self,
        round_number: int,
        baseline_action: int,
        codon_action: int,
        baseline_surprise: float,
        codon_surprise: float,
        baseline_regret: float,
        codon_regret: float,
        shock: bool,
        ndag_lag_rounds: int,
        ndag_effective_round: int,
        fallback_applied: bool,
        fallback_tier: int,
        fallback_action_id: Optional[int],
        level2_lock_active: bool,
    ) -> ShadowDecisionLog:
        log = ShadowDecisionLog(
            round_number=round_number,
            baseline_action=baseline_action,
            codon_action=codon_action,
            baseline_surprise=baseline_surprise,
            codon_surprise=codon_surprise,
            surprise_delta=codon_surprise - baseline_surprise,
            baseline_regret=baseline_regret,
            codon_regret=codon_regret,
            regret_delta=codon_regret - baseline_regret,
            shock=shock,
            ndag_lag_rounds=ndag_lag_rounds,
            ndag_effective_round=ndag_effective_round,
            fallback_applied=fallback_applied,
            fallback_tier=fallback_tier,
            fallback_action_id=fallback_action_id,
            level2_lock_active=level2_lock_active,
            recovery_half_life_surprise=None,
            recovery_half_life_regret=None,
            timestamp=time.time(),
        )
        self.logs.append(log)
        self._trim()

        half_life_surprise = self._half_life(self.logs, lambda item: item.surprise_delta)
        half_life_regret = self._half_life(self.logs, lambda item: item.regret_delta)

        enriched = ShadowDecisionLog(
            round_number=log.round_number,
            baseline_action=log.baseline_action,
            codon_action=log.codon_action,
            baseline_surprise=log.baseline_surprise,
            codon_surprise=log.codon_surprise,
            surprise_delta=log.surprise_delta,
            baseline_regret=log.baseline_regret,
            codon_regret=log.codon_regret,
            regret_delta=log.regret_delta,
            shock=log.shock,
            ndag_lag_rounds=log.ndag_lag_rounds,
            ndag_effective_round=log.ndag_effective_round,
            fallback_applied=log.fallback_applied,
            fallback_tier=log.fallback_tier,
            fallback_action_id=log.fallback_action_id,
            level2_lock_active=log.level2_lock_active,
            recovery_half_life_surprise=half_life_surprise,
            recovery_half_life_regret=half_life_regret,
            timestamp=log.timestamp,
        )
        self.logs[-1] = enriched
        return enriched

    def rolling_homeostasis_summary(self, last_n: Optional[int] = None) -> Dict[str, float]:
        logs = self.logs[-last_n:] if last_n else self.logs
        if not logs:
            return {
                "count": 0.0,
                "shock_count": 0.0,
                "median_recovery_half_life": 0.0,
                "delta_sign_stability": 1.0,
                "shock_to_recovery_success_ratio": 0.0,
            }

        half_life_values = [
            value
            for item in logs
            for value in (item.recovery_half_life_surprise, item.recovery_half_life_regret)
            if value is not None
        ]
        median_half_life = float(statistics.median(half_life_values)) if half_life_values else 0.0

        surprise_stability = self._sign_stability([item.surprise_delta for item in logs])
        regret_stability = self._sign_stability([item.regret_delta for item in logs])
        delta_sign_stability = (surprise_stability + regret_stability) / 2.0

        surprise_ratio = self._shock_to_recovery_ratio(logs, lambda item: item.surprise_delta)
        regret_ratio = self._shock_to_recovery_ratio(logs, lambda item: item.regret_delta)
        shock_to_recovery_success_ratio = (surprise_ratio + regret_ratio) / 2.0
        shock_count = sum(1 for item in logs if item.shock)

        return {
            "count": float(len(logs)),
            "shock_count": float(shock_count),
            "median_recovery_half_life": median_half_life,
            "delta_sign_stability": delta_sign_stability,
            "shock_to_recovery_success_ratio": shock_to_recovery_success_ratio,
        }

    def alert_state(
        self,
        policy: HomeostasisAlertPolicy,
        last_n: Optional[int] = None,
    ) -> Dict[str, object]:
        """Evaluate rolling metrics against policy thresholds."""
        summary = self.rolling_homeostasis_summary(last_n=last_n)
        reasons: List[str] = []

        if summary["delta_sign_stability"] < policy.sign_stability_floor:
            reasons.append(
                "delta sign stability below floor "
                f"({summary['delta_sign_stability']:.4f} < {policy.sign_stability_floor:.4f})"
            )
        if summary.get("shock_count", 0.0) > 0.0 and summary["shock_to_recovery_success_ratio"] < policy.shock_recovery_ratio_floor:
            reasons.append(
                "shock-to-recovery success ratio below floor "
                f"({summary['shock_to_recovery_success_ratio']:.4f} < {policy.shock_recovery_ratio_floor:.4f})"
            )
        if summary["median_recovery_half_life"] > policy.median_half_life_ceiling:
            reasons.append(
                "median recovery half-life above ceiling "
                f"({summary['median_recovery_half_life']:.4f} > {policy.median_half_life_ceiling:.4f})"
            )

        return {
            "homeostasis_degraded": bool(reasons),
            "reasons": reasons,
            "summary": summary,
        }


class GhostICMPCommandBuilder:
    """Build non-interactive ghost_icmp commands without hardcoded sudo."""

    RUNNER_ENV = "WAVEPROBE_GHOST_ICMP_RUNNER"

    def __init__(self, ghost_icmp_path: str):
        self.ghost_icmp_path = ghost_icmp_path
        runner = os.getenv(self.RUNNER_ENV, "").strip()
        self.runner_prefix = shlex.split(runner) if runner else []

    def build(self, *args: str) -> List[str]:
        return [*self.runner_prefix, self.ghost_icmp_path, *args]

    def permission_hint(self) -> str:
        if self.runner_prefix:
            return (
                f"ghost_icmp command failed under configured runner {self.runner_prefix!r}. "
                "Ensure the runner grants non-interactive raw socket access."
            )
        return (
            "ghost_icmp requires raw socket access. Run as root, grant the binary CAP_NET_RAW, "
            "or set WAVEPROBE_GHOST_ICMP_RUNNER to a non-interactive runner such as 'sudo -n'."
        )


class MirrorLUTRollup:
    """Mirror-LUT rollup from canonical 4096-bit addresses to compact wire keys."""

    CANONICAL_ADDRESS_BYTES = 512
    ROLLUP_ID_BYTES = 17
    DOMAIN = b"waveprobe/mirror-lut/v1"

    @staticmethod
    def canonical_address_bytes(label: str) -> bytes:
        return hashlib.shake_256(MirrorLUTRollup.DOMAIN + label.encode("utf-8")).digest(
            MirrorLUTRollup.CANONICAL_ADDRESS_BYTES
        )

    @staticmethod
    def canonical_address_int(label: str) -> int:
        return int.from_bytes(MirrorLUTRollup.canonical_address_bytes(label), "big", signed=False)

    @staticmethod
    def rollup_id(canonical_address: int, round_number: int, otp_secret: bytes) -> int:
        canonical_bytes = canonical_address.to_bytes(
            MirrorLUTRollup.CANONICAL_ADDRESS_BYTES,
            "big",
            signed=False,
        )
        material = (
            MirrorLUTRollup.DOMAIN
            + canonical_bytes
            + round_number.to_bytes(4, "big", signed=False)
            + hashlib.sha3_256(otp_secret).digest()
        )
        return int.from_bytes(
            hashlib.shake_256(material).digest(MirrorLUTRollup.ROLLUP_ID_BYTES),
            "big",
            signed=False,
        )


@dataclass
class CompressedIntent:
    """Compressed trade intent for ICMP transmission.

    Preferred wire layout (41 bytes):
      [0]     Intent type + urgency (high nibble / low nibble)
      [1..2]  Pool ID low bits [u16 BE]
      [3..4]  Amount quantized [u16 BE]
      [5..6]  Expected output quantized [u16 BE]
      [7]     Direction + token pair nibble
      [8]     Fitness [u8]
      [9..10] Swarm target [u16 BE]
      [11..12] Timestamp delta [u16 BE]
      [13..20] OTP tag (8 bytes)
      [21..24] Round number [u32 BE]
      [25..39] Pool ID high bits [15 bytes]
      [40]    Flags: bit7 phase_locked, bits6..4 schema_version, bit0 otp_present

    Legacy wire layout (42 bytes) is still accepted by unpack() for compatibility.
    """

    WIRE_BYTES = 41
    LEGACY_WIRE_BYTES = 42
    POOL_ID_LOW_LEN = 2
    POOL_ID_HIGH_LEN = 15
    POOL_ID_BYTES = POOL_ID_LOW_LEN + POOL_ID_HIGH_LEN
    FLAG_PHASE_LOCKED = 0x80
    FLAG_OTP_PRESENT = 0x01
    FLAG_SCHEMA_SHIFT = 4
    FLAG_SCHEMA_MASK = 0x70
    SCHEMA_VERSION = 0x01
    SCHEMA_MIGRATION_TABLE = {
        0x01: "compact-v1",
    }
    DEFAULT_ACCEPTED_SCHEMA_VERSIONS = frozenset(SCHEMA_MIGRATION_TABLE.keys())

    intent_type: IntentType
    pool_id: int  # 136-bit mirror-LUT rollup identifier
    amount_quantized: int  # log-bucketed to power-of-2
    expected_output: int  # log-bucketed
    direction: bool  # True = SOL→USDC, False = USDC→SOL
    fitness: int  # 0-255, mapped from smoothing_score
    swarm_target: int  # coordinated pool if >0, else solo
    phase_locked: bool  # coherence achieved?
    timestamp_delta_ms: int  # time since round start
    round_number: int = 0  # cryptographically bound round counter
    token_pair_id: int = 0  # 4-bit token pair selector
    urgency: int = 0x0F  # 4-bit urgency class

    def __post_init__(self) -> None:
        if not (0 <= self.pool_id < (1 << (self.POOL_ID_BYTES * 8))):
            raise ValueError("pool_id out of range for 17-byte encoding")
        if not (0 <= self.amount_quantized <= 0xFFFF):
            raise ValueError("amount_quantized must be in [0, 65535]")
        if not (0 <= self.expected_output <= 0xFFFF):
            raise ValueError("expected_output must be in [0, 65535]")
        if not (0 <= self.token_pair_id <= 0x0F):
            raise ValueError("token_pair_id must be in [0, 15]")
        if not (0 <= self.urgency <= 0x0F):
            raise ValueError("urgency must be in [0, 15]")
        if not (0 <= self.fitness <= 0xFF):
            raise ValueError("fitness must be in [0, 255]")
        if not (0 <= self.swarm_target <= 0xFFFF):
            raise ValueError("swarm_target must be in [0, 65535]")
        if not (0 <= self.timestamp_delta_ms <= 0xFFFF):
            raise ValueError("timestamp_delta_ms must be in [0, 65535]")
        if not (0 <= self.round_number <= 0xFFFFFFFF):
            raise ValueError("round_number must be in [0, 2^32-1]")

    @classmethod
    def accepted_schema_versions(cls) -> frozenset[int]:
        """Return accepted compact schema versions for rolling upgrades.

        WAVEPROBE_ACCEPTED_SCHEMA_VERSIONS supports comma-separated ints/hex,
        e.g. "1,0x2".
        """
        raw = os.getenv("WAVEPROBE_ACCEPTED_SCHEMA_VERSIONS", "").strip()
        if not raw:
            return cls.DEFAULT_ACCEPTED_SCHEMA_VERSIONS

        accepted = set()
        for token in raw.split(","):
            part = token.strip().lower()
            if not part:
                continue
            try:
                version = int(part, 16) if part.startswith("0x") else int(part)
            except ValueError:
                continue
            if 0 <= version <= 0x07:
                accepted.add(version)

        if not accepted:
            return cls.DEFAULT_ACCEPTED_SCHEMA_VERSIONS
        return frozenset(accepted)

    def pack(self, otp_secret: Optional[bytes] = None, mode: int = 0) -> bytes:
        """Serialize to 41-byte compact ICMP payload.

        If otp_secret is provided, an OTP tag is emitted in [13..20] and
        bit0 of [40] is set.
        """
        buf = bytearray(self.WIRE_BYTES)
        
        # [0] Intent type + urgency
        buf[0] = ((self.intent_type.value & 0x0F) << 4) | (self.urgency & 0x0F)
        
        # [1..2] Pool ID low bits
        pool_id_bytes = self.pool_id.to_bytes(self.POOL_ID_BYTES, 'big', signed=False)
        buf[1:3] = pool_id_bytes[-self.POOL_ID_LOW_LEN:]
        
        # [3..4] Amount
        buf[3:5] = struct.pack('>H', self.amount_quantized & 0xFFFF)
        
        # [5..6] Expected output
        buf[5:7] = struct.pack('>H', self.expected_output & 0xFFFF)
        
        # [7] Direction + token
        direction_bit = 0x10 if self.direction else 0x00
        buf[7] = direction_bit | (self.token_pair_id & 0x0F)
        
        # [8] Fitness
        buf[8] = self.fitness & 0xFF
        
        # [9..10] Swarm target
        buf[9:11] = struct.pack('>H', self.swarm_target & 0xFFFF)
        
        # [11..12] Timestamp delta
        buf[11:13] = struct.pack('>H', self.timestamp_delta_ms & 0xFFFF)

        # [13..39] OTP extension / extended pool identifier
        buf[13:40] = b'\x00' * 27
        buf[21:25] = struct.pack('>I', self.round_number & 0xFFFFFFFF)
        buf[25:40] = pool_id_bytes[:self.POOL_ID_HIGH_LEN]

        flags = self.SCHEMA_VERSION << self.FLAG_SCHEMA_SHIFT
        if self.phase_locked:
            flags |= self.FLAG_PHASE_LOCKED
        if otp_secret:
            flags |= self.FLAG_OTP_PRESENT
        buf[40] = flags
        if otp_secret:
            auth_header = bytes(buf[:13]) + bytes(buf[21:41])
            otp_tag = MessageOTP.generate(auth_header, otp_secret, mode, self.round_number)
            buf[13:21] = otp_tag
        
        return bytes(buf)

    @staticmethod
    def unpack(
        data: bytes,
        otp_secret: Optional[bytes] = None,
        mode: int = 0,
        require_otp: bool = False,
        current_round: Optional[int] = None,
        max_round_lag: int = 2,
        max_round_lead: int = 1,
    ) -> Optional['CompressedIntent']:
        """Deserialize from 41-byte compact or 42-byte legacy payload.

        If require_otp=True, token must be present and verify for given mode.
        """
        if len(data) < CompressedIntent.WIRE_BYTES:
            return None
        
        try:
            # Preferred compact format (41 bytes)
            if len(data) == CompressedIntent.WIRE_BYTES:
                intent_type_val = (data[0] >> 4) & 0x0F
                intent_type = IntentType(intent_type_val)
                urgency = data[0] & 0x0F

                pool_id = int.from_bytes(data[25:40] + data[1:3], 'big', signed=False)
                amount_quantized = struct.unpack('>H', data[3:5])[0]
                expected_output = struct.unpack('>H', data[5:7])[0]

                direction = (data[7] & 0x10) != 0
                token_pair_id = data[7] & 0x0F
                fitness = data[8]
                swarm_target = struct.unpack('>H', data[9:11])[0]
                timestamp_delta_ms = struct.unpack('>H', data[11:13])[0]
                round_number = struct.unpack('>I', data[21:25])[0]
                flags = data[40]
                phase_locked = (flags & CompressedIntent.FLAG_PHASE_LOCKED) != 0
                otp_enabled = (flags & CompressedIntent.FLAG_OTP_PRESENT) != 0
                schema_version = (flags & CompressedIntent.FLAG_SCHEMA_MASK) >> CompressedIntent.FLAG_SCHEMA_SHIFT
                if schema_version not in CompressedIntent.accepted_schema_versions():
                    return None

                if current_round is not None:
                    if round_number + max_round_lag < current_round:
                        return None
                    if round_number > current_round + max_round_lead:
                        return None

                if require_otp and not otp_enabled:
                    return None
                if otp_secret and otp_enabled:
                    otp_tag = data[13:21]
                    auth_header = data[:13] + data[21:41]
                    if not MessageOTP.verify(auth_header, otp_tag, otp_secret, mode, round_number):
                        return None
                elif require_otp:
                    return None

                return CompressedIntent(
                    intent_type=intent_type,
                    pool_id=pool_id,
                    amount_quantized=amount_quantized,
                    expected_output=expected_output,
                    direction=direction,
                    token_pair_id=token_pair_id,
                    urgency=urgency,
                    fitness=fitness,
                    swarm_target=swarm_target,
                    phase_locked=phase_locked,
                    timestamp_delta_ms=timestamp_delta_ms,
                    round_number=round_number,
                )

            # Legacy layout compatibility (42 bytes)
            if len(data) >= CompressedIntent.LEGACY_WIRE_BYTES:
                intent_type_val = (data[0] >> 4) & 0x0F
                intent_type = IntentType(intent_type_val)
                urgency = data[0] & 0x0F

                pool_id = int.from_bytes(data[27:42] + data[1:3], 'big', signed=False)
                amount_quantized = struct.unpack('>H', data[3:5])[0]
                expected_output = struct.unpack('>H', data[5:7])[0]

                direction = (data[7] & 0x10) != 0
                token_pair_id = data[7] & 0x0F
                fitness = data[8]
                swarm_target = struct.unpack('>H', data[9:11])[0]
                phase_locked = (data[11] & 0x80) != 0
                timestamp_delta_ms = struct.unpack('>H', data[12:14])[0]
                round_number = struct.unpack('>I', data[23:27])[0]

                if current_round is not None:
                    if round_number + max_round_lag < current_round:
                        return None
                    if round_number > current_round + max_round_lead:
                        return None

                otp_enabled = data[22] == 0xA5
                if require_otp and not otp_enabled:
                    return None
                if otp_secret and otp_enabled:
                    otp_tag = data[14:22]
                    auth_header = data[:14] + data[23:42]
                    if not MessageOTP.verify(auth_header, otp_tag, otp_secret, mode, round_number):
                        return None
                elif require_otp:
                    return None

                return CompressedIntent(
                    intent_type=intent_type,
                    pool_id=pool_id,
                    amount_quantized=amount_quantized,
                    expected_output=expected_output,
                    direction=direction,
                    token_pair_id=token_pair_id,
                    urgency=urgency,
                    fitness=fitness,
                    swarm_target=swarm_target,
                    phase_locked=phase_locked,
                    timestamp_delta_ms=timestamp_delta_ms,
                    round_number=round_number,
                )

            return None
        except (struct.error, ValueError):
            return None


class JupiterGhostClient:
    """Thin wrapper around ghost_icmp Rust tool for sending intents"""
    
    def __init__(self, ghost_icmp_path: str = "./tools/ghost_icmp/target/debug/ghost_icmp"):
        self.ghost_icmp_path = ghost_icmp_path
        self.command_builder = GhostICMPCommandBuilder(ghost_icmp_path)
    
    def send(self, target: str, mode: int, data: bytes, round_ticks: int = 60000) -> bool:
        """Send data on a specific Jupiter mode via ICMP

        Args:
            target: IP address (e.g., "192.168.1.254" — coordinator)
            mode: Jupiter mode (0-13)
            data: Packed CompressedIntent payload (φ-locked by ghost_icmp)
            round_ticks: Bateman LUT size — total ticks per round (default 60000 = 60s at 1ms res)

        The Bateman presalt tick is extracted from the CompressedIntent wire layout at
        bytes [11:13] (timestamp_delta_ms), so sender and receiver derive the same
        presalt from the same LUT position without any extra coordination.

        Returns:
            True if send succeeded, False otherwise
        """
        if mode < 0 or mode >= 14:
            return False

        # Extract tick from CompressedIntent bytes [11:13] (timestamp_delta_ms).
        # Falls back to 0 for non-CompressedIntent payloads — presalt is still valid,
        # just pinned to tick 0 of the Bateman curve.
        tick = 0
        if len(data) >= 13:
            tick = struct.unpack('>H', data[11:13])[0]

        try:
            result = subprocess.run(
                self.command_builder.build(
                    "send",
                    "--target", target,
                    "--mode", str(mode),
                    "--data", data.hex(),
                    "--round-ticks", str(round_ticks),
                    "--tick", str(tick),
                ),
                shell=False,
                check=False,
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False
        except PermissionError as exc:
            raise RuntimeError(self.command_builder.permission_hint()) from exc
        except FileNotFoundError as exc:
            raise RuntimeError(f"ghost_icmp executable not found: {self.ghost_icmp_path}") from exc
        except Exception:
            return False


class CoordinatorListener:
    """Listen for incoming ICMP ghost packets from bots
    
    Receives compressed trade intents from bots, aggregates, and coordinates
    the next round of MEV extraction.
    """
    
    def __init__(
        self,
        ghost_icmp_path: str = "./tools/ghost_icmp/target/debug/ghost_icmp",
        otp_secret: Optional[str] = None,
        require_otp: bool = True,
        replay_ttl_seconds: int = 30,
        round_policy: Optional[RoundWindowPolicy] = None,
        round_epoch_anchor: Optional[int] = None,
    ):
        self.ghost_icmp_path = ghost_icmp_path
        self.command_builder = GhostICMPCommandBuilder(ghost_icmp_path)
        self.intents: Dict[int, List[CompressedIntent]] = {}  # mode -> intents
        self.last_round_time = time.time()
        self.require_otp = require_otp
        raw_secret = otp_secret or os.getenv("WAVEPROBE_OTP_SECRET")
        if self.require_otp and not raw_secret:
            raise ValueError("WAVEPROBE_OTP_SECRET is required when OTP verification is enabled")
        self.otp_secret = raw_secret.encode("utf-8") if raw_secret else b""
        self.replay_guard = ReplayGuard(ttl_seconds=replay_ttl_seconds)
        self.adaptation = SurpriseRegretCollector()
        self.shadow = ShadowDecisionMonitor()
        self.homeostasis_alert_policy = HomeostasisAlertPolicy.from_env()

        lag_raw = os.getenv("WAVEPROBE_NDAG_OUTPUT_LAG_ROUNDS", "1").strip()
        try:
            self.ndag_output_lag_rounds = max(0, int(lag_raw))
        except ValueError:
            self.ndag_output_lag_rounds = 1
        self._ndag_feature_lag: deque[Dict[str, int]] = deque(maxlen=max(1, self.ndag_output_lag_rounds + 1))

        shadow_schema = NLUTSchema(
            version=1,
            axes=(("surprise_bin", 8), ("regret_bin", 8), ("brownout_bin", 4)),
            action_ids=(0, 1, 2, 3),
        )
        shadow_cells = 8 * 8 * 4
        shadow_table = {index: (0, 0, 0, 0) for index in range(shadow_cells)}
        self.shadow_baseline_sidecar = DeterministicNLUTSidecar(schema=shadow_schema, table=shadow_table)
        self.shadow_codon_sidecar = DeterministicNLUTSidecar(
            schema=shadow_schema,
            table=dict(shadow_table),
            codon_rules=[
                SurpriseDampeningCodon(threshold=3, penalty=3),
                RegretCooldownCodon(threshold=3, penalty=5),
                BrownoutConservationCodon(threshold=2, bonus=2),
            ],
        )

        fallback_action_raw = os.getenv("WAVEPROBE_HOMEOSTASIS_FALLBACK_ACTION_ID", "0").strip()
        try:
            self.homeostasis_fallback_action_id = int(fallback_action_raw)
        except ValueError:
            self.homeostasis_fallback_action_id = 0
        if self.homeostasis_fallback_action_id not in shadow_schema.action_ids:
            self.homeostasis_fallback_action_id = min(shadow_schema.action_ids)

        fallback_rounds_raw = os.getenv("WAVEPROBE_HOMEOSTASIS_FALLBACK_MIN_ROUNDS", "2").strip()
        try:
            self.homeostasis_fallback_min_rounds = max(1, int(fallback_rounds_raw))
        except ValueError:
            self.homeostasis_fallback_min_rounds = 2
        self._homeostasis_fallback_rounds_remaining = 0

        default_level2_sign_floor = max(0.0, self.homeostasis_alert_policy.sign_stability_floor - 0.20)
        default_level2_ratio_floor = max(0.0, self.homeostasis_alert_policy.shock_recovery_ratio_floor - 0.20)
        default_level2_half_life_ceiling = max(0.0, self.homeostasis_alert_policy.median_half_life_ceiling * 1.5)
        default_release_sign_floor = min(1.0, self.homeostasis_alert_policy.sign_stability_floor + 0.10)
        default_release_ratio_floor = min(1.0, self.homeostasis_alert_policy.shock_recovery_ratio_floor + 0.10)
        default_release_half_life_ceiling = max(0.0, self.homeostasis_alert_policy.median_half_life_ceiling - 1.0)

        try:
            self.homeostasis_level2_sign_stability_floor = float(
                os.getenv("WAVEPROBE_HOMEOSTASIS_LEVEL2_SIGN_STABILITY_FLOOR", str(default_level2_sign_floor))
            )
        except ValueError:
            self.homeostasis_level2_sign_stability_floor = default_level2_sign_floor
        try:
            self.homeostasis_level2_shock_recovery_ratio_floor = float(
                os.getenv("WAVEPROBE_HOMEOSTASIS_LEVEL2_SHOCK_RECOVERY_RATIO_FLOOR", str(default_level2_ratio_floor))
            )
        except ValueError:
            self.homeostasis_level2_shock_recovery_ratio_floor = default_level2_ratio_floor
        try:
            self.homeostasis_level2_median_half_life_ceiling = float(
                os.getenv("WAVEPROBE_HOMEOSTASIS_LEVEL2_MEDIAN_HALF_LIFE_CEILING", str(default_level2_half_life_ceiling))
            )
        except ValueError:
            self.homeostasis_level2_median_half_life_ceiling = default_level2_half_life_ceiling

        try:
            self.homeostasis_hysteresis_sign_stability_release = float(
                os.getenv("WAVEPROBE_HOMEOSTASIS_HYSTERESIS_SIGN_STABILITY_RELEASE", str(default_release_sign_floor))
            )
        except ValueError:
            self.homeostasis_hysteresis_sign_stability_release = default_release_sign_floor
        try:
            self.homeostasis_hysteresis_shock_recovery_release = float(
                os.getenv("WAVEPROBE_HOMEOSTASIS_HYSTERESIS_SHOCK_RECOVERY_RELEASE", str(default_release_ratio_floor))
            )
        except ValueError:
            self.homeostasis_hysteresis_shock_recovery_release = default_release_ratio_floor
        try:
            self.homeostasis_hysteresis_median_half_life_release = float(
                os.getenv("WAVEPROBE_HOMEOSTASIS_HYSTERESIS_MEDIAN_HALF_LIFE_RELEASE", str(default_release_half_life_ceiling))
            )
        except ValueError:
            self.homeostasis_hysteresis_median_half_life_release = default_release_half_life_ceiling

        release_rounds_raw = os.getenv("WAVEPROBE_HOMEOSTASIS_HYSTERESIS_RELEASE_ROUNDS", "2").strip()
        try:
            self.homeostasis_hysteresis_release_rounds = max(1, int(release_rounds_raw))
        except ValueError:
            self.homeostasis_hysteresis_release_rounds = 2

        self._homeostasis_level2_lock_active = False
        self._homeostasis_recovery_streak = 0

        self.round_policy = round_policy or RoundWindowPolicy.from_env()
        self.max_round_lag = self.round_policy.max_round_lag
        self.max_round_lead = self.round_policy.max_round_lead

        epoch_from_env = os.getenv("WAVEPROBE_ROUND_EPOCH_ANCHOR")
        if round_epoch_anchor is not None:
            self.round_epoch_anchor = max(0, round_epoch_anchor)
        elif epoch_from_env is not None:
            try:
                self.round_epoch_anchor = max(0, int(epoch_from_env))
            except ValueError:
                raise ValueError(f"Invalid WAVEPROBE_ROUND_EPOCH_ANCHOR: {epoch_from_env!r}") from None
        else:
            self.round_epoch_anchor = 0

        self.latest_round_by_mode: Dict[int, int] = {}

    @staticmethod
    def replay_key(data: bytes, mode: int) -> bytes:
        """Build replay key material from full packet bytes and mode."""
        return hashlib.sha256(data + mode.to_bytes(1, "big", signed=False)).digest()
    
    def listen_for_intents(self, duration_secs: int = 2, modes: Optional[List[int]] = None) -> Dict[int, List[CompressedIntent]]:
        """Listen on specific modes for incoming intents
        
        Args:
            duration_secs: How long to listen
            modes: List of modes to listen on (default: all 14)
        
        Returns:
            Dict mapping mode -> list of intents received
        """
        if modes is None:
            modes = list(range(14))
        
        intents_by_mode: Dict[int, List[CompressedIntent]] = {}
        
        for mode in modes:
            try:
                result = subprocess.run(
                    self.command_builder.build(
                        "recv",
                        "--mode", str(mode),
                        "--timeout", str(duration_secs),
                    ),
                    capture_output=True,
                    timeout=duration_secs + 2,
                    shell=False,
                    check=False,
                )
                
                # Parse output: each packet is a hex line
                if result.stdout:
                    for line in result.stdout.decode().strip().split('\n'):
                        if line and not line.startswith('['):
                            try:
                                data = bytes.fromhex(line)
                                intent = CompressedIntent.unpack(
                                    data,
                                    otp_secret=self.otp_secret,
                                    mode=mode,
                                    require_otp=self.require_otp,
                                )
                                if intent:
                                    latest_round = self.latest_round_by_mode.get(mode, self.round_epoch_anchor)
                                    if intent.round_number + self.max_round_lag < latest_round:
                                        continue
                                    if intent.round_number > latest_round + self.max_round_lead:
                                        continue
                                    self.latest_round_by_mode[mode] = max(latest_round or 0, intent.round_number)
                                    replay_key = self.replay_key(data, mode)
                                    if self.replay_guard.is_replay(replay_key):
                                        continue
                                    if mode not in intents_by_mode:
                                        intents_by_mode[mode] = []
                                    intents_by_mode[mode].append(intent)
                            except ValueError:
                                pass
            except subprocess.TimeoutExpired:
                pass
            except PermissionError as exc:
                raise RuntimeError(self.command_builder.permission_hint()) from exc
            except FileNotFoundError as exc:
                raise RuntimeError(f"ghost_icmp executable not found: {self.ghost_icmp_path}") from exc
            except Exception:
                pass
        
        return intents_by_mode
    
    def aggregate_intents(self, intents_by_mode: Dict[int, List[CompressedIntent]]) -> Dict[str, float]:
        """Analyze received intents and determine coordinated action
        
        Returns coordination metadata for bots to follow.
        """
        # Aggregate by target pool
        pool_votes: Dict[int, Tuple[int, int]] = {}  # pool_id -> (count, avg_fitness)
        
        for _, intents in intents_by_mode.items():
            for intent in intents:
                if intent.intent_type in [IntentType.BID, IntentType.EXECUTE]:
                    if intent.pool_id not in pool_votes:
                        pool_votes[intent.pool_id] = (0, 0)
                    count, sum_fitness = pool_votes[intent.pool_id]
                    pool_votes[intent.pool_id] = (count + 1, sum_fitness + intent.fitness)
        
        # Determine strongest consensus
        if not pool_votes:
            return {'consensus_pool': 0, 'consensus_strength': 0}
        
        # Deterministic tie-breaks prevent split-brain behavior across bots.
        best_pool = max(pool_votes.items(), key=lambda item: (item[1][0], item[1][1], -item[0]))
        pool_id, (count, sum_fitness) = best_pool
        avg_fitness = sum_fitness // max(1, count)
        
        return {
            'consensus_pool': pool_id,
            'consensus_strength': count,
            'avg_fitness': avg_fitness,
            'timestamp': time.time(),
        }

    def log_round_adaptation(
        self,
        round_number: int,
        expected_output: float,
        observed_output: float,
        chosen_utility: float,
        best_counterfactual_utility: float,
        shock: bool = False,
        consensus_pool: int = 0,
        consensus_strength: int = 0,
    ) -> RoundAdaptationLog:
        """Record one adaptation sample for surprise/regret analysis."""
        return self.adaptation.record_round(
            round_number=round_number,
            expected_output=expected_output,
            observed_output=observed_output,
            chosen_utility=chosen_utility,
            best_counterfactual_utility=best_counterfactual_utility,
            shock=shock,
            consensus_pool=consensus_pool,
            consensus_strength=consensus_strength,
        )

    @staticmethod
    def _bucket(value: float, bins: int, clip_min: float, clip_max: float) -> int:
        if bins <= 1:
            return 0
        value = max(clip_min, min(clip_max, value))
        width = (clip_max - clip_min) / bins
        if width <= 0:
            return 0
        bucket = int((value - clip_min) / width)
        return max(0, min(bins - 1, bucket))

    def _homeostasis_degrade_level(self, summary: Dict[str, float]) -> int:
        shock_observed = summary.get("shock_count", 0.0) > 0.0
        severe = (
            summary.get("delta_sign_stability", 1.0) < self.homeostasis_level2_sign_stability_floor
            or (
                shock_observed
                and summary.get("shock_to_recovery_success_ratio", 1.0)
                < self.homeostasis_level2_shock_recovery_ratio_floor
            )
            or summary.get("median_recovery_half_life", 0.0) > self.homeostasis_level2_median_half_life_ceiling
        )
        if severe:
            return 2

        degraded = (
            summary.get("delta_sign_stability", 1.0) < self.homeostasis_alert_policy.sign_stability_floor
            or (
                shock_observed
                and summary.get("shock_to_recovery_success_ratio", 1.0)
                < self.homeostasis_alert_policy.shock_recovery_ratio_floor
            )
            or summary.get("median_recovery_half_life", 0.0) > self.homeostasis_alert_policy.median_half_life_ceiling
        )
        return 1 if degraded else 0

    def _homeostasis_recovered_for_release(self, summary: Dict[str, float]) -> bool:
        return (
            summary.get("delta_sign_stability", 0.0) >= self.homeostasis_hysteresis_sign_stability_release
            and summary.get("shock_to_recovery_success_ratio", 0.0) >= self.homeostasis_hysteresis_shock_recovery_release
            and summary.get("median_recovery_half_life", float("inf")) <= self.homeostasis_hysteresis_median_half_life_release
        )

    def homeostasis_fallback_status(self, last_n: int = 64) -> Dict[str, float | int | bool | None]:
        """Return fallback controller status for health checks/telemetry sinks."""
        summary = self.shadow.rolling_homeostasis_summary(last_n=last_n)
        degrade_level = self._homeostasis_degrade_level(summary)

        if self._homeostasis_level2_lock_active:
            effective_tier = 2
        elif self._homeostasis_fallback_rounds_remaining > 0:
            effective_tier = 1
        else:
            effective_tier = 0

        return {
            "fallback_tier": effective_tier,
            "level2_lock_active": self._homeostasis_level2_lock_active,
            "release_streak": self._homeostasis_recovery_streak,
            "hysteresis_release_rounds": self.homeostasis_hysteresis_release_rounds,
            "fallback_rounds_remaining": self._homeostasis_fallback_rounds_remaining,
            "configured_fallback_action_id": self.homeostasis_fallback_action_id,
            "degrade_level": degrade_level,
            "summary": summary,
        }

    def to_health_payload(self, last_n: int = 64) -> Dict[str, object]:
        """Return a redacted, stable health payload for dashboards/alerts."""
        fallback = self.homeostasis_fallback_status(last_n=last_n)
        summary = fallback["summary"] if isinstance(fallback.get("summary"), dict) else {}
        payload = {
            "schema_version": "waveprobe.health.v1",
            "timestamp": int(time.time()),
            "window_rounds": int(last_n),
            "health": {
                "fallback_tier": int(fallback.get("fallback_tier", 0)),
                "level2_lock_active": bool(fallback.get("level2_lock_active", False)),
                "release_streak": int(fallback.get("release_streak", 0)),
                "hysteresis_release_rounds": int(fallback.get("hysteresis_release_rounds", 0)),
                "degrade_level": int(fallback.get("degrade_level", 0)),
                "fallback_action_engaged": bool(int(fallback.get("fallback_tier", 0)) > 0),
            },
            "metrics": {
                "count": float(summary.get("count", 0.0)),
                "shock_count": float(summary.get("shock_count", 0.0)),
                "median_recovery_half_life": float(summary.get("median_recovery_half_life", 0.0)),
                "delta_sign_stability": float(summary.get("delta_sign_stability", 1.0)),
                "shock_to_recovery_success_ratio": float(summary.get("shock_to_recovery_success_ratio", 0.0)),
            },
        }
        # Enforce JSON-safe primitives and fail closed if schema drifts.
        return json.loads(json.dumps(payload, sort_keys=True, separators=(",", ":")))

    def to_health_payload_json(self, last_n: int = 64) -> str:
        """Return the stable health payload as a pre-encoded JSON string."""
        return json.dumps(self.to_health_payload(last_n=last_n), sort_keys=True, separators=(",", ":"))

    def log_shadow_round(
        self,
        round_number: int,
        expected_output: float,
        baseline_observed_output: float,
        codon_observed_output: float,
        baseline_utility: float,
        codon_utility: float,
        best_counterfactual_utility: float,
        shock: bool = False,
        recent_action_id: int = -1,
    ) -> ShadowDecisionLog:
        """Run baseline and codon sidecars in shadow mode and record deltas."""
        baseline_surprise = self.adaptation.compute_surprise(expected_output, baseline_observed_output)
        codon_surprise = self.adaptation.compute_surprise(expected_output, codon_observed_output)
        baseline_regret = self.adaptation.compute_regret(baseline_utility, best_counterfactual_utility)
        codon_regret = self.adaptation.compute_regret(codon_utility, best_counterfactual_utility)

        features = {
            "surprise_bin": self._bucket(codon_surprise, bins=8, clip_min=0.0, clip_max=1.0),
            "regret_bin": self._bucket(codon_regret, bins=8, clip_min=0.0, clip_max=1.0),
            "brownout_bin": 3 if shock else 0,
            "recent_action_id": int(recent_action_id),
        }

        self._ndag_feature_lag.append(dict(features))
        if len(self._ndag_feature_lag) > self.ndag_output_lag_rounds:
            lagged_features = dict(self._ndag_feature_lag[-(self.ndag_output_lag_rounds + 1)])
            effective_round = max(0, round_number - self.ndag_output_lag_rounds)
        else:
            lagged_features = dict(self._ndag_feature_lag[0])
            effective_round = round_number

        baseline_action = self.shadow_baseline_sidecar.decide(effective_round, lagged_features)
        codon_action = self.shadow_codon_sidecar.decide(effective_round, lagged_features)
        fallback_applied = False
        fallback_tier = 0

        pre_summary = self.shadow.rolling_homeostasis_summary(last_n=64)
        pre_level = self._homeostasis_degrade_level(pre_summary)
        if not self._homeostasis_level2_lock_active:
            if pre_level >= 2:
                self._homeostasis_level2_lock_active = True
                self._homeostasis_recovery_streak = 0
                self._homeostasis_fallback_rounds_remaining = 0
            elif pre_level == 1:
                self._homeostasis_fallback_rounds_remaining = max(
                    self._homeostasis_fallback_rounds_remaining,
                    self.homeostasis_fallback_min_rounds,
                )

        if self._homeostasis_level2_lock_active:
            codon_action = self.homeostasis_fallback_action_id
            fallback_applied = True
            fallback_tier = 2
        elif self._homeostasis_fallback_rounds_remaining > 0:
            codon_action = self.homeostasis_fallback_action_id
            fallback_applied = True
            fallback_tier = 1
            self._homeostasis_fallback_rounds_remaining -= 1

        log = self.shadow.record(
            round_number=round_number,
            baseline_action=baseline_action,
            codon_action=codon_action,
            baseline_surprise=baseline_surprise,
            codon_surprise=codon_surprise,
            baseline_regret=baseline_regret,
            codon_regret=codon_regret,
            shock=shock,
            ndag_lag_rounds=self.ndag_output_lag_rounds,
            ndag_effective_round=effective_round,
            fallback_applied=fallback_applied,
            fallback_tier=fallback_tier,
            fallback_action_id=self.homeostasis_fallback_action_id if fallback_applied else None,
            level2_lock_active=self._homeostasis_level2_lock_active,
        )

        post_summary = self.shadow.rolling_homeostasis_summary(last_n=64)
        post_level = self._homeostasis_degrade_level(post_summary)

        if self._homeostasis_level2_lock_active:
            if self._homeostasis_recovered_for_release(post_summary):
                self._homeostasis_recovery_streak += 1
                if self._homeostasis_recovery_streak >= self.homeostasis_hysteresis_release_rounds:
                    self._homeostasis_level2_lock_active = False
                    self._homeostasis_recovery_streak = 0
            else:
                self._homeostasis_recovery_streak = 0
        else:
            if post_level >= 2:
                self._homeostasis_level2_lock_active = True
                self._homeostasis_recovery_streak = 0
                self._homeostasis_fallback_rounds_remaining = 0
            elif post_level == 1:
                self._homeostasis_fallback_rounds_remaining = max(
                    self._homeostasis_fallback_rounds_remaining,
                    self.homeostasis_fallback_min_rounds,
                )
        return log


class BotIntentBeacon:
    """Mixin for BotAgent to emit trade intents via ICMP Ghost"""
    
    def __init__(self, otp_secret: Optional[str] = None):
        raw_secret = otp_secret or os.getenv("WAVEPROBE_OTP_SECRET")
        if not raw_secret:
            raise ValueError("WAVEPROBE_OTP_SECRET is required for bot beacon emission")
        self.otp_secret = raw_secret.encode("utf-8")

    def send_trade_intent_beacon(
        self,
        coordinator_ip: str,
        bot_mode: int,
        round_number: int,
        pool_hash_prefix: int,
        amount: float,
        expected_output: float,
        is_sol_to_usdc: bool,
        smoothing_score: float,
        timestamp_delta_ms: int = 0,
        round_ticks: int = 60000,
    ) -> bool:
        """Send compressed trade intent via ICMP Ghost beacon
        
        Called from inside execute_round() before trades are sent on-chain.
        
        Returns:
            True if beacon sent, False otherwise
        """
        # Quantize amounts to log-scale (power of 2)
        def log_quantize(x: float) -> int:
            import math
            if x <= 0: return 0
            exp = int(math.log2(x))
            return max(0, min(65535, exp))
        
        pool_rollup_id = MirrorLUTRollup.rollup_id(
            canonical_address=pool_hash_prefix,
            round_number=round_number,
            otp_secret=self.otp_secret,
        )

        intent = CompressedIntent(
            intent_type=IntentType.BID,
            pool_id=pool_rollup_id,
            amount_quantized=log_quantize(amount),
            expected_output=log_quantize(expected_output),
            direction=is_sol_to_usdc,
            fitness=int(smoothing_score * 255),  # Map [0, 1] to [0, 255]
            swarm_target=0,  # No coordination for now
            phase_locked=True,  # Assume coherent for MVP
            timestamp_delta_ms=timestamp_delta_ms,
            round_number=round_number,
        )
        
        client = JupiterGhostClient()
        payload = intent.pack(otp_secret=self.otp_secret, mode=bot_mode)
        
        # Send to coordinator
        result = client.send(target=coordinator_ip, mode=bot_mode, data=payload, round_ticks=round_ticks)
        
        if result:
            print(f"[WaveProbe] Intent beacon sent on mode {bot_mode} -> {coordinator_ip}")
        
        return result


# ── Full integration example ───────────────────────────────────────────────

def demo_coordination_round():
    """Example: one full coordination round"""

    print("=" * 80)
    print("WAVEPROBE ICMP COORDINATOR DEMO")
    print("=" * 80)
    
    # Assume ghost_icmp is built
    ghost_path = "./tools/ghost_icmp/target/debug/ghost_icmp"
    if not os.path.exists(ghost_path):
        print(f"[!] ghost_icmp not found at {ghost_path}")
        print("    Build with: cd tools/ghost_icmp && cargo build")
        return
    
    coordinator = CoordinatorListener(ghost_icmp_path=ghost_path)
    
    print("\n[Phase 1] Listening for bot intents on all 14 modes (2 sec)...")
    intents_by_mode = coordinator.listen_for_intents(duration_secs=2, modes=list(range(14)))
    
    print(f"[Phase 2] Received intents from {len(intents_by_mode)} modes")
    for mode, intents in intents_by_mode.items():
        print(f"  Mode {mode}: {len(intents)} intent(s)")
    
    print("\n[Phase 3] Aggregating coordination signal...")
    coordination = coordinator.aggregate_intents(intents_by_mode)
    
    print(f"  Consensus pool: {coordination['consensus_pool']}")
    print(f"  Consensus strength: {coordination['consensus_strength']}/14")
    print(f"  Average fitness: {coordination['avg_fitness']}/255")

    round_number = int(time.time())
    shock = coordination['consensus_strength'] <= 1
    expected_output = 100.0
    baseline_observed_output = max(0.0, expected_output - (coordination['consensus_strength'] * 9.0))
    codon_observed_output = max(0.0, expected_output - (coordination['consensus_strength'] * 6.0))
    baseline_utility = float(coordination['avg_fitness'])
    codon_utility = min(255.0, baseline_utility + 8.0)
    best_counterfactual_utility = max(codon_utility, baseline_utility, 1.0)

    shadow_log = coordinator.log_shadow_round(
        round_number=round_number,
        expected_output=expected_output,
        baseline_observed_output=baseline_observed_output,
        codon_observed_output=codon_observed_output,
        baseline_utility=baseline_utility,
        codon_utility=codon_utility,
        best_counterfactual_utility=best_counterfactual_utility,
        shock=shock,
    )
    print("\n[Phase 3b] Shadow adaptation telemetry...")
    print(f"  Baseline action: {shadow_log.baseline_action}")
    print(f"  Codon action: {shadow_log.codon_action}")
    print(f"  n-DAG lag (rounds): {shadow_log.ndag_lag_rounds}")
    print(f"  n-DAG effective round: {shadow_log.ndag_effective_round}")
    print(f"  Fallback applied: {shadow_log.fallback_applied}")
    print(f"  Fallback tier: {shadow_log.fallback_tier}")
    print(f"  Fallback action id: {shadow_log.fallback_action_id}")
    print(f"  Level-2 lock active: {shadow_log.level2_lock_active}")
    print(f"  Surprise delta (codon-baseline): {shadow_log.surprise_delta:.4f}")
    print(f"  Regret delta (codon-baseline): {shadow_log.regret_delta:.4f}")
    print(f"  Recovery half-life surprise (rounds): {shadow_log.recovery_half_life_surprise}")
    print(f"  Recovery half-life regret (rounds): {shadow_log.recovery_half_life_regret}")
    summary = coordinator.shadow.rolling_homeostasis_summary(last_n=64)
    print(f"  Median recovery half-life: {summary['median_recovery_half_life']:.4f}")
    print(f"  Delta sign stability: {summary['delta_sign_stability']:.4f}")
    print(f"  Shock-to-recovery success ratio: {summary['shock_to_recovery_success_ratio']:.4f}")
    alert_state = coordinator.shadow.alert_state(
        policy=coordinator.homeostasis_alert_policy,
        last_n=64,
    )
    fallback_status = coordinator.homeostasis_fallback_status(last_n=64)
    print(
        "  Fallback status API: "
        f"tier={fallback_status['fallback_tier']} "
        f"lock={fallback_status['level2_lock_active']} "
        f"release_streak={fallback_status['release_streak']}"
    )
    health_payload = coordinator.to_health_payload(last_n=64)
    health_payload_json = coordinator.to_health_payload_json(last_n=64)
    print(
        "  Health payload: "
        f"schema={health_payload['schema_version']} "
        f"tier={health_payload['health']['fallback_tier']} "
        f"degrade={health_payload['health']['degrade_level']}"
    )
    print(f"  Health payload bytes: {len(health_payload_json.encode('utf-8'))}")
    if alert_state["homeostasis_degraded"]:
        print("  Homeostasis degraded: YES")
        for reason in alert_state["reasons"]:
            print(f"    - {reason}")
    else:
        print("  Homeostasis degraded: NO")
    
    print("\n[Phase 4] Broadcasting coordination signal back to bots...")
    print("  (In production, coordinator would send EXECUTE on each bot's mode)")
    
    print("\n" + "=" * 80)
    print("✓ Coordination complete — bots execute synchronized on-chain")
    print("=" * 80)


if __name__ == "__main__":
    demo_coordination_round()
