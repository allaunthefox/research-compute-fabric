/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

PopulationChaosDynamics.lean — Laws of discrete chaos, stability, and lifespan limits.

This module formalizes the laws of population behavior and longevity:
1. Chaos: Robert May's Logistic Map and bifurcation transitions.
2. Stability: Lotka's stable population age distribution.
3. Longevity: Tetz's Law of pangenome alterations and lifespan limits.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Population

open Semantics
open Semantics.Q16_16

/-! ## 1. Discrete Population Chaos -/

/-- The Logistic Map.
    x_{n+1} = r * x_n * (1 - x_n)
    Models population fluctuations and the transition to chaos at r > 3.57. -/
def logisticMap (x_n r : Q16_16) : Q16_16 :=
  let one_minus_x := Q16_16.sub Q16_16.one x_n
  Q16_16.mul r (Q16_16.mul x_n one_minus_x)

/-! ## 2. Stable Population Theory -/

/-- Lotka's Characteristic Invariant (Proxy).
    Describes the intrinsic rate of natural increase (r) for a stable population. -/
def lotkaStabilityScore (fertility_rate survival_rate intrinsic_rate : Q16_16) : Q16_16 :=
  -- Returns the integral result proxy for e^(-ra) p(a) m(a)
  let decay := Q16_16.sub Q16_16.one intrinsic_rate
  Q16_16.mul decay (Q16_16.mul fertility_rate survival_rate)

/-! ## 3. Longevity and Death -/

/-- Tetz's Law of Longevity (Pangenome Alterations).
    Death occurs when total alterations q(t) reach a critical threshold q_max. -/
def lifePersistenceRatio (current_alterations q_max : Q16_16) : Q16_16 :=
  if q_max == Q16_16.zero then Q16_16.zero
  else Q16_16.sub Q16_16.one (Q16_16.div current_alterations q_max)

/-- Stretched Exponential Survival (Lifespan Limit).
    Models the drop to near-zero survival probability at the species limit. -/
def survivalProbability (age limit : Q16_16) : Q16_16 :=
  if age.val.toNat > limit.val.toNat then Q16_16.zero
  else Q16_16.sub Q16_16.one (Q16_16.div age limit)

end Semantics.Biology.Population
