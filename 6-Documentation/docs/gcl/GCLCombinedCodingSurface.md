# GCL Combined Coding Surface

Status: HOLD / surface assignment map
Authority: workbench synthesis; not canonical proof
Related:

- `docs/gcl/GCLCompleteSurface.md`
- `docs/gcl/MassNumberGCLSubset.md`
- `docs/gcl/CompressionDeltaPhiGammaLambdaDoctrine.md`
- `docs/gcl/MassNumberSurfaceTranslation.md`
- `docs/gcl/SidonPhysicsNativeDeconstruction.md`
- `docs/gcl/SidonSolvedDomainTestProtocol.md`
- `docs/gcl/EquationForestActiveKernels.md`
- `docs/wiki/NotationNomenclatureRegistry.md`
- `data/cff/provenance-database.yml`

## Purpose

This document pulls the stack's variants of genetic, synthetic, symbolic, algorithmic, and surface coding into one combined GCL surface.

GCL means **Genetic Coding Language**.

GCL is the host grammar. The variants below are not competing languages. They are coding regimes that fill different GCL slots, emit different phenotypes, and require different gates.

```text
coding variant
  -> GCL genotype slots
  -> expressed phenotype
  -> admissibility / closure gates
  -> projection surface
  -> receipt target
```

## Core rule

```text
Every coding system that enters GCL must declare:

1. what its symbols are,
2. what counts as a codon / token / unit,
3. what phenotype or expression it produces,
4. what mutation means,
5. what recombination means,
6. what counts as repair,
7. what gates promotion,
8. what surface renders it,
9. what receipt would validate it,
10. what adversarial counter-surface must be survived before promotion.
```

## Claim boundary

Allowed claim:

```text
Different coding regimes can be mapped onto one GCL surface because they share
structure: encoded units, expression rules, mutation paths, repair paths,
projection boundaries, and receipts.
```

Blocked claim:

```text
All coding regimes are biologically equivalent.
```

GCL uses biological coding as an architectural analogy and engineering pattern. It does not claim that every code is DNA.

## Combined surface slots

The combined GCL surface uses the existing expansion slots from the GCL complete surface.

```text
slot.symbolic_code
slot.semantic_profile
slot.mass_profile
slot.signal_profile
slot.geometry_profile
slot.computation_profile
slot.admissibility
slot.closure
slot.projection
slot.receipts
slot.safety
slot.mutation
slot.repair
slot.adversarial_convergence
```

## Variant assignment table

