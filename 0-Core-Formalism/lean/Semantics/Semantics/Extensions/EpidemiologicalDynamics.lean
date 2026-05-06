/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

EpidemiologicalDynamics.lean — Laws of infectious disease spread and herd immunity.

This module formalizes the laws of biological contagion:
1. Transmission: The Basic Reproduction Number (R0).
2. Resistance: The Herd Immunity Threshold (HIT).
3. Dynamics: The Susceptible-Infectious-Recovered (SIR) model.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Epidemiology

open Semantics
open Semantics.Q16_16

/-! ## 1. Transmission (R0) -/

/-- Basic Reproduction Number (R0).
    R0 = beta / gamma
    Average number of secondary infections in a susceptible population. -/
def basicReproductionNumber (beta_infection_rate gamma_recovery_rate : Q16_16) : Q16_16 :=
  if gamma_recovery_rate == Q16_16.zero then Q16_16.mk 0xFFFFFFFF
  else Q16_16.div beta_infection_rate gamma_recovery_rate

/-! ## 2. Herd Immunity -/

/-- Herd Immunity Threshold (HIT).
    HIT = 1 - 1/R0
    The proportion of the population that must be immune to stop an outbreak. -/
def herdImmunityThreshold (r0 : Q16_16) : Q16_16 :=
  if r0.val.toNat < 0x00010000 then Q16_16.zero -- r0 < 1.0, no outbreak
  else Q16_16.sub Q16_16.one (Q16_16.div Q16_16.one r0)

/-! ## 3. SIR Dynamics -/

/-- SIR Model State.
    s: susceptible, i: infectious, r: recovered. -/
structure SIRState where
  s : Q16_16
  i : Q16_16
  r : Q16_16
  deriving Repr, DecidableEq

def sirUpdate (state : SIRState) (beta gamma dt : Q16_16) : SIRState :=
  let infection := Q16_16.mul (Q16_16.mul beta state.s) state.i
  let recovery := Q16_16.mul gamma state.i
  { s := Q16_16.sub state.s (Q16_16.mul infection dt)
  , i := Q16_16.add state.i (Q16_16.mul (Q16_16.sub infection recovery) dt)
  , r := Q16_16.add state.r (Q16_16.mul recovery dt) }

end Semantics.Biology.Epidemiology
