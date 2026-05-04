import Std
import Mathlib.Data.Nat.Sqrt

namespace TestTactics

theorem test_ring (k : Nat) : (k + 1) * (k + 1) = k * k + 2 * k + 1 := by ring

theorem test_omega (a b : Nat) : a + b ≥ a := by omega

theorem test_native_decide : 2 + 2 = 4 := by native_decide

end TestTactics
