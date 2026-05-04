import Semantics.FixedPoint

namespace Semantics.Foundations

open Semantics
open Semantics.Q16_16

/-! # F04: Carnot Efficiency
    η = 1 - T_cold / T_hot
-/

def carnotEfficiency (tCold tHot : Q16_16) : Q16_16 :=
  if tHot.toInt ≤ 0 then zero
  else one - (tCold / tHot)

#eval carnotEfficiency ⟨300 * 65536⟩ ⟨400 * 65536⟩
-- Expected: 0.25 (16384)

end Semantics.Foundations
