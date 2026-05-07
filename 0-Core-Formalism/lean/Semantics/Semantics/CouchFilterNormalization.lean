import Semantics.AbelianSandpileRouting
import Semantics.Genome18

/-!
# Couch Filter Normalization Witness

This module records the finite, proof-checkable part of
`data/couch_filter_normalization.json` and
`data/couch_equation_forest_analysis.json`.

The floating trajectory data remains an external empirical artifact.  The
Genome18 position, PIST admissibility flag, and normalized route-class decision
are captured here as Lean witnesses so downstream routing/proof code can depend
on stable, finite facts.
-/

namespace Semantics.CouchFilterNormalization

open Semantics.AbelianSandpileRouting

/-- Coupling regimes present in `couch_filter_normalization.json`. -/
inductive CouchCouplingRegime where
  | kappa050
  | kappa100
  | kappa150
  | kappa200
  | kappa250
  deriving Repr, Inhabited, BEq, DecidableEq

/-- Curvature summaries scaled by 1000 from the JSON file. -/
structure CouchCurvatureSummary where
  avgCurvatureMilli : Nat
  maxCurvatureMilli : Nat
  stdCurvatureMilli : Nat
  avgNormMilli : Nat
  trajectorySteps : Nat
  deriving Repr, Inhabited, BEq, DecidableEq

/-- Per-regime curvature summaries scaled by 1000 from the JSON artifact. -/
def couchCurvatureSummary : CouchCouplingRegime → CouchCurvatureSummary
  | .kappa050 =>
    { avgCurvatureMilli := 8098
    , maxCurvatureMilli := 9865
    , stdCurvatureMilli := 1654
    , avgNormMilli := 1374
    , trajectorySteps := 10 }
  | .kappa100 =>
    { avgCurvatureMilli := 8182
    , maxCurvatureMilli := 9859
    , stdCurvatureMilli := 1574
    , avgNormMilli := 1370
    , trajectorySteps := 10 }
  | .kappa150 =>
    { avgCurvatureMilli := 8272
    , maxCurvatureMilli := 9880
    , stdCurvatureMilli := 1502
    , avgNormMilli := 1367
    , trajectorySteps := 10 }
  | .kappa200 =>
    { avgCurvatureMilli := 8367
    , maxCurvatureMilli := 9930
    , stdCurvatureMilli := 1440
    , avgNormMilli := 1363
    , trajectorySteps := 10 }
  | .kappa250 =>
    { avgCurvatureMilli := 8467
    , maxCurvatureMilli := 10007
    , stdCurvatureMilli := 1391
    , avgNormMilli := 1360
    , trajectorySteps := 10 }

/-- Genome18 bins from `data/couch_equation_forest_analysis.json`. -/
def couchGenome : Semantics.Genome18 :=
  { muBin := 0
  , rhoBin := 0
  , cBin := 1
  , mBin := 0
  , neBin := 0
  , sigmaBin := 0 }

/-- The JSON-reported forest address for the couch state. -/
def couchGenomeAddress : Nat := couchGenome.addr

theorem couchGenomeAddress_eq : couchGenomeAddress = 512 := by
  native_decide

theorem couchGenomeAddress_range : couchGenomeAddress < 262144 := by
  simpa [couchGenomeAddress] using Semantics.Genome18.addr_range couchGenome

/-- PIST witness surface from the JSON artifact. -/
structure CouchPISTWitness where
  shellK : Nat
  shellT : Nat
  hashMilli : Nat
  fammFrustrationMilli : Nat
  mass : Nat
  isAdmissible : Bool
  deriving Repr, Inhabited, BEq, DecidableEq

def couchPISTWitness : CouchPISTWitness :=
  { shellK := 4
  , shellT := 11
  , hashMilli := 299
  , fammFrustrationMilli := 122
  , mass := 16
  , isAdmissible := true }

theorem couchPISTWitness_admissible :
    couchPISTWitness.isAdmissible = true := by
  native_decide

