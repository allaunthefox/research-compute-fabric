import Semantics.FixedPoint

namespace Semantics.Foundations

open Semantics
open Semantics.Q16_16

/-! # F02: Information Content Measurement
    I(x) = -log2(p(x))
-/

/-- Compute information content for a single probability value. -/
def informationContent (p : Q16_16) : Q16_16 :=
  if p.toInt ≤ 0 then maxVal
  else zero - log2 p

/-- Witness: Information of a coin flip (p=0.5) should be 1.0. -/
#eval informationContent half
-- Expected: ~1.0

/-- Witness: Information of a rare event (p=0.01). -/
def rareEvent : Q16_16 := ⟨655⟩ -- ~0.01

#eval informationContent rareEvent
-- Expected: ~6.64

end Semantics.Foundations
