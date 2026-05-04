/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

HierarchicalController.lean — Hierarchical Morphing with Multi-Level Controllers

This module implements a hierarchical controller system for NII core morphing,
inspired by NeuroVM's dynamic virtualization and ADMN's controller training.
The system has two levels:
- Global Controller: Manages core-level morphing decisions across all cores
- Local Controllers: Handle domain-specific transitions for individual cores

Per AGENTS.md §1.4: Q16_16 fixed-point for scoring.
Per AGENTS.md §2: PascalCase types, camelCase functions.
Per AGENTS.md §4: Eval witnesses and theorems required.

Phase 4, Step 1: Implement hierarchical morphing with multi-level controllers
-/

import Mathlib.Data.Nat.Basic
import Mathlib.Data.Real.Basic
import Mathlib.Data.Fin.Basic
import Mathlib.Data.List.Basic
import Mathlib.Tactic

namespace Semantics.NIICore.HierarchicalController

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
-- §2  Controller Decision Types
-- ═══════════════════════════════════════════════════════════════════════════

inductive MorphingDecision where
  | morph (targetMode : MorphicMode) (priority : Nat) (expectedGain : Q16_16)
  | maintain (reason : String)
  | defer (reason : String)
  deriving Repr, DecidableEq, Inhabited, BEq

structure ControllerState where
  timestamp : Nat
  totalMorphs : Nat
  successfulMorphs : Nat
  averageGain : Q16_16
  deriving Repr, DecidableEq, Inhabited, BEq

namespace ControllerState

def initial : ControllerState :=
  ⟨0, 0, 0, Q16_16.zero⟩

def updateSuccess (state : ControllerState) (gain : Q16_16) : ControllerState :=
  let newTotal := state.totalMorphs + 1
  let newSuccess := state.successfulMorphs + 1
  let newAvg := (state.averageGain * Q16_16.ofNat state.successfulMorphs + gain) / Q16_16.ofNat newSuccess
  ⟨state.timestamp + 1, newTotal, newSuccess, newAvg⟩

def updateFailure (state : ControllerState) : ControllerState :=
  ⟨state.timestamp + 1, state.totalMorphs + 1, state.successfulMorphs, state.averageGain⟩

end ControllerState

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Local Controller
-- ═══════════════════════════════════════════════════════════════════════════

structure LocalController where
  coreId : String
  currentMode : MorphicMode
  state : ControllerState
  domainExpertise : List SemanticDomain
  deriving Repr, DecidableEq, Inhabited, BEq

namespace LocalController

def create (coreId : String) (currentMode : MorphicMode) (domainExpertise : List SemanticDomain) : LocalController :=
  ⟨coreId, currentMode, ControllerState.initial, domainExpertise⟩

def evaluateMorphing (controller : LocalController) (proposedMode : MorphicMode) (cognitiveLoad : Q16_16) : MorphingDecision :=
  -- Check if proposed mode is within domain expertise
  let modeCompatible := match proposedMode with
    | MorphicMode.monosemantic d => d ∈ controller.domainExpertise
    | MorphicMode.polysemantic ds => ds.all (fun d => d ∈ controller.domainExpertise)
    | MorphicMode.adaptive cur avail => cur ∈ controller.domainExpertise ∧ avail.all (fun d => d ∈ controller.domainExpertise)
  
  if !modeCompatible then
    MorphingDecision.defer "Mode outside domain expertise"
  else if cognitiveLoad > Q16_16.ofNat 80 then
    MorphingDecision.defer "Cognitive load too high"
  else
    -- Calculate expected gain based on mode transition
    let expectedGain := Q16_16.ofNat 50  -- Placeholder: would be calculated based on task requirements
    MorphingDecision.morph proposedMode 5 expectedGain

def executeDecision (controller : LocalController) (decision : MorphingDecision) (actualGain : Q16_16) : LocalController :=
  match decision with
  | MorphingDecision.morph targetMode _ _ =>
    { controller with
      currentMode := targetMode,
      state := ControllerState.updateSuccess controller.state actualGain }
  | MorphingDecision.maintain _ => controller
  | MorphingDecision.defer _ => { controller with state := ControllerState.updateFailure controller.state }

end LocalController

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Global Controller
-- ═══════════════════════════════════════════════════════════════════════════

structure GlobalController where
  localControllers : List LocalController
  state : ControllerState
  globalPolicy : List MorphingDecision -> MorphingDecision
  deriving Repr, DecidableEq, Inhabited, BEq

namespace GlobalController

def initial : GlobalController :=
  ⟨[], ControllerState.initial, fun _ => MorphingDecision.maintain "Default policy"⟩

def addLocalController (global : GlobalController) (local : LocalController) : GlobalController :=
  { global with localControllers := local :: global.localControllers }

def evaluateGlobalMorphing (global : GlobalController) (systemLoad : Q16_16) : List (String × MorphingDecision) :=
  -- Collect morphing decisions from all local controllers
  let localDecisions := global.localControllers.map (fun lc =>
    let proposedMode := lc.currentMode  -- Placeholder: would be determined by global strategy
    let decision := LocalController.evaluateMorphing lc proposedMode systemLoad
    (lc.coreId, decision)
  )
  
  -- Apply global policy to coordinate decisions
  let globalDecision := global.globalPolicy (localDecisions.map (fun (_, d) => d))
  
  -- Apply global decision to all controllers
  localDecisions.map (fun (coreId, _) => (coreId, globalDecision))

