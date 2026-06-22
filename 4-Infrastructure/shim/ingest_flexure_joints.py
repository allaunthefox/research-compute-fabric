#!/usr/bin/env python3
# INFRA:DEAD rds -- AWS RDS is gone. Any file referencing rds_connect.py or this hostname is stale and must be ported.
"""Ingest Tier 2B trace flexure joints into ene.flexures.

For each theorem trace, extracts per-step transitions as flexure joints,
inserts them into ene.flexures, and mines recurring patterns.
"""

import glob
import hashlib
import json
import math
import os
import subprocess
import sys
import uuid
from collections import Counter, defaultdict
from pathlib import Path

TRACES_DIR = os.path.join(os.path.dirname(__file__), "../..", "shared-data/proof_traces")
REPORT_PATH = os.path.join(os.path.dirname(__file__), "../..", "shared-data/pist_flexure_library_report.json")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))
from trace_canary_theorems import CANARY_THEOREMS

def power_iteration(matrix, max_iter=100):
    n = len(matrix)
    if n == 0: return 0.0, [0.0]
    v = [1.0 / math.sqrt(n)] * n
    for _ in range(max_iter):
        vn = [sum(matrix[i][j] * v[j] for j in range(n)) for i in range(n)]
        nm = math.sqrt(sum(x*x for x in vn))
        if nm < 1e-12: return 0.0, v
        v = [x / nm for x in vn]
    num = sum(v[i] * sum(matrix[i][j] * v[j] for j in range(n)) for i in range(n))
    den = sum(v[i]*v[i] for i in range(n))
    return num / den if den > 0 else 0.0, v

def symmetrize(matrix):
    n = len(matrix)
    return [[(matrix[i][j] + matrix[j][i]) / 2.0 for j in range(n)] for i in range(n)]

def build_laplacian(sym):
    n = len(sym)
    lap = [[0.0]*n for _ in range(n)]
    for i in range(n):
        d = sum(sym[i])
        for j in range(n):
            lap[i][j] = d if i == j else -sym[i][j]
    return lap

def compute_spectral(matrix):
    if not matrix or len(matrix) == 0: return {}
    n = len(matrix)
    sym = symmetrize(matrix)
    lap_mat = build_laplacian(sym)
    ev_max, _ = power_iteration(sym)
    shifted = [[sym[i][j] - 0.9*ev_max*(1 if i==j else 0) for j in range(n)] for i in range(n)]
    ev_shift, _ = power_iteration(shifted)
    ev_second = max(0, ev_max - ev_shift) if ev_shift < ev_max else ev_max
    gap = ev_max - ev_second
    lap_max, _ = power_iteration(lap_mat)
    neg_lap = [[-lap_mat[i][j] for j in range(n)] for i in range(n)]
    neg_max, _ = power_iteration(neg_lap)
    lap_min = -neg_max
    ata = [[sum(matrix[k][i]*matrix[k][j] for k in range(n)) for j in range(n)] for i in range(n)]
    sv_max, _ = power_iteration(ata)
    rank = sum(1 for row in matrix if sum(row) > 0)
    total = sum(sum(row) for row in matrix)
    frob = math.sqrt(sum(cell*cell for row in matrix for cell in row))
    lap_zero = sum(1 for i in range(n) if abs(sum(matrix[i]) - matrix[i][i]) < 1e-9)
    return {
        "matrix_size": n, "rank": rank, "density": round(total/max(n*n,1), 6),
        "spectral_gap": round(gap, 6), "frobenius_norm": round(frob, 6),
        "adjacency_eigenvalue_max": round(ev_max, 6),
        "adjacency_eigenvalue_second": round(ev_second, 6),
        "laplacian_eigenvalue_max": round(lap_max, 6),
        "laplacian_eigenvalue_min": round(lap_min, 6),
        "laplacian_zero_count": lap_zero,
        "singular_value_max": round(math.sqrt(max(0, sv_max)), 6),
        "trace": sum(matrix[i][i] for i in range(n)),
    }

TACTIC_FAMILIES = {
    "rw": "rewrite", "simp": "normalization", "omega": "arithmetic",
    "induction": "induction", "ring": "algebraic", "cases": "case_analysis",
    "constructor": "constructor", "apply": "discharge", "exact": "discharge",
    "intro": "introduction", "have": "lemma_introduction",
    "calc": "calculation", "rfl": "reflexivity",
    "nlinarith": "algebraic", "native_decide": "arithmetic",
}

def classify_tactic(tactic: str) -> str:
    tl = tactic.lower()
    for key, val in TACTIC_FAMILIES.items():
        if key in tl:
            return val
    return "unknown"

