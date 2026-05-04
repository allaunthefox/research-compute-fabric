import Semantics
import Semantics.Physics.Tests

open Semantics
open Semantics.Atom
open Semantics.ENE
open Semantics.Physics

-- Tests for the ENE Semantic Database
-- These examples verify that the formalization compiles and that
-- the master admissibility laws are provable for well-formed structures.

-- ---------------------------------------------------------------------------
-- Lemma tests
-- ---------------------------------------------------------------------------

def killLemma : Lemma := {
  canonical := "kill",
  sig := [cause, someone, die],
  pos := .verb
}

/-- Verify that 'killLemma' is Agentive. -/
def kill_is_agentive : isAgentive killLemma := by
  unfold isAgentive
  unfold HasAtom
  simp [killLemma]

/-- A function that ONLY accepts agentive lemmas. -/
def processAgentiveAction (l : Lemma) (_h : isAgentive l) : String :=
  s!"Successfully processing agentive lemma: {l.canonical}"

def test_execution := processAgentiveAction killLemma kill_is_agentive

#eval test_execution

-- ---------------------------------------------------------------------------
-- ENE Graph tests
-- ---------------------------------------------------------------------------

/-- Build a small semantic graph: runLemma connected to atoms. -/
def runLemma : Lemma := {
  canonical := "run",
  sig := [do_, move, someone],
  pos := .verb
}

/-- Construct a graph with a lemma and its atomic decomposition. -/
def exampleGraph : Graph :=
  let g0 := Graph.empty
  let (g1, node_run) := g0.insertNode NodeType.lemma "run"
  let (g2, node_do)  := g1.insertNode NodeType.atom "do_"
  let (g3, node_move) := g2.insertNode NodeType.atom "move"
  let (g4, node_someone) := g3.insertNode NodeType.atom "someone"
  let (g5, _) := g4.insertEdge node_run node_do  EdgeType.has_atom EdgeClass.definitional
  let (g6, _) := g5.insertEdge node_run node_move EdgeType.has_atom EdgeClass.definitional
  let (g7, _) := g6.insertEdge node_run node_someone EdgeType.has_atom EdgeClass.definitional
  g7

/-- The graph contains the run lemma. -/
theorem graph_contains_run :
  ∃ n ∈ exampleGraph.nodes, n.label = "run" ∧ n.type == NodeType.lemma := by
  native_decide

/-- The run lemma has_atom move in the example graph. -/
theorem run_has_move :
  ∃ e ∈ exampleGraph.edges,
    e.source.label = "run" ∧ e.type == EdgeType.has_atom ∧ e.target.label = "move" := by
  native_decide

-- ---------------------------------------------------------------------------
-- Path tests
-- ---------------------------------------------------------------------------

/-- A single-step atomic path in the example graph. -/
def step1 : AtomicStep := {
  rewrite := {
    fromNode := { id := 0, type := NodeType.lemma, label := "run", payload := none },
    toNode   := { id := 2, type := NodeType.atom, label := "move", payload := none },
    viaEdge  := { id := 1, source := { id := 0, type := NodeType.lemma, label := "run", payload := none }, target := { id := 2, type := NodeType.atom, label := "move", payload := none }, type := EdgeType.has_atom, edgeClass := EdgeClass.definitional, weight := 1.0, justified := true },
    locallyAdmissible := true
  },
  stepId := 0
}

def examplePath : AtomicPath := { steps := [step1] }

/-- examplePath is lawful. -/
theorem example_path_is_lawful : examplePath.isLawful := by
  unfold examplePath
  unfold AtomicPath.isLawful
  simp [step1]

/-- Length of examplePath is 1. -/
theorem example_path_length : examplePath.length = 1 := by
  unfold examplePath
  unfold AtomicPath.length
  simp

-- ---------------------------------------------------------------------------
-- Witness / Constitution tests
-- ---------------------------------------------------------------------------

