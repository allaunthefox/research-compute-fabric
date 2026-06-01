#!/usr/bin/env python3
"""Compare Tier 1 vs Tier 2 on independent labels — with alignment check + full reporting."""
import json
import logging
import os
import sys
from collections import Counter, defaultdict
from math import sqrt

VECTORS_PATH = os.path.join(os.path.dirname(__file__), "../..",
                            "shared-data/pist_trace_tier2b_vectors.jsonl")
LABELS_PATH = os.path.join(os.path.dirname(__file__), "../..",
                           "shared-data/pist_trace_v2_ground_truth_labels.jsonl")
COMPARISON_PATH = os.path.join(os.path.dirname(__file__), "../..",
                               "shared-data/pist_tier1_vs_tier2_comparison.json")
CONFUSION_PATH = os.path.join(os.path.dirname(__file__), "../..",
                              "shared-data/pist_tier2b_confusion_matrices.json")

def load_jsonl(path):
    rows = []
    with open(path) as f:
        for line in f:
            rows.append(json.loads(line))
    return rows

def normalize(vectors):
    n = len(vectors)
    if n == 0: return vectors, [], []
    dim = len(vectors[0])
    means = [sum(v[i] for v in vectors) / n for i in range(dim)]
    stds = [sqrt(sum((v[i] - means[i])**2 for v in vectors) / max(n-1, 1)) for i in range(dim)]
    stds = [s if s > 1e-9 else 1.0 for s in stds]
    return [[(v[i] - means[i]) / stds[i] for i in range(dim)] for v in vectors], means, stds

def centroid(vecs):
    return [sum(v[i] for v in vecs) / len(vecs) for i in range(len(vecs[0]))] if vecs else []

def euclidean(a, b):
    return sqrt(sum((a[i] - b[i])**2 for i in range(len(a))))

def eval_loocv(vectors, labels):
    n = len(vectors)
    results = {}
    for method, k in [("centroid", 1), ("knn_1", 1), ("knn_3", 3)]:
        correct = 0; top2 = 0; conf = defaultdict(lambda: defaultdict(int))
        for i in range(n):
            tv = vectors[:i] + vectors[i+1:]
            tl = labels[:i] + labels[i+1:]
            test_v = vectors[i]; test_l = labels[i]
            if method == "centroid":
                cls_vecs = defaultdict(list)
                for v, l in zip(tv, tl): cls_vecs[l].append(v)
                cents = {l: centroid(vecs) for l, vecs in cls_vecs.items()}
                preds = sorted(cents.keys(), key=lambda l: euclidean(test_v, cents[l]))
                pred = preds[0]
            else:
                dists = [(euclidean(test_v, tv[j]), tl[j]) for j in range(len(tv))]
                dists.sort(key=lambda x: x[0])
                votes = Counter(tl for _, tl in dists[:k])
                pred = votes.most_common(1)[0][0]
                preds = [t[1] for t in dists[:2]]
            conf[test_l][pred] += 1
            if pred == test_l: correct += 1
            if test_l in preds[:2]: top2 += 1
        cls = sorted(set(labels))
        results[method] = {
            "accuracy": round(correct / n, 4),
            "top2_accuracy": round(top2 / n, 4),
            "confusion": {gt: {p: conf[gt][p] for p in cls} for gt in cls},
        }
    return results

FEATURES = ["matrix_size", "rank", "spectral_gap", "laplacian_zero_count", "density", "eigenvalue_max"]

