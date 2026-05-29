/-
TestCopyIf.lean — Tests for the copy_if tactic
-/
import Semantics.CopyIfTactic

namespace Semantics.TestCopyIf
open Semantics.CopyIfTactic

-- Trivial: rfl (zero delta)
theorem test_rfl : 1 = 1 := by copy_if
theorem test_rfl2 : True := by copy_if
theorem test_rfl3 : ∀ x : Nat, x = x := by intro x; copy_if

-- Trivial: decide (decidable)
theorem test_decide : 1 + 1 = 2 := by copy_if
theorem test_decide2 : true = true := by copy_if
theorem test_decide3 : 3 > 2 := by copy_if

-- Trivial: omega (linear arithmetic)
theorem test_omega (x : Nat) : x + 0 = x := by copy_if
theorem test_omega2 (x : Int) : x - x = 0 := by copy_if
theorem test_omega3 (x y : Nat) : x + y = y + x := by copy_if

-- Trivial: norm_num (numeric)
theorem test_norm_num : (2 : Nat) + 2 = 4 := by copy_if
theorem test_norm_num2 : (3 : Int) * 4 = 12 := by copy_if

-- Non-trivial: should fail with "non-trivial goal"
-- theorem test_non_trivial (x : Nat) : x * 0 = 0 := by copy_if

-- copy_if? variant: shows which closer worked
theorem test_which_rfl : 1 = 1 := by copy_if?
theorem test_which_decide : 3 > 2 := by copy_if?
theorem test_which_omega (x : Nat) : x + 0 = x := by copy_if?

end Semantics.TestCopyIf
