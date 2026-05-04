import Semantics.FixedPoint

namespace Semantics.Foundations

open Semantics
open Semantics.Q16_16

/-! # F01: Shannon Local Conditional Entropy
    H(X) = -Σ p_i log2(p_i)
-/

/-- Compute Shannon Entropy for a probability distribution.
    Assumes probabilities sum to 1.0. -/
def shannonEntropy (probs : List Q16_16) : Q16_16 :=
  probs.foldl (fun acc p =>
    if p.toInt ≤ 0 then acc
    else acc - (p * log2 p)
  ) zero

/-- Witness: Entropy of a fair coin flip (p=0.5, p=0.5) should be 1.0. -/
def fairCoin : List Q16_16 := [half, half]

#eval shannonEntropy fairCoin
-- Expected: ~1.0 (65536 in raw)

/-- Witness: Entropy of a certain event (p=1.0) should be 0.0. -/
def certainEvent : List Q16_16 := [one]

#eval shannonEntropy certainEvent
-- Expected: 0.0

end Semantics.Foundations
