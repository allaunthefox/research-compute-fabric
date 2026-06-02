import Mathlib

/- Original: ux = − ux − P ∗ u + 2 2     1 2 1 2 1 2 2 2 = − ux − P+ ∗ u + ux + h(u) − P− ∗ u + ux + h(u) + u2 2 2 2 + h(u) − λ(t)ux -/
theorem eq_7ba3cc2c96fdf78f (P : ℕ) (h : ℕ) (t : ℕ) (u : ℕ) (u2 : ℕ) (ux : ℕ) (λ : ℕ) : ux = - ux - P * u + 2 2     1 2 1 2 1 2 2 2 = - ux - P+ * u + ux + h(u) - P- * u + ux + h(u) + u2 2 2 2 + h(u) - λ(t)ux := by
  omega

