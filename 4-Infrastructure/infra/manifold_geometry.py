#!/usr/bin/env python3
"""
Manifold Intrinsic Geometry — Computing the Actual Shape of the Research Stack

This script extracts the dependency graph from Lean imports and computes:
- Geodesic distances (shortest import path)
- Curvature (information flow divergence/convergence at each module)
- Ricci curvature (neighborhood flow density)
- Central hubs (high betweenness centrality)
- Boundary modules (low in-degree, high out-degree = sources; high in, low out = sinks)
- Cyclic dependencies (genus / non-trivial topology)
- Module clustering (connected components)

The output is a JSON file with the full geometric characterization.
"""

import os
import re
import json
import sys
from pathlib import Path
from collections import defaultdict, deque
from itertools import combinations

SEMANTICS_DIR = Path("/home/allaun/Documents/Research Stack/0-Core-Formalism/lean/Semantics/Semantics")
OUTPUT_PATH = Path("/home/allaun/Documents/Research Stack/data/manifold_intrinsic_geometry.json")


def extract_imports(filepath: Path) -> list:
    """Extract Semantics.* imports from a Lean file."""
    imports = []
    try:
        text = filepath.read_text()
        for line in text.splitlines():
            m = re.match(r'^\s*import\s+Semantics\.(\S+)', line)
            if m:
                imports.append(m.group(1))
    except Exception:
        pass
    return imports


def build_graph():
    """Build adjacency list of the import graph."""
    nodes = set()
    edges = defaultdict(set)  # a -> {b, c} means a imports b and c
    reverse_edges = defaultdict(set)  # b -> {a, c} means b is imported by a and c

    if not SEMANTICS_DIR.exists():
        print(f"ERROR: {SEMANTICS_DIR} not found")
        sys.exit(1)

    # Find all .lean files in Semantics directory (excluding .lake)
    lean_files = []
    for root, dirs, files in os.walk(SEMANTICS_DIR):
        if '.lake' in root:
            continue
        dirs[:] = [d for d in dirs if d != '.lake']
        for f in files:
            if f.endswith('.lean'):
                lean_files.append(Path(root) / f)

    for fpath in lean_files:
        rel = fpath.relative_to(SEMANTICS_DIR)
        # Module name: path with / replaced by . and .lean stripped
        mod_name = str(rel).replace('/', '.').replace('.lean', '')
        nodes.add(mod_name)
        imports = extract_imports(fpath)
        for imp in imports:
            edges[mod_name].add(imp)
            reverse_edges[imp].add(mod_name)
            nodes.add(imp)

    return nodes, edges, reverse_edges


def bfs_distance(start, edges, all_nodes):
    """Compute shortest path distances from start to all reachable nodes."""
    dist = {n: float('inf') for n in all_nodes}
    dist[start] = 0
    q = deque([start])
    while q:
        u = q.popleft()
        for v in edges.get(u, []):
            if dist[v] == float('inf'):
                dist[v] = dist[u] + 1
                q.append(v)
    return dist


def compute_all_pairs_distances(nodes, edges):
    """Compute all-pairs shortest path distances."""
    distances = {}
    for n in nodes:
        distances[n] = bfs_distance(n, edges, nodes)
    return distances


def compute_curvature(node, edges, reverse_edges):
    """
    Compute Ollivier-Ricci curvature approximation for a node.
    Roughly: if many modules import this node (converge), positive curvature.
    If this node imports many and is imported by few (diverge), negative curvature.
    """
    out_deg = len(edges.get(node, set()))
    in_deg = len(reverse_edges.get(node, set()))
    if out_deg + in_deg == 0:
        return 0.0
    # Simple approximation: curvature = (in - out) / (in + out)
    # Positive = sink (information converges here)
    # Negative = source (information diverges from here)
    return (in_deg - out_deg) / (in_deg + out_deg)


