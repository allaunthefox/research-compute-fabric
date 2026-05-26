#!/usr/bin/env python3
"""Route-Repair v1.3b: theorem-shape-driven multi-step patch templates.

Splits case_split_missing into finer failure types and generates
multi-step patches from goal/hypothesis structure.
"""

import hashlib, json, os, re, subprocess, sys, time, uuid
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))
from lean_trace_bridge_v2 import prove

WORKER_URL = os.environ.get("CANARY_WORKER_URL", "http://100.110.163.82:8787")
PROOF_SERVER_TOKEN = os.environ.get("PROOF_SERVER_TOKEN", "")
if not PROOF_SERVER_TOKEN:
    tf = os.environ.get("PROOF_SERVER_TOKEN_FILE", os.path.expanduser("~/.config/ene/language-proof-server.token"))
    try: PROOF_SERVER_TOKEN = Path(tf).read_text().strip()
    except: pass

FAILURE_THEOREMS = [
    ("rw_missing_dir_1","theorem t (a b : Nat) (h : a = b) : b + 0 = a + 0 := by\n  simp"),
    ("rw_missing_dir_2","theorem t (a b : Nat) (h : a = b) : a + 1 = b + 1 := by\n  rfl"),
    ("rw_missing_dir_3","theorem t (a b : Nat) (h : a = b) : b + a = a + b := by\n  rfl"),
    ("rw_missing_dir_4","theorem t (a b : Nat) (h : a = b) : a*2 = b*2 := by\n  simp"),
    ("rw_missing_dir_5","theorem t (a b : Nat) (h : a = b) : a + 1 = b + 1 := by\n  rfl"),
    ("rw_missing_dir_6","theorem t (a b : Nat) (h : a = b) : 0 + a = 0 + b := by\n  simp"),
    ("rw_missing_dir_7","theorem t (a b : Nat) (h : a = b) (c : Nat) : a + c = b + c := by\n  rfl"),
    ("missing_assume_1","theorem t (A B : Prop) (hA : A) (hAB : A → B) : B := by\n  rfl"),
    ("missing_assume_2","theorem t (A B C : Prop) (hA : A) (hAB : A → B) (hBC : B → C) : C := by\n  simp"),
    ("missing_assume_3","theorem t (A B : Prop) (h : A ∧ B) : A := by\n  rfl"),
    ("missing_assume_4","theorem t (A B : Prop) (h : A ∨ B) : A ∨ B := by\n  simp"),
    ("missing_assume_5","theorem t (A B : Prop) (h : A → B) (hA : A) : B := by\n  rfl"),
    ("missing_assume_6","theorem t (A B : Prop) : A → B → A := by\n  rfl"),
    ("missing_assume_7","theorem t (P : Prop) : P → ¬¬P := by\n  rfl"),
    ("arith_gap_1","theorem t (a b : Nat) (h : a ≤ b) : a + 1 ≤ b + 1 := by\n  rfl"),
    ("arith_gap_2","theorem t (a b c : Nat) (h1 : a ≤ b) (h2 : b ≤ c) : a ≤ c := by\n  simp"),
    ("arith_gap_3","theorem t (a b : Nat) (h : a + b = b + a) : a = b := by\n  rfl"),
    ("arith_gap_4","theorem t (a b c : Nat) : a + b + c = a + c + b := by\n  simp"),
    ("arith_gap_5","theorem t (a b : Nat) : a * (b + 1) = a * b + a := by\n  simp"),
    ("arith_gap_6","theorem t (x : Nat) (h : x > 0) : x - 1 < x := by\n  simp"),
    ("arith_gap_7","theorem t (a b : Nat) : a + b = b + a := by\n  omega"),
    ("arith_gap_8","theorem t (a b : Nat) : (a + b) * (a + b) = a*a + 2*a*b + b*b := by\n  simp"),
    ("arith_gap_9","theorem t (x : Nat) : x + x = 2 * x := by\n  simp"),
    ("arith_gap_10","theorem t (n : Nat) : n + 0 = n := by\n  rfl"),
    ("case_split_1","theorem t (A B : Prop) (h : A ∨ B) : B ∨ A := by\n  simp"),
    ("case_split_2","theorem t (A B C : Prop) (h : A ∧ B) (h2 : A → C) : C := by\n  simp"),
    ("case_split_3","theorem t (A B : Prop) (hA : A) (hB : B) : A ∧ B := by\n  rfl"),
    ("case_split_4","theorem t (A B : Prop) (h : A ∨ B) : A ∨ B := by\n  rfl"),
    ("case_split_5","theorem t (A B : Prop) (h : A → B) (hA : A) : A ∨ B → B := by\n  simp"),
    ("case_split_6","theorem t (A B : Prop) (hA : A) (hB : B) : A ∧ B := by\n  simp"),
]


