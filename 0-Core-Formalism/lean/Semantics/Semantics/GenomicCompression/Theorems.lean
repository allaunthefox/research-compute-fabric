/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

GenomicCompression.Theorems.lean — Theorems for Genomic Compression

This module contains theorems about the genomic compression field,
including boundedness properties and monotonicity results.

Per AGENTS.md §2: PascalCase types, camelCase functions.
Per AGENTS.md §4: Every def has eval witness or theorem.
-/

import Mathlib.Data.Nat.Basic
import Mathlib.Tactic
import Semantics.FixedPoint
import Semantics.GenomicCompression.Types
import Semantics.GenomicCompression.Components
import Semantics.GenomicCompression.Field
import Semantics.GenomicCompression.Compression

namespace Semantics.GenomicCompression

open Semantics.Q16_16

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Theorems: Normalized Field Properties
-- ═══════════════════════════════════════════════════════════════════════════

/-- Theorem: Φ_genomic is bounded in [0,1] when components are normalized.
    Since phiGenomic clamps the raw value to [0,1], boundedness is trivial. -/
theorem phiGenomicBounded (comps : NormalizedComponents) (weights : GenomicWeights) :
  let phi := phiGenomic comps weights
  zero ≤ phi ∧ phi ≤ one := by
  unfold phiGenomic
  constructor
  · exact le_max_left
  · exact (le_trans (le_max_right _ _) (le_min_right _ _))

/-- Theorem: Higher hierarchy (κ̂) increases raw Φ_genomic when other components fixed.
    More multiscale reuse → better compressibility (before clamping). -/