/--
Finite COUCH F-number proxy.

The continuous COUCH equation uses forcing, hysteresis, and oscillator
curvature.  This finite witness keeps only the integer-scaled parts already
present in the JSON evidence surface:

  F_COUCH(regime) = avg_curvature + max_curvature + FAMM_frustration

This is a route-pressure indicator, not a proof about the continuous chaotic
trajectory.
-/
def couchFNumberMilli (regime : CouchCouplingRegime) : Nat :=
  let summary := couchCurvatureSummary regime
  summary.avgCurvatureMilli + summary.maxCurvatureMilli +
    couchPISTWitness.fammFrustrationMilli

/-- Threshold used to flag the high-F COUCH regime in finite witnesses. -/
def couchHighFThresholdMilli : Nat := 18500

/-- Whether a COUCH coupling regime crosses the high-F finite witness threshold. -/
def isHighFNumberCouch (regime : CouchCouplingRegime) : Bool :=
  couchFNumberMilli regime ≥ couchHighFThresholdMilli

theorem couchFNumber_kappa050_eq :
    couchFNumberMilli .kappa050 = 18085 := by
  native_decide

theorem couchFNumber_kappa250_eq :
    couchFNumberMilli .kappa250 = 18596 := by
  native_decide

theorem couchFNumber_fullSweep_eq :
    couchFNumberMilli .kappa050 = 18085 ∧
    couchFNumberMilli .kappa100 = 18163 ∧
    couchFNumberMilli .kappa150 = 18274 ∧
    couchFNumberMilli .kappa200 = 18419 ∧
    couchFNumberMilli .kappa250 = 18596 := by
  native_decide

theorem couchFNumber_increases_kappa050_to_kappa250 :
    couchFNumberMilli .kappa050 < couchFNumberMilli .kappa250 := by
  native_decide

theorem couchFNumber_strictlyRisesAcrossSweep :
    couchFNumberMilli .kappa050 < couchFNumberMilli .kappa100 ∧
    couchFNumberMilli .kappa100 < couchFNumberMilli .kappa150 ∧
    couchFNumberMilli .kappa150 < couchFNumberMilli .kappa200 ∧
    couchFNumberMilli .kappa200 < couchFNumberMilli .kappa250 := by
  native_decide

theorem couchFNumber_kappa250_high :
    isHighFNumberCouch .kappa250 = true := by
  native_decide

theorem couchFNumber_kappa050_not_high :
    isHighFNumberCouch .kappa050 = false := by
  native_decide

theorem couchFNumber_highClassification_fullSweep :
    isHighFNumberCouch .kappa050 = false ∧
    isHighFNumberCouch .kappa100 = false ∧
    isHighFNumberCouch .kappa150 = false ∧
    isHighFNumberCouch .kappa200 = false ∧
    isHighFNumberCouch .kappa250 = true := by
  native_decide

/-- Coupling value scaled by 1000, matching the kappa label. -/
def couchKappaMilli : CouchCouplingRegime → Nat
  | .kappa050 => 500
  | .kappa100 => 1000
  | .kappa150 => 1500
  | .kappa200 => 2000
  | .kappa250 => 2500

/--
Finite U-rotated COUCH value along the curvature C and coupling kappa channels.

The continuous interpretation is a small projection of the normalized U channel
along the curvature channel under coupling strength:

  U_rot(kappa) = C_avg(kappa) + kappa * U_norm(kappa)

All terms here are integer-scaled by 1000.  Division by 1000 keeps the output
in milli-units and avoids Float.
-/
def couchURotatedMilli (regime : CouchCouplingRegime) : Nat :=
  let summary := couchCurvatureSummary regime
  summary.avgCurvatureMilli +
    (couchKappaMilli regime * summary.avgNormMilli) / 1000

theorem couchURotated_kappa050_eq :
    couchURotatedMilli .kappa050 = 8785 := by
  native_decide

