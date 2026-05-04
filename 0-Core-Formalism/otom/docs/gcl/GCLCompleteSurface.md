# GCL Complete Surface

Status: HOLD / workbench projection
Authority: onboarding and language-surface spec; not canonical proof
Related: `docs/gcl/MassNumberGCLSubset.md`, `docs/wiki/NotationNomenclatureRegistry.md`

## Canonical expansion

GCL means **Genetic Coding Language**.

Earlier drafts may describe GCL as "Grammar/Concept Language". Treat that as a deprecated explanatory alias, not the canonical expansion.

## One-sentence definition

GCL is a genetic-code-inspired concept language for encoding research objects as typed, mutable, receipt-gated units that can express inheritance, mutation, recombination, repair, admissibility, projection, and eventual formalization.

```text
intuition -> encoded concept genome -> expansion slots -> admissibility gates -> receipts -> projections -> formalization targets
```

## Plain-language definition

GCL stands for Genetic Coding Language.

It is not genetic code in the biological DNA-only sense.
It borrows the architecture of genetic coding:

```text
symbols become codons
codons become typed expressions
expressions become traits/phenotypes
traits interact with environments/regimes
bad mutations get gated
useful variants get preserved
verified variants get receipts
```

GCL is not a programming language in the ordinary sense.
It is not a proof assistant.
It is not a wiki by itself.
It is not a graph renderer.

GCL is the coding layer that says:

```text
What is the encoded unit?
What are its codons, symbols, and aliases?
What does it express as a phenotype/claim?
What regime or environment activates it?
What is allowed to count as evidence?
What mutations or recombinations are allowed?
What gates block promotion?
What surfaces may render it?
What formal target would eventually make it stronger?
```

The purpose of GCL is to prevent the research stack from dissolving into loose metaphor while preserving a generative, mutation-tolerant language for new mathematics and ontology.

## Why GCL exists

The research stack contains many different surfaces:

- Notion pages
- GitHub docs
- Lean modules
- JSON-LD ontology files
- GraphML / Neo4j / Mermaid graphs
- Three.js / WebGPU visualizations
- simulation traces
- Linear issues
- conversation-derived insights
- external datasets and papers

Without a shared genetic coding layer, the same object can appear under five different names and accidentally become five different claims.

GCL exists so that a research object has one preferred genotype and many controlled phenotypes/projections.

```text
one encoded genotype
  -> many aliases
  -> many phenotypes/projections
  -> one explicit authority boundary
```

## Core doctrine

```text
A GCL object is not true because it exists.
A GCL object is heritable, mutable, traceable, and gateable because it exists.
```

GCL does not prove claims.
GCL routes claims toward proof, receipts, simulation, quarantine, repair, mutation, or deletion.

## Biological analogy boundary

GCL uses biological coding as a structural analogy and engineering pattern.

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

## What GCL handles

GCL can represent:

- concepts
- symbols
- equations
- claims
- protocols
- gates
- simulations
- datasets
- projections
- receipts
- theorem targets
- unresolved residuals
- safety boundaries
- aliases and naming conflicts
- mutation/revision histories
- recombination paths
- repair pathways
- encoded symbol/codon slots

GCL should not represent vague vibes without typing. A vague intuition may enter GCL, but only as `U_scope` or `HOLD` until typed.

## The basic GCL object

A GCL object is an encoded, typed record.

```ts
type GCLObject = {
  gcl_id: string;
  preferred_name: string;
  aliases: string[];
  kind: GCLKind;
  claim_state: ClaimState;
  authority_scope: AuthorityScope;
  definition: string;
  genotype: GCLGenotype;
  expression: GCLExpression;
  expansion_slots: ExpansionSlots;
  receipts: ReceiptRef[];
  projections: ProjectionRef[];
  canonical_refs: CanonicalRef[];
  mutation_history: MutationRef[];
  blocked_usages: string[];
};
```

The minimum valid object must declare:

```text
gcl_id
preferred_name
kind
claim_state
authority_scope
definition
genotype or encoded-slot structure
projection/canonical boundary
```

If it does not declare those, it is not a valid GCL object yet.

## Genotype and phenotype

GCL separates internal encoding from outward expression.

```text
GCL genotype
  = internal typed code / slots / symbols / constraints

GCL phenotype
  = rendered expression / wiki page / graph node / theorem target / simulator behavior
```

This prevents a visual or verbal projection from being mistaken for the encoded object.

```text
genotype != phenotype
projection != proof
```

## GCL genotype sketch

```ts
type GCLGenotype = {
  codons: GCLCodon[];
  constraints: string[];
  allowed_mutations: string[];
  repair_paths: string[];
};

type GCLCodon = {
  codon_id: string;
  slot: keyof ExpansionSlots;
  symbol?: string;
  value: unknown;
  role: "name" | "type" | "metric" | "gate" | "receipt" | "projection" | "repair";
};
```