theorem hierarchyImprovesPhiRaw 
    (comps1 comps2 : NormalizedComponents) (weights : GenomicWeights)
    (hHigher : comps2.kappaHierarchy > comps1.kappaHierarchy)
    (hOtherEq : comps1.rhoSeq = comps2.rhoSeq ∧ comps1.vEpigenetic = comps2.vEpigenetic ∧
                comps1.tauStructure = comps2.tauStructure ∧ comps1.qConservation = comps2.qConservation ∧
                comps1.hLocal = comps2.hLocal ∧ comps1.epsilonMutation = comps2.epsilonMutation) :
    phiGenomicRaw comps2 weights > phiGenomicRaw comps1 weights := by
  unfold phiGenomicRaw
  let wTotal := weights.totalWeight
  have hWPos : wTotal > zero := by
    unfold GenomicWeights.totalWeight
    cases weights.wf_nonzero
    · intro hRho
      exact add_pos_of_nonneg_of_pos hRho weights.wf_positive.2.1 
        (add_pos_of_nonneg_of_pos weights.wf_positive.2.2.1 
          (add_pos_of_nonneg_of_pos weights.wf_positive.2.2.2.1 
            (add_pos_of_nonneg_of_pos weights.wf_positive.2.2.2.2.1 
              weights.wf_positive.2.2.2.2.2.1)))
    · intro hV
      exact add_pos_of_nonneg_of_pos weights.wf_positive.1 hV 
        (add_pos_of_nonneg_of_pos weights.wf_positive.2.2.1 
          (add_pos_of_nonneg_of_pos weights.wf_positive.2.2.2.1 
            (add_pos_of_nonneg_of_pos weights.wf_positive.2.2.2.2.1 
              weights.wf_positive.2.2.2.2.2.1)))
    · intro hTau
      exact add_pos_of_nonneg_of_pos weights.wf_positive.1 weights.wf_positive.2.1 hTau 
        (add_pos_of_nonneg_of_pos weights.wf_positive.2.2.2.1 
          (add_pos_of_nonneg_of_pos weights.wf_positive.2.2.2.2.1 
            weights.wf_positive.2.2.2.2.2.1)))
    · intro hQ
      exact add_pos_of_nonneg_of_pos weights.wf_positive.1 weights.wf_positive.2.1 weights.wf_positive.2.2.1 hQ 
        (add_pos_of_nonneg_of_pos weights.wf_positive.2.2.2.2.1 
          weights.wf_positive.2.2.2.2.2.1))
    · intro hKappa
      exact add_pos_of_nonneg_of_pos weights.wf_positive.1 weights.wf_positive.2.1 weights.wf_positive.2.2.1 weights.wf_positive.2.2.2.1 hKappa 
        (add_pos_of_nonneg_of_pos weights.wf_positive.2.2.2.2.2.1)
    · intro hH
      exact add_pos_of_nonneg_of_pos weights.wf_positive.1 weights.wf_positive.2.1 weights.wf_positive.2.2.1 weights.wf_positive.2.2.2.1 weights.wf_positive.2.2.2.2.1 hH 
        weights.wf_positive.2.2.2.2.2.2.1
    · intro hEpsilon
      exact add_pos_of_nonneg_of_pos weights.wf_positive.1 weights.wf_positive.2.1 weights.wf_positive.2.2.1 weights.wf_positive.2.2.2.1 weights.wf_positive.2.2.2.2.1 weights.wf_positive.2.2.2.2.2.2.1 hEpsilon
  
  have hNumDiff := 
    (weights.wRho * comps2.rhoSeq + weights.wV * comps2.vEpigenetic + weights.wTau * comps2.tauStructure +
     weights.wQ * comps2.qConservation + weights.wKappa * comps2.kappaHierarchy -
     weights.wH * comps2.hLocal - weights.wEpsilon * comps2.epsilonMutation) -
    (weights.wRho * comps1.rhoSeq + weights.wV * comps1.vEpigenetic + weights.wTau * comps1.tauStructure +
     weights.wQ * comps1.qConservation + weights.wKappa * comps1.kappaHierarchy -
     weights.wH * comps1.hLocal - weights.wEpsilon * comps1.epsilonMutation) =
    weights.wKappa * (comps2.kappaHierarchy - comps1.kappaHierarchy) := by
    rw [hOtherEq.1, hOtherEq.2.1, hOtherEq.2.2.1, hOtherEq.2.2.2.1, hOtherEq.2.2.2.2.1, hOtherEq.2.2.2.2.2.1]
    ring_nf
  
  have hNumPos := weights.wKappa * (comps2.kappaHierarchy - comps1.kappaHierarchy) > zero := by
    apply mul_pos
    · cases weights.wf_nonzero with
      | .inl hKappa => exact hKappa
      | .inr h => cases h with
        | .inl hRho => linarith [hRho]
        | .inr h => cases h with
          | .inl hV => linarith [hV]
          | .inr h => cases h with
            | .inl hTau => linarith [hTau]
            | .inr h => cases h with
              | .inl hQ => linarith [hQ]
              | .inr h => cases h with
                | .inl hH => linarith [hH]
                | .inr hEpsilon => linarith [hEpsilon]
    · linarith [hHigher]
  
  apply (div_lt_div_right hWPos).mpr
  exact hNumPos

/-- Theorem: Compression efficiency is bounded in [0,100].
    η_compression cannot exceed 100% and cannot be negative. -/
theorem compressionEfficiencyBounded (rawSize compressedSize : Q16_16) :
  let eff := compressionEfficiency rawSize compressedSize
  zero ≤ eff ∧ eff ≤ ofNat 100 := by
  unfold compressionEfficiency
  let savings := rawSize - compressedSize
  have hEff := max zero ((savings / rawSize) * ofNat 100)
  constructor
  · exact le_max_left
  · have hSavingsLe : savings ≤ rawSize := by
      linarith [sub_le self]
    have hRatioLe : savings / rawSize ≤ one := by
      apply (div_le_iff (by positivity)).mpr
      exact hSavingsLe
    have hProductLe : (savings / rawSize) * ofNat 100 ≤ ofNat 100 := by
      nlinarith [hRatioLe]
    exact le_trans (le_max_right _ _) hProductLe

end Semantics.GenomicCompression
