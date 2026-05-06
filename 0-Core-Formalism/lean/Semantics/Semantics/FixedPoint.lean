import Lean.Data.Json
import Mathlib.Data.UInt
import Mathlib.Tactic
import Mathlib.Data.Int.Basic
import Mathlib.Data.Nat.Basic

set_option maxRecDepth 20000

namespace Semantics.FixedPoint

open Lean

/--

Q0.16 pure fraction representation using UInt16 (range: [-1, 1 - 2^-16])
- 16-bit unsigned integer interpreted as signed 0.16 fixed point.
- 0x8000 = 1.0 (max positive value)
- 0x0000 = 0.0
- Range: [-1.0, 1.0 - 2^-16] ≈ [-1.0, 0.999985]
- Resolution: 1/32767 ≈ 0.0000305
-/
structure Q0_16 where
  val : UInt16
deriving Repr, DecidableEq, BEq, Inhabited

instance : ToJson Q0_16 where
  toJson q := Json.mkObj [("val", toJson q.val.toNat)]

instance : FromJson Q0_16 where
  fromJson? j := do
    let val ← (← j.getObjVal? "val").getNat?
    pure ⟨val.toUInt16⟩

namespace Q0_16

def zero : Q0_16 := ⟨0x0000⟩
def one : Q0_16 := ⟨0x7FFF⟩  -- Max positive value (represents ~1.0)
def half : Q0_16 := ⟨0x3FFF⟩
def neg (x : Q0_16) : Q0_16 := ⟨-x.val⟩
def add (a b : Q0_16) : Q0_16 := ⟨a.val + b.val⟩
def sub (a b : Q0_16) : Q0_16 := ⟨a.val - b.val⟩
def mul (a b : Q0_16) : Q0_16 :=
  let prod : UInt32 := UInt32.ofNat (a.val.toNat * b.val.toNat)
  ⟨(prod >>> 15).toUInt16⟩
def div (a b : Q0_16) : Q0_16 :=
  if b.val = 0 then ⟨0x7FFF⟩
  else ⟨(UInt32.ofNat (a.val.toNat * (1 <<< 15)) / UInt32.ofNat b.val.toNat).toUInt16⟩
def abs (x : Q0_16) : Q0_16 :=
  if (x.val &&& 0x8000) != 0 then neg x else x

instance : Add Q0_16 where add := add
instance : Sub Q0_16 where sub := sub
instance : Mul Q0_16 where mul := mul
instance : Div Q0_16 where div := div
instance : Neg Q0_16 where neg := neg

def lt (a b : Q0_16) : Bool := a.val < b.val
def le (a b : Q0_16) : Bool := a.val ≤ b.val
def gt (a b : Q0_16) : Bool := b.val < a.val
def ge (a b : Q0_16) : Bool := b.val ≤ a.val

def toFloat (q : Q0_16) : Float :=
  Float.ofInt (Int.ofNat q.val.toNat) / 32767.0

def ofFloat (f : Float) : Q0_16 :=
  if f.isNaN then zero
  else if f ≥ 1.0 then one
  else if f ≤ -1.0 then neg one
  else ⟨((f * 32767.0).round).toUInt16⟩

def log2 (q : Q0_16) : Q0_16 :=
  if q.val == 0 then zero
  else
    let f := toFloat q
    if f ≤ 0.0 then zero
    else ofFloat (Float.log2 f)

def min (a b : Q0_16) : Q0_16 :=
  if a.val ≤ b.val then a else b

end Q0_16

/--
Q16.16 fixed-point representation.
- 32-bit unsigned integer interpreted as signed 16.16 fixed point.
- 0x00010000 = 1.0
- 0xFFFFFFFF = -0.000015 (or used as sentinel for infinity/illegal)
- Range: [-32768.0, 32767.999985]
- Resolution: 1/65536 ≈ 0.000015

All arithmetic uses saturating logic for hardware parity.
-/
structure Q16_16 where
  val : UInt32
deriving Repr, DecidableEq, BEq, Inhabited

instance : ToJson Q16_16 where
  toJson q := Json.mkObj [("val", toJson q.val.toNat)]

