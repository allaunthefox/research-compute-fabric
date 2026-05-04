/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

SoilFungalDynamics.lean — Laws of soil chemistry, hyphal growth, and global growth constraints.

This module formalizes the laws of subterranean biology and nutrient exchange:
1. Chemistry: Albrecht's Base Saturation Ratios (CEC percentages).
2. Mycorrhizae: Schnepf-Roose model for fungal hyphal tip flow.
3. Universal: The Terraced Barrel model for global growth constraints.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Subterranean

open Semantics
open Semantics.FixedPoint

/-! ## 1. Soil Base Saturation (Albrecht) -/

/-- Albrecht Base Saturation Percentage.
    %Saturation_i = (Conc_i / Total_CEC) * 100
    Models the 'ideal' chemical balance of soil for plant health. -/
def baseSaturationPct (cation_conc total_cec : Q16_16) : Q16_16 :=
  if total_cec == Q16_16.zero then Q16_16.zero
  else Q16_16.mul (Q16_16.ofInt 100) (Q16_16.div cation_conc total_cec)

/-! ## 2. Mycorrhizal Flow (Schnepf-Roose) -/

/-- Hyphal Tip Density Step (n).
    dn/dt = -v * dn/dx + b*n
    v: tip growth rate, b: branching rate.
    Models the exploratory 'mining' behavior of fungi. -/
def hyphalTipUpdate (n v grad_n b dt : Q16_16) : Q16_16 :=
  let advection := Q16_16.mul v grad_n
  let branching := Q16_16.mul b n
  let dn := Q16_16.add (Q16_16.neg advection) branching
  Q16_16.add n (Q16_16.mul dn dt)

/-! ## 3. Universal Growth (Terraced Barrel) -/

/-- Terraced Barrel Growth Rate (μ).
    μ = min(Internal_Constraint_i, Resource_Availability)
    Unifies Liebig and Monod into a sequential physical constraint law. -/
def terracedBarrelGrowth (constraints : List Q16_16) (resource_limit : Q16_16) : Q16_16 :=
  -- Returns the minimum of all internal and external constraints
  let internal_min := constraints.foldl (fun acc c => 
    if c.val.toNat < acc.val.toNat then c else acc
  ) (Q16_16.mk 0xFFFFFFFF)
  if resource_limit.val.toNat < internal_min.val.toNat then resource_limit
  else internal_min

end Semantics.Biology.Subterranean
