/-
BraidStrand.lean - Transport Topology with Bracket Shell

Braids carry the flow. Each strand accumulates PhaseVec contributions linearly
and carries a BraidBracket shell for local admissibility.

Hierarchy: DIAT leaf → AMMR vector → braid strand → bracket shell
-/

import Semantics.DynamicCanal
import Semantics.BraidBracket

namespace Semantics.BraidStrand

open DynamicCanal
open Semantics.BraidBracket

/-- BraidStrand: a single transport strand in the braid topology

  zᵢ = Σₖ Φᵢₖ  (linear AMMR accumulation)
  Bᵢ = C(zᵢ, μᵢ)  (bracket from accumulated state)
-/
structure BraidStrand where
  phaseAcc : PhaseVec    -- zᵢ: accumulated phase vector
  parity   : Bool        -- strand parity for crossing orientation
  slot     : UInt32      -- μᵢ: transport slot / channel assignment
  residue  : Fix16       -- residual from prior crossings
  jitter   : Fix16       -- timing/phase jitter bound
  bracket  : BraidBracket  -- C(zᵢ, μᵢ): admissibility shell
  deriving Repr, DecidableEq, BEq

namespace BraidStrand

/-- Create a fresh strand from initial phase contribution

  For DIAT leaf encoding: strand starts with single AMMR contribution.
-/
def fromLeaf (Φ : PhaseVec) (slot : UInt32) (μ : Fix16) : BraidStrand :=
  let z := Φ
  { phaseAcc := z
  , parity := true
  , slot := slot
  , residue := Fix16.zero
  , jitter := Fix16.zero
  , bracket := BraidBracket.fromPhaseVec z μ }

/-- Update bracket after phase accumulation changes

  Recompute C(z, μ) from current phaseAcc and slot.
  This is the correct pattern: merge linearly, then derive bracket.
-/
def updateBracket (s : BraidStrand) : BraidStrand :=
  let μ := Fix16.mk s.slot  -- slot as Q16.16 fraction
  { s with bracket := BraidBracket.fromPhaseVec s.phaseAcc μ }

/-- Add AMMR contribution to strand (linear accumulation)

  Φ is the local vector contribution from a mode/carrier.
  Bracket is NOT updated here — updateBracket must be called explicitly.
-/
def addContribution (s : BraidStrand) (Φ : PhaseVec) : BraidStrand :=
  { s with phaseAcc := PhaseVec.add s.phaseAcc Φ }

/-- Zero strand (identity element for merge) -/
def zero (slot : UInt32) : BraidStrand :=
  let z := PhaseVec.zero
  let μ := Fix16.mk slot
  { phaseAcc := z
  , parity := true
  , slot := slot
  , residue := Fix16.zero
  , jitter := Fix16.zero
  , bracket := BraidBracket.fromPhaseVec z μ }

/-- Check if strand is admissible (bracket bounds valid) -/
def isAdmissible (s : BraidStrand) : Bool :=
  s.bracket.admissible && s.bracket.gapConserved

/-- Strand magnitude ‖zᵢ‖ (norm approximation) -/
def magnitude (s : BraidStrand) : Fix16 :=
  s.phaseAcc.normApprox

/-- Strand phase angle (0 if zero vector) -/
def phaseAngle (s : BraidStrand) : Fix16 :=
  s.bracket.phi

end BraidStrand


/-- Strand registry for AVMR append-only storage -/
structure StrandRegistry where
  entries : List BraidStrand
  nextSlot : UInt32
  deriving Repr, DecidableEq

namespace StrandRegistry

def empty : StrandRegistry :=
  { entries := [], nextSlot := 0 }

def register (reg : StrandRegistry) (strand : BraidStrand) : StrandRegistry :=
  { entries := strand :: reg.entries
  , nextSlot := reg.nextSlot + 1 }

def count (reg : StrandRegistry) : Nat :=
  reg.entries.length

def allAdmissible (reg : StrandRegistry) : Bool :=
  reg.entries.all BraidStrand.isAdmissible

end StrandRegistry


#eval (BraidStrand.zero 0).isAdmissible
#eval (StrandRegistry.empty.nextSlot)

end Semantics.BraidStrand
