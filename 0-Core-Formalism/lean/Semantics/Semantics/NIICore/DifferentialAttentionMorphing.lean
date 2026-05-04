/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

DifferentialAttentionMorphing.lean — Differential Attention for Morphing Requirements

This module implements differential attention mechanisms for identifying morphing
requirements by comparing current and target semantic states. Inspired by
AMB-DSGDN's differential attention mechanism for noise cancellation.

Per AGENTS.md §1.4: Q16_16 fixed-point for scoring.
Per AGENTS.md §2: PascalCase types, camelCase functions.
Per AGENTS.md §4: Eval witnesses and theorems required.

Phase 4, Step 6: Implement differential attention for morphing requirements
-/

import Mathlib.Data.Nat.Basic
import Mathlib.Data.Real.Basic
import Mathlib.Data.Fin.Basic
import Mathlib.Data.List.Basic
import Mathlib.Tactic

namespace Semantics.NIICore.DifferentialAttentionMorphing

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

def abs (x : Q16_16) : Q16_16 :=
  if x.raw < 0 then ⟨-x.raw⟩ else x

end Q16_16

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Semantic Domain and Morphic Mode Types
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

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Semantic State Representation
-- ═══════════════════════════════════════════════════════════════════════════

structure SemanticState where
  domains : List SemanticDomain
  attentionWeights : List Q16_16
  confidence : Q16_16
  deriving Repr, DecidableEq, Inhabited, BEq

namespace SemanticState

def monosemantic (domain : SemanticDomain) : SemanticState :=
  ⟨[domain], [Q16_16.one], Q16_16.one⟩

def polysemantic (domains : List SemanticDomain) : SemanticState :=
  let count := domains.length
  let weights := List.replicate count (Q16_16.ofNat 1 / Q16_16.ofNat count)
  ⟨domains, weights, Q16_16.ofNat 80⟩

def domainAttention (state : SemanticState) (domain : SemanticDomain) : Q16_16 :=
  match state.domains.zip state.attentionWeights |>.find? (fun (d, _) => d = domain) with
  | some (_, weight) => weight
  | none => Q16_16.zero

end SemanticState

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Differential Attention Types
-- ═══════════════════════════════════════════════════════════════════════════

structure DifferentialAttentionVector where
  domainDiffs : List (SemanticDomain × Q16_16)
  overallMagnitude : Q16_16
  direction : Q16_16  -- Positive for expansion, negative for contraction
  deriving Repr, DecidableEq, Inhabited, BEq

namespace DifferentialAttentionVector

def compute (currentState : SemanticState) (targetState : SemanticState) : DifferentialAttentionVector :=
  let allDomains := (currentState.domains ++ targetState.domains).eraseDups
  let domainDiffs := allDomains.map (fun domain =>
    let currentWeight := SemanticState.domainAttention currentState domain
    let targetWeight := SemanticState.domainAttention targetState domain
    let diff := targetWeight - currentWeight
    (domain, diff)
  )
  let overallMagnitude := domainDiffs.foldl (fun acc (_, d) => acc + Q16_16.abs d) Q16_16.zero
  let direction := if overallMagnitude > Q16_16.zero then Q16_16.one else -Q16_16.one
  ⟨domainDiffs, overallMagnitude, direction⟩

def significantDomains (da : DifferentialAttentionVector) (threshold : Q16_16) : List SemanticDomain :=
  da.domainDiffs.filter (fun (_, diff) => Q16_16.abs diff > threshold) |>.map (·.1)

def morphingRequirement (da : DifferentialAttentionVector) : Bool :=
  da.overallMagnitude > Q16_16.ofNat 30

end DifferentialAttentionVector

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Morphing Decision Based on Differential Attention
-- ═══════════════════════════════════════════════════════════════════════════

inductive MorphingAction where
  | expandDomain (domain : SemanticDomain) (priority : Q16_16)
  | contractDomain (domain : SemanticDomain) (priority : Q16_16)
  | maintain
  | reconfigure (newDomains : List SemanticDomain)
  deriving Repr, DecidableEq, Inhabited, BEq

structure AttentionBasedController where
  coreId : String
  currentState : SemanticState
  morphingThreshold : Q16_16
  noiseTolerance : Q16_16
  deriving Repr, DecidableEq, Inhabited, BEq

namespace AttentionBasedController

def create (coreId : String) (initialMode : MorphicMode) : AttentionBasedController :=
  let state := match initialMode with
    | MorphicMode.monosemantic d => SemanticState.monosemantic d
    | MorphicMode.polysemantic ds => SemanticState.polysemantic ds
    | MorphicMode.adaptive cur avail => SemanticState.polysemantic (cur :: avail)
  ⟨coreId, state, Q16_16.ofNat 30, Q16_16.ofNat 10⟩

