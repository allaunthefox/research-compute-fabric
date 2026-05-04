/-
  CanonicalInterval.lean - Fixed-Point Canonical Interval Arithmetic
-/

import Semantics.DynamicCanal

namespace Semantics.CanonicalInterval

open DynamicCanal

abbrev Scalar := Fix16

structure CanonicalInterval where
  width : Scalar
  a : Scalar
  b : Scalar
  k : UInt32
  deriving Repr, DecidableEq

def canonicalIntervalInvariant (interval : CanonicalInterval) : Prop :=
  interval.width.raw = (Fix16.add interval.a interval.b).raw

end Semantics.CanonicalInterval