theorem couchURotated_kappa250_eq :
    couchURotatedMilli .kappa250 = 11867 := by
  native_decide

theorem couchURotated_fullSweep_eq :
    couchURotatedMilli .kappa050 = 8785 ∧
    couchURotatedMilli .kappa100 = 9552 ∧
    couchURotatedMilli .kappa150 = 10322 ∧
    couchURotatedMilli .kappa200 = 11093 ∧
    couchURotatedMilli .kappa250 = 11867 := by
  native_decide

theorem couchURotated_increases_kappa050_to_kappa250 :
    couchURotatedMilli .kappa050 < couchURotatedMilli .kappa250 := by
  native_decide

theorem couchURotated_strictlyRisesAcrossSweep :
    couchURotatedMilli .kappa050 < couchURotatedMilli .kappa100 ∧
    couchURotatedMilli .kappa100 < couchURotatedMilli .kappa150 ∧
    couchURotatedMilli .kappa150 < couchURotatedMilli .kappa200 ∧
    couchURotatedMilli .kappa200 < couchURotatedMilli .kappa250 := by
  native_decide

/--
Y-axis finite container for the COUCH sweep.

Fields:
  - `oSteps`: observed trajectory steps along the Y/O axis.
  - `uValueMilli`: U-rotated value for the coupling regime.
  - `rValueMilli`: constant residual/route anchor for comparison.

This container is intentionally finite: it preserves the sortable Y-axis
projection without promoting the continuous trajectory.
-/
structure CouchYAxisContainer where
  oSteps : Nat
  uValueMilli : Nat
  rValueMilli : Nat
  deriving Repr, Inhabited, BEq, DecidableEq

/-- Constant R anchor used by the Y-axis COUCH container. -/
def couchRValueConstantMilli : Nat := 1000

/-- Build the finite Y-axis container for a COUCH coupling regime. -/
def couchYAxisContainer (regime : CouchCouplingRegime) : CouchYAxisContainer :=
  let summary := couchCurvatureSummary regime
  { oSteps := summary.trajectorySteps
  , uValueMilli := couchURotatedMilli regime
  , rValueMilli := couchRValueConstantMilli }

theorem couchYAxisContainer_kappa050_eq :
    couchYAxisContainer .kappa050 =
      { oSteps := 10, uValueMilli := 8785, rValueMilli := 1000 } := by
  native_decide

theorem couchYAxisContainer_kappa250_eq :
    couchYAxisContainer .kappa250 =
      { oSteps := 10, uValueMilli := 11867, rValueMilli := 1000 } := by
  native_decide

theorem couchYAxisContainer_fullSweep_eq :
    couchYAxisContainer .kappa050 =
      { oSteps := 10, uValueMilli := 8785, rValueMilli := 1000 } ∧
    couchYAxisContainer .kappa100 =
      { oSteps := 10, uValueMilli := 9552, rValueMilli := 1000 } ∧
    couchYAxisContainer .kappa150 =
      { oSteps := 10, uValueMilli := 10322, rValueMilli := 1000 } ∧
    couchYAxisContainer .kappa200 =
      { oSteps := 10, uValueMilli := 11093, rValueMilli := 1000 } ∧
    couchYAxisContainer .kappa250 =
      { oSteps := 10, uValueMilli := 11867, rValueMilli := 1000 } := by
  native_decide

theorem couchYAxisContainer_r_constant
    (regime : CouchCouplingRegime) :
    (couchYAxisContainer regime).rValueMilli = couchRValueConstantMilli := by
  cases regime <;> native_decide

/--
COUCH route pressure combines the finite F-number, the U-rotated value, and the
constant R anchor.  The subtraction is safe because the current finite sweep has
F + U well above R for every bucket.
-/
def couchRoutePressureMilli (regime : CouchCouplingRegime) : Nat :=
  couchFNumberMilli regime + couchURotatedMilli regime -
    (couchYAxisContainer regime).rValueMilli

