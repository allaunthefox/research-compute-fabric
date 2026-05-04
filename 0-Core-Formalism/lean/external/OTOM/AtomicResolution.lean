import Semantics.FixedPoint
import Semantics.OrthogonalAmmr
import Semantics.LandauerCompression
import Semantics.EnvironmentMechanics

namespace Semantics.AtomicResolution

open Semantics
open Semantics.OrthogonalAmmr
open Semantics.LandauerCompression
open Semantics.EnvironmentMechanics

/--
Conservative witness for what atomic support remains distinguishable after
compression. This does not identify chemistry; it only budgets distinguishable
sites and bounded coordinate residual against an admissible environment witness.
-/
structure AtomicResolutionWitness where
  environment : EnvironmentWitness
  resolvedSites : Nat
  occupancyBound : Nat
  coordinateResidual : Q16_16
deriving Repr, Inhabited, DecidableEq

/--
The retained basis supports at least the claimed number of distinguishable
sites.
-/
def siteCovered (w : AtomicResolutionWitness) : Bool :=
  decide (w.resolvedSites ≤ w.environment.summary.shape.basisDim)

/--
The claimed occupancy cardinality does not exceed the supported site count.
-/
def occupancyCovered (w : AtomicResolutionWitness) : Bool :=
  decide (w.occupancyBound ≤ w.resolvedSites)

/--
Coordinate-level residual remains inside the environment residual budget.
-/
def coordinateResidualBounded (w : AtomicResolutionWitness) : Bool :=
  Q16_16.le w.coordinateResidual w.environment.residualBudget

/--
Atomic-resolution claims are admissible only when the environment is already
admissible and the site / occupancy / residual bounds all hold.
-/
def atomicallyAdmissible (w : AtomicResolutionWitness) : Bool :=
  longRangeAdmissible w.environment &&
    siteCovered w &&
    occupancyCovered w &&
    coordinateResidualBounded w

/--
Canonical constructor over an existing environment witness.
-/
def witnessOfEnvironment
  (environment : EnvironmentWitness)
  (resolvedSites occupancyBound : Nat)
  (coordinateResidual : Q16_16) :
  AtomicResolutionWitness :=
  { environment := environment
  , resolvedSites := resolvedSites
  , occupancyBound := occupancyBound
  , coordinateResidual := coordinateResidual }

/--
If all constituent bounds hold, the atomic-resolution witness is admissible.
-/
theorem atomicallyAdmissibleOfBounds
  (w : AtomicResolutionWitness)
  (hEnv : longRangeAdmissible w.environment = true)
  (hSites : siteCovered w = true)
  (hOcc : occupancyCovered w = true)
  (hCoord : coordinateResidualBounded w = true) :
  atomicallyAdmissible w = true := by
  simp [atomicallyAdmissible, hEnv, hSites, hOcc, hCoord]

/--
The site-coverage predicate exposes the underlying cardinality bound.
-/
theorem resolvedSitesLeBasisDim
  (w : AtomicResolutionWitness)
  (hSites : siteCovered w = true) :
  w.resolvedSites ≤ w.environment.summary.shape.basisDim := by
  simpa [siteCovered] using hSites

/--
Compression cannot increase the number of distinguishable sites beyond the
pre-compression retained basis together with the erased directions.
-/
theorem compressionContractsAtomicResolution
  (compression : CompressionWitness)
  (w : AtomicResolutionWitness)
  (hAlign : w.environment.summary = compression.postSummary)
  (hContract : compression.postSummary.shape.basisDim ≤ compression.preSummary.shape.basisDim)
  (hSites : siteCovered w = true) :
  w.resolvedSites + erasedDirections compression ≤
    compression.preSummary.shape.basisDim := by
  have hResolved :
      w.resolvedSites ≤ compression.postSummary.shape.basisDim := by
    simpa [hAlign] using resolvedSitesLeBasisDim w hSites
  unfold erasedDirections
  have hStep :
      w.resolvedSites + (compression.preSummary.shape.basisDim - compression.postSummary.shape.basisDim) ≤
        compression.postSummary.shape.basisDim +
          (compression.preSummary.shape.basisDim - compression.postSummary.shape.basisDim) := by
    exact Nat.add_le_add_right hResolved _
  calc
    w.resolvedSites + (compression.preSummary.shape.basisDim - compression.postSummary.shape.basisDim)
      ≤ compression.postSummary.shape.basisDim +
          (compression.preSummary.shape.basisDim - compression.postSummary.shape.basisDim) := hStep
    _ = compression.preSummary.shape.basisDim := by
      exact Nat.add_sub_of_le hContract

def sampleAtomicEnvironment : EnvironmentWitness :=
  witnessOfCompression sampleWitness 1 (Q16_16.ofInt 2) Q16_16.one Q16_16.one

def sampleAtomicResolutionWitness : AtomicResolutionWitness :=
  witnessOfEnvironment sampleAtomicEnvironment 1 1 Q16_16.one

#eval siteCovered sampleAtomicResolutionWitness
#eval occupancyCovered sampleAtomicResolutionWitness
#eval coordinateResidualBounded sampleAtomicResolutionWitness
#eval atomicallyAdmissible sampleAtomicResolutionWitness

end Semantics.AtomicResolution
