#!/usr/bin/env python3
"""Multi-tactic canary batch for Tier 2 trace pipeline."""
import json
import os
import sys
import time
import subprocess
from pathlib import Path
from collections import Counter

from trace_canary_theorems import CANARY_THEOREMS

TRACES_DIR = os.path.join(os.path.dirname(__file__), "../..", "shared-data/proof_traces")
VECTORS_PATH = os.path.join(os.path.dirname(__file__), "../..", "shared-data/pist_trace_canary_vectors.jsonl")
REPORT_PATH = os.path.join(os.path.dirname(__file__), "../..", "shared-data/pist_trace_canary_report.json")
BRIDGE = os.path.join(os.path.dirname(__file__), "lean_trace_bridge.py")
DECOMPOSE = os.path.join(os.path.dirname(__file__), "pist_trace_decompose.py")

PROOF_SERVER_TOKEN = os.environ.get("PROOF_SERVER_TOKEN", "")
if not PROOF_SERVER_TOKEN:
    tf = os.environ.get("PROOF_SERVER_TOKEN_FILE", os.path.expanduser("~/.config/ene/language-proof-server.token"))
    try:
        PROOF_SERVER_TOKEN = Path(tf).read_text().strip()
    except (FileNotFoundError, OSError):
        PROOF_SERVER_TOKEN = ""


def run_pipeline(theorem: dict) -> dict:
    name = theorem["name"]
    code = theorem["code"]
    trace_path = os.path.join(TRACES_DIR, f"canary_{name}.trace.json")
    decomp_path = os.path.join(TRACES_DIR, f"canary_{name}.decomp.json")
    os.makedirs(TRACES_DIR, exist_ok=True)

    t0 = time.time()
    r1 = subprocess.run(
        [sys.executable, BRIDGE, "--code", code, "--name", name, "--out", trace_path],
        capture_output=True, text=True, timeout=120,
        env={**os.environ, "PROOF_SERVER_TOKEN": PROOF_SERVER_TOKEN},
    )
    if r1.returncode != 0:
        return {"error": f"bridge: {r1.stderr[:200]}", "name": name}

    r2 = subprocess.run(
        [sys.executable, DECOMPOSE, trace_path, "--out", decomp_path],
        capture_output=True, text=True, timeout=30,
    )
    if r2.returncode != 0 or not os.path.exists(decomp_path):
        return {"error": f"decomp: {r2.stderr[:200]}", "name": name}

    with open(decomp_path) as f:
        decomposition = json.load(f)

    return {"name": name, "trace_file": trace_path, "wall_s": round(time.time() - t0, 2),
            "decomposition": decomposition}


def report(results, errors):
    good = [r for r in results if "error" not in r]
    n = len(good)
    print(f"\n{'='*60}\nTIER 2 TRACE CANARY REPORT\n{'='*60}", flush=True)
    print(f"Total: {len(results)} ({n} ok, {len(errors)} errors)", flush=True)

    steps = [len(r["decomposition"].get("flexure_joints", [])) for r in good]
    if steps:
        print(f"Steps: mean={sum(steps)/len(steps):.1f} max={max(steps)} min={min(steps)}", flush=True)
    statuses = Counter(r["decomposition"]["trace_summary"]["status"] for r in good)
    print(f"Status: {dict(statuses)}", flush=True)

    families = Counter()
    for r in good:
        for f, c in r["decomposition"].get("tactic_family_distribution", {}).items():
            families[f] += c
    print(f"Families: {dict(families)}", flush=True)

    u_mat = len(set(r["decomposition"]["spectral"]["n_states"] for r in good))
    u_rank = len(set(r["decomposition"]["spectral"]["rank_estimate"] for r in good))
    u_gap = len(set(round(r["decomposition"]["spectral"]["spectral_gap"], 4) for r in good))
    print(f"Unique states: {u_mat}/{n}  ranks: {u_rank}  gaps: {u_gap}/{n}", flush=True)

    v_gaps = [r for r in good if r["decomposition"]["trace_summary"]["status"] == "verified"]
    f_gaps = [r for r in good if r["decomposition"]["trace_summary"]["status"] == "failed"]
    for label, group in [("verified", v_gaps), ("failed", f_gaps)]:
        if group:
            gaps = [r["decomposition"]["spectral"]["spectral_gap"] for r in group]
            print(f"{label} (n={len(group)}): gap={sum(gaps)/len(gaps):.4f} [{min(gaps):.4f},{max(gaps):.4f}]", flush=True)

    with open(VECTORS_PATH, "w") as f:
        for r in good:
            row = {
                "name": r["name"], "status": r["decomposition"]["trace_summary"]["status"],
                "n_steps": len(r["decomposition"].get("flexure_joints", [])),
                "n_states": r["decomposition"]["spectral"]["n_states"],
                "spectral_gap": r["decomposition"]["spectral"]["spectral_gap"],
                "rank_estimate": r["decomposition"]["spectral"]["rank_estimate"],
                "density": r["decomposition"]["spectral"]["density"],
                "feature_vector": r["decomposition"]["feature_vector"],
                "tactic_family_distribution": r["decomposition"]["tactic_family_distribution"],
            }
            f.write(json.dumps(row) + "\n")
    print(f"Vectors: {VECTORS_PATH}", flush=True)

    with open(REPORT_PATH, "w") as f:
        json.dump({"n": n, "n_errors": len(errors), "status_distribution": dict(statuses),
                    "tactic_family_distribution": dict(families),
                    "unique_spectral_gaps": u_gap, "unique_rank_estimates": u_rank}, f, indent=2)
    print(f"Report: {REPORT_PATH}", flush=True)


def main():
    theorems = CANARY_THEOREMS
    print(f"Trace canary: {len(theorems)} theorems\n", flush=True)
    results, errors = [], []
    for i, theorem in enumerate(theorems):
        name = theorem["name"]
        print(f"  [{i+1}/{len(theorems)}] {name:30s} ... ", end="", flush=True)
        r = run_pipeline(theorem)
        if "error" in r:
            print(f"ERROR: {r['error'][:60]}", flush=True)
            errors.append(r)
        else:
            st = r["decomposition"]["trace_summary"]["status"]
            ns = len(r["decomposition"].get("flexure_joints", []))
            gap = r["decomposition"]["spectral"]["spectral_gap"]
            print(f"{st:10s} steps={ns:2d} gap={gap:.4f} rank={r['decomposition']['spectral']['rank_estimate']}", flush=True)
            results.append(r)
    report(results, errors)
    return 0 if len(errors) < len(theorems) / 2 else 1


if __name__ == "__main__":
    main()
