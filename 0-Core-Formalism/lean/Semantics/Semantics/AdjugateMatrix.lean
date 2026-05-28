-- Semantics.AdjugateMatrix — Division-free matrix inversion via the adjugate method
--
--   A^{-1} = adj(A) / det(A)
--
-- All operations use Q16_16 fixed-point (NO floats).
-- The single division happens only at the final step.
--
-- Provides:
--   • det2, det4, det8   — determinant via cofactor expansion (first row)
--   • minor              — (n-1)×(n-1) submatrix
--   • cofactor           — (-1)^(i+j) * det(minor)
--   • adjugate           — transpose of cofactor matrix
--   • matrixInverse      — adj(A) / det(A), None if singular
--   • matrixMultiply     — standard matrix multiply
--   • cayleyTransform    — (I - A)(I + A)^{-1} for skew-symmetric A
--
-- Author: Sovereign Stack Research
-- Date:   2026-05-28
-- License: Research-Only

import Semantics.FixedPoint

set_option linter.dupNamespace false
set_option maxRecDepth 20000

namespace Semantics.AdjugateMatrix

open Semantics.FixedPoint
open Semantics.Q16_16

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Matrix types
-- ═══════════════════════════════════════════════════════════════════════════

/-- 2×2 matrix of Q16_16 entries. -/
abbrev Matrix2 := Array (Array Q16_16)

/-- 3×3 matrix of Q16_16 entries (used for 4×4 cofactor expansion). -/
abbrev Matrix3 := Array (Array Q16_16)

/-- 4×4 matrix of Q16_16 entries. -/
abbrev Matrix4 := Array (Array Q16_16)

/-- 5×5 matrix of Q16_16 entries (used for 6×6 cofactor expansion). -/
abbrev Matrix5 := Array (Array Q16_16)

/-- 6×6 matrix of Q16_16 entries (used for 7×7 cofactor expansion). -/
abbrev Matrix6 := Array (Array Q16_16)

/-- 7×7 matrix of Q16_16 entries (used for 8×8 cofactor expansion). -/
abbrev Matrix7 := Array (Array Q16_16)

/-- 8×8 matrix of Q16_16 entries. -/
abbrev Matrix8 := Array (Array Q16_16)

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Helpers
-- ═══════════════════════════════════════════════════════════════════════════

