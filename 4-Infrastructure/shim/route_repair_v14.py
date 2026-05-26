#!/usr/bin/env python3
"""Route-Repair v1.4: 16D→4D→3D charted repair manifold.

Projects theorem structure onto a 16D modifier, chooses a local proof chart (4D),
and generates 3D-ranked patch candidates. Focused on zero-bucket repair.
"""

import json, os, re, subprocess, sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))
from route_repair_v13b import parse_theorem, prove

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


# ── 16D Modifier ──────────────────────────────────────────────────────────

def build_modifier_16d(info: dict) -> list[float]:
    """Build a 16D proof-state control vector from theorem info."""
    g = info.get("goal", "")
    R = [
        float(len(info.get("hyp_equalities", []))),        # equality_hyp_count
        float(sum(1 for h in info["_eq_objs"] if h["type"].count("=") > 0)),  # equality_direction_fit
        float(1 if any("symm" in str(h) for h in info["_eq_objs"]) else 0),   # symm_available
        float(1 if len(info.get("hyp_equalities", [])) >= 2 else 0),          # trans_chain_length
    ]
    I = [
        float(g.count("→")),                                              # goal_arrow_depth
        float(len(info.get("hyp_implications", []))),                     # hyp_implication_count
        float(len([h for h in info["_imp_objs"] if h["type"].count("→") <= 2])),  # available_antecedent
        float(1 if "¬" in g or any("¬" in h.get("type","") for h in info["_imp_objs"]) else 0),  # negation_signal
    ]
    C = [
        float(g.count("∧")),                          # goal_and_arity
        float(g.count("∨")),                          # goal_or_arity
        float(len(info.get("hyp_conjunctions", []))), # hyp_and_count
        float(len(info.get("hyp_disjunctions", []))), # hyp_or_count
    ]
    A = [
        float(sum(1 for c in g if c in "+-*/")),      # arithmetic_op_count
        float(sum(1 for c in g if c in "≤≥<>")),      # order_op_count
        float(len(info.get("goal_variables", []))),   # nat_int_variable_count
        float(1 if "simp" in info.get("tactic","") or "omega" in info.get("tactic","") else 0),  # simp_omega_signal
    ]
    return R + I + C + A


def project_4d(z16: list[float]) -> dict:
    """Project 16D modifier onto 4D repair axis."""
    if len(z16) < 16: return {"rewrite":0,"intro":0,"constructor_case":0,"arithmetic":0}
    r = sum(z16[0:4])
    i = sum(z16[4:8])
    c = sum(z16[8:12])
    a = sum(z16[12:16])
    total = r + i + c + a
    if total == 0: return {"rewrite":0.25,"intro":0.25,"constructor_case":0.25,"arithmetic":0.25}
    return {"rewrite": r/total, "intro": i/total, "constructor_case": c/total, "arithmetic": a/total}


def choose_chart(axis4d: dict) -> str:
    """Choose the local proof chart from the 4D axis."""
    return max(axis4d, key=axis4d.get)


# ── 3D Patch Embedding ─────────────────────────────────────────────────────

def embed_patch(patch: str, chart: str, tag: str, specificity=0.5, cost=0.5, success_prior=0.3) -> dict:
    """Embed a patch candidate in 3D: (specificity, cost, success_prior)."""
    return {
        "patch": patch, "chart": chart, "tag": tag,
        "specificity": specificity,
        "cost": cost,
        "success_prior": success_prior,
        "residual_risk": 1.0 - specificity,
    }


def rank_patches(patches: list[dict]) -> list[dict]:
    """Rank patches by S = α·specificity − β·cost + γ·success_prior − δ·residual_risk."""
    ALPHA, BETA, GAMMA, DELTA = 0.4, 0.3, 0.2, 0.1
    for p in patches:
        p["score"] = (ALPHA * p["specificity"] - BETA * p["cost"]
                      + GAMMA * p["success_prior"] - DELTA * p["residual_risk"])
    patches.sort(key=lambda p: -p["score"])
    return patches


# ── Chart-driven patch generators ──────────────────────────────────────────

