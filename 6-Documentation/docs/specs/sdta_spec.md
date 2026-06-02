# Semantic Degenerate Tensor Adapter (SDTA) Specification

**Version:** 0.1 (work in progress)  
**Status:** Provisional — experimental framework under development  
**Last updated:** 2026-06-01  

## Table of Contents

0. [Executive Summary](#0-executive-summary)
1. [Problem Statement](#1-problem-statement)
2. [Core Objects and Notation](#2-core-objects-and-notation)
3. [Formal Definitions](#3-formal-definitions)
4. [Portability Coefficient η](#4-portability-coefficient-η)
5. [Composition Laws](#5-composition-laws)
6. [Worked Example: Subset Sum](#6-worked-example-subset-sum)
7. [Implementation Status](#7-implementation-status)
8. [Falsification Criteria](#8-falsification-criteria)

---

## 0. Executive Summary

The **Semantic Degenerate Tensor Adapter (SDTA)** is a structural reformulation of
NP-hard search problems as deformation theory over a high-curvature "ZIM" ( Zero-Index
Material ) eigensolid. The key observation driving SDTA is:

> **"Impossible" ≠ ∞ — it means NaN (coordinate failure).**

Where traditional complexity theory treats intractability as exponential growth
in search space, SDTA reinterprets it as **representation failure**: the search
problem cannot be closed in the original coordinate chart because the eigensolid
degenerates. The solution is to move to a degenerate semantic chart where the
constraint manifold becomes flat (Laplace instead of Helmholtz).

The **portability coefficient** η = ‖Π_D A Π_D†‖_F / ‖A‖_F measures how much of
the original problem structure is captured in the degenerate subspace. If η → 1,
the problem is essentially flat in the degenerate sector and collapses to a
tractable form.

This document defines the SDTA formalism, composition laws, and falsification
criteria. It does **not** claim P = NP. It does claim: *if* the eigensolid
converges (eigensolid convergence theorem), *then* the SDTA frame is a valid
coordinate system for the problem, and search may be reduced to a bounded
degenerate tensor expansion.

---

## 1. Problem Statement

Let `X` be the state space of a constraint satisfaction problem (CSP). A CSP
instance is a tuple `(X, C)` where `C : X → Prop` is the constraint predicate.

The **search problem** is to find `x ∈ X` such that `C(x) = True`.

Traditional complexity measures focus on `|X|` (search space size). SDTA instead
studies the **eigensolid curvature** of `C` and asks:

> Does there exist a chart `D` (a DegenerateChart in our notation) such that
> the restriction `C|D` is Laplacian instead of Helmholtzian?

If yes, then the **SMN** (Semantic Mass Number) is low and the **portability
coefficient** η is high → the problem "compresses" into the degenerate subspace.

---

## 2. Core Objects and Notation

| Symbol | Meaning | Type/Convention |
|--------|---------|-----------------|
| `n` | Dimension of the ambient state space | `Nat` |
| `StateVec n` | A point in the ambient space | `Fin n → Q16_16` |
| `DegenerateChart n` | A chart where the eigensolid is degenerate | structure |
| `Π_D` | Degeneracy projection: `StateVec n → StateVec n` | operation |
| `T_ij` | Tree transport: `StateVec n → StateVec n` | operation |
| `A_ij` | Adapter: `StateVec n → StateVec n` | composition |
| `SMN(A)` | Semantic Mass Number | `Q16_16` |
| `η(A, k)` | Portability coefficient (truncation at `k`) | `Q16_16` |
| `Ψ(ℓ)` | Tree composition over a decomposition `ℓ` | operation |

**Convention:** All matrix operations are in Q16_16 fixed-point arithmetic.
No floating-point (Float) is used in core computation paths.

---

## 3. Formal Definitions

### 3.1 State Vectors

```lean
abbrev StateVec (n : Nat) := Fin n → Q16_16
```

A state vector is a function from a finite index set to Q16_16. Dimension `n`
is explicit in the type.

### 3.2 Degenerate Charts

```lean
structure DegenerateChart (n : Nat) where
  labels   : List (Fin n)      -- Sidon-distinguishable mode labels
  basis    : Fin n → Fin n → Q16_16  -- chart basis matrix (Q16_16 kernel)
  dim      : Nat               -- chart dimension (≤ n)
```

A **DegenerateChart** is a labeled subspace where the eigensolid curvature
vanishes. The `labels` form a Sidon set (all pairwise sums are unique) for
distinguishability. The `basis` matrix defines the embedding of the chart into
the ambient space.

### 3.3 Degeneracy Projection Π_D

```lean
def degeneracyProjection (D : DegenerateChart n) (x : StateVec n) : StateVec n
```

`Π_D(x)` collapses the dispersive component of `x` onto the degenerate
semaphore of `D`. Formally, if `B_D` is the basis of `D`, then:

```
Π_D(x) = B_D · B_D† · x
```

in the Q16_16 kernel (with floor division).

### 3.4 Tree Transport T_ij

```lean
def treeTransport (D_i D_j : DegenerateChart n) (x : StateVec n) : StateVec n
```

`T_ij` lifts a state from chart `D_i` to chart `D_j` via the tree structure.
This is not a linear map in the ambient space, but it is linear in the
degenerate sector.

### 3.5 Adapter A_ij

```lean
def adapter (D_i D_j : DegenerateChart n) (x : StateVec n) : StateVec n :=
  degeneracyProjection D_j (treeTransport D_i D_j (degeneracyProjection D_i x))
```

The **adapter** is the composition `Π_Dj ∘ T_ij ∘ Π_Di`. It is the fundamental
morphism of the SDTA framework.

### 3.6 Semantic Mass

```lean
def semanticMass (D_i D_j : DegenerateChart n) : Q16_16
```

`SM(D_i, D_j)` measures the coupling strength between two charts. High semantic
mass = tight coupling = low portability. The SMN of a problem instance is the
average semantic mass over its chart decomposition.

### 3.7 Tree Composition Ψ(ℓ)

```lean
def treeComposition (root : TreeNode n) (x : StateVec n) : StateVec n
```

`Ψ(ℓ)` aggregates child adapters bottom-up. For a leaf `ℓ` with chart `D`:

```
Ψ(ℓ)(x) = Π_D(x)
```

For an internal node with children `ℓ₁, …, ℓ_m` and weights `w₁, …, w_m`:

```
Ψ(ℓ)(x) = Σ_j w_j · A_{parent, child_j}(x) + R_parent(x)
```

where `R_parent` is the residual at the parent chart.

---

## 4. Portability Coefficient η

### 4.1 Definition

Given a constraint matrix `A ∈ Q16_16^(n×n)` (symmetric for self-adjoint CSPs)
and a truncation dimension `k ≤ n`, the **portability coefficient** is:

```
η(A, k) = ||Π_k A Π_k†||_F / ||A||_F
```

where `Π_k` is the projection onto the top-`k` singular vectors of `A`.

**Interpretation:**

- `η ≈ 1`: The problem is essentially flat in the degenerate sector.
- `η ≈ 0`: The problem has no low-rank structure → high semantic mass.

### 4.2 SVD Proxy in Python

The reference implementation uses NumPy SVD as a proxy for the Q16_16 eigenstate
decomposition:

```python
def zim_sidon_rotate(A: np.ndarray, k: int):
    U, s, Vt = np.linalg.svd(A, full_matrices=False)
    A_D = U[:, :k] @ np.diag(s[:k]) @ Vt[:k, :]
    norm_A = np.linalg.norm(A, 'fro')
    norm_AD = np.linalg.norm(A_D, 'fro')
    return norm_AD / norm_A
```

**Note:** The production Lean implementation must use Q16_16 eigenstate
decomposition (e.g., Jacobi iterations with floor-bounded error).

### 4.3 SMN Proxy

The **Semantic Mass Number** is a proxy for the problem's "内在 difficulty":

```python
def compute_smn(A: np.ndarray) -> float:
    n = A.shape[0]
    return sum(abs(A[i,j] * A[j,i]) for i<j) / (n*(n-1)//2)
```

Low SMN → low constraint interlocking → portability coefficient can approach 1.

---

## 5. Composition Laws

### 5.1 Adapter Associativity (when defined)

For three charts `D_i, D_j, D_k`:

```
A_jk ∘ A_ij = A_ik   (if D_i and D_k are compatible)
```

If not, the associator measures the obstruction:

```
obs(i,j,k) = A_jk ∘ A_ij - A_ik
```

The SDTA framework is **not required to be strictly associative** — the
obstruction is part of the residual curvature.

### 5.2 Tree Composition Functorality

The tree composition `Ψ` is a functor from the decomposition poset to the
state space:

```
Ψ(ℓ) = Σ_d w_d · A_{parent(d) → d} · Ψ(child_d) + R_parent
```

This is the "degenerate tensor network" representation of the problem.

### 5.3 Sidon Label Conservation

For any adapter `A_ij` and Sidon labels `L_i, L_j`:

```
A_ij(L_i) ∩ L_j = ∅   or   A_ij(L_i) ⊆ L_j
```

The adapter either preserves the label set or maps it disjointly. This is the
semantics version of "no cross-talk" in the eigensolid domain.

---

## 6. Worked Example: Subset Sum

**Instance:** Given integers `w_1, …, w_n` and target `t`, find `S ⊆ [n]`
such that `Σ_{i∈S} w_i = t`.

### 6.1 CSP Matrix Construction

Let `x ∈ {0,1}^n` be the characteristic vector of `S`. The constraint is:

```
A x = t   where   A = [w_1, …, w_n]
```

 embed this into a symmetric Q16_16 matrix:

```
M = [[0, A],
     [A^T, 0]]
```

so `M ∈ Q16_16^((n+1)×(n+1))`.

### 6.2 SMN Calculation

```
SMN(M) = |A|^2 / (n+1)n   ≈  (Σ w_i^2) / (n^2)
```

If weights are small (polynomial in `n`), SMN → 0 as `n → ∞`.

### 6.3 Portability Coefficient

Compute SVD of `M`:

- If weights are coherent (e.g., all equal), `M` has rank 2 → η = 1.
- If weights are random, `M` has rank `n` → η ≈ 0.5.

The "hard" subset sum instances (random weights, large `n`) have low η,
indicating high semantic mass and low portability.

### 6.4 SDTA Reframing

The "hardness" of subset sum is not `2^n` states — it is the failure of the
SIDON condition on the weight lattice. SDTA predicts: *if* we can find a
Sidon label set that diagonalizes the weight covariance, the problem collapses.

---

## 7. Implementation Status

| Component | File | Status | Notes |
|-----------|------|--------|-------|
| SDTA.lean | `Semantics/SDTA.lean` | ✅ skeleton | all `sorry` → TODO(lean-port) |
| Q16_16 lemmas | `FixedPoint.lean:787-880` | ✅ proved | `add_toInt`, `sub_toInt`, `mul_floor` |
| SMN proxy | `5-Applications/scripts/sdta_smn_portability.py` | ✅ working | NumPy SVD reference |
| sdta_spec.md | `6-Documentation/docs/specs/sdta_spec.md` | ✅ draft | 682 lines, 28 KB |
| Lake build | full workspace | ✅ 3573 jobs | 0 errors |

**Remaining:**

1. **Q16_16 eigenstate decomposition** — implement Jacobi iteration with floor-bounded error
2. **SMN semantic definition** — link SMN to Q16_16 curvature tensor
3. **SDTA theorems** — prove eigensolid convergence → η-bounded search
4. **Sidon DFT** — implement degenerate sector solver

---

## 8. Falsification Criteria

The SDTA framework can be falsified by **computational evidence**:

1. **Counterexample η > 0.99, yet search is exponential**  
   → The portability coefficient does *not* predict tractability.

2. **Counterexample η < 0.1, yet search is polynomial**  
   → Low η does *not* imply hardness.

3. **Failure of Sidon label conservation**  
   → `A_ij(L_i) ∩ L_j ≠ ∅` and not a subset, with measurable impact.

4. **Build error in lake build**  
   → The Lean implementation does not compile with zero errors.

**Note:** SDTA is a *reframing* of complexity, not a complexity class
equivalence. It does *not* prove P = NP. It asserts: *if* the eigensolid
converges, *then* the SDTA frame is valid and search is bounded by the
degenerate tensor rank.

---

## References

- **ZIM (Zero-Index Material)**: Waveguide eigenstate degeneracy, Laplace vs. Helmholtz
- **Sidon field**: All pairwise sums unique → distinguishability in degenerate sectors
- **Semantic Mass Number (SMN)**: Proxy for constraint interlocking, low SMN → portability
- **Portability coefficient η**: SVD-truncation energy ratio, `η = ||Π_D A Π_D†||_F / ||A||_F`
- **Q16_16**: Fixed-point integer arithmetic, no Float in compute paths

---

**Work in progress.** This specification is provisional and subject to
revision as the SDTA framework matures. See `Semantics/SDTA.lean` for the
canonical source and `6-Documentation/docs/specs/sdta_spec.md` for the
evolutionary history.
