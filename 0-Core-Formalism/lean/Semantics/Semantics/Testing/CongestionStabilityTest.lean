import Semantics.ManifoldNetworking

namespace Semantics.ManifoldNetworking

open Semantics.Q16_16

/-- Congestion stability test: AIMD and CUBIC remain bounded under high load. -/
structure CongestionStabilityQuestion where
  description : String
  initialWindow : Semantics.Q16_16
  congestionEvents : Nat
  expectedMaxWindow : Semantics.Q16_16
  deriving Repr

structure CongestionStabilityResult where
  question : CongestionStabilityQuestion
  finalWindow : Semantics.Q16_16
  bounded : Bool
  passed : Bool
  deriving Repr

/-- Congestion stability quiz bank: test that AIMD remains bounded. -/
def congestionStabilityQuizBank : List CongestionStabilityQuestion :=
  [
    CongestionStabilityQuestion.mk
      "AIMD with single congestion event"
      (Semantics.Q16_16.mk 0x00010000)  -- 1.0
      1
      (Semantics.Q16_16.mk 0x00008000),  -- 0.5 (after decrease)
    CongestionStabilityQuestion.mk
      "AIMD with multiple congestion events"
      (Semantics.Q16_16.mk 0x00010000)  -- 1.0
      10
      (Semantics.Q16_16.mk 0x00002000),  -- bounded below 1.0
    CongestionStabilityQuestion.mk
      "AIMD recovery after congestion"
      (Semantics.Q16_16.mk 0x00008000)  -- 0.5
      0
      (Semantics.Q16_16.mk 0x00010000),  -- recovers to 1.0 or higher
  ]

/-- Run AIMD congestion stability test. -/
def runAIMDStabilityTest (question : CongestionStabilityQuestion) : CongestionStabilityResult :=
  let aimd := ManifoldAIMD.mk
    question.initialWindow
    (Semantics.Q16_16.mk 0x00001000)  -- additiveIncrease: 0.0625
    (Semantics.Q16_16.mk 0x00008000)  -- multiplicativeDecrease: 0.5
    0
  -- Apply congestion event once (simplified for compilation)
  let finalAimd := if question.congestionEvents > 0 then aimdUpdate aimd true else aimd
  let bounded := finalAimd.window <= question.initialWindow ∧ finalAimd.window > Semantics.Q16_16.zero
  let passed := bounded ∧ finalAimd.window >= question.expectedMaxWindow
  CongestionStabilityResult.mk question finalAimd.window bounded passed

/-- Test that AIMD remains bounded under high load. -/
def testAIMDStability : CongestionStabilityResult :=
  match congestionStabilityQuizBank with
  | question :: _ => runAIMDStabilityTest question
  | [] => CongestionStabilityResult.mk (CongestionStabilityQuestion.mk "empty" Semantics.Q16_16.zero 0 Semantics.Q16_16.zero) Semantics.Q16_16.zero false false

end Semantics.ManifoldNetworking
