#!/usr/bin/env python3
"""
Compressor Eigenvalue Survey — Artificial Genetic Sequences
=============================================================

Generates 50 artificial genetic sequences across 6 structural families,
compresses each with 6 tools (brotli, zstd, xz, gzip, bzip2, lz4), builds
Normalized Compression Distance matrices, and eigen-decomposes to reveal
which compressors are structurally equivalent and which sequence families
separate cleanest.

Families:
  1. uniform     — single base repeated
  2. random      — uniform random ACGT
  3. codon       — valid codon triplets with stop/start structure
  4. repeat      — tandem repeats with variable period
  5. gc_skewed   — GC-biased (0%, 25%, 50%, 75%, 100% GC)
  6. real        — real E. coli + human chr21 slices
"""

import os, sys, time, json, subprocess, tempfile, hashlib, random, shutil, glob
import numpy as np
from collections import defaultdict
from pathlib import Path

# ── Config ──
OUTDIR = Path("/home/allaun/dna_benchmark/eigenvalue_survey")
OUTDIR.mkdir(parents=True, exist_ok=True)
CORPUSDIR = OUTDIR / "corpus"
CORPUSDIR.mkdir(exist_ok=True)

COMPRESSORS = ["brotli", "zstd", "xz", "gzip", "bzip2", "lz4"]
SEQUENCE_LENGTH = 100_000  # bases per sequence
SEED = 42

random.seed(SEED)
rng = np.random.RandomState(SEED)

# ── Sequence Generators ──

def make_uniform(base: str, n: int) -> str:
    return base * n

def make_random(n: int, alphabet: str = "ACGT") -> str:
    return "".join(random.choice(alphabet) for _ in range(n))

def make_codon_structured(n: int) -> str:
    """Valid codon triplets with start (ATG) and stop (TAA/TAG/TGA) sprinkled."""
    codons = [
        "TTT","TTC","TTA","TTG","TCT","TCC","TCA","TCG",
        "TAT","TAC","TGT","TGC","TGG","CTT","CTC","CTA","CTG",
        "CCT","CCC","CCA","CCG","CAT","CAC","CAA","CAG",
        "CGT","CGC","CGA","CGG","ATT","ATC","ATA","ATG",
        "ACT","ACC","ACA","ACG","AAT","AAC","AAA","AAG",
        "AGT","AGC","AGA","AGG","GTT","GTC","GTA","GTG",
        "GCT","GCC","GCA","GCG","GAT","GAC","GAA","GAG",
        "GGT","GGC","GGA","GGG",
    ]
    stops = ["TAA","TAG","TGA"]

    seq = []
    while len(seq) < n // 3:
        seq.append(random.choice(codons))
        if random.random() < 0.05:  # 5% chance of stop
            seq.append(random.choice(stops))
            if random.random() < 0.5:
                seq.append("ATG")  # restart

    result = "".join(seq)[:n]
    if len(result) < n:
        result += "A" * (n - len(result))
    return result

