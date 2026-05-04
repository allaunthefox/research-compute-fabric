import Semantics.FixedPoint
import Semantics.OrthogonalAmmr
import Semantics.LandauerCompression

namespace Semantics.EnvironmentMechanics

open Semantics
open Semantics.OrthogonalAmmr
open Semantics.LandauerCompression

/--
Environment-level witness for bounded interaction structure retained after
compression. This is the proof-layer object that links a committed O-AMMR
summary to later mechanics claims.
-/
structure EnvironmentWitness where
  summary : AmmrSummary
  retainedOrder : Nat
  interactionBudget : Q16_16
  couplingBound : Q16_16
  residualBudget : Q16_16
deriving Repr, Inhabited, DecidableEq

/--
How many retained basis directions can support the claimed interaction order.
-/
def retainedDirections (w : EnvironmentWitness) : Nat :=
  Nat.min w.summary.shape.basisDim w.retainedOrder

/--
The witness carries enough retained directions to support the claimed order.
-/
def orderCovered (w : EnvironmentWitness) : Bool :=
  w.retainedOrder ≤ w.summary.shape.basisDim

/--
The explicit long-range coupling contribution stays inside the interaction
budget.
-/
def boundedCoupling (w : EnvironmentWitness) : Bool :=
  Q16_16.le w.couplingBound w.interactionBudget

/--
Residual interaction mass excluded from the retained basis also stays inside the
same budget.
-/
def boundedResidual (w : EnvironmentWitness) : Bool :=
  Q16_16.le w.residualBudget w.interactionBudget

/--
Typed admissibility predicate for compressed summaries used in mechanics claims.
-/
def longRangeAdmissible (w : EnvironmentWitness) : Bool :=
  dimensionConsistent w.summary &&
    energyConsistent w.summary &&
    orderCovered w &&
    boundedCoupling w &&
    boundedResidual w

/--
Bridge from a compression witness into an environment witness over the post-state.
-/
def witnessOfCompression
  (compression : CompressionWitness)
  (retainedOrder : Nat)
  (interactionBudget couplingBound residualBudget : Q16_16) :
  EnvironmentWitness :=
  { summary := compression.postSummary
  , retainedOrder := retainedOrder
  , interactionBudget := interactionBudget
  , couplingBound := couplingBound
  , residualBudget := residualBudget }

/--
If each constituent bound holds, the environment witness is admissible.
-/
theorem admissibleOfBounds (w : EnvironmentWitness)
  (hDim : dimensionConsistent w.summary = true)
  (hEnergy : energyConsistent w.summary = true)
  (hOrder : orderCovered w = true)
  (hCoupling : boundedCoupling w = true)
  (hResidual : boundedResidual w = true) :
  longRangeAdmissible w = true := by
  simp [longRangeAdmissible, hDim, hEnergy, hOrder, hCoupling, hResidual]

/--
Compression-level bridge theorem: if the post-summary is admissible under the
provided budgets, the derived environment witness is admissible by definition.
-/
theorem witnessOfCompressionAdmissible
  (compression : CompressionWitness)
  (retainedOrder : Nat)
  (interactionBudget couplingBound residualBudget : Q16_16)
  (hDim : dimensionConsistent compression.postSummary = true)
  (hEnergy : energyConsistent compression.postSummary = true)
  (hOrder : retainedOrder ≤ compression.postSummary.shape.basisDim)
  (hCoupling : Q16_16.le couplingBound interactionBudget = true)
  (hResidual : Q16_16.le residualBudget interactionBudget = true) :
  longRangeAdmissible
      (witnessOfCompression compression retainedOrder
        interactionBudget couplingBound residualBudget) = true := by
  apply admissibleOfBounds
  · simpa [witnessOfCompression]
  · simpa [witnessOfCompression]
  · simpa [witnessOfCompression, orderCovered] using hOrder
  · simpa [witnessOfCompression, boundedCoupling] using hCoupling
  · simpa [witnessOfCompression, boundedResidual] using hResidual

def sampleEnvironmentWitness : EnvironmentWitness :=
  { summary := samplePostSummary
  , retainedOrder := 1
  , interactionBudget := Q16_16.ofInt 2
  , couplingBound := Q16_16.one
  , residualBudget := Q16_16.one }

def sampleCompressionEnvironmentWitness : EnvironmentWitness :=
  witnessOfCompression sampleWitness 1 (Q16_16.ofInt 2) Q16_16.one Q16_16.one

#eval retainedDirections sampleEnvironmentWitness
#eval orderCovered sampleEnvironmentWitness
#eval boundedCoupling sampleEnvironmentWitness
#eval boundedResidual sampleEnvironmentWitness
#eval longRangeAdmissible sampleEnvironmentWitness
#eval longRangeAdmissible sampleCompressionEnvironmentWitness

end Semantics.EnvironmentMechanics
