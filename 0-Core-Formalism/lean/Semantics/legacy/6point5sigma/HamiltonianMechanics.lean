import Mathlib.Tactic
import Mathlib.Data.Real.Basic
import Mathlib.Data.Fin.Basic
import Mathlib.Analysis.Calculus.Deriv.Basic
import Mathlib.Analysis.Calculus.Deriv.Prod
import Mathlib.Analysis.Calculus.FDeriv.Basic
import Mathlib.MeasureTheory.Integral.IntervalIntegral

open Real
open scoped Interval

namespace Semantics.AnalysisFoundations

-- ============================================================================
-- Single-Variable Analysis (Continuity, Differentiability, Smoothness, Convexity)
-- ============================================================================

/-- A function f : ℝ → ℝ is continuous at x₀ if the usual ε-δ definition holds. -/
def ContinuousAt (f : ℝ → ℝ) (x₀ : ℝ) : Prop :=
  ∀ (ε : ℝ), ε > 0 → ∃ (δ : ℝ), δ > 0 ∧ ∀ (x : ℝ), |x - x₀| < δ → |f x - f x₀| < ε

/-- A function f : ℝ → ℝ is continuous if it is continuous at every point. -/
def Continuous (f : ℝ → ℝ) : Prop :=
  ∀ (x₀ : ℝ), ContinuousAt f x₀

/-- Constant functions are continuous. -/
theorem constant_continuous (c : ℝ) :
  Continuous (fun _ : ℝ => c) := by
  intro x₀ ε hε
  use ε
  constructor
  · exact hε
  · intro x _hx
    simp
    linarith

/-- The identity function is continuous. -/
theorem identity_continuous :
  Continuous (fun x : ℝ => x) := by
  intro x₀ ε hε
  use ε
  constructor
  · exact hε
  · intro x hx
    linarith

/-- The squaring function is continuous. -/
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

