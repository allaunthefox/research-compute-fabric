"""Combined theorem set: 42 original + 24 v2 multi-tactic = 66 unique theorems."""

COMBINED_THEOREMS = [
    # ── Original 42 from pist_canary_batch.py ──
    ("rfl_one", "theorem t (n : Nat) : n = n := by rfl"),
    ("rfl_add", "theorem t (n : Nat) : n + 0 = n := by rfl"),
    ("rfl_succ", "theorem t (n : Nat) : n.succ = n.succ := by rfl"),
    ("simp_add_zero", "theorem t (n : Nat) : n + 0 = n := by simp"),
    ("simp_mul_one", "theorem t (n : Nat) : n * 1 = n := by simp"),
    ("simp_add_comm", "theorem t (a b : Nat) : a + b = b + a := by simp [add_comm]"),
    ("simp_add_assoc", "theorem t (a b c : Nat) : (a + b) + c = a + (b + c) := by simp [add_assoc]"),
    ("simp_mul_comm", "theorem t (a b : Nat) : a * b = b * a := by simp [mul_comm]"),
    ("omega_add", "theorem t (a b c : Nat) : a + b + c = a + c + b := by omega"),
    ("omega_mul", "theorem t (a b : Nat) : (a + b) * 2 = a*2 + b*2 := by omega"),
    ("omega_ineq", "theorem t (a b : Nat) (h : a ≤ b) : a + 1 ≤ b + 1 := by omega"),
    ("omega_mod", "theorem t (a : Nat) : a % 2 < 2 := by omega"),
    ("omega_double", "theorem t (n : Nat) : n + n = 2 * n := by omega"),
    ("ring_sq", "theorem t (x y : Nat) : (x + y)^2 = x^2 + 2*x*y + y^2 := by nlinarith"),
    ("ring_cube", "theorem t (x : Nat) : (x+1)^3 = x^3 + 3*x^2 + 3*x + 1 := by nlinarith"),
    ("ring_expand", "theorem t (a b : Nat) : (a + b) * (a - b) = a^2 - b^2 := by omega"),
    ("induct_add_zero", "theorem t (n : Nat) : n + 0 = n := by induction n with k IH; rfl; simp [add_succ, IH]"),
    ("induct_add_succ", "theorem t (n m : Nat) : n + m.succ = (n + m).succ := by induction n with k IH; rfl; simp [add_succ, IH]"),
    ("induct_mul", "theorem t (n m : Nat) : n * m = m * n := by\n  induction n with; simp; simp [mul_add, IH, add_comm, add_left_comm, add_assoc]"),
    ("rw_add_comm", "theorem t (a b : Nat) : a + b = b + a := by rw [add_comm a b]"),
    ("rw_mul_comm", "theorem t (a b : Nat) : a * b = b * a := by rw [mul_comm]"),
    ("rw_add_assoc", "theorem t (a b c : Nat) : a + b + c = c + b + a := by\n  rw [add_comm a b, add_comm (a+b) c, add_comm b a]; rfl"),
    ("with_import_list", "import Mathlib.Data.List.Basic\ntheorem t (l : List Nat) : l.reverse.reverse = l := by simp"),
    ("with_import_nat", "import Mathlib.Data.Nat.Basic\ntheorem t (a b : Nat) : a.gcd b = b.gcd a := Nat.gcd_comm a b"),
    ("with_import_int", "import Mathlib.Data.Int.Basic\ntheorem t (a b : ℤ) : a + b = b + a := by omega"),
    ("with_import_set", "import Mathlib.Data.Set.Basic\ntheorem t (s : Set Nat) : s ∪ s = s := Set.union_self s"),
    ("algebra_id", "theorem t (x : Nat) : x * 1 = x := by simp"),
    ("algebra_distrib", "theorem t (a b c : Nat) : a * (b + c) = a * b + a * c := by omega"),
    ("algebra_sq_diff", "theorem t (x y : Nat) : x^2 - y^2 = (x - y) * (x + y) := by omega"),
    ("logic_and", "theorem t (A B : Prop) : A ∧ B → A := by intro h; exact h.1"),
    ("logic_or", "theorem t (A B : Prop) : A ∨ B → B ∨ A := by intro h; cases h; right; exact h; left; exact h"),
    ("logic_not_not", "theorem t (P : Prop) : P → ¬¬P := by intro hp hnp; exact hnp hp"),
    ("logic_impl_trans", "theorem t (A B C : Prop) : (A → B) → (B → C) → (A → C) := by intro h1 h2 ha; exact h2 (h1 ha)"),
    ("order_refl", "theorem t (a : Nat) : a ≤ a := Nat.le_refl a"),
    ("order_trans", "theorem t (a b c : Nat) (h1 : a ≤ b) (h2 : b ≤ c) : a ≤ c := Nat.le_trans h1 h2"),
    ("order_antisymm", "theorem t (a b : Nat) (h1 : a ≤ b) (h2 : b ≤ a) : a = b := Nat.le_antisymm h1 h2"),
    ("expect_fail_type_mismatch", "theorem t : Nat → String := λ n => n"),
    ("expect_fail_unsat", "theorem t (x : Nat) : x < x := by omega"),
    ("expect_fail_axiom", "theorem t : 1 = 0 := by native_decide"),
    ("expect_fail_timeout_like", "theorem t (a b : Nat) : a^10 + b^10 = (a+b)^10 := by nlinarith"),
    ("complex_fib", "def fib : Nat → Nat | 0 => 0 | 1 => 1 | n+2 => fib (n+1) + fib n\ntheorem t (n : Nat) : fib (n+2) = fib (n+1) + fib n := by rfl"),
    ("complex_sum", "theorem t (n : Nat) : ∑ k in Finset.range n, k = n*(n-1)/2 := by sorry"),

    # ── V2 multi-tactic theorems (from trace_canary_theorems.py) ──
    ("rw_chain_eq", "theorem rw_chain_eq (a b c : Nat) (h1 : a = b) (h2 : b = c) : a = c := by\n  rw [h1]\n  rw [h2]"),
    ("rw_chain_mixed", "theorem rw_chain_mixed (a b : Nat) (h : a = b) : a + 0 = b := by\n  rw [h]\n  simp"),
    ("rw_chain_3step", "theorem rw_chain_3step (a b c d : Nat) (h1 : a = b) (h2 : b = c) (h3 : c = d) : a = d := by\n  rw [h1]\n  rw [h2]\n  rw [h3]"),
    ("rw_then_omega", "theorem rw_then_omega (a b c : Nat) (h : a = b + c) : a * 2 = (b + c) * 2 := by\n  rw [h]\n  omega"),
    ("cases_or_swap", "theorem cases_or_swap (A B : Prop) (h : A ∨ B) : B ∨ A := by\n  cases h\n  · right; exact h\n  · left; exact h"),
    ("cases_and_elim", "theorem cases_and_elim (A B C : Prop) (h : A ∧ B) (h2 : A → C) : C := by\n  cases h\n  apply h2\n  assumption"),
    ("constructor_example", "theorem constructor_example (A B : Prop) (hA : A) (hB : B) : A ∧ B := by\n  constructor\n  · exact hA\n  · exact hB"),
    ("apply_chain", "theorem apply_chain (A B C : Prop) (h1 : A → B) (h2 : B → C) (hA : A) : C := by\n  apply h2\n  apply h1\n  exact hA"),
    ("omega_chain_ineq", "theorem omega_chain_ineq (a b c : Nat) (h1 : a ≤ b) (h2 : b ≤ c) : a ≤ c := by\n  omega"),
    ("omega_reorder_sum", "theorem omega_reorder_sum (a b c : Nat) : a + b + c = a + c + b := by\n  omega"),
    ("omega_distrib", "theorem omega_distrib (a b c : Nat) : a * (b + c) = a * b + a * c := by\n  omega"),
    ("omega_chain_unsat", "theorem omega_chain_unsat (x : Nat) : x < x := by\n  omega"),
    ("induct_add_zero_v2", "theorem induct_add_zero (n : Nat) : n + 0 = n := by\n  induction n with\n  | zero => simp\n  | succ n ih => simp [add_succ, ih]"),
    ("induct_add_succ_v2", "theorem induct_add_succ (n m : Nat) : n + m.succ = (n + m).succ := by\n  induction n with\n  | zero => simp\n  | succ k ih => simp [add_succ, ih]"),
    ("induct_mul_zero", "theorem induct_mul_zero (n : Nat) : n * 0 = 0 := by\n  induction n with\n  | zero => simp\n  | succ k ih => simp [mul_add, add_comm, ih]"),
    ("induct_factorial", "def fac : Nat → Nat\n  | 0 => 1\n  | n+1 => fac n * (n+1)\ntheorem induct_fact (n : Nat) : fac 0 = 1 := by\n  simp [fac]"),
    ("intro_all", "theorem intro_all (A B C : Prop) : A → B → C → A := by\n  intro hA\n  intro hB\n  intro hC\n  exact hA"),
    ("intro_apply", "theorem intro_apply (A B : Prop) : (A → B) → A → B := by\n  intro h\n  intro hA\n  apply h\n  exact hA"),
    ("have_chain", "theorem have_chain (A B C : Prop) (hAB : A → B) (hBC : B → C) (hA : A) : C := by\n  have hB : B := hAB hA\n  have hC : C := hBC hB\n  exact hC"),
    ("calc_chain", "theorem calc_chain (a b : Nat) : (a + b) * (a + b) = a*a + 2*a*b + b*b := by\n  ring\n  omega"),
    ("fail_type_mismatch", "theorem fail_type_mismatch (n : Nat) : n = (\"hello\" : String) := by\n  rfl"),
    ("fail_missing_lemma", "theorem fail_missing_lemma (n : Nat) : n = n + 0 := by\n  rw [imaginary_lemma]"),
    ("fail_unsat", "theorem fail_unsat (x : Nat) (h : x > 0) : x = 0 := by\n  omega"),
    ("fail_bad_coercion", "theorem fail_bad_coercion (n : Float) : (n : Nat) = (n : Int) := by\n  rfl"),
]

# Remove duplicates while preserving order
seen = set()
UNIQUE_THEOREMS = []
for name, code in COMBINED_THEOREMS:
    key = name.replace("_v2", "")
    if key not in seen:
        seen.add(key)
        UNIQUE_THEOREMS.append({"name": name, "code": code, "domain": "combined"})
