/-
HonestParameterReport.lean — Full Parameter Accounting for BraidCore

This module explicitly lists every parameter used by the BraidCore framework,
marks each as Derived, Fitted, PostHoc, or Adopted, and locks the total
count in Lean.  This directly addresses the adversarial review's Attack #5
("Parameter Count is 11+, Not 1") and Attack #1 ("133/137 is a fitted
parameter in disguise").

The honest accounting:
- Derived: the parameter follows from the Menger sponge construction
- Fitted: the parameter was chosen to minimize error on observed data
- PostHoc: the parameter was introduced after seeing the data
- Adopted: the parameter is borrowed from external physics/theory

Conventions:
  PascalCase types, camelCase functions.
  theorem for every boundary claim.
  #eval! for executable receipt.
  Namespace: Semantics.HonestParameterReport
-/

import Semantics.Toolkit

namespace Semantics.HonestParameterReport

open Semantics.Toolkit

-- ═══════════════════════════════════════════════════════════════════════════
-- §0  Parameter Provenance Type
-- ═══════════════════════════════════════════════════════════════════════════

/-- Provenance of a framework parameter:
    - `Derived` — follows from Menger sponge construction without empirical input
    - `Fitted` — chosen to minimize prediction error on observed data
    - `PostHoc` — introduced after seeing the data, rationalized retroactively
    - `Adopted` — borrowed from established physics or external theory
    - `Tuning` — arbitrary threshold chosen for grading/convenience -/
inductive Provenance
  | derived
  | fitted
  | postHoc
  | adopted
  | tuning
  deriving Repr, DecidableEq, BEq

def Provenance.toString : Provenance → String
  | derived  => "Derived"
  | fitted   => "Fitted"
  | postHoc  => "PostHoc"
  | adopted  => "Adopted"
  | tuning   => "Tuning"

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Parameter Entry Structure
-- ═══════════════════════════════════════════════════════════════════════════

/-- A single framework parameter with honest provenance. -/
structure ParameterEntry where
  index      : Nat
  name       : String
  value      : Rat
  role       : String
  provenance : Provenance
  evidence   : String
  deriving Repr

def mkParameter (idx : Nat) (n : String) (v : Rat) (r : String)
    (p : Provenance) (e : String) : ParameterEntry :=
  { index := idx, name := n, value := v, role := r, provenance := p, evidence := e }

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  The 11+ Parameters (Locked)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Parameter 1: z = 7/27 — Menger sponge void fraction.
    CLAIMED: Derived from Menger construction (7 voids removed from 3³=27).
    HONEST: Selected from 53 candidate fractions in [0.24, 0.28];
            13/50 = 0.26 matches Mott criterion exactly.
    Status: Fitted (look-elsewhere effect). -/
def p01_zMenger : ParameterEntry :=
  mkParameter 1 "z = 7/27" zMenger
    "Core void fraction"
    .fitted
    "Selected from 53 fractions in [0.24, 0.28]; 13/50 = 0.26 is closer to Mott"

/-- Parameter 2: 133/137 — 1-loop dislocation correction.
    CLAIMED: Derived from '4 dislocation axes in Menger sponge'.
    HONEST: Reverse-engineered to minimize error on species-area/percolation.
            Worsens Mott (0.28% → 3.20%) and magnetic Ni (0.68% → 3.57%).
    Status: Fitted (single-parameter fit, selectively applied). -/
def p02_corr1Loop : ParameterEntry :=
  mkParameter 2 "133/137" corr1Loop
    "1-loop dislocation correction"
    .fitted
    "Reverse-engineered; worsens 3/6 predictions it targets"

/-- Parameter 3: 18768/18769 — 2-loop correction.
    CLAIMED: Derived from fine-structure second-order effect.
    HONEST: Never used in any reported prediction.
    Status: PostHoc (present in theory but not validated). -/
def p03_corr2Loop : ParameterEntry :=
  mkParameter 3 "18768/18769" corr2Loop
    "2-loop fine-structure correction"
    .postHoc
    "Present in framework but zero reported predictions use it"

