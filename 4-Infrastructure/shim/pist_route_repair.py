#!/usr/bin/env python3
# INFRA:DEAD rds -- AWS RDS is gone. Any file referencing rds_connect.py or this hostname is stale and must be ported.
"""Route-Repair Loop v1 — use the flexure joint library to suggest tactic repairs for failed proofs.

Takes a failed Lean proof trace, classifies it, generates candidate patches
from the predicted tactic family, retries on the proof worker, and measures recovery.
"""

import hashlib
import json
import logging
import math
import os
import re
import subprocess
import sys
import time
import uuid
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))
from pist_trace_classify_mcp import compute_spectral

FLEXURE_SESSION = "a4a0eb20-93fe-413e-8e0b-50334bb778d8"
WORKER_URL = os.environ.get("CANARY_WORKER_URL", "http://100.110.163.82:8787")
PROOF_SERVER_TOKEN = os.environ.get("PROOF_SERVER_TOKEN", "")
if not PROOF_SERVER_TOKEN:
    tf = os.environ.get("PROOF_SERVER_TOKEN_FILE", os.path.expanduser("~/.config/ene/language-proof-server.token"))
    try:
        PROOF_SERVER_TOKEN = Path(tf).read_text().strip()
    except (ValueError, TypeError, KeyError) as e: logging.warning(f"Failed to read proof server token: {e}")

TACTIC_TEMPLATES = {
    "rewrite": ["rw [%s]", "simp [%s]"],
    "normalization": ["simp", "norm_num"],
    "discharge": ["exact %s", "assumption", "apply %s"],
    "arithmetic": ["omega"],
    "case_analysis": ["cases %s", "constructor"],
    "induction": ["induction %s"],
    "introduction": ["intro %s"],
    "reflexivity": ["rfl"],
    "constructor": ["constructor"],
    "lemma_introduction": ["have h : %s := by\n  %s"],
}


def connect():
    host = os.environ.get("RDS_HOST", "database-1-instance-1.cghu8yqogqwo.us-east-1.rds.amazonaws.com")
    port = os.environ.get("RDS_PORT", "5432")
    user = os.environ.get("RDS_USER", "postgres")
    db = os.environ.get("RDS_DB", "postgres")
    token = os.environ.get("RDS_IAM_TOKEN", "")
    if not token:
        token = subprocess.check_output([
            "aws", "rds", "generate-db-auth-token",
            "--region", os.environ.get("AWS_REGION", "us-east-1"),
            "--hostname", host, "--port", port, "--username", user,
        ], text=True).strip()
    import psycopg2
    return psycopg2.connect(host=host, port=port, user=user, password=token, dbname=db, sslmode="require")


def prove(lean_code: str, name: str = "repair", timeout_s: int = 60) -> dict:
    """Send Lean code to the proof worker."""
    result = subprocess.run(
        ["curl", "-s", "--connect-timeout", "10", "-X", "POST", f"{WORKER_URL}/lean/check",
         "-H", "Content-Type: application/json",
         "-H", f"Authorization: Bearer {PROOF_SERVER_TOKEN}",
         "-d", json.dumps({"code": lean_code, "name": name})],
        capture_output=True, text=True, timeout=timeout_s,
    )
    if result.returncode != 0:
        return {"ok": False, "stdout": "", "stderr": f"curl: {result.stderr[:200]}"}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        return {"ok": False, "stdout": "", "error": str(e)}


def classify_tactic(tactic: str) -> str:
    tl = tactic.lower()
    if "rw" in tl: return "rewrite"
    if "simp" in tl: return "normalization"
    if "omega" in tl or "nlinarith" in tl: return "arithmetic"
    if "induction" in tl: return "induction"
    if "ring" in tl: return "normalization"
    if "cases" in tl: return "case_analysis"
    if "constructor" in tl: return "constructor"
    if "apply" in tl or "exact" in tl: return "discharge"
    if "intro" in tl: return "introduction"
    if "have" in tl: return "lemma_introduction"
    if "rfl" in tl: return "reflexivity"
    if "norm_num" in tl: return "normalization"
    return "unknown"


