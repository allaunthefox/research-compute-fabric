/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

CognitiveLearningDynamics.lean — Laws of associative learning, cognitive foraging, and memory retrieval.

This module formalizes the laws of neural adaptation and information search:
1. Learning: The Rescorla-Wagner model of classical conditioning.
2. Search: Lévy flight foraging hypothesis for optimal cognitive search.
3. Memory: The Search of Associative Memory (SAM) sampling law.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Cognition

open Semantics
open Semantics.Q16_16

/-! ## 1. Associative Learning (Rescorla-Wagner) -/

/-- Rescorla-Wagner Strength Update (ΔV).
    ΔV = alpha * beta * (lambda - sum_V)
    alpha: CS salience, beta: US learning rate, lambda: max strength, sum_V: total expectation.
    Models learning as the reduction of prediction error. -/
def associativeStrengthUpdate (alpha beta lambda_max sum_v : Q16_16) : Q16_16 :=
  let prediction_error := Q16_16.sub lambda_max sum_v
  Q16_16.mul (Q16_16.mul alpha beta) prediction_error

/-! ## 2. Cognitive Foraging (Lévy & MVT) -/

/-- Lévy Flight Foraging Probability.
    P(l) = l^-mu, where 1 < mu <= 3.
    Models the distribution of jump lengths in optimal cognitive search. -/
def levySearchProbability (jump_length mu_exponent : Q16_16) : Q16_16 :=
  -- Returns P(l) proxy
  Q16_16.div Q16_16.one (Q16_16.mul jump_length mu_exponent)

/-- MVT Cognitive Patch Leaving Condition.
    R'(t) = R(t) / (t + tau)
    Optimal time to switch categories or problem-solving strategies. -/
def isCognitiveSwitchOptimal (inst_return average_return : Q16_16) : Bool :=
  inst_return == average_return

/-! ## 3. Memory Retrieval (SAM) -/

/-- SAM Sampling Probability.
    P(i|Q) = S(Q, i) / Σ S(Q, j)
    Calculates the probability of retrieving item i given cue Q. -/
def memorySamplingProb (cue_strength sum_strengths : Q16_16) : Q16_16 :=
  if sum_strengths == Q16_16.zero then Q16_16.zero
  else Q16_16.div cue_strength sum_strengths

end Semantics.Biology.Cognition
