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
All budget constraints are satisfied.
--
-- Arithmetic sanity check:
-- budget constraints are logical AND conditions.
--
-- External CAS provenance:
-- Not Wolfram-verified in this chain. Do not mark as Wolfram-verified
-- unless an API result, saved query output, or reproducible external artifact
-- is attached.
-/
def allBudgetsCovered (w : MechanicalCompressionWitness) : Bool :=
  actuationBudgeted w && workBudgeted w

/--
Mechanical admissibility requires atomic admissibility plus alignment and budget
coverage.
-/
def mechanicallyAdmissible (w : MechanicalCompressionWitness) : Bool :=
  atomicallyAdmissible w.atomic &&
    summaryAligned w &&
    contactOrderCovered w &&
    allBudgetsCovered w

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
Sample mechanical compression witness for testing.
-/
def sampleMechanicalCompressionWitness : MechanicalCompressionWitness :=
  witnessOfCompression sampleWitness sampleAtomicResolutionWitness 1 Q16_16.one Q16_16.one

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
  simp [mechanicallyAdmissible, allBudgetsCovered, hAtomic, hAlign, hContact, hAct, hWork]

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

#eval summaryAligned sampleMechanicalCompressionWitness
#eval contactOrderCovered sampleMechanicalCompressionWitness
#eval actuationBudgeted sampleMechanicalCompressionWitness
#eval workBudgeted sampleMechanicalCompressionWitness
#eval mechanicallyAdmissible sampleMechanicalCompressionWitness

-- ═══════════════════════════════════════════════════════════════════════════
-- §9  Genetic Algorithm Fitness Function (BioRxiv Integration)
-- ═══════════════════════════════════════════════════════════════════════════

/-- GA fitness parameters for compression optimization.
    From bioRxiv "Optimizing Genomic Data Compression with Genetic Algorithms" (DOI: 10.1101/2025.10.23.684090) -/
structure GACompressionFitness where
  compressionRatio : Q16_16  -- CR = U_size / C_size
  decompTime : Q16_16       -- Decompression time
  compTime : Q16_16         -- Compression time
  lambda : Q16_16          -- Weighting factor for time trade-off
  deriving Repr

/-- Time penalty component: λ * (decomp_time / comp_time)
-- Arithmetic sanity check: time penalty = λ × (decompression time / compression time)
-- External CAS provenance: Not Wolfram-verified in this chain. Do not mark as
-- Wolfram-verified unless an API result, saved query output, or reproducible
-- external artifact is attached.
-/
def timePenalty (decompTime compTime lambda : Q16_16) : Q16_16 :=
  let timeRatio := decompTime / compTime
  lambda * timeRatio

#eval! timePenalty (Q16_16.ofInt 10) (Q16_16.ofInt 100) (Q16_16.ofInt 1)

/-- GA fitness function: fitness = CR - λ * (decomp_time / comp_time)
    Balances compression ratio with computational efficiency.
--
-- Arithmetic sanity check:
-- fitness = compression ratio - time penalty.
--
-- External CAS provenance:
-- Not Wolfram-verified in this chain. Do not mark as Wolfram-verified
-- unless an API result, saved query output, or reproducible external artifact
-- is attached.
-/
def gaFitnessFunction (params : GACompressionFitness) : Q16_16 :=
  params.compressionRatio - (timePenalty params.decompTime params.compTime params.lambda)

/--
Compression ratio calculation (SI Standard): CR = U_size / C_size
Dimensionless ratio (e.g., 8.0 means 8:1 compression).
Higher values indicate better compression.
-/
def compressionRatio (uncompressedSize compressedSize : Q16_16) : Q16_16 :=
  if compressedSize = Q16_16.zero then Q16_16.zero  -- Infinite compression is invalid
  else uncompressedSize / compressedSize

/-- Default GA fitness parameters (tuned for compression optimization). -/
def defaultGAFitnessParams : GACompressionFitness :=
  { compressionRatio := Q16_16.ofInt 2,  -- 2:1 compression baseline
    decompTime := Q16_16.ofInt 10,
    compTime := Q16_16.ofInt 100,
    lambda := Q16_16.ofInt 1 }    -- Unit weighting

/-- Adaptive compression fitness based on GA optimization.
    Retunes compression parameters for optimal CR vs time trade-off. -/
def adaptiveCompressionFitness (w : MechanicalCompressionWitness) (params : GACompressionFitness) : Q16_16 :=
  let estimatedCR := compressionRatio
    (Q16_16.ofInt w.compression.preSummary.shape.basisDim)
    (Q16_16.ofInt w.compression.postSummary.shape.basisDim)
  let fitnessParams := { params with compressionRatio := estimatedCR }
  gaFitnessFunction fitnessParams

-- Note: Theorem proving higher compression ratio increases fitness with fixed-point arithmetic
-- requires more advanced reasoning. The gaFitnessFunction is provided as
-- a modular component for use in fitness calculations.

-- Note: Theorem proving monotonicity of time penalty with fixed-point arithmetic
-- requires more advanced reasoning. The timePenalty function is provided as
-- a modular component for use in fitness calculations.

#eval! gaFitnessFunction defaultGAFitnessParams
-- Expected: 2 - 1 * (10/100) = 2 - 0.1 = 1.9

#eval compressionRatio (Q16_16.ofInt 1000) (Q16_16.ofInt 500)
-- Expected: 2.0 (2:1 compression)

-- #eval! adaptiveCompressionFitness sampleMechanicalCompressionWitness defaultGAFitnessParams
-- Expected: Fitness based on actual compression ratio
-- Note: Disabled because sampleMechanicalCompressionWitness depends on sorry axioms in dependencies

end Semantics.CompressionMechanics
