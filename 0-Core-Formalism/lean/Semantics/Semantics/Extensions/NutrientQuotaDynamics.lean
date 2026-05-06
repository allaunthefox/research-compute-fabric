/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

NutrientQuotaDynamics.lean — Laws of internal nutrient storage and cell composition.

This module formalizes the laws governing nutrient-limited growth and storage:
1. Storage: Michael Droop's equation for quota-dependent growth.
2. Stability: Denis Herbert's law of constant cell composition at steady state.
3. Flux: Decoupled uptake and growth kinetics for luxury consumption.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.NutrientQuota

open Semantics
open Semantics.Q16_16

/-! ## 1. Variable Internal Quota (Droop) -/

/-- Droop Growth Rate (μ).
    μ(Q) = μ_inf * (1 - Q0 / Q)
    Q: actual cell quota, Q0: subsistence quota, μ_inf: theoretical max rate.
    Formalizes how internal reserves determine growth in luxury-uptake organisms. -/
def droopGrowthRate (q_actual q_subsistence mu_inf : Q16_16) : Q16_16 :=
  if q_actual == Q16_16.zero then Q16_16.zero
  else
    let ratio := Q16_16.div q_subsistence q_actual
    Q16_16.mul mu_inf (Q16_16.sub Q16_16.one ratio)

/-! ## 2. Constant Composition (Herbert) -/

/-- Herbert's Composition Invariant (Q).
    Q = 1 / Y = Constant
    Formalizes the fixed stoichiometry of cells at steady state. -/
def cellQuotaInvariant (yield : Q16_16) : Q16_16 :=
  if yield == Q16_16.zero then Q16_16.zero
  else Q16_16.div Q16_16.one yield

/-! ## 3. Quota Dynamics -/

/-- Cell Quota Update Step (dQ/dt).
    dQ/dt = ρ(S) - μ*Q
    ρ(S): external nutrient uptake, μ: growth rate, Q: quota. -/
def quotaUpdateStep (q_current uptake_rate growth_rate dt : Q16_16) : Q16_16 :=
  let consumption := Q16_16.mul growth_rate q_current
  let dQ := Q16_16.sub uptake_rate consumption
  Q16_16.add q_current (Q16_16.mul dQ dt)

end Semantics.Biology.NutrientQuota
