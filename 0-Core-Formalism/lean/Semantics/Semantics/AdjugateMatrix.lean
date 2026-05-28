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
-- §9  Theorems (stubs — proofs deferred to TODO(lean-port))
-- ═══════════════════════════════════════════════════════════════════════════

/-- If matrixInverse returns `some inv`, then `m × inv = I`.
    TODO(lean-port): Prove from the algebraic identity A·adj(A) = det(A)·I
    and the cancellation det(A) ≠ 0 → A·(adj(A)/det(A)) = I.
    The fixed-point saturation complicates the proof; a bounded-error
    version may be more tractable. -/
theorem det_self_inverse {m : Matrix8} {inv : Matrix8}
    (h : matrixInverse m = some inv) :
    matrixMultiply m inv = identity8 := by
  sorry

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

end Semantics.AdjugateMatrix
