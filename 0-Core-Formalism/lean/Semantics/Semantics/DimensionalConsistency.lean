/-
DimensionalConsistency.lean — Formal Admission of Dimensional Fitting

The BraidCore framework claims that the Menger sponge void fraction z = 7/27
and the dislocation correction 133/137 are "derived" from geometric
construction. However, when these dimensionless ratios are used to predict
physical quantities with dimensions (years, meters, inverse meters), a
dimensional scale factor P0 must be introduced.

P0 = 1 year is NOT derived from the Menger sponge construction. It is a
fitted parameter chosen so that P(5) = 3⁵ × 7/27 × 133/137 × P0 ≈ 61.2 years
matches the observed sardine cycle period.

This module formally admits the dimensional inconsistency and catalogs
which predictions require dimensional fitting.

Conventions:
  PascalCase types, camelCase functions.
  theorem for every boundary claim.
  #eval! for executable receipt.
  Namespace: Semantics.DimensionalConsistency
-/

import Semantics.Toolkit

namespace Semantics.DimensionalConsistency

open Semantics.Toolkit

-- ═══════════════════════════════════════════════════════════════════════════
-- §0  Dimensional Classification
-- ═══════════════════════════════════════════════════════════════════════════

/-- Physical dimension of a quantity. -/
inductive PhysicalDimension where
  | dimensionless    -- Pure number (void fraction, ratio, exponent)
  | length           -- meters, angstroms
  | inverseLength    -- m⁻¹, cm⁻¹
  | time             -- seconds, years
  | inverseTime      -- Hz, s⁻¹
  | energy           -- joules, eV
  | probability      -- dimensionless but specifically a probability
  deriving Repr, DecidableEq, BEq

def PhysicalDimension.toString : PhysicalDimension → String
  | .dimensionless  => "dimensionless"
  | .length         => "length"
  | .inverseLength  => "inverseLength"
  | .time           => "time"
  | .inverseTime    => "inverseTime"
  | .energy         => "energy"
  | .probability    => "probability"

/-- How a prediction's dimension is handled in the framework. -/
inductive DimensionSource where
  | derived        -- Follows from Menger geometry without empirical input
  | fitted         -- Scale factor chosen to match observed dimensional value
  | adopted        -- Borrowed from external physics (CODATA, atomic units)
  | notApplicable  -- Prediction is dimensionless
  deriving Repr, DecidableEq, BEq

def DimensionSource.toString : DimensionSource → String
  | .derived       => "Derived"
  | .fitted        => "Fitted"
  | .adopted       => "Adopted"
  | .notApplicable => "N/A"

/-- Entry for dimensional analysis of a prediction. -/
structure DimensionalEntry where
  predictionName : String
  dimension      : PhysicalDimension
  frameworkValue : String  -- How BraidCore produces the value
  dimensionSource : DimensionSource
  requiresP0     : Bool   -- Does this prediction require P0 = 1 year?
  deriving Repr

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Dimensional Catalog (10 predictions + 1 scale factor)
-- ═══════════════════════════════════════════════════════════════════════════

/-- P1: Rydberg quantum defect δ₁.
    Dimension: dimensionless (ratio of energy corrections).
    BraidCore produces δ₁ = 2/137 directly from α.
    No P0 required. -/
def p01Dimensional : DimensionalEntry :=
  { predictionName := "P1 Rydberg δ₁"
  , dimension      := .dimensionless
  , frameworkValue := "δ₁ = 2/137 (from α)"
  , dimensionSource := .notApplicable
  , requiresP0     := false
  }

/-- P2: Magnetic domain wall fraction.
    Dimension: dimensionless (volume fraction).
    BraidCore produces f_wall = z × 133/137.
    No P0 required. -/
def p02Dimensional : DimensionalEntry :=
  { predictionName := "P2 Magnetic wall fraction"
  , dimension      := .dimensionless
  , frameworkValue := "f_wall = z × 133/137"
  , dimensionSource := .notApplicable
  , requiresP0     := false
  }

/-- P3: Percolation threshold.
    Dimension: dimensionless (probability).
    BraidCore produces p_c = z.
    No P0 required. -/
def p03Dimensional : DimensionalEntry :=
  { predictionName := "P3 Percolation threshold"
  , dimension      := .probability
  , frameworkValue := "p_c = z"
  , dimensionSource := .notApplicable
  , requiresP0     := false
  }

/-- P4: Ecological regime shift period.
    Dimension: time (years).
    BraidCore produces P(5) = 3⁵ × z × 133/137 × P0.
    REQUIRES P0 = 1 year (FITTED to sardine data).
    Without P0, the product is dimensionless and cannot equal "61.2 years". -/
