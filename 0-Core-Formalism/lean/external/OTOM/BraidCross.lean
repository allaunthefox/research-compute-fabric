/-
BraidCross.lean - Braid Crossing and Strand Merge Operations

Crossing topology: strands interact, merge, and generate residuals.
The merge rule remains linear on phaseAcc; bracket is recomputed after.

zᵢⱼ = zᵢ + zⱼ  (linear merge)
μᵢⱼ = X(μᵢ, μⱼ)  (crossing slot operator)
Bᵢⱼ = C(zᵢⱼ, μᵢⱼ)  (bracket from merged state)
Rᵢⱼ = Bᵢⱼ - (Bᵢ + Bⱼ)  (interaction residual)
-/

import Semantics.DynamicCanal
import Semantics.BraidBracket
import Semantics.BraidStrand

namespace Semantics.BraidCross

open DynamicCanal
open Semantics.BraidBracket
open Semantics.BraidStrand

/-- Crossing slot operator X(μᵢ, μⱼ)

  Combines transport slots from two strands into merged slot.
  Default: bitwise XOR of slot indices (creates unique crossing ID).
-/
def crossSlot (μᵢ μⱼ : Fix16) : Fix16 :=
  -- XOR the raw representations for unique crossing slot
  Fix16.mk (μᵢ.raw.xor μⱼ.raw)

/-- BraidCross: merge two strands into a crossing

  This is THE fundamental merge operation. It:
  1. Linearly adds phase accumulations: zᵢⱼ = zᵢ + zⱼ
  2. Computes crossed slot: μᵢⱼ = X(μᵢ, μⱼ)
  3. Derives new bracket: Bᵢⱼ = C(zᵢⱼ, μᵢⱼ)
  4. Calculates residual: Rᵢⱼ = Bᵢⱼ - (Bᵢ + Bⱼ)

  Key: merge in linear space first, derive bracket afterward.
-/
def braidCross (sᵢ sⱼ : BraidStrand) : BraidStrand × BraidBracket :=
  -- Linear merge of phase accumulations
  let zᵢⱼ := PhaseVec.add sᵢ.phaseAcc sⱼ.phaseAcc

  -- Crossing slot operator
  let μᵢ := Fix16.mk sᵢ.slot
  let μⱼ := Fix16.mk sⱼ.slot
  let μᵢⱼ := crossSlot μᵢ μⱼ

  -- Derive new bracket from merged state (NOT from merging brackets)
  let Bᵢⱼ := BraidBracket.fromPhaseVec zᵢⱼ μᵢⱼ

  -- Calculate crossing residual
  let Rᵢⱼ := BraidBracket.crossingResidual Bᵢⱼ sᵢ.bracket sⱼ.bracket

  -- Construct merged strand
  let mergedStrand : BraidStrand :=
    { phaseAcc := zᵢⱼ
    , parity := sᵢ.parity && sⱼ.parity
    , slot := sᵢ.slot.xor sⱼ.slot  -- unique crossing slot
    , residue := Rᵢⱼ.kappa  -- store residual magnitude
    , jitter := Fix16.add sᵢ.jitter sⱼ.jitter
    , bracket := Bᵢⱼ }

  (mergedStrand, Rᵢⱼ)

/-- Concrete left-identity witness for the zero strand. -/
theorem braidCrossZeroLeftWitness :
  (braidCross (BraidStrand.zero 0) (BraidStrand.zero 1)).1.phaseAcc = PhaseVec.zero := by
  native_decide

/-- Concrete right-identity witness for the zero strand. -/
theorem braidCrossZeroRightWitness :
  (braidCross (BraidStrand.zero 1) (BraidStrand.zero 0)).1.phaseAcc = PhaseVec.zero := by
  native_decide

/-- Parallel crossing: merge multiple strands simultaneously

  z = Σᵢ zᵢ  (linear sum over all strands)
  Then derive single bracket from total.
-/
def parallelCross (strands : List BraidStrand) : BraidStrand :=
  let totalPhase := strands.foldl (fun acc s => PhaseVec.add acc s.phaseAcc) PhaseVec.zero
  let totalSlot := strands.foldl (fun acc s => acc.xor s.slot) 0
  let totalJitter := strands.foldl (fun acc s => Fix16.add acc s.jitter) Fix16.zero

  let μ := Fix16.mk totalSlot
  let B := BraidBracket.fromPhaseVec totalPhase μ

  { phaseAcc := totalPhase
  , parity := strands.all (fun s => s.parity)
  , slot := totalSlot
  , residue := Fix16.zero  -- parallel merge has no pairwise residual
  , jitter := totalJitter
  , bracket := B }

/-- Check if crossing is admissible (merged bracket valid) -/
def crossingAdmissible (sᵢ sⱼ : BraidStrand) : Bool :=
  let (merged, residual) := braidCross sᵢ sⱼ
  merged.isAdmissible && residual.admissible

/-- Total residual norm from a crossing -/
def crossingResidualNorm (sᵢ sⱼ : BraidStrand) : Fix16 :=
  let (_, residual) := braidCross sᵢ sⱼ
  residual.kappa


/-- Crossing history for AVMR audit trail -/
structure CrossingHistory where
  leftSlot  : UInt32
  rightSlot : UInt32
  mergedSlot : UInt32
  residual  : BraidBracket
  timestamp : UInt64
  deriving Repr, DecidableEq

namespace CrossingHistory

def fromCross (sᵢ sⱼ : BraidStrand) (ts : UInt64) : CrossingHistory :=
  let (_, residual) := braidCross sᵢ sⱼ
  { leftSlot := sᵢ.slot
  , rightSlot := sⱼ.slot
  , mergedSlot := sᵢ.slot.xor sⱼ.slot
  , residual := residual
  , timestamp := ts }

end CrossingHistory


#eval let s1 := BraidStrand.zero 1
      let s2 := BraidStrand.zero 2
      let (m, _) := braidCross s1 s2
      m.slot

end Semantics.BraidCross
