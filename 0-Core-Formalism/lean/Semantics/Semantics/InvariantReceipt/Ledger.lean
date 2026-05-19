-- Invariant Receipt Protocol: Cost ledger and deterministic tracking
-- Constitutional layer: compiles clean

namespace InvariantReceipt

structure CostEntry where
  cost  : Int
  entry : String
  deriving Inhabited

def Ledger : Type := List CostEntry

def deterministic (l : Ledger) : Prop :=
  ∀ entry : CostEntry, List.Mem entry (l : List CostEntry) → entry.cost ≥ 0

end InvariantReceipt