/-- Parameter 4: α_T = 7/360000 — Unified coupling.
    CLAIMED: Derived from '27 × 4000/3'.
    HONEST: Arbitrary combination; no derivation from first principles.
    Status: Fitted (constructed to match Jupiter-Casimir scale). -/
def p04_alphaT : ParameterEntry :=
  mkParameter 4 "α_T = 7/360000" alphaT
    "Unified coupling constant"
    .fitted
    "Arbitrary ratio; no first-principles derivation"

/-- Parameter 5: √10 — Burden wave speed.
    CLAIMED: Natural geometric constant.
    HONEST: Borrowed from 10-dimensional string theory reference.
    Status: Adopted (external to Menger framework). -/
def p05_sqrt10 : ParameterEntry :=
  mkParameter 5 "√10" ((31622777 : Rat) / 10000000)
    "Burden wave speed / expansion factor"
    .adopted
    "Borrowed from string theory 10D literature"

/-- Parameter 6: α_core = 15.5 — Rydberg core polarization.
    CLAIMED: Framework-derived quantum defect.
    HONEST: Standard QDT parameter, universal in atomic physics.
    Status: Adopted (standard atomic physics, not framework-specific). -/
def p06_alphaCore : ParameterEntry :=
  mkParameter 6 "α_core = 15.5" ((31 : Rat) / 2)
    "Rydberg core polarization quantum defect"
    .adopted
    "Standard QDT value from atomic physics literature"

/-- Parameter 7: σ² — Semantic mass Gaussian width.
    CLAIMED: Natural resolution of burden space.
    HONEST: Tuning parameter for Gaussian kernel; set to maximize ℳ_s.
    Status: Tuning (no independent measurement). -/
def p07_sigmaSq : ParameterEntry :=
  mkParameter 7 "σ² = 0.1" ((1 : Rat) / 10)
    "Semantic mass Gaussian kernel width"
    .tuning
    "Arbitrary width; chosen to make ℳ_s look favorable"

/-- Parameter 8: Grade thresholds.
    CLAIMED: Objective quality bins.
    HONEST: Chosen to maximize reported A-rate (79%).
            1%, 3%, 5%, 10%, 15%, 20%, 35%, 50% are arbitrary cutoffs.
    Status: Tuning (eight arbitrary thresholds). -/
def p08_gradeThresholds : ParameterEntry :=
  mkParameter 8 "Grade thresholds" 8
    "Letter-grade error bins (1%, 3%, 5%, ... 50%)"
    .tuning
    "Eight arbitrary cutoffs; chosen to maximize A-rate"

/-- Parameter 9: Domain classification rule.
    CLAIMED: Structural criterion (is_z_direct).
    HONEST: Post-hoc rule; 'z-direct' = 'close to 7/27', which uses z as input.
            Circular: z-directness is defined by proximity to z.
    Status: PostHoc (classification rule invented after seeing predictions). -/
def p09_domainClassification : ParameterEntry :=
  mkParameter 9 "Domain classification" 0
    "Which predictions receive 133/137 correction"
    .postHoc
    "Circular definition: z-direct = |pred − z|/z < 5%"

/-- Parameter 10: Correction level per prediction.
    CLAIMED: Determined by domain structure.
    HONEST: Chosen per-prediction (0, 1, or 2) to minimize individual error.
    Status: PostHoc (selection after seeing which level gives best fit). -/
def p10_correctionLevel : ParameterEntry :=
  mkParameter 10 "Correction level" 0
    "0-loop / 1-loop / 2-loop per prediction"
    .postHoc
    "Selected per prediction to minimize error; no structural rule"

/-- Parameter 11: P0 = 1 year — Fishing cycle base period.
    CLAIMED: Natural timescale from Menger construction.
    HONEST: Chosen to match the observed 61-year sardine cycle.
            With P0=1, P(5)=3⁵·7/27·133/137≈61.2 yr matches observation.
    Status: Fitted (calibrated to match sardine data). -/
def p11_P0 : ParameterEntry :=
  mkParameter 11 "P0 = 1 year" 1
    "Fishing cycle base period"
    .fitted
    "Calibrated to match 61-year sardine regime shift observation"

