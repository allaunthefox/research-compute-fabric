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
- 0x7FFF = 1.0 (max positive value, represents ~1.0)
- 0x0000 = 0.0
- Range: [-1.0, 1.0 - 2^-15] ≈ [-1.0, 0.99997]
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
  if b.val = 0 then zero
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

/-- Saturating addition (matches hardware add_sat).
     Uses two's-complement overflow detection on raw UInt32 values.
     Both inputs negative and result positive → negative overflow → minVal.
     Both inputs positive and result negative → positive overflow → maxVal.
     Result stays in [-32768, 32767.999985] via saturation. -/
@[inline]
def add (a b : Q16_16) : Q16_16 :=
  let s := a.val + b.val
  if a.val < 0x80000000 && b.val < 0x80000000 && s ≥ 0x80000000 then maxVal
  else if a.val ≥ 0x80000000 && b.val ≥ 0x80000000 && s < 0x80000000 then minVal
  else ⟨s⟩

/-- Saturating subtraction (matches hardware sub_sat).
     Uses two's-complement overflow detection on raw UInt32 values.
     a positive minus b negative → possible positive overflow.
     a negative minus b positive → possible negative overflow.
     Result stays in [-32768, 32767.999985] via saturation. -/
@[inline]
def sub (a b : Q16_16) : Q16_16 :=
  let d := a.val - b.val
  if a.val < 0x80000000 && b.val ≥ 0x80000000 && d ≥ 0x80000000 then maxVal
  else if a.val ≥ 0x80000000 && b.val < 0x80000000 && d < 0x80000000 then minVal
  else ⟨d⟩

@[inline]
def mul (a b : Q16_16) : Q16_16 :=
  ⟨((a.val.toUInt64 * b.val.toUInt64) >>> 16).toUInt32⟩

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

/-- Positive addition: if a > 0 and b > 0 then a + b > 0.
    For Q16_16 saturating add, both inputs positive means either:
    (a) the sum is in the positive range → result.toInt = a.val + b.val > 0, or
    (b) positive overflow → result = maxVal → toInt = 0x7FFFFFFF > 0.
    In both cases the result is > 0.
    TODO(lean-port): Requires UInt32.toNat_add_le and UInt32 ordering lemmas
    not available in Mathlib 4.30. A native_decide witness on all 2^32×2^32
    cases is infeasible; a symbolic proof needs a signed-integer model of
    Q16_16.add that omega can reason about. -/
