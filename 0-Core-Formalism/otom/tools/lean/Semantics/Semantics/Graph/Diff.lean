/-
Project: GraphPlumbing
Domain: axis-11-geometry
Type: LeanModule
Settlement: FORMING
Authority: canonical
Route: graph-plumbing/axis-11-geometry/leanmodule/graph-diff/v0
-/

import Semantics.Graph

namespace Semantics.Graph

inductive GraphOp where
  | addNode    : String → String → GraphOp
  | removeNode : String → GraphOp
  | addEdge    : String → String → String → GraphOp
  | removeEdge : String → String → GraphOp
  | relabel    : String → String → GraphOp
  | retype     : String → String → GraphOp
  deriving Repr, DecidableEq

structure GraphDiff where
  beforeHash : String
  afterHash  : String
  ops        : List GraphOp
  deriving Repr

end Semantics.Graph
