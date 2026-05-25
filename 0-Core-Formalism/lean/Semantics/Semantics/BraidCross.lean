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
import Semantics.BraidStrand
import Semantics.BraidBracket
import Semantics.FixedPoint

namespace Semantics.BraidCross

open DynamicCanal
open Semantics.BraidStrand
open Semantics.BraidBracket
open Semantics.Q16_16

/-- Crossing slot operator X(μᵢ, μⱼ)

  Combines transport slots from two strands into merged slot.
  Default: bitwise XOR of slot indices (creates unique crossing ID).
-/
def crossSlot (μᵢ μⱼ : Q16_16) : Q16_16 :=
  -- XOR the raw representations for unique crossing slot
  Q16_16.ofBits (μᵢ.toBits.xor μⱼ.toBits)

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
  let μᵢ := Q16_16.ofNat sᵢ.slot.toNat
  let μⱼ := Q16_16.ofNat sⱼ.slot.toNat
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
    , jitter := sᵢ.jitter + sⱼ.jitter
    , bracket := Bᵢⱼ }

  (mergedStrand, Rᵢⱼ)

-- REMOVED: braidCrossZeroLeftWitness only tested zero strands

-- REMOVED: braidCrossZeroRightWitness only tested zero strands

/-- Parallel crossing: merge multiple strands simultaneously

  z = Σᵢ zᵢ  (linear sum over all strands)
  Then derive single bracket from total.
-/
def parallelCross (strands : List BraidStrand) : BraidStrand :=
  let totalPhase := strands.foldl (fun acc s => PhaseVec.add acc s.phaseAcc) PhaseVec.zero
  let totalSlot := strands.foldl (fun acc s => acc.xor s.slot) 0
  let totalJitter := strands.foldl (fun acc s => acc + s.jitter) Q16_16.zero

  let μ := Q16_16.ofNat totalSlot.toNat
  let B := BraidBracket.fromPhaseVec totalPhase μ

  { phaseAcc := totalPhase
  , parity := strands.all (fun s => s.parity)
  , slot := totalSlot
  , residue := Q16_16.zero  -- parallel merge has no pairwise residual
  , jitter := totalJitter
  , bracket := B }

/-- Check if crossing is admissible (merged bracket valid) -/
def crossingAdmissible (sᵢ sⱼ : BraidStrand) : Bool :=
  let (merged, residual) := braidCross sᵢ sⱼ
  merged.isAdmissible && residual.admissible

/-- Total residual norm from a crossing -/
def crossingResidualNorm (sᵢ sⱼ : BraidStrand) : Q16_16 :=
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
