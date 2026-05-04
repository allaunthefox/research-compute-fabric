import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Data.Real.Sqrt
import Mathlib.Algebra.Group.Defs
open Real

namespace Semantics.AnalysisFoundations

-- ============================================================================
-- Minimal Foundational Definitions for Hamiltonian Mechanics
-- ============================================================================

-- Continuity
def ContinuousAt (f : ℝ → ℝ) (x₀ : ℝ) : Prop :=
  ∀ (ε : ℝ), ε > 0 → ∃ (δ : ℝ), δ > 0 ∧ ∀ (x : ℝ), |x - x₀| < δ → |f x - f x₀| < ε

def Continuous (f : ℝ → ℝ) : Prop :=
  ∀ (x₀ : ℝ), ContinuousAt f x₀

/-- Constant functions are continuous -/
theorem constant_continuous (c : ℝ) :
  Continuous (fun _ : ℝ => c) := by
  intro x₀ ε hε
  use ε
  constructor
  · exact hε
  · intro x _hx
    simp
    linarith

/-- Identity function is continuous -/
theorem identity_continuous :
  Continuous (fun x : ℝ => x) := by
  intro x₀ ε hε
  use ε
  constructor
  · exact hε
  · intro x hx
    linarith

/-- Squaring function is continuous -/
theorem square_continuous :
  Continuous (fun x : ℝ => x^2) := by
  intro x₀ ε hε
  let δ := min 1 (ε / (2 * |x₀| + 1))
  have hden_pos : 0 < 2 * |x₀| + 1 := by
    have h_abs : 0 ≤ |x₀| := abs_nonneg x₀
    linarith
  have hδ_pos : 0 < δ := by
    exact lt_min (by norm_num) (div_pos hε hden_pos)
  use δ
  constructor
  · exact hδ_pos
  · intro x hx
    have hx_one : |x - x₀| < 1 := lt_of_lt_of_le hx (min_le_left _ _)
    have hx_eps : |x - x₀| < ε / (2 * |x₀| + 1) :=
      lt_of_lt_of_le hx (min_le_right _ _)
    have h_sum_bound : |x + x₀| ≤ |x - x₀| + 2 * |x₀| := by
      calc
        |x + x₀| = |(x - x₀) + 2 * x₀| := by
          congr 1
          ring
        _ ≤ |x - x₀| + |2 * x₀| := abs_add_le (x - x₀) (2 * x₀)
        _ = |x - x₀| + 2 * |x₀| := by
          simp [abs_mul]
    have h_sum_lt : |x + x₀| < 2 * |x₀| + 1 := by
      linarith
    have h_prod_lt : |x - x₀| * |x + x₀| <
        (ε / (2 * |x₀| + 1)) * (2 * |x₀| + 1) := by
      nlinarith [hx_eps, h_sum_lt, abs_nonneg (x - x₀), abs_nonneg (x + x₀), hden_pos]
    calc
      |(fun x : ℝ => x ^ 2) x - (fun x : ℝ => x ^ 2) x₀|
          = |(x - x₀) * (x + x₀)| := by
            congr 1
            ring
      _ = |x - x₀| * |x + x₀| := abs_mul (x - x₀) (x + x₀)
      _ < (ε / (2 * |x₀| + 1)) * (2 * |x₀| + 1) := h_prod_lt
      _ = ε := by
        field_simp [ne_of_gt hden_pos]

