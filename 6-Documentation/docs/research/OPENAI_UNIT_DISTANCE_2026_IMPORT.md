# OpenAI 2026 Planar Unit-Distance Breakthrough Import

Status: EXTERNAL_REFERENCE
Date ingested: 2026-05-20
Primary source: https://openai.com/index/model-disproves-discrete-geometry-conjecture/
Proof PDF: https://cdn.openai.com/pdf/74c24085-19b0-4534-9c90-465b8e29ad73/unit-distance-proof.pdf
Companion remarks: https://cdn.openai.com/pdf/74c24085-19b0-4534-9c90-465b8e29ad73/unit-distance-remarks.pdf
Abridged model trace: https://cdn.openai.com/pdf/1625eff6-5ac1-40d8-b1db-5d5cf925de8b/unit-distance-cot.pdf

## Claim Boundary

This is an external mathematical result, not a Research Stack theorem.

The result concerns the planar unit-distance function:

```text
nu(P) = number of unordered pairs {x,y} in P with |x-y| = 1
nu(n) = max nu(P) over all n-point planar sets P
```

OpenAI reports that an internal general-purpose reasoning model produced a proof disproving Erdős's conjectured upper bound `nu(n) <= n^(1 + C / log log n)`. The proof establishes that for infinitely many `n`, there are planar point sets with:

```text
nu(n) >= n^(1 + delta)
```

for some fixed `delta > 0`. OpenAI's summary says a forthcoming refinement by Will Sawin can take `delta = 0.014`.

## What Changed

Before this result, the best known lower-bound constructions were essentially lattice/grid constructions in the spirit of Erdős's 1946 construction. The common expectation was that square-grid-like behavior was asymptotically close to optimal.

The new result refutes that belief by importing deep algebraic number theory into planar combinatorial geometry.

## How It Was Done

The proof has two separable parts.

### 1. Arithmetic Engine

The classical grid construction can be understood through Gaussian integers `Z[i]`: many factorizations of a norm create many lattice vectors of the same length.

The new construction generalizes this idea:

- Replace `Q(i)` / Gaussian integers with `K = L(i)`, where `L` is a totally real field of growing degree.
- Choose rational primes that split completely in `L`.
- Use conjugate prime-ideal pairs in `K` to create many ideal products.
- Use a class-group pigeonhole argument to turn many ideal choices into many elements `u` with relative norm `u c(u) = 1`.
- Under every complex embedding, those elements have absolute value `1`, so they become candidate unit translations.

The hard existence input is a family of number fields with controlled discriminants/class numbers and prescribed splitting. The paper gets this via:

- unramified pro-3 class field towers
- Chebotarev splitting
- Shafarevich relation-rank estimates
- Golod-Shafarevich theory
- Hajir-Maire-style class-field-tower methods

### 2. Geometric Projection

Once the proof has many norm-one elements:

- Embed `K` into a high-dimensional complex Minkowski space.
- Build a lattice `Lambda` from a scaled ring of integers.
- Cut the lattice by a product of discs.
- Count directed pairs `(x, x+u)` where `u` is one of the many norm-one elements.
- Project injectively to one complex coordinate, identified with `R^2`.

Because the first coordinate of each `u` has modulus `1`, counted pairs project to unit segments in the plane. A packing bound controls the number of projected points, giving the polynomial improvement:

```text
nu(P_j) >= n_j^(1 + delta)
```

for infinitely many projected point sets.

## Why AI Found It

The companion remarks emphasize that the path was easy for humans to dismiss:

- Most attention was spent trying to prove the Erdős upper bound, not disprove it.
- A counterexample required seriously pursuing a generalization of the original lattice construction.
- The route only works if the solver knows enough class field theory to recognize the needed infinite towers.
- The AI appears to have persisted down a long-shot construction path while combining distant machinery.

This is a useful stack lesson: frontier search needs a route memory that does not over-penalize "unlikely but lawful" bridges between distant domains.

## Level-by-Level Import

### L0 Primordial

Import as a new arithmetic-geometric witness pattern:

```text
norm-one algebraic unit -> unit translation vector
```

This belongs beside PIST/DIAT shell arithmetic as a reminder that integer/factorization structure can surface as geometric incidence density.

### L1 Geometric

Import as a unit-distance construction surface:

```text
high-dimensional lattice cut -> injective complex-coordinate projection -> planar unit segments
```

This should inform GWL, toroidal shell, and quaternion/torsion work: useful planar geometry may be a projection shadow of a richer arithmetic embedding.

### L2 Biological

Import only as an analogy guard:

```text
latent high-dimensional code -> projected phenotype/contact graph
```

Do not promote biological claims from it. The safe use is structural: hidden algebraic constraints can produce dense observable interaction graphs.

### L3 Thermodynamic

Import as a cost/entropy lesson:

```text
many low-dimensional contacts can be generated by high-dimensional structured search
```

This matters for compression pressure and donated-cycle work: a large search cost can be worthwhile when it discovers a reusable construction family.

### L4 Security

Import into AngrySphinx/FAMM:

```text
do not discard long-shot routes solely because the community prior is low
```

The model succeeded by exploring a route humans had little incentive to pursue. FAMM scars should penalize failed routes, but not globally ban lawful cross-domain routes with strong invariant hooks.

### L5 Semantic

Import as a semantic bridge:

```text
algebraic number theory <-> discrete geometry
```

The bridge is not metaphorical: norm, splitting, embedding, projection, and unit distance are linked by explicit maps.

### L6 Meta

Import as a search-policy update:

```text
frontier discovery = broad technical vocabulary + persistence + verifier feedback
```

The relevant meta-strategy is not "AI magic"; it is cross-domain generation, strict proof checking, external expert verification, and later human simplification.

## Stack Actions

- Add `OpenAIUnitDistance2026` as an external reference in concept maps.
- Add an Erdős unit-distance route distinct from existing Erdős distinct-distance notes.
- Create future Lean/Rust placeholders only after the proof objects to formalize are selected.
- Do not claim an internal proof until a local formalization or executable verifier exists.
- Use this as a benchmark class for donated-cycle science plugins: bounded search over arithmetic/geometric construction candidates with cheap downstream invariants.

## Suggested Future Modules

```text
Semantics.UnitDistance2026
Semantics.NumberFieldUnitDistance
Semantics.ArithmeticGeometryProjection
tools-rs/unit-distance-receipts
```

These should begin as receipt/checker surfaces, not as theorem claims.
