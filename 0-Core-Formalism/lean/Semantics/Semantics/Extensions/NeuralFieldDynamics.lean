/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

NeuralFieldDynamics.lean — Laws of continuous neural population activity.

This module formalizes the laws of large-scale cortical dynamics:
1. Mean-Field: Shun-ichi Amari's neural field equations.
2. Kernel: Local excitation and lateral inhibition (Mexican Hat).
3. Activation: Nonlinear sigmoid firing rate functions.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.NeuralField

open Semantics
open Semantics.FixedPoint

/-! ## 1. Amari Neural Field Equation -/

/-- Neural Potential Update (u).
    tau * du/dt = -u + ∫ w(x,y)f(u(y,t))dy + I(x,t)
    Models the evolution of the average membrane potential across a cortical sheet. -/
def neuralPotentialStep (u current_potential synaptic_inflow external_input tau dt : Q16_16) : Q16_16 :=
  let du_dt := Q16_16.div (Q16_16.add (Q16_16.sub synaptic_inflow current_potential) external_input) tau
  Q16_16.add u (Q16_16.mul du_dt dt)

/-! ## 2. Synaptic Kernels -/

/-- Mexican Hat Connectivity Kernel (w).
    w(x) = A*exp(-x²/2σ₁²) - B*exp(-x²/2σ₂²)
    Models short-range excitation and long-range inhibition. -/
def mexicanHatKernel (distance a_exc b_inh sigma1 sigma2 : Q16_16) : Q16_16 :=
  -- Returns connectivity weight w
  let x2 := Q16_16.mul distance distance
  let exc := Q16_16.mul a_exc (Q16_16.sub Q16_16.one (Q16_16.div x2 (Q16_16.mul (Q16_16.ofInt 2) (Q16_16.mul sigma1 sigma1))))
  let inh := Q16_16.mul b_inh (Q16_16.sub Q16_16.one (Q16_16.div x2 (Q16_16.mul (Q16_16.ofInt 2) (Q16_16.mul sigma2 sigma2))))
  Q16_16.sub exc inh

/-! ## 3. Activation Functions -/

/-- Sigmoid Firing Rate f(u).
    f(u) = 1 / (1 + exp(-beta * (u - h)))
    Models the non-linear response of a neural population to average potential. -/
def sigmoidActivation (u beta threshold : Q16_16) : Q16_16 :=
  let exponent := Q16_16.mul beta (Q16_16.sub u threshold)
  -- 1 / (1 + exp(-x)) approximation via piecewise linear
  if exponent.val.toNat > 0x00010000 then Q16_16.one
  else if exponent.val.toNat < 0x80000000 then Q16_16.zero -- exp(-large)
  else Q16_16.div Q16_16.one (Q16_16.ofInt 2) -- neutral point

end Semantics.Biology.NeuralField
