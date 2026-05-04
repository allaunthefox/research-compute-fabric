# Two-Layer Kinetic Sidon Lattice v0.1

## Status

**Claim state:** `BEAUTIFUL_PROVISIONAL`

This spec refines the Quaternion Sidon Standing Field into the actual intended architecture: a **two-layer mathematical lattice** where the kinetic layer carries motion/energy/state updates and the Sidon layer carries relational pair-address structure. The important move is that Sidon sets **flow between** the layers rather than merely sitting as a static property of one lattice.

## Core thesis

The system has two coupled layers:

```text
Layer 0: Kinetic lattice
  local motion, energy, phase-clock, update dynamics

Layer 1: Sidon relational lattice
  pair signatures, anti-aliasing, addressable relational channels
```

The Sidon layer is not the whole lattice. It is the relational routing layer that makes kinetic interactions addressable.

## Why this matters

A pure kinetic lattice can move but may alias its interactions:

```text
motion without clean pair addresses
→ interference ambiguity
→ hard inverse problem
→ poor compression / poor explanation
```

A pure Sidon lattice can distinguish pair relations but lacks dynamics:

```text
addresses without motion
→ static codebook
→ no transport
→ no field behavior
```

The two-layer lattice combines them:

```text
kinetic substrate generates flux
Sidon layer assigns pairwise addresses
addressed relations feed back into kinetic updates
```

This gives:

```text
motion with addressability
coherence without alias collapse
transport with relational receipts
```

## Minimal architecture

```text
KineticSite:
  site id
  square-grid coordinate
  energy
  momentum x/y
  phase clock

PairAddress:
  source site i
  target site j
  signature

KineticToSidonFlow:
  source pair
  kinetic flux
  phase delta
  produced signature

SidonToKineticFlow:
  pair address
  feedback energy
  feedback phase
```

The core loop:

```text
kinetic state
→ pairwise kinetic relation
→ Sidon signature
→ anti-aliasing gate
→ feedback into kinetic update
```

## Sidon sets as flowing relational structure

The prior Sidon-field idea says:

```text
pairwise signatures should be unique except for trivial pair equivalence
```

The two-layer version says:

```text
Sidon structure should be transported by kinetic flow.
```

So the Sidon set is not merely:

```text
{static pair signatures}
```

It becomes:

```text
{pair signatures generated, moved, refreshed, and fed back by kinetic state}
```

In OTOM terms:

```text
kinetic layer = substrate dynamics
Sidon layer = relational address code
flow = adapter between dynamics and addressability
```

## Lawfulness gates

### Gate 1 — Flow representation

Every kinetic-to-Sidon flow must land in an addressable Sidon pair:

```text
∀ f ∈ forwardFlow,
  ∃ p ∈ sidon.pairs,
    p.i = f.sourceA ∧
    p.j = f.sourceB ∧
    p.signature = f.producedSignature
```

### Gate 2 — Sidon uniqueness

The Sidon layer must avoid nontrivial pair-signature collisions:

```text
p.signature = q.signature ⇒ same unordered pair
```

### Gate 3 — Two-layer pass condition

The lattice passes only when both conditions hold:

```text
AllForwardFlowsRepresented ∧ SidonLike
```

This means the kinetic layer has not merely generated motion; it has generated motion that is relationally addressable.

## Compression interpretation

A two-layer kinetic/Sidon lattice acts like a compression machine:

```text
raw kinetic interactions
→ pairwise relational signatures
→ collision-free address space
→ feedback-stabilized update paths
```

The Sidon layer makes the kinetic field decodable.

Without the Sidon layer:

```text
many motions may look the same
```

With the Sidon layer:

```text
each meaningful pairwise motion has a unique relational address
```

So the compression object is:

```text
motion → address → lawful reconstruction
```

## Relation to the triangle-wave standing lattice

The triangle-wave driver can sit in the kinetic layer:

```text
phase clock
+ triangle wave forcing
+ local kinetic update
```

The Sidon layer receives the resulting pairwise transitions:

```text
phase delta
+ kinetic flux
→ produced signature
```

Then the Sidon layer feeds back:

```text
valid address
→ feedback energy / feedback phase
→ next kinetic update
```

This makes the standing wave flow not just visually coherent, but **relationally indexed**.

## Δφγλ reading

```text
Δ = alias collisions, unrepresented flows, ambiguous inverse paths, kinetic noise
φ = preserved pairwise addressability across kinetic updates
γ = triangle-wave forcing, kinetic flux, phase clock, Sidon gate pressure
λ = two-layer toy lattice / simulation scale
```

The lawfulness statement:

```text
A kinetic transition is not fully lawful until its pairwise relation can be carried through the Sidon layer without alias collision.
```

## Lean artifact

Paired module:

```text
0-Core-Formalism/lean/Semantics/Semantics/TwoLayerKineticSidonLattice.lean
```

The module defines:

```text
KineticSite
KineticLayer
PairAddress
SidonLayer
KineticToSidonFlow
SidonToKineticFlow
TwoLayerLattice
FlowRepresented
AllForwardFlowsRepresented
PassesSidonTransportGate
PassesTwoLayerGate
```

Key theorem shapes:

```text
sidon_like_no_alias_collision
passes_transport_gate_no_alias
two_layer_gate_no_alias
```

Meaning:

```text
If kinetic flows are represented in the Sidon layer and the Sidon layer satisfies pairwise uniqueness, then the two-layer lattice has no nontrivial pair-address alias collision.
```

## Warden gates

### Gate 1 — Not a material claim

Blocked:

```text
The two-layer kinetic Sidon lattice proves a mercury phase.
```

Allowed:

```text
The two-layer kinetic Sidon lattice is a toy mathematical scaffold for studying motion plus relational anti-aliasing.
```

### Gate 2 — Not static Sidon only

Blocked:

```text
The Sidon layer is just a static set of signatures.
```

Allowed:

```text
The Sidon layer is a relational address space through which kinetic flows are represented and fed back.
```

### Gate 3 — Kinetics alone are insufficient

Blocked:

```text
A kinetic lattice is lawful just because it has stable motion.
```

Allowed:

```text
The kinetic lattice becomes lawfully decodable only when pairwise interactions are represented in a non-aliasing Sidon layer.
```

## Strongest formulation

> The two-layer kinetic Sidon lattice separates dynamics from relational addressability: the kinetic layer moves, the Sidon layer disambiguates, and lawful flow is the transport of Sidon-valid pair signatures between them.

That is the architecture to carry forward.