## GCL expression sketch

```ts
type GCLExpression = {
  active_regime: string;
  expressed_claims: string[];
  expressed_symbols: string[];
  projection_targets: string[];
  suppressed_traits: string[];
};
```

## GCL kinds

```ts
type GCLKind =
  | "concept"
  | "symbol"
  | "equation"
  | "claim"
  | "operator"
  | "metric"
  | "gate"
  | "protocol"
  | "simulator"
  | "dataset"
  | "receipt"
  | "projection"
  | "theorem_target"
  | "danger_boundary"
  | "mutation"
  | "repair_path"
  | "regime";
```

## Claim states

GCL uses explicit claim states so an exploratory idea cannot masquerade as proof.

```text
U_scope
  Unscoped or exploratory. Interesting but not tight enough yet.

HOLD
  Important but unresolved. Preserve it, but do not promote it.

V_scope
  Locally valid under an explicitly declared scope.

REVIEWED
  Review or audit receipts exist.

CANONICAL_LEAN
  Lean or equivalent formal receipt exists and builds.

QUARANTINE
  Unsafe, overbroad, misleading, or likely to cause category errors.
```

Default state for new concepts is `HOLD` unless clearly trivial or externally sourced.

## Authority scopes

```text
workbench_projection
  Useful for navigation, writing, and exploration only.

simulation_only
  Implemented in code or simulation, but not established as theorem or physical law.

receipt_backed
  Has benchmark, audit, dataset, trace, or source receipts.

canonical_lean
  Has formal theorem/spec receipts.

external_source
  Imported from standard math, external dataset, literature, or public spec.

safety_policy
  Gate or policy boundary.
```

Authority scope answers the question:

```text
Why is this allowed to influence decisions?
```

## Expansion slots

Expansion slots are GCL's codon-like fields.

Each subset can use the same object shell but fill different slots.

```ts
type ExpansionSlots = {
  symbolic_code?: SymbolicCodeSlot;
  semantic_profile?: SemanticProfileSlot;
  mass_profile?: MassProfileSlot;
  signal_profile?: SignalProfileSlot;
  geometry_profile?: GeometryProfileSlot;
  computation_profile?: ComputationProfileSlot;
  admissibility?: AdmissibilitySlot;
  closure?: ClosureSlot;
  projection?: ProjectionSlot;
  receipts?: ReceiptSlot;
  safety?: SafetySlot;
  mutation?: MutationSlot;
  repair?: RepairSlot;
};
```

An object does not need every slot. It only needs the slots required by its kind and subset.

## Core slots

### `slot.symbolic_code`

Stores symbols, notation, aliases, Unicode, LaTeX, SVG, font references, codon-like marks, and rendering rules.

Examples:

```text
M#
m_s
NaN_M
K_R(x,y)
Cl_A(x)
☸
```

### `slot.semantic_profile`

Stores meaning, aliases, ontology class, relation types, and human explanation.

### `slot.mass_profile`

Stores Mass-Number or Semantic Mass fields.

Used by MN-GCL.

```ts
type MassProfileSlot = {
  mass_value?: MassValue;
  semantic_density?: number;
  basin_strength?: number;
  torsion?: number;
  route_cost?: number;
};
```

### `slot.signal_profile`

Stores signal/noise/residual information.

Used by SETI-style residual verification, WaveProbe, and steganographic protocols.

### `slot.geometry_profile`

Stores manifold, topology, coordinate, curvature, graph, or CAD/shape-generation fields.

### `slot.computation_profile`

Stores executable representation, fixed-point policy, hot-path constraints, simulation hooks, and code references.

### `slot.admissibility`

Stores gates and conditions required before the object may be promoted.

```ts
type AdmissibilitySlot = {
  required_gates: string[];
  compatibility_kernel?: string;
  finite_counters?: string[];
  receipt_threshold?: string;
  lean_targets?: string[];
};
```

### `slot.closure`

Stores closure state and target.

```ts
type ClosureSlot = {
  status: "raw" | "held" | "closed" | "quotiented" | "reviewed";
  closure_operator?: string;
  equivalence_relation?: string;
  metric_target?: string;
};
```

### `slot.projection`

Stores where the object may be rendered.

Examples:

```text
Notion page
GitHub doc
Mermaid diagram
GraphML node
Neo4j node
Three.js/WebGPU visual
JSON-LD record
Linear issue
```

### `slot.receipts`

Stores proof/evidence references.

Examples:

```text
LeanTheorem
LakeBuild
Benchmark
Measurement
SourceAudit
DatasetRow
SimulationTrace
ExternalReview
SafetyGatePass
```

### `slot.safety`

