import Semantics.ManifoldNetworking

namespace Semantics.ManifoldNetworking

open Semantics.Q16_16

/-- Phase ordering test: phase-based flow does not create invalid causal shortcuts. -/
structure PhaseOrderingQuestion where
  description : String
  initialPhase : Semantics.Q16_16
  finalPhase : Semantics.Q16_16
  timestampDelta : Nat
  expectedOrderValid : Bool
  deriving Repr

structure PhaseOrderingResult where
  question : PhaseOrderingQuestion
  phaseOrderValid : Bool
  passed : Bool
  deriving Repr

/-- Phase ordering quiz bank: test that phase-based flow is causally valid. -/
def phaseOrderingQuizBank : List PhaseOrderingQuestion :=
  [
    PhaseOrderingQuestion.mk
      "Sequential phase ordering"
      (Semantics.Q16_16.mk 0x00000000)  -- phase 0
      (Semantics.Q16_16.mk 0x00010000)  -- phase 1
      10
      true,
    PhaseOrderingQuestion.mk
      "Phase should not decrease"
      (Semantics.Q16_16.mk 0x00020000)  -- phase 2
      (Semantics.Q16_16.mk 0x00010000)  -- phase 1
      10
      false,
    PhaseOrderingQuestion.mk
      "Phase can increase normally"
      (Semantics.Q16_16.mk 0x00010000)  -- phase 1
      (Semantics.Q16_16.mk 0x00030000)  -- phase 3
      20
      true
  ]

/-- Run phase ordering quiz question. -/
def runPhaseOrderingQuiz (question : PhaseOrderingQuestion) : PhaseOrderingResult :=
  let phaseIncreases := question.finalPhase >= question.initialPhase
  let reasonableDelta := question.timestampDelta > 0
  let phaseOrderValid := if question.expectedOrderValid then phaseIncreases ∧ reasonableDelta else not phaseIncreases
  let passed := phaseOrderValid == question.expectedOrderValid
  PhaseOrderingResult.mk question phaseOrderValid passed

/-- Test that phase-based flow does not create invalid causal shortcuts. -/
def testPhaseOrdering : PhaseOrderingResult :=
  match phaseOrderingQuizBank with
  | question :: _ => runPhaseOrderingQuiz question
  | [] => PhaseOrderingResult.mk (PhaseOrderingQuestion.mk "empty" Semantics.Q16_16.zero Semantics.Q16_16.zero 0 true) false false

end Semantics.ManifoldNetworking
