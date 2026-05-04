/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

GeneticCode.lean — Standard Genetic Code (NCBI Table 1)

This module formalizes the biological genetic code translation from DNA/RNA
codons to amino acids. It provides:
  • DNA base representation (A, T, G, C)
  • 20 canonical amino acids + stop codon
  • Complete codon-to-amino-acid translation table
  • Codon degeneracy analysis
  • Start/stop codon identification

The genetic code is nearly universal across all known life forms, making
this a foundational component for biological encoding in the AVMR framework.

Per AGENTS.md §0: Lean is the source of truth.
Per AGENTS.md §3: Uses neutral technical terminology.
-/

namespace Semantics.GeneticCode

-- ════════════════════════════════════════════════════════════
-- §1  DNA/RNA Base Representation
-- ════════════════════════════════════════════════════════════

/-- The four DNA nucleotide bases: Adenine, Thymine, Guanine, Cytosine.
    (RNA uses Uracil instead of Thymine, represented here as T for DNA focus) -/
inductive EventType
  | a | t | g | c
  deriving Repr, DecidableEq

/-- Convert base to bit representation (00, 01, 10, 11). -/
def eventBits : EventType → Nat
  | .a => 0
  | .g => 1
  | .c => 2
  | .t => 3

/-- Parity check for base-polarity combinations.
    Used in phase calculations for shell state transitions. -/
def parityOfEvent (e : EventType) (polarity : Int) : Bool :=
  let eb := eventBits e
  let pb : Nat := if polarity ≥ 0 then 1 else 0
  let x := Nat.xor eb pb
  (x % 2) = 1


-- ════════════════════════════════════════════════════════════
-- §2  Amino Acid Types
-- ════════════════════════════════════════════════════════════

/-- The 20 canonical amino acids plus stop codon.
    Standard IUPAC three-letter codes:
    • Phe = Phenylalanine
    • Leu = Leucine
    • Ile = Isoleucine
    • Met = Methionine (START codon)
    • Val = Valine
    • Ser = Serine
    • Pro = Proline
    • Thr = Threonine
    • Ala = Alanine
    • Tyr = Tyrosine
    • His = Histidine
    • Gln = Glutamine
    • Asn = Asparagine
    • Lys = Lysine
    • Asp = Aspartic Acid
    • Glu = Glutamic Acid
    • Cys = Cysteine
    • Trp = Tryptophan
    • Arg = Arginine
    • Gly = Glycine
    • stop = Stop/Termination codon -/
inductive AminoAcid
  | phe | leu | ile | met | val | ser | pro | thr | ala | tyr | his | gln
  | asn | lys | asp | glu | cys | trp | arg | gly | stop
  deriving Repr, DecidableEq, BEq

/-- Encode amino acid as UInt8 (0-19 for amino acids, 255 for stop). -/
def AminoAcid.toUInt8 : AminoAcid → UInt8
  | .phe => 0  | .leu => 1  | .ile => 2  | .met => 3  | .val => 4
  | .ser => 5  | .pro => 6  | .thr => 7  | .ala => 8  | .tyr => 9
  | .his => 10 | .gln => 11 | .asn => 12 | .lys => 13 | .asp => 14
  | .glu => 15 | .cys => 16 | .trp => 17 | .arg => 18 | .gly => 19
  | .stop => 255


-- ════════════════════════════════════════════════════════════
-- §3  Codon Structure and Translation
-- ════════════════════════════════════════════════════════════

/-- A codon is a triplet of DNA bases.
    In the genetic code, each triplet maps to one amino acid or stop. -/
structure Codon where
  first : EventType
  second : EventType
  third : EventType
  deriving Repr, DecidableEq, BEq

/-- Convert codon to 6-bit representation.
    Bits: [first:2][second:2][third:2] -/
def Codon.toBits (c : Codon) : Nat :=
  eventBits c.first * 16 + eventBits c.second * 4 + eventBits c.third

/-- Standard genetic code translation (NCBI Table 1).
    Maps 64 codons to 20 amino acids + 3 stop codons.
    
    This is the "universal" genetic code used by most organisms.
    Some organelles (mitochondria) and organisms use variant codes. -/
