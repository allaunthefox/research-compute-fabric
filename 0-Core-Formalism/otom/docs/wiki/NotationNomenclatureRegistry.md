# Research Notation and Nomenclature Registry

Status: HOLD / workbench projection
Authority: internal wiki spine; not canonical until validator and Lean receipts exist
Created: 2026-05-01

## Purpose

This document is the internal wiki registry for names, symbols, types, authority levels, and projection rules across the research stack.

It exists to prevent the same idea from being rediscovered under incompatible names.

The registry is not a proof. It is a routing surface. Promotion requires receipts.

```text
name -> type -> admissibility -> authority -> projection -> receipt
```

## Source surfaces indexed in this pass

This first pass aligns the following surfaces:

- Lean-style modules and specs: SSMS, SSMS_nD, NBody, Semantics, FixedPoint, NBody dynamics, manifold networking, compression/invariant modules.
- Graph surfaces: GraphML, Mermaid, knowledge graph projections, concept maps.
- Wiki surfaces: GCL/MN-GCL, Semantic Mass, admissibility closure, Ring0 gates, Research Wiki Hub.
- JSON-LD ontology: NUVMAP / MetaProbe / AngrySphinx / Forest Map / Delta GCL / FAMM / BioKernel / Great Filter CCR.
- Conversation-derived conceptual surfaces: GeoCognition, behavioral manifold, Ricci-flow/turbulence, semantic mass, Mass-Number theory, SNPAR, SETI/steganographic signal verification.

## Registry doctrine

```text
No term promotes itself.
No symbol proves itself.
No projection is canonical by default.
No emotional force, visual centrality, or graph weight counts as proof.
```

Every term must declare:

```ts
type RegistryEntry = {
  id: string;
  preferred_name: string;
  aliases: string[];
  symbol?: string;
  type_class: TypeClass;
  definition: string;
  allowed_claim_states: ClaimState[];
  authority_scope: AuthorityScope;
  canonical_surface?: string;
  projection_surfaces: string[];
  receipt_requirements: ReceiptRequirement[];
  blocked_usages: string[];
};
```

## Type classes

```ts
type TypeClass =
  | "Primitive"
  | "Operator"
  | "Metric"
  | "Gate"
  | "Manifold"
  | "Projection"
  | "Receipt"
  | "Protocol"
  | "Simulator"
  | "ClaimState"
  | "Policy"
  | "DangerBoundary";
```

## Claim states

Use these names everywhere.

```text
U_scope
  Unscoped or exploratory. May be useful, but not typed tightly enough.

HOLD
  Important, active, unresolved, not promoted.

V_scope
  Locally valid under an explicitly stated scope.

REVIEWED
  External or internal review exists and receipts are attached.

CANONICAL_LEAN
  Kernel-checked theorem/spec or machine-verifiable equivalent exists.

QUARANTINE
  Powerful, unsafe, overbroad, or likely to be misused without guardrails.
```

Never use `true`, `proven`, `obvious`, `validated`, or `real` as a claim state.

## Authority scopes

```text
workbench_projection
  Exploratory wiki/graph/language layer. Useful for orientation only.

simulation_only
  Implemented or visualized in code/sim, but not established as physical law.

receipt_backed
  Benchmarks, source audits, measurements, or reproducible traces exist.

canonical_lean
  Lean theorem/spec or typed formal artifact exists and builds without sorry.

external_source
  Imported from literature, standard math, public dataset, or external spec.

safety_policy
  Gate, refusal, ethics, privacy, or governance boundary.
```

## Core primitive registry

| ID | Preferred name | Aliases | Symbol | Type | Definition | Default state |
|---|---|---|---|---|---|---|
| `gcl` | Genetic Coding Language | GCL, deprecated alias: Grammar/Concept Language | `GCL` | Protocol | Genetic-code-inspired concept language for encoding research objects as typed, mutable, receipt-gated units with inheritance, mutation, recombination, repair, admissibility, projection, and formalization targets. | HOLD |
| `mn_gcl` | Mass-Number GCL | MN-GCL, MassNumber subset | `MN-GCL` | Protocol | Mass-Number subset/profile of Genetic Coding Language using typed expansion slots. | HOLD |
| `mass_number` | Mass Number | semantic mass number, mass index | `M#` | Primitive | Dimensionless semantic/accounting magnitude that may become route-cost evidence only after admissibility closure. | HOLD |
| `semantic_mass` | Semantic Mass | information mass, mass-like semantic pressure | `m_s` | Primitive | Dimensionless resistance/attraction/routing-cost feature; not SI physical mass. | HOLD |
| `nan_mass` | NaNMass | unresolved mass, infinite artifact | `NaN_M` | DangerBoundary | Typed unresolved mass state used when closure/accounting/admissibility fails. | HOLD |
| `closed_mass` | ClosedMass | admissible mass, receipt-backed mass | `M_cl` | Primitive | Finite mass value after closure receipt. | V_scope |
| `admissibility_closure` | Admissibility Closure | closure, closure gate | `Cl_A` | Operator | Turns raw mass-like pressure into pseudometric/quotient metric targets under constraints. | HOLD |
| `compatibility_kernel` | Compatibility Kernel | kernel K, admissibility kernel | `K_R(x,y)` | Metric | Regime-scoped compatibility between nodes under route/admissibility rules. | HOLD |
| `phi` | Phi potential | Φ, field potential, compression potential | `Φ` | Metric | Generic potential or invariant field; must be locally defined per module. | U_scope |
| `torsion` | Torsion | twist, mismatch, route torque | `τ` | Metric | Directional mismatch / twist / unresolved interface pressure. | HOLD |
| `route_cost` | Route Cost | traversal cost, adapter cost | `C_R` | Metric | Cost of moving a concept/state through a route or adapter chain. | HOLD |
| `receipt` | Receipt | evidence receipt, proof receipt | `ρ` | Receipt | Machine-readable evidence object tying a claim to source, theorem, benchmark, trace, or audit. | V_scope |