def build_joint_label(tactic: str, delta_score: float, status: str) -> str:
    """Derive a joint label from the tactic and delta."""
    fam = classify_tactic(tactic)
    if status == "failed":
        return f"failed_{fam}"
    if delta_score > 5:
        return f"high_delta_{fam}"
    elif delta_score > 2:
        return f"med_delta_{fam}"
    else:
        return f"low_delta_{fam}"

def get_theorem_labels(name: str) -> dict:
    """Look up ground-truth labels and tactic text from the theorem definitions."""
    for t in CANARY_THEOREMS:
        if t["name"] == name:
            code = t.get("code", "")
            # Extract tactics from the by-block
            tactics = []
            by_start = code.find(":= by")
            if by_start >= 0:
                body = code[by_start + 6:].strip()
            else:
                body = code
            for line in body.split("\n"):
                stripped = line.strip()
                if stripped and not stripped.startswith("--"):
                    tactics.append(stripped)
            return {
                "domain": t.get("domain", "?"),
                "proof_method": t.get("proof_method", "?"),
                "joint": t.get("joint", "?"),
                "obstruction": t.get("obstruction"),
                "rrc_shape": t.get("rrc_shape", "?"),
                "tactics": tactics,
            }
    return {"domain": "?", "proof_method": "?", "joint": "?", "obstruction": None,
            "rrc_shape": "?", "tactics": []}


