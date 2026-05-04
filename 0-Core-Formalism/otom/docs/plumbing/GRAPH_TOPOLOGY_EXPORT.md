---
project: GraphPlumbing
domain: axis-11-geometry
type: MarkdownSpec
settlement: FORMING
authority: registry
route_signature: graph-plumbing/axis-11-geometry/markdownspec/graph-topology-export/v0
canonical_target: tools/lean/Semantics/Semantics/Graph.lean
---

# Graph Topology Export v0

## Rule

```text
Graph.lean = canonical
GraphML    = transport
Mermaid    = static projection
Ace Graph  = interactive projection
```

## Purpose

Unify Graph.lean, GraphML, Mermaid, and interactive graph projections as views of one graph topology artifact class.

## Export lanes

| Lane | Path | Role |
|---|---|---|
| Lean | `tools/lean/Semantics/Semantics/Graph.lean` | canonical graph model |
| Diff | `tools/lean/Semantics/Semantics/Graph/Diff.lean` | structural delta |
| Torsion | `tools/lean/Semantics/Semantics/Graph/Torsion.lean` | diff pressure score |
| GraphML | `data/graph/transport/*.graphml` | transport |
| Mermaid | `docs/graphs/*.mmd` | readable projection |

## Mutation rule

Only the canonical graph model and routed graph diffs may update graph authority. Projection exports cannot update the graph.
