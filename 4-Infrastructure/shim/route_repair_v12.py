#!/usr/bin/env python3
"""Route-Repair v1.2: hybrid spectral + text/goal-state obstruction classification.

Gate: if matrix_size >= 3 and rank > 0 → spectral flexure retrieval
       else → text/goal-state obstruction classifier
"""

import hashlib, json, math, os, re, subprocess, sys, time, uuid
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))
from lean_trace_bridge_v2 import instrument_theorem, prove
from failure_flexure_bank import FAILURE_THEOREMS

WORKER_URL = os.environ.get("CANARY_WORKER_URL", "http://100.110.163.82:8787")
PROOF_SERVER_TOKEN = os.environ.get("PROOF_SERVER_TOKEN", "")
if not PROOF_SERVER_TOKEN:
    tf = os.environ.get("PROOF_SERVER_TOKEN_FILE", os.path.expanduser("~/.config/ene/language-proof-server.token"))
    try: PROOF_SERVER_TOKEN = Path(tf).read_text().strip()
    except: pass

LIBRARY_SESSION = "a4a0eb20-93fe-413e-8e0b-50334bb778d8"

V2_FEATURES = ["matrix_size","rank","spectral_gap","laplacian_zero_count","density",
               "adjacency_eigenvalue_max","adjacency_eigenvalue_second",
               "laplacian_eigenvalue_max","laplacian_eigenvalue_min",
               "singular_value_max","trace","frobenius_norm"]

REPAIR_POLICY = {
    "missing_rewrite_direction": ["rw [← %s]", "rw [%s]"],
    "missing_assumption_bridge": ["assumption", "exact %s", "apply %s"],
    "arithmetic_gap": ["omega"],
    "case_split_missing": ["cases %s", "constructor"],
    "induction_incomplete": ["induction %s"],
    "simplifier_gap": ["simp", "simp [%s]"],
    "coercion_mismatch": ["norm_cast", "exact %s"],
    "order_inequality_gap": ["omega"],
}


def compute_spectral(matrix):
    n=len(matrix)
    if n==0: return {}
    sym=[[(matrix[i][j]+matrix[j][i])/2 for j in range(n)] for i in range(n)]
    lap=[[sum(sym[i]) if i==j else -sym[i][j] for j in range(n)] for i in range(n)]
    def pe(m):
        v=[1.0/math.sqrt(n)]*n
        for _ in range(100):
            vn=[sum(m[i][j]*v[j] for j in range(n)) for i in range(n)]
            nm=math.sqrt(sum(x*x for x in vn))
            v=[x/nm for x in vn] if nm>0 else v
        num=sum(v[i]*sum(m[i][j]*v[j] for j in range(n)) for i in range(n))
        return num/max(sum(v[i]*v[i] for i in range(n)),1e-12)
    sm=pe(sym); lm=pe(lap)
    sh=[[sym[i][j]-0.9*sm*(i==j) for j in range(n)] for i in range(n)]
    sm2=pe(sh); gap=sm-max(0,sm-sm2)
    ev_second=sm-max(0,sm-sm2)
    neg=[[-lap[i][j] for j in range(n)] for i in range(n)]
    nm=pe(neg)
    ata=[[sum(matrix[k][i]*matrix[k][j] for k in range(n)) for j in range(n)] for i in range(n)]
    sva=math.sqrt(max(0,pe(ata)))
    rank=sum(1 for row in matrix if sum(row)>0)
    total=sum(sum(r) for r in matrix)
    frob=math.sqrt(sum(cell*cell for row in matrix for cell in row))
    lap0=sum(1 for i in range(n) if abs(sum(matrix[i])-matrix[i][i])<1e-9)
    return {"matrix_size":n,"rank":rank,"spectral_gap":round(gap,6),"density":round(total/max(n*n,1),6),
            "trace":sum(matrix[i][i] for i in range(n)),"frobenius_norm":round(frob,6),
            "laplacian_zero_count":lap0,"adjacency_eigenvalue_max":round(sm,6),
            "adjacency_eigenvalue_second":round(ev_second,6),
            "laplacian_eigenvalue_max":round(lm,6),"laplacian_eigenvalue_min":round(-nm,6),
            "singular_value_max":round(sva,6)}


def is_degenerate(features: dict) -> bool:
    return features.get("matrix_size", 0) <= 2 or features.get("rank", 0) == 0 or features.get("spectral_gap", 0) == 0


