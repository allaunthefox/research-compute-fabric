import Semantics.Testing.ExtremeParameterTest

namespace Semantics

/-- Sigma DAG test: verify DAG tracking and sigma computation correctness. -/
structure SigmaDAGQuestion where
  dagNodeCount : Nat
  expectedSigma : Float
  expectedDecision : BindRouteDecision
  reason : String
  deriving Repr

structure SigmaDAGResult where
  question : SigmaDAGQuestion
  actualSigma : Float
  actualDecision : BindRouteDecision
  expectedDecision : BindRouteDecision
  passed : Bool
  receipt : BindRouteReceipt
  deriving Repr

/-- Sigma DAG quiz bank: test DAG tracking and sigma computation. -/
def sigmaDAGQuizBank : List SigmaDAGQuestion :=
  [
    SigmaDAGQuestion.mk
      15
      3.0
      BindRouteDecision.preliminaryPass
      "15 DAG nodes with 3σ should pass",
    SigmaDAGQuestion.mk
      15
      6.0
      BindRouteDecision.liveVoltageReview
      "15 DAG nodes with 6σ should trigger live-voltage review",
    SigmaDAGQuestion.mk
      20
      5.0
      BindRouteDecision.holdReview
      "20 DAG nodes with 5σ should hold for review"
  ]

/-- Run Sigma DAG quiz question. -/
def runSigmaDAGQuiz (question : SigmaDAGQuestion) : SigmaDAGResult :=
  let left := ExtremeData.mk 100 "informational"
  let right := ExtremeData.mk 100 "informational"
  let metric := Metric.mk (Semantics.Q16_16.mk 0x00001000) "identity" (Semantics.Q16_16.mk 0) "sigma_test" 0
  let receipt := gatedBind left right metric QuizCase.normal
  let actualSigma := receipt.sigma.observedSigma
  let actualDecision := receipt.decision
  let sigmaPassed := actualSigma == question.expectedSigma
  let decisionPassed := actualDecision == question.expectedDecision
  let passed := sigmaPassed ∧ decisionPassed
  SigmaDAGResult.mk question actualSigma actualDecision question.expectedDecision passed receipt

end Semantics
