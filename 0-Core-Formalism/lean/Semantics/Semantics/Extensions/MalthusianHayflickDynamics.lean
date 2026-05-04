/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

MalthusianHayflickDynamics.lean — Laws of exponential growth and cellular division limits.

This module formalizes the laws of population expansion and cellular aging:
1. Growth: The Malthusian model of unlimited exponential population growth.
2. Limits: The Hayflick Limit for cell division and telomere shortening.
3. Senescence: The critical telomere length threshold for replicative arrest.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.ExpansionLimit

open Semantics
open Semantics.FixedPoint

/-! ## 1. Malthusian Growth -/

/-- Malthusian Growth Step (P).
    P(t) = P0 * exp(r * t)
    Models the intrinsic capacity of a population to increase indefinitely. -/
def malthusianPopulation (p0 intrinsic_rate time : Q16_16) : Q16_16 :=
  -- exp(rt) approximation via 1 + rt
  let exponent := Q16_16.mul intrinsic_rate time
  Q16_16.mul p0 (Q16_16.add Q16_16.one exponent)

/-! ## 2. Hayflick Limit (Telomere Decay) -/

/-- Telomere Length After n Divisions (Ln).
    Ln = L0 - n * deltaL
    L0: initial length, n: division count, deltaL: loss per division. -/
def telomereLength (l0 delta_l : Q16_16) (n : Nat) : Q16_16 :=
  let n_f := Q16_16.ofInt (Int.ofNat n)
  Q16_16.sub l0 (Q16_16.mul n_f delta_l)

/-- Hayflick Senescence Predicate.
    Cells enter senescence when telomere length falls below a critical threshold. -/
def isSenescent (current_l l_critical : Q16_16) : Bool :=
  current_l.val.toNat ≤ l_critical.val.toNat

end Semantics.Biology.ExpansionLimit
