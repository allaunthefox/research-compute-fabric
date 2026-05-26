#!/usr/bin/env python3
"""Route-Repair Loop v1.1: Failure Flexure Expansion + full 13-dim v2 features."""
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

V2_FEATURES = ["matrix_size", "rank", "spectral_gap", "laplacian_zero_count", "density",
               "adjacency_eigenvalue_max", "adjacency_eigenvalue_second",
               "laplacian_eigenvalue_max", "laplacian_eigenvalue_min",
               "singular_value_max", "trace", "frobenius_norm"]

OBSTRUCTION_MAP = {"rw_missing_dir": "missing_rewrite_direction","missing_assume": "missing_assumption_bridge",
    "arith_gap": "arithmetic_gap","case_split": "case_split_missing","induction_gap": "induction_incomplete",
    "simplifier_gap": "simplifier_gap","coercion_gap": "coercion_mismatch","order_gap": "order_inequality_gap"}

def obstruction_type(name):
    for p, l in OBSTRUCTION_MAP.items():
        if name.startswith(p): return l
    return "other"

def classify_tactic(t):
    tl=t.lower()
    if "rw" in tl: return "rewrite"
    if "simp" in tl: return "normalization"
    if "omega" in tl or "nlinarith" in tl: return "arithmetic"
    if "induction" in tl: return "induction"
    if "cases" in tl or "constructor" in tl: return "case_analysis"
    if "apply" in tl or "exact" in tl: return "discharge"
    if "intro" in tl: return "introduction"
    if "have" in tl: return "lemma_introduction"
    if "rfl" in tl: return "reflexivity"
    return "unknown"

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

def build_trace(name, code):
    try:
        instr,tags=instrument_theorem(code)
        if not tags: return None
        resp=prove(instr,name+"_flex")
        stdout=resp.get("stdout","") or ""
        found=[l.split("@@PIST_TRACE_JSON@@")[1].strip() for l in stdout.split("\n") if "@@PIST_TRACE_JSON@@" in l]
        if not found: return None
        hs=[hashlib.sha256(t.encode()).hexdigest()[:16] for t in found]
        uniq=list(dict.fromkeys(hs)); n=len(uniq)
        mat=[[0]*n for _ in range(n)]
        hi={h:i for i,h in enumerate(uniq)}
        for i in range(len(hs)-1):
            if hs[i] in hi and hs[i+1] in hi:
                mat[hi[hs[i]]][hi[hs[i+1]]]+=1
        sp=compute_spectral(mat)
        sp.update({"name":name,"status":"failed","obstruction":obstruction_type(name),
                   "tactic":code.split("by")[-1].strip() if "by" in code else "unknown","code":code})
        return sp
    except: return None

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

def ingest_failure_flexures(results):
    conn=connect(); cur=conn.cursor()
    sid=str(uuid.uuid4())
    cur.execute("INSERT INTO ene.sessions(id,title,event_type,content,metadata) VALUES(%s,%s,'failure_flexure','V1.1 Failure',%s::jsonb)",
                (sid,"Failure Flexure v1.1",json.dumps({"source":"failure_flexure_bank","count":len(results)})))
    for r in results:
        fid=str(uuid.uuid4()); tf=classify_tactic(r.get("tactic",""))
        sp={k:r.get(k,0) for k in V2_FEATURES}
        sig=json.dumps({"tactic":r.get("tactic","?"),"tactic_family":tf,"delta_score":abs(r.get("gap",r.get("spectral_gap",0)))*10,
            "joint_label":f"{tf}_failed_{r.get('obstruction','?')}","obstruction_type":r.get("obstruction","?"),
            "domain":"failure","proof_method":tf,"rrc_shape":"HoldForUnlawfulOrUnderspecifiedShape",
            "spectral":sp,"feature_version":"flexure-spectrum-v2"})
        sd=int(hashlib.sha256(r.get("name","?").encode()).hexdigest()[:4],16)%255
        cur.execute("INSERT INTO ene.flexures(id,session_id,step_index,pre_sidon_label,pre_residual,available_crossings,chosen_crossing,decision_signals,post_sidon_label,post_residual,converged) VALUES(%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s,%s,%s)",
                    (fid,sid,0,sd,0.5,"[]",json.dumps({"name":r.get("name","?")}),sig,sd%255,0.5,False))
    conn.commit(); cur.close(); conn.close()
    return sid