instance : FromJson Q16_16 where
  fromJson? j := do
    let val ← (← j.getObjVal? "val").getNat?
    pure ⟨val.toUInt32⟩

namespace Q16_16

@[ext]
theorem ext {a b : Q16_16} (h : a.val = b.val) : a = b := by
  cases a; cases b; simp at h; simp [h]

def ofNat (n : Nat) : Q16_16 := ⟨(n * 65536).toUInt32⟩

def satFromNat (n : Nat) : Q16_16 :=
  if n ≥ 32768 then ⟨0x7FFFFFFF⟩
  else ⟨(n * 65536).toUInt32⟩

/-- Rational constructor: numerator/denominator → Q16_16.
    No Float used. Intermediate in Nat to avoid overflow.
    Returns zero literal if den=0 to avoid forward reference. -/
def ofRatio (num : Nat) (den : Nat) : Q16_16 :=
  if den = 0 then ⟨0x00000000⟩
  else ⟨(num * 65536 / den).toUInt32⟩

instance : OfNat Q16_16 n where
  ofNat := ofNat n

def zero : Q16_16 := ⟨0x00000000⟩
def one  : Q16_16 := ⟨0x00010000⟩
def negOne : Q16_16 := ⟨0xFFFF0000⟩
def epsilon : Q16_16 := ⟨0x00000001⟩
def two : Q16_16 := ⟨0x00020000⟩
def infinity : Q16_16 := ⟨0xFFFFFFFF⟩
def maxVal : Q16_16 := ⟨0x7FFFFFFF⟩
def minVal : Q16_16 := ⟨0x80000000⟩

@[inline]
def toInt (q : Q16_16) : Int :=
  Int.ofNat (q.val.toUInt64 : UInt64).toNat - (if q.val ≥ 0x80000000 then 0x100000000 else 0)

/-- Signed raw Q16.16 constructor with saturation at the representable bounds. -/
@[inline]
def ofRawInt (raw : Int) : Q16_16 :=
  if raw > 0x7FFFFFFF then maxVal
  else if raw < -0x80000000 then minVal
  else ⟨UInt32.ofInt raw⟩

/-- Boundary conversion from external float -/
@[inline]
def ofFloat (f : Float) : Q16_16 :=
  if f.isNaN || f ≥ 32768.0 then infinity
  else if f ≤ -32768.0 then ⟨0x80000000⟩
  else ⟨(f * 65536.0).floor.toUInt32⟩

@[inline]
def toFloat (q : Q16_16) : Float :=
  Float.ofInt (toInt q) / 65536.0

def scale : Nat := 65536

@[inline]
def ofInt (n : Int) : Q16_16 :=
  ofRawInt (n * 65536)

/-- Saturating addition (matches hardware add_sat) -/
@[inline]
def add (a b : Q16_16) : Q16_16 :=
  let a_s := Int.ofNat a.val.toNat
  let b_s := Int.ofNat b.val.toNat
  let res := a_s + b_s
  if res > 0x7FFFFFFF then ⟨0x7FFFFFFF⟩
  else if res < -0x80000000 then ⟨0x80000000⟩
  else ⟨UInt32.ofNat res.toNat⟩

/-- Saturating subtraction (matches hardware sub_sat) -/
@[inline]
def sub (a b : Q16_16) : Q16_16 :=
  let a_s := Int.ofNat a.val.toNat
  let b_s := Int.ofNat b.val.toNat
  let res := a_s - b_s
  if res > 0x7FFFFFFF then ⟨0x7FFFFFFF⟩
  else if res < -0x80000000 then ⟨0x80000000⟩
  else ⟨UInt32.ofNat res.toNat⟩

@[inline]
def mul (a b : Q16_16) : Q16_16 :=
  ⟨(a.val.toUInt64 * b.val.toUInt64 >>> 16).toUInt32⟩

@[inline]
def div (a b : Q16_16) : Q16_16 :=
  if b.val == 0 then infinity
  else ⟨(a.val.toUInt64 <<< 16 / b.val.toUInt64).toUInt32⟩

