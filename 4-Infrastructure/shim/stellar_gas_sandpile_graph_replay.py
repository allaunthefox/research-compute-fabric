#!/usr/bin/env python3
"""Graph replay hardening for the stellar-gas sandpile diagnostic.

This converts the existing sandpile metaphor into a reproducible graph
diagnostic.  It is a toppling proxy over sky/redshift cells, not a physical
sandpile simulation and not a claim about stellar gas mechanics.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SANDPILE_JSON = ROOT / "shared-data/data/stellar_gas_observation/stellar_gas_abelian_sandpile_probe.json"
FINE_ZOOM_JSON = ROOT / "shared-data/data/stellar_gas_observation/stellar_gas_sandpile_fine_zoom.json"
OUT_DIR = ROOT / "shared-data/data/stellar_gas_observation"
DOCS_DIR = ROOT / "6-Documentation/docs"
TIDDLER_DIR = ROOT / "6-Documentation/tiddlywiki-local/wiki/tiddlers"

OUT_JSON = OUT_DIR / "stellar_gas_sandpile_graph_replay.json"
RECEIPT_JSON = OUT_DIR / "stellar_gas_sandpile_graph_replay_receipt.json"
DOC_MD = DOCS_DIR / "stellar_gas_sandpile_graph_replay_2026-05-09.md"
TIDDLER = TIDDLER_DIR / "Stellar Gas Sandpile Graph Replay.tid"

Z_BIN_ORDER = {
    "z_000_002": 0,
    "z_002_004": 1,
    "z_004_006": 2,
    "z_006_008": 3,
    "z_008_plus": 4,
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_payload(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_cell(cell: str) -> dict[str, Any]:
    sky_sector, z_bin = cell.split("__", 1)
    ra_sector, hemisphere = sky_sector.split("_", 1)
    return {
        "cell": cell,
        "sky_sector": sky_sector,
        "ra_sector": int(ra_sector.removeprefix("ra")),
        "hemisphere": hemisphere,
        "z_bin": z_bin,
        "z_bin_index": Z_BIN_ORDER[z_bin],
    }


def are_adjacent(a: dict[str, Any], b: dict[str, Any]) -> bool:
    same_z = a["z_bin_index"] == b["z_bin_index"]
    same_ra = a["ra_sector"] == b["ra_sector"]
    same_hemisphere = a["hemisphere"] == b["hemisphere"]
    ra_neighbor = same_z and same_hemisphere and abs(a["ra_sector"] - b["ra_sector"]) == 1
    hemisphere_neighbor = same_z and same_ra and a["hemisphere"] != b["hemisphere"]
    redshift_neighbor = same_ra and same_hemisphere and abs(a["z_bin_index"] - b["z_bin_index"]) == 1
    return ra_neighbor or hemisphere_neighbor or redshift_neighbor


def round9(value: float) -> float:
    return round(value, 9)


def seed_counts(fine_zoom: dict[str, Any]) -> dict[str, int]:
    return {
        cell["cell"]: int(cell["candidate_count"])
        for cell in fine_zoom["candidate_cells"]
    }


def node_rows(sandpile: dict[str, Any], fine_zoom: dict[str, Any]) -> list[dict[str, Any]]:
    counts = seed_counts(fine_zoom)
    index_std = float(sandpile["toppling_index_summary"]["std"]) or 1.0
    rows = []
    for row in sorted(sandpile["top_cells"], key=lambda item: item["cell"]):
        parsed = parse_cell(row["cell"])
        proxy_z = float(row["sandpile"]["toppling_index"]) / index_std
        rows.append(
            {
                **parsed,
                "state": row["sandpile"]["state"],
                "grains": float(row["sandpile"]["grains"]),
                "toppling_pressure": float(row["sandpile"]["toppling_pressure"]),
                "toppling_index": float(row["sandpile"]["toppling_index"]),
                "toppling_index_z_proxy": round9(proxy_z),
                "candidate_object_count": counts.get(row["cell"], 0),
            }
        )
    return rows


def graph_edges(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    edges = []
    for i, left in enumerate(rows):
        for right in rows[i + 1 :]:
            if are_adjacent(left, right):
                edges.append({"source": left["cell"], "target": right["cell"]})
    return edges


def adjacency(nodes: list[str], edges: list[dict[str, str]]) -> dict[str, list[str]]:
    out = {node: [] for node in nodes}
    for edge in edges:
        out[edge["source"]].append(edge["target"])
        out[edge["target"]].append(edge["source"])
    return {node: sorted(neighbors) for node, neighbors in out.items()}


def threshold_and_grain_tables(rows: list[dict[str, Any]], adj: dict[str, list[str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    threshold_table = []
    grain_table = []
    for row in rows:
        cell = row["cell"]
        degree = len(adj[cell])
        threshold = max(1, degree + 1)
        proxy_z = max(0.0, row["toppling_index_z_proxy"])
        initial_grains = max(0, math.ceil(proxy_z * threshold))
        threshold_table.append(
            {
                "cell": cell,
                "degree": degree,
                "toppling_threshold": threshold,
                "threshold_rule": "degree_plus_one_toppling_proxy",
            }
        )
        grain_table.append(
            {
                "cell": cell,
                "initial_grains": initial_grains,
                "grain_rule": "ceil(max(0, toppling_index_z_proxy) * threshold)",
                "toppling_index_z_proxy": row["toppling_index_z_proxy"],
                "seed_object_count": row["candidate_object_count"],
                "source_state": row["state"],
            }
        )
    return threshold_table, grain_table


def replay_one(seed: str, adj: dict[str, list[str]], thresholds: dict[str, int], grains: dict[str, int]) -> dict[str, Any]:
    working = dict(grains)
    topple_count = {cell: 0 for cell in working}
    touched = set()
    q: deque[str] = deque([seed])
    max_steps = max(1, len(working) * 20)
    steps = 0
    while q and steps < max_steps:
        cell = q.popleft()
        if working[cell] < thresholds[cell]:
            continue
        steps += 1
        touched.add(cell)
        topple_count[cell] += 1
        working[cell] -= thresholds[cell]
        for neighbor in adj[cell]:
            working[neighbor] += 1
            if working[neighbor] >= thresholds[neighbor]:
                q.append(neighbor)

    toppled_cells = sorted(cell for cell, count in topple_count.items() if count)
    return {
        "seed_cell": seed,
        "terminated": not q,
        "step_limit": max_steps,
        "topple_events": sum(topple_count.values()),
        "avalanche_size_cells": len(toppled_cells),
        "toppled_cells": toppled_cells,
        "final_seed_grains": working[seed],
    }


def build() -> tuple[dict[str, Any], dict[str, Any]]:
    sandpile = load_json(SANDPILE_JSON)
    fine_zoom = load_json(FINE_ZOOM_JSON)
    rows = node_rows(sandpile, fine_zoom)
    nodes = [row["cell"] for row in rows]
    edges = graph_edges(rows)
    adj = adjacency(nodes, edges)
    threshold_table, grain_table = threshold_and_grain_tables(rows, adj)
    thresholds = {row["cell"]: int(row["toppling_threshold"]) for row in threshold_table}
    grains = {row["cell"]: int(row["initial_grains"]) for row in grain_table}
    seed_cells = sorted(
        row["cell"]
        for row in rows
        if row["state"] == "AVALANCHE_CANDIDATE" and row["candidate_object_count"] > 0
    )
    avalanches = [replay_one(seed, adj, thresholds, grains) for seed in seed_cells]

    canonical_graph = {
        "adjacency_rule": (
            "Edges join same-redshift neighboring RA sectors, same-RA north/south sectors, "
            "or same-sky-sector adjacent redshift bins."
        ),
        "nodes": [
            {
                "cell": row["cell"],
                "ra_sector": row["ra_sector"],
                "hemisphere": row["hemisphere"],
                "z_bin": row["z_bin"],
            }
            for row in rows
        ],
        "edges": edges,
        "threshold_table": threshold_table,
        "initial_grain_table": grain_table,
    }
    graph_hash = sha256_payload(canonical_graph)
    replay_payload = {
        "graph_hash": graph_hash,
        "seed_cells": seed_cells,
        "avalanche_replay": avalanches,
    }
    replay_hash = sha256_payload(replay_payload)
    created = now_iso()
    result = {
        "schema": "stellar_gas_sandpile_graph_replay_v0",
        "created": created,
        "decision": "ADMIT_GRAPH_TOPPLING_PROXY_HOLD_PHYSICAL_SANDPILE_SIMULATION",
        "claim_boundary": (
            "This is a reproducible graph diagnostic and toppling proxy over existing "
            "stellar-gas evidence cells. It is not a physical sandpile simulation, "
            "not a stellar-gas mechanism proof, and not a cosmology fit."
        ),
        "sources": {
            "sandpile_probe": str(SANDPILE_JSON.relative_to(ROOT)),
            "fine_zoom_examples": str(FINE_ZOOM_JSON.relative_to(ROOT)),
        },
        "source_hashes": {
            "sandpile_probe_sha256": sha256_file(SANDPILE_JSON),
            "fine_zoom_examples_sha256": sha256_file(FINE_ZOOM_JSON),
        },
        "seed_evidence": {
            "avalanche_cell_count": len(seed_cells),
            "candidate_object_count": int(fine_zoom["rows_in_candidate_cells"]),
            "candidate_counts_by_cell": seed_counts(fine_zoom),
        },
        "adjacency_rule": canonical_graph["adjacency_rule"],
        "graph_hash": graph_hash,
        "replay_hash": replay_hash,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": rows,
        "edges": edges,
        "adjacency": adj,
        "toppling_threshold_table": threshold_table,
        "initial_grain_table": grain_table,
        "avalanche_sizes": [
            {
                "seed_cell": row["seed_cell"],
                "avalanche_size_cells": row["avalanche_size_cells"],
                "topple_events": row["topple_events"],
                "terminated": row["terminated"],
            }
            for row in avalanches
        ],
        "avalanche_replay": avalanches,
        "holds": [
            "HOLD_PHYSICAL_SANDPILE_SIMULATION",
            "HOLD_STELLAR_GAS_MECHANISM_PROOF",
            "HOLD_DIRECT_STELLAR_MASS",
            "HOLD_DIRECT_GAS_DENSITY_INFERENCE",
            "HOLD_COSMOLOGY_FIT",
        ],
    }
    receipt = {
        "receipt_type": "stellar_gas_sandpile_graph_replay_receipt",
        "created": created,
        "decision": result["decision"],
        "graph_hash": graph_hash,
        "replay_hash": replay_hash,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "seed_avalanche_cell_count": len(seed_cells),
        "seed_candidate_object_count": int(fine_zoom["rows_in_candidate_cells"]),
        "avalanche_sizes": result["avalanche_sizes"],
        "validated_outputs": [
            str(OUT_JSON.relative_to(ROOT)),
            str(RECEIPT_JSON.relative_to(ROOT)),
            str(DOC_MD.relative_to(ROOT)),
            str(TIDDLER.relative_to(ROOT)),
        ],
    }
    return result, receipt


def write_docs(result: dict[str, Any], receipt: dict[str, Any]) -> None:
    threshold_lines = "\n".join(
        f"| `{row['cell']}` | {row['degree']} | {row['toppling_threshold']} |"
        for row in result["toppling_threshold_table"]
    )
    grain_lines = "\n".join(
        f"| `{row['cell']}` | {row['initial_grains']} | {row['toppling_index_z_proxy']} | {row['seed_object_count']} |"
        for row in result["initial_grain_table"]
    )
    avalanche_lines = "\n".join(
        f"| `{row['seed_cell']}` | {row['avalanche_size_cells']} | {row['topple_events']} | `{row['terminated']}` |"
        for row in result["avalanche_sizes"]
    )
    holds = "\n".join(f"- `{hold}`" for hold in result["holds"])

    DOC_MD.write_text(
        f"""# Stellar Gas Sandpile Graph Replay

