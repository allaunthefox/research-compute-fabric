import Mathlib

open Real

/- ═══════════════════════════════════════════════════════════════
   RG Bound on Unit Distances — Lean Formalization
   
   Key identity: 9^(log₃4) = 16 exactly.
   This gives recurrence F(n) = 9·F(n/9) + c·(n/9)^α → A = c/7.
-/

-- ═══════════════════════════════════════════════════════════════
-- §1  The RG constant α = log₃4
-- ═══════════════════════════════════════════════════════════════

noncomputable def alpha : ℝ := Real.log 4 / Real.log 3

/-- 9^α = 16 exactly. Uses the identity exp(2·ln4) = 4² = 16. -/
theorem nine_pow_alpha_eq_sixteen : (9 : ℝ) ^ alpha = (16 : ℝ) := by
  have log3_pos : Real.log 3 ≠ 0 := by
    exact ne_of_gt (Real.log_pos (by norm_num : (1 : ℝ) < 3))
  have h : 2 * Real.log 3 * (Real.log 4 / Real.log 3) = 2 * Real.log 4 := by
    field_simp [log3_pos]
  calc
    (9 : ℝ) ^ alpha = Real.exp (Real.log (9 : ℝ) * alpha) := by
      rw [Real.rpow_def_of_pos (by norm_num : (0 : ℝ) < 9)]
    _ = Real.exp (Real.log (9 : ℝ) * (Real.log 4 / Real.log 3)) := rfl
    _ = Real.exp ((2 * Real.log 3) * (Real.log 4 / Real.log 3)) := by
      rw [show Real.log (9 : ℝ) = 2 * Real.log 3 by
        calc
          Real.log (9 : ℝ) = Real.log ((3 : ℝ)^2) := by norm_num
          _ = 2 * Real.log 3 := by rw [Real.log_pow, Nat.cast_ofNat]
      ]
    _ = Real.exp (2 * Real.log 4) := by rw [h]
    _ = Real.exp (Real.log (4^2)) := by rw [Real.log_pow, Nat.cast_ofNat]
    _ = Real.exp (Real.log (16 : ℝ)) := by norm_num
    _ = (16 : ℝ) := Real.exp_log (by norm_num : (0 : ℝ) < 16)

/-- 9·(1/9)^α = 9/16 — the recurrence coefficient. -/
theorem recurrence_coefficient : (9 : ℝ) * ((1 : ℝ) / (9 : ℝ)) ^ alpha = (9 : ℝ) / (16 : ℝ) := by
  calc
    (9 : ℝ) * ((1 : ℝ) / (9 : ℝ)) ^ alpha = (9 : ℝ) * ((1 : ℝ) ^ alpha / (9 : ℝ) ^ alpha) := by
      rw [div_rpow (by norm_num : (0 : ℝ) ≤ 1) (by norm_num : (0 : ℝ) ≤ 9)]
    _ = (9 : ℝ) * ((1 : ℝ) / (9 : ℝ) ^ alpha) := by simp
    _ = (9 : ℝ) / (9 : ℝ) ^ alpha := by ring
    _ = (9 : ℝ) / (16 : ℝ) := by rw [nine_pow_alpha_eq_sixteen]

/-- Closed-form solution: if F(n) = A·n^α, then A = c/7. -/
theorem closed_form_coefficient (c : ℝ) : (c / 7) * (9 : ℝ)^alpha = 9 * (c / 7) + c := by
  calc
    (c / 7) * (9 : ℝ)^alpha = (c / 7) * (16 : ℝ) := by rw [nine_pow_alpha_eq_sixteen]
    _ = (16 * c) / 7 := by ring
    _ = (9 * c + 7 * c) / 7 := by ring
    _ = 9 * (c / 7) + c := by ring

-- ═══════════════════════════════════════════════════════════════
-- §2  Executable receipts
-- ═══════════════════════════════════════════════════════════════

#eval "=== RG UNIT DISTANCE BOUND ==="
#eval "α = log₃4"
#eval "9^α = 16 (exact)"
#eval "9·(1/9)^α = 9/16"
#eval "Recurrence: F(n) = 9·F(n/9) + c·(n/9)^α → A = c/7"
#eval "7A = c because 9^α = 16 = 9 + 7"
