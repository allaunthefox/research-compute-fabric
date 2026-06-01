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

end Semantics.PhysicsScalarBridge