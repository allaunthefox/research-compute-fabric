#!/usr/bin/env python3
"""Godel Gauntlet safety-condition probe for Hutter/logogram promotion.

The race-condition gauntlet checks order sensitivity. This companion probe
checks other promotion hazards: replay, roots, provenance, residuals, unsafe
literalization, local-chart globalization, chirality adapters, 360 orientation
bucket completeness, timestamp misuse, baseline debt, and the hard Hutter Prize
resource envelope.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "godel_gauntlet_safety_condition"
REGISTRY = OUT_DIR / "godel_gauntlet_safety_condition_registry.json"
RECEIPT = OUT_DIR / "godel_gauntlet_safety_condition_receipt.json"
SUMMARY = OUT_DIR / "godel_gauntlet_safety_condition.md"
TIDDLER = REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers" / "Godel Gauntlet Safety Condition Probe.tid"

SOURCE_REFS = [
    REPO / "shared-data" / "data" / "godel_gauntlet_race_condition" / "godel_gauntlet_race_condition_receipt.json",
    REPO / "shared-data" / "data" / "hutter_multidimensional_causal_chain" / "hutter_multidimensional_causal_chain_receipt.json",
    REPO / "shared-data" / "data" / "hutter_torsion_clock_adaptation" / "hutter_torsion_clock_adaptation_receipt.json",
    REPO / "shared-data" / "data" / "observer_chart_projection_guardrail" / "observer_chart_projection_guardrail_receipt.json",
    REPO / "shared-data" / "data" / "joke_source_literalization_guardrail" / "joke_source_literalization_guardrail_receipt.json",
    REPO / "shared-data" / "data" / "logogram_dna_codec" / "logogram_dna_codec_receipt.json",
    REPO / "4-Infrastructure" / "shim" / "foundation_forward_equation_compiler.py",
]

CHECKS = [
    "exact_replay",
    "root_recomputes",
    "provenance_truthful",
    "axis_declared",
    "bounded_witness",
    "residual_declared",
    "dependency_admitted",
    "timestamp_metadata_only",
    "baseline_gate_closed",
    "chirality_adapter_declared",
    "orientation_buckets_complete",
    "safe_literalization",
    "local_chart_not_globalized",
    "order_stable_or_residual_declared",
    "resource_envelope_ok",
]

RESOURCE_ENVELOPE = {
    "source": "https://prize.hutter1.net/hrules.htm",
    "rule_summary": "Each submitted program must run under 70,000/T hours, use at most 10GB RAM and 100GB HDD temporary files, and use no GPU.",
    "max_hours_formula": "70000 / geekbench5_score_T",
    "max_ram_gb": 10,
    "max_temp_hdd_gb": 100,
    "gpu_allowed": False,
    "single_core_headline_source": "https://prize.hutter1.net/",
    "single_core_headline": "main prize page summarizes the restriction as about 50 hours using a single CPU core with <10GB RAM and <100GB HDD on the test machine",
}


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


def classify(flags: dict[str, bool]) -> str:
    if not flags["safe_literalization"]:
        return "QUARANTINE_UNSAFE_LITERALIZATION"
    if not flags["exact_replay"]:
        return "REJECT_REPLAY"
    if not flags["root_recomputes"]:
        return "REJECT_ROOT_MISMATCH"
    if not flags["provenance_truthful"]:
        return "HOLD_PROVENANCE"
    if not flags["timestamp_metadata_only"]:
        return "HOLD_CLOCK_IN_HASH"
    if not flags["axis_declared"]:
        return "HOLD_AXIS_UNDECLARED"
    if not flags["bounded_witness"]:
        return "HOLD_UNBOUNDED_WITNESS"
    if not flags["dependency_admitted"]:
        return "HOLD_DEPENDENCY_NOT_ADMITTED"
    if not flags["residual_declared"]:
        return "HOLD_RESIDUAL_MISSING"
    if not flags["local_chart_not_globalized"]:
        return "HOLD_LOCAL_CHART_GLOBALIZED"
    if not flags["chirality_adapter_declared"]:
        return "HOLD_CHIRALITY_ADAPTER_MISSING"
    if not flags["orientation_buckets_complete"]:
        return "HOLD_ORIENTATION_BUCKET_GAP"
    if not flags["order_stable_or_residual_declared"]:
        return "HOLD_HIDDEN_RACE_CONDITION"
    if not flags["baseline_gate_closed"]:
        return "HOLD_BASELINE"
    if not flags["resource_envelope_ok"]:
        return "HOLD_RESOURCE_LIMIT"
    return "ADMIT_SAFETY_CONDITION"


def case(case_id: str, description: str, overrides: dict[str, bool]) -> dict[str, Any]:
    flags = {name: True for name in CHECKS}
    flags.update(overrides)
    decision = classify(flags)
    failed = [name for name in CHECKS if not flags[name]]
    item = {
        "case_id": case_id,
        "description": description,
        "checks": flags,
        "failed_checks": failed,
        "decision": decision,
        "promotable": decision == "ADMIT_SAFETY_CONDITION",
    }
    item["case_hash"] = hash_obj({k: v for k, v in item.items() if k != "case_hash"})
    return item


def build_registry() -> dict[str, Any]:
    cases = [
        case(
            "safe_fixture_all_gates_closed",
            "Positive control: replay, roots, residuals, ordering, chirality, orientation, and baseline all close.",
            {},
        ),
        case(
            "replay_surface_matches_but_decoder_fails",
            "A route that looks semantically correct but cannot byte-replay must reject before any higher claim.",
            {"exact_replay": False},
        ),
        case(
            "root_mismatch_after_parallel_update",
            "A hidden race can surface as a recomputed root mismatch after two update lanes touch the same frame.",
            {"root_recomputes": False},
        ),
        case(
            "fixture_labeled_canonical",
            "A noncanonical fixture cannot borrow canonical enwik9 authority.",
            {"provenance_truthful": False},
        ),
        case(
            "clock_participates_in_hash",
            "Wall-clock time may timestamp a receipt, but must not participate in the replay root.",
            {"timestamp_metadata_only": False},
        ),
        case(
            "axis_free_similarity",
            "Same-looking surfaces cannot promote without a declared causal axis.",
            {"axis_declared": False},
        ),
        case(
            "long_predictive_delta_without_checkpoint",
            "A byte route with no nearby root checkpoint remains unbounded even if the delta is small.",
            {"bounded_witness": False},
        ),
        case(
            "hold_dependency_rescued_by_later_edge",
            "A later admitted edge cannot rescue an upstream HOLD dependency.",
            {"dependency_admitted": False},
        ),
        case(
            "buffalo_surface_collision_no_residual",
            "Same surface token with different role/order must carry residuals or stay HOLD.",
            {"residual_declared": False},
        ),
        case(
            "observer_chart_promoted_to_global_truth",
            "A lawful local chart becomes unsafe for promotion when treated as global codec truth.",
            {"local_chart_not_globalized": False},
        ),
        case(
            "chirality_flip_without_adapter",
            "Handedness changes need an explicit adapter and residual lane.",
            {"chirality_adapter_declared": False},
        ),
        case(
            "orientation_360_missing_bucket",
            "A 360 sharing root requires committed orientation buckets; gaps stay HOLD.",
            {"orientation_buckets_complete": False},
        ),
        case(
            "unsafe_joke_literalized_as_callable",
            "A joke source can be metadata, but unsafe procedural expansion must quarantine.",
            {"safe_literalization": False},
        ),
        case(
            "noncommuting_route_without_residual",
            "Two admitted edges that reach the same surface with different roots expose a hidden race unless residualized.",
            {"order_stable_or_residual_declared": False},
        ),
        case(
            "baseline_debt_unpaid",
            "A replay-valid route still cannot promote as Hutter candidate while baseline comparison is open.",
            {"baseline_gate_closed": False},
        ),
        case(
            "prize_resource_envelope_exceeded",
            "A route that needs too much time, RAM, temporary disk, cores, or GPU cannot promote under prize rules.",
            {"resource_envelope_ok": False},
        ),
    ]
    return {
        "schema": "godel_gauntlet_safety_condition_registry_v1",
        "source_refs": [source_ref(path) for path in SOURCE_REFS],
        "claim_boundary": (
            "Godel Gauntlet safety-condition probe only. It converts known Hutter, "
            "logogram, observer-chart, and joke-source guardrails into promotion "
            "tests. It does not change codec behavior or claim benchmark gain."
        ),
        "canonical_statement": (
            "A candidate route promotes only when replay, roots, provenance, axes, "
            "bounds, residuals, dependency status, timestamp policy, baseline, "
            "chirality, orientation buckets, literalization safety, chart scope, "
            "order stability, and the hard prize resource envelope all close."
        ),
        "gauntlet_equation": {
            "safety_gate": "Safe(c)=product(check_i(c))",
            "promotion": "Promote(c)=1[Safe(c)] else REJECT/HOLD/QUARANTINE by first failed invariant",
            "race_bridge": "order_stable_or_residual_declared imports RaceHold results from the route-order gauntlet",
        },
        "checks": CHECKS,
        "resource_envelope": RESOURCE_ENVELOPE,
        "cases": cases,
        "safety_root": hash_obj([item["case_hash"] for item in cases]),
        "aggregates": {
            "case_count": len(cases),
            "admit_count": sum(1 for item in cases if item["decision"].startswith("ADMIT")),
            "hold_count": sum(1 for item in cases if item["decision"].startswith("HOLD")),
            "reject_count": sum(1 for item in cases if item["decision"].startswith("REJECT")),
            "quarantine_count": sum(1 for item in cases if item["decision"].startswith("QUARANTINE")),
        },
    }


def build_receipt(registry: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "godel_gauntlet_safety_condition_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "registry": rel(REGISTRY),
        "registry_hash": hash_obj(registry),
        "safety_root": registry["safety_root"],
        "aggregates": registry["aggregates"],
        "decision": "ADMIT_GODEL_GAUNTLET_SAFETY_DIAGNOSTIC",
        "claim_boundary": registry["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(registry: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# Godel Gauntlet Safety Condition Probe",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        f"Safety root: `{registry['safety_root']}`",
        "",
        registry["claim_boundary"],
        "",
        "## Canonical Statement",
        "",
        registry["canonical_statement"],
        "",
        "## Equation",
        "",
    ]
    for key, value in registry["gauntlet_equation"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            "",
            "## Cases",
            "",
            "| Case | Failed checks | Decision |",
            "|---|---|---|",
        ]
    )
    for item in registry["cases"]:
        failed = ", ".join(item["failed_checks"]) if item["failed_checks"] else "none"
        lines.append(f"| `{item['case_id']}` | {failed} | `{item['decision']}` |")
    lines.extend(
        [
            "",
            "## Resource Envelope",
            "",
            f"- Source: `{registry['resource_envelope']['source']}`",
            f"- Max hours formula: `{registry['resource_envelope']['max_hours_formula']}`",
            f"- Max RAM GB: `{registry['resource_envelope']['max_ram_gb']}`",
            f"- Max temp HDD GB: `{registry['resource_envelope']['max_temp_hdd_gb']}`",
            f"- GPU allowed: `{registry['resource_envelope']['gpu_allowed']}`",
            "",
            "## Source Refs",
            "",
        ]
    )
    for source in registry["source_refs"]:
        lines.append(f"- `{source['path']}` exists: `{source['exists']}`")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tiddler(receipt: dict[str, Any]) -> None:
    text = f"""created: 20260509000000000
modified: 20260509000000000
tags: ResearchStack Hutter Compression GodelGauntlet SafetyCondition Receipt
title: Godel Gauntlet Safety Condition Probe
type: text/vnd.tiddlywiki

! Godel Gauntlet Safety Condition Probe

Durable runner:

```
4-Infrastructure/shim/godel_gauntlet_safety_condition_probe.py
```

Receipt:

```
{rel(RECEIPT)}
```

Receipt hash:

```
{receipt['receipt_hash']}
```

Safety root:

```
{receipt['safety_root']}
```

!! Doctrine

A candidate route promotes only when replay, roots, provenance, axes, bounds,
residuals, dependency status, timestamp policy, baseline, chirality, orientation
buckets, literalization safety, chart scope, order stability, and the hard
Hutter Prize resource envelope all close.

```
Safe(c)=product(check_i(c))
Promote(c)=1[Safe(c)] else REJECT/HOLD/QUARANTINE by first failed invariant
```

!! Links

* [[Godel Gauntlet Race Condition Probe]]
* [[Hutter Multidimensional Causal Chain]]
* [[Observer Chart Projection Guardrail]]
* [[Joke Source Literalization Guardrail]]
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
                "safety_root": registry["safety_root"],
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
