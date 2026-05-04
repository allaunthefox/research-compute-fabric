/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

BiologicalSensingLaws.lean — Physical limits of biological chemoreception and signaling.

This module formalizes the fundamental physical boundaries of biological sensing:
1. Precision: Berg-Purcell limit for concentration sensing.
2. Signal-to-Noise: Bialek's SNR for molecular detectors.
3. Information: Optimization of sensory systems toward physical limits.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Sensing

open Semantics
open Semantics.FixedPoint

/-! ## 1. Physical Limits of Sensing (Berg-Purcell) -/

/-- Berg-Purcell Fractional Error (δc/c).
    (δc/c)² ≈ 1 / (D * a * c * τ)
    D: Diffusion constant, a: Cell radius, c: Concentration, τ: Averaging time. -/
def bergPurcellErrorSq (diffusion radius conc time : Q16_16) : Q16_16 :=
  let denominator := Q16_16.mul (Q16_16.mul diffusion radius) (Q16_16.mul conc time)
  if denominator == Q16_16.zero then Q16_16.mk 0xFFFFFFFF
  else Q16_16.div Q16_16.one denominator

/-! ## 2. Signal-to-Noise Ratio (Bialek) -/

/-- Bialek's Signaling SNR.
    SNR ≈ (Δc)² * D * a * c * τ
    Models the detectability of concentration changes relative to thermal noise. -/
def signalingSNR (delta_c diffusion radius conc time : Q16_16) : Q16_16 :=
  let signal_sq := Q16_16.mul delta_c delta_c
  Q16_16.mul signal_sq (Q16_16.mul (Q16_16.mul diffusion radius) (Q16_16.mul conc time))

/-! ## 3. Positional Information Noise -/

/-- Positional Error (Δx) in Morphogen Gradients.
    Δx ≈ (δc/c) / |(1/c) * (dc/dx)|
    Measures the precision of embryonic patterning. -/
def positionalPrecision (fractional_error relative_gradient : Q16_16) : Q16_16 :=
  if relative_gradient == Q16_16.zero then Q16_16.zero
  else Q16_16.div fractional_error relative_gradient

end Semantics.Biology.Sensing
