-- AVM ISA v1 (Lean-only): State

import Semantics.AVMIsa.Instr

namespace Semantics.AVMIsa

/-- Machine state.

This is intentionally minimal in v1. It is sufficient to define a total `run`
with fuel.
-/
structure State where
  pc : Nat
  stack : List AnyVal
  locals : List (Option AnyVal)
  halted : Bool

deriving Inhabited

/-- Safe locals lookup (returns `none` when out of bounds). -/
def getLocal? (s : State) (i : Nat) : Option AnyVal :=
  s.locals.getD i none

/-- Safe locals set (no-op when out of bounds). -/
def setLocal (s : State) (i : Nat) (v : AnyVal) : State :=
  if h : i < s.locals.length then
    { s with locals := s.locals.set ⟨i, h⟩ (some v) }
  else
    s

end Semantics.AVMIsa
