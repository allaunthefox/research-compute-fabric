/-
Project: GraphPlumbing
Domain: axis-11-geometry
Type: LeanModule
Settlement: FORMING
Authority: canonical
Route: graph-plumbing/axis-11-geometry/leanmodule/graph/v0
-/

namespace Semantics.Graph

inductive NodeKind where
  | artifact
  | proof
  | route
  | famm
  | memory
  | evidence
  | projection
  deriving Repr, DecidableEq

structure Node where
  id    : String
  kind  : NodeKind
  label : String
  deriving Repr, DecidableEq

structure Edge where
  src   : String
  dst   : String
  label : String
  deriving Repr, DecidableEq

structure Graph where
  nodes : List Node
  edges : List Edge
  deriving Repr

end Semantics.Graph
