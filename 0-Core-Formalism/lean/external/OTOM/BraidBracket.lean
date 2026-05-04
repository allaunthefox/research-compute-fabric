/-
BraidBracket.lean - Bracket Shell for Braid Strand Admissibility

Brackets bound the flow. Each braid strand carries a bracket shell that
encodes local admissibility geometry.

Key rule: merge in linear space first, derive bracket afterward.
-/

import Semantics.DynamicCanal

namespace Semantics.BraidBracket

open DynamicCanal

/-- PhaseVec: ℝ² accumulator for AMMR (Q16.16 fixed-point) -/
structure PhaseVec where
  x : Fix16
  y : Fix16
  deriving Repr, DecidableEq, BEq

namespace PhaseVec

def zero : PhaseVec := { x := Fix16.zero, y := Fix16.zero }

def add (p q : PhaseVec) : PhaseVec :=
  if p.x.raw == 0 && p.y.raw == 0 then q
  else if q.x.raw == 0 && q.y.raw == 0 then p
  else { x := Fix16.add p.x q.x, y := Fix16.add p.y q.y }

def neg (p : PhaseVec) : PhaseVec :=
  { x := Fix16.neg p.x, y := Fix16.neg p.y }

def isZero (p : PhaseVec) : Bool :=
  p.x.raw == 0 && p.y.raw == 0

/-- Octagonal norm approximation: κ ≈ max(|x|,|y|) + (3/8)·min(|x|,|y|) -/
def normApprox (p : PhaseVec) : Fix16 :=
  let ax := if p.x.raw < 0x80000000 then p.x else Fix16.neg p.x
  let ay := if p.y.raw < 0x80000000 then p.y else Fix16.neg p.y
  let hi := if ax.raw > ay.raw then ax else ay
  let lo := if ax.raw > ay.raw then ay else ax
  -- 3/8 = 0x00006000 in Q16.16
  let lo38 := Fix16.mk ((lo.raw.toNat * 0x6000 / 0x10000).toUInt32)
  Fix16.add hi lo38

end PhaseVec


/-- BraidBracket: local admissibility geometry shell

  C(z, μ) where z is phase accumulation and μ is the slot/transport parameter.
  The bracket bounds the strand's accumulated state.
-/
structure BraidBracket where
  lower : Fix16
  upper : Fix16
  gap   : Fix16
  kappa : Fix16
  phi   : Fix16
  admissible : Bool
  deriving Repr, DecidableEq, BEq

namespace BraidBracket

/-- Zero bracket (initial state) -/
def zero : BraidBracket :=
  { lower := Fix16.zero
  , upper := Fix16.zero
  , gap   := Fix16.zero
  , kappa := Fix16.zero
  , phi   := Fix16.zero
  , admissible := true }

/-- Compute bracket from PhaseVec accumulator and slot parameter μ

  C(z, μ): derive lower, upper, gap from accumulated phase state.
  This is the core bracket calculus operator.
-/
def fromPhaseVec (z : PhaseVec) (μ : Fix16) : BraidBracket :=
  let κ := z.normApprox
  -- φ = 0 when z = (0,0)
  let ϕ := if z.isZero then Fix16.zero else
    -- atan2 approximation placeholder (actual would use Cordic or table)
    Fix16.mk 0x00008000  -- π/4 placeholder
  let lo := Fix16.sub κ μ
  let up := Fix16.add κ μ
  let g := Fix16.sub up lo
  { lower := lo
  , upper := up
  , gap   := g
  , kappa := κ
  , phi   := ϕ
  , admissible := lo.raw <= up.raw }

/-- Check gap conservation (bracketed DIAT property) -/
def gapConserved (b : BraidBracket) : Bool :=
  let expectedGap := Fix16.sub b.upper b.lower
  b.gap.raw == expectedGap.raw

/-- Componentwise addition of bracket bounds (for residual calculation) -/
def addComponentwise (x y : BraidBracket) : BraidBracket :=
  { lower := Fix16.add x.lower y.lower
  , upper := Fix16.add x.upper y.upper
  , gap   := Fix16.add x.gap y.gap
  , kappa := Fix16.add x.kappa y.kappa
  , phi   := Fix16.add x.phi y.phi
  , admissible := x.admissible && y.admissible }

/-- Crossing residual: Rᵢⱼ = Bᵢⱼ - (Bᵢ + Bⱼ)

  Measures the interaction energy between two merged strands.
-/
def crossingResidual (bij bi bj : BraidBracket) : BraidBracket :=
  let sum := addComponentwise bi bj
  { lower := Fix16.sub bij.lower sum.lower
  , upper := Fix16.sub bij.upper sum.upper
  , gap   := Fix16.sub bij.gap sum.gap
  , kappa := Fix16.sub bij.kappa sum.kappa
  , phi   := Fix16.sub bij.phi sum.phi
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

def leafEntry (slot : UInt32) (z : PhaseVec) (μ : Fix16) (ts : UInt64) : AVMREntry :=
  { slot := slot
  , phaseAcc := z
  , bracket := BraidBracket.fromPhaseVec z μ
  , residual := none
  , timestamp := ts }

def crossingEntry (slot : UInt32) (z : PhaseVec) (μ : Fix16)
                  (res : BraidBracket) (ts : UInt64) : AVMREntry :=
  { slot := slot
  , phaseAcc := z
  , bracket := BraidBracket.fromPhaseVec z μ
  , residual := some res
  , timestamp := ts }

end AVMREntry


#eval (PhaseVec.zero).normApprox.raw
#eval (BraidBracket.zero).admissible


/-- Row 80: Cosine Similarity between two PhaseVec accumulators
    cos(θ) = (a·b) / (|a| · |b|) — using octagonal norm approximation
-/
def cosineSimilarity (a b : PhaseVec) : Fix16 :=
  let dot := Fix16.add (Fix16.mul a.x b.x) (Fix16.mul a.y b.y)
  let normA := a.normApprox
  let normB := b.normApprox
  let denom := Fix16.mul normA normB
  if denom.raw == 0 then Fix16.zero
  else Fix16.div dot denom

/-- Row 81: Gradient Alignment — cosine of angle between gradient vectors
    alignment = ∇gᵢ · ∇gⱼ / (‖∇gᵢ‖ · ‖∇gⱼ‖)
    Reuses cosineSimilarity on gradient PhaseVecs.
-/
def gradientAlignment (gradI gradJ : PhaseVec) : Fix16 :=
  cosineSimilarity gradI gradJ

/-- Row 82: Phase Accumulation — discrete line integral Σ y · dx
    phase += Σ y · dx along trajectory
    Inputs: parallel arrays of (y, dx) samples.
-/
def phaseAccumulation (ys dxs : Array Fix16) : Fix16 :=
  let n := Nat.min ys.size dxs.size
  (Array.range n).foldl (fun (acc : Fix16) (i : Nat) =>
    Fix16.add acc (Fix16.mul ys[i]! dxs[i]!)
  ) Fix16.zero

#eval cosineSimilarity { x := Fix16.mk 65536, y := Fix16.zero }
                       { x := Fix16.mk 65536, y := Fix16.zero }  -- expect 1.0

end Semantics.BraidBracket
