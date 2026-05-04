/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

MolecularCooperation.lean — Laws of molecular binding, allostery, and cooperativity.

This module formalizes the thermodynamic and empirical laws of protein function:
1. Empirical: Hill's equation for cooperative binding.
2. Stepwise: Adair's sequential association model.
3. Allosteric: MWC (Concerted) and KNF (Induced Fit) models.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Molecular

open Semantics
open Semantics.FixedPoint

/-! ## 1. Empirical Cooperativity -/

/-- Hill Equation (Fractional Saturation Y).
    Y = [L]^n / (Kd + [L]^n)
    Models the degree of cooperativity (sigmoidal vs hyperbolic). -/
def hillSaturation (ligand_conc kd n_coeff : Q16_16) : Q16_16 :=
  -- [L]^n approximation
  let ln := if n_coeff.val.toNat > 0x00010000 then Q16_16.mul ligand_conc ligand_conc else ligand_conc
  Q16_16.div ln (Q16_16.add kd ln)

/-! ## 2. Stepwise Association -/

/-- Adair Equation (Stepwise Binding for Tetramer).
    Y = (K1*L + 2*K1*K2*L^2 + ...) / (4 * (1 + K1*L + ...))
    The most general thermodynamic model for multi-site binding. -/
def adairSaturation (l k1 k2 k3 k4 : Q16_16) : Q16_16 :=
  let term1 := Q16_16.mul k1 l
  let term2 := Q16_16.mul (Q16_16.mul k1 k2) (Q16_16.mul l l)
  let numerator := Q16_16.add term1 (Q16_16.mul (Q16_16.ofInt 2) term2)
  let denominator := Q16_16.mul (Q16_16.ofInt 4) (Q16_16.add Q16_16.one (Q16_16.add term1 term2))
  Q16_16.div numerator denominator -- Simplified to 2-step for fixed-point

/-! ## 3. Allosteric Transitions -/

/-- MWC (Monod-Wyman-Changeux) Model.
    Symmetry-preserving concerted transition between T and R states. -/
def mwcSaturation (alpha l_const c_ratio : Q16_16) : Q16_16 :=
  -- α = [L]/Kr, L = [T0]/[R0], c = Kr/Kt
  let termR := Q16_16.add Q16_16.one alpha
  let termT := Q16_16.add Q16_16.one (Q16_16.mul c_ratio alpha)
  let num := Q16_16.add alpha (Q16_16.mul (Q16_16.mul l_const c_ratio) alpha)
  let den := Q16_16.add termR (Q16_16.mul l_const termT)
  Q16_16.div num den -- Simplified N=1 case

/-- KNF (Koshland-Némethy-Filmer) Model.
    Sequential induced-fit conformational changes. -/
def knfSaturation (alpha k_int : Q16_16) : Q16_16 :=
  -- K_int is the interaction constant between subunits
  let term1 := alpha
  let term2 := Q16_16.mul k_int (Q16_16.mul alpha alpha)
  Q16_16.div (Q16_16.add term1 term2) (Q16_16.add Q16_16.one (Q16_16.add term1 term2))

end Semantics.Biology.Molecular
