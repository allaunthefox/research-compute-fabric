/-
  CanonicalInterval.lean - Fixed-Point Canonical Interval Arithmetic
-/

import Semantics.FixedPoint

set_option linter.dupNamespace false

namespace Semantics.CanonicalInterval

open Semantics.Q16_16

abbrev Scalar := Q16_16

structure CanonicalInterval where
  width : Scalar
  a : Scalar
  b : Scalar
  k : UInt32
  deriving Repr, DecidableEq

def canonicalIntervalInvariant (interval : CanonicalInterval) : Prop :=
  interval.width.val = (interval.a + interval.b).val

end Semantics.CanonicalInterval
