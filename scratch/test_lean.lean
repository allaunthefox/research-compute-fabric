theorem test_reflexive (q : Nat) : q = q := by
  native_decide

theorem test_arithmetic : 2 + 2 = 4 := by
  native_decide

theorem test_identity (a : Nat) : a + 0 = a := by
  native_decide
