#!/usr/bin/env python3
"""Route-Repair v1.3a: PIST-NUVMAP routing with database-backed motif ranking.

Queries ene.flexures for all candidate motifs, computes NUVMAP displacement scores,
and selects the best obstruction type via address-space ranking.
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
FAILURE_SESSION = "9b1f9591-1c34-4c21-aeb8-594448b82003"

PHI_INV = 0.618034
NUVMAP_DIMS = 16
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

def connect():
    host=os.environ.get("RDS_HOST","database-1-instance-1.cghu8yqogqwo.us-east-1.rds.amazonaws.com")
    port=os.environ.get("RDS_PORT","5432"); user=os.environ.get("RDS_USER","postgres")
    db=os.environ.get("RDS_DB","postgres")
    token=os.environ.get("RDS_IAM_TOKEN","")
    if not token:
        token=subprocess.check_output(["aws","rds","generate-db-auth-token","--region",os.environ.get("AWS_REGION","us-east-1"),
            "--hostname",host,"--port",port,"--username",user],text=True).strip()
    import psycopg2
    return psycopg2.connect(host=host,port=port,user=user,password=token,dbname=db,sslmode="require")


def compute_nuvmap(features):
    vec = [features.get(k,0) for k in V2_FEATURES]
    while len(vec) < NUVMAP_DIMS: vec.append(0.0)
    vec = vec[:NUVMAP_DIMS]
    max_abs = max(max(abs(v) for v in vec), 1e-9)
    qvec = [v/max_abs for v in vec]
    center = qvec[:]; coords = [0.0]*NUVMAP_DIMS
    for _ in range(5):
        coords = [center[i] + PHI_INV*(coords[i]-center[i]) for i in range(NUVMAP_DIMS)]
    density = max(0, min(1, sum(abs(c) for c in coords)/NUVMAP_DIMS))
    residual = max(0, min(1, abs(coords[0]-center[0])))
    confidence = max(0, min(1, 1.0 - residual))
    ev_max = abs(features.get("adjacency_eigenvalue_max",0))
    mode = "high" if ev_max>0.7 else "mid" if ev_max>0.4 else "low" if ev_max>0.1 else "transient"
    semantic = max(0, min(1, abs(features.get("density",0))))
    return {"address":hashlib.sha256(str([round(c,6) for c in coords]).encode()).hexdigest()[:16],
            "coords":[round(c,4) for c in coords[:4]],
            "spectral_mode":mode,"density_q0_16":int(density*65536),
            "confidence_q0_16":int(confidence*65536),"semantic_load_q0_16":int(semantic*65536),
            "residual_load_q0_16":int(residual*65536)}

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
    neg=[[-lap[i][j] for j in range(n)] for i in range(n)]; nm=pe(neg)
    ata=[[sum(matrix[k][i]*matrix[k][j] for k in range(n)) for j in range(n)] for i in range(n)]
    sva=math.sqrt(max(0,pe(ata)))
    rank=sum(1 for row in matrix if sum(row)>0)
    total=sum(sum(r) for r in matrix); frob=math.sqrt(sum(cell*cell for row in matrix for cell in row))
    lap0=sum(1 for i in range(n) if abs(sum(matrix[i])-matrix[i][i])<1e-9)
    return {"matrix_size":n,"rank":rank,"spectral_gap":round(gap,6),"density":round(total/max(n*n,1),6),
            "trace":sum(matrix[i][i] for i in range(n)),"frobenius_norm":round(frob,6),"laplacian_zero_count":lap0,
            "adjacency_eigenvalue_max":round(sm,6),"adjacency_eigenvalue_second":round(max(0,sm-max(0,sm-sm2)),6),
            "laplacian_eigenvalue_max":round(lm,6),"laplacian_eigenvalue_min":round(-nm,6),
            "singular_value_max":round(sva,6)}

def is_degenerate(f): return f.get("matrix_size",0)<=2 or f.get("rank",0)==0 or f.get("spectral_gap",0)==0
def extract_text_features(code):
    tactic="unknown"
    if "by " in code or "by\n" in code:
        m=re.search(r'by\s+(\S+)',code)
        if m: tactic=m.group(1)
    hyps=re.findall(r'\(([^)]+:\s*[^)]+)\)',code)
    hyp_types=[p.split(":")[1].strip() if ":" in p else "" for p in hyps]
    has_eq=any("=" in t for t in hyp_types) or "=" in code
    has_arith=any(c in code for c in "+-*/") or "omega" in tactic
    has_constructor="∧" in code or "∨" in code or "→" in code
    has_inductive=any(n in code.lower() for n in ["nat","list","option"])
    return {"tactic":tactic,"hypothesis_count":len(hyps),"has_equality":has_eq,
            "has_arithmetic":has_arith,"has_constructor":has_constructor,"has_inductive":has_inductive}

def classify_obstruction(tf):
    t=tf.get("tactic",""); eq=tf.get("has_equality",False); ar=tf.get("has_arithmetic",False)
    co=tf.get("has_constructor",False); ind=tf.get("has_inductive",False); nh=tf.get("hypothesis_count",0)
    if t in ("rw","rw_simp") and eq: return "missing_rewrite_direction"
    if co: return "case_split_missing"
    if ar and t in ("simp","rfl","omega"): return "arithmetic_gap"
    if t=="rfl" and nh>0: return "missing_assumption_bridge"
    if ind and t in ("simp","rfl"): return "induction_incomplete"
    if t=="simp": return "simplifier_gap"
    return "other"

def generate_patches(obs,code,max_p=3):
    templates=REPAIR_POLICY.get(obs,[])
    hyps=re.findall(r'\(([^)]+:\s*[^)]+)\)',code)
    hn=[]
    for h in hyps:
        p=h.split(":"); np=p[0].strip(); tp=":".join(p[1:]).strip()
        if len(np.split())==1 and tp not in ("Prop","Nat","Int","ℕ","ℤ","Type"):
            hn.append(np.strip())
    fh=hn[0] if hn else "h"
    patches=[(tmpl%fh if "%s" in tmpl else tmpl) for tmpl in templates]
    return patches[:max_p]

def nuvmap_score(delta_nuvmap, motif_support=1, obs_match=False):
    s=0.0
    s+=delta_nuvmap.get("confidence_delta",0)*0.4
    s-=delta_nuvmap.get("residual_load_delta",0)*0.3
    s-=delta_nuvmap.get("semantic_load_delta",0)*0.2
    s+=min(motif_support/10,1.0)*0.3
    s+=0.2 if obs_match else 0.0
    return s

def compute_delta_nuvmap(before,after):
    return {k:after.get(k,0)-before.get(k,0) for k in ["density_q0_16","confidence_q0_16","semantic_load_q0_16","residual_load_q0_16"]}

def build_trace(name,code):
    try:
        instr,tags=instrument_theorem(code)
        if not tags: return None
        resp=prove(instr,name+"_v13")
        stdout=resp.get("stdout","") or ""
        found=[l.split("@@PIST_TRACE_JSON@@")[1].strip() for l in stdout.split("\n") if "@@PIST_TRACE_JSON@@" in l]
        if not found: return None
        hs=[hashlib.sha256(t.encode()).hexdigest()[:16] for t in found]
        uniq=list(dict.fromkeys(hs)); n=len(uniq)
        mat=[[0]*n for _ in range(n)]
        hi={h:i for i,h in enumerate(uniq)}
        for i in range(len(hs)-1):
            if hs[i] in hi and hs[i+1] in hi: mat[hi[hs[i]]][hi[hs[i+1]]]+=1
        return compute_spectral(mat)
    except: return None


def route_repair_v13(name, code):
    resp=prove(code,name+"_init")
    if resp.get("ok",False):
        return {"name":name,"initial_status":"verified","recovered":False}
    
    sp=build_trace(name,code) or {"matrix_size":0,"rank":0,"spectral_gap":0}
    nuvmap_before=compute_nuvmap(sp)
    tf=extract_text_features(code)
    
    # Step 1: Query the flexure library for all candidate obstruction types
    try:
        conn=connect(); cur=conn.cursor()
        cur.execute("SELECT decision_signals FROM ene.flexures WHERE session_id=%s OR session_id=%s",
                    (LIBRARY_SESSION,FAILURE_SESSION))
        library=[]
        for row in cur.fetchall():
            sig=json.loads(row[0]) if isinstance(row[0],str) else row[0]
            sl=sig.get("spectral",{}); oi=sig.get("obstruction_type","?"); tf2=sig.get("tactic_family","?")
            library.append({"spectral":sl,"obstruction":oi,"tactic_family":tf2})
        cur.close(); conn.close()
    except:
        library=[]
    
    # Step 2: Score each candidate obstruction type by NUVMAP displacement
    candidate_scores=defaultdict(lambda:{"count":0,"total_score":0,"tactic_family":""})
    for lib in library:
        ls=lib.get("spectral",{})
        lib_nuvmap=compute_nuvmap(ls) if ls else nuvmap_before
        delta=compute_delta_nuvmap(nuvmap_before,lib_nuvmap)
        obs=lib.get("obstruction","?")
        score=nuvmap_score(delta, motif_support=1, obs_match=obs==classify_obstruction(tf))
        candidate_scores[obs]["count"]+=1
        candidate_scores[obs]["total_score"]+=score
        candidate_scores[obs]["tactic_family"]=lib.get("tactic_family","?")
    
    # Step 3: Pick the obstruction with the best average NUVMAP score
    best_obs="other"; best_avg_score=-999
    for obs,stats in candidate_scores.items():
        avg=stats["total_score"]/max(stats["count"],1)
        if avg>best_avg_score:
            best_avg_score=avg; best_obs=obs
    
    obstruction=best_obs
    
    # Step 4: Generate and try patches
    patches=generate_patches(obstruction,code)
    attempts=[]; best_attempt=None; recovered=False
    init_vars=code.count("("); init_ops=sum(1 for c in code if c in "+-*/^∧∨→¬∀∃≤≥")
    
    for i,patch in enumerate(patches):
        patched=code.split(":=")[0]+":= by\n  "+patch if ":=" in code else code+"\n  "+patch
        r=prove(patched,f"{name}_repair_{i}")
        ok=r.get("ok",False)
        av=patched.count("("); ao=sum(1 for c in patched if c in "+-*/^∧∨→¬∀∃≤≥")
        delta=(init_vars+init_ops)-(av+ao)
        delta_nuvmap=compute_delta_nuvmap(nuvmap_before,compute_nuvmap(sp))
        score=nuvmap_score(delta_nuvmap,motif_support=candidate_scores[obstruction]["count"],obs_match=True)
        attempt={"attempt":i+1,"patch":patch,"obstruction":obstruction,"ok":ok,"delta":delta,"score":round(score,4)}
        attempts.append(attempt)
        if ok:
            recovered=True; best_attempt=attempt; break
        if not best_attempt or score>(best_attempt.get("score",-999) or -999):
            best_attempt=attempt
    
    return {"name":name,"obstruction":obstruction,"initial_status":"failed","recovered":recovered,
            "attempts":attempts,"best_attempt":best_attempt,
            "nuvmap_before":nuvmap_before,
            "routing_method":"nuvmap_ranked",
            "candidate_scores":{o:round(s["total_score"]/max(s["count"],1),3) for o,s in candidate_scores.items()}}


def main():
    print("Route-Repair v1.3a: PIST-NUVMAP database-backed ranking\n")
    test_set=FAILURE_THEOREMS[:30]
    results=[]
    for i,(n,c) in enumerate(test_set):
        print(f"  [{i+1}/{len(test_set)}] {n:35s} ... ",end="",flush=True)
        r=route_repair_v13(n,c)
        if r["initial_status"]=="verified": print("already verified"); continue
        s="RECOVERED" if r["recovered"] else "improved" if (r.get("best_attempt") or {}).get("delta",0)>0 else "no change"
        cand=r.get("candidate_scores",{})
        top_cand=sorted(cand.items(),key=lambda x:-x[1])[:3] if cand else []
        top_str=" ".join(f"{o}={s:.1f}" for o,s in top_cand)
        print(f"{s:15s} obs={r['obstruction']:30s} top={top_str[:40]}",flush=True)
        results.append(r)
    
    n=len(results); rec=sum(1 for r in results if r["recovered"])
    print(f"\n{'='*60}\nV1.3a NUVMAP RANKING\n{'='*60}")
    print(f"Test: {n} failed | Recovered: {rec} ({rec/max(n,1):.0%})")
    
    # Per-obstruction
    by_obs=defaultdict(lambda:{"t":0,"r":0})
    for r in results:
        o=r["obstruction"]; by_obs[o]["t"]+=1
        if r["recovered"]: by_obs[o]["r"]+=1
    print(f"\nPer-obstruction:")
    for o,s in sorted(by_obs.items(),key=lambda x:-x[1]["t"]):
        print(f"  {o:30s}: n={s['t']:2d} rec={s['r']/max(s['t'],1):.0%}")
    
    # Compare with v1.2
    print(f"\nComparison: v1.2=36% vs v1.3a={rec/max(n,1):.0%}")
    
    rp_path=os.path.join(os.path.dirname(__file__),"..","..","shared-data","pist_route_repair_v13a_benchmark.json")
    with open(rp_path,"w") as f: json.dump({"n":n,"recovered":rec,"results":results},f,indent=2)
    print(f"Report: {rp_path}")

if __name__=="__main__":
    main()
