#!/usr/bin/env python3
"""Compute a receipt-bearing neural type coverage eigenvector.

This is intentionally data-source agnostic. It accepts JSONL records shaped like
the spec in docs/research/NEURAL_TYPE_EIGENVECTOR_COVERAGE.md and produces a
ranked coverage report plus simple anti-overfit checks.

The script does not claim biological completeness. It only ranks nodes already
present in the input evidence graph.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Tuple


DEFAULT_OUTPUT = Path("5-Applications/out/neural_type_eigenvector_coverage.json")


@dataclass
class NodeReceipt:
    node_id: str
    kind: str = "node"
    label: str = ""
    source_count: int = 1
    modality_count: int = 1
    missingness: float = 0.0
    contradiction_count: float = 0.0
    species: str = "unknown"
    region: str = "unknown"
    provenance: List[str] = field(default_factory=list)

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> "NodeReceipt":
        node_id = str(record.get("id") or record.get("node") or "")
        if not node_id:
            raise ValueError(f"node record missing id: {record}")

        missing = record.get("missingness")
        if missing is None and isinstance(record.get("missing"), list):
            missing = len(record["missing"])

        return cls(
            node_id=node_id,
            kind=str(record.get("kind", "node")),
            label=str(record.get("label", node_id)),
            source_count=max(1, int(record.get("source_count", 1))),
            modality_count=max(1, int(record.get("modality_count", 1))),
            missingness=float(missing or 0.0),
            contradiction_count=float(record.get("contradiction_count", 0.0)),
            species=str(record.get("species", "unknown")),
            region=str(record.get("region", "unknown")),
            provenance=[str(x) for x in record.get("provenance", [])],
        )


@dataclass(frozen=True)
class EdgeReceipt:
    src: str
    dst: str
    weight: float
    rel: str = "related"
    receipt: str = ""

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> "EdgeReceipt":
        src = str(record.get("src", ""))
        dst = str(record.get("dst", ""))
        if not src or not dst:
            raise ValueError(f"edge record missing src/dst: {record}")

        if "weight_q0_16" in record:
            weight = float(record["weight_q0_16"]) / 65535.0
        else:
            weight = float(record.get("weight", 1.0))

        if not math.isfinite(weight) or weight < 0:
            raise ValueError(f"edge has invalid weight: {record}")

        return cls(
            src=src,
            dst=dst,
            weight=weight,
            rel=str(record.get("rel", "related")),
            receipt=str(record.get("receipt", "")),
        )


def load_jsonl(path: Path) -> Tuple[Dict[str, NodeReceipt], List[EdgeReceipt]]:
    nodes: Dict[str, NodeReceipt] = {}
    edges: List[EdgeReceipt] = []

    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            kind = str(record.get("kind", ""))

            if kind == "edge":
                edge = EdgeReceipt.from_record(record)
                edges.append(edge)
                nodes.setdefault(edge.src, NodeReceipt(node_id=edge.src))
                nodes.setdefault(edge.dst, NodeReceipt(node_id=edge.dst))
            else:
                node = NodeReceipt.from_record(record)
                nodes[node.node_id] = node

    return nodes, edges


def adjacency(nodes: Mapping[str, NodeReceipt], edges: Iterable[EdgeReceipt]) -> Dict[str, Dict[str, float]]:
    graph: Dict[str, Dict[str, float]] = {node_id: {} for node_id in nodes}
    for edge in edges:
        if edge.weight == 0:
            continue
        graph.setdefault(edge.src, {})
        graph.setdefault(edge.dst, {})
        graph[edge.src][edge.dst] = graph[edge.src].get(edge.dst, 0.0) + edge.weight
        graph[edge.dst][edge.src] = graph[edge.dst].get(edge.src, 0.0) + edge.weight
    return graph


def principal_eigenvector(
    graph: Mapping[str, Mapping[str, float]],
    max_iter: int = 200,
    tolerance: float = 1e-10,
) -> Tuple[Dict[str, float], float, int, float]:
    node_ids = sorted(graph)
    if not node_ids:
        return {}, 0.0, 0, 0.0

    value = {node_id: 1.0 / math.sqrt(len(node_ids)) for node_id in node_ids}
    delta = float("inf")

    for iteration in range(1, max_iter + 1):
        next_value = {}
        for node_id in node_ids:
            next_value[node_id] = sum(weight * value[dst] for dst, weight in graph[node_id].items())

        norm = math.sqrt(sum(v * v for v in next_value.values()))
        if norm == 0:
            break
        next_value = {node_id: next_value[node_id] / norm for node_id in node_ids}
        delta = math.sqrt(sum((next_value[node_id] - value[node_id]) ** 2 for node_id in node_ids))
        value = next_value
        if delta <= tolerance:
            break

    numerator = 0.0
    denominator = 0.0
    for src in node_ids:
        av = sum(weight * value[dst] for dst, weight in graph[src].items())
        numerator += value[src] * av
        denominator += value[src] * value[src]
    eigenvalue = numerator / denominator if denominator else 0.0

    return value, eigenvalue, iteration, delta


def coverage_scores(
    nodes: Mapping[str, NodeReceipt],
    eigenvector: Mapping[str, float],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for node_id, receipt in nodes.items():
        x_node = abs(float(eigenvector.get(node_id, 0.0)))
        denominator = 1.0 + receipt.missingness + receipt.contradiction_count
        coverage = x_node * receipt.source_count * receipt.modality_count / denominator
        rows.append(
            {
                "node": node_id,
                "label": receipt.label,
                "kind": receipt.kind,
                "coverage": coverage,
                "eigenvector": x_node,
                "source_count": receipt.source_count,
                "modality_count": receipt.modality_count,
                "missingness": receipt.missingness,
                "contradiction_count": receipt.contradiction_count,
                "species": receipt.species,
                "region": receipt.region,
                "provenance": receipt.provenance,
            }
        )

    rows.sort(key=lambda row: row["coverage"], reverse=True)
    return rows


def group_holdout(
    nodes: Mapping[str, NodeReceipt],
    edges: List[EdgeReceipt],
    group_name: str,
    group_values: Iterable[str],
    top_k: int,
) -> Dict[str, Any]:
    base_graph = adjacency(nodes, edges)
    base_vec, _, _, _ = principal_eigenvector(base_graph)
    base_top = [row["node"] for row in coverage_scores(nodes, base_vec)[:top_k]]

    results = []
    for group_value in sorted(set(group_values)):
        kept_nodes = {
            node_id: node
            for node_id, node in nodes.items()
            if getattr(node, group_name) != group_value
        }
        kept_edges = [
            edge for edge in edges
            if edge.src in kept_nodes and edge.dst in kept_nodes
        ]
        vec, _, _, _ = principal_eigenvector(adjacency(kept_nodes, kept_edges))
        top = [row["node"] for row in coverage_scores(kept_nodes, vec)[:top_k]]
        overlap = len(set(base_top) & set(top)) / max(1, len(base_top))
        results.append({"held_out": group_value, "top_k_overlap": overlap, "remaining_nodes": len(kept_nodes)})

    return {"group": group_name, "top_k": top_k, "baseline_top": base_top, "results": results}


def degree_preserving_null(
    nodes: Mapping[str, NodeReceipt],
    edges: List[EdgeReceipt],
    trials: int,
    seed: int,
    top_k: int,
) -> Dict[str, Any]:
    rng = random.Random(seed)
    node_ids = sorted(nodes)
    real_vec, real_lambda, _, _ = principal_eigenvector(adjacency(nodes, edges))
    real_scores = coverage_scores(nodes, real_vec)
    real_top_mean = mean(row["coverage"] for row in real_scores[:top_k])

    null_means = []
    weights = [edge.weight for edge in edges]
    for _ in range(trials):
        shuffled_edges = []
        for weight in weights:
            src, dst = rng.sample(node_ids, 2)
            shuffled_edges.append(EdgeReceipt(src=src, dst=dst, weight=weight, rel="null"))
        vec, _, _, _ = principal_eigenvector(adjacency(nodes, shuffled_edges))
        rows = coverage_scores(nodes, vec)
        null_means.append(mean(row["coverage"] for row in rows[:top_k]))

    null_mean = mean(null_means)
    null_std = stdev(null_means)
    z_score = (real_top_mean - null_mean) / null_std if null_std else 0.0
    return {
        "trials": trials,
        "top_k": top_k,
        "real_eigenvalue": real_lambda,
        "real_top_k_mean_coverage": real_top_mean,
        "null_top_k_mean_coverage": null_mean,
        "null_top_k_std_coverage": null_std,
        "z_score": z_score,
    }


def mean(values: Iterable[float]) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def stdev(values: Iterable[float]) -> float:
    values = list(values)
    if len(values) < 2:
        return 0.0
    avg = mean(values)
    return math.sqrt(sum((value - avg) ** 2 for value in values) / (len(values) - 1))


def demo_records() -> Tuple[Dict[str, NodeReceipt], List[EdgeReceipt]]:
    records = [
        {"kind": "neuron_sample", "id": "cell:mouse:pyramidal:1", "label": "mouse pyramidal 1", "species": "mouse", "region": "cortex", "source_count": 2, "modality_count": 2, "provenance": ["demo"]},
        {"kind": "neuron_sample", "id": "cell:human:pyramidal:1", "label": "human pyramidal 1", "species": "human", "region": "cortex", "source_count": 2, "modality_count": 2, "provenance": ["demo"]},
        {"kind": "neuron_sample", "id": "cell:mouse:interneuron:1", "label": "mouse interneuron 1", "species": "mouse", "region": "cortex", "source_count": 1, "modality_count": 2, "provenance": ["demo"]},
        {"kind": "feature", "id": "feature:deep_branch_order", "label": "deep branch order", "source_count": 3, "modality_count": 2, "provenance": ["demo"]},
        {"kind": "feature", "id": "feature:long_apical_dendrite", "label": "long apical dendrite", "source_count": 3, "modality_count": 2, "provenance": ["demo"]},
        {"kind": "feature", "id": "feature:fast_spiking", "label": "fast spiking", "source_count": 1, "modality_count": 2, "provenance": ["demo"], "missingness": 0.5},
    ]
    edge_records = [
        {"kind": "edge", "src": "cell:mouse:pyramidal:1", "dst": "feature:deep_branch_order", "weight": 0.92, "receipt": "demo morphology"},
        {"kind": "edge", "src": "cell:human:pyramidal:1", "dst": "feature:deep_branch_order", "weight": 0.89, "receipt": "demo morphology"},
        {"kind": "edge", "src": "cell:mouse:pyramidal:1", "dst": "feature:long_apical_dendrite", "weight": 0.86, "receipt": "demo morphology"},
        {"kind": "edge", "src": "cell:human:pyramidal:1", "dst": "feature:long_apical_dendrite", "weight": 0.84, "receipt": "demo morphology"},
        {"kind": "edge", "src": "cell:mouse:interneuron:1", "dst": "feature:fast_spiking", "weight": 0.95, "receipt": "demo electrophysiology"},
        {"kind": "edge", "src": "feature:deep_branch_order", "dst": "feature:long_apical_dendrite", "weight": 0.60, "receipt": "demo co-occurrence"},
    ]
    nodes = {record["id"]: NodeReceipt.from_record(record) for record in records}
    edges = [EdgeReceipt.from_record(record) for record in edge_records]
    return nodes, edges


def run(nodes: Dict[str, NodeReceipt], edges: List[EdgeReceipt], top_k: int, null_trials: int, seed: int) -> Dict[str, Any]:
    graph = adjacency(nodes, edges)
    eigenvector, eigenvalue, iterations, delta = principal_eigenvector(graph)
    scores = coverage_scores(nodes, eigenvector)
    feature_scores = [row["coverage"] for row in scores if row["kind"] == "feature"]
    all_scores = [row["coverage"] for row in scores]

    return {
        "metadata": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "top_k": top_k,
            "eigenvalue": eigenvalue,
            "power_iterations": iterations,
            "residual_delta": delta,
            "mean_coverage_all_nodes": mean(all_scores),
            "mean_coverage_feature_nodes": mean(feature_scores),
        },
        "top_nodes": scores[:top_k],
        "holdouts": [
            group_holdout(nodes, edges, "species", (node.species for node in nodes.values()), top_k),
            group_holdout(nodes, edges, "region", (node.region for node in nodes.values()), top_k),
        ],
        "null_model": degree_preserving_null(nodes, edges, null_trials, seed, top_k),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Evidence graph JSONL.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--null-trials", type=int, default=25)
    parser.add_argument("--seed", type=int, default=20260506)
    parser.add_argument("--demo", action="store_true", help="Run against a tiny built-in demo graph.")
    args = parser.parse_args()

    if args.demo:
        nodes, edges = demo_records()
    elif args.input:
        nodes, edges = load_jsonl(args.input)
    else:
        parser.error("provide --input evidence.jsonl or --demo")

    result = run(nodes, edges, args.top_k, args.null_trials, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"nodes={result['metadata']['node_count']}")
    print(f"edges={result['metadata']['edge_count']}")
    print(f"eigenvalue={result['metadata']['eigenvalue']:.6f}")
    print(f"mean_coverage_all_nodes={result['metadata']['mean_coverage_all_nodes']:.6f}")
    print(f"mean_coverage_feature_nodes={result['metadata']['mean_coverage_feature_nodes']:.6f}")
    print(f"null_z_score={result['null_model']['z_score']:.6f}")
    print(f"wrote={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