def generate_rewrite_patches(code: str, info: dict) -> list[dict]:
    """Rewrite chart: simpa, rw, symm, congrArg, trans."""
    hyps = info["_eq_objs"]
    hyp_names = [h["name"] for h in hyps]
    g = info.get("goal", "")
    patches = []
    for hn in hyp_names:
        patches.append(embed_patch(f"simpa [{hn}]", "rewrite", "simpa_eq", 0.91, 0.12, 0.67))
        patches.append(embed_patch(f"rw [{hn}]\n  simp", "rewrite", "rw_simp", 0.85, 0.20, 0.33))
        patches.append(embed_patch(f"rw [← {hn}]\n  simp", "rewrite", "rw_rev_simp", 0.80, 0.20, 0.30))
        patches.append(embed_patch(f"exact {hn}.symm", "rewrite", "symm", 0.72, 0.10, 0.50))
        # congrArg for equalities of the form x + c = y + c
        for v in re.findall(r'[a-zA-Z]\s*[+*/-]', g):
            op_side = v.strip()
            patches.append(embed_patch(f"exact congrArg (fun t => t {op_side[1:]}) {hn}", "rewrite", "congrArg", 0.88, 0.15, 0.45))
    if len(hyp_names) >= 2:
        patches.append(embed_patch(f"exact {hyp_names[0]}.trans {hyp_names[1]}", "rewrite", "trans", 0.75, 0.12, 0.40))
    patches.append(embed_patch("simp", "rewrite", "simp", 0.50, 0.10, 0.20))
    return patches


def generate_intro_patches(code: str, info: dict) -> list[dict]:
    """Intro chart: implication chains, negation bridges."""
    g = info.get("goal", "")
    props = info.get("goal_propositions", [])
    patches = []
    arrow_count = g.count("→")
    
    if "¬¬" in g:
        patches.append(embed_patch("intro hp\n  intro hnp\n  exact hnp hp", "intro", "not_not", 0.93, 0.15, 0.80))
    
    # Build intro chain from goal structure
    parts = [p.strip() for p in re.split(r'→', g) if p.strip()]
    if len(parts) >= 2:
        target = parts[-1]
        intros = "\n".join(f"intro h{i}" for i in range(len(parts) - 1))
        
        if props:
            patches.append(embed_patch(f"{intros}\nexact h0", "intro", "intro_first", 0.90, 0.15, 0.70))
            if len(props) >= 2:
                patches.append(embed_patch(f"{intros}\nexact h{len(parts) - 2}", "intro", "intro_last", 0.88, 0.15, 0.65))
        
        for p in props:
            if p == target:
                patches.append(embed_patch(f"{intros}\nexact h0", "intro", "intro_target", 0.85, 0.12, 0.60))
        
        for i, part in enumerate(parts[:-1]):
            for h in info["_imp_objs"]:
                htype = h["type"]
                if htype == part or htype.startswith(part + "→"):
                    imp_name = h["name"]
                    patches.append(embed_patch(
                        f"{intros}\napply {imp_name}\nexact h{i}",
                        "intro", f"intro_apply_{i}", 0.82, 0.18, 0.55))
    
    patches.append(embed_patch("intro h\nexact h", "intro", "intro_id", 0.60, 0.08, 0.30))
    
    # Apply-exact for missing_assumption_bridge (implication + antecedent)
    for imp in info["_imp_objs"]:
        parts = [p.strip() for p in imp["type"].split("→")]
        if len(parts) >= 2:
            target, premise = parts[-1], parts[0]
            for h in info["all_hyps"]:
                if h["type"] == premise and h["name"] != imp["name"]:
                    patches.append(embed_patch(
                        f"apply {imp['name']}\n  exact {h['name']}",
                        "intro", "apply_exact", 0.90, 0.18, 0.72))
                    patches.append(embed_patch(
                        f"exact {imp['name']} {h['name']}",
                        "intro", "exact_apply", 0.88, 0.12, 0.70))
    
    # Destructuring patches for ∧ hypotheses
    for conj in info["_conj_objs"]:
        patches.append(embed_patch(f"exact {conj['name']}.left", "intro", "dot_left", 0.85, 0.08, 0.60))
        patches.append(embed_patch(f"exact {conj['name']}.right", "intro", "dot_right", 0.83, 0.08, 0.58))
        patches.append(embed_patch(f"rcases {conj['name']} with ⟨h, _⟩\n  exact h", "intro", "rcases_left", 0.82, 0.15, 0.55))
    
    return patches