def main():
    t2 = load_jsonl(VECTORS_PATH)
    labels = load_jsonl(LABELS_PATH)

    t2_map = {r["name"]: r for r in t2}
    lmap = {r["theorem_name"]: r for r in labels}

    t2_names, label_names = set(t2_map), set(lmap)
    matched = sorted(t2_names & label_names)
    print(f"Tier 2 vectors: {len(t2_names)}", flush=True)
    print(f"Labels: {len(label_names)}", flush=True)
    print(f"Matched: {len(matched)}", flush=True)
    missing_l = sorted(t2_names - label_names)
    missing_v = sorted(label_names - t2_names)
    if missing_l: print(f"Missing labels: {missing_l}", flush=True)
    if missing_v: print(f"Missing vectors: {missing_v}", flush=True)
    if len(matched) != len(t2_names):
        print(f"WARNING: Only {len(matched)}/{len(t2_names)} vectors have labels", flush=True)
    if len(matched) < 3:
        print("Too few aligned samples. Aborting.", flush=True)
        return 1

    # Build vectors
    vecs = []
    for name in matched:
        r = t2_map[name]
        vecs.append([r.get(f, 0) for f in FEATURES])
    normed, _, _ = normalize(vecs)

    TARGETS = [
        ("proof_status", "proof_status"),
        ("proof_method_label", "proof method"),
        ("domain_label", "domain"),
        ("joint_label", "joint"),
        ("obstruction_label", "obstruction"),
        ("manual_rrc_shape", "manual RRCShape"),
    ]

    all_results = {}
    confusion_matrices = {}

    print(f"\n{'='*80}", flush=True)
    print("TIER 2 PROOF-PATH SPECTRA — LABEL COMPARISON", flush=True)
    print(f"{'='*80}", flush=True)
    print(f"\n{'Target':30s} {'Method':12s} {'Acc':>6} {'Top-2':>6} {'Base':>6} {'Classes':>8} {'Samples':>8}", flush=True)
    print(f"{'-'*30} {'-'*12} {'-'*6} {'-'*6} {'-'*6} {'-'*8} {'-'*8}", flush=True)

    for key, label in TARGETS:
        targets = []
        for name in matched:
            val = lmap[name].get(key, "none")
            if val is None: val = "none"
            targets.append(val)

        dist = Counter(targets)
        classes = sorted(dist.keys())
        base = max(dist.values()) / len(targets)
        print(f"\n{label:30s} distribution: {dict(dist.most_common(5))}", flush=True)

        res = eval_loocv(normed, targets)
        all_results[key] = {}
        for method in ["centroid", "knn_1", "knn_3"]:
            r = res[method]
            all_results[key][method] = {
                "accuracy": r["accuracy"],
                "top2_accuracy": r["top2_accuracy"],
                "baseline": round(base, 4),
            }
            print(f"  {label:28s} {method:12s} {r['accuracy']:6.1%} {r['top2_accuracy']:6.1%} "
                  f"{base:6.1%} {len(classes):8d} {len(targets):8d}", flush=True)

        confusion_matrices[key] = res["centroid"]["confusion"]

    # Read Tier 1 baselines if available
    t1 = {}
    try:
        with open(os.path.join(os.path.dirname(__file__), "../..",
                               "shared-data/pist_canary_ground_truth_report.json")) as f:
            t1d = json.load(f)
            for tk, tl in [("proof_method_label", "proof_method"),
                           ("domain_label", "domain"),
                           ("manual_rrc_shape", "manual RRCShape")]:
                for m in ["centroid", "knn_3"]:
                    k = f"{tk}_{m}"
                    if k in t1d.get("results", {}):
                        t1[k] = t1d["results"][k].get("accuracy", 0)
    except (ValueError, TypeError, KeyError) as e: logging.warning(f"Failed to read Tier 1 baselines: {e}")

    # Summary comparison table
    print(f"\n{'='*80}", flush=True)
    print("SUMMARY: Tier 2 vs Tier 1 vs Majority Baseline", flush=True)
    print(f"{'='*80}", flush=True)
    print(f"\n{'Target':25s} {'T2 best':>8} {'T1 best':>8} {'Baseline':>8} {'Verdict':>12}", flush=True)
    print(f"{'-'*25} {'-'*8} {'-'*8} {'-'*8} {'-'*12}", flush=True)
    for key, label in TARGETS:
        t2_best = max(all_results.get(key, {}).get(m, {}).get("accuracy", 0) for m in ["centroid", "knn_3"])
        t1_best = max((t1.get(f"{key}_centroid", 0), t1.get(f"{key}_knn_3", 0)), default=0)
        base = all_results.get(key, {}).get("centroid", {}).get("baseline", 0)
        verdict = "★ BEATS" if t2_best > t1_best and t2_best > base else \
                  "↑ T2>T1" if t2_best > t1_best else \
                  "→ ties" if abs(t2_best - base) < 0.05 else "↓ below"
        print(f"{label:25s} {t2_best:8.1%} {t1_best:8.1%} {base:8.1%} {verdict:>12s}", flush=True)

    # Save comparison
    report = {
        "n_samples": len(matched),
        "n_features": len(FEATURES),
        "tier2_results": all_results,
        "tier1_baselines": t1,
    }
    with open(COMPARISON_PATH, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nComparison: {COMPARISON_PATH}", flush=True)

    with open(CONFUSION_PATH, "w") as f:
        json.dump(confusion_matrices, f, indent=2)
    print(f"Confusion: {CONFUSION_PATH}", flush=True)
    return 0

if __name__ == "__main__":
    main()
