import Std
import Mathlib.Data.Nat.Sqrt

namespace LemmaTest

theorem test_sub_sub (a b c : Nat) : a - b - c = a - (b + c) := by rw [Nat.sub_sub]

theorem test_sub_add_cancel (a b : Nat) (h : a ≤ b) : b - a + a = b := by apply Nat.sub_add_cancel; exact h

theorem test_add_sub_cancel_left (a b : Nat) : a + b - a = b := by rw [Nat.add_sub_cancel_left]

theorem test_add_sub_cancel_right (a b : Nat) : a + b - b = a := by rw [Nat.add_sub_cancel_right]

theorem test_add_sub_add_left (a b c : Nat) : a + b - (a + c) = b - c := by rw [Nat.add_sub_add_left]

theorem test_succ_le (a b : Nat) (h : a < b) : a + 1 ≤ b := by apply Nat.succ_le_of_lt; exact h

theorem test_sub_le_sub_right (a b : Nat) (h : a ≤ b) (c : Nat) : a - c ≤ b - c := by apply Nat.sub_le_sub_right; exact h

theorem test_le_add_right (a b : Nat) : a ≤ a + b := by apply Nat.le_add_right

theorem test_lt_succ (a : Nat) : a < a + 1 := by apply Nat.lt_succ_self

theorem test_lt_succ_iff (a b : Nat) : a < Nat.succ b ↔ a ≤ b := by rw [Nat.lt_succ_iff]

theorem test_two_mul (a : Nat) : 2 * a = a + a := by rw [Nat.two_mul]

theorem test_mul_add (a b c : Nat) : a * (b + c) = a * b + a * c := by rw [Nat.mul_add]

theorem test_add_mul (a b c : Nat) : (a + b) * c = a * c + b * c := by rw [Nat.add_mul]

theorem test_zero_le (a : Nat) : 0 ≤ a := by apply Nat.zero_le

theorem test_le_antisymm (a b : Nat) (h1 : a ≤ b) (h2 : b ≤ a) : a = b := by apply Nat.le_antisymm; exact h1; exact h2

theorem test_eq_sqrt (a n : Nat) : a = Nat.sqrt n ↔ a * a ≤ n ∧ n < (a + 1) * (a + 1) := by rw [Nat.eq_sqrt]

theorem test_lt_of_le_of_lt (a b c : Nat) (h1 : a ≤ b) (h2 : b < c) : a < c := by apply Nat.lt_of_le_of_lt h1 h2

theorem test_lt_of_lt_of_eq (a b c : Nat) (h1 : a < b) (h2 : b = c) : a < c := by apply Nat.lt_of_lt_of_eq h1 h2

end LemmaTest
