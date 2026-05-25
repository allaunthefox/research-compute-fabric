/-
ParameterSensitivity.lean -- Sensitivity of Predictions to z = 7/27

This module computes how much each prediction changes when the core parameter
z = 7/27 is perturbed by the look-elsewhere width (the distance to the
nearest competitive fraction, 13/50 = 0.26).

If a prediction shifts by MORE than its uncertainty envelope when z is
perturbed by the look-elsewhere width, the prediction is UNSTABLE -- it
rests on a knife edge and the choice of 7/27 is critical.

If a prediction shifts by LESS than its uncertainty envelope, it is STABLE --
the prediction is robust to the fraction-selection uncertainty.

Conventions:
  PascalCase types, camelCase functions.
  theorem for every boundary claim.
  #eval! for executable receipt.
  Namespace: Semantics.ParameterSensitivity
-/

import Semantics.Toolkit

namespace Semantics.ParameterSensitivity

open Semantics.Toolkit

-- =========================================================================
-- S0  Look-Elsewhere Width
-- =========================================================================

/-- The look-elsewhere width: distance from z = 7/27 to the nearest competitive
    fraction (13/50 = 0.26).  Computed exactly in FractionScan.lean:
    |7/27 - 13/50| = |350 - 351| / 1350 = 1/1350.
    This is the maximum rational perturbation that could have been chosen
    if a different fraction had been selected. -/
def lookElsewhereWidth : Rat := (1 : Rat) / 1350

/-- The 1-loop correction factor c = 133/137. -/
def corrFactor : Rat := (133 : Rat) / 137

-- =========================================================================
-- S1  Derivatives d prediction/dz
-- =========================================================================

/-- P1 Rydberg d1 = 2/137. Independent of z.
    dd1/dz = 0. -/
def derivP01 : Rat := 0

/-- P2 Magnetic wall fraction = z * 133/137.
    df/dz = 133/137. -/
def derivP02 : Rat := corrFactor

/-- P3 Percolation p_c = z.
    dp/dz = 1. -/
def derivP03 : Rat := 1

/-- P4 Ecological period P(5) = 3^5 * z * 133/137 = 243 * z * 133/137.
    dP/dz = 243 * 133/137.
    NOTE: P4 is WITHDRAWN (requires fitted P0 = 1 year). -/
def derivP04 : Rat := 243 * corrFactor

/-- P5 Mott criterion = z.
    dn/dz = 1. -/
def derivP05 : Rat := 1

/-- P6 Weak value limit = 1/a_T = 360000/7. Independent of z.
    dA_w/dz = 0. -/
def derivP06 : Rat := 0

/-- P7 Species-area exponent = z * 133/137.
    dz/dz = 133/137. -/
def derivP07 : Rat := corrFactor

/-- P8 Granular void fraction = z.
    dphi/dz = 1. -/
def derivP08 : Rat := 1

/-- P9 FQHE nu_min = z.
    dnu/dz = 1. -/
def derivP09 : Rat := 1

/-- P10 Jupiter resonance null. Independent of z.
    d/dz = 0. -/
def derivP10 : Rat := 0

/-- P11 Menger period ratio P(k+1)/P(k) = 3.
    Independent of z (derivative = 0), so perturbation = 0.
    This is the dimensionless REPLACEMENT for withdrawn P4. -/
def derivP11 : Rat := 0

-- =========================================================================
-- S2  Maximum Perturbation = derivative * lookElsewhereWidth
-- =========================================================================

/-- Maximum perturbation of a prediction under look-elsewhere width. -/
def maxPerturbation (deriv : Rat) : Rat :=
  deriv * lookElsewhereWidth

-- =========================================================================
-- S3  Uncertainty Envelopes (from PreRegisteredPredictions, in Rat form)
-- =========================================================================

/-- P1: d1 = 2/137 ~ 0.0146, s = 0.002. -/
def sigmaP01 : Rat := (2 : Rat) / 1000

