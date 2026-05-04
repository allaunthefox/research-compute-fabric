import Semantics.FixedPoint
import Semantics.DefectMechanics

namespace Semantics.CompressionMechanicsBridge

open Semantics
open Semantics.DefectMechanics
open Semantics.CompressionMechanics
open Semantics.AtomicResolution
open Semantics.LandauerCompression

/--
Minimal substrate witness for realizing a compression trace physically.
This budgets only dissipation capacity, defect tolerance, and retained support.
-/
structure SubstrateWitness where
  defect : DefectWitness
  dissipationBudget : Q16_16
  supportBudget : Nat
deriving Repr, Inhabited

/--
The substrate dissipative budget covers the work budget of the mechanical layer.
-/
def dissipationCovered (w : SubstrateWitness) : Bool :=
  Q16_16.le w.defect.mechanical.workBudget w.dissipationBudget

/--
The substrate support budget covers the distinguishable atomic support.
-/
def supportCovered (w : SubstrateWitness) : Bool :=
  decide (w.defect.mechanical.atomic.resolvedSites ≤ w.supportBudget)

/--
The substrate tolerance covers the declared defect budget.
-/
def defectToleranceCovered (w : SubstrateWitness) : Bool :=
  Q16_16.le w.defect.defectBudget w.dissipationBudget

/--
A substrate is admissible when the defect witness is admissible and the
substrate budgets cover work, support, and defect tolerance.
-/
def substrateAdmissible (w : SubstrateWitness) : Bool :=
  defectAdmissible w.defect &&
    dissipationCovered w &&
    supportCovered w &&
    defectToleranceCovered w

/--
Canonical constructor over an existing defect witness.
-/
def witnessOfDefect
  (defect : DefectWitness)
  (dissipationBudget : Q16_16)
  (supportBudget : Nat) :
  SubstrateWitness :=
  { defect := defect
  , dissipationBudget := dissipationBudget
  , supportBudget := supportBudget }

/--
If all constituent bounds hold, the substrate witness is admissible.
-/
theorem substrateAdmissibleOfBounds
  (w : SubstrateWitness)
  (hDefect : defectAdmissible w.defect = true)
  (hDissipation : dissipationCovered w = true)
  (hSupport : supportCovered w = true)
  (hTolerance : defectToleranceCovered w = true) :
  substrateAdmissible w = true := by
  simp [substrateAdmissible, hDefect, hDissipation, hSupport, hTolerance]

/--
The support-covered predicate exposes the underlying support budget.
-/
theorem resolvedSitesLeSupportBudget
  (w : SubstrateWitness)
  (hSupport : supportCovered w = true) :
  w.defect.mechanical.atomic.resolvedSites ≤ w.supportBudget := by
  simpa [supportCovered] using hSupport

/--
Defect tolerance and mechanical admissibility imply the Landauer lower bound is
covered by the substrate dissipation budget.
-/
theorem landauerCoveredBySubstrate
  (w : SubstrateWitness)
  (hMechanical : mechanicallyAdmissible w.defect.mechanical = true)
  (hDissipation : dissipationCovered w = true) :
  Q16_16.le (landauerLowerBound w.defect.mechanical.compression) w.dissipationBudget = true := by
  have hWork : workBudgeted w.defect.mechanical = true := by
    have hExpanded := hMechanical
    simp [mechanicallyAdmissible] at hExpanded
    exact hExpanded.right
  simp [workBudgeted, dissipationCovered, Q16_16.le] at hWork hDissipation ⊢
  exact Int.le_trans hWork hDissipation

/--
If a defect witness is admissible and the substrate budgets cover its retained
support and work, then the compression trace is physically admissible on that
substrate.
-/
theorem compressionTracePhysicallyAdmissible
  (w : SubstrateWitness)
  (hDefect : defectAdmissible w.defect = true)
  (hDissipation : dissipationCovered w = true)
  (hSupport : supportCovered w = true)
  (hTolerance : defectToleranceCovered w = true) :
  substrateAdmissible w = true := by
  exact substrateAdmissibleOfBounds w hDefect hDissipation hSupport hTolerance

def sampleSubstrateWitness : SubstrateWitness :=
  witnessOfDefect sampleDefectWitness (Q16_16.ofInt 2) 1

#eval dissipationCovered sampleSubstrateWitness
#eval supportCovered sampleSubstrateWitness
#eval defectToleranceCovered sampleSubstrateWitness
#eval substrateAdmissible sampleSubstrateWitness

end Semantics.CompressionMechanicsBridge
