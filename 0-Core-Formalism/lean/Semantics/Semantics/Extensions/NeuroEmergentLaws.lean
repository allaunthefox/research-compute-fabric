/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

NeuroEmergentLaws.lean — Laws of neural learning, memory, and critical emergence.

This module formalizes the laws of neural adaptation and collective organization:
1. Learning: Hebb's Law and Oja's Rule for synaptic plasticity.
2. Memory: Hopfield Network energy minimization.
3. Emergence: Self-Organized Criticality (SOC) and power-law scaling.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Emergence

open Semantics
open Semantics.FixedPoint

/-! ## 1. Synaptic Learning -/

/-- Hebb's Law (Associative Learning).
    Δw = η * x * y
    Models the strengthening of connections between co-active neurons. -/
def hebbianDelta (pre_activity post_activity learning_rate : Q16_16) : Q16_16 :=
  Q16_16.mul learning_rate (Q16_16.mul pre_activity post_activity)

/-- Oja's Rule (Stable PCA Learning).
    Δw = η * (x*y - y²*w)
    Constrains synaptic growth and extracts the principal component of input. -/
def ojaDelta (w x y learning_rate : Q16_16) : Q16_16 :=
  let y2 := Q16_16.mul y y
  let forgetting := Q16_16.mul y2 w
  let drift := Q16_16.sub (Q16_16.mul x y) forgetting
  Q16_16.mul learning_rate drift

/-! ## 2. Attractor Memory -/

/-- Hopfield Energy Function (E).
    E = -0.5 * Σ Σ w_ij * s_i * s_j
    Measures the stability of a neural state relative to stored memories. -/
def hopfieldEnergy (weights : List (List Q16_16)) (states : List Q16_16) : Q16_16 :=
  -- Returns the Lyapunov energy value
  let interaction_sum := weights.mapIdx (fun i row =>
    let si := states.get! i
    row.mapIdx (fun j wij =>
      let sj := states.get! j
      Q16_16.mul wij (Q16_16.mul si sj)
    ) |>.foldl Q16_16.add Q16_16.zero
  ) |>.foldl Q16_16.add Q16_16.zero
  Q16_16.mul (Q16_16.ofInt (-1)) (Q16_16.div interaction_sum (Q16_16.ofInt 2))

/-! ## 3. Self-Organized Criticality -/

/-- Power Law Distribution (SOC).
    P(s) = s^-tau
    Models the distribution of 'avalanches' in neural firing and ecosystems. -/
def avalancheProbability (size tau_exponent : Q16_16) : Q16_16 :=
  -- size^-tau approximation
  let size_f := size
  Q16_16.div Q16_16.one (Q16_16.mul size_f tau_exponent)

end Semantics.Biology.Emergence
