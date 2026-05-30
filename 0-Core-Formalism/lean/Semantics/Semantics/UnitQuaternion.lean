import Semantics.FixedPoint
import Semantics.SLUG3
import Mathlib.Data.Fin.Basic
import Mathlib.Algebra.Quaternion
import Semantics.Q16_16Numerics

namespace Semantics

open Q16_16

-- ═══════════════════════════════════════════════════════════════════════════
-- §0  Fixed-Point Trigonometry (using rigorous Q16_16Numerics)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Cosine using rigorous Q16_16Numerics.
    Input: angle in radians, scaled to Q16_16.
    Output: cos(angle) in Q16_16 with error < 2⁻¹⁶. -/
def cos (x : Q16_16) : Q16_16 :=
  Semantics.Q16_16Numerics.cos x

/-- Sine using rigorous Q16_16Numerics.
    Input: angle in radians, scaled to Q16_16.
    Output: sin(angle) in Q16_16 with error < 2⁻¹⁶. -/
def sin (x : Q16_16) : Q16_16 :=
  Semantics.Q16_16Numerics.sin x

/-- Arccosine using rigorous Q16_16Numerics.
    Input: value in [-1.0, 1.0], scaled to Q16_16.
    Output: arccos(value) in radians with error < 2⁻¹⁶. -/
def acos (x : Q16_16) : Q16_16 :=
  Semantics.Q16_16Numerics.acos x

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Unit Quaternion Receipt Type (S³ Embedding)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Quaternion representing a point intended to live on S³.

    This module uses Q16_16 approximations for trigonometry, SLERP, and fixed-point
    multiplication. Those operations do not currently carry exact algebraic proofs
    that `w² + x² + y² + z² = 1`. The previous version stored that exact theorem as
    a field and filled it with `sorry` in every nontrivial operation.

    `wf_unit` is therefore an explicit receipt bit: it records that the value was
    produced by a unit-preserving constructor or by an operation that propagates such
    a receipt. Exact norm preservation belongs in a future real/quaternion bridge,
    not in this approximate Q16_16 hot path. -/
structure UnitQuaternion where
  w : Q16_16  -- scalar (real) part
  x : Q16_16  -- i component
  y : Q16_16  -- j component
  z : Q16_16  -- k component
  wf_unit : Bool  -- approximate unit-norm receipt, not an exact theorem
  deriving Repr

namespace UnitQuaternion

/-- Fixed-point norm-square witness value. -/
def normSq (q : UnitQuaternion) : Q16_16 :=
  q.w * q.w + q.x * q.x + q.y * q.y + q.z * q.z

/-- Identity quaternion (1, 0, 0, 0) - neutral element. -/
def identity : UnitQuaternion :=
  { w := one
    x := zero
    y := zero
    z := zero
    wf_unit := true }

/-- Quaternion multiplication (Hamilton product).
    The unit receipt is propagated from both inputs. -/
def mul (a b : UnitQuaternion) : UnitQuaternion :=
  let w' := a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z
  let x' := a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y
  let y' := a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x
  let z' := a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w
  { w := w', x := x', y := y', z := z', wf_unit := a.wf_unit && b.wf_unit }

/-- Dot product as scalar part of a × b* (conjugate product).
    For exact unit quaternions: a · b = cos(θ). In this module it is the Q16_16
    approximate dot product. -/
def dot (a b : UnitQuaternion) : Q16_16 :=
  a.w * b.w + a.x * b.x + a.y * b.y + a.z * b.z

/-- Great circle distance on S³: approximate arccos(a · b).
    For compression: distance maps to dissimilarity metric.
    Uses rigorous Q16_16Numerics.acos for proper precision. -/
def distance (a b : UnitQuaternion) : Q16_16 :=
  let d := dot a b
  if d.val ≥ 0x00010000 then  -- d ≥ 1.0
    zero  -- distance = 0 (identical)
  else if d.val ≤ 0xFFFF0000 then  -- d ≤ -1.0
    Semantics.Q16_16Numerics.pi  -- π ≈ 3.14159
  else
    Semantics.Q16_16Numerics.acos d  -- rigorous arccos

/-- Quaternion conjugate: q* = [w, -x, -y, -z].
    The unit receipt is preserved. -/
def conjugate (q : UnitQuaternion) : UnitQuaternion :=
  { w := q.w, x := neg q.x, y := neg q.y, z := neg q.z, wf_unit := q.wf_unit }

/-- Quaternion inverse: q⁻¹ = q* / ||q||².
    For receipt-carrying unit quaternions, q⁻¹ is represented by conjugate. -/
def inv (q : UnitQuaternion) : UnitQuaternion :=
  q.conjugate

/-- Rotation of point p by unit quaternion q.
    This implementation intentionally returns the vector part of q·p·q⁻¹, but the
    pure-vector input is not itself a unit quaternion. Its receipt is therefore false. -/
def rotateVector (q : UnitQuaternion) (v : Q16_16 × Q16_16 × Q16_16) : Q16_16 × Q16_16 × Q16_16 :=
  let (vx, vy, vz) := v
  let p := { w := zero, x := vx, y := vy, z := vz, wf_unit := false }
  let rotated := (q.mul p).mul q.inv
  (rotated.x, rotated.y, rotated.z)

