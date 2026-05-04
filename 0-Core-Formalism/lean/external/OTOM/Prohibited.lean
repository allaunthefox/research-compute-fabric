import Semantics.Constitution

namespace Semantics.ENE

/-!
# Prohibitions: What is NOT allowed in the ENE model

This module defines the negative space of the semantic universe:
every structure, transition, and collapse that violates the
constitutional membrane is explicitly ruled out.
-/

-- ============================================================================
-- 1. SEMANTIC PROHIBITIONS
-- ============================================================================

/-- A lemma without semantic atoms is not allowed.
Every meaning-bearing object must decompose into atoms. -/
def NotAllowed_EmptyLemma (l : Lemma) : Prop :=
  l.sig = []

/-- A decomposition that does not match its lemma's signature is not allowed. -/
def NotAllowed_UnfaithfulDecomposition (l : Lemma) (d : AtomicDecomposition) : Prop :=
  ¬FaithfulDecomposition l d

/-- UInt32 weights are always non-negative, so this check is vacuous. Kept for API compatibility. -/
def NotAllowed_NegativeWeightInNormalForm (_wa : WeightedAtom) : Prop :=
  False

-- ============================================================================
-- 2. GRAPH PROHIBITIONS
-- ============================================================================

/-- A graph containing active quarantined edges (positive weight) is not allowed. -/
def NotAllowed_ActiveQuarantine (g : Graph) : Prop :=
  ¬g.noActiveQuarantine

/-- An observation node with no outgoing projection edge is not allowed. -/
def NotAllowed_OrphanObservation (g : Graph) (n : Node) : Prop :=
  n.type = NodeType.observation ∧ ¬(∃ e ∈ g.edges, e.source = n ∧ e.type = EdgeType.projects_to)

/-- An edge that claims capability-bearing status without justification is not allowed. -/
def NotAllowed_UncertifiedCapabilityEdge (e : Edge) : Prop :=
  e.edgeClass = EdgeClass.capabilityBearing ∧ e.justified = false

-- ============================================================================
-- 3. PATH PROHIBITIONS
-- ============================================================================

/-- A "magic semantic jump" — a path step that is not locally admissible — is not allowed. -/
def NotAllowed_MagicSemanticJump (step : AtomicStep) : Prop :=
  step.rewrite.locallyAdmissible = false

/-- A non-lawful path is not allowed. -/
def NotAllowed_UnlawfulPath (p : AtomicPath) : Prop :=
  ¬p.isLawful

/-- Connecting two paths whose endpoints do not match is not allowed. -/
def NotAllowed_DisconnectedPathComposition (p1 p2 : AtomicPath) : Prop :=
  ¬(AtomicPath.canCompose p1 p2)

-- ============================================================================
-- 4. WITNESS / CONSTITUTION PROHIBITIONS
-- ============================================================================

/-- A witness without provenance is not allowed. -/
def NotAllowed_WitnessWithoutProvenance (w : Witness) : Prop :=
  ¬(w.receipt.provenance = WitnessProvenance.observation ∨
    w.receipt.provenance = WitnessProvenance.inference ∨
    w.receipt.provenance = WitnessProvenance.projection ∨
    w.receipt.provenance = WitnessProvenance.evolution ∨
    w.receipt.provenance = WitnessProvenance.translation ∨
    w.receipt.provenance = WitnessProvenance.composed)

/-- Negative accumulated load is not allowed. -/
def NotAllowed_NegativeLoad (w : Witness) : Prop :=
  w.accumulatedLoad < 0.0

/-- A node that is not grounded in atoms is not allowed. -/
def NotAllowed_UngroundedNode (g : Groundedness) : Prop :=
  g.atomicBasis = false

/-- A node whose universality class is invisible is not allowed. -/
def NotAllowed_InvisibleUniversality (g : Groundedness) : Prop :=
  g.classMembershipVisible = false

-- ============================================================================
-- 5. UNIVERSALITY PROHIBITIONS
-- ============================================================================

/-- Losing universality-class identity under projection is not allowed. -/
def NotAllowed_UniversalityLossUnderProjection (cd : ClassifiedDynamics) : Prop :=
  ¬projectionPreservesUniversality cd

/-- Losing universality-class identity under scalar collapse is not allowed. -/
def NotAllowed_UniversalityLossUnderCollapse (cd : ClassifiedDynamics) : Prop :=
  ¬collapsePreservesUniversality cd