def generate_constructor_patches(code: str, info: dict) -> list[dict]:
    """Constructor chart: ∧, ∨, branch-complete blocks."""
    g = info.get("goal", "")
    props = info.get("goal_propositions", [])
    hyps = info["all_hyps"]
    patches = []
    
    if "∧" in g:
        # Constructor with specific hypotheses
        for h in hyps:
            ht = h["type"]
            if "∧" in ht:
                patches.append(embed_patch(
                    "constructor\n· exact " + h["name"] + ".left\n· exact " + h["name"] + ".right",
                    "constructor_case", "constructor_from_and", 0.90, 0.18, 0.70))
            elif ht in g.split("∧"):
                patches.append(embed_patch(
                    f"constructor\n· exact {h['name']}",
                    "constructor_case", "constructor_exact", 0.85, 0.15, 0.60))
        # Constructor with assumption
        patches.append(embed_patch(
            "constructor\n· assumption\n· assumption",
            "constructor_case", "constructor_assume", 0.80, 0.12, 0.50))
        # Constructor with hypotheses matching goal conjuncts
        gparts = [p.strip() for p in g.split("∧") if p.strip()]
        for gp in gparts:
            for h in hyps:
                if h["type"] == gp and h["name"] != gp:
                    patches.append(embed_patch(
                        f"constructor\n· exact {h['name']}",
                        "constructor_case", "constructor_hyp_match", 0.90, 0.15, 0.68))
        # Constructor with first two non-type hypotheses
        hyp_names = [h["name"] for h in hyps if h["type"] not in ("Prop", "Nat", "Int", "ℕ", "ℤ", "Type")]
        if len(hyp_names) >= 2:
            patches.append(embed_patch(
                f"constructor\n· exact {hyp_names[0]}\n· exact {hyp_names[1]}",
                "constructor_case", "constructor_hyp_names", 0.88, 0.15, 0.65))
    
    if "∨" in g:
        parts = [p.strip() for p in g.split("∨") if p.strip()]
        for h in hyps:
            ht = h["type"]
            if "∨" in ht:
                hparts = [p.strip() for p in ht.split("∨")]
                if len(hparts) == 2 and len(parts) == 2:
                    if hparts[0] == parts[1] and hparts[1] == parts[0]:
                        patches.append(embed_patch(
                            f"cases {h['name']} with\n| inl h => right; exact h\n| inr h => left; exact h",
                            "constructor_case", "or_swap_full", 0.92, 0.22, 0.80))
                    if hparts == parts:
                        patches.append(embed_patch(
                            f"cases {h['name']} with\n| inl h => left; exact h\n| inr h => right; exact h",
                            "constructor_case", "or_same_full", 0.90, 0.22, 0.75))
    
    # Generic fallback
    patches.append(embed_patch("constructor\n· assumption\n· assumption", "constructor_case", "constructor_generic", 0.50, 0.12, 0.25))
    return patches


def generate_arithmetic_patches(info: dict) -> list[dict]:
    """Arithmetic chart: omega, norm_num, simp chains."""
    patches = []
    patches.append(embed_patch("omega", "arithmetic", "omega", 0.80, 0.08, 0.75))
    patches.append(embed_patch("norm_num", "arithmetic", "norm_num", 0.65, 0.08, 0.40))
    patches.append(embed_patch("simp\n  omega", "arithmetic", "simp_omega", 0.70, 0.15, 0.50))
    patches.append(embed_patch("simp\n  norm_num", "arithmetic", "simp_norm_num", 0.60, 0.15, 0.35))
    for h in info["_eq_objs"]:
        patches.append(embed_patch(f"rw [{h['name']}]\n  omega", "arithmetic", "rw_omega", 0.75, 0.18, 0.55))
    return patches


def classify_obstruction_from_info(info: dict) -> str:
    """Classify obstruction from parsed theorem info."""
    g = info.get("goal", "")
    hyps = info["all_hyps"]
    hyp_impls = info["_imp_objs"]
    hyp_eqs = info["_eq_objs"]
    hyp_disjs = info["_disj_objs"]
    hyp_conjs = info["_conj_objs"]
    vars = info.get("goal_variables", [])
    tactic = info.get("tactic", "")
    
    if "∧" in g and not hyp_conjs: return "constructor_missing"
    if hyp_disjs and "∨" in g: return "case_split_missing"
    if hyp_conjs and "∧" not in g: return "missing_destructuring"
    if hyp_impls and "→" not in g: return "missing_assumption_bridge"
    if g.count("→") >= 2: return "intro_chain_missing"
    if "¬" in g: return "contradiction_bridge"
    if hyp_eqs: return "missing_rewrite_direction"
    if vars and tactic in ("simp","rfl","omega"): return "arithmetic_gap"
    if "∨" in g: return "case_split_missing"
    if "∧" in g: return "constructor_missing"
    if tactic == "rfl": return "missing_assumption_bridge"
    return "other"


