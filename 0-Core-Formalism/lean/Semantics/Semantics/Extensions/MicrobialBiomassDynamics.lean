/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

MicrobialBiomassDynamics.lean — Laws of microbial growth, maintenance, and biomass accumulation.

This module formalizes the laws of sub-cellular and population-scale growth:
1. Growth: Monod substrate kinetics and Verhulst logistic growth.
2. Energy: Pirt's law for maintenance energy partitioning.
3. Biomass: Gompertz sigmoidal growth for tumors and colonies.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Biomass

open Semantics
open Semantics.Q16_16

/-! ## 1. Nutrient-Limited Growth (Monod) -/

/-- Monod Growth Rate (μ).
    μ = μ_max * S / (Ks + S)
    S: Substrate concentration, Ks: Half-saturation constant. -/
def monodGrowthRate (mu_max substrate ks_half_sat : Q16_16) : Q16_16 :=
  let num := Q16_16.mul mu_max substrate
  let den := Q16_16.add ks_half_sat substrate
  if den == Q16_16.zero then Q16_16.zero
  else Q16_16.div num den

/-! ## 2. Maintenance Energy (Pirt) -/

/-- Pirt's Maintenance Law (qs).
    qs = μ / Y_G + m
    qs: Specific uptake rate, Y_G: True growth yield, m: Maintenance rate. -/
def specificUptakeRate (growth_rate true_yield maintenance : Q16_16) : Q16_16 :=
  let growth_cost := if true_yield == Q16_16.zero then Q16_16.zero else Q16_16.div growth_rate true_yield
  Q16_16.add growth_cost maintenance

/-! ## 3. Population Dynamics (Verhulst) -/

/-- Verhulst Logistic Growth Step.
    dP/dt = r*P * (1 - P/K)
    r: Intrinsic growth rate, K: Carrying capacity. -/
def logisticGrowthUpdate (pop r capacity dt : Q16_16) : Q16_16 :=
  let resistance := Q16_16.sub Q16_16.one (Q16_16.div pop capacity)
  let growth := Q16_16.mul (Q16_16.mul r pop) resistance
  Q16_16.add pop (Q16_16.mul growth dt)

/-! ## 4. Asymmetric Biomass Growth (Gompertz) -/

/-- Gompertz Biomass Growth Rate (dV/dt).
    dV/dt = r * V * ln(K/V)
    Models asymmetric sigmoidal growth where maximum rate is at 1/e of K. -/
def gompertzGrowthUpdate (volume r capacity dt : Q16_16) : Q16_16 :=
  -- ln(K/V) approximation via (K/V - 1)
  let log_proxy := Q16_16.sub (Q16_16.div capacity volume) Q16_16.one
  let growth := Q16_16.mul (Q16_16.mul r volume) log_proxy
  Q16_16.add volume (Q16_16.mul growth dt)

end Semantics.Biology.Biomass
