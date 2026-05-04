---
project: OTOM
domain: axis-06-safety
type: MarkdownSpec
settlement: FORMING
authority: registry
route_signature: otom/axis-06-safety/markdownspec/agents/v0
---

# AGENTS — Operating Rules v0

## Core rules

1. Lean is canonical truth.
2. Python/Rust/Verilog are extraction targets unless explicitly promoted.
3. GraphML is transport, not graph authority.
4. Mermaid/Ace/Figma are projections, not graph authority.
5. Notion and Linear are mirrors/workflow surfaces, not proof authority.
6. Every promoted artifact must declare Project, Domain, Type, Settlement, and Authority.
7. Nothing updates FAMM or canonical memory directly; artifacts must route through normalization first.

## No-direct-mutation rule

```text
artifact → fingerprint → route → outcome → memory
```

Any bypass of this route is an invalid mutation.

## Quarantine rule

Projection-only, operational-only, or quarantined artifacts cannot update canonical Lean or FAMM basins.

## Hot-path numerical rule

Fixed-point arithmetic is preferred for formal/extraction paths. Float usage must be marked as debug, boundary, or non-hot-path.

## Repo placement rule

Use:

```text
Project → Domain → Type → Settlement
```

See `docs/plumbing/PROJECT_DOMAIN_TYPE_MAP.md`.