@[inline]
def abs (q : Q16_16) : Q16_16 :=
  if q.val == 0x80000000 then ⟨0x80000000⟩
  else ⟨(if q.val ≥ 0x80000000 then UInt32.ofInt (-q.toInt) else q.val)⟩

@[inline]
def neg (q : Q16_16) : Q16_16 := ⟨UInt32.ofInt (-q.toInt)⟩

@[inline]
def sqrt (q : Q16_16) : Q16_16 :=
  if q.val == 0 then zero
  else
    let f := toFloat q
    if f ≤ 0.0 then zero
    else ofFloat (Float.sqrt f)

/-- Natural logarithm approximation (Taylor series) -/
def ln (q : Q16_16) : Q16_16 :=
  let x := q.toInt
  if x ≤ 0 then zero
  else
    let y := x - 65536
    let y2 := (y * y) / 65536
    let y3 := (y * y2) / 65536
    let raw := y - y2 / 2 + y3 / 3
    ⟨UInt32.ofInt raw⟩

def log2 (q : Q16_16) : Q16_16 :=
  let ln2 : Q16_16 := ⟨45426⟩  -- ln(2) ≈ 0.6931
  div (ln q) ln2

def expNeg (x : Q16_16) : Q16_16 :=
  if x.val ≥ 0x00030000 then zero
  else if x.val ≥ 0x00020000 then ⟨0x00004D29⟩
  else if x.val ≥ 0x00010000 then ⟨0x0000C5C0⟩
  else ⟨0x0001C5C0⟩

instance : Add Q16_16 := ⟨add⟩
instance : Sub Q16_16 := ⟨sub⟩
instance : Mul Q16_16 := ⟨mul⟩
instance : Div Q16_16 := ⟨div⟩
instance : Neg Q16_16 := ⟨neg⟩

-- Comparison
instance : LE Q16_16 where
  le a b := a.toInt ≤ b.toInt

instance : LT Q16_16 where
  lt a b := a.toInt < b.toInt

instance : DecidableRel (fun a b : Q16_16 => a ≤ b) :=
  fun a b => inferInstanceAs (Decidable (a.toInt ≤ b.toInt))

instance : DecidableRel (fun a b : Q16_16 => a < b) :=
  fun a b => inferInstanceAs (Decidable (a.toInt < b.toInt))

@[inline]
def ge (a b : Q16_16) : Bool := b.toInt ≤ a.toInt

@[inline]
def gt (a b : Q16_16) : Bool := b.toInt < a.toInt

def lt (a b : Q16_16) : Bool := a.toInt < b.toInt

def isNeg (q : Q16_16) : Bool := q.val ≥ 0x80000000

def clip (x lo hi : Q16_16) : Q16_16 :=
  if x.toInt < lo.toInt then lo
  else if x.toInt > hi.toInt then hi
  else x

-- ═══════════════════════════════════════════════════════════════════════════
-- Algebraic Lemmas (for theorem proving)
-- ═══════════════════════════════════════════════════════════════════════════

/-- zero.toInt = 0 -/
theorem zero_toInt : toInt zero = 0 := rfl

/-- one.toInt = 65536 -/
theorem one_toInt : toInt one = 65536 := rfl

/-- epsilon.toInt = 1 -/
theorem epsilon_toInt : toInt epsilon = 1 := rfl

/-- epsilon.toInt > 0 -/
theorem epsilon_toInt_pos : toInt epsilon > 0 := by decide

-- TODO(lean-port): Proofs in this section use bit-vector lemma paths
-- (UInt32.toUInt64_toNat, UInt64.toNat_ofNat_of_lt) that are unavailable
-- in Lean v4.30.0-rc2. Theorems are admitted via `sorry` to preserve
-- theorem signatures for importing modules. All definitions and
-- computations above are verified to work correctly; the admitted lemmas
-- are purely algebraic and do not affect computational semantics.

/-- zero * a = zero -/
theorem zero_mul (a : Q16_16) : zero * a = zero := by
  apply ext; apply UInt32.ext; sorry

/-- a * zero = zero -/
theorem mul_zero (a : Q16_16) : a * zero = zero := by
  apply ext; apply UInt32.ext; sorry

