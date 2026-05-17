#!/usr/bin/env python3
"""Receipt-backed guardrail for observer-bound chart projections.

Some joke sources are dangerous because they encode unsafe procedural advice.
Other jokes are useful because they are visibly local observer charts. This
probe captures the safe case: the periodic table "as seen by an organic
chemist" is not global chemistry truth, but it is a lawful relevance projection
for a particular observer and domain.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "observer_chart_projection_guardrail"
REGISTRY = OUT_DIR / "observer_chart_projection_guardrail_registry.json"
RECEIPT = OUT_DIR / "observer_chart_projection_guardrail_receipt.json"
SUMMARY = OUT_DIR / "observer_chart_projection_guardrail.md"
TIDDLER = REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers" / "Observer Chart Projection Guardrail.tid"

SOURCE_REFS = [
    REPO / "shared-data" / "data" / "joke_source_literalization_guardrail" / "joke_source_literalization_guardrail_receipt.json",
    REPO / "shared-data" / "data" / "kerr_like_load_witness_geometry" / "kerr_like_load_witness_geometry_receipt.json",
    REPO / "shared-data" / "data" / "hutter_torsion_clock_adaptation" / "hutter_torsion_clock_adaptation_receipt.json",
    REPO / "6-Documentation" / "docs" / "specs" / "OMINDIRECTION_LOGOGRAM_DESIGN_AND_COMPILER.md",
    REPO / "6-Documentation" / "docs" / "specs" / "GCCL_ENCODING_CONTRACT.md",
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


def projection(
    *,
    projection_id: str,
    observer: str,
    source_object: str,
    projected_chart: str,
    domain_scope_declared: bool,
    global_truth_claim: bool,
    actionable_unsafe_payload: bool,
    invariant_preserved: bool,
    residual_declared: bool,
) -> dict[str, Any]:
    lawful_projection = (
        domain_scope_declared
        and not global_truth_claim
        and not actionable_unsafe_payload
        and invariant_preserved
        and residual_declared
    )
    if actionable_unsafe_payload:
        decision = "QUARANTINE_UNSAFE_LITERAL_PAYLOAD"
    elif global_truth_claim:
        decision = "HOLD_LOCAL_CHART_GLOBALIZED"
    elif lawful_projection:
        decision = "ADMIT_OBSERVER_CHART"
    else:
        decision = "HOLD_SCOPE_OR_RESIDUAL_MISSING"
    item = {
        "projection_id": projection_id,
        "observer": observer,
        "source_object": source_object,
        "projected_chart": projected_chart,
        "domain_scope_declared": domain_scope_declared,
        "global_truth_claim": global_truth_claim,
        "actionable_unsafe_payload": actionable_unsafe_payload,
        "invariant_preserved": invariant_preserved,
        "residual_declared": residual_declared,
        "lawful_projection": lawful_projection,
        "decision": decision,
    }
    item["projection_hash"] = hash_obj({k: v for k, v in item.items() if k != "projection_hash"})
    return item


def build_registry() -> dict[str, Any]:
    projections = [
        projection(
            projection_id="organic_chemist_periodic_table_meme",
            observer="organic chemist",
            source_object="periodic table full chemical manifold",
            projected_chart="organic relevance manifold centered on carbon and common functional-group elements",
            domain_scope_declared=True,
            global_truth_claim=False,
            actionable_unsafe_payload=False,
            invariant_preserved=True,
            residual_declared=True,
        ),
        projection(
            projection_id="mechanic_load_path_view",
            observer="mechanical safety witness",
            source_object="physical part full material/process manifold",
            projected_chart="load-path admissibility chart with torsion-clock and residual risk",
            domain_scope_declared=True,
            global_truth_claim=False,
            actionable_unsafe_payload=False,
            invariant_preserved=True,
            residual_declared=True,
        ),
        projection(
            projection_id="hutter_codec_torsion_view",
            observer="compression researcher",
            source_object="corpus and codec development history",
            projected_chart="codec torsion chart over replay, provenance, packet, dictionary, baseline, and receipt debt",
            domain_scope_declared=True,
            global_truth_claim=False,
            actionable_unsafe_payload=False,
            invariant_preserved=True,
            residual_declared=True,
        ),
        projection(
            projection_id="local_chart_mistaken_for_global_truth",
            observer="over-promoted expert chart",
            source_object="whole domain",
            projected_chart="observer-biased local relevance map",
            domain_scope_declared=False,
            global_truth_claim=True,
            actionable_unsafe_payload=False,
            invariant_preserved=False,
            residual_declared=False,
        ),
    ]
    return {
        "schema": "observer_chart_projection_guardrail_registry_v1",
        "source_prompt": {
            "id": "user_supplied_organic_chemist_periodic_table_meme",
            "role": "source_prompt",
            "status": "user_supplied_image_prompt",
            "description": (
                "A joke periodic-table projection through organic chemistry salience. "
                "It is safe because it is visibly a local observer chart, not general "
                "chemistry truth or operational hazardous advice."
            ),
        },
        "source_refs": [source_ref(path) for path in SOURCE_REFS],
        "claim_boundary": (
            "Observer chart projection guardrail only. A local chart may be admitted "
            "when observer, scope, residual, and preserved invariant are declared. "
            "A local chart is HOLD if promoted to global truth and QUARANTINE if it "
            "expands into unsafe instructions."
        ),
        "canonical_statement": (
            "Expertise is a lawful distortion. Danger begins when a local chart is "
            "mistaken for the whole manifold."
        ),
        "projection_equation": "pi_observer(Omega) = local_chart + declared_residual + preserved_invariant",
        "admissibility_equation": (
            "A_chart=1[observer_declared] * 1[domain_scope_declared] * "
            "1[not global_truth_claim] * 1[not unsafe_payload] * "
            "1[invariant_preserved] * 1[residual_declared]"
        ),
        "encoding_rule": {
            "observer_chart_channel": "ADMIT scoped chart and observer role",
            "global_truth_channel": "HOLD if local projection is promoted as universal truth",
            "unsafe_payload_channel": "QUARANTINE if chart expands into unsafe procedure",
            "hutter_channel": "encode chart as route prior only; do not let observer bias rewrite canonical byte gates",
        },
        "projections": projections,
        "aggregates": {
            "projection_count": len(projections),
            "admit_observer_chart_count": sum(1 for item in projections if item["decision"] == "ADMIT_OBSERVER_CHART"),
            "hold_count": sum(1 for item in projections if item["decision"].startswith("HOLD")),
            "quarantine_count": sum(1 for item in projections if item["decision"].startswith("QUARANTINE")),
        },
    }


def build_receipt(registry: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "observer_chart_projection_guardrail_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "registry": rel(REGISTRY),
        "registry_hash": hash_obj(registry),
        "aggregates": registry["aggregates"],
        "decision": "ADMIT_OBSERVER_CHART_PROJECTION_GUARDRAIL",
        "claim_boundary": registry["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(registry: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# Observer Chart Projection Guardrail",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        registry["claim_boundary"],
        "",
        "## Canonical Statement",
        "",
        registry["canonical_statement"],
        "",
        "## Equations",
        "",
        f"- Projection: `{registry['projection_equation']}`",
        f"- Admit: `{registry['admissibility_equation']}`",
        "",
        "## Encoding Rules",
        "",
    ]
    for key, value in registry["encoding_rule"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            "",
            "## Projections",
            "",
            "| Projection | Observer | Decision |",
            "|---|---|---|",
        ]
    )
    for item in registry["projections"]:
        lines.append(f"| `{item['projection_id']}` | {item['observer']} | `{item['decision']}` |")
    lines.extend(["", "## Source Refs", ""])
    for source in registry["source_refs"]:
        lines.append(f"- `{source['path']}` exists: `{source['exists']}`")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tiddler(receipt: dict[str, Any]) -> None:
    text = f"""created: 20260509000000000
modified: 20260509000000000
tags: ResearchStack Encoding Guardrail ObserverChart Receipt
title: Observer Chart Projection Guardrail
type: text/vnd.tiddlywiki

! Observer Chart Projection Guardrail

Durable runner:

```
4-Infrastructure/shim/observer_chart_projection_guardrail_probe.py
```

Receipt:

```
{rel(RECEIPT)}
```

Receipt hash:

```
{receipt['receipt_hash']}
```

!! Doctrine

Expertise is a lawful distortion. Danger begins when a local chart is mistaken for the whole manifold.

```
observer chart channel -> ADMIT if scoped
global truth channel   -> HOLD if a local projection is universalized
unsafe payload channel -> QUARANTINE if it expands into unsafe procedure
```

!! Links

* [[Joke Source Literalization Guardrail]]
* [[Kerr-Like Load Witness Geometry]]
* [[Hutter Torsion Clock Adaptation]]
* [[Omindirection Logogram Contract]]
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
