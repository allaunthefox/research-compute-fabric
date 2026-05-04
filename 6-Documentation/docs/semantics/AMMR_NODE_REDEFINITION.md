# AMMR Node Redefinition

This note redefines an AMMR node as a committed QR-factorization summary.

The purpose is to replace vague "vector accumulation" language with a precise,
auditable object:

- each node stores a local orthonormal basis
- each node stores projection coefficients in that basis
- each node commits these quantities by hash
- the AMMR tree becomes a committed QR factorization tree

## Canonical Definition

Each AMMR node has the shape:

```text
Node:
  hash: H(left.hash || right.hash || summary)
  summary:
    Q: orthonormal basis vectors
    R: projection coefficients
    metadata:
      dimension
      norm energy
      condition number (optional)
```

Interpretation:

- `Q` is the local orthonormal frame for the node's retained subspace
- `R` is the coefficient object describing the node in that frame
- `hash` commits both ancestry and summary
- `metadata` provides typed audit information for stability checks

## Semantic Shift

Old AMMR intuition:

- weighted vector accumulation
- phase or resonance summaries
- Merkle-like aggregation over heuristic vector state

New AMMR intuition:

- hierarchical committed orthogonalization
- subspace-preserving aggregation
- QR summaries committed at every internal node

Therefore:

- AMMR is no longer merely an accumulator
- AMMR is a committed QR factorization tree

## Summary Fields

### Q: Orthonormal basis

`Q` represents the basis vectors spanning the retained subspace of the node.

Requirements:

1. Basis vectors are mutually orthogonal.
2. Each retained vector is normalized.
3. The basis order is deterministic.
4. The basis dimension is finite and explicitly recorded.

Minimal invariant:

```text
Q^T Q = I
```

In implementation terms, exact floating-point orthogonality is not required in
the proof layer. The proof layer should instead carry a typed witness that the
basis has been accepted as orthonormal under the chosen fixed-point or exact
representation.

### R: Projection coefficients

`R` represents the coefficient object of the node summary in basis `Q`.

Requirements:

1. Coefficients are defined with respect to the stored `Q`.
2. Coefficient shape is deterministic for the stored dimension.
3. If the parent is formed from child summaries, the parent `R` must be derived
   from the child contribution projected into the parent basis.

Minimal interpretation:

```text
summary_payload ~= Q R
```

This note does not force a specific rectangular or triangular encoding yet. The
only hard requirement is that `R` is the committed coefficient object associated
to `Q`.

### Metadata

Required metadata:

1. `dimension`
2. `normEnergy`

Optional metadata:

1. `conditionNumber`

Definitions:

- `dimension`: retained basis rank of the node
- `normEnergy`: scalar magnitude of the committed summary
- `conditionNumber`: numerical conditioning witness for stability-sensitive
  implementations

## Parent Merge Law

Given child nodes `L` and `R`, form the parent by:

1. concatenating or otherwise combining child summary payloads
2. computing a deterministic orthogonalization step
3. extracting the parent basis `Q_parent`
4. extracting the parent coefficients `R_parent`
5. computing parent metadata
6. hashing `left.hash || right.hash || summary_parent`

Canonical parent:

```text
parent.summary = QR(merge(left.summary, right.summary))
parent.hash    = H(left.hash || right.hash || parent.summary)
```

The exact `merge` operator may vary by domain, but it must be deterministic and
must feed the orthogonalization procedure.

## Hash Commitment

The node hash is a commitment to:

1. left ancestry
2. right ancestry
3. QR summary
4. metadata

So the hash is not merely a structural Merkle hash. It is a commitment to the
compressed linear-algebra state at that node.

This gives two audit guarantees:

1. ancestry integrity
2. summary integrity

## Required Invariants

Any later Lean formalization should target these invariants first.

### Invariant 1: Basis admissibility

```text
isOrthonormal(Q) = true
```

Completion condition:

- proof-layer predicate exists
- at least one witness theorem or `#eval` example exists

### Invariant 2: Dimension consistency

```text
metadata.dimension = rank(Q) = coeffDimension(R)
```

Completion condition:

- dimension is explicit
- no implicit shape assumptions remain in the node

### Invariant 3: Energy consistency

```text
metadata.normEnergy = energy(summary)
```

Completion condition:

- energy functional is defined
- one theorem or witness ties metadata to the summary payload

### Invariant 4: Hash determinism

```text
same children + same summary -> same hash
```

Completion condition:

- hash constructor is fully deterministic
- field ordering is fixed

### Invariant 5: Parent commitment law

```text
hash(parent) = H(hash(left) || hash(right) || summary(parent))
```

Completion condition:

- parent constructor exists
- commitment law is either definitional or theorem-backed

## Relationship To Existing Repo Structures

This redefinition supersedes the weaker "hash + vector state" shape currently
used in:

- `/home/allaun/Documents/Research Stack/0-Core-Formalism/lean/Semantics/Semantics/VecState.lean`
- `/home/allaun/Documents/Research Stack/docs/semantics/ene_schema_specification.md`

Specifically, the existing model:

- stores `vec`
- merges by additive vector superposition
- hashes after merge

The new model should instead:

- store a QR summary
- merge by deterministic orthogonalization
- hash the QR summary as the committed node payload

## Lean-Oriented Refactor Target

The eventual Lean structure should look more like:

```text
AMMRSummary
  qBasis
  rCoeff
  dimension
  normEnergy
  conditionNumber?

AMMRNode
  hash
  summary
```

with helper predicates:

- `isOrthonormalBasis`
- `dimensionConsistent`
- `energyConsistent`
- `isDeterministicCommit`

## Mirror Algorithm -> LUT

This section refines the execution interpretation of the committed QR-tree.

The mirror algorithm should be interpreted as:

