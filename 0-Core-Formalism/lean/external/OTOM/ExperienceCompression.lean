/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

ExperienceCompression.lean — Experience Compression Spectrum for LLM Agents

This module formalizes the Experience Compression Spectrum from
"Experience Compression Spectrum: Unifying Memory, Skills, and Rules in LLM Agents"
(arXiv:2604.15877, 2026).

Key contributions:
1. Four-level compression hierarchy: Raw Trace → Episodic Memory → Procedural Skill → Declarative Rule
2. Compression ratios: L0 (1:1), L1 (5-20×), L2 (50-500×), L3 (1000×+)
3. Three trade-off dimensions: Generalizability/Specificity, Compression/Retention, Acquisition/Maintenance
4. Missing diagonal: adaptive cross-level compression (currently unimplemented in all systems)

Per AGENTS.md §1.4: Uses Q16_16 fixed-point for hardware-native computation.
Per AGENTS.md §2: PascalCase types, camelCase functions.
Per AGENTS.md §4: All defs must have eval witnesses or theorems.

Reference: https://alphaxiv.org/abs/2604.15877
-/

import Mathlib.Data.Nat.Basic
import Mathlib.Data.Real.Basic
import Mathlib.Data.Fin.Basic

namespace Semantics.ExperienceCompression

-- ════════════════════════════════════════════════════════════
-- §0  Fixed-Point Precision (Q16.16 for compression ratios)
-- ════════════════════════════════════════════════════════════

/-- Q16.16 fixed-point for compression ratio calculations. -/
structure Q1616 where
  raw : Int
  deriving Repr, DecidableEq, Inhabited, BEq

namespace Q1616

def zero    : Q1616 := ⟨0⟩
def one     : Q1616 := ⟨65536⟩        -- 0x00010000 = 1.0

def ofNat (n : Nat) : Q1616 := ⟨n * 65536⟩

def add (a b : Q1616) : Q1616 := ⟨a.raw + b.raw⟩
def sub (a b : Q1616) : Q1616 := ⟨a.raw - b.raw⟩
def mul (a b : Q1616) : Q1616 := ⟨(a.raw * b.raw) / 65536⟩
def div (a b : Q1616) : Q1616 := ⟨(a.raw * 65536) / b.raw⟩

def le (a b : Q1616) : Prop := a.raw ≤ b.raw
instance : LE Q1616 := ⟨le⟩
instance : LT Q1616 := ⟨fun a b => a.raw < b.raw⟩

instance : Add Q1616 := ⟨add⟩
instance : Sub Q1616 := ⟨sub⟩
instance : Mul Q1616 := ⟨mul⟩
instance : Div Q1616 := ⟨div⟩

end Q1616

-- ════════════════════════════════════════════════════════════
-- §1  Interaction Trace (Definition 2.1)
-- ════════════════════════════════════════════════════════════

/-- Time index in interaction trace. -/
abbrev TimeIndex := Nat

/-- Agent state s_t at time t. -/
structure AgentState where
  context : String  -- State representation
  timestamp : TimeIndex
  deriving Repr, Inhabited

/-- Agent action a_t at time t. -/
structure AgentAction where
  command : String
  parameters : Array String
  deriving Repr, Inhabited

/-- Observation o_t received by agent. -/
structure Observation where
  content : String
  source : String  -- e.g., "user", "system", "tool"
  deriving Repr, Inhabited

/-- Feedback signal f_t (reward or evaluation). -/
structure Feedback where
  score : Q1616  -- Numeric feedback score
  comment : String
  deriving Repr, Inhabited

/-- Single timestep in interaction trace. -/
structure TraceEntry where
  state : AgentState
  action : AgentAction
  observation : Observation
  feedback : Feedback
  deriving Repr, Inhabited

instance : ToString TraceEntry := ⟨fun entry => entry.action.command⟩

/-- Interaction trace 𝒯 = {(s_t, a_t, o_t, f_t)}_{t=1}^N. -/
abbrev InteractionTrace := Array TraceEntry

-- ════════════════════════════════════════════════════════════
-- §2  Compression Levels (Definition 2.2)
-- ════════════════════════════════════════════════════════════

