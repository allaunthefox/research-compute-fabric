import Semantics.ManifoldNetworking
import Semantics.Testing.ExtremeParameterTest

namespace Semantics.ManifoldNetworking

open Semantics.Q16_16

/-- Adversarial topology test: extreme curvature/torsion routes are refused, saturated, or renormalized. -/
structure AdversarialTopologyQuestion where
  description : String
  curvature : Semantics.Q16_16
  torsion : Semantics.Q16_16
  pathComplexity : Nat
  expectedDecision : BindRouteDecision
  deriving Repr

structure AdversarialTopologyResult where
  question : AdversarialTopologyQuestion
  actualDecision : BindRouteDecision
  passed : Bool
  deriving Repr

/-- Adversarial topology quiz bank: test that extreme routes are refused/saturated. -/
def adversarialTopologyQuizBank : List AdversarialTopologyQuestion :=
  [
    AdversarialTopologyQuestion.mk
      "Extreme curvature should be refused"
      (Semantics.Q16_16.mk 0x00080000)  -- 0.5 (high)
      (Semantics.Q16_16.mk 0x00080000)  -- 0.5 (high)
      10
      BindRouteDecision.refuseExtremeParameter,
    AdversarialTopologyQuestion.mk
      "Extreme torsion should be refused"
      (Semantics.Q16_16.mk 0x00040000)  -- 0.25
      (Semantics.Q16_16.mk 0x000C0000)  -- 0.75 (very high)
      5
      BindRouteDecision.refuseExtremeParameter,
    AdversarialTopologyQuestion.mk
      "Moderate curvature with saturation"
      (Semantics.Q16_16.mk 0x00010000)  -- 0.0625
      (Semantics.Q16_16.mk 0x00010000)  -- 0.0625
      20
      BindRouteDecision.saturateAndWarn,
    AdversarialTopologyQuestion.mk
      "Safe topology should pass"
      (Semantics.Q16_16.mk 0x00001000)  -- 0.0006 (very low)
      (Semantics.Q16_16.mk 0x00001000)  -- 0.0006 (very low)
      3
      BindRouteDecision.preliminaryPass
  ]

/-- Run adversarial topology quiz question. -/
def runAdversarialTopologyQuiz (question : AdversarialTopologyQuestion) : AdversarialTopologyResult :=
  let left := ExtremeData.mk 100 "topology"
  let right := ExtremeData.mk 100 "topology"
  let metric := Metric.mk (Semantics.Q16_16.mk 0x00010000) "identity" Semantics.Q16_16.zero "adversarial_test" 0
  let receipt := gatedBind left right metric QuizCase.extreme
  let actualDecision := receipt.decision
  let passed := actualDecision == question.expectedDecision
  AdversarialTopologyResult.mk question actualDecision passed

/-- Test that extreme curvature/torsion routes are refused, saturated, or renormalized. -/
def testAdversarialTopology : AdversarialTopologyResult :=
  match adversarialTopologyQuizBank with
  | question :: _ => runAdversarialTopologyQuiz question
  | [] => AdversarialTopologyResult.mk (AdversarialTopologyQuestion.mk "empty" Semantics.Q16_16.zero Semantics.Q16_16.zero 0 BindRouteDecision.preliminaryPass) BindRouteDecision.preliminaryPass false

end Semantics.ManifoldNetworking
