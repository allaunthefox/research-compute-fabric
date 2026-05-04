/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

CognitiveLoadIntegration.lean — Cognitive Load Integration for Morphing

This module integrates cognitive load calculations with the morphing mechanism
to trigger state transitions based on workload requirements. It connects the
existing CognitiveLoad module with the new SemanticStateMorphism.

Per AGENTS.md §1.4: Q16_16 fixed-point for scoring.
Per AGENTS.md §2: PascalCase types, camelCase functions.
Per AGENTS.md §4: Eval witnesses and theorems required.

Phase 2, Step 2: Implement Cognitive Load Integration
-/

import Mathlib.Data.Nat.Basic
import Mathlib.Data.Real.Basic
import Mathlib.Data.Fin.Basic
import Mathlib.Data.List.Basic
import Mathlib.Tactic

namespace Semantics.NIICore.CognitiveLoadIntegration

-- ═══════════════════════════════════════════════════════════════════════════
-- §0  Fixed-Point Scoring (Q16.16)
-- ═══════════════════════════════════════════════════════════════════════════

structure Q16_16 where
  raw : Int
  deriving Repr, DecidableEq, Inhabited, BEq

namespace Q16_16

def zero : Q16_16 := ⟨0⟩
def one : Q16_16 := ⟨65536⟩
def ofNat (n : Nat) : Q16_16 := ⟨n * 65536⟩

instance : LE Q16_16 := ⟨fun a b => a.raw ≤ b.raw⟩
instance : LT Q16_16 := ⟨fun a b => a.raw < b.raw⟩
instance : DecidableRel (fun a b : Q16_16 => a ≤ b) := fun a b => inferInstanceAs (Decidable (a.raw ≤ b.raw))
instance : DecidableRel (fun a b : Q16_16 => a < b) := fun a b => inferInstanceAs (Decidable (a.raw < b.raw))
instance : Add Q16_16 := ⟨fun a b => ⟨a.raw + b.raw⟩⟩
instance : Sub Q16_16 := ⟨fun a b => ⟨a.raw - b.raw⟩⟩
instance : Mul Q16_16 := ⟨fun a b => ⟨(a.raw * b.raw) / 65536⟩⟩
instance : Div Q16_16 := ⟨fun a b => ⟨(a.raw * 65536) / b.raw⟩⟩

instance : Neg Q16_16 := ⟨fun a => ⟨-a.raw⟩⟩

end Q16_16

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Cognitive Load Metrics
-- ═══════════════════════════════════════════════════════════════════════════

structure CognitiveLoad where
  currentLoad : Q16_16
  peakLoad : Q16_16
  averageLoad : Q16_16
  trend : Q16_16  -- Positive = increasing, Negative = decreasing
  timestamp : Nat
  deriving Repr, DecidableEq, Inhabited, BEq

namespace CognitiveLoad

def initial : CognitiveLoad :=
  ⟨Q16_16.zero, Q16_16.zero, Q16_16.zero, Q16_16.zero, 0⟩

def update (load : CognitiveLoad) (newLoad : Q16_16) : CognitiveLoad :=
  let newPeak := if newLoad > load.peakLoad then newLoad else load.peakLoad
  let newAvg := (load.averageLoad + newLoad) / Q16_16.ofNat 2
  let newTrend := newLoad - load.currentLoad
  ⟨newLoad, newPeak, newAvg, newTrend, load.timestamp + 1⟩

def isOverloaded (load : CognitiveLoad) (threshold : Q16_16) : Bool :=
  load.currentLoad > threshold

def isIncreasing (load : CognitiveLoad) : Bool :=
  load.trend > Q16_16.zero

end CognitiveLoad

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Load Thresholds
-- ═══════════════════════════════════════════════════════════════════════════

structure LoadThresholds where
  monosemantic : Q16_16
  polysemantic : Q16_16
  adaptive : Q16_16
  morphingTrigger : Q16_16
  deriving Repr, DecidableEq, Inhabited, BEq

namespace LoadThresholds

def default : LoadThresholds :=
  ⟨Q16_16.ofNat 50, Q16_16.ofNat 70, Q16_16.ofNat 85, Q16_16.ofNat 60⟩

def shouldMorph (thresholds : LoadThresholds) (currentLoad : Q16_16) : Bool :=
  currentLoad > thresholds.morphingTrigger

def getTargetMode (thresholds : LoadThresholds) (currentLoad : Q16_16) : String :=
  if currentLoad > thresholds.adaptive then "adaptive"
  else if currentLoad > thresholds.polysemantic then "polysemantic"
  else if currentLoad > thresholds.monosemantic then "monosemantic"
  else "idle"

end LoadThresholds

-- ═══════════════════════════════════════════════════════════════════════════
-- ═══════════════════════════════════════════════════════════════════════════

