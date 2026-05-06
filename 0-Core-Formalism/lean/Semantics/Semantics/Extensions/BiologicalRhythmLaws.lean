/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

BiologicalRhythmLaws.lean — Laws of chemical oscillators, synchronization, and conservation.

This module formalizes the laws of temporal organization and mass balance:
1. Chemical: The Oregonator model of the Belousov-Zhabotinsky reaction.
2. Synchrony: Strogatz's model of pulse-coupled firefly entrainment.
3. Conservation: The general continuity equation for biological quantities.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Rhythms

open Semantics
open Semantics.Q16_16

/-! ## 1. Chemical Oscillators (Oregonator) -/

/-- Oregonator BZ Reaction Step.
    Governs the concentration shifts in non-equilibrium chemical clocks. -/
structure OregonatorState where
  x_acid : Q16_16
  y_bromide : Q16_16
  z_catalyst : Q16_16
  deriving Repr, DecidableEq

def oregonatorUpdate (s : OregonatorState) (q f epsilon delta dt : Q16_16) : OregonatorState :=
  let x := s.x_acid
  let y := s.y_bromide
  let z := s.z_catalyst
  let dx := Q16_16.div (Q16_16.add (Q16_16.sub (Q16_16.mul q y) (Q16_16.mul x y)) (Q16_16.mul x (Q16_16.sub Q16_16.one x))) epsilon
  let dy := Q16_16.div (Q16_16.add (Q16_16.sub (Q16_16.neg (Q16_16.mul q y)) (Q16_16.mul x y)) (Q16_16.mul f z)) delta
  let dz := Q16_16.sub x z
  { x_acid := Q16_16.add x (Q16_16.mul dx dt)
  , y_bromide := Q16_16.add y (Q16_16.mul dy dt)
  , z_catalyst := Q16_16.add z (Q16_16.mul dz dt) }

/-! ## 2. Collective Synchrony (Strogatz) -/

/-- Strogatz Firefly Synchrony Law.
    dtheta/dt = omega + A * sin(Theta - theta)
    Models the entrainment of a biological oscillator to a stimulus. -/
def synchronyPhaseDrift (omega coupling_strength phase_diff : Q16_16) : Q16_16 :=
  -- omega + A * sin(delta_theta) approximation
  let sine_approx := phase_diff -- linear approximation for sin
  Q16_16.add omega (Q16_16.mul coupling_strength sine_approx)

/-- Entrainment Condition.
    |Omega - omega| <= A
    Synchronization is possible only if coupling strength exceeds frequency mismatch. -/
def isEntrained (omega_stim omega_nat coupling_strength : Q16_16) : Bool :=
  let mismatch := Q16_16.abs (Q16_16.sub omega_stim omega_nat)
  mismatch.val.toNat ≤ coupling_strength.val.toNat

/-! ## 3. Biological Conservation -/

/-- General Biological Continuity Equation.
    du/dt + div(Vu) = F(t, x, u)
    Formalizes the conservation of population mass or chemical concentration. -/
def continuityUpdate (u flux_divergence reaction_rate dt : Q16_16) : Q16_16 :=
  let du := Q16_16.add (Q16_16.neg flux_divergence) reaction_rate
  Q16_16.add u (Q16_16.mul du dt)

end Semantics.Biology.Rhythms