Stores blocked usages, risk tags, safety scopes, and quarantine triggers.

### `slot.mutation`

Stores how a concept may change without identity loss.

```ts
type MutationSlot = {
  allowed_mutations: string[];
  forbidden_mutations: string[];
  mutation_receipts: string[];
};
```

### `slot.repair`

Stores how an invalid, NaN-like, or quarantined object may be repaired.

```ts
type RepairSlot = {
  repair_paths: string[];
  required_receipts: string[];
  quarantine_exit_conditions: string[];
};
```

## Subsets and profiles

A GCL subset is a constrained profile of Genetic Coding Language.

It does not replace GCL. It fills specific expansion slots and adds validation rules.

Known or planned subsets:

| Subset | Purpose |
|---|---|
| MN-GCL | Mass-Number / Semantic Mass / NaNMass / admissibility closure |
| Signal-GCL | Signal/noise/residual/steganographic/SETI verification |
| Geo-GCL | Geometry, topology, manifold, CAD, shape generation |
| Gate-GCL | Safety gates, Ring0, AngrySphinx, quarantine rules |
| Sim-GCL | Simulation objects, traces, parameters, status boundaries |
| Lean-GCL | Formal theorem/spec targets and proof receipts |
| Bio-GCL | Biological/codon/hachimoji/BioKernel translation layer |

## MN-GCL as example subset

MN-GCL is the Mass-Number subset of Genetic Coding Language.

It uses:

```text
slot.symbolic_code
slot.mass_profile
slot.admissibility
slot.closure
slot.projection
slot.receipts
slot.safety
slot.mutation
slot.repair
```

It adds the rule:

```text
Mass is not distance.
Mass becomes distance only through admissibility closure.
```

It also adds the finite-first rule:

```text
Infinity-like behavior is not a MassValue.
It routes to NaNMass until closure explains it.
```

## Projection/canonical boundary

GCL objects may be projected to many surfaces, but projections do not become proof.

```text
GCL object
  -> Notion page
  -> GitHub doc
  -> GraphML node
  -> Mermaid diagram
  -> Three.js/WebGPU render
  -> Linear issue
```

These are phenotypes/projections.

Canonical authority requires receipts.

```text
projection != proof
phenotype != genotype
visual centrality != truth
simulation convergence != theorem
LLM agreement != validation
```

## Receipts

A receipt is an attached evidence object.

```ts
type ReceiptRef = {
  receipt_id: string;
  receipt_type: ReceiptType;
  target_claim: string;
  source: string;
  status: "missing" | "present" | "failed" | "superseded";
};
```

Receipt types:

```ts
type ReceiptType =
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

## How a new idea enters GCL

When someone has a new idea, do not ask whether it is true first.
Ask how it is encoded and expressed.

```text
1. Name it.
2. Assign one preferred name.
3. Record aliases.
4. Declare kind.
5. Encode genotype/codons or expansion slots.
6. Declare expressed phenotype/claim.
7. Declare claim_state.
8. Declare authority_scope.
9. Fill required expansion slots.
10. Add blocked usages.
11. Attach receipts or mark receipts missing.
12. Route to projection, validation, repair, mutation, or quarantine.
```

## Example: Semantic Mass

```yaml
gcl_id: semantic_mass
preferred_name: Semantic Mass
aliases:
  - information mass
  - mass-like semantic pressure
kind: concept
claim_state: HOLD
authority_scope: workbench_projection
definition: >
  Dimensionless semantic/routing feature representing resistance, attraction,
  basin pressure, or route cost. It is not SI physical mass.
genotype:
  codons:
    - codon_id: SM_NAME
      slot: semantic_profile
      role: name
      value: Semantic Mass
    - codon_id: SM_MASS
      slot: mass_profile
      role: metric
      value: unresolved
blocked_usages:
  - Do not claim physical mass equivalence without SI mapping.
  - Do not treat graph centrality as proof of semantic mass.
expansion_slots:
  mass_profile:
    mass_value:
      tag: NaNMass
      reason: missing_admissibility
      evidence: []
  admissibility:
    required_gates:
      - EvidenceGate
      - AdmissibilityGate
  projection:
    allowed:
      - Notion
      - GitHubDocs
      - GraphML
      - Neo4j
      - Mermaid
```

## Example: Newtonian Superfluid Simulation

```yaml
gcl_id: newtonian_superfluid_simulation
preferred_name: Newtonian Superfluid Simulation
aliases:
  - emergent universe simulator
  - pulsating superfluid medium
kind: simulator
claim_state: HOLD
authority_scope: simulation_only
definition: >
  2D particle simulation using attraction, repulsion, damping, velocity caps,
  and boundary reflections as a visual sketch of a superfluid-like emergent medium.
