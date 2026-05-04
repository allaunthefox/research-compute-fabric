---
project: OTOM
domain: axis-12-publishing
type: MarkdownSpec
settlement: FORMING
authority: registry
route_signature: otom/axis-12-publishing/markdownspec/project-map/v0
---

# OTOM Project Map

## Repository structure

| Path | Purpose | Authority |
|---|---|---|
| `tools/lean/Semantics/` | Lean canonical truth package | canonical |
| `docs/` | documentation, papers, specs, boundary records | registry |
| `docs/plumbing/` | artifact normalization, route, graph, authority specs | registry |
| `infra/` | Python shims and distributed infrastructure | extraction-target |
| `scripts/` | ingestion and processing scripts | operational |
| `data/` | datasets, fixtures, graph transports, benchmarks | evidence/input |
| `hardware/` | Verilog / FPGA designs | extraction-target |
| `core/` | Rust / extracted core targets | extraction-target |
| `out/` | generated reports and attestations | output |
| `tests/` | testbenches and equivalence tests | gate-support |
| `config/` | configuration files | operational |

## Main entry points

- `README.md` — repo orientation and authority rule
- `docs/plumbing/PROJECT_DOMAIN_TYPE_MAP.md` — placement taxonomy
- `docs/plumbing/GITHUB_MISSING_MAP.md` — current backfill map
- `tools/lean/Semantics/Semantics/Constitution.lean` — Lean entry point

## Current phase

`FORMING`: repository shell has been seeded; canonical Lean and graph modules are scaffolds until build and proof gates are active.