/-- Threshold above which COUCH should leave local execution and route to atlas. -/
def couchAtlasThresholdMilli : Nat := 27000

/-- Threshold above which COUCH is too pressured for atlas routing and should reject. -/
def couchRejectThresholdMilli : Nat := 29000

/--
COUCH routing mode: this is the practical reason the finite witnesses exist.

Low pressure may execute locally, medium pressure must route through the atlas,
and high pressure is rejected/quarantined rather than promoted.
-/
def couchRoutingMode (regime : CouchCouplingRegime) : MorphicRoutingMode :=
  let pressure := couchRoutePressureMilli regime
  if pressure ≥ couchRejectThresholdMilli then .rejectDivergent
  else if pressure ≥ couchAtlasThresholdMilli then .exploreAtlas
  else .exploitLocal

/-- Existing routing action vocabulary selected by the COUCH route-pressure gate. -/
def couchRoutingAction (regime : CouchCouplingRegime) : RoutingAction :=
  morphicModeToAction (couchRoutingMode regime)

theorem couchRoutePressure_fullSweep_eq :
    couchRoutePressureMilli .kappa050 = 25870 ∧
    couchRoutePressureMilli .kappa100 = 26715 ∧
    couchRoutePressureMilli .kappa150 = 27596 ∧
    couchRoutePressureMilli .kappa200 = 28512 ∧
    couchRoutePressureMilli .kappa250 = 29463 := by
  native_decide

theorem couchRoutingMode_fullSweep_eq :
    couchRoutingMode .kappa050 = .exploitLocal ∧
    couchRoutingMode .kappa100 = .exploitLocal ∧
    couchRoutingMode .kappa150 = .exploreAtlas ∧
    couchRoutingMode .kappa200 = .exploreAtlas ∧
    couchRoutingMode .kappa250 = .rejectDivergent := by
  native_decide

theorem couchRoutingAction_fullSweep_eq :
    couchRoutingAction .kappa050 = Semantics.RoutingAction.local ∧
    couchRoutingAction .kappa100 = Semantics.RoutingAction.local ∧
    couchRoutingAction .kappa150 = Semantics.RoutingAction.atlas ∧
    couchRoutingAction .kappa200 = Semantics.RoutingAction.atlas ∧
    couchRoutingAction .kappa250 = Semantics.RoutingAction.reject := by
  native_decide

/--
Forest signals corresponding to the couch Genome18 bins.  Low verification
pressure means the morphic route should not execute locally without atlas
verification, even though the PIST witness is admissible.
-/
def couchForestSignals : ForestRouteSignals :=
  { routingLoad := 0
  , verificationPressure := 0
  , connectance := 1
  , compressionResidue := 0
  , effectiveSample := 0
  , fitnessProxy := 0 }

theorem couchForestGenome_eq :
    forestGenome couchForestSignals = couchGenome := by
  rfl

/-- The normalized couch route is atlas-routed, not directly local. -/
def couchNormalizedRouteMode : MorphicRoutingMode :=
  refineModeWithForest .exploitLocal couchForestSignals

theorem couchNormalizedRouteMode_eq :
    couchNormalizedRouteMode = .exploreAtlas := by
  native_decide

theorem couchNormalizedRouteAction_eq :
    morphicModeToAction couchNormalizedRouteMode = Semantics.RoutingAction.atlas := by
  native_decide

/-- The corrected sweep is no longer coupling-invariant. -/
theorem couchCouplingSummary_sensitive :
    couchCurvatureSummary .kappa050 ≠ couchCurvatureSummary .kappa250 := by
  native_decide

/-- The corrected sweep reports increasing average curvature across the tested range. -/
theorem couchAvgCurvature_kappa050_lt_kappa250 :
    (couchCurvatureSummary .kappa050).avgCurvatureMilli <
      (couchCurvatureSummary .kappa250).avgCurvatureMilli := by
  native_decide

end Semantics.CouchFilterNormalization
