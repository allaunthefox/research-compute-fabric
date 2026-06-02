import Mathlib

/- Original: di=1 |i⟩⟨i|A + |d⟩⟨d|A , trHB (|V0 ⟩⟩⟨⟨V0 |) = P′ (1 − ε2 ) di=1 |i⟩⟨i|A ,  if d is odd , if d is even  so trHB (|V0 ⟩⟩⟨⟨V0 |) ≤ IA -/
theorem eq_2fd8a5739608720e (A : ℕ) (IA : ℕ) (P : ℕ) (V0 : ℕ) (d : ℕ) (di : ℕ) (even : ℕ) (i : ℕ) (is : ℕ) (odd : ℕ) (so : ℕ) (trHB : ℕ) (ε2 : ℕ) : di=1 |i⟩⟨i|A + |d⟩⟨d|A ∧ trHB (|V0 ⟩⟩⟨⟨V0 |) = P′ (1 - ε2 ) di=1 |i⟩⟨i|A ∧ if d is odd ∧ if d is even so trHB (|V0 ⟩⟩⟨⟨V0 |) ≤ IA := by
  omega

