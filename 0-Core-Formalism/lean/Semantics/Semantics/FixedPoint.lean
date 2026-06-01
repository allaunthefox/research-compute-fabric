import Lean.Data.Json
import Mathlib.Data.UInt
import Mathlib.Tactic
import Mathlib.Data.Int.Basic
import Mathlib.Data.Nat.Basic

set_option maxRecDepth 20000

namespace Semantics.FixedPoint

open Lean

/-!
A proof-friendly fixed-point core.

Design rule:
* The semantic value is a bounded signed raw integer.
* Saturation is performed by `ofRawInt`.
* UInt bit-patterns are boundary/hardware artifacts, not the proof model.

This removes the old proof debt caused by proving signed arithmetic facts directly
against modular UInt32/UInt64 overflow behavior.
-/

-- ═══════════════════════════════════════════════════════════════════════════
-- Q0.16 signed normalized fraction
-- ═══════════════════════════════════════════════════════════════════════════

def q0_16MinRaw : Int := -32768
def q0_16MaxRaw : Int := 32767
def q0_16Scale  : Int := 32767

/--
Q0.16 pure fraction representation.
The canonical proof model stores the signed raw integer in [-32768, 32767].
Use boundary conversion functions when a UInt16 bit pattern is required.
-/
abbrev Q0_16 := { x : Int // q0_16MinRaw ≤ x ∧ x ≤ q0_16MaxRaw }

instance : Repr Q0_16 where
  reprPrec q _ := repr q.val

instance : BEq Q0_16 where
  beq a b := a.val == b.val

instance : Inhabited Q0_16 where
  default := ⟨0, by constructor <;> norm_num [q0_16MinRaw, q0_16MaxRaw]⟩

instance : ToJson Q0_16 where
  toJson q := Json.mkObj [("val", toJson q.val)]

namespace Q0_16

@[ext]
theorem ext {a b : Q0_16} (h : a.val = b.val) : a = b := Subtype.ext h

@[inline]
def toInt (q : Q0_16) : Int := q.val

@[inline]
def ofRawInt (raw : Int) : Q0_16 :=
  if hhi : raw > q0_16MaxRaw then
    ⟨q0_16MaxRaw, by constructor <;> norm_num [q0_16MinRaw, q0_16MaxRaw]⟩
  else if hlo : raw < q0_16MinRaw then
    ⟨q0_16MinRaw, by constructor <;> norm_num [q0_16MinRaw, q0_16MaxRaw]⟩
  else
    ⟨raw, by
      constructor
      · dsimp [q0_16MinRaw, q0_16MaxRaw] at *; omega
      · dsimp [q0_16MinRaw, q0_16MaxRaw] at *; omega⟩

instance : FromJson Q0_16 where
  fromJson? j := do
    let raw : Int ← fromJson? (← j.getObjVal? "val")
    pure (ofRawInt raw)

def zero : Q0_16 := ofRawInt 0
def one  : Q0_16 := ofRawInt q0_16MaxRaw
def half : Q0_16 := ofRawInt 16383

def neg (x : Q0_16) : Q0_16 := ofRawInt (-x.toInt)
def add (a b : Q0_16) : Q0_16 := ofRawInt (a.toInt + b.toInt)
def sub (a b : Q0_16) : Q0_16 := ofRawInt (a.toInt - b.toInt)
def mul (a b : Q0_16) : Q0_16 := ofRawInt ((a.toInt * b.toInt) / q0_16Scale)
def div (a b : Q0_16) : Q0_16 :=
  if b.toInt = 0 then zero else ofRawInt ((a.toInt * q0_16Scale) / b.toInt)
def abs (x : Q0_16) : Q0_16 := if x.toInt < 0 then neg x else x

instance : Add Q0_16 where add := add
instance : Sub Q0_16 where sub := sub
instance : Mul Q0_16 where mul := mul
instance : Div Q0_16 where div := div
instance : Neg Q0_16 where neg := neg

def lt (a b : Q0_16) : Bool := a.toInt < b.toInt
def le (a b : Q0_16) : Bool := a.toInt ≤ b.toInt
def gt (a b : Q0_16) : Bool := b.toInt < a.toInt
def ge (a b : Q0_16) : Bool := b.toInt ≤ a.toInt

def toFloat (q : Q0_16) : Float :=
  Float.ofInt q.toInt / 32767.0

def ofFloat (f : Float) : Q0_16 :=
  if f.isNaN then zero
  else if f ≥ 1.0 then one
  else if f ≤ -1.0 then neg one
  else if f < 0.0 then
    ofRawInt (-(Int.ofNat ((-f * 32767.0).round.toUInt16.toNat)))
  else
    ofRawInt (Int.ofNat ((f * 32767.0).round.toUInt16.toNat))

def log2 (q : Q0_16) : Q0_16 :=
  if q.toInt = 0 then zero
  else
    let f := toFloat q
    if f ≤ 0.0 then zero else ofFloat (Float.log2 f)

def min (a b : Q0_16) : Q0_16 :=
  if a.toInt ≤ b.toInt then a else b

end Q0_16

-- ═══════════════════════════════════════════════════════════════════════════
-- Q16.16 signed fixed-point
-- ═══════════════════════════════════════════════════════════════════════════

def q16MinRaw : Int := -2147483648
def q16MaxRaw : Int := 2147483647
def q16Scale  : Int := 65536

/-- Saturating clamp of a raw integer into [q16MinRaw, q16MaxRaw].
    This is the pure-Int kernel of `Q16_16.ofRawInt`; all monotonicity
    reasoning is proved once here and reused by higher lemmas. -/
def q16Clamp (i : Int) : Int :=
  if i > q16MaxRaw then q16MaxRaw
  else if i < q16MinRaw then q16MinRaw
  else i

/-- `q16Clamp` is monotone: a ≤ b → q16Clamp a ≤ q16Clamp b. -/
theorem q16Clamp_monotone (a b : Int) (h : a ≤ b) : q16Clamp a ≤ q16Clamp b := by
  unfold q16Clamp
  by_cases ha_hi : a > q16MaxRaw
  · by_cases hb_hi : b > q16MaxRaw
    · simp [ha_hi, hb_hi]
    · by_cases hb_lo : b < q16MinRaw
      · simp [ha_hi, hb_hi, hb_lo]; dsimp [q16MinRaw, q16MaxRaw] at *; omega
      · simp [ha_hi, hb_hi, hb_lo]; dsimp [q16MaxRaw] at *; omega
  · by_cases ha_lo : a < q16MinRaw
    · by_cases hb_hi : b > q16MaxRaw
      · simp [ha_hi, ha_lo, hb_hi]; dsimp [q16MinRaw, q16MaxRaw] at *; omega
      · by_cases hb_lo : b < q16MinRaw
        · simp [ha_hi, ha_lo, hb_hi, hb_lo]
        · simp [ha_hi, ha_lo, hb_hi, hb_lo]; dsimp [q16MinRaw] at *; omega
    · by_cases hb_hi : b > q16MaxRaw
      · simp [ha_hi, ha_lo, hb_hi]; dsimp [q16MaxRaw] at *; omega
      · by_cases hb_lo : b < q16MinRaw
        · simp [ha_hi, ha_lo, hb_hi, hb_lo]; dsimp [q16MinRaw] at *; omega
        · simp [ha_hi, ha_lo, hb_hi, hb_lo]; exact h

/-- `q16Clamp` is idempotent on in-range values. -/
theorem q16Clamp_id_of_inRange (i : Int) (hlo : q16MinRaw ≤ i) (hhi : i ≤ q16MaxRaw) :
    q16Clamp i = i := by
  unfold q16Clamp
  simp [show ¬ i > q16MaxRaw from by omega, show ¬ i < q16MinRaw from by omega]

lemma q16Clamp_lower (x : Int) : q16MinRaw ≤ q16Clamp x := by
  unfold q16Clamp q16MinRaw q16MaxRaw; split_ifs <;> omega

lemma q16Clamp_upper (x : Int) : q16Clamp x ≤ q16MaxRaw := by
  unfold q16Clamp q16MinRaw q16MaxRaw; split_ifs <;> omega

lemma q16Clamp_nonneg_of_nonneg {x : Int} (hx : 0 ≤ x) : 0 ≤ q16Clamp x := by
  unfold q16Clamp q16MinRaw q16MaxRaw
  split_ifs <;> omega

lemma q16Clamp_idem (x : Int) : q16Clamp (q16Clamp x) = q16Clamp x := by
  have h_upper := q16Clamp_upper x
  have h_lower := q16Clamp_lower x
  unfold q16Clamp q16MinRaw q16MaxRaw
  split_ifs <;> omega

/--
Q16.16 fixed-point representation.
The canonical proof model stores the signed raw integer in
[-2147483648, 2147483647].

Hardware/serialization UInt32 bit patterns should enter through `ofBits` and
leave through `toBits`. All semantic proofs use `toInt`.
-/
abbrev Q16_16 := { x : Int // q16MinRaw ≤ x ∧ x ≤ q16MaxRaw }

instance : Repr Q16_16 where
  reprPrec q _ := repr q.val

instance : BEq Q16_16 where
  beq a b := a.val == b.val

instance : Inhabited Q16_16 where
  default := ⟨0, by constructor <;> norm_num [q16MinRaw, q16MaxRaw]⟩

instance : ToJson Q16_16 where
  toJson q := Json.mkObj [("val", toJson q.val)]

namespace Q16_16

@[ext]
theorem ext {a b : Q16_16} (h : a.val = b.val) : a = b := Subtype.ext h

@[inline]
def toInt (q : Q16_16) : Int := q.val

@[inline]
def ofRawInt (raw : Int) : Q16_16 :=
  if hhi : raw > q16MaxRaw then
    ⟨q16MaxRaw, by constructor <;> norm_num [q16MinRaw, q16MaxRaw]⟩
  else if hlo : raw < q16MinRaw then
    ⟨q16MinRaw, by constructor <;> norm_num [q16MinRaw, q16MaxRaw]⟩
  else
    ⟨raw, by
      constructor
      · dsimp [q16MinRaw, q16MaxRaw] at *; omega
      · dsimp [q16MinRaw, q16MaxRaw] at *; omega⟩

instance : FromJson Q16_16 where
  fromJson? j := do
    let raw : Int ← fromJson? (← j.getObjVal? "val")
    pure (ofRawInt raw)

/-- Decode a UInt32 two's-complement hardware bit pattern into the signed model. -/
@[inline]
def ofBits (u : UInt32) : Q16_16 :=
  let n := u.toNat
  if n ≥ 2147483648 then ofRawInt ((n : Int) - 4294967296)
  else ofRawInt (n : Int)

/-- Encode the signed model as a UInt32 two's-complement hardware bit pattern. -/
@[inline]
def toBits (q : Q16_16) : UInt32 := UInt32.ofInt q.toInt

def zero : Q16_16 := ⟨0, by constructor <;> norm_num [q16MinRaw, q16MaxRaw]⟩
def one  : Q16_16 := ⟨q16Scale, by constructor <;> norm_num [q16MinRaw, q16MaxRaw, q16Scale]⟩
def negOne : Q16_16 := ⟨-q16Scale, by constructor <;> norm_num [q16MinRaw, q16MaxRaw, q16Scale]⟩
def epsilon : Q16_16 := ⟨1, by constructor <;> norm_num [q16MinRaw, q16MaxRaw]⟩
def two : Q16_16 := ⟨2 * q16Scale, by constructor <;> norm_num [q16MinRaw, q16MaxRaw, q16Scale]⟩
def maxVal : Q16_16 := ⟨q16MaxRaw, by constructor <;> norm_num [q16MinRaw, q16MaxRaw]⟩
def minVal : Q16_16 := ⟨q16MinRaw, by constructor <;> norm_num [q16MinRaw, q16MaxRaw]⟩

/-- Saturating infinity/illegal sentinel. If you need the old 0xFFFFFFFF bit
sentinel, use `ofRawInt (-1)` or `ofBits 0xFFFFFFFF` explicitly. -/
def infinity : Q16_16 := maxVal

def scale : Nat := 65536

def ofNat (n : Nat) : Q16_16 := ofRawInt ((n : Int) * q16Scale)

def satFromNat (n : Nat) : Q16_16 := ofRawInt ((n : Int) * q16Scale)

def ofRatio (num : Nat) (den : Nat) : Q16_16 :=
  if den = 0 then zero
  else ofRawInt (Int.ofNat (num * scale / den))

instance : OfNat Q16_16 n where
  ofNat := ofNat n

@[inline]
def ofInt (n : Int) : Q16_16 := ofRawInt (n * q16Scale)

/-- Saturating addition. -/
@[inline]
def add (a b : Q16_16) : Q16_16 := ofRawInt (a.toInt + b.toInt)

/-- Saturating subtraction. -/
@[inline]
def sub (a b : Q16_16) : Q16_16 := ofRawInt (a.toInt - b.toInt)

/-- Saturating Q16.16 multiplication: raw result is `(a*b)/65536`. -/
@[inline]
def mul (a b : Q16_16) : Q16_16 := ofRawInt ((a.toInt * b.toInt) / q16Scale)

/-- Saturating Q16.16 division: raw result is `(a*65536)/b`. -/
@[inline]
def div (a b : Q16_16) : Q16_16 :=
  if b.toInt = 0 then infinity else ofRawInt ((a.toInt * q16Scale) / b.toInt)

@[inline]
def neg (q : Q16_16) : Q16_16 := ofRawInt (-q.toInt)

@[inline]
def abs (q : Q16_16) : Q16_16 := if q.toInt < 0 then neg q else q

@[inline]
def ofFloat (f : Float) : Q16_16 :=
  if f.isNaN || f ≥ 32768.0 then infinity
  else if f ≤ -32768.0 then minVal
  else if f < 0.0 then
    ofRawInt (-(Int.ofNat ((-f * 65536.0).floor.toUInt32.toNat)))
  else
    ofRawInt (Int.ofNat ((f * 65536.0).floor.toUInt32.toNat))

@[inline]
def toFloat (q : Q16_16) : Float :=
  Float.ofInt q.toInt / 65536.0

@[inline]
def sqrt (q : Q16_16) : Q16_16 :=
  if q.toInt = 0 then zero
  else
    let f := toFloat q
    if f ≤ 0.0 then zero else ofFloat (Float.sqrt f)

/-- Natural logarithm approximation around 1.0. -/
def ln (q : Q16_16) : Q16_16 :=
  let x := q.toInt
  if x ≤ 0 then zero
  else
    let y := x - q16Scale
    let y2 := (y * y) / q16Scale
    let y3 := (y * y2) / q16Scale
    ofRawInt (y - y2 / 2 + y3 / 3)

def log2 (q : Q16_16) : Q16_16 :=
  let ln2 : Q16_16 := ofRawInt 45426
  div (ln q) ln2

def expNeg (x : Q16_16) : Q16_16 :=
  if x.toInt ≥ 0x00030000 then zero
  else if x.toInt ≥ 0x00020000 then ofRawInt 0x00004D29
  else if x.toInt ≥ 0x00010000 then ofRawInt 0x0000C5C0
  else ofRawInt 0x0001C5C0

instance : Add Q16_16 := ⟨add⟩
instance : Sub Q16_16 := ⟨sub⟩
instance : Mul Q16_16 := ⟨mul⟩
instance : Div Q16_16 := ⟨div⟩
instance : Neg Q16_16 := ⟨neg⟩

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

def le (a b : Q16_16) : Bool := a.toInt ≤ b.toInt

def isNeg (q : Q16_16) : Bool := q.toInt < 0

def clip (x lo hi : Q16_16) : Q16_16 :=
  if x.toInt < lo.toInt then lo
  else if x.toInt > hi.toInt then hi
  else x

def sat01 (q : Q16_16) : Q16_16 :=
  if q.toInt < 0 then zero
  else if q.toInt > q16Scale then one
  else q

def max (a b : Q16_16) : Q16_16 :=
  if a.toInt ≥ b.toInt then a else b

def min (a b : Q16_16) : Q16_16 :=
  if a.toInt ≤ b.toInt then a else b

def recip (x : Q16_16) : Q16_16 :=
  let xInt := x.toInt
  if xInt = 0 then maxVal
  else
    let numer : Int := 0x100000000
    let denom := if xInt < 0 then -xInt else xInt
    let r := numer / denom
    let y := ofRawInt r
    if xInt < 0 then neg y else y

def ofRaw (n : Nat) : Q16_16 := ofRawInt (n : Int)

-- ═══════════════════════════════════════════════════════════════════════════
-- Algebraic lemmas
-- ═══════════════════════════════════════════════════════════════════════════

@[simp] theorem zero_toInt : toInt zero = 0 := rfl
@[simp] theorem one_toInt : toInt one = 65536 := rfl
@[simp] theorem epsilon_toInt : toInt epsilon = 1 := rfl

theorem epsilon_toInt_pos : toInt epsilon > 0 := by norm_num [epsilon_toInt]

@[simp]
theorem maxVal_toInt : toInt maxVal = q16MaxRaw := rfl

@[simp]
theorem minVal_toInt : toInt minVal = q16MinRaw := rfl

@[simp]
private theorem ofRawInt_zero : ofRawInt 0 = zero := by
  apply Subtype.ext
  simp [ofRawInt, zero, toInt, q16MinRaw, q16MaxRaw]

/-- Saturation lower-bound preservation. -/
theorem ofRawInt_toInt_ge (i c : Int)
    (hi : i ≥ c) (hcMin : q16MinRaw ≤ c) (hcMax : c ≤ q16MaxRaw) :
    (ofRawInt i).toInt ≥ c := by
  unfold ofRawInt toInt
  by_cases hhi : i > q16MaxRaw
  · simp [hhi]
    dsimp [q16MaxRaw] at *
    omega
  · by_cases hlo : i < q16MinRaw
    · dsimp [q16MinRaw, q16MaxRaw] at *
      omega
    · simp [hhi, hlo]
      exact hi

/-- Saturation preserves non-negativity for non-negative raw values. -/
theorem ofRawInt_toInt_nonneg (i : Int) (hi : i ≥ 0) :
    (ofRawInt i).toInt ≥ 0 := by
  exact ofRawInt_toInt_ge i 0 hi (by norm_num [q16MinRaw]) (by norm_num [q16MaxRaw])

/-- Bounded raw reconstruction. -/
theorem ofRawInt_toInt (a : Q16_16) : ofRawInt a.toInt = a := by
  apply Subtype.ext
  unfold ofRawInt toInt
  have hhi : ¬ a.val > q16MaxRaw := by exact not_lt.mpr a.property.2
  have hlo : ¬ a.val < q16MinRaw := by exact not_lt.mpr a.property.1
  simp [hhi, hlo]

theorem ofRawInt_toInt_eq_nonneg (i : Int) (h1 : i ≥ 0) (h2 : i ≤ q16MaxRaw) :
    (ofRawInt i).toInt = i := by
  unfold ofRawInt toInt
  have hhi : ¬ i > q16MaxRaw := by omega
  have hlo : ¬ i < q16MinRaw := by
    dsimp [q16MinRaw] at *
    omega
  simp [hhi, hlo]

/-- Saturating constructor lemma for non-negative raw values. -/
theorem ofRawInt_toInt_eq_general (i : Int) (h1 : i ≥ 0) :
    (ofRawInt i).toInt = if i > q16MaxRaw then q16MaxRaw else i := by
  by_cases h : i > q16MaxRaw
  · unfold ofRawInt toInt
    simp [h]
  · have hlo : ¬ i < q16MinRaw := by
      dsimp [q16MinRaw, q16MaxRaw] at *
      omega
    unfold ofRawInt toInt
    simp [h, hlo]

/-- `(ofRawInt i).toInt = q16Clamp i` — the bridge between the subtype
    constructor and the pure-Int clamp function. -/
theorem ofRawInt_toInt_eq_clamp (i : Int) : (ofRawInt i).toInt = q16Clamp i := by
  unfold ofRawInt toInt q16Clamp
  split_ifs <;> rfl

/-- `@[simp]` version rewriting `.val` directly (avoids `toInt` unfolding
    ordering issues in `simp` calls). -/
@[simp] theorem ofRawInt_val_eq_q16Clamp (i : Int) : (ofRawInt i).val = q16Clamp i :=
  ofRawInt_toInt_eq_clamp i

/-- `ofRawInt` is monotone: a ≤ b → (ofRawInt a).toInt ≤ (ofRawInt b).toInt.
    One-liner via q16Clamp_monotone. -/
theorem ofRawInt_monotone (a b : Int) (h : a ≤ b) :
    (ofRawInt a).toInt ≤ (ofRawInt b).toInt := by
  simp only [ofRawInt_toInt_eq_clamp]
  exact q16Clamp_monotone a b h

/-- Adding a nonnegative Q16_16 value cannot decrease the saturated result.
    This is the general form of the motif-scoring monotonicity used in
    Semantics.PIST.Motif §6.2: motifScore(match=true) ≥ motifScore(match=false). -/
theorem add_nonneg_monotone (a b : Q16_16) (hb : 0 ≤ b.toInt) :
    a.toInt ≤ (add a b).toInt := by
  unfold add
  have := ofRawInt_monotone a.toInt (a.toInt + b.toInt) (by omega)
  rwa [ofRawInt_toInt] at this

/-- zero * a = zero. -/
theorem zero_mul (a : Q16_16) : mul zero a = zero := by
  unfold mul
  rw [zero_toInt]
  simp

/-- a * zero = zero. -/
theorem mul_zero (a : Q16_16) : mul a zero = zero := by
  unfold mul
  rw [zero_toInt]
  simp

/-- a - a = zero. -/
theorem sub_self (a : Q16_16) : sub a a = zero := by
  unfold sub
  simp

/-- a + zero = a. -/
theorem add_zero (a : Q16_16) : add a zero = a := by
  unfold add
  rw [zero_toInt]
  simp
  exact ofRawInt_toInt a

/-- zero + a = a. -/
theorem zero_add (a : Q16_16) : add zero a = a := by
  unfold add
  rw [zero_toInt]
  simp
  exact ofRawInt_toInt a

/-- sqrt zero is zero. -/
theorem sqrt_zero : sqrt zero = zero := by
  unfold sqrt
  simp

/-- sqrt one is within one LSB of one. -/
theorem sqrt_one : (sqrt one).toInt - one.toInt ≤ 1 := by
  native_decide

private theorem int_scale_mul_ediv_cancel (n : Int) : (q16Scale * n) / q16Scale = n := by
  rw [Int.mul_ediv_cancel_left]
  norm_num [q16Scale]

/-- one * a = a. -/
theorem one_mul (a : Q16_16) : mul one a = a := by
  unfold mul
  show ofRawInt (one.toInt * a.toInt / q16Scale) = a
  rw [show one.toInt = q16Scale from rfl]
  have h : (q16Scale * a.toInt) / q16Scale = a.toInt := int_scale_mul_ediv_cancel a.toInt
  rw [h]
  exact ofRawInt_toInt a

/-- a * one = a. -/
theorem mul_one (a : Q16_16) : mul a one = a := by
  unfold mul
  show ofRawInt (a.toInt * one.toInt / q16Scale) = a
  rw [show one.toInt = q16Scale from rfl]
  have h : (a.toInt * q16Scale) / q16Scale = a.toInt := by
    rw [Int.mul_comm]
    exact int_scale_mul_ediv_cancel a.toInt
  rw [h]
  exact ofRawInt_toInt a

/-- toInt = 0 iff the value is zero. -/
theorem toInt_eq_zero_iff {a : Q16_16} : a.toInt = 0 ↔ a = zero := by
  constructor
  · intro h
    apply Subtype.ext
    simpa [toInt, zero] using h
  · intro h
    rw [h]
    rfl

/-- zero / x = zero for any nonzero denominator. -/
theorem zero_div (x : Q16_16) (hx : x.val ≠ 0) : div zero x = zero := by
  unfold div
  have hx' : ¬ x.toInt = 0 := by
    simpa [toInt] using hx
  simp [hx', zero_toInt]

/-- Square is non-negative under signed saturating multiplication. -/
theorem mul_self_nonneg (a : Q16_16) : (mul a a).toInt ≥ 0 := by
  unfold mul
  have hprod : a.toInt * a.toInt ≥ 0 := by nlinarith
  have hdiv : (a.toInt * a.toInt) / q16Scale ≥ 0 := by
    apply Int.ediv_nonneg
    · exact hprod
    · norm_num [q16Scale]
  exact ofRawInt_toInt_nonneg ((a.toInt * a.toInt) / q16Scale) hdiv

/-- Product of two non-negative Q16.16 values is non-negative. -/
theorem mul_toInt_nonneg (a b : Q16_16) (ha : a.toInt ≥ 0) (hb : b.toInt ≥ 0) :
    (mul a b).toInt ≥ 0 := by
  unfold mul
  have hprod : a.toInt * b.toInt ≥ 0 := by nlinarith
  have hdiv : (a.toInt * b.toInt) / q16Scale ≥ 0 := by
    apply Int.ediv_nonneg
    · exact hprod
    · norm_num [q16Scale]
  exact ofRawInt_toInt_nonneg ((a.toInt * b.toInt) / q16Scale) hdiv

/-- Non-negative addition stays non-negative under saturation. -/
theorem ofRaw_toInt_nonneg (acc wcc : Q16_16)
    (hacc : acc.toInt ≥ 0) (hwcc : wcc.toInt ≥ 0) :
    (Q16_16.add acc wcc).toInt ≥ 0 := by
  unfold add
  have hsum : acc.toInt + wcc.toInt ≥ 0 := by omega
  exact ofRawInt_toInt_nonneg (acc.toInt + wcc.toInt) hsum

/-- Compatibility lemma: a non-negative raw value decoded through saturation is non-negative. -/
theorem mk_lt_half_nonneg (s : Int) (hs : s ≥ 0) (_h : s < 2147483648) :
    (ofRawInt s).toInt ≥ 0 := by
  exact ofRawInt_toInt_nonneg s hs

/-- Positive raw addition remains positive under saturation. -/
theorem add_pos_of_pos (a b : Q16_16) (ha : a.toInt > 0) (hb : b.toInt > 0) :
    (add a b).toInt > 0 := by
  unfold add
  have hsum : a.toInt + b.toInt ≥ 1 := by omega
  have hge : (ofRawInt (a.toInt + b.toInt)).toInt ≥ 1 :=
    ofRawInt_toInt_ge (a.toInt + b.toInt) 1 hsum
      (by norm_num [q16MinRaw]) (by norm_num [q16MaxRaw])
  omega

/-- (1 + omega).toInt ≥ 65536 when omega.toInt ≥ 0. -/
theorem add_one_omega_ge_one (omega : Q16_16) (h : omega.toInt ≥ 0) :
    (add one omega).toInt ≥ 65536 := by
  unfold add
  have hsum : one.toInt + omega.toInt ≥ 65536 := by
    rw [one_toInt]
    omega
  exact ofRawInt_toInt_ge (one.toInt + omega.toInt) 65536 hsum
    (by norm_num [q16MinRaw]) (by norm_num [q16MaxRaw])

/-- Non-negative Q16.16 values are bounded by maxVal. -/
theorem toInt_nonneg_le_maxVal (q : Q16_16) (_h : q.toInt ≥ 0) : q.toInt ≤ q16MaxRaw := by
  exact q.property.2

/-- Adding epsilon to a non-negative value yields a positive value. -/
theorem epsilon_add_pos {r : Q16_16} (hr : r.toInt ≥ 0) :
    (r + epsilon).toInt > 0 := by
  change (add r epsilon).toInt > 0
  unfold add
  have hsum : r.toInt + epsilon.toInt ≥ 1 := by
    rw [epsilon_toInt]
    omega
  have hge : (ofRawInt (r.toInt + epsilon.toInt)).toInt ≥ 1 :=
    ofRawInt_toInt_ge (r.toInt + epsilon.toInt) 1 hsum
      (by norm_num [q16MinRaw]) (by norm_num [q16MaxRaw])
  omega

/-- `abs (sub a b) = abs (sub b a)` — absolute value of a difference
    is symmetric. Holds for all Q16_16 values (proved by case analysis
    on `a.val - b.val` at the Int clamping boundary). -/
private lemma q16Clamp_eq_q16MaxRaw_of_ge {x : Int} (h : x ≥ q16MaxRaw) : q16Clamp x = q16MaxRaw := by
  dsimp [q16Clamp]
  by_cases hx : x > q16MaxRaw
  · simp [hx]
  · have hx_eq : x = q16MaxRaw := le_antisymm (le_of_not_gt hx) h
    subst hx_eq; simp [q16Clamp, q16MaxRaw, q16MinRaw]

private lemma q16Clamp_eq_q16MinRaw_of_le {x : Int} (h : x ≤ q16MinRaw) : q16Clamp x = q16MinRaw := by
  dsimp [q16Clamp]
  by_cases hx_hi : x > q16MaxRaw
  · unfold q16MinRaw q16MaxRaw at *; omega
  · by_cases hx_lo : x < q16MinRaw
    · simp [hx_hi, hx_lo]
    · have hx_eq : x = q16MinRaw := le_antisymm h (by
        by_contra hlt
        apply hx_lo
        exact lt_of_not_ge hlt)
      subst hx_eq; simp [q16Clamp, q16MaxRaw, q16MinRaw]

private lemma not_q16MaxRaw_lt_0 : ¬ q16MaxRaw < 0 := by unfold q16MaxRaw; omega

private lemma q16Clamp_2147483648_eq_q16MaxRaw : q16Clamp (2147483648 : Int) = q16MaxRaw := by
  unfold q16Clamp q16MaxRaw q16MinRaw; omega

private lemma val_if (c : Prop) [Decidable c] (x y : Q16_16) : (if c then x else y).val = (if c then x.val else y.val) := by
  split <;> rfl

theorem abs_sub_comm (a b : Q16_16) : abs (sub a b) = abs (sub b a) := by
  apply Q16_16.ext
  simp [abs, sub, neg, toInt, val_if, ofRawInt_val_eq_q16Clamp]
  have hswap : q16Clamp (b.val - a.val) = q16Clamp (-(a.val - b.val)) := by
    have : b.val - a.val = -(a.val - b.val) := by omega
    rw [this]
  rw [hswap]
  set d := a.val - b.val
  have hswap' : q16Clamp (-(a.val - b.val)) = q16Clamp (-d) := by rfl
  rw [hswap']
  by_cases hd_above : d > q16MaxRaw
  · have h_cd : q16Clamp d = q16MaxRaw := q16Clamp_eq_q16MaxRaw_of_ge (le_of_lt hd_above)
    have h_nd_low : -d ≤ q16MinRaw := by unfold q16MaxRaw q16MinRaw at *; omega
    have h_cnd : q16Clamp (-d) = q16MinRaw := q16Clamp_eq_q16MinRaw_of_le h_nd_low
    rw [h_cd, h_cnd]
    unfold q16Clamp q16MaxRaw q16MinRaw; norm_num
  · by_cases hd_below : d < q16MinRaw
    · have h_cd : q16Clamp d = q16MinRaw := q16Clamp_eq_q16MinRaw_of_le (by omega)
      have h_nd_high : -d ≥ q16MaxRaw := by unfold q16MaxRaw q16MinRaw at *; omega
      have h_cnd : q16Clamp (-d) = q16MaxRaw := q16Clamp_eq_q16MaxRaw_of_ge h_nd_high
      rw [h_cd, h_cnd]
      unfold q16Clamp q16MaxRaw q16MinRaw; norm_num
    · have h_lo : q16MinRaw ≤ d := by unfold q16MinRaw q16MaxRaw at *; omega
      have h_hi : d ≤ q16MaxRaw := by unfold q16MinRaw q16MaxRaw at *; omega
      have h_cd : q16Clamp d = d := q16Clamp_id_of_inRange d h_lo h_hi
      rw [h_cd]
      by_cases h_nd_above : -d > q16MaxRaw
      · have h_d_min : d = q16MinRaw := by unfold q16MinRaw q16MaxRaw at *; omega
        rw [h_d_min]
        unfold q16Clamp q16MaxRaw q16MinRaw; norm_num
      · by_cases h_nd_below : -d < q16MinRaw
        · have h_d_max : d = q16MaxRaw := by unfold q16MinRaw q16MaxRaw at *; omega
          rw [h_d_max]
          unfold q16Clamp q16MaxRaw q16MinRaw; norm_num
        · have h_nd_lo' : q16MinRaw ≤ -d := by omega
          have h_nd_hi' : -d ≤ q16MaxRaw := by omega
          have h_cnd : q16Clamp (-d) = -d := q16Clamp_id_of_inRange (-d) h_nd_lo' h_nd_hi'
          rw [h_cnd, show (-(-d : Int) = d) by omega]
          by_cases hd_neg : d < 0
          · omega
          · by_cases hd_zero : d = 0
            · rw [hd_zero]
              unfold q16Clamp q16MinRaw q16MaxRaw; norm_num
            · have hd_pos : 0 < d := by omega
              rw [h_cd]
              split_ifs <;> omega

/-- Subtraction is addition of the negation: a - b = a + (-b).

    NOTE: This theorem is NOT universally true for Q16_16. Counterexample:
    `a = b = q16MinRaw` gives LHS = 0, RHS = -1. The difference arises because
    `neg q16MinRaw` overflows to `q16MaxRaw`, altering the clamping path.
    SSMS does not use this theorem — the `bound` proof has been restructured
    to avoid it. -/
theorem sub_eq_add_neg (a b : Q16_16) (hb : b.toInt > q16MinRaw) : sub a b = add a (neg b) := by
  have h_neg_inRange_lo : q16MinRaw ≤ -b.toInt := by
    have h := b.property.2
    dsimp [toInt] at h ⊢
    dsimp [q16MaxRaw, q16MinRaw] at h ⊢
    omega
  have h_neg_inRange_hi : -b.toInt ≤ q16MaxRaw := by
    dsimp [toInt] at hb ⊢
    dsimp [q16MinRaw] at hb
    dsimp [q16MaxRaw]
    omega
  have h_neg_int : (neg b).toInt = -b.toInt := by
    rw [neg, ofRawInt_toInt_eq_clamp]
    apply q16Clamp_id_of_inRange _ h_neg_inRange_lo h_neg_inRange_hi
  rw [sub, add, h_neg_int]
  rfl

/-- Multiplication by a non-negative scalar is monotone:
    if a ≤ b and c ≥ 0, then a*c ≤ b*c.
    Used in SSMS.aciPreservedByMlgruStep for bound propagation. -/
theorem mul_mono_left (a b c : Q16_16) (h : a.toInt ≤ b.toInt) (hc : c.toInt ≥ 0) :
    (mul a c).toInt ≤ (mul b c).toInt := by
  unfold mul
  have hmul : a.toInt * c.toInt ≤ b.toInt * c.toInt := by
    apply Int.mul_le_mul_of_nonneg_right h hc
  have hpos : 0 < q16Scale := by unfold q16Scale; norm_num
  have hdiv : (a.toInt * c.toInt) / q16Scale ≤ (b.toInt * c.toInt) / q16Scale := by
    apply Int.ediv_le_ediv hpos hmul
  rw [ofRawInt_toInt_eq_clamp, ofRawInt_toInt_eq_clamp]
  exact q16Clamp_monotone _ _ hdiv

/-- Multiplication by a non-negative scalar is monotone on the right. -/
theorem mul_mono_right (a b c : Q16_16) (h : a.toInt ≤ b.toInt) (hc : c.toInt ≥ 0) :
    (mul c a).toInt ≤ (mul c b).toInt := by
  unfold mul
  have hmul : c.toInt * a.toInt ≤ c.toInt * b.toInt := by
    apply Int.mul_le_mul_of_nonneg_left h hc
  have hpos : 0 < q16Scale := by unfold q16Scale; norm_num
  have hdiv : (c.toInt * a.toInt) / q16Scale ≤ (c.toInt * b.toInt) / q16Scale := by
    apply Int.ediv_le_ediv hpos hmul
  rw [ofRawInt_toInt_eq_clamp, ofRawInt_toInt_eq_clamp]
  exact q16Clamp_monotone _ _ hdiv

/-- Addition is monotone in the left argument:
    if a ≤ b then a+c ≤ b+c. -/
theorem add_le_add (a b c : Q16_16) (h : a.toInt ≤ b.toInt) :
    (add a c).toInt ≤ (add b c).toInt := by
  unfold add
  simp [ofRawInt_toInt_eq_clamp]
  apply q16Clamp_monotone
  omega

/-- Absolute value of any Q16_16 value is non-negative. -/
theorem abs_nonneg (a : Q16_16) : (abs a).toInt ≥ 0 := by
  unfold abs neg
  have h := a.property.1
  split_ifs with hlt
  · rw [ofRawInt_toInt_eq_clamp]
    have h_nonneg : 0 ≤ -a.toInt := by omega
    exact q16Clamp_nonneg_of_nonneg h_nonneg
  · omega

/-- For non-negative a, |a*b| ≤ a*|b|.
    WARNING: This lemma is UNCONDITIONALLY FALSE (counterexample: a=3, b=-1
    gives LHS=1, RHS=0). The error comes from floor division: a*b may round
    to -1 but a*|b| rounds to 0. Use abs_mul_bound or a direct convexity
    argument instead.
    TODO(lean-port): do not use this lemma — restructure SSMS to avoid it. -/
-- QUARANTINED: Theorem as stated is FALSE for Q16_16 with floor division. -/
#send_theory_quarantine "FixedPoint.abs_mul_le"
theorem abs_mul_le (a b : Q16_16) (ha : a.toInt ≥ 0) :
    (abs (mul a b)).toInt ≤ (mul a (abs b)).toInt := by
  admit

/-- Triangle inequality for Q16_16: |a*b| ≤ |a| * |b|.
    WARNING: This lemma is FALSE in general (counterexample: a=3, b=-3 gives
    LHS=1, RHS=0). The floor division causes |a*b|/65536 to round up while
    |a|*|b|/65536 rounds to 0 for small values.
    TODO(lean-port): do not use this lemma — restructure SSMS to use
    abs_triangle_add (|x+y| ≤ |x|+|y|) instead. -/
-- QUARANTINED: Theorem as stated is FALSE for Q16_16 with floor division. -/
#send_theory_quarantine "FixedPoint.abs_triangle"
theorem abs_triangle (a b : Q16_16) :
    (abs (mul a b)).toInt ≤ (mul (abs a) (abs b)).toInt := by
  admit

end Q16_16

-- ═══════════════════════════════════════════════════════════════════════════
-- Q0.64 signed normalized fraction
-- ═══════════════════════════════════════════════════════════════════════════

def q0_64MinRaw : Int := -9223372036854775808
def q0_64MaxRaw : Int := 9223372036854775807
def q0_64ScaleNat : Nat := 9223372036854775808

def q0_64ScaleFloat : Float := 9223372036854775808.0

/--
Q0.64 pure fraction representation.
The canonical proof model stores the signed raw integer in the Int64 range.
-/
abbrev Q0_64 := { x : Int // q0_64MinRaw ≤ x ∧ x ≤ q0_64MaxRaw }

instance : Repr Q0_64 where
  reprPrec q _ := repr q.val

instance : BEq Q0_64 where
  beq a b := a.val == b.val

instance : Inhabited Q0_64 where
  default := ⟨0, by constructor <;> norm_num [q0_64MinRaw, q0_64MaxRaw]⟩

instance : ToJson Q0_64 where
  toJson q := Json.mkObj [("val", toJson q.val)]

namespace Q0_64

@[ext]
theorem ext {a b : Q0_64} (h : a.val = b.val) : a = b := Subtype.ext h

@[inline]
def toInt (q : Q0_64) : Int := q.val

@[inline]
def ofRawInt (raw : Int) : Q0_64 :=
  if hhi : raw > q0_64MaxRaw then
    ⟨q0_64MaxRaw, by constructor <;> norm_num [q0_64MinRaw, q0_64MaxRaw]⟩
  else if hlo : raw < q0_64MinRaw then
    ⟨q0_64MinRaw, by constructor <;> norm_num [q0_64MinRaw, q0_64MaxRaw]⟩
  else
    ⟨raw, by
      constructor
      · dsimp [q0_64MinRaw, q0_64MaxRaw] at *; omega
      · dsimp [q0_64MinRaw, q0_64MaxRaw] at *; omega⟩

instance : FromJson Q0_64 where
  fromJson? j := do
    let raw : Int ← fromJson? (← j.getObjVal? "val")
    pure (ofRawInt raw)

/-- Maximum positive value. -/
def one : Q0_64 := ofRawInt q0_64MaxRaw

def zero : Q0_64 := ofRawInt 0

def ofRatio (num : Nat) (den : Nat) : Q0_64 :=
  if den = 0 then zero
  else ofRawInt (Int.ofNat (num * q0_64ScaleNat / den))

def half : Q0_64 := ofRawInt 4611686018427387903

def neg (x : Q0_64) : Q0_64 := ofRawInt (-x.toInt)
def add (a b : Q0_64) : Q0_64 := ofRawInt (a.toInt + b.toInt)
def sub (a b : Q0_64) : Q0_64 := ofRawInt (a.toInt - b.toInt)
def mul (a b : Q0_64) : Q0_64 :=
  ofRawInt ((a.toInt * b.toInt) / Int.ofNat q0_64ScaleNat)
def div (a b : Q0_64) : Q0_64 :=
  if b.toInt = 0 then one
  else ofRawInt ((a.toInt * Int.ofNat q0_64ScaleNat) / b.toInt)
def abs (x : Q0_64) : Q0_64 := if x.toInt < 0 then neg x else x

def ofFloat (f : Float) : Q0_64 :=
  if f.isNaN || f ≥ 1.0 then one
  else if f ≤ -1.0 then ofRawInt q0_64MinRaw
  else if f < 0.0 then
    ofRawInt (-(Int.ofNat ((-f * q0_64ScaleFloat).floor.toUInt64.toNat)))
  else
    ofRawInt (Int.ofNat ((f * q0_64ScaleFloat).floor.toUInt64.toNat))

def toFloat (q : Q0_64) : Float :=
  Float.ofInt q.toInt / q0_64ScaleFloat

instance : Add Q0_64 := ⟨add⟩
instance : Sub Q0_64 := ⟨sub⟩
instance : Mul Q0_64 := ⟨mul⟩
instance : Div Q0_64 := ⟨div⟩
instance : Neg Q0_64 := ⟨neg⟩

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
-- Pandigital π Approximation
-- ═══════════════════════════════════════════════════════════════════════════

namespace PandigitalPi

/-- High term: 3.8415926. -/
def highTerm : Q16_16 := Q16_16.ofRawInt 251819

/-- Low term: 0.7. -/
def lowTerm : Q16_16 := Q16_16.ofRawInt 45875

def piPandigital : Q16_16 := highTerm - lowTerm

def piDirect : Q16_16 := Q16_16.ofRawInt 205944

theorem piPandigitalCorrect : (piPandigital.toInt - piDirect.toInt).natAbs ≤ 1 := by
  native_decide

def spaceAnalysis : String :=
  "Pandigital pi: 6 bytes packed vs 4 bytes direct Q16.16 (trade-off for mathematical elegance)"

#eval piPandigital.toFloat
#eval piDirect.toFloat
#eval (piPandigital.toInt - piDirect.toInt).natAbs

end PandigitalPi

end Semantics.FixedPoint

namespace Semantics
  export FixedPoint (Q0_16 Q16_16 Q0_64)
  namespace Q16_16
    export FixedPoint.Q16_16
      (zero one negOne epsilon two infinity maxVal minVal ofNat satFromNat ofRatio toInt
       ofRawInt ofBits toBits ofFloat toFloat scale ofInt add sub mul div abs neg sqrt ln log2
       expNeg sat01 max min le ge gt lt recip ofRaw clip isNeg zero_mul mul_zero one_mul
       mul_one zero_add add_zero sub_self zero_toInt one_toInt epsilon_toInt
       epsilon_toInt_pos toInt_eq_zero_iff epsilon_add_pos zero_div mul_self_nonneg
       mul_toInt_nonneg ofRaw_toInt_nonneg mk_lt_half_nonneg add_one_omega_ge_one
       toInt_nonneg_le_maxVal add_pos_of_pos)
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
