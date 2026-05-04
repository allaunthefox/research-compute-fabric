import Mathlib.Tactic.Omega

theorem test (omega : Int) (h_omega : omega ≥ 0) (h_bound : 65536 + omega ≤ 2147483647) :
  (if (65536 + omega).toNat % 4294967296 < 2147483648 then Int.ofNat ((65536 + omega).toNat % 4294967296) else Int.ofNat ((65536 + omega).toNat % 4294967296) - 4294967296) ≥ 65536 := by
  omega
