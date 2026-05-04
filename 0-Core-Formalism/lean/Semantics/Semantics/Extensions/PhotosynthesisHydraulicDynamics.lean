/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

PhotosynthesisHydraulicDynamics.lean — Laws of carbon assimilation, stomatal control, and WUE.

This module formalizes the laws of plant gas exchange and energetics:
1. Assimilation: The FvCB model for Rubisco and RuBP limited photosynthesis.
2. Control: The Ball-Berry model for stomatal conductance (gs).
3. Efficiency: Water-Use Efficiency (WUE) and the carbon-water compromise.
4. Response: The non-rectangular hyperbola (NRH) light response curve.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Photosynthesis

open Semantics
open Semantics.FixedPoint

/-! ## 1. Carbon Assimilation (FvCB) -/

/-- Rubisco-Limited Rate (Ac).
    Ac = Vcmax * (Cc - Gamma) / (Cc + Kc*(1 + O/Ko))
    Models the biochemical capacity of the Calvin cycle at low CO2. -/
def rubiscoLimitedRate (vcmax cc gamma kc ko o_conc : Q16_16) : Q16_16 :=
  let num := Q16_16.sub cc gamma
  let den := Q16_16.add cc (Q16_16.mul kc (Q16_16.add Q16_16.one (Q16_16.div o_conc ko)))
  if den == Q16_16.zero then Q16_16.zero
  else Q16_16.mul vcmax (Q16_16.div num den)

/-- RuBP Regeneration-Limited Rate (Aj).
    Aj = (J / 4) * (Cc - Gamma) / (Cc + 2*Gamma)
    Models the light-limited capacity of electron transport. -/
def rubpRegenRate (j_flux cc gamma : Q16_16) : Q16_16 :=
  let num := Q16_16.sub cc gamma
  let den := Q16_16.add cc (Q16_16.mul (Q16_16.ofInt 2) gamma)
  if den == Q16_16.zero then Q16_16.zero
  else Q16_16.mul (Q16_16.div j_flux (Q16_16.ofInt 4)) (Q16_16.div num den)

/-! ## 2. Stomatal Conductance (Ball-Berry) -/

/-- Ball-Berry Conductance (gs).
    gs = g0 + m * (An * hs / Cs)
    g0: residual conductance, m: sensitivity, An: assimilation, hs: humidity, Cs: surface CO2. -/
def stomatalConductance (g0 sensitivity an humidity cs : Q16_16) : Q16_16 :=
  if cs == Q16_16.zero then g0
  else 
    let bb_index := Q16_16.div (Q16_16.mul an humidity) cs
    Q16_16.add g0 (Q16_16.mul sensitivity bb_index)

/-! ## 3. Water-Use Efficiency (WUE) -/

/-- Intrinsic Water-Use Efficiency (iWUE).
    iWUE = An / gs
    Formalizes the carbon-gain per unit of water-loss capacity. -/
def intrinsicWUE (an gs : Q16_16) : Q16_16 :=
  if gs == Q16_16.zero then Q16_16.zero
  else Q16_16.div an gs

/-! ## 4. Light Response (NRH) -/

/-- Rectangular Hyperbola Light Response (Pn).
    Pn = (alpha * I * Pmax) / (alpha * I + Pmax) - Rd
    Models the saturating response of photosynthesis to light intensity. -/
def lightResponseRate (alpha intensity pmax rd : Q16_16) : Q16_16 :=
  let gain := Q16_16.mul alpha intensity
  let num := Q16_16.mul gain pmax
  let den := Q16_16.add gain pmax
  if den == Q16_16.zero then Q16_16.neg rd
  else Q16_16.sub (Q16_16.div num den) rd

end Semantics.Biology.Photosynthesis