def ingest_flexures():
    """Main ingestion pass."""
    trace_files = sorted(glob.glob(os.path.join(TRACES_DIR, "v2_canary_*.json")))
    if not trace_files:
        print("No trace files found", flush=True)
        return
    
    print(f"Found {len(trace_files)} trace files", flush=True)
    
    # Connect to RDS
    host = os.environ.get("RDS_HOST", "database-1-instance-1.cghu8yqogqwo.us-east-1.rds.amazonaws.com")
    port = os.environ.get("RDS_PORT", "5432")
    user = os.environ.get("RDS_USER", "postgres")
    db = os.environ.get("RDS_DB", "postgres")
    token = os.environ.get("RDS_IAM_TOKEN", "")
    if not token:
        region = os.environ.get("AWS_REGION", "us-east-1")
        token = subprocess.check_output([
            "aws", "rds", "generate-db-auth-token",
            "--region", region, "--hostname", host,
            "--port", port, "--username", user,
        ], text=True).strip()
    
    import psycopg2
    conn = psycopg2.connect(
        host=host, port=port, user=user, password=token, dbname=db,
        sslmode="require",
    )
    cur = conn.cursor()
    
    # Create a session for this batch
    session_id = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO ene.sessions (id, title, event_type, content, metadata) "
        "VALUES (%s, %s, 'flexure_ingest', 'Tier 2B flexure joint batch ingestion', %s::jsonb)",
        (session_id, "Tier 2B Flexure Ingestion",
         json.dumps({"source": "lean_trace_v2_canary", "trace_count": len(trace_files)})),
    )
    
    all_joints = []
    total_inserted = 0
    total_skipped = 0
    
    for fpath in trace_files:
        with open(fpath) as f:
            trace = json.load(f)
        
        name = trace.get("name", Path(fpath).stem)
        status = trace.get("status", "?")
        tags = trace.get("trace_tags", [])
        matrix = trace.get("transition_matrix", [])
        n_unique = trace.get("n_unique", 0)
        
        labels = get_theorem_labels(name)
        tactics = labels.get("tactics", [])
        
        # Compute full spectral features from the transition matrix
        spectral = compute_spectral(matrix)
        
        # Build flexure joints from tag pairs
        joints = []
        for i in range(0, len(tags) - 1, 2):
            if i + 1 >= len(tags):
                break
            step = i // 2
            tactic = tactics[step] if step < len(tactics) else f"step_{step}"
            tactic_family = classify_tactic(tactic)
            
            bh = hashlib.sha256(tags[i].encode()).hexdigest()[:16]
            ah = hashlib.sha256(tags[i+1].encode()).hexdigest()[:16]
            delta_score = abs(int(bh[:4], 16) - int(ah[:4], 16)) % 10
            
            joint_label = build_joint_label(tactic, delta_score, status)
            
            joint = {
                "step": step,
                "tactic": tactic,
                "tactic_family": tactic_family,
                "before_hash": bh,
                "after_hash": ah,
                "delta_score": delta_score,
                "joint_label": joint_label,
                "domain": labels["domain"],
                "proof_method": labels["proof_method"],
                "rrc_shape": labels["rrc_shape"],
                "obstruction": labels.get("obstruction"),
                "matrix_rank": max(0, n_unique - 1),
                "n_unique": n_unique,
                "status": status,
                "spectral": spectral,  # full spectral profile
            }
            joints.append(joint)
        
        # Insert joints
        for j in joints:
            flex_id = str(uuid.uuid4())
            signals = json.dumps({
                "tactic": j["tactic"],
                "tactic_family": j["tactic_family"],
                "delta_score": j["delta_score"],
                "joint_label": j["joint_label"],
                "domain": j["domain"],
                "proof_method": j["proof_method"],
                "rrc_shape": j["rrc_shape"],
                "obstruction": j.get("obstruction"),
                "matrix_rank": j["matrix_rank"],
                "n_unique_states": j["n_unique"],
                "spectral": j.get("spectral", {}),
                "feature_version": "flexure-spectrum-v2",
            })
            
            chosen = json.dumps({"tactic_applied": j["tactic"], "joint_type": j["joint_label"]})
            available = json.dumps([{"step": j["step"], "tactic_family": j["tactic_family"]}])
            
            try:
                cur.execute(
                    """INSERT INTO ene.flexures
                       (id, session_id, step_index, pre_sidon_label, pre_residual,
                        available_crossings, chosen_crossing, decision_signals,
                        post_sidon_label, post_residual, converged)
                       VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb,
                               %s, %s, %s)""",
                    (flex_id, session_id, j["step"],
                     int(j["before_hash"][:4], 16) % 255,  # hash as Sidon-like label
                     1.0 - j["delta_score"] / 10.0,  # residual = 1 - normalized delta
                     available, chosen, signals,
                     int(j["after_hash"][:4], 16) % 255,
                     j["delta_score"] / 10.0,
                     j["status"] == "verified"),
                )
                total_inserted += 1
            except Exception as e:
                total_skipped += 1
            
            all_joints.append(j)
        
        print(f"  {name:30s}: {len(joints)} joints", flush=True)
    
    conn.commit()
    
    # ── Motif extraction ──
    print(f"\nInserted: {total_inserted} flexures, Skipped: {total_skipped}", flush=True)
    
    # Extract recurring joint patterns from all_joints
    motif_counter = Counter()
    for j in all_joints:
        motif = (j["tactic_family"], j["joint_label"], j["status"])
        motif_counter[motif] += 1
    
    print(f"\nRecurring joint motifs (frequency ≥ 2):", flush=True)
    motif_count = 0
    for (fam, jl, status), count in sorted(motif_counter.items(), key=lambda x: -x[1]):
        if count >= 2:
            print(f"  {fam:20s} {jl:30s} {status:10s}: {count:3d}x", flush=True)
            
            # Insert into flexure_patterns
            pat_id = str(uuid.uuid4())
            sig = hashlib.sha256(f"{fam}_{jl}_{status}".encode()).hexdigest()[:16]
            cur.execute(
                """INSERT INTO ene.flexure_patterns
                   (id, pattern_signature, pre_conditions, decision_rules, outcome_stats, frequency)
                   VALUES (%s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s)
                   ON CONFLICT (pattern_signature) DO UPDATE SET
                     frequency = ene.flexure_patterns.frequency + %s,
                     last_seen = now()""",
                (pat_id, sig,
                 json.dumps({"tactic_family": fam}),
                 json.dumps({"joint_type": jl}),
                 json.dumps({"status": status, "count": count}),
                 count, count),
            )
            motif_count += 1
    
    conn.commit()
    print(f"Patterns inserted: {motif_count}", flush=True)
    
    # ── Summary ──
    print(f"\nFlexure joint library summary:", flush=True)
    statuses = Counter(j["status"] for j in all_joints)
    print(f"  Total joints: {len(all_joints)}", flush=True)
    print(f"  Status: {dict(statuses)}", flush=True)
    
    families = Counter(j["tactic_family"] for j in all_joints)
    print(f"  Families: {dict(families.most_common(5))}", flush=True)
    
    joint_labels = Counter(j["joint_label"] for j in all_joints)
    print(f"  Joint labels: {dict(joint_labels.most_common(5))}", flush=True)
    
    report = {
        "session_id": session_id,
        "total_flexures_inserted": total_inserted,
        "total_skipped": total_skipped,
        "motifs_discovered": motif_count,
        "joint_library_summary": {
            "total_joints": len(all_joints),
            "status": dict(statuses),
            "tactic_families": dict(families.most_common(5)),
            "joint_labels": dict(joint_labels.most_common(5)),
            "motifs": {f"{fam}_{jl}_{st}": cnt for (fam, jl, st), cnt in
                   sorted(motif_counter.items(), key=lambda x: -x[1])},
        },
    }
    
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport: {REPORT_PATH}", flush=True)
    
    cur.close()
    conn.close()
    print(f"\nSession ID: {session_id} (use with flexure_analyze)", flush=True)


if __name__ == "__main__":
    ingest_flexures()
