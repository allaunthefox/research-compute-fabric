/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

PhysiologicalInvariants.lean — Laws of cardiovascular flow, cardiac output, and scaling.

This module formalizes the biophysical laws of animal physiology:
1. Cardiovascular: Poiseuille's flow and Starling's mechanism.
2. Output: Fick Principle for oxygen transport.
3. Scaling: Body size, limb length, and lineage growth (Bergmann, Allen, Cope).
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Physiology

open Semantics
open Semantics.FixedPoint

/-! ## 1. Cardiovascular Dynamics -/

/-- Poiseuille's Law (Blood Flow Rate).
    Q = (ΔP * π * r^4) / (8 * η * L)
    Models the massive impact of vessel radius on flow. -/
def poiseuilleFlow (deltaP radius viscosity length : Q16_16) : Q16_16 :=
  let r2 := Q16_16.mul radius radius
  let r4 := Q16_16.mul r2 r2
  let numerator := Q16_16.mul deltaP (Q16_16.mul (Q16_16.mk 0x00032440) r4) -- π ≈ 3.1416
  let denominator := Q16_16.mul (Q16_16.ofInt 8) (Q16_16.mul viscosity length)
  Q16_16.div numerator denominator

/-- Starling's Law of the Heart.
    Stroke Volume (SV) is proportional to End-Diastolic Volume (EDV).
    SV = k * EDV -/
def strokeVolume (edv k_contractility : Q16_16) : Q16_16 :=
  Q16_16.mul edv k_contractility

/-! ## 2. Metabolic Output -/

/-- Fick Principle (Cardiac Output).
    CO = VO2 / (CaO2 - CvO2)
    Calculates total flow based on oxygen consumption and content difference. -/
def cardiacOutput (vo2 cao2 cvo2 : Q16_16) : Q16_16 :=
  let diff := Q16_16.sub cao2 cvo2
  if diff == Q16_16.zero then Q16_16.zero
  else Q16_16.div vo2 diff

/-! ## 3. Biophysical Scaling -/

/-- Surface Area to Volume Ratio (SA:V).
    Models Bergmann's and Allen's rules for heat conservation.
    ratio = SA / V ∝ 1 / L -/
def savRatio (length : Q16_16) : Q16_16 :=
  Q16_16.div Q16_16.one length

/-- Cope's Rule (Lineage Body Size Growth).
    Size_t = Size_0 * exp(k * t)
    Formalizes the macroevolutionary trend toward larger size. -/
def copeSizeGrowth (size0 k t : Q16_16) : Q16_16 :=
  -- exp(kt) approximation via 1 + kt
  let exponent := Q16_16.mul k t
  Q16_16.mul size0 (Q16_16.add Q16_16.one exponent)

end Semantics.Biology.Physiology
