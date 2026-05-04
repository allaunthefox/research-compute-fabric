# Orthogonal AMMR and CRC Pattern Memory

This document specifies Orthogonal AMMR (O-AMMR) as a projection-based
generalization of AMMR and defines its integration into AMMR-backed CRC pattern
memory.

The central move is:

- replace additive or scalar summaries with orthogonal projection summaries
- preserve integrity via cryptographic commitment
- preserve informational structure via retained orthogonal subspaces

## Section 1: Orthogonal AMMR - Projection-Based Merge Laws

### 1. Overview

Orthogonal AMMR (O-AMMR) extends the standard Algebraic Merkle Mountain Range by
replacing scalar or associative summaries with projection-based geometric
summaries.

Each node encodes:

1. a cryptographic commitment
2. a structured orthogonal representation of its underlying data

The structure functions as a verifiable dimensionality-reduction engine,
preserving both:

1. integrity, through hashing
2. informational structure, through orthogonal bases

### 2. Node Structure

Each node `N` is defined as:

```text
N = {
  hash: H(N_left.hash || N_right.hash || Q || R),
  summary: {
    Q: orthonormal basis matrix,
    R: projection coefficients,
    shape: (rows, cols),
    energy: ||R||_F
  }
}
```

Where:

- `Q` spans the retained subspace of inputs
- `R` encodes projections of inputs into that basis
- `energy` captures total signal magnitude

### 3. Canonical Merge Law

To ensure determinism across distributed systems, merge is defined as:

```text
merge(A, B) = Orthogonalize(Canonicalize(A ∪ B))
```

#### 3.1 Canonicalization

Inputs are sorted deterministically:

1. by hash, or
2. by structural index

This ensures:

```text
identical input sets -> identical ordering -> identical summaries
```

#### 3.2 Orthogonalization

Instead of naive Gram-Schmidt, the implementation should use one of:

1. Modified Gram-Schmidt (MGS)
2. Householder QR
3. SVD, preferred for numerical stability

The factorization target is:

```text
X -> Q R
```

with:

- `Qᵀ Q = I`
- `R` upper triangular in QR form
- or diagonal / singular-value aligned when using SVD-style retention

### 4. Order-Independent Variant

The recommended order-independent form is covariance accumulation:

```text
C = Σ_i x_i x_iᵀ
```

Then:

```text
C = U Σ Uᵀ
```

Where:

- `U` becomes the orthogonal basis
- `Σ` encodes signal strength

This form is:

1. associative
2. commutative
3. appropriate for distributed AMMR aggregation

### 5. Hash Stability

Floating-point summaries must be stabilized before commitment.

Canonical rule:

```text
Q_quant = round(Q, ε)
R_quant = round(R, ε)
hash = H(... || Q_quant || R_quant || ...)
```

Without quantization:

```text
identical math -> different hashes -> consensus failure
```

### 6. Basis Truncation

To prevent unbounded basis growth:

```text
retain i iff Σ_i >= λ
```

Only dominant components are retained.

This yields:

1. compressed summaries
2. bounded memory
3. suppression of low-energy directions

### 7. Interpretation

O-AMMR transforms the structure into:

```text
a committed projection space of computation history
```

Each node encodes:

1. what directions of information exist
2. what signal strength is retained in those directions
3. what redundancy has been removed through projection

## Section 2: Integration into AMMR-Backed CRC Pattern Memory

### 1. Redefinition of CRC Squares

Previously:

- CRC squares cached discrete pattern signatures

Now:

- CRC squares store local orthogonal summaries

Canonical regional form:

```text
CRC_region:
  Q_local
  Σ_local
  trust
  stability
```

### 2. CRC Signature Function

Instead of:

```text
CRC = hash(pattern bits)
```

use:

```text
CRC = H(Q_quant, Σ_quant)
```

This encodes:

1. pattern structure
2. pattern strength
3. dimensional composition

### 3. Local n-map Schema

Each region maps:

```text
n-map:
  index  -> basis vector direction
  weight -> singular value
```

So each cell contributes:

1. to a direction in feature space
2. not merely to a binary local state

