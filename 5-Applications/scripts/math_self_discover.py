#!/usr/bin/env python3
"""
Math Self-Discovery: Unsupervised Structural Taxonomy from Naked Equations.

Feeds the stripped math-raw dataset into two parallel discovery channels:
  1. STRUCTURAL FINGERPRINTING — canonicalizes each equation to a "shape signature"
     by anonymizing variables, collapsing numbers, normalizing whitespace.
     Groups equations by pure structural form (e.g., v0 = v1 + v2).

  2. EMBEDDING + DENSITY CLUSTERING — TF-IDF vectors of math tokens,
     UMAP dimensionality reduction, HDBSCAN density-based clustering.
     Discovers usage-based groupings (e.g., all equations using ∂, ∇ together).

No human labels, no domain tags, no pattern names.
The clusters emerge from the math itself.
"""

import re
import json
import uuid
import hashlib
from collections import Counter, defaultdict
from datetime import datetime

import numpy as np
import pyarrow.parquet as pq
import pyarrow as pa
from sklearn.feature_extraction.text import TfidfVectorizer
import umap
import hdbscan

BASE = "/home/allaun/Documents/Research Stack/3-Mathematical-Models/equations_parquet_tagged"
INPUT = f"{BASE}/equations_math_raw.parquet"
OUTPUT = f"{BASE}/../math_self_discovered.json"
CLUSTERED = f"{BASE}/equations_self_clustered.parquet"
SUMMARY = f"{BASE}/../math_self_discovery_summary.json"

# ── Config ───────────────────────────────────────────────────────────────────
SAMPLE_SIZE = 100_000      # For UMAP+HDBSCAN (density clustering is expensive)
N_TOP_FINGERPRINTS = 100   # Report top structural motifs
N_CLUSTERS_TO_SAMPLE = 50  # Show samples from top embedding clusters

# ── 1. Structural Fingerprinting ───────────────────────────────────────────────

# Token types for variable anonymization
GREEK = r'[αβγδεζηθικλμνξοπρστυφχψωΓΔΘΛΞΠΣΦΨΩ]'
LATIN_VAR = r'[a-zA-Z]'
NUMBER = r'\d+(?:\.\d+)?'

VAR_COUNTER = 0
VAR_MAP = {}

def reset_var_map():
    global VAR_COUNTER, VAR_MAP
    VAR_COUNTER = 0
    VAR_MAP = {}

def get_var_token(var: str) -> str:
    """Map a variable name to a generic vN token, preserving Greek separately."""
    global VAR_COUNTER
    key = var.strip()
    if key not in VAR_MAP:
        VAR_MAP[key] = f"v{VAR_COUNTER}"
        VAR_COUNTER += 1
    return VAR_MAP[key]

def structural_fingerprint(eq: str) -> str:
    """
    Create a canonical structural signature of an equation.
    - Replaces variable names with generic v0, v1, ...
    - Collapses numbers to 'N'
    - Normalizes whitespace
    - Removes LaTeX command backslashes
    """
    if not eq:
        return ""

    reset_var_map()
    text = eq.strip()

    # Remove LaTeX command backslashes (keep the command name as token)
    text = re.sub(r'\\([a-zA-Z]+)', r'\1', text)

    # Replace numbers with N
    text = re.sub(r'\d+(?:\.\d+)?', 'N', text)

    # Tokenize: Greek letters, Latin single letters, multi-letter identifiers
    # Greek letters → g0, g1, ...
    greek_map = {}
    greek_counter = [0]
    def greek_repl(m):
        c = m.group(0)
        if c not in greek_map:
            greek_map[c] = f"g{greek_counter[0]}"
            greek_counter[0] += 1
        return greek_map[c]
    text = re.sub(GREEK, greek_repl, text)

    # Single Latin letters (that look like variables) → vN
    # But avoid replacing inside words. Use a heuristic: standalone letters
    def latin_repl(m):
        return get_var_token(m.group(0))
    text = re.sub(r'(?<![a-zA-Z])[a-zA-Z](?![a-zA-Z])', latin_repl, text)

    # Multi-letter identifiers (functions, commands without backslash)
    def multi_repl(m):
        w = m.group(0)
        # Skip common math function names
        if w.lower() in {'sin', 'cos', 'tan', 'exp', 'log', 'ln', 'sqrt',
                         'det', 'tr', 'dim', 'ker', 'rank', 'span'}:
            return w.lower()
        return get_var_token(w)
    text = re.sub(r'[a-zA-Z]{2,}', multi_repl, text)

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Collapse repeated N N N → N
    text = re.sub(r'N\s+N', 'N', text)
    text = re.sub(r'N\s+N', 'N', text)

    return text


# ── 2. Embedding + Density Clustering ────────────────────────────────────────

