#!/usr/bin/env python3
"""Calibration harness for the PIST spectral classifier.

Reads the validation report, extracts spectral feature vectors,
tests separability via leave-one-out nearest-centroid classification.
Does NOT produce a production model — only a measured calibration signal.
"""

import json
import os
import sys
import argparse
from collections import defaultdict
from math import sqrt

FEATURE_NAMES = [
    "zero_mode_proxy_count",
    "rank_estimate",
    "laplacian_zero_count",
    "spectral_gap",
    "crossing_density",
    "strand_entropy",
]

EIGEN_LEN = 8   # symmetric_eigenvalues[0:8]
SINGULAR_LEN = 8  # singular_values[0:8]


def extract_vector(p: dict) -> list[float]:
    """Build a flat numeric vector from one prediction entry."""
    v = []
    for name in FEATURE_NAMES:
        v.append(float(p.get(name, 0)))
    # Eigenvalues
    ev = p.get("eigenvalues", [])
    for i in range(EIGEN_LEN):
        v.append(float(ev[i]) if i < len(ev) else 0.0)
    # Singular values (if present; zero-padded if absent)
    sv = p.get("singular_values", [])
    for i in range(SINGULAR_LEN):
        v.append(float(sv[i]) if i < len(sv) else 0.0)
    return v


def feature_dim() -> int:
    return len(FEATURE_NAMES) + EIGEN_LEN + SINGULAR_LEN


def normalize(vectors: list[list[float]]) -> tuple[list[list[float]], list[float], list[float]]:
    """Z-score normalize each feature dimension."""
    n = len(vectors)
    if n == 0:
        return vectors, [], []
    dim = len(vectors[0])
    means = [sum(v[i] for v in vectors) / n for i in range(dim)]
    stds = [sqrt(sum((v[i] - means[i]) ** 2 for v in vectors) / max(n - 1, 1)) for i in range(dim)]
    stds = [s if s > 1e-9 else 1.0 for s in stds]  # avoid div-by-zero
    normed = [[(v[i] - means[i]) / stds[i] for i in range(dim)] for v in vectors]
    return normed, means, stds


def centroid(vectors: list[list[float]]) -> list[float]:
    if not vectors:
        return []
    dim = len(vectors[0])
    return [sum(v[i] for v in vectors) / len(vectors) for i in range(dim)]


def euclidean(a: list[float], b: list[float]) -> float:
    return sqrt(sum((a[i] - b[i]) ** 2 for i in range(len(a))))


