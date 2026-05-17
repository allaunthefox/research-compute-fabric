/-
DESIInvariant.lean — DESI DR1/DR2 Observational Invariants

Hardcodes DESI cosmological measurements as fixed-point constants.
These are the observational ground truth against which the 16D
horn-fiber / Menger/Koch model is projected.

All values are precomputed Q16_16 integers (scale = 65536) for
dimensionless fractions; dimensional quantities (H₀, r_d) are
raw Int with documented units.

Zero Float arithmetic in this file. Every constant is an explicit
Int literal computed offline.

Sources:
  DESI DR1: arXiv:2404.03002 (2024)
  DESI DR2: arXiv:2503.xxxxx (2025)

Conventions:
  PascalCase types, camelCase functions.
  structure for domain concepts.
  theorem for every boundary claim.
  #eval! for executable receipt (safe against transitive sorry).
  Namespace: Semantics.Physics.DESIInvariant
-/

import Semantics.FixedPoint

open Semantics

set_option linter.dupNamespace false

namespace Semantics.Physics.DESIInvariant

-- ═══════════════════════════════════════════════════════════════════════════
-- §0  Fixed-Point Scale
-- ═══════════════════════════════════════════════════════════════════════════

/-- Q16_16 scale factor: 1.0 = 65536 -/
def SCALE : Int := 65536

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  BAO Sound Horizon (raw Int, units: Mpc)
-- ═══════════════════════════════════════════════════════════════════════════

/-- r_d = 147.09 Mpc (DESI DR1) -/
def rD_DR1 : Int := 147

/-- r_d = 147.18 Mpc (DESI DR2) -/
def rD_DR2 : Int := 147

/-- r_d uncertainty, Q16_16: 0.26 × 65536 = 17039 -/
def rD_DR2_sigma : Int := 17039

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Dark Energy Equation of State (Q16_16, dimensionless)
--     w₀ and w_a are dimensionless parameters in [-2, 0]
-- ═══════════════════════════════════════════════════════════════════════════

/-- w₀ = -0.827 (DESI DR1) : -0.827 × 65536 = -54198 -/
def w0_DR1 : Int := -54198

/-- w₀ = -0.89  (DESI DR2) : -0.89  × 65536 = -58327 -/
def w0_DR2 : Int := -58327

/-- w₀ uncertainty (DR2), Q16_16: 0.04 × 65536 = 2621 -/
def w0_DR2_sigma : Int := 2621

/-- w_a = -0.75 (DESI DR1) : -0.75 × 65536 = -49152 -/
def wa_DR1 : Int := -49152

/-- w_a = -0.48 (DESI DR2) : -0.48 × 65536 = -31457 -/
def wa_DR2 : Int := -31457

/-- w_a uncertainty (DR2), Q16_16: 0.10 × 65536 = 6554 -/
def wa_DR2_sigma : Int := 6554

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  ΛCDM Reference Values (Q16_16, dimensionless)
-- ═══════════════════════════════════════════════════════════════════════════

/-- ΛCDM prediction: w₀ = -1.0 → -1.0 × 65536 = -65536 -/
def w0_LCDM : Int := -65536

/-- ΛCDM prediction: w_a = 0.0 -/
def wa_LCDM : Int := 0

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Hubble Constant (raw Int, units: km/s/Mpc × 100 for precision)
--     Stored as H₀ × 100 to preserve 0.01 precision without Float
-- ═══════════════════════════════════════════════════════════════════════════

/-- H₀ = 68.52 km/s/Mpc (DESI DR1), stored as 6852 -/
def H0_DR1 : Int := 6852

/-- H₀ = 68.26 km/s/Mpc (DESI DR2), stored as 6826 -/
def H0_DR2 : Int := 6826

/-- H₀ uncertainty (DR2), stored as 53 (i.e. ±0.53 km/s/Mpc × 100) -/
def H0_DR2_sigma : Int := 53

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  Matter Density and Fluctuation Amplitude (Q16_16, dimensionless)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Ω_m = 0.2947 (DESI DR2), Q16_16: 0.2947 × 65536 = 19312 -/
def OmegaM_DR2 : Int := 19312

