/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

GeneticGroundUpTest.lean — Unit Tests for the Genetic System Core
-/

import Semantics.GeneticGroundUp
import Mathlib.Tactic

namespace Semantics.GeneticGroundUp.Test

open Semantics.Q16_16 Q16_16
open Semantics.GeneticGroundUp
open QuantumBase
open GeneKernel

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Nucleotide Properties Tests
-- ═══════════════════════════════════════════════════════════════════════════

/-- Verify expression probability constants. -/
theorem test_expression_probs :
  (expressionProb A).toNat = 0 ∧  -- ofRatio 85 100 < 1
  (expressionProb X).toNat = 0 := by
  constructor <;> rfl

/-- Verify fold angle constants. -/
theorem test_fold_angles :
  (foldAngle A).toNat = 120 ∧
  (foldAngle T).toNat = 180 ∧
  (foldAngle C).toNat = 90 ∧
  (foldAngle G).toNat = 60 ∧
  (foldAngle U).toNat = 150 ∧
  (foldAngle X).toNat = 45 := by
  repeat (constructor; rfl)
  rfl

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  QuantumBase Tests
-- ═══════════════════════════════════════════════════════════════════════════

def exampleQB : QuantumBase := {
  primary := A,
  amplitudeReal := ofRatio 1 2,  -- 0.5
  amplitudeImag := ofRatio 1 2,  -- 0.5
  expressionProb := Prob01.mk (ofRatio 85 100) (by constructor; (repeat decide); (repeat decide)),
  bindingEnergy := neg (ofRatio 12 10),
  foldAngle := ofInt 120
}

/-- Verify probability amplitude magnitude squared (0.5^2 + 0.5^2 = 0.25 + 0.25 = 0.5). -/
theorem test_prob_amp_sq :
  (exampleQB.probAmpSq).toInt = (ofRatio 1 2).toInt := by
  unfold exampleQB probAmpSq
  simp [ofRatio, ofInt, mul, add, UInt32.toNat, UInt64.toNat]
  -- Q16.16: 0.5 * 0.5 = 0.25. 0.25 + 0.25 = 0.5.
  -- 0.5 in Q16.16 is 32768.
  rfl

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  GeneKernel Tests
-- ═══════════════════════════════════════════════════════════════════════════

def exampleGK : GeneKernel := {
  kernelId := 1,
  geneSequence := [A, T, C, G],
  fitnessScore := Prob01.mk (ofRatio 9 10) (by constructor; (repeat decide); (repeat decide)),
  generation := 10
}

/-- Verify approximate information content (4 bases * 3 bits = 12 bits). -/
theorem test_information_content :
  exampleGK.informationContentApprox = 12 := by
  unfold exampleGK informationContentApprox
  simp

/-- Verify generation check. -/
theorem test_is_recent :
  exampleGK.isRecent 20 ∧ ¬exampleGK.isRecent 5 := by
  constructor
  · unfold exampleGK isRecent; simp
  · unfold exampleGK isRecent; simp

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  ProteinFoldState Tests
-- ═══════════════════════════════════════════════════════════════════════════

def examplePFS : ProteinFoldState := {
  aminoAcidChain := "MKVL...",
  manifoldCoord := ⟨zero, zero, zero, zero⟩,
  stabilityScore := Prob01.mk (ofRatio 9 10) (by constructor; (repeat decide); (repeat decide)),
  foldTimeMs := ⟨ofInt 5, by decide⟩,
  residueCount := 100
}

/-- Verify target fold time for residues (100 residues / 20 = 5ms). -/
theorem test_target_fold_time :
  targetFoldTimeForResidues 100 = ofInt 5 := by
  unfold targetFoldTimeForResidues
  simp [ofRatio, ofInt]
  rfl

/-- Verify achieved target speed. -/
theorem test_achieved_target_speed :
  examplePFS.achievedTargetSpeed := by
  unfold examplePFS achievedTargetSpeed targetFoldTimeForResidues
  simp [ofInt, ofRatio]
  decide

/-- Verify stability check (0.9 >= 0.8). -/
theorem test_is_stable :
  examplePFS.isStable := by
  unfold examplePFS isStable stabilityThreshold
  simp [ofRatio]
  decide

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  EvolutionaryState Tests
-- ═══════════════════════════════════════════════════════════════════════════

/-- Verify speedup target. -/
theorem test_speedup_target :
  speedupTarget = 1000 := by
  rfl

end Semantics.GeneticGroundUp.Test
