# Project / Domain / Type Map — OTOM

Generated: 2026-04-29

## Purpose

This file defines the canonical naming and placement taxonomy for Research Stack artifacts when promoting connected-source material into GitHub.

The repo should not be split or populated by vibes, paper titles, or transient chat labels. Every artifact must be placed by:

```text
Project → Domain → Type → Settlement State
```

This aligns with the uploaded Windsurf codemap, which defines OTOM as the Ordered Transformation & Orchestration Model, Lean 4 as canonical truth, Python and Verilog as extraction targets, and the lifecycle `SEED → FORMING → STABLE → CRYSTALLIZED → COMPRESSED`.

## Canonical tuple

```yaml
Project:        broad workstream or named system
Domain:         ENE axis / reality field / problem space
Type:           artifact class or implementation surface
Settlement:     SEED | FORMING | STABLE | CRYSTALLIZED | COMPRESSED
Authority:      canonical | registry | mirror | projection | evidence | quarantine
TargetPath:     concrete GitHub path
```

Short form:

```text
<Project>/<Domain>/<Type>/<Settlement>
```

Example:

```text
OTOM/Formalization/LeanModule/STABLE
```

## Project dimension

A Project is the named workstream or umbrella system.

| Project | Meaning | Primary GitHub locus |
|---|---|---|
| `OTOM` | Ordered Transformation & Orchestration Model; top-level orchestration frame | root repo |
| `ENE` | Endless Node Edges distributed substrate and publishing pipeline | `docs/ene/`, `infra/`, `tools/lean/.../ENE*` |
| `FAMM` | Frustration Aligned Memory Management | `tools/lean/Semantics/Semantics/FAMM.lean`, `docs/famm/` |
| `EquationForest` | Equation taxonomy, kernels, streets, bridges, phylogeny | `docs/equations/`, `docs/papers/` |
| `CompressionOrganism` | Hutter/compression organism family | `docs/compression/`, `data/compression/` |
| `AngrySphinx` | Post-quantum / safety / lattice defense family | `docs/security/`, `tools/lean/.../Safety/` |
| `NUVMAP` | Fixed-point UV/spectral projection map and lookup layer | `tools/lean/Semantics/Semantics/NUVMAP.lean`, `docs/nuvmap/` |
| `GraphPlumbing` | Artifact normalization, Graph.lean, graph diff, torsion, FAMM route memory | `docs/plumbing/`, `tools/lean/.../Plumbing/`, `tools/lean/.../Graph/` |
| `HardwareWarden` | FPGA / Verilog / warden node target | `hardware/`, `docs/hardware/` |
| `MarketFilter` | Behavioral point / market prototype filtering, not advice | `docs/market/`, `tools/lean/.../Market/`, `data/market/` |

## Domain dimension

Domain is the reality field. Use the ENE 14-axis schema as the default domain vocabulary.

| Domain ID | Domain | Meaning |
|---|---|---|
| `axis-00-substrate` | Substrate / Entropy / Foam | base substrate, entropy, generative field |
| `axis-01-compression` | Compression / Information Theory | compression, coding, reducibility, Hutter lane |
| `axis-02-physics` | Physics / Thermodynamics / Energy | energy, thermodynamics, physical analogues |
| `axis-03-neural` | Neural / Cognitive / Manifold | cognition, neural manifolds, SNNs, memory fields |
| `axis-04-formalization` | Formalization / Lean / Logic | Lean, theorem/proof, formal contracts |
| `axis-05-markets` | Markets / Economic / MEV | market behavior, MEV, economic dynamics |
| `axis-06-safety` | Safety / Alignment / Audit | safety, containment, audits, boundaries |
| `axis-07-attestation` | Attestation / Provenance / Cryptography | signatures, hashes, ENE receipts, provenance |
| `axis-08-hardware` | Hardware / FPGA / Warden | Verilog, FPGA, boards, warden nodes |
| `axis-09-signal` | Signal / DSP / Carriers | audio, spectral, DisplayPort, carrier systems |
| `axis-10-bioinfo` | Synthesis / Bioinfo / DNA | DNA, synthesis, biological compression |
| `axis-11-geometry` | Geometry / Topology / Manifold | topology, graph geometry, Ricci/torsion structures |
| `axis-12-publishing` | Publishing / Workflow / Metatype | Notion, Linear, Zenodo, arXiv, metatype pipeline |
| `axis-13-sovereignty` | Sovereignty / Philosophy / Ethics | cognitive sovereignty, ethical frame, philosophy |

## Type dimension

Type identifies the artifact class. This decides GitHub placement and authority rules.

| Type | Meaning | Preferred path pattern | Authority default |
|---|---|---|---|
| `LeanModule` | canonical Lean source | `tools/lean/Semantics/Semantics/**/*.lean` | canonical |
| `LeanTest` | Lean/proof test | `tools/lean/Semantics/Tests/**/*.lean` or `tests/lean/` | canonical-support |
| `MarkdownSpec` | architecture/spec document | `docs/**/*.md` | registry |
| `PaperDraft` | publishable paper/report | `docs/papers/**/*.md` | registry/evidence |
| `PythonShim` | extraction/ops shim | `infra/**/*.py`, `scripts/**/*.py` | extraction-target |
| `RustCore` | core extracted target | `core/**/*.rs` | extraction-target |
| `VerilogHardware` | hardware design | `hardware/**/*.v`, `hardware/**/*.sv` | extraction-target |
| `Dataset` | data fixture, benchmark, archive | `data/**/*` | evidence/input |
| `GraphMLTransport` | graph transport artifact | `data/graph/**/*.graphml` | transport |
| `MermaidProjection` | static visual projection | `docs/graphs/**/*.mmd` | projection |
| `AceProjection` | interactive visual projection | external/Ace reference only | projection |
| `NotionMirror` | Notion page/spec mirror | linked from docs, not canonical | mirror |
| `LinearTask` | issue/task/action artifact | linked from docs, not canonical | operational |
| `Workflow` | GitHub Actions / CI | `.github/workflows/*.yml` | gate |
| `Config` | configuration file | `config/**/*`, `.env.example` | operational |
| `QuarantineRecord` | stored but blocked from FAMM/canonical updates | `docs/safety/quarantine/**/*.md` | quarantine |