def classify_trace_against_library(trace: dict) -> dict:
    """Classify a trace against the flexure library and return predictions."""
    import hashlib as hl
    matrix = trace.get("transition_matrix", [])
    if not matrix or len(matrix) == 0:
        return {"tactic_family": "unknown", "confidence": 0.0, "nearest_motifs": []}
    
    sp = compute_spectral(matrix)
    vec = [sp.get(k, 0) for k in ["matrix_size", "rank", "spectral_gap", "laplacian_zero_count",
                                    "density", "eigenvalue_max"]]
    
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT decision_signals FROM ene.flexures WHERE session_id = %s", (FLEXURE_SESSION,))
        library = []
        for row in cur.fetchall():
            sig = json.loads(row[0]) if isinstance(row[0], str) else row[0]
            sp_lib = sig.get("spectral", {})
            lv = [sp_lib.get(k, 0) for k in ["matrix_size", "rank", "spectral_gap", "laplacian_zero_count",
                                               "density", "eigenvalue_max"]]
            library.append({"features": lv, "tf": sig.get("tactic_family", "?")})
        
        # kNN vote
        scored = []
        for lib in library:
            dist = math.sqrt(sum((vec[i] - lib["features"][i])**2 for i in range(len(vec))))
            scored.append((dist, lib["tf"]))
        scored.sort(key=lambda x: x[0])
        top3 = scored[:3]
        votes = Counter(tf for _, tf in top3)
        predicted = votes.most_common(1)[0][0]
        confidence = votes.most_common(1)[0][1] / len(top3)
        
        # Get motifs
        cur.execute("SELECT id, pattern_signature, frequency, pre_conditions FROM ene.flexure_patterns ORDER BY frequency DESC")
        motifs = []
        for row in cur.fetchall():
            pre = json.loads(row[3]) if isinstance(row[3], str) else row[3]
            motifs.append({"id": str(row[0]), "frequency": row[2], "tactic_family": pre.get("tactic_family", "?")})
        motifs.sort(key=lambda m: m["frequency"], reverse=True)
        
        cur.close()
        conn.close()
        return {"tactic_family": predicted, "confidence": round(confidence, 2), "nearest_motifs": motifs[:5]}
    except Exception as e:
        return {"tactic_family": "unknown", "confidence": 0.0, "nearest_motifs": [], "error": str(e)[:80]}


def parse_theorem(code: str) -> dict:
    """Extract variables and hypotheses from a Lean theorem statement."""
    vars_list = []
    hyps_list = []
    
    # Extract everything between theorem name and :=
    m = re.search(r'theorem\s+\w+\s+(.*?)\s*:=', code)
    if m:
        signature = m.group(1)
        # Split by parenthesized groups
        parts = re.findall(r'\(([^)]+)\)', signature)
        for part in parts:
            # Each part is like "h : a = b" or "n : Nat"
            sub = [p.strip() for p in part.split(":")]
            if len(sub) == 2:
                name_part = sub[0]
                type_part = sub[1]
                # If multiple names: "a b c : Nat"
                names = [n.strip() for n in name_part.split()]
                for n in names:
                    if type_part.strip() in ["Prop", "Nat", "Int", "ℕ", "ℤ"]:
                        vars_list.append(n)
                    else:
                        hyps_list.append((n, type_part.strip()))
    
    return {"variables": vars_list, "hypotheses": hyps_list}


def generate_patches(predicted_family: str, theorem_code: str, theorem_info: dict, max_patches: int = 3) -> list[str]:
    """Generate candidate tactic patches for a given tactic family."""
    patches = []
    hyps = theorem_info.get("hypotheses", [])
    vars_list = theorem_info.get("variables", [])
    
    templates = TACTIC_TEMPLATES.get(predicted_family, ["simp"])
    
    for tmpl in templates[:max_patches]:
        if "%s" in tmpl:
            # Substitute with available hypotheses
            for hyp_name, hyp_type in hyps[:3]:
                patch = tmpl % hyp_name
                patches.append(patch)
            if not hyps and vars_list:
                patch = tmpl % vars_list[0]
                patches.append(patch)
        else:
            patches.append(tmpl)
    
    # Deduplicate and limit
    seen = set()
    unique = []
    for p in patches:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique[:max_patches]


