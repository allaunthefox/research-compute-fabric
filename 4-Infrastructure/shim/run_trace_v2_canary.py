#!/usr/bin/env python3
"""Tier 2B trace canary — run 24 theorems through instrumented trace bridge.
Uses lean_trace_bridge_v2 directly (not as subprocess).
"""
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))
from trace_canary_theorems import CANARY_THEOREMS
from lean_trace_bridge_v2 import instrument_theorem, prove

os.makedirs(os.path.join(os.path.dirname(__file__), "../..", "shared-data/proof_traces"), exist_ok=True)
TRACES_DIR = os.path.join(os.path.dirname(__file__), "../..", "shared-data/proof_traces")
REPORT_PATH = os.path.join(os.path.dirname(__file__), "../..", "shared-data/pist_trace_v2_canary_report.json")

PROOF_SERVER_TOKEN = os.environ.get("PROOF_SERVER_TOKEN", "")
if not PROOF_SERVER_TOKEN:
    tf = os.environ.get("PROOF_SERVER_TOKEN_FILE", os.path.expanduser("~/.config/ene/language-proof-server.token"))
    try:
        PROOF_SERVER_TOKEN = Path(tf).read_text().strip()
    except (FileNotFoundError, OSError):
        PROOF_SERVER_TOKEN = ""


def run_trace(theorem: dict) -> dict:
    name = theorem["name"]
    code = theorem["code"]
    
    instr, tags = instrument_theorem(code)
    resp = prove(instr, name + "_t2b")
    ok = resp.get("ok", False)
    stdout = resp.get("stdout", "")
    
    # Parse trace tags
    found_tags = []
    for line in stdout.split("\n"):
        if "@@PIST_TRACE_JSON@@" in line:
            tag = line.split("@@PIST_TRACE_JSON@@")[1].strip()
            found_tags.append(tag)
    
    # Build transition matrix from trace hashes
    hashes = [hashlib.sha256(t.encode()).hexdigest()[:16] for t in found_tags]
    unique = list(dict.fromkeys(hashes))
    h2i = {h: i for i, h in enumerate(unique)}
    n = len(unique)
    matrix = [[0] * n for _ in range(n)]
    for i in range(len(hashes) - 1):
        if hashes[i] in h2i and hashes[i + 1] in h2i:
            matrix[h2i[hashes[i]]][h2i[hashes[i + 1]]] += 1
    
    gap = (n * 1.0) if n > 0 else 0  # spectral gap = n_unique (for now)
    
    return {
        "name": name,
        "ok": ok,
        "status": "verified" if ok else "failed",
        "trace_tags": found_tags,
        "n_steps": len(found_tags),
        "n_unique": n,
        "transition_matrix": matrix,
        "spectral_gap": gap,
    }


def main():
    theorems = CANARY_THEOREMS
    print(f"V2 Trace canary: {len(theorems)} theorems\n", flush=True)
    
    results = []
    for i, theorem in enumerate(theorems):
        name = theorem["name"]
        print(f"  [{i+1}/{len(theorems)}] {name:30s} ... ", end="", flush=True)
        r = run_trace(theorem)
        print(f"{r['status']:10s} tags={r['n_steps']:2d} uniq={r['n_unique']:2d} gap={r['spectral_gap']:.1f}", flush=True)
        results.append(r)
    
    # Report
    print(f"\n{'='*60}", flush=True)
    print("TIER 2B TRACE CANARY REPORT", flush=True)
    print(f"{'='*60}", flush=True)
    
    good = [r for r in results if r.get("trace_tags")]
    n_ok = sum(1 for r in results if r["ok"])
    steps = [r["n_steps"] for r in good]
    uniqs = [r["n_unique"] for r in good]
    
    print(f"\nTotal: {len(results)} (ok={n_ok}, tags>0={len(good)})", flush=True)
    if steps:
        print(f"Trace tags per proof: mean={sum(steps)/len(steps):.1f} max={max(steps)} min={min(steps)}", flush=True)
    if uniqs:
        print(f"Unique states: max={max(uniqs)} min={min(uniqs)} varied={len(set(uniqs))>1}", flush=True)
    
    non_one = sum(1 for r in good if r["n_unique"] > 1)
    print(f"Transition matrices >1x1: {non_one}/{len(good)}", flush=True)
    
    statuses = Counter(r["status"] for r in results)
    print(f"Status: {dict(statuses)}", flush=True)
    
    # Save results
    for r in results:
        tf = os.path.join(TRACES_DIR, f"v2_canary_{r['name']}.json")
        with open(tf, "w") as f:
            json.dump(r, f, indent=2)
    
    report = {
        "n": len(results),
        "n_ok": n_ok,
        "n_with_traces": len(good),
        "n_matrices_gt_1x1": non_one,
        "avg_steps": round(sum(steps)/len(steps), 1) if steps else 0,
        "status_distribution": dict(statuses),
    }
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport: {REPORT_PATH}", flush=True)


if __name__ == "__main__":
    main()