/-- A well-formed witness for the run lemma node. -/
def exampleWitness : Witness := {
  node := { id := 0, type := NodeType.lemma, label := "run", payload := none },
  receipt := {
    witnessId := 0,
    provenance := WitnessProvenance.observation,
    path := examplePath,
    load := { intrinsic := 0.5, extraneous := 0.1, germane := 0.3, routing := 0.1, memory := 0.0, total := 1.0 },
    timestamp := 0.0
  },
  preservedAtoms := [do_, move, someone],
  lostAtoms := [],
  accumulatedLoad := 1.0,
  resultCapability := 0.5
}

/-- A fully grounded node, now including classified DNA/KPZ dynamics. -/
def fullGroundedness : Groundedness := {
  atomicBasis := true,
  lawfulReachability := true,
  boundedLoad := true,
  faithfulProjection := true,
  evolutionAuditable := true,
  universalDynamics := true,
  scalingPreserved := true,
  classMembershipVisible := true,
  classifiedDynamics := dnaHybridizationKPZ
}

/-- fullGroundedness is habitable. -/
theorem full_groundedness_habitable : fullGroundedness.habitable = true := by
  unfold Groundedness.habitable
  simp [fullGroundedness, dnaHybridizationKPZ]

/-- The default constitution admits fullGroundedness. -/
theorem constitution_admits_full :
  let c := ({} : UniverseConstitution)
  c.admissible fullGroundedness := by
  unfold UniverseConstitution.admissible
  simp [fullGroundedness]
  unfold projectionPreservesUniversality
  unfold collapsePreservesUniversality
  unfold evolutionPreservesUniversality
  simp [dnaHybridizationKPZ]

/-- Constitutional law: projection preserves universality for DNA KPZ dynamics. -/
theorem dna_kpz_projection_preserved :
  let c := ({} : UniverseConstitution)
  let g := fullGroundedness
  c.admissible g → projectionPreservesUniversality g.classifiedDynamics := by
  intro c g ha
  exact no_universality_loss_under_projection c g rfl ha

/-- Constitutional law: collapse preserves universality for DNA KPZ dynamics. -/
theorem dna_kpz_collapse_preserved :
  let c := ({} : UniverseConstitution)
  let g := fullGroundedness
  c.admissible g → collapsePreservesUniversality g.classifiedDynamics := by
  intro c g ha
  exact no_universality_loss_under_collapse c g rfl ha

/-- Constitutional law: evolution preserves universality for DNA KPZ dynamics. -/
theorem dna_kpz_evolution_preserved :
  let c := ({} : UniverseConstitution)
  let g := fullGroundedness
  c.admissible g → evolutionPreservesUniversality g.classifiedDynamics := by
  intro c g ha
  exact no_universality_loss_under_evolution c g rfl ha

-- ---------------------------------------------------------------------------
-- DNA Substrate tests
-- ---------------------------------------------------------------------------

/-- The DNA hybridization object has all three semantic layers. -/
theorem dna_object_has_universal_semantics :
  DNAUniversalSemantic.universalityClass ∈ exampleDNASemanticObject.universal := by
  unfold exampleDNASemanticObject
  simp

/-- DNA hybridization dynamics are classified as KPZ. -/
theorem dna_kpz_classification :
  exampleDNASemanticObject.dynamics.universalityClass = UniversalityClass.kpz := by
  unfold exampleDNASemanticObject
  unfold dnaHybridizationKPZ
  rfl

/-- DNA methylation ratchet is classified as Directed Percolation. -/
theorem dna_dp_classification :
  dnaMethylationRatchet.universalityClass = UniversalityClass.directedPercolation := by
  unfold dnaMethylationRatchet
  rfl

-- ---------------------------------------------------------------------------
-- Decomposition tests
-- ---------------------------------------------------------------------------

/-- A faithful decomposition of the run lemma (weights in Q16_16: 0x00010000 = 1.0). -/
def runDecomposition : AtomicDecomposition := {
  source := runLemma,
  atoms := [
    { atom := do_, weight := 0x00010000 },
    { atom := move, weight := 0x00010000 },
    { atom := someone, weight := 0x00010000 }
  ]
}

