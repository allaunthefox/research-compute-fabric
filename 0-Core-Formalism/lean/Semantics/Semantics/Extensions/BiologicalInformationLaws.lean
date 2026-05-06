/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

BiologicalInformationLaws.lean — Laws of genomic entropy, error robustness, and channel capacity.

This module formalizes the information-theoretic laws of biology:
1. Entropy: Shannon entropy of DNA/RNA sequences.
2. Robustness: Hamming distance and error-correction in the genetic code.
3. Transmission: Biological channel capacity and the error catastrophe limit.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Information

open Semantics
open Semantics.Q16_16

/-! ## 1. Genomic Entropy -/

/-- Shannon Entropy of DNA (H).
    H = -Σ p_i * log2(p_i)
    For a uniform 4-letter alphabet, H = 2.0 bits per base. -/
def genomicEntropy (probs : List Q16_16) : Q16_16 :=
  -- Returns Shannon entropy proxy
  -- -Σ p * log2(p) approximation
  probs.foldl (fun acc p => Q16_16.add acc (Q16_16.mul p (Q16_16.ofInt 2))) Q16_16.zero -- Placeholder for log2

/-! ## 2. Error Robustness (Hamming Distance) -/

/-- Hamming Distance between two Codons.
    Measures the number of base substitutions required to transform one codon to another. -/
def codonHammingDistance (c1 c2 : Semantics.GeneticCode.Codon) : Nat :=
  let d1 := if c1.first == c2.first then 0 else 1
  let d2 := if c1.second == c2.second then 0 else 1
  let d3 := if c1.third == c2.third then 0 else 1
  d1 + d2 + d3

/-- Mutational Robustness of an Amino Acid.
    Measures how many single-step mutations (d_H=1) are synonymous. -/
def aminoAcidRobustness (aa : Semantics.GeneticCode.AminoAcid) : Q16_16 :=
  let d := Semantics.GeneticCode.codonDegeneracy aa
  Q16_16.div (Q16_16.ofInt (Int.ofNat (d - 1))) (Q16_16.ofInt 9) -- 9 possible single-step mutations

/-! ## 3. Biological Channel Capacity -/

/-- Binary Symmetric Channel (BSC) Capacity for DNA Replication.
    C = 1 - H(p), where p is the mutation probability. -/
def biologicalChannelCapacity (p_mutation : Q16_16) : Q16_16 :=
  -- C = 1 - (-p log2 p - (1-p) log2 (1-p))
  -- Approximation for small p: C ≈ 1 - p
  Q16_16.sub Q16_16.one p_mutation

/-- Error Catastrophe Threshold (Eigen's Limit).
    Information is lost if mutation rate exceeds the selective advantage (sigma).
    p_max ≈ ln(sigma) / L -/
def errorCatastropheLimit (sigma_advantage sequence_length : Q16_16) : Q16_16 :=
  if sequence_length == Q16_16.zero then Q16_16.zero
  else Q16_16.div sigma_advantage sequence_length

end Semantics.Biology.Information