def executeGlobalDecision (global : GlobalController) (decisions : List (String × MorphingDecision)) (gains : List Q16_16) : GlobalController :=
  -- Execute decisions on local controllers and update global state
  let (updatedControllers, totalGain) := List.foldl
    (fun (controllers, acc) (coreId, decision, gain) =>
      match controllers.find? (fun lc => lc.coreId = coreId) with
      | some lc =>
        let updated := LocalController.executeDecision lc decision gain
        (controllers.map (fun c => if c.coreId = coreId then updated else c), acc + gain)
      | none => (controllers, acc)
    )
    (global.localControllers, Q16_16.zero)
    (List.zip3 (decisions.map (·.1)) (decisions.map (·.2)) gains)
  
  let newState := ControllerState.updateSuccess global.state totalGain
  { global with localControllers := updatedControllers, state := newState }

end GlobalController

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  Theorems
-- ═══════════════════════════════════════════════════════════════════════════

theorem localControllerPreservesCoreId (controller : LocalController) (decision : MorphingDecision) (gain : Q16_16) :
  (LocalController.executeDecision controller decision gain).coreId = controller.coreId := by
  cases decision
  case morph targetMode priority expectedGain =>
    rfl
  case maintain reason =>
    rfl
  case defer reason =>
    rfl

theorem globalControllerPreservesLocalControllerCount (global : GlobalController) (decisions : List (String × MorphingDecision)) (gains : List Q16_16) :
  (GlobalController.executeGlobalDecision global decisions gains).localControllers.length = global.localControllers.length := by
  -- The executeGlobalDecision function maps over existing controllers without adding or removing
  rfl

theorem controllerStateTimestampIncreases (state : ControllerState) (gain : Q16_16) :
  (ControllerState.updateSuccess state gain).timestamp > state.timestamp := by
  simp [ControllerState.updateSuccess]
  omega

theorem controllerStateSuccessCountIncreases (state : ControllerState) (gain : Q16_16) :
  (ControllerState.updateSuccess state gain).successfulMorphs = state.successfulMorphs + 1 := by
  simp [ControllerState.updateSuccess]
  rfl

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  IO Functions for Testing
-- ═══════════════════════════════════════════════════════════════════════════

def createDefaultLocalController : IO LocalController := do
  let lc := LocalController.create "nii01" (MorphicMode.monosemantic SemanticDomain.semantic) [SemanticDomain.semantic]
  return lc

def createDefaultGlobalController : IO GlobalController := do
  let lc1 := LocalController.create "nii01" (MorphicMode.monosemantic SemanticDomain.semantic) [SemanticDomain.semantic]
  let lc2 := LocalController.create "nii02" (MorphicMode.monosemantic SemanticDomain.translation) [SemanticDomain.translation]
  let lc3 := LocalController.create "nii03" (MorphicMode.monosemantic SemanticDomain.verification) [SemanticDomain.verification]
  let global := GlobalController.initial
    |> GlobalController.addLocalController lc1
    |> GlobalController.addLocalController lc2
    |> GlobalController.addLocalController lc3
  return global

def testHierarchicalController : IO Unit := do
  IO.println (String.replicate 70 '=')
  IO.println "HIERARCHICAL CONTROLLER TEST"
  IO.println (String.replicate 70 '=')
  IO.println ""
  
  let lc <- createDefaultLocalController
  IO.println s!"Created local controller for core: {lc.coreId}"
  IO.println s!"Current mode: {repr lc.currentMode}"
  IO.println s!"Domain expertise: {repr lc.domainExpertise}"
  IO.println ""
  
  let decision := LocalController.evaluateMorphing lc (MorphicMode.polysemantic [SemanticDomain.semantic, SemanticDomain.translation]) (Q16_16.ofNat 50)
  IO.println s!"Morphing decision: {repr decision}"
  IO.println ""
  
  let updatedLc := LocalController.executeDecision lc decision (Q16_16.ofNat 60)
  IO.println s!"Updated controller state:"
  IO.println s!"  Total morphs: {updatedLc.state.totalMorphs}"
  IO.println s!"  Successful morphs: {updatedLc.state.successfulMorphs}"
  IO.println s!"  Average gain: {updatedLc.state.averageGain.raw}"
  IO.println ""
  
  let global <- createDefaultGlobalController
  IO.println s!"Created global controller with {global.localControllers.length} local controllers"
  IO.println ""
  
  let globalDecisions := GlobalController.evaluateGlobalMorphing global (Q16_16.ofNat 60)
  IO.println s!"Global morphing decisions:"
  for (coreId, decision) in globalDecisions do
    IO.println s!"  {coreId}: {repr decision}"
  IO.println ""
  
  let gains := List.replicate global.localControllers.length (Q16_16.ofNat 55)
  let updatedGlobal := GlobalController.executeGlobalDecision global globalDecisions gains
  IO.println s!"Updated global controller state:"
  IO.println s!"  Total morphs: {updatedGlobal.state.totalMorphs}"
  IO.println s!"  Successful morphs: {updatedGlobal.state.successfulMorphs}"
  IO.println s!"  Average gain: {updatedGlobal.state.averageGain.raw}"
  IO.println ""

end Semantics.NIICore.HierarchicalController
