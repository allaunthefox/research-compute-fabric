import Semantics.Witness
import Semantics.Canon

namespace Semantics.ENE

-- Evolution
--
-- Defines self-modification under constitution.
-- The system may change, but it must never become alien to its own audit surface.

/-- A record of a single self-modification event. -/
structure SelfModification where
  id : Nat
  description : String
  priorState : Graph
  postState : Graph
  witness : Witness
  timestamp : Float

deriving Repr

/-- An audit surface is the set of nodes and edges that must remain inspectable
after any evolution step. -/
structure AuditSurface where
  requiredNodes : List Node
  requiredEdges : List Edge
  transparency : Float -- 0.0 to 1.0

deriving Repr, BEq

/-- An evolution contract governs how the graph may change. -/
structure EvolutionContract where
  contractId : Nat
  preservesAuditSurface : SelfModification → AuditSurface → Bool
  replayable : SelfModification → Bool
  preservesConstitution : SelfModification → UniverseConstitution → Bool

/-- An evolution step is admissible if it satisfies the contract. -/
def EvolutionAdmissible
  (mod : SelfModification)
  (contract : EvolutionContract)
  (surface : AuditSurface)
  (constitution : UniverseConstitution) : Prop :=
  contract.preservesAuditSurface mod surface = true ∧
  contract.replayable mod = true ∧
  contract.preservesConstitution mod constitution = true

-- Evolution theorems (anti-insect / anti-epistemic-erasure laws)

/-- No evolution without auditability. -/
theorem no_evolution_without_auditability
  (mod : SelfModification)
  (contract : EvolutionContract)
  (surface : AuditSurface)
  (constitution : UniverseConstitution)
  (h : EvolutionAdmissible mod contract surface constitution) :
  contract.preservesAuditSurface mod surface = true := by
  unfold EvolutionAdmissible at h
  exact h.1

/-- No evolution without replayability. -/
theorem no_evolution_without_replayability
  (mod : SelfModification)
  (contract : EvolutionContract)
  (surface : AuditSurface)
  (constitution : UniverseConstitution)
  (h : EvolutionAdmissible mod contract surface constitution) :
  contract.replayable mod = true := by
  unfold EvolutionAdmissible at h
  exact h.2.1

/-- No epistemic self-erasure: the constitution must survive evolution. -/
theorem no_epistemic_self_erasure
  (mod : SelfModification)
  (contract : EvolutionContract)
  (surface : AuditSurface)
  (constitution : UniverseConstitution)
  (h : EvolutionAdmissible mod contract surface constitution) :
  contract.preservesConstitution mod constitution = true := by
  unfold EvolutionAdmissible at h
  exact h.2.2

/-- Capability legibility is coupled to evolution:
a valid modification must be replayable, ensuring its capability impact
remains inspectable. -/
theorem capability_legibility_coupled
  (mod : SelfModification)
  (contract : EvolutionContract)
  (surface : AuditSurface)
  (constitution : UniverseConstitution)
  (h : EvolutionAdmissible mod contract surface constitution) :
  contract.replayable mod = true := by
  unfold EvolutionAdmissible at h
  exact h.2.1

/-- Atomic grounding is preserved under evolution if the post-state graph
contains all atoms referenced by the modification witness. -/
def preservesAtomicGrounding (mod : SelfModification) : Prop :=
  ∀ a ∈ mod.witness.preservedAtoms,
    ∃ n ∈ mod.postState.nodes,
      n.type = NodeType.atom ∧ n.label = atomLabel a

/-- Projection faithfulness is preserved if the post-state graph
contains no active quarantined edges. -/
def preservesProjectionContract (mod : SelfModification) : Prop :=
  mod.postState.noActiveQuarantine

end Semantics.ENE
