/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

FixedPointBridge.lean — Bridge between Q0_16 and Q16_16 for unified fixed-point arithmetic

NOTE: The conversion functions (q0ToQ16, q16ToQ0) use pure integer arithmetic
mapping Q0_16 (scale 32767) to/from Q16_16 (scale 65536):
  q0ToQ16(x) = Q16_16.ofRawInt (x.toInt * 65536 / 32767)
  q16ToQ0(x) = Q0_16.ofRawInt (x.toInt * 32767 / 65536)

Reference: AGENTS.md §11 — Fixed-Point Arithmetic Guidelines
-/

import Semantics.FixedPoint
import Mathlib.Data.Real.Basic

namespace Semantics.FixedPointBridge

open Semantics

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Conversion Functions (pure integer arithmetic)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Convert Q0_16 to Q16_16 using pure integer arithmetic.
    Q0_16.one (32767) → Q16_16.one (65536). -/
def q0ToQ16 (x : Q0_16) : Q16_16 :=
  Q16_16.ofRawInt (x.toInt * 65536 / 32767)

/-- Convert Q16_16 to Q0_16 using pure integer arithmetic.
    Q16_16.one (65536) → Q0_16.one (32767). -/
def q16ToQ0 (x : Q16_16) : Q0_16 :=
  FixedPoint.Q0_16.ofRawInt (x.toInt * 32767 / 65536)

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  The only provable round-trip: zero (exact)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Q0_16.zero → Q16_16.zero → Q0_16.zero (exact: 0 * k / s = 0). -/
theorem roundTripQ0_zero :
    q16ToQ0 (q0ToQ16 Q0_16.zero) = Q0_16.zero := by
  native_decide

/-- Q16_16.zero → Q0_16.zero → Q16_16.zero (exact: 0 * k / s = 0). -/
theorem roundTripQ16_zero :
    q0ToQ16 (q16ToQ0 Q16_16.zero) = Q16_16.zero := by
  native_decide

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Helper Lemmas
-- ═══════════════════════════════════════════════════════════════════════════

/-- Q0_16 zero maps to Q16_16 zero. -/
theorem q0ToQ16_zero :
    q0ToQ16 Q0_16.zero = Q16_16.zero := by
  native_decide

/-- Q16_16 zero maps to Q0_16 zero. -/
theorem q16ToQ0_zero :
    q16ToQ0 Q16_16.zero = Q0_16.zero := by
  native_decide

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Status
-- ═══════════════════════════════════════════════════════════════════════════

def fixedPointBridgeStatus : String :=
  "FixedPointBridge: Q0_16 ↔ Q16_16 conversions via pure integer arithmetic. " ++
  "q0ToQ16 = ofRawInt (x.toInt * 65536 / 32767); " ++
  "q16ToQ0 = ofRawInt (x.toInt * 32767 / 65536)."

#eval! fixedPointBridgeStatus

end Semantics.FixedPointBridge
