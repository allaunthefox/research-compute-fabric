/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

LifeHistoryOptimizationLaws.lean — Laws of offspring investment and reproductive strategy.

This module formalizes the laws of biological resource allocation:
1. Lack's Principle: Optimal clutch size for maximizing surviving offspring.
2. Smith-Fretwell: The trade-off between offspring size and offspring number.
3. Scaling: Life history parameter scaling with body mass.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Optimization

open Semantics
open Semantics.Q16_16

/-! ## 1. Optimal Clutch Size (Lack's Principle) -/

/-- Lack's Fitness Function (W).
    W = n * P(n)
    n: clutch size, P(n): individual survival probability. -/
def survivingOffspringCount (n_size : Nat) (survival_prob : Q16_16) : Q16_16 :=
  let n_f := Q16_16.ofInt (Int.ofNat n_size)
  Q16_16.mul n_f survival_prob

/-- Individual Survival Probability (P).
    P(n) = exp(-k * n)
    Models the reduction in survival as parental resources are spread thinner. -/
def offspringSurvivalProb (n_size : Nat) (k_mortality : Q16_16) : Q16_16 :=
  -- exp(-kn) approximation via 1 - kn
  let n_f := Q16_16.ofInt (Int.ofNat n_size)
  Q16_16.sub Q16_16.one (Q16_16.mul k_mortality n_f)

/-! ## 2. Offspring Size vs. Number (Smith-Fretwell) -/

/-- Smith-Fretwell Fitness (W).
    W = (R / s) * f(s)
    R: total reproductive resources, s: individual investment (size), f(s): offspring fitness. -/
def parentalFitness (r_resources s_size f_offspring : Q16_16) : Q16_16 :=
  if s_size == Q16_16.zero then Q16_16.zero
  else Q16_16.mul (Q16_16.div r_resources s_size) f_offspring

/-- Optimal Size Condition (MVT).
    At optimal s*, f'(s) = f(s) / s. -/
def isOffspringSizeOptimal (marginal_fitness fitness_per_size : Q16_16) : Bool :=
  marginal_fitness == fitness_per_size

/-! ## 3. Life History Scaling -/

/-- Offspring Number Scaling.
    n ∝ M^(-1/4). -/
def offspringNumberScaling (body_mass : Q16_16) : Q16_16 :=
  -- Returns n proxy (M^-0.25)
  Q16_16.div Q16_16.one body_mass -- Placeholder for M^0.25

end Semantics.Biology.Optimization
