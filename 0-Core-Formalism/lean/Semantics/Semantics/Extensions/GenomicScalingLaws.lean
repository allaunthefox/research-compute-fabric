/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

GenomicScalingLaws.lean — Laws of gene family size and functional category scaling.

This module formalizes Eugene Koonin's universal scaling laws of genome evolution:
1. Complexity: The power law distribution of gene family sizes.
2. Architecture: Functional scaling laws (Non-linear scaling of regulation).
3. Dynamics: The Birth-Death-Innovation Model (BDIM) for genome expansion.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.GenomeScaling

open Semantics
open Semantics.FixedPoint

/-! ## 1. Gene Family Complexity -/

/-- Gene Family Size Probability (Pi).
    P(i) = i^-gamma
    i: family size (paralog count), gamma: scaling exponent (typically 1.5 - 3.0).
    Formalizes the 'Superfamily' distribution in genomes. -/
def familySizeProb (size_i gamma_exponent : Q16_16) : Q16_16 :=
  -- Returns probability Pi
  -- size^-gamma approximation
  Q16_16.div Q16_16.one (Q16_16.mul size_i gamma_exponent)

/-! ## 2. Functional Scaling (Architecture) -/

/-- Functional Category Scaling (Nc).
    Nc = k * G^alpha
    G: total gene count, alpha: category-specific exponent.
    Exponents: alpha ≈ 2 (Regulation), alpha ≈ 1 (Metabolism), alpha ≈ 0.3 (Translation). -/
def functionalGeneCount (total_genes k_const alpha_exponent : Q16_16) : Q16_16 :=
  -- Returns number of genes in category c
  -- k * G^alpha approximation
  let g_pow := if alpha_exponent.val.toNat > 0x00018000 then Q16_16.mul total_genes total_genes -- approx quadratic
               else if alpha_exponent.val.toNat < 0x00008000 then total_genes -- simplified sub-linear
               else total_genes -- linear
  Q16_16.mul k_const g_pow

/-! ## 3. Birth-Death-Innovation Dynamics -/

/-- BDIM Population Step (ni).
    dni/dt = lambda_{i-1}*ni-1 - (lambda_i + delta_i)ni + delta_{i+1}*ni+1
    lambda: birth rate, delta: death rate.
    Models the temporal evolution of gene family sizes. -/
def bdimUpdate (n_i birth_rate death_rate inflow outflow dt : Q16_16) : Q16_16 :=
  let dn := Q16_16.sub (Q16_16.add inflow (Q16_16.mul birth_rate n_i)) (Q16_16.add outflow (Q16_16.mul death_rate n_i))
  Q16_16.add n_i (Q16_16.mul dn dt)

end Semantics.Biology.GenomeScaling
