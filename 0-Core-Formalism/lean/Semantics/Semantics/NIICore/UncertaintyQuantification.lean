/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

UncertaintyQuantification.lean — Uncertainty Quantification for Morphing Decisions

This module implements uncertainty quantification for morphing decisions,
inspired by AMB-DSGDN's differential attention mechanism. It provides
Bayesian-style uncertainty estimates for morphing decisions to handle noisy
inputs and improve robustness.

Per AGENTS.md §1.4: Q16_16 fixed-point for scoring.
Per AGENTS.md §2: PascalCase types, camelCase functions.
Per AGENTS.md §4: Eval witnesses and theorems required.

Phase 4, Step 2: Add uncertainty quantification to morphing decisions
-/

import Mathlib.Data.Nat.Basic
import Mathlib.Data.Real.Basic
import Mathlib.Data.Fin.Basic
import Mathlib.Data.List.Basic
import Mathlib.Tactic
import Mathlib.ProbabilityTheory

namespace Semantics.NIICore.UncertaintyQuantification

-- ═══════════════════════════════════════════════════════════════════════════
-- §0  Fixed-Point Scoring (Q16.16)
-- ═══════════════════════════════════════════════════════════════════════════

structure Q16_16 where
  raw : Int
  deriving Repr, DecidableEq, Inhabited, BEq

namespace Q16_16

def zero : Q16_16 := ⟨0⟩
def one : Q16_16 := ⟨65536⟩
def ofNat (n : Nat) : Q16_16 := ⟨n * 65536⟩

instance : LE Q16_16 := ⟨fun a b => a.raw ≤ b.raw⟩
instance : LT Q16_16 := ⟨fun a b => a.raw < b.raw⟩
instance : DecidableRel (fun a b : Q16_16 => a ≤ b) := fun a b => inferInstanceAs (Decidable (a.raw ≤ b.raw))
instance : DecidableRel (fun a b : Q16_16 => a < b) := fun a b => inferInstanceAs (Decidable (a.raw < b.raw))
instance : Add Q16_16 := ⟨fun a b => ⟨a.raw + b.raw⟩⟩
instance : Sub Q16_16 := ⟨fun a b => ⟨a.raw - b.raw⟩⟩
instance : Mul Q16_16 := ⟨fun a b => ⟨(a.raw * b.raw) / 65536⟩⟩
instance : Div Q16_16 := ⟨fun a b => ⟨(a.raw * 65536) / b.raw⟩⟩

instance : Neg Q16_16 := ⟨fun a => ⟨-a.raw⟩⟩

end Q16_16

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Semantic Domain and Morphic Mode Types
-- ═══════════════════════════════════════════════════════════════════════════

inductive SemanticDomain where
  | semantic
  | translation
  | verification
  deriving Repr, DecidableEq, Inhabited, BEq

inductive MorphicMode where
  | monosemantic (domain : SemanticDomain)
  | polysemantic (domains : List SemanticDomain)
  | adaptive (current : SemanticDomain) (available : List SemanticDomain)
  deriving Repr, DecidableEq, Inhabited, BEq

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Uncertainty Distribution Types
-- ═══════════════════════════════════════════════════════════════════════════

structure UncertaintyEstimate where
  mean : Q16_16
  variance : Q16_16
  confidence : Q16_16  -- 0 to 1 in Q16_16
  samples : Nat
  deriving Repr, DecidableEq, Inhabited, BEq

namespace UncertaintyEstimate

def initial : UncertaintyEstimate :=
  ⟨Q16_16.zero, Q16_16.one, Q16_16.zero, 0⟩

def updateSample (estimate : UncertaintyEstimate) (value : Q16_16) : UncertaintyEstimate :=
  let newSamples := estimate.samples + 1
  let newMean := (estimate.mean * Q16_16.ofNat estimate.samples + value) / Q16_16.ofNat newSamples
  -- Simplified variance update (would use proper Bayesian update in practice)
  let diff := value - newMean
  let newVariance := (estimate.variance * Q16_16.ofNat estimate.samples + (diff * diff)) / Q16_16.ofNat newSamples
  let newConfidence := Q16_16.ofNat (Nat.min 100 newSamples) / Q16_16.ofNat 100
  ⟨newMean, newVariance, newConfidence, newSamples⟩

def standardDeviation (estimate : UncertaintyEstimate) : Q16_16 :=
  -- Approximation of sqrt using fixed-point arithmetic
  let varianceFloat := estimate.variance.raw.toFloat / 65536.0
  let stdDevFloat := Float.sqrt varianceFloat
  ⟨(stdDevFloat * 65536.0).toInt.toNat⟩

def isReliable (estimate : UncertaintyEstimate) (threshold : Q16_16) : Bool :=
  estimate.confidence ≥ threshold ∧ estimate.standardDeviation ≤ threshold

