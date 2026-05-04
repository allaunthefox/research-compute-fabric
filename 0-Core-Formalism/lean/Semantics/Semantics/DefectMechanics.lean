import Semantics.FixedPoint
import Semantics.CompressionMechanics

namespace Semantics.DefectMechanics

open Semantics
open Semantics.CompressionMechanics
open Semantics.AtomicResolution
open Semantics.LandauerCompression

/--
Conservative defect-style witness over the mechanical compression layer.
This tracks only bounded distortion and vacancy-like cardinality. It does not
identify a defect species or infer atomistic geometry.
-/
structure DefectWitness where
  mechanical : MechanicalCompressionWitness
  vacancyCount : Nat
  distortionScore : Q16_16
  defectBudget : Q16_16
deriving Repr, Inhabited

/--
The vacancy-like count does not exceed the supported occupancy bound.
-/
def vacancyCovered (w : DefectWitness) : Bool :=
  decide (w.vacancyCount ≤ w.mechanical.atomic.occupancyBound)

/--
The distortion score remains within the declared defect budget.
-/
def distortionBounded (w : DefectWitness) : Bool :=
  Q16_16.le w.distortionScore w.defectBudget

/--
The declared defect budget stays within the available actuation budget.
-/
def defectBudgeted (w : DefectWitness) : Bool :=
  Q16_16.le w.defectBudget w.mechanical.actuationBudget

/--
Defect admissibility requires the mechanical witness plus bounded vacancy-like
count and bounded distortion.
-/
def defectAdmissible (w : DefectWitness) : Bool :=
  mechanicallyAdmissible w.mechanical &&
    vacancyCovered w &&
    distortionBounded w &&
    defectBudgeted w

/--
Canonical constructor over an existing mechanical witness.
-/
def witnessOfMechanical
  (mechanical : MechanicalCompressionWitness)
  (vacancyCount : Nat)
  (distortionScore defectBudget : Q16_16) :
  DefectWitness :=
  { mechanical := mechanical
  , vacancyCount := vacancyCount
  , distortionScore := distortionScore
  , defectBudget := defectBudget }

/--
If all constituent bounds hold, the defect witness is admissible.
-/
theorem defectAdmissibleOfBounds
  (w : DefectWitness)
  (hMechanical : mechanicallyAdmissible w.mechanical = true)
  (hVacancy : vacancyCovered w = true)
  (hDistortion : distortionBounded w = true)
  (hBudget : defectBudgeted w = true) :
  defectAdmissible w = true := by
  simp [defectAdmissible, hMechanical, hVacancy, hDistortion, hBudget]

/--
The vacancy-covered predicate exposes the underlying occupancy bound.
-/
theorem vacancyCountLeOccupancyBound
  (w : DefectWitness)
  (hVacancy : vacancyCovered w = true) :
  w.vacancyCount ≤ w.mechanical.atomic.occupancyBound := by
  simpa [vacancyCovered] using hVacancy

/--
Vacancy-like cardinality also contracts through compression under the same
alignment, contraction, contact, and site assumptions already required by the
mechanical witness.
-/
theorem compressionContractsVacancyCount
  (w : DefectWitness)
  (hAlign : summaryAligned w.mechanical = true)
  (hContract : w.mechanical.compression.postSummary.shape.basisDim ≤
    w.mechanical.compression.preSummary.shape.basisDim)
  (hSites : siteCovered w.mechanical.atomic = true)
  (hOcc : occupancyCovered w.mechanical.atomic = true)
  (hVacancy : vacancyCovered w = true) :
  w.vacancyCount + erasedDirections w.mechanical.compression ≤
    w.mechanical.compression.preSummary.shape.basisDim := by
  have hVacancyOcc :
      w.vacancyCount ≤ w.mechanical.atomic.occupancyBound := by
    exact vacancyCountLeOccupancyBound w hVacancy
  have hOccSites :
      w.mechanical.atomic.occupancyBound ≤ w.mechanical.atomic.resolvedSites := by
    simpa [occupancyCovered] using hOcc
  have hVacancySites :
      w.vacancyCount ≤ w.mechanical.atomic.resolvedSites := by
    exact Nat.le_trans hVacancyOcc hOccSites
  have hSummary :
      w.mechanical.atomic.environment.summary = w.mechanical.compression.postSummary := by
    simpa [summaryAligned] using hAlign
  have hResolvedContract :
      w.mechanical.atomic.resolvedSites + erasedDirections w.mechanical.compression ≤
        w.mechanical.compression.preSummary.shape.basisDim := by
    exact compressionContractsAtomicResolution
      w.mechanical.compression w.mechanical.atomic hSummary hContract hSites
  calc
    w.vacancyCount + erasedDirections w.mechanical.compression
      ≤ w.mechanical.atomic.resolvedSites + erasedDirections w.mechanical.compression := by
        exact Nat.add_le_add_right hVacancySites _
    _ ≤ w.mechanical.compression.preSummary.shape.basisDim := hResolvedContract

/--
Distortion bounded by the defect budget and defect budget bounded by actuation
imply distortion bounded by the actuation budget.
-/
theorem distortionLeActuationBudget
  (w : DefectWitness)
  (hDistortion : distortionBounded w = true)
  (hBudget : defectBudgeted w = true) :
  Q16_16.le w.distortionScore w.mechanical.actuationBudget = true := by
  simp [distortionBounded, defectBudgeted, Q16_16.le] at hDistortion hBudget ⊢
  exact Int.le_trans hDistortion hBudget

def sampleDefectWitness : DefectWitness :=
  witnessOfMechanical sampleMechanicalCompressionWitness 1 Q16_16.one Q16_16.one

#eval vacancyCovered sampleDefectWitness
#eval distortionBounded sampleDefectWitness
#eval defectBudgeted sampleDefectWitness
#eval defectAdmissible sampleDefectWitness

end Semantics.DefectMechanics