def math_tokenizer(text: str) -> list:
    """Tokenize math into structural units for TF-IDF."""
    tokens = []
    # Multi-char operators
    tokens += re.findall(r'==|<=|>=|!=|\\to|\\mapsto|\\cdot|\\times|\\frac|\\sum|\\prod|\\int', text)
    # Single-char math operators and symbols
    tokens += re.findall(r'[\+\-*/=<>≥≤≈∼∂∇∆∫∑∏±∓×÷√∧∨¬⇒⇔∀∃⟨⟩|∈∉⊂⊃⊆⊇∪∩→↦^]', text)
    # Greek letters
    tokens += re.findall(GREEK, text)
    # Variables (single latin letters)
    tokens += re.findall(r'(?<![a-zA-Z])[a-zA-Z](?![a-zA-Z])', text)
    # Subscript patterns
    tokens += re.findall(r'[a-zA-Z]_\{[^}]*\}', text)
    tokens += re.findall(r'[a-zA-Z]_\w', text)
    # Numbers
    tokens += re.findall(r'\d+', text)
    return tokens


def discover_clusters(texts: list, sample_size: int = SAMPLE_SIZE):
    """Run UMAP + HDBSCAN on TF-IDF embeddings of a sample."""
    print(f"\n  [EMBEDDING] Building TF-IDF vectors for {len(texts):,} equations...")

    # Use a sample for density clustering (UMAP+HDBSCAN is O(n²) in worst case)
    if len(texts) > sample_size:
        rng = np.random.default_rng(seed=42)
        indices = rng.choice(len(texts), size=sample_size, replace=False)
        sample_texts = [texts[i] for i in indices]
    else:
        indices = np.arange(len(texts))
        sample_texts = texts

    vectorizer = TfidfVectorizer(
        tokenizer=math_tokenizer,
        token_pattern=None,
        lowercase=False,
        min_df=2,
        max_df=0.9,
        ngram_range=(1, 2),
    )
    tfidf = vectorizer.fit_transform(sample_texts)
    print(f"    TF-IDF shape: {tfidf.shape}")

    print("  [UMAP] Reducing to 2D...")
    reducer = umap.UMAP(
        n_neighbors=15,
        min_dist=0.1,
        n_components=2,
        random_state=42,
        metric='cosine',
        verbose=False,
    )
    embedding = reducer.fit_transform(tfidf)
    print(f"    Embedding shape: {embedding.shape}")

    print("  [HDBSCAN] Density clustering...")
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=50,
        min_samples=5,
        metric='euclidean',
        cluster_selection_method='eom',
    )
    labels = clusterer.fit_predict(embedding)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = list(labels).count(-1)
    print(f"    Clusters found: {n_clusters}")
    print(f"    Noise points:   {n_noise} ({n_noise/len(labels)*100:.1f}%)")

    return labels, embedding, indices, vectorizer, reducer


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("═" * 60)
    print("  MATH SELF-DISCOVERY")
    print("  Unsupervised structural taxonomy from naked equations")
    print("═" * 60)

    print(f"\nLoading math-raw dataset...")
    df = pq.read_table(INPUT).to_pandas()
    n_total = len(df)
    print(f"  Loaded {n_total:,} naked equations")

    # ── Channel 1: Structural Fingerprinting ─────────────────────────────────
    print("\n" + "─" * 50)
    print("  CHANNEL 1: Structural Fingerprinting")
    print("  " + "─" * 50)

    print("  Computing structural fingerprints for all equations...")
    df['fingerprint'] = df['equation'].apply(structural_fingerprint)

    print("  Counting unique structural motifs...")
    fp_counts = Counter(df['fingerprint'])
    n_unique = len(fp_counts)
    print(f"  Unique structural forms: {n_unique:,}")

    # Find the top structural motifs
    top_fps = fp_counts.most_common(N_TOP_FINGERPRINTS)
    print(f"\n  Top {N_TOP_FINGERPRINTS} Structural Motifs:")
    print(f"  {'Rank':>5} {'Count':>10} {'%':>6}  Motif")
    print(f"  {'-'*70}")
    structural_motifs = []
    for rank, (fp, cnt) in enumerate(top_fps, 1):
        pct = cnt / n_total * 100
        fp_display = fp[:80] + "..." if len(fp) > 80 else fp
        print(f"  {rank:>5} {cnt:>10,} {pct:>6.2f}%  {fp_display}")
        structural_motifs.append({
            "rank": rank,
            "fingerprint": fp,
            "count": cnt,
            "percentage": round(pct, 4),
        })

    # Collect samples for top motifs
    print(f"\n  Collecting samples for top motifs...")
    motif_samples = {}
    for fp, cnt in top_fps[:20]:
        samples = df[df['fingerprint'] == fp]['equation'].head(5).tolist()
        motif_samples[fp] = samples

    # ── Channel 2: Embedding + Density Clustering ────────────────────────────
    print("\n" + "─" * 50)
    print("  CHANNEL 2: Embedding + Density Clustering")
    print("  " + "─" * 50)

    # Use raw equation text (not fingerprint) for embedding
    texts = df['equation'].fillna("").astype(str).tolist()
    labels, embedding, sample_indices, vectorizer, reducer = discover_clusters(texts)

    # Build cluster reports
    cluster_sizes = Counter(labels)
    n_clusters = len(cluster_sizes) - (1 if -1 in cluster_sizes else 0)

    print(f"\n  Top {N_CLUSTERS_TO_SAMPLE} Embedding Clusters:")
    print(f"  {'Cluster':>8} {'Size':>10} {'%':>6}  Sample")
    print(f"  {'-'*70}")

    embedding_clusters = []
    for cluster_id, size in cluster_sizes.most_common(N_CLUSTERS_TO_SAMPLE):
        if cluster_id == -1:
            continue  # Skip noise
        pct = size / len(labels) * 100

        # Get top TF-IDF terms for this cluster
        cluster_mask = labels == cluster_id
        cluster_texts = [texts[sample_indices[i]] for i in range(len(labels)) if labels[i] == cluster_id]
        cluster_tfidf = vectorizer.transform(cluster_texts)
        mean_scores = np.asarray(cluster_tfidf.mean(axis=0)).flatten()
        top_idx = np.argsort(mean_scores)[-10:][::-1]
        feature_names = vectorizer.get_feature_names_out()
        top_terms = [feature_names[i] for i in top_idx if mean_scores[i] > 0]

        # Sample equations
        samples = [texts[sample_indices[i]] for i in np.where(cluster_mask)[0][:3]]

        print(f"  {cluster_id:>8} {size:>10,} {pct:>6.2f}%  terms={top_terms[:5]}")
        for s in samples:
            s_short = s[:70] + "..." if len(s) > 70 else s
            print(f"                    {s_short}")

        embedding_clusters.append({
            "cluster_id": int(cluster_id),
            "size": int(size),
            "percentage": round(pct, 4),
            "top_terms": top_terms,
            "samples": samples,
        })

    # ── Assign all equations to nearest embedding cluster ───────────────────
    print(f"\n  Assigning all {n_total:,} equations to clusters...")

    # For full assignment: transform all equations, project with UMAP, find nearest cluster sample
    print("  Transforming full dataset through TF-IDF + UMAP...")
    all_tfidf = vectorizer.transform(texts)
    all_embedding = reducer.transform(all_tfidf)

    # Assign each point to nearest cluster centroid (or keep as noise)
    cluster_centroids = {}
    for cid in set(labels):
        if cid == -1:
            continue
        mask = labels == cid
        cluster_centroids[cid] = embedding[mask].mean(axis=0)

    # For each full-data point, find nearest centroid
    full_labels = []
    for i, point in enumerate(all_embedding):
        # Find nearest centroid
        best_cid = -1
        best_dist = float('inf')
        for cid, centroid in cluster_centroids.items():
            dist = np.linalg.norm(point - centroid)
            if dist < best_dist:
                best_dist = dist
                best_cid = cid

        # If too far from any centroid, mark as noise (-1)
        # Use a threshold based on cluster standard deviations
        full_labels.append(best_cid)

    df['embedding_cluster'] = full_labels
    df['umap_x'] = all_embedding[:, 0]
    df['umap_y'] = all_embedding[:, 1]

    full_cluster_sizes = Counter(full_labels)
    print(f"  Full assignment complete.")
    print(f"  Largest clusters:")
    for cid, size in full_cluster_sizes.most_common(10):
        pct = size / n_total * 100
        print(f"    Cluster {cid:>3}: {size:>9,} ({pct:5.2f}%)")

    # ── Write clustered parquet ──────────────────────────────────────────────
    print(f"\nWriting self-clustered parquet to {CLUSTERED}...")
    cols_to_write = ['uuid', 'equation', 'refined_equation', 'fingerprint',
                     'embedding_cluster', 'umap_x', 'umap_y']
    out_df = df[cols_to_write].copy()
    table = pa.Table.from_pandas(out_df)
    pq.write_table(table, CLUSTERED, compression="zstd")
    print(f"  Done.")

    # ── Write discovery report ───────────────────────────────────────────────
    print(f"\nWriting discovery report to {OUTPUT}...")
    report = {
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "total_equations": n_total,
        "unique_structural_forms": n_unique,
        "embedding_clusters_found": n_clusters,
        "embedding_sample_size": SAMPLE_SIZE,
        "structural_motifs": structural_motifs,
        "motif_samples": {k: v for k, v in list(motif_samples.items())[:20]},
        "embedding_clusters": embedding_clusters,
        "full_cluster_distribution": dict(full_cluster_sizes.most_common()),
    }
    with open(OUTPUT, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    print(f"  Done.")

    # ── Write summary ────────────────────────────────────────────────────────
    summary = {
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "input": INPUT,
        "output_parquet": CLUSTERED,
        "output_report": OUTPUT,
        "total_equations": n_total,
        "unique_structural_forms": n_unique,
        "embedding_clusters": n_clusters,
        "columns": cols_to_write,
    }
    with open(SUMMARY, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "═" * 60)
    print("  MATH SELF-DISCOVERY COMPLETE")
    print(f"  {n_total:,} equations → {n_unique:,} structural forms → {n_clusters} embedding clusters")
    print("═" * 60)


if __name__ == "__main__":
    main()
