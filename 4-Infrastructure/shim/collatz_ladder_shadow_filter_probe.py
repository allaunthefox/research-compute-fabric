#!/usr/bin/env python3
"""Collatz ladder shadow-filter receipt for witness roughness.

Collatz is used here as a deterministic integer-shadow filter, not as physics
or compression proof. A witness state is quantized to an integer; the Collatz
path gives a cheap roughness/traversal signal. The ladder generalization maps
reducible states downward, irreducible torsioned states upward with closure
repair, and unsafe states to a declared horizon.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "collatz_ladder_shadow_filter"
REGISTRY = OUT_DIR / "collatz_ladder_shadow_filter_registry.json"
RECEIPT = OUT_DIR / "collatz_ladder_shadow_filter_receipt.json"
SUMMARY = OUT_DIR / "collatz_ladder_shadow_filter.md"
TIDDLER = REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers" / "Collatz Ladder Shadow Filter.tid"

SOURCE_REFS = [
    REPO / "shared-data" / "data" / "godel_gauntlet_safety_condition" / "godel_gauntlet_safety_condition_receipt.json",
    REPO / "shared-data" / "data" / "torsion_interval_gaussian_splat_witness" / "torsion_interval_gaussian_splat_witness_receipt.json",
    REPO / "shared-data" / "data" / "pixelwell_external_prior" / "pixelwell_external_prior_receipt.json",
    REPO / "shared-data" / "data" / "hutter_multidimensional_causal_chain" / "hutter_multidimensional_causal_chain_receipt.json",
]


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_obj(obj: Any) -> str:
    return sha256_bytes(stable_json(obj).encode("utf-8"))


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def file_hash(path: Path) -> str | None:
    return sha256_bytes(path.read_bytes()) if path.exists() else None


def source_ref(path: Path) -> dict[str, Any]:
    return {"path": rel(path), "exists": path.exists(), "sha256": file_hash(path)}


def collatz_path(n: int, max_steps: int = 512) -> dict[str, Any]:
    if n < 1:
        raise ValueError("Collatz shadow requires a positive integer")
    path = [n]
    parity = []
    current = n
    for _ in range(max_steps):
        if current == 1:
            break
        if current % 2 == 0:
            parity.append("E")
            current //= 2
        else:
            parity.append("O")
            current = 3 * current + 1
        path.append(current)
    reached_one = path[-1] == 1
    odd_count = parity.count("O")
    even_count = parity.count("E")
    return {
        "start": n,
        "steps": len(path) - 1,
        "reached_one": reached_one,
        "max_value": max(path),
        "odd_count": odd_count,
        "even_count": even_count,
        "parity_prefix": "".join(parity[:64]),
        "path_hash": hash_obj(path),
    }


def quantize_state(state: dict[str, Any]) -> int:
    payload = stable_json(state).encode("utf-8")
    # Keep values small enough for fixture readability while still deterministic.
    return int.from_bytes(hashlib.sha256(payload).digest()[:4], "big") % 5000 + 2


def classify_shadow(shadow: dict[str, Any], residual_risk: float, sigma_max: int) -> str:
    if residual_risk >= 0.9:
        return "HOLD_RESIDUAL_HORIZON"
    if not shadow["reached_one"]:
        return "HOLD_COLLATZ_BOUND_EXCEEDED"
    if shadow["steps"] > sigma_max:
        return "HOLD_RECURSION_ROUGHNESS"
    if shadow["odd_count"] > shadow["even_count"]:
        return "HOLD_ODD_BRANCH_BURST"
    return "ADMIT_COLLATZ_SHADOW_FILTER"


def sample_state(
    state_id: str,
    ladder_rung: int,
    torsion: float,
    residual_risk: float,
    axes: list[str],
    sigma_max: int,
) -> dict[str, Any]:
    state = {
        "state_id": state_id,
        "ladder_rung": ladder_rung,
        "torsion": torsion,
        "residual_risk": residual_risk,
        "axes": axes,
    }
    n = quantize_state(state)
    shadow = collatz_path(n)
    decision = classify_shadow(shadow, residual_risk, sigma_max)
    item = {
        "state": state,
        "integer_shadow": n,
        "collatz_shadow": shadow,
        "sigma_max": sigma_max,
        "decision": decision,
        "route_role": "roughness_hint_only",
    }
    item["sample_hash"] = hash_obj({k: v for k, v in item.items() if k != "sample_hash"})
    return item


def build_registry() -> dict[str, Any]:
    sigma_max = 120
    samples = [
        sample_state("boring_replay_root", 0, 0.05, 0.05, ["provenance", "byte_neighbor"], sigma_max),
        sample_state("chirality_torsion_adapter", 2, 0.35, 0.22, ["chirality", "codec_torsion"], sigma_max),
        sample_state("orientation_360_bump", 3, 0.44, 0.31, ["orientation_360_share", "semantic_class"], sigma_max),
        sample_state("gaussian_splat_hotspot", 4, 0.72, 0.58, ["codec_torsion", "observer_chart"], sigma_max),
        sample_state("residual_horizon_packet", 5, 0.93, 0.94, ["byte_neighbor", "observer_chart"], sigma_max),
    ]
    return {
        "schema": "collatz_ladder_shadow_filter_registry_v1",
        "source_refs": [source_ref(path) for path in SOURCE_REFS],
        "claim_boundary": (
            "Collatz ladder shadow-filter diagnostic only. It uses Collatz paths as "
            "deterministic integer-shadow roughness hints and traversal schedules. "
            "It does not prove the Collatz conjecture, mechanical safety, or Hutter compression."
        ),
        "canonical_statement": (
            "Reducible states project downward, irreducible torsioned states expand "
            "upward with a closure witness, and unsafe residuals terminate at a "
            "declared horizon. Collatz parity is the integer-shadow scheduler for "
            "testing recursion roughness."
        ),
        "collatz_equation": {
            "integer_shadow": "n_k = Q(Omega_k)",
            "ordinary_step": "C(n)=n/2 if even, 3n+1 if odd",
            "stopping_time": "sigma_C(n)=min m such that C^m(n)=1",
            "filter": "A_C(Omega)=1[sigma_C(Q(Omega)) <= sigma_max]",
        },
        "ladder_generalization": {
            "state": "Omega_k=(rho,G,Gamma,C,T,R_M,epsilon)_k",
            "down_branch": "pi_{k-1}(Omega_k) when reducible/admissible",
            "up_branch": "Phi_{k+1}(Omega_k)=3Omega+1_closure+Delta_T+epsilon_repair when torsioned/irreducible",
            "horizon": "bottom if residual exceeds admissible boundary",
            "terminal_classes": ["stable_invariant_attractor", "bounded_chart_cycle", "declared_non_admissible_boundary"],
        },
        "samples": samples,
        "shadow_root": hash_obj([item["sample_hash"] for item in samples]),
        "aggregates": {
            "sample_count": len(samples),
            "admit_count": sum(1 for item in samples if item["decision"].startswith("ADMIT")),
            "hold_count": sum(1 for item in samples if item["decision"].startswith("HOLD")),
            "max_stopping_time": max(item["collatz_shadow"]["steps"] for item in samples),
            "max_shadow_value": max(item["collatz_shadow"]["max_value"] for item in samples),
        },
        "decision": "ADMIT_COLLATZ_LADDER_SHADOW_FILTER_DIAGNOSTIC",
    }


def build_receipt(registry: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "collatz_ladder_shadow_filter_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "registry": rel(REGISTRY),
        "registry_hash": hash_obj(registry),
        "shadow_root": registry["shadow_root"],
        "aggregates": registry["aggregates"],
        "decision": registry["decision"],
        "claim_boundary": registry["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(registry: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# Collatz Ladder Shadow Filter",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        f"Shadow root: `{registry['shadow_root']}`",
        "",
        registry["claim_boundary"],
        "",
        "## Canonical Statement",
        "",
        registry["canonical_statement"],
        "",
        "## Collatz Equation",
        "",
    ]
    for key, value in registry["collatz_equation"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Ladder Generalization", ""])
    for key, value in registry["ladder_generalization"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Samples", "", "| State | n | Steps | Odd | Even | Max | Decision |", "|---|---:|---:|---:|---:|---:|---|"])
    for item in registry["samples"]:
        shadow = item["collatz_shadow"]
        lines.append(
            f"| `{item['state']['state_id']}` | {item['integer_shadow']} | {shadow['steps']} | "
            f"{shadow['odd_count']} | {shadow['even_count']} | {shadow['max_value']} | `{item['decision']}` |"
        )
    lines.extend(["", "## Source Refs", ""])
    for source in registry["source_refs"]:
        lines.append(f"- `{source['path']}` exists: `{source['exists']}`")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tiddler(receipt: dict[str, Any]) -> None:
    text = f"""created: 20260509000000000
