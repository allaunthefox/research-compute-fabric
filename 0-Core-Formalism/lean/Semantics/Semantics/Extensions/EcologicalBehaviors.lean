/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

EcologicalBehaviors.lean — Laws of competition, resilience, and behavioral evolution.

This module formalizes macroscopic biological laws:
1. Competition: Gause's Principle of Exclusion.
2. Resilience: Allee thresholds and island dynamics.
3. Behavior: Optimal foraging and kin selection.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Ecology

open Semantics
open Semantics.Q16_16

/-! ## 1. Resource Competition -/

/-- Gause's Competitive Exclusion Step.
    Describes how two species compete for the same niche.
    dN1/dt = r1*N1 * (K1 - N1 - α12*N2) / K1 -/
def competitiveExclusionUpdate (n1 n2 r1 k1 alpha12 dt : Q16_16) : Q16_16 :=
  let competition := Q16_16.sub k1 (Q16_16.add n1 (Q16_16.mul alpha12 n2))
  let growth := Q16_16.div (Q16_16.mul (Q16_16.mul r1 n1) competition) k1
  Q16_16.add n1 (Q16_16.mul growth dt)

/-! ## 2. Population Resilience -/

/-- The Allee Effect.
    Population growth is negative below a critical threshold A.
    dN/dt = r*N * (N/A - 1) * (1 - N/K) -/
def alleeEffectRate (n r a k : Q16_16) : Q16_16 :=
  let term1 := Q16_16.sub (Q16_16.div n a) Q16_16.one
  let term2 := Q16_16.sub Q16_16.one (Q16_16.div n k)
  Q16_16.mul (Q16_16.mul r n) (Q16_16.mul term1 term2)

/-- Island Biogeography Equilibrium.
    dS/dt = I - E, where I decreases with S and E increases with S. -/
def islandSpeciesFlux (s i_max e_max p : Q16_16) : Q16_16 :=
  let immigration := Q16_16.mul i_max (Q16_16.sub Q16_16.one (Q16_16.div s p))
  let extinction := Q16_16.div (Q16_16.mul e_max s) p
  Q16_16.sub immigration extinction

/-! ## 3. Behavioral Evolution -/

/-- Marginal Value Theorem (MVT).
    Optimal stay time occurs when instantaneous gain rate equals average gain rate. -/
def optimalStayTimeCondition (gain_rate average_gain : Q16_16) : Bool :=
  -- Returns true if stay time is optimal (within epsilon)
  let diff := Q16_16.sub gain_rate average_gain
  diff.val.toNat < 0x00000400 -- 0.01 tolerance

/-- Hamilton's Rule (Kin Selection).
    rB > C
    Altruism spreads if relatedness * benefit > cost. -/
def hamiltionRuleSatisfied (r b c : Q16_16) : Bool :=
  Q16_16.gt (Q16_16.mul r b) c

end Semantics.Biology.Ecology
