#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Reference helpers for explicit test gate semantics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal


GateSeverity = Literal["HARD", "SOFT", "INFO"]
GateVerdict = Literal["PASS", "WARN", "FAIL"]


@dataclass(frozen=True)
class GateCheck:
    """One explicit gate in a test or validation surface."""

    gate_id: str
    severity: GateSeverity
    passed: bool
    condition: str
    observed: object | None = None
    threshold: object | None = None
    failure_message: str = ""


@dataclass(frozen=True)
class GateSummary:
    """Aggregated verdict over a bundle of gates."""

    verdict: GateVerdict
    hard_failed: tuple[str, ...]
    soft_failed: tuple[str, ...]
    info_failed: tuple[str, ...]
    total_gates: int


def summarize_gates(checks: Iterable[GateCheck]) -> GateSummary:
    """Apply the canonical gate policy.

    Verdict order:
    1. Any HARD failure -> FAIL
    2. Else any SOFT failure -> WARN
    3. Else -> PASS
    """

    hard_failed: list[str] = []
    soft_failed: list[str] = []
    info_failed: list[str] = []
    count = 0

    for check in checks:
        count += 1
        if check.passed:
            continue
        if check.severity == "HARD":
            hard_failed.append(check.gate_id)
        elif check.severity == "SOFT":
            soft_failed.append(check.gate_id)
        else:
            info_failed.append(check.gate_id)

    if hard_failed:
        verdict: GateVerdict = "FAIL"
    elif soft_failed:
        verdict = "WARN"
    else:
        verdict = "PASS"

    return GateSummary(
        verdict=verdict,
        hard_failed=tuple(hard_failed),
        soft_failed=tuple(soft_failed),
        info_failed=tuple(info_failed),
        total_gates=count,
    )
