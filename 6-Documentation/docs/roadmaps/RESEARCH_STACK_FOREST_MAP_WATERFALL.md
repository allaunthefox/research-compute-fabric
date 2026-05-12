> **NOTE:** This roadmap has been superseded by [ROADMAP.md](../../6-Documentation/docs/roadmaps/ROADMAP.md). Retained for historical reference.

# Research Stack Forest Map Waterfall

```yaml
source_repo: allaunthefox/NoDupeLabs
source_issue: 68
source_title: "Waterfall: Complete the Research Stack Forest Map"
migration_reason: "Misplaced Research Stack roadmap/authority model; belongs in Research-Stack canonical planning docs."
target_repo: allaunthefox/Research-Stack
target_path: docs/roadmaps/RESEARCH_STACK_FOREST_MAP_WATERFALL.md
claim_state: ACTIVE_PLANNING
status: HOLD_UNTIL_CHILD_ISSUES_SPLIT
created_from: user-provided GitHub issue export
```

## Purpose

Create the broad-strokes execution plan for completing the entire Research Stack map: artifacts, equations, graphs, numeric motifs, gradient roads, torsion, FAMM memory, and private connector plumbing.

## Operating definition

The completed map is not a single visualization. It is a full epistemic pipeline:

```text
artifact / paper / equation / code / graph / note
→ normalization
→ fingerprint
→ graph/equation extraction
→ candidate roads
→ authority gate
→ Graph.lean canonical audit
→ graph diff / torsion / curvature
→ FAMM basin-hold-scar memory
→ Obsidian + Neo4j topological engine
→ Notion / Drive / Ace projections
```

## Authority hierarchy

| Authority | Role |
|---|---|
| Graph.lean | canonical graph authority |
| ENE | provenance / archive authority |
| Notion | semantic registry |
| Obsidian | local human-readable workbench mirror |
| Neo4j | private topology traversal/query engine |
| GraphML | transport |
| Mermaid | static projection |
| Ace | interactive projection |
| Consensus | external literature context only |
| Airtable | structured ops mirror |
| Google Drive | private searchable manifest/storage mirror |

## Completion philosophy

The goal is not to make the system agree with itself. The goal is to make the map expose where ideas, equations, and artifacts agree or disagree structurally.

A completed map must contain:

| Structure | Meaning |
|---|---|
| basins | repeated low-torsion stable route families |
| holds | useful but unresolved frontiers |
| scars | repeated invalid/high-torsion routes |
| degenerate flats | regions where parameter changes fail to affect curvature/torsion |
| light sources | external coordinate frames that illuminate without certifying |

---

# Phase 0 — Lock authority and substrate plumbing

## Deliverables

- [ ] Artifact Normalization Layer
- [ ] Graph Diff + Torsion Detector spec
- [ ] ENE private connector router
- [ ] Google Drive private ENE manifest
- [ ] Obsidian + Neo4j Topological Engine connector
- [ ] Mount ENE connector in private server
- [ ] Mount Topological Engine connector in private server
- [ ] Confirm private substrate connectors remain scoped to local/private access

## Acceptance criteria

- ENE health endpoint responds only in the intended private environment.
- Topological Engine health endpoint responds only in the intended private environment.
- Private substrate connectors are not exposed as public interfaces.
- Secrets are stored only in the intended secret-management environment.

---

# Phase 1 — Build canonical forest skeleton

## Goal

Create the minimum load-bearing map skeleton that everything else attaches to.

## Deliverables

- [ ] Graph.lean canonical Research Stack graph snapshot
- [ ] ForestGradientRoads.lean
- [ ] SemanticNumberPatternSearch.lean
- [ ] chemistry_physics_nspace_roads.lean
- [ ] Canonical node taxonomy
- [ ] Canonical edge taxonomy

## Canonical node taxonomy

```text
Artifact
Equation
Variable
Domain
Road
Motif
Source
LightSourceFrame
GraphSnapshot
Route
FAMMState
AuthorityBoundary
```

## Canonical edge taxonomy

```text
NORMALIZES_TO
HAS_FINGERPRINT
ROUTES_TO
WRITES_MEMORY
CONTAINS_EQUATION
USES_VARIABLE
SHARES_MOTIF
DERIVES_FROM
CONSTRAINS
PROJECTS_TO
TRANSPORTS_TO
ILLUMINATES
HAS_TORSION
HAS_OUTCOME
```

## Acceptance criteria

- Graph.lean can represent the core map without relying on GraphML, Mermaid, Neo4j, or Ace.
- Every projection preserves authority_scope, outcome, torsion, coherence, provenance_hash, source_of_truth, and quarantine_status.

---

# Phase 2 — Complete equation inventory by domain

## Goal

Turn weak equation regions into explicit equation packs.

## Current seed packs

- Chemistry–Physics N-Space Spine v0
- Geometry–Energy Core pack
- Dynamics / Coupled Oscillator / COUCH pack
- Information / Entanglement / Spacetime light-source pack
- Compression / Topology / Hutter route pack
- Statistical mechanics / probability landscape pack
- Optimization / Bayesian / decision-policy pack
- Materials / molecular descriptors / local density kernels pack

## Required equation pack fields

```yaml
name:
domain:
equation:
variables:
meaning:
authority:
proof_status:
outcome:
layer:
bind:
source_uri:
provenance_hash:
```

## Acceptance criteria

- Each equation pack includes all required fields.
- All new equation packs enter as HOLD unless canonicalized or independently verified.

---

# Phase 3 — Semantic Number Pattern Search

## Goal

Extract numeric motifs and prevent false-attractor pattern hallucination.