blocked_usages:
  - Do not claim physical cosmology proof.
  - Do not claim empirical fluid validity without measurement receipts.
receipts:
  - type: SimulationTrace
    status: missing
projection:
  allowed:
    - GitHubDocs
    - ThreeJS
    - WebGPU
    - Wiki
```

## Example: NaNMass

```yaml
gcl_id: nan_mass
preferred_name: NaNMass
aliases:
  - unresolved mass
  - infinity-like mass failure
kind: danger_boundary
claim_state: HOLD
authority_scope: workbench_projection
definition: >
  Typed unresolved mass state used when an expression fails finite thermodynamic
  accounting, admissibility, regime compatibility, or closure.
blocked_usages:
  - Do not normalize to infinity.
  - Do not compare to finite mass without closure.
  - Do not promote as physical mass.
repair:
  repair_paths:
    - limit
    - renormalization
    - quotient
    - finite surrogate
    - quarantine
```

## Gate flow

```text
NEW_OBJECT
  -> GENOTYPE_ENCODING
  -> TYPE_ASSIGNMENT
  -> SLOT_FILL
  -> EXPRESSION_CHECK
  -> CLAIM_STATE_ASSIGNMENT
  -> AUTHORITY_SCOPE_ASSIGNMENT
  -> RECEIPT_CHECK
  -> ADMISSIBILITY_CHECK
  -> PROJECTION
  -> HOLD | V_SCOPE | REVIEWED | CANONICAL_LEAN | QUARANTINE
```

## Promotion rules

A GCL object can move from `HOLD` to `V_scope` only if:

- its scope is explicit
- its type is explicit
- its encoded slots are explicit
- its expressed phenotype/claim is explicit
- its blocked usages are explicit
- receipts required for that scope are present
- no gate rejects the promotion

A GCL object can move to `CANONICAL_LEAN` only if:

- Lean/formal artifact exists
- build succeeds
- theorem/spec target matches the claim
- no `sorry` or equivalent gap is being hidden

## Failure modes

GCL should catch these:

```text
alias drift
symbol drift
genotype/phenotype confusion
projection/proof confusion
simulation/proof confusion
raw mass treated as distance
infinity treated as MassValue
external source treated as internal proof
LLM agreement treated as evidence
unscoped metaphor promoted as law
mutation without receipt
missing receipt hidden by beautiful language
```

## Minimal validator requirements

A GCL validator should reject any object missing:

```text
gcl_id
preferred_name
kind
claim_state
authority_scope
definition
genotype or encoded slots
projection/canonical boundary
```

For subset objects, it should also reject missing subset-required slots.

For MN-GCL, reject if missing:

```text
mass_value
admissibility.status
claim_state
authority_scope
receipt list
blocked usages
repair path for NaNMass or quarantine states
```

## Relationship to the wiki

The internal wiki is a human-facing phenotype/projection of GCL.

A wiki page should be generated from or synchronized with a GCL object.

```text
GCL object -> wiki page
```

The reverse may be allowed during drafting, but only if the page is later parsed into a valid GCL object.

```text
wiki page -> draft GCL object -> validator -> registry
```

## Relationship to Lean

Lean is not required for every GCL object.

Lean is required when a claim becomes formal, mathematical, or promotion-critical.

GCL should produce Lean targets such as:

```text
definition target
theorem target
invariant target
counterexample target
boundedness proof
closure proof
quotient construction
```

## Relationship to JSON-LD

JSON-LD is the machine-ontology transport surface.

A GCL object should be serializable as JSON-LD:

```json
{
  "@id": "urn:otom:gcl:concept:semantic-mass:v0.1",
  "@type": "GCLConcept",
  "preferredName": "Semantic Mass",
  "claimState": "HOLD",
  "authorityScope": "workbench_projection"
}
```

## Relationship to GraphML and Neo4j

GraphML/Neo4j represent relationships between objects.

They may show:

```text
requires
blocks
aliases
projects_to
has_receipt
is_subset_of
routes_through
is_quarantined_by
mutates_to
repairs_to
expresses
inherits_from
```

They may not assert truth by graph structure alone.

## Relationship to Three.js/WebGPU

Three.js/WebGPU may render dynamic symbols, manifold fields, mass-like visual weights, torsion, and basin structure.

This is a projection/phenotype.

```text
rendered mass-looking object != mass proof
```

## GCL complete surface summary

GCL has seven jobs:

```text
1. Encode things.
2. Name things.
3. Type things.
4. Express things.
5. Gate things.
6. Route things.
7. Preserve receipts.
```

It does not have one job:

```text
It does not declare things true by existing.
```

## Operating sentence

```text
GCL is the Genetic Coding Language that lets strange research objects mutate, recombine, and express themselves without letting them skip typing, receipts, gates, repair, or closure.
```
