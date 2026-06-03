"""Failure Flexure Expansion — 50+ deliberately diverse failed/partial Lean proofs.

Covers 8 failure types: missing_rewrite, missing_assumption, arithmetic_gap,
case_split_missing, induction_incomplete, simplifier_gap, coercion_mismatch, order_gap.

Each theorem is designed to fail with the specific obstruction type.
"""

FAILURE_THEOREMS = [
    # ── Missing rewrite direction (rw needs ← or different order) ──
    ("rw_missing_dir_1", "theorem t (a b : Nat) (h : a = b) : b + 0 = a + 0 := by\n  simp"),
    ("rw_missing_dir_2", "theorem t (a b c : Nat) (h1 : a = b) (h2 : b = c) : a = c := by\n  rfl"),
    ("rw_missing_dir_3", "theorem t (a b : Nat) (h : a + b = b + a) : b + a = a + b := by\n  rfl"),
    ("rw_missing_dir_4", "theorem t (a b : Nat) (h : a = b) : a*2 = b*2 := by\n  simp"),
    ("rw_missing_dir_5", "theorem t (a b : Nat) (h : a = b) : a + 1 = b + 1 := by\n  rfl"),
    ("rw_missing_dir_6", "theorem t (a b : Nat) (h : a = b) : 0 + a = 0 + b := by\n  simp"),
    ("rw_missing_dir_7", "theorem t (a b : Nat) (h : a = b) (c : Nat) : a + c = b + c := by\n  rfl"),

    # ── Missing assumption bridge (needs exact, assumption, apply) ──
    ("missing_assume_1", "theorem t (A B : Prop) (hA : A) (hAB : A → B) : B := by\n  rfl"),
    ("missing_assume_2", "theorem t (A B C : Prop) (hA : A) (hAB : A → B) (hBC : B → C) : C := by\n  simp"),
    ("missing_assume_3", "theorem t (A B : Prop) (h : A ∧ B) : A := by\n  rfl"),
    ("missing_assume_4", "theorem t (A B : Prop) (h : A ∨ B) : A ∨ B := by\n  simp"),
    ("missing_assume_5", "theorem t (A B : Prop) (h : A → B) (hA : A) : B := by\n  rfl"),
    ("missing_assume_6", "theorem t (A B : Prop) : A → B → A := by\n  rfl"),
    ("missing_assume_7", "theorem t (P : Prop) : P → ¬¬P := by\n  rfl"),

    # ── Arithmetic gap (needs omega, linarith, nlinarith) ──
    ("arith_gap_1", "theorem t (a b : Nat) (h : a ≤ b) : a + 1 ≤ b + 1 := by\n  rfl"),
    ("arith_gap_2", "theorem t (a b c : Nat) (h1 : a ≤ b) (h2 : b ≤ c) : a ≤ c := by\n  simp"),
    ("arith_gap_3", "theorem t (a b : Nat) (h : a + b = b + a) : a = b := by\n  rfl"),
    ("arith_gap_4", "theorem t (a b c : Nat) : a + b + c = a + c + b := by\n  simp"),
    ("arith_gap_5", "theorem t (a b : Nat) : a * (b + 1) = a * b + a := by\n  simp"),
    ("arith_gap_6", "theorem t (x : Nat) (h : x > 0) : x - 1 < x := by\n  simp"),
    ("arith_gap_7", "theorem t (a b : Nat) : a + b = b + a := by\n  omega"),
    ("arith_gap_8", "theorem t (a b : Nat) : (a + b) * (a + b) = a*a + 2*a*b + b*b := by\n  simp"),
    ("arith_gap_9", "theorem t (x : Nat) : x + x = 2 * x := by\n  simp"),
    ("arith_gap_10", "theorem t (n : Nat) : n + 0 = n := by\n  rfl"),

    # ── Case split missing (needs cases, by_cases, constructor) ──
    ("case_split_1", "theorem t (A B : Prop) (h : A ∨ B) : B ∨ A := by\n  simp"),
    ("case_split_2", "theorem t (A B C : Prop) (h : A ∧ B) (h2 : A → C) : C := by\n  simp"),
    ("case_split_3", "theorem t (A B : Prop) (hA : A) (hB : B) : A ∧ B := by\n  rfl"),
    ("case_split_4", "theorem t (A B : Prop) (h : A ∨ B) : A ∨ B := by\n  rfl"),
    ("case_split_5", "theorem t (A B : Prop) (h : A → B) : A ∨ B → B := by\n  simp"),
    ("case_split_6", "theorem t (A B : Prop) (hA : A) (hB : B) : A ∧ B := by\n  simp"),
    ("case_split_7", "theorem t (A B : Prop) (h : A ∧ B) : A := by\n  simp"),
    ("case_split_8", "theorem t (A : Prop) : A → A := by\n  rfl"),

    # ── Induction incomplete (missing induction case handling) ──
    ("induction_gap_1", "theorem t (n : Nat) : n + 0 = n := by\n  simp"),
    ("induction_gap_2", "theorem t (n m : Nat) : n + m.succ = (n + m).succ := by\n  simp"),
    ("induction_gap_3", "theorem t (n : Nat) : n * 0 = 0 := by\n  simp"),
    ("induction_gap_4", "theorem t (m n : Nat) : m + n = n + m := by\n  omega"),
    ("induction_gap_5", "theorem t (n : Nat) : 0 + n = n := by\n  simp"),
    ("induction_gap_6", "theorem t (n : Nat) : n + 0 = n := by\n  rfl"),
    ("induction_gap_7", "theorem t (n : Nat) : n ≤ n := by\n  simp"),
    ("induction_gap_8", "theorem t (n : Nat) : n - n = 0 := by\n  simp"),
    ("induction_gap_9", "theorem t (n : Nat) : n * 1 = n := by\n  simp"),
    ("induction_gap_10", "theorem t (n m : Nat) : n + m = m + n := by\n  simp"),

    # ── Simplifier almost works (needs extra simp lemma) ──
    ("simplifier_gap_1", "theorem t (l : List Nat) : l.reverse.reverse = l := by\n  simp"),
    ("simplifier_gap_2", "theorem t (l : List Nat) : [] ++ l = l := by\n  simp"),
    ("simplifier_gap_3", "theorem t (s : Set Nat) : s ∪ s = s := by\n  simp"),
    ("simplifier_gap_4", "theorem t (s : Set Nat) : s ∩ s = s := by\n  simp"),
    ("simplifier_gap_5", "theorem t (n : Nat) : n + 0 = n := by\n  simp"),
    ("simplifier_gap_6", "theorem t (a b : Nat) : a + b = b + a := by\n  simp"),

    # ── Coercion / type mismatch ──
    ("coercion_gap_1", "theorem t (n : Nat) : (n : Nat) = (n : Int) := by\n  rfl"),
    ("coercion_gap_2", "theorem t (n : Nat) : n = (n : Nat) := by\n  rfl"),
    ("coercion_gap_3", "theorem t (n : Nat) (m : Nat) : n + m = m + n := by\n  omega"),
    ("coercion_gap_4", "theorem t (x : Int) : (x : Nat) = (x : Int) := by\n  rfl"),

    # ── Order / inequality gap ──
    ("order_gap_1", "theorem t (a b : Nat) (h : a ≤ b) : a * 2 ≤ b * 2 := by\n  simp"),
    ("order_gap_2", "theorem t (a b c : Nat) (h1 : a ≤ b) (h2 : b ≤ c) : a ≤ c := by\n  rfl"),
    ("order_gap_3", "theorem t (a b : Nat) (h : a ≤ b) : a + 1 ≤ b + 1 := by\n  simp"),
    ("order_gap_4", "theorem t (a b : Nat) : a ≤ a := by\n  rfl"),
    ("order_gap_5", "theorem t (a b : Nat) (h : a ≤ b) (h2 : b ≤ a) : a = b := by\n  simp"),
    ("order_gap_6", "theorem t (a b : Nat) (h : a ≤ b) : 0 ≤ b - a := by\n  simp"),
    ("order_gap_7", "theorem t (a b : Nat) (h : a < b) : a + 1 ≤ b := by\n  simp"),
    ("order_gap_8", "theorem t (a b : Nat) (h : a ≤ b) : a ≤ b + 1 := by\n  simp"),
]
