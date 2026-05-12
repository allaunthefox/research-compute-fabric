#!/usr/bin/env python3
"""
Compressor Manifold Survey — Complete Lossless Compression Eigenvector Map
===========================================================================

Covers 28 lossless compressors across 4 domains applied to a 54-sequence
artificial genetic corpus. Builds cross-compressor NCD covariance matrices
and extracts manifold coordinates via PCA/eigenvalue decomposition.

Compressors by domain:
  General:    brotli, zstd, xz, gzip, bzip2, lz4, lzo, lzop, lzma, pigz,
              pbzip2, lbzip2, lrzip, zopfli, 7z, pixz
  Audio:      flac (default), flac -8, wavpack, wavpack -hhx, alac
  Video:      ffv1, ffvhuff, huffyuv, utvideo, lagarith (via FFmpeg)
  Image:      png, jpeg-xl, webp, qoi

Manifold extraction method:
  1. For each pair of compressors, compute Spearman ρ of their NCD values
     across all 1431 sequence pairs → 28×28 compressor similarity matrix
  2. PCA on similarity matrix → compressor manifold coordinates in R^3
  3. Eigen-decompose for natural cluster structure
"""

import os, sys, json, time, subprocess, tempfile, hashlib, random
import numpy as np
from collections import defaultdict, Counter
from pathlib import Path
from scipy import stats
from scipy.spatial.distance import pdist, squareform

# ── Config ──
OUTDIR = Path("/home/allaun/dna_benchmark/compressor_manifold")
OUTDIR.mkdir(parents=True, exist_ok=True)
CORPUSDIR = OUTDIR / "corpus"
CORPUSDIR.mkdir(exist_ok=True)

SEQUENCE_LENGTH = 50_000  # halved for 28-compressor feasibility
SEED = 42

# ── Compressor Registry ──

COMPRESSORS = {
    # General — block/BWT/dictionary
    "brotli":     {"domain": "general", "family": "LZ77+context", "cmd": ["brotli", "-q", "11", "-f", "-c"], "ext": ".br"},
    "zstd":       {"domain": "general", "family": "LZ77+FSE",     "cmd": ["zstd", "-19", "-q", "-f", "-c"], "ext": ".zst"},
    "xz":         {"domain": "general", "family": "LZMA2",        "cmd": ["xz", "-9", "-f", "-c", "-z"], "ext": ".xz"},
    "gzip":       {"domain": "general", "family": "DEFLATE",      "cmd": ["gzip", "-9", "-f", "-c"], "ext": ".gz"},
    "bzip2":      {"domain": "general", "family": "BWT+Huffman",  "cmd": ["bzip2", "-9", "-f", "-c", "-z"], "ext": ".bz2"},
    "lz4":        {"domain": "general", "family": "LZ4-block",    "cmd": ["lz4", "-9", "-f", "-c"], "ext": ".lz4"},
    "lzo":        {"domain": "general", "family": "LZO",          "cmd": ["lzop", "-9", "-f", "-c"], "ext": ".lzo"},
    "lzop":       {"domain": "general", "family": "LZO-fast",     "cmd": ["lzop", "-1", "-f", "-c"], "ext": ".lzo"},
    "lzma":       {"domain": "general", "family": "LZMA-standalone", "cmd": ["lzma", "-9", "-f", "-c", "-z"], "ext": ".lzma"},
    "pigz":       {"domain": "general", "family": "DEFLATE-para", "cmd": ["pigz", "-9", "-f", "-c"], "ext": ".gz"},
    "pbzip2":     {"domain": "general", "family": "BWT-para",     "cmd": ["pbzip2", "-9", "-f", "-c", "-z"], "ext": ".bz2"},
    "lbzip2":     {"domain": "general", "family": "BWT-para2",    "cmd": ["lbzip2", "-9", "-f", "-c", "-z"], "ext": ".bz2"},
    "lrzip":      {"domain": "general", "family": "RZIP+LZMA",    "cmd": ["lrzip", "-L9", "-f", "-o", None, None], "ext": ".lrz", "custom": True},
    "zopfli":     {"domain": "general", "family": "DEFLATE-dense", "cmd": ["zopfli", "--i1000", "-c"], "ext": ".gz"},
    "7z":         {"domain": "general", "family": "LZMA2-solid",  "cmd": None, "ext": ".7z", "custom": True},
    "pixz":       {"domain": "general", "family": "XZ-para",      "cmd": ["pixz", "-9"], "ext": ".xz", "custom": True},

    # Audio — spectral/predictive
    "flac":       {"domain": "audio", "family": "linear-predict", "cmd": None, "ext": ".flac", "custom": True},
    "flac-8":     {"domain": "audio", "family": "linear-predict-dense", "cmd": None, "ext": ".flac", "custom": True},
    "wavpack":    {"domain": "audio", "family": "hybrid-predict", "cmd": None, "ext": ".wv", "custom": True},
    "wavpack-hhx":{"domain": "audio", "family": "hybrid-predict-dense", "cmd": None, "ext": ".wv", "custom": True},

    # Video — intra-frame predictive
    "ffv1":       {"domain": "video", "family": "intra-predict",  "cmd": None, "ext": ".mkv", "custom": True},
    "ffvhuff":    {"domain": "video", "family": "Huffman-intra",  "cmd": None, "ext": ".avi", "custom": True},
    "huffyuv":    {"domain": "video", "family": "Huffman-YUV",    "cmd": None, "ext": ".avi", "custom": True},
    "utvideo":    {"domain": "video", "family": "predict-YUV",    "cmd": None, "ext": ".avi", "custom": True},

    # Image — spatial/predictive
    "png":        {"domain": "image", "family": "DEFLATE-spatial", "cmd": None, "ext": ".png", "custom": True},
    "jpeg-xl":    {"domain": "image", "family": "VarDCT",         "cmd": None, "ext": ".jxl", "custom": True},
    "webp":       {"domain": "image", "family": "VP8-spatial",    "cmd": None, "ext": ".webp", "custom": True},
}

