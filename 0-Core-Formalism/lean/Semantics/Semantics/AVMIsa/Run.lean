-- AVM ISA v1 (Lean-only): Run semantics (fuel-bounded)

import Semantics.AVMIsa.Step

namespace Semantics.AVMIsa

/-- Fuel for total execution. -/
abbrev Fuel := Nat

/-- Fuel-bounded run.

Stops when:
- fuel exhausted
- machine halted
- an error occurs
-/
def run (fuel : Fuel) (program : List Instr) (s : State) : Outcome State :=
  match fuel with
  | 0 => Outcome.ok s
  | Nat.succ f =>
      if s.halted then Outcome.ok s
      else
        match step program s with
        | Outcome.err e => Outcome.err e
        | Outcome.ok s1 => run f program s1

/-- Canary: boolean not.

#eval should produce `true` on top of stack.
-/
def canaryNot : List Instr :=
  [
    Instr.push ⟨AvmTy.bool, AvmVal.b false⟩,
    Instr.prim Prim.not,
    Instr.halt
  ]

/-- Canary initial state. -/
def canaryState : State :=
  { pc := 0, stack := [], locals := [], halted := false }

#eval run 8 canaryNot canaryState

end Semantics.AVMIsa
