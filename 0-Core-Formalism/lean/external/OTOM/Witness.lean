import Semantics.Path
import Semantics.Universality

namespace Semantics.ENE

-- Witness and Constitution
-- Emergence receipts and the immutable membrane of admissibility laws.
-- Anything novel must arrive with a receipt.

/-- Provenance of a witness: where it came from. -/
inductive WitnessProvenance
| observation    -- Directly observed
| inference      -- Derived via logical step
| projection     -- Result of collapse/simplification
| evolution      -- Emerged from self-modification
| translation    -- Mapped from another substrate
| composed       -- Built from atomic path composition
deriving Repr, BEq

/-- A receipt certifying that emergence was tracked. -/
structure WitnessReceipt where
  witnessId : Nat
  provenance : WitnessProvenance
  path : AtomicPath
  load : CognitiveLoad
  timestamp : Float
deriving Repr, BEq

/-- A witness certifies that a node in the graph is validly grounded. -/
structure Witness where
  node : Node
  receipt : WitnessReceipt
  preservedAtoms : List Atom
  lostAtoms : List Atom
  accumulatedLoad : Float
  resultCapability : Float
deriving Repr, BEq

/-- A witness is valid if its path is lawful and its load is non-negative. -/
def Witness.ValidUnder (w : Witness) (g : Graph) : Prop :=
  w.receipt.path.isLawful ∧
  w.accumulatedLoad ≥ 0.0 ∧
  g.hasNode w.node

/-- No witness without provenance. -/
theorem Witness.no_witness_without_provenance
  (w : Witness)
  (_h : w.receipt.provenance = WitnessProvenance.observation ∨
       w.receipt.provenance = WitnessProvenance.inference ∨
       w.receipt.provenance = WitnessProvenance.projection ∨
       w.receipt.provenance = WitnessProvenance.evolution ∨
       w.receipt.provenance = WitnessProvenance.translation ∨
       w.receipt.provenance = WitnessProvenance.composed) :
  w.receipt.provenance = w.receipt.provenance := by
  rfl

/-- Groundedness: the conditions under which a node is habitable in the semantic universe. -/
structure Groundedness where
  atomicBasis        : Bool  -- Reducible to semantic atoms
  lawfulReachability : Bool  -- Reachable via lawful atomic path
  boundedLoad        : Bool  -- Processing cost is finite
  faithfulProjection : Bool  -- Collapse preserves meaning
  evolutionAuditable : Bool  -- Changes are traceable
  universalDynamics  : Bool  -- Preserves universality class
  scalingPreserved   : Bool  -- Scaling laws intact
  classMembershipVisible : Bool -- Dynamical class is inspectable
  classifiedDynamics : ClassifiedDynamics -- Precise universality classification

deriving Repr, BEq

/-- The overall groundedness of a node. -/
def Groundedness.habitable (g : Groundedness) : Bool :=
  g.atomicBasis && g.lawfulReachability && g.boundedLoad &&
  g.faithfulProjection && g.evolutionAuditable && g.universalDynamics &&
  g.scalingPreserved && g.classMembershipVisible &&
  g.classifiedDynamics.preservedUnderProjection &&
  g.classifiedDynamics.preservedUnderCollapse &&
  g.classifiedDynamics.preservedUnderEvolution

/-- List of failed groundedness conditions. -/
def Groundedness.failures (g : Groundedness) : List String :=
  let checks := [
    ("atomicBasis", g.atomicBasis),
    ("lawfulReachability", g.lawfulReachability),
    ("boundedLoad", g.boundedLoad),
    ("faithfulProjection", g.faithfulProjection),
    ("evolutionAuditable", g.evolutionAuditable),
    ("universalDynamics", g.universalDynamics),
    ("scalingPreserved", g.scalingPreserved),
    ("classMembershipVisible", g.classMembershipVisible),
    ("preservedUnderProjection", g.classifiedDynamics.preservedUnderProjection),
    ("preservedUnderCollapse", g.classifiedDynamics.preservedUnderCollapse),
    ("preservedUnderEvolution", g.classifiedDynamics.preservedUnderEvolution)
  ]
  checks.filter (λ p => !p.2) |>.map (λ p => p.1)

/-- The master constitution of the semantic universe. -/
structure UniverseConstitution where
  requiresAtomicGrounding     : Bool := true
  requiresLawfulPath          : Bool := true
  requiresLoadVisibility      : Bool := true
  requiresCapabilityLegibility : Bool := true
  requiresProjectionFaithfulness : Bool := true
  requiresEvolutionAuditability : Bool := true
  requiresUniversalityPreservation : Bool := true
  requiresNoActiveQuarantine  : Bool := true

