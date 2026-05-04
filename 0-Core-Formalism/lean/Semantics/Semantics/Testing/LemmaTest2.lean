import Std
import Mathlib.Data.Nat.Sqrt

namespace LemmaTest2

lemma expand_k1_sq (k : Nat) : (k + 1) * (k + 1) = k * k + 2 * k + 1 := by
  rw [Nat.add_mul]
  rw [Nat.mul_add]
  simp [Nat.mul_one, Nat.one_mul]
  rw [Nat.add_assoc]
  rw [←Nat.add_assoc k k 1]
  rw [show k + k = 2 * k by rw [Nat.two_mul]]
  rw [Nat.add_assoc]

end LemmaTest2
