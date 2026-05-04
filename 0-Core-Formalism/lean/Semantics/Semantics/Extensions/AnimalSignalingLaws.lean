/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

AnimalSignalingLaws.lean — Laws of honest communication and the handicap principle.

This module formalizes the laws of biological signaling:
1. Handicap: Zahavi's principle of costly signaling.
2. Honesty: Grafen's marginal cost condition for stable signaling.
3. Equilibrium: The perceptual identity between signal and true quality.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.Signaling

open Semantics
open Semantics.FixedPoint

/-! ## 1. Strategic Handicap (Grafen) -/

/-- Signal Fitness Function (w).
    w = f(a, p, q)
    a: advertising level, p: perceived quality, q: true quality. -/
def signalFitness (a p q k_cost k_benefit : Q16_16) : Q16_16 :=
  -- Fitness increases with p and q, but decreases with a.
  let cost := Q16_16.mul k_cost a
  let benefit := Q16_16.mul k_benefit p
  Q16_16.add (Q16_16.sub q cost) benefit

/-! ## 2. Conditions for Honesty -/

/-- Marginal Cost Condition (w13 > 0).
    The cost of increasing the signal must be lower for higher quality individuals.
    Returns true if signaling is stable and honest. -/
def isHonestyStable (q_high q_low a_level k_cost_high k_cost_low : Q16_16) : Bool :=
  -- Marginal cost of a for high quality must be < marginal cost for low quality
  k_cost_high.val.toNat < k_cost_low.val.toNat

/-! ## 3. Honest Equilibrium -/

/-- Perceptual Identity.
    At equilibrium, the receiver's perception (p) equals the signaler's true quality (q). -/
def checkHonestEquilibrium (perceived_p true_q : Q16_16) : Bool :=
  perceived_p == true_q

end Semantics.Biology.Signaling