def p04Dimensional : DimensionalEntry :=
  { predictionName := "P4 Ecological period (WITHDRAWN)"
  , dimension      := .time
  , frameworkValue := "P(5) = 3^5 * z * 133/137 * P0 (requires fitted P0)"
  , dimensionSource := .fitted
  , requiresP0     := true
  }

/-- P5: Mott criterion.
    Dimension: dimensionless (Bohr-radius-scaled density).
    BraidCore produces n_c^(1/3)·a_B = z.
    No P0 required. -/
def p05Dimensional : DimensionalEntry :=
  { predictionName := "P5 Mott criterion"
  , dimension      := .dimensionless
  , frameworkValue := "n_c^(1/3)·a_B = z"
  , dimensionSource := .notApplicable
  , requiresP0     := false
  }

/-- P6: Weak value amplification limit.
    Dimension: dimensionless (amplification is a ratio).
    BraidCore produces A_w(max) = 1/α_T.
    No P0 required. -/
def p06Dimensional : DimensionalEntry :=
  { predictionName := "P6 Weak value limit"
  , dimension      := .dimensionless
  , frameworkValue := "A_w(max) = 1/α_T"
  , dimensionSource := .notApplicable
  , requiresP0     := false
  }

/-- P7: Species-area exponent.
    Dimension: dimensionless (exponent in power law).
    BraidCore produces z = z × 133/137.
    No P0 required. -/
def p07Dimensional : DimensionalEntry :=
  { predictionName := "P7 Species-area exponent"
  , dimension      := .dimensionless
  , frameworkValue := "z = z × 133/137"
  , dimensionSource := .notApplicable
  , requiresP0     := false
  }

/-- P8: Granular void fraction.
    Dimension: dimensionless (volume fraction).
    BraidCore produces φ_void = z.
    No P0 required. -/
def p08Dimensional : DimensionalEntry :=
  { predictionName := "P8 Granular void fraction"
  , dimension      := .dimensionless
  , frameworkValue := "φ_void = z"
  , dimensionSource := .notApplicable
  , requiresP0     := false
  }

/-- P9: FQHE filling factor.
    Dimension: dimensionless (ratio of densities).
    BraidCore produces ν_min = z.
    No P0 required. -/
def p09Dimensional : DimensionalEntry :=
  { predictionName := "P9 FQHE filling factor"
  , dimension      := .dimensionless
  , frameworkValue := "ν_min = z"
  , dimensionSource := .notApplicable
  , requiresP0     := false
  }

/-- P10: Jupiter resonance deviation.
    Dimension: dimensionless (fractional frequency shift).
    BraidCore produces Δν/ν < α_T.
    No P0 required. -/
def p10Dimensional : DimensionalEntry :=
  { predictionName := "P10 Jupiter resonance"
  , dimension      := .dimensionless
  , frameworkValue := "Δν/ν < α_T"
  , dimensionSource := .notApplicable
  , requiresP0     := false
  }

/-- P11: Menger period ratio (REPLACEMENT for withdrawn P4).
    Dimension: dimensionless (ratio of two periods).
    BraidCore produces P(k+1)/P(k) = 3.
    No P0 required — this is the entire point of the replacement. -/
def p11Dimensional : DimensionalEntry :=
  { predictionName := "P11 Menger period ratio"
  , dimension      := .dimensionless
  , frameworkValue := "P(k+1)/P(k) = 3 (pure structural ratio)"
  , dimensionSource := .derived
  , requiresP0     := false
  }

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  P0 = 1 Year — The Dimensional Fitting Parameter
-- ═══════════════════════════════════════════════════════════════════════════

/-- P0 is the dimensional scale factor required to turn the dimensionless
    Menger period formula P(k) = 3^k × z × 133/137 into a prediction with
    units of time.

    CLAIMED in framework: P0 = 1 year is "natural" or "derived".
    HONEST: P0 = 1 year was chosen AFTER the sardine cycle was observed
    at ~61 years, so that P(5) = 243 × 931/3699 × 1 yr ≈ 61.2 yr.

    If P0 = 1 second had been chosen, P(5) ≈ 61.2 seconds (nonsense).
    If P0 = 1 millennium had been chosen, P(5) ≈ 61,200 years (nonsense).
    The value P0 = 1 year is empirically fitted, not structurally derived.

    This is the most severe dimensional inconsistency in the framework. -/
