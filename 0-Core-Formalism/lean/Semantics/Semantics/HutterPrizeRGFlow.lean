import Semantics.FixedPoint
import Semantics.Biology.RGFlowBioinformatics

namespace Semantics.HutterPrizeRGFlow

open Semantics

/-- Helper: convert Float to Q16_16 by multiplying by 65536 -/
def floatToQ16_16 (f : Float) : Semantics.Q16_16.Q16_16 :=
  let scaled := f * 65536.0
  let int := scaled.toUInt32.toNat
  Semantics.Q16_16.Q16_16.ofNat int

/-! # Hutter Prize RGFlow Filter

RGFlow-based filtering for Hutter Prize text compression (enwik8).
Maps text to DNA, then to amino acids, then applies RGFlow analysis
to identify lawful informatic phases in text.

Citation: Adapted from Python implementation (hutter_rgflow_filter.py)
-/

/-- DNA nucleotide representation. -/
inductive DNANucleotide where
  | A
  | C
  | G
  | T
deriving Repr, BEq, DecidableEq

/-- Amino acid representation (20 standard + stop). -/
inductive AminoAcid where
  | F | L | I | M | V | S | P | T | A | Y
  | H | Q | N | K | D | E | C | W | R | G
  | Stop
deriving Repr, BEq, DecidableEq

/-- DNA codon (3 nucleotides). -/
structure DNACodon where
  n1 : DNANucleotide
  n2 : DNANucleotide
  n3 : DNANucleotide
deriving Repr, BEq

/-- Map 2-bit value to DNA nucleotide. -/
def bitsToDNANucleotide (b : UInt8) : DNANucleotide :=
  match b &&& 0b11 with
  | 0 => .A
  | 1 => .C
  | 2 => .G
  | _ => .T

/-- Map character to DNA nucleotides (2 bits per char). -/
def charToDNA (c : Char) : List DNANucleotide :=
  let val := c.toNat.toUInt8
  let n1 := bitsToDNANucleotide (val >>> 6)
  let n2 := bitsToDNANucleotide ((val >>> 4) &&& 0b11)
  let n3 := bitsToDNANucleotide ((val >>> 2) &&& 0b11)
  let n4 := bitsToDNANucleotide (val &&& 0b11)
  [n1, n2, n3, n4]