def parse_theorem(code: str) -> dict:
    """Parse a Lean theorem into structured goal/hypothesis data."""
    # Extract all parenthesized type annotations
    raw_hyps = re.findall(r'\(([^)]+:\s*[^)]+)\)', code)
    all_hyps = []
    for h in raw_hyps:
        parts = h.split(":")
        if len(parts) >= 2:
            names = parts[0].strip().split()
            typ = ":".join(parts[1:]).strip()
            for n in names:
                all_hyps.append({"name": n.strip(), "type": typ, "is_prop": typ == "Prop",
                                 "is_nat": typ in ("Nat", "ℕ"), "is_int": typ in ("Int", "ℤ")})
    
    # Extract goal (last type annotation before :=)
    goal = ""
    m = re.findall(r':\s*([^:]+?)\s*:=', code)
    if m:
        goal = m[-1].strip()
    
    # Simple goal structure analysis
    goal_has_and = "∧" in goal
    goal_has_or = "∨" in goal
    goal_has_arrow = "→" in goal
    goal_has_not = "¬" in goal
    goal_has_eq = "=" in goal
    goal_has_ineq = any(c in goal for c in "≤≥<>")
    goal_has_arith = any(c in goal for c in "+-*/")
    goal_propositions = [h["name"] for h in all_hyps if h["is_prop"]]
    goal_variables = [h["name"] for h in all_hyps if h["is_nat"] or h["is_int"]]
    
    # Hypothesis structure analysis
    hyp_implications = [h for h in all_hyps if "→" in h["type"]]
    hyp_conjunctions = [h for h in all_hyps if "∧" in h["type"]]
    hyp_disjunctions = [h for h in all_hyps if "∨" in h["type"]]
    hyp_equalities = [h for h in all_hyps if "=" in h["type"]]
    hyp_foralls = [h for h in all_hyps if "∀" in h["type"]]
    hyp_nat = [h for h in all_hyps if h["is_nat"]]
    
    # Find hypothesis matching goal
    goal_matches = [h for h in all_hyps if h["type"] == goal]
    
    # Foralls — also treat as implication-like: h: ∀ x, P x has head "∀"
    _imp_objs = hyp_implications + hyp_foralls
    
    return {
        "goal": goal,
        "goal_has_and": goal_has_and, "goal_has_or": goal_has_or,
        "goal_has_arrow": goal_has_arrow, "goal_has_not": goal_has_not,
        "goal_has_eq": goal_has_eq, "goal_has_ineq": goal_has_ineq,
        "goal_has_arith": goal_has_arith,
        "all_hyps": all_hyps, "goal_propositions": goal_propositions,
        "goal_variables": goal_variables, "goal_matches": [h["name"] for h in goal_matches],
        "hyp_implications": [h["name"] for h in hyp_implications],
        "hyp_conjunctions": [h["name"] for h in hyp_conjunctions],
        "hyp_disjunctions": [h["name"] for h in hyp_disjunctions],
        "hyp_equalities": [h["name"] for h in hyp_equalities],
        "_all_hyp_objs": all_hyps,
        "_imp_objs": _imp_objs,
        "_conj_objs": hyp_conjunctions,
        "_disj_objs": hyp_disjunctions,
        "_eq_objs": hyp_equalities,
        "hyp_nat": [h["name"] for h in hyp_nat],
        "tactic": "unknown",
    }


