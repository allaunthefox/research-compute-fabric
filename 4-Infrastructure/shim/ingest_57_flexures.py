#!/usr/bin/env python3
# INFRA:DEAD rds -- AWS RDS is gone. Any file referencing rds_connect.py or this hostname is stale and must be ported.
"""Ingest 57 theorem vectors into ene.flexures with full v2 spectral features."""

import hashlib
import json
import os
from rds_connect import connect_rds
import sys
import uuid
from collections import Counter, defaultdict
from pathlib import Path

VECTORS_PATH = os.path.join(os.path.dirname(__file__), "../..", "shared-data/pist_trace_scaled_vectors.jsonl")
REPORT_PATH = os.path.join(os.path.dirname(__file__), "../..", "shared-data/pist_flexure_v2_report.json")


def classify_tactic(name: str) -> str:
    name_lower = name.lower()
    if "rw" in name_lower: return "rewrite"
    if "simp" in name_lower: return "normalization"
    if "omega" in name_lower: return "arithmetic"
    if "induct" in name_lower: return "induction"
    if "ring" in name_lower or "calc" in name_lower: return "algebraic"
    if "cases" in name_lower or "constructor" in name_lower: return "case_analysis"
    if "apply" in name_lower or "intro" in name_lower or "have" in name_lower: return "discharge"
    if "rfl" in name_lower: return "reflexivity"
    if "logic" in name_lower or "order" in name_lower: return "discharge"
    if "with_import" in name_lower or "algebra" in name_lower: return "normalization"
    if "expect_fail" in name_lower or "fail" in name_lower: return "unknown"
    if "complex" in name_lower: return "induction"
    return "unknown"


def main():
    with open(VECTORS_PATH) as f:
        records = [json.loads(line) for line in f]
    print(f"Vectors: {len(records)}", flush=True)

    conn = connect_rds()
    cur = conn.cursor()

    # Create new session (keep old data)
    session_id = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO ene.sessions (id, title, event_type, content, metadata) "
        "VALUES (%s, %s, 'flexure_ingest', '57-theorem v2 spectral batch', %s::jsonb)",
        (session_id, "Tier 2B 57-theorem v2", json.dumps({"source": "57_batch", "count": len(records)})),
    )

    joint_labels = Counter()
    tactic_families = Counter()
    total_joints = 0

    for r in records:
        name = r.get("name", "?")
        status = r.get("status", "failed")
        tf = classify_tactic(name)
        
        # Create a single flexure per theorem (the matrix represents the whole proof path)
        flex_id = str(uuid.uuid4())
        spectral = {k: r.get(k, 0) for k in ["matrix_size", "rank", "spectral_gap", "laplacian_zero_count",
                                               "density", "adjacency_eigenvalue_max", "adjacency_eigenvalue_second",
                                               "laplacian_eigenvalue_max", "laplacian_eigenvalue_min",
                                               "singular_value_max", "trace", "frobenius_norm"]}
        signals = json.dumps({
            "tactic": name, "tactic_family": tf, "delta_score": abs(r.get("gap", 0)) * 10,
            "joint_label": f"{tf}_{status}", "domain": "mixed", "proof_method": tf,
            "rrc_shape": "?", "obstruction": None, "matrix_rank": r.get("rank", 0),
            "n_unique_states": r.get("n", 0), "spectral": spectral,
            "feature_version": "flexure-spectrum-v2",
        })
        chosen = json.dumps({"theorem": name, "status": status})
        available = json.dumps([{"step": 0, "tactic_family": tf}])
        sidon = int(hashlib.sha256(name.encode()).hexdigest()[:4], 16) % 255
        
        cur.execute(
            "INSERT INTO ene.flexures (id, session_id, step_index, pre_sidon_label, pre_residual, "
            "available_crossings, chosen_crossing, decision_signals, post_sidon_label, post_residual, converged) "
            "VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s, %s)",
            (flex_id, session_id, 0, sidon, 0.5, available, chosen, signals,
             sidon % 255, 0.5, status == "verified"),
        )
        tactic_families[tf] += 1
        joint_labels[f"{tf}_{status}"] += 1
        total_joints += 1

    conn.commit()
    print(f"Inserted: {total_joints} flexures", flush=True)

    # Motif discovery
    cur.execute(
        "SELECT decision_signals->>'tactic_family', decision_signals->>'joint_label', converged, count(*) "
        "FROM ene.flexures WHERE session_id = %s GROUP BY 1, 2, 3 HAVING count(*) >= 2",
        (session_id,),
    )
    motif_count = 0
    for row in cur.fetchall():
        fam, label, converged, freq = row
        sig = hashlib.sha256(f"{fam}_{label}".encode()).hexdigest()[:16]
        cur.execute(
            "INSERT INTO ene.flexure_patterns (id, pattern_signature, pre_conditions, decision_rules, outcome_stats, frequency) "
            "VALUES (%s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s) "
            "ON CONFLICT (pattern_signature) DO UPDATE SET frequency = ene.flexure_patterns.frequency + %s",
            (str(uuid.uuid4()), sig, json.dumps({"tactic_family": fam}),
             json.dumps({"joint_type": label}), json.dumps({"status": "verified" if converged else "failed", "count": freq}),
             freq, freq),
        )
        motif_count += 1

    conn.commit()
    print(f"Motifs: {motif_count}", flush=True)
    print(f"Tactic families: {dict(tactic_families.most_common(5))}", flush=True)
    print(f"Joint labels: {dict(joint_labels.most_common(5))}", flush=True)
    print(f"Session: {session_id}", flush=True)

    with open(REPORT_PATH, "w") as f:
        json.dump({"session_id": session_id, "total_flexures": total_joints, "motifs": motif_count,
                    "tactic_families": dict(tactic_families.most_common(5)),
                    "joint_labels": dict(joint_labels.most_common(5))}, f, indent=2)
    print(f"Report: {REPORT_PATH}", flush=True)
    conn.close()


if __name__ == "__main__":
    main()
