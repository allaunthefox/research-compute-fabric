-- Semantics.PIST.Spectral — Q16_16 proof-trace spectral feature extraction
--
-- Ports the domain logic from pist_trace_classify_mcp.py into Lean:
--   • power_iteration(matrix, max_iter=100)
--   • compute_spectral(matrix) → SpectralProfile
--   • classify_tactic_from_name(name) → TacticFamily
--
-- Python source:      4-Infrastructure/shim/pist_trace_classify_mcp.py
-- Python functions:   power_iteration, compute_spectral, classify_tactic_from_name
-- BOUNDARY comment:   Semantics.PIST.Spectral (this file)
--
-- The Python shim remains responsible for JSON I/O, RDS queries, and MCP
-- protocol. This module is the authoritative specification for the
-- spectral arithmetic and tactic inference.

import Semantics.FixedPoint

namespace Semantics.PIST.Spectral

open Semantics.FixedPoint
open Semantics.Q16_16

-- ─────────────────────────────────────────────────────────────────────────────
-- §1  Tactic family enumeration
--     Ports classify_tactic_from_name() — name-based tactic-family lookup.
-- ─────────────────────────────────────────────────────────────────────────────

/-- The eight proof-tactic families inferred by name heuristic. -/
inductive TacticFamily where
  | rewrite       -- "rw" in name
  | normalization -- "simp" in name
  | arithmetic    -- "omega" in name
  | induction     -- "induct" in name
  | algebraic     -- "ring" or "calc" in name
  | case_analysis -- "cases" or "constructor" in name
  | discharge     -- "apply", "intro", "have", or "logic" in name
  | reflexivity   -- "rfl" in name
  | unknown       -- no match
  deriving Repr, DecidableEq, BEq

/-- Classify a theorem name into a tactic family.
    Mirrors `classify_tactic_from_name` in pist_trace_classify_mcp.py. -/
def classifyTacticFromName (name : String) : TacticFamily :=
  let n := name.toLower
  if n.containsSubstr "rw"          then .rewrite
  else if n.containsSubstr "simp"   then .normalization
  else if n.containsSubstr "omega"  then .arithmetic
  else if n.containsSubstr "induct" then .induction
  else if n.containsSubstr "ring" ||
          n.containsSubstr "calc"   then .algebraic
  else if n.containsSubstr "cases" ||
          n.containsSubstr "constructor" then .case_analysis
  else if n.containsSubstr "apply" ||
          n.containsSubstr "intro"  ||
          n.containsSubstr "have"   ||
          n.containsSubstr "logic"  then .discharge
  else if n.containsSubstr "rfl"    then .reflexivity
  else .unknown

-- ─────────────────────────────────────────────────────────────────────────────
-- §2  Integer square root
--     Newton's method on integers: isqrt(n) = floor(√n).
-- ─────────────────────────────────────────────────────────────────────────────

/-- Integer square root via Newton's method. Returns floor(√n). -/
def isqrt (n : Int) : Int :=
  if n ≤ 0 then 0
  else
    let rec loop (x : Int) (fuel : Nat) : Int :=
      match fuel with
      | 0     => x
      | f + 1 =>
        let x' := (x + n / x) / 2
        if x' ≥ x then x else loop x' f
    loop (n / 2 + 1) 64

-- ─────────────────────────────────────────────────────────────────────────────
-- §3  Matrix-vector helpers (Array-based, pure Int arithmetic)
-- ─────────────────────────────────────────────────────────────────────────────

/-- Safe index into an Array (Array Int). Returns 0 for out-of-bounds. -/
@[inline]
private def getEntry (mat : Array (Array Int)) (i j : Nat) : Int :=
  mat.getD i #[] |>.getD j 0

/-- Row sum of an int matrix row. -/
@[inline]
private def rowSum (mat : Array (Array Int)) (i n : Nat) : Int :=
  (List.range n).foldl (fun acc j => acc + getEntry mat i j) 0

/-- Symmetrize a matrix: sym[i][j] = (mat[i][j] + mat[j][i]) / 2. -/
private def symmetrize (mat : Array (Array Int)) (n : Nat) : Array (Array Int) :=
  Array.ofFn (n := n) fun i =>
    Array.ofFn (n := n) fun j =>
      (getEntry mat i.val j.val + getEntry mat j.val i.val) / 2

/-- Laplacian of a symmetrized matrix: L[i][j] = deg(i) if i=j else −sym[i][j]. -/
private def buildLaplacian (sym : Array (Array Int)) (n : Nat) : Array (Array Int) :=
  Array.ofFn (n := n) fun i =>
    let deg := rowSum sym i.val n
    Array.ofFn (n := n) fun j =>
      if i.val = j.val then deg else -(getEntry sym i.val j.val)

/-- AᵀA: (AᵀA)[i][j] = Σ_k mat[k][i] * mat[k][j]. -/
private def buildATA (mat : Array (Array Int)) (n : Nat) : Array (Array Int) :=
  Array.ofFn (n := n) fun i =>
    Array.ofFn (n := n) fun j =>
      (List.range n).foldl (fun acc k =>
        acc + getEntry mat k i.val * getEntry mat k j.val) 0

