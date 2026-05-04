import Semantics.FixedPoint
import Semantics.OrthogonalAmmr

namespace Semantics.CompressionEvidence

open Semantics
open Semantics.OrthogonalAmmr

/--
Quantized budget for a retained-basis compression witness.
-/
structure BasisBudget where
  retainedDim : Nat
  interactionOrder : Nat
  residualLimit : Q16_16
deriving Repr, Inhabited, DecidableEq

/--
Proof-layer local environment witness.
`retainedEnergy` is the explicitly modeled contribution and `residualEnergy` is
the tracked omitted remainder.
-/
structure LocalEnvironment where
  summary : AmmrSummary
  retainedEnergy : Q16_16
  residualEnergy : Q16_16
  totalEnergy : Q16_16
deriving Repr, Inhabited, DecidableEq

/--
Canonical constructor: total energy is the retained term plus the tracked
residual term.
-/
def mkLocalEnvironment
  (summary : AmmrSummary)
  (retainedEnergy residualEnergy : Q16_16) :
  LocalEnvironment :=
  { summary := summary
  , retainedEnergy := retainedEnergy
  , residualEnergy := residualEnergy
  , totalEnergy := Q16_16.add retainedEnergy residualEnergy }

/--
Retained-basis error witness for the environment.
-/
def retainedBasisError (_budget : BasisBudget) (env : LocalEnvironment) : Q16_16 :=
  env.residualEnergy

/--
The retained basis covers the claimed interaction order.
-/
def isBodyOrderedUpTo (budget : BasisBudget) (env : LocalEnvironment) : Bool :=
  budget.interactionOrder ≤ budget.retainedDim &&
    budget.retainedDim ≤ env.summary.shape.basisDim

/--
The tracked residual stays inside the declared compression budget.
-/
def withinResidualLimit (budget : BasisBudget) (env : LocalEnvironment) : Bool :=
  Q16_16.le (retainedBasisError budget env) budget.residualLimit

/--
Compression evidence is admissible when summary metadata is self-consistent, the
retained basis covers the claimed interaction order, and the tracked residual is
inside budget.
-/
def compressionAdmissible (budget : BasisBudget) (env : LocalEnvironment) : Bool :=
  dimensionConsistent env.summary &&
    energyConsistent env.summary &&
    isBodyOrderedUpTo budget env &&
    withinResidualLimit budget env

/--
The canonical constructor decomposes total energy into retained and residual
terms by definition.
-/
theorem energyDecomposesRetainedPlusResidual
  (summary : AmmrSummary)
  (retainedEnergy residualEnergy : Q16_16) :
  (mkLocalEnvironment summary retainedEnergy residualEnergy).totalEnergy =
    Q16_16.add retainedEnergy residualEnergy := by
  rfl

/--
For environments built canonically, the retained-basis error is exactly the
tracked residual witness.
-/
theorem retainedBasisErrorEqResidual
  (budget : BasisBudget)
  (summary : AmmrSummary)
  (retainedEnergy residualEnergy : Q16_16) :
  retainedBasisError budget
      (mkLocalEnvironment summary retainedEnergy residualEnergy) =
    residualEnergy := by
  simp [retainedBasisError, mkLocalEnvironment]

/--
Residual admissibility is monotone in the declared residual limit.
-/
theorem residualToleranceMonotone
  (smallBudget largeBudget : BasisBudget)
  (env : LocalEnvironment)
  (hLimit : Q16_16.le smallBudget.residualLimit largeBudget.residualLimit = true)
  (hWithin : withinResidualLimit smallBudget env = true) :
  withinResidualLimit largeBudget env = true := by
  simp [withinResidualLimit, retainedBasisError, Q16_16.le] at hWithin hLimit ⊢
  exact Int.le_trans hWithin hLimit

/--
If all constituent witnesses hold, the compression evidence is admissible.
-/
theorem admissibleOfEvidence
  (budget : BasisBudget)
  (env : LocalEnvironment)
  (hDim : dimensionConsistent env.summary = true)
  (hEnergy : energyConsistent env.summary = true)
  (hOrder : isBodyOrderedUpTo budget env = true)
  (hResidual : withinResidualLimit budget env = true) :
  compressionAdmissible budget env = true := by
  simp [compressionAdmissible, hDim, hEnergy, hOrder, hResidual]

def sampleBudget : BasisBudget :=
  { retainedDim := 1
  , interactionOrder := 1
  , residualLimit := Q16_16.one }

def sampleEnvironment : LocalEnvironment :=
  mkLocalEnvironment (leafSummary 3 0 Q16_16.one) Q16_16.one Q16_16.zero

def sampleResidualEnvironment : LocalEnvironment :=
  mkLocalEnvironment (leafSummary 3 0 Q16_16.one) Q16_16.one Q16_16.one

#eval retainedBasisError sampleBudget sampleEnvironment
#eval isBodyOrderedUpTo sampleBudget sampleEnvironment
#eval withinResidualLimit sampleBudget sampleEnvironment
#eval compressionAdmissible sampleBudget sampleEnvironment
#eval retainedBasisError sampleBudget sampleResidualEnvironment
#eval withinResidualLimit sampleBudget sampleResidualEnvironment

end Semantics.CompressionEvidence
