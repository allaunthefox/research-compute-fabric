#!/usr/bin/env python3
"""Receipt-backed Hutter differential frame chain probe.

Frame-invariant roots give a discrete differential chain:

    x_i --dx_i--> x_{i+1}

The transition is admissible only if x_i is independently replayable, dx_i
rehydrates the next frame, and the recomputed root equals R_{i+1}. This keeps
differentials as bounded witnesses rather than a fragile predictive chain.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "hutter_differential_frame_chain"
REGISTRY = OUT_DIR / "hutter_differential_frame_chain_registry.json"
RECEIPT = OUT_DIR / "hutter_differential_frame_chain_receipt.json"
SUMMARY = OUT_DIR / "hutter_differential_frame_chain.md"
TIDDLER = REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers" / "Hutter Differential Frame Chain.tid"

SOURCE_REFS = [
    REPO / "shared-data" / "data" / "hutter_frame_invariant_root" / "hutter_frame_invariant_root_receipt.json",
    REPO / "shared-data" / "data" / "hutter_torsion_clock_adaptation" / "hutter_torsion_clock_adaptation_receipt.json",
    REPO / "shared-data" / "data" / "enwiki9_logogram_canonical_baseline_probe" / "enwiki9_logogram_canonical_baseline_probe_receipt.json",
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


def frame_state(frame_id: int, class_name: str, raw_hash: str, core_hash: str, independently_replayable: bool) -> dict[str, Any]:
    payload = {
        "frame_id": frame_id,
        "class_name": class_name,
        "raw_hash": raw_hash,
        "core_hash": core_hash,
        "independently_replayable": independently_replayable,
    }
    payload["root"] = hash_obj(payload)
    return payload


def transition(
    *,
    transition_id: str,
    source: dict[str, Any],
    target: dict[str, Any],
    differential_hash: str,
    rehydrates_target: bool,
    root_recomputes: bool,
    bounded_delta: bool,
) -> dict[str, Any]:
    admissible = (
        source["independently_replayable"]
        and target["independently_replayable"]
        and rehydrates_target
        and root_recomputes
        and bounded_delta
    )
    if not source["independently_replayable"] or not target["independently_replayable"]:
        decision = "HOLD_FRAME_REPLAY_REQUIRED"
    elif not rehydrates_target:
        decision = "REJECT_DIFFERENTIAL_REPLAY"
    elif not root_recomputes:
        decision = "REJECT_ROOT_MISMATCH"
    elif not bounded_delta:
        decision = "HOLD_UNBOUNDED_DIFFERENTIAL"
    else:
        decision = "ADMIT_DIFFERENTIAL_FRAME_EDGE"
    item = {
        "transition_id": transition_id,
        "source_frame": source["frame_id"],
        "target_frame": target["frame_id"],
        "source_root": source["root"],
        "target_root": target["root"],
        "differential_hash": differential_hash,
        "rehydrates_target": rehydrates_target,
        "root_recomputes": root_recomputes,
        "bounded_delta": bounded_delta,
        "admissible": admissible,
        "equation": "x_i + dx_i -> x_{i+1}; H(replay(x_i,dx_i)) == R_{i+1}",
        "decision": decision,
    }
    item["transition_hash"] = hash_obj({k: v for k, v in item.items() if k != "transition_hash"})
    return item


def build_registry() -> dict[str, Any]:
    frames = [
        frame_state(0, "xml_head", "raw_xml_head", "core_xml_head", True),
        frame_state(1, "template_heavy", "raw_template_heavy", "core_template_heavy", True),
        frame_state(2, "link_heavy", "raw_link_heavy", "core_link_heavy", True),
        frame_state(3, "mixed_high_entropy", "raw_mixed_high_entropy", "core_mixed_high_entropy", True),
        frame_state(4, "unsafe_long_predictive_chain", "raw_predictive", "core_predictive", False),
    ]
    transitions = [
        transition(
            transition_id="dx_0_1",
            source=frames[0],
            target=frames[1],
            differential_hash=hash_obj({"from": 0, "to": 1, "opcode": "template_delta"}),
            rehydrates_target=True,
            root_recomputes=True,
            bounded_delta=True,
        ),
        transition(
            transition_id="dx_1_2",
            source=frames[1],
            target=frames[2],
            differential_hash=hash_obj({"from": 1, "to": 2, "opcode": "link_delta"}),
            rehydrates_target=True,
            root_recomputes=True,
            bounded_delta=True,
        ),
        transition(
            transition_id="dx_2_3",
            source=frames[2],
            target=frames[3],
            differential_hash=hash_obj({"from": 2, "to": 3, "opcode": "entropy_patch"}),
            rehydrates_target=True,
            root_recomputes=True,
            bounded_delta=True,
        ),
        transition(
            transition_id="dx_3_4_unbounded",
            source=frames[3],
            target=frames[4],
            differential_hash=hash_obj({"from": 3, "to": 4, "opcode": "fragile_predictive_chain"}),
            rehydrates_target=True,
            root_recomputes=True,
            bounded_delta=False,
        ),
    ]
    return {
        "schema": "hutter_differential_frame_chain_registry_v1",
        "source_refs": [source_ref(path) for path in SOURCE_REFS],
        "claim_boundary": (
            "Hutter differential frame chain diagnostic only. It formalizes x_i to "
            "x_{i+1} transitions over independently replayable frame roots. It does "
            "not change the codec or assert actual corpus compression gains."
        ),
        "canonical_statement": (
            "Frame roots give states; differentials give admissible edges. A delta "
            "is trusted only if it rehydrates the target and recomputes the target root."
        ),
        "chain_equation": {
            "state": "x_i := independently replayable frame with root R_i",
            "edge": "dx_i := bounded differential witness from x_i to x_{i+1}",
            "admission": "A(dx_i)=1[Decode(x_i,dx_i)=x_{i+1}] * 1[H(x_{i+1})=R_{i+1}] * 1[bounded_delta]",
            "global_chain": "x_0 --dx_0--> x_1 --dx_1--> ... --dx_n--> x_{n+1}",
        },
        "hutter_role": {
            "mjpeg_analogy": "root frames are independently replayable key frames; differentials are bounded shortcut edges",
            "torsion_link": "unbounded differentials add route_coupling and predictive-chain torsion",
            "admissible_use": "use dx_i for compression only when root frames remain available as finite checkpoints",
        },
        "frames": frames,
        "transitions": transitions,
        "chain_root": hash_obj([item["transition_hash"] for item in transitions]),
        "aggregates": {
            "frame_count": len(frames),
            "transition_count": len(transitions),
            "admitted_transition_count": sum(1 for item in transitions if item["decision"] == "ADMIT_DIFFERENTIAL_FRAME_EDGE"),
            "hold_transition_count": sum(1 for item in transitions if item["decision"].startswith("HOLD")),
            "reject_transition_count": sum(1 for item in transitions if item["decision"].startswith("REJECT")),
        },
    }


def build_receipt(registry: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "hutter_differential_frame_chain_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "registry": rel(REGISTRY),
        "registry_hash": hash_obj(registry),
        "chain_root": registry["chain_root"],
        "aggregates": registry["aggregates"],
        "decision": "ADMIT_HUTTER_DIFFERENTIAL_FRAME_CHAIN_DIAGNOSTIC",
        "claim_boundary": registry["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(registry: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# Hutter Differential Frame Chain",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        f"Chain root: `{registry['chain_root']}`",
        "",
        registry["claim_boundary"],
        "",
        "## Canonical Statement",
        "",
        registry["canonical_statement"],
        "",
        "## Chain Equation",
        "",
    ]
    for key, value in registry["chain_equation"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            "",
            "## Transitions",
            "",
            "| Transition | Source | Target | Decision |",
            "|---|---:|---:|---|",
        ]
    )
    for item in registry["transitions"]:
        lines.append(f"| `{item['transition_id']}` | {item['source_frame']} | {item['target_frame']} | `{item['decision']}` |")
    lines.extend(["", "## Hutter Role", ""])
    for key, value in registry["hutter_role"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Source Refs", ""])
    for source in registry["source_refs"]:
        lines.append(f"- `{source['path']}` exists: `{source['exists']}`")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tiddler(receipt: dict[str, Any]) -> None:
    text = f"""created: 20260509000000000
modified: 20260509000000000
tags: ResearchStack Hutter Compression DifferentialChain Receipt
title: Hutter Differential Frame Chain
type: text/vnd.tiddlywiki

! Hutter Differential Frame Chain

Durable runner:

```
4-Infrastructure/shim/hutter_differential_frame_chain_probe.py
```

Receipt:

```
{rel(RECEIPT)}
```

Receipt hash:

```
{receipt['receipt_hash']}
```

Chain root:

```
{receipt['chain_root']}
```

!! Doctrine

Frame roots give states. Differentials give admissible edges.

```
x_i --dx_i--> x_(i+1)
A(dx_i)=1[Decode(x_i,dx_i)=x_(i+1)] * 1[H(x_(i+1))=R_(i+1)] * 1[bounded_delta]
```

This lets the codec say x leads to x(i) without losing independently replayable roots.

!! Links

* [[Hutter Frame Invariant Root]]
* [[Hutter Torsion Clock Adaptation]]
* [[Torsion Interval Gaussian Splat Witness]]
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
                "chain_root": registry["chain_root"],
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