/-- Map DNA codon to amino acid using standard genetic code. -/
def codonToAminoAcid (codon : DNACodon) : AminoAcid :=
  match codon with
  | ⟨.A, .A, .A⟩ => .F | ⟨.A, .A, .C⟩ => .F | ⟨.A, .A, .G⟩ => .L | ⟨.A, .A, .T⟩ => .L
  | ⟨.A, .C, .A⟩ => .L | ⟨.A, .C, .C⟩ => .L | ⟨.A, .C, .G⟩ => .L | ⟨.A, .C, .T⟩ => .L
  | ⟨.A, .G, .A⟩ => .I | ⟨.A, .G, .C⟩ => .I | ⟨.A, .G, .G⟩ => .I | ⟨.A, .G, .T⟩ => .M
  | ⟨.A, .T, .A⟩ => .V | ⟨.A, .T, .C⟩ => .V | ⟨.A, .T, .G⟩ => .V | ⟨.A, .T, .T⟩ => .V
  | ⟨.C, .A, .A⟩ => .S | ⟨.C, .A, .C⟩ => .S | ⟨.C, .A, .G⟩ => .S | ⟨.C, .A, .T⟩ => .S
  | ⟨.C, .C, .A⟩ => .P | ⟨.C, .C, .C⟩ => .P | ⟨.C, .C, .G⟩ => .P | ⟨.C, .C, .T⟩ => .P
  | ⟨.C, .G, .A⟩ => .T | ⟨.C, .G, .C⟩ => .T | ⟨.C, .G, .G⟩ => .T | ⟨.C, .G, .T⟩ => .T
  | ⟨.C, .T, .A⟩ => .A | ⟨.C, .T, .C⟩ => .A | ⟨.C, .T, .G⟩ => .A | ⟨.C, .T, .T⟩ => .A
  | ⟨.G, .A, .A⟩ => .Y | ⟨.G, .A, .C⟩ => .Y | ⟨.G, .A, .G⟩ => .Stop | ⟨.G, .A, .T⟩ => .Stop
  | ⟨.G, .C, .A⟩ => .H | ⟨.G, .C, .C⟩ => .H | ⟨.G, .C, .G⟩ => .Q | ⟨.G, .C, .T⟩ => .Q
  | ⟨.G, .G, .A⟩ => .N | ⟨.G, .G, .C⟩ => .N | ⟨.G, .G, .G⟩ => .K | ⟨.G, .G, .T⟩ => .K
  | ⟨.G, .T, .A⟩ => .D | ⟨.G, .T, .C⟩ => .D | ⟨.G, .T, .G⟩ => .E | ⟨.G, .T, .T⟩ => .E
  | ⟨.T, .A, .A⟩ => .C | ⟨.T, .A, .C⟩ => .C | ⟨.T, .A, .G⟩ => .Stop | ⟨.T, .A, .T⟩ => .W
  | ⟨.T, .C, .A⟩ => .R | ⟨.T, .C, .C⟩ => .R | ⟨.T, .C, .G⟩ => .R | ⟨.T, .C, .T⟩ => .R
  | ⟨.T, .G, .A⟩ => .S | ⟨.T, .G, .C⟩ => .S | ⟨.T, .G, .G⟩ => .R | ⟨.T, .G, .T⟩ => .R
  | ⟨.T, .T, .A⟩ => .G | ⟨.T, .T, .C⟩ => .G | ⟨.T, .T, .G⟩ => .G | ⟨.T, .T, .T⟩ => .G

/-- Map DNA sequence to amino acids. -/
def dnaToAminoAcids (dna : List DNANucleotide) : List AminoAcid :=
  let rec helper (remaining : List DNANucleotide) : List AminoAcid :=
    match remaining with
    | n1 :: n2 :: n3 :: rest => codonToAminoAcid ⟨n1, n2, n3⟩ :: helper rest
    | _ => []
  helper dna

/-- Map text to amino acids (text -> DNA -> amino acids). -/
def textToAminoAcids (text : String) : List AminoAcid :=
  let dna := text.toList.flatMap charToDNA
  dnaToAminoAcids dna

/-- Count unique amino acids in list. -/
def countUniqueAminoAcids (acids : List AminoAcid) : Nat :=
  acids.eraseDups.length

/-- Calculate spectral density (unique acids / 21). -/
def spectralDensity (acids : List AminoAcid) : Semantics.Q16_16.Q16_16 :=
  let unique := countUniqueAminoAcids acids
  let total := acids.length
  if total == 0 then Semantics.Q16_16.Q16_16.zero
  else Semantics.Q16_16.Q16_16.div (Semantics.Q16_16.Q16_16.ofNat unique) (Semantics.Q16_16.Q16_16.ofNat 21)

/-- Count transitions between different amino acids. -/
def countTransitions (acids : List AminoAcid) : Nat :=
  match acids with
  | [] => 0
  | [_] => 0
  | _ =>
    let pairs := acids.zip acids.tail
    pairs.filter (fun (a, b) => a ≠ b) |>.length

/-- Calculate mu_q (transition rate scaled by 0.1). -/
def calculateMuQ (acids : List AminoAcid) : Semantics.Q16_16.Q16_16 :=
  let total := acids.length
  if total == 0 then Semantics.Q16_16.Q16_16.zero
  else
    let transitions := countTransitions acids
    let rate := Semantics.Q16_16.Q16_16.div (Semantics.Q16_16.Q16_16.ofNat transitions) (Semantics.Q16_16.Q16_16.ofNat total)
    Semantics.Q16_16.Q16_16.mul rate (floatToQ16_16 0.1)

