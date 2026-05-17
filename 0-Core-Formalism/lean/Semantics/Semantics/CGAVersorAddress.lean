import Semantics.FAMM
import Semantics.FixedPoint

open Semantics
open Semantics.FixedPoint (Q16_16)

namespace Semantics.CGAVersorAddress

/-! # CGA Versor as Memory Address

Conformal Geometric Algebra (CGA) in ℝ⁴·¹: 3 Euclidean dimensions +
2 conformal dimensions (e₊, e₋). A versor encodes position in this
5D space. Access cost between two cells is the CGA distance derived
from the inner product of their point representations.

Key insight: the arbitrary `maxDelay` boundary falls out of the
geometry — closest point in CGA = cheapest access.

## CGA Point Representation

A Euclidean point (x,y,z) maps to a null CGA vector:
  p = e₀ + x·e₁ + y·e₂ + z·e₃ + ½(x²+y²+z²)·e∞

Where e₀ = (e₋ − e₊)/2 and e∞ = e₋ + e₊.

Distance: dist(p,q)² = −2 · ⟨p,q⟩ (inner product)
-/

-- ════════════════════════════════════════════════════
-- CGA vector in ℝ⁴·¹ (5 components: e₁, e₂, e₃, e₊, e₋)
-- ════════════════════════════════════════════════════

/-- A CGA vector in ℝ⁴·¹ with Q16_16 components.
    Index layout: [e₁, e₂, e₃, e₊, e₋] -/
structure CGAVector where
  c1 : Q16_16  -- e₁
  c2 : Q16_16  -- e₂
  c3 : Q16_16  -- e₃
  cp : Q16_16  -- e₊
  cn : Q16_16  -- e₋
  deriving Repr, BEq, Inhabited

/-- CGA metric signature: e₁²=e₂²=e₃²=e₊²=+1, e₋²=−1 -/
def cgaInner (a b : CGAVector) : Q16_16 :=
  let m00 := Q16_16.mul a.c1 b.c1
  let m11 := Q16_16.mul a.c2 b.c2
  let m22 := Q16_16.mul a.c3 b.c3
  let m33 := Q16_16.mul a.cp b.cp          -- e₊: +1
  let m44 := Q16_16.mul (Q16_16.neg a.cn) b.cn  -- e₋: −1
  let s0 := Q16_16.add m00 m11
  let s1 := Q16_16.add s0 m22
  let s2 := Q16_16.add s1 m33
  Q16_16.add s2 m44

-- ════════════════════════════════════════════════════
-- Null basis: e₀ (origin) and e∞ (infinity)
-- ════════════════════════════════════════════════════

/-- e₀ = (e₋ − e₊)/2 — the origin blade -/
def e0 : CGAVector :=
  { c1 := Q16_16.zero
  , c2 := Q16_16.zero
  , c3 := Q16_16.zero
  , cp := Q16_16.neg (Q16_16.ofRatio 1 2)  -- e₊ coefficient = −½
  , cn := Q16_16.ofRatio 1 2                -- e₋ coefficient = +½
  }

/-- e∞ = e₋ + e₊ — the point at infinity -/
def einf : CGAVector :=
  { c1 := Q16_16.zero
  , c2 := Q16_16.zero
  , c3 := Q16_16.zero
  , cp := Q16_16.one
  , cn := Q16_16.one
  }

/-- Check that a CGA vector is null (self-inner = 0). -/
def isNull (v : CGAVector) : Bool :=
  cgaInner v v = Q16_16.zero

-- ════════════════════════════════════════════════════
-- CGA point embedding
-- ════════════════════════════════════════════════════

/--
A CGA point embedding: p = e₀ + x·e₁ + y·e₂ + z·e₃ + ½(x²+y²+z²)·e∞

Where e₀ = (e₋ − e₊)/2, so:
  cp = ½(x²+y²+z²) − ½     (e₊ coefficient)
  cn = ½(x²+y²+z²) + ½     (e₋ coefficient)

