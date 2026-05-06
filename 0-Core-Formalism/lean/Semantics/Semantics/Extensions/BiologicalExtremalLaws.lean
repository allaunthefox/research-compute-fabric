/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

BiologicalExtremalLaws.lean — Extremal principles of biological action, time, and power.

This module formalizes the variational and optimality laws of biological systems:
1. Least Time: Fermat's Principle for animal foraging and trail paths.
2. Max Flux: Maximum metabolic throughput in constrained networks.
3. Max Power: Lotka's principle of useful energy transformation.
4. Least Action: Euler-Lagrange trajectories for population dynamics.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Extremal

open Semantics
open Semantics.Q16_16

/-! ## 1. Principle of Least Time (Fermat) -/

/-- Biological Snell's Law (Animal Refraction).
    sin(theta1) / v1 = sin(theta2) / v2
    Models optimal foraging pathing across heterogeneous terrain. -/
def animalPathRefraction (v1 v2 sin_theta1 : Q16_16) : Q16_16 :=
  -- Returns sin(theta2)
  Q16_16.div (Q16_16.mul v2 sin_theta1) v1

/-! ## 2. Principle of Maximum Flux (Metabolism) -/

/-- Maximum Flux Objective (Z).
    Maximize Z = Σ c_i * v_i subject to S * v = 0
    Formalizes the cellular goal of maximizing growth or ATP production. -/
def metabolicFluxObjective (fluxes weights : List Q16_16) : Q16_16 :=
  List.zipWith Q16_16.mul fluxes weights |>.foldl Q16_16.add Q16_16.zero

/-! ## 3. Maximum Power Principle (Lotka-Odum) -/

/-- Useful Power Output (P).
    P = efficiency * flux
    Evolved systems maximize the rate of useful energy transformation. -/
def powerOutput (efficiency flux : Q16_16) : Q16_16 :=
  Q16_16.mul efficiency flux

/-! ## 4. Principle of Least Action (Dynamics) -/

/-- Biological Action Lagrangian (L).
    L = T - V
    T: Kinetic energy (growth rate), V: Potential energy (constraints). -/
def populationLagrangian (kinetic potential : Q16_16) : Q16_16 :=
  Q16_16.sub kinetic potential

/-- Action Functional Integral (S).
    S = ∫ L dt
    The true population trajectory minimizes this action. -/
def populationAction (lagrangians : List Q16_16) (dt : Q16_16) : Q16_16 :=
  let sum_l := lagrangians.foldl Q16_16.add Q16_16.zero
  Q16_16.mul sum_l dt

end Semantics.Biology.Extremal
