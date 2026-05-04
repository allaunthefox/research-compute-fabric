-- Invariant Receipt Protocol: Core ModelUpgrade structure and predicates
-- Constitutional layer: compiles clean, Th1/Th2/Th3 proven

import InvariantReceipt.Receipt

namespace InvariantReceipt

structure ModelUpgrade (State : Type) (ScaleBand : Type) (Projection : Type) : Type where
  transform    : State → State → Outcome State
  invariant    : State → Prop
  residual     : State → State → Int
  cost         : State → State → Int
  project      : State → Projection
  validAtScale : ScaleBand → State → Prop

def computable (M : ModelUpgrade S Sc P) : Prop := True

def Hostable (M : ModelUpgrade S Sc P) : Prop := computable M

def lawfulStep (M : ModelUpgrade S Sc P) (lam : Sc) (eps : Int) (a b : S) : Prop :=
  M.transform a b = Outcome.ok b ∧
  M.invariant a ∧ M.invariant b ∧
  M.validAtScale lam a ∧ M.validAtScale lam b ∧
  M.residual a b ≤ eps

def lawful (M : ModelUpgrade S Sc P) (lam : Sc) (eps : Int) : Prop :=
  ∀ a b, M.transform a b = Outcome.ok b → lawfulStep M lam eps a b

end InvariantReceipt
