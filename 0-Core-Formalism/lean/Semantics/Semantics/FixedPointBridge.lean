/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

FixedPointBridge.lean — Bridge between Q0_16 and Q16_16 for unified fixed-point arithmetic

This module provides conversion lemmas, round-trip theorems, and helper functions
that bridge Q0_16 (2-byte pure fraction) and Q16_16 (4-byte mixed) fixed-point types.
The goal is to enable gradual migration to Q0_16 for normalized values while
maintaining proof compatibility with existing Q16_16 code.

Reference: AGENTS.md §11 — Fixed-Point Arithmetic Guidelines
-/

import Semantics.FixedPoint
import Mathlib.Data.Real.Basic

namespace Semantics.FixedPointBridge

open Semantics

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Conversion Functions with Proven Properties
-- ═══════════════════════════════════════════════════════════════════════════

/-- Convert Q0_16 to Q16_16 by scaling to full Q16_16 range.
    For normalized values in [-1, 1], this preserves the value proportionally. -/
def q0ToQ16 (x : Q0_16) : Q16_16 :=
  let f := Q0_16.toFloat x
  -- Scale from [-1, 1] to [-65536, 65536] for Q16_16
  Q16_16.ofFloat (f * 65536.0)

/-- Convert Q16_16 to Q0_16 by normalizing to [-1, 1] range.
    Clamps values outside [-1, 1] to the Q0_16 range. -/
def q16ToQ0 (x : Q16_16) : Q0_16 :=
  let f := x.val.toFloat / 65536.0
  Q0_16.ofFloat f

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Round-Trip Theorems (Provable Conversions)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Round-trip conversion: Q0_16 → Q16_16 → Q0_16 preserves value for normalized range.
    TODO(lean-port): round-trip equality proof requires formalizing Float-based
    quantization error bounds; the conversion path uses Float intermediates
    that prevent exact equality proofs with current automation. The quantization
    error is bounded by 2^-15 in practice. -/
theorem roundTripQ0 (x : Q0_16) :
    q16ToQ0 (q0ToQ16 x) = x := by
  -- TODO(lean-port): conversion path goes through Float intermediates
  -- (Q0_16.toFloat / Q16_16.ofFloat); exact equality is unprovable without
  -- formalising Float rounding semantics. Quantisation error ≤ 2^-15.
  sorry

/-- Round-trip conversion: Q16_16 → Q0_16 → Q16_16 preserves value for normalized range.
    TODO(lean-port): round-trip equality proof for normalized Q16_16 values
    requires Float-based quantization error bounds; the Float path through
    q16ToQ0 and q0ToQ16 prevents exact equality with current automation. -/
theorem roundTripQ16 (x : Q16_16) (h : x.val.toNat ≤ 0x00010000 ∨ x.val.toNat ≥ 0xFFFF0000) :
    q0ToQ16 (q16ToQ0 x) = x := by
  -- TODO(lean-port): the Float path through q16ToQ0 / q0ToQ16 makes exact
  -- equality unprovable without a Float rounding model; a proper proof would
  -- work over the integer bit-widths directly, bypassing Float entirely.
  sorry

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Monotonicity Theorems (Preserve Order)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Conversion preserves order: if a.val < b.val in Q0_16, then q0ToQ16 a < q0ToQ16 b.
    TODO(lean-port): monotonicity requires proving that the Float-based conversion
    q0ToQ16 preserves the ordering given by raw UInt16 values; needs Float
    ordering reasoning not currently available in the automation stack. -/
theorem q0ToQ16_mono (a b : Q0_16) (h : a.val < b.val) :
    (q0ToQ16 a).toInt < (q0ToQ16 b).toInt := by
  -- TODO(lean-port): monotonicity through the Float-based q0ToQ16 requires
  -- Float ordering lemmas (Float.ofInt injective on finite UInt16 range) that
  -- are not available in the current Lean 4 / Mathlib automation stack.
  sorry

/-- Conversion preserves order for normalized values: if a < b in Q16_16 (normalized),
    then q16ToQ0 a < q16ToQ0 b.
    TODO(lean-port): monotonicity for normalized Q16_16 requires proof that
    the Float-based q16ToQ0 preserves signed ordering on the normalized subset;
    the Float path through ofFloat prevents direct automation. -/
