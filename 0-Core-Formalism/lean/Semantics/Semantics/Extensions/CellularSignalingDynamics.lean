/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

CellularSignalingDynamics.lean — Laws of ultrasensitivity, cell cycles, and chemotaxis.

This module formalizes the laws of sub-cellular decision making and motion:
1. Ultrasensitivity: Goldbeter-Koshland zeroth-order switch.
2. Cell Cycle: Tyson's mitotic oscillator (limit cycle).
3. Rhythms: Goldbeter's PER-CRY molecular feedback.
4. Chemotaxis: Keller-Segel drift-diffusion dynamics.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Signaling

open Semantics
open Semantics.FixedPoint

/-! ## 1. Zeroth-Order Ultrasensitivity -/

/-- Goldbeter-Koshland Function (x).
    Describes the sharp 'on-off' switch in covalent modification cycles. -/
def goldbeterKoshlandSwitch (v1 v2 j1 j2 : Q16_16) : Q16_16 :=
  let b := Q16_16.add (Q16_16.sub v2 v1) (Q16_16.add (Q16_16.mul v2 j1) (Q16_16.mul v1 j2))
  let discriminant := Q16_16.sub (Q16_16.mul b b) (Q16_16.mul (Q16_16.ofInt 4) (Q16_16.mul (Q16_16.sub v2 v1) (Q16_16.mul v1 j2)))
  -- Placeholder for sqrt(discriminant)
  let sqrt_disc := b
  Q16_16.div (Q16_16.mul (Q16_16.ofInt 2) (Q16_16.mul v1 j2)) (Q16_16.add b sqrt_disc)

/-! ## 2. Mitotic Oscillator (Cell Cycle) -/

/-- Tyson's Mitotic Oscillator Step (u, v).
    du/dt = k4(v - u)(alpha + u^2) - k6*u
    dv/dt = kappa - k6*u -/
structure MitoticState where
  u_active_mpf : Q16_16
  v_total_cyclin : Q16_16
  deriving Repr, DecidableEq

def tysonStep (s : MitoticState) (k4 k6 kappa alpha dt : Q16_16) : MitoticState :=
  let u2 := Q16_16.mul s.u_active_mpf s.u_active_mpf
  let du := Q16_16.sub (Q16_16.mul k4 (Q16_16.mul (Q16_16.sub s.v_total_cyclin s.u_active_mpf) (Q16_16.add alpha u2))) (Q16_16.mul k6 s.u_active_mpf)
  let dv := Q16_16.sub kappa (Q16_16.mul k6 s.u_active_mpf)
  { u_active_mpf := Q16_16.add s.u_active_mpf (Q16_16.mul du dt)
  , v_total_cyclin := Q16_16.add s.v_total_cyclin (Q16_16.mul dv dt) }

/-! ## 3. Molecular Rhythms (Goldbeter) -/

/-- PER-CRY Feedback Logic.
    Models the repressive delay in the molecular circadian clock. -/
def molecularRepression (activator repressor hill_coeff k_threshold : Q16_16) : Q16_16 :=
  -- Returns the repressed synthesis rate
  let r_n := if hill_coeff.val.toNat > 0x00010000 then Q16_16.mul repressor repressor else repressor
  let k_n := if hill_coeff.val.toNat > 0x00010000 then Q16_16.mul k_threshold k_threshold else k_threshold
  Q16_16.div k_n (Q16_16.add k_n r_n)

/-! ## 4. Chemotaxis (Keller-Segel) -/

/-- Keller-Segel Drift Term.
    J_chem = chi * u * grad(c)
    Calculates the advective flux of cells toward a chemical gradient. -/
def chemotacticFlux (density sensitivity gradient : Q16_16) : Q16_16 :=
  Q16_16.mul sensitivity (Q16_16.mul density gradient)

end Semantics.Biology.Signaling