/-- P2: f_wall = 931/3699 ~ 0.252, s = 0.03. -/
def sigmaP02 : Rat := (3 : Rat) / 100

/-- P3: p_c = 7/27 ~ 0.259, s = 0.015. -/
def sigmaP03 : Rat := (15 : Rat) / 1000

/-- P4: P(5) ~ 61.2 yr, s = 8 yr.  WITHDRAWN. -/
def sigmaP04 : Rat := 8

/-- P5: n_c^(1/3)*a_B = 7/27 ~ 0.259, s = 0.01. -/
def sigmaP05 : Rat := (1 : Rat) / 100

/-- P6: A_w(max) ~ 51,429, s = 5,000. -/
def sigmaP06 : Rat := 5000

/-- P7: z = 931/3699 ~ 0.252, s = 0.03. -/
def sigmaP07 : Rat := (3 : Rat) / 100

/-- P8: phi_void = 7/27 ~ 0.259, s = 0.02. -/
def sigmaP08 : Rat := (2 : Rat) / 100

/-- P9: nu_min ~ 7/27 ~ 0.259, s = 0.016 (exploratory, wide). -/
def sigmaP09 : Rat := (3277 : Rat) / (65536 * 2)  -- half envelope width ~ 0.025

/-- P10: null, s = 2e-5. -/
def sigmaP10 : Rat := (2 : Rat) / 100000

/-- P11: period ratio = 3, s = 0.3 (10% relative). -/
def sigmaP11 : Rat := (3 : Rat) / 10

-- =========================================================================
-- S4  Stability Check: perturbation < sigma ?
-- =========================================================================

/-- Is the prediction stable? True if max perturbation < sigma. -/
def isStable (deriv sigma : Rat) : Bool :=
  maxPerturbation deriv < sigma

-- =========================================================================
-- S5  Theorems -- Stability (executable via native_decide)
-- =========================================================================

/-- P1 is stable (derivative = 0, perturbation = 0 < 0.002). -/
theorem p01Stable :
    isStable derivP01 sigmaP01 = true := by
  native_decide

/-- P2 is stable: perturbation = (133/137) * (1/1350) ~ 0.00072 < 0.03. -/
theorem p02Stable :
    isStable derivP02 sigmaP02 = true := by
  native_decide

/-- P3 is stable: perturbation = 1/1350 ~ 0.00074 < 0.015. -/
theorem p03Stable :
    isStable derivP03 sigmaP03 = true := by
  native_decide

/-- P4 is stable: perturbation = 243 * (133/137) * (1/1350) ~ 0.175 < 8.
    NOTE: P4 is withdrawn for dimensional inconsistency, not instability. -/
theorem p04Stable :
    isStable derivP04 sigmaP04 = true := by
  native_decide

/-- P5 is stable: perturbation = 1/1350 ~ 0.00074 < 0.01. -/
theorem p05Stable :
    isStable derivP05 sigmaP05 = true := by
  native_decide

/-- P6 is stable (derivative = 0, perturbation = 0 < 5000). -/
theorem p06Stable :
    isStable derivP06 sigmaP06 = true := by
  native_decide

/-- P7 is stable: perturbation = (133/137) * (1/1350) ~ 0.00072 < 0.03. -/
theorem p07Stable :
    isStable derivP07 sigmaP07 = true := by
  native_decide

/-- P8 is stable: perturbation = 1/1350 ~ 0.00074 < 0.02. -/
theorem p08Stable :
    isStable derivP08 sigmaP08 = true := by
  native_decide

/-- P9 is stable: perturbation = 1/1350 ~ 0.00074 < 0.025. -/
theorem p09Stable :
    isStable derivP09 sigmaP09 = true := by
  native_decide

/-- P10 is stable (derivative = 0, perturbation = 0 < 2e-5). -/
theorem p10Stable :
    isStable derivP10 sigmaP10 = true := by
  native_decide

