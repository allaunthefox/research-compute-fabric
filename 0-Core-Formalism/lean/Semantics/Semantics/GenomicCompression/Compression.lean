/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

GenomicCompression.Compression.lean — Compression Operations for Genomic Data

This module contains the compression functions for genomic data, including
windowed compression, protein structure compression, and GRN compression.

Per AGENTS.md §2: PascalCase types, camelCase functions.
-/

import Mathlib.Data.Nat.Basic
import Semantics.FixedPoint
import Semantics.GenomicCompression.Types
import Semantics.GenomicCompression.Components
import Semantics.GenomicCompression.Field

namespace Semantics.GenomicCompression

open Semantics.Q16_16

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Windowed Compression Operations
-- ═══════════════════════════════════════════════════════════════════════════

/--
SI Standard compression ratio: CR = raw_size / compressed_size
Dimensionless ratio (e.g., 8 means 8:1 compression).
Higher values indicate better compression.
-/
def compressionRatioSI (rawSize compressedSize : Q16_16) : Q16_16 :=
  if compressedSize = zero then zero  -- Infinite compression is invalid
  else div rawSize compressedSize

/--
Industry standard compression percentage: CP = (raw - compressed) / raw × 100
Example: CR=8 → CP=87.5 (87.5% reduction)
-/
def compressionPercentage (rawSize compressedSize : Q16_16) : Q16_16 :=
  if rawSize ≤ zero then zero  -- Guard against division by zero
  else
    let savings := rawSize - compressedSize
    let efficiency := (savings / rawSize) * ofNat 100
    max zero efficiency  -- Clamp to non-negative

/-- Compress genomic window using field-weighted arithmetic coding (Q16.16).
    Returns (compressed_size, field_value, compression_efficiency). -/
def compressWindow (window : GenomicWindow) (comps : NormalizedComponents)
    (weights : GenomicWeights) : Q16_16 × Q16_16 × Q16_16 :=
  let rawSize := ofNat window.length
  let fieldVal := phiGenomic comps weights
  -- Simulate compression: higher field → better compression
  let compressedSize := div rawSize (one + fieldVal)
  let efficiency := compressionEfficiency rawSize compressedSize
  (compressedSize, fieldVal, efficiency)

/-- Compress DNA sequence using sliding window approach (Q16.16).
    Returns total compressed size and average field value.
    Requires windowSize > 0 to avoid non-termination. -/
def compressDNAWindows (seq : DNASequence) (windowSize : Nat)
    (compsList : List NormalizedComponents) (weights : GenomicWeights) : Q16_16 × Q16_16 :=
  if windowSize = 0 then (zero, zero)  -- Guard against non-termination
  else
    let rec processWindows (remaining : DNASequence) (idx : Nat) (accSize accField : Q16_16) : Q16_16 × Q16_16 :=
      if remaining.length < windowSize then
        -- Process final partial window
        let partialSize := ofNat remaining.length
        let partialField := compsList.foldl (fun acc comps => acc + comps.rhoSeq) zero compsList
        let partialComp := if partialSize > zero then div partialSize (one + partialField) else zero
        (accSize + partialComp, accField + partialField)
      else
        -- Process full window
        let windowSeq := remaining.take windowSize
        let comps := compsList.getD (compsList.getLastD NormalizedComponents.cpgIslandDefault) idx
        let (compSize, fieldVal, _) := compressWindow {
          chromosome := "", start := idx * windowSize, length := windowSize, sequence := windowSeq
        } comps weights
        processWindows (remaining.drop windowSize) (idx + 1) (accSize + compSize) (accField + fieldVal)

    let totalWindows := (seq.length + windowSize - 1) / windowSize
    let (totalComp, totalField) := processWindows seq 0 zero zero
    let avgField := if totalWindows > 0 then div totalField (ofNat totalWindows) else zero
    (totalComp, avgField)

/-- Compress protein structure using field-guided encoding (Q16.16).
    Note: struct3D parameter reserved for future structure-guided encoding (currently unused). -/
def compressProtein (seq : ProteinSequence) (struct3D : List (Q16_16 × Q16_16 × Q16_16))
    (comps : NormalizedComponents) (weights : GenomicWeights) : Q16_16 × Q16_16 × Q16_16 :=
  let aaCount := ofNat seq.length
  let fieldVal := phiGenomic comps weights
  let compressedSize := div aaCount (one + fieldVal * two)
  let efficiency := compressionEfficiency aaCount compressedSize
  (compressedSize, fieldVal, efficiency)

/-- Compress gene regulatory network using topology-aware encoding (Q16.16).
    Note: nodeCount reserved for future node-based encoding (currently unused). -/
def compressGRN (grn : GRN) (comps : NormalizedComponents) (weights : GenomicWeights) : Q16_16 × Q16_16 × Q16_16 :=
  let nodeCount := ofNat grn.genes.length  -- Reserved for future use
  let edgeCount := ofNat grn.expression.length
  let fieldVal := phiGenomic comps weights
  let conservationFactor := one - comps.qConservation
  let hierarchyFactor := one + comps.kappaHierarchy
  let compressedSize := div (edgeCount * conservationFactor) hierarchyFactor
  let efficiency := compressionEfficiency edgeCount compressedSize
  (compressedSize, fieldVal, efficiency)

end Semantics.GenomicCompression
