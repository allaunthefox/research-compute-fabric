/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

LifeHistoryTradeoffLaws.lean — Laws of energy allocation, maturation, and semelparity.

This module formalizes the laws of biological investment and life history strategies:
1. Semelparity: Cole's Paradox resolution and the annual-perennial fitness boundary.
2. Maturation: Stearns' invariant for relative size at maturity.
3. Allocation: The Principle of Allocation for energy budgeting.
4. Fitness: The Euler-Lotka discrete characteristic sum.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.LifeHistory

open Semantics
open Semantics.FixedPoint

/-! ## 1. Cole's Paradox Resolution -/

/-- Required Annual Offspring (ma).
    ma = mp + S / s
    ma, mp: offspring of annual vs perennial, S: adult survival, s: juvenile survival.
    The threshold where an annual strategy becomes fitter than a perennial one. -/
def annualOffspringThreshold (mp_offspring adult_survival juv_survival : Q16_16) : Q16_16 :=
  if juv_survival == Q16_16.zero then Q16_16.mk 0xFFFFFFFF
  else Q16_16.add mp_offspring (Q16_16.div adult_survival juv_survival)

/-! ## 2. Maturity Invariants (Stearns) -/

/-- Relative Size at Maturity Invariant.
    L_maturity / L_infinity ≈ Constant (e.g., 0.65 for many fish). -/
def relativeMaturitySize (l_alpha l_inf : Q16_16) : Q16_16 :=
  if l_inf == Q16_16.zero then Q16_16.zero
  else Q16_16.div l_alpha l_inf

/-! ## 3. Principle of Allocation -/

/-- Energy Allocation Sum (T).
    T = R + S + G
    T: Total energy, R: Reproduction, S: Survival, G: Growth.
    Formalizes the fundamental trade-off: energy used for one cannot be used for others. -/
def totalEnergyBudget (reproduction survival growth : Q16_16) : Q16_16 :=
  Q16_16.add reproduction (Q16_16.add survival growth)

/-! ## 4. Fundamental Fitness Law (Euler-Lotka) -/

/-- Discrete Euler-Lotka Sum (Proxy).
    Σ exp(-rx) * l(x) * m(x) = 1
    Measures the net reproductive rate of a population. -/
def netReproductiveRate (intrinsic_rate time_steps : Nat) (survival_probs fecundities : List Q16_16) : Q16_16 :=
  -- Returns the sum proxy
  let terms := List.zipWith (fun l m => Q16_16.mul l m) survival_probs fecundities
  terms.foldl Q16_16.add Q16_16.zero

end Semantics.Biology.LifeHistory
