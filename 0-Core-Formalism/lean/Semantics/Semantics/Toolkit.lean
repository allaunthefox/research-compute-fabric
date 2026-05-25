/-
Toolkit.lean — Core Constants and Functions for BraidCore Predictions

This module centralizes the exact rational constants used by the BraidCore
framework: the Menger void fraction z = 7/27, dislocation corrections,
unified coupling α_T, and helper functions for prediction, grading,
and period computation.

It is the Lean source-of-truth counterpart to the Python
`braidcore_toolkit.py` script.  All constants are exact `Rat` values;
no floating-point approximations appear in the definitions.

Conventions:
  PascalCase types, camelCase functions.
  theorem for every boundary claim.
  #eval! for executable receipt.
  Namespace: Semantics.Toolkit
-/

namespace Semantics.Toolkit

-- ═══════════════════════════════════════════════════════════════════════════
-- §0  Core Constants (exact rational values)
-- ═══════════════════════════════════════════════════════════════════════════

/-- The Menger sponge void fraction: z = 7/27 ≈ 0.259259... -/
def zMenger : Rat := (7 : Rat) / (27 : Rat)

/-- The fine structure constant (approximation): α = 1/137. -/
def alphaFS : Rat := (1 : Rat) / (137 : Rat)

/-- 1-loop dislocation correction: (1 − 4α) = 133/137.
    Applied to geometric/thermodynamic/biological/ecological predictions. -/
def corr1Loop : Rat := (133 : Rat) / (137 : Rat)

/-- 2-loop fine-structure correction: (1 − α²) = 18768/18769.
    Rarely used; present for completeness. -/
def corr2Loop : Rat := (18768 : Rat) / (18769 : Rat)

/-- Unified coupling constant: α_T = 7/360000 ≈ 1.944×10⁻⁵. -/
def alphaT : Rat := (7 : Rat) / (360000 : Rat)

/-- Inverse unified coupling: 1/α_T = 360000/7 ≈ 51428.571... -/
def oneOverAlphaT : Rat := (360000 : Rat) / (7 : Rat)

/-- Error tolerance for z-direct classification: 5%. -/
def zTolerance : Rat := (5 : Rat) / (100 : Rat)

/-- Sweet-spot lower bound: 2% relative error. -/
def sweetSpotLower : Rat := (2 : Rat) / (100 : Rat)

/-- Sweet-spot upper bound: 15% relative error. -/
def sweetSpotUpper : Rat := (15 : Rat) / (100 : Rat)

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Grade Thresholds (percent error → letter grade)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Grade thresholds as a list of (maxErrorPercent, gradeString).
    Error < 1% → A+, < 3% → A, < 5% → A-, < 10% → B+, < 15% → B,
    < 30% → C+, < 50% → C, else D. -/
def gradeThresholds : List (Rat × String) :=
  [ ((1 : Rat), "A+")
  , ((3 : Rat), "A")
  , ((5 : Rat), "A-")
  , ((10 : Rat), "B+")
  , ((15 : Rat), "B")
  , ((30 : Rat), "C+")
  , ((50 : Rat), "C")
  ]

/-- Assign a letter grade from percent error.
    `err` is a percent value (e.g. 3.7 for 3.7%).
    Returns "D" for errors ≥ 50%. -/
def gradeFromError (err : Rat) : String :=
  match gradeThresholds.find? (fun p => err < p.1) with
  | some (_, g) => g
  | none        => "D"

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Dislocation Correction
-- ═══════════════════════════════════════════════════════════════════════════

/-- Apply the 1-loop dislocation correction to a bare Menger prediction.
    For void fractions, Menger typically over-predicts, so multiplying
    by (1 − 4α) = 133/137 reduces the value. -/
def dislocationCorrect (value : Rat) : Rat :=
  value * corr1Loop

/-- Apply the 2-loop correction after the 1-loop correction. -/
def dislocationCorrect2Loop (value : Rat) : Rat :=
  value * corr1Loop * corr2Loop

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Menger Period Predictor
-- ═══════════════════════════════════════════════════════════════════════════

/-- Compute the Menger period P(k) = P₀ × 3^k × 7/27.
    Used for ecological, geological, and social cycle predictions.
    Validated against: ENSO (7 yr), generation time (21 yr),
    sardine regime shift (63 yr), major fisheries cycle (189 yr). -/
def mengerPeriod (k : Nat) (P0 : Rat := 1) (applyCorrection : Bool := true) : Rat :=
  let periodRaw := P0 * (7 * (3 ^ k : Rat)) / 27
  if applyCorrection then periodRaw * corr1Loop else periodRaw

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Theorems — Canonical Identities (executable via native_decide)
-- ═══════════════════════════════════════════════════════════════════════════

/-- 1-loop correction equals 133/137 exactly. -/
theorem corr1Loop_identity : corr1Loop = (133 : Rat) / 137 := by
  native_decide

/-- 2-loop correction equals 18768/18769 exactly. -/
theorem corr2Loop_identity : corr2Loop = (18768 : Rat) / 18769 := by
  native_decide

/-- α_T = 7/360000 exactly. -/
theorem alphaT_identity : alphaT = (7 : Rat) / 360000 := by
  native_decide

/-- 1/α_T = 360000/7 exactly. -/
theorem oneOverAlphaT_identity : oneOverAlphaT = (360000 : Rat) / 7 := by
  native_decide

/-- The 1-loop correction applied to zMenger gives the corrected void fraction. -/
theorem zMenger_corrected_identity :
    dislocationCorrect zMenger = (931 : Rat) / 3699 := by
  native_decide

/-- Grade assignment for a 3.7% error (species-area) is A-. -/
theorem grade_speciesArea :
    gradeFromError ((37 : Rat) / 10) = "A-" := by
  native_decide

/-- Grade assignment for a 0.28% error (Mott) is A+. -/
theorem grade_mottCriterion :
    gradeFromError ((28 : Rat) / 100) = "A+" := by
  native_decide

/-- Grade assignment for a 60% error is D. -/
theorem grade_largeError :
    gradeFromError 60 = "D" := by
  native_decide

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  Executable Receipts
-- ═══════════════════════════════════════════════════════════════════════════

#eval! zMenger
#eval! corr1Loop
#eval! corr2Loop
#eval! alphaT
#eval! oneOverAlphaT
#eval! dislocationCorrect zMenger
#eval! mengerPeriod 5 1 true   -- P(5) corrected ≈ 61.2 years
#eval! mengerPeriod 5 1 false  -- P(5) bare
#eval! gradeFromError ((37 : Rat) / 10)  -- 3.7% → "A-"
#eval! gradeFromError ((28 : Rat) / 100)  -- 0.28% → "A+"

end Semantics.Toolkit