/-- Ω_m uncertainty (DR2), Q16_16: 0.0056 × 65536 = 367 -/
def OmegaM_DR2_sigma : Int := 367

/-- σ₈ = 0.808 (DESI DR2), Q16_16: 0.808 × 65536 = 52953 -/
def sigma8_DR2 : Int := 52953

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  Observation Record
-- ═══════════════════════════════════════════════════════════════════════════

/-- Named DESI parameter (finite, indexable) -/
inductive DESIParam where
  | w0
  | wa
  | h0
  | omegaM
  | sigma8
  | rD
  deriving Repr, DecidableEq

/-- Packaged DESI observation set -/
structure DESIObservation where
  w0 : Int
  wa : Int
  h0 : Int
  omegaM : Int
  sigma8 : Int
  rD : Int
  w0_sigma : Int
  wa_sigma : Int
  h0_sigma : Int
  omegaM_sigma : Int
  rD_sigma : Int
  w0_LCDM : Int
  wa_LCDM : Int
  deriving Repr, Inhabited

/-- DESI DR2 preferred invariant set -/
def desiDR2 : DESIObservation :=
  { w0            := w0_DR2
  , wa            := wa_DR2
  , h0            := H0_DR2
  , omegaM        := OmegaM_DR2
  , sigma8        := sigma8_DR2
  , rD            := rD_DR2
  , w0_sigma      := w0_DR2_sigma
  , wa_sigma      := wa_DR2_sigma
  , h0_sigma      := H0_DR2_sigma
  , omegaM_sigma  := OmegaM_DR2_sigma
  , rD_sigma      := rD_DR2_sigma
  , w0_LCDM       := w0_LCDM
  , wa_LCDM       := wa_LCDM
  }

-- ═══════════════════════════════════════════════════════════════════════════
-- §7  Key Observational Theorems
-- ═══════════════════════════════════════════════════════════════════════════

/-- DESI DR2 finds w₀ > -1 (dark energy is not a cosmological constant) -/
theorem w0_above_LCDM : w0_DR2 > w0_LCDM := by
  native_decide

/-- DESI DR2 finds w_a < 0 (dark energy was stronger in the past) -/
theorem wa_below_LCDM : wa_DR2 < wa_LCDM := by
  native_decide

/-- w₀ is within 3σ of the reported central value -/
theorem w0_in_3sigma :
  -58327 - 3*2621 ≤ w0_DR2 ∧ w0_DR2 ≤ -58327 + 3*2621 := by
  native_decide

/-- w_a is within 3σ of the reported central value -/
theorem wa_in_3sigma :
  -31457 - 3*6554 ≤ wa_DR2 ∧ wa_DR2 ≤ -31457 + 3*6554 := by
  native_decide

/-- Ω_m is within 3σ of the reported central value -/
theorem omegam_in_3sigma :
  19312 - 3*367 ≤ OmegaM_DR2 ∧ OmegaM_DR2 ≤ 19312 + 3*367 := by
  native_decide

-- ═══════════════════════════════════════════════════════════════════════════
-- §8  Executable Receipts
-- ═══════════════════════════════════════════════════════════════════════════

-- Receipt: DESI DR2 w₀ = -0.89 in Q16_16
#eval! w0_DR2

-- Receipt: DESI DR2 w_a = -0.48 in Q16_16
#eval! wa_DR2

-- Receipt: ΛCDM w₀ = -1.0 in Q16_16
#eval! w0_LCDM

-- Receipt: DESI DR2 H₀ = 68.26 (×100)
#eval! H0_DR2

-- Receipt: DESI DR2 Ω_m = 0.2947 in Q16_16
#eval! OmegaM_DR2

-- Receipt: DESI DR2 σ₈ = 0.808 in Q16_16
#eval! sigma8_DR2

-- Receipt: DESI DR2 r_d = 147 Mpc
#eval! rD_DR2

end Semantics.Physics.DESIInvariant
