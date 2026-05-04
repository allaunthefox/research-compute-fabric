---
project: GraphPlumbing
domain: axis-12-publishing
type: MarkdownSpec
settlement: FORMING
authority: registry
route_signature: graph-plumbing/axis-12-publishing/markdownspec/artifact-normalization/v0
canonical_target: tools/lean/Semantics/Semantics/Plumbing/Artifact.lean
---

# Artifact Normalization Layer v0

## Purpose

Normalize every incoming item before it can influence graph, FAMM, memory, or publication surfaces.

```text
artifact → fingerprint → route → outcome → memory
```

## Required fields

- `artifactId`
- `artifactKind`
- `project`
- `domain`
- `type`
- `settlement`
- `title`
- `contentHash`
- `semanticHash`
- `authorityLevel`
- `quarantine`
- `tags`
- `summary`

## Canonical Lean

See:

```text
tools/lean/Semantics/Semantics/Plumbing/Artifact.lean
```

## Non-bypass rule

No artifact may update canonical graph, FAMM, or memory unless routed through this layer.