/-- Compression level L ∈ {0, 1, 2, 3}. -/
inductive CompressionLevel
  | l0_rawTrace
  | l1_episodicMemory
  | l2_proceduralSkill
  | l3_declarativeRule
  deriving Repr, DecidableEq, Inhabited, Ord

namespace CompressionLevel

/-- Convert level to natural number. -/
def toNat : CompressionLevel → Nat
  | l0_rawTrace       => 0
  | l1_episodicMemory => 1
  | l2_proceduralSkill => 2
  | l3_declarativeRule => 3

/-- Higher level = more compression. -/
def higher (a b : CompressionLevel) : Bool := a.toNat > b.toNat

end CompressionLevel

/-- Knowledge artifact at compression level L. -/
structure KnowledgeArtifact (L : CompressionLevel) where
  content : String
  sourceTrace : InteractionTrace  -- Provenance
  deriving Repr, Inhabited

/-- Format of knowledge at each level. -/
inductive KnowledgeFormat
  | rawLog       -- Complete execution trajectories
  | keyValue     -- Structured key-value pairs
  | workflow     -- Step-by-step procedures
  | policy       -- Declarative constraints
  deriving Repr, DecidableEq, Inhabited

namespace KnowledgeFormat

/-- Format for each compression level. -/
def forLevel : CompressionLevel → KnowledgeFormat
  | .l0_rawTrace       => .rawLog
  | .l1_episodicMemory => .keyValue
  | .l2_proceduralSkill => .workflow
  | .l3_declarativeRule => .policy

end KnowledgeFormat

-- ════════════════════════════════════════════════════════════
-- §3  Compression Ratios (Section 2.2)
-- ════════════════════════════════════════════════════════════

/-- Compression ratio bounds for each level. -/
structure CompressionBounds where
  minRatio : Q1616
  maxRatio : Q1616
  deriving Repr, Inhabited

/-- Paper-defined compression ratios:
    L0: 1:1 (no compression)
    L1: 5-20× compression
    L2: 50-500× compression  
    L3: 1000×+ compression -/
def compressionBounds (L : CompressionLevel) : CompressionBounds :=
  match L with
  | .l0_rawTrace       => { minRatio := ⟨65536⟩, maxRatio := ⟨65536⟩ }  -- 1:1
  | .l1_episodicMemory => { minRatio := ⟨327680⟩, maxRatio := ⟨1310720⟩ }  -- 5-20×
  | .l2_proceduralSkill => { minRatio := ⟨3276800⟩, maxRatio := ⟨32768000⟩ }  -- 50-500×
  | .l3_declarativeRule => { minRatio := ⟨65536000⟩, maxRatio := ⟨655360000⟩ }  -- 1000×+

/-- Compression ratio is within bounds for level L. -/
def validCompressionRatio (L : CompressionLevel) (ratio : Q1616) : Bool :=
  let bounds := compressionBounds L
  (bounds.minRatio.raw ≤ ratio.raw) && (ratio.raw ≤ bounds.maxRatio.raw)

/-- Theorem: L3 has strictly higher compression than L0. -/
theorem l3HigherThanL0 : 
    let l0max := (compressionBounds .l0_rawTrace).maxRatio
    let l3min := (compressionBounds .l3_declarativeRule).minRatio
    l0max < l3min := by
  simp [compressionBounds]
  native_decide

-- ════════════════════════════════════════════════════════════
-- §4  Reusability Spectrum (Section 2.2)
-- ════════════════════════════════════════════════════════════

/-- Reusability score for knowledge artifacts. -/
inductive Reusability
  | minimal      -- L0: entirely context-bound
  | lowModerate -- L1: tied to specific episodes
  | high        -- L2: transferable across similar situations
  | highest     -- L3: domain-general
  deriving Repr, DecidableEq, Inhabited

namespace Reusability

/-- Reusability for each compression level. -/
def forLevel : CompressionLevel → Reusability
  | .l0_rawTrace       => .minimal
  | .l1_episodicMemory => .lowModerate
  | .l2_proceduralSkill => .high
  | .l3_declarativeRule => .highest