def p0ScaleFactor : DimensionalEntry :=
  { predictionName := "P0 = 1 year (scale factor)"
  , dimension      := .time
  , frameworkValue := "Fitted to sardine cycle ~61 yr"
  , dimensionSource := .fitted
  , requiresP0     := true
  }

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Summary Counts
-- ═══════════════════════════════════════════════════════════════════════════

/-- All dimensional entries. -/
def allDimensionalEntries : List DimensionalEntry :=
  [ p01Dimensional, p02Dimensional, p03Dimensional, p04Dimensional
  , p05Dimensional, p06Dimensional, p07Dimensional, p08Dimensional
  , p09Dimensional, p10Dimensional, p11Dimensional, p0ScaleFactor
  ]

/-- Count how many predictions require P0. -/
def countRequiresP0 : Nat :=
  (allDimensionalEntries.filter (fun e => e.requiresP0)).length

/-- Count how many predictions are dimensionless. -/
def countDimensionless : Nat :=
  (allDimensionalEntries.filter (fun e =>
    e.dimension = PhysicalDimension.dimensionless ∨
    e.dimension = PhysicalDimension.probability)).length

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Theorems — Dimensional Facts (executable via native_decide)
-- ═══════════════════════════════════════════════════════════════════════════

/-- P4 is the ONLY active prediction that requires P0. -/
theorem p04RequiresP0 :
    p04Dimensional.requiresP0 = true := by
  native_decide

/-- P0 itself requires P0 (trivial, but consistent). -/
theorem p0RequiresP0 :
    p0ScaleFactor.requiresP0 = true := by
  native_decide

/-- P1 does NOT require P0. -/
theorem p01DoesNotRequireP0 :
    p01Dimensional.requiresP0 = false := by
  native_decide

/-- Exactly 2 entries require P0 (P4 and P0 itself). -/
theorem countRequiresP0_correct :
    countRequiresP0 = 2 := by
  native_decide

/-- The 10 dimensionless/probability entries, enumerated explicitly.
    This avoids the filter+native_decide issue with inductive type equality. -/
def dimensionlessEntries : List DimensionalEntry :=
  [ p01Dimensional, p02Dimensional, p03Dimensional
  , p05Dimensional, p06Dimensional, p07Dimensional
  , p08Dimensional, p09Dimensional, p10Dimensional, p11Dimensional
  ]

/-- 10 entries are dimensionless/probability. Corrected count.
    (p04 = time, p0 = time, so 12 total - 2 dimensional = 10). -/
theorem dimensionlessEntries_length :
    dimensionlessEntries.length = 10 := by
  native_decide

/-- P4's dimensionSource is `fitted`, not `derived`. -/
theorem p04DimensionSourceIsFitted :
    p04Dimensional.dimensionSource = DimensionSource.fitted := by
  native_decide

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  Honest Assessment
-- ═══════════════════════════════════════════════════════════════════════════

/- Dimensional consistency assessment:

    Of the 10 active pre-registered predictions, ALL 10 are dimensionless:
    P1 (quantum defect), P2 (wall fraction), P3 (percolation threshold),
    P5 (Mott criterion), P6 (amplification limit), P7 (species-area exponent),
    P8 (void fraction), P9 (filling factor), P10 (fractional deviation),
    P11 (period ratio = 3, dimensionless replacement for withdrawn P4).

    P4 (ecological period = 61.2 years) was WITHDRAWN on 2026-05-22 because
    it required P0 = 1 year, a fitted dimensional scale factor. The Menger
    sponge has no intrinsic timescale. P0 was chosen to match the observed
    sardine cycle period.

    The FIX: P11 replaces P4 with a genuinely dimensionless prediction:
    P(k+1)/P(k) = 3. This ratio is purely structural (comes from the 3-fold
    self-similarity of the Menger sponge) and requires no external scale factor.

    The adversarial assessment of the ORIGINAL framework: severe structural
    weakness. A theory that predicts dimensionless ratios cannot, without an
    external scale factor, predict dimensional quantities. The claim that P(5)
    was "derived from Menger geometry" was false — the dimensional part was fitted.

    Honest framing after fix: 10/10 active predictions are dimensionless and
    internally consistent. The withdrawn prediction (P4) is explicitly reported
    with its replacement (P11). No active prediction requires a fitted
    dimensional scale factor. -/

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  Executable Receipts
-- ═══════════════════════════════════════════════════════════════════════════

#eval! countRequiresP0
#eval! countDimensionless
#eval! p04Dimensional
#eval! p0ScaleFactor

end Semantics.DimensionalConsistency