/-- P11 is stable (derivative = 0, perturbation = 0 < 0.3). -/
theorem p11Stable :
    isStable derivP11 sigmaP11 = true := by
  native_decide

/-- ALL 11 predictions (including withdrawn P4) are stable under look-elsewhere
    perturbation. This is the key theorem: the choice of 7/27 vs 13/50 does NOT
    cause any prediction to shift outside its uncertainty envelope.
    Note: P4 is withdrawn for dimensional inconsistency, NOT for instability. -/
theorem allPredictionsStable :
    isStable derivP01 sigmaP01 = true /\
    isStable derivP02 sigmaP02 = true /\
    isStable derivP03 sigmaP03 = true /\
    isStable derivP04 sigmaP04 = true /\
    isStable derivP05 sigmaP05 = true /\
    isStable derivP06 sigmaP06 = true /\
    isStable derivP07 sigmaP07 = true /\
    isStable derivP08 sigmaP08 = true /\
    isStable derivP09 sigmaP09 = true /\
    isStable derivP10 sigmaP10 = true /\
    isStable derivP11 sigmaP11 = true := by
  constructor
  . native_decide
  constructor
  . native_decide
  constructor
  . native_decide
  constructor
  . native_decide
  constructor
  . native_decide
  constructor
  . native_decide
  constructor
  . native_decide
  constructor
  . native_decide
  constructor
  . native_decide
  constructor
  . native_decide
  . native_decide

-- =========================================================================
-- S6  Stability Ratios (how many sigmas fit in the perturbation)
-- =========================================================================

/-- Stability ratio: sigma / maxPerturbation. Higher = more stable.
    For deriv = 0, returns infinity representation (a large sentinel). -/
def stabilityRatio (deriv sigma : Rat) : Rat :=
  if deriv = 0 then 1000000  -- effectively infinite for zero-derivative preds
  else sigma / maxPerturbation deriv

/-- P2 stability ratio: sigma / perturbation ~ 0.03 / 0.00072 ~ 41.7. -/
theorem p02StabilityRatio :
    stabilityRatio derivP02 sigmaP02 > 40 := by
  native_decide

/-- P4 stability ratio: sigma / perturbation ~ 8 / 0.175 ~ 45.7. -/
theorem p04StabilityRatio :
    stabilityRatio derivP04 sigmaP04 > 40 := by
  native_decide

/-- P5 stability ratio: sigma / perturbation ~ 0.01 / 0.00074 ~ 13.5. -/
theorem p05StabilityRatio :
    stabilityRatio derivP05 sigmaP05 > 10 := by
  native_decide

-- =========================================================================
-- S7  Honest Assessment
-- =========================================================================

/- Stability assessment:

    All 11 predictions are stable under the look-elsewhere perturbation.
    The maximum shift from z = 7/27 to z = 13/50 (Dz = 1/1350 ~ 0.00074)
    is smaller than the uncertainty envelope for every prediction.

    The strongest stability comes from:
    - P1, P6, P10, P11 (derivative = 0): completely independent of z
    - P2, P7 (derivative = 133/137 ~ 0.97): perturbation ~ 0.00072
    - P3, P5, P8, P9 (derivative = 1): perturbation ~ 0.00074
    - P4 (derivative = 243 * 133/137 ~ 236): perturbation ~ 0.175 yr

    The adversarial claim "7/27 is a knife-edge choice" is formally
    disproven: even if the nearest alternative fraction (13/50) had been
    chosen, all predictions would remain within their stated uncertainty.

    However, this does NOT mean 7/27 is physically motivated. It only means
    the framework's predictions are not numerologically fragile. -/

-- =========================================================================
-- S8  Executable Receipts
-- =========================================================================

#eval! lookElsewhereWidth
#eval! maxPerturbation derivP02
#eval! maxPerturbation derivP04
#eval! maxPerturbation derivP05
#eval! stabilityRatio derivP02 sigmaP02
#eval! stabilityRatio derivP04 sigmaP04

end Semantics.ParameterSensitivity
