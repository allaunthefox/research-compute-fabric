-- AVM ISA v1 (Lean-only): Types
-- Core rule: closed-world finite type universe; no Float.

import Semantics.FixedPoint

namespace Semantics.AVMIsa

/-- Finite AVM type universe. Closed-world; extend only by adding constructors. -/
inductive AvmTy : Type where
  | q0_16 : AvmTy
  | q16_16 : AvmTy
  | bool : AvmTy
  deriving DecidableEq, BEq, Inhabited, Repr

end Semantics.AVMIsa