def classify_obstruction(code: str) -> str:
    """Improved obstruction classifier with finer distinction between failure types."""
    info = parse_theorem(code)
    g = info["goal"]
    
    if "by " in code or "by\n" in code:
        m = re.search(r'by\s+(\S+)', code)
        if m: info["tactic"] = m.group(1)
    
    tactic = info["tactic"]
    has_arith = info["goal_has_arith"] or info["goal_variables"]
    has_rewrite_hyp = len(info["hyp_equalities"]) > 0 and tactic in ("simp", "rw")
    
    # Priority order: most specific first
    
    # 1. Constructor goal (∧, and-like structure in goal)
    if g.count("∧") == 1 and not info["hyp_conjunctions"]:
        return "constructor_missing"
    
    # 2. Or-swap: goal has ∨, hypothesis has ∨ with swapped arguments
    if info["goal_has_or"] and info["hyp_disjunctions"]:
        return "case_split_missing"
    
    # 3. And-elimination: hypothesis has ∧, goal is a conjunct
    if info["hyp_conjunctions"] and not info["goal_has_and"]:
        return "missing_destructuring"
    
    # 4. Or-anything: goal has ∨
    if info["goal_has_or"]:
        return "case_split_missing"
    
    # 5. Implication chain: hypothesis is A → B, goal is B, have A
    if info["hyp_implications"] and not info["goal_has_arrow"]:
        return "missing_assumption_bridge"
    
    # 6. Intro chain: goal has multiple arrows
    if info["goal_has_arrow"]:
        return "intro_chain_missing"
    
    # 7. Negation: goal has ¬
    if info["goal_has_not"]:
        return "contradiction_bridge"
    
    # 8. Rewrite with equality hypothesis
    if has_rewrite_hyp:
        return "missing_rewrite_direction"
    
    # 9. Arithmetic target with simp/rfl tactic
    if has_arith and tactic in ("simp", "rfl", "omega"):
        return "arithmetic_gap"
    
    # 10. Pure assumption: rfl with hypotheses
    if tactic == "rfl" and len(info["goal_propositions"]) > 0:
        return "missing_assumption_bridge"
    
    # 11. Induction
    if len(info["goal_variables"]) > 0 and tactic in ("simp", "rfl"):
        return "induction_incomplete"
    
    return "other"


