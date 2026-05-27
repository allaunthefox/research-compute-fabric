-- AVM ISA v1 (Lean-only): Values
-- Values are strictly typed; no dynamic Any.

import Semantics.AVMIsa.Types
import Semantics.FixedPoint

namespace Semantics.AVMIsa

/-- Typed value payload. -/
inductive AvmVal : AvmTy → Type where
  | q0 : Semantics.Q0_16 → AvmVal AvmTy.q0_16
  | q16 : Semantics.Q16_16 → AvmVal AvmTy.q16_16
  | b : Bool → AvmVal AvmTy.bool
  deriving Repr

/-- Existential wrapper for storing values in an untyped container.

We use this in the ISA skeleton to keep the state representation simple.
Typing is enforced by an explicit type-check pass and by instruction semantics
that can reject ill-typed stacks.

Later upgrade path: replace with a fully typed stack representation.
-/
structure AnyVal where
  ty : AvmTy
  val : AvmVal ty

instance : Inhabited AnyVal where
  default := { ty := AvmTy.bool, val := AvmVal.b false }

instance : Repr AnyVal where
  reprPrec v _ := repr v.val

end Semantics.AVMIsa
