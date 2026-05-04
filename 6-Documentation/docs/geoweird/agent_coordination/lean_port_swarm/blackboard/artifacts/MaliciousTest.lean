-- MALICIOUS INTERSECTION TEST
-- Purpose: Attempt to violate AGENTS.md rules to test enforcement
-- Expected: Build should FAIL with clear errors

import Semantics.Substrate
import Semantics.Decomposition

namespace malicious_test

-- ATTACK 1: Wildcard pattern match (violates §1.5, §3)
def badStackConsumption (op : OpCode) : Nat × Nat :=
  match op with
  | OpCode.nop => (0, 0)
  | OpCode.pop => (1, 0)
  | _ => (999, 999)  -- WILDCARD: Should be rejected

-- ATTACK 2: Float in core logic (violates §1.4)
def badCostFunction (x : Float) (y : Float) : UInt32 :=
  let result := (x + y) * 0.5  -- Float arithmetic in core
  (result * 65536.0).toUInt32

-- ATTACK 3: Partial function (violates §1.5)
partial def badRecursive (n : Nat) : Nat :=
  if n = 0 then 0
  else badRecursive (n - 1) + 1

-- ATTACK 4: Sorry in proof (violates §1.6)
theorem badTheorem (x : Nat) : x + 0 = x := by
  sorry  -- Unproven theorem

-- ATTACK 5: Tautological proof (structural smell)
theorem tautology (x : Nat) : x = x := by
  rfl  -- This is fine, but let's make a bad one
theorem badProof (x : Nat) : x + 1 = x + 2 := by
  simp  -- This should fail

-- ATTACK 6: Open string parsing for decisions (violates §1.5)
def badDecisionParser (s : String) : Bool :=
  if s = "allowed" then true
  else if s = "prohibited" then false
  else s.contains "maybe"  -- Open string matching!

-- ATTACK 7: Snake_case naming (violates §2)
structure bad_snake_case_struct where
  snake_field : Nat

def bad_snake_function (bad_param : Nat) : Nat :=
  bad_param + 1

-- ATTACK 8: Missing totality proof
def noTotalityProof (op : OpCode) : UInt8 :=
  OpCode.toU8 op  -- No corresponding theorem

end malicious_test
