# Language Set Manifold Graph Typing

Status: Draft v0.1
Date: 2026-05-08
Scope: RRC typing surface for whole language sets, conlangs, programming
languages, formal languages, esolangs, notation systems, and symbolic families
Claim boundary: this is a routing and compression-admission contract. It does
not prove linguistic truth, translation quality, cultural ownership, or
compression gain.

## 1. Purpose

This document defines how an entire language set can be typed as a manifold
graph for the Rainbow Raccoon Compiler.

The unit is not a token, glyph, word, or source snippet. The unit is a
language/code-set graph:

```text
language or code set
  -> typed category inventory
  -> grammar, morphology, type, or control edges
  -> density markers
  -> surface realization views
  -> residual/replay policy
  -> RRC admissibility receipt
```

The goal is to let RRC classify a language family, notation system,
constructed language, programming language, proof language, esolang, or formal
pattern language as a reusable compression and projection surface while keeping
glyph identity, cultural identity, lexicon, source text, and program examples
separate from the internal atom payload. What we need are density markers.

## 2. First Principles

### Principle 1: A Language Set Is A Graph, Not A Bag Of Words

A language set must be represented by typed nodes and typed edges:

```text
root / stem / symbol / phrase / grammatical category / surface form
```

Edges declare how the parts combine, mutate, omit, scope, or repair each other.

### Principle 2: Surface Form Is Not Payload

The graph may point to words, phonemes, glyphs, scripts, or rendered examples,
but these are adapter views. The canonical payload is the typed graph plus its
replay law.

### Principle 3: Dense Morphology Is A Compression Surface

Systems such as Ithkuil are useful because they show how many semantic axes can
be packed into a small surface form. RRC should extract this as a lawful
category-portmanteau shape, not copy the language.

### Principle 3A: Density Markers Are The Payload-Relevant Signal

The compiler does not need glyphs, words, or copied source programs. It needs
markers that explain why a surface carries unusually high information density.
For human languages this often comes from morphology, mutation, script
layering, or semantic radicals. For coding languages it often comes from type
systems, stack effects, implicit search, array rank, self-modification, layout
channels, or tiny opcode sets:

```text
strict affix slot
semantic category portmanteau
mutation edge
case/number ladder
script-view separation
machine-parseable grammar
minimal lexicon with high residual pressure
stack effect signature
typeclass dictionary
unification search tree
self-modifying instruction surface
invisible token channel
```

These density markers become graph nodes. Glyphs and lexemes remain external
surface views unless a source license explicitly permits deeper use.

### Principle 4: Predictable Material Must Be Replayable

If a language graph omits predictable material, the decoder must recover it
from grammar tables or declare a residual sidecar.

### Principle 5: Whole-Language Typing Is HOLD By Default

A whole language graph is large and easy to overclaim. It becomes CANDIDATE only
when source identity, graph schema, replay law, negative controls, and scale
band are declared.

## 3. RRC Shape

The new RRC lawful shape is:

```text
LanguageSetManifoldGraph
```

Canonical pipeline:

```text
language source set
  -> language-set manifest
  -> category inventory
  -> typed manifold graph
  -> RRC 16-axis projection
  -> nearest lawful shape
  -> type witness
  -> residual/replay receipt
```

Coding and formal language sets use the same shape:

```text
programming/formal language source set
  -> operator/type/control inventory
  -> typed manifold graph
  -> density markers
  -> RRC 16-axis projection
  -> residual/replay receipt
```

## 4. Graph Schema

Minimum graph packet:

```yaml
language_set_graph:
  language_set_id:
  source_scope:
  license_boundary:
  category_inventory:
  node_types:
  edge_types:
  surface_views:
  manifold_axes:
  replay_law:
  residual_policy:
  negative_controls:
  rrc_receipt:
```

Required node types:

| Node Type | Meaning |
|---|---|
| `root` | durable lexical or symbolic root |
| `category` | grammatical, semantic, proof, or compression axis |
| `density_marker` | abstract reason the language surface carries compressed information |
| `surface` | word, glyph, phoneme, script form, or rendering view |
| `portmanteau` | compact carrier of multiple category values |
| `residual` | omitted, ambiguous, repaired, or lossy evidence |
| `witness` | source, replay, hash, or negative-control evidence |

Required edge types:

| Edge Type | Meaning |
|---|---|
| `realizes` | category or payload becomes a surface form |
| `scopes` | one category controls another |
| `mutates` | surface or category changes by rule |
| `omits` | predictable material is not directly stored |
| `repairs` | sidecar/replay restores omitted or ambiguous material |
| `contrasts` | negative-control or minimal-pair evidence |
| `projects_to` | graph maps into an RRC lawful shape |

## 5. Ithkuil Starter Read

Ithkuil's useful eigenvector for this stack is:

```text
maximal semantic specificity
per minimal surface form
by projecting meaning through obligatory, typed, multi-axis morphology
where sound/script are compressed views over recoverable grammar
```

RRC adaptation:

```text
Ithkuil source descriptions
  -> category inventory
  -> semantic category portmanteau graph
  -> morpho-phonemic surface view
  -> omitted predictable material as replay law
  -> residual sidecar for ambiguity or unsupported categories
```

