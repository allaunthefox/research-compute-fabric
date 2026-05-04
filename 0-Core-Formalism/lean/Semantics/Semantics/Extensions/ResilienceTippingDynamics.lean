/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

ResilienceTippingDynamics.lean — Laws of critical slowing down and ecological tipping points.

This module formalizes the laws of biological resilience and phase transitions:
1. Early Warning: Critical Slowing Down (CSD) and increased autocorrelation.
2. Stability: Eigenvalue-based recovery rate from perturbations.
3. Resilience: Basin of attraction geometry (Latitude and Resistance).
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Resilience

open Semantics
open Semantics.FixedPoint

/-! ## 1. Critical Slowing Down (CSD) -/

/-- Autocorrelation Early Warning (AR1).
    alpha = exp(lambda * dt)
    As tipping point approaches (lambda -> 0), alpha -> 1.0. -/
def autocorrelationProxy (eigenvalue time_step : Q16_16) : Q16_16 :=
  -- Returns alpha (autocorrelation coefficient)
  -- exp(lambda * dt) approximation via 1 + lambda * dt
  Q16_16.add Q16_16.one (Q16_16.mul eigenvalue time_step)

/-- CSD Variance Increase.
    Var = sigma^2 / (1 - alpha^2)
    Models the explosion of variance as a system becomes unstable. -/
def varianceIncrease (noise_sigma alpha : Q16_16) : Q16_16 :=
  let den := Q16_16.sub Q16_16.one (Q16_16.mul alpha alpha)
  if den == Q16_16.zero then Q16_16.mk 0xFFFFFFFF
  else Q16_16.div (Q16_16.mul noise_sigma noise_sigma) den

/-! ## 2. Linear Stability -/

/-- Recovery Rate (λ).
    The speed at which a system returns to equilibrium. -/
def recoveryRate (perturbation_decay_time : Q16_16) : Q16_16 :=
  -- lambda = -1 / tau
  if perturbation_decay_time == Q16_16.zero then Q16_16.zero
  else Q16_16.neg (Q16_16.div Q16_16.one perturbation_decay_time)

/-! ## 3. Basin of Attraction Geometry -/

/-- Resilience Resistance (Basin Depth).
    Measures the steepness of the potential well. -/
def basinResistance (slope : Q16_16) : Q16_16 :=
  slope

/-- Resilience Latitude (Basin Width).
    The maximum perturbation distance before a regime shift occurs. -/
def basinLatitude (threshold_dist : Q16_16) : Q16_16 :=
  threshold_dist

end Semantics.Biology.Resilience
