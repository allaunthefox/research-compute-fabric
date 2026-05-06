/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

FisherGeometricAdaptationLaws.lean — Laws of phenotypic complexity and beneficial mutations.

This module formalizes R.A. Fisher's Geometric Model (FGM) of adaptation:
1. Fitness: Gaussian phenotypic fitness potential.
2. Mutation: The probability of a beneficial mutation in n-dimensional space.
3. Complexity: The cost of complexity and the law of small mutations.
4. Pleiotropy: The geometric impact of a single mutation vector.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.FisherGeometric

open Semantics
open Semantics.Q16_16

/-! ## 1. Phenotypic Fitness Potential -/

/-- FGM Fitness Function (w).
    w(z) = exp(-||z - z_opt||^2 / 2sigma^2)
    Models fitness as the Euclidean proximity to a multidimensional optimum. -/
def phenotypicFitness (distance_sq sigma_sq : Q16_16) : Q16_16 :=
  -- exp(-d^2 / 2s^2) approximation via 1 - d^2 / 2s^2
  let den := Q16_16.mul (Q16_16.ofInt 2) sigma_sq
  if den == Q16_16.zero then Q16_16.zero
  else Q16_16.sub Q16_16.one (Q16_16.div distance_sq den)

/-! ## 2. Beneficial Mutation Probability -/

/-- Probability of a Beneficial Mutation (Pa).
    Pa ≈ 1 - Φ(r * sqrt(n) / 2d)
    r: mutation magnitude, n: complexity (dimensions), d: distance to optimum.
    Formalizes the 'Cost of Complexity' in evolution. -/
def beneficialMutationProb (magnitude complexity distance : Q16_16) : Q16_16 :=
  -- Returns Pa
  -- 1 - (r * sqrt(n) / 2d) approximation
  let num := Q16_16.mul magnitude complexity -- simplified for sqrt(n)
  let den := Q16_16.mul (Q16_16.ofInt 2) distance
  if den == Q16_16.zero then Q16_16.zero
  else Q16_16.sub Q16_16.one (Q16_16.div num den)

/-! ## 3. Cost of Complexity Scaling -/

/-- Law of Small Mutations.
    As mutation size r -> 0, Pa -> 0.5.
    Small mutations are the primary driver of adaptation in complex systems. -/
def Pa_limit_zero : Q16_16 :=
  -- Returns 0.5 in Q16.16
  Q16_16.div Q16_16.one (Q16_16.ofInt 2)

/-- Complexity Penalty.
    Beneficial probability decreases as 1/sqrt(n). -/
def complexityPenalty (n_dims : Nat) : Q16_16 :=
  let n_f := Q16_16.ofInt (Int.ofNat n_dims)
  Q16_16.div Q16_16.one n_f -- Placeholder for sqrt(n)

end Semantics.Biology.FisherGeometric
