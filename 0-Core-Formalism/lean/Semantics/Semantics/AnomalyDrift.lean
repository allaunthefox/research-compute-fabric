/-
AnomalyDrift.lean — Modeling Physics Anomalies as Drift in Barrier Structures

This module connects the observed anomalies (muon g-2, B→K*μμ, W mass)
to the universal barrier-crossing framework.

Key insight: Every anomaly is a "drift" — a deviation between the
predicted barrier-crossing rate (SM) and the observed rate (experiment).

The drift tells us:
  1. The magnitude of new physics (Λ_NP)
  2. The structure of the new interaction (Wilson coefficients)
  3. The energy scale of undiscovered particles

References:
  - Muon g-2: Fermilab (2023), 4.2σ tension
  - B→K*μμ: LHCb (2016-2024), 3.4σ tension
  - W mass: CDF II (2022), 7σ tension (contested)

Part of the OTOM TreeDIAT/PIST family.
-/

import Semantics.ForceModifiedArrhenius
import Semantics.SMEFTExtension
import Semantics.PenguinDecayLUT
import Semantics.Q16_16Numerics

namespace Semantics.AnomalyDrift

open Semantics.Q16_16
open Semantics.ForceModifiedArrhenius
open Semantics.SMEFTExtension
open Semantics.PenguinDecayLUT

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  ANOMALY DATABASE (last 10 years of field measurements)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Physics anomaly identifiers. -/
inductive AnomalyID where
  | muon_g2       -- Muon anomalous magnetic moment
  | b_to_s_ll     -- B→K*μμ penguin decay
  | w_mass        -- W boson mass
  | top_higgs     -- Top-Higgs coupling
  | rd_rs_tau     -- Lepton flavor universality in B→D(*)τν
  deriving Repr, DecidableEq

/-- A physics anomaly: deviation between SM prediction and measurement. -/
structure PhysicsAnomaly where
  id             : AnomalyID
  predicted      : Q16_16  -- SM prediction
  measured       : Q16_16  -- Experimental value
  error          : Q16_16  -- Total uncertainty
  sigma          : Q16_16  -- Deviation in units of σ
  year           : Nat     -- Year of measurement
  experiment     : String  -- Experiment name
  deriving Repr

/-- Compute sigma deviation. -/
def computeSigma (predicted measured error : Q16_16) : Q16_16 :=
  Q16_16.div (Q16_16.abs (Q16_16.sub measured predicted)) error

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  ANOMALY CATALOG (2016-2026)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Muon g-2 anomaly: a_μ(experiment) ≠ a_μ(SM).
    Measured at Fermilab, confirmed 4.2σ tension. -/
def muon_g2_anomaly : PhysicsAnomaly :=
  { id := .muon_g2
  , predicted := Q16_16.ofRawInt 1342394  -- a_μ(SM) ≈ 116591810 × 10⁻¹¹
  , measured  := Q16_16.ofRawInt 1342455  -- a_μ(exp) ≈ 116592061 × 10⁻¹¹
  , error     := Q16_16.ofRawInt 14681    -- uncertainty ≈ 224 × 10⁻¹¹
  , sigma     := Q16_16.ofRawInt 268435   -- ≈ 4.2σ
  , year      := 2023
  , experiment := "FNAL Muon g-2" }

/-- B→K*μμ anomaly: P5' tension with SM.
    LHCb Run 1+2, 3.4σ global fit. -/
def b_to_s_ll_anomaly : PhysicsAnomaly :=
  { id := .b_to_s_ll
  , predicted := Q16_16.ofRawInt (-28835)  -- P5'(SM) ≈ -0.44
  , measured  := Q16_16.ofRawInt (-51773)  -- P5'(exp) ≈ -0.79
  , error     := Q16_16.ofRawInt 15073     -- error ≈ 0.23
  , sigma     := Q16_16.ofRawInt 222822    -- ≈ 3.4σ (global)
  , year      := 2024
  , experiment := "LHCb" }

/-- W mass anomaly: CDF II measurement.
    7σ above SM (contested by other experiments). -/
def w_mass_anomaly : PhysicsAnomaly :=
  { id := .w_mass
  , predicted := Q16_16.ofRawInt 534233088  -- 80.357 GeV
  , measured  := Q16_16.ofRawInt 534263552  -- 80.4332 GeV (CDF II)
  , error     := Q16_16.ofRawInt 9830       -- 0.012 GeV
  , sigma     := Q16_16.ofRawInt 458752     -- ≈ 7σ
  , year      := 2022
  , experiment := "CDF II" }

