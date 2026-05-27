/-!
# Rainbow Raccoon Compiler Logogram Projection

This module formalizes the small claim proven by the current Python receipt:

* a logogram can be type-admissible as a `LogogramProjection`;
* a torn logogram can be projection-admissible after repair/quarantine;
* the same torn logogram is not merge-admissible.

This is intentionally not a proof that the source mathematics is true. It is a
proof that the routing discipline separates type admission, projection
admission, and merge admission.
-/

namespace Semantics.RRCLogogramProjection

/-- Lawful RRC type-shapes currently used by the shim. -/
inductive RRCShape where
  | signalShapedRouteCompiler
  | projectableGeometryTopology
  | cognitiveLoadField
  | cadForceProbeReceipt
  | logogramProjection
  | holdForUnlawfulOrUnderspecifiedShape
  deriving DecidableEq, Repr

/-- RRC witness status. `candidate` is not a proof; it only admits next-stage checks. -/
inductive WitnessStatus where
  | candidate
  | hold
  deriving DecidableEq, Repr

/-- Semantic topology regime for a compiled logogram. -/
inductive SemanticRegime where
  | beautifulTopologicalFolding
  | uglyAsymmetricPruning
  | horribleManifoldTearing
  deriving DecidableEq, Repr

/-- Projection lane chosen after semantic-regime gating. -/
inductive ProjectionLane where
  | normalProjection
  | quarantineProjection
  deriving DecidableEq, Repr

/-- Receipt core for one compiled logogram projection. -/
structure LogogramReceipt where
  shape : RRCShape
  status : WitnessStatus
  regime : SemanticRegime
  payloadBound : Bool
  contradictionWitness : Bool
  tearBoundary : Bool
  detachedMass : Bool
  residualLane : Bool
  deriving Repr

/-- A tear is repaired only when it has all quarantine evidence. -/
def hasTearRepair (r : LogogramReceipt) : Bool :=
  r.contradictionWitness && r.tearBoundary && r.detachedMass && r.residualLane

/-- Type admission: the object has the RRC logogram shape and bounded payload. -/
def typeAdmissible (r : LogogramReceipt) : Bool :=
  r.shape == RRCShape.logogramProjection &&
  r.status == WitnessStatus.candidate &&
  r.payloadBound

/-- Merge admission: only non-tearing logogram projections may enter ordinary merge space. -/
def mergeAdmissible (r : LogogramReceipt) : Bool :=
  typeAdmissible r &&
  r.regime != SemanticRegime.horribleManifoldTearing

/-- Projection admission: non-tears project normally; repaired tears project into quarantine. -/
def projectionAdmissible (r : LogogramReceipt) : Bool :=
  typeAdmissible r &&
  (r.regime != SemanticRegime.horribleManifoldTearing || hasTearRepair r)

/-- Lane choice is a pure function of the semantic regime. -/
def projectionLane (r : LogogramReceipt) : ProjectionLane :=
  if r.regime == SemanticRegime.horribleManifoldTearing then
    ProjectionLane.quarantineProjection
  else
    ProjectionLane.normalProjection

/-- The repaired `semantic_tear` receipt from the Python bridge, abstracted to booleans. -/
def semanticTearReceipt : LogogramReceipt :=
  { shape := RRCShape.logogramProjection
    status := WitnessStatus.candidate
    regime := SemanticRegime.horribleManifoldTearing
    payloadBound := true
    contradictionWitness := true
    tearBoundary := true
    detachedMass := true
    residualLane := true }

/-- An ordinary logogram projection with no tear. -/
def ordinaryLogogramReceipt : LogogramReceipt :=
  { shape := RRCShape.logogramProjection
    status := WitnessStatus.candidate
    regime := SemanticRegime.uglyAsymmetricPruning
    payloadBound := true
    contradictionWitness := false
    tearBoundary := false
    detachedMass := false
    residualLane := false }

/-- A torn logogram with no repair evidence remains projection-inadmissible. -/
def unrepairedTearReceipt : LogogramReceipt :=
  { shape := RRCShape.logogramProjection
    status := WitnessStatus.candidate
    regime := SemanticRegime.horribleManifoldTearing
    payloadBound := true
    contradictionWitness := false
    tearBoundary := false
    detachedMass := false
    residualLane := false }

/-! ## Executable theorem witnesses -/

theorem semantic_tear_projects_after_repair :
    projectionAdmissible semanticTearReceipt = true := by
  decide

theorem semantic_tear_does_not_merge :
    mergeAdmissible semanticTearReceipt = false := by
  decide

theorem semantic_tear_uses_quarantine_lane :
    projectionLane semanticTearReceipt = ProjectionLane.quarantineProjection := by
  decide

theorem unrepaired_tear_does_not_project :
    projectionAdmissible unrepairedTearReceipt = false := by
  decide

theorem ordinary_logogram_projects_and_merges :
    projectionAdmissible ordinaryLogogramReceipt = true ∧
    mergeAdmissible ordinaryLogogramReceipt = true ∧
    projectionLane ordinaryLogogramReceipt = ProjectionLane.normalProjection := by
  decide

/-- Any merge-admissible logogram is also projection-admissible. -/
theorem merge_implies_projection (r : LogogramReceipt) :
    mergeAdmissible r = true -> projectionAdmissible r = true := by
  unfold mergeAdmissible projectionAdmissible
  intro h
  cases hType : typeAdmissible r
  · simp [hType] at h
  · cases hRegime : (r.regime != SemanticRegime.horribleManifoldTearing)
    · simp [hType, hRegime] at h
    · exact rfl

/-- A repaired tear is projection-admissible but not merge-admissible. -/
theorem repaired_tear_separates_projection_from_merge
    (r : LogogramReceipt)
    (hType : typeAdmissible r = true)
    (hTear : r.regime = SemanticRegime.horribleManifoldTearing)
    (hRepair : hasTearRepair r = true) :
    projectionAdmissible r = true ∧ mergeAdmissible r = false := by
  constructor
  · unfold projectionAdmissible
    simp [hType, hTear, hRepair]
  · unfold mergeAdmissible
    simp [hType, hTear]

/-! ## Eval witnesses for script/readback use. -/

-- semanticTearReceipt: repaired tear, logogram type → admissible for projection, not merge, normal lane
#eval projectionAdmissible semanticTearReceipt   -- expect: true
#eval mergeAdmissible semanticTearReceipt        -- expect: false
#eval projectionLane semanticTearReceipt         -- expect: Semantics.RRCLogogramProjection.ProjectionLane.quarantineProjection
-- unrepairedTearReceipt: unrepaired tear → not admissible for projection
#eval projectionAdmissible unrepairedTearReceipt -- expect: false
-- ordinaryLogogramReceipt: no tear → merge admissible
#eval mergeAdmissible ordinaryLogogramReceipt    -- expect: true

end Semantics.RRCLogogramProjection
