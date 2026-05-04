/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

SemanticStateMorphism.lean — Semantic State Morphism State Machine

This module implements the SemanticStateMorphism state machine for core mode
transitions. It defines state types, transition functions, and state machine
logic for NII cores to morph between semantic domains.

Per AGENTS.md §1.4: Q16_16 fixed-point for scoring.
Per AGENTS.md §2: PascalCase types, camelCase functions.
Per AGENTS.md §4: Eval witnesses and theorems required.

Phase 2, Step 1: Implement SemanticStateMorphism state machine
-/

import Mathlib.Data.Nat.Basic
import Mathlib.Data.Real.Basic
import Mathlib.Data.Fin.Basic
import Mathlib.Data.List.Basic
import Mathlib.Tactic

namespace Semantics.NIICore.SemanticStateMorphism

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
-- §1  Semantic State Types
-- ═══════════════════════════════════════════════════════════════════════════

inductive SemanticDomain where
  | semantic      -- Pattern recognition and semantic extraction
  | translation   -- Rust → Lean translation
  | verification  -- Proof generation
  | math          -- Mathematical reasoning
  | logic         -- Logical deduction
  | language      -- Natural language processing
  | code          -- Code generation and analysis
  deriving Repr, DecidableEq, Inhabited, BEq

inductive MorphicMode where
  | monosemantic (domain : SemanticDomain)
  | polysemantic (domains : List SemanticDomain)
  | adaptive (current : SemanticDomain) (available : List SemanticDomain)
  deriving Repr, DecidableEq, Inhabited, BEq

inductive StateTransition where
  | idle : StateTransition
  | transitioning : MorphicMode → MorphicMode → StateTransition
  | active : MorphicMode → StateTransition
  | error : String → StateTransition
  deriving Repr, DecidableEq, Inhabited, BEq

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Semantic State Machine
-- ═══════════════════════════════════════════════════════════════════════════

structure SemanticState where
  coreId : String
  currentMode : MorphicMode
  transition : StateTransition
  timestamp : Nat
  cognitiveLoad : Q16_16
  deriving Repr, DecidableEq, Inhabited, BEq

namespace SemanticState

def initial (coreId : String) : SemanticState :=
  let mode := MorphicMode.monosemantic SemanticDomain.semantic
  ⟨coreId, mode, StateTransition.active mode, 0, Q16_16.zero⟩

def transitionTo (state : SemanticState) (newMode : MorphicMode) (load : Q16_16) : SemanticState :=
  let trans := StateTransition.transitioning state.currentMode newMode
  ⟨state.coreId, newMode, trans, state.timestamp + 1, load⟩

def setIdle (state : SemanticState) : SemanticState :=
  ⟨state.coreId, state.currentMode, StateTransition.idle, state.timestamp + 1, Q16_16.zero⟩

def setError (state : SemanticState) (errorMsg : String) : SemanticState :=
  ⟨state.coreId, state.currentMode, StateTransition.error errorMsg, state.timestamp + 1, Q16_16.zero⟩

end SemanticState

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Transition Functions
-- ═══════════════════════════════════════════════════════════════════════════

structure TransitionCost where
  fromMode : MorphicMode
  toMode : MorphicMode
  cost : Q16_16
  validity : Bool
  deriving Repr, DecidableEq, Inhabited, BEq

namespace TransitionCost

