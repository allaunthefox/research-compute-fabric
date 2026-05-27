#!/usr/bin/env python3
"""Enrich canary receipts with full spectral data, then train classifiers.

Usage:
    python3 pist_enrich_and_train.py
"""

import json
import os
import subprocess
import sys
import tempfile
from collections import defaultdict
from math import sqrt

PIST_DECOMPOSE = os.environ.get(
    "PIST_DECOMPOSE_BIN",
    "/home/allaun/.local/share/opencode/worktree/"
    "0b42981cf7f7d5e172b1e93f8d4bb64a3dd63962/Turn-and-Burn/infra/rust/"
    "ene-rds/target/release/pist-decompose",
)

FEATURE_NAMES = [
    "zero_mode_proxy_count",
    "rank_estimate",
    "laplacian_zero_count",
    "spectral_gap",
    "crossing_density",
    "strand_entropy",
]
EIGEN_LEN = 8
SINGULAR_LEN = 8


def extract(pist_out: dict) -> dict:
    """Extract flattened feature vector from pist-decompose output."""
    spectral = pist_out.get("spectral", {})
    braid = pist_out.get("braid", {})
    gamma = pist_out.get("gamma_packet", {})
    zmp = spectral.get("zero_mode_proxy_count", 0)
    rank = spectral.get("rank_estimate", 0)
    lap0 = spectral.get("laplacian_zero_count", 0)
    gap = spectral.get("symmetric_spectral_gap", 0)
    cd = braid.get("crossing_density", 0)
    sent = braid.get("strand_entropy", 0)
    ev = spectral.get("symmetric_eigenvalues")
    if not ev:
        ev = [0.0] * 8
    sv = spectral.get("singular_values")
    if not sv:
        sv = [0.0] * 8
    slack = braid.get("sidon_slack", 0)
    yb = braid.get("yang_baxter_valid", True)
    steps = braid.get("step_count", 0)
    gamma_v = gamma.get("gamma", {}).get("value", 0)
    chi = gamma.get("chi", 0)
    kappa = gamma.get("kappa", 0)
    tau = gamma.get("tau", 0)
    theta = gamma.get("theta", 0)
    eps = gamma.get("epsilon", 0)
    mhash = braid.get("matrix_hash", "?")[:16]
    chash = pist_out.get("canonical_hash", "?")[:16]

    vec = [zmp, rank, lap0, gap, cd, sent]
    for v in ev[:EIGEN_LEN]:
        vec.append(float(v))
    for v in sv[:SINGULAR_LEN]:
        vec.append(float(v))
    vec.extend([float(slack), 1.0 if yb else 0.0, float(steps),
                float(gamma_v), float(chi), float(kappa), float(tau), float(theta), float(eps)])

    return {
        "vector": vec,
        "features": dict(zip(FEATURE_NAMES, [zmp, rank, lap0, gap, cd, sent])),
        "eigenvalues": [round(float(v), 6) for v in ev[:EIGEN_LEN]],
        "singular_values": [round(float(v), 6) for v in sv[:SINGULAR_LEN]],
        "matrix_hash": mhash,
        "canonical_hash": chash,
    }


