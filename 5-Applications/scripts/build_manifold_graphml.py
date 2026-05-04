#!/usr/bin/env python3
"""
build_manifold_graphml.py — Build GraphML from Research Stack manifold geometry.

Reads manifold_intrinsic_geometry.json (output of manifold_geometry.py)
and writes a GraphML file with full geometric attributes per node and edge.

Nodes: Lean modules with curvature, centrality, in/out degree, component, type
Edges: import dependencies with geodesic weight

Usage:
    python3 5-Applications/scripts/build_manifold_graphml.py
"""

import json
import os
import sys
from pathlib import Path

import networkx as nx

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"


def load_geometry(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_topology(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_manifold_graph(geometry: dict, topology: dict) -> nx.DiGraph:
    G = nx.DiGraph()

    meta = geometry.get("meta", {})
    for k, v in meta.items():
        # GraphML can't serialize dict/bool; flatten primitive values only
        if isinstance(v, (str, int, float)):
            G.graph[k] = v

    full = topology.get("full_graph", {})
    nodes = full.get("nodes", [])
    edges_map = full.get("edges", {})

    # Index curvature and centrality
    curvature = {}
    for item in geometry.get("positive_curvature", []):
        curvature[item["module"]] = item["curvature"]
    for item in geometry.get("negative_curvature", []):
        curvature[item["module"]] = item["curvature"]

    centrality = {}
    for item in geometry.get("hubs", []):
        centrality[item["module"]] = item["centrality"]

    # Index sources/sinks
    source_degree = {}
    for item in geometry.get("sources", []):
        source_degree[item["module"]] = item.get("out_degree", 0)

    sink_degree = {}
    for item in geometry.get("sinks", []):
        sink_degree[item["module"]] = item.get("in_degree", 0)

    # Components index
    component_map = {}
    for comp in topology.get("components", []):
        cid = comp.get("id", "unknown")
        for member in comp.get("members", []):
            component_map[member] = cid

    # Holes index (gap modules)
    gap_modules = set()
    for hole in topology.get("holes", []):
        for mod in hole.get("missing_modules", []):
            gap_modules.add(mod)

    # Add nodes (nodes are plain module name strings)
    for name in nodes:
        G.add_node(
            name,
            type="module",
            centrality=centrality.get(name, 0.0),
            curvature=curvature.get(name, 0.0),
            component=component_map.get(name, "unknown"),
            is_source=str(name in source_degree),
            is_sink=str(name in sink_degree),
            is_gap=str(name in gap_modules),
        )

    # Add edges (edges_map is dict: src -> [dst, ...])
    for src, dsts in edges_map.items():
        for dst in dsts:
            G.add_edge(src, dst, relation="IMPORTS", weight=1.0)

    return G


def write_graphml(G: nx.DiGraph, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(G, str(path))
    print(f"GraphML saved: {path}")
    print(f"  Nodes: {G.number_of_nodes()}")
    print(f"  Edges: {G.number_of_edges()}")
    meta = G.graph.get("meta", {})
    print(f"  Diameter: {meta.get('diameter', 'N/A')}")
    print(f"  Components: {meta.get('component_count', 'N/A')}")
    print(f"  Cycles: {meta.get('cycle_count', 'N/A')}")


def write_mermaid_hub(G: nx.DiGraph, path: Path, top_n: int = 50):
    """Write a Mermaid diagram of top hubs for quick visualization."""
    hubs = sorted(
        ((n, d["centrality"]) for n, d in G.nodes(data=True) if d.get("centrality", 0) > 0),
        key=lambda x: x[1],
        reverse=True,
    )[:top_n]

    lines = ["graph TD"]
    for name, cent in hubs:
        safe = name.replace(".", "_")
        label = f"{name}({name}\\nC={cent:.2f})"
        lines.append(f"    {safe}[\"{label}\"]")

    # Add edges between hubs
    hub_names = {n for n, _ in hubs}
    for src, dst, data in G.edges(data=True):
        if src in hub_names and dst in hub_names:
            lines.append(f"    {src.replace('.', '_')} --> {dst.replace('.', '_')}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Mermaid hub diagram: {path}")


def main():
    geom_path = DATA_DIR / "manifold_intrinsic_geometry.json"
    topo_path = DATA_DIR / "manifold_topology_report.json"

    if not geom_path.exists():
        print(f"Geometry data not found: {geom_path}")
        sys.exit(1)
    if not topo_path.exists():
        print(f"Topology data not found: {topo_path}")
        sys.exit(1)

    geometry = load_geometry(geom_path)
    # The intrinsic geometry JSON contains both geometry metrics AND the full graph
    # (nodes/edges/full_graph). topology report is a different schema from manifold_perception.
    G = build_manifold_graph(geometry, geometry)

    graphml_path = ARTIFACTS_DIR / "manifold_geometry.graphml"
    write_graphml(G, graphml_path)

    mermaid_path = ARTIFACTS_DIR / "manifold_hubs.mmd"
    write_mermaid_hub(G, mermaid_path, top_n=30)

    print("Done.")


if __name__ == "__main__":
    main()
