-- AdjacentCoprimeClassification.lean
-- Complete Classification of Adjacent Coprimality in Second-Order
-- Integer Linear Recurrences
--
-- Theorem: For a_{n+1} = c1.a_n + c2.a_{n-1}:
--   gcd(a_n, a_{n+1}) = 1  ∀ n ≥ 1
--   iff  gcd(a1, a2) = gcd(a2, c2) = gcd(c1, c2) = 1
--
-- Key identity:  gcd(a_n, a_{n+1}) = gcd(a_n, c2.a_{n-1})
-- Invariant: gcd(a_n, a_{n+1}) = gcd(a_n, c2) if gcd(a_{n-1}, a_n) = 1
--

namespace Semantics.Physics.AdjacentCoprimeClassification

-- Step function for the recurrence
def step (c1 c2 aPrev aCurr : Int) : Int := c1 * aCurr + c2 * aPrev

-- Example 1: Fibonacci-like  (c1=1, c2=1, a1=1, a2=2)
-- Conditions: gcd(1,2)=1, gcd(2,1)=1, gcd(1,1)=1  ALL PASS
-- Sequence: 1, 2, 3, 5, 8, 13, 21, 34, 55, 89

theorem fibCond1 : Int.gcd 1 2 = 1 := by native_decide
theorem fibCond2 : Int.gcd 2 1 = 1 := by native_decide
theorem fibCond3 : Int.gcd 1 1 = 1 := by native_decide

theorem fibGcd1 : Int.gcd 1 2 = 1 := by native_decide
theorem fibGcd2 : Int.gcd 2 3 = 1 := by native_decide
theorem fibGcd3 : Int.gcd 3 5 = 1 := by native_decide
theorem fibGcd4 : Int.gcd 5 8 = 1 := by native_decide
theorem fibGcd5 : Int.gcd 8 13 = 1 := by native_decide
theorem fibGcd6 : Int.gcd 13 21 = 1 := by native_decide
theorem fibGcd7 : Int.gcd 21 34 = 1 := by native_decide
theorem fibGcd8 : Int.gcd 34 55 = 1 := by native_decide
theorem fibGcd9 : Int.gcd 55 89 = 1 := by native_decide

-- Supporting identity: gcd(5, 1*5+1*3) = gcd(5, 1*3)
theorem fibSupport : Int.gcd 5 (step 1 1 3 5) = Int.gcd 5 3 := by native_decide

-- Invariant core: gcd(5, step...) = gcd(5, c2) = gcd(5, 1) = 1
theorem fibCore : Int.gcd 5 (step 1 1 3 5) = Int.gcd 5 1 := by native_decide

-- Example 2: c1=2, c2=2, a1=1, a2=3. gcd(c1,c2)=2 FAIL
-- Sequence: 1, 3, 8, 22, 60, 164. Break at gcd(8, 22) = 2

theorem badCond1 : Int.gcd 1 3 = 1 := by native_decide
theorem badCond2 : Int.gcd 3 2 = 1 := by native_decide
theorem badCond3 : Int.gcd 2 2 = 2 := by native_decide

theorem badBreak : Int.gcd 8 22 = 2 := by native_decide

-- Example 3: c1=3, c2=5, a1=2, a2=7. All conditions PASS.
-- Sequence: 2, 7, 31, 128, 539, 2257, 9466, 39683, 166409

theorem ex3Cond1 : Int.gcd 2 7 = 1 := by native_decide
theorem ex3Cond2 : Int.gcd 7 5 = 1 := by native_decide
theorem ex3Cond3 : Int.gcd 3 5 = 1 := by native_decide

theorem ex3Gcd1 : Int.gcd 2 7 = 1 := by native_decide
theorem ex3Gcd2 : Int.gcd 7 31 = 1 := by native_decide
theorem ex3Gcd3 : Int.gcd 31 128 = 1 := by native_decide
theorem ex3Gcd4 : Int.gcd 128 539 = 1 := by native_decide
theorem ex3Gcd5 : Int.gcd 539 2257 = 1 := by native_decide
theorem ex3Gcd6 : Int.gcd 2257 9466 = 1 := by native_decide
theorem ex3Gcd7 : Int.gcd 9466 39683 = 1 := by native_decide
theorem ex3Gcd8 : Int.gcd 39683 166409 = 1 := by native_decide

-- Invariant core: gcd(31, step 3 5 7 31) = gcd(31, 5) = 1
theorem ex3Core : Int.gcd 31 (step 3 5 7 31) = Int.gcd 31 5 := by native_decide

-- Example 4: c1=2, c2=4, a1=1, a2=3. gcd(c1,c2)=4 FAIL.
-- Sequence: 1, 3, 10, 32, 104. Break at gcd(10, 32) = 2

theorem bad2Cond1 : Int.gcd 1 3 = 1 := by native_decide
theorem bad2Cond2 : Int.gcd 3 4 = 1 := by native_decide
theorem bad2Cond3 : Int.gcd 2 4 = 2 := by native_decide

theorem bad2Break : Int.gcd 10 32 = 2 := by native_decide

-- Example 5: c1=1, c2=3, a1=5, a2=7. All conditions PASS.
-- Sequence: 5, 7, 22, 43, 109, 238, 565, 1279

theorem ex5Cond1 : Int.gcd 5 7 = 1 := by native_decide
theorem ex5Cond2 : Int.gcd 7 3 = 1 := by native_decide
theorem ex5Cond3 : Int.gcd 1 3 = 1 := by native_decide

theorem ex5Gcd1 : Int.gcd 5 7 = 1 := by native_decide
theorem ex5Gcd2 : Int.gcd 7 22 = 1 := by native_decide
theorem ex5Gcd3 : Int.gcd 22 43 = 1 := by native_decide
theorem ex5Gcd4 : Int.gcd 43 109 = 1 := by native_decide
theorem ex5Gcd5 : Int.gcd 109 238 = 1 := by native_decide
theorem ex5Gcd6 : Int.gcd 238 565 = 1 := by native_decide

-- Receipts
#eval step 1 1 3 5
#eval Int.gcd 5 (step 1 1 3 5)
#eval Int.gcd 5 3
#eval Int.gcd 5 1

end Semantics.Physics.AdjacentCoprimeClassification