## Deliverables

- [ ] src/plumbing/semantic_number_pattern_search.ts
- [ ] numeric_motifs.json
- [ ] numeric_pattern_roads.json
- [ ] numeric_torsion_candidates.json
- [ ] false_attractor_report.json

## Required motif fields

```yaml
motif_id:
value:
normalized_form:
role:
operator_context:
equation_id:
equation_source:
domain:
authority:
provenance_hash:
perturbation_sensitivity:
baseline_frequency:
torsion:
outcome:
```

## False-attractor gates

- operator-context gate
- domain-context gate
- perturbation test
- randomized baseline
- source-independence check
- authority gate

## Acceptance criteria

- Raw numeric resemblance cannot create a basin.
- High-frequency + high-torsion motifs are flagged as false-attractor candidates.
- COUCH kappa degeneracy is detected as flat/degenerate if curvature does not respond to perturbation.

---

# Phase 4 — Fix COUCH coupling degeneracy

## Problem

Prior run indicated identical curvature across kappa regimes. That implies the coupling term or curvature metric is not actually responding to kappa.

## Target equation form

```text
xddot_i = -gamma xdot_i - omega_i^2 x_i - sum_j kappa_ij (x_i - x_j) + F_i(t)
```

## Deliverables

- [ ] Explicit kappa-dependent acceleration term
- [ ] Sweep kappa and compute curvature/torsion response
- [ ] Verify curvature responds under nontrivial coupling
- [ ] If still flat, isolate metric failure vs dynamics failure

## Acceptance criteria

- kappa perturbation changes trajectory and/or measured torsion in expected regimes.
- Flat result is classified as degeneracy, not basin.

---

# Phase 5 — Extract first verified basin candidate

## Target

Geometry–Energy Core.

## Candidate road

```text
configuration coordinate
→ scalar energy field
→ gradient force
→ dynamics
→ structural distribution
```

## Deliverables

- [ ] Compute torsion distribution over geometry-energy roads
- [ ] Compute curvature variance over repeated routes
- [ ] Compare against randomized baseline
- [ ] Require at least two independent sources or canonical support
- [ ] Promote only to candidate basin, not final truth

## Acceptance criteria

- mean torsion < threshold
- variance torsion < threshold
- baseline lift > threshold
- no projection-only load-bearing edges
- no quarantine boundary active
- repeatable under perturbation

---

# Phase 6 — Build torsion heatmap

## Goal

Visualize structural residuals across the forest.

## Deliverables

- [ ] torsion_heatmap.json
- [ ] Neo4j high-torsion query suite
- [ ] Obsidian report note
- [ ] Ace projection if available
- [ ] Notion registry summary

## Heatmap categories

| Category | Meaning |
|---|---|
| low torsion / repeated | basin candidate |
| moderate torsion / context | frontier hold |
| high torsion / repeated | scar candidate |
| zero-response perturbation | degenerate flat |

---

# Phase 7 — Batch ingest light-source corpus

## Goal

Use external papers as coordinate light sources, not proof authorities.

## Deliverables

- [ ] Consensus literature pulls by domain
- [ ] Paper equation extraction
- [ ] Candidate graph extraction
- [ ] Graph.lean draft conversion
- [ ] Diff against Research Stack graph
- [ ] FAMM HOLD/basin/scar writes

## Rule

```text
external paper → light source frame → candidate graph/equations → Graph.lean draft → diff/torsion → FAMM outcome
```

Never:

```text
paper similarity → direct basin
```

---

# Phase 8 — Neo4j topological traversal

## Goal

Use Neo4j as the private query engine for candidate roads.

## Deliverables

- [ ] Import Obsidian wikilinks
- [ ] Import equation packs
- [ ] Import motif roads
- [ ] Import FAMM state
- [ ] Query candidate basin/scar/frontier regions

## Required Cypher families

- high-torsion roads
- motif bridges
- light-source illumination paths
- low-torsion basin candidates
- degenerate flats
- orphan nodes / ungrounded roads

## Acceptance criteria

- Neo4j can propose candidate topology but cannot certify it.
- All proposed roads must return to Graph.lean / torsion / FAMM.

---

# Phase 9 — Closure criteria for complete map

The map is complete enough when:

- [ ] Every artifact source has an authority scope.
- [ ] Every graph representation has authority level.
- [ ] Every equation has domain, variables, source, and outcome.
- [ ] Every numeric motif has semantic role and operator context.
- [ ] Every route has cost, torsion, coherence, conflicts, and outcome.
- [ ] Every basin has repeatability and baseline support.
- [ ] Every scar is preserved as route memory.
- [ ] Every hold has a next action or is explicitly archived.
- [ ] No projection can become canonical.
- [ ] No unnormalized artifact can affect FAMM.
- [ ] No external paper can create a basin directly.

---

# Immediate next actions

1. Generate numeric_motifs.json from research-stack/equation-packs/chemistry_physics_nspace_spine_v0.json.
2. Generate numeric_pattern_roads.json.
3. Draft chemistry_physics_nspace_roads.lean.
4. Run the first positive test on geometry-energy roads.
5. Run the first negative test on COUCH kappa degeneracy.

---

# Migration note

This roadmap was originally recorded in allaunthefox/NoDupeLabs as issue #68. It belongs in Research-Stack because it defines the canonical forest-map authority model, execution phases, Graph.lean authority, FAMM memory layer, private ENE plumbing, Neo4j traversal engine, and projection rules for the research stack.

This imported copy should be treated as the canonical planning document unless superseded by child issues or more specific implementation artifacts.