/-- A function f : ℝ → ℝ is differentiable at x₀ with derivative f' if the limit
of the difference quotient exists and equals f'. -/
def DifferentiableAt (f : ℝ → ℝ) (x₀ : ℝ) : Prop :=
  ∃ (f' : ℝ), ∀ (ε : ℝ), ε > 0 → ∃ (δ : ℝ), δ > 0 ∧
    ∀ (h : ℝ), 0 < |h| ∧ |h| < δ → |(f (x₀ + h) - f x₀) / h - f'| < ε

/-- A function f : ℝ → ℝ is differentiable if it is differentiable at every point. -/
def Differentiable (f : ℝ → ℝ) : Prop :=
  ∀ (x₀ : ℝ), DifferentiableAt f x₀

/-- The squaring function is differentiable, with derivative 2x. -/
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

/-- Division by a non-zero constant preserves differentiability. -/
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
/-- A function is C^k if it is k times differentiable. -/
inductive CK : (ℝ → ℝ) → ℕ → Prop where
  | c0 : ∀ f, Continuous f → CK f 0
  | cs : ∀ f k, CK f k → Differentiable f → CK f (k + 1)

/-- A function is C^∞ (smooth) if it is C^k for all k. -/
def CInf (f : ℝ → ℝ) : Prop :=
  ∀ (k : ℕ), CK f k

-- Convexity
/-- A function f : ℝ → ℝ is convex if the epigraph inequality holds. -/
def Convex (f : ℝ → ℝ) : Prop :=
  ∀ (x y : ℝ) (t : ℝ), 0 ≤ t ∧ t ≤ 1 → f (t * x + (1 - t) * y) ≤ t * f x + (1 - t) * f y

/-- The norm squared x ↦ x² is convex. -/
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

-- ============================================================================
-- Proper ODE Theory
-- ============================================================================

/-- A trajectory γ : ℝ → ℝ solves the 1D ODE ẋ = f(x) with initial condition x₀
if γ(0) = x₀ and γ has derivative f(γ(t)) at every time t. -/
def IsSolution1D (f : ℝ → ℝ) (x₀ : ℝ) (γ : ℝ → ℝ) : Prop :=
  γ 0 = x₀ ∧ ∀ t, HasDerivAt γ (f (γ t)) t

/-- A trajectory γ : ℝ → ℝⁿ solves the nD ODE ẋ = f(x) with initial condition x₀. -/
def IsSolutionND {n : ℕ} (f : (Fin n → ℝ) → (Fin n → ℝ)) (x₀ : Fin n → ℝ) (γ : ℝ → (Fin n → ℝ)) : Prop :=
  γ 0 = x₀ ∧ ∀ t, HasDerivAt γ (f (γ t)) t

/-- The Picard iterates for an ODE ẋ = f(x) with initial condition x₀:
γ₀(t) = x₀,  γ_{m+1}(t) = x₀ + ∫₀ᵗ f(γ_m(s)) ds. -/
noncomputable def picardIterate {n : ℕ} (f : (Fin n → ℝ) → (Fin n → ℝ)) (x₀ : Fin n → ℝ) : ℕ → ℝ → (Fin n → ℝ)
  | 0 => fun _ => x₀
  | m+1 => fun t => x₀ + ∫ s in (0)..t, f (picardIterate f x₀ m s)

/-- The constant trajectory at an equilibrium point is a valid ODE solution.
This is elementary because the derivative of a constant function is 0,
and at equilibrium f(x₀) = 0. -/
theorem constant_equilibrium_solution (f : ℝ → ℝ) (x₀ : ℝ) (hf : f x₀ = 0) :
  IsSolution1D f x₀ (fun _ => x₀) := by
  constructor
  · rfl
  · intro t
    rw [hf]
    exact hasDerivAt_const t x₀

/-- Uniqueness of solutions for globally Lipschitz ODEs.
If two trajectories solve the same ODE with the same initial condition,
they must be identical. This is the uniqueness half of Picard-Lindelöf,
proven via a discrete Gronwall argument on the squared Euclidean norm. -/
theorem picard_lindelof_uniqueness {n : ℕ} (f : (Fin n → ℝ) → (Fin n → ℝ)) (x₀ : Fin n → ℝ) (K : ℝ)
    (hK : K ≥ 0)
    (h_lipschitz : ∀ x y, ‖f x - f y‖ ≤ K * ‖x - y‖)
    (γ₁ γ₂ : ℝ → (Fin n → ℝ))
    (h₁ : IsSolutionND f x₀ γ₁) (h₂ : IsSolutionND f x₀ γ₂) :
  γ₁ = γ₂ := by
  have h_init : γ₁ 0 = x₀ := h₁.1
  have h_init₂ : γ₂ 0 = x₀ := h₂.1
  have heq0 : γ₁ 0 = γ₂ 0 := by rw [h_init, h_init₂]
  have h_deriv₁ := h₁.2
  have h_deriv₂ := h₂.2
  funext t
  have ht : γ₁ t = γ₂ t := by
    -- Consider the squared Euclidean norm D(s) = Σ_i (γ₁(s) i - γ₂(s) i)².
    -- We show D(t) = 0 for all t, which implies γ₁(t) = γ₂(t).
    let D := fun s : ℝ => ∑ i : Fin n, ((γ₁ s i - γ₂ s i) ^ 2)
    -- D is differentiable because it is a finite sum of squares of differentiable functions.
    have hD_deriv : ∀ s, HasDerivAt D (∑ i, (2 * (γ₁ s i - γ₂ s i) * (f (γ₁ s) i - f (γ₂ s) i))) s := by
      intro s
      have h_diff_i : ∀ i, HasDerivAt (fun u => (γ₁ u i - γ₂ u i) ^ 2)
          (2 * (γ₁ s i - γ₂ s i) * (f (γ₁ s) i - f (γ₂ s) i)) s := by
        intro i
        have h1 : HasDerivAt (fun u => γ₁ u i - γ₂ u i) (f (γ₁ s) i - f (γ₂ s) i) s := by
          have hg1 := HasFDerivAt.comp_hasDerivAt s
            (ContinuousLinearMap.hasFDerivAt ( ContinuousLinearMap.proj i))
            (h_deriv₁ s)
          have hg2 := HasFDerivAt.comp_hasDerivAt s
            (ContinuousLinearMap.hasFDerivAt ( ContinuousLinearMap.proj i))
            (h_deriv₂ s)
          simpa using HasDerivAt.sub hg1 hg2
        have h2 := HasDerivAt.mul h1 h1
        convert h2 using 1
        ring
      simpa using HasDerivAt.sum h_diff_i
    -- D satisfies the differential inequality D'(s) ≤ 2nK D(s).
    have hD_bound : ∀ s, (∑ i, (2 * (γ₁ s i - γ₂ s i) * (f (γ₁ s) i - f (γ₂ s) i))) ≤ 2 * n * K * (D s) := by
      intro s
      let a := fun i => γ₁ s i - γ₂ s i
      let b := fun i => f (γ₁ s) i - f (γ₂ s) i
      have h_abs : ∀ i, |b i| ≤ K * ‖a‖ := by
        intro i
        have h_lip := h_lipschitz (γ₁ s) (γ₂ s)
        have hbi : |b i| ≤ ‖f (γ₁ s) - f (γ₂ s)‖ := by
          simp [b, norm_le_pi_norm_apply]
        linarith [hbi, h_lip]
      have h_sum : ∑ i, (2 * (a i) * (b i)) ≤ 2 * (∑ i, |a i| * |b i|) := by
        apply Finset.sum_le_sum
        intro i _
        have h1 : a i * b i ≤ |a i| * |b i| := by
          apply le_trans (le_abs_self (a i * b i))
          rw [abs_mul]
        linarith
      have h_sum2 : ∑ i, |a i| * |b i| ≤ ∑ i, |a i| * (K * ‖a‖) := by
        apply Finset.sum_le_sum
        intro i _
        have h2 := h_abs i
        nlinarith [abs_nonneg (a i)]
      have h_sum3 : ∑ i, |a i| * (K * ‖a‖) = K * ‖a‖ * (∑ i, |a i|) := by
        rw [Finset.sum_mul]
        apply Finset.sum_congr rfl
        intro i _
        ring
      have h_sum4 : ∑ i, |a i| ≤ n * ‖a‖ := by
        have h5 : ∀ i, |a i| ≤ ‖a‖ := by
          intro i
          exact norm_le_pi_norm_apply a i
        have h6 : ∑ i, |a i| ≤ ∑ i, ‖a‖ := by
          apply Finset.sum_le_sum
          intro i _
          exact h5 i
        simp at h6
        nlinarith
      have h_D : D s = ‖a‖ ^ 2 := by
        simp [D, a, sq]
        rfl
      nlinarith [h_sum, h_sum2, h_sum3, h_sum4, h_D, hK]
    -- Consider g(s) = exp(-2nKs) D(s). Its derivative is non-positive.
    let g := fun s : ℝ => Real.exp (-2 * n * K * s) * (D s)
    have hg0 : g 0 = 0 := by
      simp [g, D, heq0]
    have hg_nonpos : ∀ s, HasDerivAt g ((Real.exp (-2 * n * K * s)) * ((∑ i, (2 * (γ₁ s i - γ₂ s i) * (f (γ₁ s) i - f (γ₂ s) i))) - 2 * n * K * (D s))) s := by
      intro s
      have he : HasDerivAt (fun u => Real.exp (-2 * n * K * u)) (Real.exp (-2 * n * K * s) * (-2 * n * K)) s := by
        have h1 : HasDerivAt (fun u => -2 * n * K * u) (-2 * n * K) s := by
          convert HasDerivAt.const_mul (hasDerivAt_id s) (-2 * n * K) using 1
          ring
        apply HasDerivAt.comp s (hasDerivAt_exp (-2 * n * K * s)) h1
      have hD := hD_deriv s
      have hmul := HasDerivAt.mul he hD
      convert hmul using 1
      ring
    -- g is non-increasing because its derivative is everywhere ≤ 0.
    have hg_antitone : ∀ a b, a ≤ b → g b ≤ g a := by
      intro a b hab
      by_cases h_eq : a = b
      · rw [h_eq]
      · have h_lt : a < b := by linarith
        have hdiff : Differentiable ℝ g := by
          intro s
          exact HasDerivAt.differentiableAt (hg_nonpos s)
        have hcont := Differentiable.continuous hdiff
        have hcont_on : ContinuousOn g (Set.Icc a b) := hcont.continuousOn
        have hder : ∀ s ∈ Set.Ioo a b, HasDerivAt g ((Real.exp (-2 * n * K * s)) * ((∑ i, (2 * (γ₁ s i - γ₂ s i) * (f (γ₁ s) i - f (γ₂ s) i))) - 2 * n * K * (D s))) s := by
          intro s _
          exact hg_nonpos s
        have hder_nonpos : ∀ s ∈ Set.Ioo a b, (Real.exp (-2 * n * K * s)) * ((∑ i, (2 * (γ₁ s i - γ₂ s i) * (f (γ₁ s) i - f (γ₂ s) i))) - 2 * n * K * (D s)) ≤ 0 := by
          intro s hs
          have he_pos : 0 < Real.exp (-2 * n * K * s) := Real.exp_pos (-2 * n * K * s)
          have hinner := hD_bound s
          nlinarith [he_pos]
        have hmvt : ∃ c ∈ Set.Ioo a b, g b - g a = (Real.exp (-2 * n * K * c)) * ((∑ i, (2 * (γ₁ c i - γ₂ c i) * (f (γ₁ c) i - f (γ₂ c) i))) - 2 * n * K * (D c)) * (b - a) := by
          apply exists_hasDerivAt_eq_slope g (fun s => (Real.exp (-2 * n * K * s)) * ((∑ i, (2 * (γ₁ s i - γ₂ s i) * (f (γ₁ s) i - f (γ₂ s) i))) - 2 * n * K * (D s))) a b h_lt hcont_on
          intro x hx
          exact hder x hx
        rcases hmvt with ⟨c, hc, heq⟩
        have hc_nonpos : (Real.exp (-2 * n * K * c)) * ((∑ i, (2 * (γ₁ c i - γ₂ c i) * (f (γ₁ c) i - f (γ₂ c) i))) - 2 * n * K * (D c)) ≤ 0 := hder_nonpos c hc
        nlinarith [hc_nonpos]
    -- Since g(0) = 0 and g is non-increasing, g(t) ≤ 0 for t ≥ 0 and g(t) ≥ 0 for t ≤ 0.
    -- But g(t) ≥ 0 always because D(t) ≥ 0. Hence g(t) = 0 everywhere.
    have hg_le0 : g t ≤ 0 := by
      by_cases ht0 : t ≥ 0
      · have : g t ≤ g 0 := hg_antitone 0 t ht0
        linarith [this, hg0]
      · have ht0' : t ≤ 0 := by linarith
        have : g 0 ≤ g t := hg_antitone t 0 ht0'
        linarith [this, hg0]
    have hg_ge0 : 0 ≤ g t := by
      simp [g]
      apply mul_nonneg
      · apply le_of_lt (Real.exp_pos (-2 * n * K * t))
      · simp [D]
        apply Finset.sum_nonneg
        intro i _
        apply sq_nonneg
    have hgt0 : g t = 0 := by linarith [hg_le0, hg_ge0]
    have hDt0 : D t = 0 := by
      simp [g] at hgt0
      have he_pos : 0 < Real.exp (-2 * n * K * t) := Real.exp_pos (-2 * n * K * t)
      nlinarith [he_pos]
    have h_eq_i : ∀ i, γ₁ t i - γ₂ t i = 0 := by
      intro i
      have h_nonneg : (γ₁ t i - γ₂ t i) ^ 2 ≥ 0 := sq_nonneg (γ₁ t i - γ₂ t i)
      have h_sum : ∑ i, ((γ₁ t i - γ₂ t i) ^ 2) = 0 := hDt0
      have h_zero : (γ₁ t i - γ₂ t i) ^ 2 = 0 := by
        have h1 : (γ₁ t i - γ₂ t i) ^ 2 ≤ ∑ i, ((γ₁ t i - γ₂ t i) ^ 2) := by
          apply Finset.single_le_sum (fun j _ => sq_nonneg (γ₁ t j - γ₂ t j))
          simp
        nlinarith
      have h_zero2 : γ₁ t i - γ₂ t i = 0 := pow_eq_zero h_zero
      exact h_zero2
    funext i
    linarith [h_eq_i i]
  exact ht

/-- The Picard-Lindelöf theorem: for a globally Lipschitz vector field, there exists
a unique global solution to the initial value problem. (Global Lipschitz implies
linear growth, which prevents finite-time blowout.)

Existence follows from the Banach fixed-point theorem applied to the Picard
operator P(γ)(t) = x₀ + ∫₀ᵗ f(γ(s)) ds on C([−T,T]) with T < 1/K. The
contraction constant is < 1, yielding a unique local fixed point. Global
existence follows by gluing local solutions (the global Lipschitz bound
prevents finite-time blowup). Uniqueness is `picard_lindelof_uniqueness` above. -/
theorem picard_lindelof {n : ℕ} (f : (Fin n → ℝ) → (Fin n → ℝ)) (x₀ : Fin n → ℝ) (K : ℝ)
    (hK : K ≥ 0)
    (h_lipschitz : ∀ x y, ‖f x - f y‖ ≤ K * ‖x - y‖) :
  ∃! γ : ℝ → (Fin n → ℝ), IsSolutionND f x₀ γ := by
  -- Existence follows from the Banach fixed-point theorem applied to the Picard
  -- operator P(γ)(t) = x₀ + ∫₀ᵗ f(γ(s)) ds on C([−T,T]) with T < 1/(2K). With
  -- the weighted sup-norm ‖γ‖_w = sup e^{−2K|t|}‖γ(t)‖, one shows P is a strict
  -- contraction (constant 1/2) via the calculation:
  --   ‖P(γ₁)−P(γ₂)‖_w ≤ sup_t e^{−2K|t|}·|∫₀ᵗ K·‖γ₁−γ₂‖_w·e^{2K|s|}ds|
  --                   ≤ (K‖γ₁−γ₂‖_w)·(e^{2Kt}−1)/(2K)·e^{−2Kt}
  --                   ≤ ‖γ₁−γ₂‖_w / 2.
  -- The unique fixed point solves the ODE on [−T,T]; global existence follows
  -- by gluing (the linear growth bound ‖f(x)‖ ≤ ‖f(x₀)‖+K‖x−x₀‖ prevents blowup).
  -- A full Lean proof requires formalizing C([−T,T]) as a complete metric space,
  -- the weighted-norm contraction estimate, and the local-to-global extension.
  -- TODO(lean-port): Prove existence via Banach fixed-point theorem on Picard operator.
  -- Requires: complete metric space C([-T,T]), weighted sup-norm ‖γ‖_w = sup e^{-2K|t|}‖γ(t)‖,
  -- contraction constant 1/2 via ‖P(γ₁)-P(γ₂)‖_w ≤ ‖γ₁-γ₂‖_w / 2,
  -- and local-to-global extension via linear growth bound ‖f(x)‖ ≤ ‖f(x₀)‖+K‖x-x₀‖.
  have hex : ∃ γ, IsSolutionND f x₀ γ := sorry
  have hunique : ∀ γ₁ γ₂, IsSolutionND f x₀ γ₁ → IsSolutionND f x₀ γ₂ → γ₁ = γ₂ := by
    intro γ₁ γ₂ h₁ h₂
    exact picard_lindelof_uniqueness f x₀ K hK h_lipschitz γ₁ γ₂ h₁ h₂
  exact exists_unique_of_exists_of_unique hex hunique

-- ============================================================================
-- Multivariable Differential Calculus on Phase Space
-- ============================================================================

/-- Phase space for a system with n degrees of freedom: pairs (q, p) of
position and momentum vectors. -/
def PhaseSpace (n : ℕ) := (Fin n → ℝ) × (Fin n → ℝ)

/-- Replace the q-coordinate at index i with value t, keeping all other
coordinates fixed. -/
def replaceQ {n : ℕ} (x : PhaseSpace n) (i : Fin n) (t : ℝ) : PhaseSpace n :=
  ⟨fun j => if j = i then t else x.1 j, x.2⟩

/-- Replace the p-coordinate at index i with value t, keeping all other
coordinates fixed. -/
def replaceP {n : ℕ} (x : PhaseSpace n) (i : Fin n) (t : ℝ) : PhaseSpace n :=
  ⟨x.1, fun j => if j = i then t else x.2 j⟩

/-- H has partial derivative d with respect to q_i at point x. -/
def HasPartialDerivAtQ {n : ℕ} (H : PhaseSpace n → ℝ) (i : Fin n) (d : ℝ) (x : PhaseSpace n) : Prop :=
  HasDerivAt (fun t : ℝ => H (replaceQ x i t)) d (x.1 i)

/-- H has partial derivative d with respect to p_i at point x. -/
def HasPartialDerivAtP {n : ℕ} (H : PhaseSpace n → ℝ) (i : Fin n) (d : ℝ) (x : PhaseSpace n) : Prop :=
  HasDerivAt (fun t : ℝ => H (replaceP x i t)) d (x.2 i)

/-- The gradient of H with respect to the q-coordinates.
If the partial derivative does not exist, we arbitrarily set it to 0. -/
noncomputable def gradQ {n : ℕ} (H : PhaseSpace n → ℝ) (x : PhaseSpace n) : Fin n → ℝ :=
  fun i => if h : ∃ d, HasPartialDerivAtQ H i d x then h.choose else 0

/-- The gradient of H with respect to the p-coordinates.
If the partial derivative does not exist, we arbitrarily set it to 0. -/
noncomputable def gradP {n : ℕ} (H : PhaseSpace n → ℝ) (x : PhaseSpace n) : Fin n → ℝ :=
  fun i => if h : ∃ d, HasPartialDerivAtP H i d x then h.choose else 0

-- ============================================================================
-- Symplectic Structure
-- ============================================================================

/-- The canonical symplectic form on phase space:
ω((q,p), (q',p')) = Σ_i (p_i q'_i - q_i p'_i). -/
def ω {n : ℕ} (u v : PhaseSpace n) : ℝ :=
  ∑ i : Fin n, (u.2 i * v.1 i - u.1 i * v.2 i)

/-- The symplectic form is bilinear (linear in each argument separately).
We state this as two theorems. -/
theorem ω_linear_left {n : ℕ} (u₁ u₂ v : PhaseSpace n) (c : ℝ) :
  ω (c • u₁ + u₂) v = c * ω u₁ v + ω u₂ v := by
  unfold ω
  simp [Finset.sum_add_distrib, Finset.mul_sum, add_mul, mul_add, mul_sub]
  rw [← Finset.sum_add_distrib]
  apply Finset.sum_congr rfl
  intro i _
  ring

/-- The symplectic form is antisymmetric: ω(u, v) = -ω(v, u). -/
theorem ω_antisymmetric {n : ℕ} (u v : PhaseSpace n) :
  ω u v = -ω v u := by
  unfold ω
  rw [← Finset.sum_neg_distrib]
  apply Finset.sum_congr rfl
  intro i _
  ring

/-- The symplectic form is non-degenerate: if ω(u, v) = 0 for all v, then u = 0. -/
theorem ω_nondegenerate {n : ℕ} (u : PhaseSpace n)
    (h : ∀ v : PhaseSpace n, ω u v = 0) : u = 0 := by
  have hq : u.1 = 0 := by
    funext j
    let v : PhaseSpace n := ⟨0, fun i => if i = j then 1 else 0⟩
    have hω := h v
    simp [ω, v] at hω
    linarith
  have hp : u.2 = 0 := by
    funext j
    let v : PhaseSpace n := ⟨fun i => if i = j then 1 else 0, 0⟩
    have hω := h v
    simp [ω, v] at hω
    linarith
  exact Prod.ext hq hp

-- ============================================================================
-- Hamiltonian Vector Field
-- ============================================================================

/-- The Hamiltonian vector field X_H associated to a Hamiltonian function H.
In coordinates: X_H = (∂H/∂p, -∂H/∂q), which is equivalent to
ω(X_H, ·) = dH via the symplectic musical isomorphism. -/
noncomputable def HamiltonianVectorField {n : ℕ} (H : PhaseSpace n → ℝ) (x : PhaseSpace n) : PhaseSpace n :=
  ⟨gradP H x, -gradQ H x⟩

/-- Hamilton's equations in vector field form: a trajectory γ satisfies
ẋ = X_H(x), i.e., the time derivative of γ at t equals the Hamiltonian
vector field evaluated at γ(t). -/
def IsHamiltonianTrajectory {n : ℕ} (H : PhaseSpace n → ℝ) (γ : ℝ → PhaseSpace n) : Prop :=
  ∀ t, HasDerivAt γ (HamiltonianVectorField H (γ t)) t

/-- Hamilton's equations in coordinates: for each degree of freedom i,
dq_i/dt = ∂H/∂p_i and dp_i/dt = -∂H/∂q_i.

This follows from the product decomposition of HasDerivAt for
functions into product types (Mathlib.Analysis.Calculus.Deriv.Prod)
combined with component-wise extraction via continuous linear evaluation. -/
theorem hamiltonian_eqs_coordinates {n : ℕ} (H : PhaseSpace n → ℝ) (γ : ℝ → PhaseSpace n)
    (h_traj : IsHamiltonianTrajectory H γ) (t : ℝ) :
  ∀ i : Fin n, HasDerivAt (fun s => (γ s).1 i) (gradP H (γ t) i) t ∧
              HasDerivAt (fun s => (γ s).2 i) (-gradQ H (γ t) i) t := by
  intro i
  have h_deriv := h_traj t
  have h_fst : HasDerivAt (fun s => (γ s).1) (HamiltonianVectorField H (γ t)).1 t := by
    simpa [HamiltonianVectorField] using HasDerivAt.fst h_deriv
  have h_snd : HasDerivAt (fun s => (γ s).2) (HamiltonianVectorField H (γ t)).2 t := by
    simpa [HamiltonianVectorField] using HasDerivAt.snd h_deriv
  constructor
  · -- q_i derivative: compose the first-component derivative with evaluation at i
    let eval_i : (Fin n → ℝ) →L[ℝ] ℝ :=
      { toFun := fun f => f i,
        map_add' := by intros; rfl,
        map_smul' := by intros; rfl,
        cont := by continuity }
    have heval : HasFDerivAt eval_i eval_i ((γ t).1) := eval_i.hasFDerivAt
    have hcomp := HasFDerivAt.comp_hasDerivAt t heval h_fst
    simpa [HamiltonianVectorField, eval_i] using hcomp
  · -- p_i derivative: compose the second-component derivative with evaluation at i
    let eval_i : (Fin n → ℝ) →L[ℝ] ℝ :=
      { toFun := fun f => f i,
        map_add' := by intros; rfl,
        map_smul' := by intros; rfl,
        cont := by continuity }
    have heval : HasFDerivAt eval_i eval_i ((γ t).2) := eval_i.hasFDerivAt
    have hcomp := HasFDerivAt.comp_hasDerivAt t heval h_snd
    simpa [HamiltonianVectorField, eval_i] using hcomp

-- ============================================================================
-- Example: The 1D Harmonic Oscillator
-- ============================================================================

/-- The Hamiltonian for a 1D harmonic oscillator with mass m and spring constant k:
H(q, p) = p²/(2m) + kq²/2. -/
def HarmonicOscillatorH (m k : ℝ) (hm : m > 0) (hk : k > 0) : PhaseSpace 1 → ℝ :=
  fun x => (x.2 0)^2 / (2 * m) + k * (x.1 0)^2 / 2

/-- The partial derivative of the harmonic oscillator Hamiltonian with respect to p. -/
theorem harmonic_oscillator_partial_p (m k : ℝ) (hm : m > 0) (hk : k > 0) (q p : ℝ) :
  HasDerivAt (fun t : ℝ => t^2 / (2 * m) + k * q^2 / 2) (p / m) p := by
  have h1 : HasDerivAt (fun t => t^2) (2 * p) p := hasDerivAt_pow 2 p
  have h2 : HasDerivAt (fun t => t^2 / (2 * m)) ((2 * p) / (2 * m)) p := by
    simpa using HasDerivAt.mul_const (c := 1 / (2 * m)) h1
  have h3 : HasDerivAt (fun _ => k * q^2 / 2) 0 p := hasDerivAt_const p (k * q^2 / 2)
  convert HasDerivAt.add h2 h3 using 1
  field_simp [ne_of_gt hm]
  ring

/-- The partial derivative of the harmonic oscillator Hamiltonian with respect to q. -/
theorem harmonic_oscillator_partial_q (m k : ℝ) (hm : m > 0) (hk : k > 0) (q p : ℝ) :
  HasDerivAt (fun t : ℝ => p^2 / (2 * m) + k * t^2 / 2) (k * q) q := by
  have h1 : HasDerivAt (fun _ => p^2 / (2 * m)) 0 q := hasDerivAt_const q (p^2 / (2 * m))
  have h2 : HasDerivAt (fun t => t^2) (2 * q) q := hasDerivAt_pow 2 q
  have h3 : HasDerivAt (fun t => k * t^2 / 2) (k * (2 * q) / 2) q := by
    simpa using HasDerivAt.mul_const (c := k / 2) h2
  convert HasDerivAt.add h1 h3 using 1
  field_simp [ne_of_gt hm]
  ring

/-- The q-gradient of the harmonic oscillator Hamiltonian equals k·q. -/
lemma gradQ_harmonic_oscillator (m k : ℝ) (hm : m > 0) (hk : k > 0) (x : PhaseSpace 1) :
  gradQ (HarmonicOscillatorH m k hm hk) x 0 = k * x.1 0 := by
  have hex : ∃ d, HasPartialDerivAtQ (HarmonicOscillatorH m k hm hk) 0 d x := by
    use k * x.1 0
    simpa [HasPartialDerivAtQ, replaceQ, HarmonicOscillatorH] using
      harmonic_oscillator_partial_q m k hm hk (x.1 0) (x.2 0)
  have h1 : HasPartialDerivAtQ (HarmonicOscillatorH m k hm hk) 0 (gradQ (HarmonicOscillatorH m k hm hk) x 0) x := by
    simpa [gradQ, hex] using Classical.choose_spec hex
  have h2 : HasPartialDerivAtQ (HarmonicOscillatorH m k hm hk) 0 (k * x.1 0) x := by
    simpa [HasPartialDerivAtQ, replaceQ, HarmonicOscillatorH] using
      harmonic_oscillator_partial_q m k hm hk (x.1 0) (x.2 0)
  exact HasDerivAt.unique h1 h2

/-- The p-gradient of the harmonic oscillator Hamiltonian equals p/m. -/
lemma gradP_harmonic_oscillator (m k : ℝ) (hm : m > 0) (hk : k > 0) (x : PhaseSpace 1) :
  gradP (HarmonicOscillatorH m k hm hk) x 0 = x.2 0 / m := by
  have hex : ∃ d, HasPartialDerivAtP (HarmonicOscillatorH m k hm hk) 0 d x := by
    use x.2 0 / m
    simpa [HasPartialDerivAtP, replaceP, HarmonicOscillatorH] using
      harmonic_oscillator_partial_p m k hm hk (x.1 0) (x.2 0)
  have h1 : HasPartialDerivAtP (HarmonicOscillatorH m k hm hk) 0 (gradP (HarmonicOscillatorH m k hm hk) x 0) x := by
    simpa [gradP, hex] using Classical.choose_spec hex
  have h2 : HasPartialDerivAtP (HarmonicOscillatorH m k hm hk) 0 (x.2 0 / m) x := by
    simpa [HasPartialDerivAtP, replaceP, HarmonicOscillatorH] using
      harmonic_oscillator_partial_p m k hm hk (x.1 0) (x.2 0)
  exact HasDerivAt.unique h1 h2

/-- The Hamiltonian equations for the 1D harmonic oscillator are:
ẋq = p/m and ẋp = -kq. -/
theorem harmonic_oscillator_equations (m k : ℝ) (hm : m > 0) (hk : k > 0) (γ : ℝ → PhaseSpace 1)
    (h_traj : IsHamiltonianTrajectory (HarmonicOscillatorH m k hm hk) γ) (t : ℝ) :
  HasDerivAt (fun s => (γ s).1 0) ((γ t).2 0 / m) t ∧
  HasDerivAt (fun s => (γ s).2 0) (-k * (γ t).1 0) t := by
  have hcoords := hamiltonian_eqs_coordinates (HarmonicOscillatorH m k hm hk) γ h_traj t 0
  have hq : gradP (HarmonicOscillatorH m k hm hk) (γ t) 0 = (γ t).2 0 / m := gradP_harmonic_oscillator m k hm hk (γ t)
  have hp : gradQ (HarmonicOscillatorH m k hm hk) (γ t) 0 = k * (γ t).1 0 := gradQ_harmonic_oscillator m k hm hk (γ t)
  constructor
  · rw [hq] at hcoords
    exact hcoords.1
  · rw [hp] at hcoords
    have h_neg : -gradQ (HarmonicOscillatorH m k hm hk) (γ t) 0 = -k * (γ t).1 0 := by
      rw [hp]
      ring
    rwa [h_neg] at hcoords

-- ============================================================================
-- Energy Conservation
-- ============================================================================

/-- Any continuous linear functional on PhaseSpace n can be evaluated using
the standard basis vectors. In coordinates:
L(v_q, v_p) = Σ_i (v_q i · L(e_{q_i}) + v_p i · L(e_{p_i})). -/
lemma clm_on_phaseSpace {n : ℕ} (L : PhaseSpace n →L[ℝ] ℝ) (v : PhaseSpace n) :
  L v = ∑ i : Fin n, (v.1 i * L (⟨fun j => if j = i then 1 else 0, 0⟩)
                     + v.2 i * L (⟨0, fun j => if j = i then 1 else 0⟩)) := by
  have h1 : v.1 = ∑ i : Fin n, v.1 i • (fun j => if j = i then (1 : ℝ) else 0) := by
    funext j
    simp [Finset.sum_apply, ite_mul, zero_mul, mul_ite, mul_zero]
    rw [Finset.sum_ite_eq']
    simp
  have h2 : v.2 = ∑ i : Fin n, v.2 i • (fun j => if j = i then (1 : ℝ) else 0) := by
    funext j
    simp [Finset.sum_apply, ite_mul, zero_mul, mul_ite, mul_zero]
    rw [Finset.sum_ite_eq']
    simp
  have h3 : v = (∑ i : Fin n, v.1 i • (⟨fun j => if j = i then 1 else 0, 0⟩ : PhaseSpace n))
              + (∑ i : Fin n, v.2 i • (⟨0, fun j => if j = i then 1 else 0⟩ : PhaseSpace n)) := by
    rw [Prod.ext_iff]
    constructor
    · rw [h1]
      simp [Finset.sum_apply, smul_eq_mul]
    · rw [h2]
      simp [Finset.sum_apply, smul_eq_mul]
  rw [h3]
  simp [map_add, map_sum, map_smul]
  rw [← Finset.sum_add_distrib]
  apply Finset.sum_congr rfl
  intro i _
  ring

/-- Energy conservation: along a Hamiltonian trajectory, the Hamiltonian H(γ(t))
is constant in time, i.e., its time derivative is 0.

The proof uses the chain rule for Fréchet derivatives:
d/dt H(γ(t)) = D H(γ(t)) [γ'(t)] = D H(γ(t)) [X_H(γ(t))].

We require as a hypothesis that H has a Fréchet derivative at γ(t) which agrees
with the partial derivatives on the standard basis vectors. This is equivalent
to differentiability of H. The Hamiltonian structure then guarantees the
derivative vanishes by antisymmetry of the symplectic form. -/
theorem energy_conservation {n : ℕ} (H : PhaseSpace n → ℝ) (γ : ℝ → PhaseSpace n)
    (h_traj : IsHamiltonianTrajectory H γ) (t : ℝ)
    (h_diff : ∃ L : PhaseSpace n →L[ℝ] ℝ, HasFDerivAt H L (γ t) ∧
      (∀ i, L (⟨fun j => if j = i then 1 else 0, 0⟩) = gradQ H (γ t) i) ∧
      (∀ i, L (⟨0, fun j => if j = i then 1 else 0⟩) = gradP H (γ t) i)) :
  HasDerivAt (fun s => H (γ s)) 0 t := by
  rcases h_diff with ⟨L, hL, hLq, hLp⟩
  have h_chain := HasFDerivAt.comp_hasDerivAt t hL (h_traj t)
  have h_zero : L (HamiltonianVectorField H (γ t)) = 0 := by
    rw [clm_on_phaseSpace L (HamiltonianVectorField H (γ t))]
    simp only [HamiltonianVectorField]
    rw [← Finset.sum_add_distrib]
    apply Finset.sum_congr rfl
    intro i _
    rw [hLq i, hLp i]
    ring
  simpa [h_zero] using h_chain

-- ============================================================================
-- Poisson Brackets
-- ============================================================================

/-- The Poisson bracket of two scalar functions f and g on phase space.
In coordinates: {f, g} = Σ_i (∂f/∂q_i · ∂g/∂p_i - ∂f/∂p_i · ∂g/∂q_i). -/
noncomputable def poissonBracket {n : ℕ} (f g : PhaseSpace n → ℝ) (x : PhaseSpace n) : ℝ :=
  ∑ i : Fin n, (gradQ f x i * gradP g x i - gradP f x i * gradQ g x i)

/-- The Poisson bracket is antisymmetric: {f, g} = -{g, f}. -/
theorem poissonBracket_antisym {n : ℕ} (f g : PhaseSpace n → ℝ) (x : PhaseSpace n) :
  poissonBracket f g x = -poissonBracket g f x := by
  unfold poissonBracket
  rw [← Finset.sum_neg_distrib]
  apply Finset.sum_congr rfl
  intro i _
  ring

/-- The Poisson bracket of any function with itself vanishes: {H, H} = 0.
This is an immediate consequence of antisymmetry. -/
theorem poissonBracket_self_zero {n : ℕ} (H : PhaseSpace n → ℝ) (x : PhaseSpace n) :
  poissonBracket H H x = 0 := by
  have h : poissonBracket H H x = -poissonBracket H H x := by
    rw [poissonBracket_antisym]
  linarith

/-- A quantity f is conserved along the Hamiltonian flow of H if and only if
its Poisson bracket with H vanishes: {f, H} = 0.

This follows from the chain rule: df/dt = {f, H} along trajectories.
The proof requires the multivariable chain rule (as in energy_conservation),
so we state this as a definition of what it means to be "conserved". -/
def IsConserved {n : ℕ} (f H : PhaseSpace n → ℝ) : Prop :=
  ∀ x, poissonBracket f H x = 0

-- ============================================================================
-- Flow of a Vector Field
-- ============================================================================

/-- A flow of a vector field V on phase space is a family of maps ϕ^t such that
for every initial point x, the curve t ↦ ϕ^t(x) is a solution of the ODE
with initial condition x. -/
def IsFlow {n : ℕ} (V : PhaseSpace n → PhaseSpace n) (ϕ : ℝ → PhaseSpace n → PhaseSpace n) : Prop :=
  (∀ x, ϕ 0 x = x) ∧ (∀ x t, HasDerivAt (fun s => ϕ s x) (V (ϕ t x)) t)

/-- The identity property of the flow: ϕ^0 = id. -/
theorem flow_identity {n : ℕ} (V : PhaseSpace n → PhaseSpace n) (ϕ : ℝ → PhaseSpace n → PhaseSpace n)
    (h_flow : IsFlow V ϕ) :
  ∀ x, ϕ 0 x = x := by
  intro x
  exact (h_flow.1 x)

/-- The semigroup property of the flow: ϕ^{s+t} = ϕ^s ∘ ϕ^t.
This is one of the fundamental properties of flows of ODEs.

The proof uses the uniqueness theorem picard_lindelof_uniqueness:
both sides are solutions of the same ODE with the same initial condition
ϕ^t(x) at time 0, hence they coincide. -/
theorem flow_semigroup {n : ℕ} (V : PhaseSpace n → PhaseSpace n) (ϕ : ℝ → PhaseSpace n → PhaseSpace n)
    (h_flow : IsFlow V ϕ)
    (h_lipschitz : ∃ K : ℝ, K ≥ 0 ∧ ∀ x y, ‖V x - V y‖ ≤ K * ‖x - y‖) :
  ∀ x s t, ϕ (s + t) x = ϕ s (ϕ t x) := by
  intro x s t
  rcases h_lipschitz with ⟨K, hK, hV_lip⟩
  -- Both sides satisfy the ODE with initial condition ϕ^t(x) at time 0.
  let γ₁ := fun u : ℝ => ϕ (t + u) x
  let γ₂ := fun u : ℝ => ϕ u (ϕ t x)
  have hγ₁_init : γ₁ 0 = ϕ t x := by simp [γ₁]
  have hγ₂_init : γ₂ 0 = ϕ t x := by simp [γ₂, h_flow.1]
  have hγ₁_sol : IsSolutionND (fun y => V y) (ϕ t x) γ₁ := by
    constructor
    · exact hγ₁_init
    · intro u
      have h := h_flow.2 x (t + u)
      have h' : HasDerivAt (fun v => ϕ v x) (V (ϕ (t + u) x)) (t + u) := by
        simpa using h
      have h_comp : HasDerivAt (fun v => ϕ (t + v) x) (V (ϕ (t + u) x)) u := by
        have h_shift : HasDerivAt (fun v => t + v) 1 u := hasDerivAt_id' u
        exact HasDerivAt.comp u h' h_shift
      simpa [γ₁] using h_comp
  have hγ₂_sol : IsSolutionND (fun y => V y) (ϕ t x) γ₂ := by
    constructor
    · exact hγ₂_init
    · intro u
      have h := h_flow.2 (ϕ t x) u
      simpa [γ₂] using h
  have heq := picard_lindelof_uniqueness (fun y => V y) (ϕ t x) K hK hV_lip γ₁ γ₂ hγ₁_sol hγ₂_sol
  have h_at_s : γ₁ s = γ₂ s := by
    rw [heq]
  simp [γ₁, γ₂] at h_at_s
  exact h_at_s

-- ============================================================================
-- Liouville's Theorem (Symplecticity of Hamiltonian Flow)
-- ============================================================================

/-- A map F : PhaseSpace n → PhaseSpace n is symplectic if it preserves
the canonical symplectic form at the linearized (fderiv) level:
ω(DF(u), DF(v)) = ω(u, v) for all tangent vectors u, v. -/
def IsSymplecticMap {n : ℕ} (F : PhaseSpace n → PhaseSpace n) : Prop :=
  ∀ x u v, ω (fderiv ℝ F x u) (fderiv ℝ F x v) = ω u v

-- ============================================================================
-- Hamiltonian Hessian and Linearized Vector Field
-- ============================================================================

/-- Second partial derivative ∂²H/∂q_i∂q_j, defined as the derivative of
(gradQ H · e_i) with respect to q_j. -/
noncomputable def hessianQQ {n : ℕ} (H : PhaseSpace n → ℝ) (x : PhaseSpace n) (i j : Fin n) : ℝ :=
  if h : ∃ d, HasDerivAt (fun t => gradQ H (replaceQ x j t) i) d (x.1 j) then h.choose else 0

/-- Second partial derivative ∂²H/∂p_i∂p_j. -/
noncomputable def hessianPP {n : ℕ} (H : PhaseSpace n → ℝ) (x : PhaseSpace n) (i j : Fin n) : ℝ :=
  if h : ∃ d, HasDerivAt (fun t => gradP H (replaceP x j t) i) d (x.2 j) then h.choose else 0

/-- Second partial derivative ∂²H/∂q_i∂p_j. -/
noncomputable def hessianQP {n : ℕ} (H : PhaseSpace n → ℝ) (x : PhaseSpace n) (i j : Fin n) : ℝ :=
  if h : ∃ d, HasDerivAt (fun t => gradQ H (replaceP x j t) i) d (x.2 j) then h.choose else 0

/-- Second partial derivative ∂²H/∂p_i∂q_j. -/
noncomputable def hessianPQ {n : ℕ} (H : PhaseSpace n → ℝ) (x : PhaseSpace n) (i j : Fin n) : ℝ :=
  if h : ∃ d, HasDerivAt (fun t => gradP H (replaceQ x j t) i) d (x.1 j) then h.choose else 0

/-- The derivative of the Hamiltonian vector field X_H at x applied to v.
In coordinates:
  (DX_H · v)_q_i = Σ_j (hessianPQ_ij · v_q_j + hessianPP_ij · v_p_j)
  (DX_H · v)_p_i = Σ_j (−hessianQQ_ij · v_q_j − hessianQP_ij · v_p_j) -/
def DX_H_action {n : ℕ} (H : PhaseSpace n → ℝ) (x : PhaseSpace n) (v : PhaseSpace n) : PhaseSpace n :=
  ⟨fun i => ∑ j : Fin n, (hessianPQ H x i j * v.1 j + hessianPP H x i j * v.2 j),
   fun i => ∑ j : Fin n, (-hessianQQ H x i j * v.1 j - hessianQP H x i j * v.2 j)⟩

/-- The Hamiltonian vector field derivative is skew-symmetric with respect to ω:
ω(DX_H · u, v) + ω(u, DX_H · v) = 0.

This is the infinitesimal algebraic identity underlying symplectic preservation.
The proof expands both terms and uses Clairaut's theorem (symmetry of mixed
partials) to show all terms cancel in pairs. -/
lemma hamiltonian_skew_symmetric {n : ℕ} (H : PhaseSpace n → ℝ) (x : PhaseSpace n)
    (u v : PhaseSpace n)
    (h_clairaut : ∀ i j, hessianQQ H x i j = hessianQQ H x j i
                        ∧ hessianPP H x i j = hessianPP H x j i
                        ∧ hessianQP H x i j = hessianPQ H x j i) :
  ω (DX_H_action H x u) v + ω u (DX_H_action H x v) = 0 := by
  -- Expand both terms fully using definitions
  simp only [ω, DX_H_action]
  -- The QQ terms cancel by antisymmetry of (u_q_i·v_q_j − u_q_j·v_q_i) + symmetry of hessianQQ
  have h_QQ : ∑ i : Fin n, ∑ j : Fin n,
      (-hessianQQ H x i j * u.1 j * v.1 i + hessianQQ H x i j * u.1 i * v.1 j) = 0 := by
    have h_symm : ∀ i j, hessianQQ H x i j = hessianQQ H x j i := fun i j => (h_clairaut i j).1
    have h_total : ∑ i, ∑ j, hessianQQ H x i j * (u.1 i * v.1 j - u.1 j * v.1 i) = 0 := by
      have h1 : ∑ i, ∑ j, hessianQQ H x i j * (u.1 i * v.1 j - u.1 j * v.1 i)
          = ∑ j, ∑ i, hessianQQ H x j i * (u.1 j * v.1 i - u.1 i * v.1 j) := by
        rw [Finset.sum_comm]
        apply Finset.sum_congr rfl
        intro i _
        apply Finset.sum_congr rfl
        intro j _
        ring
      have h2 : ∑ j, ∑ i, hessianQQ H x j i * (u.1 j * v.1 i - u.1 i * v.1 j)
          = -∑ i, ∑ j, hessianQQ H x i j * (u.1 i * v.1 j - u.1 j * v.1 i) := by
        simp_rw [h_symm]
        have h_neg : ∀ i j, u.1 j * v.1 i - u.1 i * v.1 j = -(u.1 i * v.1 j - u.1 j * v.1 i) := by
          intro i j; ring
        simp_rw [h_neg, mul_neg, Finset.sum_neg_distrib]
      linarith [h1, h2]
    have h_eq : ∀ i j, -hessianQQ H x i j * u.1 j * v.1 i + hessianQQ H x i j * u.1 i * v.1 j
        = hessianQQ H x i j * (u.1 i * v.1 j - u.1 j * v.1 i) := by
      intro i j; ring
    simp_rw [h_eq]
    exact h_total
  -- The PP terms: same argument
  have h_PP : ∑ i : Fin n, ∑ j : Fin n,
      (-hessianPP H x i j * u.2 j * v.2 i + hessianPP H x i j * u.2 i * v.2 j) = 0 := by
    have h_symm : ∀ i j, hessianPP H x i j = hessianPP H x j i := fun i j => (h_clairaut i j).2.1
    have h_total : ∑ i, ∑ j, hessianPP H x i j * (u.2 i * v.2 j - u.2 j * v.2 i) = 0 := by
      have h1 : ∑ i, ∑ j, hessianPP H x i j * (u.2 i * v.2 j - u.2 j * v.2 i)
          = ∑ j, ∑ i, hessianPP H x j i * (u.2 j * v.2 i - u.2 i * v.2 j) := by
        rw [Finset.sum_comm]
        apply Finset.sum_congr rfl
        intro i _
        apply Finset.sum_congr rfl
        intro j _
        ring
      have h2 : ∑ j, ∑ i, hessianPP H x j i * (u.2 j * v.2 i - u.2 i * v.2 j)
          = -∑ i, ∑ j, hessianPP H x i j * (u.2 i * v.2 j - u.2 j * v.2 i) := by
        simp_rw [h_symm]
        have h_neg : ∀ i j, u.2 j * v.2 i - u.2 i * v.2 j = -(u.2 i * v.2 j - u.2 j * v.2 i) := by
          intro i j; ring
        simp_rw [h_neg, mul_neg, Finset.sum_neg_distrib]
      linarith [h1, h2]
    have h_eq : ∀ i j, -hessianPP H x i j * u.2 j * v.2 i + hessianPP H x i j * u.2 i * v.2 j
        = hessianPP H x i j * (u.2 i * v.2 j - u.2 j * v.2 i) := by
      intro i j; ring
    simp_rw [h_eq]
    exact h_total
  -- The cross terms (QP + PQ): cancel using hessianQP_ij = hessianPQ_ji
  have h_cross : ∑ i : Fin n, ∑ j : Fin n,
      (-hessianQP H x i j * u.2 j * v.1 i + hessianQP H x i j * u.1 i * v.2 j
       - hessianPQ H x i j * u.1 j * v.2 i + hessianPQ H x i j * u.2 i * v.1 j) = 0 := by
    have h_cross_symm : ∀ i j, hessianQP H x i j = hessianPQ H x j i := fun i j => (h_clairaut j i).2.2
    have h_eq : ∀ i j, -hessianQP H x i j * u.2 j * v.1 i + hessianQP H x i j * u.1 i * v.2 j
        - hessianPQ H x i j * u.1 j * v.2 i + hessianPQ H x i j * u.2 i * v.1 j
        = hessianPQ H x j i * (-u.2 j * v.1 i + u.1 i * v.2 j)
        + hessianPQ H x i j * (-u.1 j * v.2 i + u.2 i * v.1 j) := by
      intro i j
      rw [h_cross_symm i j]
      ring
    simp_rw [h_eq]
    have h_total : ∑ i, ∑ j, hessianPQ H x j i * (-u.2 j * v.1 i + u.1 i * v.2 j)
        + ∑ i, ∑ j, hessianPQ H x i j * (-u.1 j * v.2 i + u.2 i * v.1 j) = 0 := by
      have h_swap : ∑ i, ∑ j, hessianPQ H x j i * (-u.2 j * v.1 i + u.1 i * v.2 j)
          = ∑ i, ∑ j, hessianPQ H x i j * (u.2 i * v.1 j - u.1 j * v.2 i) := by
        rw [Finset.sum_comm]
        apply Finset.sum_congr rfl
        intro i _
        apply Finset.sum_congr rfl
        intro j _
        ring
      rw [h_swap]
      have h_cancel : ∀ i j, hessianPQ H x i j * (u.2 i * v.1 j - u.1 j * v.2 i)
          + hessianPQ H x i j * (-u.1 j * v.2 i + u.2 i * v.1 j) = 0 := by
        intro i j
        ring
      simp_rw [h_cancel]
      simp
    linarith [h_total]
  -- Rearrange each (i,j) term into the four groups
  have h_rearrange : ∀ i j,
      (-hessianQQ H x i j * u.1 j * v.1 i - hessianQP H x i j * u.2 j * v.1 i
       - hessianPQ H x i j * u.1 j * v.2 i - hessianPP H x i j * u.2 j * v.2 i
       + hessianPQ H x i j * u.2 i * v.1 j + hessianPP H x i j * u.2 i * v.2 j
       + hessianQQ H x i j * u.1 i * v.1 j + hessianQP H x i j * u.1 i * v.2 j)
      = hessianQQ H x i j * (u.1 i * v.1 j - u.1 j * v.1 i)
      + hessianPP H x i j * (u.2 i * v.2 j - u.2 j * v.2 i)
      + hessianPQ H x i j * (u.2 i * v.1 j - u.1 j * v.2 i)
      + hessianQP H x i j * (u.1 i * v.2 j - u.2 j * v.1 i) := by
    intro i j; ring
  simp_rw [h_rearrange]
  -- Split into four double sums
  rw [← Finset.sum_add_distrib, ← Finset.sum_add_distrib]
  -- Match with the three cancellation lemmas
  have h_sum3_4 : (∑ i : Fin n, ∑ j : Fin n, hessianPQ H x i j * (u.2 i * v.1 j - u.1 j * v.2 i))
      + (∑ i : Fin n, ∑ j : Fin n, hessianQP H x i j * (u.1 i * v.2 j - u.2 j * v.1 i))
      = ∑ i : Fin n, ∑ j : Fin n,
        (-hessianQP H x i j * u.2 j * v.1 i + hessianQP H x i j * u.1 i * v.2 j
         - hessianPQ H x i j * u.1 j * v.2 i + hessianPQ H x i j * u.2 i * v.1 j) := by
    rw [← Finset.sum_add_distrib]
    apply Finset.sum_congr rfl
    intro i _
    rw [← Finset.sum_add_distrib]
    apply Finset.sum_congr rfl
    intro j _
    ring
  linarith [h_QQ, h_PP, h_cross, h_sum3_4]

/-- Derivative of the symplectic form composed with two curves:
d/dt ω(a(t), b(t)) = ω(a'(t), b(t)) + ω(a(t), b'(t)). -/
lemma deriv_of_bilinear_ω {n : ℕ} (a b : ℝ → PhaseSpace n) (a' b' : PhaseSpace n) (t : ℝ)
    (ha : HasDerivAt a a' t) (hb : HasDerivAt b b' t) :
  HasDerivAt (fun s => ω (a s) (b s)) (ω a' (b t) + ω (a t) b') t := by
  -- Expand ω as a sum of products
  have h_expand : ∀ s, ω (a s) (b s) = ∑ i : Fin n, ((a s).2 i * (b s).1 i - (a s).1 i * (b s).2 i) := by
    intro s; rfl
  rw [show (fun s => ω (a s) (b s)) = fun s => ∑ i, ((a s).2 i * (b s).1 i - (a s).1 i * (b s).2 i)
      by funext s; apply h_expand]
  -- Extract component-wise derivatives using projection CLMs
  have ha1 i : HasDerivAt (fun s => (a s).1 i) (a'.1 i) t := by
    let eval_i : (Fin n → ℝ) →L[ℝ] ℝ :=
      ⟨fun f => f i, by intros; rfl, by intros; rfl, by continuity⟩
    have heval : HasFDerivAt eval_i eval_i ((a t).1) := eval_i.hasFDerivAt
    have ha_fst : HasDerivAt (fun s => (a s).1) a'.1 t := HasDerivAt.fst ha
    exact HasFDerivAt.comp_hasDerivAt t heval ha_fst
  have ha2 i : HasDerivAt (fun s => (a s).2 i) (a'.2 i) t := by
    let eval_i : (Fin n → ℝ) →L[ℝ] ℝ :=
      ⟨fun f => f i, by intros; rfl, by intros; rfl, by continuity⟩
    have heval : HasFDerivAt eval_i eval_i ((a t).2) := eval_i.hasFDerivAt
    have ha_snd : HasDerivAt (fun s => (a s).2) a'.2 t := HasDerivAt.snd ha
    exact HasFDerivAt.comp_hasDerivAt t heval ha_snd
  have hb1 i : HasDerivAt (fun s => (b s).1 i) (b'.1 i) t := by
    let eval_i : (Fin n → ℝ) →L[ℝ] ℝ :=
      ⟨fun f => f i, by intros; rfl, by intros; rfl, by continuity⟩
    have heval : HasFDerivAt eval_i eval_i ((b t).1) := eval_i.hasFDerivAt
    have hb_fst : HasDerivAt (fun s => (b s).1) b'.1 t := HasDerivAt.fst hb
    exact HasFDerivAt.comp_hasDerivAt t heval hb_fst
  have hb2 i : HasDerivAt (fun s => (b s).2 i) (b'.2 i) t := by
    let eval_i : (Fin n → ℝ) →L[ℝ] ℝ :=
      ⟨fun f => f i, by intros; rfl, by intros; rfl, by continuity⟩
    have heval : HasFDerivAt eval_i eval_i ((b t).2) := eval_i.hasFDerivAt
    have hb_snd : HasDerivAt (fun s => (b s).2) b'.2 t := HasDerivAt.snd hb
    exact HasFDerivAt.comp_hasDerivAt t heval hb_snd
  -- Differentiate the sum term by term using product rule
  have h_deriv : HasDerivAt (fun s => ∑ i, ((a s).2 i * (b s).1 i - (a s).1 i * (b s).2 i))
      (∑ i, (a'.2 i * (b t).1 i + (a t).2 i * b'.1 i - a'.1 i * (b t).2 i - (a t).1 i * b'.2 i)) t := by
    apply HasDerivAt.sum
    intro i _
    apply HasDerivAt.sub
    · apply HasDerivAt.mul (ha2 i) (hb1 i)
    · apply HasDerivAt.mul (ha1 i) (hb2 i)
  convert h_deriv using 1
  -- Show the derivative equals ω(a', b) + ω(a, b')
  simp [ω]
  rw [← Finset.sum_add_distrib]
  apply Finset.sum_congr rfl
  intro i _
  ring

-- ============================================================================
-- Liouville's Theorem (Symplecticity of Hamiltonian Flow)
-- ============================================================================

/-- A map F : PhaseSpace n → PhaseSpace n is symplectic if it preserves
the canonical symplectic form at the linearized (fderiv) level:
ω(DF(u), DF(v)) = ω(u, v) for all tangent vectors u, v. -/
def IsSymplecticMap {n : ℕ} (F : PhaseSpace n → PhaseSpace n) : Prop :=
  ∀ x u v, ω (fderiv ℝ F x u) (fderiv ℝ F x v) = ω u v

/-- Liouville's theorem: the flow of a Hamiltonian vector field preserves
the canonical symplectic form.

Proof ingredients:
1. Clairaut's theorem (symmetry of mixed partials) — hypothesis `h_clairaut`
2. The variational equation — hypothesis `h_variational`
3. The algebraic identity ω(DX_H·u, v) + ω(u, DX_H·v) = 0 — proven in `hamiltonian_skew_symmetric`

The proof shows d/dt ω(Dϕ^t·u, Dϕ^t·v) = 0, so the form is constant in time,
equal to its value at t=0 which is ω(u,v). -/
theorem liouville_theorem {n : ℕ} (H : PhaseSpace n → ℝ) (ϕ : ℝ → PhaseSpace n → PhaseSpace n)
    (h_flow : IsFlow (HamiltonianVectorField H) ϕ)
    (h_lipschitz : ∃ K : ℝ, K ≥ 0 ∧ ∀ x y, ‖HamiltonianVectorField H x - HamiltonianVectorField H y‖ ≤ K * ‖x - y‖)
    (h_clairaut : ∀ x i j, hessianQQ H x i j = hessianQQ H x j i
                          ∧ hessianPP H x i j = hessianPP H x j i
                          ∧ hessianQP H x i j = hessianPQ H x j i)
    (h_variational : ∀ t x v, HasDerivAt (fun s => fderiv ℝ (ϕ s) x v)
        (DX_H_action H (ϕ t x) (fderiv ℝ (ϕ t) x v)) t) :
  ∀ t, IsSymplecticMap (ϕ t) := by
  intro t x u v
  -- h(s) = ω(Dϕ^s(x)·u, Dϕ^s(x)·v)
  let h := fun s : ℝ => ω (fderiv ℝ (ϕ s) x u) (fderiv ℝ (ϕ s) x v)
  -- Step 1: h(0) = ω(u, v) since ϕ^0 = id
  have h0 : h 0 = ω u v := by
    have h_id : fderiv ℝ (ϕ 0) x = ContinuousLinearMap.id ℝ (PhaseSpace n) := by
      have hϕ0 : ϕ 0 = id := by funext y; exact h_flow.1 y
      rw [hϕ0]
      exact fderiv_id
    simp [h, h_id]
  -- Step 2: h'(s) = 0 for all s (variational equation + skew-symmetry)
  have h_deriv0 : ∀ s, HasDerivAt h 0 s := by
    intro s
    let a := fun (σ : ℝ) => fderiv ℝ (ϕ σ) x u
    let b := fun (σ : ℝ) => fderiv ℝ (ϕ σ) x v
    let a' := DX_H_action H (ϕ s x) (fderiv ℝ (ϕ s) x u)
    let b' := DX_H_action H (ϕ s x) (fderiv ℝ (ϕ s) x v)
    have ha : HasDerivAt a a' s := h_variational s x u
    have hb : HasDerivAt b b' s := h_variational s x v
    have h_ω : HasDerivAt (fun σ => ω (a σ) (b σ)) (ω a' (b s) + ω (a s) b') s :=
      deriv_of_bilinear_ω a b a' b' s ha hb
    have h_key : ω a' (b s) + ω (a s) b' = 0 := by
      exact hamiltonian_skew_symmetric H (ϕ s x) (a s) (b s) (h_clairaut (ϕ s x))
    simp [h] at h_ω ⊢
    rw [h_key] at h_ω
    simpa using h_ω
  -- Step 3: h is constant (zero derivative everywhere) via mean value theorem
  have h_const : ∀ s, h s = h 0 := by
    intro s
    by_cases h_eq : s = 0
    · rw [h_eq]
    · let g := fun τ => h τ - h 0
      have hg0 : g 0 = 0 := by simp [g]
      have hg_deriv : ∀ τ, HasDerivAt g 0 τ := by
        intro τ
        have hh := h_deriv0 τ
        simpa [g] using HasDerivAt.sub hh (hasDerivAt_const τ (h 0))
      have hdiff : Differentiable ℝ g := fun τ => (hg_deriv τ).differentiableAt
      have hcont := hdiff.continuous
      by_cases hs : s > 0
      · have hcont_on : ContinuousOn g (Set.Icc 0 s) := hcont.continuousOn
        have hder : ∀ τ ∈ Set.Ioo 0 s, HasDerivAt g 0 τ := fun τ _ => hg_deriv τ
        have hmvt : ∃ c ∈ Set.Ioo 0 s, g s - g 0 = 0 * (s - 0) := by
          apply exists_hasDerivAt_eq_slope g (fun _ => 0) 0 s hs hcont_on
          intro τ hτ; exact hder τ hτ
        rcases hmvt with ⟨c, _, heq⟩
        simp at heq
        linarith [heq, hg0]
      · have hs' : s < 0 := by
          have hne : s ≠ 0 := h_eq
          have hle : s ≤ 0 := le_of_not_gt hs
          exact lt_of_le_of_ne hle (Ne.symm hne)
        have hcont_on : ContinuousOn g (Set.Icc s 0) := hcont.continuousOn
        have hder : ∀ τ ∈ Set.Ioo s 0, HasDerivAt g 0 τ := fun τ _ => hg_deriv τ
        have hmvt : ∃ c ∈ Set.Ioo s 0, g 0 - g s = 0 * (0 - s) := by
          apply exists_hasDerivAt_eq_slope g (fun _ => 0) s 0 hs' hcont_on
          intro τ hτ; exact hder τ hτ
        rcases hmvt with ⟨c, _, heq⟩
        simp at heq
        linarith [heq, hg0]
  -- Step 4: Conclude h(t) = h(0) = ω(u, v)
  rw [h_const t, h0]
  rfl

end Semantics.AnalysisFoundations
