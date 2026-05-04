/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

Burgers.lean — Regularized Burgers PDE Formalism

This module formalizes the regularized Burgers equation primitives used in the
FNWH (Field-Native Witness Hierarchy). It implements the complexity-driven 
viscosity stiffening and pressure regularization as described in 
docs/specs/BurgersHarmonicPeelingVerification.md.

Equation:
  u_t + u u_x = ν_eff u_xx + η - λ ∂_x Φ_Ω

Complexity Metric:
  Ω[u] = 1/2 Σ_{n=1}^N n^2 |a_n|^2
-/

import Semantics.FixedPoint
import Semantics.WitnessGrammar
import Mathlib.Tactic

namespace Semantics.FNWH.Burgers

open Semantics
open Semantics.Q16_16
open Semantics.WitnessGrammar

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Fundamental Constants
-- ═══════════════════════════════════════════════════════════════════════════

/-- Stiffening factor κ = 0.3547.
    0.3547 * 65536 ≈ 23245. -/
def kappa : Q16_16 := ⟨23245⟩

/-- Default base viscosity ν_0 = 0.1.
    0.1 * 65536 ≈ 6554. -/
def defaultNu0 : Q16_16 := ⟨6554⟩

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Complexity Metrics (Ω)
-- ═══════════════════════════════════════════════════════════════════════════

/-- Compute the complexity contribution of a single witness: n^2 * |a|^2.
    n is the frequency index, a is the amplitude. -/
def witnessComplexityContribution (w : Semantics.WitnessGrammar.Witness) : Q16_16 :=
  let n := w.frequency
  let n2 := Q16_16.mul n n
  let a := w.amplitude
  let a2 := Q16_16.mul a a
  Q16_16.mul n2 a2

/-- Compute the total complexity metric Ω for a WitnessGrammar.
    Ω = 1/2 Σ n^2 |a_n|^2.
    Uses toList.foldl for straightforward inductive reasoning about the sum. -/
def complexityOmega (g : Semantics.WitnessGrammar.WitnessGrammar) : Q16_16 :=
  let sum := g.witnesses.toList.foldl (fun acc w => 
    Q16_16.add acc (witnessComplexityContribution w)) Q16_16.zero
  let half : Q16_16 := Q16_16.ofRaw 32768 -- 0.5 * 65536 = 32768
  Q16_16.mul half sum

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Regularized Parameters
-- ═══════════════════════════════════════════════════════════════════════════

/-- Effective viscosity ν_eff = ν_0 (1 + Ω). -/
def effectiveViscosity (nu0 omega : Q16_16) : Q16_16 :=
  Q16_16.mul nu0 (Q16_16.add Q16_16.one omega)

/-- Regularized quantum pressure Q_eff = Q_0 (1 + κ Ω). -/
def regularizedPressure (q0 omega : Q16_16) : Q16_16 :=
  Q16_16.mul q0 (Q16_16.add Q16_16.one (Q16_16.mul kappa omega))

/-- Stiffening multiplier (1 + κ Ω). -/
def stiffeningMultiplier (omega : Q16_16) : Q16_16 :=
  Q16_16.add Q16_16.one (Q16_16.mul kappa omega)

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Validation & Theorems
-- ═══════════════════════════════════════════════════════════════════════════

/-- 3-mode toy witness grammar for testing. -/
def toyGrammar : Semantics.WitnessGrammar.WitnessGrammar := {
  witnesses := #[
    { frequency := Q16_16.ofInt 1, amplitude := Q16_16.ofFloat 1.0, phase := Q16_16.zero, role := WitnessRole.carrier, action := WitnessAction.routeToBHOCS },
    { frequency := Q16_16.ofInt 2, amplitude := Q16_16.ofFloat 0.3, phase := Q16_16.zero, role := WitnessRole.texture, action := WitnessAction.routeToFAMM },
    { frequency := Q16_16.ofInt 3, amplitude := Q16_16.ofFloat 0.1, phase := Q16_16.zero, role := WitnessRole.texture, action := WitnessAction.routeToFAMM }
  ],
  residualEnergy := Q16_16.zero,
  closed := true
}

#eval complexityOmega toyGrammar

/-- Positivity property of witness complexity: w_n^2 * |a_n|^2 is always non-negative. -/
lemma witnessComplexity_nonneg (w : Semantics.WitnessGrammar.Witness) :
  (witnessComplexityContribution w).toInt ≥ 0 :=
by
  unfold witnessComplexityContribution
  -- n^2 ≥ 0
  have h_n2 := Q16_16.mul_self_nonneg w.frequency
  -- a^2 ≥ 0
  have h_a2 := Q16_16.mul_self_nonneg w.amplitude
  -- (n^2 * a^2) ≥ 0
  apply Q16_16.mul_toInt_nonneg
  · exact h_n2
  · exact h_a2


/-- Positivity property of Ω: complexity is always non-negative. -/
lemma complexityOmega_nonneg (g : Semantics.WitnessGrammar.WitnessGrammar) :
  (complexityOmega g).toInt ≥ 0 :=