-- ─────────────────────────────────────────────────────────────────────────────
-- §4  Power iteration (Q16_16 fixed-point)
--     Ports power_iteration(matrix, max_iter=100).
-- ─────────────────────────────────────────────────────────────────────────────

/-- L2 norm squared of a Q16_16 vector (raw Int to avoid saturation). -/
private def normSqRaw (v : Array Q16_16) : Int :=
  v.foldl (fun acc x => acc + x.toInt * x.toInt) 0

/-- Matrix-vector multiply: (mat × v)[i] = Σ_j mat[i][j] * v[j].
    mat entries are raw Int; v components are Q16_16. Result in Q16_16. -/
private def matVecMul (mat : Array (Array Int)) (n : Nat) (v : Array Q16_16) : Array Q16_16 :=
  Array.ofFn (n := n) fun i =>
    let s : Int := (List.range n).foldl (fun acc j =>
      acc + getEntry mat i.val j * (v.getD j zero).toInt) 0
    ofRawInt s

/-- Power iteration: dominant eigenvalue of mat as Q16_16 raw integer.
    max_iter=100 in Python; we use Nat fuel. -/
def powerIteration (mat : Array (Array Int)) (maxIter : Nat := 100) : Q16_16 :=
  let n := mat.size
  if n = 0 then zero
  else
    -- Initial uniform vector: 1/n in Q16_16 = 65536 / n
    let initVal := ofRawInt ((q16Scale : Int) / (n : Int))
    let v₀ : Array Q16_16 := Array.replicate n initVal
    let rec iterate (v : Array Q16_16) (fuel : Nat) : Array Q16_16 :=
      match fuel with
      | 0     => v
      | f + 1 =>
        let mv  := matVecMul mat n v
        let nm2 := normSqRaw mv
        if nm2 ≤ 0 then v
        else
          let nm := isqrt nm2
          if nm = 0 then v
          else
            -- Normalize: vn[i] = mv[i] * q16Scale / nm
            let vn := mv.map (fun x => ofRawInt (x.toInt * q16Scale / nm))
            iterate vn f
    let vFinal := iterate v₀ maxIter
    -- Rayleigh quotient: v·(Mv) / (v·v)
    let mv  := matVecMul mat n vFinal
    let num : Int := (List.range n).foldl (fun acc i =>
      acc + (vFinal.getD i zero).toInt * (mv.getD i zero).toInt) 0
    let den : Int := normSqRaw vFinal
    if den ≤ 0 then zero
    else ofRawInt (num * q16Scale / den)

-- ─────────────────────────────────────────────────────────────────────────────
-- §5  Spectral profile structure
-- ─────────────────────────────────────────────────────────────────────────────

/-- Full v2 spectral profile from a proof transition matrix.
    Mirrors the dict returned by compute_spectral() in the Python shim.
    All values are Q16_16. Integer-count fields (matrix_size, rank,
    trace_val, laplacian_zero_count) are stored as Q16_16.ofRawInt n. -/
structure SpectralProfile where
  matrix_size              : Q16_16  -- n
  rank                     : Q16_16  -- count of non-zero rows
  spectral_gap              : Q16_16  -- ev_max − ev_second
  density                   : Q16_16  -- total / n²
  trace_val                 : Q16_16  -- Σ mat[i][i]
  frobenius_norm            : Q16_16  -- isqrt(Σ cell²)
  laplacian_zero_count      : Q16_16  -- count of zero-degree rows
  adjacency_eigenvalue_max  : Q16_16  -- ev_max of symmetrized adjacency
  laplacian_eigenvalue_max  : Q16_16  -- ev_max of Laplacian
  singular_value_max        : Q16_16  -- √(max eigenvalue of AᵀA)
  deriving Repr

/-- Zero profile for empty or degenerate matrices. -/
def emptyProfile : SpectralProfile :=
  { matrix_size             := zero
    rank                    := zero
    spectral_gap              := zero
    density                   := zero
    trace_val                 := zero
    frobenius_norm            := zero
    laplacian_zero_count      := zero
    adjacency_eigenvalue_max  := zero
    laplacian_eigenvalue_max  := zero
    singular_value_max        := zero }

-- ─────────────────────────────────────────────────────────────────────────────
-- §6  computeSpectral
--     Ports compute_spectral(matrix) from pist_trace_classify_mcp.py.
-- ─────────────────────────────────────────────────────────────────────────────

/-- Compute the full spectral profile of a proof transition matrix.
    Mirrors compute_spectral() in pist_trace_classify_mcp.py.
    All floating-point operations are replaced with Q16_16 or integer arithmetic. -/
