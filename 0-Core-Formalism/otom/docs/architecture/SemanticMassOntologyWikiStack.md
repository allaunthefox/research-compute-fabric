# Semantic Mass Ontology Wiki Stack

## Purpose

This note defines a custom knowledge/wiki stack for a geometric ontology where semantic information is treated as dimensionless physical mass.

The wiki is not merely a text repository. It becomes a dynamic manifold engine that stores, queries, visualizes, and audits semantic mass, density, gravity, basins, symbolic morphology, and law-like concept interactions.

## Core Statement

```text
Standard wiki = flat text + links
Semantic-mass wiki = weighted manifold + typed physical interactions + dynamic graph state
```

The stack must support:

```text
semantic mass variables
weighted links
basin formation
typed interaction edges
dynamic graph layout
symbol morphology
frontmatter receipts
triple-store export
local-first markdown
formal audit boundaries
```

## Layer 1: Local Knowledge Substrate

Recommended base:

```text
Obsidian vault or local Markdown vault
```

Every concept, theorem, variable, object, or operator receives frontmatter.

Example:

```yaml
title: Semantic Mass
kind: concept
status: U_scope
mass_number: 0.87
semantic_density: 0.72
basin_strength: 0.64
torsion: 0.18
claim_state: BEAUTIFUL_PROVISIONAL
receipts:
  - DefinitionReceipt
  - MetricReceipt
links_out:
  - target: FAMM
    predicate: exerts_gravitational_pull_on
    weight: 0.81
  - target: InvertedFAMM
    predicate: reveals_negative_space_in
    weight: 0.66
```

## Layer 2: Semantic Gravity and Basins

Standard wiki links treat all page-to-page relations as equal. Semantic-mass ontology requires weighted edges.

Node variables:

```text
mass_number
semantic_density
basin_strength
torsion
route_cost
receipt_coverage
validator_coverage
claim_state
```

Graph behavior:

```text
high mass_number -> anchor node
high density -> local compression kernel
high basin_strength -> stable attractor
high torsion -> unresolved edge stress
low receipt_coverage -> promotion block
```

Force-directed graph mapping:

```text
attraction(A,B) = edge_weight(A,B) * mass_number(A) * mass_number(B)
repulsion(A,B) = torsion(A,B) + ontology_conflict(A,B)
layout_energy = attraction - repulsion - routing_cost
```

## Layer 3: Ontological Links as Physical Law Edges

Hyperlinks are insufficient. Links must be typed interactions.

Use subject-predicate-object triples:

```text
Subject -- Predicate -- Object
```

Examples:

```text
Semantic Mass -- exerts_gravitational_pull_on -- FAMM Basin
Anti-Music -- destabilizes -- Stable Harmonic Attractor
AMREF -- filters -- Music-Like Carrier
Inverted FAMM -- infers -- Missing Law Pressure
Fermat Shell Descent -- constructs -- Coordinate Witness
```

Predicates should be specific:

```text
exerts_gravitational_pull_on
stabilizes
compresses
routes_into
fractures
reveals_negative_space_in
requires_receipt
blocks_promotion_of
generates_candidate_for
```

## Layer 4: Dynamic Symbol System

If a symbol represents mass, density, or thermodynamic work, its rendered form should be allowed to vary by parameter.

Implementation options:

```text
SVG injection for dynamic symbols
Typst macros for parameterized math operators
KaTeX/MathJax macros for lightweight display
script-generated symbol variants for graph overlays
```

Example symbolic policy:

```text
stroke_width(symbol) = base_width + alpha * mass_number
inner_complexity(symbol) = floor(beta * semantic_density)
opacity(symbol) = receipt_coverage
outline_torsion(symbol) = torsion
```

Meaning:

```text
heavier concepts visibly render heavier
higher-density concepts render more compressed/complex
unverified concepts render with lower confidence opacity
high-torsion concepts display edge distortion or warning halos
```

## Layer 5: Query Engine

Minimum viable query layer:

```text
Obsidian Dataview
local scripts over Markdown frontmatter
Neo4j export for graph queries
RDF/Turtle or JSON-LD export for semantic triples
```

Example queries:

```text
Find nodes with mass_number > 0.8 and receipt_coverage < 0.5
Find high-torsion edges touching V_scope claims
Find concepts exerting gravitational pull on AMREF
Find route basins where claim_state is not REVIEWED
Find U_scope nodes with high basin_strength and missing ValidatorReceipt
```

## Layer 6: Graph Database / Manifold Backend

Recommended evolution:

