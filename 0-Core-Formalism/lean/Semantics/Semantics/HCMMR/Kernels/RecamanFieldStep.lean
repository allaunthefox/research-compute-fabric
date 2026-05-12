/-
RecamanFieldStep.lean — Recamán signed-step reflex kernel for HCMMR field traversal.

Recamán sequence: a_0=0, a_n = a_{n-1}-n if positive and unused, else a_{n-1}+n.
HCMMR mapping: try negative/Underverse step → if admissible and unoccupied → commit;
else reflect into positive ladder. Each step is a semicircle in circle-packing:
center m_n = (a_{n-1}+a_n)/2, radius r_n = n/2, sign s_n ∈ {+,-}.
-/

import Semantics.HCMMR.Core
import Semantics.FixedPoint

namespace Semantics.HCMMR.Kernels.RecamanFieldStep

open Semantics.HCMMR.Core
open Semantics.FixedPoint (Q16_16)

structure RecamanStep where
  stepIndex         : Nat
  currentState      : Q16_16
  nextState         : Q16_16
  attemptedNegative : Bool
  reflectedPositive : Bool
  residual          : Q16_16
  deriving Repr, BEq, DecidableEq, Inhabited

structure RecamanArc where
  center    : Q16_16
  radius    : Q16_16
  sign      : Q16_16
  arcLength : Q16_16
  curvature : Q16_16
  deriving Repr, BEq, DecidableEq, Inhabited

def recamanFieldStep (currentState : Q16_16) (stepIndex : Nat) (visitedSet : List Q16_16) (fieldGate : Gate) : RecamanStep :=
  let n := Q16_16.ofInt (Int.ofNat stepIndex)
  let negativeCandidate := currentState - n
  let negativeValid := Q16_16.gt negativeCandidate Q16_16.zero
  let negativeUnused := ¬ visitedSet.any (fun v => v == negativeCandidate)
  let gateAdmits := fieldGate.verdict == GateVerdict.admit
  if negativeValid && negativeUnused && gateAdmits then
    { stepIndex         := stepIndex
    , currentState      := currentState
    , nextState         := negativeCandidate
    , attemptedNegative := true
    , reflectedPositive := false
    , residual          := Q16_16.zero
    }
  else
    let positiveCandidate := currentState + n
    { stepIndex         := stepIndex
    , currentState      := currentState
    , nextState         := positiveCandidate
    , attemptedNegative := true
    , reflectedPositive := true
    , residual          := if negativeValid && negativeUnused then fieldGate.score else Q16_16.one
    }

def arcFromStep (step : RecamanStep) : RecamanArc :=
  let n := Q16_16.ofInt (Int.ofNat step.stepIndex)
  let center := (step.currentState + step.nextState) * Q16_16.recip (Q16_16.two)
  let radius := n * Q16_16.recip (Q16_16.two)
  let s := if step.reflectedPositive then Q16_16.one else Q16_16.negOne
  let piApprox : Q16_16 := ⟨205944⟩
  let arclen := piApprox * radius
  let curv := if radius.val == 0 then Q16_16.maxVal else Q16_16.recip radius
  { center    := center
  , radius    := radius
  , sign      := s
  , arcLength := arclen
  , curvature := curv
  }

def circleIntersectionCheck (a b : RecamanArc) : Bool :=
  let d := Q16_16.abs (a.center - b.center)
  let sumRadii := a.radius + b.radius
  let diffRadii := Q16_16.abs (a.radius - b.radius)
  let withinOuter := Q16_16.le d sumRadii
  let outsideInner := Q16_16.ge d diffRadii
  withinOuter && outsideInner

def cumulativeArcLength (steps : List RecamanStep) : Q16_16 :=
  let piApprox : Q16_16 := ⟨205944⟩
  let f (acc : Q16_16) (step : RecamanStep) : Q16_16 :=
    let n := Q16_16.ofInt (Int.ofNat step.stepIndex)
    let r := n * Q16_16.recip (Q16_16.two)
    acc + piApprox * r
  steps.foldl f Q16_16.zero

def recamanGateAdmit : Gate :=
  { name     := "RecamanFieldStep"
  , required := false
  , score    := Q16_16.one
  , verdict  := GateVerdict.admit
  }

def fixtureStep1 : RecamanStep :=
  { stepIndex         := 1
  , currentState      := Q16_16.zero
  , nextState         := Q16_16.one
  , attemptedNegative := false
  , reflectedPositive := false
  , residual          := Q16_16.zero
  }

def fixtureStep2 : RecamanStep :=
  { stepIndex         := 2
  , currentState      := Q16_16.one
  , nextState         := Q16_16.ofInt 3
  , attemptedNegative := true
  , reflectedPositive := true
  , residual          := Q16_16.one
  }

def fixtureStep3 : RecamanStep :=
  { stepIndex         := 3
  , currentState      := Q16_16.ofInt 3
  , nextState         := Q16_16.ofInt 6
  , attemptedNegative := true
  , reflectedPositive := true
  , residual          := Q16_16.one
  }

def fixtureArc1 : RecamanArc := arcFromStep fixtureStep1
def fixtureArc2 : RecamanArc := arcFromStep fixtureStep2

def fixtureVisited : List Q16_16 := [Q16_16.one, Q16_16.ofInt 3]
def fixtureGate : Gate :=
  { name := "testFieldGate", required := true, score := Q16_16.one, verdict := GateVerdict.admit }

theorem recaman_gate_name_correct : recamanGateAdmit.name = "RecamanFieldStep" := by
  rfl

theorem recaman_gate_verdict_admits : recamanGateAdmit.verdict = GateVerdict.admit := by
  rfl

theorem fixture_step1_index_one : fixtureStep1.stepIndex = 1 := by rfl
theorem fixture_step2_index_two : fixtureStep2.stepIndex = 2 := by rfl
theorem fixture_step1_reflected_false : fixtureStep1.reflectedPositive = false := by rfl
theorem fixture_step2_reflected_true : fixtureStep2.reflectedPositive = true := by rfl

#eval recamanFieldStep Q16_16.zero 1 [] fixtureGate
#eval recamanFieldStep Q16_16.one 2 fixtureVisited fixtureGate
#eval fixtureArc1
#eval fixtureArc2
#eval circleIntersectionCheck fixtureArc1 fixtureArc2
#eval cumulativeArcLength [fixtureStep1, fixtureStep2, fixtureStep3]
#eval cumulativeArcLength []
#eval recamanGateAdmit

end Semantics.HCMMR.Kernels.RecamanFieldStep