by
  unfold complexityOmega
  -- First prove the fold sum is non-negative by induction on the witness list
  have h_fold_nonneg (acc : Q16_16) (h_acc : acc.toInt ≥ 0) : 
    (g.witnesses.toList.foldl (fun a w => Q16_16.add a (witnessComplexityContribution w)) acc).toInt ≥ 0 := by
    induction' g.witnesses.toList with w ws ih generalizing acc
    · simpa using h_acc
    · rw [List.foldl_cons]
      apply ih
      unfold Q16_16.add
      apply Q16_16.ofRaw_toInt_nonneg
      have h_wcc_nonneg := witnessComplexity_nonneg w
      omega
  have h_sum_nonneg : (g.witnesses.toList.foldl (fun a w => Q16_16.add a (witnessComplexityContribution w)) Q16_16.zero).toInt ≥ 0 :=
    h_fold_nonneg Q16_16.zero (by rw [Q16_16.zero_toInt]; omega)
  -- mul half sum where half > 0 and sum ≥ 0
  apply Q16_16.mul_toInt_nonneg
  · unfold Q16_16.ofRaw; simp; omega
  · exact h_sum_nonneg


/-- Positivity property: Effective viscosity is always ≥ base viscosity for any grammar. -/
theorem nu_eff_ge_nu0 (nu0 : Q16_16) (g : Semantics.WitnessGrammar.WitnessGrammar) (h_nu0 : nu0.toInt ≥ 0) :
  (effectiveViscosity nu0 (complexityOmega g)).toInt ≥ nu0.toInt :=
by
  unfold effectiveViscosity
  let omega := complexityOmega g
  have h_omega := complexityOmega_nonneg g
  -- 1 + omega ≥ 1 (i.e., (1+omega).toInt ≥ 65536)
  have h_one_plus_omega : (Q16_16.add Q16_16.one omega).toInt ≥ 65536 :=
    Q16_16.add_one_omega_ge_one omega h_omega
  unfold Q16_16.mul
  -- We need to show: (ofRaw (nu0.toInt * (1+omega).toInt / 65536)).toInt ≥ nu0.toInt
  -- Let a = nu0.toInt, b = (1+omega).toInt, d = 65536
  -- We know a ≥ 0, b ≥ d, d > 0
  -- The key inequality: a*b/d ≥ a when a ≥ 0 and b ≥ d
  set a := nu0.toInt with ha
  set b := (Q16_16.add Q16_16.one omega).toInt with hb
  set d := 65536 with hd
  have ha_nonneg : 0 ≤ a := h_nu0
  have hb_ge_d : d ≤ b := h_one_plus_omega
  have hd_pos : 0 < d := by omega
  have h_inner : a * b / d ≥ a := by
    -- If a = 0, division yields 0, so 0 ≥ 0 holds trivially
    by_cases ha_zero : a = 0
    · subst a; simp
    · have ha_pos : 0 < a := by omega
      -- Proof by contradiction: assume a*b/d < a
      by_contra! h_lt
      -- Then a*b/d + 1 ≤ a
      have h_q_plus_one_le_a : a * b / d + 1 ≤ a := by omega
      -- Euclidean division: a*b = (a*b/d)*d + (a*b % d)
      have h_eq := Int.ediv_add_emod (a * b) d
      have h_mod_lt : a * b % d < d := Int.emod_lt _ hd_pos
      -- From Euclidean division: a*b < (a*b/d + 1)*d
      have h_ab_lt_q1_times_d : a * b < (a * b / d + 1) * d := by
        nlinarith
      -- Since a*b/d + 1 ≤ a, we have (a*b/d + 1)*d ≤ a*d
      have h_q1_times_d_le_a_times_d : (a * b / d + 1) * d ≤ a * d := by
        nlinarith
      -- Since b ≥ d, we have a*b ≥ a*d
      have h_ab_ge_a_times_d : a * b ≥ a * d :=
        mul_le_mul_of_nonneg_left hb_ge_d ha_nonneg
      -- Now: a*b < (a*b/d+1)*d ≤ a*d ≤ a*b, a contradiction
      nlinarith
  -- Now handle the ofRaw saturation:
  unfold Q16_16.ofRaw
  split
  · -- Saturated case: result > 0x7FFFFFFF → toInt = 0x7FFFFFFF
    rename_i h_sat
    -- 0x7FFFFFFF ≥ a since a ≤ 0x7FFFFFFF (from the definition of Q16_16)
    have h_a_bound : a ≤ 0x7FFFFFFF := Q16_16.toInt_nonneg_le_maxVal nu0 h_nu0
    unfold Q16_16.toInt
    simp
    omega
  · split
    · -- Saturated negative case: impossible since a*b/d ≥ a ≥ 0
      rename_i h_not_gt h_neg
      omega
    · -- Normal case: ofRaw preserves the value
      rename_i h_not_gt h_not_neg
      unfold Q16_16.toInt
      -- Need to show the toNat conversion preserves the inequality
      have h_val_eq : (a * b / d).toNat % 0x100000000 = (a * b / d).toNat := by
        apply Nat.mod_eq_of_lt
        have h_nonneg : 0 ≤ a * b / d := Int.ediv_nonneg (by
          have h_ab_nonneg : 0 ≤ a * b := mul_nonneg ha_nonneg (by omega)
          exact h_ab_nonneg) hd_pos
        have h_lt_pow32 : a * b / d < 2^32 := by
          have h_bound : a * b / d ≤ 0x7FFFFFFF := by
            push_neg at h_not_gt
            omega
          omega
        have h_nat_lt : (a * b / d).toNat < 0x100000000 := by
          have h_nonneg : 0 ≤ a * b / d := by
            apply Int.ediv_nonneg
            · apply mul_nonneg ha_nonneg; omega
            · omega
          omega
        exact h_nat_lt
      simp only [h_val_eq, Int.toNat_of_nonneg (by
        apply Int.ediv_nonneg (mul_nonneg ha_nonneg (by omega)) hd_pos
      )]
      exact h_inner


end Semantics.FNWH.Burgers
