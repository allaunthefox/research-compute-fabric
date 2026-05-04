/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

EvolutionaryLandscapeDynamics.lean — Laws of adaptive landscapes and the shifting balance theory.

This module formalizes the laws of population movement across fitness manifolds:
1. Gradient: Wright's equation for frequency change via selection gradients.
2. Fitness: The mean fitness landscape as a multi-dimensional surface.
3. Balance: The three phases of Wright's Shifting Balance Theory.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Landscapes

open Semantics
open Semantics.FixedPoint

/-! ## 1. Wright's Gradient Law -/

/-- Allele Frequency Change (Δq).
    Δq = [q*(1-q) / 2w_avg] * (dw_avg / dq)
    Models the 'gradient ascent' of a population toward a local fitness peak. -/
def frequencyChangeGradient (q w_avg grad_w : Q16_16) : Q16_16 :=
  let var_term := Q16_16.mul q (Q16_16.sub Q16_16.one q)
  let den := Q16_16.mul (Q16_16.ofInt 2) w_avg
  if den == Q16_16.zero then Q16_16.zero
  else Q16_16.mul (Q16_16.div var_term den) grad_w

/-! ## 2. Mean Fitness (Adaptive Landscape) -/

/-- Population Mean Fitness (w_avg).
    w_avg = p²*w11 + 2pq*w12 + q²*w22
    Defines the value of the adaptive landscape at a specific coordinate. -/
def populationMeanFitness (p q w11 w12 w22 : Q16_16) : Q16_16 :=
  let p2 := Q16_16.mul p p
  let q2 := Q16_16.mul q q
  let two_pq := Q16_16.mul (Q16_16.ofInt 2) (Q16_16.mul p q)
  Q16_16.add (Q16_16.mul p2 w11) (Q16_16.add (Q16_16.mul two_pq w12) (Q16_16.mul q2 w22))

/-! ## 3. Shifting Balance Transitions -/

/-- Phase I: Exploratory Drift.
    Checks if genetic drift is strong enough to cross a fitness valley. -/
def isDriftDominant (n_effective selection_s : Q16_16) : Bool :=
  -- 4 * Ne * s < 1
  let product := Q16_16.mul (Q16_16.ofInt 4) (Q16_16.mul n_effective selection_s)
  product.val.toNat < 0x00010000 -- < 1.0 in Q16.16

/-- Phase II: Mass Selection.
    Checks if a subpopulation is at the base of a higher peak. -/
def isAscendingPeak (gradient : Q16_16) : Bool :=
  gradient.val.toNat > 0

end Semantics.Biology.Landscapes
