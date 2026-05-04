/-
Project: GraphPlumbing
Domain: axis-11-geometry
Type: LeanModule
Settlement: FORMING
Authority: canonical
Route: graph-plumbing/axis-11-geometry/leanmodule/torsion/v0
-/

import Semantics.Graph.Diff

namespace Semantics.Graph

structure TorsionScore where
  contradictionPressure : Nat
  routeInstability      : Nat
  adapterMismatch       : Nat
  authorityConflict     : Nat
  compressionDeltaAbs   : Nat
  total                 : Nat
  deriving Repr, DecidableEq

def zeroTorsion : TorsionScore :=
  { contradictionPressure := 0
    routeInstability := 0
    adapterMismatch := 0
    authorityConflict := 0
    compressionDeltaAbs := 0
    total := 0 }

end Semantics.Graph
