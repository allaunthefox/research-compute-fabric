# Framework Reader Ramp

Status: HOLD / translation doctrine
Authority: workbench explanation; not formal proof
Related:

- `docs/gcl/NonCompressedGoxelGeometryDoctrine.md`
- `docs/gcl/GoxelShapeRepresentationCollapseAddendum.md`
- `docs/gcl/EquationUnderverseDoctrine.md`
- `docs/gcl/FundamentalLawUnderverseMap.md`
- `docs/gcl/HolyDiverGoxelMOIMBridge.md`

## Purpose

This page exists to prevent future confusion.

The native framework language is dense. Terms like Goxel, Underverse, ACI, Warden, Hyper-PIST, void carrier, negative sequence, and NaN-field snip make sense inside the stack, but they should not be the first entry point for a new reader.

Use this page as the public-facing ramp.

## One-sentence public doorway

```text
This framework treats shape, state, and failure as things that should remain uncommitted until enough constraints exist to choose a safe representation.
```

## Three-layer explanation rule

Always explain the framework in this order:

```text
Layer 1: Practical engineering problem
Layer 2: Formal abstraction
Layer 3: Native manifold language
```

Do not start with Layer 3 unless the reader already knows the stack.

## Layer 1: Practical engineering problem

Ordinary systems often commit too early to one representation.

Examples:

```text
voxel grid
mesh
signed distance field
CAD boundary representation
graph
lattice
fluid field
state machine
kernel route
```

Early commitment is useful, but it fails when the system has:

```text
recursive geometry
unresolved state
invalid overlap
unbounded error
representation ambiguity
failed binding
missing route
NaN-like propagation
```

The practical goal is:

```text
prevent premature representation collapse,
track invalid states instead of ignoring them,
and snip unbounded errors before they contaminate the active model.
```

## Layer 2: Formal abstraction

The framework introduces two core abstractions.

### Goxel

```text
Goxel = pre-representation manifold primitive.
```

A Goxel does not directly mean cube, mesh, voxel, field, or CAD body.

It holds local manifold possibility before the system chooses a representation.

```text
Goxel
  -> constraints accumulate
  -> representation system selected
  -> geometry becomes representable
  -> ACI / Warden validation decides whether it can persist
```

### Underverse

```text
Underverse = bounded residual accounting layer.
```

The Underverse is not a literal reality-layer.

It records what failed, was excluded, remained absent, became forbidden, or tried to become unbounded.

```text
positive state
  -> validation check
  -> residual / forbidden / unbounded part detected
  -> Underverse receipt emitted
  -> bad field is snipped, quarantined, compressed, or rerouted
```

## Layer 3: Native manifold language

The native version says:

```text
Goxels preserve pre-shape manifold superposition.
The Underverse records negative / missing / failed / forbidden branches.
Void carriers are receipted non-arrivals.
Warden prevents unbounded NaN-field propagation.
ACI validates admissible collapse.
```

This is correct inside the stack, but it is too compressed for first contact.

## Glossary: native term to public translation

| Native term | Public translation |
|---|---|
| Goxel | pre-representation geometry / manifold primitive |
| Voxel | committed grid sample |
| Hoxel | committed higher-dimensional / temporal transition cell |
| Underverse | residual / failure-space accounting layer |
| Void carrier | constraint witness / receipted non-arrival |
| Law violation | unresolved pre-collapse possibility or failed validation case |
| NaN field | undefined, unbounded, untyped, or non-payable computational state |
| Warden | validation, quarantine, and safety gate |
| ACI | admissibility / collision-invariant check |
| Hyper-PIST surface | recursive activation manifold |
| Negative sequence | typed absence sequence |
| Sidion / Sidon collision | structured collision / forbidden overlap test |
| Partial compression | representation becoming stable but not yet validated |
| Representation collapse | selecting a concrete shape/state system |

## Reader-safe core explanation

Use this paragraph for newcomers:

```text
I am building a way to model systems where ordinary shape, state, or rule representations fail because the system has unresolved possibilities, recursive geometry, invalid states, or unbounded errors. A Goxel is a pre-representation manifold primitive: it delays commitment to voxel, mesh, field, CAD, graph, or lattice form until constraints choose the right representation. The Underverse is the diagnostic shadow layer: it records what failed, was forbidden, remained absent, or became unbounded, so bad states can be snipped before they contaminate the active model.
```

## What the framework is not claiming

Do not claim:

```text
The Underverse is a literal physical realm.
Goxels are literal particles in reality.
Void carriers are anti-photons.
Apparent law violations are physically allowed after collapse.
Infinite degrees of freedom are implemented literally.
```

Allowed claims:

```text
The Underverse is a bounded diagnostic transform.
Goxels are modeling primitives for delayed representation choice.
Void carriers are constraint witnesses: absence is informative inside an expectation field.
Apparent law violations are temporary unresolved pre-representation possibilities.
Infinite-seeming possibility must be implemented with finite bounded state.
```

## Practical payoff

The framework is useful if it helps do at least one of these:

```text
prevent premature representation collapse
choose voxel / mesh / SDF / CAD / graph / lattice form later and more safely
track residuals instead of hiding them
snip unbounded NaN fields before propagation
record why validation failed
route failed states into quarantine instead of letting them contaminate the model
make recursive geometry and same-locus manifold ambiguity auditable
```

## Minimal architecture

```text
Incoming state
  -> Goxel phase: unresolved possibility allowed
  -> Partial compression: candidate representation appears
  -> ACI check: local admissibility measured
  -> Warden check: systemic safety measured
  -> Commit: stable representation persists
  -> Underverse: failed, missing, unbounded, or forbidden branches are receipted
```

## Goxel rule

```text
A Goxel is not a shape.
A Goxel is pre-shape potential.
Shape appears only after collapse into a representation system.
```

Examples of representation systems:

```text
voxel lattice
hoxel cell
mesh surface
implicit scalar field
signed distance field
spline surface
CAD boundary representation
graph complex
simplicial complex
phonon or carrier lattice
fluid level set
manifold patch
```

## Underverse rule

```text
The Underverse is not ontology.
The Underverse is a pruning operator.
```

Operational rule:

```text
if state is undefined
or state is unbounded
or state is untyped
or state violates law without receipt
or state recursively expands without compression progress:
    convert to Underverse packet
    remove from active manifold
    route to Warden / quarantine / compression review
```

## Void carrier rule

```text
A void carrier is not a payload carrier.
It is a constraint witness.
```

It does not transmit by containing a message.

It updates the receiving system because a permitted or expected state failed to appear.

```text
Photons inform by arriving.
Void carriers inform by being absent where arrival was constrained.
```

## Explanation order for future writing

When writing papers, docs, posts, or READMEs:

1. Start with the engineering problem.
2. Introduce Goxel as delayed representation commitment.
3. Introduce Underverse as failure/residual accounting.
4. Introduce Warden/ACI as validation gates.
5. Only then introduce Hyper-PIST, negative sequences, void carriers, Sidion language, or manifold poetry.

## Compact final summary

```text
The framework is an engineering grammar for delayed commitment and bounded failure. Goxels hold unresolved manifold possibility before representation collapse. The Underverse records the failed, missing, forbidden, or unbounded parts as finite receipts. Warden and ACI prevent those residues from contaminating the committed model.
```