def compute_betweenness_centrality(nodes, edges):
    """Compute betweenness centrality (approximate, for connected pairs)."""
    # For each pair (s, t), count how many shortest paths go through each node
    centrality = {n: 0 for n in nodes}
    node_list = list(nodes)

    for s in node_list:
        # BFS from s
        dist = {n: float('inf') for n in nodes}
        dist[s] = 0
        pred = {n: [] for n in nodes}
        q = deque([s])
        while q:
            u = q.popleft()
            for v in edges.get(u, set()):
                if dist[v] == float('inf'):
                    dist[v] = dist[u] + 1
                    q.append(v)
                    pred[v].append(u)
                elif dist[v] == dist[u] + 1:
                    pred[v].append(u)

        # Count paths (simplified: assume each edge contributes 1 path)
        for t in node_list:
            if t == s or dist[t] == float('inf'):
                continue
            # Mark all nodes on any shortest path from s to t
            visited = set()
            stack = [t]
            while stack:
                u = stack.pop()
                if u in visited or u == s:
                    continue
                visited.add(u)
                for p in pred.get(u, []):
                    if p not in visited:
                        stack.append(p)
            for u in visited:
                if u != t:
                    centrality[u] += 1

    # Normalize
    max_c = max(centrality.values()) if centrality else 1
    if max_c > 0:
        centrality = {k: v / max_c for k, v in centrality.items()}
    return centrality


def find_cycles(nodes, edges):
    """Find all simple cycles in the graph (up to length 5 for performance)."""
    cycles = []
    visited = set()

    def dfs(node, path, depth):
        if depth > 5:
            return
        for neighbor in edges.get(node, set()):
            if neighbor == path[0] and len(path) >= 2:
                cycles.append(path + [neighbor])
            elif neighbor not in path and neighbor not in visited:
                visited.add(neighbor)
                dfs(neighbor, path + [neighbor], depth + 1)
                visited.remove(neighbor)

    for n in nodes:
        visited.clear()
        visited.add(n)
        dfs(n, [n], 1)

    # Deduplicate (same cycle, different start points)
    unique_cycles = []
    seen = set()
    for c in cycles:
        # Normalize: start from smallest element, keep direction
        start_idx = c.index(min(c[:-1]))
        normalized = tuple(c[start_idx:-1] + c[:start_idx] + [c[start_idx]])
        if normalized not in seen:
            seen.add(normalized)
            unique_cycles.append(c)

    return unique_cycles


def find_connected_components(nodes, edges):
    """Find weakly connected components (treating edges as undirected)."""
    visited = set()
    components = []

    # Build undirected adjacency
    undirected = defaultdict(set)
    for u, vs in edges.items():
        for v in vs:
            undirected[u].add(v)
            undirected[v].add(u)

    def bfs(start):
        comp = []
        q = deque([start])
        visited.add(start)
        while q:
            u = q.popleft()
            comp.append(u)
            for v in undirected[u]:
                if v not in visited:
                    visited.add(v)
                    q.append(v)
        return comp

    for n in nodes:
        if n not in visited:
            components.append(bfs(n))

    return components


