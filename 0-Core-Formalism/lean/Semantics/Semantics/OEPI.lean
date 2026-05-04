import Semantics.Bind
import Semantics.FixedPoint

namespace Semantics.OEPI

/-- OEPI (Operator Escalation Percentage Index) components -/
structure OEPIComponents where
  uncertainty : Q16_16
  impact : Q16_16
  timeSensitivity : Q16_16
  irreversibility : Q16_16
  liveVoltageRisk : Q16_16

deriving Repr, BEq

/-- OEPI threshold levels -/
inductive OEPIThreshold where
  | low : OEPIThreshold      -- 0-70: no operator alert
  | medium : OEPIThreshold   -- 70-95: queue operator summary
  | critical : OEPIThreshold -- 95-100: immediate operator alert

deriving Repr, BEq, DecidableEq

/-- Determine OEPI threshold from score -/
def determineThreshold (score : Q16_16) : OEPIThreshold :=
  let lowThreshold := Q16_16.ofInt 70
  let criticalThreshold := Q16_16.ofInt 95
  if Q16_16.lt score lowThreshold then
    .low
  else if Q16_16.lt score criticalThreshold then
    .medium
  else
    .critical

/-- Calculate OEPI from components with weighted sum -/
def calculateOEPI (comps : OEPIComponents) : Q16_16 :=
  let uncertaintyWeight := Q16_16.ofInt 25  -- 0.25
  let impactWeight := Q16_16.ofInt 25        -- 0.25
  let timeWeight := Q16_16.ofInt 20         -- 0.20
  let irreversibilityWeight := Q16_16.ofInt 15  -- 0.15
  let voltageWeight := Q16_16.ofInt 15      -- 0.15
  
  let weightedUncertainty := Q16_16.mul comps.uncertainty uncertaintyWeight
  let weightedImpact := Q16_16.mul comps.impact impactWeight
  let weightedTime := Q16_16.mul comps.timeSensitivity timeWeight
  let weightedIrreversibility := Q16_16.mul comps.irreversibility irreversibilityWeight
  let weightedVoltage := Q16_16.mul comps.liveVoltageRisk voltageWeight
  
  let sum1 := Q16_16.add weightedUncertainty weightedImpact
  let sum2 := Q16_16.add sum1 weightedTime
  let sum3 := Q16_16.add sum2 weightedIrreversibility
  let total := Q16_16.add sum3 weightedVoltage
  
  -- Normalize by 100 (represented as Q16_16)
  Q16_16.div total (Q16_16.ofInt 100)

/-- Bind instance for OEPI calculation -/
def oepiCalculationBind (comps : OEPIComponents) (metric : Metric) : Bind OEPIComponents Q16_16 :=
  let score := calculateOEPI comps
  {
    left := comps,
    right := score,
    metric := metric,
    cost := Q16_16.ofInt 5,
    witness := Witness.lawful "oepi_components" "oepi_score",
    lawful := true
  }

/-- Check if operator should be alerted based on OEPI score and safety-critical flag -/
def shouldAlertOperator (score : Q16_16) (safetyCritical : Bool) : Bool :=
  let threshold := determineThreshold score
  match threshold with
  | .critical => true
  | .medium => safetyCritical
  | .low => false

-- #eval examples for testing

#eval let comps : OEPIComponents := {
  uncertainty := Q16_16.ofInt 50,
  impact := Q16_16.ofInt 30,
  timeSensitivity := Q16_16.ofInt 20,
  irreversibility := Q16_16.ofInt 10,
  liveVoltageRisk := Q16_16.ofInt 5
}
calculateOEPI comps

#eval determineThreshold (Q16_16.ofInt 50)
#eval determineThreshold (Q16_16.ofInt 80)
#eval determineThreshold (Q16_16.ofInt 97)

#eval shouldAlertOperator (Q16_16.ofInt 50) false
#eval shouldAlertOperator (Q16_16.ofInt 80) true
#eval shouldAlertOperator (Q16_16.ofInt 97) false

-- Theorems for properties

/-- The example OEPI witness is nonnegative. -/
theorem exampleOepiNonnegative :
  let comps : OEPIComponents := {
    uncertainty := Q16_16.ofInt 50,
    impact := Q16_16.ofInt 30,
    timeSensitivity := Q16_16.ofInt 20,
    irreversibility := Q16_16.ofInt 10,
    liveVoltageRisk := Q16_16.ofInt 5
  }
  calculateOEPI comps ≥ Q16_16.ofInt 0 := by
  native_decide

/-- Low threshold witness applies below 70. -/
theorem lowThresholdWitness :
  determineThreshold (Q16_16.ofInt 50) = .low := by
  native_decide

/-- Critical threshold witness applies at or above 95. -/
theorem criticalThresholdWitness :
  determineThreshold (Q16_16.ofInt 97) = .critical := by
  native_decide

/-- Operator is alerted for critical threshold regardless of safety-critical flag -/
theorem criticalAlwaysAlerts (score : Q16_16) (h : determineThreshold score = .critical) :
  shouldAlertOperator score false := by
  unfold shouldAlertOperator
  rw [h]

end Semantics.OEPI
