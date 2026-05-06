/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

CognitiveEfficiencyLaws.lean — Laws of information processing, movement, and metabolic cost.

This module formalizes the informational and metabolic constraints on cognitive systems:
1. Decision: Hick's Law for reaction time vs choice count.
2. Motor: Fitts's Law for movement time vs target difficulty.
3. Signals: Zipf's Law for frequency distributions in biological data.
4. Cost: Laughlin's Law for the metabolic expense of information capacity.
-/

import Semantics.FixedPoint
import Semantics.GeneticCode
import Semantics.Spectrum

namespace Semantics.Biology.CognitiveEfficiency

open Semantics
open Semantics.Q16_16

/-! ## 1. Decision Complexity -/

/-- Hick's Law (Reaction Time).
    RT = a + b * log2(n + 1)
    Models the time to make a decision among n equally probable choices. -/
def hicksReactionTime (n_choices : Nat) (a_const b_slope : Q16_16) : Q16_16 :=
  -- log2(n+1) approximation
  let n_f := Q16_16.ofInt (Int.ofNat (n_choices + 1))
  let log_n := if n_choices > 7 then Q16_16.ofInt 3 else Q16_16.one -- very simplified log2
  Q16_16.add a_const (Q16_16.mul b_slope log_n)

/-! ## 2. Motor Precision -/

/-- Fitts's Law (Movement Time).
    MT = a + b * log2(A/W + 1)
    A: Amplitude (distance), W: Width (target accuracy). -/
def fittsMovementTime (amplitude width : Q16_16) (a_const b_slope : Q16_16) : Q16_16 :=
  let difficulty := Q16_16.add (Q16_16.div amplitude width) Q16_16.one
  -- log2(difficulty) approximation
  let log_diff := difficulty
  Q16_16.add a_const (Q16_16.mul b_slope log_diff)

/-! ## 3. Signal Distributions -/

/-- Zipf's Law Probability.
    P(r) = 1 / (r^s * H_N,s)
    Models the frequency of codewords or species rank-abundance. -/
def zipfProbability (rank : Nat) (s_exponent : Q16_16) : Q16_16 :=
  let rank_f := Q16_16.ofInt (Int.ofNat rank)
  -- rank^-s approximation
  Q16_16.div Q16_16.one (Q16_16.mul rank_f s_exponent)

/-! ## 4. Metabolic Cost of Information -/

/-- Laughlin's Law (Metabolic Cost of Bits).
    Cost ∝ Information Capacity
    Models the high energy requirement of maintaining large-bandwidth neural channels. -/
def metabolicBitCost (capacity : Q16_16) (atp_per_bit : Q16_16) : Q16_16 :=
  Q16_16.mul capacity atp_per_bit

end Semantics.Biology.CognitiveEfficiency
