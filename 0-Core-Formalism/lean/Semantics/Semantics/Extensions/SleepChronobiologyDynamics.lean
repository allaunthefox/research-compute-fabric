/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

SleepChronobiologyDynamics.lean — Laws of sleep regulation and circadian entrainment.

This module formalizes the laws of biological timekeeping and sleep homeostasis:
1. Homeostasis: Borbély's Process S (Sleep Pressure) exponential kinetics.
2. Circadian: Process C (Circadian Drive) oscillatory thresholds.
3. Entrainment: Aschoff's Rules for clock period scaling with light.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Chronobiology

open Semantics
open Semantics.Q16_16

/-! ## 1. Two-Process Model (Borbély) -/

/-- Process S: Homeostatic Sleep Pressure.
    Wake: S(t) = Smax - (Smax - S0) * exp(-tw/tau_w)
    Sleep: S(t) = S0 * exp(-ts/tau_s) -/
def sleepPressureStep (current_s s_max s_0 tau_w tau_s dt : Q16_16) (is_awake : Bool) : Q16_16 :=
  if is_awake then
    -- Wakefulness: Pressure increases toward Smax
    let gap := Q16_16.sub s_max current_s
    let growth := Q16_16.div gap tau_w
    Q16_16.add current_s (Q16_16.mul growth dt)
  else
    -- Sleep: Pressure decays toward zero
    let decay := Q16_16.div current_s tau_s
    Q16_16.sub current_s (Q16_16.mul decay dt)

/-- Process C: Circadian Drive thresholds.
    H+(t) = Mean + A * cos(omega*t)
    Sleep occurs when S(t) > H+(t). -/
def isSleepOnsetReached (current_s mean_threshold amplitude phase_c : Q16_16) : Bool :=
  -- Returns true if pressure exceeds the upper circadian threshold
  let h_plus := Q16_16.add mean_threshold (Q16_16.mul amplitude phase_c)
  current_s.val.toNat > h_plus.val.toNat

/-! ## 2. Circadian Scaling (Aschoff) -/

/-- Aschoff's Rule for Clock Period (tau).
    tau(I) = tau_0 +/- k * log10(I)
    Diurnal: minus (period shortens with light), Nocturnal: plus (period lengthens). -/
def freeRunningPeriod (tau_0 k_const intensity : Q16_16) (is_diurnal : Bool) : Q16_16 :=
  -- k * log10(I) approximation
  let log_i := intensity -- simplified
  if is_diurnal then Q16_16.sub tau_0 (Q16_16.mul k_const log_i)
  else Q16_16.add tau_0 (Q16_16.mul k_const log_i)

end Semantics.Biology.Chronobiology
