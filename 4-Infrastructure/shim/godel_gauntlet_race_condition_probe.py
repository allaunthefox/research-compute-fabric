#!/usr/bin/env python3
"""Gödel Gauntlet race-condition probe for Hutter causal axes.

The multidimensional causal graph admits individual edges, but that is not
enough to prove that concurrent routes commute. This probe applies the local
Gödel Gauntlet rule: no promotion from surface plausibility. Edge compositions
must be order-stable, receipt-stable, and residual-declared before they can be
used as shared Hutter route structure.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "godel_gauntlet_race_condition"
REGISTRY = OUT_DIR / "godel_gauntlet_race_condition_registry.json"
RECEIPT = OUT_DIR / "godel_gauntlet_race_condition_receipt.json"
SUMMARY = OUT_DIR / "godel_gauntlet_race_condition.md"
TIDDLER = REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers" / "Godel Gauntlet Race Condition Probe.tid"

MULTI_CAUSAL_REGISTRY = (
    REPO
    / "shared-data"
    / "data"
    / "hutter_multidimensional_causal_chain"
    / "hutter_multidimensional_causal_chain_registry.json"
)
MULTI_CAUSAL_RECEIPT = (
    REPO
    / "shared-data"
    / "data"
    / "hutter_multidimensional_causal_chain"
    / "hutter_multidimensional_causal_chain_receipt.json"
)
FOUNDATION_COMPILER = REPO / "4-Infrastructure" / "shim" / "foundation_forward_equation_compiler.py"

AXIS_PRIORITY = {
    "provenance": 0,
    "corpus_offset": 1,
    "byte_neighbor": 2,
    "semantic_class": 3,
    "chirality": 4,
    "orientation_360_share": 5,
    "codec_torsion": 6,
    "observer_chart": 7,
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


def load_multidimensional_graph() -> dict[str, Any]:
    if not MULTI_CAUSAL_REGISTRY.exists():
        raise FileNotFoundError(f"missing source registry: {MULTI_CAUSAL_REGISTRY}")
    return json.loads(MULTI_CAUSAL_REGISTRY.read_text(encoding="utf-8"))


def edge_by_id(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {edge["edge_id"]: edge for edge in graph["edges"]}


def transition_digest(state: dict[str, Any], edge: dict[str, Any]) -> dict[str, Any]:
    """Apply an edge as a typed transition over a compact route state."""
    axes = list(state["axes"])
    axes.append(edge["axis"])
    route = list(state["route"])
    route.append(edge["edge_id"])
    source_target = list(state["source_target"])
    source_target.append([edge["source"], edge["target"]])
    return {
        "start": state["start"],
        "end": edge["target"],
        "axes": axes,
        "route": route,
        "source_target": source_target,
        "residuals": list(state["residuals"]) + ([] if edge["bounded"] else ["unbounded_edge"]),
        "axis_priority_trace": [AXIS_PRIORITY.get(axis, 99) for axis in axes],
        "route_root": hash_obj(
            {
                "start": state["start"],
                "end": edge["target"],
                "axes": axes,
                "route": route,
                "source_target": source_target,
                "edge_hash": edge["edge_hash"],
            }
        ),
    }


def run_route(start: str, edge_ids: list[str], edges: dict[str, dict[str, Any]]) -> dict[str, Any]:
    state = {
        "start": start,
        "end": start,
        "axes": [],
        "route": [],
        "source_target": [],
        "residuals": [],
        "axis_priority_trace": [],
        "route_root": hash_obj({"start": start, "empty": True}),
    }
    for edge_id in edge_ids:
        state = transition_digest(state, edges[edge_id])
    return state


def axis_order_valid(state: dict[str, Any]) -> bool:
    trace = state["axis_priority_trace"]
    return trace == sorted(trace)


def make_test(
    graph: dict[str, Any],
    test_id: str,
    description: str,
    start: str,
    route_a: list[str],
    route_b: list[str],
    expected_same_root: bool,
    residual_declared: bool,
) -> dict[str, Any]:
    edges = edge_by_id(graph)
    state_a = run_route(start, route_a, edges)
    state_b = run_route(start, route_b, edges)
    same_root = state_a["route_root"] == state_b["route_root"]
    same_end = state_a["end"] == state_b["end"]
    order_a_valid = axis_order_valid(state_a)
    order_b_valid = axis_order_valid(state_b)
    all_edges_admitted = all(edges[edge_id]["decision"] == "ADMIT_CAUSAL_EDGE" for edge_id in set(route_a + route_b))
    exposes_race = all_edges_admitted and same_end and same_root != expected_same_root
    hidden_race = all_edges_admitted and same_end and not same_root and not residual_declared

    if hidden_race:
        decision = "HOLD_HIDDEN_RACE_CONDITION"
    elif exposes_race:
        decision = "HOLD_RACE_EXPECTATION_MISMATCH"
    elif not all_edges_admitted:
        decision = "HOLD_DEPENDENCY_NOT_ADMITTED"
    elif not order_a_valid or not order_b_valid:
        decision = "HOLD_AXIS_ORDER_NONCANONICAL"
    elif same_root == expected_same_root:
        decision = "ADMIT_ORDER_STABLE_ROUTE" if same_root else "ADMIT_DECLARED_NONCOMMUTING_ROUTE"
    else:
        decision = "HOLD_GAUNTLET_UNSETTLED"

    item = {
        "test_id": test_id,
        "description": description,
        "start": start,
        "route_a": route_a,
        "route_b": route_b,
        "expected_same_root": expected_same_root,
        "residual_declared": residual_declared,
        "same_end": same_end,
        "same_root": same_root,
        "route_a_order_valid": order_a_valid,
        "route_b_order_valid": order_b_valid,
        "all_edges_admitted": all_edges_admitted,
        "hidden_race": hidden_race,
        "state_a": state_a,
        "state_b": state_b,
        "decision": decision,
    }
    item["test_hash"] = hash_obj({k: v for k, v in item.items() if k != "test_hash"})
    return item


def build_registry() -> dict[str, Any]:
    graph = load_multidimensional_graph()
    tests = [
        make_test(
            graph,
            "godel_commute_provenance_then_semantic",
            "Provenance before semantic reuse should be canonical and stable.",
            "x0",
            ["e_provenance_0_4", "e_semantic_0_4"],
            ["e_provenance_0_4", "e_semantic_0_4"],
            expected_same_root=True,
            residual_declared=True,
        ),
        make_test(
            graph,
            "godel_race_semantic_vs_provenance",
            "Semantic reuse before provenance can look plausible but changes the route root.",
            "x0",
            ["e_semantic_0_4", "e_provenance_0_4"],
            ["e_provenance_0_4", "e_semantic_0_4"],
            expected_same_root=True,
            residual_declared=False,
        ),
        make_test(
            graph,
            "godel_race_chirality_vs_byte",
            "Byte-neighbor and chirality edges share a target; wrong order hides whether handedness was checked before replay.",
            "x0",
            ["e_chirality_0_1", "e_byte_0_1"],
            ["e_byte_0_1", "e_chirality_0_1"],
            expected_same_root=True,
            residual_declared=False,
        ),
        make_test(
            graph,
            "godel_declared_chirality_flip_noncommuting",
            "A chirality flip followed by torsion pressure is declared noncommuting because handedness changes the adapter lane.",
            "x1",
            ["e_chirality_flip_1_2", "e_torsion_1_3"],
            ["e_torsion_1_3", "e_chirality_flip_1_2"],
            expected_same_root=False,
            residual_declared=True,
        ),
        make_test(
            graph,
            "godel_360_share_vs_provenance",
            "A 360 share root without provenance-first ordering can race against canonical input trust.",
            "x0",
            ["e_360_share_0_4", "e_provenance_0_4"],
            ["e_provenance_0_4", "e_360_share_0_4"],
            expected_same_root=True,
            residual_declared=False,
        ),
        make_test(
            graph,
            "godel_dependency_hold_propagates",
            "An already-HOLD unbounded predictive edge cannot be rescued by a later admitted share edge.",
            "x3",
            ["e_unbounded_predictive", "e_360_share_0_4"],
            ["e_360_share_0_4", "e_unbounded_predictive"],
            expected_same_root=False,
            residual_declared=True,
        ),
    ]
    return {
        "schema": "godel_gauntlet_race_condition_registry_v1",
        "source_refs": [source_ref(path) for path in [MULTI_CAUSAL_REGISTRY, MULTI_CAUSAL_RECEIPT, FOUNDATION_COMPILER]],
        "claim_boundary": (
            "Gödel Gauntlet race-condition probe only. It exposes order-sensitive "
            "route compositions in Hutter causal-axis diagnostics; it does not "
            "change the codec, prove concurrency safety, or claim benchmark gain."
        ),
        "canonical_statement": (
            "Individually admitted causal edges do not promote as a shared route "
            "until their compositions commute, or their noncommutation is explicitly "
            "declared as residual."
        ),
        "gauntlet_equation": {
            "edge": "e_{i,j}^{axis}: x_i -> x_j",
            "composition": "R(a;b) == R(b;a) or residual_noncommuting(a,b) declared",
            "race_gate": "RaceHold(a,b)=1[same_end] * 1[root_mismatch] * 1[residual_missing]",
            "promotion": "Promote(route)=1[all_edges_admitted] * 1[order_canonical] * 1[not RaceHold]",
        },
        "axis_priority": AXIS_PRIORITY,
        "tests": tests,
        "gauntlet_root": hash_obj([test["test_hash"] for test in tests]),
        "aggregates": {
            "test_count": len(tests),
            "admit_count": sum(1 for test in tests if test["decision"].startswith("ADMIT")),
            "hold_count": sum(1 for test in tests if test["decision"].startswith("HOLD")),
            "hidden_race_count": sum(1 for test in tests if test["decision"] == "HOLD_HIDDEN_RACE_CONDITION"),
            "order_noncanonical_count": sum(1 for test in tests if test["decision"] == "HOLD_AXIS_ORDER_NONCANONICAL"),
        },
    }


def build_receipt(registry: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "godel_gauntlet_race_condition_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "registry": rel(REGISTRY),
        "registry_hash": hash_obj(registry),
        "gauntlet_root": registry["gauntlet_root"],
        "aggregates": registry["aggregates"],
        "decision": "ADMIT_GODEL_GAUNTLET_RACE_DIAGNOSTIC",
        "claim_boundary": registry["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(registry: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# Godel Gauntlet Race Condition Probe",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`",
        f"Gauntlet root: `{registry['gauntlet_root']}`",
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
            "## Tests",
            "",
            "| Test | Route A | Route B | Same end | Same root | Decision |",
            "|---|---|---|---:|---:|---|",
        ]
    )
    for test in registry["tests"]:
        lines.append(
            f"| `{test['test_id']}` | `{' -> '.join(test['route_a'])}` | "
            f"`{' -> '.join(test['route_b'])}` | {test['same_end']} | "
            f"{test['same_root']} | `{test['decision']}` |"
        )
    lines.extend(["", "## Source Refs", ""])
    for source in registry["source_refs"]:
        lines.append(f"- `{source['path']}` exists: `{source['exists']}`")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tiddler(receipt: dict[str, Any]) -> None:
    text = f"""created: 20260509000000000
modified: 20260509000000000
tags: ResearchStack Hutter Compression GodelGauntlet RaceCondition Receipt
title: Godel Gauntlet Race Condition Probe
type: text/vnd.tiddlywiki

! Godel Gauntlet Race Condition Probe

Durable runner:

```
4-Infrastructure/shim/godel_gauntlet_race_condition_probe.py
```

Receipt:

```
{rel(RECEIPT)}
```

Receipt hash:

```
{receipt['receipt_hash']}
```

Gauntlet root:

```
{receipt['gauntlet_root']}
```

!! Doctrine

Individually admitted causal edges do not promote as shared Hutter route
structure until their compositions commute, or their noncommutation is declared
as residual.

```
R(a;b) == R(b;a) or residual_noncommuting(a,b) declared
RaceHold(a,b)=1[same_end] * 1[root_mismatch] * 1[residual_missing]
```

This is the race-condition version of the Gödel Gauntlet: same output surface
is not proof of lawful operator order.

!! Links

* [[Hutter Multidimensional Causal Chain]]
* [[Hutter Differential Frame Chain]]
* [[Hutter Frame Invariant Root]]
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
                "gauntlet_root": registry["gauntlet_root"],
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
