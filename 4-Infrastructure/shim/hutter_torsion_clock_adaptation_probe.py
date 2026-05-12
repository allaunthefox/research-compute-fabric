#!/usr/bin/env python3
"""Adapt torsion-clock witness geometry back into Hutter/logogram research.

The mechanical model says wall-clock time is a shadow and accumulated torsion is
the causal state coordinate. In the Hutter/logogram setting, the analogue is
codec torsion: accumulated byte debt, dictionary debt, receipt overhead,
provenance uncertainty, baseline gap, and route coupling.

This probe does not change the codec. It defines a receipt-state atlas for the
existing Hutter ladder so "near compression" cannot masquerade as finite byte
admission.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "hutter_torsion_clock_adaptation"
REGISTRY = OUT_DIR / "hutter_torsion_clock_adaptation_registry.json"
RECEIPT = OUT_DIR / "hutter_torsion_clock_adaptation_receipt.json"
SUMMARY = OUT_DIR / "hutter_torsion_clock_adaptation.md"
TIDDLER = REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers" / "Hutter Torsion Clock Adaptation.tid"

TORSION_ERGOREGION_THRESHOLD = 1000
TORSION_HORIZON_THRESHOLD = 5000

SOURCE_REFS = [
    REPO / "shared-data" / "data" / "kerr_like_load_witness_geometry" / "kerr_like_load_witness_geometry_receipt.json",
    REPO / "shared-data" / "data" / "asymptotic_closure_horizon" / "asymptotic_closure_horizon_receipt.json",
    REPO / "shared-data" / "data" / "enwiki9_logogram_receipt_aggregation_probe" / "enwiki9_logogram_receipt_aggregation_probe_receipt.json",
    REPO / "shared-data" / "data" / "enwiki9_logogram_dictionary_amortization_probe" / "enwiki9_logogram_dictionary_amortization_probe_receipt.json",
    REPO / "shared-data" / "data" / "enwiki9_logogram_canonical_baseline_probe" / "enwiki9_logogram_canonical_baseline_probe_receipt.json",
    REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers" / "Hutter Prize Compression.tid",
    REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers" / "Merkle Tensegrity Load Equation Harness.tid",
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


def rung(
    *,
    rung_id: str,
    gate: str,
    claim: str,
    replay_fail: bool = False,
    provenance_debt: int = 0,
    packet_debt: int = 0,
    dictionary_debt: int = 0,
    baseline_debt: int = 0,
    receipt_debt: int = 0,
    route_coupling: int = 0,
    finite_byte_pass: bool = False,
) -> dict[str, Any]:
    torsion = (
        provenance_debt
        + packet_debt
        + dictionary_debt
        + baseline_debt
        + receipt_debt
        + route_coupling
        + (TORSION_HORIZON_THRESHOLD if replay_fail else 0)
    )
    if replay_fail:
        decision = "REJECT_REPLAY_HORIZON"
    elif finite_byte_pass and torsion < TORSION_ERGOREGION_THRESHOLD:
        decision = "ADMIT_FINITE_BYTE_CHART"
    elif torsion >= TORSION_HORIZON_THRESHOLD:
        decision = "HOLD_HUTTER_FAILURE_HORIZON"
    elif torsion >= TORSION_ERGOREGION_THRESHOLD:
        decision = "HOLD_HUTTER_ERGOREGION"
    else:
        decision = "HOLD_INCOMPLETE_FINITE_GATE"
    item = {
        "rung_id": rung_id,
        "gate": gate,
        "claim": claim,
        "codec_torsion": torsion,
        "torsion_components": {
            "replay_fail_horizon": TORSION_HORIZON_THRESHOLD if replay_fail else 0,
            "provenance_debt": provenance_debt,
            "packet_debt": packet_debt,
            "dictionary_debt": dictionary_debt,
            "baseline_debt": baseline_debt,
            "receipt_debt": receipt_debt,
            "route_coupling": route_coupling,
        },
        "finite_byte_pass": finite_byte_pass,
        "decision": decision,
    }
    item["rung_hash"] = hash_obj({k: v for k, v in item.items() if k != "rung_hash"})
    return item


def build_registry() -> dict[str, Any]:
    rungs = [
        rung(
            rung_id="v1_replay_core_expands",
            gate="PASS",
            claim="byte replay closes but core expands",
            packet_debt=2400,
            receipt_debt=700,
            finite_byte_pass=False,
        ),
        rung(
            rung_id="v2_core_shrinks_packet_expands",
            gate="PASS_ADD",
            claim="core shrinks but receipt/packet overhead remains active",
            packet_debt=1600,
            receipt_debt=900,
            finite_byte_pass=False,
        ),
        rung(
            rung_id="v3_packet_shrinks_global_holds",
            gate="PASS_ADD_PAUSE_SUBTRACT",
            claim="packet shrink appears; dictionary debt keeps global in HOLD",
            dictionary_debt=1064,
            route_coupling=250,
            finite_byte_pass=False,
        ),
        rung(
            rung_id="v4_fixture_global_shrinks",
            gate="PASS_ADD_PAUSE_SUBTRACT",
            claim="fixture-level global shrink appears; provenance remains noncanonical",
            provenance_debt=1800,
            baseline_debt=1200,
            finite_byte_pass=False,
        ),
        rung(
            rung_id="v5_canonical_slice_baseline",
            gate="PROVENANCE_PASS_ADD_PAUSE_SUBTRACT_BASELINE",
            claim="canonical slice and baseline gate; codec remains frozen",
            provenance_debt=0,
            baseline_debt=2800,
            route_coupling=600,
            finite_byte_pass=False,
        ),
        rung(
            rung_id="future_canonical_baseline_candidate",
            gate="PROVENANCE_PASS_ADD_PAUSE_SUBTRACT_BASELINE",
            claim="target state: canonical replay, global positive, baseline not worse",
            provenance_debt=0,
            packet_debt=0,
            dictionary_debt=0,
            baseline_debt=0,
            receipt_debt=250,
            route_coupling=100,
            finite_byte_pass=True,
        ),
    ]
    return {
        "schema": "hutter_torsion_clock_adaptation_registry_v1",
        "claim_boundary": (
            "Hutter torsion-clock adaptation only. It maps mechanical torsion-clock "
            "witness geometry into codec/accounting state advance. It does not change "
            "the encoder, does not claim Hutter-score competitiveness, and does not "
            "replace canonical byte-count gates."
        ),
        "source_refs": [source_ref(path) for path in SOURCE_REFS],
        "time_substitution": {
            "mechanical_source": "wall-clock time is a shadow; torsion is the causal state coordinate",
            "hutter_adaptation": "elapsed research time is a shadow; codec torsion is accumulated unresolved byte/accounting debt",
            "codec_torsion": "T_H = replay_horizon + provenance_debt + packet_debt + dictionary_debt + baseline_debt + receipt_debt + route_coupling",
            "hash_policy": "generated_at_utc remains metadata_only; codec_torsion participates in registry hash",
        },
        "state_atlas": {
            "safe_chart": "finite replay, counted packet/global bytes, canonical provenance, and baseline gate close",
            "ergoregion": "packet/global improvement is visible, but some static assumption fails: provenance, amortization, or baseline",
            "horizon": "replay/provenance/baseline failure is large enough that the route cannot be certified as a candidate",
            "frame_dragging": "changing dictionary, protocol, or target class while measuring drags neighboring deltas and contaminates attribution",
            "geodesic": "shortest frozen-codec route from fixture evidence to canonical baseline evidence",
        },
        "admissibility_equation": (
            "A_H=1[exact_replay] * 1[canonical_or_fixture_label_truthful] * "
            "1[delta_packet>0] * 1[delta_global>0] * 1[baseline_gate_closed] * "
            "1[T_H < ergoregion_threshold]"
        ),
        "avoid": [
            "counting elapsed wall-clock effort as progress",
            "treating near-zero global delta as finite admission",
            "changing codec and accounting scope in the same receipt",
            "optimizing dictionary from non-target language fixtures before canonical enwik9 failure analysis",
            "using citation or model confidence as a substitute for byte replay",
        ],
        "rungs": rungs,
        "aggregates": {
            "rung_count": len(rungs),
            "admit_count": sum(1 for item in rungs if item["decision"] == "ADMIT_FINITE_BYTE_CHART"),
            "ergoregion_hold_count": sum(1 for item in rungs if item["decision"] == "HOLD_HUTTER_ERGOREGION"),
            "horizon_hold_count": sum(1 for item in rungs if item["decision"] == "HOLD_HUTTER_FAILURE_HORIZON"),
            "reject_count": sum(1 for item in rungs if item["decision"] == "REJECT_REPLAY_HORIZON"),
            "ergoregion_threshold": TORSION_ERGOREGION_THRESHOLD,
            "horizon_threshold": TORSION_HORIZON_THRESHOLD,
        },
    }


def build_receipt(registry: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "hutter_torsion_clock_adaptation_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "registry": rel(REGISTRY),
        "registry_hash": hash_obj(registry),
        "aggregates": registry["aggregates"],
        "decision": "ADMIT_HUTTER_TORSION_CLOCK_ACCOUNTING_DIAGNOSTIC",
        "claim_boundary": registry["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(registry: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# Hutter Torsion-Clock Adaptation",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        "",
        registry["claim_boundary"],
        "",
        "## Time Substitution",
        "",
        f"- Mechanical source: {registry['time_substitution']['mechanical_source']}",
        f"- Hutter adaptation: {registry['time_substitution']['hutter_adaptation']}",
        f"- Codec torsion: `{registry['time_substitution']['codec_torsion']}`",
        f"- Hash policy: `{registry['time_substitution']['hash_policy']}`",
        "",
        "## State Atlas",
        "",
    ]
    for key, value in registry["state_atlas"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            "",
            "## Admissibility",
            "",
            f"`{registry['admissibility_equation']}`",
            "",
            "## Rungs",
            "",
            "| Rung | Gate | Codec torsion | Decision |",
            "|---|---|---:|---|",
        ]
    )
    for item in registry["rungs"]:
        lines.append(f"| `{item['rung_id']}` | `{item['gate']}` | {item['codec_torsion']} | `{item['decision']}` |")
    lines.extend(["", "## Avoid", ""])
    for item in registry["avoid"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Source Refs", ""])
    for source in registry["source_refs"]:
        lines.append(f"- `{source['path']}` exists: `{source['exists']}`")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tiddler(receipt: dict[str, Any]) -> None:
    text = f"""created: 20260509000000000
modified: 20260509000000000
tags: ResearchStack Hutter Compression Receipt TorsionClock
title: Hutter Torsion Clock Adaptation
type: text/vnd.tiddlywiki

! Hutter Torsion Clock Adaptation

Durable runner:

```
4-Infrastructure/shim/hutter_torsion_clock_adaptation_probe.py
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

Elapsed research time is a shadow. Codec torsion is accumulated unresolved byte/accounting debt:

```
T_H = replay_horizon + provenance_debt + packet_debt + dictionary_debt + baseline_debt + receipt_debt + route_coupling
```

Near compression remains HOLD until finite replay, packet/global, provenance, and baseline gates close.

!! Links

* [[Hutter Prize Compression]]
* [[Merkle Tensegrity Load Equation Harness]]
* [[Kerr-Like Load Witness Geometry]]
* [[Asymptotic Closure Horizon]]
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
