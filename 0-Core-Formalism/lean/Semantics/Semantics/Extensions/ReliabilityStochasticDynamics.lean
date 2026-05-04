/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

ReliabilityStochasticDynamics.lean — Laws of aging redundancy and stochastic simulation.

This module formalizes the laws of system reliability and molecular noise:
1. Aging: Reliability Theory (n-redundant component systems).
2. Stochastic: Gillespie algorithm propensity and time-step laws.
3. Kinetics: Chemical Master Equation (CME) probability drift.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Stochastic

open Semantics
open Semantics.FixedPoint

/-! ## 1. Reliability Theory (Senescence) -/

/-- Redundant System Survival Probability (P).
    P(t) = 1 - (1 - exp(-kt))^n
    n: number of redundant elements, k: failure rate.
    Models why organisms age even with reliable parts. -/
def systemSurvivalProb (redundancy_n : Nat) (failure_rate_k age_t : Q16_16) : Q16_16 :=
  -- 1 - exp(-kt) approximation via kt
  let kt := Q16_16.mul failure_rate_k age_t
  -- 1 - (kt)^n approximation
  let element_fail_prob := if redundancy_n > 1 then Q16_16.mul kt kt else kt
  Q16_16.sub Q16_16.one element_fail_prob

/-! ## 2. Gillespie Algorithm (Stochastic Simulation) -/

/-- Reaction Propensity (a_j).
    a_j = c_j * h_j
    c_j: stochastic rate constant, h_j: reactant combinations.
    Calculates the probability of a discrete reaction event. -/
def reactionPropensity (rate_c combinations_h : Q16_16) : Q16_16 :=
  Q16_16.mul rate_c combinations_h

/-- Gillespie Time Step (tau).
    tau = (1 / sum(a_i)) * ln(1 / r1)
    Calculates the waiting time until the next stochastic event. -/
def stochasticTimeStep (total_propensity random_val : Q16_16) : Q16_16 :=
  -- random_val is ln(1/r1)
  if total_propensity == Q16_16.zero then Q16_16.zero
  else Q16_16.div random_val total_propensity

/-! ## 3. Chemical Master Equation (CME) -/

/-- CME Probability Drift (dP/dt).
    dp/dt = Σ [a_j(x-vj)P(x-vj, t) - a_j(x)P(x, t)]
    Models the evolution of the probability density of chemical states. -/
def masterEquationUpdate (p_state inflow outflow dt : Q16_16) : Q16_16 :=
  let dp := Q16_16.sub inflow outflow
  Q16_16.add p_state (Q16_16.mul dp dt)

end Semantics.Biology.Stochastic