## Canonical non-identities

These are explicit category boundaries.

```text
mass_number != distance
semantic_mass != physical_mass
projection != proof
graph_centrality != truth
simulator_success != theorem
infinity_like != MassValue
emotional_intensity != evidence
LLM_agreement != validation
genotype != phenotype
mutation != validation
```

## GCL genetic-code doctrine

GCL borrows genetic-code architecture as an engineering pattern:

```text
symbols/codons -> typed expressions -> traits/phenotypes -> regime expression -> gate pressure -> repair/mutation -> receipts
```

Allowed analogy:

```text
codon-like slots
mutation/revision
recombination of concepts
repair pathways
expression under regimes
genotype/phenotype split
fitness under evidence gates
```

Forbidden overclaim:

```text
GCL is literal DNA.
GCL proves biology.
GCL proves claims by evolutionary language alone.
GCL mutations are valid because they are generative.
```

## MassValue type

Use this in GCL, MN-GCL, JSON, TypeScript, and future Lean mirrors.

```ts
type MassValue =
  | { tag: "FiniteMass"; value: number; unit: "dimensionless" }
  | { tag: "NaNMass"; reason: NaNMassReason; evidence: string[] }
  | { tag: "ClosedMass"; value: number; closure_receipt: string };

type NaNMassReason =
  | "division_by_unclosed_zero"
  | "unbounded_route_cost"
  | "missing_admissibility"
  | "regime_mismatch"
  | "infinite_projection_artifact"
  | "comparison_without_common_closure";
```

## Universe-local infinity rule

```text
Other universe:
  may permit completed infinity as a native object

This executable universe:
  requires finite thermodynamic accounting
  rejects infinity as MassValue
  routes infinity-like behavior to NaNMass
```

Use `NaNMass`, `LimitBoundary`, `QuotientBoundary`, or `RenormalizationCandidate`; do not use `InfiniteMass`.

## Formal notation rules

### Scalars

| Symbol | Name | Scope |
|---|---|---|
| `m_s` | semantic mass | dimensionless semantic/routing feature |
| `M#` | mass number | nuclide-inspired semantic/accounting index |
| `Φ` | potential | must be module-local unless explicitly universalized |
| `τ` | torsion/turbulence | interface mismatch; must declare which layer |
| `κ` | curvature | geometry/route curvature; not free metaphor |
| `ε` | epsilon floor | nonzero numerical/log boundary |
| `ρ` | receipt | proof/evidence object |
| `C_R` | route cost | route-scoped cost |
| `K_R` | compatibility kernel | regime-scoped compatibility |
| `d_θ` | closed distance | admissibility-closed distance target |

### Operators

| Symbol | Preferred name | Meaning |
|---|---|---|
| `bind(x,opt,metric)` | Bind | cognitive/load alignment operator |
| `Cl_A(x)` | Admissibility closure | closure under admissibility rules |
| `Q(x)` | Quotient | quotient by zero-distance/equivalence relation |
| `Π_P(x)` | Projection | projection to a rendering/surface, never proof |
| `R_G(x)` | RGFlow filter | scale-stability / attractor check |
| `W_P(x)` | WaveProbe | spectral/energy probe over a state |
| `Gate_R(x)` | Regime gate | safety/admissibility gate for regime R |

### Relations

| Symbol | Preferred name | Meaning |
|---|---|---|
| `x ~_A y` | admissibly equivalent | equivalent under admissibility relation A |
| `x ->_R y` | route transition | transition through route R |
| `x ⊢ ρ` | receipt-backed | x has receipt ρ |
| `x ⊣ Gate` | gate-held | x is blocked/held by gate |
| `x ⊘ R` | refused in regime | rejected by regime R |

