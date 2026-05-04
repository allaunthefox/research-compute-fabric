# OTOM — Ordered Transformation & Orchestration Model

OTOM is the canonical GitHub seed repository for the Research Stack: a Lean-first system for information theory, compression, graph/torsion routing, neural/manifold semantics, infrastructure shims, and hardware extraction targets.

## Grounding axioms

1. **Lean is the source of truth.** Python, Rust, Verilog, GraphML, Mermaid, and UI surfaces are extraction targets or projections.
2. **Publishing pipeline:** Substrate / ENE ↔ Surface / Notion ↔ Intent / Linear ⟹ Metatype.
3. **Settlement lifecycle:** `SEED → FORMING → STABLE → CRYSTALLIZED → COMPRESSED`.

## Authority rule

```text
Lean / Graph.lean      = canonical structure and proof authority
GraphML               = transport format
Mermaid               = static projection
Ace Knowledge Graph   = interactive projection only
Notion                = semantic registry / spec source
Linear                = task graph
Airtable              = operational mirror if connected later
Consensus             = literature context, not proof
GitHub                = code/provenance surface once seeded
```

Nothing updates canonical memory directly. Every item must become an artifact first:

```text
artifact → fingerprint → route → outcome → memory
```

## Placement tuple

All promoted artifacts use:

```text
Project → Domain → Type → Settlement State
```

See [`docs/plumbing/PROJECT_DOMAIN_TYPE_MAP.md`](docs/plumbing/PROJECT_DOMAIN_TYPE_MAP.md).

## Current bootstrap docs

- [`docs/plumbing/GITHUB_MISSING_MAP.md`](docs/plumbing/GITHUB_MISSING_MAP.md)
- [`docs/plumbing/PROJECT_DOMAIN_TYPE_MAP.md`](docs/plumbing/PROJECT_DOMAIN_TYPE_MAP.md)
- [`PROJECT_MAP.md`](PROJECT_MAP.md)
- [`TODO_MAP.md`](TODO_MAP.md)
- [`CONCEPTS.md`](CONCEPTS.md)
- [`docs/AGENTS.md`](docs/AGENTS.md)
- [`docs/ENE_SCHEMA.md`](docs/ENE_SCHEMA.md)

## Canonical Lean entry

```text
tools/lean/Semantics/Semantics/Constitution.lean
```

## Repository status

This repo is being seeded from connected-source audit results. Treat current modules as `FORMING` until `lake build` and proof obligations are wired into CI.