def make_tandem_repeat(n: int, periods: list = None) -> str:
    """Varying tandem repeats."""
    if periods is None:
        periods = [2, 3, 4, 5, 7, 11, 17, 23, 47, 101]

    seq = []
    while len(seq) < n:
        period = random.choice(periods)
        unit = make_random(period)
        reps = max(1, min(100, (n - len(seq)) // period))
        seq.extend(unit * reps)

    return "".join(seq)[:n]

def make_gc_skewed(n: int, gc_fraction: float) -> str:
    """Generate sequence with exact GC fraction."""
    at_bases = ["A", "T"]
    gc_bases = ["G", "C"]
    n_gc = int(n * gc_fraction)
    n_at = n - n_gc

    seq = [random.choice(gc_bases) for _ in range(n_gc)] + \
          [random.choice(at_bases) for _ in range(n_at)]
    random.shuffle(seq)
    return "".join(seq)

def make_markov_structured(n: int, order: int = 2) -> str:
    """Generate sequence from Markov chain with pronounced transition bias."""
    # Learn from E. coli if available, else use fixed transition matrix
    ecoli_path = "/home/allaun/dna_benchmark/data/ecoli.fna.gz"
    if os.path.exists(ecoli_path):
        import gzip
        raw = []
        with gzip.open(ecoli_path, "rt") as f:
            for line in f:
                if not line.startswith(">"):
                    raw.append(line.strip().upper())
        ecoli = "".join(raw)[:500000]
        # Build transition counts
        trans = defaultdict(lambda: defaultdict(int))
        for i in range(len(ecoli) - order):
            ctx = ecoli[i:i+order]
            nxt = ecoli[i+order]
            trans[ctx][nxt] += 1

        # Generate from learned transitions
        seq = list(ecoli[:order])  # seed with real context
        while len(seq) < n:
            ctx = "".join(seq[-order:])
            choices = trans.get(ctx, {"A":1,"C":1,"G":1,"T":1})
            total = sum(choices.values())
            r = random.randint(0, total - 1)
            cum = 0
            for base, count in choices.items():
                cum += count
                if r < cum:
                    seq.append(base)
                    break
    else:
        # Fallback: simple GC-bias Markov chain
        seq = list(make_random(order))
        while len(seq) < n:
            ctx = "".join(seq[-order:])
            gc_count = sum(1 for c in ctx if c in "GC")
            p_gc = max(0.1, min(0.9, gc_count / order + random.uniform(-0.1, 0.1)))
            if random.random() < p_gc:
                seq.append(random.choice("GC"))
            else:
                seq.append(random.choice("AT"))

    return "".join(seq)[:n]

# ── Build Corpus ──

# Move helper before corpus section
def _shannon_entropy(seq: str) -> float:
    from collections import Counter
    c = Counter(seq)
    n = len(seq)
    return -sum((v/n) * np.log2(v/n) for v in c.values() if v > 0)

print("=" * 60)
print("GENERATING ARTIFICIAL GENETIC SEQUENCE CORPUS")
print("=" * 60)

corpus = {}

# Family 1: Uniform (8 sequences)
print("\n[Family: uniform]")
for base in ["A", "C", "G", "T"]:
    for mult in [1, 2, 3, 5, 10]:
        unit = base * mult
        seq = make_uniform(base, SEQUENCE_LENGTH)
        name = f"uniform_{unit[:20]}_x{len(seq)//len(unit)}"
        corpus[name] = seq
        print(f"  {name:40s} {len(seq):,} bases")

# Family 2: Random (5 sequences)
print("\n[Family: random]")
for i, n in enumerate([SEQUENCE_LENGTH]):
    for seed_offset in range(5):
        random.seed(SEED + seed_offset + 100)
        seq = make_random(n)
        name = f"random_seed{seed_offset}"
        corpus[name] = seq
        print(f"  {name:40s} {len(seq):,} bases  entropy={_shannon_entropy(seq):.2f}")

# Family 3: Codon-structured (5 sequences)
print("\n[Family: codon]")
for seed_offset in range(5):
    random.seed(SEED + seed_offset + 200)
    seq = make_codon_structured(SEQUENCE_LENGTH)
    name = f"codon_seed{seed_offset}"
    corpus[name] = seq
    print(f"  {name:40s} {len(seq):,} bases")

# Family 4: Tandem repeats (8 sequences)
print("\n[Family: repeat]")
repeat_configs = [
    ([2, 4, 8, 16], "pow2"),
    ([2, 3, 5, 7, 11], "primes"),
    ([10, 20, 50, 100], "large"),
    ([3, 7, 15, 31], "shift"),
    ([2, 4, 6, 8, 10], "even"),
    ([1, 2, 3, 5, 8, 13], "fib"),
    ([11, 23, 47], "sparse"),
    ([4, 8, 16, 32, 64, 128], "binary"),
]
for periods, label in repeat_configs:
    random.seed(SEED + 300)
    seq = make_tandem_repeat(SEQUENCE_LENGTH, periods)
    name = f"repeat_{label}"
    corpus[name] = seq
    print(f"  {name:40s} {len(seq):,} bases  periods={periods}")

# Family 5: GC-skewed (5 sequences)
print("\n[Family: gc_skewed]")
for gc in [0.00, 0.25, 0.50, 0.75, 1.00]:
    seq = make_gc_skewed(SEQUENCE_LENGTH, gc)
    name = f"gc_skewed_{int(gc*100):03d}"
    corpus[name] = seq
    print(f"  {name:40s} {len(seq):,} bases  GC={gc:.0%}")

# Family 6: Markov-structured (5 sequences)
print("\n[Family: markov]")
for seed_offset in range(5):
    random.seed(SEED + seed_offset + 400)
    seq = make_markov_structured(SEQUENCE_LENGTH, order=2)
    name = f"markov_seed{seed_offset}"
    corpus[name] = seq
    print(f"  {name:40s} {len(seq):,} bases")

# Family 7: Real slices (6 sequences)
print("\n[Family: real]")
import gzip
real_names = []
for label, path in [("ecoli", "/home/allaun/dna_benchmark/data/ecoli.fna.gz"),
                     ("chr21", "/home/allaun/dna_benchmark/data/chr21.fa.gz")]:
    raw = []
    with gzip.open(path, "rt") as f:
        for line in f:
            if not line.startswith(">"):
                raw.append(line.strip().upper())
    genome = "".join(raw)
    for i in range(3):
        start = i * SEQUENCE_LENGTH + 50000
        seq = genome[start:start + SEQUENCE_LENGTH]
        if len(seq) >= SEQUENCE_LENGTH // 2:
            name = f"real_{label}_slice{i}"
            corpus[name] = seq
            real_names.append(name)
            print(f"  {name:40s} {len(seq):,} bases  pos={start}")

# Write corpus
print(f"\nTotal sequences: {len(corpus)}")
for name, seq in corpus.items():
    fname = name + ".dna"
    with open(CORPUSDIR / fname, "w") as f:
        f.write(seq)

# ── Helper ──
# ── Compression Benchmark ──
print("\n" + "=" * 60)
print("COMPRESSING WITH ALL TOOLS")
print("=" * 60)

compression_results = {}  # (name, compressor) -> dict

for name, seq in sorted(corpus.items()):
    dna_path = CORPUSDIR / (name + ".dna")
    orig_size = len(seq)

    for comp in COMPRESSORS:
        # Measure compressed size
        if comp == "brotli":
            cmd = ["brotli", "-q", "11", "-f", str(dna_path)]
            ext = ".br"
        elif comp == "zstd":
            cmd = ["zstd", "-19", "-q", "-f", str(dna_path)]
            ext = ".zst"
        elif comp == "xz":
            cmd = ["xz", "-9", "-f", "-k", str(dna_path)]
            ext = ".xz"
        elif comp == "gzip":
            cmd = ["gzip", "-9", "-f", "-k", str(dna_path)]
            ext = ".gz"
        elif comp == "bzip2":
            cmd = ["bzip2", "-9", "-f", "-k", str(dna_path)]
            ext = ".bz2"
        elif comp == "lz4":
            cmd = ["lz4", "-9", "-f", str(dna_path)]
            ext = ".lz4"
        else:
            continue

        t0 = time.time()
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        dt = time.time() - t0

        cpath = str(dna_path) + ext
        if os.path.exists(cpath):
            csize = os.path.getsize(cpath)
            os.unlink(cpath)
        else:
            csize = orig_size  # fallback: no compression

        compression_results[(name, comp)] = {
            "original": orig_size,
            "compressed": csize,
            "bpb": round(csize * 8 / orig_size, 3),
            "ratio": round(csize / orig_size, 4),
            "time_s": round(dt, 4),
        }

        if r.returncode != 0 and r.returncode is not None:
            print(f"  WARN: {comp} on {name} returned {r.returncode}")

    # Quick progress
    if len(compression_results) % 50 == 0:
        print(f"  {len(compression_results)} compression measurements...")

print(f"  Complete: {len(compression_results)} total measurements")

# ── NCD Matrix: Normalized Compression Distance ──
print("\n" + "=" * 60)
print("COMPUTING NCD MATRICES PER COMPRESSOR")
print("=" * 60)

names = sorted(corpus.keys())
n = len(names)

# Per-compressor NCD: NCD(x,y) = (C(xy) - min(C(x),C(y))) / max(C(x),C(y))
ncd_matrices = {}  # compressor -> n x n matrix

for comp in COMPRESSORS:
    C = {}  # name -> compressed size

    for name in names:
        key = (name, comp)
        if key in compression_results:
            C[name] = compression_results[key]["compressed"]
        else:
            C[name] = len(corpus[name])  # fallback

    # Compute pairwise NCD using concatenation compression
    # For efficiency, approximate: use sum of individual sizes as xy size
    # Full NCD would concatenate and compress; we use the approximation
    # NCD_appx(x,y) = (C(x)+C(y) - 2*min(C(x),C(y))) / (C(x)+C(y) - min(C(x),C(y)))
    # Actually using simpler: NCD ~ C(xy) via C(x)+C(y) with some overhead

    # We'll compute full pairwise by actually concatenating and compressing
    M = np.zeros((n, n))

    pairwise_needed = n * (n - 1) // 2
    done = 0

    for i in range(n):
        M[i, i] = 0.0
        for j in range(i + 1, n):
            # Concatenate
            xy = corpus[names[i]] + corpus[names[j]]
            xy_bytes = xy.encode()

            if comp == "brotli":
                cmd = ["brotli", "-q", "11", "-f", "-c"]
                r = subprocess.run(cmd, input=xy_bytes, capture_output=True, timeout=30)
                cxy = len(r.stdout) if r.stdout else len(xy_bytes)
            elif comp == "zstd":
                cmd = ["zstd", "-19", "-q", "-f", "-c"]
                r = subprocess.run(cmd, input=xy_bytes, capture_output=True, timeout=30)
                cxy = len(r.stdout) if r.stdout else len(xy_bytes)
            elif comp == "xz":
                cmd = ["xz", "-9", "-f", "-c", "-z"]
                r = subprocess.run(cmd, input=xy_bytes, capture_output=True, timeout=30)
                cxy = len(r.stdout) if r.stdout else len(xy_bytes)
            elif comp == "gzip":
                cmd = ["gzip", "-9", "-f", "-c"]
                r = subprocess.run(cmd, input=xy_bytes, capture_output=True, timeout=30)
                cxy = len(r.stdout) if r.stdout else len(xy_bytes)
            elif comp == "bzip2":
                cmd = ["bzip2", "-9", "-f", "-c", "-z"]
                r = subprocess.run(cmd, input=xy_bytes, capture_output=True, timeout=30)
                cxy = len(r.stdout) if r.stdout else len(xy_bytes)
            elif comp == "lz4":
                cmd = ["lz4", "-9", "-f", "-c"]
                r = subprocess.run(cmd, input=xy_bytes, capture_output=True, timeout=30)
                cxy = len(r.stdout) if r.stdout else len(xy_bytes)
            else:
                cxy = len(xy_bytes)

            # NCD formula
            cx = C[names[i]]
            cy = C[names[j]]
            num = cxy - min(cx, cy)
            den = max(cx, cy)

            if den > 0:
                ncd_val = max(0.0, min(1.0, num / den))
            else:
                ncd_val = 0.0

            M[i, j] = ncd_val
            M[j, i] = ncd_val

            done += 1
            if done % 100 == 0:
                print(f"  {comp}: {done}/{pairwise_needed} pairs...")

    ncd_matrices[comp] = M
    print(f"  {comp}: complete  ({pairwise_needed} pairs)")

# ── Eigen-decomposition ──
print("\n" + "=" * 60)
print("EIGEN-DECOMPOSING NCD MATRICES")
print("=" * 60)

eigen_results = {}

for comp in COMPRESSORS:
    M = ncd_matrices[comp]
    e_vals, e_vecs = np.linalg.eigh(M)

    # Sort by ascending eigenvalue (largest negative = most structure)
    order = np.argsort(e_vals)
    e_vals = e_vals[order]
    e_vecs = e_vecs[:, order]

    # Leading eigenvalues
    top_k = 8
    eigen_results[comp] = {
        "eigenvalues": e_vals[:top_k].tolist(),
        "all_eigenvalues": e_vals.tolist(),
        "eigenvectors_top": {},
        "spectral_norm": float(np.linalg.norm(e_vals, 2)),
        "trace": float(np.trace(M)),
        "frobenius": float(np.linalg.norm(M, "fro")),
        "rank_estimate": int((np.abs(e_vals) > 1e-6).sum()),
    }

    # Top eigenvector weights per sequence
    for k in range(min(top_k, len(e_vals))):
        vec = e_vecs[:, k]
        top_indices = np.argsort(-np.abs(vec))[:5]

        eigen_results[comp][f"eigenvectors_top"][f"mode_{k}"] = {
            "eigenvalue": round(e_vals[k], 6),
            "top_sequences": [
                {
                    "name": names[i],
                    "weight": round(float(vec[i]), 6),
                    "family": names[i].split("_")[0],
                }
                for i in top_indices
            ],
        }

    print(f"  {comp:8s}: λ₀={e_vals[0]:.4f} λ₁={e_vals[1]:.4f} λ₂={e_vals[2]:.4f}  "
          f"|λ|₂={eigen_results[comp]['spectral_norm']:.2f}  trace={eigen_results[comp]['trace']:.1f}")

# ── Compressor-to-Compressor Similarity ──
print("\n" + "=" * 60)
print("COMPRESSOR EIGENVALUE SIMILARITY MATRIX")
print("=" * 60)

comp_sim = np.zeros((len(COMPRESSORS), len(COMPRESSORS)))
for a, ca in enumerate(COMPRESSORS):
    for b, cb in enumerate(COMPRESSORS):
        if a <= b:
            # Cosine similarity of eigenvalue spectra
            ev_a = np.array(eigen_results[ca]["all_eigenvalues"])
            ev_b = np.array(eigen_results[cb]["all_eigenvalues"])
            cos_sim = np.dot(ev_a, ev_b) / (np.linalg.norm(ev_a) * np.linalg.norm(ev_b) + 1e-12)
            comp_sim[a, b] = cos_sim
            comp_sim[b, a] = cos_sim

print(f"  {'':<8s}", end="")
for c in COMPRESSORS:
    print(f"{c:<8s}", end="")
print()
for a, ca in enumerate(COMPRESSORS):
    print(f"  {ca:<8s}", end="")
    for b, cb in enumerate(COMPRESSORS):
        val = comp_sim[a, b]
        bar = "█" * int(val * 8) if val > 0.5 else ""
        marker = "◉" if a == b else ""
        print(f"{val:.4f} {bar}{marker:<3s}", end="  " if b < len(COMPRESSORS) - 1 else "")
    print()

# ── Family Separation Score ──
print("\n" + "=" * 60)
print("FAMILY SEPARATION BY COMPRESSOR")
print("=" * 60)

families = defaultdict(list)
for i, name in enumerate(names):
    family = name.split("_")[0]
    families[family].append(i)

separation_scores = {}
for comp in COMPRESSORS:
    M = ncd_matrices[comp]

    # Intra-family distance
    intra = 0.0
    intra_pairs = 0
    inter = 0.0
    inter_pairs = 0

    family_list = list(families.keys())
    for fi, f1 in enumerate(family_list):
        members1 = families[f1]
        for a in members1:
            for b in members1:
                if a < b:
                    intra += M[a, b]
                    intra_pairs += 1

        for f2 in family_list[fi + 1:]:
            members2 = families[f2]
            for a in members1:
                for b in members2:
                    inter += M[a, b]
                    inter_pairs += 1

    intra_avg = intra / max(intra_pairs, 1)
    inter_avg = inter / max(inter_pairs, 1)
    separation = inter_avg - intra_avg

    separation_scores[comp] = {
        "intra_family_ncd": round(intra_avg, 4),
        "inter_family_ncd": round(inter_avg, 4),
        "separation": round(separation, 4),
        "ratio": round(inter_avg / max(intra_avg, 1e-9), 2),
    }

    print(f"  {comp:8s}: intra={intra_avg:.4f}  inter={inter_avg:.4f}  "
          f"Δ={separation:.4f}  ratio={inter_avg/max(intra_avg,1e-9):.1f}x")

# ── Save Results ──
final_report = {
    "corpus": {
        "total_sequences": len(corpus),
        "sequence_length": SEQUENCE_LENGTH,
        "families": {f: [n for n in names if n.startswith(f)] for f in families},
    },
    "compression_results": {f"{k[0]}__{k[1]}": v for k, v in compression_results.items()},
    "eigen_results": eigen_results,
    "compressor_similarity": {COMPRESSORS[a]: {COMPRESSORS[b]: round(float(comp_sim[a,b]), 6) for b in range(len(COMPRESSORS))} for a in range(len(COMPRESSORS))},
    "family_separation": separation_scores,
    "ncd_matrices_summary": {comp: {
        "shape": list(ncd_matrices[comp].shape),
        "mean": round(float(ncd_matrices[comp].mean()), 6),
        "std": round(float(ncd_matrices[comp].std()), 6),
        "min": round(float(ncd_matrices[comp].min()), 6),
        "max": round(float(ncd_matrices[comp].max()), 6),
    } for comp in COMPRESSORS},
}

with open(OUTDIR / "eigenvalue_survey.json", "w") as f:
    json.dump(final_report, f, indent=2, sort_keys=True, default=str)

print(f"\n{'='*60}")
print(f"COMPLETE — Output: {OUTDIR / 'eigenvalue_survey.json'}")
print(f"Corpus: {len(corpus)} sequences × {len(COMPRESSORS)} compressors")
print(f"Pairwise NCD: ~{n*(n-1)//2} pairs × {len(COMPRESSORS)} compressors")
print(f"{'='*60}")
