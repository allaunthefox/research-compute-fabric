import Semantics.FixedPoint

namespace Semantics.Foundations

open Semantics
open Semantics.Q16_16

/-! # F06: Net Energy Balance Threshold
    E_balance = E_gain - E_cost
-/

def energyBalance (gain cost : Q16_16) : Q16_16 :=
  gain - cost

#eval energyBalance ⟨100 * 65536⟩ ⟨80 * 65536⟩
-- Expected: 20.0

end Semantics.Foundations
