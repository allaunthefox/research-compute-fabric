/-
Project: FAMM
Domain: axis-03-neural
Type: LeanModule
Settlement: FORMING
Authority: canonical
Route: famm/axis-03-neural/leanmodule/famm/v0
-/

namespace Semantics.FAMM

inductive RouteMemoryKind where
  | success
  | partial
  | failed
  | held
  deriving Repr, DecidableEq

structure RouteMemory where
  routeSignature : String
  kind           : RouteMemoryKind
  pressure       : Nat
  note           : String
  deriving Repr, DecidableEq

end Semantics.FAMM
