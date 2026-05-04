#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
# PTOS: LAYER=CORE / DOMAIN=COMPUTE / CONDITION=EXPERIMENTAL / STAGE=ACTIVE / SOURCE=CODE
"""Crossbreed Shear Validator — T-C-P Cross-Domain Shear Unity

Surviving Invariant
-------------------
Name:        T-C-P Cross-Domain Shear Unity
Description: The sum of pairwise constraint shears among temporal, coherence,
             and progress dimensions across lighthouse and quantum-gravity
             domains is exactly unity.
Equation:    (T_A C_B - C_A T_B) + (C_A P_B - P_A C_B) + (T_A P_B - P_A T_B) = 1
Domains:     🕯️ Lighthouse Keeper × 🌌 Quantum Gravity Researcher

This module provides a deterministic, mathematically-rigid validator for the
shear-unity invariant. It operates on 7-dimensional constraint vectors (T, S, C,
F, R, P, W) but extracts the T/C/P subspace to evaluate the cross-domain shear.
"""

from __future__ import annotations

import math
import sys
from typing import Any, Dict, List, Mapping, Sequence

# ── Constants ─────────────────────────────────────────────────────────────────

EPSILON: float = 1e-9
DIMENSIONS: List[str] = ["T", "S", "C", "F", "R", "P", "W"]

# ── Validator ─────────────────────────────────────────────────────────────────


class CrossbreedShearValidator:
    """Deterministic validator for the T-C-P Cross-Domain Shear Unity invariant.

    The validator accepts constraint surfaces expressed as 7-dimensional vectors
    (or as T/C/P sub-dictionaries) and evaluates the shear equation that must
    hold at the intersection boundary of the Lighthouse Keeper and Quantum
    Gravity Researcher domains.
    """

    @staticmethod
    def _extract_tcp(value: Mapping[str, Any]) -> Dict[str, float]:
        """Extract T, C, P floats from a mapping.

        If the input is a sequence, it is treated as a 7D vector ordered
        [T, S, C, F, R, P, W] and the T, C, P slots are pulled out.
        """
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            vec = [float(v) for v in value]
            if len(vec) < 7:
                raise ValueError(
                    f"7D vector required for Hadamard intersection, got {len(vec)} elements"
                )
            return {"T": vec[0], "C": vec[2], "P": vec[5]}

        missing = {"T", "C", "P"} - set(value.keys())
        if missing:
            raise KeyError(f"Missing required shear dimensions: {missing}")
        return {k: float(value[k]) for k in ("T", "C", "P")}

    def compute_shear_unity(
        self,
        constraints_a: Mapping[str, Any],
        constraints_b: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """Compute the left-hand side of the shear-unity equation.

        Args:
            constraints_a: Domain A constraint surface (dict or 7D sequence).
            constraints_b: Domain B constraint surface (dict or 7D sequence).

        Returns:
            {
                "value": float,      # computed LHS
                "holds": bool,       # True if |value - 1.0| <= 1e-9
                "components": {
                    "tc": T_A*C_B - C_A*T_B,
                    "cp": C_A*P_B - P_A*C_B,
                    "tp": T_A*P_B - P_A*T_B,
                },
            }
        """
        a = self._extract_tcp(constraints_a)
        b = self._extract_tcp(constraints_b)

        tc = a["T"] * b["C"] - a["C"] * b["T"]
        cp = a["C"] * b["P"] - a["P"] * b["C"]
        tp = a["T"] * b["P"] - a["P"] * b["T"]

        value = tc + cp + tp
        holds = math.isclose(value, 1.0, abs_tol=EPSILON)

        return {
            "value": value,
            "holds": holds,
            "components": {
                "tc": tc,
                "cp": cp,
                "tp": tp,
            },
        }

    def hadamard_intersection(
        self,
        a: Sequence[float],
        b: Sequence[float],
    ) -> List[float]:
        """Return the 7D Hadamard (element-wise) product of two constraint vectors.

        Args:
            a: 7-dimensional constraint vector.
            b: 7-dimensional constraint vector.

        Returns:
            List of 7 floats representing the intersection surface.
        """
        if len(a) != 7 or len(b) != 7:
            raise ValueError(
                f"Hadamard intersection requires exactly 7D inputs (got {len(a)} and {len(b)})"
            )
        return [float(x) * float(y) for x, y in zip(a, b)]


# ── Demonstration ─────────────────────────────────────────────────────────────


def _demo() -> int:
    validator = CrossbreedShearValidator()

    # Actual expert-derived constraints for the Lighthouse Keeper × Quantum
    # Gravity Researcher crossbreed (see 6-Documentation/docs/audits/EXHAUSTIVE_DOMAIN_EXPERT_LIST.md).
    lighthouse_constraints = {
        "T": 0.97,
        "S": 0.51,
        "C": 0.98,
        "F": 0.72,
        "R": 0.92,
        "P": 0.75,
        "W": 0.48,
    }

    qg_constraints = {
        "T": 0.1,
        "S": 0.25,
        "C": 0.9,
        "F": 0.0,
        "R": 0.360673590227324,
        "P": 0.5,
        "W": 0.274,
    }

    print("=" * 60)
    print("T-C-P CROSS-DOMAIN SHEAR UNITY — DEMONSTRATION")
    print("=" * 60)
    print("Domain A: 🕯️ Lighthouse Keeper")
    print("Domain B: 🌌 Quantum Gravity Researcher")
    print()

    # 1. Shear unity evaluation
    result = validator.compute_shear_unity(lighthouse_constraints, qg_constraints)
    print(f"Shear value: {result['value']:.12f}")
    print(f"Holds (ε ≤ {EPSILON}): {result['holds']}")
    print("Components:")
    for key, val in result["components"].items():
        print(f"  {key}: {val:.12f}")
    print()

    # 2. 7D Hadamard intersection
    vec_a = [lighthouse_constraints[d] for d in DIMENSIONS]
    vec_b = [qg_constraints[d] for d in DIMENSIONS]
    intersection = validator.hadamard_intersection(vec_a, vec_b)
    print("7D Hadamard intersection:")
    for d, val in zip(DIMENSIONS, intersection):
        print(f"  {d}: {val:.12f}")
    print()

    print("=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)

    return 0 if result["holds"] else 1


if __name__ == "__main__":
    sys.exit(_demo())
