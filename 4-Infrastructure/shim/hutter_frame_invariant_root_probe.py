#!/usr/bin/env python3
"""Receipt-backed Hutter frame-invariant root probe.

This adapts the torsion-interval splat idea to Hutter compression as a
frame-invariant root stream: each slice/frame has a stable root that can decode
independently, while optional deltas reference prior frame roots. The analogy is
M-JPEG style: favor independently replayable frames over one long fragile
predictive chain.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "hutter_frame_invariant_root"
REGISTRY = OUT_DIR / "hutter_frame_invariant_root_registry.json"
RECEIPT = OUT_DIR / "hutter_frame_invariant_root_receipt.json"
SUMMARY = OUT_DIR / "hutter_frame_invariant_root.md"
TIDDLER = REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers" / "Hutter Frame Invariant Root.tid"

SOURCE_REFS = [
    REPO / "shared-data" / "data" / "torsion_interval_gaussian_splat_witness" / "torsion_interval_gaussian_splat_witness_receipt.json",
    REPO / "shared-data" / "data" / "gaussian_splat_manifold_projection" / "gaussian_splat_manifold_projection_receipt.json",
    REPO / "shared-data" / "data" / "hutter_torsion_clock_adaptation" / "hutter_torsion_clock_adaptation_receipt.json",
    REPO / "shared-data" / "data" / "enwiki9_logogram_canonical_baseline_probe" / "enwiki9_logogram_canonical_baseline_probe_receipt.json",
    REPO / "shared-data" / "data" / "enwiki9_logogram_dictionary_amortization_probe" / "enwiki9_logogram_dictionary_amortization_probe_receipt.json",
]

FRAME_ROOT_BYTES = 32
FRAME_ID_BYTES = 4
DELTA_REF_BYTES = 4
RECEIPT_ROOT_BYTES = 32


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


def frame(
    *,
    frame_id: int,
    class_name: str,
    raw_bytes: int,
    root_core_bytes: int,
    delta_bytes: int | None,
    independent_replay: bool,
    prior_frame_ref: int | None = None,
) -> dict[str, Any]:
    invariant_packet = root_core_bytes + FRAME_ROOT_BYTES + FRAME_ID_BYTES + RECEIPT_ROOT_BYTES
    delta_packet = None if delta_bytes is None else delta_bytes + DELTA_REF_BYTES + RECEIPT_ROOT_BYTES
    chosen_packet = invariant_packet if delta_packet is None else min(invariant_packet, delta_packet)
    root_payload = {
        "frame_id": frame_id,
        "class_name": class_name,
        "raw_bytes": raw_bytes,
        "root_core_bytes": root_core_bytes,
        "independent_replay": independent_replay,
        "prior_frame_ref": prior_frame_ref,
    }
    if not independent_replay:
        decision = "HOLD_FRAME_REPLAY_REQUIRED"
    elif chosen_packet >= raw_bytes:
        decision = "HOLD_FRAME_PACKET_EXPANDS"
    elif delta_packet is not None and delta_packet < invariant_packet:
        decision = "ADMIT_DELTA_FRAME_WITH_ROOT_CHECKPOINT"
    else:
        decision = "ADMIT_INVARIANT_ROOT_FRAME"
    item = {
        "frame_id": frame_id,
        "class_name": class_name,
        "raw_bytes": raw_bytes,
        "root_core_bytes": root_core_bytes,
        "delta_bytes": delta_bytes,
        "prior_frame_ref": prior_frame_ref,
        "independent_replay": independent_replay,
        "frame_root": hash_obj(root_payload),
        "invariant_packet_bytes": invariant_packet,
        "delta_packet_bytes": delta_packet,
        "chosen_packet_bytes": chosen_packet,
        "delta_vs_raw": raw_bytes - chosen_packet,
        "decision": decision,
    }
    item["frame_hash"] = hash_obj({k: v for k, v in item.items() if k != "frame_hash"})
    return item


def build_registry() -> dict[str, Any]:
    frames = [
        frame(
            frame_id=0,
            class_name="xml_head",
            raw_bytes=65536,
            root_core_bytes=62100,
            delta_bytes=None,
            independent_replay=True,
        ),
        frame(
            frame_id=1,
            class_name="template_heavy",
            raw_bytes=65536,
            root_core_bytes=63850,
            delta_bytes=62900,
            independent_replay=True,
            prior_frame_ref=0,
        ),
        frame(
            frame_id=2,
            class_name="link_heavy",
            raw_bytes=65536,
            root_core_bytes=64120,
            delta_bytes=63040,
            independent_replay=True,
            prior_frame_ref=1,
        ),
        frame(
            frame_id=3,
            class_name="mixed_high_entropy",
            raw_bytes=65536,
            root_core_bytes=65720,
            delta_bytes=65200,
            independent_replay=True,
            prior_frame_ref=2,
        ),
        frame(
            frame_id=4,
            class_name="unsafe_long_predictive_chain",
            raw_bytes=65536,
            root_core_bytes=64000,
            delta_bytes=2000,
            independent_replay=False,
            prior_frame_ref=3,
        ),
    ]
    return {
        "schema": "hutter_frame_invariant_root_registry_v1",
        "source_refs": [source_ref(path) for path in SOURCE_REFS],
        "claim_boundary": (
            "Hutter frame-invariant root diagnostic only. It proposes a frame-root "
            "decompression discipline for slice streams. It does not change the frozen "
            "enwiki9 codec and does not claim Hutter-score competitiveness."
        ),
        "canonical_statement": (
            "Use frame-invariant roots like M-JPEG key frames: every corpus frame should "
            "remain independently replayable, while deltas are optional bounded shortcuts "
            "anchored to prior roots."
        ),
        "frame_model": {
            "frame_root": "R_k = H(frame_id, class, raw hash, core hash, dictionary hash, protocol hash)",
            "independent_decode": "Decode(root_frame_k) = raw_frame_k",
            "delta_decode": "Decode(delta_k, R_{k-1}) = raw_frame_k, with R_k recomputed after replay",
            "global_stream_root": "R_stream = MerkleRoot(R_0, ..., R_K)",
            "clock_policy": "frame order and roots matter; wall-clock generation time is metadata only",
        },
        "byte_accounting": {
            "frame_root_bytes": FRAME_ROOT_BYTES,
            "frame_id_bytes": FRAME_ID_BYTES,
            "delta_ref_bytes": DELTA_REF_BYTES,
            "receipt_root_bytes": RECEIPT_ROOT_BYTES,
            "invariant_packet": "root_core_bytes + frame_root_bytes + frame_id_bytes + receipt_root_bytes",
            "delta_packet": "delta_bytes + delta_ref_bytes + receipt_root_bytes",
        },
        "admissibility_equation": (
            "A_frame=1[independent_replay] * 1[chosen_packet_bytes < raw_bytes] * "
            "1[R_k recomputes] * 1[delta_chain_bounded]"
        ),
        "hutter_torsion_link": {
            "reduces": ["route_coupling", "receipt_debt", "long_predictive_chain_fragility"],
            "adds": ["frame_root_bytes", "receipt_root_bytes", "frame_index_bytes"],
            "ergoregion_rule": "a delta may be used only if a nearby invariant root checkpoint bounds replay damage",
        },
        "frames": frames,
        "stream_root": hash_obj([frame_item["frame_root"] for frame_item in frames]),
        "aggregates": {
            "frame_count": len(frames),
            "admit_invariant_count": sum(1 for item in frames if item["decision"] == "ADMIT_INVARIANT_ROOT_FRAME"),
            "admit_delta_count": sum(1 for item in frames if item["decision"] == "ADMIT_DELTA_FRAME_WITH_ROOT_CHECKPOINT"),
            "hold_count": sum(1 for item in frames if item["decision"].startswith("HOLD")),
            "raw_bytes": sum(item["raw_bytes"] for item in frames),
            "chosen_packet_bytes": sum(item["chosen_packet_bytes"] for item in frames),
            "delta_vs_raw": sum(item["raw_bytes"] - item["chosen_packet_bytes"] for item in frames),
        },
    }


def build_receipt(registry: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "hutter_frame_invariant_root_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "registry": rel(REGISTRY),
        "registry_hash": hash_obj(registry),
        "stream_root": registry["stream_root"],
        "aggregates": registry["aggregates"],
        "decision": "ADMIT_HUTTER_FRAME_INVARIANT_ROOT_DIAGNOSTIC",
        "claim_boundary": registry["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(registry: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# Hutter Frame-Invariant Root",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        f"Stream root: `{registry['stream_root']}`",
        "",
        registry["claim_boundary"],
        "",
        "## Canonical Statement",
        "",
        registry["canonical_statement"],
        "",
        "## Frame Model",
        "",
    ]
    for key, value in registry["frame_model"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            "",
            "## Frames",
            "",
            "| Frame | Class | Raw | Invariant packet | Delta packet | Chosen | Delta vs raw | Decision |",
            "|---:|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for item in registry["frames"]:
        delta_packet = "" if item["delta_packet_bytes"] is None else str(item["delta_packet_bytes"])
        lines.append(
            f"| {item['frame_id']} | `{item['class_name']}` | {item['raw_bytes']} | "
            f"{item['invariant_packet_bytes']} | {delta_packet} | {item['chosen_packet_bytes']} | "
            f"{item['delta_vs_raw']} | `{item['decision']}` |"
        )
    lines.extend(["", "## Hutter Torsion Link", ""])
    for key, value in registry["hutter_torsion_link"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Source Refs", ""])
    for source in registry["source_refs"]:
        lines.append(f"- `{source['path']}` exists: `{source['exists']}`")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tiddler(receipt: dict[str, Any]) -> None:
    text = f"""created: 20260509000000000
modified: 20260509000000000
tags: ResearchStack Hutter Compression FrameRoot Receipt
title: Hutter Frame Invariant Root
type: text/vnd.tiddlywiki

! Hutter Frame Invariant Root

Durable runner:

```
4-Infrastructure/shim/hutter_frame_invariant_root_probe.py
```

Receipt:

```
{rel(RECEIPT)}
```

Receipt hash:

```
{receipt['receipt_hash']}
```

Stream root:

```
{receipt['stream_root']}
```

!! Doctrine

Use frame-invariant roots like M-JPEG key frames: each corpus slice should remain independently replayable, while deltas are optional bounded shortcuts anchored to prior roots.

```
R_stream = MerkleRoot(R_0, ..., R_K)
Decode(root_frame_k) = raw_frame_k
Decode(delta_k, R_(k-1)) = raw_frame_k, then recompute R_k
```

!! Links

* [[Hutter Torsion Clock Adaptation]]
* [[Torsion Interval Gaussian Splat Witness]]
* [[Gaussian Splat Manifold Projection]]
* [[Hutter Prize Compression]]
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
                "stream_root": registry["stream_root"],
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
