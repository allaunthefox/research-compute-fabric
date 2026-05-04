namespace Semantics.PhysicsScalar

abbrev Q16_16 := UInt32

namespace Q16_16

def scale : Nat := 65536

def maxNat : Nat := 4294967295

def zero : Q16_16 := UInt32.ofNat 0

def one : Q16_16 := UInt32.ofNat 65536

def half : Q16_16 := UInt32.ofNat 32768

def quarter : Q16_16 := UInt32.ofNat 16384

def two : Q16_16 := UInt32.ofNat 131072

def three : Q16_16 := UInt32.ofNat 196608

def four : Q16_16 := UInt32.ofNat 262144

def maxValue : Q16_16 := UInt32.ofNat maxNat

def satFromNat (value : Nat) : Q16_16 :=
  if value <= maxNat then UInt32.ofNat value else UInt32.ofNat maxNat

def fromRawNat (value : Nat) : Q16_16 :=
  satFromNat value

def fromNat (value : Nat) : Q16_16 :=
  satFromNat (value * scale)

def toNatFloor (value : Q16_16) : Nat :=
  value.toNat / scale

def add (left right : Q16_16) : Q16_16 :=
  satFromNat (left.toNat + right.toNat)

def addSaturating (left right : Q16_16) : Q16_16 :=
  add left right

def sub (left right : Q16_16) : Q16_16 :=
  if left.toNat <= right.toNat then zero else UInt32.ofNat (left.toNat - right.toNat)

def subSaturating (left right : Q16_16) : Q16_16 :=
  sub left right

def mul (left right : Q16_16) : Q16_16 :=
  satFromNat ((left.toNat * right.toNat) / scale)

def mulQ16_16 (left right : Q16_16) : Q16_16 :=
  mul left right

def div (left right : Q16_16) : Q16_16 :=
  if right = zero then maxValue else satFromNat ((left.toNat * scale) / right.toNat)

def divQ16_16 (left right : Q16_16) : Q16_16 :=
  div left right

def min (left right : Q16_16) : Q16_16 :=
  if left.toNat <= right.toNat then left else right

def max (left right : Q16_16) : Q16_16 :=
  if left.toNat >= right.toNat then left else right

def clamp (value lower upper : Q16_16) : Q16_16 :=
  max lower (min value upper)

def avg (left right : Q16_16) : Q16_16 :=
  UInt32.ofNat ((left.toNat + right.toNat) / 2)

def mean3 (a b c : Q16_16) : Q16_16 :=
  UInt32.ofNat ((a.toNat + b.toNat + c.toNat) / 3)

def absDiff (left right : Q16_16) : Q16_16 :=
  if left.toNat >= right.toNat then UInt32.ofNat (left.toNat - right.toNat) else UInt32.ofNat (right.toNat - left.toNat)

def lerpQ16_16 (startValue endValue weight : Q16_16) : Q16_16 :=
  let retained := mul startValue (sub one weight)
  let shifted := mul endValue weight
  add retained shifted

def ge (left right : Q16_16) : Bool :=
  left.toNat >= right.toNat

def gt (left right : Q16_16) : Bool :=
  left.toNat > right.toNat

def le (left right : Q16_16) : Bool :=
  left.toNat <= right.toNat

def lt (left right : Q16_16) : Bool :=
  left.toNat < right.toNat

def eq (left right : Q16_16) : Bool :=
  left.toNat = right.toNat

def isZero (value : Q16_16) : Bool :=
  value = zero

def nonZero (value : Q16_16) : Bool :=
  value != zero

def betweenInclusive (value lower upper : Q16_16) : Bool :=
  ge value lower && le value upper

end Q16_16

end Semantics.PhysicsScalar
