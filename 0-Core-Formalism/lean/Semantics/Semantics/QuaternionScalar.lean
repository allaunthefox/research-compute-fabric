/-
  QuaternionScalar.lean - Quaternion-based Dimensionless Scalar Field Set
  and Bracketed PBACS Style Representation

  Based on quaternionic algebra: q = q₀ + q₁i + q₂j + q₃k
  where q₀ is the dimensionless scalar part representing:
  - Temporal Identity (Hamilton's time interpretation)
  - Metric of Alignment (cosine of half-angle rotation)
  - Information Density (entropy/compression efficiency)

  References:
  - Chappell et al. (2016). Time As a Geometric Property of Space.
  - Hanson (2020). Quaternion-based spatial-coordinate alignment.
  - Quee (1983). Quaternion algebra in three-dimensional space.
-/

import Semantics.FixedPoint

namespace Semantics.QuaternionScalar

open Semantics.Q16_16

/-- Quaternion with dimensionless scalar part -/
structure Quaternion where
  scalar : Q16_16  -- q₀: dimensionless scalar (time, alignment, density)
  i : Q16_16       -- q₁: i-component
  j : Q16_16       -- q₂: j-component
  k : Q16_16       -- q₃: k-component
  deriving Repr, DecidableEq, BEq

namespace Quaternion

/-- Create a quaternion from scalar and vector parts -/
def make (scalar i j k : Q16_16) : Quaternion :=
  { scalar := scalar, i := i, j := j, k := k }

/-- Zero quaternion -/
def zero : Quaternion :=
  make Q16_16.zero Q16_16.zero Q16_16.zero Q16_16.zero

/-- Identity quaternion (scalar = 1, vector = 0) -/
def one : Quaternion :=
  make Q16_16.one Q16_16.zero Q16_16.zero Q16_16.zero

/-- Vector part magnitude squared (|v|² = q₁² + q₂² + q₃²) -/
def vectorMagSq (q : Quaternion) : Q16_16 :=
  q.i * q.i + q.j * q.j + q.k * q.k

/-- Full quaternion magnitude squared (|q|² = q₀² + |v|²) -/
def magSq (q : Quaternion) : Q16_16 :=
  q.scalar * q.scalar + vectorMagSq q

/-- Quaternion addition -/
def add (x y : Quaternion) : Quaternion :=
  mk (x.scalar + y.scalar) (x.i + y.i) (x.j + y.j) (x.k + y.k)

/-- Quaternion multiplication: q² = q₀² - |v|² + 2q₀v -/
def mul (x y : Quaternion) : Quaternion :=
  let newScalar := x.scalar * y.scalar - x.i * y.i - x.j * y.j - x.k * y.k
  let newI := x.scalar * y.i + x.i * y.scalar + x.j * y.k - x.k * y.j
  let newJ := x.scalar * y.j - x.i * y.k + x.j * y.scalar + x.k * y.i
  let newK := x.scalar * y.k + x.i * y.j - x.j * y.i + x.k * y.scalar
  mk newScalar newI newJ newK

/-- Quaternion squaring -/
def sq (q : Quaternion) : Quaternion :=
  mul q q

/-- Scalar part of quaternion (q₀) -/
def scalarPart (q : Quaternion) : Q16_16 :=
  q.scalar

/-- Vector part of quaternion (v = q₁i + q₂j + q₃k) -/
def vectorPart (q : Quaternion) : Quaternion :=
  make Q16_16.zero q.i q.j q.k

/-- Check if quaternion is a unit quaternion (|q| = 1) -/
def isUnit (q : Quaternion) : Bool :=
  magSq q == Q16_16.one

/-- Cosine of half-angle for unit quaternions: q₀ = cos(θ/2) -/
def halfAngleCosine (q : Quaternion) : Q16_16 :=
  if isUnit q then q.scalar else Q16_16.zero

/-- Information density interpretation (scalar as entropy density) -/
def informationDensity (q : Quaternion) : Q16_16 :=
  q.scalar

/-- Temporal identity interpretation (scalar as time scale factor) -/
def temporalScale (q : Quaternion) : Q16_16 :=
  q.scalar

instance : Add Quaternion where
  add := add

instance : Mul Quaternion where
  mul := mul

instance : Zero Quaternion where
  zero := zero

instance : One Quaternion where
  one := one

end Quaternion

/-- Bracketed PBACS style quaternion representation -/
structure BracketedQuaternion where
  lowerScalar : Q16_16   -- Lower bound for scalar part
  upperScalar : Q16_16   -- Upper bound for scalar part
  valueScalar : Q16_16   -- Value for scalar part
  lowerVector : Quaternion  -- Lower bound for vector part
  upperVector : Quaternion  -- Upper bound for vector part
  valueVector : Quaternion  -- Value for vector part
  scale : UInt32
  deriving Repr, DecidableEq, BEq

namespace BracketedQuaternion

/-- Encode a bracketed quaternion from bounds and values -/
def encode (lowerScalar upperScalar valueScalar : Q16_16)
          (lowerVector upperVector valueVector : Quaternion)
          (scale : UInt32) : BracketedQuaternion :=
  {
    lowerScalar := lowerScalar,
    upperScalar := upperScalar,
    valueScalar := valueScalar,
    lowerVector := lowerVector,
    upperVector := upperVector,
    valueVector := valueVector,
    scale := scale
  }

/-- Width of scalar bracket -/
def scalarWidth (b : BracketedQuaternion) : Q16_16 :=
  b.upperScalar - b.lowerScalar

/-- Width of vector bracket (magnitude) -/
def vectorWidth (b : BracketedQuaternion) : Q16_16 :=
  let lowerMag := Quaternion.magSq b.lowerVector
  let upperMag := Quaternion.magSq b.upperVector
  upperMag - lowerMag

/-- Check if scalar value is within bounds -/
def scalarInBounds (b : BracketedQuaternion) : Bool :=
  b.lowerScalar.val <= b.valueScalar.val && b.valueScalar.val <= b.upperScalar.val

/-- Check if vector value is within bounds -/
def vectorInBounds (b : BracketedQuaternion) : Bool :=
  let valMag := Quaternion.magSq b.valueVector
  let lowerMag := Quaternion.magSq b.lowerVector
  let upperMag := Quaternion.magSq b.upperVector
  lowerMag.val <= valMag.val && valMag.val <= upperMag.val

/-- Bracketed quaternion addition -/
def bracketAdd (x y : BracketedQuaternion) : BracketedQuaternion :=
  let newLowerScalar := x.lowerScalar + y.lowerScalar
  let newValueScalar := x.valueScalar + y.valueScalar
  let newUpperScalar := x.upperScalar + y.upperScalar
  let newLowerVector := Quaternion.add x.lowerVector y.lowerVector
  let newValueVector := Quaternion.add x.valueVector y.valueVector
  let newUpperVector := Quaternion.add x.upperVector y.upperVector
  encode newLowerScalar newUpperScalar newValueScalar
        newLowerVector newUpperVector newValueVector
        (UInt32.ofNat (Nat.max x.scale.toNat y.scale.toNat))

/-- Bracketed quaternion multiplication (conservative bounds) -/
def bracketMulConservative (x y : BracketedQuaternion) : BracketedQuaternion :=
  -- Scalar bounds: [ls1*ls2 - max|v1||v2|, us1*us2 - min|v1||v2|]
  let ls1 := x.lowerScalar
  let us1 := x.upperScalar
  let ls2 := y.lowerScalar
  let us2 := y.upperScalar
  let v1LowerMag := Quaternion.magSq x.lowerVector
  let v1UpperMag := Quaternion.magSq x.upperVector
  let v2LowerMag := Quaternion.magSq y.lowerVector
  let v2UpperMag := Quaternion.magSq y.upperVector
  
  let maxProduct := max (max (ls1*ls2) (ls1*us2)) (max (us1*ls2) (us1*us2))
  let minProduct := min (min (ls1*ls2) (ls1*us2)) (min (us1*ls2) (us1*us2))
  let maxVMag := max (max v1LowerMag v1UpperMag) (max v2LowerMag v2UpperMag)
  let minVMag := min (min v1LowerMag v1UpperMag) (min v2LowerMag v2UpperMag)
  
  let newLowerScalar := minProduct - maxVMag
  let newUpperScalar := maxProduct - minVMag
  let newValueScalar := x.valueScalar * y.valueScalar
  
  -- Vector bounds (conservative)
  let newLowerVector := Quaternion.mul x.lowerVector y.lowerVector
  let newUpperVector := Quaternion.mul x.upperVector y.upperVector
  let newValueVector := Quaternion.mul x.valueVector y.valueVector
  
  encode newLowerScalar newUpperScalar newValueScalar
        newLowerVector newUpperVector newValueVector
        (UInt32.ofNat (Nat.max x.scale.toNat y.scale.toNat))

/-- Extract the central quaternion value -/
def centralValue (b : BracketedQuaternion) : Quaternion :=
  Quaternion.mk b.valueScalar b.valueVector.i b.valueVector.j b.valueVector.k

/-- Check if bracket represents a unit quaternion range -/
def isUnitRange (b : BracketedQuaternion) (tolerance : Q16_16) : Bool :=
  let centralMag := Quaternion.magSq (centralValue b)
  let diff := centralMag - one
  let absDiff := if diff.val >= 0 then diff else -diff
  absDiff.val <= tolerance.val

/-- Temporal scale interpretation for bracketed quaternion -/
def bracketTemporalScale (b : BracketedQuaternion) : Q16_16 :=
  b.valueScalar

/-- Information density interpretation for bracketed quaternion -/
def bracketInformationDensity (b : BracketedQuaternion) : Q16_16 :=
  b.valueScalar

/-- Metric of alignment (cosine of half-angle) for bracketed quaternion -/
def bracketAlignmentMetric (b : BracketedQuaternion) : Q16_16 :=
  if isUnitRange b (Q16_16.ofFloat 0.01) then b.valueScalar else Q16_16.zero

end BracketedQuaternion

#eval Quaternion.make (Q16_16.ofFloat 1.0) (Q16_16.ofFloat 0.0) (Q16_16.ofFloat 0.0) (Q16_16.ofFloat 0.0)
#eval Quaternion.magSq (Quaternion.make (Q16_16.ofFloat 1.0) (Q16_16.ofFloat 0.0) (Q16_16.ofFloat 0.0) (Q16_16.ofFloat 0.0))
#eval Quaternion.isUnit (Quaternion.make (Q16_16.ofFloat 1.0) (Q16_16.ofFloat 0.0) (Q16_16.ofFloat 0.0) (Q16_16.ofFloat 0.0))

end Semantics.QuaternionScalar
