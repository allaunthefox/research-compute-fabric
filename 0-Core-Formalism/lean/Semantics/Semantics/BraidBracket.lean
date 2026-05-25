/-
BraidBracket.lean - Bracket Shell for Braid Strand Admissibility

Brackets bound the flow. Each braid strand carries a bracket shell that
encodes local admissibility geometry.

Key rule: merge in linear space first, derive bracket afterward.
-/

import Semantics.DynamicCanal

set_option linter.dupNamespace false

namespace Semantics.BraidBracket

open DynamicCanal

/-- PhaseVec: ℝ² accumulator for AMMR (Q16.16 fixed-point) -/
structure PhaseVec where
  x : Q16_16
  y : Q16_16
  deriving Repr, DecidableEq, BEq

namespace PhaseVec

def zero : PhaseVec := { x := Q16_16.zero, y := Q16_16.zero }

def add (p q : PhaseVec) : PhaseVec :=
  if p.x.val == 0 && p.y.val == 0 then q
  else if q.x.val == 0 && q.y.val == 0 then p
  else { x := Q16_16.add p.x q.x, y := Q16_16.add p.y q.y }

def neg (p : PhaseVec) : PhaseVec :=
  { x := Q16_16.neg p.x, y := Q16_16.neg p.y }

def isZero (p : PhaseVec) : Bool :=
  p.x.val == 0 && p.y.val == 0

/-- Octagonal norm approximation: κ ≈ max(|x|,|y|) + (3/8)·min(|x|,|y|) -/
def normApprox (p : PhaseVec) : Q16_16 :=
  let ax := if p.x.val < 0 then p.x else Q16_16.neg p.x
  let ay := if p.y.val < 0 then p.y else Q16_16.neg p.y
  let hi := if ax.val > ay.val then ax else ay
  let lo := if ax.val > ay.val then ay else ax
  -- 3/8 = 0x00006000 in Q16.16
  let lo38 : Q16_16 := Q16_16.ofRawInt ((lo.val.toNat * 0x6000 / 0x10000) : Int)
  Q16_16.add hi lo38

end PhaseVec


/-- BraidBracket: local admissibility geometry shell

  C(z, μ) where z is phase accumulation and μ is the slot/transport parameter.
  The bracket bounds the strand's accumulated state.
-/
structure BraidBracket where
  lower : Q16_16
  upper : Q16_16
  gap   : Q16_16
  kappa : Q16_16
  phi   : Q16_16
  admissible : Bool
  deriving Repr, DecidableEq, BEq

namespace BraidBracket

/-- Zero bracket (initial state) -/
def zero : BraidBracket :=
  { lower := Q16_16.zero
  , upper := Q16_16.zero
  , gap   := Q16_16.zero
  , kappa := Q16_16.zero
  , phi   := Q16_16.zero
  , admissible := true }

/-- Compute bracket from PhaseVec accumulator and slot parameter μ

  C(z, μ): derive lower, upper, gap from accumulated phase state.
  This is the core bracket calculus operator.
-/
def fromPhaseVec (z : PhaseVec) (μ : Q16_16) : BraidBracket :=
  let κ := z.normApprox
  -- φ = 0 when z = (0,0)
  let ϕ := if z.isZero then Q16_16.zero else
    -- atan2 approximation placeholder (actual would use Cordic or table)
    Q16_16.ofRawInt 0x00008000 -- π/4 placeholder
  let lo := Q16_16.sub κ μ
  let up := Q16_16.add κ μ
  let g := Q16_16.sub up lo
  { lower := lo
  , upper := up
  , gap   := g
  , kappa := κ
  , phi   := ϕ
  , admissible := lo.val <= up.val }

/-- Check gap conservation (bracketed DIAT property) -/
def gapConserved (b : BraidBracket) : Bool :=
  let expectedGap := Q16_16.sub b.upper b.lower
  b.gap.val == expectedGap.val