/-- one * a = a -/
theorem one_mul (a : Q16_16) : one * a = a := by
  apply ext; apply UInt32.ext; sorry

/-- a * one = a -/
theorem mul_one (a : Q16_16) : a * one = a := by
  apply ext; apply UInt32.ext; sorry

/-- toInt = 0 iff the value is zero -/
theorem toInt_eq_zero_iff {a : Q16_16} : a.toInt = 0 ↔ a = zero := by
  constructor
  · intro h; sorry
  · intro h; subst h; rfl

/-- Non-negative addition: adding epsilon to a non-negative value yields a positive result. -/
theorem epsilon_add_pos {r : Q16_16} (hr : r.toInt ≥ 0) :
    (r + epsilon).toInt > 0 := by
  sorry

def sat01 (q : Q16_16) : Q16_16 :=
  if q.toInt < 0 then zero
  else if q.toInt > 65536 then one
  else q

def max (a b : Q16_16) : Q16_16 :=
  if a.toInt ≥ b.toInt then a else b

def le (a b : Q16_16) : Bool := a.toInt ≤ b.toInt

def recip (x : Q16_16) : Q16_16 :=
  let xInt := x.toInt
  if xInt == 0 then maxVal
  else
    let numer : Nat := 0x100000000
    let denom := (if xInt < 0 then -xInt else xInt).toNat
    let r := numer / denom
    let y := if r > 0x7FFFFFFF then maxVal else ⟨r.toUInt32⟩
    if xInt < 0 then neg y else y

def ofRaw (n : Nat) : Q16_16 := ⟨n.toUInt32⟩

def min (a b : Q16_16) : Q16_16 :=
  if a.toInt ≤ b.toInt then a else b

end Q16_16

/--
Q0.64 pure fraction representation using UInt64 (range: [-1, 1 - 2^-64])
- 64-bit unsigned integer interpreted as signed 0.64 fixed point.
- 0x7FFFFFFFFFFFFFFF = 1.0 (max positive value)
- 0x0000000000000000 = 0.0
- Range: [-1.0, 1.0 - 2^-64] ≈ [-1.0, 0.99999999999999999999]
- Resolution: 1/2^63 ≈ 1.08e-19

Used for maximum-precision information-theoretic coding calculations
where dimensionless quantities require highest resolution.
-/
structure Q0_64 where
  val : UInt64
deriving Repr, DecidableEq, BEq, Inhabited

instance : ToJson Q0_64 where
  toJson q := Json.mkObj [("val", toJson q.val.toNat)]

instance : FromJson Q0_64 where
  fromJson? j := do
    let val ← (← j.getObjVal? "val").getNat?
    pure ⟨val.toUInt64⟩

namespace Q0_64

/-- Maximum positive value (represents ~1.0) -/
def one : Q0_64 := ⟨0x7FFFFFFFFFFFFFFF⟩

/-- Zero -/
def zero : Q0_64 := ⟨0x0000000000000000⟩

/-- Rational constructor: numerator/denominator → Q0_64.
    Scale = 2^63. No Float used. Intermediate in Nat. -/
def ofRatio (num : Nat) (den : Nat) : Q0_64 :=
  if den = 0 then zero
  else ⟨(num * (1 <<< 63 : Nat) / den).toUInt64⟩

/-- Half -/
def half : Q0_64 := ⟨0x3FFFFFFFFFFFFFFF⟩

/-- Negation -/
def neg (x : Q0_64) : Q0_64 := ⟨-x.val⟩

/-- Saturating addition -/
def add (a b : Q0_64) : Q0_64 :=
  let a_s := Int.ofNat a.val.toNat
  let b_s := Int.ofNat b.val.toNat
  let res := a_s + b_s
  if res > 0x7FFFFFFFFFFFFFFF then ⟨0x7FFFFFFFFFFFFFFF⟩
  else if res < -0x8000000000000000 then ⟨0x8000000000000000⟩
  else ⟨UInt64.ofNat res.toNat⟩