def generate_patches(code: str, obstruction: str, max_p: int = 5) -> list[dict]:
    """Generate multi-step patch candidates from theorem shape."""
    info = parse_theorem(code)
    g = info["goal"]
    patches = []
    
    def add(patch: str, tag: str):
        patches.append({"patch": patch, "tag": tag})
    
    hyps = info["all_hyps"]
    impls = info["_imp_objs"]
    conj_h = info["_conj_objs"]
    disj_h = info["_disj_objs"]
    eq_h = info["_eq_objs"]
    goal_m = info["goal_matches"]
    props = info["goal_propositions"]
    vnames = info["goal_variables"][:1]
    nat_var = vnames[0] if vnames else "n"
    
    # ── Constructor missing: ⊢ A ∧ B ──
    if obstruction == "constructor_missing":
        parts = [p.strip() for p in g.split("∧") if p.strip()]
        for h in hyps:
            if h["type"] in parts:
                add(f"constructor\n  · exact {h['name']}", "constructor_exact")
        for h in hyps:
            if h["is_prop"] and h["type"] not in ("Prop",):
                add(f"constructor\n  · exact {h['name']}", "constructor_exact_prop")
        add("constructor\n  · assumption\n  · assumption", "constructor_assumption")
        if props:
            add(f"constructor\n  · exact {props[0]}\n  · exact {props[1] if len(props) > 1 else props[0]}", "constructor_props")
    
    # ── Case split missing: ⊢ ∨ from ∨ hypothesis ──
    if obstruction == "case_split_missing":
        for h in disj_h:
            name = h["name"]
            # Check if this is a swap (B ∨ A from A ∨ B)
            htype = h["type"]
            if "∨" in htype:
                hparts = [p.strip() for p in htype.split("∨")]
                gparts = [p.strip() for p in g.split("∨") if p.strip()]
                if len(hparts) == 2 and len(gparts) == 2:
                    if hparts[0] == gparts[1] and hparts[1] == gparts[0]:
                        # Swap pattern
                        add(f"""cases {name} with
  | inl h => right; exact h
  | inr h => left; exact h""", "case_swap")
                    elif hparts == gparts:
                        add(f"""cases {name} with
  | inl h => left; exact h
  | inr h => right; exact h""", "case_same")
        # Generic: try both branches
        for h in disj_h[:1]:
            add(f"""cases {h['name']} with
  | inl h => right; exact h
  | inr h => left; exact h""", "case_swap_generic")
            add(f"""cases {h['name']} with
  | inl h => left; exact h
  | inr h => right; exact h""", "case_same_generic")
    
    # ── Missing destructuring: ⊢ A from h : A ∧ B ──
    if obstruction == "missing_destructuring":
        for h in conj_h:
            name = h["name"]
            add(f"exact {name}.left", "dot_left")
            add(f"exact {name}.right", "dot_right")
            add(f"""cases {name} with
  | intro h1 h2 => exact h1""", "cases_and_elim")
            add(f"""rcases {name} with ⟨h1, h2⟩
  exact h1""", "rcases_elim")
    
    # ── Missing assumption bridge: have A → B and A, need B ──
    if obstruction == "missing_assumption_bridge":
        for imp in impls:
            parts = [p.strip() for p in imp["type"].split("→")]
            target = parts[-1]
            # Find hypothesis matching the premise
            for h in hyps:
                if h["type"] == parts[0] and h["name"] != imp["name"]:
                    add(f"apply {imp['name']}\n  exact {h['name']}", "apply_exact")
                    add(f"exact {imp['name']} {h['name']}", "exact_apply")
        # Try all combos
        for imp in impls[:2]:
            for h in hyps[:5]:
                if h["name"] != imp["name"]:
                    add(f"apply {imp['name']}\n  exact {h['name']}", "apply_exact_gen")
        add("assumption", "assumption")
    
    # ── Intro chain: ⊢ A → B → A ──
    if obstruction == "intro_chain_missing":
        arrow_count = g.count("→")
        intros = "\n  ".join([f"intro h{i}" for i in range(arrow_count)])
        # For A → B → A, the last intro gives the answer
        if props:
            add(f"""{intros}
  exact h0""", "intro_first")
            if len(props) >= 2:
                add(f"""{intros}
  exact h{arrow_count - 1}""", "intro_last")
        # Generic
        if props:
            add(f"""{intros}
  exact {props[0]}""", "intro_prop")
        # Find the right intro by matching goal structure
        parts = [p.strip() for p in g.split("→") if p.strip()]
        if len(parts) >= 2:
            # Last part of arrow chain = target
            target = parts[-1]
            for i, part in enumerate(parts[:-1]):
                if part == target:
                    add(f"""{intros}
  exact h{i}""", f"intro_match_{i}")
                # Check if a hypothesis matches this part
                for h in hyps:
                    if h["type"] == part:
                        add(f"""{intros}
  apply h{h['name'] if len(hyps) > 3 else int(h['name'][-1])}
  exact h{(i or 0)}""", f"intro_apply_{i}")
        add(f"""intro h
  exact h""", "intro_single")
    
    # ── Contradiction bridge: ⊢ ¬¬P or have P and ¬P ──
    if obstruction == "contradiction_bridge":
        all_names = [h["name"] for h in hyps]
        add("intro hnp\n  exact hnp hp", "contra_bridge")
        for h1 in hyps:
            for h2 in hyps:
                if h1["type"] == f"¬{h2['type']}" or h2["type"] == f"¬{h1['type']}":
                    add(f"exact {h2['name']} {h1['name']}", "contra_exact")
    
    # ── Rewrite direction ──
    if obstruction == "missing_rewrite_direction":
        for h in eq_h[:1]:
            add(f"rw [← {h}]\n  simp", "rw_reverse_simp")
            add(f"rw [{h}]\n  simp", "rw_forward_simp")
            add(f"rw [← {h}]\n  rfl", "rw_reverse_rfl")
            add(f"rw [{h}]\n  rfl", "rw_forward_rfl")
    
    # ── Arithmetic gap ──
    if obstruction == "arithmetic_gap":
        add("omega", "omega")
        add("norm_num", "norm_num")
        for h in eq_h[:1]:
            add(f"rw [{h}]\n  omega", "rw_omega")
        add("simp\n  omega", "simp_omega")
        add("simp\n  norm_num", "simp_norm_num")
    
    # ── Induction incomplete ──
    if obstruction == "induction_incomplete":
        add(f"""induction {nat_var} with
  | zero => simp
  | succ n ih => simp [ih]""", "induction_simp")
        add(f"""induction {nat_var} with
  | zero => simp
  | succ n ih => simp [Nat.succ_eq_add_one, ih]""", "induction_succ")
    
    # ── Cross-domain hybrid patches ──
    has_logic = info["goal_has_and"] or info["goal_has_or"] or info["goal_has_arrow"]
    has_nat = len(info["goal_variables"]) > 0
    if has_logic and has_nat:
        add("omega\n  simp", "cross_omega_simp")
        add("simp\n  omega", "cross_simp_omega")
    
    # Deduplicate and limit
    seen = set()
    unique = []
    for p in patches:
        key = p["patch"]
        if key not in seen:
            seen.add(key)
            unique.append(p)
        if len(unique) >= max_p:
            break
    
    return unique[:max_p]


