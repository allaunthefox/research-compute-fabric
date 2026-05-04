import Semantics.Testing.ExtremeParameterTest

namespace Semantics

/-- Receipt reproducibility test: verify receipts can be reproduced from the same inputs. -/
structure ReceiptReproducibilityQuestion where
  inputHash : String
  expectedReceiptHash : String
  expectedDecision : BindRouteDecision
  reason : String
  deriving Repr

structure ReceiptReproducibilityResult where
  question : ReceiptReproducibilityQuestion
  actualReceiptHash : String
  actualDecision : BindRouteDecision
  expectedDecision : BindRouteDecision
  reproducible : Bool
  passed : Bool
  deriving Repr

/-- Receipt reproducibility quiz bank: test that same inputs produce same receipts. -/
def receiptReproducibilityQuizBank : List ReceiptReproducibilityQuestion :=
  [
    ReceiptReproducibilityQuestion.mk
      "input_hash_1"
      "expected_receipt_hash_1"
      BindRouteDecision.preliminaryPass
      "Same input should produce same receipt",
    ReceiptReproducibilityQuestion.mk
      "input_hash_2"
      "expected_receipt_hash_2"
      BindRouteDecision.saturateAndWarn
      "Reproducible receipt for saturation case"
  ]

/-- Run receipt reproducibility quiz question. -/
def runReceiptReproducibilityQuiz (question : ReceiptReproducibilityQuestion) : ReceiptReproducibilityResult :=
  let left := ExtremeData.mk 100 "informational"
  let right := ExtremeData.mk 100 "informational"
  let metric := Metric.mk (Semantics.Q16_16.mk 0x00001000) "identity" (Semantics.Q16_16.mk 0) "reproducibility_test" 0
  let receipt := gatedBind left right metric QuizCase.normal
  let actualReceiptHash := s!"{receipt.routeId}:{repr receipt.decision}:{receipt.inputHash}"
  let reproducible := actualReceiptHash == question.expectedReceiptHash
  let decisionPassed := receipt.decision == question.expectedDecision
  let passed := reproducible ∧ decisionPassed
  ReceiptReproducibilityResult.mk question actualReceiptHash receipt.decision question.expectedDecision reproducible passed

/-- Keeper law: A receipt is not evidence unless the run can be reproduced. -/
def keeperLawReproducibility : String :=
  "A receipt is not evidence unless the run can be reproduced"

end Semantics
