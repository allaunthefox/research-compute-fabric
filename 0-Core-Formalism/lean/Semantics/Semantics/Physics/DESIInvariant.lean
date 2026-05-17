/-
DESIInvariant.lean — DESI DR1/DR2 Observational Invariants

Hardcodes DESI cosmological measurements as fixed-point constants.

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

import Semantics.Physics.Q16Utils
open Semantics.Physics.Q16Utils

namespace Semantics.Physics.DESIInvariant

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  BAO Sound Horizon (raw Int, units: Mpc × 100 for precision)
-- ═══════════════════════════════════════════════════════════════════════════

/-- r_d = 147.09 Mpc (DESI DR1), stored as 14709 (×100) -/
def rdDr1 : Int := 14709

/-- r_d = 147.18 Mpc (DESI DR2), stored as 14718 (×100) -/
def rdDr2 : Int := 14718

/-- r_d uncertainty, Q16_16: 0.26 × 65536 = 17039 -/
def rdDr2Sigma : Int := 17039

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Dark Energy Equation of State (Q16_16, dimensionless)
--     w₀ and w_a are dimensionless parameters in [-2, 0]
-- ═══════════════════════════════════════════════════════════════════════════

/-- w₀ = -0.827 (DESI DR1, arXiv:2404.03002)
    Q16_16: -0.827 × 65536 = -54198 -/
def w0Dr1 : Int := -54198

/-- w₀ = -0.838 (DESI DR2, arXiv:2503.14738, DESI+CMB+Pantheon+)
    Q16_16: -0.838 × 65536 = -54919 -/
def w0Dr2 : Int := -54919

/-- w₀ uncertainty (DR2), Q16_16: ±0.055 × 65536 = 3604 -/
def w0Dr2Sigma : Int := 3604

/-- w_a = -0.75 (DESI DR1)
    Q16_16: -0.75 × 65536 = -49152 -/
def waDr1 : Int := -49152

/-- w_a = -0.59 (DESI DR2)
    Q16_16: -0.59 × 65536 = -38666 -/
def waDr2 : Int := -38666

/-- w_a uncertainty (DR2), Q16_16: ±0.25 × 65536 = 16384 -/
def waDr2Sigma : Int := 16384

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  ΛCDM Reference Values (Q16_16, dimensionless)
-- ═══════════════════════════════════════════════════════════════════════════

/-- ΛCDM prediction: w₀ = -1.0 → -1.0 × 65536 = -65536 -/
def w0Lcdm : Int := -65536

/-- ΛCDM prediction: w_a = 0.0 -/
def waLcdm : Int := 0

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Hubble Constant (raw Int, units: km/s/Mpc × 100 for precision)
--     Stored as H₀ × 100 to preserve 0.01 precision without Float
-- ═══════════════════════════════════════════════════════════════════════════

/-- H₀ = 68.52 km/s/Mpc (DESI DR1), stored as 6852 -/
def h0Dr1 : Int := 6852

/-- H₀ = 68.26 km/s/Mpc (DESI DR2), stored as 6826 -/
def h0Dr2 : Int := 6826

/-- H₀ uncertainty (DR2), stored as 45 (i.e. ±0.45 km/s/Mpc × 100) -/
def h0Dr2Sigma : Int := 45

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  Matter Density and Fluctuation Amplitude (Q16_16, dimensionless)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Ω_m = 0.295 (DESI DR1, arXiv:2404.03002)
    Q16_16: 0.295 × 65536 = 19333 -/
def omegaMDr1 : Int := 19333

/-- Ω_m = 0.2975 (DESI DR2, arXiv:2503.14738)
    Q16_16: 0.2975 × 65536 = 19498 -/
def omegaMDr2 : Int := 19498

/-- Ω_m uncertainty (DR2), Q16_16: ±0.0086 × 65536 = 564 -/
def omegaMDr2Sigma : Int := 564

/-- σ₈ = 0.812 (DESI DR2), Q16_16: 0.812 × 65536 = 53215 -/
def sigma8Dr2 : Int := 53215

/-- σ₈ uncertainty (DR2), Q16_16: ±0.011 × 65536 = 721 -/
def sigma8Dr2Sigma : Int := 721

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  Observation Record
-- ═══════════════════════════════════════════════════════════════════════════

-- REMOVED: DESIParam was unused

