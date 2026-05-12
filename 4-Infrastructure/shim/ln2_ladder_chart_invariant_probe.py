#!/usr/bin/env python3
"""ln(2) ladder-chart invariant probe.

This fixture records a small, exact example of the ladder model: one invariant
object, ln(2), observed through several lawful charts.  It also records the
projection guardrails: infinite sum/integral exchange and endpoint convergence
must be justified, and symbolic/rhythmic shadows are not proof by themselves.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "ln2_ladder_chart_invariant"
REGISTRY = OUT_DIR / "ln2_ladder_chart_invariant_registry.json"
RECEIPT = OUT_DIR / "ln2_ladder_chart_invariant_receipt.json"
SUMMARY = OUT_DIR / "ln2_ladder_chart_invariant.md"
TIDDLER = REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers" / "ln2 Ladder Chart Invariant.tid"

SOURCE_REFS = [
    REPO / "shared-data" / "data" / "observer_chart_projection_guardrail" / "observer_chart_projection_guardrail_receipt.json",
    REPO / "shared-data" / "data" / "collatz_ladder_shadow_filter" / "collatz_ladder_shadow_filter_receipt.json",
    REPO / "shared-data" / "data" / "underverse_variant_accounting" / "underverse_variant_accounting_receipt.json",
    REPO / "6-Documentation" / "docs" / "specs" / "FORWARD_FOUNDATION_EQUATION_COMPILER.md",
]

LN2 = math.log(2.0)
TOL = 1.0e-12


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


def alternating_harmonic(partials: int) -> float:
    return sum(((-1.0) ** n) / (n + 1) for n in range(partials))


def unit_interval_midpoint(samples: int) -> float:
    step = 1.0 / samples
    return sum(step / (1.0 + (i + 0.5) * step) for i in range(samples))


def chart_entry(
    chart_id: str,
    projection: str,
    evaluation: str,
    value: float | None,
    decision: str,
    guardrail: str,
    role: str = "lawful_chart",
) -> dict[str, Any]:
    error = None if value is None else abs(value - LN2)
    entry = {
        "chart_id": chart_id,
        "projection": projection,
        "evaluation": evaluation,
        "value": value,
        "target_ln2": LN2,
        "abs_error": error,
        "decision": decision,
        "guardrail": guardrail,
        "role": role,
    }
    entry["chart_hash"] = hash_obj({k: v for k, v in entry.items() if k != "chart_hash"})
    return entry


def build_registry() -> dict[str, Any]:
    charts = [
        chart_entry(
            "direct_antiderivative",
            "I=int_0^infty 1/(1+e^x) dx",
            "[-log(1+e^-x)]_0^infty = log(2)",
            LN2,
            "ADMIT_EXACT_CHART",
            "improper endpoint limit must be declared",
        ),
        chart_entry(
            "exponential_substitution",
            "u=e^-x maps x in [0,infty) to u in [1,0]",
            "I=int_0^1 1/(1+u) du = log(2)",
            LN2,
            "ADMIT_EXACT_CHART",
            "orientation reversal and dx=-du/u must be paid",
        ),
        chart_entry(
            "geometric_expansion",
            "1/(1+e^x)=e^-x/(1+e^-x)=sum_n (-1)^n e^{-(n+1)x}",
            "termwise integral gives alternating harmonic series",
            alternating_harmonic(100000),
            "ADMIT_LIMIT_CHART_WITH_JUSTIFICATION",
            "exchange of infinite sum and improper integral requires convergence justification",
        ),
        chart_entry(
            "alternating_harmonic_series",
            "sum_{n=0}^infty (-1)^n/(n+1)",
            "Taylor log(1+z) at z=1 gives log(2)",
            alternating_harmonic(100000),
            "ADMIT_LIMIT_CHART_WITH_ENDPOINT_GUARD",
            "endpoint z=1 needs Abel/alternating convergence justification",
        ),
        chart_entry(
            "unit_interval_integral",
            "int_0^1 du/(1+u)",
            "midpoint numerical replay over unit chart",
            unit_interval_midpoint(1_000_000),
            "ADMIT_NUMERIC_REPLAY_CHART",
            "numeric replay is evidence only; exact chart is antiderivative",
        ),
        chart_entry(
            "parametric_derivative_trick",
            "d/da log(1+a) at a=1 or eta/xi-style derivative route",
            "derivative/integral parameter chart returns log(2) when domain is declared",
            LN2,
            "ADMIT_SYMBOLIC_CHART",
            "parameter domain and derivative-exchange law must be declared",
        ),
        chart_entry(
            "music_sheet_shadow",
            "rhythmic or symbolic shadow of the transform ladder",
            "no numeric proof; chart is mnemonic/projection only",
            None,
            "HOLD_SHADOW_ONLY",
            "rhythm-shadow cannot certify the invariant without a lawful adapter",
            role="observer_shadow",
        ),
    ]
    return {
        "schema": "ln2_ladder_chart_invariant_registry_v1",
        "source_refs": [source_ref(path) for path in SOURCE_REFS],
        "invariant": {
            "id": "ln2",
            "canonical_object": "I=int_0^infty 1/(1+e^x) dx = ln(2)",
            "numeric_value": LN2,
            "short_form": "ln 2 is the invariant; the integral, series, substitution, and rhythm are charts.",
        },
        "claim_boundary": (
            "Toy ladder-chart invariant fixture only. The admitted charts show "
            "that one object can survive lawful projection changes. The fixture "
            "does not admit arbitrary symbolic shadows, unjustified exchange of "
            "limits, or rhythm/music notation as proof."
        ),
        "canonical_statement": (
            "A lawful object survives chart changes. A bad derivation loses the "
            "invariant during projection. A good proof states the adapter, pays "
            "the endpoint and limit-exchange costs, and shows every shadow belongs "
            "to the same object."
        ),
        "ladder_mapping": {
            "continuous_field_chart": "improper integral",
            "substitution_chart": "unit interval projection",
            "packetized_recursive_chart": "geometric expansion",
            "parity_torsion_chart": "alternating harmonic signs",
            "invariant_attractor": "ln(2)",
            "observer_shadow": "music/rhythm notation, held until adapter exists",
        },
        "charts": charts,
        "chart_root": hash_obj([chart["chart_hash"] for chart in charts]),
        "aggregates": {
            "chart_count": len(charts),
            "admit_count": sum(1 for chart in charts if chart["decision"].startswith("ADMIT")),
            "hold_count": sum(1 for chart in charts if chart["decision"].startswith("HOLD")),
            "max_numeric_error": max(chart["abs_error"] or 0.0 for chart in charts),
            "missing_source_count": sum(1 for path in SOURCE_REFS if not path.exists()),
        },
        "decision": "ADMIT_LN2_LADDER_CHART_FIXTURE_WITH_SHADOW_HOLD",
    }


def build_receipt(registry: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "ln2_ladder_chart_invariant_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "registry": rel(REGISTRY),
        "registry_hash": hash_obj(registry),
        "chart_root": registry["chart_root"],
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
        "# ln2 Ladder Chart Invariant",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        f"Chart root: `{registry['chart_root']}`",
        "",
        registry["claim_boundary"],
        "",
        "## Invariant",
        "",
        registry["invariant"]["short_form"],
        "",
        "## Canonical Statement",
        "",
        registry["canonical_statement"],
        "",
        "## Charts",
        "",
        "| Chart | Projection | Decision | Guardrail |",
        "|---|---|---|---|",
    ]
    for chart in registry["charts"]:
        lines.append(
            f"| {chart['chart_id']} | {chart['projection']} | "
            f"{chart['decision']} | {chart['guardrail']} |"
        )
    lines.extend(
        [
            "",
            "## Aggregates",
            "",
            f"- Charts: `{registry['aggregates']['chart_count']}`",
            f"- Admitted charts: `{registry['aggregates']['admit_count']}`",
            f"- Held shadows: `{registry['aggregates']['hold_count']}`",
            f"- Max numeric error: `{registry['aggregates']['max_numeric_error']}`",
            f"- Missing sources: `{registry['aggregates']['missing_source_count']}`",
        ]
    )
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tiddler(registry: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "created: 20260509000000000",
        "modified: 20260509000000000",
        "tags: ResearchStack Ladder Invariant Chart Guardrail",
        "title: ln2 Ladder Chart Invariant",
        "type: text/vnd.tiddlywiki",
        "",
        "! ln2 Ladder Chart Invariant",
        "",
        registry["invariant"]["short_form"],
        "",
        f"* Decision: `{receipt['decision']}`",
        f"* Receipt hash: `{receipt['receipt_hash']}`",
        f"* Chart root: `{registry['chart_root']}`",
        f"* Registry: `{rel(REGISTRY)}`",
        f"* Receipt: `{rel(RECEIPT)}`",
        "",
        "!! Rule",
        "",
        "A lawful object survives chart changes; an observer shadow stays HOLD until its adapter and proof obligations are declared.",
        "",
        "```",
        registry["invariant"]["canonical_object"],
        "```",
        "",
        "!! Charts",
        "",
        "| Chart | Decision | Guardrail |",
        "|---|---|---|",
    ]
    for chart in registry["charts"]:
        lines.append(f"| {chart['chart_id']} | {chart['decision']} | {chart['guardrail']} |")
    lines.extend(
        [
            "",
            "!! Links",
            "",
            "* [[Observer Chart Projection Guardrail]]",
            "* [[Collatz Ladder Shadow Filter]]",
            "* [[Underverse Variant Accounting]]",
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
                "chart_root": registry["chart_root"],
                "aggregates": registry["aggregates"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
