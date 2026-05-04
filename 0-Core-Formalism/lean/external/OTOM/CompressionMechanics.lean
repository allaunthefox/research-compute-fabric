import Semantics.FixedPoint
import Semantics.LandauerCompression
import Semantics.EnvironmentMechanics
import Semantics.AtomicResolution

namespace Semantics.CompressionMechanics

open Semantics
open Semantics.LandauerCompression
open Semantics.EnvironmentMechanics
open Semantics.AtomicResolution

/--
Mechanical-level witness over a compression trace and an admissible atomic
resolution witness. This budgets only contact order, actuation budget, and work
budget; it does not claim geometry, force fields, or chemistry.
-/
structure MechanicalCompressionWitness where
  compression : CompressionWitness
  atomic : AtomicResolutionWitness
  contactOrder : Nat
  actuationBudget : Q16_16
  workBudget : Q16_16
deriving Repr, Inhabited

/--
The atomic witness is aligned to the post-compression summary.
-/
def summaryAligned (w : MechanicalCompressionWitness) : Bool :=
  decide (w.atomic.environment.summary = w.compression.postSummary)

/--
The claimed mechanical contact order does not exceed the distinguishable site
count.
-/
def contactOrderCovered (w : MechanicalCompressionWitness) : Bool :=
  decide (w.contactOrder ≤ w.atomic.resolvedSites)

/--
The actuation budget does not exceed the environment interaction budget.
-/
def actuationBudgeted (w : MechanicalCompressionWitness) : Bool :=
  Q16_16.le w.actuationBudget w.atomic.environment.interactionBudget

/--
The work budget covers the Landauer lower bound of the compression witness.
-/
def workBudgeted (w : MechanicalCompressionWitness) : Bool :=
  Q16_16.le (landauerLowerBound w.compression) w.workBudget

/--
Mechanical admissibility requires atomic admissibility plus alignment and budget
coverage.
-/
def mechanicallyAdmissible (w : MechanicalCompressionWitness) : Bool :=
  atomicallyAdmissible w.atomic &&
    summaryAligned w &&
    contactOrderCovered w &&
    actuationBudgeted w &&
    workBudgeted w

/--
Canonical constructor over existing compression and atomic witnesses.
-/
def witnessOfCompression
  (compression : CompressionWitness)
  (atomic : AtomicResolutionWitness)
  (contactOrder : Nat)
  (actuationBudget workBudget : Q16_16) :
  MechanicalCompressionWitness :=
  { compression := compression
  , atomic := atomic
  , contactOrder := contactOrder
  , actuationBudget := actuationBudget
  , workBudget := workBudget }

/--
If all constituent bounds hold, the mechanical witness is admissible.
-/
theorem mechanicallyAdmissibleOfBounds
  (w : MechanicalCompressionWitness)
  (hAtomic : atomicallyAdmissible w.atomic = true)
  (hAlign : summaryAligned w = true)
  (hContact : contactOrderCovered w = true)
  (hAct : actuationBudgeted w = true)
  (hWork : workBudgeted w = true) :
  mechanicallyAdmissible w = true := by
  simp [mechanicallyAdmissible, hAtomic, hAlign, hContact, hAct, hWork]

/--
If an irreversible compression is budgeted mechanically, the work budget is
strictly positive.
-/
theorem positiveWorkOfIrreversibleCompression
  (w : MechanicalCompressionWitness)
  (hWork : workBudgeted w = true)
  (hErase : erasedDirections w.compression > 0) :
  Q16_16.gt w.workBudget Q16_16.zero = true := by
  have hLower :
      Q16_16.gt (landauerLowerBound w.compression) Q16_16.zero = true := by
    exact positiveErasurePositiveLowerBound w.compression hErase
  simp [workBudgeted, Q16_16.le, Q16_16.gt] at hWork hLower ⊢
  exact Int.lt_of_lt_of_le hLower hWork

/--
Mechanical contact order contracts through compression under explicit alignment
and basis-dimension contraction assumptions.
-/
theorem compressionContractsMechanicalOrder
  (w : MechanicalCompressionWitness)
  (hAlign : summaryAligned w = true)
  (hContract : w.compression.postSummary.shape.basisDim ≤
    w.compression.preSummary.shape.basisDim)
  (hContact : contactOrderCovered w = true)
  (hSites : siteCovered w.atomic = true) :
  w.contactOrder + erasedDirections w.compression ≤
    w.compression.preSummary.shape.basisDim := by
  have hContactLe :
      w.contactOrder ≤ w.atomic.resolvedSites := by
    simpa [contactOrderCovered] using hContact
  have hAtomicContract :
      w.atomic.resolvedSites + erasedDirections w.compression ≤
        w.compression.preSummary.shape.basisDim := by
    have hSummary :
        w.atomic.environment.summary = w.compression.postSummary := by
      simpa [summaryAligned] using hAlign
    exact compressionContractsAtomicResolution w.compression w.atomic
      hSummary hContract hSites
  calc
    w.contactOrder + erasedDirections w.compression
      ≤ w.atomic.resolvedSites + erasedDirections w.compression := by
        exact Nat.add_le_add_right hContactLe _
    _ ≤ w.compression.preSummary.shape.basisDim := hAtomicContract

def sampleMechanicalCompressionWitness : MechanicalCompressionWitness :=
  witnessOfCompression sampleWitness sampleAtomicResolutionWitness 1 Q16_16.one Q16_16.one

#eval summaryAligned sampleMechanicalCompressionWitness
#eval contactOrderCovered sampleMechanicalCompressionWitness
#eval actuationBudgeted sampleMechanicalCompressionWitness
#eval workBudgeted sampleMechanicalCompressionWitness
#eval mechanicallyAdmissible sampleMechanicalCompressionWitness

end Semantics.CompressionMechanics