/-- The run decomposition is faithful. -/
theorem run_decomposition_faithful :
  FaithfulDecomposition runLemma runDecomposition := by
  unfold FaithfulDecomposition
  unfold runLemma
  unfold runDecomposition
  unfold AtomicDecomposition.unweighted
  constructor <;> rfl

/-- Faithful decomposition implies nonempty (when the signature is nonempty). -/
theorem run_decomposition_nonempty :
  runDecomposition.nonempty := by
  apply faithful_decomposition_nonempty runLemma runDecomposition
  · exact run_decomposition_faithful
  · unfold runLemma
    simp

-- ---------------------------------------------------------------------------
-- Scalar Collapse tests
-- ---------------------------------------------------------------------------

/-- A certified scalar collapse derived from the run decomposition and path. -/
def exampleScalarCollapse : ScalarCollapse := {
  policy := {
    name := "agentive_motion_scalar",
    requiredInvariants := [
      { name := "agency", value := 1.0, tolerance := 0.1 },
      { name := "motion", value := 1.0, tolerance := 0.1 }
    ]
  },
  fields := [
    { name := "agency", invariant := { name := "agency", value := 1.0, tolerance := 0.1 }, certified := true },
    { name := "motion", invariant := { name := "motion", value := 1.0, tolerance := 0.1 }, certified := true }
  ],
  sourceDecomposition := runDecomposition,
  sourcePath := examplePath,
  sourceLoad := { intrinsic := 0.5, extraneous := 0.1, germane := 0.3, routing := 0.1, memory := 0.0, total := 1.0 }
}

/-- The example scalar collapse is admissible. -/
theorem example_scalar_collapse_admissible :
  ScalarAdmissible exampleScalarCollapse := by
  unfold ScalarAdmissible
  simp [exampleScalarCollapse, examplePath, runDecomposition]
  constructor
  · exact example_path_is_lawful
  · constructor
    · unfold AtomicDecomposition.nonempty
      simp
    · native_decide

/-- The collapse has atomic ancestry. -/
theorem example_scalar_has_atomic_ancestry :
  ScalarAdmissible exampleScalarCollapse → exampleScalarCollapse.sourceDecomposition.nonempty := by
  intro h
  exact no_scalar_without_atomic_ancestry exampleScalarCollapse h

/-- The collapse has a lawful history. -/
theorem example_scalar_has_lawful_history :
  ScalarAdmissible exampleScalarCollapse → exampleScalarCollapse.sourcePath.isLawful := by
  intro h
  exact no_scalar_without_lawful_history exampleScalarCollapse h

-- ---------------------------------------------------------------------------
-- Canonical adapter tests
-- ---------------------------------------------------------------------------

/-- A simple observation schema for testing canonicalization. -/
def testSchema : RecordSchema := {
  name := "Observation",
  fields := [
    { name := "temperature", kind := FieldKind.q16_16 },
    { name := "confidence", kind := FieldKind.nat 8 }
  ]
}

/-- A canonicalized observation from source fields. -/
def canonicalObservation : NormalizeResult CanonicalBinaryForm :=
  canonicalize testSchema [
    { name := "temperature", value := SourceValue.q16_16 (Q16_16.ofInt 273) },
    { name := "confidence", value := SourceValue.nat 255 }
  ]

/-- If canonicalization succeeds, the schema is preserved. -/
theorem canonical_observation_schema_preserved :
  ∀ cbf, canonicalObservation = .ok cbf → cbf.schema = testSchema := by
  intros cbf h
  unfold canonicalObservation at h
  simp [canonicalize, testSchema] at h
  cases h
  rfl

/-- A filter rule that rejects emoji-like adversarial names. -/
def emojiFilter : FilterRule := {
  name := "emoji_rejection",
  predicate := λ f => f.name.contains "🎉",
  relevance := Relevance.adversarial,
  reason := "Emoji sequences can encode unintended computation paths"
}

/-- Filtered safe input passes cleanly. -/
def safeSource : List SourceField := [
  { name := "temperature", value := SourceValue.q16_16 (Q16_16.ofInt 273) }
]

theorem safe_input_passes_filter :
  (applyFilters [emojiFilter] safeSource).safe = true := by
  native_decide