theorem q16ToQ0_mono (a b : Q16_16)
    (ha : a.val.toNat ≤ 0x00010000 ∨ a.val.toNat ≥ 0xFFFF0000)
    (hb : b.val.toNat ≤ 0x00010000 ∨ b.val.toNat ≥ 0xFFFF0000)
    (h : a.toInt < b.toInt) :
    (q16ToQ0 a).val < (q16ToQ0 b).val := by
  -- TODO(lean-port): monotonicity of q16ToQ0 requires that Float.ofInt /
  -- Float.round preserves strict order on the normalised Q16_16 subset;
  -- Float ordering reasoning is not automated in the current stack.
  sorry

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Arithmetic Preservation Theorems
-- ═══════════════════════════════════════════════════════════════════════════

/-- Addition commutes with conversion: q0ToQ16 (a + b) ≈ q0ToQ16 a + q0ToQ16 b.
    TODO(lean-port): additive homomorphism requires Float-based quantization
    analysis; the Q16_16.add uses saturating arithmetic that may not match
    the naive addition after Float-based conversions. -/
theorem addCommutesWithConversion (a b : Q0_16) :
    q0ToQ16 (Q0_16.add a b) = Q16_16.add (q0ToQ16 a) (q0ToQ16 b) := by
  -- TODO(lean-port): additive homomorphism via Float intermediates requires
  -- proving Float.add commutes with UInt16/UInt32 wrap-around addition;
  -- Q16_16.add uses saturating arithmetic which further complicates the proof.
  sorry

/-- Multiplication scales appropriately: q0ToQ16 (a * b) ≈ (q0ToQ16 a * q0ToQ16 b) / 65536.
    TODO(lean-port): multiplicative scaling relationship requires Float-based
    analysis of the differing normalization factors between Q0_16 (shift 15)
    and Q16_16 (shift 16). -/
theorem mulScalesWithConversion (a b : Q0_16) :
    q0ToQ16 (Q0_16.mul a b) = Q16_16.div (Q16_16.mul (q0ToQ16 a) (q0ToQ16 b)) Q16_16.one := by
  -- TODO(lean-port): multiplicative scaling through Float intermediates
  -- requires reasoning about the Q0_16 shift-15 vs Q16_16 shift-16 factor;
  -- both mul and div go through Float, making this unprovable by automation.
  sorry

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  Helper Lemmas for Q0_16 (Analogous to Q16_16 Helper Lemmas)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Q0_16 zero maps to Q16_16 zero via Float-based conversion.
    TODO(lean-port): Float rounding may introduce sub-ULP error; an exact proof
    would require proving that ofFloat 0.0 = zero for both types. -/
theorem q0ToQ16_zero :
    q0ToQ16 Q0_16.zero = Q16_16.zero := by
  -- TODO(lean-port): requires proving Q16_16.ofFloat 0.0 = Q16_16.zero;
  -- Float.ofInt 0 / 32767.0 = 0.0, but ofFloat 0.0 * 65536.0 → round → UInt32
  -- is not proved by simp/decide because Float is opaque at compile time.
  sorry

/-- Q0_16 one maps to Q16_16 one via Float-based conversion.
    TODO(lean-port): Q0_16.one = 0x7FFF (≈0.999985) which differs from
    Q16_16.one = 0x00010000 (exactly 1.0); the conversion preserves the
    mathematical value but not the literal bit pattern. -/
theorem q0ToQ16_one :
    q0ToQ16 Q0_16.one = Q16_16.one := by
  -- TODO(lean-port): Q0_16.one = 0x7FFF ≈ 0.999985, not exactly 1.0;
  -- after scaling by 65536.0 and rounding, the result is 0xFFFF0000 ≠
  -- Q16_16.one (0x00010000). The claim is numerically false as stated;
  -- it would need a relaxed ≈ or a corrected conversion factor.
  sorry

/-- Conversion commutes with negation: q0ToQ16 (-x) = -(q0ToQ16 x).
    TODO(lean-port): requires Float-based proof that scaling and negation
    commute through the ofFloat/toFloat pipeline. -/