## Name casing rules

```text
Lean namespaces/types: PascalCase
Lean functions/values: camelCase
Docs/wiki concepts: Title Case
Stable IDs: snake_case
Graph node IDs: kebab-case or snake_case, but do not mix in one graph
JSON-LD IDs: urn:<domain>:<type>:<name>:<version>
File paths: PascalCase for concept docs, snake_case for generated data
```

Examples:

```text
Concept: Semantic Mass
Stable ID: semantic_mass
Lean type: SemanticMass
Lean function: semanticMassCost
Graph node: semantic-mass
JSON-LD: urn:otom:concept:semantic-mass:v0.1
```

## Surface map

| Surface | Canonical role | Allowed contents | Forbidden contents |
|---|---|---|---|
| Lean | formal kernel | types, theorems, executable checks | hype, metaphors as proof |
| GitHub docs | durable spec | registry, schemas, theorem targets | uncited promotion |
| Notion wiki | navigation/workbench | glossary, status, routing, backlinks | final authority unless receipts exist |
| GraphML/Neo4j | relationship projection | nodes, edges, typed relations | proof by centrality |
| Mermaid | lightweight diagram | flows and doctrine maps | canonical semantics |
| Three.js/WebGPU | visual projection | rendered state, dynamic symbols | truth claims from visuals |
| JSON-LD | machine ontology | IDs, types, links, policies | vague untyped terms |
| Linear | execution tracker | issues, acceptance criteria, sync receipts | scientific proof itself |

## Major framework names

| Preferred name | Aliases | Definition | Notes |
|---|---|---|---|
| GeoCognition | geocognitive translation, geo-semantic translation | Meaning first represented as geometry, topology, route, pressure, flow, or manifold event before language. | Keep. |
| OTOM | Object Tracing on Manifolds, Object Model for Tracing Information | Publication-facing framing for tracing objects/information across manifolds. | Preferred over OMT for public docs. |
| OMT | Ontological Manifold Theory | Older conceptual name for manifold ontology. | Alias; avoid as public primary. |
| ENE | Endless Node Edges | Memory / topological storage substrate. | Define per repo/schema. |
| PTOS | Pipeline/Topological OS, traversal runtime | Runtime/ISA layer for traversal and routing. | Needs exact expansion lock. |
| GCL | Genetic Coding Language | Genetic-code-inspired concept language; deprecated alias: Grammar/Concept Language. | Canonical expansion corrected 2026-05-01. |
| MN-GCL | Mass-Number GCL | Mass-number subset/profile of Genetic Coding Language. | Keep. |
| SNPAR | Snapper | Snap/avalanche/reorganization model for entropy sorting/cognition. | HOLD pending formal type. |
| NUVMAP | Spectral pixel/state container | u/v spectral-albedo projection and wider JSON-LD approach. | Keep as container/ontology family. |
| WaveProbe | spectral probe | Energy/spectral probe and coarse-graining layer. | Keep. |
| RGFlow | lawfulness filter | Scale-stability / attractor / coarse-graining test. | Keep. |
| DIAT | Dual-Interval Algebraic Transform | Integers represented by distance to adjacent squares and related algebraic data. | Formalize separately. |
| AVMR | Algebraic Vector Mountain Range | Append-only hierarchical vector-state merge structure. | Formalize separately. |
| AMMR | Algebraic Merkle Mountain Range | Merkle-like algebraic commit/history structure. | Formalize separately. |
| AngrySphinx | refusal/containment layer | Allow-list-first, deny-by-default, receipt-writing gate layer. | Safety-critical. |
| FAMM | Failure/Attractor Memory Map | Stores scars/basins; repeated failures become routing constraints. | Needs acronym expansion lock. |

## Equation families

Every equation entry must declare:

```ts
type EquationEntry = {
  id: string;
  display: string;
  variables: VariableDecl[];
  domain: string;
  units: "dimensionless" | "SI" | "mixed" | "symbolic";
  source: "standard" | "derived" | "proposal" | "simulation";
  claim_state: ClaimState;
  receipt_refs: string[];
};
```

### Reserved equation families

| Family | ID prefix | Notes |
|---|---|---|
| Mass-number closure | `eq_mn_` | admissibility, compatibility, quotient closure |
| Compression | `eq_comp_` | CR, log-loss, arithmetic coding, Hutter targets |
| Geometry/topology | `eq_geo_` | manifolds, Ricci, curvature, geodesics |
| Dynamics | `eq_dyn_` | N-body, Hamiltonian, Verlet, flow |
| Signal | `eq_sig_` | WaveProbe, SETI, steganographic signal/noise |
| Governance/safety | `eq_gate_` | AngrySphinx, refusal, risk, thresholds |
| Biology/chemistry | `eq_bio_` | BioKernel, nitrogenase regression, OpenWorm |
| Cognition/load | `eq_cog_` | bind, routing load, dyscalculia route model, SNPAR |

