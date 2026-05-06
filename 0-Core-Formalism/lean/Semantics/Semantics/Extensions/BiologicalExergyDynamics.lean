/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

BiologicalExergyDynamics.lean — Laws of exergy destruction and entropy production.

This module formalizes the thermodynamic laws of biological work and dissipation:
1. Dissipation: The Gouy-Stodola Theorem for exergy destruction.
2. Stability: Prigogine's Principle of Minimum Entropy Production.
3. Drive: Ziegler's Principle of Maximum Entropy Production.
4. Work: Metabolic efficiency and useful work output.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Exergy

open Semantics
open Semantics.Q16_16

/-! ## 1. Exergy Destruction (Gouy-Stodola) -/

/-- Gouy-Stodola Law (I).
    I = T0 * S_gen
    I: Exergy destruction (lost work), T0: environmental temperature, S_gen: entropy production.
    Quantifies the fundamental energy cost of biological irreversibility. -/
def exergyDestruction (temp_0 entropy_gen : Q16_16) : Q16_16 :=
  Q16_16.mul temp_0 entropy_gen

/-! ## 2. Entropy Production Extremals -/

/-- Prigogine's Minimum Entropy Production Step.
    Near-equilibrium systems tend toward states that minimize dS_gen/dt. -/
def minimumEntropyProductionUpdate (current_s_gen drift_rate dt : Q16_16) : Q16_16 :=
  -- Returns the next entropy production rate
  Q16_16.sub current_s_gen (Q16_16.mul drift_rate dt)

/-- Ziegler's Maximum Entropy Production Rate.
    Systems far from equilibrium maximize the rate of entropy production (σ). -/
def maximumEntropyProductionRate (forces fluxes : List Q16_16) : Q16_16 :=
  List.zipWith Q16_16.mul forces fluxes |>.foldl Q16_16.add Q16_16.zero

/-! ## 3. Metabolic Work Efficiency -/

/-- Useful Biological Work (W).
    W_actual = W_max - I
    Formalizes the 'useful work' available after accounting for exergy destruction. -/
def actualMetabolicWork (w_max exergy_destroyed : Q16_16) : Q16_16 :=
  Q16_16.sub w_max exergy_destroyed

end Semantics.Biology.Exergy