def nearest_centroid_classify(
    vectors: list[list[float]], labels: list[str], centroids: dict[str, list[float]]
) -> list[str]:
    results = []
    for v in vectors:
        best_label = None
        best_dist = float("inf")
        for label, c in centroids.items():
            d = euclidean(v, c)
            if d < best_dist:
                best_dist = d
                best_label = label
        results.append(best_label)
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Calibration harness for PIST spectral classifier"
    )
    parser.add_argument(
        "--input",
        default="shared-data/rrc_pist_exact_validation.json",
        help="Input validation report JSON",
    )
    parser.add_argument(
        "--out",
        default="shared-data/rrc_pist_training_report.json",
        help="Output training report JSON",
    )
    parser.add_argument(
        "--vectors",
        default="shared-data/rrc_pist_feature_vectors.jsonl",
        help="Output feature vectors as JSONL",
    )
    args = parser.parse_args()

    # ── Load validation report ──
    input_path = os.path.join(os.path.dirname(__file__), "../..", args.input)
    with open(input_path) as f:
        report = json.load(f)

    predictions = report.get("predictions", [])
    n = len(predictions)
    if n == 0:
        print("ERROR: No predictions found in input.", flush=True)
        return 1

    print(f"Loaded {n} labeled predictions", flush=True)

    # ── Build feature vectors ──
    vectors = []
    labels = []
    for p in predictions:
        v = extract_vector(p)
        vectors.append(v)
        labels.append(p["ground_truth"])

    # Normalize
    normed, means, stds = normalize(vectors)
    dim = feature_dim()

    # ── Feature variance diagnostic ──
    feature_var = {}
    for i, name in enumerate(FEATURE_NAMES):
        vals = [v[i] for v in vectors]
        mean = sum(vals) / n
        var = sum((x - mean) ** 2 for x in vals) / max(n - 1, 1)
        uniq = len(set(vals))
        feature_var[name] = {
            "mean": round(mean, 4),
            "variance": round(var, 4),
            "unique": uniq,
            "collapsed": uniq <= 1,
        }

    for band in ["eigenvalues", "singular_values"]:
        for i in range(8):
            idx = len(FEATURE_NAMES) + (0 if band == "eigenvalues" else 8) + i
            vals = [v[idx] for v in vectors]
            mean = sum(vals) / n
            var = sum((x - mean) ** 2 for x in vals) / max(n - 1, 1)
            uniq = len(set(round(x, 6) for x in vals))
            feature_var[f"{band}[{i}]"] = {
                "mean": round(mean, 4),
                "variance": round(var, 4),
                "unique": uniq,
                "collapsed": uniq <= 1,
            }

    collapsed_dims = [k for k, v in feature_var.items() if v.get("collapsed")]
    print(f"  Feature dimensions: {dim}", flush=True)
    print(f"  Collapsed features: {len(collapsed_dims)} {collapsed_dims[:5]}", flush=True)

    # ── Unique labels ──
    unique_labels = sorted(set(labels))
    print(f"  Unique labels: {len(unique_labels)} {unique_labels}", flush=True)

    # ── Label balance ──
    label_counts = defaultdict(int)
    for lbl in labels:
        label_counts[lbl] += 1
    print(f"  Label distribution:", flush=True)
    for lbl in sorted(label_counts.keys()):
        print(f"    {lbl:35s}: {label_counts[lbl]:3d}", flush=True)

    # ── Leave-one-out nearest-centroid ──
    correct = 0
    confusion = defaultdict(lambda: defaultdict(int))
    class_distances = defaultdict(list)

    for i in range(n):
        train_v = normed[:i] + normed[i + 1:]
        train_l = labels[:i] + labels[i + 1:]
        test_v = normed[i]
        test_l = labels[i]

        # Build centroids per class from training set
        class_vectors = defaultdict(list)
        for v, lbl in zip(train_v, train_l):
            class_vectors[lbl].append(v)
        centroids = {lbl: centroid(vecs) for lbl, vecs in class_vectors.items()}

        # Classify test point
        best_label = None
        best_dist = float("inf")
        for lbl, c in centroids.items():
            d = euclidean(test_v, c)
            if d < best_dist:
                best_dist = d
                best_label = lbl
        class_distances[test_l].append(best_dist)

        if best_label == test_l:
            correct += 1
        confusion[test_l][best_label] += 1

    accuracy = correct / n if n > 0 else 0
    print(f"\n  Leave-one-out nearest-centroid accuracy: {correct}/{n} = {accuracy:.1%}",
          flush=True)

    # Per-class accuracy
    print(f"\n  Per-class:", flush=True)
    print(f"    {'Class':35s} {'N':>5} {'Correct':>8} {'Acc':>6}", flush=True)
    for lbl in sorted(unique_labels):
        total = label_counts[lbl]
        corr = confusion[lbl][lbl]
        print(f"    {lbl:35s} {total:5d} {corr:8d} {(corr/total*100 if total else 0):5.1f}%",
              flush=True)

    # Confusion matrix
    print(f"\n  Confusion matrix (rows=truth, cols=pred):", flush=True)
    header = f"    {'':20s}" + "".join(f"{c[:16]:>16s}" for c in unique_labels)
    print(header)
    for gt in unique_labels:
        row = f"    {gt[:20]:20s}"
        for p in unique_labels:
            row += f"{confusion[gt][p]:>16d}"
        print(row)

    # Nearest same-class vs different-class distance
    same_dists = []
    diff_dists = []
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            d = euclidean(normed[i], normed[j])
            if labels[i] == labels[j]:
                same_dists.append(d)
            else:
                diff_dists.append(d)
    avg_same = sum(same_dists) / len(same_dists) if same_dists else 0
    avg_diff = sum(diff_dists) / len(diff_dists) if diff_dists else 0
    sep_ratio = avg_same / max(avg_diff, 1e-9)
    print(f"\n  Within-class mean distance: {avg_same:.4f}", flush=True)
    print(f"  Between-class mean distance: {avg_diff:.4f}", flush=True)
    print(f"  Separation ratio (same/diff): {sep_ratio:.4f}", flush=True)

    # ── Class centroids ──
    centroids: dict[str, list[float]] = {}
    for lbl in unique_labels:
        idxs = [i for i, l in enumerate(labels) if l == lbl]
        centroids[lbl] = centroid([normed[i] for i in idxs])

    # ── Build warnings ──
    warnings = [
        f"Only {n} labeled samples; classifier is calibration-only.",
        "Do not promote model to production until full 278 labeled equations are available.",
    ]
    if collapsed_dims:
        warnings.append(
            f"Collapsed features ({len(collapsed_dims)}): {collapsed_dims[:5]}. "
            "These dimensions carry no discriminative power."
        )
    if accuracy < 0.3:
        warnings.append("Accuracy below 30%. Spectral features may need richer extraction.")
    elif accuracy > 0.7:
        warnings.append(f"Accuracy {accuracy:.0%} is promising but overfits to {n} samples.")

    # ── Output report ──
    report = {
        "n_samples": n,
        "dimension": dim,
        "method": "leave_one_out_nearest_centroid_v1",
        "accuracy": round(accuracy, 4),
        "unique_labels": unique_labels,
        "label_distribution": dict(label_counts),
        "per_class": {
            lbl: {
                "n": label_counts[lbl],
                "correct": confusion[lbl][lbl],
                "accuracy": round(confusion[lbl][lbl] / max(label_counts[lbl], 1), 4),
            }
            for lbl in unique_labels
        },
        "confusion_matrix": {gt: dict(preds) for gt, preds in confusion.items()},
        "feature_variance": feature_var,
        "collapsed_features": collapsed_dims,
        "within_class_distance": round(avg_same, 4),
        "between_class_distance": round(avg_diff, 4),
        "separation_ratio": round(sep_ratio, 4),
        "class_centroids": {lbl: [round(v, 4) for v in c] for lbl, c in centroids.items()},
        "normalization": {
            "means": [round(m, 4) for m in means],
            "stds": [round(s, 4) for s in stds],
        },
        "warnings": warnings,
    }

    out_path = os.path.join(os.path.dirname(__file__), "../..", args.out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport: {out_path}", flush=True)

    # ── Output feature vectors as JSONL ──
    vecs_path = os.path.join(os.path.dirname(__file__), "../..", args.vectors)
    os.makedirs(os.path.dirname(vecs_path), exist_ok=True)
    with open(vecs_path, "w") as f:
        for p, v, l in zip(predictions, normed, labels):
            row = {
                "equation": p["equation"],
                "label": l,
                "features": {name: round(v[i], 6) for i, name in enumerate(FEATURE_NAMES)},
                "eigenvalues": [round(v[len(FEATURE_NAMES) + i], 6) for i in range(EIGEN_LEN)],
                "singular_values": [round(v[len(FEATURE_NAMES) + EIGEN_LEN + i], 6) for i in range(SINGULAR_LEN)],
                "vector": [round(x, 6) for x in v],
            }
            f.write(json.dumps(row) + "\n")
    print(f"Feature vectors: {vecs_path}", flush=True)

    return 0 if accuracy > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