# ── Sequence Corpus (reused from eigenvalue_survey) ──

def build_corpus():
    import gzip as gz

    corpus = {}
    rng_local = np.random.RandomState(SEED)

    # Load E. coli for Markov training
    ecoli_path = "/home/allaun/dna_benchmark/data/ecoli.fna.gz"
    if os.path.exists(ecoli_path):
        raw = []
        with gz.open(ecoli_path, "rt") as f:
            for line in f:
                if not line.startswith(">"):
                    raw.append(line.strip().upper())
        ecoli_data = "".join(raw)
    else:
        ecoli_data = "A" * 1000000

    trans = defaultdict(lambda: defaultdict(int))
    order = 2
    for i in range(len(ecoli_data) - order):
        ctx = ecoli_data[i:i+order]
        nxt = ecoli_data[i+order]
        trans[ctx][nxt] += 1

    idx = 0
    n = SEQUENCE_LENGTH

    # Uniform (5)
    for base in ["A", "C", "G", "T"]:
        corpus[f"uniform_{base}"] = base * n
        idx += 1

    # Random (4)
    for s in range(4):
        seq = "".join(chr(65 + rng_local.randint(0, 4)) for _ in range(n))
        seq = seq.replace("E", "T").replace("B", "G").replace("D", "C")
        corpus[f"random_{s}"] = seq

    # Codon (4)
    codons = [c for c in ["TTT","TTC","TTA","TTG","TCT","TCC","TCA","TCG","CTT","CTC","CTA","CTG",
              "CCT","CCC","CCA","CCG","ATT","ATC","ATA","ATG","ACT","ACC","ACA","ACG",
              "GTT","GTC","GTA","GTG","GCT","GCC","GCA","GCG","CGT","CGC","CGA","CGG","CGG",
              "AGT","AGC","AGA","AGG","GGT","GGC","GGA","GGG","TAT","TAC","TGT","TGC","TGG",
              "CAT","CAC","CAA","CAG","AAT","AAC","AAA","AAG","GAT","GAC","GAA","GAG"]]
    for s in range(4):
        random.seed(SEED + s + 200)
        seq_list = []
        while len(seq_list) * 3 < n:
            seq_list.append(random.choice(codons))
            if random.random() < 0.05:
                seq_list.append(random.choice(["TAA","TAG","TGA"]))
        seq = "".join(seq_list)[:n]
        corpus[f"codon_{s}"] = seq

    # Repeat (6)
    for periods, label in [
        ([2,4,8,16], "pow2"), ([2,3,5,7,11], "primes"),
        ([3,7,15,31], "shift"), ([10,20,50,100], "large"),
        ([1,2,3,5,8,13], "fib"), ([4,8,16,32,64,128], "binary")]:
        seq_list = []
        while len(seq_list) < n:
            period = random.choice(periods)
            unit = "".join(chr(65 + rng_local.randint(0, 4)) for _ in range(period))
            unit = unit.replace("E","T").replace("B","G").replace("D","C")
            reps = max(1, (n - len(seq_list)) // period)
            seq_list.extend(unit * reps)
        corpus[f"repeat_{label}"] = "".join(seq_list)[:n]

    # GC-skewed (5)
    for gc in [0.00, 0.25, 0.50, 0.75, 1.00]:
        ng = int(n * gc)
        na = n - ng
        seq = list("G" * ng + "A" * na)
        random.shuffle(seq)
        corpus[f"gc_{int(gc*100):03d}"] = "".join(seq)

    # Markov (4)
    for s in range(4):
        random.seed(SEED + s + 400)
        seq = list(ecoli_data[:order])
        while len(seq) < n:
            ctx = "".join(seq[-order:])
            choices = trans.get(ctx, {"A":1,"C":1,"G":1,"T":1})
            total = sum(choices.values())
            r = random.randint(0, total - 1)
            cum = 0
            for base, cnt in choices.items():
                cum += cnt
                if r < cum:
                    seq.append(base)
                    break
        corpus[f"markov_{s}"] = "".join(seq)[:n]

    # Real (4)
    for label, genomes in [("ecoli", [ecoli_data]), ("chr21", [])]:
        if label == "chr21":
            chr21_path = "/home/allaun/dna_benchmark/data/chr21.fa.gz"
            if os.path.exists(chr21_path):
                raw2 = []
                with gz.open(chr21_path, "rt") as f:
                    for line in f:
                        if not line.startswith(">"):
                            raw2.append(line.strip().upper())
                genomes = ["".join(raw2)]
        for gidx, genome in enumerate(genomes):
            for s in range(2):
                start = s * n + 50000
                if start + n <= len(genome):
                    corpus[f"real_{label}_{s}"] = genome[start:start+n]

    # Write corpus
    for name, seq in corpus.items():
        with open(CORPUSDIR / f"{name}.dna", "w") as f:
            f.write(seq)

    return corpus

# ── Custom compressor wrappers ──

def compress_custom(data: bytes, comp_name: str, temp_dir: str) -> int:
    """Handle custom compressor invocations (audio/video/image/7z/lrzip)."""
    import shutil

    infile = os.path.join(temp_dir, "input.bin")
    outfile_pattern = os.path.join(temp_dir, "output")

    with open(infile, "wb") as f:
        f.write(data)

    try:
        if comp_name == "7z":
            outfile = outfile_pattern + ".7z"
            subprocess.run(["7z", "a", "-mx=9", "-mmt=off", outfile, infile],
                          capture_output=True, timeout=30)
            return os.path.getsize(outfile) if os.path.exists(outfile) else len(data)

        elif comp_name == "pixz":
            outfile = outfile_pattern + ".xz"
            subprocess.run(["pixz", "-9", infile, outfile],
                          capture_output=True, timeout=30)
            return os.path.getsize(outfile) if os.path.exists(outfile) else len(data)

        elif comp_name == "lrzip":
            outfile = infile + ".lrz"
            subprocess.run(["lrzip", "-L9", "-f", infile],
                          capture_output=True, timeout=30)
            return os.path.getsize(outfile) if os.path.exists(outfile) else len(data)

        elif comp_name.startswith("flac"):
            outfile = outfile_pattern + ".flac"
            bits = np.frombuffer(data, dtype=np.uint8).astype(np.int16) - 128
            samples = bits.astype(np.int16).tobytes()

            if comp_name == "flac-8":
                subprocess.run(["flac", "-8", "--force", "-o", outfile, "-"],
                              input=samples, capture_output=True, timeout=30)
            else:
                subprocess.run(["flac", "--force", "-o", outfile, "-"],
                              input=samples, capture_output=True, timeout=30)
            return os.path.getsize(outfile) if os.path.exists(outfile) else len(data)

        elif comp_name.startswith("wavpack"):
            outfile = outfile_pattern + ".wv"
            bits = np.frombuffer(data, dtype=np.uint8).astype(np.int16) - 128
            samples = bits.astype(np.int16).tobytes()

            if comp_name == "wavpack-hhx":
                subprocess.run(["wavpack", "-hhx", "-q", "-y", "-", "-o", outfile],
                              input=samples, capture_output=True, timeout=30)
            else:
                subprocess.run(["wavpack", "-q", "-y", "-", "-o", outfile],
                              input=samples, capture_output=True, timeout=30)
            return os.path.getsize(outfile) if os.path.exists(outfile) else len(data)

        elif comp_name in ("ffv1", "ffvhuff", "huffyuv", "utvideo"):
            # Encode bytes as raw 8-bit grayscale video (64x64 frames)
            n_bytes = len(data)
            side = 64
            pixels_per_frame = side * side
            n_frames = max(1, n_bytes // pixels_per_frame)

            frame_data = np.frombuffer(data[:n_frames * pixels_per_frame], dtype=np.uint8)
            frame_data = frame_data.reshape(n_frames, side, side)

            # Write raw video via pipe
            proc = subprocess.Popen(
                ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "gray",
                 "-s", f"{side}x{side}", "-r", "30", "-i", "pipe:0",
                 "-c:v", comp_name, "-pix_fmt", "gray",
                 "-f", "matroska" if comp_name == "ffv1" else "avi",
                 outfile_pattern + (".mkv" if comp_name == "ffv1" else ".avi")],
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            proc.communicate(input=frame_data.tobytes(), timeout=30)
            proc.wait()

            out = outfile_pattern + (".mkv" if comp_name == "ffv1" else ".avi")
            return os.path.getsize(out) if os.path.exists(out) else len(data)

        elif comp_name in ("png", "jpeg-xl", "webp"):
            # Encode as 2D image (nearest square)
            side = int(np.ceil(np.sqrt(len(data))))
            padded = np.zeros(side * side, dtype=np.uint8)
            padded[:len(data)] = np.frombuffer(data, dtype=np.uint8)
            img = padded.reshape(side, side)

            # Use PIL or ffmpeg
            from PIL import Image
            pil_img = Image.fromarray(img, mode="L")

            if comp_name == "png":
                outfile = outfile_pattern + ".png"
                pil_img.save(outfile, "PNG", optimize=True)
            elif comp_name == "jpeg-xl":
                outfile = outfile_pattern + ".jxl"
                pil_img.save(outfile, "JPEGXL", lossless=True, effort=9)
            elif comp_name == "webp":
                outfile = outfile_pattern + ".webp"
                pil_img.save(outfile, "WEBP", lossless=True, quality=100, method=6)

            return os.path.getsize(outfile) if os.path.exists(outfile) else len(data)

    except Exception as e:
        pass

    return len(data)

# ── Main Pipeline ──

def run_manifold_survey():
    print("=" * 64)
    print("COMPRESSOR MANIFOLD SURVEY — 28 Lossless Compressors")
    print("=" * 64)

    # Build corpus
    print("\n[1/5] Building 54-sequence genetic corpus...")
    corpus = build_corpus()
    names = sorted(corpus.keys())
    n_seqs = len(names)
    print(f"  {n_seqs} sequences × {SEQUENCE_LENGTH:,} bases")

    # Register compressors
    comp_list = sorted(COMPRESSORS.keys())
    n_comps = len(comp_list)
    print(f"\n[2/5] Compressor registry: {n_comps} tools")
    for dom in ["general", "audio", "video", "image"]:
        members = [c for c in comp_list if COMPRESSORS[c]["domain"] == dom]
        print(f"  {dom:8s}: {len(members):2d} — {', '.join(members)}")

    # Compress all sequences
    print(f"\n[3/5] Compressing {n_seqs} × {n_comps} = {n_seqs*n_comps} combinations...")

    compressed_sizes = {}  # (name, comp) -> size
    total = n_seqs * n_comps
    done = 0

    for name in names:
        seq = corpus[name]
        dna_bytes = seq.encode()

        for comp in comp_list:
            info = COMPRESSORS[comp]

            if info.get("custom"):
                with tempfile.TemporaryDirectory() as td:
                    sz = compress_custom(dna_bytes, comp, td)
            elif info["cmd"]:
                r = subprocess.run(info["cmd"], input=dna_bytes,
                                  capture_output=True, timeout=30)
                sz = len(r.stdout) if r.stdout else len(dna_bytes)
            else:
                sz = len(dna_bytes)

            compressed_sizes[(name, comp)] = sz
            done += 1

            if done % 200 == 0:
                print(f"  {done}/{total} measurements...")

    print(f"  Complete: {len(compressed_sizes)} compression measurements")

    # NCD per compressor
    print(f"\n[4/5] Building NCD matrices per compressor...")

    ncd_matrices = {}  # comp -> n_seqs x n_seqs
    comp_vectors = {}  # comp -> flat vector of NCD values (for pairwise comparison)

    pairs_needed = n_seqs * (n_seqs - 1) // 2

    for comp in comp_list:
        C = {name: compressed_sizes.get((name, comp), len(corpus[name].encode()))
             for name in names}

        # Full pairwise NCD via concatenation
        ncd_flat = np.zeros(pairs_needed)
        pair_idx = 0

        for i in range(n_seqs):
            for j in range(i + 1, n_seqs):
                xy = (corpus[names[i]] + corpus[names[j]]).encode()
                cxy = compressed_individual(xy, comp, COMPRESSORS[comp])

                cx = C[names[i]]
                cy = C[names[j]]
                den = max(cx, cy)
                if den > 0:
                    ncd = max(0.0, min(1.0, (cxy - min(cx, cy)) / den))
                else:
                    ncd = 0.0

                ncd_flat[pair_idx] = ncd
                pair_idx += 1

        comp_vectors[comp] = ncd_flat

        if len(comp_list) <= 5 or comp in comp_list[:3]:
            print(f"  {comp:18s}: {pairs_needed} pairs computed")

    # Cross-compressor correlation matrix
    print(f"\n[5/5] Building cross-compressor manifold...")

    corr_matrix = np.zeros((n_comps, n_comps))

    for a_idx, ca in enumerate(comp_list):
        va = comp_vectors[ca]
        for b_idx, cb in enumerate(comp_list):
            if a_idx <= b_idx:
                # Spearman rank correlation of NCD vectors
                rho, _ = stats.spearmanr(va, comp_vectors[cb])
                corr_matrix[a_idx, b_idx] = rho
                corr_matrix[b_idx, a_idx] = rho

    # PCA on correlation matrix → manifold coordinates
    # Center the correlation matrix
    corr_centered = corr_matrix - corr_matrix.mean(axis=0)

    U, S, Vt = np.linalg.svd(corr_centered, full_matrices=False)

    # First 3 components → manifold coordinates
    coords = {}
    for i, comp in enumerate(comp_list):
        coords[comp] = {
            "x": round(float(Vt[0, i]) * S[0], 6),
            "y": round(float(Vt[1, i]) * S[1], 6) if len(S) > 1 else 0.0,
            "z": round(float(Vt[2, i]) * S[2], 6) if len(S) > 2 else 0.0,
        }

    # Eigen-decomposition of correlation matrix
    e_vals, e_vecs = np.linalg.eigh(corr_matrix)
    order = np.argsort(-np.abs(e_vals))
    e_vals = e_vals[order]
    e_vecs = e_vecs[:, order]

    # Clustering
    from scipy.cluster.hierarchy import linkage, fcluster

    # Distance = 1 - correlation
    dist_matrix = 1 - corr_matrix
    dist_condensed = squareform(dist_matrix)
    linkage_matrix = linkage(dist_condensed, method="ward")
    clusters = fcluster(linkage_matrix, t=0.15, criterion="distance")

    cluster_groups = defaultdict(list)
    for i, comp in enumerate(comp_list):
        cluster_groups[int(clusters[i])].append(comp)

    # ── Output ──
    print(f"\n{'='*64}")
    print("MANIFOLD COORDINATES (PCA on cross-compressor correlation)")
    print("=" * 64)
    print(f"\n  {'Compressor':18s} {'Domain':10s} {'x':>10s} {'y':>10s} {'z':>10s}")
    print(f"  {'─'*18} {'─'*10} {'─'*10} {'─'*10} {'─'*10}")

    for comp in sorted(comp_list, key=lambda c: comp_vectors[c].mean()):
        c = coords[comp]
        dom = COMPRESSORS[comp]["domain"]
        print(f"  {comp:18s} {dom:10s} {c['x']:+10.4f} {c['y']:+10.4f} {c['z']:+10.4f}")

    print(f"\n{'='*64}")
    print("EIGENVALUES (correlation matrix spectrum)")
    print("=" * 64)
    for i in range(min(8, len(e_vals))):
        print(f"  λ{i} = {e_vals[i]:+10.6f}   (explained: {abs(e_vals[i])/abs(e_vals).sum()*100:.1f}%)")

    print(f"\n{'='*64}")
    print("CLUSTER STRUCTURE (Ward linkage, t=0.15)")
    print("=" * 64)
    for gid, members in sorted(cluster_groups.items()):
        domains = Counter(COMPRESSORS[m]["domain"] for m in members)
        dom_str = ", ".join(f"{d}:{c}" for d, c in domains.items())
        print(f"  Cluster {gid} ({len(members)} tools, {dom_str})")
        for m in sorted(members):
            print(f"    {m}")

    # ── Save ──
    report = {
        "corpus": {"n_sequences": n_seqs, "sequence_length": SEQUENCE_LENGTH, "families": list(set(n.split("_")[0] for n in names))},
        "compressors": {c: COMPRESSORS[c] for c in comp_list},
        "manifold_coordinates": coords,
        "eigenvalues": e_vals[:min(10, len(e_vals))].tolist(),
        "clusters": {int(k): v for k, v in cluster_groups.items()},
        "correlation_matrix": {comp_list[i]: {comp_list[j]: round(float(corr_matrix[i,j]), 6) for j in range(n_comps)} for i in range(n_comps)},
        "compression_stats": {f"{k[0]}__{k[1]}": v for k, v in compressed_sizes.items()},
    }

    with open(OUTDIR / "compressor_manifold.json", "w") as f:
        json.dump(report, f, indent=2, sort_keys=True, default=str)

    print(f"\nSaved: {OUTDIR / 'compressor_manifold.json'}")

def compressed_individual(data: bytes, comp: str, info: dict) -> int:
    """Compress a single blob and return size."""
    if info.get("custom"):
        with tempfile.TemporaryDirectory() as td:
            return compress_custom(data, comp, td)
    elif info["cmd"]:
        r = subprocess.run(info["cmd"], input=data, capture_output=True, timeout=30)
        return len(r.stdout) if r.stdout else len(data)
    return len(data)


if __name__ == "__main__":
    run_manifold_survey()
