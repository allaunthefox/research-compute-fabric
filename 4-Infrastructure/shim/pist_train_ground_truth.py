#!/usr/bin/env python3
"""Train on ground-truth labels (proof_method, domain, RRCShape).

Usage:
    python3 pist_train_ground_truth.py
"""

import json
import os
import sys
from collections import Counter, defaultdict
from math import sqrt

FEATURE_VECTORS_PATH = os.path.join(os.path.dirname(__file__), "../..",
                                    "shared-data/pist_canary_feature_vectors.jsonl")
GROUND_TRUTH_PATH = os.path.join(os.path.dirname(__file__), "../..",
                                 "shared-data/pist_canary_ground_truth_labels.jsonl")
REPORT_PATH = os.path.join(os.path.dirname(__file__), "../..",
                           "shared-data/pist_canary_ground_truth_report.json")


def load_vectors(path: str) -> list[dict]:
    rows = []
    with open(path) as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def load_labels(path: str) -> dict[str, dict]:
    labels = {}
    with open(path) as f:
        for line in f:
            row = json.loads(line)
            labels[row["theorem_name"]] = row
    return labels


def normalize(vectors):
    n = len(vectors)
    if n == 0:
        return vectors, [], []
    dim = len(vectors[0])
    means = [sum(v[i] for v in vectors) / n for i in range(dim)]
    stds = [sqrt(sum((v[i] - means[i]) ** 2 for v in vectors) / max(n - 1, 1)) for i in range(dim)]
    stds = [s if s > 1e-9 else 1.0 for s in stds]
    return [[(v[i] - means[i]) / stds[i] for i in range(dim)] for v in vectors], means, stds


def centroid(vecs):
    if not vecs:
        return []
    return [sum(v[i] for v in vecs) / len(vecs) for i in range(len(vecs[0]))]


def euclidean(a, b):
    return sqrt(sum((a[i] - b[i]) ** 2 for i in range(len(a))))


def knn(train_v, train_l, test_v, k):
    dists = sorted(
        [(euclidean(test_v, tv), tl) for tv, tl in zip(train_v, train_l)],
        key=lambda x: x[0],
    )
    votes = Counter(tl for _, tl in dists[:k])
    return votes.most_common(1)[0][0]


def eval_loocv(vectors, labels, method="centroid", k=3):
    n = len(vectors)
    correct = 0
    top2_correct = 0
    n_classes = len(set(labels))
    confusion = defaultdict(lambda: defaultdict(int))

    for i in range(n):
        tv = vectors[:i] + vectors[i + 1 :]
        tl = labels[:i] + labels[i + 1 :]
        test_v = vectors[i]
        test_l = labels[i]

        if method == "centroid":
            cls_vecs = defaultdict(list)
            for v, l in zip(tv, tl):
                cls_vecs[l].append(v)
            cents = {l: centroid(vecs) for l, vecs in cls_vecs.items()}
            preds = sorted(
                cents.keys(), key=lambda l: euclidean(test_v, cents[l])
            )
            pred = preds[0]
            top2 = preds[:2]
        else:
            dists = sorted(
                [(euclidean(test_v, tv[j]), tl[j]) for j in range(len(tv))],
                key=lambda x: x[0],
            )
            votes = Counter(tl for _, tl in dists[:k])
            pred = votes.most_common(1)[0][0]
            top2 = [t[1] for t in dists[:2]]

        confusion[test_l][pred] += 1
        if pred == test_l:
            correct += 1
        if test_l in top2:
            top2_correct += 1

    baseline = max(Counter(labels).values()) / n
    accuracy = correct / n
    top2_acc = top2_correct / n

    return accuracy, top2_acc, dict(confusion), baseline


def main():
    vectors = load_vectors(FEATURE_VECTORS_PATH)
    gt_labels = load_labels(GROUND_TRUTH_PATH)

    # Align by theorem name
    aligned = []
    for v in vectors:
        name = v.get("name", "")
        if name in gt_labels:
            aligned.append((v["vector"], gt_labels[name]))

    n = len(aligned)
    print(f"Aligned vectors: {n}", flush=True)

    raw_vecs = [a[0] for a in aligned]
    normed, _, _ = normalize(raw_vecs)

    TARGETS = [
        ("proof_method_label", "Proof method"),
        ("domain_label", "Domain"),
        ("manual_rrc_shape", "Manual RRCShape"),
    ]

    results = {}

    for key, label in TARGETS:
        print(f"\n{'=' * 60}", flush=True)
        print(f"TARGET: {label} ({key})", flush=True)
        print(f"{'=' * 60}", flush=True)

        targets = []
        for _, lbl in aligned:
            val = lbl.get(key, "unknown")
            if val is None:
                val = "none"
            targets.append(val)

        classes = sorted(set(targets))
        dist = Counter(targets)
        print(f"Classes ({len(classes)}): {dict(dist)}", flush=True)
        print(f"Majority baseline: {max(dist.values()) / n:.1%}", flush=True)

        for method, k in [
            ("centroid", None),
            ("knn_1", 1),
            ("knn_3", 3),
            ("knn_5", 5),
        ]:
            acc, top2, conf, baseline = eval_loocv(
                normed, targets, "centroid" if method == "centroid" else "knn", k or 3
            )
            print(f"  {method:15s} LOOCV: {acc:.1%} ({int(acc * n)}/{n})  "
                  f"top-2: {top2:.1%}  baseline: {baseline:.1%}",
                  flush=True)

            results[f"{key}_{method}"] = {
                "accuracy": round(acc, 4),
                "top2_accuracy": round(top2, 4),
                "baseline": round(baseline, 4),
                "n_classes": len(classes),
                "improvement_over_baseline": round(
                    (acc - baseline) / max(baseline, 0.01), 3
                ),
            }

        # Per-class accuracy for centroid
        acc, top2, conf, baseline = eval_loocv(normed, targets, "centroid", 3)
        print(f"\n  Per-class (centroid):")
        for cls in sorted(classes):
            tp = conf.get(cls, {}).get(cls, 0)
            total = dist[cls]
            print(f"    {cls:30s} {tp:3d}/{total:3d} = {tp / max(total, 1):.0%}")

    # Summary
    print(f"\n{'=' * 60}", flush=True)
    print("SUMMARY", flush=True)
    print(f"{'=' * 60}", flush=True)
    print(f"{'Target':35s} {'Method':12s} {'Acc':>6} {'Top-2':>6} {'Base':>6} {'Impr':>6}",
          flush=True)
    print(f"{'-' * 35} {'-' * 12} {'-' * 6} {'-' * 6} {'-' * 6} {'-' * 6}", flush=True)
    for key, label in TARGETS:
        for method in ["centroid", "knn_3"]:
            r = results.get(f"{key}_{method}", {})
            impr = r.get("improvement_over_baseline", 0)
            print(
                f"{label:35s} {method:12s} "
                f"{r.get('accuracy', 0):6.1%} "
                f"{r.get('top2_accuracy', 0):6.1%} "
                f"{r.get('baseline', 0):6.1%} "
                f"{impr:>+5.1f}x",
                flush=True,
            )

    # Save report
    report = {
        "n_samples": n,
        "targets": {key: label for key, label in TARGETS},
        "results": results,
        "class_distributions": {
            key: dict(Counter([lbl.get(key, "unknown") for _, lbl in aligned]))
            for key, _ in TARGETS
        },
    }
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport: {REPORT_PATH}", flush=True)
    return 0


if __name__ == "__main__":
    main()
