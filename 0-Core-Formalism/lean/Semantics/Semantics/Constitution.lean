import Semantics.Atoms
import Semantics.Lemmas
import Semantics.Decomposition
import Semantics.Projections
import Semantics.Graph
import Semantics.Path
import Semantics.Witness
import Semantics.Diagnostics
import Semantics.Universality
import Semantics.Substrate
import Semantics.Canon
import Semantics.Evolution
import Semantics.ScalarCollapse

namespace Semantics.ENE

-- Constitution
--
-- The immutable membrane of the semantic universe.
-- This module imports all lower layers and exposes the master
-- admissibility laws that govern what may exist, move, collapse,
-- and evolve within the ENE database.
--
-- Includes the forced-translation contract: the codebase is translated
-- into Lean as a fault-injection probe. Breaks are the deliverable, not
-- the artifact. A translation that cannot break cannot teach. If a
-- fragment cannot be translated tightly today, translating it later
-- will be strictly worse — defects compound, context evaporates, and
-- the silencers of today become the load-bearing assumptions of
-- tomorrow. Tight now, or flagged now. No third state.

/-- The complete constitution bundles semantic, dynamical, and operational laws. -/
structure GroundedUniverseConstitution where
  semantic : UniverseConstitution
  universality : Bool := true -- universality preservation is mandatory
  canonical : Bool := true     -- canonical normalization is mandatory
  evolution : Bool := true     -- evolution auditability is mandatory
  scalar : Bool := true        -- scalar collapse certification is mandatory

deriving Repr, BEq

/-- A semantic object is fully admissible only if it satisfies all constitutional layers. -/
def FullyAdmissible
  (c : GroundedUniverseConstitution)
  (g : Groundedness)
  (sc : Option ScalarCollapse) : Prop :=
  c.semantic.admissible g ∧
  c.universality = true ∧
  c.canonical = true ∧
  c.evolution = true ∧
  c.scalar = true ∧
  (match sc with
   | some collapse => ScalarAdmissible collapse
   | none => true)

-- Master theorems (the immutable membrane)

/-- Semantic grounding is required. -/
theorem no_object_without_semantic_grounding
  (c : GroundedUniverseConstitution)
  (g : Groundedness)
  (sc : Option ScalarCollapse)
  (h : FullyAdmissible c g sc)
  (hc : c.semantic.requiresAtomicGrounding = true) :
  g.atomicBasis = true := by
  unfold FullyAdmissible at h
  exact no_rooms_without_foundations c.semantic g hc h.1

/-- Lawful paths are required. -/
theorem no_motion_without_lawful_path
  (c : GroundedUniverseConstitution)
  (g : Groundedness)
  (sc : Option ScalarCollapse)
  (h : FullyAdmissible c g sc)
  (hc : c.semantic.requiresLawfulPath = true) :
  g.lawfulReachability = true := by
  unfold FullyAdmissible at h
  exact no_corridors_without_laws c.semantic g hc h.1

/-- Load visibility is required. -/
theorem no_complexity_without_load_map
  (c : GroundedUniverseConstitution)
  (g : Groundedness)
  (sc : Option ScalarCollapse)
  (h : FullyAdmissible c g sc)
  (hc : c.semantic.requiresLoadVisibility = true) :
  g.boundedLoad = true := by
  unfold FullyAdmissible at h
  exact no_depth_without_map c.semantic g hc h.1

/-- Universality preservation is mandatory at the top level. -/
theorem no_universality_loss_under_constitution
  (c : GroundedUniverseConstitution)
  (g : Groundedness)
  (sc : Option ScalarCollapse)
  (h : FullyAdmissible c g sc) :
  c.universality = true := by
  unfold FullyAdmissible at h
  exact h.2.1

/-- Canonical normalization is mandatory. -/
theorem canonical_form_required
  (c : GroundedUniverseConstitution)
  (g : Groundedness)
  (sc : Option ScalarCollapse)
  (h : FullyAdmissible c g sc) :
  c.canonical = true := by
  unfold FullyAdmissible at h
  exact h.2.2.1

/-- Evolution auditability is mandatory. -/
theorem evolution_audit_required
  (c : GroundedUniverseConstitution)
  (g : Groundedness)
  (sc : Option ScalarCollapse)
  (h : FullyAdmissible c g sc) :
  c.evolution = true := by
  unfold FullyAdmissible at h
  exact h.2.2.2.1

/-- Scalar collapse certification is mandatory. -/
theorem scalar_certification_required
  (c : GroundedUniverseConstitution)
  (g : Groundedness)
  (sc : Option ScalarCollapse)
  (h : FullyAdmissible c g sc) :
  c.scalar = true := by
  unfold FullyAdmissible at h
  exact h.2.2.2.2.1

/-- If a scalar collapse is present, it must be admissible. -/
theorem scalar_collapse_must_be_admissible
  (c : GroundedUniverseConstitution)
  (g : Groundedness)
  (sc : ScalarCollapse)
  (h : FullyAdmissible c g (some sc)) :
  ScalarAdmissible sc := by
  unfold FullyAdmissible at h
  exact h.2.2.2.2.2

