/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

BiologicalRegulationDynamics.lean — Laws of metabolic control, robust adaptation, and regulatory selection.

This module formalizes the laws of biological feedback and regulation:
1. Metabolism: Metabolic Control Analysis (MCA) coefficients and summation theorems.
2. Robustness: Barkai-Leibler perfect adaptation and integral feedback.
3. Selection: Savageau's Demand Theory for gene regulatory logic.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Regulation

open Semantics
open Semantics.Q16_16

/-! ## 1. Metabolic Control Analysis (MCA) -/

/-- MCA Flux Control Coefficient (CJv).
    CJv = (d ln J) / (d ln v)
    Quantifies the system-level sensitivity of flux J to local enzyme activity v. -/
def fluxControlCoefficient (delta_j j delta_v v : Q16_16) : Q16_16 :=
  let j_ratio := Q16_16.div delta_j j
  let v_ratio := Q16_16.div delta_v v
  if v_ratio == Q16_16.zero then Q16_16.zero
  else Q16_16.div j_ratio v_ratio

/-- MCA Summation Theorem.
    Σ CJv_i = 1.0
    The total control of a metabolic flux is conserved across all components. -/
def isControlLawful (coefficients : List Q16_16) : Bool :=
  let sum := coefficients.foldl Q16_16.add Q16_16.zero
  sum == Q16_16.one

/-! ## 2. Robust Adaptation (Barkai-Leibler) -/

/-- Barkai-Leibler Integral Feedback.
    dm/dt = k_R*[R] - k_B*[B]*phi(A)
    Models perfect adaptation in signaling networks (e.g., chemotaxis). -/
def adaptationUpdate (m k_r r k_b b phi_a dt : Q16_16) : Q16_16 :=
  let dm := Q16_16.sub (Q16_16.mul k_r r) (Q16_16.mul (Q16_16.mul k_b b) phi_a)
  Q16_16.add m (Q16_16.mul dm dt)

/-- Perfect Adaptation Condition.
    At steady state, activity A is independent of stimulus L. -/
def isAdapted (dm : Q16_16) : Bool :=
  dm == Q16_16.zero

/-! ## 3. Regulatory Logic Selection (Savageau) -/

/-- Savageau's Demand Rule.
    High Demand (D -> 1) selects for Positive Regulation (Activators).
    Low Demand (D -> 0) selects for Negative Regulation (Repressors). -/
inductive RegulatoryMode | positive | negative

def optimalRegulatoryMode (demand : Q16_16) : RegulatoryMode :=
  if demand.val.toNat > 0x00008000 then RegulatoryMode.positive -- D > 0.5
  else RegulatoryMode.negative

end Semantics.Biology.Regulation