def apply_patch(original_code: str, patch_tactic: str) -> str:
    """Apply a tactic patch to a Lean proof. Replaces the by-block."""
    m = re.search(r'(:= by\s*)(.*?)(\n\s*(?:\n|theorem|def))?$', original_code, re.DOTALL)
    if m:
        prefix = original_code[:m.start(1)] + ":= by"
        patch = f"  {patch_tactic}"
        return prefix + "\n" + patch
    return original_code + "\n  " + patch_tactic


def measure_complexity(code: str) -> dict:
    """Estimate goal complexity from theorem structure."""
    n_vars = code.count("(")
    n_hyps = code.count(":=")
    n_operators = sum(1 for c in code if c in "+-*/^∧∨→¬∀∃≤≥")
    return {"variables": n_vars, "operators": n_operators, "raw_chars": len(code)}


def route_repair(lean_code: str, theorem_name: str = "unnamed",
                 max_attempts: int = 3, allowed_families: list[str] | None = None) -> dict:
    """Full route-repair loop: classify → patch → retry → measure."""
    result = {
        "theorem_name": theorem_name,
        "initial_status": "unknown",
        "predicted_tactic_family": None,
        "confidence": 0.0,
        "nearest_motifs": [],
        "attempts": [],
        "best_attempt": None,
        "recovered": False,
        "elapsed_s": 0.0,
    }
    
    t0 = time.time()
    
    # Step 1: Build a minimal trace from the original (failed) proof
    # We need a transition matrix. For a single-tactic theorem, it's 2x2.
    # For multi-tactic, parse the by-block.
    trace_tags = []
    by_match = re.search(r'by\s+(.+?)$', lean_code, re.DOTALL)
    if by_match:
        body = by_match.group(1).strip()
        for line in body.split(";"):
            t = line.strip()
            if t:
                trace_tags.append(f"step_before_{t}")
                trace_tags.append(f"step_after_{t}")
    
    if not trace_tags:
        # Default: one-step trace
        trace_tags = ["step_0_before", "step_0_after"]
    
    hs = [hashlib.sha256(t.encode()).hexdigest()[:16] for t in trace_tags]
    uniq = list(dict.fromkeys(hs))
    n = len(uniq)
    mat = [[0] * n for _ in range(n)]
    hi = {h: i for i, h in enumerate(uniq)}
    for i in range(len(hs) - 1):
        if hs[i] in hi and hs[i + 1] in hi:
            mat[hi[hs[i]]][hi[hs[i + 1]]] += 1
    
    trace = {"transition_matrix": mat, "trace_tags": trace_tags, "theorem_name": theorem_name}
    
    # Step 2: Classify against the flexure library
    classification = classify_trace_against_library(trace)
    predicted_family = classification["tactic_family"]
    result["predicted_tactic_family"] = predicted_family
    result["confidence"] = classification["confidence"]
    result["nearest_motifs"] = classification.get("nearest_motifs", [])
    result["initial_status"] = "failed"
    
    if allowed_families and predicted_family not in allowed_families:
        predicted_family = allowed_families[0]
    
    # Step 3: Generate candidate patches
    theorem_info = parse_theorem(lean_code)
    patches = generate_patches(predicted_family, lean_code, theorem_info, max_patches=max_attempts)
    
    # Step 4: Try each patch on the proof worker
    best_complexity = float("inf")
    best_attempt = None
    
    for i, patch in enumerate(patches):
        patched_code = apply_patch(lean_code, patch)
        resp = prove(patched_code, f"{theorem_name}_repair_{i}")
        ok = resp.get("ok", False)
        stdout = resp.get("stdout", "") or ""
        stderr = resp.get("stderr", "") or ""
        
        # Measure complexity delta
        complexity_before = measure_complexity(lean_code)
        complexity_after = measure_complexity(patched_code)
        delta = (complexity_before["raw_chars"] - complexity_after["raw_chars"])
        
        attempt = {
            "attempt": i + 1,
            "candidate_patch": patch,
            "tactic_family": predicted_family,
            "status": "verified" if ok else "failed",
            "goal_complexity_delta": delta,
            "variables_before": complexity_before["variables"],
            "variables_after": complexity_after["variables"],
            "stdout_preview": stdout[:200],
            "stderr_preview": stderr[:200],
        }
        result["attempts"].append(attempt)
        
        if ok:
            result["recovered"] = True
            result["best_attempt"] = attempt
            break
        
        # Track best by complexity reduction
        if delta < best_complexity:
            best_complexity = delta
            best_attempt = attempt
    
    if not result["recovered"] and best_attempt:
        result["best_attempt"] = best_attempt
    
    result["elapsed_s"] = round(time.time() - t0, 2)
    return result