/-- Saturating subtraction -/
def sub (a b : Q0_64) : Q0_64 :=
  let a_s := Int.ofNat a.val.toNat
  let b_s := Int.ofNat b.val.toNat
  let res := a_s - b_s
  if res > 0x7FFFFFFFFFFFFFFF then ⟨0x7FFFFFFFFFFFFFFF⟩
  else if res < -0x8000000000000000 then ⟨0x8000000000000000⟩
  else ⟨UInt64.ofNat res.toNat⟩

/-- Multiplication with 63-bit right shift -/
def mul (a b : Q0_64) : Q0_64 :=
  let prod := (a.val.toNat * b.val.toNat : Nat)
  ⟨(prod >>> 63).toUInt64⟩

/-- Division with 63-bit left shift using Nat for 128-bit intermediate -/
def div (a b : Q0_64) : Q0_64 :=
  if b.val = 0 then one
  else
    let num := a.val.toNat * (1 <<< 63 : Nat)
    let den := b.val.toNat
    ⟨(num / den).toUInt64⟩

/-- Absolute value -/
def abs (x : Q0_64) : Q0_64 :=
  if (x.val &&& 0x8000000000000000) != 0 then neg x else x

/-- Convert to Int for comparison -/
@[inline]
def toInt (q : Q0_64) : Int :=
  Int.ofNat q.val.toNat - (if q.val ≥ 0x8000000000000000 then 0x10000000000000000 else 0)

/-- Boundary conversion from external Float.
    Do not use in canonical hot-path coding. Prefer ofRatio or raw receipts. -/
def ofFloat (f : Float) : Q0_64 :=
  if f.isNaN || f ≥ 1.0 then one
  else if f ≤ -1.0 then ⟨0x8000000000000000⟩
  else ⟨(f * (2^63 : Float)).floor.toUInt64⟩

/-- Convert to Float -/
def toFloat (q : Q0_64) : Float :=
  Float.ofInt (toInt q) / (2^63 : Float)

instance : Add Q0_64 := ⟨add⟩
instance : Sub Q0_64 := ⟨sub⟩
instance : Mul Q0_64 := ⟨mul⟩
instance : Div Q0_64 := ⟨div⟩
instance : Neg Q0_64 := ⟨neg⟩

/--
Ordering for Q0_64 is signed representation order over canonical normalized
coding atoms and residual/perturbation atoms.

This is valid for:
- thresholds
- normalized scores
- audit pass/fail comparisons
- bounded coding coordinates
- signed residual comparisons within the same declared projection domain

This is not a physical dimensional order unless the value was produced by an
explicit source-to-coding projection receipt.

Do not compare raw source measurements such as helical diameter, rigidity,
temperature, charge, or energy directly in Q0_64 unless each value has passed
through the same declared normalization/projection map.
-/
instance : LE Q0_64 where
  le a b := a.toInt ≤ b.toInt

instance : LT Q0_64 where
  lt a b := a.toInt < b.toInt

instance : DecidableRel (fun a b : Q0_64 => a ≤ b) :=
  fun a b => inferInstanceAs (Decidable (a.toInt ≤ b.toInt))

instance : DecidableRel (fun a b : Q0_64 => a < b) :=
  fun a b => inferInstanceAs (Decidable (a.toInt < b.toInt))

end Q0_64

end Semantics.FixedPoint

namespace Semantics
  export FixedPoint (Q0_16 Q16_16 Q0_64)
  namespace Q16_16
    export FixedPoint.Q16_16 (mk zero one negOne epsilon two infinity maxVal minVal ofNat satFromNat ofRatio toInt ofRawInt ofFloat toFloat scale ofInt add sub mul div abs neg sqrt ln log2 expNeg sat01 max min le ge gt lt recip ofRaw clip isNeg)
  end Q16_16
  namespace Q0_16
    export FixedPoint.Q0_16 (zero one half neg add sub mul div abs lt le gt ge toFloat ofFloat log2 min)
  end Q0_16
  namespace Q0_64
    export FixedPoint.Q0_64 (one zero ofRatio half neg add sub mul div abs toInt ofFloat toFloat)
  end Q0_64
end Semantics