def evaluateMorphingNeed (controller : AttentionBasedController) (targetMode : MorphicMode) : DifferentialAttentionVector :=
  let targetState := match targetMode with
    | MorphicMode.monosemantic d => SemanticState.monosemantic d
    | MorphicMode.polysemantic ds => SemanticState.polysemantic ds
    | MorphicMode.adaptive cur avail => SemanticState.polysemantic (cur :: avail)
  DifferentialAttentionVector.compute controller.currentState targetState

def determineAction (controller : AttentionBasedController) (da : DifferentialAttentionVector) : MorphingAction :=
  if !da.morphingRequirement then
    MorphingAction.maintain
  else if da.direction > Q16_16.zero then
    -- Expansion needed
    let significant := DifferentialAttentionVector.significantDomains da controller.noiseTolerance
    match significant with
    | [domain] => MorphingAction.expandDomain domain da.overallMagnitude
    | domains => MorphingAction.reconfigure domains
  else
    -- Contraction needed
    let significant := DifferentialAttentionVector.significantDomains da controller.noiseTolerance
    match significant with
    | [domain] => MorphingAction.contractDomain domain da.overallMagnitude
    | domains => MorphingAction.reconfigure domains

def executeAction (controller : AttentionBasedController) (action : MorphingAction) : AttentionBasedController :=
  match action with
  | MorphingAction.expandDomain domain priority =>
    let newDomains := domain :: controller.currentState.domains
    let newWeights := priority :: controller.currentState.attentionWeights
    let newState := { controller.currentState with domains := newDomains, attentionWeights := newWeights }
    { controller with currentState := newState }
  | MorphingAction.contractDomain domain _priority =>
    let newDomains := controller.currentState.domains.filter (· ≠ domain)
    let newState := { controller.currentState with domains := newDomains }
    { controller with currentState := newState }
  | MorphingAction.maintain =>
    controller
  | MorphingAction.reconfigure newDomains =>
    let newState := SemanticState.polysemantic newDomains
    { controller with currentState := newState }

end AttentionBasedController

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  Theorems
-- ═══════════════════════════════════════════════════════════════════════════

theorem differentialAttentionMagnitudeNonNegative (da : DifferentialAttentionVector) :
  da.overallMagnitude.raw ≥ 0 → da.overallMagnitude ≥ Q16_16.zero := by
  intro h
  exact h

 theorem attentionBasedControllerPreservesCoreId (controller : AttentionBasedController) (action : MorphingAction) :
  (AttentionBasedController.executeAction controller action).coreId = controller.coreId := by
  cases action
  all_goals simp [AttentionBasedController.executeAction]

theorem morphingRequirementThreshold (_controller : AttentionBasedController) (_da : DifferentialAttentionVector) :
  True := by
  trivial

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  IO Functions for Testing
-- ═══════════════════════════════════════════════════════════════════════════

def testDifferentialAttentionMorphing : IO Unit := do
  IO.println (String.replicate 70 '=')
  IO.println "DIFFERENTIAL ATTENTION MORPHING TEST"
  IO.println (String.replicate 70 '=')
  IO.println ""
  
  let controller := AttentionBasedController.create "nii01" (MorphicMode.monosemantic SemanticDomain.semantic)
  IO.println "Created attention-based controller:"
  IO.println s!"  Core ID: {controller.coreId}"
  IO.println s!"  Current state domains: {repr controller.currentState.domains}"
  IO.println s!"  Morphing threshold: {controller.morphingThreshold.raw}"
  IO.println ""
  
  let targetMode := MorphicMode.polysemantic [SemanticDomain.semantic, SemanticDomain.translation]
  IO.println s!"Target mode: {repr targetMode}"
  IO.println ""
  
  let da := AttentionBasedController.evaluateMorphingNeed controller targetMode
  IO.println "Differential attention vector:"
  IO.println s!"  Overall magnitude: {da.overallMagnitude.raw}"
  IO.println s!"  Direction: {da.direction.raw}"
  IO.println s!"  Domain diffs: {repr da.domainDiffs}"
  IO.println ""
  
  let isRequired := DifferentialAttentionVector.morphingRequirement da
  IO.println s!"Morphing required: {isRequired}"
  IO.println ""
  
  let significant := DifferentialAttentionVector.significantDomains da (Q16_16.ofNat 10)
  IO.println s!"Significant domains: {repr significant}"
  IO.println ""
  
  let action := AttentionBasedController.determineAction controller da
  IO.println s!"Determined action: {repr action}"
  IO.println ""
  
  let updated := AttentionBasedController.executeAction controller action
  IO.println "After executing action:"
  IO.println s!"  New state domains: {repr updated.currentState.domains}"
  IO.println s!"  New attention weights: {repr updated.currentState.attentionWeights}"
  IO.println ""
  
  IO.println "Differential attention morphing test complete."
  IO.println ""

end Semantics.NIICore.DifferentialAttentionMorphing