| Variant | Canonical GCL assignment | Symbol/codon unit | Phenotype / expression | Primary slots | Gate |
|---|---|---|---|---|---|
| Biological DNA/RNA coding | Bio-GCL external-source analogue | nucleotide triplet / codon | amino acid / protein / regulatory behavior | symbolic_code, signal_profile, computation_profile, mutation, repair | external evidence; no direct internal truth promotion |
| Synthetic genetic coding | Bio-GCL synthetic-code analogue | engineered codon / expanded alphabet unit | engineered expression / programmable biological behavior | symbolic_code, computation_profile, safety, mutation, repair | biosafety + source receipts |
| Hachimoji / expanded-base coding | Bio-GCL expanded alphabet profile | 8-symbol synthetic base alphabet / expanded codon | higher alphabet-capacity biological-like encoding | symbolic_code, signal_profile, computation_profile | source audit + no overclaim gate |
| Stack-native GCL | Host grammar | GCLCodon / expansion slot | typed concept object / claim / projection | all slots | GCL validator |
| MN-GCL | Mass-Number subset | mass-profile codon / symbolic marker | Mass Number / Semantic Mass / NaNMass state | symbolic_code, mass_profile, admissibility, closure, receipts, repair | finite-first closure gate |
| Signal-GCL | Signal/residual subset | sample / residual / probe unit | WaveProbe / signal packet / residual trace | signal_profile, receipts, projection, safety | measurement receipt gate |
| Geo-GCL | Geometry/topology subset | coordinate / simplex / graph cell / Goxel | surface / manifold / CAD / topology projection | geometry_profile, projection, closure | surface anchor + reverse collapse |
| Gate-GCL | Safety and promotion subset | gate token / policy marker | HOLD / QUARANTINE / V_scope / block state | admissibility, safety, receipts, repair | Warden gate |
| Sim-GCL | Simulation subset | parameter / trace / state packet | toy model / simulator behavior / run trace | computation_profile, signal_profile, receipts, projection | simulation-only authority gate |
| Lean-GCL | Formal target subset | definition / theorem / invariant / counterexample | Lean module / theorem target / build receipt | computation_profile, closure, receipts, admissibility | lake build + no hidden gaps |
| BioKernel / peptide mechanics | Bio-GCL + Sim-GCL bridge | codon / amino acid / kinetic window | cotranslational bias / folding toy model | signal_profile, computation_profile, receipts | empirical boundary + simulation receipt |
| Algorithmic source code | Algo-GCL profile | function / class / import / constant / AST node | executable behavior / refactor candidate | computation_profile, mutation, repair, receipts | test + semantic equivalence gate |
| AVM bytecode / nanokernel coding | Kernel-GCL profile | instruction / fixed-point atom / state transition | deterministic step / orchestration unit | computation_profile, safety, receipts, closure | fixed-point + determinism gate |
| WebGPU / shader coding | Surface-runtime GCL profile | buffer / kernel / shader invocation | visual surface / compute projection | computation_profile, geometry_profile, projection | F32 render-only boundary gate |
| Repository memory cards | Repo-GCL profile | path card / file hash / onboarding record | drift-aware agent context | semantic_profile, receipts, mutation, repair | hash staleness gate |
| ISO-language GCL experiment | Language-GCL experimental profile | registry row codon / motif macro / APN address | language packet / RGFlow observation | symbolic_code, semantic_profile, signal_profile, projection | experimental-only gate |
| Sidon coding | Sidon-GCL collision-law profile | pair path / sum address / history hash | lawful alias or collision packet | symbolic_code, closure, safety, receipts | no incompatible same-address history gate |
| Mass Number process coding | Cognitive-GCL profile | modeling-step codon / invariant field | compressed reasoning packet | semantic_profile, mass_profile, projection, receipts | reverse-collapse gate |
| Cultural / ritual coding | Culture-GCL profile | symbol / gesture / ritual step / social token | transmitted meaning / performance invariant | semantic_profile, signal_profile, projection, mutation | interpretation must name carrier + invariant |
| JSON-LD ontology coding | Ontology-GCL transport | `@id` / `@type` / relation tuple | machine-readable object registry | semantic_profile, projection, receipts | schema validity gate |
| GraphML / Neo4j coding | Graph-GCL transport | node / edge / relation label | relationship graph phenotype | semantic_profile, projection, receipts | graph centrality is not truth gate |
| Mermaid coding | Diagram-GCL projection | node / edge / flow unit | human-readable diagram phenotype | projection, semantic_profile | projection-not-proof gate |
| Equation forest coding | Kernel-GCL registry profile | kernel entry / hyper-term bucket | routable equation-family object | symbolic_code, computation_profile, admissibility | registry typing gate |
| Adversarial convergence coding | Warden-GCL dialectical audit profile | thesis / contra-surface / surviving concession / synthesis | adversarial_convergence, safety, receipts, admissibility | no unopposed synthesis promotion |
| Underverse coding | Failure-GCL profile | invalid residue / blocked path / shadow packet | quarantine / snip / repair candidate | safety, repair, receipts, projection | Warden quarantine gate |

## Surface interpretation

The combined GCL surface is not one flat table of names.

It is a layered surface where every coding variant lands on shared operations:

```text
encode
express
mutate
recombine
repair
gate
project
receipt
oppose
synthesize
```

