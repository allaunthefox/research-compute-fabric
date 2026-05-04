/-
  ComputationProfile.lean - Minimal stub
-/

import Semantics.DynamicCanal

namespace Semantics.ComputationProfile

open DynamicCanal

abbrev Scalar := Fix16

structure ComputationProfile where
  parallelism : Scalar
  memoryAccess : Scalar
  branching : Scalar
  deriving Repr, DecidableEq

end Semantics.ComputationProfile
