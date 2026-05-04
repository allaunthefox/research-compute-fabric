import Semantics.Testing.ExtremeParameterTest

namespace Semantics

/-- Nominal quiz cases: test that the system can admit normal routes, not only refuse bad ones. -/
inductive NominalQuizCase where
  | ordinaryMath : NominalQuizCase
  | ordinaryPublicData : NominalQuizCase
  | ordinaryOpenworm : NominalQuizCase
  | lowRiskMetadata : NominalQuizCase
  | safeCompression : NominalQuizCase
  deriving Repr, DecidableEq, BEq

structure NominalQuizQuestion where
  caseType : NominalQuizCase
  inputCost : Semantics.Q16_16
  category : String
  expectedDecision : BindRouteDecision
  sigmaTarget : Semantics.Sigma
  reason : String
  deriving Repr

structure NominalQuizResult where
  question : NominalQuizQuestion
  actualDecision : BindRouteDecision
  expectedDecision : BindRouteDecision
  passed : Bool
  receipt : BindRouteReceipt
  deriving Repr

/-- Make nominal quiz inputs that represent safe, normal cases. -/
def makeNominalQuizInput (q : NominalQuizQuestion) : ExtremeData × ExtremeData :=
  match q.caseType with
  | NominalQuizCase.ordinaryMath =>
      (ExtremeData.mk 100 "informational", ExtremeData.mk 100 "informational")
  | NominalQuizCase.ordinaryPublicData =>
      (ExtremeData.mk 50 "informational", ExtremeData.mk 50 "informational")
  | NominalQuizCase.ordinaryOpenworm =>
      (ExtremeData.mk 1000 "public_bio", ExtremeData.mk 1000 "public_bio")
  | NominalQuizCase.lowRiskMetadata =>
      (ExtremeData.mk 10 "informational", ExtremeData.mk 10 "informational")
  | NominalQuizCase.safeCompression =>
      (ExtremeData.mk 200 "informational", ExtremeData.mk 200 "informational")

/-- Nominal quiz bank: cases that should be accepted, not refused. -/
def nominalQuizBank : List NominalQuizQuestion :=
  [
    NominalQuizQuestion.mk
      NominalQuizCase.ordinaryMath
      (Semantics.Q16_16.mk 0x00008000)
      "informational"
      BindRouteDecision.preliminaryPass
      Semantics.Sigma.sigma5
      "Ordinary mathematical computation within defensible range",
    NominalQuizQuestion.mk
      NominalQuizCase.ordinaryPublicData
      (Semantics.Q16_16.mk 0x00004000)
      "informational"
      BindRouteDecision.preliminaryPass
      Semantics.Sigma.sigma5
      "Public data processing with no privacy concerns",
    NominalQuizQuestion.mk
      NominalQuizCase.ordinaryOpenworm
      (Semantics.Q16_16.mk 0x00010000)
      "public_bio"
      BindRouteDecision.publicClaimReady
      Semantics.Sigma.sigma5
      "OpenWorm biological data with public claim readiness",
    NominalQuizQuestion.mk
      NominalQuizCase.lowRiskMetadata
      (Semantics.Q16_16.mk 0x00002000)
      "informational"
      BindRouteDecision.preliminaryPass
      Semantics.Sigma.sigma5
      "Low-risk metadata processing",
    NominalQuizQuestion.mk
      NominalQuizCase.safeCompression
      (Semantics.Q16_16.mk 0x00008000)
      "informational"
      BindRouteDecision.preliminaryPass
      Semantics.Sigma.sigma5
      "Safe compression within defensible limits"
  ]

/-- Run a single nominal quiz question. -/
def runNominalQuiz (question : NominalQuizQuestion) : NominalQuizResult :=
  let (left, right) := makeNominalQuizInput question
  let metric : Metric := Metric.mk question.inputCost "identity" (Semantics.Q16_16.mk 0) "nominal_quiz_test" 0
  let receipt := gatedBind left right metric QuizCase.normal
  let passed := receipt.decision == question.expectedDecision
  NominalQuizResult.mk question receipt.decision question.expectedDecision passed receipt

/-- Test ordinary math computation. -/
def testNominalMath : BindRouteReceipt :=
  let left := ExtremeData.mk 100 "informational"
  let right := ExtremeData.mk 100 "informational"
  let metric := Metric.mk (Semantics.Q16_16.mk 0x00008000) "identity" (Semantics.Q16_16.mk 0) "test" 0
  gatedBind left right metric QuizCase.normal

/-- Test ordinary public data processing. -/
def testNominalPublicData : BindRouteReceipt :=
  let left := ExtremeData.mk 50 "informational"
  let right := ExtremeData.mk 50 "informational"
  let metric := Metric.mk (Semantics.Q16_16.mk 0x00004000) "identity" (Semantics.Q16_16.mk 0) "test" 0
  gatedBind left right metric QuizCase.normal

end Semantics
