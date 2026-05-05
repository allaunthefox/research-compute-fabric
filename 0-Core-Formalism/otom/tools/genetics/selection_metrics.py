#!/usr/bin/env python3
"""Selection metrics scaffold for the OTOM genetics information substrate.

This module is intentionally small and dependency-free.  It turns the genetics
boundary record's first promotion candidate into an executable path:

  - Tajima's D from segregating sites, pairwise differences, and sample size
  - Hudson-style FST from within-population and between-population differences

Claim-state boundary:
  These functions are engineering scaffolds.  They do not by themselves prove
  selection, ancestry, or fitness claims.  Promotion requires provenance-bearing
  data fixtures and receipts.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Iterable, Sequence


@dataclass(frozen=True)
class TajimasDInput:
    """Inputs for Tajima's D.

    sample_size:
        Number of sampled haploid sequences. Must be at least 2.
    segregating_sites:
        Count of segregating sites S. Must be non-negative.
    pairwise_differences:
        Average number of pairwise differences pi across the region.
    """

    sample_size: int
    segregating_sites: int
    pairwise_differences: float


@dataclass(frozen=True)
class TajimasDResult:
    theta_watterson: float
    tajimas_d: float
    variance: float
    claim_state: str = "ENGINEERING_SCAFFOLD"


@dataclass(frozen=True)
class FstResult:
    within_mean: float
    between_mean: float
    fst: float
    claim_state: str = "ENGINEERING_SCAFFOLD"


def _validate_nonnegative(name: str, value: float) -> None:
    if value < 0:
        raise ValueError(f"{name} must be non-negative, got {value!r}")


def harmonic_sum(n: int, power: int = 1) -> float:
    """Return sum_{i=1}^{n} 1 / i^power."""

    if n < 1:
        raise ValueError(f"n must be >= 1, got {n!r}")
    if power < 1:
        raise ValueError(f"power must be >= 1, got {power!r}")
    return sum(1.0 / (i**power) for i in range(1, n + 1))


def tajimas_d(data: TajimasDInput) -> TajimasDResult:
    """Compute Tajima's D using the standard finite-sample constants.

    D = (pi - S/a1) / sqrt(e1*S + e2*S*(S-1))

    Returns D=0 when S=0 and variance is zero, because there is no segregating
    signal to evaluate.  Callers should treat that as non-promoting evidence.
    """

    n = data.sample_size
    s = data.segregating_sites
    pi = data.pairwise_differences

    if n < 2:
        raise ValueError(f"sample_size must be >= 2, got {n!r}")
    _validate_nonnegative("segregating_sites", s)
    _validate_nonnegative("pairwise_differences", pi)

    a1 = harmonic_sum(n - 1, 1)
    a2 = harmonic_sum(n - 1, 2)
    b1 = (n + 1) / (3 * (n - 1))
    b2 = (2 * (n * n + n + 3)) / (9 * n * (n - 1))
    c1 = b1 - (1 / a1)
    c2 = b2 - ((n + 2) / (a1 * n)) + (a2 / (a1 * a1))
    e1 = c1 / a1
    e2 = c2 / ((a1 * a1) + a2)

    theta_w = s / a1
    variance = e1 * s + e2 * s * (s - 1)

    if variance <= 0:
        return TajimasDResult(theta_watterson=theta_w, tajimas_d=0.0, variance=variance)

    return TajimasDResult(
        theta_watterson=theta_w,
        tajimas_d=(pi - theta_w) / sqrt(variance),
        variance=variance,
    )


def _mean(values: Sequence[float], name: str) -> float:
    if not values:
        raise ValueError(f"{name} must contain at least one value")
    for value in values:
        _validate_nonnegative(name, value)
    return sum(values) / len(values)


def hudson_fst(within_pairwise_differences: Sequence[float], between_pairwise_differences: Sequence[float]) -> FstResult:
    """Compute a simple Hudson-style FST estimate.

    FST = 1 - mean_within / mean_between

    The input values should be pairwise sequence differences or comparable
    genetic distances.  If between-population divergence is zero, FST is returned
    as zero to avoid division by zero; callers should treat that as non-promoting.
    """

    within = _mean(within_pairwise_differences, "within_pairwise_differences")
    between = _mean(between_pairwise_differences, "between_pairwise_differences")

    if between <= 0:
        return FstResult(within_mean=within, between_mean=between, fst=0.0)

    fst = 1.0 - (within / between)
    if fst < 0:
        fst = 0.0
    if fst > 1:
        fst = 1.0
    return FstResult(within_mean=within, between_mean=between, fst=fst)


def mass_number_selection_pressure(tajima: TajimasDResult, fst: FstResult) -> float:
    """Toy MassNumber pressure proxy for promotion triage.

    This is deliberately not a formal MassNumber implementation.  It gives a
    monotone engineering score for issue triage:

      abs(TajimaD) + FST

    The score must be replaced by the Lean/Q16_16 MassNumber gate before any
    reviewed claim is promoted.
    """

    return abs(tajima.tajimas_d) + fst.fst


def _demo() -> None:
    tajima = tajimas_d(TajimasDInput(sample_size=10, segregating_sites=12, pairwise_differences=4.2))
    fst = hudson_fst(within_pairwise_differences=[1.2, 1.5, 1.1], between_pairwise_differences=[3.0, 3.3, 2.8])
    print("tajimas_d", tajima)
    print("hudson_fst", fst)
    print("selection_pressure_proxy", mass_number_selection_pressure(tajima, fst))


if __name__ == "__main__":
    _demo()