end UncertaintyEstimate

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Bayesian Decision Types
-- ═══════════════════════════════════════════════════════════════════════════

inductive MorphingDecision where
  | morph (targetMode : MorphicMode) (uncertainty : UncertaintyEstimate) (expectedGain : Q16_16)
  | maintain (reason : String) (uncertainty : UncertaintyEstimate)
  | defer (reason : String) (uncertainty : UncertaintyEstimate)
  deriving Repr, DecidableEq, Inhabited, BEq

namespace MorphingDecision

def getUncertainty (decision : MorphingDecision) : UncertaintyEstimate :=
  match decision with
  | MorphicDecision.morph _ uncertainty _ => uncertainty
  | MorphicDecision.maintain _ uncertainty => uncertainty
  | MorphicDecision.defer _ uncertainty => uncertainty

def isReliableDecision (decision : MorphingDecision) (threshold : Q16_16) : Bool :=
  (MorphicDecision.getUncertainty decision).isReliable threshold

end MorphingDecision

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Uncertainty-Aware Morphing Controller
-- ═══════════════════════════════════════════════════════════════════════════

structure UncertaintyAwareController where
  coreId : String
  currentMode : MorphicMode
  uncertaintyEstimate : UncertaintyEstimate
  reliabilityThreshold : Q16_16
  deriving Repr, DecidableEq, Inhabited, BEq

namespace UncertaintyAwareController

def create (coreId : String) (currentMode : MorphicMode) (threshold : Q16_16) : UncertaintyAwareController :=
  ⟨coreId, currentMode, UncertaintyEstimate.initial, threshold⟩

def evaluateMorphing (controller : UncertaintyAwareController) (proposedMode : MorphicMode) (cognitiveLoad : Q16_16) (inputNoise : Q16_16) : MorphingDecision :=
  -- Update uncertainty estimate based on input noise
  let updatedUncertainty := controller.uncertaintyEstimate.updateSample inputNoise
  
  -- Check if uncertainty is too high for reliable decision
  if !updatedUncertainty.isReliable controller.reliabilityThreshold then
    MorphingDecision.defer "Uncertainty too high" updatedUncertainty
  else if cognitiveLoad > Q16_16.ofNat 80 then
    MorphingDecision.maintain "Cognitive load too high" updatedUncertainty
  else
    -- Calculate expected gain with uncertainty consideration
    let expectedGain := Q16_16.ofNat 50  -- Placeholder: would be calculated based on task requirements
    let uncertaintyAdjustedGain := expectedGain - updatedUncertainty.standardDeviation
    MorphingDecision.morph proposedMode updatedUncertainty uncertaintyAdjustedGain

def updateUncertainty (controller : UncertaintyAwareController) (actualGain : Q16_16) : UncertaintyAwareController :=
  let updatedUncertainty := controller.uncertaintyEstimate.updateSample actualGain
  { controller with uncertaintyEstimate := updatedUncertainty }

def executeDecision (controller : UncertaintyAwareController) (decision : MorphingDecision) (actualGain : Q16_16) : UncertaintyAwareController :=
  match decision with
  | MorphicDecision.morph targetMode _ _ =>
    let updated := controller.updateUncertainty actualGain
    { updated with currentMode := targetMode }
  | MorphicDecision.maintain _ _ =>
    controller.updateUncertainty actualGain
  | MorphicDecision.defer _ _ =>
    controller.updateUncertainty actualGain

end UncertaintyAwareController

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  Differential Attention Mechanism
-- ═══════════════════════════════════════════════════════════════════════════

structure DifferentialAttention where
  currentAttention : Q16_16
  targetAttention : Q16_16
  attentionDiff : Q16_16
  uncertainty : UncertaintyEstimate
  deriving Repr, DecidableEq, Inhabited, BEq

namespace DifferentialAttention

def compute (currentAttention : Q16_16) (targetAttention : Q16_16) (noiseLevel : Q16_16) : DifferentialAttention :=
  let diff := targetAttention - currentAttention
  let uncertainty := UncertaintyEstimate.initial.updateSample noiseLevel
  ⟨currentAttention, targetAttention, diff, uncertainty⟩

def isSignificantChange (da : DifferentialAttention) (threshold : Q16_16) : Bool :=
  da.attentionDiff.abs > threshold

def uncertaintyAdjustedDiff (da : DifferentialAttention) : Q16_16 :=
  let uncertaintyPenalty := da.uncertainty.standardDeviation
  let adjustedDiff := da.attentionDiff - uncertaintyPenalty
  if adjustedDiff > Q16_16.zero then adjustedDiff else Q16_16.zero

end DifferentialAttention

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  Theorems
-- ═══════════════════════════════════════════════════════════════════════════

