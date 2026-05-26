CANARY_THEOREMS = [
    # ── 1. rewrite chains (each step necessary) ──
    {
        "name": "rw_chain_eq",
        "code": 'theorem rw_chain_eq (a b c : Nat) (h1 : a = b) (h2 : b = c) : a = c := by\n  rw [h1]\n  rw [h2]',
        "domain": "equality", "proof_method": "rewrite", "joint": "equality_chaining_2step",
        "obstruction": None, "rrc_shape": "CadForceProbeReceipt",
    },
    {
        "name": "rw_chain_mixed",
        "code": 'theorem rw_chain_mixed (a b : Nat) (h : a = b) : a + 0 = b := by\n  rw [h]\n  simp',
        "domain": "arithmetic", "proof_method": "rewrite", "joint": "rw_then_simp",
        "obstruction": None, "rrc_shape": "CadForceProbeReceipt",
    },
    {
        "name": "rw_chain_3step",
        "code": 'theorem rw_chain_3step (a b c d : Nat) (h1 : a = b) (h2 : b = c) (h3 : c = d) : a = d := by\n  rw [h1]\n  rw [h2]\n  rw [h3]',
        "domain": "equality", "proof_method": "rewrite", "joint": "equality_chaining_3step",
        "obstruction": None, "rrc_shape": "CadForceProbeReceipt",
    },
    {
        "name": "rw_then_omega",
        "code": 'theorem rw_then_omega (a b c : Nat) (h : a = b + c) : a * 2 = (b + c) * 2 := by\n  rw [h]\n  omega',
        "domain": "arithmetic", "proof_method": "rewrite", "joint": "rw_then_arithmetic",
        "obstruction": None, "rrc_shape": "CadForceProbeReceipt",
    },

    # ── 2. case analysis chains ──
    {
        "name": "cases_or_swap",
        "code": 'theorem cases_or_swap (A B : Prop) (h : A ∨ B) : B ∨ A := by\n  cases h\n  · right; exact h\n  · left; exact h',
        "domain": "logic", "proof_method": "cases", "joint": "disjunction_swap",
        "obstruction": None, "rrc_shape": "LogogramProjection",
    },
    {
        "name": "cases_and_elim",
        "code": 'theorem cases_and_elim (A B C : Prop) (h : A ∧ B) (h2 : A → C) : C := by\n  cases h\n  apply h2\n  assumption',
        "domain": "logic", "proof_method": "cases", "joint": "conjunction_elim_then_apply",
        "obstruction": None, "rrc_shape": "LogogramProjection",
    },
    {
        "name": "constructor_example",
        "code": 'theorem constructor_example (A B : Prop) (hA : A) (hB : B) : A ∧ B := by\n  constructor\n  · exact hA\n  · exact hB',
        "domain": "logic", "proof_method": "constructor", "joint": "conjunction_intro",
        "obstruction": None, "rrc_shape": "LogogramProjection",
    },
    {
        "name": "apply_chain",
        "code": 'theorem apply_chain (A B C : Prop) (h1 : A → B) (h2 : B → C) (hA : A) : C := by\n  apply h2\n  apply h1\n  exact hA',
        "domain": "logic", "proof_method": "apply", "joint": "implication_chaining",
        "obstruction": None, "rrc_shape": "LogogramProjection",
    },

    # ── 3. omega with multiple constraints ──
    {
        "name": "omega_chain_ineq",
        "code": 'theorem omega_chain_ineq (a b c : Nat) (h1 : a ≤ b) (h2 : b ≤ c) : a ≤ c := by\n  omega',
        "domain": "order", "proof_method": "omega", "joint": "transitivity_closure",
        "obstruction": None, "rrc_shape": "SignalShapedRouteCompiler",
    },
    {
        "name": "omega_reorder_sum",
        "code": 'theorem omega_reorder_sum (a b c : Nat) : a + b + c = a + c + b := by\n  omega',
        "domain": "arithmetic", "proof_method": "omega", "joint": "reorder_summands",
        "obstruction": None, "rrc_shape": "SignalShapedRouteCompiler",
    },
    {
        "name": "omega_distrib",
        "code": 'theorem omega_distrib (a b c : Nat) : a * (b + c) = a * b + a * c := by\n  omega',
        "domain": "algebra", "proof_method": "omega", "joint": "distributivity",
        "obstruction": None, "rrc_shape": "SignalShapedRouteCompiler",
    },
    {
        "name": "omega_chain_unsat",
        "code": 'theorem omega_chain_unsat (x : Nat) : x < x := by\n  omega',
        "domain": "order", "proof_method": "omega", "joint": "unsatisfiable_linear",
        "obstruction": "unsatisfiable_goal", "rrc_shape": "HoldForUnlawfulOrUnderspecifiedShape",
    },

    # ── 4. induction chains ──
    {
        "name": "induct_add_zero",
        "code": 'theorem induct_add_zero (n : Nat) : n + 0 = n := by\n  induction n with\n  | zero => simp\n  | succ n ih => simp [add_succ, ih]',
        "domain": "arithmetic", "proof_method": "induction", "joint": "inductive_proof",
        "obstruction": None, "rrc_shape": "ProjectableGeometryTopology",
    },
    {
        "name": "induct_add_succ",
        "code": 'theorem induct_add_succ (n m : Nat) : n + m.succ = (n + m).succ := by\n  induction n with\n  | zero => simp\n  | succ k ih => simp [add_succ, ih]',
        "domain": "arithmetic", "proof_method": "induction", "joint": "inductive_succ",
        "obstruction": None, "rrc_shape": "ProjectableGeometryTopology",
    },
    {
        "name": "induct_mul_zero",
        "code": 'theorem induct_mul_zero (n : Nat) : n * 0 = 0 := by\n  induction n with\n  | zero => simp\n  | succ k ih => simp [mul_add, add_comm, ih]',
        "domain": "arithmetic", "proof_method": "induction", "joint": "inductive_mul",
        "obstruction": None, "rrc_shape": "ProjectableGeometryTopology",
    },
    {
        "name": "induct_factorial",
        "code": 'def fac : Nat → Nat\n  | 0 => 1\n  | n+1 => fac n * (n+1)\ntheorem induct_fact (n : Nat) : fac 0 = 1 := by\n  simp [fac]',
        "domain": "arithmetic", "proof_method": "simp", "joint": "definitional_unfold",
        "obstruction": None, "rrc_shape": "CognitiveLoadField",
    },

    # ── 5. intro + apply chains ──
    {
        "name": "intro_all",
        "code": 'theorem intro_all (A B C : Prop) : A → B → C → A := by\n  intro hA\n  intro hB\n  intro hC\n  exact hA',
        "domain": "logic", "proof_method": "intro", "joint": "multiple_introductions",
        "obstruction": None, "rrc_shape": "LogogramProjection",
    },
    {
        "name": "intro_apply",
        "code": 'theorem intro_apply (A B : Prop) : (A → B) → A → B := by\n  intro h\n  intro hA\n  apply h\n  exact hA',
        "domain": "logic", "proof_method": "apply", "joint": "intro_then_apply",
        "obstruction": None, "rrc_shape": "LogogramProjection",
    },
    {
        "name": "have_chain",
        "code": 'theorem have_chain (A B C : Prop) (hAB : A → B) (hBC : B → C) (hA : A) : C := by\n  have hB : B := hAB hA\n  have hC : C := hBC hB\n  exact hC',
        "domain": "logic", "proof_method": "have", "joint": "lemma_chaining",
        "obstruction": None, "rrc_shape": "LogogramProjection",
    },
    {
        "name": "calc_chain",
        "code": 'theorem calc_chain (a b : Nat) : (a + b) * (a + b) = a*a + 2*a*b + b*b := by\n  ring\n  omega',
        "domain": "algebra", "proof_method": "ring", "joint": "ring_then_omega",
        "obstruction": None, "rrc_shape": "SignalShapedRouteCompiler",
    },

    # ── 6. failure cases ──
    {
        "name": "fail_type_mismatch",
        "code": 'theorem fail_type_mismatch (n : Nat) : n = (\"hello\" : String) := by\n  rfl',
        "domain": "type_error", "proof_method": "rfl", "joint": "type_mismatch",
        "obstruction": "type_mismatch", "rrc_shape": "HoldForUnlawfulOrUnderspecifiedShape",
    },
    {
        "name": "fail_missing_lemma",
        "code": 'theorem fail_missing_lemma (n : Nat) : n = n + 0 := by\n  rw [imaginary_lemma]',
        "domain": "arithmetic", "proof_method": "rewrite", "joint": "missing_dependency",
        "obstruction": "missing_lemma", "rrc_shape": "HoldForUnlawfulOrUnderspecifiedShape",
    },
    {
        "name": "fail_unsat",
        "code": 'theorem fail_unsat (x : Nat) (h : x > 0) : x = 0 := by\n  omega',
        "domain": "order", "proof_method": "omega", "joint": "contradictory_goal",
        "obstruction": "unsatisfiable_goal", "rrc_shape": "HoldForUnlawfulOrUnderspecifiedShape",
    },
    {
        "name": "fail_bad_coercion",
        "code": 'theorem fail_bad_coercion (n : Float) : (n : Nat) = (n : Int) := by\n  rfl',
        "domain": "type_error", "proof_method": "rfl", "joint": "coercion_mismatch",
        "obstruction": "type_mismatch", "rrc_shape": "HoldForUnlawfulOrUnderspecifiedShape",
    },
]