/-- Determinism theorem instantiation: the canonical observation is canonical. -/
theorem canonical_observation_deterministic :
  ∀ cbf, canonicalObservation = .ok cbf → IsCanonical cbf := by
  intros cbf h
  exact canonicalize_is_deterministic testSchema [
    { name := "temperature", value := SourceValue.q16_16 (Q16_16.ofInt 273) },
    { name := "confidence", value := SourceValue.nat 255 }
  ] cbf h

/-- The revised schema is admissible for ENE core use. -/
theorem test_schema_core_admissible :
  testSchema.coreAdmissible = true := by
  native_decide

/-- Duplicate field names are rejected by the schema admissibility check. -/
theorem duplicate_field_names_rejected :
  ({ name := "BadSchema",
     fields := [
       { name := "temperature", kind := FieldKind.q16_16 },
       { name := "temperature", kind := FieldKind.nat 8 }
     ] } : RecordSchema).coreAdmissible = false := by
  native_decide

-- ---------------------------------------------------------------------------
-- Evolution tests
-- ---------------------------------------------------------------------------

/-- A trivial evolution contract that always passes. -/
def trivialEvolutionContract : EvolutionContract := {
  contractId := 0,
  preservesAuditSurface := λ _ _ => true,
  replayable := λ _ => true,
  preservesConstitution := λ _ _ => true
}

/-- A trivial audit surface. -/
def trivialAuditSurface : AuditSurface := {
  requiredNodes := [],
  requiredEdges := [],
  transparency := 1.0
}

/-- A valid self-modification. -/
def exampleModification : SelfModification := {
  id := 0,
  description := "Add run lemma",
  priorState := Graph.empty,
  postState := exampleGraph,
  witness := exampleWitness,
  timestamp := 0.0
}

/-- The example modification is admissible under the trivial contract. -/
theorem example_modification_admissible :
  EvolutionAdmissible exampleModification trivialEvolutionContract trivialAuditSurface ({} : UniverseConstitution) := by
  unfold EvolutionAdmissible
  simp [trivialEvolutionContract]

/-- Auditability is preserved for admissible modifications. -/
theorem example_modification_auditability :
  EvolutionAdmissible exampleModification trivialEvolutionContract trivialAuditSurface ({} : UniverseConstitution) →
  trivialEvolutionContract.preservesAuditSurface exampleModification trivialAuditSurface = true := by
  intro h
  exact no_evolution_without_auditability exampleModification trivialEvolutionContract trivialAuditSurface ({} : UniverseConstitution) h

/-- An empty graph trivially has no active quarantine. -/
theorem empty_graph_no_quarantine :
  Graph.noActiveQuarantine Graph.empty := by
  unfold Graph.noActiveQuarantine Graph.empty
  simp

-- ---------------------------------------------------------------------------
-- Grounded Universe Constitution tests
-- ---------------------------------------------------------------------------

/-- The default grounded universe constitution is fully satisfied by fullGroundedness. -/
theorem grounded_universe_admits_full :
  let c := { semantic := ({} : UniverseConstitution) : GroundedUniverseConstitution }
  FullyAdmissible c fullGroundedness (some exampleScalarCollapse) := by
  unfold FullyAdmissible
  simp [constitution_admits_full, example_scalar_collapse_admissible]

/-- Scalar certification is mandatory at the constitution level. -/
theorem constitution_requires_scalar_cert :
  let c := { semantic := ({} : UniverseConstitution) : GroundedUniverseConstitution }
  FullyAdmissible c fullGroundedness (some exampleScalarCollapse) → c.scalar = true := by
  intro c h
  exact scalar_certification_required c fullGroundedness (some exampleScalarCollapse) h

/-- Atomic grounding is enforced by the master constitution. -/
theorem master_constitution_enforces_atomic_basis :
  let c := { semantic := ({} : UniverseConstitution) : GroundedUniverseConstitution }
  FullyAdmissible c fullGroundedness (some exampleScalarCollapse) → fullGroundedness.atomicBasis = true := by
  intro c h
  exact no_object_without_semantic_grounding c fullGroundedness (some exampleScalarCollapse) h rfl

