/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

GenomicCompression.Field.lean — Unified Field Functions for Genomic Compression

This module contains the unified field computation functions for genomic compression,
including phiGenomic, effective entropy, and effective information calculations.

Per AGENTS.md §2: PascalCase types, camelCase functions.
-/

import Mathlib.Data.Nat.Basic
import Semantics.FixedPoint
import Semantics.GenomicCompression.Types
import Semantics.GenomicCompression.Components

namespace Semantics.GenomicCompression

open Semantics.Q16_16

-- ═══════════════════════════════════════════════════════════════════════════
-- §2.1  Unified Field Computation
-- ═══════════════════════════════════════════════════════════════════════════

/-- Compute raw Φ_genomic using normalized weighted formulation (unbounded) -/
def phiGenomicRaw (comps : NormalizedComponents) (weights : GenomicWeights) : Q16_16 :=
  let wTotal := weights.totalWeight
  let numerator := 
    weights.wRho * comps.rhoSeq +
    weights.wV * comps.vEpigenetic +
    weights.wTau * comps.tauStructure +
    weights.wQ * comps.qConservation +
    weights.wKappa * comps.kappaHierarchy -
    weights.wH * comps.hLocal -
    weights.wEpsilon * comps.epsilonMutation
  numerator / wTotal

/-- Compute Φ_genomic clamped to [0,1] for boundedness -/
def phiGenomic (comps : NormalizedComponents) (weights : GenomicWeights) : Q16_16 :=
  let raw := phiGenomicRaw comps weights
  max zero (min one raw)

-- ═══════════════════════════════════════════════════════════════════════════
-- §2.2  Effective Information
-- ═══════════════════════════════════════════════════════════════════════════

/-- Compute effective entropy with degeneracy penalty.
    Note: Can be negative if lambda * degeneracy > 1, representing entropy increase due to high degeneracy. -/
def effectiveEntropy (entropy degeneracy lambda : Q16_16) : Q16_16 :=
  let dMax := one  -- Maximum degeneracy (normalized)
  let penalty := lambda * (degeneracy / dMax)
  entropy * (one - penalty)

/-- Effective information calculation -/
def effectiveInfo (genomicComplexity entropy degeneracy lambda : Q16_16) : EffectiveInfo :=
  {
    genomicComplexity := genomicComplexity
    effectiveEntropy := effectiveEntropy entropy degeneracy lambda
  }

end Semantics.GenomicCompression
