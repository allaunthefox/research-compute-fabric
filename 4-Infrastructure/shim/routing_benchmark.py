#!/usr/bin/env python3
"""Routing benchmark: can pist_trace_classify predict the next proof tactic?

For each multi-step v2 trace, creates partial traces by removing the last tactic,
classifies the partial trace, and checks if the predicted tactic family matches
the actual next tactic.
"""
# PARTIAL BOUNDARY: contains domain logic; not a provable surface. Port to Lean/RRC before treating as authoritative.

import glob
import json
import math
import os
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))
from trace_canary_theorems import CANARY_THEOREMS
from pist_trace_classify_mcp import compute_spectral, FEATURE_KEYS, connect, FLEXURE_SESSION

TRACES_DIR = os.path.join(os.path.dirname(__file__), "../..", "shared-data/proof_traces")
LEAN_WORKER = os.environ.get("CANARY_WORKER_URL", "http://100.110.163.82:8787")
REPORT_PATH = os.path.join(os.path.dirname(__file__), "../..", "shared-data/pist_trace_routing_benchmark.json")
PROOF_SERVER_TOKEN = os.environ.get("PROOF_SERVER_TOKEN", "")


def load_motifs():
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT decision_signals, converged FROM ene.flexures WHERE session_id = %s",
        (FLEXURE_SESSION,),
    )
    library = []
    for row in cur.fetchall():
        sig = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        sp = sig.get("spectral", {})
        lvec = [sp.get(k, 0) for k in FEATURE_KEYS]
        library.append({
            "features": lvec, "tactic_family": sig.get("tactic_family", "?"),
            "joint_label": sig.get("joint_label", "?"), "converged": row[1],
        })
    
    cur.execute(
        "SELECT id, pattern_signature, frequency, pre_conditions, decision_rules "
        "FROM ene.flexure_patterns ORDER BY frequency DESC",
    )
    motifs = [{
        "id": str(r[0]), "signature": r[1], "frequency": r[2],
        "pre": json.loads(r[3]) if isinstance(r[3], str) else r[3],
        "rules": json.loads(r[4]) if isinstance(r[4], str) else r[4],
    } for r in cur.fetchall()]
    cur.close()
    conn.close()
    return library, motifs


def nearest_motifs(vec, motifs, top_k=3):
    """Find nearest motifs by weighted frequency score."""
    scored = []
    for m in motifs:
        score = m["frequency"] / 100.0  # base score from frequency
        scored.append({"score": round(score, 3), "motif": m})
    scored.sort(key=lambda x: -x["score"])
    return scored[:top_k]


def compute_spectral_from_json(json_str: str) -> dict:
    """Parse JSON string and compute spectral features."""
    trace = json.loads(json_str)
    matrix = trace.get("transition_matrix", [])
    if not matrix or len(matrix) == 0:
        return {}
    return compute_spectral(matrix)


def classify_partial(partial_matrix, motifs, library, top_k=3):
    """Classify a partial trace matrix against the motif library."""
    if not partial_matrix or len(partial_matrix) == 0:
        return {"tactic_family": "?", "joint_label": "?"}
    sp = compute_spectral(partial_matrix)
    vec = [sp.get(k, 0) for k in FEATURE_KEYS]
    
    # Find nearest flexures by Euclidean distance
    scored = []
    for lib in library:
        dist = math.sqrt(sum((vec[i] - lib["features"][i])**2 for i in range(len(vec))))
        scored.append({"dist": dist, "tactic_family": lib["tactic_family"],
                        "joint_label": lib["joint_label"]})
    scored.sort(key=lambda x: x["dist"])
    
    # Vote by nearest neighbors
    top = scored[:top_k]
    families = Counter(t["tactic_family"] for t in top)
    return {"tactic_family": families.most_common(1)[0][0], "votes": len(top)}


def classify_tactic(tactic: str) -> str:
    tl = tactic.lower()
    if "rw" in tl: return "rewrite"
    if "simp" in tl: return "normalization"
    if "omega" in tl: return "arithmetic"
    if "induction" in tl: return "induction"
    if "ring" in tl or "nlinarith" in tl or "calc" in tl: return "algebraic"
    if "cases" in tl: return "case_analysis"
    if "constructor" in tl: return "constructor"
    if "apply" in tl or "exact" in tl: return "discharge"
    if "intro" in tl: return "introduction"
    if "have" in tl: return "lemma_introduction"
    if "rfl" in tl: return "reflexivity"
    return "unknown"


def get_theorem_tactics(name: str) -> list[str]:
    """Get tactic list for a theorem from the knowledge base."""
    for t in CANARY_THEOREMS:
        if t["name"] == name:
            code = t.get("code", "")
            by_start = code.find(":= by")
            if by_start >= 0:
                body = code[by_start + 6:].strip()
                tactics = []
                for line in body.split("\n"):
                    stripped = line.strip()
                    if stripped and not stripped.startswith("--") and not stripped.startswith("/-") and not stripped.startswith("|"):
                        tactics.append(stripped)
                return tactics
    return []


def build_trace_matrix(tags: list[str]) -> list[list[int]]:
    """Build transition matrix from trace tags."""
    import hashlib
    hs = [hashlib.sha256(t.encode()).hexdigest()[:16] for t in tags]
    uniq = list(dict.fromkeys(hs))
    n = len(uniq)
    mat = [[0] * n for _ in range(n)]
    hi = {h: i for i, h in enumerate(uniq)}
    for i in range(len(hs) - 1):
        if hs[i] in hi and hs[i + 1] in hi:
            mat[hi[hs[i]]][hi[hs[i + 1]]] += 1
    return mat


