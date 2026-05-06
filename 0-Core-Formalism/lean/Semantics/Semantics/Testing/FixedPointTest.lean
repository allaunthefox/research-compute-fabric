/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

FixedPointTest.lean — Unit Tests for Q16.16 Fixed-Point Arithmetic
-/

import Semantics.FixedPoint
import Mathlib.Tactic

namespace Semantics.FixedPoint.Test

open Semantics.Q16_16 Q16_16

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Basic Conversion Tests
-- ═══════════════════════════════════════════════════════════════════════════

/-- 0x00010000 should be 1. -/
theorem test_ofInt_one : (ofInt 1).val.toNat = 65536 := rfl

/-- 1.0 should be 65536. -/
theorem test_ofRatio_one : (ofRatio 1 1).val.toNat = 65536 := rfl

/-- 0.5 should be 32768. -/
theorem test_ofRatio_half : (ofRatio 1 2).val.toNat = 32768 := rfl

/-- 120.0 should be 120 * 65536. -/
theorem test_ofInt_120 : (ofInt 120).val.toNat = 120 * 65536 := rfl

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Arithmetic Tests
-- ═══════════════════════════════════════════════════════════════════════════

/-- 1.0 + 1.0 = 2.0. -/
theorem test_add_one_one : (ofInt 1 + ofInt 1) = ofInt 2 := rfl

/-- 1.0 * 2.0 = 2.0. -/
theorem test_mul_one_two : (ofInt 1 * ofInt 2) = ofInt 2 := by
  unfold Mul.mul mul
  simp [UInt32.toNat, UInt64.toNat, UInt64.mul, UInt64.shiftRight]
  rfl

/-- 0.5 * 0.5 = 0.25. -/
theorem test_mul_half_half : (ofRatio 1 2 * ofRatio 1 2) = ofRatio 1 4 := by
  unfold Mul.mul mul
  simp [UInt32.toNat, UInt64.toNat, UInt64.mul, UInt64.shiftRight]
  rfl

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Saturating Arithmetic Tests
-- ═══════════════════════════════════════════════════════════════════════════

/-- maxVal + 1 should still be maxVal. -/
theorem test_add_overflow : (maxVal + ofInt 1) = maxVal := rfl

/-- minVal + (-1) should still be minVal. -/
theorem test_add_underflow : (minVal + neg (ofInt 1)) = minVal := rfl

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Signed Integer Tests
-- ═══════════════════════════════════════════════════════════════════════════

/-- toInt of 1.0 is 1. -/
theorem test_toInt_one : (ofInt 1).toInt = 1 := rfl

/-- toInt of -1.0 is -1. -/
theorem test_toInt_neg_one : (neg (ofInt 1)).toInt = -1 := rfl

/-- toInt of zero is 0. -/
theorem test_toInt_zero : zero.toInt = 0 := rfl

end Semantics.FixedPoint.Test