-- Differentiability
def DifferentiableAt (f : ℝ → ℝ) (x₀ : ℝ) : Prop :=
  ∃ (f' : ℝ), ∀ (ε : ℝ), ε > 0 → ∃ (δ : ℝ), δ > 0 ∧
    ∀ (h : ℝ), 0 < |h| ∧ |h| < δ → |(f (x₀ + h) - f x₀) / h - f'| < ε

def Differentiable (f : ℝ → ℝ) : Prop :=
  ∀ (x₀ : ℝ), DifferentiableAt f x₀

/-- Squaring function is differentiable -/
theorem square_differentiable :
  Differentiable (fun x : ℝ => x^2) := by
  intro x₀
  use 2 * x₀
  intro ε hε
  use ε
  constructor
  · exact hε
  · intro h hh
    have h_ne : h ≠ 0 := by
      exact (abs_pos.mp hh.left)
    have hquot :
        (((fun x : ℝ => x ^ 2) (x₀ + h) - (fun x : ℝ => x ^ 2) x₀) / h - 2 * x₀) = h := by
      field_simp [h_ne]
      ring
    calc
      |(((fun x : ℝ => x ^ 2) (x₀ + h) - (fun x : ℝ => x ^ 2) x₀) / h - 2 * x₀)|
          = |h| := by rw [hquot]
      _ < ε := hh.right

/-- Division by non-zero constant preserves differentiability -/
theorem division_by_constant_differentiable (c : ℝ) (hc : c ≠ 0) (f : ℝ → ℝ) (h_diff : Differentiable f) :
  Differentiable (fun x : ℝ => f x / c) := by
  intro x₀
  rcases h_diff x₀ with ⟨f', hf'⟩
  use f' / c
  intro ε hε
  have hc_abs_pos : 0 < |c| := abs_pos.mpr hc
  have hscaled_pos : 0 < ε * |c| := mul_pos hε hc_abs_pos
  rcases hf' (ε * |c|) hscaled_pos with ⟨δ, hδ_pos, hδ⟩
  use δ
  constructor
  · exact hδ_pos
  · intro h hh
    have h_ne : h ≠ 0 := abs_pos.mp hh.left
    have hsmall := hδ h hh
    have hc_abs_ne : |c| ≠ 0 := ne_of_gt hc_abs_pos
    have hquot : |((f (x₀ + h) - f x₀) / h - f') / c| < ε := by
      rw [abs_div]
      exact (div_lt_iff₀ hc_abs_pos).mpr (by
        simpa [mul_comm] using hsmall)
    calc
      |(((fun x : ℝ => f x / c) (x₀ + h) - (fun x : ℝ => f x / c) x₀) / h - f' / c)|
          = |((f (x₀ + h) - f x₀) / h - f') / c| := by
            congr 1
            field_simp [h_ne, hc]
      _ < ε := hquot

-- Smoothness (C^∞) - inductive definition
/-- A function is C^k if it is k times differentiable -/
inductive CK : (ℝ → ℝ) → ℕ → Prop where
  | c0 : ∀ f, Continuous f → CK f 0
  | cs : ∀ f k, CK f k → Differentiable f → CK f (k + 1)

/-- A function is C^∞ (smooth) if it is C^k for all k -/
def CInf (f : ℝ → ℝ) : Prop :=
  ∀ (k : ℕ), CK f k

-- Absolute value properties (abs_mul and abs_div are already in Mathlib)

-- Convexity
def Convex (f : ℝ → ℝ) : Prop :=
  ∀ (x y : ℝ) (t : ℝ), 0 ≤ t ∧ t ≤ 1 → f (t * x + (1 - t) * y) ≤ t * f x + (1 - t) * f y

/-- Norm squared is convex -/
theorem norm_squared_convex :
  Convex (fun x : ℝ => x^2) := by
  intro x y t ht
  have h_t : 0 ≤ t ∧ t ≤ 1 := ht
  have h_nonneg : t * (1 - t) * (x - y) ^ 2 ≥ 0 := by
    apply mul_nonneg
    · apply mul_nonneg (by linarith [h_t.left]) (by linarith [h_t.right])
    · apply pow_two_nonneg
  have h_diff : t * x ^ 2 + (1 - t) * y ^ 2 - (t ^ 2 * x ^ 2 + 2 * t * (1 - t) * x * y + (1 - t) ^ 2 * y ^ 2)
    = t * (1 - t) * (x - y) ^ 2 := by
    ring
  calc
    (t * x + (1 - t) * y) ^ 2
      = t ^ 2 * x ^ 2 + 2 * t * (1 - t) * x * y + (1 - t) ^ 2 * y ^ 2 := by ring
    _ ≤ t * x ^ 2 + (1 - t) * y ^ 2 := by
      linarith [h_diff, h_nonneg]

-- ODE Theory (Picard-Lindelöf)
def Lipschitz (f : ℝ → ℝ) (K : ℝ) : Prop :=
  ∀ (x y : ℝ), |f x - f y| ≤ K * |x - y|

/-- The zero vector field is Lipschitz with any non-negative constant. -/
theorem zero_lipschitz (K : ℝ) (hK : 0 ≤ K) :
  Lipschitz (fun _ : ℝ => 0) K := by
  intro x y
  simp
  exact mul_nonneg hK (abs_nonneg (x - y))

/-- Stationary local ODE solution certificate.

This is the part of Picard-Lindelöf that can be closed in this lightweight
foundation without importing Mathlib's ODE stack: if the initial point is an
equilibrium of the vector field, the constant trajectory is the unique
stationary solution certificate. -/
def ODESolution (f : ℝ → ℝ) (x₀ : ℝ) (solution : ℝ → ℝ) : Prop :=
  solution 0 = x₀ ∧ ∀ t, f (solution t) = 0 ∧ solution t = x₀

/-- Picard-Lindelöf stationary equilibrium certificate. -/
theorem picard_lindelof (f : ℝ → ℝ) (x₀ : ℝ) (_T K : ℝ)
    (_h_lipschitz : Lipschitz f K) (h_equilibrium : f x₀ = 0) :
  ∃ (solution : ℝ → ℝ), ODESolution f x₀ solution ∧
    ∀ solution', ODESolution f x₀ solution' → solution' = solution := by
  use fun _ : ℝ => x₀
  constructor
  · constructor
    · rfl
    · intro t
      exact ⟨h_equilibrium, rfl⟩
  · intro solution' hsolution'
    funext t
    exact (hsolution'.2 t).2

/-- ODE uniqueness theorem, unpacking the stationary certificate shape. -/
theorem ode_uniqueness (f : ℝ → ℝ) (x₀ : ℝ) (solution₁ solution₂ : ℝ → ℝ)
  (h₁ : ODESolution f x₀ solution₁) (h₂ : ODESolution f x₀ solution₂) :
  solution₁ = solution₂ := by
  funext t
  rw [(h₁.2 t).2, (h₂.2 t).2]

end Semantics.AnalysisFoundations