# ── Main repair loop ───────────────────────────────────────────────────────

def route_repair_v14(name: str, code: str, max_attempts=6) -> dict:
    """16D→4D→3D charted repair."""
    resp = prove(code, name + "_init")
    if resp.get("ok", False):
        return {"name": name, "initial_status": "verified", "recovered": False}
    
    info = parse_theorem(code)
    if "by " in code or "by\n" in code:
        m = re.search(r'by\s+(\S+)', code)
        if m: info["tactic"] = m.group(1)
    else:
        info["tactic"] = ""
    
    z16 = build_modifier_16d(info)
    axis4d = project_4d(z16)
    chart = choose_chart(axis4d)
    obstruction = classify_obstruction_from_info(info)
    
    # Generate patches from the chosen chart
    chart_generators = {
        "rewrite": lambda: generate_rewrite_patches(code, info),
        "intro": lambda: generate_intro_patches(code, info),
        "constructor_case": lambda: generate_constructor_patches(code, info),
        "arithmetic": lambda: generate_arithmetic_patches(info),
    }
    
    # Generate from all charts, preferring the primary chart
    all_patches = chart_generators.get(chart, lambda: [])()
    
    # Fill with arithmetic fallback if empty
    if not all_patches:
        all_patches = generate_arithmetic_patches(info)
    
    ranked = rank_patches(all_patches)[:max_attempts]
    attempts = []; recovered = False; best = None
    
    for i, cand in enumerate(ranked):
        patched = code.split(":=")[0] + ":= by\n" if ":=" in code else code + "\n"
        patch_lines = cand["patch"].split("\n")
        patched += "\n".join("  " + ln for ln in patch_lines)
        
        r = prove(patched, f"{name}_repair_{i}")
        ok = r.get("ok", False)
        attempt = {"attempt": i+1, "chart": chart, "tag": cand["tag"],
                    "score": round(cand["score"], 3), "ok": ok}
        attempts.append(attempt)
        if ok:
            recovered = True; best = attempt; break
        if not best: best = attempt
    
    return {
        "name": name, "obstruction": obstruction, "chart": chart,
        "z16": [round(v, 2) for v in z16],
        "axis4d": {k: round(v, 3) for k, v in axis4d.items()},
        "initial_status": "failed", "recovered": recovered,
        "attempts": attempts, "best_attempt": best, "n_candidates": len(ranked),
    }


def main():
    print("Route-Repair v1.4: 16D→4D→3D charted repair manifold\n")
    test_set = FAILURE_THEOREMS[:30]
    results = []
    
    for i, (n, c) in enumerate(test_set):
        print(f"  [{i+1}/{len(test_set)}] {n:35s} ... ", end="", flush=True)
        r = route_repair_v14(n, c)
        if r["initial_status"] == "verified": print("already verified"); continue
        s = "RECOVERED" if r["recovered"] else "no change"
        tag = (r.get("best_attempt") or {}).get("tag", "-")
        print(f"{s:15s} chart={r['chart']:20s} obs={r['obstruction']:30s} tag={tag:25s}", flush=True)
        results.append(r)
    
    n = len(results); rec = sum(1 for r in results if r["recovered"])
    by_obs = defaultdict(lambda: {"t": 0, "r": 0})
    for r in results:
        o = r["obstruction"]; by_obs[o]["t"] += 1
        if r["recovered"]: by_obs[o]["r"] += 1
    
    print(f"\n{'='*60}\nV1.4 CHARTED REPAIR\n{'='*60}")
    print(f"Test: {n} failed | Recovered: {rec} ({rec/max(n,1):.0%})")
    print(f"\nPer-obstruction:")
    for o, s in sorted(by_obs.items(), key=lambda x: -x[1]["t"]):
        print(f"  {o:30s}: n={s['t']:2d} rec={s['r']/max(s['t'],1):.0%}")
    
    # Chart distribution
    by_chart = Counter(r["chart"] for r in results)
    print(f"\nChart distribution: {dict(by_chart)}")
    
    print(f"\nAblation: v1.2=36% → v1.3a=36% → v1.3b=54% → v1.4={rec/max(n,1):.0%}")
    
    rp = "shared-data/pist_route_repair_v14_benchmark.json"
    with open(rp, "w") as f:
        json.dump({"n": n, "recovered": rec, "results": results}, f, indent=2)
    print(f"Report: {rp}")


if __name__ == "__main__":
    from collections import Counter, defaultdict
    main()
