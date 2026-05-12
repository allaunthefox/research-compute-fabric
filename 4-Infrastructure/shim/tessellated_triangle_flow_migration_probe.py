#!/usr/bin/env python3
"""Tessellated triangle flow-map probe for route prediction guardrails.

This records a bounded triangular map with a simple flow-control equation. Bird
migration is used as an intuitive route-prediction fixture: seasonal direction,
wind assist, stopover pressure, obstacle cost, and route memory can steer motion
between neighboring cells. The fixture is a routing/prediction pattern only; it
does not claim ecological forecasting authority.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "shared-data" / "data" / "tessellated_triangle_flow_migration"
REGISTRY = OUT_DIR / "tessellated_triangle_flow_migration_registry.json"
RECEIPT = OUT_DIR / "tessellated_triangle_flow_migration_receipt.json"
SUMMARY = OUT_DIR / "tessellated_triangle_flow_migration.md"
TIDDLER = REPO / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers" / "Tessellated Triangle Flow Migration.tid"

SOURCE_REFS = [
    REPO / "shared-data" / "data" / "hutter_prize_next_roadmap" / "hutter_prize_next_roadmap_receipt.json",
    REPO / "shared-data" / "data" / "hutter_multidimensional_causal_chain" / "hutter_multidimensional_causal_chain_receipt.json",
    REPO / "shared-data" / "data" / "gaussian_splat_manifold_projection" / "gaussian_splat_manifold_projection_receipt.json",
    REPO / "shared-data" / "data" / "torsion_interval_gaussian_splat_witness" / "torsion_interval_gaussian_splat_witness_receipt.json",
    REPO / "shared-data" / "data" / "collatz_couch_route_pressure" / "collatz_couch_route_pressure_receipt.json",
    REPO / "shared-data" / "data" / "underverse_variant_accounting" / "underverse_variant_accounting_receipt.json",
    REPO / "0-Core-Formalism" / "lean" / "Semantics" / "Semantics" / "TriangleManifold.lean",
]

FLOW_WEIGHTS = {
    "seasonal_heading": 3,
    "wind_assist": 2,
    "stopover_memory": 2,
    "obstacle_cost": -3,
    "novelty_cost": -1,
}

ADMIT_THRESHOLD = 4
HOLD_THRESHOLD = 1
METABOLIC_HOLD_DECISION = "HOLD_INVERSE_FERMAT_FAMM_UNDERVERSE"


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_obj(obj: Any) -> str:
    return sha256_bytes(stable_json(obj).encode("utf-8"))


def merkle_root(leaves: list[str]) -> str:
    if not leaves:
        return sha256_bytes(b"")
    level = leaves[:]
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [sha256_bytes((level[index] + level[index + 1]).encode("ascii")) for index in range(0, len(level), 2)]
    return level[0]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def file_hash(path: Path) -> str | None:
    return sha256_bytes(path.read_bytes()) if path.exists() else None


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def source_ref(path: Path) -> dict[str, Any]:
    receipt = read_json(path)
    return {
        "path": rel(path),
        "exists": path.exists(),
        "sha256": file_hash(path),
        "receipt_hash": receipt.get("receipt_hash") if isinstance(receipt, dict) else None,
        "decision": receipt.get("decision") if isinstance(receipt, dict) else None,
    }


def triangle(cell_id: str, row: int, col: int, orientation: str, label: str) -> dict[str, Any]:
    item = {
        "cell_id": cell_id,
        "row": row,
        "col": col,
        "orientation": orientation,
        "label": label,
        "vertices": [
            [col, row],
            [col + 1, row],
            [col + (0 if orientation == "down" else 1), row + 1],
        ],
    }
    item["cell_hash"] = hash_obj(item)
    return item


def flow_score(features: dict[str, int]) -> int:
    return sum(FLOW_WEIGHTS[name] * value for name, value in features.items())


def route(
    *,
    route_id: str,
    source: str,
    target: str,
    chart: str,
    features: dict[str, int],
    bounded: bool,
    provenance_declared: bool,
    prediction_scope_declared: bool,
    global_truth_claim: bool = False,
) -> dict[str, Any]:
    score = flow_score(features)
    if global_truth_claim:
        decision = "HOLD_TRIANGLE_FLOW_GLOBALIZED"
    elif not bounded:
        decision = "REJECT_UNBOUNDED_TRIANGLE_FLOW"
    elif not provenance_declared:
        decision = "HOLD_FLOW_PROVENANCE"
    elif not prediction_scope_declared:
        decision = "HOLD_MIGRATION_PREDICTION_SCOPE"
    elif score >= ADMIT_THRESHOLD:
        decision = "ADMIT_TRIANGLE_FLOW_HINT"
    elif score >= HOLD_THRESHOLD:
        decision = "HOLD_TRIANGLE_FLOW_WEAK_HINT"
    else:
        decision = "HOLD_FLOW_BOUNDARY"
    item = {
        "route_id": route_id,
        "source": source,
        "target": target,
        "chart": chart,
        "features": features,
        "flow_score": score,
        "bounded": bounded,
        "provenance_declared": provenance_declared,
        "prediction_scope_declared": prediction_scope_declared,
        "global_truth_claim": global_truth_claim,
        "decision": decision,
    }
    item["route_hash"] = hash_obj({k: v for k, v in item.items() if k != "route_hash"})
    return item


def metabolic_route(
    *,
    route_id: str,
    source: str,
    target: str,
    chart: str,
    outcome_value: int,
    path_cost: int,
    metabolic_cost: int,
    obstacle_cost: int,
    residual_cost: int,
    bounded: bool,
    provenance_declared: bool,
    outcome_receipt: bool,
) -> dict[str, Any]:
    fitness = outcome_value - path_cost - metabolic_cost - obstacle_cost - residual_cost
    if not bounded:
        decision = "REJECT_UNBOUNDED_METABOLIC_ROUTE"
    elif not provenance_declared:
        decision = "HOLD_FLOW_PROVENANCE"
    elif not outcome_receipt:
        decision = METABOLIC_HOLD_DECISION
    else:
        decision = "HOLD_INVERSE_FERMAT_FAMM_ADAPTER"
    item = {
        "route_id": route_id,
        "source": source,
        "target": target,
        "chart": chart,
        "outcome_value": outcome_value,
        "path_cost": path_cost,
        "metabolic_cost": metabolic_cost,
        "obstacle_cost": obstacle_cost,
        "residual_cost": residual_cost,
        "fitness": fitness,
        "bounded": bounded,
        "provenance_declared": provenance_declared,
        "outcome_receipt": outcome_receipt,
        "underverse_variant": "U_INVERSE_FERMAT_FAMM",
        "decision": decision,
    }
    item["route_hash"] = hash_obj({k: v for k, v in item.items() if k != "route_hash"})
    return item


def build_registry() -> dict[str, Any]:
    cells = [
        triangle("T00", 0, 0, "up", "wintering_origin_or_frame_root"),
        triangle("T01", 0, 1, "down", "coastal_corridor_or_xml_head"),
        triangle("T10", 1, 0, "down", "river_corridor_or_link_heavy"),
        triangle("T11", 1, 1, "up", "stopover_node_or_template_heavy"),
        triangle("T20", 2, 0, "up", "barrier_cell_or_ref_heavy"),
        triangle("T21", 2, 1, "down", "destination_basin_or_prose_heavy"),
    ]
    routes = [
        route(
            route_id="seasonal_coastal_route",
            source="T00",
            target="T01",
            chart="bird_migration_fixture",
            features={
                "seasonal_heading": 1,
                "wind_assist": 1,
                "stopover_memory": 1,
                "obstacle_cost": 0,
                "novelty_cost": 0,
            },
            bounded=True,
            provenance_declared=True,
            prediction_scope_declared=True,
        ),
        route(
            route_id="river_stopover_route",
            source="T10",
            target="T11",
            chart="bird_migration_fixture",
            features={
                "seasonal_heading": 1,
                "wind_assist": 0,
                "stopover_memory": 1,
                "obstacle_cost": 0,
                "novelty_cost": 1,
            },
            bounded=True,
            provenance_declared=True,
            prediction_scope_declared=True,
        ),
        route(
            route_id="storm_barrier_route",
            source="T11",
            target="T20",
            chart="bird_migration_fixture",
            features={
                "seasonal_heading": 1,
                "wind_assist": -1,
                "stopover_memory": 0,
                "obstacle_cost": 1,
                "novelty_cost": 1,
            },
            bounded=True,
            provenance_declared=True,
            prediction_scope_declared=True,
        ),
        route(
            route_id="hutter_frame_class_route",
            source="T01",
            target="T11",
            chart="hutter_frame_fixture",
            features={
                "seasonal_heading": 1,
                "wind_assist": 0,
                "stopover_memory": 1,
                "obstacle_cost": 0,
                "novelty_cost": 0,
            },
            bounded=True,
            provenance_declared=True,
            prediction_scope_declared=True,
        ),
        route(
            route_id="unbounded_prediction_claim",
            source="T00",
            target="T21",
            chart="bird_migration_fixture",
            features={
                "seasonal_heading": 1,
                "wind_assist": 1,
                "stopover_memory": 1,
                "obstacle_cost": 0,
                "novelty_cost": 0,
            },
            bounded=False,
            provenance_declared=True,
            prediction_scope_declared=False,
            global_truth_claim=True,
        ),
    ]
    metabolic_routes = [
        metabolic_route(
            route_id="physarum_style_best_food_route",
            source="T00",
            target="T21",
            chart="slime_mold_metabolic_fixture",
            outcome_value=12,
            path_cost=3,
            metabolic_cost=2,
            obstacle_cost=1,
            residual_cost=2,
            bounded=True,
            provenance_declared=True,
            outcome_receipt=False,
        ),
        metabolic_route(
            route_id="hutter_best_outcome_route_pressure",
            source="T01",
            target="T11",
            chart="hutter_frame_fixture",
            outcome_value=9,
            path_cost=2,
            metabolic_cost=1,
            obstacle_cost=0,
            residual_cost=3,
            bounded=True,
            provenance_declared=True,
            outcome_receipt=False,
        ),
    ]
    return {
        "schema": "tessellated_triangle_flow_migration_registry_v1",
        "source_refs": [source_ref(path) for path in SOURCE_REFS],
        "claim_boundary": (
            "Tessellated triangle flow-map diagnostic only. Bird migration supplies "
            "a route-prediction pattern fixture over seasonal heading, wind assist, "
            "stopover memory, obstacles, and novelty. Slime-mold metabolic fitness "
            "and inverse-Fermat/FAMM route selection are recorded as Underverse HOLD "
            "lanes. This does not claim ecological forecasting authority, species-level "
            "prediction, metabolic optimization authority, or Hutter compression."
        ),
        "canonical_statement": (
            "A tessellated triangle map bounds the local chart; a flow-control "
            "equation chooses legal neighboring moves; migration-like patterns "
            "stress test directional memory, barriers, and prediction scope. "
            "Slime-mold fitness probes shortest metabolic routes to high-value "
            "outcomes, but remains Underverse until adapter, residual, and outcome "
            "receipts close."
        ),
        "flow_equation": {
            "cell_state": "x_i = triangle_cell(position, orientation, class, receipt)",
            "control": "u_ij = 3*seasonal_heading + 2*wind_assist + 2*stopover_memory - 3*obstacle_cost - novelty_cost",
            "transition": "x_{k+1}=argmax_j u_ij over adjacent tessellated cells, else HOLD",
            "admission": "A=1[bounded and provenance_declared and prediction_scope_declared and not global_truth_claim]",
        },
        "inverse_fermat_famm": {
            "status": "U_under",
            "variant_id": "U_INVERSE_FERMAT_FAMM",
            "meaning": "inverse Fermat route pressure: choose bounded metabolic path to best outcome instead of accepting apparent geometric elegance",
            "fitness": "Phi(route)=outcome_value-path_cost-metabolic_cost-obstacle_cost-residual_cost",
            "promotion_rule": "stay HOLD until domain adapter, residual policy, and outcome receipt are explicit",
        },
        "hutter_mapping": {
            "triangle_cell": "canonical frame/window class",
            "migration_route": "multi-axis causal route across frame classes",
            "seasonal_heading": "expected corpus-phase direction",
            "wind_assist": "baseline/logogram support",
            "stopover_memory": "prior admitted root reuse",
            "obstacle_cost": "packet/global/baseline debt",
            "novelty_cost": "new dictionary or adapter burden",
        },
        "cells": cells,
        "routes": routes,
        "metabolic_routes": metabolic_routes,
        "cells_root": merkle_root([item["cell_hash"] for item in cells]),
        "routes_root": merkle_root([item["route_hash"] for item in routes + metabolic_routes]),
        "aggregates": {
            "cell_count": len(cells),
            "route_count": len(routes) + len(metabolic_routes),
            "flow_route_count": len(routes),
            "metabolic_route_count": len(metabolic_routes),
            "admit_count": sum(1 for item in routes + metabolic_routes if item["decision"].startswith("ADMIT")),
            "hold_count": sum(1 for item in routes + metabolic_routes if item["decision"].startswith("HOLD")),
            "reject_count": sum(1 for item in routes + metabolic_routes if item["decision"].startswith("REJECT")),
            "flow_weights": FLOW_WEIGHTS,
            "admit_threshold": ADMIT_THRESHOLD,
            "hold_threshold": HOLD_THRESHOLD,
        },
    }


def build_receipt(registry: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema": "tessellated_triangle_flow_migration_receipt_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "timestamp_role": "metadata_only",
        "generated_at_utc_included_in_receipt_hash": False,
        "registry": rel(REGISTRY),
        "registry_hash": hash_obj(registry),
        "cells_root": registry["cells_root"],
        "routes_root": registry["routes_root"],
        "aggregates": registry["aggregates"],
        "decision": "ADMIT_TRIANGLE_FLOW_MIGRATION_DIAGNOSTIC",
        "claim_boundary": registry["claim_boundary"],
    }
    receipt["receipt_hash"] = sha256_bytes(
        stable_json({k: v for k, v in receipt.items() if k not in {"receipt_hash", "generated_at_utc"}}).encode("utf-8")
    )
    return receipt


def write_summary(registry: dict[str, Any], receipt: dict[str, Any]) -> None:
    lines = [
        "# Tessellated Triangle Flow Migration",
        "",
        f"Decision: `{receipt['decision']}`  ",
        f"Receipt hash: `{receipt['receipt_hash']}`  ",
        f"Cells root: `{receipt['cells_root']}`  ",
        f"Routes root: `{receipt['routes_root']}`",
        "",
        registry["claim_boundary"],
        "",
        "## Canonical Statement",
        "",
        registry["canonical_statement"],
        "",
        "## Flow Equation",
        "",
    ]
    for key, value in registry["flow_equation"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Inverse Fermat FAMM Underverse", ""])
    for key, value in registry["inverse_fermat_famm"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            "",
            "## Hutter Mapping",
            "",
            "| Triangle/migration term | Hutter role |",
            "|---|---|",
        ]
    )
    for key, value in registry["hutter_mapping"].items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(["", "## Routes", "", "| Route | Chart | Score | Decision |", "|---|---|---:|---|"])
    for item in registry["routes"]:
        lines.append(f"| `{item['route_id']}` | `{item['chart']}` | {item['flow_score']} | `{item['decision']}` |")
    lines.extend(["", "## Metabolic Routes", "", "| Route | Chart | Fitness | Decision |", "|---|---|---:|---|"])
    for item in registry["metabolic_routes"]:
        lines.append(f"| `{item['route_id']}` | `{item['chart']}` | {item['fitness']} | `{item['decision']}` |")
    lines.extend(["", "## Source Refs", ""])
    for source in registry["source_refs"]:
        lines.append(f"- `{source['path']}` exists: `{source['exists']}` decision: `{source['decision']}`")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tiddler(registry: dict[str, Any], receipt: dict[str, Any]) -> None:
    text = f"""created: 20260509000000000
