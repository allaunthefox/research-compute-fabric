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

/-- Bridge arithmetic operations to maintain compatibility during migration -/
def add (a b : PhysicsScalar.Q16_16) : PhysicsScalar.Q16_16 :=
  fromFixedPoint ((toFixedPoint a) + (toFixedPoint b))

def mul (a b : PhysicsScalar.Q16_16) : PhysicsScalar.Q16_16 :=
  fromFixedPoint ((toFixedPoint a) * (toFixedPoint b))

def sub (a b : PhysicsScalar.Q16_16) : PhysicsScalar.Q16_16 :=
  fromFixedPoint ((toFixedPoint a) - (toFixedPoint b))

/-- Bridge comparison operations -/
def gt (a : PhysicsScalar.Q16_16) (b : PhysicsScalar.Q16_16) : Bool :=
  (toFixedPoint a).gt (toFixedPoint b)

def ge (a : PhysicsScalar.Q16_16) (b : PhysicsScalar.Q16_16) : Bool :=
  (toFixedPoint a).ge (toFixedPoint b)

def le (a : PhysicsScalar.Q16_16) (b : PhysicsScalar.Q16_16) : Bool :=
  (toFixedPoint a).le (toFixedPoint b)

/-- Bridge constants for PhysicsScalar compatibility -/
def zero : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.zero
def one : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.one
def two : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.two
def three : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.three
def four : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.four
def half : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.half
def quarter : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.quarter
def maxValue : PhysicsScalar.Q16_16 := PhysicsScalar.Q16_16.maxValue

end Semantics.PhysicsScalarBridge