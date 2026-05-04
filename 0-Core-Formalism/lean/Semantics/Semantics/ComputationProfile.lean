/-
  ComputationProfile.lean - Minimal stub
-/

import Mathlib.Data.Nat.Basic
import Mathlib.Data.Int.Basic
import Semantics.DynamicCanal
import Semantics.FixedPoint

namespace Semantics.ComputationProfile

open DynamicCanal
open Semantics.Q16_16

abbrev Scalar := Q16_16

structure Profile where
  parallelism : Scalar
  memoryAccess : Scalar
  branching : Scalar
  deriving Repr, DecidableEq

end Semantics.ComputationProfile