/-- Losing universality-class identity under evolution is not allowed. -/
def NotAllowed_UniversalityLossUnderEvolution (cd : ClassifiedDynamics) : Prop :=
  ¬evolutionPreservesUniversality cd

-- ============================================================================
-- 6. CANONICAL / SERIALIZATION PROHIBITIONS
-- ============================================================================

/-- Adversarial structure in canonical inputs is not allowed. -/
def NotAllowed_AdversarialCanonicalInput (fr : FilterResult) : Prop :=
  fr.safe = false

/-- Emoji-based or weird-machine field names in canonical inputs are not allowed. -/
def NotAllowed_WeirdMachineInput (f : SourceField) : Prop :=
  f.name.contains "🎉" ∨ f.name.contains "🔥" ∨ f.name.contains "💀"

/-- Nondeterministic serialization of the same canonical form is not allowed. -/
def NotAllowed_NondeterministicCanonicalForm (cbf : CanonicalBinaryForm) : Prop :=
  ¬IsCanonical cbf

/-- A canonical schema that is not core-admissible is not allowed in ENE core paths. -/
def NotAllowed_NonCoreCanonicalSchema (schema : RecordSchema) : Prop :=
  schema.coreAdmissible = false

-- ============================================================================
-- 7. EVOLUTION PROHIBITIONS
-- ============================================================================

/-- Self-modification that erases its own audit trail is not allowed. -/
def NotAllowed_EpistemicSelfErasure
  (mod : SelfModification)
  (contract : EvolutionContract)
  (surface : AuditSurface) : Prop :=
  contract.preservesAuditSurface mod surface = false

/-- Evolution that is not replayable is not allowed. -/
def NotAllowed_UnreplayableEvolution
  (mod : SelfModification)
  (contract : EvolutionContract) : Prop :=
  contract.replayable mod = false

/-- Evolution that violates the constitution is not allowed. -/
def NotAllowed_UnconstitutionalEvolution
  (mod : SelfModification)
  (contract : EvolutionContract)
  (constitution : UniverseConstitution) : Prop :=
  contract.preservesConstitution mod constitution = false

-- ============================================================================
-- 8. SCALAR COLLAPSE PROHIBITIONS
-- ============================================================================

/-- A scalar without atomic ancestry is not allowed. -/
def NotAllowed_ScalarWithoutAtomicAncestry (sc : ScalarCollapse) : Prop :=
  ¬sc.sourceDecomposition.nonempty

/-- A scalar missing a required certified invariant is not allowed. -/
def NotAllowed_UncertifiedScalarInvariant
  (sc : ScalarCollapse)
  (inv : ScalarInvariant) : Prop :=
  inv ∈ sc.policy.requiredInvariants ∧ ¬(∃ f ∈ sc.fields, f.invariant.name = inv.name ∧ f.certified = true)

/-- A scalar collapse with negative source load is not allowed. -/
def NotAllowed_ScalarWithNegativeLoad (sc : ScalarCollapse) : Prop :=
  sc.sourceLoad.total < 0.0

-- ============================================================================
-- 9. MASTER CONSTITUTIONAL PROHIBITIONS
-- ============================================================================

/-- A fully ungrounded object is not allowed. -/
def NotAllowed_FullyUngrounded
  (c : GroundedUniverseConstitution)
  (g : Groundedness)
  (sc : Option ScalarCollapse) : Prop :=
  ¬FullyAdmissible c g sc

/-- A scalar collapse that violates its policy is not allowed. -/
def NotAllowed_PolicyViolatingCollapse (sc : ScalarCollapse) : Prop :=
  ¬ScalarAdmissible sc

-- ============================================================================
-- 10. PHYSICAL HALLUCINATION PROHIBITIONS (ZOMBIE BUGS)
-- ============================================================================

/-- 
Any signal claiming to use the 160.2 GHz Cosmic Microwave Background (CMB) 
as a master phase-lock or coherent clock source is prohibited. 
CMB isotropy is a thermodynamic equilibrium state, not a local phase reference.
-/
def NotAllowed_CosmicClocking (signal_source : String) : Prop :=
  signal_source = "CMB_160_GHZ" ∨ signal_source = "COSMIC_PHASE_LOCK"

/--
Using Planck-scale units for macro-scale travel-time estimation without 
a derived renormalization path is prohibited.
-/
def NotAllowed_UnrenormalizedPlanckTime (t : UInt32) : Prop :=
  t < 1000 -- Too small to be physically grounded for seismic travel-times

-- ============================================================================
-- Theorems: Positive laws imply negative prohibitions
-- ============================================================================