def run_pist(receipt: dict) -> dict | None:
    """Run pist-decompose on a receipt dict."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(receipt, f)
        fpath = f.name
    try:
        r = subprocess.run([PIST_DECOMPOSE, fpath, "--num-leaves", "8"],
                           capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            return None
        return json.loads(r.stdout)
    finally:
        os.unlink(fpath)


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
    dists = [(euclidean(test_v, tv), tl) for tv, tl in zip(train_v, train_l)]
    dists.sort(key=lambda x: x[0])
    nearest = dists[:k]
    votes = defaultdict(int)
    for _, lbl in nearest:
        votes[lbl] += 1
    return max(votes, key=votes.get)


def eval_loocv(vectors, labels, method="centroid", k=3):
    n = len(vectors)
    correct = 0
    top2_correct = 0
    confusion = defaultdict(lambda: defaultdict(int))
    for i in range(n):
        train_v = vectors[:i] + vectors[i + 1:]
        train_l = labels[:i] + labels[i + 1:]
        test_v = vectors[i]
        test_l = labels[i]

        if method == "centroid":
            cls_vecs = defaultdict(list)
            for v, lbl in zip(train_v, train_l):
                cls_vecs[lbl].append(v)
            centroids_dict = {lbl: centroid(vecs) for lbl, vecs in cls_vecs.items()}
            pred = min(centroids_dict, key=lambda lbl: euclidean(test_v, centroids_dict[lbl]))
        else:
            pred = knn(train_v, train_l, test_v, k)

        confusion[test_l][pred] += 1
        if pred == test_l:
            correct += 1
        # top-2 check
        dists = sorted([(euclidean(test_v, cent), lbl) for lbl, cent in centroids_dict.items()]) if method == "centroid" else sorted([(euclidean(test_v, train_v[j]), train_l[j]) for j in range(len(train_v))])[:2]
        top2_labels = [d[1] for d in dists[:2]]
        if test_l in top2_labels:
            top2_correct += 1

    return correct / n, top2_correct / n, dict(confusion)


def main():
    receipts_path = os.path.join(os.path.dirname(__file__), "../..",
                                 "shared-data/pist_canary_receipts.jsonl")
    results_path = os.path.join(os.path.dirname(__file__), "../..",
                                "shared-data/pist_canary_results.jsonl")

    # Load results to get status/label info
    results = []
    with open(results_path) as f:
        for line in f:
            row = json.loads(line)
            results.append(row)

    # Load receipts and run PIST
    enriched = []
    with open(receipts_path) as f:
        for line in f:
            receipt = json.loads(line)
            enriched.append(receipt)

    print(f"Loaded {len(results)} results, {len(enriched)} receipts", flush=True)

    # Re-run PIST on each receipt and collect rich features
    records = []
    for i, (result, receipt) in enumerate(zip(results, enriched)):
        print(f"  [{i+1}/{len(results)}] {result['name']:30s} ... ", end="", flush=True)
        pist = run_pist(receipt)
        if pist is None:
            print("PIST FAILED", flush=True)
            continue
        ext = extract(pist)
        records.append({
            "name": result["name"],
            "status": result["status"],
            "ok": result["ok"],
            "rrc_shape": result["exact_shape"],
            "vector": ext["vector"],
            "features": ext["features"],
            "eigenvalues": ext["eigenvalues"],
            "singular_values": ext["singular_values"],
            "matrix_hash": ext["matrix_hash"],
            "canonical_hash": ext["canonical_hash"],
        })
        print(f"ok ZMP={ext['features']['zero_mode_proxy_count']} rank={ext['features']['rank_estimate']}", flush=True)

    n = len(records)
    print(f"\nEnriched: {n} records", flush=True)

    # Prepare feature matrix
    vectors = [r["vector"] for r in records]
    dim = len(vectors[0])
    normed, means, stds = normalize(vectors)

    # Feature variance
    print(f"\nFeature dimensions: {dim}", flush=True)
    for i, name in enumerate(FEATURE_NAMES):
        vals = [r["features"][name] for r in records]
        uniq = len(set(vals))
        print(f"  {name:25s} uniq={uniq:2d} vals=[{min(vals)},{max(vals)}]", flush=True)

    # ── Train on rrc_shape ──
    print("\n" + "=" * 60, flush=True)
    print("TARGET: RRCShape (exact classifier prediction)", flush=True)
    print("=" * 60, flush=True)

    labels_rrc = [r["rrc_shape"] for r in records]
    unique_labels = sorted(set(labels_rrc))
    print(f"Labels: {unique_labels}", flush=True)
    print(f"Distribution: {dict(Counter(labels_rrc))}", flush=True)

    for method, k in [("centroid", None), ("knn_1", 1), ("knn_3", 3), ("knn_5", 5)]:
        acc, top2, conf = eval_loocv(normed, labels_rrc, "centroid" if method == "centroid" else "knn", k or 3)
        print(f"\n  {method:15s} LOOCV accuracy: {acc:.1%} ({int(acc*n)}/{n}) top-2: {top2:.1%}", flush=True)

    # ── Train on proof status ──
    print("\n" + "=" * 60, flush=True)
    print("TARGET: Proof Status (verified vs failed)", flush=True)
    print("=" * 60, flush=True)

    # Map status to binary
    def status_binary(s):
        return "verified" if "verified" in s else "failed"

    labels_status = [status_binary(r["status"]) for r in records]
    print(f"Distribution: {dict(Counter(labels_status))}", flush=True)

    for method, k in [("centroid", None), ("knn_3", 3), ("knn_5", 5)]:
        acc, top2, conf = eval_loocv(normed, labels_status, "centroid" if method == "centroid" else "knn", k or 3)
        print(f"  {method:15s} LOOCV accuracy: {acc:.1%} ({int(acc*n)}/{n})", flush=True)

    # ── Save enriched features ──
    vec_path = os.path.join(os.path.dirname(__file__), "../..",
                            "shared-data/pist_canary_feature_vectors.jsonl")
    with open(vec_path, "w") as f:
        for r in records:
            f.write(json.dumps({
                "name": r["name"],
                "status": r["status"],
                "rrc_shape": r["rrc_shape"],
                "vector": [round(x, 6) for x in r["vector"]],
                "features": r["features"],
                "eigenvalues": r["eigenvalues"],
                "singular_values": r["singular_values"],
            }) + "\n")
    print(f"\nFeature vectors: {vec_path}", flush=True)

    # Summary report
    rrc_acc_centroid, rrc_top2, _ = eval_loocv(normed, labels_rrc, "centroid")
    status_acc_centroid, status_top2, _ = eval_loocv(normed, labels_status, "centroid", 3)

    report = {
        "n_samples": n,
        "dimension": dim,
        "targets": ["rrc_shape", "proof_status"],
        "rrc_shape": {
            "unique_labels": unique_labels,
            "distribution": dict(Counter(labels_rrc)),
            "centroid_loocv_accuracy": round(rrc_acc_centroid, 4),
            "centroid_top2_accuracy": round(rrc_top2, 4),
        },
        "proof_status": {
            "distribution": dict(Counter(labels_status)),
            "centroid_loocv_accuracy": round(status_acc_centroid, 4),
            "centroid_top2_accuracy": round(status_top2, 4),
        },
        "warnings": [
            f"Only {n} samples; all results are calibration-only.",
            "Do not promote to production until 278+ labeled artifacts.",
        ],
    }

    report_path = os.path.join(os.path.dirname(__file__), "../..",
                               "shared-data/pist_canary_training_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Report: {report_path}", flush=True)
    return 0


if __name__ == "__main__":
    from collections import Counter
    sys.exit(main())