/-- Construct a receipt-carrying quaternion from axis-angle representation.
    Because trigonometry is approximate in Q16_16, this carries a unit receipt rather
    than an exact norm proof. -/
def fromAxisAngle (axis : Q16_16 × Q16_16 × Q16_16) (angle : Q16_16) : UnitQuaternion :=
  let (ux, uy, uz) := axis
  let cosHalf := cos (angle / ofInt 2)
  let sinHalf := sin (angle / ofInt 2)
  let norm := Semantics.Q16_16Numerics.sqrt (ux * ux + uy * uy + uz * uz)
  let cosTheta := cosHalf
  let sinTheta := sinHalf * norm
  { w := cosTheta, x := sinTheta * ux, y := sinTheta * uy, z := sinTheta * uz,
    wf_unit := true }

/-- Extract axis-angle from unit quaternion.
    Returns (axis, angle) where axis is unit vector and angle ∈ [0, 2π). -/
def toAxisAngle (q : UnitQuaternion) : (Q16_16 × Q16_16 × Q16_16) × Q16_16 :=
  let angle := ofNat 2 * acos q.w  -- θ = 2·arccos(w)
  let sinHalf := sin (angle / ofNat 2)
  let axis := if sinHalf.val > 0x00000100 then  -- sin(θ/2) ≠ 0
    (q.x / sinHalf, q.y / sinHalf, q.z / sinHalf)
  else
    (one, zero, zero)  -- Identity rotation: arbitrary axis
  (axis, angle)

/-- Spherical Linear Interpolation (SLERP) between two unit quaternions.
    The result receives a unit receipt when both endpoints carry one. -/
def slerp (a b : UnitQuaternion) (t : Q16_16) : UnitQuaternion :=
  let dotAB := a.dot b
  let (b', dotAB') := if dotAB.val < 0x00008000 then
    ({ w := neg b.w, x := neg b.x, y := neg b.y, z := neg b.z,
       wf_unit := b.wf_unit }, neg dotAB)
  else
    (b, dotAB)

  let omega := acos dotAB'  -- Angle between quaternions
  let sinOmega := sin omega

  if sinOmega.val < 0x00000100 then  -- Quaternions nearly parallel
    let w1 := one - t
    let w2 := t
    { w := w1 * a.w + w2 * b'.w,
      x := w1 * a.x + w2 * b'.x,
      y := w1 * a.y + w2 * b'.y,
      z := w1 * a.z + w2 * b'.z,
      wf_unit := a.wf_unit && b'.wf_unit }
  else
    let w1 := sin ((one - t) * omega) / sinOmega
    let w2 := sin (t * omega) / sinOmega
    { w := w1 * a.w + w2 * b'.w,
      x := w1 * a.x + w2 * b'.x,
      y := w1 * a.y + w2 * b'.y,
      z := w1 * a.z + w2 * b'.z,
      wf_unit := a.wf_unit && b'.wf_unit }

/-- Convert unit quaternion to 3×3 rotation matrix (row-major). -/
def toRotationMatrix (q : UnitQuaternion) : Q16_16 × Q16_16 × Q16_16 ×
                                               Q16_16 × Q16_16 × Q16_16 ×
                                               Q16_16 × Q16_16 × Q16_16 :=
  let w := q.w; let x := q.x; let y := q.y; let z := q.z
  let two := ofNat 2

  let m00 := one - two * (y * y + z * z)
  let m01 := two * (x * y - z * w)
  let m02 := two * (x * z + y * w)

  let m10 := two * (x * y + z * w)
  let m11 := one - two * (x * x + z * z)
  let m12 := two * (y * z - x * w)

  let m20 := two * (x * z - y * w)
  let m21 := two * (y * z + x * w)
  let m22 := one - two * (x * x + y * y)

  (m00, m01, m02, m10, m11, m12, m20, m21, m22)

/-- Check chiral compatibility: D+L→W collapse detection. -/
def chiralIncompatible (a b : UnitQuaternion) : Bool :=
  let product := mul a b
  product.w.val < 0x00008000

/-- Ternary classification from quaternion dot product (SLUG-3 gate). -/
def toTernary (a b : UnitQuaternion) (threshold : Q16_16) : SLUG3.Ternary :=
  let d := dot a b
  if d ≥ threshold then
    SLUG3.Ternary.high
  else if d ≤ neg threshold then
    SLUG3.Ternary.low
  else
    SLUG3.Ternary.mid

/-- Identity carries a unit receipt. -/
theorem identityCarriesUnitWitness : identity.wf_unit = true := by
  rfl

/-- Conjugation preserves the unit receipt. -/
theorem conjugatePreservesWitness (q : UnitQuaternion) : q.conjugate.wf_unit = q.wf_unit := by
  rfl

/-- Multiplication carries the conjunction of input unit receipts. -/
theorem mulWitness (a b : UnitQuaternion) : (a.mul b).wf_unit = (a.wf_unit && b.wf_unit) := by
  rfl

end UnitQuaternion

end Semantics