Status: `GRAPH_TOPPLING_PROXY`

Decision: `{result['decision']}`

This hardening pass turns the sandpile metaphor into a reproducible graph
diagnostic. Nodes are sky/redshift cells. Edges are defined by sky-sector
neighbors plus adjacent redshift bins. Grain and toppling values are diagnostic
proxies derived from the existing cell-level toppling index.

Claim boundary: this is not a physical sandpile simulation, not a stellar-gas
mechanism proof, not direct stellar mass, not gas density inference, and not a
cosmology fit.

## Replay Receipt

```json
{json.dumps(receipt, indent=2, sort_keys=True)}
```

## Seed Evidence

```text
avalanche cells:      {result['seed_evidence']['avalanche_cell_count']}
candidate objects:    {result['seed_evidence']['candidate_object_count']}
graph nodes:          {result['node_count']}
graph edges:          {result['edge_count']}
graph hash:           {result['graph_hash']}
replay hash:          {result['replay_hash']}
```

## Toppling Threshold Table

| cell | degree | threshold |
| --- | ---: | ---: |
{threshold_lines}

## Initial Grain Table

| cell | initial grains | index z proxy | seed objects |
| --- | ---: | ---: | ---: |
{grain_lines}

## Avalanche Sizes

| seed cell | size cells | topple events | terminated |
| --- | ---: | ---: | --- |
{avalanche_lines}