/-- Packaged DESI observation set -/
structure DESIObservation where
  w0 : Int
  wa : Int
  h0 : Int
  omegaM : Int
  sigma8 : Int
  rd : Int
  w0_sigma : Int
  wa_sigma : Int
  h0_sigma : Int
  omegaM_sigma : Int
  sigma8_sigma : Int
  rD_sigma : Int
  w0Lcdm : Int
  waLcdm : Int
  deriving Repr, Inhabited

/-- DESI DR1 preferred invariant set (arXiv:2404.03002) -/
def desiDR1 : DESIObservation :=
  { w0            := w0Dr1
  , wa            := waDr1
  , h0            := h0Dr1
  , omegaM        := omegaMDr1
  , sigma8        := 53215
  , rd            := rdDr1
  , w0_sigma      := 4129
  , wa_sigma      := 19005
  , h0_sigma      := 50
  , omegaM_sigma  := 524
  , sigma8_sigma  := 852
  , rD_sigma      := 17039
  , w0Lcdm       := w0Lcdm
  , waLcdm       := waLcdm
  }

/-- DESI DR2 preferred invariant set (arXiv:2503.14738, DESI+CMB+Pantheon+) -/
def desiDR2 : DESIObservation :=
  { w0            := w0Dr2
  , wa            := waDr2
  , h0            := h0Dr2
  , omegaM        := omegaMDr2
  , sigma8        := sigma8Dr2
  , rd            := rdDr2
  , w0_sigma      := w0Dr2Sigma
  , wa_sigma      := waDr2Sigma
  , h0_sigma      := h0Dr2Sigma
  , omegaM_sigma  := omegaMDr2Sigma
  , sigma8_sigma  := sigma8Dr2Sigma
  , rD_sigma      := rdDr2Sigma
  , w0Lcdm       := w0Lcdm
  , waLcdm       := waLcdm
  }

-- ═══════════════════════════════════════════════════════════════════════════
-- §7  Key Observational Theorems
-- ═══════════════════════════════════════════════════════════════════════════

/-- DESI DR2 finds w₀ > -1 (dark energy is not a cosmological constant) -/
theorem w0AboveLcdm : w0Dr2 > w0Lcdm := by
  native_decide

/-- DESI DR2 finds w_a < 0 (dark energy was stronger in the past) -/
theorem waBelowLcdm : waDr2 < waLcdm := by
  native_decide

/-- w₀ DR2 is consistent with DR1 within 1σ -/
theorem w0Dr1Dr2Consistent : absDiff w0Dr1 w0Dr2 ≤ w0Dr2Sigma := by
  native_decide

/-- w_a DR2 is consistent with DR1 within 1σ (larger DR2 uncertainty) -/
theorem waDr1Dr2Consistent : absDiff waDr1 waDr2 ≤ waDr2Sigma := by
  native_decide

/-- Ω_m DR1 and DR2 are consistent within 1σ -/
theorem omegaMDr1Dr2Consistent : absDiff omegaMDr1 omegaMDr2 ≤ omegaMDr2Sigma := by
  native_decide

-- ═══════════════════════════════════════════════════════════════════════════
-- §8  Executable Receipts
-- ═══════════════════════════════════════════════════════════════════════════

-- Receipt: DESI DR1 w₀ = -0.827 in Q16_16
#eval! w0Dr1

-- Receipt: DESI DR2 w₀ = -0.838 in Q16_16
#eval! w0Dr2

-- Receipt: DESI DR1 w_a = -0.75 in Q16_16
#eval! waDr1

-- Receipt: DESI DR2 w_a = -0.59 in Q16_16
#eval! waDr2

-- Receipt: ΛCDM w₀ = -1.0 in Q16_16
#eval! w0Lcdm

-- Receipt: DESI DR1 H₀ = 68.52 (×100)
#eval! h0Dr1

-- Receipt: DESI DR2 H₀ = 68.26 (×100)
#eval! h0Dr2

-- Receipt: DESI DR1 Ω_m = 0.295 in Q16_16
#eval! omegaMDr1

-- Receipt: DESI DR2 Ω_m = 0.2975 in Q16_16
#eval! omegaMDr2

-- Receipt: DESI DR2 σ₈ = 0.812 in Q16_16
#eval! sigma8Dr2

end Semantics.Physics.DESIInvariant
