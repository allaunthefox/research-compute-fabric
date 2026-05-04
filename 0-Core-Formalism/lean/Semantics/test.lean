import Semantics.FixedPoint
open Semantics

namespace Semantics.Q16_16

theorem test_add_one_omega_ge_one (omega : Q16_16) (h_omega : omega.toInt ≥ 0) :
    (add one omega).toInt ≥ one.toInt := by
  have h_one_toInt : one.toInt = 65536 := rfl
  unfold add
  rw [h_one_toInt]
  have h_nonneg : 0 ≤ 65536 + omega.toInt := by omega
  by_cases h_bound : 65536 + omega.toInt ≤ 0x7FFFFFFF
  · rw [ofRaw_toInt_eq _ h_nonneg h_bound]
    omega
  · -- saturates
    push_neg at h_bound
    have : ofRaw (65536 + omega.toInt) = maxVal := by
      unfold ofRaw
      split
      · rfl
      · omega
    rw [this]
    have : maxVal.toInt = 2147483647 := rfl
    rw [this]
    omega
end Semantics.Q16_16
