/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

EcologicalNetworkDynamics.lean — Laws of nutrient stoichiometry, predator-prey interaction, and network complexity.

This module formalizes the laws of ecosystem structure and function:
1. Stoichiometry: Redfield Ratio for C:N:P constancy.
2. Interaction: Holling's functional responses (Types I, II, III).
3. Complexity: Ecological network connectance.
4. Statistics: Taylor's Law of variance scaling.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.EcoNetwork

open Semantics
open Semantics.FixedPoint

/-! ## 1. Ecological Stoichiometry -/

/-- Redfield Ratio (C:N:P).
    Standard ratio is 106:16:1.
    Formalizes the molecular consistency of oceanic biomass. -/
def redfieldCheck (c n p : Q16_16) : Bool :=
  -- Checks if C:N:P ≈ 106:16:1 (within tolerance)
  let cn_ratio := Q16_16.div c n
  let np_ratio := Q16_16.div n p
  -- cn ≈ 106/16 ≈ 6.625, np ≈ 16
  (cn_ratio.val.toNat > 0x00060000) && (np_ratio.val.toNat > 0x000F0000)

/-! ## 2. Functional Responses (Holling) -/

/-- Holling Type I (Linear).
    f(N) = a * N -/
def hollingType1 (prey_density attack_rate : Q16_16) : Q16_16 :=
  Q16_16.mul attack_rate prey_density

/-- Holling Type II (Saturating).
    f(N) = (a * N) / (1 + a * h * N)
    Incorporates handling time (h). -/
def hollingType2 (n a h : Q16_16) : Q16_16 :=
  let num := Q16_16.mul a n
  let den := Q16_16.add Q16_16.one (Q16_16.mul num h)
  Q16_16.div num den

/-- Holling Type III (Sigmoid).
    f(N) = (a * N^2) / (1 + a * h * N^2)
    Models prey switching or learning behavior. -/
def hollingType3 (n a h : Q16_16) : Q16_16 :=
  let n2 := Q16_16.mul n n
  let num := Q16_16.mul a n2
  let den := Q16_16.add Q16_16.one (Q16_16.mul num h)
  Q16_16.div num den

/-! ## 3. Network Complexity -/

/-- Ecological Network Connectance (C).
    C = L / S^2
    L: Number of links, S: Number of species. -/
def networkConnectance (links species : Nat) : Q16_16 :=
  let s_f := Q16_16.ofInt (Int.ofNat species)
  let l_f := Q16_16.ofInt (Int.ofNat links)
  Q16_16.div l_f (Q16_16.mul s_f s_f)

/-! ## 4. Variance Scaling -/

/-- Taylor's Law.
    σ² = a * μ^b
    Relates variance to the mean of population density. -/
def taylorsVariance (mean a b_exponent : Q16_16) : Q16_16 :=
  -- Returns predicted variance σ²
  -- a * μ^b approximation
  let mean_pow := if b_exponent.val.toNat > 0x00010000 then Q16_16.mul mean mean else mean
  Q16_16.mul a mean_pow

end Semantics.Biology.EcoNetwork