/-- Count occurrences of each amino acid. -/
def aminoAcidCounts (acids : List AminoAcid) : List Nat :=
  let allTypes := [.F, .L, .I, .M, .V, .S, .P, .T, .A, .Y,
                  .H, .Q, .N, .K, .D, .E, .C, .W, .R, .G, .Stop]
  allTypes.map (fun t => acids.filter (· = t) |>.length)

/-- Calculate Shannon entropy of amino acid distribution. -/
def aminoAcidEntropy (acids : List AminoAcid) : Semantics.Q16_16.Q16_16 :=
  let total := acids.length
  if total == 0 then Semantics.Q16_16.Q16_16.zero
  else
    let counts := aminoAcidCounts acids
    let log2 (_x : Semantics.Q16_16.Q16_16) : Semantics.Q16_16.Q16_16 :=
      -- Simplified log2 approximation for Q16_16
      -- TODO: Implement proper log2 for Q16_16
      Semantics.Q16_16.Q16_16.zero
    let entropy := counts.foldl (fun acc count =>
      if count == 0 then acc
      else
        let p := Semantics.Q16_16.Q16_16.div (Semantics.Q16_16.Q16_16.ofNat count) (Semantics.Q16_16.Q16_16.ofNat total)
        let term := Semantics.Q16_16.Q16_16.mul p (log2 p)
        Semantics.Q16_16.Q16_16.sub acc term) Semantics.Q16_16.Q16_16.zero
    Semantics.Q16_16.Q16_16.neg entropy

/-- RGFlow filter parameters for text data. -/
structure RGFlowTextParams where
  entropyMin : Semantics.Q16_16.Q16_16  := floatToQ16_16 2.5
  entropyMax : Semantics.Q16_16.Q16_16  := floatToQ16_16 4.2
  spectralMax : Semantics.Q16_16.Q16_16 := floatToQ16_16 0.95
deriving Inhabited

/-- Calculate sigma_q based on entropy and spectral density filters. -/
def calculateSigmaQ (entropy : Semantics.Q16_16.Q16_16) (spectralDensity : Semantics.Q16_16.Q16_16)
                    (params : RGFlowTextParams) : Semantics.Q16_16.Q16_16 :=
  if Semantics.Q16_16.Q16_16.lt params.entropyMin entropy && Semantics.Q16_16.Q16_16.lt entropy params.entropyMax &&
     Semantics.Q16_16.Q16_16.lt spectralDensity params.spectralMax then
    Semantics.Q16_16.Q16_16.add Semantics.Q16_16.Q16_16.one (Semantics.Q16_16.Q16_16.div entropy (floatToQ16_16 4.0))
  else
    floatToQ16_16 0.5

/-- RGFlow state for text window. -/
structure TextRGFlowState where
  mu_q : Semantics.Q16_16.Q16_16
  sigma_q : Semantics.Q16_16.Q16_16
  entropy : Semantics.Q16_16.Q16_16
  spectralDensity : Semantics.Q16_16.Q16_16
  lawful : Bool

/-- Calculate RGFlow state for text window. -/
def calculateTextRGFlowState (text : String) (params : RGFlowTextParams) : TextRGFlowState :=
  let acids := textToAminoAcids text
  let entropy := aminoAcidEntropy acids
  let spectral := spectralDensity acids
  let mu_q := calculateMuQ acids
  let sigma_q := calculateSigmaQ entropy spectral params
  let lawful := Semantics.Q16_16.Q16_16.lt params.entropyMin entropy && Semantics.Q16_16.Q16_16.lt entropy params.entropyMax &&
                Semantics.Q16_16.Q16_16.lt spectral params.spectralMax
  { mu_q := mu_q
  , sigma_q := sigma_q
  , entropy := entropy
  , spectralDensity := spectral
  , lawful := lawful }

/-- Filter text window for lawfulness under RGFlow. -/
def isTextLawful (text : String) (params : RGFlowTextParams) : Bool :=
  (calculateTextRGFlowState text params).lawful

end Semantics.HutterPrizeRGFlow