## Settlement state dimension

Every artifact must declare one settlement state.

| Settlement | Meaning | GitHub implication |
|---|---|---|
| `SEED` | idea exists, no stable draft | place as issue, note, or draft spec |
| `FORMING` | active draft or scaffold | allowed in repo with clear TODOs |
| `STABLE` | ready for use | docs/code can be referenced by other modules |
| `CRYSTALLIZED` | encoded into code/hardware/proof | implementation exists and is routed through CI/build |
| `COMPRESSED` | operational, no longer only text | represented as reusable code/data/proof artifact |

## Authority dimension

Authority determines what an artifact may update.

| Authority | May update canonical Lean? | May update FAMM? | Notes |
|---|---:|---:|---|
| `canonical` | yes | yes | Lean/proof/build-gated source |
| `registry` | no | yes, if not quarantined | accepted docs/spec registry |
| `evidence` | no | yes, as evidence context | literature, benchmark, external report |
| `mirror` | no | no by default | Notion/Airtable/Drive mirrors |
| `projection` | no | no | Mermaid, Ace, Figma, slides |
| `operational` | no | no by default | Linear task state, deployment notes |
| `quarantine` | no | no | stored but cannot mutate basins |

## Required front matter

Every promoted Markdown spec should begin with:

```yaml
---
project: OTOM
domain: axis-04-formalization
type: MarkdownSpec
settlement: FORMING
authority: registry
route_signature: project/domain/type/v0
canonical_target: tools/lean/Semantics/Semantics/...
---
```

Every Lean module should include a header comment:

```lean
/-
Project: OTOM
Domain: axis-04-formalization
Type: LeanModule
Settlement: FORMING
Authority: canonical
Route: otom/formalization/leanmodule/v0
-/
```

## Naming convention

### Path convention

```text
<surface>/<project-or-domain>/<artifact-name>.<ext>
```

Examples:

```text
docs/plumbing/ARTIFACT_NORMALIZATION.md
docs/nuvmap/NUVMAP_SPECTRAL_PROJECTION.md
tools/lean/Semantics/Semantics/Plumbing/Artifact.lean
tools/lean/Semantics/Semantics/NUVMAP.lean
data/graph/transport/research-stack-v0.graphml
docs/graphs/research-stack-v0.mmd
```

### Route signature convention

```text
<project>/<domain>/<type>/<name>/v<major>
```

Examples:

```text
otom/axis-04-formalization/leanmodule/constitution/v0
graph-plumbing/axis-11-geometry/graph-diff/torsion-detector/v0
nuvmap/axis-09-signal/spectral-projection/fixed-point-uv/v0
```

## Repo split rule

Do not create or split repos until the artifact tuple proves that the object is a different project, not merely a different domain or type.

Use one repo when:

```text
same Project, multiple Domains, multiple Types
```

Consider a separate repo only when:

```text
different Project + independent lifecycle + independent CI/build + independent publication surface
```

Current default:

```text
allaunthefox/OTOM is the canonical seed repo.
```

## Initial placement examples

| Artifact | Project | Domain | Type | Settlement | Target path |
|---|---|---|---|---|---|
| Constitution.lean | OTOM | axis-04-formalization | LeanModule | FORMING | `tools/lean/Semantics/Semantics/Constitution.lean` |
| Artifact normalization | GraphPlumbing | axis-12-publishing | MarkdownSpec | FORMING | `docs/plumbing/ARTIFACT_NORMALIZATION.md` |
| Artifact.lean | GraphPlumbing | axis-04-formalization | LeanModule | FORMING | `tools/lean/Semantics/Semantics/Plumbing/Artifact.lean` |
| Graph diff torsion | GraphPlumbing | axis-11-geometry | LeanModule | FORMING | `tools/lean/Semantics/Semantics/Graph/Torsion.lean` |
| NUVMAP projection | NUVMAP | axis-09-signal | LeanModule | FORMING | `tools/lean/Semantics/Semantics/NUVMAP.lean` |
| FPGA warden spec | HardwareWarden | axis-08-hardware | MarkdownSpec | FORMING | `docs/hardware/FPGA_WARDEN_NODE_SPEC.md` |
| Market filter boundary | MarketFilter | axis-05-markets | QuarantineRecord / MarkdownSpec | FORMING | `docs/safety/MARKET_FILTER_BOUNDARY.md` |

## Immediate next action

Use this taxonomy to update `docs/plumbing/GITHUB_MISSING_MAP.md` so every missing item has:

```text
Project | Domain | Type | Settlement | TargetPath | Priority
```

This makes the missing map actionable instead of a flat checklist.
