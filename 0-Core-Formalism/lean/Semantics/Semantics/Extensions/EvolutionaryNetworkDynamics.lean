/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

EvolutionaryNetworkDynamics.lean — Laws of evolutionary strategy and network topology.

This module formalizes the laws of competition and structure in biological systems:
1. Strategy: Evolutionarily Stable Strategies (ESS) and Hawk-Dove games.
2. Macroevolution: Van Valen's Law of Constant Extinction.
3. Topology: Scale-free networks and preferential attachment.
4. Robustness: Neutral networks and genotype-phenotype neutrality.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Evolutionary

open Semantics
open Semantics.Q16_16

/-! ## 1. Evolutionary Game Theory -/

/-- ESS Mixed Strategy (Hawk-Dove).
    p = V / C
    Probability of playing Hawk when cost of injury C exceeds resource value V. -/
def hawkDoveMixedStrategy (v_value c_cost : Q16_16) : Q16_16 :=
  if c_cost.val.toNat > v_value.val.toNat then Q16_16.div v_value c_cost
  else Q16_16.one -- Pure Hawk is ESS

/-- ESS Stability Condition.
    E(S, S) > E(T, S)
    Strategy S cannot be invaded by mutant strategy T. -/
def isStrategyStable (payoff_ss payoff_ts : Q16_16) : Bool :=
  payoff_ss.val.toNat > payoff_ts.val.toNat

/-! ## 2. Macroevolutionary Laws -/

/-- Van Valen's Law of Constant Extinction.
    ln(N) = -k*t + C
    Extinction probability is constant within a taxonomic group. -/
def genusExtinctionRate (k_ext t_time c_initial : Q16_16) : Q16_16 :=
  -- ln(N) approximation
  Q16_16.sub c_initial (Q16_16.mul k_ext t_time)

/-! ## 3. Biological Network Topology -/

/-- Scale-Free Degree Distribution (P(k)).
    P(k) = k^-gamma
    Models the robustness of metabolic and interaction networks. -/
def degreeProbability (k_degree gamma_exponent : Q16_16) : Q16_16 :=
  -- k^-gamma approximation
  Q16_16.div Q16_16.one (Q16_16.mul k_degree gamma_exponent)

/-- Preferential Attachment Weight.
    w_i = k_i / Σ k_j
    New nodes prefer to connect to highly-connected hubs. -/
def attachmentWeight (k_i sum_k : Q16_16) : Q16_16 :=
  if sum_k == Q16_16.zero then Q16_16.zero
  else Q16_16.div k_i sum_k

/-! ## 4. Robustness and Neutrality -/

/-- Neutral Mutation Condition (Kimura).
    |s| < 1 / Ne
    A mutation is effectively neutral if its selection coefficient s is smaller than 1/Ne. -/
def isMutationNeutral (s_coeff n_effective : Q16_16) : Bool :=
  let threshold := Q16_16.div Q16_16.one n_effective
  s_coeff.val.toNat < threshold.val.toNat

end Semantics.Biology.Evolutionary
