-- Invariant Receipt Protocol: Substrate adapter with round-trip law
-- Constitutional layer: compiles clean, Th2 proven

import InvariantReceipt.Core

namespace InvariantReceipt

structure SubstrateAdapter (M : ModelUpgrade S Sc P) where
  target      : String
  TargetState : Type
  toTarget    : S → TargetState
  fromTarget  : TargetState → S
  roundTrip   : ∀ s, M.invariant s → fromTarget (toTarget s) = s

end InvariantReceipt
