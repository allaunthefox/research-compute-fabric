/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

GenomicEvolutionLaws.lean — Laws of mutation accumulation and the drift-selection barrier.

This module formalizes the laws governing genomic complexity and stability:
1. Accumulation: Muller's Ratchet and the loss of the fittest class.
2. Barrier: Lynch's Drift-Barrier hypothesis for genome expansion.
3. Equilibrium: Neutral genetic diversity and mutation-drift balance.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.GenomeEvolution

open Semantics
open Semantics.Q16_16

/-! ## 1. Mutation Accumulation (Muller's Ratchet) -/

/-- Fittest Class Population (n0).
    n0 = N * exp(-lambda / s)
    N: effective population size, lambda: mutation rate, s: selection cost.
    The ratchet clicks if n0 becomes too small. -/
def fittestClassSize (n_pop lambda_rate selection_s : Q16_16) : Q16_16 :=
  -- exp(-lambda/s) approximation via 1 - lambda/s
  if selection_s == Q16_16.zero then Q16_16.zero
  else
    let decay := Q16_16.sub Q16_16.one (Q16_16.div lambda_rate selection_s)
    Q16_16.mul n_pop decay

/-! ## 2. The Drift Barrier (Lynch's Law) -/

/-- Selection Visibility Condition.
    Selection can 'see' and purify a mutation only if |s| > 1 / (2 * Ne).
    Otherwise, the mutation is governed by random genetic drift. -/
def isSelectionVisible (selection_s n_effective : Q16_16) : Bool :=
  let drift_power := Q16_16.div Q16_16.one (Q16_16.mul (Q16_16.ofInt 2) n_effective)
  selection_s.val.toNat > drift_power.val.toNat

/-! ## 3. Mutation-Drift Equilibrium -/

/-- Neutral Genetic Diversity (θ).
    θ = 4 * Ne * u
    Ne: Effective population size, u: mutation rate per nucleotide. -/
def neutralDiversityTheta (n_effective mutation_u : Q16_16) : Q16_16 :=
  Q16_16.mul (Q16_16.ofInt 4) (Q16_16.mul n_effective mutation_u)

end Semantics.Biology.GenomeEvolution