Different variants emphasize different operations.

```text
Biological code:
  mutation, expression, redundancy, repair

Synthetic code:
  engineered alphabet, controlled expression, safety boundary

Algorithmic code:
  executable behavior, refactor, tests, semantic equivalence

Mass Number code:
  invariant compression, admissibility closure, reverse collapse

Sidon code:
  lawful aliasing, collision detection, same-address history safety

Surface code:
  projection, inspection, probe, receipt display

Adversarial convergence code:
  thesis, contra-surface, surviving phi, failure residue, earned confidence
```

## GCL host grammar

A combined GCL object should use this host form:

```ts
type CombinedGCLCodingObject = {
  gcl_id: string;
  preferred_name: string;
  aliases: string[];
  coding_variant: CodingVariant;
  kind: GCLKind;
  claim_state: ClaimState;
  authority_scope: AuthorityScope;
  definition: string;
  genotype: GCLGenotype;
  expression: GCLExpression;
  expansion_slots: ExpansionSlots;
  gates: GateRef[];
  receipts: ReceiptRef[];
  projections: ProjectionRef[];
  mutation_history: MutationRef[];
  repair_paths: RepairRef[];
  adversarial_convergence?: AdversarialConvergencePass;
  blocked_usages: string[];
};
```

## Coding variant enum

```ts
type CodingVariant =
  | "biological_dna_rna"
  | "synthetic_genetic"
  | "hachimoji_expanded_alphabet"
  | "stack_native_gcl"
  | "mn_gcl"
  | "signal_gcl"
  | "geo_gcl"
  | "gate_gcl"
  | "sim_gcl"
  | "lean_gcl"
  | "bio_kernel"
  | "algorithmic_source"
  | "avm_bytecode"
  | "nanokernel_orchestration"
  | "webgpu_shader"
  | "repository_memory"
  | "language_registry_gcl"
  | "sidon_collision_law"
  | "mass_number_process"
  | "cultural_ritual"
  | "jsonld_ontology"
  | "graphml_neo4j"
  | "mermaid_projection"
  | "equation_forest_registry"
  | "adversarial_convergence"
  | "underverse_failure";
```

## Compression mapping

The combined surface exists because all coding regimes can be read as compression systems.

```text
compression = collapse with accountability
```

GCL asks:

```text
What phi survives?
What delta is introduced?
Under what gamma pressure?
At what lambda scale?
Can the object reverse-collapse?
Did histories alias lawfully?
What did Warden receipt?
What adversarial counter-surface did it survive?
```

Variant-specific compression roles:

| Variant family | Compression role | Failure mode |
|---|---|---|
| Biological / synthetic | controlled degeneracy and mutation tolerance | phenotype drift / unsafe expression |
| Stack-native GCL | typed concept compression | metaphor promoted without receipts |
| MN-GCL | process/mass/invariant compression | raw mass treated as metric before closure |
| Signal-GCL | residual compression | signal/noise confusion |
| Geo-GCL | shape/surface compression | projection mistaken for proof |
| Algorithmic-GCL | executable behavior compression | AST similarity mistaken for semantic equivalence |
| Sidon-GCL | address collapse with lawful aliasing | incompatible histories share one address |
| Adversarial-Convergence-GCL | truth-claim compression under opposition | unopposed synthesis / no surviving phi |
| Lean-GCL | formal compression | theorem target does not match claim |
| Underverse-GCL | failure compression | failure language recursively explains itself |

## Controlled degeneracy rule

Biology does not use pure uniqueness. Biology uses controlled degeneracy.

GCL should therefore not require that every encoding be unique.

It should require:

```text
No incompatible histories may collapse into the same committed address.
```

Allowed alias:

```text
different encodings
  -> same invariant phi
  -> same authority boundary
  -> reverse-collapse or repair path exists
  -> receipt records the alias rule
```

Blocked alias:

```text
different encodings
  -> same address
  -> incompatible history
  -> no reverse-collapse
  -> no alias policy
```

This is the bridge between Bio-GCL degeneracy and Sidon-GCL collision law.

## Adversarial convergence pass

Adversarial convergence is not a new truth source. It is a Warden-side dialectical pressure test for any GCL claim, operator, collapse, analogy, or source import.

```text
candidate claim
  -> positive case
  -> strongest contra-surface
  -> surviving phi
  -> failure residue
  -> bounded synthesis
  -> Warden state
```

Use this mapping:

| Symbol | Adversarial convergence meaning |
|---|---|
| `Δ` | what changed after adversarial pressure |
| `φ` | the claim, invariant, or concession that survives both sides |
| `γ` | adversarial pressure: counterargument strength, evidence conflict, stakes |
| `λ` | scale: sentence, claim, file, module, theory, corpus, policy domain |

Operational test:

```text
At scale λ, under adversarial pressure γ, what φ survives,
and what Δ residue must Warden record?
```

Required object shape:

```ts
type AdversarialConvergencePass = {
  positive_case: string;
  contra_surface: string;
  surviving_phi: string;
  delta_residue: string;
  gamma_pressure: "low" | "medium" | "high" | "extreme";
  lambda_scale: string;
  synthesis: string;
  warden_status: "DRAFT" | "HOLD" | "CANDIDATE" | "BLOCK" | "REVIEWED";
  source_receipts: string[];
};
```

The pass belongs in Receipt-Space / Warden-Space, not in the canonical coding substrate.

```text
AC is not the geometry.
AC is how Warden interrogates the geometry.
```

## GCL subset assignment

### Bio-GCL

Purpose:

```text
Map biological and synthetic coding concepts into GCL without overclaiming biological equivalence.
```

Primary slots:

```text
slot.symbolic_code
slot.signal_profile
slot.computation_profile
slot.mutation
slot.repair
slot.safety
slot.receipts
```

Required boundary:

```text
Bio-GCL analogy is structural unless external biological receipts exist.
```

### MN-GCL

Purpose:

```text
Map Mass Numbers, Semantic Mass, NaNMass, route cost, torsion, and admissibility closure.
```

Primary slots:

```text
slot.symbolic_code
slot.mass_profile
slot.admissibility
slot.closure
slot.projection
slot.receipts
slot.safety
slot.repair
```

Required boundary:

```text
Mass is not distance. Mass becomes distance only through admissibility closure.
```

### Sidon-GCL

Purpose:

```text
Map controlled degeneracy and lawful aliasing as a collision-law surface.
```

Primary slots:

```text
slot.symbolic_code
slot.computation_profile
slot.admissibility
slot.closure
slot.safety
slot.receipts
```

Required boundary:

```text
No incompatible pair-history collision may survive at a committed address.
```

### Algorithmic-GCL

Purpose:

```text
Map executable code into concept genes: files, functions, classes, constants,
imports, tests, invariants, and refactor candidates.
```

Primary slots:

```text
slot.computation_profile
slot.semantic_profile
slot.mutation
slot.repair
slot.receipts
slot.safety
```

Required boundary:

```text
AST similarity is suspicion, not semantic equivalence.
```

### Adversarial-Convergence-GCL

Purpose:

```text
Map thesis/contra/synthesis reasoning into a bounded Warden audit pass so that
new claims are not promoted merely because they are fluent, coherent, or pretty.
```

Primary slots:

```text
slot.adversarial_convergence
slot.safety
slot.receipts
slot.admissibility
slot.repair
```

Required boundary:

```text
No adversary, no earned confidence.
No surviving phi, no promotion.
```

### Surface-GCL

Purpose:

```text
Map GCL objects into visible surfaces: WasmGPU, Three.js, GraphML, Mermaid,
Neo4j, Notion, GitHub docs, and Linear issues.
```

Primary slots:

```text
slot.geometry_profile
slot.signal_profile
slot.projection
slot.receipts
slot.safety
```

Required boundary:

```text
projection != proof
phenotype != genotype
visual centrality != truth
```

### Underverse-GCL

Purpose:

```text
Map failures, invalid aliases, unclosed infinities, broken reverse-collapse paths,
and unsafe overclaims into bounded residue packets.
```

Primary slots:

```text
slot.safety
slot.repair
slot.receipts
slot.projection
```

Required boundary:

```text
Failure must be receipted, not hidden in active surface language.
```

## Minimal combined validator

A combined GCL validator should reject any object that lacks:

```text
gcl_id
preferred_name
coding_variant
kind
claim_state
authority_scope
definition
symbol/codon/unit declaration
expression/phenotype declaration
projection/canonical boundary
blocked usages
```

It should also reject:

```text
biological analogy promoted as biological evidence
projection promoted as proof
AST similarity promoted as semantic equivalence
same-address alias without alias policy
recursive abstraction without reverse collapse
raw infinity promoted as MassValue
float canonical values in hot-path computation profiles
unopposed synthesis promoted as earned confidence
bounded synthesis promoted without surviving phi
```

## Warden rules

```text
if coding_variant == biological_dna_rna
and authority_scope != external_source
and claim uses biological fact language:
  emit UnderversePacket.bio_overclaim
  block promotion
```

```text
if coding_variant in {synthetic_genetic, hachimoji_expanded_alphabet}
and external source receipts are missing:
  mark HOLD
  require SourceAudit
```

```text
if two encoded histories share committed_address
and alias_policy == null:
  emit UnderversePacket.unlawful_coding_alias
  block promotion
```

```text
if projection_surface is present
and canonical_refs are missing
and claim_state requests CANONICAL_LEAN:
  emit UnderversePacket.projection_proof_confusion
  block promotion
```

```text
if coding_variant == algorithmic_source
and proposed collapse lacks behavior-preserving tests:
  mark HOLD
  require TestReceipt
```

```text
if recursive reference exists
and reverse_collapse_target == null:
  emit UnderversePacket.recursive_abstraction_without_ground
  block promotion
```

```text
if model_output proposes a new compression operator
and adversarial_convergence == null:
  emit UnderversePacket.unopposed_synthesis
  mark HOLD
```

```text
if adversarial_convergence.surviving_phi == ""
or adversarial_convergence.surviving_phi == null:
  emit UnderversePacket.no_surviving_phi
  block promotion
```

```text
if adversarial_convergence.contra_surface == ""
or adversarial_convergence.gamma_pressure == "low" and claim_state requests REVIEWED:
  emit UnderversePacket.weak_adversary
  mark HOLD
```

```text
if source_import.type in {blog, essay, article}
and source_import.claims_neuroscience_or_biology
and no peer_reviewed_source_receipt exists:
  mark HOLD
  require analogy_bounded_language
```

## First canonical surface doctrine

```text
GCL is the combined surface on which biological, synthetic, symbolic,
algorithmic, geometric, formal, adversarial, and failure-coding regimes can be
compared without being collapsed into the same ontology.
```

Shorter:

```text
GCL unifies coding surfaces, not truth claims.
```

## First implementation target

The first executable implementation should not try to encode all variants.

It should implement four profiles:

```text
1. Stack-native GCL object validator
2. Sidon-GCL lawful-alias validator
3. Algorithmic-GCL AST observation packet validator
4. Adversarial-Convergence-GCL Warden pass validator
```

Then add Bio-GCL only as external-source / analogy-bounded objects.

## Compact doctrine

```text
Every code becomes GCL only after it declares its unit, expression, mutation,
repair, gate, projection, receipt, and adversarial counter-surface. GCL allows
many coding regimes to share a surface, but Warden prevents them from sharing
authority unless their evidence, closure, reverse-collapse paths, and surviving
phi match.
```