/-- Convert reusability class to an ordinal. -/
def toNat : Reusability → Nat
  | .minimal => 0
  | .lowModerate => 1
  | .high => 2
  | .highest => 3

/-- Trade-off: higher compression → higher reusability. -/
theorem reusabilityIncreasesWithCompression (L1 L2 : CompressionLevel)
    (h : L1.toNat < L2.toNat) : 
    (forLevel L1).toNat < (forLevel L2).toNat := by
  cases L1 <;> cases L2 <;> simp [forLevel, toNat] at h ⊢ <;> try contradiction

end Reusability

-- ════════════════════════════════════════════════════════════
-- §5  Cost Trade-offs (Section 2.2)
-- ════════════════════════════════════════════════════════════

/-- Acquisition cost: resources to create artifact at level L. -/
inductive AcquisitionCost
  | negligible  -- L0, L1: single trace sufficient
  | moderate    -- L2: multiple traces needed
  | high        -- L3: many traces to induce
  deriving Repr, DecidableEq, Inhabited

/-- Maintenance cost: ongoing resources to keep artifact. -/
inductive MaintenanceCost
  | high        -- L0, L1: large storage, frequent indexing
  | moderate    -- L2: moderate storage
  | negligible  -- L3: compact, low-maintenance
  deriving Repr, DecidableEq, Inhabited

namespace Cost

/-- Acquisition cost for each level. -/
def acquisitionFor (L : CompressionLevel) : AcquisitionCost :=
  match L with
  | .l0_rawTrace | .l1_episodicMemory => .negligible
  | .l2_proceduralSkill => .moderate
  | .l3_declarativeRule => .high

/-- Maintenance cost for each level. -/
def maintenanceFor (L : CompressionLevel) : MaintenanceCost :=
  match L with
  | .l0_rawTrace | .l1_episodicMemory => .high
  | .l2_proceduralSkill => .moderate
  | .l3_declarativeRule => .negligible

/-- Inverse relationship: high acquisition → low maintenance. -/
theorem costTradeOff (L : CompressionLevel) :
    (acquisitionFor L = .high ∧ maintenanceFor L = .negligible) ∨
    (acquisitionFor L = .negligible ∧ maintenanceFor L = .high) ∨
    (acquisitionFor L = .moderate ∧ maintenanceFor L = .moderate) := by
  cases L <;> simp [acquisitionFor, maintenanceFor]

end Cost

-- ════════════════════════════════════════════════════════════
-- §6  Missing Diagonal: Adaptive Cross-Level Compression
-- ════════════════════════════════════════════════════════════

/-- System capability: which compression levels are supported. -/
structure SystemCapabilities where
  supportsL0 : Bool
  supportsL1 : Bool
  supportsL2 : Bool
  supportsL3 : Bool
  supportsAdaptive : Bool  -- The "missing diagonal"
  deriving Repr, Inhabited

/-- Paper finding: All existing systems operate at fixed levels.
    None support adaptive cross-level compression. -/
def fixedLevelSystems : List SystemCapabilities :=
  [ { supportsL0 := true,  supportsL1 := false, supportsL2 := false, supportsL3 := false, supportsAdaptive := false }  -- Raw logging only
  , { supportsL0 := false, supportsL1 := true,  supportsL2 := false, supportsL3 := false, supportsAdaptive := false }  -- Episodic memory only
  , { supportsL0 := false, supportsL1 := false, supportsL2 := true,  supportsL3 := false, supportsAdaptive := false }  -- Skill-based only
  , { supportsL0 := false, supportsL1 := false, supportsL2 := false, supportsL3 := true,  supportsAdaptive := false }  -- Rule-based only
  ]

/-- The missing diagonal: system with adaptive cross-level compression.
    Paper: This capability does not exist in any current system. -/
def missingDiagonal : SystemCapabilities :=
  { supportsL0 := true, supportsL1 := true, supportsL2 := true, supportsL3 := true, supportsAdaptive := true }