def prove(lean_code, name="repair", timeout_s=60):
    result = subprocess.run(
        ["curl", "-s", "--connect-timeout", "10", "-X", "POST", f"{WORKER_URL}/lean/check",
         "-H", "Content-Type: application/json",
         "-H", f"Authorization: Bearer {PROOF_SERVER_TOKEN}",
         "-d", json.dumps({"code": lean_code, "name": name})],
        capture_output=True, text=True, timeout=timeout_s,
    )
    if result.returncode != 0:
        return {"ok": False, "stdout": "", "error": f"curl: {result.stderr[:200]}"}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"ok": False, "stdout": "", "error": "json decode"}


def route_repair(name, code, max_attempts=5):
    resp = prove(code, name + "_init")
    if resp.get("ok", False):
        return {"name": name, "initial_status": "verified", "recovered": False}
    
    obstruction = classify_obstruction(code)
    candidates = generate_patches(code, obstruction, max_attempts)
    attempts = []; recovered = False; best = None
    
    for i, cand in enumerate(candidates):
        patched = code.split(":=")[0] + ":= by\n" if ":=" in code else code + "\n"
        # Normalize indentation for multi-line patches
        patch_lines = cand["patch"].split("\n")
        patched += "\n".join("  " + line for line in patch_lines)
        
        r = prove(patched, f"{name}_repair_{i}")
        ok = r.get("ok", False)
        attempt = {"attempt": i+1, "tag": cand["tag"], "patch": cand["patch"][:60], "ok": ok}
        attempts.append(attempt)
        if ok:
            recovered = True; best = attempt; break
        if not best: best = attempt
    
    return {"name": name, "obstruction": obstruction, "initial_status": "failed",
            "recovered": recovered, "attempts": attempts, "best_attempt": best,
            "n_candidates": len(candidates)}


def main():
    print("Route-Repair v1.3b: theorem-shape-driven multi-step templates\n")
    test_set = FAILURE_THEOREMS[:30]
    results = []
    
    for i, (n, c) in enumerate(test_set):
        print(f"  [{i+1}/{len(test_set)}] {n:35s} ... ", end="", flush=True)
        r = route_repair(n, c)
        if r["initial_status"] == "verified":
            print("already verified"); continue
        s = "RECOVERED" if r["recovered"] else "no change"
        tag = (r.get("best_attempt") or {}).get("tag", "-")
        print(f"{s:15s} obs={r['obstruction']:30s} tag={tag:25s} candidates={r['n_candidates']}", flush=True)
        results.append(r)
    
    n = len(results); rec = sum(1 for r in results if r["recovered"])
    print(f"\n{'='*60}\nV1.3b MULTI-STEP\n{'='*60}")
    print(f"Test: {n} failed | Recovered: {rec} ({rec/max(n,1):.0%})")
    
    by_obs = defaultdict(lambda: {"t":0,"r":0})
    for r in results:
        o = r["obstruction"]; by_obs[o]["t"] += 1
        if r["recovered"]: by_obs[o]["r"] += 1
    print(f"\nPer-obstruction:")
    for o,s in sorted(by_obs.items(),key=lambda x:-x[1]["t"]):
        print(f"  {o:30s}: n={s['t']:2d} rec={s['r']/max(s['t'],1):.0%}")
    
    print(f"\nAblation: v1.1(spectral)=0% → v1.2(hybrid)=36% → v1.3a(NUVMAP)=36% → v1.3b(multi-step)={rec/max(n,1):.0%}")
    
    rp = "shared-data/pist_route_repair_v13b_benchmark.json"
    with open(rp, "w") as f:
        json.dump({"n": n, "recovered": rec, "results": results}, f, indent=2)
    print(f"Report: {rp}")


if __name__ == "__main__":
    from collections import defaultdict
    main()