def main():
    print("[ManifoldGeometry] Building dependency graph...")
    nodes, edges, reverse_edges = build_graph()
    print(f"  Nodes: {len(nodes)}")
    print(f"  Edges: {sum(len(v) for v in edges.values())}")

    print("[ManifoldGeometry] Computing geodesic distances...")
    distances = compute_all_pairs_distances(nodes, edges)

    # Compute diameter (longest shortest path)
    finite_dists = [d for dd in distances.values() for d in dd.values() if d != float('inf') and d > 0]
    diameter = max(finite_dists) if finite_dists else 0
    avg_dist = sum(finite_dists) / len(finite_dists) if finite_dists else 0

    print(f"  Diameter: {diameter}")
    print(f"  Average distance: {avg_dist:.2f}")

    print("[ManifoldGeometry] Computing curvature...")
    curvature = {n: compute_curvature(n, edges, reverse_edges) for n in nodes}

    print("[ManifoldGeometry] Computing centrality...")
    centrality = compute_betweenness_centrality(nodes, edges)

    print("[ManifoldGeometry] Finding cycles...")
    cycles = find_cycles(nodes, edges)
    print(f"  Cycles found: {len(cycles)}")

    print("[ManifoldGeometry] Finding connected components...")
    components = find_connected_components(nodes, edges)
    print(f"  Components: {len(components)}")

    # Identify key geometric features
    hubs = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:15]
    high_curv = sorted(curvature.items(), key=lambda x: x[1], reverse=True)[:10]
    low_curv = sorted(curvature.items(), key=lambda x: x[1])[:10]

    # Boundary detection
    sources = [(n, len(edges.get(n, set())), len(reverse_edges.get(n, set())))
               for n in nodes if len(reverse_edges.get(n, set())) == 0 and len(edges.get(n, set())) > 0]
    sinks = [(n, len(edges.get(n, set())), len(reverse_edges.get(n, set())))
             for n in nodes if len(edges.get(n, set())) == 0 and len(reverse_edges.get(n, set())) > 0]

    # Modules with no imports and no importers (isolated points)
    isolated = [n for n in nodes if len(edges.get(n, set())) == 0 and len(reverse_edges.get(n, set())) == 0]

    report = {
        "meta": {
            "node_count": len(nodes),
            "edge_count": sum(len(v) for v in edges.values()),
            "diameter": diameter,
            "average_distance": avg_dist,
            "cycle_count": len(cycles),
            "component_count": len(components),
        },
        "hubs": [{"module": n, "centrality": round(c, 4)} for n, c in hubs],
        "positive_curvature": [{"module": n, "curvature": round(c, 4)} for n, c in high_curv],
        "negative_curvature": [{"module": n, "curvature": round(c, 4)} for n, c in low_curv],
        "sources": [{"module": n, "out_degree": o, "in_degree": i} for n, o, i in sources],
        "sinks": [{"module": n, "out_degree": o, "in_degree": i} for n, o, i in sinks],
        "isolated": isolated,
        "cycles": [c for c in cycles[:20]],  # Limit output size
        "components": [
            {"size": len(comp), "modules": comp[:50]}  # Truncate large components
            for comp in sorted(components, key=len, reverse=True)
        ],
        "full_graph": {
            "nodes": list(nodes),
            "edges": {k: list(v) for k, v in edges.items()},
        },
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"[ManifoldGeometry] Wrote: {OUTPUT_PATH}")

    # Print summary
    print("\n" + "=" * 70)
    print("INTRINSIC GEOMETRY OF THE RESEARCH STACK")
    print("=" * 70)
    print(f"\nScale: {len(nodes)} modules, {sum(len(v) for v in edges.values())} import edges")
    print(f"Diameter (longest shortest path): {diameter}")
    print(f"Average geodesic distance: {avg_dist:.2f}")
    print(f"Cycles (non-trivial topology): {len(cycles)}")
    print(f"Connected components: {len(components)}")

    print(f"\n--- HUBS (High Betweenness Centrality) ---")
    for n, c in hubs[:10]:
        print(f"  {n:40s}  centrality={c:.4f}")

    print(f"\n--- POSITIVE CURVATURE (Information Converges Here) ---")
    for n, c in high_curv[:5]:
        print(f"  {n:40s}  curvature={c:+.4f}")

    print(f"\n--- NEGATIVE CURVATURE (Information Diverges From Here) ---")
    for n, c in low_curv[:5]:
        print(f"  {n:40s}  curvature={c:+.4f}")

    print(f"\n--- SOURCES (No imports, pure origin) ---")
    for n, o, i in sources[:5]:
        print(f"  {n:40s}  out={o}")

    print(f"\n--- SINKS (No exports, dead ends) ---")
    for n, o, i in sinks[:5]:
        print(f"  {n:40s}  in={i}")

    if isolated:
        print(f"\n--- ISOLATED POINTS (No connections) ---")
        for n in isolated[:10]:
            print(f"  {n}")

    if cycles:
        print(f"\n--- CYCLES (Non-contractible loops) ---")
        for c in cycles[:5]:
            print(f"  {' -> '.join(c)}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
