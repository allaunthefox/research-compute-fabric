#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Reference helpers for attention-stage and multipath cognitive load tests.

This module is intentionally small and boring. It is not the whole runtime
router. It is a clean-room reference implementation for the equations in:

- 6-Documentation/docs/ATTENTION_SURFACE_REFINEMENT_OF_CANONICAL_EQUATION_2026-04-09.md
- 6-Documentation/docs/MULTIPATH_COGNITIVE_LOAD_REFINEMENT_2026-04-09.md

The goal is to make the emerging mechanics testable before they sprawl.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Iterable, Mapping


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True)
class SourceObservation:
    """A single source-family observation over one or more candidates."""

    source_id: str
    family_weight: float = 1.0
    freshness: float = 1.0
    health: float = 1.0
    trust: float = 1.0
    support: Mapping[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class AttentionBreakdown:
    """Explainable score components for one candidate."""

    candidate: str
    convergence: float
    contradiction: float
    degradation: float
    hot_cost: float
    total: float


@dataclass(frozen=True)
class LoadBreakdown:
    """Weighted multipath load components."""

    intrinsic: float
    extraneous: float
    germane: float
    routing: float
    memory: float
    total: float


def effective_evidence_weight(observation: SourceObservation) -> float:
    """Combine source-family weight with freshness, health, and trust."""

    return max(0.0, float(observation.family_weight)) * (
        _clamp01(observation.freshness)
        * _clamp01(observation.health)
        * _clamp01(observation.trust)
    )


def _support_value(observation: SourceObservation, candidate: str) -> float:
    return max(0.0, float(observation.support.get(candidate, 0.0)))


def convergence_score(
    candidate: str,
    observations: Iterable[SourceObservation],
) -> float:
    """Weighted positive support for a candidate across source families."""

    total = 0.0
    for observation in observations:
        total += effective_evidence_weight(observation) * _support_value(
            observation, candidate
        )
    return total


def contradiction_score(
    candidate: str,
    observations: Iterable[SourceObservation],
) -> float:
    """Pairwise disagreement over the same candidate.

    High disagreement can increase attention while still failing the truth gate.
    """

    scored = []
    for observation in observations:
        weight = effective_evidence_weight(observation)
        support = _support_value(observation, candidate)
        scored.append((weight, support))

    total = 0.0
    for i in range(len(scored)):
        weight_i, support_i = scored[i]
        for j in range(i + 1, len(scored)):
            weight_j, support_j = scored[j]
            total += weight_i * weight_j * abs(support_i - support_j)
    return total


def degradation_penalty(
    candidate: str,
    observations: Iterable[SourceObservation],
) -> float:
    """Penalty for leaning on stale, unhealthy, or weakly trusted evidence."""

    total = 0.0
    for observation in observations:
        raw_weight = max(0.0, float(observation.family_weight))
        quality = (
            _clamp01(observation.freshness)
            * _clamp01(observation.health)
            * _clamp01(observation.trust)
        )
        total += raw_weight * (1.0 - quality) * _support_value(observation, candidate)
    return total


def attention_score(
    candidate: str,
    observations: Iterable[SourceObservation],
    *,
    alpha_conv: float = 1.0,
    alpha_ctr: float = 1.0,
    alpha_deg: float = 1.0,
    alpha_hot: float = 1.0,
    hot_cost: float = 0.0,
) -> AttentionBreakdown:
    """Compute the attention-stage score for a candidate."""

    convergence = convergence_score(candidate, observations)
    contradiction = contradiction_score(candidate, observations)
    degradation = degradation_penalty(candidate, observations)
    total = (
        alpha_conv * convergence
        + alpha_ctr * contradiction
        - alpha_deg * degradation
        - alpha_hot * max(0.0, float(hot_cost))
    )
    return AttentionBreakdown(
        candidate=candidate,
        convergence=convergence,
        contradiction=contradiction,
        degradation=degradation,
        hot_cost=max(0.0, float(hot_cost)),
        total=total,
    )


def promote_candidates(
    scores: Mapping[str, float],
    threshold: float,
) -> set[str]:
    """Return the promoted candidate set."""

    return {candidate for candidate, score in scores.items() if score >= threshold}


def softmax_activation(
    scores: Mapping[str, float],
    *,
    beta: float = 1.0,
    top_k: int | None = None,
) -> dict[str, float]:
    """Convert attention scores into a bounded activation field."""

    if not scores:
        return {}

    ordered = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    if top_k is not None:
        if top_k <= 0:
            return {}
        ordered = ordered[:top_k]

    max_score = max(score for _, score in ordered)
    weights = {
        candidate: math.exp(float(beta) * (score - max_score))
        for candidate, score in ordered
    }
    denom = sum(weights.values())
    if denom == 0.0:
        return {candidate: 0.0 for candidate in weights}
    return {candidate: value / denom for candidate, value in weights.items()}


def activation_entropy(activations: Mapping[str, float]) -> float:
    """Shannon entropy of the activation field in bits."""

    total = 0.0
    for probability in activations.values():
        if probability > 0.0:
            total -= probability * math.log2(probability)
    return total


def support_size(activations: Mapping[str, float]) -> int:
    """Number of paths with nonzero activation mass."""

    return sum(1 for value in activations.values() if value > 0.0)


def premature_collapse_penalty(
    activations: Mapping[str, float],
    viable_paths: Iterable[str],
    *,
    min_secondary_mass: float = 0.2,
) -> float:
    """Penalty when a viable second path is collapsed too early."""

    masses = sorted(
        (max(0.0, float(activations.get(path, 0.0))) for path in viable_paths),
        reverse=True,
    )
    if len(masses) < 2:
        return 0.0
    return max(0.0, float(min_secondary_mass) - masses[1])


def overdiffuse_penalty(
    activations: Mapping[str, float],
    *,
    max_active_paths: int = 3,
    max_entropy_bits: float = 1.5,
) -> float:
    """Penalty when the activation field spreads too wide."""

    active_excess = max(0, support_size(activations) - int(max_active_paths))
    entropy_excess = max(0.0, activation_entropy(activations) - float(max_entropy_bits))
    return float(active_excess) + entropy_excess


def multipath_extraneous_load(
    path_mismatch: Mapping[str, float],
    activations: Mapping[str, float],
    *,
    viable_paths: Iterable[str] | None = None,
    mu_prem: float = 1.0,
    mu_diff: float = 1.0,
    min_secondary_mass: float = 0.2,
    max_active_paths: int = 3,
    max_entropy_bits: float = 1.5,
) -> float:
    """Reference multipath extraneous-load calculation."""

    weighted_mismatch = 0.0
    for path, mass in activations.items():
        weighted_mismatch += float(mass) * max(0.0, float(path_mismatch.get(path, 0.0)))

    viable = viable_paths if viable_paths is not None else activations.keys()
    prem = premature_collapse_penalty(
        activations,
        viable,
        min_secondary_mass=min_secondary_mass,
    )
    diffuse = overdiffuse_penalty(
        activations,
        max_active_paths=max_active_paths,
        max_entropy_bits=max_entropy_bits,
    )
    return weighted_mismatch + float(mu_prem) * prem + float(mu_diff) * diffuse


def multipath_routing_load(
    attention_cost: float,
    activations: Mapping[str, float],
    *,
    maintain_coeff: float = 1.0,
    entropy_coeff: float = 1.0,
    collapse_cost: float = 0.0,
) -> float:
    """Reference routing-load split into attention, maintenance, and collapse."""

    return (
        max(0.0, float(attention_cost))
        + float(maintain_coeff) * support_size(activations)
        + float(entropy_coeff) * activation_entropy(activations)
        + max(0.0, float(collapse_cost))
    )


def multipath_memory_load(
    store_size: int,
    activations: Mapping[str, float],
    *,
    memory_hits: Iterable[str] | None = None,
    retrieval_cost: float = 1.0,
    update_cost: float = 1.0,
    eviction_pressure: float = 0.0,
    conflict_penalty: float = 0.0,
) -> float:
    """Reference ensemble memory-load calculation."""

    hits = set(memory_hits or ())
    hit_mass = sum(
        float(mass) for path, mass in activations.items() if path in hits and mass > 0.0
    )
    return (
        math.log2(max(1, int(store_size)))
        + float(retrieval_cost) * hit_mass
        + max(0.0, float(update_cost))
        + max(0.0, float(eviction_pressure))
        + max(0.0, float(conflict_penalty))
    )


def truth_gate(
    *,
    consensus_sources: int,
    min_sources: int = 2,
    onchain_verified: bool,
    recovery_matches: bool,
) -> bool:
    """Conservative truth gate used after attention promotion."""

    return (
        int(consensus_sources) >= int(min_sources)
        and bool(onchain_verified)
        and bool(recovery_matches)
    )


def total_multipath_load(
    *,
    intrinsic: float,
    extraneous: float,
    germane: float,
    routing: float,
    memory: float,
    lambda_i: float = 1.0,
    lambda_e: float = 1.0,
    lambda_g: float = 1.0,
    lambda_r: float = 1.0,
    lambda_m: float = 1.0,
) -> LoadBreakdown:
    """Assemble weighted total load from already-computed components."""

    total = (
        float(lambda_i) * float(intrinsic)
        + float(lambda_e) * float(extraneous)
        - float(lambda_g) * float(germane)
        + float(lambda_r) * float(routing)
        + float(lambda_m) * float(memory)
    )
    return LoadBreakdown(
        intrinsic=float(intrinsic),
        extraneous=float(extraneous),
        germane=float(germane),
        routing=float(routing),
        memory=float(memory),
        total=total,
    )
