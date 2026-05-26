#!/usr/bin/env python3
"""Batch-validate pist-decompose with matrix diagnostics and exact spectrum.

Reads docs/rrc_equation_classification.md, runs each equation through
pist-decompose, collects diagnostics:
- Are crossing matrices unique?
- Does exact spectrum classify better than convergence proxy?
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict

def require_path(obj, *path):
    cur = obj
    for key in path:
        if key not in cur:
            raise KeyError(f"Missing path: {'.'.join(path)} in result")
        cur = cur[key]
    return cur


PIST_DECOMPOSE = os.environ.get(
    "PIST_DECOMPOSE_BIN",
    "/home/allaun/.local/share/opencode/worktree/"
    "0b42981cf7f7d5e172b1e93f8d4bb64a3dd63962/Turn-and-Burn/infra/rust/"
    "ene-rds/target/release/pist-decompose",
)

RRC_FILE = os.path.join(os.path.dirname(__file__), "../..",
                        "docs/rrc_equation_classification.md")


def parse_rrc_table(path: str) -> list[dict]:
    with open(path) as f:
        text = f.read()

    # Counts section (for header info)
    counts_section = text.split("## Counts By RRC Shape")[-1].split("## ")[0]
    print(f"  Counts section: {sum(int(m[0]) for m in [re.findall(r'\|\s*`\w+`\s*\|\s*(\d+)', line) for line in counts_section.split(chr(10))] if m)} total", file=sys.stderr)

    # Sample Projections section
    equations = []
    sample_section = text.split("## Sample Projections")[-1].split("## ")[0]
    for line in sample_section.split("\n"):
        parts = [p.strip().replace("`", "") for p in line.split("|")]
        if len(parts) >= 5 and parts[1] and parts[2] and parts[3]:
            eq_name = parts[1]
            shape = parts[2]
            status = parts[3]
            equations.append({"equation": eq_name, "shape": shape, "status": status})
    print(f"  Sample section: {len(equations)} equations", file=sys.stderr)
    return equations


def build_receipt(eq: dict) -> dict:
    return {
        "receipt_version": "rrc-proof-receipt-v1",
        "theorem_name": eq["equation"],
        "equation_text": eq["equation"],
        "theorem_statement": f"{eq['equation']} is a {eq['shape']} equation",
        "proof_script": f"by native_decide -- {eq['shape']}",
        "imports": ["Semantics", "RRCShape"],
        "dependencies": ["RRCLogogramProjection.lean"],
        "source_hash": eq["equation"],
        "environment_hash": f"lean4-v4.30.0-{eq['shape']}",
        "status": "verified",
        "kernel_checked": True,
        "elapsed_ms": 42,
        "metrics": {"statement_chars": len(eq["equation"]), "proof_chars": len(eq["shape"]),
                    "dependency_count": 1, "import_count": 2, "tactic_count": 1, "ast_depth_estimate": 3},
    }


def classify(eq: dict, cmdline: str = "") -> dict:
    receipt = build_receipt(eq)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(receipt, f)
        fpath = f.name
    try:
        extra = cmdline.split()
        result = subprocess.run(
            [PIST_DECOMPOSE, fpath, "--num-leaves", "8"] + extra,
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0:
            return {"error": result.stderr[:200], "equation": eq["equation"]}
        return json.loads(result.stdout)
    finally:
        os.unlink(fpath)


def main():
    print("Loading RRC equation classification...", flush=True)
    equations = parse_rrc_table(RRC_FILE)
    print(f"Loaded {len(equations)} equations", flush=True)

    predictions = []
    errors = []
    matrix_hashes = Counter()
    canonical_hashes = Counter()

    for i, eq in enumerate(equations):
        print(f"  [{i+1}/{len(equations)}] {eq['equation']:40s} → ", end="", flush=True)
        result = classify(eq, "")
        if "error" in result:
            print(f"ERROR: {result['error'][:60]}", flush=True)
            errors.append(result)
            continue

        mhash = require_path(result, "braid", "matrix_hash")[:16]
        chash = require_path(result, "canonical_hash")[:16]
        proxy_label = require_path(result, "rrc_shape", "proxy", "label")
        exact_label = require_path(result, "rrc_shape", "exact", "label")
        zmp = require_path(result, "spectral", "zero_mode_proxy_count")
        sym_ev = require_path(result, "spectral", "symmetric_eigenvalues") or [0.0] * 8
        sv_raw = result.get("spectral", {}).get("singular_values")
        if sv_raw is None:
            singular_v = [0.0] * 8
        else:
            singular_v = [float(v) if v is not None else 0.0 for v in sv_raw]
        lap_zero = require_path(result, "spectral", "laplacian_zero_count")
        rank = require_path(result, "spectral", "rank_estimate")
        cd = require_path(result, "braid", "crossing_density")
        sent = require_path(result, "braid", "strand_entropy")
        gap = require_path(result, "spectral", "symmetric_spectral_gap")
        matrix_hashes[mhash] += 1
        canonical_hashes[chash] += 1

        print(f"{proxy_label:35s} | exact={exact_label:30s} | ZMP={zmp} | hash={mhash} | "
              f"rank={rank} | lap_zero={lap_zero} | gap={gap:.3f}",
              flush=True)

        predictions.append({
            "equation": eq["equation"],
            "ground_truth": eq["shape"],
            "proxy_pred": proxy_label,
            "exact_pred": exact_label,
            "zmp": zmp,
            "eigenvalues": [round(v, 4) for v in sym_ev],
            "singular_values": [round(v, 4) for v in singular_v],
            "laplacian_zero_count": lap_zero,
            "rank_estimate": rank,
            "crossing_density": cd,
            "strand_entropy": sent,
            "spectral_gap": round(gap, 4),
            "matrix_hash": mhash,
            "canonical_hash": chash,
        })

    # ── Diagnostics Report ──
    print("\n" + "=" * 70, flush=True)
    print("DIAGNOSTICS", flush=True)
    print("=" * 70)

    print(f"\nEquations processed: {len(predictions)}")
    print(f"Errors: {len(errors)}")
    print(f"Unique canonical hashes: {len(canonical_hashes)} / {len(predictions)}")
    print(f"Unique matrix hashes: {len(matrix_hashes)} / {len(predictions)}")

    # Duplicate analysis
    dup_matrices = {h: c for h, c in matrix_hashes.items() if c > 1}
    dup_canonical = {h: c for h, c in canonical_hashes.items() if c > 1}
    if dup_matrices:
        print(f"\nColliding matrix hashes ({len(dup_matrices)} groups):")
        for h, c in sorted(dup_matrices.items(), key=lambda x: -x[1])[:10]:
            eqs = [p["equation"] for p in predictions if p["matrix_hash"] == h]
            print(f"  {h} appears {c}x: {', '.join(eqs[:5])}")
    if dup_canonical:
        print(f"\nColliding canonical hashes ({len(dup_canonical)} groups):")
        for h, c in sorted(dup_canonical.items(), key=lambda x: -x[1])[:10]:
            eqs = [p["equation"] for p in predictions if p["canonical_hash"] == h]
            print(f"  {h} appears {c}x: {', '.join(eqs[:5])}")
    else:
        print("\nNo canonical hash collisions — every equation has a unique receipt fingerprint.")

    # ── Classifier Accuracy ──
    print("\n" + "=" * 70, flush=True)
    print("CLASSIFIER ACCURACY", flush=True)
    print("=" * 70)

    for label, pred_key in [("PROXY (ZMP threshold)", "proxy_pred"), ("EXACT (spectral classifier)", "exact_pred")]:
        correct = sum(1 for p in predictions if p[pred_key] == p["ground_truth"])
        total = len(predictions)
        acc = correct / total * 100 if total > 0 else 0
        print(f"\n{label}: {correct}/{total} = {acc:.1f}%")

        # Per class
        classes = sorted(set(p["ground_truth"] for p in predictions) |
                         set(p[pred_key] for p in predictions))
        print(f"  {'Class':35s} {'Count':>6} {'Correct':>8} {'Acc':>6}")
        print(f"  {'-'*35} {'-'*6} {'-'*8} {'-'*6}")
        for cls in classes:
            cls_total = sum(1 for p in predictions if p["ground_truth"] == cls)
            cls_correct = sum(1 for p in predictions if p["ground_truth"] == cls and p[pred_key] == cls)
            print(f"  {cls:35s} {cls_total:6d} {cls_correct:8d} {(cls_correct/cls_total*100 if cls_total else 0):5.1f}%")

    # ── ZMP Distribution by Ground Truth ──
    print(f"\n  ZMP distribution by ground truth:")
    zmp_by_gt = defaultdict(list)
    for p in predictions:
        zmp_by_gt[p["ground_truth"]].append(p["zmp"])
    for gt in sorted(zmp_by_gt.keys()):
        vals = zmp_by_gt[gt]
        print(f"    {gt:35s} mean={sum(vals)/len(vals):.2f} min={min(vals)} max={max(vals)} uniq={len(set(vals))}")

    # ── Spectral Feature Distribution ──
    print(f"\n  Spectral feature ranges:")
    for key, label in [("laplacian_zero_count", "Lap zero count"),
                        ("rank_estimate", "Rank estimate"),
                        ("crossing_density", "Crossing density"),
                        ("strand_entropy", "Strand entropy"),
                        ("spectral_gap", "Spectral gap")]:
        vals = [p.get(key, 0) for p in predictions]
        uniq = len(set(vals))
        print(f"    {label:25s}: uniq={uniq:2d}  min={min(vals):.4f} max={max(vals):.4f} {'' if uniq > 1 else '(SINGLETON — no discriminative power)'}")

    # ── Save report ──
    report = {
        "summary": {
            "total": len(predictions),
            "errors": len(errors),
            "unique_matrix_hashes": len(matrix_hashes),
            "unique_canonical_hashes": len(canonical_hashes),
            "proxy_accuracy": sum(1 for p in predictions if p["proxy_pred"] == p["ground_truth"]) / len(predictions) if predictions else 0,
            "exact_accuracy": sum(1 for p in predictions if p["exact_pred"] == p["ground_truth"]) / len(predictions) if predictions else 0,
            "matrix_hash_collisions": sum(1 for h, c in matrix_hashes.items() if c > 1),
            "canonical_hash_collisions": sum(1 for h, c in canonical_hashes.items() if c > 1),
        },
        "per_class_proxy": {},
        "per_class_exact": {},
        "zmp_distribution": {gt: {"mean": sum(v)/len(v), "min": min(v), "max": max(v), "unique": len(set(v))}
                             for gt, v in zmp_by_gt.items()},
        "predictions": predictions,
    }

    report_path = os.path.join(os.path.dirname(__file__), "../..",
                               "shared-data/rrc_pist_exact_validation.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nFull report: {report_path}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
