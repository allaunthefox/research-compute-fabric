#!/usr/bin/env python3
"""Map equation forest: extract symbols and build connection graph."""
import json, re, sys
from collections import defaultdict
from pathlib import Path

DBS = [
    "3-Mathematical-Models/equations_100/equations_database.jsonl",
    "3-Mathematical-Models/equations_10000/equations_database.jsonl",
    "3-Mathematical-Models/equations_parallel_10000/equations_database.jsonl",
]

SYMBOL_RE = re.compile(r'[a-zA-Z\u03b1-\u03c9\u0391-\u03a9\u2102\u2115\u211a\u211d\u2124][a-zA-Z0-9]*')

def extract_symbols(eq: str) -> set:
    return set(SYMBOL_RE.findall(eq))

def main():
    equations = []
    for path in DBS:
        p = Path("/home/allaun/Documents/Research Stack") / path
        if not p.exists():
            print(f"SKIP: {path}")
            continue
        with open(p) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                eq = obj.get("equation") or obj.get("normalized", "")
                if eq:
                    equations.append({
                        "id": obj.get("equation_id", f"eq_{len(equations)}"),
                        "equation": eq,
                        "source": obj.get("source", ""),
                        "source_type": obj.get("source_type", ""),
                        "paper_title": obj.get("paper_title", ""),
                        "category": obj.get("category", ""),
                        "symbols": list(extract_symbols(eq)),
                    })

    print(f"Loaded {len(equations)} equations")

    # Build symbol -> equation index mapping
    symbol_to_eqs = defaultdict(list)
    for i, eq in enumerate(equations):
        for sym in eq["symbols"]:
            symbol_to_eqs[sym].append(i)

    # Build edges: shared symbols
    edges = []
    for sym, idxs in symbol_to_eqs.items():
        if len(idxs) < 2:
            continue
        for i in range(len(idxs)):
            for j in range(i+1, len(idxs)):
                edges.append({
                    "source": equations[idxs[i]]["id"],
                    "target": equations[idxs[j]]["id"],
                    "type": "shares_variable",
                    "symbol": sym,
                })

    # Build edges: same source paper
    source_to_eqs = defaultdict(list)
    for i, eq in enumerate(equations):
        if eq["source"]:
            source_to_eqs[eq["source"]].append(i)
    for src, idxs in source_to_eqs.items():
        if len(idxs) < 2:
            continue
        for i in range(len(idxs)):
            for j in range(i+1, len(idxs)):
                edges.append({
                    "source": equations[idxs[i]]["id"],
                    "target": equations[idxs[j]]["id"],
                    "type": "same_paper",
                    "paper": src,
                })

    # Deduplicate edges
    seen = set()
    unique_edges = []
    for e in edges:
        key = tuple(sorted([e["source"], e["target"]])) + (e["type"],)
        if key not in seen:
            seen.add(key)
            unique_edges.append(e)

    # Output
    graph = {
        "meta": {
            "total_equations": len(equations),
            "total_edges": len(unique_edges),
            "databases": DBS,
        },
        "nodes": [{"id": eq["id"], "equation": eq["equation"][:200], "source": eq["source"], "category": eq["category"]} for eq in equations[:1000]],
        "edges": unique_edges[:5000],
        "symbol_frequency": dict(sorted(
            {sym: len(idxs) for sym, idxs in symbol_to_eqs.items()}.items(),
            key=lambda x: -x[1]
        )[:100]),
    }

    out = Path("/home/allaun/Documents/Research Stack/3-Mathematical-Models/equation_forest_graph.json")
    with open(out, "w") as f:
        json.dump(graph, f, indent=2)
    print(f"Wrote {out}")
    print(f"  Nodes: {len(graph['nodes'])}")
    print(f"  Edges: {len(graph['edges'])}")
    print(f"  Top symbols: {list(graph['symbol_frequency'].keys())[:10]}")

if __name__ == "__main__":
    main()
