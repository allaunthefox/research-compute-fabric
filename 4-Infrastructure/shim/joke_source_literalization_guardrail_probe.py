#!/usr/bin/env python3
"""Receipt-backed guardrail for joke sources with unsafe literal payloads.

The project can cite a joke as a real source prompt, but that does not mean the
literal payload becomes an executable instruction. This probe adds the missing
guardrail for encoding systems:

* parody/satire may be retained as provenance metadata;
* unsafe domain advice must not be promoted into actionable logograms;
* compression may preserve the existence and role of the source without
  preserving operationally harmful details as callable procedures.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "joke_source_literalization_guardrail"
REGISTRY = OUT_DIR / "joke_source_literalization_guardrail_registry.json"
RECEIPT = OUT_DIR / "joke_source_literalization_guardrail_receipt.json"
SUMMARY = OUT_DIR / "joke_source_literalization_guardrail.md"
TIDDLER = REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers" / "Joke Source Literalization Guardrail.tid"

SOURCE_REFS = [
    REPO / "shared-data" / "data" / "bibliographic_event_horizon" / "bibliographic_event_horizon_receipt.json",
    REPO / "shared-data" / "data" / "asymptotic_closure_horizon" / "asymptotic_closure_horizon_receipt.json",
    REPO / "shared-data" / "data" / "hutter_torsion_clock_adaptation" / "hutter_torsion_clock_adaptation_receipt.json",
    REPO / "6-Documentation" / "docs" / "specs" / "FORWARD_FOUNDATION_EQUATION_COMPILER.md",
    REPO / "6-Documentation" / "docs" / "specs" / "OMINDIRECTION_LOGOGRAM_DESIGN_AND_COMPILER.md",
]

LITERALIZATION_HORIZON = 1000


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


def route(
    *,
    route_id: str,
    payload_role: str,
    domain_risk: int,
    satire_marker: bool,
    actionable_literalization: bool,
    safety_context_present: bool,
    preserves_operational_steps: bool,
) -> dict[str, Any]:
    literalization_risk = (
        domain_risk
        + (350 if satire_marker and actionable_literalization else 0)
        + (350 if preserves_operational_steps else 0)
        + (250 if not safety_context_present else 0)
    )
    horizon = literalization_risk >= LITERALIZATION_HORIZON
    if horizon and actionable_literalization:
        decision = "QUARANTINE_UNSAFE_LITERALIZATION"
    elif horizon:
        decision = "HOLD_SAFETY_CONTEXT_REQUIRED"
    else:
        decision = "ADMIT_METADATA_ONLY"
    item = {
        "route_id": route_id,
        "payload_role": payload_role,
        "domain_risk": domain_risk,
        "satire_marker": satire_marker,
        "actionable_literalization": actionable_literalization,
        "safety_context_present": safety_context_present,
        "preserves_operational_steps": preserves_operational_steps,
        "literalization_risk": literalization_risk,
        "literalization_horizon": horizon,
        "decision": decision,
    }
    item["route_hash"] = hash_obj({k: v for k, v in item.items() if k != "route_hash"})
    return item


def build_registry() -> dict[str, Any]:
    routes = [
        route(
            route_id="joke_post_as_source_prompt",
            payload_role="provenance_metadata",
            domain_risk=200,
            satire_marker=True,
            actionable_literalization=False,
            safety_context_present=True,
            preserves_operational_steps=False,
        ),
        route(
            route_id="unsafe_chemistry_tips_as_logogram",
            payload_role="callable_procedure_candidate",
            domain_risk=650,
            satire_marker=True,
            actionable_literalization=True,
            safety_context_present=False,
            preserves_operational_steps=True,
        ),
        route(
            route_id="unsafe_chemistry_tips_as_training_text",
            payload_role="raw_text_corpus_payload",
            domain_risk=650,
            satire_marker=True,
            actionable_literalization=True,
            safety_context_present=False,
            preserves_operational_steps=True,
        ),
        route(
            route_id="guardrail_summary",
            payload_role="non_operational_safety_summary",
            domain_risk=250,
            satire_marker=True,
            actionable_literalization=False,
            safety_context_present=True,
            preserves_operational_steps=False,
        ),
    ]
    return {
        "schema": "joke_source_literalization_guardrail_registry_v1",
        "source_prompt": {
            "id": "user_supplied_unsafe_chemistry_joke_image",
            "role": "source_prompt",
            "status": "user_supplied_image_prompt",
            "description": (
                "A joke post framed as chemistry advice. Its value is as a guardrail "
                "example: satire can be cited as provenance, but unsafe procedural "
                "content must not be promoted into executable encoding atoms."
            ),
            "verbatim_payload_policy": "do_not_reproduce_operational_steps",
        },
        "source_refs": [source_ref(path) for path in SOURCE_REFS],
        "claim_boundary": (
            "Joke-source literalization guardrail only. The source may be retained as "
            "metadata and cited as an encoding-risk example. Unsafe literal payloads "
            "are not admitted as callable procedures, training targets, or logograms."
        ),
        "encoding_rule": {
            "metadata_channel": "ADMIT source identity, satire role, risk label, and receipt hash",
            "payload_channel": "QUARANTINE operational unsafe steps",
            "summary_channel": "ADMIT non-operational safety summary",
            "logogram_channel": "HOLD or QUARANTINE if a glyph would expand into unsafe procedure",
        },
        "admissibility_equation": (
            "A_joke_payload=1[source_role_metadata] * 1[not actionable_literalization] * "
            "1[not preserves_operational_steps] * 1[safety_context_present]"
        ),
        "hutter_adaptation": {
            "codec_torsion_component": "unsafe_literalization_debt",
            "rule": "a corpus atom that compresses into harmful procedural replay adds horizon-level torsion unless quarantined",
            "safe_compression": "preserve citation and risk class, not executable unsafe procedure",
        },
        "routes": routes,
        "aggregates": {
            "route_count": len(routes),
            "metadata_admit_count": sum(1 for item in routes if item["decision"] == "ADMIT_METADATA_ONLY"),
            "quarantine_count": sum(1 for item in routes if item["decision"] == "QUARANTINE_UNSAFE_LITERALIZATION"),
            "hold_count": sum(1 for item in routes if item["decision"].startswith("HOLD")),
            "literalization_horizon": LITERALIZATION_HORIZON,
        },
    }


def build_receipt(registry: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "joke_source_literalization_guardrail_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "registry": rel(REGISTRY),
        "registry_hash": hash_obj(registry),
        "aggregates": registry["aggregates"],
        "decision": "ADMIT_JOKE_SOURCE_METADATA_QUARANTINE_UNSAFE_LITERALIZATION",
        "claim_boundary": registry["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(registry: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# Joke Source Literalization Guardrail",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        registry["claim_boundary"],
        "",
        "## Rule",
        "",
        f"`{registry['admissibility_equation']}`",
        "",
        "## Encoding Channels",
        "",
    ]
    for key, value in registry["encoding_rule"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            "",
            "## Routes",
            "",
            "| Route | Payload role | Risk | Decision |",
            "|---|---|---:|---|",
        ]
    )
    for item in registry["routes"]:
        lines.append(f"| `{item['route_id']}` | `{item['payload_role']}` | {item['literalization_risk']} | `{item['decision']}` |")
    lines.extend(["", "## Hutter Adaptation", ""])
    for key, value in registry["hutter_adaptation"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Source Refs", ""])
    for source in registry["source_refs"]:
        lines.append(f"- `{source['path']}` exists: `{source['exists']}`")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tiddler(receipt: dict[str, Any]) -> None:
    text = f"""created: 20260509000000000
modified: 20260509000000000
tags: ResearchStack Safety Encoding Guardrail Receipt
title: Joke Source Literalization Guardrail
type: text/vnd.tiddlywiki

! Joke Source Literalization Guardrail

Durable runner:

```
4-Infrastructure/shim/joke_source_literalization_guardrail_probe.py
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

A joke source can be a real citation, but unsafe literal payloads cannot become executable encoding atoms.

```
metadata channel      -> ADMIT
unsafe payload channel -> QUARANTINE
summary channel       -> ADMIT only if non-operational
logogram channel      -> HOLD/QUARANTINE if expansion becomes unsafe procedure
```

!! Hutter Link

Unsafe literalization is codec torsion. If a compressed atom expands into harmful procedural replay, it stays outside the candidate archive unless quarantined or transformed into non-operational metadata.

!! Links

* [[Bibliographic Event Horizon]]
* [[Asymptotic Closure Horizon]]
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
