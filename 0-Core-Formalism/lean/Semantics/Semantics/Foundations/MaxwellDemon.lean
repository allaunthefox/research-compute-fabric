import Semantics.FixedPoint

namespace Semantics.Foundations

open Semantics
open Semantics.Q16_16

/-! # F07: Maxwell-Demon Recovery Ratio
    η_demon = E_recovered / (k_B * T * I)
-/

def maxwellDemonRecovery (eRecovered temp info : Q16_16) : Q16_16 :=
  let kB : Q16_16 := ⟨6⟩
  let denom := kB * temp * info
  if denom.toInt ≤ 0 then zero
  else eRecovered / denom

#eval maxwellDemonRecovery ⟨10 * 65536⟩ ⟨300 * 65536⟩ ⟨1 * 65536⟩

end Semantics.Foundations