Use Ithkuil as a design precedent for category density. Do not copy protected
lexicon or glyph identity into payload identity. The useful extraction is the
density-marker set:

```text
multi-axis morphology
semantic category portmanteau
morpho-phonemic surface
prosodic metadata
```

## 6. RRC 16-Axis Projection

A language-set graph projects into the existing RRC axes:

```text
semantic_entropy
geometric_mass
compression_pressure
topology_torsion
receipt_density
field_energy
hardware_affinity
proof_readiness
residual_risk
shape_closure
history_depth
negative_control_strength
projection_declared
decoder_declared
witness_declared
scale_band_declared
```

Language-set specific readings:

| RRC Axis | Language-Set Meaning |
|---|---|
| `semantic_entropy` | category density and root ambiguity |
| `geometric_mass` | graph size, topology, and category connectivity |
| `compression_pressure` | byte pressure reduced by category bundling |
| `topology_torsion` | irregular mutation, exception, and ambiguity stress |
| `receipt_density` | source, hash, and replay evidence |
| `field_energy` | active category interactions |
| `hardware_affinity` | finite tables, bounded codes, and packet suitability |
| `proof_readiness` | formal schema and executable witnesses |
| `residual_risk` | omitted material or unsupported category drift |
| `shape_closure` | graph completeness under replay |
| `history_depth` | diachronic layers or versioned grammar history |
| `negative_control_strength` | contrastive examples and failure cases |
| `projection_declared` | graph-to-RRC mapping is explicit |
| `decoder_declared` | replay/decode path is explicit |
| `witness_declared` | source and receipt evidence is explicit |
| `scale_band_declared` | scope is bounded by corpus, grammar version, or slice |

## 7. Admission Gate

A language-set graph is CANDIDATE only when:

```text
source scope declared
+ category inventory declared
+ graph schema declared
+ replay/decoder declared
+ residual policy declared
+ negative controls declared
+ scale band declared
+ RRC receipt emitted
```

Otherwise it is HOLD.

QUARANTINE applies when:

```text
protected glyph identity is treated as payload
or source/cultural identity is erased
or replay mutates meaning without residual
or semantic tear is merged into ordinary token space
```

## 8. Byte Law

Promotion requires:

```text
B(graph law)
+ B(category inventory)
+ B(source/registry refs)
+ B(residual sidecar)
+ B(receipt)
< B(explicit token/phrase table)
```

If the graph is beautiful but not cheaper, it remains a documentation or routing
surface, not a compression promotion.

## 9. Starter Language-Set Manifest

```yaml
language_set_id: "LANG.ITHKUIL.DESIGN_PRECEDENT.0001"
source_scope: "public grammar descriptions and official documentation"
license_boundary: "extract category geometry only; do not copy lexicon/glyph identity"
density_markers:
  - multi_axis_morphology
  - semantic_category_portmanteau
  - morpho_phonemic_surface
  - prosodic_metadata
category_inventory:
  - root
  - stem
  - formative
  - adjunct
  - configuration
  - affiliation
  - perspective
  - case
  - validation
  - bias
  - tone
  - stress
node_types:
  - root
  - category
  - surface
  - portmanteau
  - residual
  - witness
edge_types:
  - realizes
  - scopes
  - mutates
  - omits
  - repairs
  - contrasts
  - projects_to
surface_views:
  - romanized examples
  - morpho-phonemic script descriptions
manifold_axes: "RRC 16-axis projection"
replay_law: "category bundle plus grammar table reconstructs predictable surface material"
residual_policy: "unsupported category, ambiguity, or copied glyph identity remains HOLD"
negative_controls:
  - "surface word without category inventory"
  - "glyph copied as payload"
  - "category bundle without replay law"
rrc_receipt: "LanguageSetManifoldGraph candidate only after replay evidence"
```

## 10. Implementation Anchors

Registry builder:

```text
4-Infrastructure/shim/language_set_manifold_registry.py
```

Registry outputs:

```text
shared-data/data/language_set_manifold_graph/language_set_registry.jsonl
shared-data/data/language_set_manifold_graph/language_set_graph_nodes.csv
shared-data/data/language_set_manifold_graph/language_set_graph_edges.csv
shared-data/data/language_set_manifold_graph/language_set_registry_receipt.json
```

LangChain splitter-derived expansion:

```text
LangChain Language enum / text splitter docs
  -> language-aware split boundary
  -> density marker candidate
  -> LanguageSetManifoldGraph packet
```

LangChain is not used as an authority on language semantics. It is used as a
pragmatic discovery surface: if a framework needs language-aware splitters for
Python, Java, C++, Markdown, LaTeX, HTML, Solidity, COBOL, and similar targets,
then those languages likely expose boundary markers that are worth typing as
density nodes.

RRC shim shape:

```text
4-Infrastructure/shim/rainbow_raccoon_compiler.py
```

Existing language-manifold prior:

```text
6-Documentation/papers/OTOM/17_Meta_Manifold_Language_Merging.md
6-Documentation/papers/OTOM/13_Language_as_Inverted_Manifold.md
```

Wiki card:

```text
6-Documentation/tiddlywiki-local/wiki/tiddlers/Language Set Manifold Graph Typing.tid
```