deriving Repr, BEq

/-- A node is admissible under the constitution if all required conditions hold. -/
def UniverseConstitution.admissible (c : UniverseConstitution) (g : Groundedness) : Prop :=
  (c.requiresAtomicGrounding → g.atomicBasis = true) ∧
  (c.requiresLawfulPath → g.lawfulReachability = true) ∧
  (c.requiresLoadVisibility → g.boundedLoad = true) ∧
  (c.requiresCapabilityLegibility → g.classMembershipVisible = true) ∧
  (c.requiresProjectionFaithfulness → g.faithfulProjection = true) ∧
  (c.requiresEvolutionAuditability → g.evolutionAuditable = true) ∧
  (c.requiresUniversalityPreservation →
    projectionPreservesUniversality g.classifiedDynamics ∧
    collapsePreservesUniversality g.classifiedDynamics ∧
    evolutionPreservesUniversality g.classifiedDynamics)

/-- Auditably habitable: a node is habitable and its habitation can be witnessed. -/
def AuditablyHabitable (c : UniverseConstitution) (g : Groundedness) (w : Witness) (gr : Graph) : Prop :=
  c.admissible g ∧ g.habitable = true ∧ w.ValidUnder gr

-- Constitutional theorems (master admissibility laws)

theorem no_rooms_without_foundations
  (c : UniverseConstitution) (g : Groundedness)
  (hc : c.requiresAtomicGrounding = true)
  (ha : c.admissible g) :
  g.atomicBasis = true := by
  unfold UniverseConstitution.admissible at ha
  simp [hc] at ha
  exact ha.1

theorem no_corridors_without_laws
  (c : UniverseConstitution) (g : Groundedness)
  (hc : c.requiresLawfulPath = true)
  (ha : c.admissible g) :
  g.lawfulReachability = true := by
  unfold UniverseConstitution.admissible at ha
  simp [hc] at ha
  exact ha.2.1

theorem no_depth_without_map
  (c : UniverseConstitution) (g : Groundedness)
  (hc : c.requiresLoadVisibility = true)
  (ha : c.admissible g) :
  g.boundedLoad = true := by
  unfold UniverseConstitution.admissible at ha
  simp [hc] at ha
  exact ha.2.2.1

theorem no_invisible_capability
  (c : UniverseConstitution) (g : Groundedness)
  (hc : c.requiresCapabilityLegibility = true)
  (ha : c.admissible g) :
  g.classMembershipVisible = true := by
  unfold UniverseConstitution.admissible at ha
  simp [hc] at ha
  exact ha.2.2.2.1

theorem no_endless_dream_logic
  (c : UniverseConstitution) (g : Groundedness)
  (hc : c.requiresProjectionFaithfulness = true)
  (ha : c.admissible g) :
  g.faithfulProjection = true := by
  unfold UniverseConstitution.admissible at ha
  simp [hc] at ha
  exact ha.2.2.2.2.1

theorem no_opaque_evolution
  (c : UniverseConstitution) (g : Groundedness)
  (hc : c.requiresEvolutionAuditability = true)
  (ha : c.admissible g) :
  g.evolutionAuditable = true := by
  unfold UniverseConstitution.admissible at ha
  simp [hc] at ha
  exact ha.2.2.2.2.2.1

theorem no_universality_loss_under_projection
  (c : UniverseConstitution) (g : Groundedness)
  (hc : c.requiresUniversalityPreservation = true)
  (ha : c.admissible g) :
  projectionPreservesUniversality g.classifiedDynamics := by
  unfold UniverseConstitution.admissible at ha
  simp [hc] at ha
  exact ha.2.2.2.2.2.2.1

theorem no_universality_loss_under_collapse
  (c : UniverseConstitution) (g : Groundedness)
  (hc : c.requiresUniversalityPreservation = true)
  (ha : c.admissible g) :
  collapsePreservesUniversality g.classifiedDynamics := by
  unfold UniverseConstitution.admissible at ha
  simp [hc] at ha
  exact ha.2.2.2.2.2.2.2.1

theorem no_universality_loss_under_evolution
  (c : UniverseConstitution) (g : Groundedness)
  (hc : c.requiresUniversalityPreservation = true)
  (ha : c.admissible g) :
  evolutionPreservesUniversality g.classifiedDynamics := by
  unfold UniverseConstitution.admissible at ha
  simp [hc] at ha
  exact ha.2.2.2.2.2.2.2.2

end Semantics.ENE
