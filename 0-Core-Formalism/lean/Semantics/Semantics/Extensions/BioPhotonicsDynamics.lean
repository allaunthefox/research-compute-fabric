/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

BioPhotonicsDynamics.lean — Laws of radiative transfer and bioluminescence kinetics.

This module formalizes the laws of light transport and emission in biological systems:
1. Transport: The Diffusion Approximation of the Radiative Transfer Equation (RTE).
2. Emission: Firefly Luciferase kinetic rate laws.
3. Attenuation: The Beer-Lambert law for light absorption in tissue.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Photonics

open Semantics
open Semantics.Q16_16

/-! ## 1. Tissue Light Transport -/

/-- Diffusion Approximation for Fluence Rate (Φ).
    (1/c) * dΦ/dt = div(D * grad(Φ)) - mu_a * Φ + S
    D: Diffusion coefficient, mu_a: absorption coefficient, S: source.
    Models photon transport in scattering-dominated media. -/
def fluenceRateUpdate (phi speed_c diffusion laplacian mu_a source dt : Q16_16) : Q16_16 :=
  let transport := Q16_16.mul diffusion laplacian
  let loss := Q16_16.mul mu_a phi
  let dPhi := Q16_16.mul speed_c (Q16_16.add (Q16_16.sub transport loss) source)
  Q16_16.add phi (Q16_16.mul dPhi dt)

/-! ## 2. Bioluminescence Emission -/

/-- Luciferase Emission Rate (v).
    v = V_max * [S] / (Km + [S])
    Models the photon emission rate as a function of luciferin concentration. -/
def photonEmissionRate (v_max substrate k_m : Q16_16) : Q16_16 :=
  let den := Q16_16.add k_m substrate
  if den == Q16_16.zero then Q16_16.zero
  else Q16_16.div (Q16_16.mul v_max substrate) den

/-! ## 3. Absorption (Beer-Lambert) -/

/-- Beer-Lambert Intensity Law.
    I = I0 * exp(-mu_a * z)
    Models the exponential decay of light in a non-scattering medium. -/
def lightIntensityAtDepth (i0 mu_a depth : Q16_16) : Q16_16 :=
  -- I0 * exp(-mu_a * z) approximation via 1 - mu_a * z
  let decay := Q16_16.sub Q16_16.one (Q16_16.mul mu_a depth)
  Q16_16.mul i0 decay

end Semantics.Biology.Photonics