def main():
    print("Routing benchmark: can pist_trace_classify predict the next tactic?\n", flush=True)
    
    library, motifs = load_motifs()
    print(f"Library: {len(library)} flexures, {len(motifs)} motifs", flush=True)
    
    # Load all v2 trace files
    trace_files = sorted(glob.glob(os.path.join(TRACES_DIR, "v2_canary_*.json")))
    print(f"Trace files: {len(trace_files)}", flush=True)
    
    results = []
    total_predictions = 0
    correct_predictions = 0
    total_reduction = 0
    reduction_count = 0
    
    for fpath in trace_files:
        with open(fpath) as f:
            trace = json.load(f)
        
        name = trace.get("name", "?")
        tags = trace.get("trace_tags", [])
        tactics = get_theorem_tactics(name)
        
        if len(tags) < 4 or len(tactics) < 2:
            continue  # skip single-tactic proofs
        
        # For each step, create a partial trace (remove suffix tags)
        for step in range(1, len(tactics)):
            # Keep only tags up to step_{step-1}_after
            include_tags = tags[:step * 2]
            partial_matrix = build_trace_matrix(include_tags)
            full_matrix = build_trace_matrix(tags[: (step + 1) * 2])
            
            # Get the actual next tactic
            actual_tactic = tactics[step]
            actual_family = classify_tactic(actual_tactic)
            
            # Classify the partial trace
            pred = classify_partial(partial_matrix, motifs, library, top_k=3)
            predicted_family = pred["tactic_family"]
            
            total_predictions += 1
            if predicted_family == actual_family:
                correct_predictions += 1
            
            # Compute complexity reduction from this step
            full_sp = compute_spectral(full_matrix)
            partial_sp = compute_spectral(partial_matrix)
            complexity_before = partial_sp.get("matrix_size", 0) * 10 + partial_sp.get("spectral_gap", 0) * 5
            complexity_after = full_sp.get("matrix_size", 0) * 10 + full_sp.get("spectral_gap", 0) * 5
            delta = complexity_before - complexity_after
            total_reduction += delta
            reduction_count += 1
            
            results.append({
                "theorem": name, "step": step,
                "actual_tactic": actual_tactic, "actual_family": actual_family,
                "predicted_family": predicted_family,
                "correct": predicted_family == actual_family,
                "complexity_delta": round(delta, 4),
                "partial_size": partial_sp.get("matrix_size", 0),
                "full_size": full_sp.get("matrix_size", 0),
            })
    
    n = len(results)
    accuracy = correct_predictions / max(total_predictions, 1)
    avg_reduction = total_reduction / max(reduction_count, 1)
    
    print(f"\n{'='*60}", flush=True)
    print("ROUTING BENCHMARK RESULTS", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"Total predictions: {total_predictions}", flush=True)
    print(f"Correct tactic family: {correct_predictions} / {total_predictions} = {accuracy:.1%}", flush=True)
    print(f"Average complexity reduction per step: {avg_reduction:.4f}", flush=True)
    
    # Per-family accuracy
    family_results = defaultdict(lambda: {"correct": 0, "total": 0})
    for r in results:
        fam = r["actual_family"]
        family_results[fam]["total"] += 1
        if r["correct"]:
            family_results[fam]["correct"] += 1
    
    print(f"\nPer-tactic-family accuracy:", flush=True)
    for fam, stats in sorted(family_results.items(), key=lambda x: -x[1]["total"]):
        acc = stats["correct"] / max(stats["total"], 1)
        print(f"  {fam:20s}: {stats['correct']:3d}/{stats['total']:3d} = {acc:.0%}", flush=True)
    
    # Size reduction
    size_deltas = [r["full_size"] - r["partial_size"] for r in results]
    avg_size_reduction = sum(size_deltas) / max(len(size_deltas), 1)
    print(f"\nAverage transition matrix size reduction: {avg_size_reduction:.2f} ", flush=True)
    
    # Confusion: which families get confused?
    confusion = defaultdict(lambda: defaultdict(int))
    for r in results:
        confusion[r["actual_family"]][r["predicted_family"]] += 1
    
    print(f"\nConfusion matrix (actual → predicted):", flush=True)
    families = sorted(set(r["actual_family"] for r in results) | set(r["predicted_family"] for r in results))
    for af in families:
        for pf in families:
            if confusion[af][pf] > 0 and af != pf:
                print(f"  {af:20s} → {pf:20s}: {confusion[af][pf]:3d}x", flush=True)
    
    # Save report
    report = {
        "n_predictions": total_predictions,
        "n_correct": correct_predictions,
        "tactic_family_accuracy": round(accuracy, 4),
        "average_complexity_reduction": round(avg_reduction, 4),
        "average_size_reduction": round(avg_size_reduction, 2),
        "per_family_accuracy": {f: {"correct": s["correct"], "total": s["total"],
                                     "accuracy": round(s["correct"] / max(s["total"], 1), 4)}
                                 for f, s in family_results.items()},
        "confusion_matrix": {af: dict(pf) for af, pf in confusion.items()},
        "predictions": results,
    }
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport: {REPORT_PATH}", flush=True)
    
    return 0


if __name__ == "__main__":
    main()
