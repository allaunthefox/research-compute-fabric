#!/usr/bin/env python3
"""Receipt-backed multidimensional causal chain probe for Hutter frames.

The differential frame chain need not be a single linear sequence. A frame root
can participate in multiple typed causal axes: byte-neighbor, semantic class,
provenance, torsion/accounting, chirality, 360 orientation sharing, and
spatial/corpus offset. This probe models a multidimensional causal graph where
each edge has a declared axis and bounded witness.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "hutter_multidimensional_causal_chain"
REGISTRY = OUT_DIR / "hutter_multidimensional_causal_chain_registry.json"
RECEIPT = OUT_DIR / "hutter_multidimensional_causal_chain_receipt.json"
SUMMARY = OUT_DIR / "hutter_multidimensional_causal_chain.md"
TIDDLER = REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers" / "Hutter Multidimensional Causal Chain.tid"

SOURCE_REFS = [
    REPO / "shared-data" / "data" / "hutter_differential_frame_chain" / "hutter_differential_frame_chain_receipt.json",
    REPO / "shared-data" / "data" / "hutter_frame_invariant_root" / "hutter_frame_invariant_root_receipt.json",
    REPO / "shared-data" / "data" / "hutter_torsion_clock_adaptation" / "hutter_torsion_clock_adaptation_receipt.json",
    REPO / "shared-data" / "data" / "observer_chart_projection_guardrail" / "observer_chart_projection_guardrail_receipt.json",
    REPO / "shared-data" / "data" / "logogram_dna_codec" / "logogram_dna_codec_receipt.json",
]

ALLOWED_AXES = [
    "byte_neighbor",
    "semantic_class",
    "provenance",
    "codec_torsion",
    "chirality",
    "orientation_360_share",
    "corpus_offset",
    "observer_chart",
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


def node(
    node_id: str,
    frame_id: int,
    class_name: str,
    offset: int,
    root: str,
    chirality: str,
    orientation_degrees: int,
) -> dict[str, Any]:
    payload = {
        "node_id": node_id,
        "frame_id": frame_id,
        "class_name": class_name,
        "offset": offset,
        "root": root,
        "chirality": chirality,
        "orientation_degrees": orientation_degrees,
    }
    payload["node_hash"] = hash_obj(payload)
    return payload


def edge(
    *,
    edge_id: str,
    source: str,
    target: str,
    axis: str,
    relation: str,
    witness: str,
    bounded: bool,
    reversible: bool,
    root_check: bool,
    global_truth_claim: bool = False,
) -> dict[str, Any]:
    axis_declared = axis in ALLOWED_AXES
    admissible = axis_declared and bounded and root_check and not global_truth_claim
    if not axis_declared:
        decision = "HOLD_AXIS_UNDECLARED"
    elif global_truth_claim:
        decision = "HOLD_LOCAL_EDGE_GLOBALIZED"
    elif not root_check:
        decision = "REJECT_CAUSAL_ROOT_MISMATCH"
    elif not bounded:
        decision = "HOLD_UNBOUNDED_CAUSAL_EDGE"
    else:
        decision = "ADMIT_CAUSAL_EDGE"
    item = {
        "edge_id": edge_id,
        "source": source,
        "target": target,
        "axis": axis,
        "relation": relation,
        "witness": witness,
        "bounded": bounded,
        "reversible": reversible,
        "root_check": root_check,
        "global_truth_claim": global_truth_claim,
        "admissible": admissible,
        "decision": decision,
    }
    item["edge_hash"] = hash_obj({k: v for k, v in item.items() if k != "edge_hash"})
    return item


def build_registry() -> dict[str, Any]:
    nodes = [
        node("x0", 0, "xml_head", 0, hash_obj({"frame": 0, "class": "xml_head"}), "L", 0),
        node("x1", 1, "template_heavy", 65536, hash_obj({"frame": 1, "class": "template_heavy"}), "L", 90),
        node("x2", 2, "link_heavy", 131072, hash_obj({"frame": 2, "class": "link_heavy"}), "R", 180),
        node("x3", 3, "mixed_high_entropy", 196608, hash_obj({"frame": 3, "class": "mixed_high_entropy"}), "R", 270),
        node("x4", 4, "xml_head", 1_000_000, hash_obj({"frame": 4, "class": "xml_head"}), "L", 360),
    ]
    edges = [
        edge(
            edge_id="e_byte_0_1",
            source="x0",
            target="x1",
            axis="byte_neighbor",
            relation="next corpus frame",
            witness="bounded delta dx_0_1",
            bounded=True,
            reversible=False,
            root_check=True,
        ),
        edge(
            edge_id="e_semantic_0_4",
            source="x0",
            target="x4",
            axis="semantic_class",
            relation="same xml-head observer chart across offsets",
            witness="class root and feature signature match",
            bounded=True,
            reversible=True,
            root_check=True,
        ),
        edge(
            edge_id="e_torsion_1_3",
            source="x1",
            target="x3",
            axis="codec_torsion",
            relation="dictionary/receipt pressure increases toward mixed entropy",
            witness="codec torsion debt vector",
            bounded=True,
            reversible=False,
            root_check=True,
        ),
        edge(
            edge_id="e_provenance_0_4",
            source="x0",
            target="x4",
            axis="provenance",
            relation="canonical enwik9 provenance relation",
            witness="source file hash and offset receipt",
            bounded=True,
            reversible=False,
            root_check=True,
        ),
        edge(
            edge_id="e_chirality_0_1",
            source="x0",
            target="x1",
            axis="chirality",
            relation="same handedness preserves frame orientation under template projection",
            witness="chirality bit and phase placement receipt",
            bounded=True,
            reversible=True,
            root_check=True,
        ),
        edge(
            edge_id="e_chirality_flip_1_2",
            source="x1",
            target="x2",
            axis="chirality",
            relation="handedness flip requires explicit adapter and residual declaration",
            witness="chirality flip adapter with declared residual",
            bounded=True,
            reversible=False,
            root_check=True,
        ),
        edge(
            edge_id="e_360_share_0_4",
            source="x0",
            target="x4",
            axis="orientation_360_share",
            relation="same root family shareable across a closed 0-to-360 orientation sweep",
            witness="orientation bucket roots at 0, 90, 180, 270, and 360 degrees",
            bounded=True,
            reversible=True,
            root_check=True,
        ),
        edge(
            edge_id="e_bad_global_chart",
            source="x2",
            target="x3",
            axis="observer_chart",
            relation="local chart incorrectly promoted to global codec truth",
            witness="observer chart without residual",
            bounded=True,
            reversible=False,
            root_check=True,
            global_truth_claim=True,
        ),
        edge(
            edge_id="e_unbounded_predictive",
            source="x3",
            target="x4",
            axis="byte_neighbor",
            relation="long predictive jump without nearby root checkpoint",
            witness="unbounded delta chain",
            bounded=False,
            reversible=False,
            root_check=True,
        ),
    ]
    return {
        "schema": "hutter_multidimensional_causal_chain_registry_v1",
        "source_refs": [source_ref(path) for path in SOURCE_REFS],
        "claim_boundary": (
            "Hutter multidimensional causal chain diagnostic only. It models typed "
            "relations among frame roots; it does not alter codec behavior or assert "
            "actual compression gain."
        ),
        "canonical_statement": (
            "A frame root is a node. A differential or relation is an edge. Causality "
            "is admissible only along a declared axis with bounded witness and root check. "
            "Chirality and 360 orientation sharing are axes, not informal global truth."
        ),
        "causal_equation": {
            "node": "x_i := frame root plus observer/corpus metadata",
            "edge": "e_{i,j}^{axis}: x_i -> x_j",
            "admission": "A(e)=1[axis_declared] * 1[bounded_witness] * 1[root_check] * 1[not globalized_local_chart]",
            "graph": "G_H=(X,E_axis) with byte, semantic, provenance, torsion, chirality, 360 orientation sharing, offset, and observer-chart axes",
        },
        "allowed_axes": ALLOWED_AXES,
        "hutter_role": {
            "multi_axis_prediction": "x can lead to x(i) along different declared axes, not just next byte frame",
            "chirality_axis": "handedness is a routing/admission coordinate when frame orientation or phase matters",
            "orientation_360_share": "closed orientation sweeps can share a frame-invariant root when every bucket is committed",
            "compression_use": "reuse roots/classes/routes when causal edge is admitted",
            "guardrail": "axis-free similarity is HOLD; globalized local chart is HOLD; unbounded predictive jump is HOLD",
        },
        "nodes": nodes,
        "edges": edges,
        "graph_root": hash_obj({"nodes": [item["node_hash"] for item in nodes], "edges": [item["edge_hash"] for item in edges]}),
        "aggregates": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "admitted_edge_count": sum(1 for item in edges if item["decision"] == "ADMIT_CAUSAL_EDGE"),
            "hold_edge_count": sum(1 for item in edges if item["decision"].startswith("HOLD")),
            "reject_edge_count": sum(1 for item in edges if item["decision"].startswith("REJECT")),
        },
    }


def build_receipt(registry: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "hutter_multidimensional_causal_chain_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "registry": rel(REGISTRY),
        "registry_hash": hash_obj(registry),
        "graph_root": registry["graph_root"],
        "aggregates": registry["aggregates"],
        "decision": "ADMIT_HUTTER_MULTIDIMENSIONAL_CAUSAL_CHAIN_DIAGNOSTIC",
        "claim_boundary": registry["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(registry: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# Hutter Multidimensional Causal Chain",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        f"Graph root: `{registry['graph_root']}`",
        "",
        registry["claim_boundary"],
        "",
        "## Canonical Statement",
        "",
        registry["canonical_statement"],
        "",
        "## Causal Equation",
        "",
    ]
    for key, value in registry["causal_equation"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            "",
            "## Edges",
            "",
            "| Edge | Axis | Source | Target | Decision |",
            "|---|---|---|---|---|",
        ]
    )
    for item in registry["edges"]:
        lines.append(f"| `{item['edge_id']}` | `{item['axis']}` | `{item['source']}` | `{item['target']}` | `{item['decision']}` |")
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
tags: ResearchStack Hutter Compression CausalChain Receipt
title: Hutter Multidimensional Causal Chain
type: text/vnd.tiddlywiki

! Hutter Multidimensional Causal Chain

Durable runner:

```
4-Infrastructure/shim/hutter_multidimensional_causal_chain_probe.py
```

Receipt:

```
{rel(RECEIPT)}
```

Receipt hash:

```
{receipt['receipt_hash']}
```

Graph root:

```
{receipt['graph_root']}
```

!! Doctrine

A frame root is a node. A differential or relation is an edge. Causality is admissible only along a declared axis with bounded witness and root check.

```
e_{{i,j}}^axis : x_i -> x_j
A(e)=1[axis_declared] * 1[bounded_witness] * 1[root_check]
```

This lets x lead to x(i) across byte, semantic, provenance, torsion, chirality, 360 orientation-sharing, corpus-offset, and observer-chart dimensions.

Chirality is treated as a real routing/admission axis. The 360 sharing axis is
accepted only as a bounded closed-orientation sweep with committed bucket roots,
not as a free claim that every observer chart shares the same global truth.

!! Links

* [[Hutter Differential Frame Chain]]
* [[Hutter Frame Invariant Root]]
* [[Observer Chart Projection Guardrail]]
* [[Hutter Torsion Clock Adaptation]]
* [[Logogram-DNA Codec Receipt]]
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
                "graph_root": registry["graph_root"],
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
