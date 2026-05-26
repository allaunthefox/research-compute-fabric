#!/usr/bin/env python3
"""Compare Tier 1 hash-spectra vs Tier 2 proof-path spectra on independent labels.

Reads:
  - shared-data/pist_trace_tier2b_vectors.jsonl (Tier 2B spectral features)
  - shared-data/pist_canary_ground_truth_labels.jsonl (independent labels)
  - shared-data/pist_canary_ground_truth_report.json (Tier 1 baseline)

Outputs:
  - shared-data/pist_tier1_vs_tier2_comparison.json
"""
import json
import os
import sys
from collections import Counter, defaultdict
from math import sqrt

VECTORS_PATH = os.path.join(os.path.dirname(__file__), "../..",
                            "shared-data/pist_trace_tier2b_vectors.jsonl")
LABELS_PATH = os.path.join(os.path.dirname(__file__), "../..",
                           "shared-data/pist_trace_v2_ground_truth_labels.jsonl")
TIER1_PATH = os.path.join(os.path.dirname(__file__), "../..",
                          "shared-data/pist_canary_ground_truth_report.json")
OUT_PATH = os.path.join(os.path.dirname(__file__), "../..",
                        "shared-data/pist_tier1_vs_tier2_comparison.json")


def normalize(vectors):
    n = len(vectors)
    if n == 0: return vectors, [], []
    dim = len(vectors[0])
    means = [sum(v[i] for v in vectors) / n for i in range(dim)]
    stds = [sqrt(sum((v[i] - means[i])**2 for v in vectors) / max(n-1,1)) for i in range(dim)]
    stds = [s if s > 1e-9 else 1.0 for s in stds]
    return [[(v[i] - means[i]) / stds[i] for i in range(dim)] for v in vectors], means, stds


def centroid(vecs):
    return [sum(v[i] for v in vecs) / len(vecs) for i in range(len(vecs[0]))] if vecs else []


def euclidean(a, b):
    return sqrt(sum((a[i] - b[i])**2 for i in range(len(a))))


def eval_loocv(vectors, labels, k=3):
    n = len(vectors)
    correct = 0
    top2 = 0
    confusion = defaultdict(lambda: defaultdict(int))
    for i in range(n):
        tv = vectors[:i] + vectors[i+1:]
        tl = labels[:i] + labels[i+1:]
        tv_v = test_v = vectors[i]
        test_l = labels[i]
        cls_vecs = defaultdict(list)
        for v, l in zip(tv, tl):
            cls_vecs[l].append(v)
        cents = {l: centroid(vecs) for l, vecs in cls_vecs.items()}
        preds = sorted(cents.keys(), key=lambda l: euclidean(test_v, cents[l]))
        pred = preds[0]
        if pred == test_l: correct += 1
        if test_l in preds[:2]: top2 += 1
    acc = correct / n
    return acc, top2 / n, max(Counter(labels).values()) / n


BUILTIN_FEATURES = ["matrix_size", "rank", "spectral_gap", "laplacian_zero_count", "density", "eigenvalue_max"]