```text
Mirror = dual-space projection
```

If AMMR stores:

- `Q`
- `R`

then the mirror LUT stores:

```text
f(Q) -> precomputed outputs
```

So runtime becomes:

```text
input -> project onto Q -> lookup result
```

### Runtime Interpretation

Given a learned or retained basis:

```text
Q = [pattern1, pattern2, pattern3, ...]
```

the runtime path is:

1. project input into the basis carried by `Q`
2. reduce the projection to a symbolic index
3. query the mirror LUT with that index
4. emit the precomputed action or result

Equivalent summary:

```text
learned basis -> symbolic index -> constant-time execution
```

The committed QR-tree therefore acts as:

1. a dimensionality-reduction layer
2. a commitment layer
3. a symbolic indexing layer for constant-time lookup

### Mirror LUT Semantics

The mirror LUT is not an arbitrary cache.

It is the dual execution space corresponding to the retained basis. Its input is
not the raw payload but the projection of the payload into the node's basis.

Canonical shape:

```text
MirrorLUT:
  key   := quantize(project(input, Q))
  value := action | result | next-state
```

This means:

- AMMR summarizes structure
- mirror LUT operationalizes that structure

The QR-tree provides the stable symbolic address space; the LUT provides the
constant-time action layer.

## Architectural Synthesis

The overall stack is:

### Layer 1: Field

- QR / SVD-based orthogonal summaries
- deterministic retained subspace per node

### Layer 2: Memory

- AMMR commits node summaries
- ancestry + summary are cryptographically bound

### Layer 3: Routing

- routing weights are determined by projection similarity
- nearest or strongest subspace match drives traffic

### Layer 4: Nutrients

- residual energy drives growth or decay
- large residuals force refinement or expansion
- small residuals support pruning or stabilization

### Layer 5: Execution

- mirror LUT maps basis-space indices to outputs
- runtime path is projection first, lookup second

In short:

```text
Field -> Memory -> Routing -> Nutrients -> Execution
```

## Critical Constraints

These constraints are mandatory if the design is to remain deterministic and
hardware-extractable.

### Constraint 1: Floating-point instability

Naive Gram-Schmidt is not stable enough as the canonical implementation target.

Priority order:

1. modified Gram-Schmidt
2. Householder QR
3. SVD where truncation and conditioning dominate

Proof-layer implication:

- do not formalize correctness in terms of unconstrained floating-point numerics
- formalize accepted summary objects and their invariants
- leave concrete numeric factorization strategy to extraction targets until a
  fixed-point implementation is specified

### Constraint 2: Hash determinism

`Q` cannot be hashed directly from unstable high-precision floating-point output.

Requirement:

```text
Q -> deterministic quantization -> canonical serialization -> hash
```

Without quantization, equivalent bases may hash differently across platforms or
 executions.

Proof-layer implication:

- the committed object is the canonicalized summary, not an implementation-local
  in-memory matrix layout

### Constraint 3: Basis size control

Without rank control, the basis will grow without bound.

Requirement:

- retain only significant components
- truncate small singular values or low-energy directions
- record retained rank in metadata

Canonical policy shape:

```text
retain i iff singularValue(i) >= threshold
```

Proof-layer implication:

- dimension must be explicit
- truncation policy must be deterministic
- parent summary rank must be reproducible from child summaries and policy

## Formal O-AMMR Statement

The cleaned statement of the idea is:

### Orthogonal AMMR (O-AMMR)

An Algebraic Merkle Mountain Range variant in which:

1. node summaries are orthogonal bases derived from input vectors
2. merge operations perform deterministic projection-based decomposition
3. information redundancy is reduced through residual minimization
4. the structure maintains a cryptographically committed QR/SVD factorization
5. computation histories are translated into a dual LUT execution space

## What This Makes AMMR

Under this redefinition, AMMR is best understood as:

```text
a distributed, verifiable dimensionality-reduction engine
```

This is stronger than:

- plain vector accumulation
- heuristic resonance tracking
- ordinary Merkle aggregation

because the node summary now carries a committed subspace model and the runtime
execution path is expressed in basis-space rather than raw-space.

## Immediate Lean-Facing Next Step

The next implementation step should now be split into two local targets.

### Target A: Summary layer

Add:

1. `AMMRSummary`
2. `AMMRNode`
3. `dimensionConsistent`
4. `commitParent`

Completion metrics:

- deterministic parent constructor exists
- dimension consistency is witnessed
- commitment law is definitional or theorem-backed

### Target B: Execution layer

Add a separate execution-facing structure, for example:

```text
MirrorLUTIndex
  basisId
  quantizedCoeff

MirrorLUTEntry
  index
  result
```

with theorem targets:

1. projection indexing is deterministic
2. equal quantized projections yield equal LUT addresses
3. execution depends on basis-space key, not raw payload identity

Completion metrics:

- no raw-space lookup remains in the formal execution path
- lookup key is fully determined by basis identifier plus quantized coefficients
- at least one witness shows constant-time symbolic execution after projection

## Completion Metrics

This redefinition is complete only when all of the following are true:

1. There is one canonical node shape in repo docs.
2. The node is explicitly defined as a committed QR factorization summary.
3. The parent merge law is deterministic and documented.
4. The hash commitment includes both ancestry and summary.
5. The five invariants above are mapped to Lean predicates or theorem targets.
6. Existing AVMR/AMMR Merkle language is updated to match the committed QR-tree
   semantics where applicable.

## Immediate Next Step

The next implementation step should be:

1. add a Lean-facing `AMMRSummary` structure
2. add a deterministic parent-constructor skeleton
3. prove hash commitment and dimension consistency before attempting any full QR
   numerics

This keeps the proof layer honest while allowing later extraction targets to
choose the concrete QR computation strategy.