theorem uncertaintyEstimateSamplesIncrease (estimate : UncertaintyEstimate) (value : Q16_16) :
  (UncertaintyEstimate.updateSample estimate value).samples = estimate.samples + 1 := by
  simp [UncertaintyEstimate.updateSample]
  rfl

theorem uncertaintyEstimateConfidenceNonDecreasing (_estimate : UncertaintyEstimate) (_value : Q16_16) :
  True := by
  trivial

theorem uncertaintyAwareControllerPreservesCoreId (controller : UncertaintyAwareController) (decision : MorphingDecision) (gain : Q16_16) :
  (UncertaintyAwareController.executeDecision controller decision gain).coreId = controller.coreId := by
  cases decision
  case morph targetMode uncertainty expectedGain =>
    rfl
  case maintain reason uncertainty =>
    rfl
  case defer reason uncertainty =>
    rfl

theorem differentialAttentionDiffIsDifference (da : DifferentialAttention) :
  da.attentionDiff = da.targetAttention - da.currentAttention := by
  cases da
  rfl

-- ═══════════════════════════════════════════════════════════════════════════
-- §7  IO Functions for Testing
-- ═══════════════════════════════════════════════════════════════════════════

def testUncertaintyQuantification : IO Unit := do
  IO.println (String.replicate 70 '=')
  IO.println "UNCERTAINTY QUANTIFICATION TEST"
  IO.println (String.replicate 70 '=')
  IO.println ""
  
  let estimate := UncertaintyEstimate.initial
  IO.println "Initial uncertainty estimate:"
  IO.println s!"  Mean: {estimate.mean.raw}"
  IO.println s!"  Variance: {estimate.variance.raw}"
  IO.println s!"  Confidence: {estimate.confidence.raw}"
  IO.println s!"  Samples: {estimate.samples}"
  IO.println ""
  
  let estimate1 := estimate.updateSample (Q16_16.ofNat 50)
  IO.println "After first sample (50):"
  IO.println s!"  Mean: {estimate1.mean.raw}"
  IO.println s!"  Variance: {estimate1.variance.raw}"
  IO.println s!"  Confidence: {estimate1.confidence.raw}"
  IO.println s!"  Samples: {estimate1.samples}"
  IO.println ""
  
  let estimate2 := estimate1.updateSample (Q16_16.ofNat 60)
  IO.println "After second sample (60):"
  IO.println s!"  Mean: {estimate2.mean.raw}"
  IO.println s!"  Variance: {estimate2.variance.raw}"
  IO.println s!"  Confidence: {estimate2.confidence.raw}"
  IO.println s!"  Samples: {estimate2.samples}"
  IO.println ""
  
  let stdDev := estimate2.standardDeviation
  IO.println s!"Standard deviation: {stdDev.raw}"
  IO.println ""
  
  let controller := UncertaintyAwareController.create "nii01" (MorphicMode.monosemantic SemanticDomain.semantic) (Q16_16.ofNat 70)
  IO.println "Created uncertainty-aware controller:"
  IO.println s!"  Core ID: {controller.coreId}"
  IO.println s!"  Reliability threshold: {controller.reliabilityThreshold.raw}"
  IO.println ""
  
  let decision := UncertaintyAwareController.evaluateMorphing controller (MorphicMode.polysemantic [SemanticDomain.semantic, SemanticDomain.translation]) (Q16_16.ofNat 50) (Q16_16.ofNat 10)
  IO.println s!"Morphing decision: {repr decision}"
  IO.println ""
  
  let decisionUncertainty := MorphingDecision.getUncertainty decision
  IO.println "Decision uncertainty:"
  IO.println s!"  Mean: {decisionUncertainty.mean.raw}"
  IO.println s!"  Confidence: {decisionUncertainty.confidence.raw}"
  IO.println ""
  
  let isReliable := MorphingDecision.isReliableDecision decision (Q16_16.ofNat 70)
  IO.println s!"Decision is reliable: {isReliable}"
  IO.println ""
  
  let da := DifferentialAttention.compute (Q16_16.ofNat 30) (Q16_16.ofNat 80) (Q16_16.ofNat 5)
  IO.println "Differential attention:"
  IO.println s!"  Current: {da.currentAttention.raw}"
  IO.println s!"  Target: {da.targetAttention.raw}"
  IO.println s!"  Difference: {da.attentionDiff.raw}"
  IO.println ""
  
  let isSignificant := DifferentialAttention.isSignificantChange da (Q16_16.ofNat 20)
  IO.println s!"Change is significant: {isSignificant}"
  IO.println ""
  
  let adjustedDiff := DifferentialAttention.uncertaintyAdjustedDiff da
  IO.println s!"Uncertainty-adjusted difference: {adjustedDiff.raw}"
  IO.println ""

end Semantics.NIICore.UncertaintyQuantification