def extract_text_features(code: str) -> dict:
    """Extract text/goal-state features from a Lean theorem for obstruction classification."""
    code_lower = code.lower()
    tactic = "unknown"
    if "by " in code or "by\n" in code:
        m = re.search(r'by\s+(\S+)', code)
        if m: tactic = m.group(1)
    
    # Extract hypotheses
    hyps = []
    for m in re.finditer(r'\(([^)]+:\s*[^)]+)\)', code):
        parts = m.group(1).split(":")
        if len(parts) >= 2:
            names = parts[0].strip().split()
            typ = ":".join(parts[1:]).strip()
            for n in names:
                hyps.append((n.strip(), typ))
    
    hyp_types = [t for _, t in hyps]
    hyp_names = [n for n, _ in hyps]
    
    # Goal analysis
    goal = code  # use full code for pattern detection since goal extraction is unreliable
    
    has_equality = any("=" in t for t in hyp_types) or "=" in goal
    has_order = any(t in ["Nat","ℕ","Int","ℤ"] for t in hyp_types) and any(c in goal for c in "≤≥<>")
    has_arithmetic = any(c in code for c in "+-*/") or "omega" in tactic
    has_constructor = "∧" in goal or "∨" in goal or "→" in goal or "↔" in goal
    has_inductive = any(n in code_lower for n in ["nat","list","option"])
    
    op_counts = {}
    for c in "+-*/^∧∨→¬∀∃≤≥=":
        op_counts[c] = code.count(c)
    
    return {
        "tactic": tactic, "goal": goal[:100],
        "hypothesis_count": len(hyps), "hypothesis_names": hyp_names[:5],
        "hypothesis_types": hyp_types[:5],
        "has_equality": has_equality, "has_order": has_order,
        "has_arithmetic": has_arithmetic, "has_constructor": has_constructor,
        "has_inductive": has_inductive,
        "operator_counts": {k: v for k, v in op_counts.items() if v > 0},
    }


def classify_obstruction(tf: dict) -> str:
    """Classify obstruction type from text features — ordered by specificity."""
    tactic = tf.get("tactic", "")
    has_eq = tf.get("has_equality", False)
    has_order = tf.get("has_order", False)
    has_arith = tf.get("has_arithmetic", False)
    has_constructor = tf.get("has_constructor", False)
    has_inductive = tf.get("has_inductive", False)
    n_hyps = tf.get("hypothesis_count", 0)
    goal = tf.get("goal", "")
    
    # RW with equality → rewrite direction
    if tactic in ("rw", "rw_simp") and has_eq:
        return "missing_rewrite_direction"
    # Constructor goal with rfl/simp → case split
    if has_constructor or ("∧" in goal or "∨" in goal or "→" in goal):
        return "case_split_missing"
    # Arithmetic symbols with simp/rfl/omega that are _not_ pure equality — arithmetic gap
    if has_arith and tactic in ("simp", "rfl", "omega"):
        return "arithmetic_gap"
    # RFL with hypotheses and no constructor target → assumption bridge failure
    if tactic == "rfl" and n_hyps > 0:
        return "missing_assumption_bridge"
    # Inductive type → induction incomplete
    if has_inductive and tactic in ("simp", "rfl"):
        return "induction_incomplete"
    # Simp with no clear pattern → simplifier gap
    if tactic == "simp":
        return "simplifier_gap"
    # Order/inequality symbols
    if has_order:
        return "order_inequality_gap"
    # Coercion-like patterns
    if tactic == "rfl" and any(c in str(tf) for c in ["nat", "int"]):
        return "coercion_mismatch"
    return "other"


def build_trace(name: str, code: str) -> dict | None:
    """Run a theorem through the trace bridge and return spectral + text features."""
    try:
        instr, tags = instrument_theorem(code)
        if not tags: return None
        resp = prove(instr, name + "_flex")
        stdout = resp.get("stdout", "") or ""
        found = [l.split("@@PIST_TRACE_JSON@@")[1].strip() for l in stdout.split("\n") if "@@PIST_TRACE_JSON@@" in l]
        if not found: return None
        hs = [hashlib.sha256(t.encode()).hexdigest()[:16] for t in found]
        uniq = list(dict.fromkeys(hs)); n = len(uniq)
        mat = [[0] * n for _ in range(n)]
        hi = {h: i for i, h in enumerate(uniq)}
        for i in range(len(hs) - 1):
            if hs[i] in hi and hs[i + 1] in hi: mat[hi[hs[i]]][hi[hs[i + 1]]] += 1
        sp = compute_spectral(mat)
        tf = extract_text_features(code)
        return {"name": name, "spectral": sp, "text_features": tf, "code": code}
    except:
        return None


