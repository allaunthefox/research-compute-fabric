/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

LocomotionMuscleDynamics.lean — Laws of animal movement and muscle contraction.

This module formalizes the physical laws of biological locomotion:
1. Fluid: Strouhal Number for swimming and flying efficiency.
2. Terrestrial: Froude Number for gait transition and walking limits.
3. Muscle: Huxley's Cross-Bridge Model of contraction kinetics.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Locomotion

open Semantics
open Semantics.Q16_16

/-! ## 1. Fluid Locomotion (Strouhal) -/

/-- Strouhal Number (St).
    St = (f * A) / U
    f: Stroke frequency, A: Oscillation amplitude, U: Forward speed.
    Optimal efficiency for swimming/flying is 0.2 < St < 0.4. -/
def strouhalNumber (frequency amplitude speed : Q16_16) : Q16_16 :=
  if speed == Q16_16.zero then Q16_16.zero
  else Q16_16.div (Q16_16.mul frequency amplitude) speed

/-- Propulsive Efficiency Proxy.
    Returns 1.0 if St is in the optimal range [0.2, 0.4]. -/
def isPropulsionEfficient (st : Q16_16) : Bool :=
  let st_val := st.val.toNat
  st_val > 0x00003333 && st_val < 0x00006666 -- approx 0.2 and 0.4

/-! ## 2. Terrestrial Locomotion (Froude) -/

/-- Froude Number (Fr).
    Fr = v^2 / (g * L)
    v: Speed, g: Gravity, L: Leg length.
    Gait transition (walk to run) occurs at Fr ≈ 0.5. -/
def froudeNumber (speed gravity leg_length : Q16_16) : Q16_16 :=
  let v2 := Q16_16.mul speed speed
  let den := Q16_16.mul gravity leg_length
  if den == Q16_16.zero then Q16_16.zero
  else Q16_16.div v2 den

/-! ## 3. Muscle Mechanics (Huxley) -/

/-- Huxley Cross-Bridge Attachment Rate (Simplified).
    dn/dt = f(x)*(1-n) - g(x)*n
    n: fraction of attached bridges, f/g: attach/detach rates. -/
def crossBridgeUpdate (n f_rate g_rate dt : Q16_16) : Q16_16 :=
  let dn := Q16_16.sub (Q16_16.mul f_rate (Q16_16.sub Q16_16.one n)) (Q16_16.mul g_rate n)
  Q16_16.add n (Q16_16.mul dn dt)

end Semantics.Biology.Locomotion
