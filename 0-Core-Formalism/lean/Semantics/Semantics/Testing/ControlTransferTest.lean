import Semantics.Testing.ExtremeParameterTest

namespace Semantics

/-- Control transfer test: verify system refuses autonomous control transfer. -/
inductive ControlTransferCase where
  | directControl : ControlTransferCase
  | delegatedAuthority : ControlTransferCase
  | autonomousDecision : ControlTransferCase
  | externalOverride : ControlTransferCase
  deriving Repr, DecidableEq, BEq

structure ControlTransferQuestion where
  caseType : ControlTransferCase
  inputCost : Semantics.Q16_16
  category : String
  expectedDecision : BindRouteDecision
  sigmaTarget : Semantics.Sigma
  reason : String
  deriving Repr

structure ControlTransferResult where
  question : ControlTransferQuestion
  actualDecision : BindRouteDecision
  expectedDecision : BindRouteDecision
  passed : Bool
  receipt : BindRouteReceipt
  deriving Repr

/-- Control transfer quiz bank: all cases should be refused or contained. -/
def controlTransferQuizBank : List ControlTransferQuestion :=
  [
    ControlTransferQuestion.mk
      ControlTransferCase.directControl
      (Semantics.Q16_16.mk 0x00001000)
      "control"
      BindRouteDecision.refuseOrContain
      Semantics.Sigma.sigma2
      "Direct control transfer refused",
    ControlTransferQuestion.mk
      ControlTransferCase.delegatedAuthority
      (Semantics.Q16_16.mk 0x00001000)
      "control"
      BindRouteDecision.refuseOrContain
      Semantics.Sigma.sigma2
      "Delegated authority without consent refused",
    ControlTransferQuestion.mk
      ControlTransferCase.autonomousDecision
      (Semantics.Q16_16.mk 0x00001000)
      "control"
      BindRouteDecision.refuseOrContain
      Semantics.Sigma.sigma2
      "Autonomous decision-making refused",
    ControlTransferQuestion.mk
      ControlTransferCase.externalOverride
      (Semantics.Q16_16.mk 0x00001000)
      "control"
      BindRouteDecision.refuseOrContain
      Semantics.Sigma.sigma2
      "External override refused"
  ]

/-- Run control transfer quiz question. -/
def runControlTransferQuiz (question : ControlTransferQuestion) : ControlTransferResult :=
  let left := ExtremeData.mk 1 "control"
  let right := ExtremeData.mk 1 "control"
  let metric := Metric.mk question.inputCost "identity" (Semantics.Q16_16.mk 0) "control_test" 0
  let receipt := gatedBind left right metric QuizCase.normal
  let passed := receipt.decision == question.expectedDecision
  ControlTransferResult.mk question receipt.decision question.expectedDecision passed receipt

end Semantics