FAILED_THEOREMS = [
    ("simp_add_comm", 'theorem t (a b : Nat) : a + b = b + a := by\n  simp [add_comm]'),
    ("simp_add_assoc", 'theorem t (a b c : Nat) : (a + b) + c = a + (b + c) := by\n  simp [add_assoc]'),
    ("rw_mul_comm", 'theorem t (a b : Nat) : a * b = b * a := by\n  rw [mul_comm]'),
    ("rw_add_comm", 'theorem t (a b : Nat) : a + b = b + a := by\n  rw [add_comm a b]'),
    ("induct_add_zero", 'theorem t (n : Nat) : n + 0 = n := by\n  induction n with k IH; rfl; simp [add_succ, IH]'),
    ("omega_chain_unsat", 'theorem t (x : Nat) : x < x := by\n  omega'),
    ("fail_unsat", 'theorem t (x : Nat) (h : x > 0) : x = 0 := by\n  omega'),
    ("fail_type_mismatch", 'theorem t (n : Nat) : n = ("hello" : String) := by\n  rfl'),
    ("logic_or", 'theorem t (A B : Prop) : A ∨ B → B ∨ A := by\n  intro h; cases h; right; exact h; left; exact h'),
]


def main():
    print("Route-Repair Loop v1 benchmark\n", flush=True)
    
    results = []
    recovered = 0
    total_attempts = 0
    
    for name, code in FAILED_THEOREMS:
        print(f"  [{name:30s}] ", end="", flush=True)
        r = route_repair(code, name, max_attempts=3)
        
        best = r["best_attempt"] or {}
        status = "RECOVERED" if r["recovered"] else "still_broken"
        print(f"{status:15s} pred={r['predicted_tactic_family']:15s} "
              f"conf={r['confidence']:.2f} patches={len(r['attempts'])} "
              f"elapsed={r['elapsed_s']:.1f}s", flush=True)
        
        results.append(r)
        if r["recovered"]:
            recovered += 1
        total_attempts += len(r["attempts"])
    
    # Summary
    print(f"\n{'='*60}", flush=True)
    print("ROUTE-REPAIR BENCHMARK SUMMARY", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"Total theorems: {len(results)}", flush=True)
    print(f"Recovered: {recovered}/{len(results)} = {recovered/len(results):.0%}", flush=True)
    print(f"Total patches tried: {total_attempts}", flush=True)
    
    # Per-family stats
    by_family = defaultdict(lambda: {"trials": 0, "recovered": 0})
    for r in results:
        fam = r["predicted_tactic_family"]
        by_family[fam]["trials"] += 1
        if r["recovered"]:
            by_family[fam]["recovered"] += 1
        for att in r["attempts"]:
            pass
    
    print(f"\nPer-family recovery:", flush=True)
    for fam, stats in sorted(by_family.items(), key=lambda x: -x[1]["trials"]):
        rec_rate = stats["recovered"] / max(stats["trials"], 1)
        print(f"  {fam:20s}: {stats['recovered']:2d}/{stats['trials']:2d} = {rec_rate:.0%}", flush=True)
    
    # Mean patches per theorem
    avg_patches = total_attempts / max(len(results), 1)
    print(f"\nAvg patches per theorem: {avg_patches:.1f}", flush=True)
    print(f"Avg elapsed per theorem: {sum(r['elapsed_s'] for r in results)/len(results):.1f}s", flush=True)
    
    # Save
    report_path = os.path.join(os.path.dirname(__file__), "../..",
                               "shared-data/pist_route_repair_benchmark.json")
    with open(report_path, "w") as f:
        json.dump({"n_theorems": len(results), "recovered": recovered,
                    "total_attempts": total_attempts, "results": results,
                    "summary": {"recovery_rate": round(recovered / max(len(results), 1), 4),
                                "per_family": {f: round(s["recovered"] / max(s["trials"], 1), 3)
                                              for f, s in by_family.items()}}}, f, indent=2)
    print(f"\nReport: {report_path}", flush=True)


if __name__ == "__main__":
    main()