### 4. Pattern Matching

Pattern matching becomes projection-based:

```text
similarity(A, B) = ||Q_Aᵀ Q_B||
```

Meaning:

- similarity is the degree of alignment between retained subspaces

This replaces:

1. Hamming distance
2. bitwise comparison

### 5. Nutrient Dynamics

The nutrient layer becomes geometric rather than symbolic.

#### Nutrient Gain Law

```text
gain = ||x - Q Qᵀ x||
```

This is the residual after projection.

Interpretation:

- high residual -> new information -> high nutrient
- low residual -> redundant information -> low nutrient

#### Nutrient Decay Law

```text
Σ_i down -> branch pruned
```

Interpretation:

- weak directions lose energy
- low-energy directions are eventually removed

#### Duty Threshold Law

A region activates when:

```text
||Σ|| > θ
```

#### Routing Export Law

Mycorrhizal routing weight is:

```text
w_(A->B) = ||Q_Aᵀ Q_B|| * trust_A
```

Meaning:

- regions share signals when they span similar subspaces

#### AMMR Lock-In Rule

A pattern is committed when all of the following hold:

1. basis is stable across steps
2. singular values are stable across steps
3. projection error is below threshold

### 6. Solver Update Order

Each orthogonal update step proceeds as:

1. Observe
   Convert cell states into vectors.

2. Project
   Apply:
   ```text
   x -> Q Qᵀ x
   ```

3. Compute residual
   ```text
   r = x - Q Qᵀ x
   ```

4. Update proposals
   If residual is large, propose a new retained direction.

5. Update CRC bases
   Re-orthogonalize the local region.

6. Update AMMR
   Merge orthogonal summaries upward through the tree.

7. Nutrient update
   Reward residual energy and decay weak singular directions.

### 7. Mirror Algorithm

AMMR provides:

```text
(Q, Σ)
```

The mirror layer computes:

```text
coefficients = Qᵀ x
```

Then:

```text
output = LUT(coefficients)
```

This provides:

1. constant-time inference after projection
2. no repeated basis recomputation at execution time

### 8. Resulting System Behavior

The resulting system is:

```text
a self-compressing, projection-driven field solver
```

Where:

1. patterns are stored as subspaces
2. learning means discovering new orthogonal directions
3. memory means persistent basis vectors
4. pruning means removing low-energy directions

## Final Synthesis

The integrated system is:

1. AMMR
   Cryptographic commitment and hierarchical structure

2. Orthogonalization
   Redundancy removal through basis extraction

3. Nutrients
   Residual-driven learning and decay

4. Mycorrhizal routing
   Connectivity driven by subspace similarity

5. Mirror LUT
   Constant-time execution over projected coordinates

In plain terms, the system becomes:

```text
a distributed, verifiable, self-pruning basis-learning machine
```

This is more than:

1. pattern matching
2. storage
3. ordinary cached execution

It is:

```text
structure-preserving computation memory
```

## Completion Metrics

This specification is implementation-ready only when all of the following are
 mapped to code or theorem targets:

1. node structure with `Q`, `R`, and committed hash
2. deterministic merge law
3. quantized hash commitment
4. truncation rule with explicit threshold
5. projection-based CRC signature
6. projection similarity routing law
7. residual-based nutrient update law
8. mirror LUT execution keyed by projected coefficients

## Immediate Lean Targets

The smallest truthful Lean-facing targets suggested by this spec are:

1. `AMMRSummary`
   Fields:
   - basis witness
   - coefficient witness
   - shape
   - energy

2. `CRCRegionSummary`
   Fields:
   - local basis witness
   - local strength witness
   - trust
   - stability

3. `projectionSimilarity`
   Purpose:
   - typed similarity witness between retained subspaces

4. `residualEnergy`
   Purpose:
   - typed nutrient gain witness

5. `MirrorLUTIndex`
   Purpose:
   - projected-coordinate key for execution

The first theorem targets should be:

1. deterministic merge produces equal committed parent for equal canonical inputs
2. residual energy is zero for perfectly represented inputs
3. equal projected coefficients yield equal mirror LUT index
