/-
Project: GraphPlumbing
Domain: axis-04-formalization
Type: LeanModule
Settlement: FORMING
Authority: canonical
Route: graph-plumbing/axis-04-formalization/leanmodule/famm-update/v0
-/

import Semantics.Plumbing.Artifact
import Semantics.Plumbing.Route

namespace Semantics.Plumbing

inductive FammEffect where
  | noChange
  | strengthenBasin : String → FammEffect
  | weakenBasin     : String → FammEffect
  | createScar      : String → FammEffect
  | createHold      : String → FammEffect
  | quarantineSignal : String → FammEffect
  deriving Repr, DecidableEq

structure FammUpdate where
  artifactId : String
  effect     : FammEffect
  reason     : String
  deriving Repr

def canEmitFammUpdate (a : ArtifactRecord) : Bool :=
  mayUpdateFAMM a

end Semantics.Plumbing
