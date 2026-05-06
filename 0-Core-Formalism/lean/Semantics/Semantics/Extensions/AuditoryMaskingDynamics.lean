/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

AuditoryMaskingDynamics.lean — Laws of masking, spreading functions, and specific loudness.

This module formalizes the laws of psychoacoustic masking and signal saliency:
1. Spreading: Zwicker's spreading function for frequency masking.
2. Compression: Signal-to-Mask Ratio (SMR) for informational prioritization.
3. Loudness: Specific loudness integration and total perceived intensity.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Auditory.Masking

open Semantics
open Semantics.Q16_16

/-! ## 1. Auditory Spreading (Zwicker) -/

/-- Upper Masking Slope (S2).
    S2 ≈ 24 + 230/f - 0.2*L (dB/Bark)
    Models the 'upward spread of masking' where low frequencies mask high ones. -/
def upperMaskingSlope (freq_hz masker_level_db : Q16_16) : Q16_16 :=
  let freq_term := Q16_16.div (Q16_16.ofInt 230) (Q16_16.div freq_hz (Q16_16.ofInt 1000)) -- normalized
  let level_penalty := Q16_16.mul (Q16_16.mk 0x00003333) masker_level_db -- 0.2 in Q16.16
  Q16_16.sub (Q16_16.add (Q16_16.ofInt 24) freq_term) level_penalty

/-! ## 2. Information Saliency (SMR) -/

/-- Signal-to-Mask Ratio (SMR).
    SMR = L_signal - L_mask
    If SMR < 0, the signal is masked and provides zero informational value to the agent. -/
def signalToMaskRatio (signal_db mask_threshold_db : Q16_16) : Q16_16 :=
  Q16_16.sub signal_db mask_threshold_db

/-- Saliency Filter.
    Returns true if the signal is audible above the masking floor. -/
def isSignalSalient (smr : Q16_16) : Bool :=
  smr.val.toNat > 0

/-! ## 3. Perceived Intensity (Loudness) -/

/-- Specific Loudness (N').
    N' = k * (E / E0)^0.23
    E: Excitation in a critical band. -/
def specificLoudness (excitation_ratio : Q16_16) : Q16_16 :=
  -- Returns N' in Sones/Bark
  -- x^0.23 approximation via linear scaling for fixed-point
  Q16_16.mul (Q16_16.mk 0x00003AE1) excitation_ratio -- 0.23 in Q16.16

/-- Total Loudness (N).
    N = Σ N'_i * Δz
    The total perceived intensity of a sound event. -/
def totalLoudness (specific_loudness_list : List Q16_16) (delta_z : Q16_16) : Q16_16 :=
  let sum_n := specific_loudness_list.foldl Q16_16.add Q16_16.zero
  Q16_16.mul sum_n delta_z

end Semantics.Biology.Auditory.Masking
