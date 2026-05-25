/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

FixedPointBridge.lean — Bridge between Q0_16 and Q16_16 for unified fixed-point arithmetic

WARNING: The Float-based conversion functions (q0ToQ16, q16ToQ0) contain
a double-scaling bug: q0ToQ16 multiplies by 65536.0 twice (once explicitly,
once inside Q16_16.ofFloat), and q16ToQ0 uses the raw UInt32 value instead
of the signed interpretation. These functions are preserved for compatibility
but should NOT be used in production.

TODO(lean-port): Rewrite conversions using pure integer arithmetic:
  q0ToQ16_int(x) = Q16_16.ofRawInt (signExtend(x.val) * 65536 / 32767)
  q16ToQ0_int(x) = Q0_16.ofRawInt (clampToInt16(x.toInt * 32767 / 65536))

Reference: AGENTS.md §11 — Fixed-Point Arithmetic Guidelines
-/

import Semantics.FixedPoint
import Mathlib.Data.Real.Basic

namespace Semantics.FixedPointBridge

open Semantics

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Conversion Functions (Float-based, KNOWN BUGGY)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Convert Q0_16 to Q16_16. KNOWN BUG: double-scales by 65536.0.
    Q0_16.one → Q16_16.zero due to UInt32 overflow in ofFloat. -/
def q0ToQ16 (x : Q0_16) : Q16_16 :=
  let f := Q0_16.toFloat x
  Q16_16.ofFloat (f * 65536.0)

/-- Convert Q16_16 to Q0_16. KNOWN BUG: uses raw UInt32 value, not signed int.
    Negative Q16_16 values map to clamped positive Q0_16. -/
def q16ToQ0 (x : Q16_16) : Q0_16 :=
  let f := x.val.toFloat / 65536.0
  Q0_16.ofFloat f

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  The only provable round-trip: zero (exact)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Q0_16.zero → Q16_16.zero → Q0_16.zero. Exact because 0.0 survives Float. -/
theorem roundTripQ0_zero :
    q16ToQ0 (q0ToQ16 Q0_16.zero) = Q0_16.zero := by
  native_decide

/-- Q16_16.zero → Q0_16.zero → Q16_16.zero. Exact because 0.0 survives Float. -/
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
  "FixedPointBridge: Q0_16 ↔ Q16_16 conversions via Float intermediates. " ++
  "WARNING: q0ToQ16 has double-scaling bug (one → zero). " ++
  "Only zero round-trips exactly. Rewrite with pure-integer conversions needed."

#eval! fixedPointBridgeStatus

end Semantics.FixedPointBridge