def route_repair(name, code, library_session, failure_session, max_attempts=5):
    resp=prove(code,name+"_init")
    if resp.get("ok",False):
        return {"name":name,"initial_status":"verified","recovered":False,"notes":"already verified"}
    instr,tags=instrument_theorem(code)
    if tags:
        hs=[hashlib.sha256(t.encode()).hexdigest()[:16] for t in tags]
        uniq=list(dict.fromkeys(hs)); n=len(uniq)
        mat=[[0]*n for _ in range(n)]
        hi={h:i for i,h in enumerate(uniq)}
        for i in range(len(hs)-1):
            if hs[i] in hi and hs[i+1] in hi: mat[hi[hs[i]]][hi[hs[i+1]]]+=1
    else: mat=[[1]]
    sp=compute_spectral(mat)
    vec=[sp.get(k,0) for k in V2_FEATURES]
    
    conn=connect(); cur=conn.cursor()
    cur.execute("SELECT decision_signals FROM ene.flexures WHERE session_id=%s OR session_id=%s",(library_session,failure_session))
    library=[]
    for row in cur.fetchall():
        sig=json.loads(row[0]) if isinstance(row[0],str) else row[0]
        sl=sig.get("spectral",{}); lv=[sl.get(k,0) for k in V2_FEATURES]
        library.append({"features":lv,"tf":sig.get("tactic_family","?"),"obs":sig.get("obstruction_type","?"),"jl":sig.get("joint_label","?")})
    cur.close(); conn.close()
    
    scored=[(math.sqrt(sum((vec[i]-l["features"][i])**2 for i in range(len(vec)))),l) for l in library if len(l["features"])==len(vec)]
    scored.sort(key=lambda x:x[0])
    top3=scored[:3]
    votes=Counter(lib["obs"] for _,lib in top3)
    predicted_obs=votes.most_common(1)[0][0] if votes else "other"
    
    # Map obstruction type to patch family
    obs_to_family = {"missing_rewrite_direction":"rewrite","missing_assumption_bridge":"discharge",
        "arithmetic_gap":"arithmetic","case_split_missing":"case_analysis",
        "induction_incomplete":"induction","simplifier_gap":"normalization",
        "coercion_mismatch":"normalization","order_inequality_gap":"arithmetic"}
    predicted_family = obs_to_family.get(predicted_obs, "normalization")
    
    # Extract actual hypothesis names from the theorem
    hyps = re.findall(r'\(([^)]+:\s*[^)]+)\)', code)
    hyp_names = []
    for h in hyps:
        parts = h.split(":")
        names_part = parts[0].strip()
        for n in names_part.split():
            if n.strip():
                hyp_names.append(n.strip())
    first_hyp = hyp_names[0] if hyp_names else "h"
    
    pc=[]
    if predicted_family=="rewrite":
        pc+=["rw ["+first_hyp+"]","rw [← "+first_hyp+"]"]
    elif predicted_family=="discharge":
        pc+=["exact "+first_hyp,"assumption","apply "+first_hyp]
    elif predicted_family=="normalization":
        pc+=["simp","norm_num"]
    elif predicted_family=="arithmetic":
        pc+=["omega"]
    elif predicted_family=="case_analysis":
        pc+=["cases h","constructor"]
    elif predicted_family=="induction":
        pc+=["induction n"]
    else: pc+=["simp","omega"]
    
    init_vars=code.count("("); init_ops=sum(1 for c in code if c in "+-*/^∧∨→¬∀∃≤≥")
    attempts=[]; best_delta=-999; best_attempt=None; recovered=False
    
    for i,patch in enumerate(pc[:max_attempts]):
        patched=code.split(":=")[0]+":=" if ":=" in code else code
        patched+="\n  "+patch
        r=prove(patched,f"{name}_repair_{i}")
        ok=r.get("ok",False)
        av=patched.count("("); ao=sum(1 for c in patched if c in "+-*/^∧∨→¬∀∃≤≥")
        delta=(init_vars+init_ops)-(av+ao)
        if delta>best_delta:
            best_delta=delta; best_attempt={"patch":patch,"delta":delta,"ok":ok}
        if ok:
            recovered=True; best_attempt={"patch":patch,"delta":delta,"ok":ok}; break
        attempts.append({"attempt":i+1,"patch":patch,"family":predicted_family,"ok":ok,"delta":delta})
    
    return {"name":name,"obstruction":obstruction_type(name),"initial_status":"failed",
            "predicted_family":predicted_family,"recovered":recovered,"best_delta":best_delta,
            "partial_improvement":best_delta>0,"attempts":attempts,"best_attempt":best_attempt}

