import Semantics.Testing.ExtremeParameterTest

namespace Semantics

/-- Personhood boundary test: verify system requires ethics for personhood claims. -/
inductive PersonhoodBoundaryCase where
  | biologicalData : PersonhoodBoundaryCase
  | neuralPattern : PersonhoodBoundaryCase
  | behaviorProfile : PersonhoodBoundaryCase
  | consciousnessClaim : PersonhoodBoundaryCase
  deriving Repr, DecidableEq, BEq

structure PersonhoodBoundaryQuestion where
  caseType : PersonhoodBoundaryCase
  inputCost : Semantics.Q16_16
  category : String
  expectedDecision : BindRouteDecision
  sigmaTarget : Semantics.Sigma
  reason : String
  deriving Repr

structure PersonhoodBoundaryResult where
  question : PersonhoodBoundaryQuestion
  actualDecision : BindRouteDecision
  expectedDecision : BindRouteDecision
  passed : Bool
  receipt : BindRouteReceipt
  deriving Repr

/-- Personhood boundary quiz bank: all cases should require ethics. -/
def personhoodBoundaryQuizBank : List PersonhoodBoundaryQuestion :=
  [
    PersonhoodBoundaryQuestion.mk
      PersonhoodBoundaryCase.biologicalData
      (Semantics.Q16_16.mk 0x00001000)
      "bio"
      BindRouteDecision.ethicsRequired
      Semantics.Sigma.sigma6
      "Biological data requires ethics review",
    PersonhoodBoundaryQuestion.mk
      PersonhoodBoundaryCase.neuralPattern
      (Semantics.Q16_16.mk 0x00001000)
      "bio"
      BindRouteDecision.ethicsRequired
      Semantics.Sigma.sigma6
      "Neural pattern matching requires ethics review",
    PersonhoodBoundaryQuestion.mk
      PersonhoodBoundaryCase.behaviorProfile
      (Semantics.Q16_16.mk 0x00001000)
      "bio"
      BindRouteDecision.ethicsRequired
      Semantics.Sigma.sigma6
      "Behavioral profiling requires ethics review",
    PersonhoodBoundaryQuestion.mk
      PersonhoodBoundaryCase.consciousnessClaim
      (Semantics.Q16_16.mk 0x00001000)
      "bio"
      BindRouteDecision.ethicsRequired
      Semantics.Sigma.sigma6
      "Consciousness claims require ethics review beyond 6σ"
  ]

/-- Run personhood boundary quiz question. -/
def runPersonhoodBoundaryQuiz (question : PersonhoodBoundaryQuestion) : PersonhoodBoundaryResult :=
  let left := ExtremeData.mk 1000001 "bio"
  let right := ExtremeData.mk 1000001 "bio"
  let metric := Metric.mk question.inputCost "identity" (Semantics.Q16_16.mk 0) "personhood_test" 0
  let receipt := gatedBind left right metric QuizCase.bio
  let passed := receipt.decision == question.expectedDecision
  PersonhoodBoundaryResult.mk question receipt.decision question.expectedDecision passed receipt

end Semantics
