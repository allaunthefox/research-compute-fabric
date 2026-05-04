/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

EpidemiologicalTrophicDynamics.lean — Laws of infection chain-binomials and trophic waves.

This module formalizes the laws of contagion spread and food web energy flow:
1. Infection: The Reed-Frost chain-binomial model for discrete generations.
2. Flow: The 'trophic wave' advection equation for biomass transfer.
3. Loss: Trophic kinetics and metabolic attenuation across levels.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Waves

open Semantics
open Semantics.FixedPoint

/-! ## 1. Discrete Infection (Reed-Frost) -/

/-- Reed-Frost Generation Step (C).
    C_{t+1} = S_t * (1 - q^Ct)
    St: susceptible, Ct: current cases, q: probability of escaping contact.
    Models the generation-by-generation spread of an epidemic. -/
def reedFrostNewCases (susceptible current_cases q_escape : Q16_16) : Q16_16 :=
  -- q^Ct approximation via 1 - Ct * p
  let p_contact := Q16_16.sub Q16_16.one q_escape
  let prob_infect := Q16_16.mul current_cases p_contact
  Q16_16.mul susceptible prob_infect

/-! ## 2. Trophic Biomass Waves -/

/-- Trophic Advection Step (Phi).
    dPhi/dt = -d(K*Phi)/dtau - mu*Phi
    Phi: biomass flow, K: trophic kinetics, tau: trophic level, mu: loss rate.
    Models the 'wave' of biomass moving up the food web spectrum. -/
def trophicWaveUpdate (phi kinetics grad_phi loss_rate dt : Q16_16) : Q16_16 :=
  let advection := Q16_16.mul kinetics grad_phi
  let loss := Q16_16.mul loss_rate phi
  let dPhi := Q16_16.add (Q16_16.neg advection) (Q16_16.neg loss)
  Q16_16.add phi (Q16_16.mul dPhi dt)

/-- Trophic Kinetic Constant (K).
    Related to the P/B ratio at a specific trophic level. -/
def trophicKinetics (production biomass : Q16_16) : Q16_16 :=
  if biomass == Q16_16.zero then Q16_16.zero
  else Q16_16.div production biomass

end Semantics.Biology.Waves