/-- Parameter 12: z-direct tolerance = 5%.
    CLAIMED: Natural structural boundary.
    HONEST: Chosen so that 7/27 is included but 28/27 is excluded.
    Status: Tuning (threshold set to capture intended predictions). -/
def p12_zTolerance : ParameterEntry :=
  mkParameter 12 "z-direct tolerance" zTolerance
    "Structural detector tolerance"
    .tuning
    "Chosen so 7/27 passes and 28/27 fails; no derivation"

/-- Parameter 13: Sweet-spot bounds [2%, 15%].
    CLAIMED: Natural correctable-error band.
    HONEST: Chosen to bracket the errors of predictions that 'need' correction.
    Status: Tuning (bounds set after observing error distribution). -/
def p13_sweetSpotBounds : ParameterEntry :=
  mkParameter 13 "Sweet-spot bounds" 0
    "2–15% correctable error band"
    .tuning
    "Chosen after seeing error distribution; no structural derivation"

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Parameter Registry
-- ═══════════════════════════════════════════════════════════════════════════

/-- The complete, honest parameter list. -/
def parameterRegistry : List ParameterEntry :=
  [ p01_zMenger, p02_corr1Loop, p03_corr2Loop, p04_alphaT
  , p05_sqrt10, p06_alphaCore, p07_sigmaSq, p08_gradeThresholds
  , p09_domainClassification, p10_correctionLevel, p11_P0
  , p12_zTolerance, p13_sweetSpotBounds
  ]

/-- Total parameter count. -/
def totalParameterCount : Nat := parameterRegistry.length

/-- Count parameters by provenance. -/
def countByProvenance (p : Provenance) : Nat :=
  (parameterRegistry.filter (fun e => e.provenance = p)).length

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Theorems — Honest Accounting (executable via native_decide)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Total parameter count is exactly 13. -/
theorem totalParameterCount_is13 : totalParameterCount = 13 := by
  native_decide

/-- Fitted parameters: z, 133/137, α_T, P0 = 4. -/
theorem fittedCount_is4 : countByProvenance .fitted = 4 := by
  native_decide

/-- PostHoc parameters: 2-loop, domain class, correction level = 3. -/
theorem postHocCount_is3 : countByProvenance .postHoc = 3 := by
  native_decide

/-- Tuning parameters: σ², grade thresholds, z tolerance, sweet spot = 4. -/
theorem tuningCount_is4 : countByProvenance .tuning = 4 := by
  native_decide

/-- Adopted parameters: √10, α_core = 2. -/
theorem adoptedCount_is2 : countByProvenance .adopted = 2 := by
  native_decide

/-- Derived parameters: NONE. Zero parameters are truly derived from the
    Menger sponge construction without empirical input.
    This is the honest admission the adversarial reviewer demanded. -/
theorem derivedCount_is0 : countByProvenance .derived = 0 := by
  native_decide

/-- The honest parameter budget: 13 total = 4 fitted + 3 postHoc + 4 tuning
    + 2 adopted + 0 derived.
    With 13 parameters and 19 data points, degrees of freedom = 6.
    This is honest phenomenology, not first-principles physics. -/
theorem parameterBudgetBalanced :
    countByProvenance .fitted + countByProvenance .postHoc +
    countByProvenance .tuning + countByProvenance .adopted +
    countByProvenance .derived = totalParameterCount := by
  native_decide

/-- The 133/137 correction is honestly classified as Fitted, not Derived.
    This theorem is the formal admission that Attack #1 identifies correctly. -/
theorem corr1Loop_isFitted_notDerived :
    p02_corr1Loop.provenance = .fitted ∧
    p02_corr1Loop.provenance ≠ .derived := by
  native_decide

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  Executable Receipts
-- ═══════════════════════════════════════════════════════════════════════════

#eval! totalParameterCount
#eval! countByProvenance .derived
#eval! countByProvenance .fitted
#eval! countByProvenance .postHoc
#eval! countByProvenance .tuning
#eval! countByProvenance .adopted

#eval! parameterRegistry

end Semantics.HonestParameterReport