def main():
    # Load Tier 2B vectors
    t2_records = {}
    with open(VECTORS_PATH) as f:
        for line in f:
            r = json.loads(line)
            t2_records[r["name"]] = r
    print(f"Tier 2 vectors: {len(t2_records)}", flush=True)

    # Load ground-truth labels
    labels = {}
    with open(LABELS_PATH) as f:
        for line in f:
            lbl = json.loads(line)
            labels[lbl["theorem_name"]] = lbl
    print(f"Labels: {len(labels)}", flush=True)

    # Load Tier 1 report for baseline comparison
    tier1_baselines = {}
    try:
        with open(TIER1_PATH) as f:
            t1 = json.load(f)
            for target_key, target_label in t1.get("targets", {}).items():
                for method in ["centroid", "knn_3"]:
                    key = f"{target_key}_{method}"
                    if key in t1.get("results", {}):
                        tier1_baselines[key] = t1["results"][key]["accuracy"]
    except FileNotFoundError:
        pass
    print(f"Tier 1 baselines: {len(tier1_baselines)} targets", flush=True)

    # Align records by name
    aligned = [(k, v) for k, v in t2_records.items() if k in labels]
    print(f"Aligned: {len(aligned)}", flush=True)

    # Build feature vectors
    t2_vectors = []
    t2_names = []
    for name, rec in aligned:
        vec = [rec.get(f, 0) for f in BUILTIN_FEATURES]
        t2_vectors.append(vec)
        t2_names.append(name)

    t2_norm, _, _ = normalize(t2_vectors)
    print(f"Tier 2 feature dim: {len(BUILTIN_FEATURES)}", flush=True)

    TARGETS = [
        ("proof_status", "proof_status"),
        ("proof_method_label", "proof method"),
        ("domain_label", "domain"),
        ("manual_rrc_shape", "manual RRCShape"),
    ]

    results = {}
    print(f"\n{'='*70}", flush=True)
    print("TIER 2 VS TIER 1 COMPARISON", flush=True)
    print(f"{'='*70}", flush=True)
    print(f"\n{'Target':30s} {'Method':12s} {'Tier 2':>8} {'Tier 1':>8} {'Majority':>8} {'Improves':>10}",
          flush=True)
    print(f"{'-'*30} {'-'*12} {'-'*8} {'-'*8} {'-'*8} {'-'*10}", flush=True)

    for key, label in TARGETS:
        targets = []
        for name in t2_names:
            val = labels[name].get(key, "unknown") or "none"
            targets.append(val)

        dist = Counter(targets)
        majority_baseline = max(dist.values()) / len(targets)
        print(f"\n{label:30s} distribution: {dict(dist.most_common(3))}", flush=True)

        for method_name, method_key in [("centroid", "centroid"), ("knn_3", "knn_3")]:
            acc, top2, majority = eval_loocv(t2_norm, targets, 3 if method_key != "centroid" else 1)

            t1_key = f"{key}_{method_key}"
            tier1_acc = tier1_baselines.get(t1_key, None)

            improves = "YES" if tier1_acc is not None and acc > tier1_acc else ("NO" if tier1_acc is not None else "N/A")

            print(f"  {label:28s} {method_name:12s} "
                  f"{acc:8.1%} {tier1_acc or 0:8.1%} {majority:8.1%} {improves:>10s}",
                  flush=True)

            results[f"{key}_{method_key}"] = {
                "tier2_accuracy": round(acc, 4),
                "tier2_top2": round(top2, 4),
                "tier1_accuracy": round(tier1_acc, 4) if tier1_acc else None,
                "majority_baseline": round(majority, 4),
                "tier2_beats_tier1": acc > (tier1_acc or 0),
                "improves_over_baseline": round((acc - majority) / max(majority, 0.01), 3),
                "n_samples": len(targets),
                "distribution": dict(dist),
            }

    # Print summary
    print(f"\n{'='*70}", flush=True)
    print("SUMMARY: Does Tier 2 beat Tier 1?", flush=True)
    print(f"{'='*70}", flush=True)
    wins = sum(1 for k, v in results.items() if v.get("tier2_beats_tier1"))
    total = sum(1 for k, v in results.items() if v.get("tier1_accuracy") is not None)
    print(f"Tier 2 wins: {wins}/{total} targets", flush=True)
    for k, v in sorted(results.items()):
        if v.get("tier1_accuracy") is not None:
            comp = "BEATS" if v["tier2_accuracy"] > v["tier1_accuracy"] else "behind"
            print(f"  {k:35s} T2={v['tier2_accuracy']:.1%} T1={v['tier1_accuracy']:.1%} ({comp})", flush=True)

    # Save
    report = {
        "n_samples": len(aligned),
        "tier2_accuracy": {"proof_status": results.get("proof_status_centroid", {}).get("tier2_accuracy", 0)},
        "results": results,
        "conclusion": {
            "tier2_wins": wins,
            "total_comparable": total,
        }
    }
    with open(OUT_PATH, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport: {OUT_PATH}", flush=True)
    return 0


if __name__ == "__main__":
    main()
