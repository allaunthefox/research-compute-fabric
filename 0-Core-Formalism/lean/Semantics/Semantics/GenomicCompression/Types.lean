/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

GenomicCompression.Types.lean — Basic Types for Genomic Compression

This module contains the fundamental type definitions for genomic compression,
including nucleotides, DNA sequences, amino acids, proteins, gene regulatory networks,
epigenetic data, and genomic windows.

Per AGENTS.md §2: PascalCase types, camelCase functions.
-/

import Mathlib.Data.Nat.Basic
import Semantics.FixedPoint

namespace Semantics.GenomicCompression

open Semantics.Q16_16

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Types: Genomic Sequences
-- ═══════════════════════════════════════════════════════════════════════════

/-- Nucleotide base type -/
inductive Nucleotide where
  | A | C | G | T
  deriving BEq, DecidableEq, Repr

/-- DNA sequence as list of nucleotides -/
abbrev DNASequence := List Nucleotide

/-- Amino acid type (20 standard) -/
inductive AminoAcid where
  | A | R | N | D | C | Q | E | G | H | I | L | K | M | F | P | S | T | W | Y | V
  deriving BEq, DecidableEq, Repr

/-- Protein sequence as list of amino acids -/
abbrev ProteinSequence := List AminoAcid

/-- Gene Regulatory Network state (simplified) -/
structure GRN where
  genes : List String
  expression : List Q16_16  -- Normalized expression levels (Q16.16)
  deriving BEq, DecidableEq, Repr

-- ═══════════════════════════════════════════════════════════════════════════
-- §1.1  Epigenetic Types (from 2504.03733)
-- ═══════════════════════════════════════════════════════════════════════════

/-- CpG island: region with high CG density -/
structure CpGIsland where
  chromosome : String
  start : Nat
  end : Nat
  cpgCount : Nat
  gcContent : Float  -- GC fraction (0-1)
  length : Nat
  deriving BEq, DecidableEq, Repr

/-- Methylation level at a specific CpG site -/
structure MethylationSite where
  chromosome : String
  position : Nat
  methylation : Q16_16  -- 0 = unmethylated, 1.0 = fully methylated (Q16.16)
  coverage : Nat       -- Sequencing depth
  deriving BEq, DecidableEq, Repr

/-- Methylation matrix for multiple cell types -/
structure MethylationMatrix where
  sites : List MethylationSite
  cellTypes : List String
  values : List (List Q16_16)  -- Matrix: cellTypes × sites (Q16.16)
  deriving BEq, DecidableEq, Repr

/-- Chromatin accessibility (ATAC-seq) data -/
structure ChromatinAccessibility where
  chromosome : String
  start : Nat
  end : Nat
  signal : Q16_16  -- Accessibility signal (0-1) in Q16.16
  deriving BEq, DecidableEq, Repr

/-- Histone modification mark -/
structure HistoneMark where
  chromosome : String
  start : Nat
  end : Nat
  mark : String  -- e.g., "H3K27ac", "H3K4me3"
  signal : Q16_16  -- Signal intensity in Q16.16
  deriving BEq, DecidableEq, Repr

/-- Multi-modal epigenetic data -/
structure EpigeneticData where
  sequence : DNASequence
  methylation : List MethylationSite
  accessibility : List ChromatinAccessibility
  histone : List HistoneMark
  cellType : String
  deriving BEq, DecidableEq, Repr

-- ═══════════════════════════════════════════════════════════════════════════
-- §1.2  Protein Structure Types (from 2503.16659)
-- ═══════════════════════════════════════════════════════════════════════════

/-- 3D protein structure coordinates (simplified) -/
structure Protein3DStructure where
  residues : List (Q16_16 × Q16_16 × Q16_16)  -- (x, y, z) coordinates in Q16.16
  deriving BEq, DecidableEq, Repr

-- ═══════════════════════════════════════════════════════════════════════════
-- §1.3  Gene Regulatory Network Types (from 2504.12610)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Genomic window: fixed-length segment for field computation -/
structure GenomicWindow where
  chromosome : String
  start : Nat
  length : Nat  -- Window size (recommended: 1000-10000 bp)
  sequence : DNASequence
  deriving Repr, Inhabited

end Semantics.GenomicCompression
