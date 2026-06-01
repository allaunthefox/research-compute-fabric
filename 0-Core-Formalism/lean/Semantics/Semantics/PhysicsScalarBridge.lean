import Semantics.FixedPoint
import Semantics.PhysicsScalar

namespace Semantics.PhysicsScalarBridge

open Semantics.FixedPoint
open Semantics.PhysicsScalar

/-- Convert from PhysicsScalar.Q16_16 (UInt32) to FixedPoint.Q16_16 (Int subtype).
    This is a lossy conversion that maps the unsigned range to signed range.
    Note: This is not a perfect bijection due to different semantic models. -/
def toFixedPoint (ps : PhysicsScalar.Q16_16) : Semantics.FixedPoint.Q16_16 :=
  let rawInt := ps.toNat - 2147483648
  Semantics.FixedPoint.Q16_16.ofRawInt rawInt

/-- Convert from FixedPoint.Q16_16 (Int subtype) to PhysicsScalar.Q16_16 (UInt32).
    This is a lossy conversion that maps the signed range to unsigned range. -/
def fromFixedPoint (fp : Semantics.FixedPoint.Q16_16) : PhysicsScalar.Q16_16 :=
  let rawNat := fp.toInt + 2147483648
  PhysicsScalar.Q16_16.satFromNat rawNat.toNat

/-- Bridge constants - just forward to PhysicsScalar for consistency -/
def scale : Nat := PhysicsScalar.Q16_16.scale
def maxNat : Nat := PhysicsScalar.Q16_16.maxNat
def zero : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.zero
def one : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.one
def two : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.two
def three : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.three
def four : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.four
def half : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.half
def quarter : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.quarter
def eighth : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.eighth
def maxValue : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.maxValue

/-- Bridge PhysicsScalar-specific functions (just forward) -/
def fromRawNat (v : Nat) : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.fromRawNat v
def satFromNat (v : Nat) : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.satFromNat v
def toNatFloor (v : PhysicsScalar.Q16_16) : Nat := PhysicsScalar.Q16_16.toNatFloor v
def add (a b : PhysicsScalar.Q16_16) : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.add a b
def addSaturating (a b : PhysicsScalar.Q16_16) : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.addSaturating a b
def sub (a b : PhysicsScalar.Q16_16) : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.sub a b
def subSaturating (a b : PhysicsScalar.Q16_16) : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.subSaturating a b
def mul (a b : PhysicsScalar.Q16_16) : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.mul a b
def mulQ16_16 (a b : PhysicsScalar.Q16_16) : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.mulQ16_16 a b
def div (a b : PhysicsScalar.Q16_16) : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.div a b
def divQ16_16 (a b : PhysicsScalar.Q16_16) : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.divQ16_16 a b
def min (a b : PhysicsScalar.Q16_16) : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.min a b
def max (a b : PhysicsScalar.Q16_16) : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.max a b
def clamp (v a b : PhysicsScalar.Q16_16) : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.clamp v a b
def avg (a b : PhysicsScalar.Q16_16) : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.avg a b
def mean3 (a b c : PhysicsScalar.Q16_16) : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.mean3 a b c
def absDiff (a b : PhysicsScalar.Q16_16) : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.absDiff a b
def lerpQ16_16 (s e w : PhysicsScalar.Q16_16) : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.lerpQ16_16 s e w
def isZero (v : PhysicsScalar.Q16_16) : Bool := PhysicsScalar.Q16_16.isZero v
def nonZero (v : PhysicsScalar.Q16_16) : Bool := PhysicsScalar.Q16_16.nonZero v
def betweenInclusive (v a b : PhysicsScalar.Q16_16) : Bool := PhysicsScalar.Q16_16.betweenInclusive v a b

/-- Bridge comparison operations -/
def gt (a : PhysicsScalar.Q16_16) (b : PhysicsScalar.Q16_16) : Bool :=
  a.toNat > b.toNat

def ge (a : PhysicsScalar.Q16_16) (b : PhysicsScalar.Q16_16) : Bool :=
  a.toNat >= b.toNat

def le (a : PhysicsScalar.Q16_16) (b : PhysicsScalar.Q16_16) : Bool :=
  a.toNat <= b.toNat

def lt (a : PhysicsScalar.Q16_16) (b : PhysicsScalar.Q16_16) : Bool :=
  a.toNat < b.toNat

def eq (a : PhysicsScalar.Q16_16) (b : PhysicsScalar.Q16_16) : Bool :=
  a.toNat = b.toNat

end Semantics.PhysicsScalarBridge