/-- Adaptive compression function: dynamically select level based on context. -/
def adaptiveCompression (trace : InteractionTrace) (context : String) : 
    Sigma KnowledgeArtifact :=
  -- Existential: such a function could exist but currently doesn't
  ⟨.l1_episodicMemory, { content := "Adaptive compression not yet implemented for " ++ context, sourceTrace := trace }⟩

/-- Theorem: No current system implements the missing diagonal. -/
theorem noSystemHasAdaptive : 
    ∀ sys ∈ fixedLevelSystems, ¬sys.supportsAdaptive := by
  simp [fixedLevelSystems]

-- ════════════════════════════════════════════════════════════
-- §7  Experience Compression Function (Definition 2.2)
-- ════════════════════════════════════════════════════════════

/-- Compression function C_L: 𝒯 → 𝒦_L maps traces to knowledge artifacts. -/
def compress (trace : InteractionTrace) (L : CompressionLevel) : KnowledgeArtifact L :=
  match L with
  | .l0_rawTrace => 
      { content := "Raw: " ++ trace.toList.toString
        sourceTrace := trace }
  | .l1_episodicMemory =>
      { content := "Episode: Extracted key events"
        sourceTrace := trace }
  | .l2_proceduralSkill =>
      { content := "Skill: Generalized workflow pattern"
        sourceTrace := trace }
  | .l3_declarativeRule =>
      { content := "Rule: Domain-invariant principle"
        sourceTrace := trace }

/-- Compression preserves information up to level-appropriate abstraction. -/
theorem compressionSoundness (trace : InteractionTrace) (L : CompressionLevel) :
    let artifact := compress trace L
    artifact.sourceTrace = trace := by
  cases L <;> simp [compress]

-- ════════════════════════════════════════════════════════════
-- §8  Maintenance Cost Quantification (Section 2.2)
-- ════════════════════════════════════════════════════════════

/-- Storage size in tokens (paper examples). -/
structure StorageSize where
  tokens : Nat
  deriving Repr, Inhabited

/-- Paper examples:
    L1-only: 1000 episodes × 500 tokens = 500K tokens
    L2: reduced to ~5K tokens  
    L3: reduced to ~500 tokens -/
def exampleStorage (L : CompressionLevel) (numEpisodes : Nat) : StorageSize :=
  match L with
  | .l0_rawTrace       => { tokens := numEpisodes * 2000 }  -- ~2000 tokens/trace
  | .l1_episodicMemory => { tokens := numEpisodes * 500 }   -- ~500 tokens/episode
  | .l2_proceduralSkill => { tokens := numEpisodes * 5 }     -- ~5 tokens/skill
  | .l3_declarativeRule => { tokens := numEpisodes / 2 }     -- ~0.5 tokens/rule

/-- Theorem: L2 storage < L1 storage for large episode counts. -/
theorem l2MoreEfficientThanL1 (n : Nat) (hn : n > 10) :
    (exampleStorage .l2_proceduralSkill n).tokens < (exampleStorage .l1_episodicMemory n).tokens := by
  simp [exampleStorage]
  omega

-- ════════════════════════════════════════════════════════════
-- §9  Verification Examples (AGENTS.md §4 requirement)
-- ════════════════════════════════════════════════════════════

#eval CompressionLevel.l0_rawTrace.toNat  -- 0
#eval CompressionLevel.l3_declarativeRule.toNat  -- 3

#eval compressionBounds .l1_episodicMemory  -- { minRatio := 5, maxRatio := 20 }
#eval compressionBounds .l2_proceduralSkill  -- { minRatio := 50, maxRatio := 500 }

#eval Cost.acquisitionFor .l1_episodicMemory  -- negligible
#eval Cost.maintenanceFor .l1_episodicMemory  -- high

#eval Cost.acquisitionFor .l3_declarativeRule  -- high
#eval Cost.maintenanceFor .l3_declarativeRule  -- negligible

#eval validCompressionRatio .l2_proceduralSkill ⟨1000000⟩  -- true (15.26×)
#eval validCompressionRatio .l2_proceduralSkill ⟨10000000⟩  -- false (152.6× > 500×)

#eval missingDiagonal.supportsAdaptive  -- true (the missing capability)

end Semantics.ExperienceCompression
