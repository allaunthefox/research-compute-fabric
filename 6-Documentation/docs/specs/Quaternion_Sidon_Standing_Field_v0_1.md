# Quaternion Sidon Standing Field v0.1

## Status

**Claim state:** `BEAUTIFUL_PROVISIONAL`

This spec records a speculative OTOM toy formalism recovered from the **Mercury Superfluidity Under Compression** chat export. The concept begins from a physics thought experiment about mercury under Jupiter-level compression, then refines into a mathematical model: a square-grid cellular lattice whose local sites carry quaternion-like spin/phase rotors, driven by a triangle-wave standing field, with a Sidon-like pairwise uniqueness law acting as the meta-emergent anti-aliasing property.

## Source boundary

The source discussion explicitly separates the physical claim from the mathematical intuition:

```text
unlikely: mercury atoms become a helium-like superfluid
more plausible: compressed mercury might support superconducting or condensate-like quasiparticle order
useful toy model: quaternion rotors + Sidon-like pairwise uniqueness + triangle-wave standing lattice
```

This spec does **not** claim that mercury becomes a superfluid under Jovian compression. It records the formal structure that emerged from the thought experiment.

## Core object

The toy model is:

```text
square lattice
+ local quaternion/SU(2)-like phase rotors
+ magneto-electric symmetry-breaking seed
+ pressure-locking intuition
+ pairwise Sidon-like anti-aliasing
+ triangle-wave cellular standing-flow update
```

A compact description:

```text
q_i ∈ SU(2) ≅ unit quaternions
Δq_ij = q_i⁻¹ q_j
Sidon-like gate: Δq_ij = Δq_kl only for the same unordered pair
```

In implementation scaffolds, the exact quaternion arithmetic may be replaced by discrete signatures until Q16.16 or algebraic quaternion support exists.

## Physical interpretation boundary

### Blocked claim

```text
Jupiter-level compression makes mercury a normal atomic superfluid.
```

### Allowed hypothesis

```text
Extreme compression plus low temperature plus external bias might make mercury interesting as a scaffold for superconducting or condensate-like quasiparticle order.
```

### Allowed toy formalism

```text
A compressed heavy-metal lattice can be modeled as local phase rotors whose pairwise interaction signatures may benefit from Sidon-like anti-collision structure.
```

## Mechanism map

```text
Jovian compression
→ dense lattice / metallic scaffold

weak magneto-electric bias
→ spin/orbital/phase alignment seed

heavy-element spin-orbit coupling
→ couples orbital distortion to spin response

paired collective modes
→ possible bosonic quasiparticle condensate-like order

Sidon-like pair uniqueness
→ pairwise phase relations remain addressable and minimally degenerate

triangle-wave cellular driver
→ square-grid standing-wave transport toy model
```

## Why quaternion rotors

Spin is not literally a little arrow rotating in space. The useful mathematical image is a local internal rotor. For spinor-like systems, the geometry of `SU(2)` and unit quaternions is a natural language.

Toy state:

```text
q_i = a_i + b_i i + c_i j + d_i k
```

with unit-like constraint in a later fixed-point version:

```text
a_i² + b_i² + c_i² + d_i² ≈ 1
```

The quaternion picture preserves:

```text
phase
orientation
handedness
double-cover behavior
relative spin/orbit geometry
```

## Sidon-like meta-emergence

A classical Sidon set has unique pairwise sums. The toy lattice generalizes this idea from additive integers to pairwise phase signatures.

Classical form:

```text
a + b = c + d ⇒ {a,b} = {c,d}
```

Quaternionic lattice form:

```text
σ(i,j) = σ(k,l) ⇒ {i,j} = {k,l}
```

where:

```text
σ(i,j) = encoded pairwise relative phase / interaction signature
```

Interpretation:

```text
coherent, but not ambiguous
phase-locked, but not collapsed into aliasing
relationally addressable, not merely ordered
```

This is why the Sidon-like property is meta-emergent: it is not the condensate itself, but a rule over how the condensate's pairwise channels avoid degeneracy.

## Triangle-wave standing cellular field

The visual model from the source chat is:

```text
square grid
+ cellular update law
+ triangle-wave phase driver
+ standing-wave flow
```

Minimal symbolic form:

```text
Λ = square lattice
u_ij(t) = local state
S_ij(t) = Tri(ωt + k·r_ij) + Tri(ωt - k·r_ij)
u_ij(t+1) = F(u_ij(t), neighbors(u_ij(t)), S_ij(t))
```

Triangle-wave forcing matters because it is piecewise linear:

```text
linear ramp up
→ turning point
→ linear ramp down
```

That gives:

```text
snap points
clean reversals
clocked phase corridors
standing interference nodes
compression-friendly discrete structure
```

## OTOM / GCL interpretation

```text
Δ = alias collisions, phase degeneracy, decoherence, thermal disorder, lattice frustration
φ = preserved pairwise distinguishability and coherent rotor relation
γ = pressure, magneto-electric seed, triangle-wave forcing
λ = toy square lattice / simulation scale, not real material phase
```

The lawfulness statement:

```text
A coherent lattice is not lawful enough if its pairwise channels alias.
A Sidon-like field adds the anti-collision condition needed for addressable coherence.
```

## Lean artifact

Paired module:

```text
0-Core-Formalism/lean/Semantics/Semantics/QuaternionSidonField.lean
```

The module defines:

```text
GridCoord
QuaternionRotor
LatticeSite
PairSignature
TriangleWaveDriver
CellularUpdate
StandingWaveField
SidonLike
AliasCollision
PassesSidonGate
```

Key theorem shape:

```text
sidon_like_no_alias_collision
```

Meaning:

```text
If the pair signatures satisfy the Sidon-like uniqueness condition, then there is no nontrivial alias collision.
```

It also includes a four-site square-grid example with a triangle-wave driver and pair signatures that pass the Sidon gate.

## Warden gates

### Gate 1 — Mercury superfluid boundary

Blocked:

```text
Mercury becomes a helium-like superfluid under Jupiter compression.
```

Allowed:

```text
The thought experiment motivates a quaternion/Sidon standing-field toy model and a possible superconducting/quasiparticle-condensate hypothesis.
```

### Gate 2 — Sidon field is not a new force

Blocked:

```text
Sidon field is a physical force.
```

Allowed:

```text
Sidon field is an emergent relational ordering / anti-aliasing condition over pairwise interaction signatures.
```

### Gate 3 — Quaternion spin is a mathematical skin

Blocked:

```text
The material literally contains classical quaternion objects.
```

Allowed:

```text
Quaternion rotors are a compact way to model local spinor-like internal phase orientation.
```

### Gate 4 — Toy lattice is not experiment

Blocked:

```text
The square-grid triangle-wave automaton proves the material phase.
```

Allowed:

```text
The square-grid triangle-wave automaton is a simulation scaffold for lawfulness, aliasing, and standing-flow structure.
```

## Strongest formulation

> A Quaternion Sidon Standing Field is a toy model of addressable coherence: local quaternion-like rotors phase-lock under structured forcing while a Sidon-like pair uniqueness gate prevents the coherent field from collapsing into ambiguous pairwise aliasing.

That is the part OTOM should carry forward.
