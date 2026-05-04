import Semantics.FixedPoint

namespace Semantics.Foundations

open Semantics
open Semantics.Q16_16

/-! # F03: Hierarchical Entropy Decomposition
    H_hier = Σ w_i H_i
-/

def hierarchicalEntropy (weights : List Q16_16) (entropies : List Q16_16) : Q16_16 :=
  (weights.zip entropies).foldl (fun acc (w, h) =>
    acc + (w * h)
  ) zero

#eval hierarchicalEntropy [half, half] [one, zero]
-- Expected: 0.5 (32768)

end Semantics.Foundations