modified: 20260509000000000
tags: ResearchStack Hutter TriangleManifold Flow Migration Receipt
title: Tessellated Triangle Flow Migration
type: text/vnd.tiddlywiki

! Tessellated Triangle Flow Migration

Durable runner:

```
4-Infrastructure/shim/tessellated_triangle_flow_migration_probe.py
```

Receipt:

```
{rel(RECEIPT)}
```

Receipt hash:

```
{receipt['receipt_hash']}
```

Cells root:

```
{receipt['cells_root']}
```

Routes root:

```
{receipt['routes_root']}
```

!! Doctrine

A tessellated triangle map bounds the local chart. A flow-control equation
chooses legal neighboring moves. Bird migration is a prediction-pattern fixture:
direction, wind, memory, barriers, and novelty can route a path, but do not
certify ecological truth or compression gain.

```
u_ij = 3*seasonal_heading + 2*wind_assist + 2*stopover_memory - 3*obstacle_cost - novelty_cost
x_{{k+1}} = argmax_j u_ij over adjacent tessellated cells, else HOLD
```

!! Inverse Fermat FAMM Underverse

Slime-mold style metabolic fitness is recorded as `U_INVERSE_FERMAT_FAMM`.
It can probe shortest routes to best outcomes, but it stays HOLD until the
domain adapter, residual policy, and outcome receipt close.

```
Phi(route)=outcome_value-path_cost-metabolic_cost-obstacle_cost-residual_cost
```

!! Links

* [[Hutter Prize Next Roadmap]]
* [[Hutter Multidimensional Causal Chain]]
* [[Gaussian Splat Manifold Projection]]
* [[Torsion Interval Gaussian Splat Witness]]
* [[Collatz COUCH Route Pressure Probe]]
* [[Underverse Variant Accounting]]
"""
    TIDDLER.write_text(text, encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
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
                "cells_root": receipt["cells_root"],
                "routes_root": receipt["routes_root"],
                "decision": receipt["decision"],
                "aggregates": receipt["aggregates"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
