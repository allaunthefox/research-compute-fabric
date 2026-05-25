/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

GenomicCompression.lean — Orchestrator for Genomic Compression Modules

This module serves as the orchestrator for the Genomic Compression framework,
importing and re-exporting all core sub-modules for genomic sequence compression
using the unified field Φ(x) approach.

Sub-modules:
- Types: Basic genomic types (Nucleotide, DNASequence, AminoAcid, etc.)
- Components: NormalizedComponents and GenomicWeights structures
- Field: phiGenomic and related field computation functions
- Compression: Compression operations (compressWindow, compressDNAWindows, etc.)
- Theorems: Formal theorems about boundedness and monotonicity
- NonDriftProof: Formal proof that transformation is mathematically derivable

Key insights from literature:
- 2504.03733: AI for Epigenetic Sequence Analysis → Methylation pattern compression
- 2503.16659: Protein Representation Learning → Structural compression in latent space
- 2504.12610: Gene Regulatory Network Inference → Network topology compression

  REFERENCES:
    See 6-Documentation/docs/provenance/LANGUAGE_MATH_MODEL_SOURCES.cff
    for full DOIs. Arxiv IDs above correspond to recent preprints;
    lookup at https://arxiv.org/abs/<id> for current status.

Per AGENTS.md §1.4: Q16_16 fixed-point for hardware extraction.
Per AGENTS.md §2: PascalCase types, camelCase functions.
Per AGENTS.md §4: Every def has eval witness or theorem.

TODO(lean-port): Extract formal lemmas from 2504.03733 epigenetic analysis
TODO(lean-port): Connect to ProteinRepresentation.lean (from 2503.16659) -- Connected via ProteinRepresentation.lean
TODO(lean-port): Prove compression bounds vs standard codecs (gzip, bzip2)
-/

import Mathlib.Data.Nat.Basic
import Mathlib.Data.Real.Basic
import Mathlib.Tactic
import Semantics.FixedPoint
import Semantics.Functions.MathQuery
import Semantics.GenomicCompression.Types
import Semantics.GenomicCompression.Components
import Semantics.GenomicCompression.Field
import Semantics.GenomicCompression.Compression
import Semantics.GenomicCompression.Theorems
import Semantics.GenomicCompression.NonDriftProof

namespace Semantics.GenomicCompression

-- Re-export all core types and structures
open Types
open Components
open Field
open Compression
open Theorems
open NonDriftProof

open Semantics.Q16_16

-- ═══════════════════════════════════════════════════════════════════════════
-- Orchestrator Notes
-- ═══════════════════════════════════════════════════════════════════════════
-- Core genomic compression functionality has been extracted to sub-modules:
-- - Types: Basic genomic types (Nucleotide, DNASequence, AminoAcid, etc.)
-- - Components: NormalizedComponents and GenomicWeights structures
-- - Field: phiGenomic and related field computation functions
-- - Compression: Compression operations (compressWindow, compressDNAWindows, etc.)
-- - Theorems: Formal theorems about boundedness and monotonicity
-- - NonDriftProof: Formal proof that transformation is mathematically derivable
-- 
-- Swarm, Triumvirate, and Topology sections remain in this file for now.
-- These should be moved to separate modules or removed as they are unrelated
-- to the core genomics compression purpose.
-- ═══════════════════════════════════════════════════════════════════════════

end Semantics.GenomicCompression
