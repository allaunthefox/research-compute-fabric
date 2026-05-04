/-
  NonEuclideanGeometry.lean - Parallel Transport Writhe and Path Validation
  Ports rows 135-136 from MATH_MODEL_MAP.tsv (Python → Lean).

  Concept vectors are 14D arrays of Q16.16.
  PHI = golden ratio ≈ 1.6180 = 106039 in Q16.16.
  Window W = 16 points for writhe integral.
-/
import Semantics.Bind
import Semantics.FixedPoint

namespace Semantics.NonEuclideanGeometry

open Q16_16

-- PHI = (1 + √5)/2 ≈ 1.6180339887 → 1.6180 * 65536 = 106039
def phi : Q16_16 := ⟨106039⟩

-- cos(π/4) ≈ 0.7071 → 46341 in Q16.16
def cosQtrPi : Q16_16 := ⟨46341⟩

-- 0.5 in Q16.16
def half : Q16_16 := ⟨32768⟩

-- Oblique projection offset: cos(π/4) * 0.5
def dOblique : Q16_16 := mul cosQtrPi half

-- Row 135: Parallel Transport Writhe
-- Project ND point to oblique 2D: (x + z·dox, y + z·doy), dox=doy=cos(π/4)·0.5
-- Then writhe = Σ(ax·by - ay·bx) / (n-1)
-- Input: array of 3D points represented as (x, y, z) Q16.16 triples
structure Point3 where
  x : Q16_16
  y : Q16_16
  z : Q16_16
deriving Repr, Inhabited, DecidableEq

def obliqueProject (p : Point3) : Q16_16 × Q16_16 :=
  (add p.x (mul p.z dOblique), add p.y (mul p.z dOblique))

def parallelTransportWrithe (history : Array Point3) : Q16_16 :=
  let n := history.size
  if n < 2 then zero
  else
    let projected : Array (Q16_16 × Q16_16) := history.map obliqueProject
    let deltas : Array (Q16_16 × Q16_16) := (Array.range (n - 1)).map fun i =>
      let a := projected[i]!
      let b := projected[i + 1]!
      (sub b.1 a.1, sub b.2 a.2)
    let total := Array.foldl (fun (acc : Q16_16) (i : Nat) =>
      if i + 1 < deltas.size then
        let a := deltas[i]!
        let b := deltas[i + 1]!
        let cross := abs (sub (mul a.1 b.2) (mul a.2 b.1))
        add acc cross
      else acc
    ) zero (Array.range (deltas.size))
    let divisor := (n - 1)
    if divisor == 0 then zero else ⟨total.val / divisor.toUInt32⟩

-- Row 136: NE Path Validation
-- PHI-weighted distance: d = √(Σ w_i · (a_i - b_i)²), w_i = PHI^(-i)
-- Validation thresholds: max_jump > 5.0 → fail; |writhe| > 2.0 → fail

-- PHI^(-i) approximation: PHI^(-i) ≈ (65536/106039)^i in Q16.16
-- Use: w_0=65536, w_i = w_{i-1} * 65536 / 106039
def phiWeights (n : Nat) : Array Q16_16 :=
  (Array.range n).foldl (fun (acc : Array Q16_16 × Q16_16) _ =>
    (acc.1.push acc.2, div acc.2 phi)
  ) (#[], one) |>.1

-- PHI-weighted squared distance (no sqrt — use as ordinal metric)
def phiWeightedDistSq (a b : Array Q16_16) : Q16_16 :=
  let n := Nat.min a.size b.size
  let weights := phiWeights n
  Array.foldl (fun acc i =>
    let diff := abs (sub a[i]! b[i]!)
    let sq := mul diff diff
    add acc (mul weights[i]! sq)
  ) zero (Array.range n)

-- Threshold: 5.0 in Q16.16 = 327680
def maxJumpThreshold : Q16_16 := ⟨327680⟩
-- Writhe bound: 2.0 in Q16.16 = 131072
def maxWrithe : Q16_16 := ⟨131072⟩

inductive PathValidity | Valid | JumpTooLarge | WritheTooLarge | Unstable
  deriving Repr, DecidableEq, Inhabited

def validatePath (pathPoints : Array (Array Q16_16)) (writhe : Q16_16) : PathValidity :=
  -- Check writhe bound
  if writhe.val > maxWrithe.val then PathValidity.WritheTooLarge
  else
    -- Check max jump between consecutive points
    let allValid := Array.range (pathPoints.size - 1) |>.all fun i =>
      let d := phiWeightedDistSq pathPoints[i]! pathPoints[i + 1]!
      d.val ≤ maxJumpThreshold.val
    if allValid then .Valid else PathValidity.JumpTooLarge

-- Geometry invariant and bind
def pathInvariant (pts : Array Point3) : String := s!"nepath[{pts.size}]"

def pathCost (a b : Array Point3) (_m : Metric) : Q16_16 :=
  let wa := parallelTransportWrithe a
  let wb := parallelTransportWrithe b
  Q16_16.ofNat (abs (sub wa wb)).val.toNat

def nEGeomBind (a b : Array Point3) (m : Metric) : Bind (Array Point3) (Array Point3) :=
  geometricBind a b m pathCost pathInvariant pathInvariant

-- Verify
#eval parallelTransportWrithe #[
  Point3.mk ⟨65536⟩ ⟨0⟩ ⟨0⟩,
  Point3.mk ⟨0⟩ ⟨65536⟩ ⟨0⟩,
  Point3.mk ⟨0⟩ ⟨0⟩ ⟨65536⟩
]

end Semantics.NonEuclideanGeometry
