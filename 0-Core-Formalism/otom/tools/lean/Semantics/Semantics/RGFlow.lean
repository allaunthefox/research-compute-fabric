/-
Project: OTOM
Domain: axis-11-geometry
Type: LeanModule
Settlement: FORMING
Authority: canonical
Route: otom/axis-11-geometry/leanmodule/rgflow/v0
-/

namespace Semantics.RGFlow

structure AdmissibilityGate where
  routeSignature : String
  threshold      : Nat
  score          : Nat
  deriving Repr, DecidableEq

def passes (g : AdmissibilityGate) : Bool :=
  g.score >= g.threshold

end Semantics.RGFlow