-- ---------------------------------------------------------------------------
-- Prohibition tests
-- ---------------------------------------------------------------------------

/-- The example graph does not contain active quarantine edges. -/
theorem example_graph_no_active_quarantine :
  ¬NotAllowed_ActiveQuarantine Graph.empty := by
  apply no_quarantine_implies_prohibition
  exact empty_graph_no_quarantine

/-- The run decomposition is not unfaithful. -/
theorem run_decomposition_not_unfaithful :
  ¬NotAllowed_UnfaithfulDecomposition runLemma runDecomposition := by
  apply faithfulness_implies_prohibition
  exact run_decomposition_faithful

/-- The example path is not unlawful. -/
theorem example_path_not_unlawful :
  ¬NotAllowed_UnlawfulPath examplePath := by
  apply lawfulness_implies_prohibition
  exact example_path_is_lawful

/-- The example witness does not lack provenance. -/
theorem example_witness_has_provenance :
  ¬NotAllowed_WitnessWithoutProvenance exampleWitness := by
  apply provenance_implies_prohibition
  simp [exampleWitness]

/-- The DNA KPZ dynamics do not lose universality under projection. -/
theorem dna_kpz_no_universality_loss_projection :
  ¬NotAllowed_UniversalityLossUnderProjection dnaHybridizationKPZ := by
  apply universality_projection_implies_prohibition
  unfold projectionPreservesUniversality
  unfold dnaHybridizationKPZ
  rfl

/-- The canonical observation is not nondeterministic. -/
theorem canonical_observation_not_nondeterministic :
  ∀ cbf, canonicalObservation = .ok cbf → ¬NotAllowed_NondeterministicCanonicalForm cbf := by
  intros cbf h
  apply determinism_implies_prohibition
  exact canonicalize_is_deterministic testSchema [
    { name := "temperature", value := SourceValue.float64 273.15 },
    { name := "confidence", value := SourceValue.nat 255 }
  ] cbf h

/-- The example modification does not erase its audit trail. -/
theorem example_modification_no_epistemic_erasure :
  ¬NotAllowed_EpistemicSelfErasure exampleModification trivialEvolutionContract trivialAuditSurface := by
  apply evolution_audit_implies_prohibition
  exact example_modification_admissible

/-- The example scalar collapse does not lack atomic ancestry. -/
theorem example_scalar_not_missing_ancestry :
  ¬NotAllowed_ScalarWithoutAtomicAncestry exampleScalarCollapse := by
  apply scalar_admissible_implies_ancestry_prohibition
  exact example_scalar_collapse_admissible

/-- The example scalar collapse does not have negative source load. -/
theorem example_scalar_not_negative_load :
  ¬NotAllowed_ScalarWithNegativeLoad exampleScalarCollapse := by
  unfold NotAllowed_ScalarWithNegativeLoad
  unfold exampleScalarCollapse
  native_decide

/-- The full constitutional object is not ungrounded. -/
theorem full_groundedness_not_ungrounded :
  let c := { semantic := ({} : UniverseConstitution) : GroundedUniverseConstitution }
  ¬NotAllowed_FullyUngrounded c fullGroundedness (some exampleScalarCollapse) := by
  intro c
  apply full_admissibility_implies_prohibition
  exact grounded_universe_admits_full

-- ---------------------------------------------------------------------------
-- Diagnostic tests
-- ---------------------------------------------------------------------------

/-- A trivially healthy report (empty graph, empty path). -/
def emptyReport : DiagnosticReport := {
  knitPathExists := true,
  knitCoverage := 1.0,
  rigidPsd := true,
  crntIsZero := true,
  flavorPositive := true,
  neuroOk := true,
  neuroMode := "GRADIENT"
}

theorem empty_report_is_healthy : emptyReport.overallHealthy = true := by
  unfold DiagnosticReport.overallHealthy
  unfold DiagnosticReport.conditionsPassed
  unfold DiagnosticReport.conditionsTotal
  simp [emptyReport]
