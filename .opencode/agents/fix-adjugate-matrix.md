---
description: Fix the two sorry blocks in AdjugateMatrix.lean (det_self_inverse_approx and det_self_inverse_exact). Use ONLY when asked to fix AdjugateMatrix sorry or resolve matrix inverse proofs.
mode: subagent
model: anthropic/claude-sonnet-4-6
permission:
  edit: allow
  bash: allow
  read: allow
---

# Fix AdjugateMatrix.lean sorry blocks

## Context

`Semantics/AdjugateMatrix.lean` has two `sorry` blocks related to the 8×8 matrix inverse correctness:

### Sorry 1: `det_self_inverse_approx` (line 296)

```lean
theorem det_self_inverse_approx {m : Matrix8} {inv : Matrix8} (ε : Q16_16)
    (h : matrixInverse m = some inv) :
    matrixApproxEq (matrixMultiply m inv) identity8 ε := by
  sorry
```

**Blocker:** Q16_16 truncation causes 1 LSB error in division/multiplication. The theorem claims `m × inv ≈ I` within tolerance `ε`, but the proof requires formalizing the error propagation through adjugate-based matrix inversion on fixed-point arithmetic.

**Path forward:**
- (a) Prove a bounded-error variant with explicit ε bound derived from Q16_16 division error
- (b) Add exact-div precondition (if det divides cleanly)
- (c) Port to Mathlib ℚ proof where Laplace cofactor identity has a clean proof

### Sorry 2: `det_self_inverse_exact` (line 305)

```lean
theorem det_self_inverse_exact {m : Matrix8} {inv : Matrix8}
    (h : matrixInverse m = some inv)
    (h_div_exact : ∀ i j : Fin 8, ((getEntry (adjugate m) j.val i.val).toInt * 65536) % (det8 m).toInt = 0)
    (h_mul_exact : ∀ i j k : Fin 8, ((getEntry m i.val k.val).toInt * (getEntry inv k.val j.val).toInt) % 65536 = 0) :
    matrixMultiply m inv = identity8 := by
  sorry
```

**Blocker:** Requires showing that when all Q16_16 division and multiplication operations are exact (no truncation), the adjugate-based inverse satisfies `m × inv = I` exactly. The `h_div_exact` and `h_mul_exact` hypotheses pin down the exactness conditions.

**Path forward:** This is a pure integer-arithmetic proof under the exactness hypotheses. The Laplace cofactor expansion `m × adj(m) = det(m) · I` needs to be formalized for 8×8 matrices over ℤ, then the exactness hypotheses lift it to Q16_16.

## Note

`det_self_inverse` (the original single sorry from prior audits) was refactored into these two variants. `det_self_inverse_identity` (identity matrix case) was proven via computation.

## Steps

1. Read `Semantics/AdjugateMatrix.lean` lines 270-310
2. Read `Semantics/FixedPoint.lean` for Q16_16 arithmetic lemmas
3. Decide strategy: exact-path (`det_self_inverse_exact`) is likely easier since hypotheses remove all rounding concerns
4. Prove `det_self_inverse_exact` first (integer-arithmetic Laplace expansion)
5. Then address `det_self_inverse_approx` (requires error-bound analysis)
6. Build: `lake build Semantics.AdjugateMatrix`
7. Build: `lake build Compiler`