/-- Componentwise addition of bracket bounds (for residual calculation) -/
def addComponentwise (x y : BraidBracket) : BraidBracket :=
  { lower := Q16_16.add x.lower y.lower
  , upper := Q16_16.add x.upper y.upper
  , gap   := Q16_16.add x.gap y.gap
  , kappa := Q16_16.add x.kappa y.kappa
  , phi   := Q16_16.add x.phi y.phi
  , admissible := x.admissible && y.admissible }

/-- Crossing residual: Rᵢⱼ = Bᵢⱼ - (Bᵢ + Bⱼ)

  Measures the interaction energy between two merged strands.
-/
def crossingResidual (bij bi bj : BraidBracket) : BraidBracket :=
  let sum := addComponentwise bi bj
  { lower := Q16_16.sub bij.lower sum.lower
  , upper := Q16_16.sub bij.upper sum.upper
  , gap   := Q16_16.sub bij.gap sum.gap
  , kappa := Q16_16.sub bij.kappa sum.kappa
  , phi   := Q16_16.sub bij.phi sum.phi
  , admissible := bij.admissible && bi.admissible && bj.admissible }

end BraidBracket


/-- AVMR (Append-Only Vector Magnitude Registry) hierarchy entry

  Stores the immutable history of braid operations for audit/attestation.
-/
structure AVMREntry where
  slot      : UInt32
  phaseAcc  : PhaseVec
  bracket   : BraidBracket
  residual  : Option BraidBracket  -- Some if from crossing, None if leaf
  timestamp : UInt64
  deriving Repr, DecidableEq, BEq

namespace AVMREntry

def leafEntry (slot : UInt32) (z : PhaseVec) (μ : Q16_16) (ts : UInt64) : AVMREntry :=
  { slot := slot
  , phaseAcc := z
  , bracket := BraidBracket.fromPhaseVec z μ
  , residual := none
  , timestamp := ts }

def crossingEntry (slot : UInt32) (z : PhaseVec) (μ : Q16_16)
                  (res : BraidBracket) (ts : UInt64) : AVMREntry :=
  { slot := slot
  , phaseAcc := z
  , bracket := BraidBracket.fromPhaseVec z μ
  , residual := some res
  , timestamp := ts }

end AVMREntry


#eval (PhaseVec.zero).normApprox.val
#eval (BraidBracket.zero).admissible


/-- Row 80: Cosine Similarity between two PhaseVec accumulators
    cos(θ) = (a·b) / (|a| · |b|) — using octagonal norm approximation
-/
def cosineSimilarity (a b : PhaseVec) : Q16_16 :=
  let dot := Q16_16.add (Q16_16.mul a.x b.x) (Q16_16.mul a.y b.y)
  let normA := a.normApprox
  let normB := b.normApprox
  let denom := Q16_16.mul normA normB
  if denom.val == 0 then Q16_16.zero
  else Q16_16.div dot denom

/-- Row 81: Gradient Alignment — cosine of angle between gradient vectors
    alignment = ∇gᵢ · ∇gⱼ / (‖∇gᵢ‖ · ‖∇gⱼ‖)
    Reuses cosineSimilarity on gradient PhaseVecs.
-/
def gradientAlignment (gradI gradJ : PhaseVec) : Q16_16 :=
  cosineSimilarity gradI gradJ

/-- Row 82: Phase Accumulation — discrete line integral Σ y · dx
    phase += Σ y · dx along trajectory
    Inputs: parallel arrays of (y, dx) samples.
-/
def phaseAccumulation (ys dxs : Array Q16_16) : Q16_16 :=
  let n := Nat.min ys.size dxs.size
  (Array.range n).foldl (fun (acc : Q16_16) (i : Nat) =>
    Q16_16.add acc (Q16_16.mul ys[i]! dxs[i]!)
  ) Q16_16.zero

#eval cosineSimilarity { x := Q16_16.ofRawInt 65536, y := Q16_16.zero }
                       { x := Q16_16.ofRawInt 65536, y := Q16_16.zero }  -- expect 1.0

end Semantics.BraidBracket