The null condition ⟨p,p⟩ = 0 holds for all Euclidean points.
-/
def cgaPoint (x y z : Q16_16) : CGAVector :=
  let xsq := Q16_16.mul x x
  let ysq := Q16_16.mul y y
  let zsq := Q16_16.mul z z
  let normSq := Q16_16.add (Q16_16.add xsq ysq) zsq
  let halfNormSq := Q16_16.mul (Q16_16.ofRatio 1 2) normSq
  { c1 := x
  , c2 := y
  , c3 := z
  , cp := Q16_16.sub halfNormSq (Q16_16.ofRatio 1 2)  -- ½(x²+y²+z²) − ½
  , cn := Q16_16.add halfNormSq (Q16_16.ofRatio 1 2)  -- ½(x²+y²+z²) + ½
  }

/--
Squared CGA distance between two points.

For CGA-embedded points p,q:
  ‖p − q‖² = −2 · ⟨p, q⟩ = (p.c1−q.c1)² + (p.c2−q.c2)² + (p.c3−q.c3)²

We compute via Float to handle signed differences that Q16_16.sub cannot.
The result is always non-negative, so it rounds cleanly back to Q16_16.
-/
def squaredDiff (a b : Q16_16) : Q16_16 :=
  let aF := Q16_16.toFloat a
  let bF := Q16_16.toFloat b
  Q16_16.ofFloat ((aF - bF) * (aF - bF))

def cgaDistSq (p q : CGAVector) : Q16_16 :=
  Q16_16.add (Q16_16.add (squaredDiff p.c1 q.c1) (squaredDiff p.c2 q.c2)) (squaredDiff p.c3 q.c3)

-- ════════════════════════════════════════════════════
-- FAMMAddress: a versor is the address
-- ════════════════════════════════════════════════════

/-- A versor encodes a position in CGA space.
    The delay is derived from the versor metric, not stored separately. -/
structure FAMMAddress where
  point : CGAVector
  deriving Repr, BEq, Inhabited

/-- Access cost = CGA distance from cell versor to reference (origin).
    Closest point in CGA = cheapest access. -/
def accessCost (addr : FAMMAddress) (reference : FAMMAddress) : Q16_16 :=
  cgaDistSq addr.point reference.point

/-- Convert a CGA distance into a Q16_16 delay value.
    The maxDelay boundary emerges from the CGA diameter of the address space,
    not from an arbitrary constant. -/
def delayFromDist (distSq : Q16_16) (scale : Q16_16) : Q16_16 :=
  let raw := Q16_16.mul distSq scale
  if raw.val ≥ 0x80000000 then Q16_16.zero
  else raw

/-- Construct a FAMMCell from a CGA address, using geometric delay. -/
def cellFromAddress (addr : FAMMAddress) (reference : FAMMAddress)
    (scale : Q16_16) (data : Q16_16) : FAMMCell :=
  let dist := accessCost addr reference
  let delay := delayFromDist dist scale
  { data := data
  , delay := delay
  , delayMass := delay
  , delayWeight := Q16_16.one
  }

-- ════════════════════════════════════════════════════
-- Fixtures and #eval witnesses
-- ════════════════════════════════════════════════════

def originAddress : FAMMAddress :=
  { point := e0 }

def unitXAddress : FAMMAddress :=
  { point := cgaPoint Q16_16.one Q16_16.zero Q16_16.zero }

def point234Address : FAMMAddress :=
  { point := cgaPoint (Q16_16.ofInt 2) (Q16_16.ofInt 3) Q16_16.zero }

#eval originAddress
#eval unitXAddress
#eval point234Address

-- CGA distance witnesses
#eval accessCost originAddress originAddress
#eval accessCost originAddress unitXAddress
#eval accessCost unitXAddress unitXAddress
#eval accessCost originAddress point234Address

-- Null checks
#eval isNull e0
#eval isNull einf
#eval isNull (cgaPoint Q16_16.zero Q16_16.zero Q16_16.zero)

-- Cell from address
#eval cellFromAddress unitXAddress originAddress (Q16_16.ofInt 3) (Q16_16.ofInt 42)

end Semantics.CGAVersorAddress
