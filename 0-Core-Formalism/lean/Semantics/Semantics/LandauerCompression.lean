import Semantics.FixedPoint
import Semantics.OrthogonalAmmr

namespace Semantics.LandauerCompression

open Semantics
open Semantics.OrthogonalAmmr
open Semantics.FixedPoint (Q0_16.ofRawInt)

/--
Abstract one-bit Landauer unit in proof-layer Q16.16 form.
This is a normalized lower-bound unit, not a calibrated physical constant.
-/
def landauerUnitCost : Q16_16 := Q16_16.one

/--
Compression witness comparing a pre-summary and post-summary.
-/
structure CompressionWitness where
  preSummary : AmmrSummary
  postSummary : AmmrSummary
deriving Repr, Inhabited

/--
Erased-information witness in units of retained basis directions.
This is the smallest truthful bridge currently available from O-AMMR:
if fewer directions are retained after compression, information has been
irreversibly discarded from the proof-layer summary.
-/
def erasedDirections (w : CompressionWitness) : Nat :=
  w.preSummary.shape.basisDim - w.postSummary.shape.basisDim

/--
Irreversibility predicate: some retained directions were discarded.
-/
def isIrreversible (w : CompressionWitness) : Bool :=
  erasedDirections w > 0

/--
Landauer lower bound for the witness.
For the first proof layer we use the minimal honest bound:

- zero if no retained direction was erased
- one normalized Landauer unit if any retained direction was erased

This avoids accidental overflow semantics in the proof core while still proving
the intended bridge from irreversibility to nonzero thermodynamic cost.
-/
def landauerLowerBound (w : CompressionWitness) : Q16_16 :=
  let erased := erasedDirections w
  if erased == 0 then Q16_16.zero else landauerUnitCost

/--
Reversible witnesses have zero lower bound.
-/
theorem reversibleZeroBound (w : CompressionWitness)
  (h : erasedDirections w = 0) :
  landauerLowerBound w = Q16_16.zero := by
  simp [landauerLowerBound, h, Q16_16.zero]

/--
Positive erased-direction witness implies a nonzero lower bound.
-/
theorem positiveErasurePositiveLowerBound (w : CompressionWitness)
  (h : erasedDirections w > 0) :
  Q16_16.gt (landauerLowerBound w) Q16_16.zero = true := by
  cases ndef : erasedDirections w with
  | zero =>
      simp [ndef] at h
  | succ n =>
      simp [landauerLowerBound, ndef, landauerUnitCost, Q16_16.gt, Q16_16.zero]
      native_decide

/--
Summary-level constructor for a compression witness.
-/
def witnessOfSummaries (preSummary postSummary : AmmrSummary) : CompressionWitness :=
  { preSummary := preSummary, postSummary := postSummary }

/--
O-AMMR-specific irreversible update witness from retained basis reduction.
-/
def witnessOfNodes (preNode postNode : AmmrNode) : CompressionWitness :=
  witnessOfSummaries preNode.summary postNode.summary

/--
Example: prune one retained direction from a two-direction summary.
-/
def samplePreSummary : AmmrSummary :=
  { qBasis := [unitVec 3 0, unitVec 3 1]
  , rCoeff := [Q16_16.one, Q16_16.one]
  , shape := { ambientDim := 3, basisDim := 2 }
  , energy := coeffEnergy [Q16_16.one, Q16_16.one] }

/--
Example: retain only one direction after compression.
-/
def samplePostSummary : AmmrSummary :=
  { qBasis := [unitVec 3 0]
  , rCoeff := [Q16_16.one]
  , shape := { ambientDim := 3, basisDim := 1 }
  , energy := coeffEnergy [Q16_16.one] }

def sampleWitness : CompressionWitness :=
  witnessOfSummaries samplePreSummary samplePostSummary

def sampleReversibleWitness : CompressionWitness :=
  witnessOfSummaries samplePostSummary samplePostSummary

#eval erasedDirections sampleWitness
#eval isIrreversible sampleWitness
#eval landauerLowerBound sampleWitness
#eval erasedDirections sampleReversibleWitness
#eval landauerLowerBound sampleReversibleWitness

/-! ## MNLOG-001 Mass Number Valuations for LandauerCompression Theorems

    Doctrine: Logic can have a mass-number value only after we say which reality is weighing it.
    These valuations are field-local under the thermodynamic compression reality contract.
-/

/-- Reality contract for Landauer compression theorems -/
structure LandauerRealityField where
  domain      := "thermodynamic compression"
  contract    := "Landauer principle: information erasure has nonzero thermodynamic cost"
  validator   := "computational proof (native_decide, simp)"

/-- Residual model for Landauer compression theorems -/
structure LandauerResidualModel where
  uncertainty  : Nat  -- Unresolved edge cases in continuum limit
  assumptions  : Nat  -- Axiomatic dependencies (Q16_16 arithmetic)
  cost         : Nat  -- Proof complexity

/-- Projection rule for Landauer compression theorems -/
structure LandauerProjectionRule where
  name     := "linear projection"
  scaling  := 256  -- Q8_8 approximation

/-- Logical mass structure for Landauer theorems -/
structure LandauerLogicalMass where
  field          : LandauerRealityField
  admissible     : Nat  -- Proof strength, thermodynamic relevance
  residual       : LandauerResidualModel
  projection     : LandauerProjectionRule

/-- Compute mass number for Landauer theorem -/
def LandauerLogicalMass.massNumber (lm : LandauerLogicalMass) : Q0_16 :=
  let totalResidual := lm.residual.uncertainty + lm.residual.assumptions + lm.residual.cost
  let denom := 1 + totalResidual
  let maxVal : Nat := 32767
  if denom = 0 then Q0_16.zero
  else
    let scaled := if lm.admissible ≥ maxVal then maxVal else lm.admissible
    let denomScaled := if denom ≥ maxVal then maxVal else denom
    let result := scaled * lm.projection.scaling / denomScaled
    Q0_16.ofRawInt (result : Int)

/-- Mass number for reversibleZeroBound theorem -/
def reversibleZeroBoundMass : LandauerLogicalMass :=
  {
    field := { domain := "thermodynamic compression", contract := "reversible compression has zero cost", validator := "computational proof" },
    admissible := 85,  -- High: fundamental thermodynamic principle
    residual := { uncertainty := 1, assumptions := 2, cost := 3 },  -- Low proof complexity
    projection := { name := "linear projection", scaling := 256 }
  }

/-- Mass number for positiveErasurePositiveLowerBound theorem -/
def positiveErasurePositiveLowerBoundMass : LandauerLogicalMass :=
  {
    field := { domain := "thermodynamic compression", contract := "irreversible erasure has nonzero cost", validator := "computational proof" },
    admissible := 90,  -- Very high: core Landauer principle
    residual := { uncertainty := 2, assumptions := 2, cost := 4 },  -- Moderate proof complexity
    projection := { name := "linear projection", scaling := 256 }
  }

#eval! reversibleZeroBoundMass.massNumber
-- Note: This valuation means "high admissibility under computational proof validator"
-- It does NOT mean "this theorem is universally true". Truth is proven by the theorem itself.

#eval! positiveErasurePositiveLowerBoundMass.massNumber
-- Note: This valuation means "very high admissibility with moderate proof cost"
-- Truth still requires the formal proof provided in the theorem.

end Semantics.LandauerCompression
