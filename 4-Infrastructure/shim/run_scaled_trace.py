#!/usr/bin/env python3
"""Complete Tier 2B scaled batch — process all theorems with incremental save."""
import hashlib, json, os, sys, time
from math import sqrt
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))
from lean_trace_bridge_v2 import instrument_theorem, prove
from combined_theorems import UNIQUE_THEOREMS

VECTORS_PATH = os.path.join(os.path.dirname(__file__), "../..", "shared-data/pist_trace_scaled_vectors.jsonl")
LABELS_PATH = os.path.join(os.path.dirname(__file__), "../..", "shared-data/pist_trace_scaled_labels.jsonl")
REPORT_PATH = os.path.join(os.path.dirname(__file__), "../..", "shared-data/pist_trace_scaled_report.json")
CHECKPOINT_PATH = "/tmp/scaled_checkpoint.json"

PROOF_SERVER_TOKEN = os.environ.get("PROOF_SERVER_TOKEN", "")

def spectral(matrix):
    n = len(matrix)
    if n == 0: return {}
    sym = [[(matrix[i][j]+matrix[j][i])/2.0 for j in range(n)] for i in range(n)]
    lap = [[sum(sym[i]) if i==j else -sym[i][j] for j in range(n)] for i in range(n)]
    def pe(m):
        v = [1.0/sqrt(n)]*n
        for _ in range(100):
            vn = [sum(m[i][j]*v[j] for j in range(n)) for i in range(n)]
            nm = sqrt(sum(x*x for x in vn))
            v = [x/nm for x in vn] if nm > 0 else v
        num = sum(v[i]*sum(m[i][j]*v[j] for j in range(n)) for i in range(n))
        return num/max(sum(v[i]*v[i] for i in range(n)), 1e-12)
    sm = pe(sym)
    sh = [[sym[i][j]-0.9*sm*(i==j) for j in range(n)] for i in range(n)]
    sm2 = pe(sh)
    gap = sm - max(0, sm - sm2)
    return {"matrix_size": n, "rank": sum(1 for r in matrix if sum(r)>0),
            "spectral_gap": round(gap,6), "laplacian_zero_count": sum(1 for i in range(n) if sum(lap[i])<1e-9),
            "density": round(sum(sum(r) for r in matrix)/max(n*n,1),6),
            "eigenvalue_max": round(sm,6)}

def process(name, code):
    try:
        instr, tags = instrument_theorem(code)
        if not tags: return None
        t0 = time.time()
        resp = prove(instr, name+"_t2b")
        dt = time.time() - t0
        if not resp.get("ok", False) and any(e in str(resp) for e in ["timeout","error","curl"]):
            return None
        stdout = resp.get("stdout","") or ""
        found = [l.split("@@PIST_TRACE_JSON@@")[1].strip() for l in stdout.split("\n") if "@@PIST_TRACE_JSON@@" in l]
        if not found: return None
        hs = [hashlib.sha256(t.encode()).hexdigest()[:16] for t in found]
        uniq = list(dict.fromkeys(hs))
        n = len(uniq)
        mat = [[0]*n for _ in range(n)]
        hi = {h:i for i,h in enumerate(uniq)}
        for i in range(len(hs)-1):
            if hs[i] in hi and hs[i+1] in hi:
                mat[hi[hs[i]]][hi[hs[i+1]]] += 1
        sp = spectral(mat)
        if not sp: return None
        sp["name"] = name
        sp["status"] = "verified" if resp.get("ok") else "failed"
        sp["n_tags"] = len(found)
        sp["wall_s"] = round(dt, 2)
        return sp
    except Exception as e:
        return None