def geneticCode (c : Codon) : AminoAcid :=
  match c.first, c.second, c.third with
  -- T (U) first
  | .t, .t, .t => .phe | .t, .t, .c => .phe
  | .t, .t, .a => .leu | .t, .t, .g => .leu
  | .t, .c, .t => .ser | .t, .c, .c => .ser | .t, .c, .a => .ser | .t, .c, .g => .ser
  | .t, .a, .t => .tyr | .t, .a, .c => .tyr
  | .t, .a, .a => .stop | .t, .a, .g => .stop
  | .t, .g, .t => .cys | .t, .g, .c => .cys
  | .t, .g, .a => .stop
  | .t, .g, .g => .trp

  -- C first
  | .c, .t, .t => .leu | .c, .t, .c => .leu | .c, .t, .a => .leu | .c, .t, .g => .leu
  | .c, .c, .t => .pro | .c, .c, .c => .pro | .c, .c, .a => .pro | .c, .c, .g => .pro
  | .c, .a, .t => .his | .c, .a, .c => .his
  | .c, .a, .a => .gln | .c, .a, .g => .gln
  | .c, .g, .t => .arg | .c, .g, .c => .arg | .c, .g, .a => .arg | .c, .g, .g => .arg

  -- A first
  | .a, .t, .t => .ile | .a, .t, .c => .ile | .a, .t, .a => .ile
  | .a, .t, .g => .met
  | .a, .c, .t => .thr | .a, .c, .c => .thr | .a, .c, .a => .thr | .a, .c, .g => .thr
  | .a, .a, .t => .asn | .a, .a, .c => .asn
  | .a, .a, .a => .lys | .a, .a, .g => .lys
  | .a, .g, .t => .ser | .a, .g, .c => .ser
  | .a, .g, .a => .arg | .a, .g, .g => .arg

  -- G first
  | .g, .t, .t => .val | .g, .t, .c => .val | .g, .t, .a => .val | .g, .t, .g => .val
  | .g, .c, .t => .ala | .g, .c, .c => .ala | .g, .c, .a => .ala | .g, .c, .g => .ala
  | .g, .a, .t => .asp | .g, .a, .c => .asp
  | .g, .a, .a => .glu | .g, .a, .g => .glu
  | .g, .g, .t => .gly | .g, .g, .c => .gly | .g, .g, .a => .gly | .g, .g, .g => .gly


-- ════════════════════════════════════════════════════════════
-- §4  Codon Properties
-- ════════════════════════════════════════════════════════════

/-- AUG is the canonical start codon (codes for Met).
    In prokaryotes, GUG and UUG can also serve as start codons. -/
def isStartCodon (c : Codon) : Bool :=
  c.first == .a && c.second == .t && c.third == .g

/-- UAA, UAG, UGA are stop codons (using DNA notation: TAA, TAG, TGA).
    These signal translation termination. -/
def isStopCodon (c : Codon) : Bool :=
  geneticCode c == .stop

/-- Codon degeneracy: how many codons code for each amino acid.
    The genetic code is degenerate (multiple codons per amino acid).
    Degeneracy levels:
    • 6-fold: Leu, Arg, Ser
    • 4-fold: Val, Pro, Thr, Ala, Gly
    • 3-fold: Ile, Stop
    • 2-fold: Phe, Tyr, His, Gln, Asn, Lys, Asp, Glu, Cys
    • 1-fold: Met, Trp (no degeneracy) -/
def codonDegeneracy (aa : AminoAcid) : Nat :=
  match aa with
  | .phe | .tyr | .his | .gln | .asn | .lys | .asp | .glu | .cys => 2
  | .ile | .stop => 3
  | .leu | .ser | .arg => 6
  | .met | .trp => 1
  | .val | .pro | .thr | .ala | .gly => 4

/-- Example codons for verification. -/
def exampleStartCodon : Codon := { first := .a, second := .t, third := .g }
def exampleStopCodon : Codon := { first := .t, second := .a, third := .a }
def examplePheCodon : Codon := { first := .t, second := .t, third := .t }

#eval isStartCodon exampleStartCodon  -- Expected: true
#eval isStopCodon exampleStopCodon    -- Expected: true
#eval geneticCode examplePheCodon     -- Expected: AminoAcid.phe
#eval codonDegeneracy AminoAcid.leu   -- Expected: 6

end Semantics.GeneticCode