## Holds

{holds}
""",
        encoding="utf-8",
    )

    TIDDLER.write_text(
        f"""title: Stellar Gas Sandpile Graph Replay
tags: StellarGasObservation SemanticMassNumbers Sandpile GraphReplay Receipts
type: text/vnd.tiddlywiki

Status: <<tag GRAPH_TOPPLING_PROXY>>

Decision: `{result['decision']}`

This tiddler records the graph/replay hardening of the stellar-gas sandpile
diagnostic. It is a toppling proxy over evidence cells, not a physical sandpile
simulation or mechanism proof.

```
avalanche cells:   {result['seed_evidence']['avalanche_cell_count']}
candidate objects: {result['seed_evidence']['candidate_object_count']}
graph nodes:       {result['node_count']}
graph edges:       {result['edge_count']}
graph hash:        {result['graph_hash']}
replay hash:       {result['replay_hash']}
```

!! Toppling Threshold Table

|cell | degree | threshold |
|---|---:|---:|
{threshold_lines}

!! Initial Grain Table

|cell | initial grains | index z proxy | seed objects |
|---|---:|---:|---:|
{grain_lines}

!! Avalanche Sizes

|seed cell | size cells | topple events | terminated |
|---|---:|---:|---|
{avalanche_lines}

!! Boundary

Diagnostic/toppling proxy only. Holds: {", ".join(result["holds"])}.
""",
        encoding="utf-8",
    )


def main() -> None:
    result, receipt = build()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    TIDDLER_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    RECEIPT_JSON.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_docs(result, receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