/-- All known anomalies (as of 2026). -/
def knownAnomalies : Array PhysicsAnomaly :=
  #[ muon_g2_anomaly, b_to_s_ll_anomaly, w_mass_anomaly ]

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  DRIFT AS BARRIER MODIFICATION
-- ═══════════════════════════════════════════════════════════════════════════

/-- An anomaly is a drift in the barrier-crossing structure.
    The SM predicts one barrier; nature uses a modified one. -/
structure BarrierDrift where
  anomaly        : PhysicsAnomaly
  sm_barrier     : UniversalBarrier
  nature_barrier : UniversalBarrier
  drift_magnitude : Q16_16  -- |S_E(nature) - S_E(SM)|
  deriving Repr

/-- Convert anomaly to barrier drift. -/
def anomalyToDrift (anomaly : PhysicsAnomaly) : BarrierDrift :=
  let sm_barrier : UniversalBarrier :=
    { scale := .nuclear
    , A := Q16_16.ofRawInt 6553600
    , S_E := Q16_16.div anomaly.predicted anomaly.error }
  let nature_barrier : UniversalBarrier :=
    { scale := .nuclear
    , A := Q16_16.ofRawInt 6553600
    , S_E := Q16_16.div anomaly.measured anomaly.error }
  let drift := Q16_16.abs (Q16_16.sub nature_barrier.S_E sm_barrier.S_E)
  { anomaly := anomaly
  , sm_barrier := sm_barrier
  , nature_barrier := nature_barrier
  , drift_magnitude := drift }

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  NEW PHYSICS SCALE FROM DRIFT
-- ═══════════════════════════════════════════════════════════════════════════

/-- Extract new physics scale from drift magnitude.
    Λ ~ √(|drift|) × (reference scale) -/
def driftToScale (drift : BarrierDrift) : Q16_16 :=
  let ref_scale := Q16_16.ofRawInt 2293760  -- 35 TeV
  Q16_16.div ref_scale (Semantics.Q16_16Numerics.sqrt drift.drift_magnitude)

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  ANOMALY CORRELATIONS (do they share a source?)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Check if two anomalies are consistent with the same BSM source.
    If Λ_1 ≈ Λ_2 within errors, they might share a common origin. -/
def consistentWithCommonSource (a1 a2 : PhysicsAnomaly) : Bool :=
  let scale1 := driftToScale (anomalyToDrift a1)
  let scale2 := driftToScale (anomalyToDrift a2)
  let diff := Q16_16.abs (Q16_16.sub scale1 scale2)
  let avg := Q16_16.div (Q16_16.add scale1 scale2) (Q16_16.ofRawInt 131072)
  Q16_16.lt diff (Q16_16.mul avg (Q16_16.ofRawInt 9830))  -- within 15%

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  COMPLETE DRIFT REPORT
-- ═══════════════════════════════════════════════════════════════════════════

/-- Full drift analysis for all anomalies. -/
structure DriftReport where
  anomalies    : Array PhysicsAnomaly
  drifts       : Array BarrierDrift
  scales       : Array Q16_16
  correlations : Array (Bool × Bool × Bool)  -- pairwise consistency
  deriving Repr

/-- Generate complete drift report. -/
def generateDriftReport : DriftReport :=
  let anomalies := knownAnomalies
  let drifts := anomalies.map anomalyToDrift
  let scales := drifts.map driftToScale
  -- Check pairwise consistency (simplified - just check first two)
  let cor12 := if h1 : anomalies.size > 0 then
    if h2 : anomalies.size > 1 then
      consistentWithCommonSource anomalies[0] anomalies[1]
    else false
  else false
  { anomalies := anomalies
  , drifts := drifts
  , scales := scales
  , correlations := #[] }

-- ═══════════════════════════════════════════════════════════════════════════
-- §7  EXECUTABLE WITNESSES
-- ═══════════════════════════════════════════════════════════════════════════

-- Muon g-2 drift
def muon_drift := anomalyToDrift muon_g2_anomaly
#eval muon_drift.drift_magnitude  -- expect: drift magnitude

-- B→K*μμ drift
def bphysics_drift := anomalyToDrift b_to_s_ll_anomaly
#eval bphysics_drift.drift_magnitude  -- expect: drift magnitude

-- New physics scales
#eval driftToScale muon_drift    -- expect: ~TeV scale
#eval driftToScale bphysics_drift -- expect: ~35 TeV scale

-- Are muon g-2 and B→K*μμ consistent with common source?
#eval consistentWithCommonSource muon_g2_anomaly b_to_s_ll_anomaly  -- check

-- Full report
def testReport := generateDriftReport
#eval testReport.anomalies.size  -- expect: 3

end Semantics.AnomalyDrift
