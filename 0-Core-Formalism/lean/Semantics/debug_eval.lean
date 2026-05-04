import Semantics.FixedPoint
open Semantics

namespace CoarseGraining

def coarseGrainFactor (loopIter : Nat) (maxLoops : Nat) : Q16_16 :=
  if maxLoops = 0 then Q16_16.one
  else if loopIter >= maxLoops then Q16_16.ofFloat 0.5  -- Minimum 50% precision
  else
    let ratio := Q16_16.ofNat loopIter / Q16_16.ofNat maxLoops
    let factor := Q16_16.one - (ratio * Q16_16.ofFloat 0.5)  -- Linear decay to 50%
    Q16_16.max (Q16_16.ofFloat 0.5) factor

end CoarseGraining

#eval CoarseGraining.coarseGrainFactor 5 10