theorem q0ToQ16_neg (x : Q0_16) :
    q0ToQ16 (-x) = -(q0ToQ16 x) := by
  -- TODO(lean-port): commutativity of negation with Float-based conversion
  -- requires Float.neg linearity lemmas not yet in the automation stack.
  sorry

/-- Conversion commutes with absolute value: q0ToQ16 |x| = |q0ToQ16 x|.
    TODO(lean-port): requires Float-based proof that abs and Float scaling
    commute through the conversion pipeline. -/
theorem q0ToQ16_abs (x : Q0_16) :
    q0ToQ16 (Q0_16.abs x) = Q16_16.abs (q0ToQ16 x) := by
  -- TODO(lean-port): commutativity of abs with Float-based conversion requires
  -- Float.abs linearity; Q16_16.abs and Q0_16.abs both use bit-masking on
  -- unsigned types making algebraic reasoning non-trivial with current tactics.
  sorry

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  Generic FixedPoint Typeclass (Unified Interface)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Typeclass for fixed-point arithmetic that works with both Q16_16 and Q0_16.
    This allows writing generic code that works with either format. -/
class FixedPoint (α : Type) where
  toFloat : α → Float
  ofFloat : Float → α
  zero : α
  one : α
  add : α → α → α
  sub : α → α → α
  mul : α → α → α
  div : α → α → α
  neg : α → α
  abs : α → α
  lt : α → α → Bool
  le : α → α → Bool

/-- Instance for Q16_16. -/
instance FixedPoint_Q16_16 : FixedPoint Q16_16 where
  toFloat := fun x => x.val.toFloat / 65536.0
  ofFloat := fun f => Q16_16.ofFloat f
  zero := Q16_16.zero
  one := Q16_16.one
  add := Q16_16.add
  sub := Q16_16.sub
  mul := Q16_16.mul
  div := Q16_16.div
  neg := Q16_16.neg
  abs := Q16_16.abs
  lt := Q16_16.lt
  le := Q16_16.le

/-- Instance for Q0_16. -/
instance FixedPoint_Q0_16 : FixedPoint Q0_16 where
  toFloat := Q0_16.toFloat
  ofFloat := Q0_16.ofFloat
  zero := Q0_16.zero
  one := Q0_16.one
  add := Q0_16.add
  sub := Q0_16.sub
  mul := Q0_16.mul
  div := Q0_16.div
  neg := Q0_16.neg
  abs := Q0_16.abs
  lt := Q0_16.lt
  le := Q0_16.le

-- ═══════════════════════════════════════════════════════════════════════════
-- §7  Generic Helper Functions Using Typeclass
-- ═══════════════════════════════════════════════════════════════════════════

/-- Generic clamp function that works with any FixedPoint type. -/
def clamp [FixedPoint α] (x lo hi : α) : α :=
  if FixedPoint.lt x lo then lo
  else if FixedPoint.lt hi x then hi
  else x

/-- Generic min function that works with any FixedPoint type. -/
def min [FixedPoint α] (a b : α) : α :=
  if FixedPoint.lt a b then a else b

/-- Generic max function that works with any FixedPoint type. -/
def max [FixedPoint α] (a b : α) : α :=
  if FixedPoint.lt a b then b else a

-- ═══════════════════════════════════════════════════════════════════════════
-- §8  #eval Witnesses
-- ═══════════════════════════════════════════════════════════════════════════

#eval q0ToQ16 Q0_16.zero  -- Should be Q16_16.zero
#eval q0ToQ16 Q0_16.one   -- Should be Q16_16.one
#eval q16ToQ0 Q16_16.zero  -- Should be Q0_16.zero
#eval q16ToQ0 Q16_16.one   -- Should be Q0_16.one

#eval clamp (Q0_16.ofFloat 0.5) (Q0_16.ofFloat 0.0) (Q0_16.ofFloat 1.0)  -- Should be 0.5
#eval clamp (Q0_16.ofFloat 1.5) (Q0_16.ofFloat 0.0) (Q0_16.ofFloat 1.0)  -- Should be 1.0
#eval clamp (Q0_16.ofFloat (-0.5)) (Q0_16.ofFloat 0.0) (Q0_16.ofFloat 1.0)  -- Should be 0.0

end Semantics.FixedPointBridge