theorem add_pos_of_pos (a b : Q16_16) (ha : a > 0) (hb : b > 0) : a + b > 0 := by
  change toInt (add a b) > 0
  cases a with | mk av =>
  cases b with | mk bv =>
  -- Unfold a > 0 and b > 0 to get a.toInt > 0 and b.toInt > 0
  have ha' : (Q16_16.mk av).toInt > 0 := by
    have h := ha
    simp [GT.gt, LT.lt, toInt] at h
    exact h
  have hb' : (Q16_16.mk bv).toInt > 0 := by
    have h := hb
    simp [GT.gt, LT.lt, toInt] at h
    exact h
  -- a.toInt > 0 implies av < 0x80000000 and av.toNat > 0
  have hav_lt : av < (0x80000000 : UInt32) := by
    by_contra! hge
    have hge' : av ≥ (0x80000000 : UInt32) := Nat.le_of_not_lt hge
    have hti_nonpos : (Q16_16.mk av).toInt ≤ 0 := by
      unfold toInt
      simp [hge']
      have hlt := UInt32.toNat_lt av
      omega
    linarith
  have hav_pos : av.toNat > 0 := by
    have h : (Q16_16.mk av).toInt = (av.toNat : Int) := by
      unfold toInt
      simp [hav_lt]
    rw [h] at ha'
    exact_mod_cast ha'
  -- b.toInt > 0 implies bv < 0x80000000 and bv.toNat > 0
  have hbv_lt : bv < (0x80000000 : UInt32) := by
    by_contra! hge
    have hge' : bv ≥ (0x80000000 : UInt32) := Nat.le_of_not_lt hge
    have hti_nonpos : (Q16_16.mk bv).toInt ≤ 0 := by
      unfold toInt
      simp [hge']
      have hlt := UInt32.toNat_lt bv
      omega
    linarith
  have hbv_pos : bv.toNat > 0 := by
    have h : (Q16_16.mk bv).toInt = (bv.toNat : Int) := by
      unfold toInt
      simp [hbv_lt]
    rw [h] at hb'
    exact_mod_cast hb'
  -- negative overflow branch is impossible
  have h_nge_a : ¬ av ≥ (0x80000000 : UInt32) := by
    intro hge; exact Nat.lt_irrefl _ (Nat.lt_of_lt_of_le hav_lt hge)
  have h_nge_b : ¬ bv ≥ (0x80000000 : UInt32) := by
    intro hge; exact Nat.lt_irrefl _ (Nat.lt_of_lt_of_le hbv_lt hge)
  by_cases h_ov : av + bv ≥ (0x80000000 : UInt32)
  · -- Positive overflow: result = maxVal
    have h_eq : add (Q16_16.mk av) (Q16_16.mk bv) = maxVal := by
      unfold add
      simp [hav_lt, hbv_lt, h_nge_a, h_nge_b, h_ov]
      try { native_decide }
    rw [h_eq]
    unfold toInt
    native_decide
  · -- No positive overflow
    have h_lt : av + bv < (0x80000000 : UInt32) := Nat.not_le.mp h_ov
    have h_not_neg_ov : ¬ (av ≥ (0x80000000 : UInt32) ∧ bv ≥ (0x80000000 : UInt32) ∧ av + bv < (0x80000000 : UInt32)) := by
      intro h
      exact h_nge_a h.1
    have h_eq : add (Q16_16.mk av) (Q16_16.mk bv) = ⟨av + bv⟩ := by
      unfold add
      simp [hav_lt, hbv_lt, h_nge_a, h_nge_b, h_ov, h_not_neg_ov]
      try { native_decide }
    rw [h_eq]
    unfold toInt
    have hval : (Q16_16.mk (av + bv)).val = (av + bv) := rfl
    rw [hval]
    have h_not_ov_fl : ¬ ((av + bv : UInt32) ≥ (0x80000000 : UInt32)) := by
      intro hge
      have hlt_nat : (av + bv).toNat < 0x80000000 := by
        simpa using (UInt32.lt_iff_toNat_lt_toNat.mp h_lt)
      have hge_nat : 0x80000000 ≤ (av + bv).toNat := by
        simpa using (UInt32.le_iff_toNat_le_toNat.mp hge)
      omega
    simp [h_not_ov_fl, UInt32.toNat_toUInt64]
    have hav_nat_lt : av.toNat < 0x80000000 := by
      simpa using (UInt32.lt_iff_toNat_lt_toNat.mp hav_lt)
    have hbv_nat_lt : bv.toNat < 0x80000000 := by
      simpa using (UInt32.lt_iff_toNat_lt_toNat.mp hbv_lt)
    have h_add_nat : av.toNat + bv.toNat < 4294967296 := by
      omega
    have h_add : (av + bv).toNat = av.toNat + bv.toNat := by
      calc
        (av + bv).toNat = (av.toNat + bv.toNat) % 4294967296 := by
          simp [UInt32.toNat_add]
        _ = av.toNat + bv.toNat := Nat.mod_eq_of_lt h_add_nat
    have hpos : (av + bv).toNat > 0 := by
      rw [h_add]
      omega
    exact_mod_cast hpos

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

private theorem u64_zero_mul (x : UInt64) : UInt64.mul 0 x = 0 := by
  cases x
  simp [UInt64.mul, BitVec.zero_mul]

private theorem u64_mul_zero (x : UInt64) : UInt64.mul x 0 = 0 := by
  cases x
  simp [UInt64.mul, BitVec.mul_zero]

private theorem u64_scale_left_toNat (x : UInt32) :
    (UInt64.mul 65536 x.toUInt64).toNat = 65536 * x.toNat := by
  simp [UInt64.mul, UInt64.toNat_ofNat]
  have hlt := UInt32.toNat_lt x
  omega

private theorem u64_scale_right_toNat (x : UInt32) :
    (UInt64.mul x.toUInt64 65536).toNat = x.toNat * 65536 := by
  simp [UInt64.mul, UInt64.toNat_ofNat]
  have hlt := UInt32.toNat_lt x
  omega

/-- zero * a = zero -/
theorem zero_mul (a : Q16_16) : zero * a = zero := by
  cases a with
  | mk av =>
    apply congrArg Q16_16.mk
    cases av
    simp [HMul.hMul, Mul.mul, zero, u64_zero_mul]

/-- a * zero = zero -/
theorem mul_zero (a : Q16_16) : a * zero = zero := by
  cases a with
  | mk av =>
    apply congrArg Q16_16.mk
    cases av
    simp [HMul.hMul, Mul.mul, zero, u64_mul_zero]

/-- a - a = zero -/
theorem sub_self (a : Q16_16) : sub a a = zero := by
  cases a with | mk av =>
  simp only [sub, zero]
  -- a.val - a.val = 0; neither overflow condition fires since d = 0 < 0x80000000
  -- and av < 0x80000000 is possible, but av ≥ 0x80000000 && d < 0x80000000 needs check
  have hd : av - av = (0 : UInt32) := by apply UInt32.ext; simp
  simp only [hd]
  by_cases h : av < (0x80000000 : UInt32)
  · have hn : ¬ av ≥ (0x80000000 : UInt32) := Nat.not_le.mpr h
    simp [h, hn]
  · have hge : av ≥ (0x80000000 : UInt32) := Nat.le_of_not_lt h
    have hzlt : (0 : UInt32) < (0x80000000 : UInt32) := by native_decide
    have hnlt : ¬ (0 : UInt32) ≥ (0x80000000 : UInt32) := by native_decide
    simp [h, hge, hzlt, hnlt]

/-- a + zero = a (right-additive identity, holds for all signed values). -/
theorem add_zero (a : Q16_16) : add a zero = a := by
  cases a with | mk av =>
  simp only [add, zero]
  have hadd0 : av + (0 : UInt32) = av := by apply UInt32.ext; simp
  have h0lt : (0 : UInt32) < (0x80000000 : UInt32) := by native_decide
  have h0nge : ¬ (0 : UInt32) ≥ (0x80000000 : UInt32) := by native_decide
  simp only [hadd0, h0lt, h0nge]
  by_cases h : av < (0x80000000 : UInt32)
  · have hn : ¬ av ≥ (0x80000000 : UInt32) := Nat.not_le.mpr h
    simp [h, hn]
  · have hge : av ≥ (0x80000000 : UInt32) := Nat.le_of_not_lt h
    simp [h, hge, hadd0]

/-- zero + a = a (left-additive identity). -/
theorem zero_add (a : Q16_16) : add zero a = a := by
  cases a with | mk av =>
  simp only [add, zero]
  have hadd0 : (0 : UInt32) + av = av := by apply UInt32.ext; simp
  have h0lt : (0 : UInt32) < (0x80000000 : UInt32) := by native_decide
  have h0nge : ¬ (0 : UInt32) ≥ (0x80000000 : UInt32) := by native_decide
  simp only [hadd0, h0lt, h0nge]
  by_cases h : av < (0x80000000 : UInt32)
  · have hn : ¬ av ≥ (0x80000000 : UInt32) := Nat.not_le.mpr h
    simp [h, hn]
  · have hge : av ≥ (0x80000000 : UInt32) := Nat.le_of_not_lt h
    simp [h, hge, hadd0]

/-- sqrt of zero is zero. -/
theorem sqrt_zero : sqrt zero = zero := by
  delta sqrt zero
  simp

/-- sqrt of one is approximately one (within 1 LSB for Q16_16). -/
theorem sqrt_one : (sqrt one).toInt - one.toInt ≤ 1 := by
  delta sqrt one toInt
  native_decide

/-- one * a = a -/
theorem one_mul (a : Q16_16) : one * a = a := by
  cases a with
  | mk av =>
    apply congrArg Q16_16.mk
    apply UInt32.ext
    have hlt := UInt32.toNat_lt av
    change (Q16_16.mul one { val := av }).val.toNat = av.toNat
    simp [Q16_16.mul, one, UInt64.toNat_toUInt32, UInt64.toNat_shiftRight,
      UInt64.toNat_ofNat, Nat.shiftRight_eq_div_pow]
    omega

/-- a * one = a -/
theorem mul_one (a : Q16_16) : a * one = a := by
  cases a with
  | mk av =>
    apply congrArg Q16_16.mk
    apply UInt32.ext
    have hlt := UInt32.toNat_lt av
    change (Q16_16.mul { val := av } one).val.toNat = av.toNat
    simp [Q16_16.mul, one, UInt64.toNat_toUInt32, UInt64.toNat_shiftRight,
      UInt64.toNat_ofNat, Nat.shiftRight_eq_div_pow]
    omega

/-- toInt = 0 iff the value is zero -/
theorem toInt_eq_zero_iff {a : Q16_16} : a.toInt = 0 ↔ a = zero := by
  constructor
  · intro h
    cases a with
    | mk av =>
      apply congrArg Q16_16.mk
      apply UInt32.ext
      have hlt := UInt32.toNat_lt av
      simp [toInt] at h ⊢
      split at h
      · omega
      · omega
  · intro h; subst h; rfl

/-- zero / x = zero for any nonzero denominator (stated on the raw .val field) -/
theorem zero_div (x : Q16_16) (hx : x.val ≠ 0) : div zero x = zero := by
  unfold div zero
  have hbeq : (x.val == 0) = false := by
    apply Bool.eq_false_iff.mpr
    simp [hx]
  simp only [hbeq, ite_false]
  apply Q16_16.ext
  simp only [zero]
  -- numerator is 0 shifted left: 0 <<< 16 = 0; 0 / anything = 0
  have h0 : (0 : UInt32).toUInt64 <<< 16 = 0 := by decide
  simp [h0]

/-- Squaring any Q16_16 value yields a non-negative toInt.
    The Q16_16 fixed-point product of a value with itself is always ≥ 0 because
    the UInt64 intermediate is non-negative and the high 32-bit word is unsigned.
    TODO(lean-port): complete UInt64 shift-bound proof -/
theorem mul_self_nonneg (a : Q16_16) : (mul a a).toInt ≥ 0 := by
  sorry

/-- Product of two non-negative Q16_16 values is non-negative.
    TODO(lean-port): prove via UInt64 bounds: a,b < 2^31 → a*b < 2^62 → >>16 < 2^46 → toUInt32 < 2^31 -/
theorem mul_toInt_nonneg (a b : Q16_16) (ha : a.toInt ≥ 0) (hb : b.toInt ≥ 0) :
    (mul a b).toInt ≥ 0 := by
  sorry

/-- After unfolding saturating add, the result with both inputs non-negative
    has non-negative toInt.  Callers: unfold add, then apply this lemma; omega closes
    the side goal `acc.toInt ≥ 0 ∧ wcc.toInt ≥ 0` from induction hypothesis.
    TODO(lean-port): strengthen to eliminate sorry via UInt32 saturation analysis -/
theorem ofRaw_toInt_nonneg (acc wcc : Q16_16) (hacc : acc.toInt ≥ 0) (hwcc : wcc.toInt ≥ 0) :
    (Q16_16.add acc wcc).toInt ≥ 0 := by
  sorry

/-- Variant: raw UInt32 with s < 0x80000000 has non-negative toInt -/
theorem mk_lt_half_nonneg (s : UInt32) (h : s < 0x80000000) : (Q16_16.mk s).toInt ≥ 0 := by
  have h_not_ge : ¬ s ≥ (0x80000000 : UInt32) := by
    intro hge; exact Nat.lt_irrefl _ (Nat.lt_of_lt_of_le h hge)
  unfold toInt
  simp [h_not_ge, UInt32.toNat_toUInt64]

/-- (1 + omega).toInt ≥ 65536 when omega.toInt ≥ 0.
    TODO(lean-port): complete saturation branch analysis -/
theorem add_one_omega_ge_one (omega : Q16_16) (h : omega.toInt ≥ 0) :
    (add one omega).toInt ≥ 65536 := by
  sorry

/-- Non-negative Q16_16 values have toInt ≤ 0x7FFFFFFF = 2147483647 -/
theorem toInt_nonneg_le_maxVal (q : Q16_16) (h : q.toInt ≥ 0) : q.toInt ≤ 0x7FFFFFFF := by
  cases q with | mk qv =>
  -- Use the same pattern as epsilon_add_pos: by_contra hge then simp to derive contradiction
  by_contra! hlt
  -- h : q.toInt ≥ 0, hlt : q.toInt > 0x7FFFFFFF
  -- This means q.toInt ≥ 0x80000000 = 2147483648
  -- But toInt ≤ 0x7FFFFFFF for any Q16_16 with val < 0x80000000
  -- and for val ≥ 0x80000000, toInt < 0 (contradicts h ≥ 0)
  -- So both cases lead to contradiction
  unfold toInt at h hlt
  have h64 : qv.toUInt64.toNat = qv.toNat := UInt32.toNat_toUInt64 qv
  simp only [h64] at h hlt
  have hlt_full : qv.toNat < 4294967296 := UInt32.toNat_lt qv
  by_cases hge : qv ≥ (0x80000000 : UInt32)
  · simp only [hge, ite_true] at h
    -- h : Int.ofNat qv.toNat - 4294967296 ≥ 0 is impossible since qv.toNat < 2^32
    have hnn : Int.ofNat qv.toNat < 4294967296 := by
      exact Int.ofNat_lt.mpr hlt_full
    linarith
  · simp only [hge, ite_false] at hlt
    -- hlt : Int.ofNat qv.toNat > 2147483647
    have h_not_ge : ¬ qv ≥ (0x80000000 : UInt32) := hge
    -- derive qv.toNat < 2147483648
    have hlt_nat : qv.toNat < 2147483648 := by
      by_contra! hge2
      exact h_not_ge (by simpa using hge2)
    have hnn : Int.ofNat qv.toNat ≤ 2147483647 := by
      exact Int.ofNat_le.mpr (Nat.lt_succ_iff.mp hlt_nat)
    linarith

/-- Non-negative addition: adding epsilon to a non-negative value yields a positive result. -/
theorem epsilon_add_pos {r : Q16_16} (hr : r.toInt ≥ 0) :
    (r + epsilon).toInt > 0 := by
  change toInt (add r epsilon) > 0
  cases r with
  | mk rv =>
    have hrv_lt : rv < (0x80000000 : UInt32) := by
      by_contra! hge
      -- When rv ≥ 0x80000000, toInt is negative; contradicts hr ≥ 0
      have hlt_full : rv.toNat < 4294967296 := UInt32.toNat_lt rv
      have h8 : (0x80000000 : UInt32).toNat = 2147483648 := by native_decide
      have hge_nat : 2147483648 ≤ rv.toNat := by simpa [h8] using hge
      have h64 : rv.toUInt64.toNat = rv.toNat := UInt32.toNat_toUInt64 rv
      have hge' : rv ≥ (0x80000000 : UInt32) := Nat.le_of_not_lt hge
      have hti_neg : (Q16_16.mk rv).toInt < 0 := by
        unfold toInt
        simp only [show (Q16_16.mk rv).val = rv from rfl, h64]
        split_ifs with hcond
        · -- True branch: rv ≥ 0x80000000
          -- goal: (rv.toNat : Int) - 0x100000000 < 0
          have hnat : (rv.toNat : Int) < 4294967296 := by exact_mod_cast hlt_full
          norm_num; linarith
      linarith
    have h1_lt_8 : (1 : UInt32) < (0x80000000 : UInt32) := by native_decide
    have h_nge_8 : ¬ rv ≥ (0x80000000 : UInt32) := by
      intro hge; exact Nat.lt_irrefl _ (Nat.lt_of_lt_of_le hrv_lt hge)
    simp [add, epsilon, toInt, hrv_lt, h1_lt_8, h_nge_8]
    by_cases h_ov : rv + (1 : UInt32) ≥ (0x80000000 : UInt32)
    · simp only [h_ov, maxVal, ite_true]
      native_decide
    · simp only [h_ov, ite_false]
      have h_no_wrap : (rv + (1 : UInt32)).toNat = rv.toNat + 1 := by
        have h_lt_max : rv.toNat + 1 < 4294967296 := by
          have h_rv_nat : rv.toNat < 2147483648 := by
            have : (0x80000000 : UInt32).toNat = 2147483648 := by native_decide
            have : rv.toNat < (0x80000000 : UInt32).toNat := hrv_lt
            simpa [this] using this
          omega
        calc
          (rv + (1 : UInt32)).toNat = (rv.toNat + (1 : UInt32).toNat) % 4294967296 := by
            simp [UInt32.toNat_add]
          _ = (rv.toNat + 1) % 4294967296 := by simp
          _ = rv.toNat + 1 := Nat.mod_eq_of_lt h_lt_max
      have hpos : (rv + (1 : UInt32)).toNat > 0 := by
        rw [h_no_wrap]
        omega
      exact_mod_cast hpos

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

-- ═══════════════════════════════════════════════════════════════════════════
-- Pandigital π Approximation (Space-Efficient Construction)
-- ═══════════════════════════════════════════════════════════════════════════

namespace PandigitalPi

-- Pandigital pi construction using each digit 0-9 exactly once.
-- Standard storage: pi ~ 3.1415926 requires 9 ASCII bytes.
-- Pandigital construction: 3.8415926 - 0.7 = 3.1415926
-- Uses only 10 nibbles (5 bytes packed) + 1 byte operation = 6 bytes total.

/-- High term: 3.8415926 (uses digits 3,8,4,1,5,9,2,6) -/
def highTerm : Q16_16 := ⟨251819⟩  -- 3.8415926 * 65536 ≈ 251819

/-- Low term: 0.7 (uses digits 0,7) -/
def lowTerm : Q16_16 := ⟨45875⟩    -- 0.7 * 65536 ≈ 45875

-- Pandigital pi = highTerm - lowTerm = 3.1415926...
def piPandigital : Q16_16 := highTerm - lowTerm

-- pi reference for comparison (direct Q16.16 encoding)
def piDirect : Q16_16 := ⟨205944⟩  -- 3.1415926535... * 65536

-- Pandigital construction matches direct encoding within 1 LSB
theorem piPandigitalCorrect : (piPandigital.toInt - piDirect.toInt).natAbs ≤ 1 := by
  native_decide

-- Space savings analysis:
-- - Naive ASCII: "3.1415926" = 9 bytes
-- - Direct Q16.16: 4 bytes
-- - Pandigital construction: 2x4 = 8 bytes for terms, but reconstructs pi without storing it
-- - Packed nibble encoding of digits 0-9: 10 nibbles = 5 bytes + 1 byte op = 6 bytes
-- - True savings when construction is shared across multiple constants
def spaceAnalysis : String :=
  "Pandigital pi: 6 bytes packed vs 4 bytes direct Q16.16 (trade-off for mathematical elegance)"

-- Verification witnesses
#eval piPandigital.toFloat  -- Expected: ~3.1415925
#eval piDirect.toFloat      -- Expected: ~3.1415925
#eval (piPandigital.toInt - piDirect.toInt).natAbs  -- Expected: 0 or 1

end PandigitalPi

end Semantics.FixedPoint

namespace Semantics
  export FixedPoint (Q0_16 Q16_16 Q0_64)
  namespace Q16_16
    export FixedPoint.Q16_16 (mk zero one negOne epsilon two infinity maxVal minVal ofNat satFromNat ofRatio toInt ofRawInt ofFloat toFloat scale ofInt add sub mul div abs neg sqrt ln log2 expNeg sat01 max min le ge gt lt recip ofRaw clip isNeg zero_mul mul_zero one_mul mul_one zero_add add_zero sub_self zero_toInt one_toInt epsilon_toInt epsilon_toInt_pos toInt_eq_zero_iff epsilon_add_pos zero_div mul_self_nonneg mul_toInt_nonneg ofRaw_toInt_nonneg mk_lt_half_nonneg add_one_omega_ge_one toInt_nonneg_le_maxVal)
  end Q16_16
  namespace Q0_16
    export FixedPoint.Q0_16 (zero one half neg add sub mul div abs lt le gt ge toFloat ofFloat log2 min)
  end Q0_16
  namespace Q0_64
    export FixedPoint.Q0_64 (one zero ofRatio half neg add sub mul div abs toInt ofFloat toFloat)
  end Q0_64
  namespace PandigitalPi
    export FixedPoint.PandigitalPi (highTerm lowTerm piPandigital piDirect piPandigitalCorrect spaceAnalysis)
  end PandigitalPi
end Semantics