/-- If a graph satisfies noActiveQuarantine, then active quarantine is prohibited. -/
theorem no_quarantine_implies_prohibition
  (g : Graph)
  (h : g.noActiveQuarantine) :
  ¬NotAllowed_ActiveQuarantine g := by
  unfold NotAllowed_ActiveQuarantine
  exact not_not_intro h

/-- If a decomposition is faithful, then unfaithful decomposition is prohibited. -/
theorem faithfulness_implies_prohibition
  (l : Lemma)
  (d : AtomicDecomposition)
  (h : FaithfulDecomposition l d) :
  ¬NotAllowed_UnfaithfulDecomposition l d := by
  unfold NotAllowed_UnfaithfulDecomposition
  exact not_not_intro h

/-- If a path is lawful, then unlawful paths are prohibited. -/
theorem lawfulness_implies_prohibition
  (p : AtomicPath)
  (h : p.isLawful) :
  ¬NotAllowed_UnlawfulPath p := by
  unfold NotAllowed_UnlawfulPath
  exact not_not_intro h

/-- If a witness has valid provenance, then missing provenance is prohibited. -/
theorem provenance_implies_prohibition
  (w : Witness)
  (h : w.receipt.provenance = WitnessProvenance.observation ∨
       w.receipt.provenance = WitnessProvenance.inference ∨
       w.receipt.provenance = WitnessProvenance.projection ∨
       w.receipt.provenance = WitnessProvenance.evolution ∨
       w.receipt.provenance = WitnessProvenance.translation ∨
       w.receipt.provenance = WitnessProvenance.composed) :
  ¬NotAllowed_WitnessWithoutProvenance w := by
  unfold NotAllowed_WitnessWithoutProvenance
  exact not_not_intro h

/-- If universality is preserved under projection, then its loss is prohibited. -/
theorem universality_projection_implies_prohibition
  (cd : ClassifiedDynamics)
  (h : projectionPreservesUniversality cd) :
  ¬NotAllowed_UniversalityLossUnderProjection cd := by
  unfold NotAllowed_UniversalityLossUnderProjection
  exact not_not_intro h

/-- If a canonical form is canonical, then nondeterminism is prohibited. -/
theorem determinism_implies_prohibition
  (cbf : CanonicalBinaryForm)
  (h : IsCanonical cbf) :
  ¬NotAllowed_NondeterministicCanonicalForm cbf := by
  unfold NotAllowed_NondeterministicCanonicalForm
  exact not_not_intro h

/-- If a schema is core-admissible, then the non-core-schema prohibition does not apply. -/
theorem core_schema_implies_prohibition
  (schema : RecordSchema)
  (h : schema.coreAdmissible = true) :
  ¬NotAllowed_NonCoreCanonicalSchema schema := by
  unfold NotAllowed_NonCoreCanonicalSchema
  intro hcontra
  rw [h] at hcontra
  simp at hcontra

/-- If an evolution is admissible, then epistemic self-erasure is prohibited. -/
theorem evolution_audit_implies_prohibition
  (mod : SelfModification)
  (contract : EvolutionContract)
  (surface : AuditSurface)
  (constitution : UniverseConstitution)
  (h : EvolutionAdmissible mod contract surface constitution) :
  ¬NotAllowed_EpistemicSelfErasure mod contract surface := by
  unfold NotAllowed_EpistemicSelfErasure
  have ha := no_evolution_without_auditability mod contract surface constitution h
  intro hcontra
  rw [ha] at hcontra
  simp at hcontra

/-- If a scalar collapse is admissible, then missing atomic ancestry is prohibited. -/
theorem scalar_admissible_implies_ancestry_prohibition
  (sc : ScalarCollapse)
  (h : ScalarAdmissible sc) :
  ¬NotAllowed_ScalarWithoutAtomicAncestry sc := by
  unfold NotAllowed_ScalarWithoutAtomicAncestry
  have ha := no_scalar_without_atomic_ancestry sc h
  intro hcontra
  exact hcontra ha

/-- If an object is fully admissible under the constitution, then being fully ungrounded is prohibited. -/
theorem full_admissibility_implies_prohibition
  (c : GroundedUniverseConstitution)
  (g : Groundedness)
  (sc : Option ScalarCollapse)
  (h : FullyAdmissible c g sc) :
  ¬NotAllowed_FullyUngrounded c g sc := by
  unfold NotAllowed_FullyUngrounded
  exact not_not_intro h

end Semantics.ENE
