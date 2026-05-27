-- AVM ISA v1 (Lean-only): Instructions
-- Closed-world opcodes. No CALL/IMPORT. No string dispatch.

import Semantics.AVMIsa.Value

namespace Semantics.AVMIsa

/-- Finite primitive set (closed-world).

If extensibility is needed, add a constructor here and define its semantics in Lean.
Backends must implement the same semantics.
-/
inductive Prim : Type where
  | addSatQ0
  | subSatQ0
  | addSatQ16
  | subSatQ16
  | and
  | or
  | not
  deriving DecidableEq, BEq, Inhabited, Repr

/-- Core instruction set.

`load`/`store` use `Nat` indices in this v1 skeleton.
Strict implementations SHOULD replace them with `Fin n` once the local-frame
size is part of `Program`.
-/
inductive Instr : Type where
  | push : AnyVal → Instr
  | pop : Instr
  | dup : Instr
  | swap : Instr
  | load : Nat → Instr
  | store : Nat → Instr
  | jump : Nat → Instr
  | jumpIf : Nat → Instr
  | prim : Prim → Instr
  | halt : Instr
  deriving Inhabited, Repr

end Semantics.AVMIsa