def connect():
    host = os.environ.get("RDS_HOST", "database-1-instance-1.cghu8yqogqwo.us-east-1.rds.amazonaws.com")
    port = os.environ.get("RDS_PORT", "5432"); user = os.environ.get("RDS_USER", "postgres")
    db = os.environ.get("RDS_DB", "postgres")
    token = os.environ.get("RDS_IAM_TOKEN", "")
    if not token:
        token = subprocess.check_output(["aws", "rds", "generate-db-auth-token",
            "--region", os.environ.get("AWS_REGION", "us-east-1"),
            "--hostname", host, "--port", port, "--username", user], text=True).strip()
    import psycopg2
    return psycopg2.connect(host=host, port=port, user=user, password=token, dbname=db, sslmode="require")


def spectral_route(features, library_session, failure_session):
    """kNN against flexure library for multi-step traces."""
    conn = connect(); cur = conn.cursor()
    cur.execute("SELECT decision_signals FROM ene.flexures WHERE session_id=%s OR session_id=%s",
                (library_session, failure_session))
    library = []
    for row in cur.fetchall():
        sig = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        sl = sig.get("spectral", {}); lv = [sl.get(k, 0) for k in V2_FEATURES]
        library.append({"features": lv, "obs": sig.get("obstruction_type", "?"), "tf": sig.get("tactic_family", "?")})
    cur.close(); conn.close()
    
    if not library: return "other"
    vec = [features.get(k, 0) for k in V2_FEATURES]
    scored = [(math.sqrt(sum((vec[i] - l["features"][i])**2 for i in range(len(vec)))), l) for l in library if len(l["features"]) == len(vec)]
    scored.sort(key=lambda x: x[0])
    top3 = scored[:3]
    obs_votes = Counter(lib["obs"] for _, lib in top3)
    return obs_votes.most_common(1)[0][0] if obs_votes else "other"


def text_route(tf: dict) -> str:
    """Classify obstruction from text features (fallback for degenerate traces)."""
    return classify_obstruction(tf)


def generate_patches(obstruction_type: str, code: str, max_patches: int = 3) -> list[str]:
    """Generate repair patches for an obstruction type."""
    templates = REPAIR_POLICY.get(obstruction_type, [])
    # Extract hypothesis names — filter to single-named hypotheses (not type decls)
    hyps = re.findall(r'\(([^)]+:\s*[^)]+)\)', code)
    hyp_names = []
    for h in hyps:
        parts = h.split(":")
        names_part = parts[0].strip()
        type_part = ":".join(parts[1:]).strip()
        # A hypothesis has exactly one name (like "h : A" not "A B : Prop")
        if len(names_part.split()) == 1 and type_part not in ("Prop", "Nat", "Int", "ℕ", "ℤ", "Type"):
            hyp_names.append(names_part.strip())
    first_hyp = hyp_names[0] if hyp_names else "h"
    
    patches = []
    for tmpl in templates:
        if "%s" in tmpl:
            patches.append(tmpl % first_hyp)
        else:
            patches.append(tmpl)
    return patches[:max_patches]