def calculate (fromMode toMode : MorphicMode) : TransitionCost :=
  match fromMode, toMode with
  | MorphicMode.monosemantic _, MorphicMode.monosemantic _ => ⟨fromMode, toMode, Q16_16.zero, true⟩
  | MorphicMode.monosemantic _, MorphicMode.polysemantic _ => ⟨fromMode, toMode, Q16_16.ofNat 10, true⟩
  | MorphicMode.monosemantic _, MorphicMode.adaptive _ _ => ⟨fromMode, toMode, Q16_16.ofNat 15, true⟩
  | MorphicMode.polysemantic _, MorphicMode.monosemantic _ => ⟨fromMode, toMode, Q16_16.ofNat 5, true⟩
  | MorphicMode.polysemantic _, MorphicMode.polysemantic _ => ⟨fromMode, toMode, Q16_16.ofNat 3, true⟩
  | MorphicMode.polysemantic _, MorphicMode.adaptive _ _ => ⟨fromMode, toMode, Q16_16.ofNat 8, true⟩
  | MorphicMode.adaptive _ _, MorphicMode.monosemantic _ => ⟨fromMode, toMode, Q16_16.ofNat 7, true⟩
  | MorphicMode.adaptive _ _, MorphicMode.polysemantic _ => ⟨fromMode, toMode, Q16_16.ofNat 6, true⟩
  | MorphicMode.adaptive _ _, MorphicMode.adaptive _ _ => ⟨fromMode, toMode, Q16_16.ofNat 4, true⟩

def isTransitionValid (cost : TransitionCost) : Bool :=
  cost.validity

end TransitionCost

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  State Machine Logic
-- ═══════════════════════════════════════════════════════════════════════════

structure StateMachine where
  states : List SemanticState
  currentState : SemanticState
  transitionHistory : List TransitionCost
  deriving Repr, DecidableEq, Inhabited, BEq

namespace StateMachine

def initial (coreId : String) : StateMachine :=
  let initState := SemanticState.initial coreId
  ⟨[initState], initState, []⟩

def transition (machine : StateMachine) (newMode : MorphicMode) (load : Q16_16) : StateMachine :=
  let cost := TransitionCost.calculate machine.currentState.currentMode newMode
  let newState := SemanticState.transitionTo machine.currentState newMode load
  let newStates := newState :: machine.states
  let newHistory := cost :: machine.transitionHistory
  ⟨newStates, newState, newHistory⟩

def canTransition (machine : StateMachine) (newMode : MorphicMode) : Bool :=
  let cost := TransitionCost.calculate machine.currentState.currentMode newMode
  TransitionCost.isTransitionValid cost

def setIdle (machine : StateMachine) : StateMachine :=
  let newState := SemanticState.setIdle machine.currentState
  let newStates := newState :: machine.states
  ⟨newStates, newState, machine.transitionHistory⟩

end StateMachine

-- ═══════════════════════════════════════════════════════════════════════════
-- ═══════════════════════════════════════════════════════════════════════════

theorem transition_cost_non_negative :
  ∀ (fromMode toMode : MorphicMode),
    (TransitionCost.calculate fromMode toMode).cost ≥ Q16_16.zero := by
  intro fromMode toMode
  cases fromMode
  <;> cases toMode
  <;> simp [TransitionCost.calculate, Q16_16.zero, Q16_16.ofNat]
  apply Nat.zero_le

theorem state_machine_preserves_core_id :
  ∀ (machine : StateMachine) (newMode : MorphicMode) (load : Q16_16),
    (StateMachine.transition machine newMode load).currentState.coreId = machine.currentState.coreId := by
  intro machine newMode load
  cases machine
  simp [StateMachine.transition, SemanticState.transitionTo]

theorem idle_state_has_zero_cognitive_load :
  ∀ (state : SemanticState),
    (SemanticState.setIdle state).cognitiveLoad = Q16_16.zero := by
  intro state
  cases state
  simp [SemanticState.setIdle]

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  IO Functions for Testing
-- ═══════════════════════════════════════════════════════════════════════════

def testStateMachine : IO Unit :=
  let machine := StateMachine.initial "nii01"
  IO.println s!"Initial state: {machine.currentState.currentMode}"
  
  let newMode := MorphicMode.polysemantic [SemanticDomain.semantic, SemanticDomain.translation]
  let newMachine := StateMachine.transition machine newMode Q16_16.ofNat 50
  IO.println s"After transition: {newMachine.currentState.currentMode}"
  
  let canTrans := StateMachine.canTransition machine newMode
  IO.println s!"Can transition: {canTrans}"

end Semantics.NIICore.SemanticStateMorphism
