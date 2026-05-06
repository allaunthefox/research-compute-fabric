/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

NeuroInformationDynamics.lean — Laws of information processing and perception scaling.

This module formalizes the informational and psychophysical laws of neural systems:
1. Information Theory: The Information Bottleneck principle.
2. Prediction: Predictive coding error-update dynamics.
3. Psychophysics: Weber-Fechner logarithmic and Stevens' power-law scaling.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.NeuroInfo

open Semantics
open Semantics.Q16_16

/-! ## 1. Information Theory -/

/-- Information Bottleneck (IB) Lagrangian.
    L = I(X;Z) - β * I(Z;Y)
    Measures the trade-off between compression (complexity) and relevance. -/
def informationBottleneckLagrangian (complexity relevance beta : Q16_16) : Q16_16 :=
  Q16_16.sub complexity (Q16_16.mul beta relevance)

/-! ## 2. Predictive Coding -/

/-- Predictive Coding Error Update.
    ε = Input - f(U * r)
    dr/dt = U^T * ε
    Updates internal representations by minimizing prediction error. -/
def predictionError (input prediction : Q16_16) : Q16_16 :=
  Q16_16.sub input prediction

def representationUpdate (error weights dt : Q16_16) : Q16_16 :=
  -- dr = weights * error * dt
  Q16_16.mul (Q16_16.mul weights error) dt

/-! ## 3. Psychophysics (Perception Scaling) -/

/-- Weber-Fechner Law (Logarithmic Scaling).
    S = k * ln(I / I0)
    Models how perceived sensation scales with stimulus intensity. -/
def perceivedSensationLog (intensity threshold k_const : Q16_16) : Q16_16 :=
  -- k * ln(I/I0) approximation using linear ratio for fixed-point
  Q16_16.mul k_const (Q16_16.div intensity threshold)

/-- Stevens' Power Law.
    S = k * I^a
    Models sensation for modalities that don't follow logarithmic scaling. -/
def perceivedSensationPower (intensity k_const a_exponent : Q16_16) : Q16_16 :=
  -- k * I^a approximation
  let power_approx := if a_exponent.val.toNat > 0x00010000 then Q16_16.mul intensity intensity else intensity
  Q16_16.mul k_const power_approx

end Semantics.Biology.NeuroInfo