def route_repair(name: str, code: str, library_session: str, failure_session: str, max_attempts: int = 5) -> dict:
    """Hybrid route-repair: spectral for multi-step, text for degenerate."""
    # Build trace
    instr, tags = instrument_theorem(code)
    if not tags:
        sp = {"matrix_size": 0, "rank": 0, "spectral_gap": 0}
    else:
        hs = [hashlib.sha256(t.encode()).hexdigest()[:16] for t in tags]
        uniq = list(dict.fromkeys(hs)); n = len(uniq)
        mat = [[0] * n for _ in range(n)]
        hi = {h: i for i, h in enumerate(uniq)}
        for i in range(len(hs) - 1):
            if hs[i] in hi and hs[i+1] in hi:
                mat[hi[hs[i]]][hi[hs[i+1]]] += 1
        sp = compute_spectral(mat)
    
    tf = extract_text_features(code)
    
    # Degeneracy gate
    if is_degenerate(sp):
        obstruction = text_route(tf)
        routing_method = "text_fallback"
    else:
        obstruction = spectral_route(sp, library_session, failure_session)
        routing_method = "spectral_flexure"
    
    # Verify initial failure
    resp = prove(code, name + "_init")
    if resp.get("ok", False):
        return {"name": name, "initial_status": "verified", "recovered": False, "notes": "already verified"}
    
    # Generate patches
    patches = generate_patches(obstruction, code, max_patches=max_attempts)
    init_vars = code.count("("); init_ops = sum(1 for c in code if c in "+-*/^∧∨→¬∀∃≤≥")
    attempts = []; best_delta = -999; best_attempt = None; recovered = False
    
    for i, patch in enumerate(patches):
        patched = code.split(":=")[0] + ":= by\n  " + patch
        r = prove(patched, f"{name}_repair_{i}")
        ok = r.get("ok", False)
        av = patched.count("("); ao = sum(1 for c in patched if c in "+-*/^∧∨→¬∀∃≤≥")
        delta = (init_vars + init_ops) - (av + ao)
        if delta > best_delta:
            best_delta = delta; best_attempt = {"patch": patch, "delta": delta, "ok": ok}
        if ok:
            recovered = True; best_attempt = {"patch": patch, "delta": delta, "ok": ok}; break
        attempts.append({"attempt": i + 1, "patch": patch, "obstruction": obstruction, "ok": ok, "delta": delta})
    
    return {
        "name": name, "obstruction": obstruction,
        "routing_method": routing_method,
        "initial_status": "failed", "recovered": recovered,
        "best_delta": best_delta, "partial_improvement": best_delta > 0,
        "attempts": attempts, "best_attempt": best_attempt,
        "matrix_size": sp.get("matrix_size", 0),
        "rank": sp.get("rank", 0),
        "tactic": tf.get("tactic", "?"),
        "has_equality": tf.get("has_equality", False),
        "has_arithmetic": tf.get("has_arithmetic", False),
        "has_constructor": tf.get("has_constructor", False),
    }


def main():
    print("Route-Repair v1.2: hybrid spectral + text obstruction classifier\n")
    failure_session = "9b1f9591-1c34-4c21-aeb8-594448b82003"
    test_set = FAILURE_THEOREMS[:30]
    
    results = []
    for i, (n, c) in enumerate(test_set):
        print(f"  [{i+1}/{len(test_set)}] {n:35s} ... ", end="", flush=True)
        r = route_repair(n, c, LIBRARY_SESSION, failure_session)
        if r["initial_status"] == "verified":
            print("already verified"); continue
        s = "RECOVERED" if r["recovered"] else "improved" if r.get("partial_improvement") else "no change"
        print(f"{s:15s} obs={r['obstruction']:30s} method={r['routing_method']:18s} "
              f"tactic={r['tactic']:8s} eq={r['has_equality']} arith={r['has_arithmetic']}", flush=True)
        results.append(r)
    
    n = len(results); rec = sum(1 for r in results if r["recovered"]); part = sum(1 for r in results if r.get("partial_improvement"))
    
    print(f"\n{'='*60}\nV1.2 HYBRID REPORT\n{'='*60}")
    print(f"Test: {n} failed | Recovered: {rec} ({rec/max(n,1):.0%}) | Partial: {part} ({part/max(n,1):.0%})")
    
    # Obstruction distribution
    obs_dist = Counter(r["obstruction"] for r in results)
    print(f"\nObstruction distribution:", flush=True)
    for obs, cnt in sorted(obs_dist.items(), key=lambda x: -x[1]):
        rec_obs = sum(1 for r in results if r["obstruction"] == obs and r["recovered"])
        print(f"  {obs:30s}: n={cnt:2d} rec={rec_obs}")
    
    routing = Counter(r["routing_method"] for r in results)
    print(f"\nRouting: text_fallback={routing.get('text_fallback', 0)}, spectral={routing.get('spectral_flexure', 0)}")
    
    rp_path = os.path.join(os.path.dirname(__file__), "..", "..", "shared-data", "pist_route_repair_v12_benchmark.json")
    with open(rp_path, "w") as f:
        json.dump({"n": n, "recovered": rec, "partial": part, "results": results, "routing": dict(routing)}, f, indent=2)
    print(f"\nReport: {rp_path}")


if __name__ == "__main__":
    main()
