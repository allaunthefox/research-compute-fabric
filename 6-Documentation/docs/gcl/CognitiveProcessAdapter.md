# Cognitive Process Adapter

Status: HOLD / adapter doctrine
Authority: workbench synthesis; not formal proof
Related:

- `docs/gcl/ErdosMentalModelMassNumberMap.md`
- `docs/gcl/MassNumberSurfaceTranslation.md`
- `docs/gcl/FrameworkReaderRamp.md`
- `docs/gcl/EquationUnderverseDoctrine.md`

## Purpose

This document defines an adapter for extracting usable process from many mathematical minds.

The premise:

```text
Many minds worked the problem.
The useful artifact is not only the final theorem.
The useful artifact is the process by which each mind made the problem tractable.
```

The adapter converts those processes into Mass Numbers and then surfaces.

```text
mind process -> adapter -> Mass Number -> Surface
```

## Core definition

```text
Cognitive Process Adapter = a translation layer that extracts a solver's modeling process, normalizes it into a Mass Number packet, and projects it into a surface that the stack can compare, reuse, and audit.
```

This is not mind-reading.

It is a disciplined reconstruction from public artifacts:

```text
proofs
papers
lectures
worked examples
failed constructions
counterexamples
notations
diagrams
computational searches
heuristics
historical commentary
```

## Why this exists

Erdos-style domains were not solved by one universal mental method.

They were worked through a cloud of methods:

```text
geometric intuition
order-type compression
probabilistic existence
extremal counting
additive collision control
finite obstruction search
algorithmic enumeration
counterexample farming
notation compression
```

The adapter preserves those methods as reusable process objects.

## Pipeline

```text
Source artifact
  -> Process extraction
  -> Representation shift detection
  -> Invariant detection
  -> Obstruction detection
  -> Proof-engine detection
  -> Underverse shadow detection
  -> Mass Number packet
  -> Surface projection
  -> ACI / Warden validation
```

## Adapter input

```text
ProcessSource = {
  source_id,
  source_type,
  problem_id,
  solver_or_school,
  artifact_kind,
  claim_scope,
  validation_status
}
```

Example source types:

```text
paper
proof sketch
lecture note
computer proof
historical commentary
code repository
counterexample database
worked notebook
```

## Adapter output

```text
ProcessAdapterPacket = {
  problem_id,
  solver_or_school,
  source_artifact,
  object_before,
  object_after,
  representation_shift,
  invariant_focus,
  threshold_pressure,
  obstruction_shape,
  proof_engine,
  search_strategy,
  compression_gain,
  underverse_shadow,
  surface_projection,
  confidence_level,
  evidence_receipt
}
```

## The central adapter question

Do not ask only:

```text
What did they prove?
```

Ask:

```text
What object did their mind use to carry the problem?
```

Then ask:

```text
What did that object become after the adapter translated it?
```

## Process extraction fields

### 1. Object before

What did the raw problem appear to be?

```text
points
integers
graphs
colors
edges
sets
subsequences
configurations
```

### 2. Object after

What did the solver transform it into?

```text
order type
cup-cap sequence
random graph
density threshold
additive collision graph
signature function
finite search tree
energy estimate
container family
```

### 3. Representation shift

The modeling move.

```text
coordinates -> orientations
geometry -> sequence
integer sums -> collision surface
coloring -> obstruction graph
construction -> probability space
proof -> algorithmic certificate
```

### 4. Invariant focus

What stayed meaningful through the translation?

```text
convexity
unique sums
monochromatic clique
edge density
forbidden configuration count
orientation sign
additive energy
```

### 5. Obstruction shape

What was the problem trying to avoid or force?

```text
counterexample
near-counterexample
collision
bad event
forbidden subgraph
non-convex delay configuration
unrealizable signature
search dead branch
```

### 6. Proof engine

What style carried the result?

```text
pigeonhole
induction
probabilistic method
extremal counting
finite geometry
container method
regularity method
energy method
computer enumeration
constructive algorithm
```

### 7. Underverse shadow

What did the method exclude, hide, fail to represent, or leave as residue?

```text
avoiders
failed branches
unrealizable signatures
collision residue
bad-event clusters
unbounded search
lost metric information
near-threshold configurations
```

## Process-to-Mass translation

```text
MassNumber = bind_process(
  representation_shift,
  invariant_focus,
  threshold_pressure,
  obstruction_shape,
  proof_engine,
  underverse_shadow
)
```

The Mass Number does not claim the process is the theorem.

It records how the theorem became visible.

## Mass-to-Surface translation

```text
Surface = project_mass_number(MassNumber)
```

Mapping:

```text
representation_shift -> seam
invariant_focus      -> contour / anchor
threshold_pressure   -> ridge / height field
obstruction_shape    -> hole / wall
proof_engine         -> flow rule
search_strategy      -> path family
underverse_shadow    -> scar field / negative relief
compression_gain     -> gradient shortening
```

## Adapter families

### A1: Geometric intuition adapter

```text
raw object: point configuration
process: see convexity, cups, caps, order, orientation
surface: convexity forcing ridge with non-convex delay holes
```

### A2: Probabilistic method adapter

```text
raw object: hard construction
process: replace construction with random space and bad-event counting
surface: probability-pressure surface with rare-event holes and concentration ridges
```

### A3: Extremal adapter

```text
raw object: large finite structure
process: ask maximum density before a forbidden form appears
surface: density height field with forcing ridge and avoider basin
```

### A4: Additive / Sidon adapter

```text
raw object: integer set
process: translate equal sums into collision topology
surface: additive collision surface with uniqueness basins and repeated-sum scars
```

### A5: Signature / order-type adapter

```text
raw object: coordinates
process: discard metric data and keep orientation signatures
surface: sign-configuration surface with realizability seams and unrealizable scars
```

### A6: Algorithmic obstruction adapter

```text
raw object: possible construction
process: search partial states while maintaining avoidance invariant
surface: search-tree terrain with dead branches, forced contradictions, and certificate ridges
```

## Confidence labels

Adapter outputs must be labeled.

```text
DIRECT:
  source explicitly describes the method

INFERRED:
  method is reconstructed from proof structure

SPECULATIVE:
  method is a useful stack translation but not historically asserted

REJECTED:
  translation does not preserve the source process
```

## Anti-drift rule

Do not claim:

```text
This is exactly what the solver thought.
```

Allowed claim:

```text
This is a faithful adapter for the modeling process visible in the artifact.
```

## Minimal working example

For an Erdős-Szekeres convex polygon proof:

```text
source_artifact: proof / exposition
object_before: finite planar point set
object_after: ordered sequence / cup-cap relation / order type
representation_shift: coordinates -> order / orientation signs
invariant_focus: convex subset
threshold_pressure: point count required to force convex n-gon
obstruction_shape: configurations delaying convexity
proof_engine: geometric Ramsey / pigeonhole / induction / enumeration
underverse_shadow: non-convex delay configurations and near-counterexamples
surface_projection: convexity ridge, avoider holes, order-type seams, cup-cap flow lines
```

## Implementation rule

Every imported process must produce both:

```text
1. a Mass Number packet
2. a Surface projection
```

If it cannot produce a surface, keep it in HOLD state.

If the surface has no invariant, keep it in DRAFT state.

If the surface has no validation path, do not promote it.

## Compact doctrine

```text
The adapter does not collect only what mathematicians proved. It collects how their minds made the problem movable: the representation shift, invariant, obstruction, proof engine, search strategy, and residue. Mass Numbers hold that process. Surfaces render it. ACI and Warden decide whether it is reusable.
```