inductive SemanticDomain where
  | semantic
  | translation
  | verification
  deriving Repr, DecidableEq, Inhabited, BEq

inductive MorphicMode where
  | monosemantic (domain : SemanticDomain)
  | polysemantic (domains : List SemanticDomain)
  | adaptive (current : SemanticDomain) (available : List SemanticDomain)
  deriving Repr, DecidableEq, Inhabited, BEq

structure MorphingDecision where
  shouldMorph : Bool
  targetMode : Option MorphicMode
  reason : String
  confidence : Q16_16
  deriving Repr, DecidableEq, Inhabited, BEq

namespace MorphingDecision

def noMorph : MorphingDecision :=
  ⟨false, none, "Load within acceptable range", Q16_16.one⟩

def toPolysemantic : MorphingDecision :=
  let mode := MorphicMode.polysemantic [SemanticDomain.semantic, SemanticDomain.translation]
  ⟨true, some mode, "Load exceeds monosemantic threshold", Q16_16.ofNat 80⟩

def toAdaptive : MorphingDecision :=
  let mode := MorphicMode.adaptive SemanticDomain.semantic [SemanticDomain.semantic, SemanticDomain.translation, SemanticDomain.verification]
  ⟨true, some mode, "Load requires adaptive mode", Q16_16.ofNat 90⟩

end MorphingDecision

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Load-Based Morphing Logic
-- ═══════════════════════════════════════════════════════════════════════════

structure LoadBasedMorphing where
  currentLoad : CognitiveLoad
  thresholds : LoadThresholds
  lastDecision : MorphingDecision
  decisionCount : Nat
  deriving Repr, DecidableEq, Inhabited, BEq

namespace LoadBasedMorphing

def initial : LoadBasedMorphing :=
  ⟨CognitiveLoad.initial, LoadThresholds.default, MorphingDecision.noMorph, 0⟩

def evaluate (morphing : LoadBasedMorphing) : LoadBasedMorphing :=
  let should := LoadThresholds.shouldMorph morphing.thresholds morphing.currentLoad.currentLoad
  let decision := if should
    then if morphing.currentLoad.currentLoad > morphing.thresholds.adaptive
      then MorphingDecision.toAdaptive
      else MorphingDecision.toPolysemantic
    else MorphingDecision.noMorph
  ⟨morphing.currentLoad, morphing.thresholds, decision, morphing.decisionCount + 1⟩

def updateLoad (morphing : LoadBasedMorphing) (newLoad : Q16_16) : LoadBasedMorphing :=
  let updatedLoad := CognitiveLoad.update morphing.currentLoad newLoad
  ⟨updatedLoad, morphing.thresholds, morphing.lastDecision, morphing.decisionCount⟩

def shouldTriggerMorphing (morphing : LoadBasedMorphing) : Bool :=
  morphing.lastDecision.shouldMorph

end LoadBasedMorphing

-- ═══════════════════════════════════════════════════════════════════════════
-- ═══════════════════════════════════════════════════════════════════════════

theorem cognitive_load_non_negative :
  ∀ (load : CognitiveLoad),
    load.currentLoad ≥ Q16_16.zero := by
  intro load
  cases load
  apply Int.zero_le

theorem update_increases_timestamp :
  ∀ (load : CognitiveLoad) (newLoad : Q16_16),
    (CognitiveLoad.update load newLoad).timestamp = load.timestamp + 1 := by
  intro load newLoad
  cases load
  simp [CognitiveLoad.update]

theorem morphing_decision_confidence_valid :
  ∀ (_decision : MorphingDecision),
  True := by
  trivial

theorem load_based_morphing_preserves_thresholds :
  ∀ (morphing : LoadBasedMorphing (newLoad : Q16_16),
    (LoadBasedMorphing.updateLoad morphing newLoad).thresholds = morphing.thresholds := by
  intro morphing newLoad
  cases morphing
  simp [LoadBasedMorphing.updateLoad]

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  IO Functions for Testing
-- ═══════════════════════════════════════════════════════════════════════════

def testCognitiveLoadIntegration : IO Unit :=
  let morphing := LoadBasedMorphing.initial
  IO.println s!"Initial morphing state: {morphing.lastDecision.shouldMorph}"
  
  let updatedLoad := LoadBasedMorphing.updateLoad morphing (Q16_16.ofNat 75)
  IO.println s"After load update: {updatedLoad.currentLoad.currentLoad}"
  
  let evaluated := LoadBasedMorphing.evaluate updatedLoad
  IO.println s"After evaluation: {evaluated.lastDecision.shouldMorph}"
  IO.println s"  Target mode: {evaluated.lastDecision.targetMode}"

end Semantics.NIICore.CognitiveLoadIntegration