-- ─────────────────────────────────────────────────────────────────────
-- Translation Contract — forced translation as fault injection
-- ─────────────────────────────────────────────────────────────────────
--
-- The translation of the codebase into Lean is a probe. The probe only
-- works if it is not allowed to silently degrade. Each constructor of
-- TranslationSilencer names one shape, observed in practice, that lets
-- a translated module typecheck without surfacing a fault that exists
-- in the source. Silencers are forbidden by this constitution.
--
-- The alternative to a silencer is a flag: an explicit, locatable,
-- human-acknowledged record that a fragment cannot be translated tightly
-- today. Flags are the trace; silencers destroy the trace. The two are
-- not interchangeable.

/-- A translation silencer: a construct that lets the formalisation
succeed without surfacing a fault that exists in the source.

Each constructor names one shape that has been observed in practice.
This list is open-ended — new shapes should be added as they are
discovered, and the contract re-checked. -/
inductive TranslationSilencer
  | wildcardOnInductive   -- `_ => …` arm on a closed inductive match
  | proofGapAdmission     -- any proof placeholder in proof or term
  | softPassExtern        -- extern declaration that always returns success
  | tautologyProof        -- `unfold …; simp` proof of a definition restated as theorem
  | dualTableUnverified   -- parallel encode/decode tables without a roundtrip theorem
  | optionFallbackSilent  -- `Option`/`Except` return that absorbs a structural error silently
  | stubExtractedFunction -- function body replaced by a constant or default value
  | unitTypePlaceholder   -- `Unit` standing in for a real type that should be defined
deriving Repr, BEq, DecidableEq

/-- A flagged untranslatable fragment: an explicit, addressable record
that a piece of the source resists tight translation. The flag itself
is the trace; its existence is information; its absence is silence.

A flag is valid only when acknowledged by a human reviewer — an
unacknowledged flag is indistinguishable from drift. -/
structure UntranslatableFragment where
  locator      : String   -- file:line or symbolic identifier
  reason       : String   -- why translation refuses to be tight here
  acknowledged : Bool := false
deriving Repr, BEq

/-- A per-module translation contract. Lists every silencer present in
the module (must be empty for admissibility) and every flagged fragment
deferred for human review. -/
structure TranslationContract where
  moduleName : String
  silencers  : List TranslationSilencer
  flags      : List UntranslatableFragment
deriving Repr, BEq

/-- A translation is admissible iff it contains zero silencers AND
every flagged fragment has been explicitly acknowledged. There is no
third state — silencer, acknowledged flag, or incomplete. -/
def TranslationAdmissible (t : TranslationContract) : Prop :=
  t.silencers = [] ∧ ∀ f ∈ t.flags, f.acknowledged = true

/-- First law of forced translation: a single silencer blocks
admissibility. Contrapositive of the empty-list requirement, exposed as
a callable lemma so downstream modules can refute admissibility by
exhibiting any one silencer. -/
theorem silencer_blocks_admissibility
  (t : TranslationContract) (s : TranslationSilencer)
  (hmem : s ∈ t.silencers) :
  ¬ TranslationAdmissible t := by
  intro hadm
  have hempty : t.silencers = [] := hadm.1
  rw [hempty] at hmem
  exact List.not_mem_nil hmem

/-- Second law: an unacknowledged flag also blocks admissibility. A
flag is a deferral, not a free pass — it must pass through a human
review boundary before the contract can be considered satisfied. -/
theorem unacknowledged_flag_blocks_admissibility
  (t : TranslationContract) (f : UntranslatableFragment)
  (hmem : f ∈ t.flags) (hack : f.acknowledged = false) :
  ¬ TranslationAdmissible t := by
  intro hadm
  have hall : ∀ g ∈ t.flags, g.acknowledged = true := hadm.2
  have : f.acknowledged = true := hall f hmem
  rw [this] at hack
  exact Bool.noConfusion hack

/-- Third law: silence is only admissible when both lists are empty.
The empty-contract case — a module with no silencers and no flags —
is the only fully-translated state. Everything else is open work. -/
theorem fully_translated_iff_empty
  (t : TranslationContract) :
  (t.silencers = [] ∧ t.flags = []) → TranslationAdmissible t := by
  intro ⟨hs, hf⟩
  refine ⟨hs, ?_⟩
  intro f hmem
  rw [hf] at hmem
  exact absurd hmem (List.not_mem_nil)

-- Self-flag: Constitution.lean defines the translation contract machinery
-- but contains no populated TranslationContract instances. This is the
-- dogfood case: the contract that cannot detect its own absence of use.
-- AGENTS.md violations found by opencode review in dependent modules:
--   - Decomposition.lean: Float (weight, timestamp) — violates §1.4
--   - Lemmas.lean: pos : String (open type) — violates §1.5
-- These flags remain unacknowledged pending mechanical port to Q16_16
-- and PartOfSpeech enumeration respectively.
def constitutionSelfContract : TranslationContract := {
  moduleName := "Semantics.Constitution"
  silencers := []
  flags := [
    {
      locator := "Semantics.Decomposition:13"
      reason := "weight : Float — AGENTS.md §1.4 prohibits Float in core. Port to Q16_16 (UInt32)."
      acknowledged := false
    },
    {
      locator := "Semantics.Decomposition:28"
      reason := "timestamp : Float — AGENTS.md §1.4 prohibits Float in core. Port to UInt32 (Unix epoch)."
      acknowledged := false
    },
    {
      locator := "Semantics.Lemmas:12"
      reason := "pos : String — AGENTS.md §1.5 requires finite enumerable type. Define PartOfSpeech enum."
      acknowledged := false
    }
  ]
}

end Semantics.ENE
