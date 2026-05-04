namespace Semantics

/--
Q16.16 fixed-point representation.
- 32-bit unsigned integer interpreted as signed 16.16 fixed point.
- 0x00010000 = 1.0
- 0xFFFFFFFF = -0.000015 (or used as sentinel for infinity/illegal)
- Range: [-32768.0, 32767.999985]
- Resolution: 1/65536 ≈ 0.000015

All arithmetic uses 64-bit intermediates to prevent overflow,
then truncates back to 32 bits.
-/
structure Q16_16 where
  val : UInt32
deriving Repr, DecidableEq, BEq, Inhabited

namespace Q16_16

def zero : Q16_16 := ⟨0x00000000⟩
def one  : Q16_16 := ⟨0x00010000⟩
def infinity : Q16_16 := ⟨0xFFFFFFFF⟩

@[inline]
def ofInt (n : Int) : Q16_16 :=
  ⟨UInt32.ofInt (n * 65536)⟩

@[inline]
def toInt (q : Q16_16) : Int :=
  Int.ofNat (q.val.toUInt64 : UInt64).toNat - (if q.val ≥ 0x80000000 then 0x100000000 else 0)

@[inline]
def toFloat (q : Q16_16) : Float :=
  Float.ofInt (toInt q) / 65536.0

@[inline]
def ofFloat (f : Float) : Q16_16 :=
  if f.isNaN || f ≥ 32768.0 then infinity
  else if f ≤ -32768.0 then ⟨0x80000000⟩
  else ⟨(f * 65536.0).floor.toUInt32⟩

@[inline]
def add (a b : Q16_16) : Q16_16 := ⟨(a.val.toUInt64 + b.val.toUInt64).toUInt32⟩

@[inline]
def sub (a b : Q16_16) : Q16_16 := ⟨(a.val.toUInt64 - b.val.toUInt64).toUInt32⟩

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
  else ⟨(if q.val ≥ 0x80000000 then UInt32.ofInt (-Int.ofNat q.val.toNat) else q.val)⟩

@[inline]
def max (a b : Q16_16) : Q16_16 :=
  ⟨if a.val ≥ b.val then a.val else b.val⟩

@[inline]
def min (a b : Q16_16) : Q16_16 :=
  ⟨if a.val ≤ b.val then a.val else b.val⟩

@[inline]
def neg (q : Q16_16) : Q16_16 := ⟨UInt32.ofInt (-q.toInt)⟩

@[inline]
def sqrt (q : Q16_16) : Q16_16 :=
  if q.val == 0 then zero
  else
    let f := toFloat q
    if f ≤ 0.0 then zero
    else ofFloat (Float.sqrt f)

@[inline]
def pow (a b : Q16_16) : Q16_16 :=
  ofFloat (Float.pow (toFloat a) (toFloat b))

@[inline]
def sin (q : Q16_16) : Q16_16 :=
  ofFloat (Float.sin (toFloat q))

@[inline]
def gt (a b : Q16_16) : Bool := a.toInt > b.toInt

@[inline]
def lt (a b : Q16_16) : Bool := a.toInt < b.toInt

@[inline]
def le (a b : Q16_16) : Bool := a.toInt ≤ b.toInt

@[inline]
def ge (a b : Q16_16) : Bool := a.toInt ≥ b.toInt

-- Typeclass instances for comparison operators
instance : LE Q16_16 where
  le a b := a.toInt ≤ b.toInt

instance : LT Q16_16 where
  lt a b := a.toInt < b.toInt

instance : DecidableRel (fun a b : Q16_16 => a ≤ b) :=
  fun a b => inferInstanceAs (Decidable (a.toInt ≤ b.toInt))

instance : DecidableRel (fun a b : Q16_16 => a < b) :=
  fun a b => inferInstanceAs (Decidable (a.toInt < b.toInt))

end Q16_16

end Semantics
