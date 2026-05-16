#!/usr/bin/env python3
"""NUVMAP Delta-DAG Search Compressor.

Prototype for graph k-coloring.

It combines:
  - FAMM/DSATUR route pressure,
  - delta-edge trace compression,
  - NUVMAP projected state addresses,
  - DAG node merging,
  - scar/nogood cache,
  - exact zero-conflict receipt.

This is not a P-vs-NP claim. It is a route/topology/receipt compressor.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass
class Metrics:
    attempts: int = 0
    backtracks: int = 0
    dag_nodes: int = 0
    dag_edges: int = 0
    cache_hits: int = 0
    nogoods: int = 0
    max_depth: int = 0


def build_adj(n: int, edges: list[list[int]]) -> list[set[int]]:
    adj = [set() for _ in range(n)]
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
    return adj


def domains(colors: list[int], adj: list[set[int]], k: int) -> list[int]:
    masks = []
    full = (1 << k) - 1
    for v, c in enumerate(colors):
        if c >= 0:
            masks.append(1 << c)
            continue
        used = 0
        for nb in adj[v]:
            if colors[nb] >= 0:
                used |= 1 << colors[nb]
        masks.append(full & ~used)
    return masks


def popcount(x: int) -> int:
    return int(x).bit_count()


def canonical_color_relabel(colors: list[int]) -> list[int]:
    mapping = {}
    nxt = 0
    out = []
    for c in colors:
        if c < 0:
            out.append(-1)
        elif c in mapping:
            out.append(mapping[c])
        else:
            mapping[c] = nxt
            out.append(nxt)
            nxt += 1
    return out


def nuvmap_key(
    colors: list[int],
    adj: list[set[int]],
    k: int,
    projection_level: str,
) -> str:
    dm = domains(colors, adj, k)
    uncolored = [v for v, c in enumerate(colors) if c < 0]
    residual_conflicts = sum(1 for u in range(len(adj)) for v in adj[u] if u < v and colors[u] >= 0 and colors[u] == colors[v])

    if projection_level == "exact":
        payload = {
            "level": projection_level,
            "colors": colors,
            "domains": dm,
            "residual_conflicts": residual_conflicts,
        }
    elif projection_level == "symmetry":
        payload = {
            "level": projection_level,
            "colors": canonical_color_relabel(colors),
            "domains": dm,
            "frontier": [
                [v, popcount(dm[v]), len([nb for nb in adj[v] if colors[nb] < 0])]
                for v in uncolored
            ],
            "residual_conflicts": residual_conflicts,
        }
    elif projection_level == "semantic":
        payload = {
            "level": projection_level,
            "uncolored_count": len(uncolored),
            "domain_hist": sorted([popcount(dm[v]) for v in uncolored]),
            "saturation_hist": sorted([k - popcount(dm[v]) for v in uncolored]),
            "residual_conflicts": residual_conflicts,
        }
    else:
        payload = {
            "level": "frontier",
            "uncolored": uncolored,
            "domain_masks": [dm[v] for v in uncolored],
            "frontier_degree": [len([nb for nb in adj[v] if colors[nb] < 0]) for v in uncolored],
            "residual_conflicts": residual_conflicts,
        }

    return sha256_json(payload)


def choose_vertex(colors: list[int], adj: list[set[int]], k: int) -> int | None:
    dm = domains(colors, adj, k)
    best = None
    best_key = None
    for v, c in enumerate(colors):
        if c >= 0:
            continue
        dmask = dm[v]
        dsize = popcount(dmask)
        saturation = k - dsize
        degree = len(adj[v])
        key = (saturation, -dsize, degree, -v)
        if best_key is None or key > best_key:
            best_key = key
            best = v
    return best


def color_order(v: int, colors: list[int], adj: list[set[int]], k: int) -> list[int]:
    dm = domains(colors, adj, k)[v]
    return [c for c in range(k) if dm & (1 << c)]


def zero_conflicts(colors: list[int], edges: list[list[int]]) -> bool:
    return all(colors[u] >= 0 and colors[v] >= 0 and colors[u] != colors[v] for u, v in edges)


def solve_graph_coloring(config: dict[str, Any]) -> dict[str, Any]:
    n = int(config["n"])
    k = int(config.get("k", 3))
    edges = config["edges"]
    projection_level = config.get("projection_level", "frontier")
    max_attempts = int(config.get("max_attempts", 1_000_000))

    adj = build_adj(n, edges)
    colors = [-1] * n
    metrics = Metrics()
    node_seen: dict[str, int] = {}
    nogood: set[str] = set()
    edge_hashes: list[str] = []
    delta_stream: list[dict[str, Any]] = []

    problem_hash = sha256_json({"n": n, "k": k, "edges": sorted([sorted(e) for e in edges])})
    rule_hash = sha256_json({"rule": "FAMM_DSatur_NUVMAP_DeltaDAG_v0.1", "projection_level": projection_level})

    def touch_node(depth: int) -> str:
        key = nuvmap_key(colors, adj, k, projection_level)
        if key in node_seen:
            metrics.cache_hits += 1
        else:
            node_seen[key] = len(node_seen)
        metrics.max_depth = max(metrics.max_depth, depth)
        return key

    def dfs(depth: int) -> bool:
        if metrics.attempts >= max_attempts:
            return False

        parent_key = touch_node(depth)
        if parent_key in nogood:
            metrics.cache_hits += 1
            return False

        v = choose_vertex(colors, adj, k)
        if v is None:
            return zero_conflicts(colors, edges)

        opts = color_order(v, colors, adj, k)
        if not opts:
            nogood.add(parent_key)
            metrics.nogoods += 1
            return False

        for c in opts:
            if metrics.attempts >= max_attempts:
                return False
            metrics.attempts += 1

            colors[v] = c
            child_key = touch_node(depth + 1)

            delta = {
                "op": "assign",
                "vertex": v,
                "color": c,
                "depth": depth,
                "parent": parent_key,
                "child": child_key,
            }
            delta["edge_hash"] = sha256_json(delta)
            delta_stream.append(delta)
            edge_hashes.append(delta["edge_hash"])
            metrics.dag_edges += 1

            dm = domains(colors, adj, k)
            contradiction = any(colors[u] < 0 and dm[u] == 0 for u in range(n))

            if not contradiction and dfs(depth + 1):
                return True

            colors[v] = -1
            metrics.backtracks += 1

        nogood.add(parent_key)
        metrics.nogoods += 1
        return False

    solved = dfs(0)
    metrics.dag_nodes = len(node_seen)

    bits_per_cell = max(1, (k + 1).bit_length())
    full_snapshot_bits = max(1, len(delta_stream)) * n * bits_per_cell

    vertex_bits = max(1, n.bit_length())
    color_bits = max(1, k.bit_length())
    delta_bits = max(1, len(delta_stream)) * (2 + vertex_bits + color_bits)

    touches = metrics.dag_nodes + metrics.cache_hits
    dag_merge_gain = touches / max(1, metrics.dag_nodes)

    receipt = {
        "receipt_type": "famm_nuvmap_delta_dag_search_receipt",
        "schema_version": "0.1.0",
        "problem_type": "graph_k_coloring",
        "problem_hash": problem_hash,
        "route_rule_hash": rule_hash,
        "projection_level": projection_level,
        "n": n,
        "k": k,
        "edge_count": len(edges),
        "solved": solved,
        "solution": colors if solved else None,
        "exact_receipt": {
            "zero_conflicts": bool(solved and zero_conflicts(colors, edges)),
            "residual_conflicts": 0 if solved else None,
        },
        "metrics": metrics.__dict__,
        "compression_estimate": {
            "full_snapshot_bits": full_snapshot_bits,
            "delta_stream_bits": delta_bits,
            "delta_trace_gain": full_snapshot_bits / max(1, delta_bits),
            "dag_merge_gain": dag_merge_gain,
            "combined_delta_dag_gain": (full_snapshot_bits / max(1, delta_bits)) * dag_merge_gain,
        },
        "dag": {
            "node_count": metrics.dag_nodes,
            "edge_count": metrics.dag_edges,
            "node_hashes_sha256": sha256_json(sorted(node_seen.keys())),
            "edge_hashes_sha256": sha256_json(edge_hashes),
            "nogood_hashes_sha256": sha256_json(sorted(nogood)),
        },
        "delta_stream_sha256": sha256_json(delta_stream),
        "no_drift_boundary": (
            "This is search topology compression, not a P-vs-NP claim. "
            "Exactness comes only from the final zero-residual verifier."
        ),
    }
    receipt["receipt_sha256"] = sha256_json(receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    receipt = solve_graph_coloring(config)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")

    print(f"Wrote {out_path}")
    print(f"Solved: {receipt['solved']}")
    print(f"Attempts: {receipt['metrics']['attempts']}")
    print(f"DAG nodes: {receipt['metrics']['dag_nodes']}")
    print(f"Cache hits: {receipt['metrics']['cache_hits']}")
    print(f"Delta trace gain: {receipt['compression_estimate']['delta_trace_gain']:.2f}x")
    print(f"DAG merge gain: {receipt['compression_estimate']['dag_merge_gain']:.2f}x")
    print(f"Combined delta-DAG gain: {receipt['compression_estimate']['combined_delta_dag_gain']:.2f}x")
    print(f"Receipt SHA-256: {receipt['receipt_sha256']}")


if __name__ == "__main__":
    main()
