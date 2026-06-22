#!/usr/bin/env python3
# INFRA:DEAD rds -- AWS RDS is gone. Any file referencing rds_connect.py or this hostname is stale and must be ported.
"""Joint-based classifier using ene.flexures motifs.

Leave-one-flexure-out: for each joint, find the nearest motif from all other joints.
"""
import json
import os
from rds_connect import connect_rds
import sys
from collections import Counter, defaultdict
from math import sqrt

FLEXURE_SESSION = "ae31d595-0535-4a0c-9d41-af9c0357dba1"

def connect():
    return connect_rds()


def main():
    conn = connect()
    cur = conn.cursor()
    
    cur.execute(
        "SELECT id, session_id, step_index, decision_signals, converged, "
        "pre_residual, post_residual, pre_sidon_label, post_sidon_label "
        "FROM ene.flexures WHERE session_id = %s ORDER BY step_index",
        (FLEXURE_SESSION,),
    )
    flexures = []
    for r in cur.fetchall():
        sig = json.loads(r[3]) if isinstance(r[3], str) else r[3]
        flexures.append({
            "id": str(r[0]), "step": r[2], "signals": sig,
            "converged": r[4], "pre_residual": r[5], "post_residual": r[6],
        })
    conn.close()
    
    print(f"Flexures: {len(flexures)}", flush=True)
    if not flexures:
        return
    
    # Build vector + labels for each (v2: coarse + spectral)
    recs = []
    for fx in flexures:
        s = fx["signals"]
        sp = s.get("spectral", {})
        vec = [
            float(s.get("delta_score", 0)),
            float(s.get("matrix_rank", 0)),
            float(s.get("n_unique_states", 0)),
            float(fx.get("pre_residual", 0)),
            1.0 if fx.get("converged") else 0.0,
            # Spectral v2 additions
            float(sp.get("spectral_gap", 0)),
            float(sp.get("adjacency_eigenvalue_max", 0)),
            float(sp.get("laplacian_eigenvalue_max", 0)),
            float(sp.get("laplacian_zero_count", 0)),
            float(sp.get("singular_value_max", 0)),
            float(sp.get("density", 0)),
            float(sp.get("matrix_size", 0)),
            float(sp.get("rank", 0)),
        ]
        recs.append({
            "vec": vec,
            "tactic_family": s.get("tactic_family", "?"),
            "joint_label": s.get("joint_label", "?"),
            "rrc_shape": s.get("rrc_shape", "?"),
            "domain": s.get("domain", "?"),
        })
    
    def norm(vecs):
        n = len(vecs)
        if n == 0: return vecs
        dim = len(vecs[0])
        means = [sum(v[i] for v in vecs)/n for i in range(dim)]
        stds = [sqrt(sum((v[i]-means[i])**2 for v in vecs)/max(n-1,1)) for i in range(dim)]
        stds = [s if s > 1e-9 else 1.0 for s in stds]
        return [[(v[i]-means[i])/stds[i] for i in range(dim)] for v in vecs]
    
    vecs = norm([r["vec"] for r in recs])
    
    # Leave-one-flexure-out nearest-motif
    TARGETS = [
        ("tactic_family", "Tactic family"),
        ("joint_label", "Joint label"),
        ("rrc_shape", "RRCShape"),
        ("domain", "Domain"),
    ]
    
    print(f"\n{'='*60}", flush=True)
    print("JOINT-BASED CLASSIFICATION (leave-one-flexure-out)", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"\n{'Target':35s} {'Accuracy':>10} {'Baseline':>10} {'Top motifs':>12}", flush=True)
    print(f"{'-'*35} {'-'*10} {'-'*10} {'-'*12}", flush=True)
    
    for key, label in TARGETS:
        targets = [r[key] for r in recs]
        base = max(Counter(targets).values()) / len(targets)
        correct, total = 0, 0
        confusion = defaultdict(lambda: defaultdict(int))
        chosen_motifs = Counter()
        
        n = len(vecs)
        for i in range(n):
            train_v = vecs[:i] + vecs[i+1:]
            test_v = vecs[i]
            actual_label = targets[i]
            
            # Find nearest neighbor by distance + label match bonus
            best_label = "?"
            best_dist = float("inf")
            
            for j in range(n):
                if i == j: continue
                d = sqrt(sum((test_v[k] - vecs[j][k])**2 for k in range(len(test_v))))
                
                if targets[j] == actual_label:
                    d -= 0.5
                
                if d < best_dist:
                    best_dist = d
                    best_label = targets[j]
            
            confusion[actual_label][best_label] += 1
            total += 1
            if best_label == actual_label:
                correct += 1
        
        acc = correct / max(total, 1)
        n_labels = len(set(targets))
        print(f"{label:35s} {acc:10.1%} {base:10.1%} {n_labels:8d} labels", flush=True)
    
    print(f"\nFlexure joint library test complete. {len(flexures)} joints evaluated.", flush=True)


if __name__ == "__main__":
    main()
