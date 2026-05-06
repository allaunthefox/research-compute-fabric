/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

CancerMetabolicDynamics.lean — Laws of mutation kinetics and metabolic elasticity.

This module formalizes the laws of oncogenesis and metabolic control:
1. Oncology: Knudson's two-hit and multi-hit mutation probability laws.
2. Control: MCA elasticity coefficients and the connectivity theorem.
3. Evolution: The Price equation for trait partitioning.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.CancerMetabolic

open Semantics
open Semantics.Q16_16

/-! ## 1. Mutation Kinetics (Knudson) -/

/-- Multi-Hit Mutation Probability (P).
    P(t) ≈ 1 - exp(-k * t^n)
    n: number of rate-limiting genetic hits. -/
def cancerOnsetProb (time rate_k hits_n : Q16_16) : Q16_16 :=
  -- k * t^n approximation
  let tn := if hits_n.val.toNat > 0x00010000 then Q16_16.mul time time else time
  let exponent := Q16_16.mul rate_k tn
  -- 1 - exp(-x) approximation via x
  exponent

/-! ## 2. Metabolic Elasticity (MCA) -/

/-- MCA Elasticity Coefficient (ε).
    ε^v_s = (d ln v) / (d ln s)
    Quantifies the local sensitivity of a single enzyme v to a metabolite s. -/
def elasticityCoefficient (delta_v v delta_s s : Q16_16) : Q16_16 :=
  let v_ratio := Q16_16.div delta_v v
  let s_ratio := Q16_16.div delta_s s
  if s_ratio == Q16_16.zero then Q16_16.zero
  else Q16_16.div v_ratio s_ratio

/-- MCA Connectivity Theorem Identity.
    Σ CJv_i * ε^vi_s = 0
    Links systemic flux control to local elasticities. -/
def checkConnectivityTheorem (control_elasticity_products : List Q16_16) : Bool :=
  let sum := control_elasticity_products.foldl Q16_16.add Q16_16.zero
  sum == Q16_16.zero

/-! ## 3. Trait Evolution (Price) -/

/-- Price Equation Selection Term.
    Selection = Cov(w, z) / w_avg
    Calculates the portion of trait change due to fitness-trait covariance. -/
def priceSelectionTerm (cov_wz w_avg : Q16_16) : Q16_16 :=
  if w_avg == Q16_16.zero then Q16_16.zero
  else Q16_16.div cov_wz w_avg

end Semantics.Biology.CancerMetabolic
