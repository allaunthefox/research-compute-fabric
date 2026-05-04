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
