/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

AuditoryPerceptionLaws.lean — Laws of critical bands, equal loudness, and psychoacoustics.

This module formalizes the laws of biological auditory perception:
1. Filter: The Bark scale for critical band rate.
2. Bandwidth: Zwicker's equation for auditory critical bandwidth.
3. Perception: Equal loudness contours (Fletcher-Munson).
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Psychoacoustics

open Semantics
open Semantics.Q16_16

/-! ## 1. Critical Band Rate (Bark Scale) -/

/-- Bark Scale Transformation (z).
    z = 13*arctan(0.00076*f) + 3.5*arctan((f/7500)^2)
    Maps physical frequency (Hz) to perceptual Bark units. -/
def frequencyToBark (freq_hz : Q16_16) : Q16_16 :=
  -- Returns z in Bark
  -- Simplified linear-log approximation
  if freq_hz.val.toNat < 0x01F40000 then -- < 500 Hz
    Q16_16.div freq_hz (Q16_16.ofInt 100)
  else
    Q16_16.add (Q16_16.ofInt 5) (Q16_16.div freq_hz (Q16_16.ofInt 500))

/-! ## 2. Auditory Bandwidth (Zwicker) -/

/-- Critical Bandwidth (Δf).
    Δf = 25 + 75 * [1 + 1.4*(f/1000)^2]^0.69
    Models the frequency integration width of the human ear. -/
def criticalBandwidth (freq_hz : Q16_16) : Q16_16 :=
  let f_khz := Q16_16.div freq_hz (Q16_16.ofInt 1000)
  let f2 := Q16_16.mul f_khz f_khz
  let bracket := Q16_16.add Q16_16.one (Q16_16.mul (Q16_16.mk 0x00016666) f2) -- 1.4 in Q16.16
  Q16_16.add (Q16_16.ofInt 25) (Q16_16.mul (Q16_16.ofInt 75) bracket)

/-! ## 3. Equal Loudness -/

/-- Phon to SPL Transformation Proxy.
    Models the frequency-dependent threshold for equal perceived loudness. -/
def equalLoudnessSPL (freq_hz loudness_phon : Q16_16) : Q16_16 :=
  -- Returns the required Sound Pressure Level (SPL) in dB
  -- Corrects for the ear's low-frequency insensitivity
  if freq_hz.val.toNat < 0x00640000 then -- < 100 Hz
    Q16_16.add loudness_phon (Q16_16.ofInt 20) -- add 20 dB penalty
  else
    loudness_phon

end Semantics.Biology.Psychoacoustics