def main():
    print("V1.1: Failure Flexure Expansion + 13-dim v2 features\n")
    traced=[]
    for i,(n,c) in enumerate(FAILURE_THEOREMS):
        print(f"  [{i+1}/{len(FAILURE_THEOREMS)}] {n:35s} ... ",end="",flush=True)
        r=build_trace(n,c)
        if r is None: print("SKIP")
        else:
            traced.append(r)
            print(f"n={r.get('matrix_size','?'):2d} obs={r.get('obstruction','?')[:20]}")
    print(f"\n  Traced: {len(traced)}/{len(FAILURE_THEOREMS)}")
    
    failure_session=ingest_failure_flexures(traced)
    print(f"  Failure session: {failure_session}")
    
    combined_session="a4a0eb20-93fe-413e-8e0b-50334bb778d8"
    test_set=FAILURE_THEOREMS[:30]
    results=[]
    rec=part=worse=0; td=0; dc=0
    
    for i,(n,c) in enumerate(test_set):
        print(f"  [{i+1}/{len(test_set)}] {n:35s} ... ",end="",flush=True)
        r=route_repair(n,c,combined_session,failure_session)
        if r["initial_status"]=="verified":
            print("already verified"); continue
        s="RECOVERED" if r["recovered"] else "improved" if r.get("partial_improvement") else "no change"
        print(f"{s:15s} pred={r['predicted_family']:12s} delta={r['best_delta']:+d}")
        results.append(r)
        if r["recovered"]: rec+=1
        if r.get("partial_improvement"): part+=1
        if r["best_delta"]<0: worse+=1
        td+=r["best_delta"]; dc+=1
    
    n=len(results); ad=td/max(dc,1)
    print(f"\n{'='*60}\nROUTE-REPAIR V1.1\n{'='*60}")
    print(f"Test set: {n} failed | Recovered: {rec} ({rec/max(n,1):.0%}) | Partial: {part} ({part/max(n,1):.0%}) | Avg ΔC: {ad:.2f}")
    
    by_obs=defaultdict(lambda:{"t":0,"r":0,"p":0,"d":0})
    for r in results:
        o=r.get("obstruction","?"); by_obs[o]["t"]+=1
        if r["recovered"]: by_obs[o]["r"]+=1
        if r.get("partial_improvement"): by_obs[o]["p"]+=1
        by_obs[o]["d"]+=r["best_delta"]
    print(f"\nPer-obstruction:")
    for o,s in sorted(by_obs.items(),key=lambda x:-x[1]["t"]):
        print(f"  {o:30s}: n={s['t']:2d} rec={s['r']/max(s['t'],1):.0%} part={s['p']/max(s['t'],1):.0%} ΔC={s['d']/max(s['t'],1):+.1f}")
    
    rp={"n":n,"recovered":rec,"partial_improvement":part,"avg_delta":round(ad,2),
        "failure_session_id":failure_session,"combined_session_id":combined_session,"results":results}
    rp_path=os.path.join(os.path.dirname(__file__),"../..","shared-data/pist_route_repair_v11_benchmark.json")
    with open(rp_path,"w") as f: json.dump(rp,f,indent=2)
    print(f"\nReport: {rp_path}")

if __name__=="__main__":
    main()
