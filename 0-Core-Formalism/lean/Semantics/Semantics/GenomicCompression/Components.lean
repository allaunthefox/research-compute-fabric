/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

GenomicCompression.Components.lean — Component Structures for Genomic Compression

This module contains the component structures for the genomic compression field,
including NormalizedComponents (normalized field values) and GenomicWeights (explicit weights).

Per AGENTS.md §2: PascalCase types, camelCase functions.
-/

import Mathlib.Data.Nat.Basic
import Semantics.FixedPoint

namespace Semantics.GenomicCompression

open Semantics.Q16_16

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Unified Field Components
-- ═══════════════════════════════════════════════════════════════════════════

/-- Normalized component values (all in [0,1] range, Q16.16) -/
structure NormalizedComponents where
  rhoSeq : Q16_16      -- ρ̂_seq: sequence consistency [0,1]
  vEpigenetic : Q16_16 -- v̂_epigenetic: epigenetic regularity [0,1]
  tauStructure : Q16_16 -- τ̂_structure: structural coherence [0,1]
  qConservation : Q16_16 -- q̂_conservation: evolutionary conservation [0,1]
  kappaHierarchy : Q16_16 -- κ̂_hierarchy: multiscale reuse [0,1]
  hLocal : Q16_16      -- Ĥ_local: local entropy penalty [0,1]
  epsilonMutation : Q16_16 -- ε̂_mutation: mutation deviation [0,1]
  
  wf_normalized : rhoSeq ≥ zero ∧ rhoSeq ≤ one ∧
                  vEpigenetic ≥ zero ∧ vEpigenetic ≤ one ∧
                  tauStructure ≥ zero ∧ tauStructure ≤ one ∧
                  qConservation ≥ zero ∧ qConservation ≤ one ∧
                  kappaHierarchy ≥ zero ∧ kappaHierarchy ≤ one ∧
                  hLocal ≥ zero ∧ hLocal ≤ one ∧
                  epsilonMutation ≥ zero ∧ epsilonMutation ≤ one
  deriving Repr

namespace NormalizedComponents

/-- Default normalized components for CpG-rich region (Q16.16) -/
def cpgIslandDefault : NormalizedComponents :=
  { rhoSeq := ofNat 80        -- High sequence consistency (0.80)
    vEpigenetic := ofNat 60    -- High epigenetic regularity (0.60)
    tauStructure := ofNat 30   -- Moderate structural coherence (0.30)
    qConservation := ofNat 50  -- Moderate conservation (0.50)
    kappaHierarchy := ofNat 40 -- Significant hierarchy (0.40)
    hLocal := ofNat 30         -- Moderate entropy penalty (0.30)
    epsilonMutation := ofNat 10 -- Low mutation deviation (0.10)
    wf_normalized := by simp [zero, one, le_refl] }

/-- Default normalized components for protein coding region (Q16.16) -/
def codingRegionDefault : NormalizedComponents :=
  { rhoSeq := ofNat 90        -- Very high sequence consistency (0.90)
    vEpigenetic := zero        -- No epigenetics in coding
    tauStructure := ofNat 50   -- High structural coherence (0.50)
    qConservation := ofNat 70  -- High conservation (0.70)
    kappaHierarchy := ofNat 60 -- High hierarchy (0.60)
    hLocal := ofNat 20         -- Low entropy penalty (0.20)
    epsilonMutation := ofNat 5  -- Very low mutation (0.05)
    wf_normalized := by simp [zero, one, le_refl] }

end NormalizedComponents

/-- Explicit weights for field components (Q16.16, nonnegative)
    At least one weight must be strictly positive to ensure totalWeight > 0 for division -/
structure GenomicWeights where
  wRho : Q16_16      -- Weight for sequence consistency
  wV : Q16_16        -- Weight for epigenetic regularity
  wTau : Q16_16      -- Weight for structural coherence
  wQ : Q16_16        -- Weight for evolutionary conservation
  wKappa : Q16_16    -- Weight for multiscale hierarchy
  wH : Q16_16        -- Weight for entropy penalty
  wEpsilon : Q16_16  -- Weight for mutation penalty
  
  wf_positive : wRho ≥ zero ∧ wV ≥ zero ∧ wTau ≥ zero ∧
                wQ ≥ zero ∧ wKappa ≥ zero ∧ wH ≥ zero ∧ wEpsilon ≥ zero
  wf_nonzero : wRho > zero ∨ wV > zero ∨ wTau > zero ∨ wQ > zero ∨
               wKappa > zero ∨ wH > zero ∨ wEpsilon > zero
  deriving Repr

namespace GenomicWeights

/-- Default weights for DNA methylation compression (balanced)
    Note: Q16_16 uses fixed-point with 16 fractional bits (1 unit = 1/65536).
    For interpretation, divide by 65536 to get decimal value. -/
def dnaMethylationDefault : GenomicWeights :=
  { wRho := one        -- Sequence: baseline importance (1.0)
    wV := ofNat 15      -- Epigenetic: moderate weight (~0.00023 in decimal)
    wTau := ofNat 10    -- Structure: lower weight (~0.00015 in decimal)
    wQ := ofNat 15      -- Conservation: moderate weight (~0.00023 in decimal)
    wKappa := ofNat 20  -- Hierarchy: significant weight (~0.00031 in decimal)
    wH := ofNat 10      -- Entropy penalty: moderate (~0.00015 in decimal)
    wEpsilon := ofNat 10 -- Mutation penalty: moderate (~0.00015 in decimal)
    wf_positive := by simp [zero, le_refl]
    wf_nonzero := by left; exact one_gt_zero }

/-- Default weights for protein structure compression (structure-focused)
    Note: Q16_16 uses fixed-point with 16 fractional bits (1 unit = 1/65536).
    For interpretation, divide by 65536 to get decimal value. -/
def proteinStructureDefault : GenomicWeights :=
  { wRho := ofNat 5     -- Sequence: low importance (~0.00008 in decimal)
    wV := zero          -- No epigenetics in proteins
    wTau := ofNat 40    -- Structure: primary weight (~0.00061 in decimal)
    wQ := ofNat 20      -- Conservation: significant (~0.00031 in decimal)
    wKappa := ofNat 30  -- Hierarchy: very significant (~0.00046 in decimal)
    wH := ofNat 5       -- Entropy penalty: low (~0.00008 in decimal)
    wEpsilon := ofNat 0  -- No mutation penalty for static structures
    wf_positive := by simp [zero, le_refl]
    wf_nonzero := by left; exact Nat.zero_lt_ofNat 40 }

/-- Total weight sum for normalization -/
def totalWeight (w : GenomicWeights) : Q16_16 :=
  w.wRho + w.wV + w.wTau + w.wQ + w.wKappa + w.wH + w.wEpsilon

end GenomicWeights

/-- Effective information: I_eff(x) = G(x) · H_eff(x) -/
structure EffectiveInfo where
  genomicComplexity : Q16_16  -- G(x): genomic complexity
  effectiveEntropy : Q16_16   -- H_eff(x): entropy adjusted for degeneracy
  deriving Repr

end Semantics.GenomicCompression