def computeSpectral (mat : Array (Array Int)) : SpectralProfile :=
  let n := mat.size
  if n = 0 then emptyProfile
  else
    let sym  := symmetrize mat n
    let lap  := buildLaplacian sym n

    -- Dominant eigenvalue of symmetrized adjacency matrix
    let evMax := powerIteration sym

    -- Second eigenvalue via shift-deflation:
    --   shifted[i][j] = sym[i][j] − 0.9*ev_max  (diagonal shift only)
    --   0.9 * 65536 = 58982   (Q16_16 raw for 0.9)
    let shiftAmt : Int := (evMax.toInt * 58982) / q16Scale
    let shiftedMat : Array (Array Int) :=
      Array.ofFn (n := n) fun i =>
        Array.ofFn (n := n) fun j =>
          let base := getEntry sym i.val j.val
          if i.val = j.val then base - shiftAmt else base
    let evShift  := powerIteration shiftedMat
    let evSecond : Q16_16 :=
      if evShift.toInt < evMax.toInt
      then ofRawInt (Int.natAbs (evMax.toInt - evShift.toInt) : Int)
      else evMax
    let spectralGap := sub evMax evSecond

    -- Laplacian dominant eigenvalue
    let lapMax := powerIteration lap

    -- Density = total / n²
    let total  : Int := mat.foldl (fun acc row => acc + row.foldl (· + ·) 0) 0
    let nSqI   : Int := (n * n : Nat)
    let density := if nSqI ≤ 0 then zero else ofRawInt (total * q16Scale / nSqI)

    -- Trace = Σ mat[i][i]
    let traceInt : Int := (List.range n).foldl (fun acc i => acc + getEntry mat i i) 0
    let traceVal := ofRawInt traceInt

    -- Frobenius norm = isqrt(Σ cell²)
    let frobSq   : Int := mat.foldl (fun acc row => acc + row.foldl (fun a c => a + c * c) 0) 0
    let frobNorm := ofRawInt (isqrt frobSq)

    -- Rank = count of rows with at least one non-zero entry
    let rankVal  : Int := mat.foldl (fun acc row =>
      acc + if row.any (· ≠ 0) then 1 else 0) 0

    -- Laplacian zero count = rows where off-diagonal sum = 0
    -- Python: |sum(row) - row[i]| < 1e-9 → exact integer: rowSum(i) - mat[i][i] = 0
    let lapZero  : Int := (List.range n).foldl (fun acc i =>
      let rs := rowSum mat i n
      let d  := getEntry mat i i
      acc + if rs - d = 0 then 1 else 0) 0

    -- Singular value max = sqrt(ev_max of AᵀA)
    let ataM     := buildATA mat n
    let ataEv    := powerIteration ataM
    let svMax    := if ataEv.toInt > 0 then sqrt ataEv else zero

    { matrix_size             := ofRawInt (n : Int)
      rank                    := ofRawInt rankVal
      spectral_gap              := spectralGap
      density                   := density
      trace_val                 := traceVal
      frobenius_norm            := frobNorm
      laplacian_zero_count      := ofRawInt lapZero
      adjacency_eigenvalue_max  := evMax
      laplacian_eigenvalue_max  := lapMax
      singular_value_max        := svMax }

-- ─────────────────────────────────────────────────────────────────────────────
-- §7  Executable witnesses
-- ─────────────────────────────────────────────────────────────────────────────

/-! ### TacticFamily classification witnesses -/

-- expect: Semantics.PIST.Spectral.TacticFamily.rewrite
#eval classifyTacticFromName "my_rw_lemma"
-- expect: Semantics.PIST.Spectral.TacticFamily.arithmetic
#eval classifyTacticFromName "add_comm_omega"
-- expect: Semantics.PIST.Spectral.TacticFamily.normalization
#eval classifyTacticFromName "simp_all_helper"
-- expect: Semantics.PIST.Spectral.TacticFamily.unknown
#eval classifyTacticFromName "my_theorem"
-- expect: Semantics.PIST.Spectral.TacticFamily.reflexivity
#eval classifyTacticFromName "rfl_test"

/-! ### Integer square root witnesses -/

-- expect: 3
#eval isqrt 9
-- expect: 4
#eval isqrt 16
-- expect: 14
#eval isqrt 200  -- floor(√200) = floor(14.14…) = 14
-- expect: 0
#eval isqrt 0

/-! ### Power iteration witness
    2×2 identity matrix → dominant eigenvalue = 1 (Q16_16 raw = 65536). -/

-- expect: 65536
#eval! (powerIteration #[#[1, 0], #[0, 1]]).toInt

/-! ### computeSpectral witness
    2×2 matrix [[1,1],[0,1]]: matrix_size=2, rank=2, trace=2. -/

-- expect: 2
#eval! (computeSpectral #[#[1, 1], #[0, 1]]).matrix_size.toInt
-- expect: 2
#eval! (computeSpectral #[#[1, 1], #[0, 1]]).rank.toInt
-- expect: 2
#eval! (computeSpectral #[#[1, 1], #[0, 1]]).trace_val.toInt

end Semantics.PIST.Spectral