modified: 20260509000000000
tags: ResearchStack Collatz Ladder ShadowFilter Hutter HOLD Receipt
title: Collatz Ladder Shadow Filter
type: text/vnd.tiddlywiki

! Collatz Ladder Shadow Filter

Durable runner:

```
4-Infrastructure/shim/collatz_ladder_shadow_filter_probe.py
```

Receipt:

```
{rel(RECEIPT)}
```

Receipt hash:

```
{receipt['receipt_hash']}
```

Shadow root:

```
{receipt['shadow_root']}
```

!! Doctrine

Collatz is used as a deterministic integer-shadow filter, not as physics or
compression proof. Short paths are recursion-tame route hints. Long paths,
odd-branch bursts, or residual horizons stay inspection/HOLD surfaces.

!! Links

* [[Godel Gauntlet Safety Condition Probe]]
* [[Torsion Interval Gaussian Splat Witness]]
* [[PixelWell External Prior]]
* [[Hutter Multidimensional Causal Chain]]
"""
    TIDDLER.write_text(text, encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    registry = build_registry()
    receipt = build_receipt(registry)
    REGISTRY.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(registry, receipt)
    write_tiddler(receipt)
    print(
        json.dumps(
            {
                "registry": rel(REGISTRY),
                "receipt": rel(RECEIPT),
                "summary": rel(SUMMARY),
                "tiddler": rel(TIDDLER),
                "receipt_hash": receipt["receipt_hash"],
                "shadow_root": registry["shadow_root"],
                "decision": receipt["decision"],
                "aggregates": registry["aggregates"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
