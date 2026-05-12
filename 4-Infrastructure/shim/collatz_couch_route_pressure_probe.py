#!/usr/bin/env python3
"""Collatz/COUCH route-pressure probe.

COUCH is local project terminology here: a finite route-pressure witness over
coupling regimes. This probe keeps the existing COUCH witnesses frozen and uses
Collatz only as an integer-shadow roughness scheduler over those finite packets.
It does not promote the continuous COUCH equation or the Collatz conjecture.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "collatz_couch_route_pressure"
REGISTRY = OUT_DIR / "collatz_couch_route_pressure_registry.json"
RECEIPT = OUT_DIR / "collatz_couch_route_pressure_receipt.json"
SUMMARY = OUT_DIR / "collatz_couch_route_pressure.md"
TIDDLER = REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers" / "Collatz COUCH Route Pressure Probe.tid"

SOURCE_REFS = [
    REPO / "0-Core-Formalism" / "lean" / "Semantics" / "Semantics" / "CouchFilterNormalization.lean",
    REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers" / "COUCH Family.tid",
    REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers" / "F-Number COUCH.tid",
    REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers" / "Route-Pressure COUCH Gate.tid",
    REPO / "shared-data" / "data" / "collatz_ladder_shadow_filter" / "collatz_ladder_shadow_filter_receipt.json",
    REPO / "shared-data" / "data" / "godel_gauntlet_safety_condition" / "godel_gauntlet_safety_condition_receipt.json",
]

COUCH_REGIMES = [
    {
        "regime": "kappa050",
        "kappa_milli": 500,
        "f_couch_milli": 18085,
        "u_rot_milli": 8785,
        "r_value_milli": 1000,
        "p_couch_milli": 25870,
        "routing_mode": "exploitLocal",
    },
    {
        "regime": "kappa100",
        "kappa_milli": 1000,
        "f_couch_milli": 18163,
        "u_rot_milli": 9552,
        "r_value_milli": 1000,
        "p_couch_milli": 26715,
        "routing_mode": "exploitLocal",
    },
    {
        "regime": "kappa150",
        "kappa_milli": 1500,
        "f_couch_milli": 18274,
        "u_rot_milli": 10322,
        "r_value_milli": 1000,
        "p_couch_milli": 27596,
        "routing_mode": "exploreAtlas",
    },
    {
        "regime": "kappa200",
        "kappa_milli": 2000,
        "f_couch_milli": 18419,
        "u_rot_milli": 11093,
        "r_value_milli": 1000,
        "p_couch_milli": 28512,
        "routing_mode": "exploreAtlas",
    },
    {
        "regime": "kappa250",
        "kappa_milli": 2500,
        "f_couch_milli": 18596,
        "u_rot_milli": 11867,
        "r_value_milli": 1000,
        "p_couch_milli": 29463,
        "routing_mode": "rejectDivergent",
    },
]

SIGMA_MAX = 120


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
        raise ValueError("Collatz COUCH shadow requires a positive integer")
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
    return {
        "start": n,
        "steps": len(path) - 1,
        "reached_one": path[-1] == 1,
        "max_value": max(path),
        "odd_count": parity.count("O"),
        "even_count": parity.count("E"),
        "parity_prefix": "".join(parity[:64]),
        "path_hash": hash_obj(path),
    }


def classify(regime: dict[str, Any], shadow: dict[str, Any]) -> str:
    if regime["routing_mode"] == "rejectDivergent":
        return "REJECT_COUCH_DIVERGENT"
    if not shadow["reached_one"]:
        return "HOLD_COLLATZ_BOUND_EXCEEDED"
    if shadow["steps"] > SIGMA_MAX:
        return "HOLD_COLLATZ_COUCH_ROUGHNESS"
    if regime["routing_mode"] == "exploreAtlas":
        return "HOLD_COUCH_ATLAS_ROUTE"
    return "ADMIT_LOCAL_COUCH_COLLATZ_HINT"


def build_case(regime: dict[str, Any]) -> dict[str, Any]:
    shadow = collatz_path(regime["p_couch_milli"])
    decision = classify(regime, shadow)
    case = {
        **regime,
        "integer_shadow": {
            "rule": "n_k = P_COUCH(kappa)",
            "value": regime["p_couch_milli"],
        },
        "collatz_shadow": shadow,
        "sigma_max": SIGMA_MAX,
        "decision": decision,
        "route_role": "roughness_scheduler_only",
    }
    case["case_hash"] = hash_obj({k: v for k, v in case.items() if k != "case_hash"})
    return case


def build_registry() -> dict[str, Any]:
    cases = [build_case(regime) for regime in COUCH_REGIMES]
    decisions = sorted({case["decision"] for case in cases})
    return {
        "schema": "collatz_couch_route_pressure_registry_v1",
        "source_refs": [source_ref(path) for path in SOURCE_REFS],
        "claim_boundary": (
            "COUCH supplies finite route pressure over local coupling regimes. "
            "Collatz supplies deterministic recursion roughness over the finite "
            "COUCH pressure packets. This is a scheduler/guardrail diagnostic, "
            "not a proof of the continuous COUCH equation, the Collatz conjecture, "
            "mechanical safety, or Hutter compression."
        ),
        "canonical_statement": (
            "COUCH decides local, atlas, or divergent route pressure; Collatz "
            "then probes each finite P_COUCH packet for integer-shadow recursion "
            "roughness. Local COUCH routes with tame shadows may be used as local "
            "hints, atlas routes remain HOLD for atlas verification, and divergent "
            "COUCH routes reject before Collatz can rescue them."
        ),
        "couch_equations": {
            "f_number": "F_COUCH(kappa)=avg_curvature_milli(kappa)+max_curvature_milli(kappa)+FAMM_frustration_milli",
            "u_rotated": "U_rot(kappa)=avg_curvature_milli(kappa)+kappa_milli*avg_norm_milli(kappa)/1000",
            "route_pressure": "P_COUCH(kappa)=F_COUCH(kappa)+U_rot(kappa)-R_value",
            "local_atlas_reject_thresholds": {
                "atlas_threshold_milli": 27000,
                "reject_threshold_milli": 29000,
            },
        },
        "collatz_equations": {
            "integer_shadow": "n_k=P_COUCH(kappa)",
            "ordinary_step": "C(n)=n/2 if even, 3n+1 if odd",
            "stopping_time": "sigma_C(n)=min m such that C^m(n)=1",
            "filter": "A_CC(kappa)=COUCH_mode(kappa) and sigma_C(P_COUCH(kappa))<=sigma_max",
        },
        "cases": cases,
        "case_root": hash_obj([case["case_hash"] for case in cases]),
        "aggregates": {
            "case_count": len(cases),
            "admit_count": sum(1 for case in cases if case["decision"].startswith("ADMIT")),
            "hold_count": sum(1 for case in cases if case["decision"].startswith("HOLD")),
            "reject_count": sum(1 for case in cases if case["decision"].startswith("REJECT")),
            "decision_counts": {
                decision: sum(1 for case in cases if case["decision"] == decision)
                for decision in decisions
            },
            "max_stopping_time": max(case["collatz_shadow"]["steps"] for case in cases),
            "max_shadow_value": max(case["collatz_shadow"]["max_value"] for case in cases),
        },
        "decision": "ADMIT_COLLATZ_COUCH_ROUTE_PRESSURE_DIAGNOSTIC",
    }


def build_receipt(registry: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "collatz_couch_route_pressure_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "registry": rel(REGISTRY),
        "registry_hash": hash_obj(registry),
        "case_root": registry["case_root"],
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
        "# Collatz COUCH Route Pressure Probe",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        f"Case root: `{registry['case_root']}`",
        "",
        registry["claim_boundary"],
        "",
        "## Canonical Statement",
        "",
        registry["canonical_statement"],
        "",
        "## Equations",
        "",
        f"- `{registry['couch_equations']['f_number']}`",
        f"- `{registry['couch_equations']['route_pressure']}`",
        f"- `{registry['collatz_equations']['integer_shadow']}`",
        f"- `{registry['collatz_equations']['ordinary_step']}`",
        f"- `{registry['collatz_equations']['filter']}`",
        "",
        "## Sweep",
        "",
        "| Regime | F_COUCH | U_rot | P_COUCH | COUCH mode | Collatz steps | Max value | Decision |",
        "|---|---:|---:|---:|---|---:|---:|---|",
    ]
    for case in registry["cases"]:
        lines.append(
            f"| {case['regime']} | {case['f_couch_milli']} | {case['u_rot_milli']} | "
            f"{case['p_couch_milli']} | {case['routing_mode']} | "
            f"{case['collatz_shadow']['steps']} | {case['collatz_shadow']['max_value']} | "
            f"{case['decision']} |"
        )
    lines.extend(
        [
            "",
            "## Aggregates",
            "",
            f"- Cases: `{registry['aggregates']['case_count']}`",
            f"- Admitted local hints: `{registry['aggregates']['admit_count']}`",
            f"- HOLD routes: `{registry['aggregates']['hold_count']}`",
            f"- Rejected routes: `{registry['aggregates']['reject_count']}`",
            f"- Max stopping time: `{registry['aggregates']['max_stopping_time']}`",
            f"- Max shadow value: `{registry['aggregates']['max_shadow_value']}`",
        ]
    )
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tiddler(registry: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "created: 20260509000000000",
        "modified: 20260509000000000",
        "tags: ResearchStack COUCH Collatz Hutter Routing Probe",
        "title: Collatz COUCH Route Pressure Probe",
        "type: text/vnd.tiddlywiki",
        "",
        "! Collatz COUCH Route Pressure Probe",
        "",
        "COUCH is used with its local formal meaning: a finite route-pressure gate over coupling regimes.",
        "",
        f"* Decision: `{receipt['decision']}`",
        f"* Receipt hash: `{receipt['receipt_hash']}`",
        f"* Case root: `{registry['case_root']}`",
        f"* Registry: `{rel(REGISTRY)}`",
        f"* Receipt: `{rel(RECEIPT)}`",
        "",
        "!! Rule",
        "",
        "Collatz is a deterministic roughness scheduler over finite `P_COUCH` packets. It cannot rescue a divergent COUCH route and does not prove Collatz or the continuous COUCH equation.",
        "",
        "```",
        registry["couch_equations"]["route_pressure"],
        registry["collatz_equations"]["integer_shadow"],
        registry["collatz_equations"]["filter"],
        "```",
        "",
        "!! Sweep",
        "",
        "| Regime | P_COUCH | COUCH mode | Collatz steps | Decision |",
        "|---|---:|---|---:|---|",
    ]
    for case in registry["cases"]:
        lines.append(
            f"| {case['regime']} | {case['p_couch_milli']} | {case['routing_mode']} | "
            f"{case['collatz_shadow']['steps']} | {case['decision']} |"
        )
    lines.extend(
        [
            "",
            "!! Links",
            "",
            "* [[COUCH Family]]",
            "* [[F-Number COUCH]]",
            "* [[Route-Pressure COUCH Gate]]",
            "* [[Collatz Ladder Shadow Filter]]",
            "* [[Godel Gauntlet Safety Condition Probe]]",
        ]
    )
    TIDDLER.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TIDDLER.parent.mkdir(parents=True, exist_ok=True)
    registry = build_registry()
    receipt = build_receipt(registry)
    REGISTRY.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(registry, receipt)
    write_tiddler(registry, receipt)
    print(
        json.dumps(
            {
                "registry": rel(REGISTRY),
                "receipt": rel(RECEIPT),
                "summary": rel(SUMMARY),
                "tiddler": rel(TIDDLER),
                "receipt_hash": receipt["receipt_hash"],
                "case_root": registry["case_root"],
                "aggregates": registry["aggregates"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
