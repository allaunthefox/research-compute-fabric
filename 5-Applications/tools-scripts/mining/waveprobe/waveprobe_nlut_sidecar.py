#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Deterministic n-LUT sidecar for decision scoring.

This module is intentionally decision-only and does not participate in
transport identity, packet auth, or replay checks.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Protocol, Tuple


@dataclass(frozen=True)
class NLUTSchema:
    """Canonical schema for n-LUT indexing."""

    version: int
    axes: Tuple[Tuple[str, int], ...]
    action_ids: Tuple[int, ...]

    def __post_init__(self) -> None:
        if self.version < 0:
            raise ValueError("version must be non-negative")
        if not self.axes:
            raise ValueError("at least one axis is required")
        if not self.action_ids:
            raise ValueError("at least one action_id is required")
        seen = set()
        for name, bins in self.axes:
            if name in seen:
                raise ValueError(f"duplicate axis name: {name}")
            if bins <= 0:
                raise ValueError(f"axis bins must be > 0 for axis {name}")
            seen.add(name)

    def hash(self) -> str:
        payload = {
            "version": self.version,
            "axes": list(self.axes),
            "action_ids": list(self.action_ids),
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True)
class DecisionContext:
    """Immutable context passed through codon primitives."""

    round_number: int
    features: Dict[str, int]
    idx: int
    scores: Tuple[int, ...]
    action_ids: Tuple[int, ...]


class CodonRule(Protocol):
    """Protocol for pluggable deterministic codon rules."""

    name: str

    def apply(self, context: DecisionContext) -> DecisionContext:
        ...


@dataclass(frozen=True)
class SurpriseDampeningCodon:
    """Dampen high-risk actions when surprise bucket is elevated."""

    threshold: int = 3
    penalty: int = 5
    target_feature: str = "surprise_bin"
    name: str = "surprise_dampening"

    def apply(self, context: DecisionContext) -> DecisionContext:
        if int(context.features.get(self.target_feature, 0)) < self.threshold:
            return context
        adjusted = [max(-32768, score - self.penalty) for score in context.scores]
        return DecisionContext(
            round_number=context.round_number,
            features=context.features,
            idx=context.idx,
            scores=tuple(adjusted),
            action_ids=context.action_ids,
        )


@dataclass(frozen=True)
class RegretCooldownCodon:
    """Discourage repeating recent action under high regret buckets."""

    threshold: int = 3
    penalty: int = 8
    target_feature: str = "regret_bin"
    recent_action_feature: str = "recent_action_id"
    name: str = "regret_cooldown"

    def apply(self, context: DecisionContext) -> DecisionContext:
        if int(context.features.get(self.target_feature, 0)) < self.threshold:
            return context

        recent_action = int(context.features.get(self.recent_action_feature, -1))
        if recent_action not in context.action_ids:
            return context

        adjusted = list(context.scores)
        target_pos = context.action_ids.index(recent_action)
        adjusted[target_pos] = max(-32768, adjusted[target_pos] - self.penalty)
        return DecisionContext(
            round_number=context.round_number,
            features=context.features,
            idx=context.idx,
            scores=tuple(adjusted),
            action_ids=context.action_ids,
        )


@dataclass(frozen=True)
class BrownoutConservationCodon:
    """Prefer lower action ids during brownout buckets (resource-conservative fallback)."""

    threshold: int = 2
    bonus: int = 4
    target_feature: str = "brownout_bin"
    name: str = "brownout_conservation"

    def apply(self, context: DecisionContext) -> DecisionContext:
        if int(context.features.get(self.target_feature, 0)) < self.threshold:
            return context

        min_action = min(context.action_ids)
        adjusted = list(context.scores)
        for pos, action_id in enumerate(context.action_ids):
            if action_id == min_action:
                adjusted[pos] = min(32767, adjusted[pos] + self.bonus)
                break
        return DecisionContext(
            round_number=context.round_number,
            features=context.features,
            idx=context.idx,
            scores=tuple(adjusted),
            action_ids=context.action_ids,
        )


@dataclass
class DeterministicNLUTSidecar:
    """Deterministic n-LUT scorer with round-based schema hash pinning."""

    schema: NLUTSchema
    table: Dict[int, Tuple[int, ...]]
    pinned_round_schema_hash: Dict[int, str] = field(default_factory=dict)
    codon_rules: List[CodonRule] = field(default_factory=list)

    def pin_schema_for_round(self, round_number: int) -> str:
        if round_number < 0:
            raise ValueError("round_number must be non-negative")
        schema_hash = self.schema.hash()
        existing = self.pinned_round_schema_hash.get(round_number)
        if existing is not None and existing != schema_hash:
            raise ValueError(
                f"schema hash mismatch for round {round_number}: pinned={existing} current={schema_hash}"
            )
        self.pinned_round_schema_hash[round_number] = schema_hash
        return schema_hash

    def index(self, features: Dict[str, int]) -> int:
        idx = 0
        for axis_name, bins in self.schema.axes:
            value = int(features.get(axis_name, 0))
            value = max(0, min(bins - 1, value))
            idx = (idx * bins) + value
        return idx

    def scores_for_index(self, idx: int) -> Tuple[int, ...]:
        default_scores = tuple(0 for _ in self.schema.action_ids)
        scores = self.table.get(idx, default_scores)
        if len(scores) != len(self.schema.action_ids):
            raise ValueError("score tuple size does not match schema action_ids")
        return scores

    def apply_codons(self, context: DecisionContext) -> DecisionContext:
        result = context
        for codon in self.codon_rules:
            result = codon.apply(result)
        return result

    def decide(self, round_number: int, features: Dict[str, int]) -> int:
        self.pin_schema_for_round(round_number)
        idx = self.index(features)
        scores = self.scores_for_index(idx)
        context = DecisionContext(
            round_number=round_number,
            features=dict(features),
            idx=idx,
            scores=scores,
            action_ids=self.schema.action_ids,
        )
        context = self.apply_codons(context)
        scores = context.scores

        best_pos = 0
        best_score = scores[0]
        best_action = self.schema.action_ids[0]
        for pos in range(1, len(scores)):
            score = scores[pos]
            action = self.schema.action_ids[pos]
            if score > best_score:
                best_pos = pos
                best_score = score
                best_action = action
                continue
            if score == best_score and action < best_action:
                best_pos = pos
                best_score = score
                best_action = action

        _ = best_pos
        return best_action


def build_flat_table(size: int, actions: Iterable[int], fill: int = 0) -> Dict[int, Tuple[int, ...]]:
    """Convenience helper for deterministic table bootstrap."""
    action_list = tuple(actions)
    if size < 0:
        raise ValueError("size must be non-negative")
    return {index: tuple(fill for _ in action_list) for index in range(size)}