## Projection discipline

A projection is a view of a formal object.

```text
canonical object -> projection -> human-readable view
```

Allowed projections:

```text
Lean -> theorem docs
JSON-LD -> ontology graph
GraphML -> Neo4j/topological map
Mermaid -> wiki diagram
Three.js/WebGPU -> dynamic symbol field
Notion -> navigation page
Linear -> issue/acceptance criteria
```

Blocked projection claims:

```text
"The graph says it is true."
"The symbol looks heavy, so it is high mass."
"The simulation converged, so the theorem holds."
"The LLM agrees, so it is validated."
```

## Receipt classes

```ts
type ReceiptRequirement =
  | "LeanTheorem"
  | "LakeBuild"
  | "Benchmark"
  | "Measurement"
  | "SourceAudit"
  | "DatasetRow"
  | "SimulationTrace"
  | "ExternalReview"
  | "SafetyGatePass"
  | "HumanApproval";
```

## Gate registry

| Gate | Symbol | Function |
|---|---|---|
| Ring0InternalAlarmGate | `Gate_R0` | Protects ring-0 cognition/trauma/load primitives from unsafe automatic expansion. |
| AngrySphinx | `Gate_AS` | Deny-by-default containment and refusal layer. |
| AdmissibilityGate | `Gate_A` | Blocks promotion until typed closure exists. |
| EvidenceGate | `Gate_ρ` | Blocks promotion until receipts exist. |
| ProjectionGate | `Gate_Π` | Blocks projection from being treated as proof. |
| SafetyScopeGate | `Gate_S` | Blocks unsafe or overbroad operationalization. |

## SETI/steganographic signal notation

Use this family for signal/noise work.

```text
S          signal candidate
N          noise / unresolved question
R          receiver regime
C          code/channel hypothesis
K_R        receiver/regime compatibility kernel
ρ_S        signal receipt
H0         null/noise hypothesis
H1         structured/source hypothesis
Λ(S)       likelihood or evidence ratio
Π_C(S)     projection under code hypothesis C
```

Doctrine:

```text
Noise is not garbage by default.
Noise is unresolved structure until the regime proves otherwise.
```

## Cognitive/load notation

Use this family for routing-load and geo-semantic translation.

```text
P          semantic packet
A_i        adapter/carrier
R          route
C_R(P)     route cost of packet P
τ_R(P)     turbulence on route R
bind       alignment operator
L_I        intrinsic load
L_G        germane load
L_R        routing load
L_E        extraneous load
L_M        memory load
```

Pipeline form:

```text
P_final = A_math ∘ A_language ∘ A_metaphor ∘ A_motion ∘ A_spatial(P_initial)
```

Do not pathologize the route. Treat alternate routing as architecture, then measure cost and loss.

## Lean naming target

Future Lean mirror should use:

```lean
namespace OTOM.Registry

inductive ClaimState
  | uScope
  | hold
  | vScope
  | reviewed
  | canonicalLean
  | quarantine

inductive AuthorityScope
  | workbenchProjection
  | simulationOnly
  | receiptBacked
  | canonicalLean
  | externalSource
  | safetyPolicy

inductive NaNMassReason
  | divisionByUnclosedZero
  | unboundedRouteCost
  | missingAdmissibility
  | regimeMismatch
  | infiniteProjectionArtifact
  | comparisonWithoutCommonClosure

inductive MassValue
  | finiteMass : Nat -> MassValue
  | nanMass : NaNMassReason -> MassValue
  | closedMass : Nat -> String -> MassValue

end OTOM.Registry
```

Actual numeric implementation should use fixed-point/integer representation, not Float, in hot paths.

## Promotion checklist

An entry may move beyond HOLD only when all apply:

- It has a stable ID.
- It has one preferred name.
- Aliases are recorded.
- Type class is declared.
- Authority scope is declared.
- Claim state is declared.
- Projection/canonical boundary is explicit.
- Receipts are listed or explicitly missing.
- Blocked usages are listed.
- If executable, it avoids Float in hot paths unless legacy or explicitly scoped.

## Immediate cleanup tasks

1. Create `registry/terms.jsonld` mirror from this table.
2. Create `registry/symbols.yaml` for custom symbol rendering.
3. Create `Semantics/Registry.lean` with claim-state and MassValue scaffolding.
4. Add validator rule: every wiki node must declare `claim_state`, `authority_scope`, and `receipt_refs`.
5. Create GraphML projection from this registry, but mark it `projection_only`.
6. Backfill existing docs: Semantic Mass, MN-GCL, SNPAR, NUVMAP, AngrySphinx, GeoCognition.

## Operating sentence

```text
The wiki is not a scrapbook. It is a typed routing surface from intuition to formal receipts.
```