/-- Safe entry access: returns zero for out-of-bounds indices. -/
@[inline]
private def getEntry (m : Array (Array Q16_16)) (i j : Nat) : Q16_16 :=
  (m.getD i #[]).getD j zero

/-- Extract a minor submatrix: remove row `skipRow` and column `skipCol`. -/
private def minorSubmatrix (m : Array (Array Q16_16)) (n skipRow skipCol : Nat) :
    Array (Array Q16_16) :=
  let rows := (List.range n).filterMap fun i =>
    if i = skipRow then none
    else
      let row := (List.range n).filterMap fun j =>
        if j = skipCol then none
        else some (getEntry m i j)
      some row.toArray
  rows.toArray

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Determinant functions (cofactor expansion along first row)
-- ═══════════════════════════════════════════════════════════════════════════

/-- 2×2 determinant: ad - bc. -/
def det2 (m : Matrix2) : Q16_16 :=
  let a := getEntry m 0 0
  let b := getEntry m 0 1
  let c := getEntry m 1 0
  let d := getEntry m 1 1
  sub (mul a d) (mul b c)

/-- 3×3 determinant via cofactor expansion along first row. -/
def det3 (m : Matrix3) : Q16_16 :=
  (List.range 3).foldl (fun acc j =>
    let s : Q16_16 :=
      if (j : Nat) % 2 = 0 then getEntry m 0 j
      else neg (getEntry m 0 j)
    let subM := minorSubmatrix m 3 0 j
    add acc (mul s (det2 subM))
  ) zero

/-- 4×4 determinant via cofactor expansion along first row. -/
def det4 (m : Matrix4) : Q16_16 :=
  (List.range 4).foldl (fun acc j =>
    let s : Q16_16 :=
      if (j : Nat) % 2 = 0 then getEntry m 0 j
      else neg (getEntry m 0 j)
    let subM := minorSubmatrix m 4 0 j
    add acc (mul s (det3 subM))
  ) zero

/-- 5×5 determinant via cofactor expansion along first row. -/
def det5 (m : Matrix5) : Q16_16 :=
  (List.range 5).foldl (fun acc j =>
    let s : Q16_16 :=
      if (j : Nat) % 2 = 0 then getEntry m 0 j
      else neg (getEntry m 0 j)
    let subM := minorSubmatrix m 5 0 j
    add acc (mul s (det4 subM))
  ) zero

/-- 6×6 determinant via cofactor expansion along first row. -/
def det6 (m : Matrix6) : Q16_16 :=
  (List.range 6).foldl (fun acc j =>
    let s : Q16_16 :=
      if (j : Nat) % 2 = 0 then getEntry m 0 j
      else neg (getEntry m 0 j)
    let subM := minorSubmatrix m 6 0 j
    add acc (mul s (det5 subM))
  ) zero

/-- 7×7 determinant via cofactor expansion along first row. -/
def det7 (m : Matrix7) : Q16_16 :=
  (List.range 7).foldl (fun acc j =>
    let s : Q16_16 :=
      if (j : Nat) % 2 = 0 then getEntry m 0 j
      else neg (getEntry m 0 j)
    let subM := minorSubmatrix m 7 0 j
    add acc (mul s (det6 subM))
  ) zero

/-- 8×8 determinant via cofactor expansion along first row.
    Recurses: det8 → det7 → det6 → det5 → det4 → det3 → det2.
    All arithmetic is Q16_16 saturating fixed-point. -/
def det8 (m : Matrix8) : Q16_16 :=
  (List.range 8).foldl (fun acc j =>
    let s : Q16_16 :=
      if (j : Nat) % 2 = 0 then getEntry m 0 j
      else neg (getEntry m 0 j)
    let subM := minorSubmatrix m 8 0 j
    add acc (mul s (det7 subM))
  ) zero

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Minor and cofactor (8×8)
-- ═══════════════════════════════════════════════════════════════════════════

/-- 7×7 minor of an 8×8 matrix: delete given row and column. -/
def minor8 (m : Matrix8) (row col : Nat) : Matrix7 :=
  minorSubmatrix m 8 row col

/-- Cofactor: (-1)^(row+col) * det(minor). -/
def cofactor8 (m : Matrix8) (row col : Nat) : Q16_16 :=
  let s := if (row + col) % 2 = 0 then one else negOne
  mul s (det7 (minor8 m row col))

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  Adjugate matrix (8×8)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Cofactor matrix: cof[i][j] = cofactor(i,j).
    Adjugate = transpose(cofactor matrix).
    Since we build the transpose directly, entry (i,j) = cofactor(j,i). -/
def adjugate (m : Matrix8) : Matrix8 :=
  Array.ofFn (n := 8) fun (i : Fin 8) =>
    Array.ofFn (n := 8) fun (j : Fin 8) =>
      cofactor8 m j.val i.val

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  Matrix multiply (8×8)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Standard matrix multiply: (a × b)[i][j] = Σ_k a[i][k] * b[k][j]. -/
def matrixMultiply (a b : Matrix8) : Matrix8 :=
  Array.ofFn (n := 8) fun (i : Fin 8) =>
    Array.ofFn (n := 8) fun (j : Fin 8) =>
      (List.range 8).foldl (fun acc k =>
        add acc (mul (getEntry a i.val k) (getEntry b k j.val))
      ) zero

-- ═══════════════════════════════════════════════════════════════════════════
-- §7  Matrix inverse via adjugate
-- ═══════════════════════════════════════════════════════════════════════════

/-- Matrix inverse using adjugate method: A^{-1} = adj(A) / det(A).
    Returns none if det(A) = 0 (singular matrix).
    The single division happens only here — all intermediate work is
    multiplication and addition. -/
def matrixInverse (m : Matrix8) : Option Matrix8 :=
  let d := det8 m
  if d.toInt = 0 then none
  else
    let adj := adjugate m
    some (Array.ofFn (n := 8) fun (i : Fin 8) =>
      Array.ofFn (n := 8) fun (j : Fin 8) =>
        div (getEntry adj i.val j.val) d)

-- ═══════════════════════════════════════════════════════════════════════════
-- §8  Cayley transform
-- ═══════════════════════════════════════════════════════════════════════════

/-- 8×8 identity matrix. -/
def identity8 : Matrix8 :=
  Array.ofFn (n := 8) fun (i : Fin 8) =>
    Array.ofFn (n := 8) fun (j : Fin 8) =>
      if i.val = j.val then one else zero

/-- Cayley transform: given a skew-symmetric matrix A, compute
    (I - A)(I + A)^{-1}.
    For skew-symmetric A, this produces an orthogonal matrix.
    Returns none if (I + A) is singular. -/
def cayleyTransform (skew : Matrix8) : Option Matrix8 :=
  let iPlusA : Matrix8 := Array.ofFn (n := 8) fun (i : Fin 8) =>
    Array.ofFn (n := 8) fun (j : Fin 8) =>
      if i.val = j.val
      then add one (getEntry skew i.val j.val)
      else getEntry skew i.val j.val
  let iMinusA : Matrix8 := Array.ofFn (n := 8) fun (i : Fin 8) =>
    Array.ofFn (n := 8) fun (j : Fin 8) =>
      if i.val = j.val
      then sub one (getEntry skew i.val j.val)
      else neg (getEntry skew i.val j.val)
  match matrixInverse iPlusA with
  | none => none
  | some inv => some (matrixMultiply iMinusA inv)

-- ═══════════════════════════════════════════════════════════════════════════
-- §9  Theorems
-- ═══════════════════════════════════════════════════════════════════════════

/-- If matrixInverse returns `some inv`, then `m × inv = I`.

    MATHEMATICAL PROOF SKETCH (exact arithmetic over a field F):

    1. From `h`, extract `d := det8 m ≠ 0`.
    2. By definition of `matrixInverse` and `adjugate`,
       `inv[i][j] = cofactor8 m j i / d`  (note the transpose: adj = cof^T).
    3. The Laplace cofactor identity gives:
         Σ_k m[i][k] · cofactor8 m j k = det8 m · δ(i,j)
       This holds because:
       - When i = j, the left side is exactly the cofactor expansion of
         det8 m along row i.
       - When i ≠ j, the left side is the determinant of a matrix with
         two identical rows (row i replaced by row j), hence 0.
    4. Dividing by d:  Σ_k m[i][k] · (cofactor8 m j k / d) = δ(i,j).
    5. Therefore (m × inv)[i][j] = δ(i,j), i.e., m × inv = I.

    Q16_16 OBSTRUCTION:

    This theorem is **not exactly true** over saturating Q16_16 fixed-point
    arithmetic.  The source of error is integer truncation in `div` and `mul`:

    - `div a b` = ofRawInt ((a * 65536) / b)    — truncates toward zero
    - `mul a b` = ofRawInt ((a * b) / 65536)     — truncates toward zero

    When `det8 m` does not divide the adjugate entries exactly, `div`
    introduces a truncation error of up to 1 LSB per entry.  This error
    propagates through `mul` and `add` in the matrix multiply.

    Concrete counterexample: m = diag(3, 1, 1, 1, 1, 1, 1, 1).
      det(m) = 3, inv[0][0] = div(65536, 196608) = ofRawInt(21845)
      (exact 1/3 would be 21845.333…; truncation gives 21845).
      (m × inv)[0][0] = mul(196608, 21845) = ofRawInt(65535) ≠ 65536 = one.
      Error: 1 LSB.

    For matrices where `det8 m` divides all adjugate entries exactly
    (e.g., permutation matrices, power-of-2 diagonal matrices), the
    identity holds.  `native_decide` confirms it for the identity matrix
    (see `identity8_self_inverse` and `det_self_inverse_identity` below).

    TODO(lean-port): Prove one of:
    (a) A bounded-error variant: each entry of `m × inv` is within 1 LSB
        of `identity8`.  This requires bounding the accumulated truncation
        error through 8 multiply-accumulate steps.
    (b) An exact version with a precondition that det8 m divides all
        cofactor products exactly (e.g., det8 m is a power of 2, or
        all entries are small enough to avoid truncation).
    (c) A version over ℚ using Mathlib's matrix library, where the
        Laplace cofactor identity has a clean proof. -/
/-- Entry-wise approximate equality of two 8×8 matrices within a given tolerance. -/
def matrixApproxEq (a b : Matrix8) (tolerance : Q16_16) : Prop :=
  ∀ i j : Fin 8, (abs (sub (getEntry a i.val j.val) (getEntry b i.val j.val))).toInt ≤ tolerance.toInt

/-- If matrixInverse returns `some inv`, then `m × inv` is approximately `I`
    within a bounded truncation error `ε`. -/
theorem det_self_inverse_approx {m : Matrix8} {inv : Matrix8} (ε : Q16_16)
    (h : matrixInverse m = some inv) :
    matrixApproxEq (matrixMultiply m inv) identity8 ε := by
  sorry

/-- If all division and multiplication operations are exact (no truncation),
    then `m × inv = I` holds exactly. -/
theorem det_self_inverse_exact {m : Matrix8} {inv : Matrix8}
    (h : matrixInverse m = some inv)
    (h_div_exact : ∀ i j : Fin 8, ((getEntry (adjugate m) j.val i.val).toInt * 65536) % (det8 m).toInt = 0)
    (h_mul_exact : ∀ i j k : Fin 8, ((getEntry m i.val k.val).toInt * (getEntry inv k.val j.val).toInt) % 65536 = 0) :
    matrixMultiply m inv = identity8 := by
  sorry

/-- The 8×8 identity matrix is its own inverse.  Proved by computation. -/
theorem identity8_self_inverse :
    matrixInverse identity8 = some identity8 := by
  native_decide

/-- Multiplying the 8×8 identity by itself yields the identity. -/
theorem identity8_mul_self :
    matrixMultiply identity8 identity8 = identity8 := by
  native_decide

/-- det(identity8) = 1 in Q16_16. -/
theorem det8_identity :
    det8 identity8 = one := by
  native_decide

/-- `det_self_inverse` holds for the identity matrix: if
    `matrixInverse identity8 = some inv`, then `identity8 × inv = identity8`.
    Follows from `identity8_self_inverse` and `identity8_mul_self`. -/
theorem det_self_inverse_identity {inv : Matrix8}
    (h : matrixInverse identity8 = some inv) :
    matrixMultiply identity8 inv = identity8 := by
  have hinv : inv = identity8 := by
    rw [identity8_self_inverse] at h
    exact (Option.some_injective _ h).symm
  subst hinv
  exact identity8_mul_self

/-- Cayley-transformed skew-symmetric matrix is orthogonal:
    Q^T Q = I.  Follows from the algebraic identity
    (I-A)(I+A)^{-1} · ((I-A)(I+A)^{-1})^T = I when A^T = -A.
    TODO(lean-port): Formalize skew-symmetry premise and prove. -/
theorem cayley_is_orthogonal {skew : Matrix8} {q : Matrix8}
    (_h : cayleyTransform skew = some q) :
    -- Stated informally: the result should be orthogonal.
    -- Full formalization needs matrix-transpose and product lemmas.
    True := by
  trivial

-- ═══════════════════════════════════════════════════════════════════════════
-- §10  Executable witnesses
-- ═══════════════════════════════════════════════════════════════════════════

-- 2×2 determinant witness: [[1,0],[0,1]] → 1.0
-- expect: 65536 (raw for 1.0)
#eval (det2 #[#[one, zero], #[zero, one]]).toInt

-- 2×2 determinant witness: [[2,3],[1,4]] → 2*4 - 3*1 = 5
-- expect: 327680 (raw for 5.0 = 5 * 65536)
#eval (det2 #[#[ofInt 2, ofInt 3], #[ofInt 1, ofInt 4]]).toInt

-- 8×8 identity determinant → 1.0
-- expect: 65536
#eval! (det8 identity8).toInt

-- matrixInverse of identity → some identity
-- expect: some (8×8 matrix of ones on diagonal)
#eval! (matrixInverse identity8).map (fun m => (getEntry m 0 0).toInt)

-- matrixMultiply I I = I
-- expect: 65536 (one on diagonal)
#eval! (getEntry (matrixMultiply identity8 identity8) 0 0).toInt
-- expect: 0 (zero off diagonal)
#eval! (getEntry (matrixMultiply identity8 identity8) 0 1).toInt

-- Cayley transform of zero matrix → (I)(I)^{-1} = I
-- expect: 65536 (one on diagonal)
#eval! match cayleyTransform (Array.replicate 8 (Array.replicate 8 zero)) with
       | some q => (getEntry q 0 0).toInt
       | none   => (-1 : Int)

-- det_self_inverse counterexample: diag(3,1,...,1) has 1-LSB error.
-- det(m) = 3 (Q16_16: 196608); entry (0,0) of m × m⁻¹ = 65535 ≠ 65536.
-- This demonstrates that det_self_inverse is not exactly true in Q16_16.
-- expect: 65535 (one LSB below identity)
#eval! let m := Array.ofFn (n := 8) fun (i : Fin 8) =>
          Array.ofFn (n := 8) fun (j : Fin 8) =>
            if i.val = j.val then (if i.val = 0 then ofInt 3 else one) else zero
       let inv := (matrixInverse m).getD identity8
       (getEntry (matrixMultiply m inv) 0 0).toInt

end Semantics.AdjugateMatrix