```text
Markdown vault -> JSON-LD export -> Neo4j/RDF graph -> visualization engine
```

Suggested graph schema:

```text
(:Concept {mass_number, density, torsion, claim_state})
(:Theorem {proof_state, lean_file, receipts})
(:Operator {domain, codomain, energy_cost})
(:Receipt {type, status, source})
(:EdgeLaw {predicate, weight, confidence, failure_mode})
```

Relationship examples:

```cypher
(:Concept)-[:EXERTS_GRAVITY {weight: 0.81}]->(:Concept)
(:Theorem)-[:REQUIRES_RECEIPT]->(:Receipt)
(:Operator)-[:DESTABILIZES]->(:Attractor)
(:Concept)-[:ROUTES_THROUGH {cost: 0.33}]->(:Concept)
```

## Layer 7: Audit Gating

A semantic-mass wiki must not allow high-mass concepts to become automatically trusted.

Promotion gates:

```text
U_scope -> obligation map only
HOLD -> coherent but receipt-deficient
V_scope -> receipts present and validator accepted
REVIEWED -> external or formal review complete
QUARANTINE -> adversarial shortcut / noise / failed audit
```

High mass with low receipts is dangerous:

```text
high mass_number + low receipt_coverage = gravitational hallucination risk
```

Required mitigation:

```text
increase validator pressure
add explicit receipt list
decrease graph promotion weight
mark as high-priority proof obligation
```

## Layer 8: Recommended Stack

### Minimal local stack

```text
Obsidian
Markdown frontmatter
Dataview
Juggl or graph plugin
Git version control
Python scripts for graph export
```

### Research-grade stack

```text
Obsidian vault
Typst for theorem/report rendering
JSON-LD as canonical graph exchange
Neo4j for relationship queries
Mermaid/GraphML for projections
Lean for theorem gates
GitHub for evidence receipts
Linear for task routing
Notion for human-facing project docs
```

### High-end dynamic stack

```text
local Markdown vault
custom symbolic SVG renderer
Neo4j or RDF triplestore
WebGPU/Canvas graph visualization
force-directed semantic gravity layout
receipt-aware graph routing
FAMM/Inverted FAMM update loop
```

## Architecture Rule

```text
Graph.lean = canonical law core
GraphML / JSON-LD = transport layer
Mermaid / Obsidian graph / Neo4j browser = projection layer
```

Do not confuse projection with canon.

## Wiki Behavior Requirements

The wiki should support:

```text
weighted concept gravity
basin discovery
typed semantic triples
frontmatter receipts
dynamic symbol rendering
claim-state gating
route-cost queries
negative-space search
formal proof links
empirical measurement links
```

It should not treat:

```text
all links as equal
all concepts as flat text
all visuals as evidence
high graph centrality as proof
unverified high-mass concepts as REVIEWED
```

## Side-Quest Implementation Plan

```text
1. Define canonical frontmatter schema.
2. Build sample pages for Semantic Mass, FAMM, Inverted FAMM, AMREF, Fermat Shell Descent.
3. Write Markdown -> JSON-LD exporter.
4. Write JSON-LD -> Neo4j importer.
5. Add graph layout weights from mass_number and torsion.
6. Add receipt coverage and claim-state overlays.
7. Add symbol renderer for dynamic SVG mass glyphs.
8. Add queries for high-mass/low-receipt danger zones.
9. Wire Linear issues to missing receipt nodes.
10. Keep Lean theorem receipts as the promotion boundary.
```

## Boundary

Do not claim:

```text
semantic mass is SI physical mass
visual mass proves mathematical truth
graph centrality proves ontological priority
wiki topology replaces formal validation
```

Allowed claim:

```text
A semantic-mass ontology wiki can model concepts as dimensionless weighted graph objects whose interactions, basins, and proof obligations are queried and visualized using mass-like variables while remaining receipt-gated.
```

## Audit Classification

```text
Receipt: SemanticMassOntologyWikiStack
Status: ARCHITECTURE_DRAFT
Gate: U_scope
Reason: coherent as an infrastructure design, but requires schema implementation, exporter/importer code, graph validation, receipt wiring, and formal claim-state boundaries.
```

## Required Receipts

```text
FrontmatterSchemaReceipt
TriplePredicateReceipt
MassNumberMetricReceipt
GraphExportReceipt
Neo4jImportReceipt
DynamicSymbolReceipt
ClaimStateGateReceipt
ReceiptCoverageReceipt
LinearTaskRoutingReceipt
LeanTheoremLinkReceipt
```
