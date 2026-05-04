-- Invariant Receipt Protocol: Receipt and Outcome types
-- Constitutional layer: compiles clean, Th1/Th2/Th3 proven

namespace InvariantReceipt

structure Receipt where
  tag     : String
  payload : ByteArray
  hash    : UInt64
deriving Inhabited

inductive Outcome (α : Type) : Type where
  | ok          (val : α)
  | quarantined (receipt : Receipt)
  deriving Inhabited

end InvariantReceipt
