#!/usr/bin/env python3
"""MS3C-RG route-prior geometry shim.

This is intentionally a small integer-first harness. It computes the corrected
S3C split, a Matroska-style nested shell descriptor, and a bounded shear score.
It does not make physical brane claims; it emits a route-prior codon that GCL
must admit or refuse.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class S3CSplit:
    n: int
    k: int
    a: int
    b0: int
    b_plus: int
    mass: int
    mirror_delta: int
    parity: int


@dataclass(frozen=True)
class MatroskaCodon:
    k: int
    a: int
    b0: int
    b_plus: int
    mass: int
    mirror_delta: int
    parity: int
    shell_phase: float
    contra_rotation: int
    shear: int
    claim_status: str = "route_prior_geometry_not_physical_brane_claim"


def s3c_split(n: int) -> S3CSplit:
    if n < 0:
        raise ValueError("n must be non-negative")
    k = math.isqrt(n)
    a = n - k * k
    b0 = (k + 1) * (k + 1) - 1 - n
    b_plus = b0 + 1
    return S3CSplit(
        n=n,
        k=k,
        a=a,
        b0=b0,
        b_plus=b_plus,
        mass=a * b0,
        mirror_delta=a - b0,
        parity=n & 1,
    )


def signed_contra_rotation(split: S3CSplit, parent_k: int | None = None) -> int:
    parent = split.k - 1 if parent_k is None else parent_k
    direction = 1 if split.k % 2 == 0 else -1
    parent_direction = 1 if parent % 2 == 0 else -1
    return direction - parent_direction


def shear_score(split: S3CSplit, contra_rotation: int) -> int:
    width = max(1, 2 * split.k)
    mass_term = (split.mass * 255) // max(1, split.k * split.k)
    mirror_term = (abs(split.mirror_delta) * 255) // width
    tension_term = (split.b_plus * 255) // max(1, 2 * split.k + 1)
    contra_term = min(255, abs(contra_rotation) * 96)
    return min(255, (mass_term + mirror_term + tension_term + contra_term) // 4)


def make_codon(n: int, parent_k: int | None = None) -> MatroskaCodon:
    split = s3c_split(n)
    contra = signed_contra_rotation(split, parent_k)
    phase_width = max(1, 2 * split.k + 1)
    phase = split.a / phase_width
    shear = shear_score(split, contra)
    return MatroskaCodon(
        k=split.k,
        a=split.a,
        b0=split.b0,
        b_plus=split.b_plus,
        mass=split.mass,
        mirror_delta=split.mirror_delta,
        parity=split.parity,
        shell_phase=round(phase, 6),
        contra_rotation=contra,
        shear=shear,
    )


def event(codon: MatroskaCodon) -> dict[str, object]:
    verdict = "observe"
    if codon.shear >= 220:
        verdict = "renormalize"
    elif codon.shear >= 144:
        verdict = "route_candidate"
    return {
        "v": "ms3c-rg-0.2",
        "claim_status": codon.claim_status,
        "matroska_codon": asdict(codon),
        "gcl_wrap": [
            "OBSERVE",
            "BIND",
            "ROUTE",
            "SIGMA_CHECK",
            "POLICY_CHECK",
            "DAG_CHECK",
            "VERIFY",
            "RECEIPT",
        ],
        "famm_memory": {
            "failed_route": "coarse_grain_ban_region",
            "successful_route": "reinforce_route_prior",
            "ambiguous_route": "hold_review",
        },
        "route_prior_verdict": verdict,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("n", type=lambda value: int(value, 0))
    parser.add_argument("--parent-k", type=int, default=None)
    args = parser.parse_args()
    print(json.dumps(event(make_codon(args.n, args.parent_k)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