def main():
    theorems = UNIQUE_THEOREMS
    print(f"Complete batch: {len(theorems)} theorems\n", flush=True)
    
    results = []
    for i, th in enumerate(theorems):
        name = th["name"]
        code = th["code"]
        print(f"  [{i+1}/{len(theorems)}] {name:30s} ... ", end="", flush=True)
        r = process(name, code)
        if r is None:
            print("SKIP", flush=True)
        else:
            results.append(r)
            print(f"{r['status']:10s} n={r['matrix_size']:2d} rank={r['rank']:2d} gap={r['spectral_gap']:.4f}", flush=True)
        if (i+1) % 10 == 0 or i == len(theorems)-1:
            with open(CHECKPOINT_PATH, "w") as f:
                json.dump({"idx": i+1, "results": results}, f)
    
    print(f"\nProcessed: {len(results)}/{len(theorems)}", flush=True)
    
    verified = sum(1 for r in results if r["status"]=="verified")
    failed = sum(1 for r in results if r["status"]=="failed")
    print(f"Verified: {verified}, Failed: {failed}", flush=True)
    
    for label in ["verified", "failed"]:
        subset = [r for r in results if r["status"]==label]
        if subset:
            g = [r["spectral_gap"] for r in subset]
            rk = [r["rank"] for r in subset]
            sn = [r["matrix_size"] for r in subset]
            print(f"  {label:10s}: size={sum(sn)/len(sn):.1f} rank={sum(rk)/len(rk):.2f} "
                  f"gap={sum(g)/len(g):.4f}", flush=True)
    
    # Save vectors
    with open(VECTORS_PATH, "w") as f:
        for r in results:
            f.write(json.dumps(r)+"\n")
    print(f"Vectors: {VECTORS_PATH} ({len(results)} records)", flush=True)
    
    # Labels
    with open(LABELS_PATH, "w") as f:
        for r in results:
            name = r["name"]
            domain = "arithmetic" if any(k in name for k in ["rfl","simp","omega","ring","induct","algebra","with_import"]) else \
                     "logic" if any(k in name for k in ["logic","intro","apply","cases","constructor","have"]) else \
                     "order" if "order" in name else \
                     "type_error" if "type" in name else \
                     "equality" if "rw" in name else "other"
            pm = "rfl" if "rfl" in name else "simp" if "simp" in name else "omega" if "omega" in name else \
                 "ring" if "ring" in name or "calc" in name else "induction" if "induct" in name else \
                 "rw" if "rw" in name else "apply" if "apply" in name or "intro" in name or "have" in name else \
                 "cases" if "cases" in name or "constructor" in name else "other"
            rrc = "CognitiveLoadField" if pm in ("rfl","simp") else \
                  "SignalShapedRouteCompiler" if pm in ("omega","ring") else \
                  "CadForceProbeReceipt" if pm in ("rw",) else \
                  "ProjectableGeometryTopology" if pm=="induction" else \
                  "LogogramProjection" if pm in ("apply","cases") else \
                  "HoldForUnlawfulOrUnderspecifiedShape"
            f.write(json.dumps({"theorem_name":name,"proof_status":r["status"],
                                "domain_label":domain,"proof_method_label":pm,
                                "manual_rrc_shape":rrc})+"\n")
    print(f"Labels: {LABELS_PATH}", flush=True)
    
    # LOOCV
    feats = ["matrix_size","rank","spectral_gap","laplacian_zero_count","density","eigenvalue_max"]
    vecs = [[r.get(f,0) for f in feats] for r in results]
    n = len(vecs)
    if n == 0: print("No results"); return
    means = [sum(v[i] for v in vecs)/n for i in range(6)]
    stds = [sqrt(sum((v[i]-means[i])**2 for v in vecs)/max(n-1,1)) for i in range(6)]
    stds = [s if s>1e-9 else 1.0 for s in stds]
    normed = [[(v[i]-means[i])/stds[i] for i in range(6)] for v in vecs]
    
    def centroid(vecs):
        return [sum(v[i] for v in vecs)/len(vecs) for i in range(len(vecs[0]))] if vecs else []
    
    def loocv(vecs, labels):
        c, t2 = 0, 0
        for i in range(len(vecs)):
            tv = vecs[:i]+vecs[i+1:]; tl = labels[:i]+labels[i+1:]
            cents = {}
            for l in set(tl):
                cents[l] = centroid([v for v, l2 in zip(tv, tl) if l2 == l])
            preds = sorted(cents, key=lambda l: sqrt(sum((vecs[i][j]-cents[l][j])**2 for j in range(len(vecs[i])))))
            if preds[0] == labels[i]: c += 1
            if labels[i] in preds[:2]: t2 += 1
        return c/len(vecs), t2/len(vecs)
    
    print(f"\n{'='*60}", flush=True)
    print("LOOCV (Tier 2B scaled)", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"\n{'Target':25s} {'Acc':>7} {'Top-2':>7}", flush=True)
    print(f"{'-'*25} {'-'*7} {'-'*7}", flush=True)
    
    with open(LABELS_PATH) as f:
        lm = {json.loads(line)["theorem_name"]: json.loads(line) for line in f}
    
    for key, label in [("proof_status","proof status"),("domain_label","domain"),
                        ("proof_method_label","proof method"),("manual_rrc_shape","manual RRCShape")]:
        targets = [lm[r["name"]].get(key,"?") for r in results]
        acc, top2 = loocv(normed, targets)
        from collections import Counter
        base = max(Counter(targets).values())/len(targets)
        print(f"{label:25s} {acc:7.1%} {top2:7.1%} (base={base:.0%})", flush=True)
    
    with open(REPORT_PATH, "w") as f:
        json.dump({"n":len(results),"verified":verified,"failed":failed}, f, indent=2)
    print(f"\nReport: {REPORT_PATH}", flush=True)

if __name__ == "__main__":
    main()
