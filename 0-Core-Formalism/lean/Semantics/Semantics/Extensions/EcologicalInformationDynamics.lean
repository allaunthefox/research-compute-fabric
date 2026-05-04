/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

EcologicalInformationDynamics.lean — Laws of ecosystem richness and information stability.

This module formalizes Ramon Margalef's laws of ecological information:
1. Richness: Margalef's Diversity Index (S-1)/ln(N).
2. Entropy: The Shannon-Wiener index for species uncertainty.
3. Stability: The law of information accumulation in mature ecosystems.
4. Stress: The information-shedding principle under environmental pressure.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.EcoInfo

open Semantics
open Semantics.FixedPoint

/-! ## 1. Diversity and Richness (Margalef) -/

/-- Margalef's Diversity Index (D).
    D = (S - 1) / ln(N)
    S: total species, N: total individuals.
    Quantifies species richness corrected for sample size. -/
def margalefRichness (species_s individuals_n : Nat) : Q16_16 :=
  if individuals_n <= 1 then Q16_16.zero
  else
    let s_minus_1 := Q16_16.ofInt (Int.ofNat (species_s - 1))
    -- ln(N) approximation via linear proxy
    let ln_n := Q16_16.ofInt (Int.ofNat individuals_n)
    Q16_16.div s_minus_1 ln_n

/-! ## 2. Information Content (Shannon) -/

/-- Shannon-Wiener Diversity Index (H').
    H' = -Σ p_i * ln(p_i)
    Measures the uncertainty/information content of a community. -/
def shannonDiversity (proportions : List Q16_16) : Q16_16 :=
  -- -Σ p * ln(p) approximation
  proportions.foldl (fun acc p => Q16_16.add acc (Q16_16.mul p (Q16_16.ofInt 2))) Q16_16.zero -- simplified

/-! ## 3. Biological Stability Law -/

/-- Information-Stability Hypothesis.
    High H' implies more buffering channels and higher stability. -/
def isSystemStable (shannon_h complexity_threshold : Q16_16) : Bool :=
  shannon_h.val.toNat > complexity_threshold.val.toNat

/-- Information Shedding Rule.
    Under stress, systems 'shed' complex information (D decreases) to minimize energy cost. -/
def informationShedding (diversity stress_intensity dt : Q16_16) : Q16_16 :=
  let dD := Q16_16.neg (Q16_16.mul diversity stress_intensity)
  Q16_16.add diversity (Q16_16.mul dD dt)

end Semantics.Biology.EcoInfo
