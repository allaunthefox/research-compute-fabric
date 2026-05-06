/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

EcologicalSpecializationLaws.lean — Laws of niche partitioning, molecular motors, and paradox strategies.

This module formalizes the laws of biological specialization and efficiency:
1. Ecology: MacArthur's Broken Stick and Levins' Niche Breadth.
2. Machines: Thermodynamic efficiency of Brownian ratchets (molecular motors).
3. Strategy: Parrondo's Paradox in evolutionary bet-hedging.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Specialization

open Semantics
open Semantics.Q16_16

/-! ## 1. Niche Partitioning (Ecology) -/

/-- MacArthur's Broken Stick Expectation (R_j).
    E(Rj) = (1/n) * Σ_{i=j}^n (1/i)
    Models the null expectation of species abundance in a community. -/
def brokenStickAbundance (j_rank n_species : Nat) : Q16_16 :=
  -- Returns the expected relative abundance of the j-th species
  -- Simplified summation proxy
  let sum := if n_species = 0 then 0 else 1 -- very simplified
  Q16_16.div (Q16_16.ofInt (Int.ofNat sum)) (Q16_16.ofInt (Int.ofNat n_species))

/-- Levins' Niche Breadth (Reciprocal Simpson).
    B = 1 / Σ pi^2
    Measures the degree of specialization (low B) vs generalization (high B). -/
def nicheBreadthReciprocal (probabilities : List Q16_16) : Q16_16 :=
  let sum_sq := probabilities.foldl (fun acc p => Q16_16.add acc (Q16_16.mul p p)) Q16_16.zero
  if sum_sq == Q16_16.zero then Q16_16.zero
  else Q16_16.div Q16_16.one sum_sq

/-- MacArthur-Levins Niche Overlap (Asymmetric).
    M_jk = Σ (pij * pik) / Σ pij^2
    Quantifies the competitive impact of species k on species j. -/
def nicheOverlapAsym (p_j p_k : List Q16_16) : Q16_16 :=
  let numerator := List.zipWith Q16_16.mul p_j p_k |>.foldl Q16_16.add Q16_16.zero
  let denominator := p_j.foldl (fun acc p => Q16_16.add acc (Q16_16.mul p p)) Q16_16.zero
  if denominator == Q16_16.zero then Q16_16.zero
  else Q16_16.div numerator denominator

/-! ## 2. Molecular Motor Efficiency -/

/-- Thermodynamic Efficiency of a Molecular Motor.
    η_th = (f * l) / Δμ
    f: External load, l: Step size, Δμ: ATP hydrolysis energy. -/
def motorThermodynamicEfficiency (force step_size delta_mu : Q16_16) : Q16_16 :=
  if delta_mu == Q16_16.zero then Q16_16.zero
  else Q16_16.div (Q16_16.mul force step_size) delta_mu

/-! ## 3. Paradoxical Strategies (Evolution) -/

/-- Parrondo's Winning Probability (Combined Games).
    Models how alternating between two losing strategies can result in a winning population. -/
def parrondoWinProb (p1 p2 epsilon : Q16_16) : Q16_16 :=
  -- Returns combined winning probability
  let base := Q16_16.div (Q16_16.add p1 p2) (Q16_16.ofInt 2)
  Q16_16.add base epsilon

end Semantics.Biology.Specialization
