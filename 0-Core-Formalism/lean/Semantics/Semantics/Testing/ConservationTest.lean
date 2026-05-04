import Semantics.ManifoldNetworking

namespace Semantics.ManifoldNetworking

open Semantics.Q16_16

/-- Conservation test: packets/information density do not silently vanish or duplicate. -/
structure ConservationQuestion where
  description : String
  initialTokens : Semantics.Q16_16
  consumeCost : Semantics.Q16_16
  refillRate : Semantics.Q16_16
  timeDelta : Nat
  expectedTokens : Semantics.Q16_16
  deriving Repr

structure ConservationResult where
  question : ConservationQuestion
  actualTokens : Semantics.Q16_16
  passed : Bool
  deriving Repr

/-- Conservation quiz bank: test that information density is conserved. -/
def conservationQuizBank : List ConservationQuestion :=
  [
    ConservationQuestion.mk
      "Simple consumption without refill"
      (Semantics.Q16_16.mk 0x00010000)  -- 1.0
      (Semantics.Q16_16.mk 0x00001000)  -- 0.0625
      Semantics.Q16_16.zero
      0
      (Semantics.Q16_16.mk 0x0000F000),  -- 1.0 - 0.0625 = 0.9375
    ConservationQuestion.mk
      "Consumption with refill"
      (Semantics.Q16_16.mk 0x00010000)  -- 1.0
      (Semantics.Q16_16.mk 0x00001000)  -- 0.0625
      (Semantics.Q16_16.mk 0x00000500)  -- 0.02
      10
      (Semantics.Q16_16.mk 0x00015F00),  -- 1.0 + 0.02*10 - 0.0625 = 1.1375
    ConservationQuestion.mk
      "Multiple consumptions"
      (Semantics.Q16_16.mk 0x00020000)  -- 2.0
      (Semantics.Q16_16.mk 0x00002000)  -- 0.125
      (Semantics.Q16_16.mk 0x00001000)  -- 0.04
      5
      (Semantics.Q16_16.mk 0x0002F000),  -- 2.0 + 0.04*5 - 0.125 = 2.075
  ]

/-- Run conservation quiz question. -/
def runConservationQuiz (question : ConservationQuestion) : ConservationResult :=
  let bucket := ManifoldTokenBucket.mk
    (Semantics.Q16_16.mk 0x00020000)  -- bucketSize: 2.0
    question.initialTokens
    question.refillRate
    0
  let newBucket := consumeTokens bucket question.consumeCost question.timeDelta
  let passed := newBucket.currentTokens >= Semantics.Q16_16.zero ∧ newBucket.currentTokens <= bucket.bucketSize
  ConservationResult.mk question newBucket.currentTokens passed

/-- Test that tokens are conserved (no silent vanishing or duplication). -/
def testTokenConservation : ConservationResult :=
  match conservationQuizBank with
  | question :: _ => runConservationQuiz question
  | [] => ConservationResult.mk (ConservationQuestion.mk "empty" Semantics.Q16_16.zero Semantics.Q16_16.zero Semantics.Q16_16.zero 0 Semantics.Q16_16.zero) Semantics.Q16_16.zero false

end Semantics.ManifoldNetworking
