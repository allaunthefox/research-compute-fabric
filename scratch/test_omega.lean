import Mathlib.Tactic

theorem test_reflexive : ∀ (q : Nat), q = q := by
  omega

theorem test_identity : ∀ (a : Nat), a + 0 = a := by
  omega

theorem test_arithmetic : 2 + 2 = 4 := by
  omega
