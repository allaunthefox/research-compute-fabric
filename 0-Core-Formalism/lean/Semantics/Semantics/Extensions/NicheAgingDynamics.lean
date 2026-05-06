/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

NicheAgingDynamics.lean — Laws of resource competition, aging correlations, and mortality plateaus.

This module formalizes the laws of niche survival and the temporal limits of life:
1. Competition: Tilman's R* theory for resource competition.
2. Aging: Strehler-Mildvan correlation between initial mortality and aging rate.
3. Mortality: Late-life deceleration and the logistic mortality plateau.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.NicheAging

open Semantics
open Semantics.Q16_16

/-! ## 1. Resource Competition (Tilman) -/

/-- Tilman's R* Equilibrium.
    R* = (K * d) / (mu_max - d)
    The minimum resource level required for a population to sustain itself. -/
def resourceThresholdRStar (half_sat_k mortality_d growth_mu_max : Q16_16) : Q16_16 :=
  let num := Q16_16.mul half_sat_k mortality_d
  let den := Q16_16.sub growth_mu_max mortality_d
  if den == Q16_16.zero then Q16_16.zero
  else Q16_16.div num den

/-! ## 2. Aging and Vitality (Strehler-Mildvan) -/

/-- Strehler-Mildvan Correlation (Alpha-Beta).
    ln(alpha) = ln(K) - (V0/deltaE) * beta
    Relates the environmental risk (alpha) to the intrinsic aging rate (beta). -/
def strehlerMildvanCorrelation (beta v0_deltaE k_const : Q16_16) : Q16_16 :=
  -- Returns predicted ln(alpha)
  Q16_16.sub k_const (Q16_16.mul v0_deltaE beta)

/-- Vitality Decay Law.
    V(t) = V0 * (1 - Bt)
    Models the linear decline of homeostatic energy reserves with age. -/
def vitalityDecay (v0 b_rate age : Q16_16) : Q16_16 :=
  let decay := Q16_16.mul b_rate age
  Q16_16.mul v0 (Q16_16.sub Q16_16.one decay)

/-! ## 3. Mortality Plateaus -/

/-- Logistic Mortality Plateau.
    mu(x) = (a * exp(bx)) / (1 + (a/s)*(exp(bx) - 1))
    Models the deceleration of mortality at extreme old age. -/
def plateauMortality (age a_const b_rate s_limit : Q16_16) : Q16_16 :=
  -- exp(bx) approximation
  let exp_bx := Q16_16.add Q16_16.one (Q16_16.mul b_rate age)
  let num := Q16_16.mul a_const exp_bx
  let den := Q16_16.add Q16_16.one (Q16_16.mul (Q16_16.div a_const s_limit) (Q16_16.sub exp_bx Q16_16.one))
  Q16_16.div num den

end Semantics.Biology.NicheAging
