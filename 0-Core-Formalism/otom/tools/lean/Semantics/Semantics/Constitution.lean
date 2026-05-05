/-
Project: OTOM
Domain: axis-04-formalization
Type: LeanModule
Settlement: FORMING
Authority: canonical
Route: otom/axis-04-formalization/leanmodule/constitution/v0
-/

import Semantics.Plumbing.Artifact
import Semantics.Plumbing.Route
import Semantics.Plumbing.FAMMUpdate
import Semantics.Graph
import Semantics.Graph.Diff
import Semantics.Graph.Torsion
import Semantics.FAMM
import Semantics.RGFlow
import Semantics.VisualPrimitive

namespace Semantics.Constitution

/-- Repository-level invariant: artifacts route before mutation. -/
def artifactFirstInvariant : Prop := True

/-- FORMING marker for the bootstrap constitution. -/
def settlementState : String := "FORMING"

/-- Visual primitives are now part of the canonical witness surface. -/
def visualPrimitiveWitnessSurface : Prop := True

end Semantics.Constitution
