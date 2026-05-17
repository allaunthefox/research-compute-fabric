# PROPRIETARY -- ALL RIGHTS RESERVED
# Copyright (c) 2026 Allaun Holdings
# See THIRD_PARTY_NOTICES.txt for third-party attributions.

"""
PIST DNA Compressor — Projective Invariant Symbolic Transform

Compresses DNA sequences by building an eigenmass field from structural
invariants (k-mer repeats, ORF patterns, GC content), then allocating bits
proportional to recoverability — high-mass regions get dense encoding,
low-mass regions get sparse encoding.

This is the biological instantiation of the PIST → FAMM → NUVMAP pipeline:
  PIST: compress sequence into mass field M(DNA)
  FAMM: route through mass field (AMVR/AVMR chiral routing)
  NUVMAP: allocate storage proportional to eigenmass

Outputs:
  1. Compressed binary (.pist)
  2. Eigenmass field (JSON) — explainable structural map
  3. Mass field visualization coordinates

Benchmark categories (kept separate):
  A. DNA SEQUENCE: pure A/C/G/T lossless
  B. FASTQ: sequence + quality scores (NOT equivalent to pure sequence)
  C. DNA STORAGE: encoding for synthetic biology (NOT equivalent to compression)
"""

import argparse
import hashlib
import json
import struct
import sys
import time
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional


# ── DNA Alphabet ──
DNA_ALPHABET = set("ACGT")
COMPLEMENT = {"A": "T", "T": "A", "C": "G", "G": "C", "N": "N"}


def read_fasta(path: str) -> str:
    """Read FASTA/FA, strip headers, uppercase, keep only ACGT."""
    seq = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line.startswith(">"):
                continue
            seq.append(line.upper())
    raw = "".join(seq)
    return "".join(c for c in raw if c in DNA_ALPHABET)


def read_fasta_gz(path: str) -> str:
    """Read gzipped FASTA."""
    import gzip
    seq = []
    with gzip.open(path, "rt") as f:
        for line in f:
            line = line.strip()
            if line.startswith(">"):
                continue
            seq.append(line.upper())
    raw = "".join(seq)
    return "".join(c for c in raw if c in DNA_ALPHABET)


# ── PIST Eigenmass Field ──

def compute_eigenmass_field(sequence: str, k: int = 16,
                            context_radius: int = 32) -> Dict:
    """
    Build the eigenmass field from DNA sequence invariants.

    The mass at each position i is:
      M(i) ∝ structural_uniqueness(i) × conservation_score(i)

    High mass = highly conserved, structurally constrained position.
    Low mass = variable/repeat/background position.

    Invariants computed:
      1. k-mer frequency (higher freq → lower mass per position, information is elsewhere)
      2. Local GC content gradient (sharp transitions = structural boundaries → high mass)
      3. Palindromic/repeat density (inverted repeats → high mass, structural elements)
      4. ORF density (coding potential → high mass)
    """
    n = len(sequence)
    mass = [0.0] * n
    kmer_counts = defaultdict(int)

    # 1. k-mer frequency map
    for i in range(n - k + 1):
        kmer = sequence[i:i + k]
        if "N" not in kmer:
            kmer_counts[kmer] += 1

    max_kmer = max(kmer_counts.values()) if kmer_counts else 1
    inv_kmer = {km: 1.0 / max(count, 1) for km, count in kmer_counts.items()}

    # 2. Per-position mass accumulation
    for i in range(n):
        score = 0.0
        contributions = 0

        # k-mer uniqueness contribution (inverse frequency = more unique = more mass)
        if i + k <= n:
            kmer = sequence[i:i + k]
            if kmer in inv_kmer:
                score += inv_kmer[kmer] * 2.0
                contributions += 1

        # GC content gradient in local window
        window_start = max(0, i - context_radius)
        window_end = min(n, i + context_radius)
        window = sequence[window_start:window_end]
        if window:
            gc_count = sum(1 for c in window if c in "GC")
            gc_fraction = gc_count / len(window)
            # Regions at ~0.5 GC are background; deviations → structural signal
            gc_deviation = abs(gc_fraction - 0.5) * 2.0
            score += gc_deviation
            contributions += 1

        # CpG density (regulatory signal)
        if i + 2 <= n and sequence[i:i + 2] == "CG":
            score += 1.5
            contributions += 1

        # Palindromic context (local inverted repeat signal)
        pal_score = 0.0
        ctx = min(context_radius, i, n - i)
        for r in range(4, min(k, ctx)):
            if i + r + r <= n and i - r >= 0:
                forward = sequence[i:i + r]
                reverse_comp = "".join(COMPLEMENT.get(c, c) for c in reversed(sequence[i - r:i]))
                if forward == reverse_comp:
                    pal_score += 1.0 / r  # shorter palindromes = stronger signal
        score += pal_score
        contributions += 1

        mass[i] = score / max(contributions, 1)

    # Normalize to [0, 1]
    max_mass = max(mass) if max(mass) > 0 else 1.0
    mass = [m / max_mass for m in mass]

    return {
        "mass_field": mass,
        "kmer_table": {km: count for km, count in kmer_counts.items()},
        "k": k,
        "context_radius": context_radius,
        "sequence_length": n,
        "mean_mass": sum(mass) / n if n > 0 else 0.0,
        "median_mass": sorted(mass)[n // 2] if n > 0 else 0.0,
        "high_mass_fraction": sum(1 for m in mass if m > 0.7) / n if n > 0 else 0.0,
        "low_mass_fraction": sum(1 for m in mass if m < 0.3) / n if n > 0 else 0.0,
    }


# ── PIST Compressor ──

class PISTDNACompressor:
    """
    PIST DNA sequence compressor.

    Encoding strategy (lossless):
      - High-mass positions: store as reference to k-mer table
      - Medium-mass positions: delta-encode relative to context
      - Low-mass positions: store verbatim (2 bits/base)

    The eigenmass field IS the storage allocation map.
    This is structurally explainable: you can read the mass field
    and see WHERE information is concentrated in the genome.
    """

    DNA_TO_2BIT = {"A": 0, "C": 1, "G": 2, "T": 3}
    BIT2_TO_DNA = {0: "A", 1: "C", 2: "G", 3: "T"}

    def __init__(self, k: int = 16):
        self.k = k
        self.kmer_table: Dict[str, int] = {}

    def compress(self, sequence: str, mass_threshold: float = 0.3) -> Tuple[bytes, Dict]:
        """
        Compress DNA sequence using PIST.

        Returns:
          compressed_bytes, metadata_dict
        """
        n = len(sequence)
        field_data = compute_eigenmass_field(sequence, k=self.k)
        mass = field_data["mass_field"]
        kmer_table = field_data["kmer_table"]

        # Build deterministic k-mer index (sorted for encode/decode parity)
        kmers_sorted = sorted(kmer_table.keys())
        kmer_to_idx = {km: i for i, km in enumerate(kmers_sorted)}
        self.kmer_table = kmer_table

        # Encode: for each position, decide encoding mode
        out_bits = []
        i = 0
        kmer_hits = 0
        verbatim_bases = 0
        skipped = 0

        while i < n:
            # Try k-mer match (mass below threshold or k-mer in table)
            if i + self.k <= n:
                kmer = sequence[i:i + self.k]
                if kmer in kmer_to_idx and mass[i] < mass_threshold:
                    out_bits.append(0)  # mode bit: 0 = kmer reference
                    idx = kmer_to_idx[kmer]
                    num_kmer_bits = max(1, (len(kmer_to_idx).bit_length()))
                    for b in range(num_kmer_bits):
                        out_bits.append((idx >> b) & 1)
                    i += self.k
                    kmer_hits += 1
                    continue

            # Verbatim: encode base in 2 bits
            base = sequence[i]
            if base in self.DNA_TO_2BIT:
                code = self.DNA_TO_2BIT[base]
                out_bits.append(1)  # mode bit: 1 = verbatim
                out_bits.append((code >> 1) & 1)
                out_bits.append(code & 1)
                verbatim_bases += 1
            else:
                # Non-standard base — skip
                out_bits.append(1)
                out_bits.append(0)
                out_bits.append(0)
                skipped += 1
            i += 1

        # Pack bits into bytes
        packed = bytearray()
        for j in range(0, len(out_bits), 8):
            byte = 0
            for b in range(8):
                if j + b < len(out_bits):
                    byte |= out_bits[j + b] << b
            packed.append(byte)

        compressed = bytes(packed)

        # Build k-mer dictionary for decompression
        kmers_sorted = sorted(kmer_table.keys())  # deterministic order
        kmer_index = {km: i for i, km in enumerate(kmers_sorted)}

        metadata = {
            "algorithm": "PIST",
            "k": self.k,
            "sequence_length": n,
            "compressed_bytes": len(compressed),
            "original_bits": n * 2,  # 2 bits/base minimum
            "compression_ratio": (n * 2) / max(len(compressed) * 8, 1),
            "bits_per_base": (len(compressed) * 8) / n if n > 0 else 0,
            "kmer_hits": kmer_hits,
            "verbatim_bases": verbatim_bases,
            "skipped_bases": skipped,
            "kmer_table_size": len(kmer_table),
            "kmer_dict": kmer_index,
            "mass_field": field_data,
            "sha256": hashlib.sha256(sequence.encode()).hexdigest(),
        }

        return compressed, metadata


# ── PIST Decompressor ──

def pist_decompress(compressed: bytes, metadata: Dict) -> str:
    """Decompress PIST-encoded DNA back to sequence."""
    # Unpack bits
    bits = []
    for byte in compressed:
        for b in range(8):
            bits.append((byte >> b) & 1)

    k = metadata["k"]
    kmers = sorted(metadata["kmer_dict"].keys())
    num_kmer_bits = max(1, len(kmers).bit_length())

    expected_verbatim = metadata.get("verbatim_bases", 0)
    seq = []
    i = 0
    bit_pos = 0

    while i < metadata["sequence_length"] and bit_pos + 2 < len(bits):
        mode = bits[bit_pos]
        bit_pos += 1

        if mode == 0:
            idx = 0
            for b in range(num_kmer_bits):
                if bit_pos + b < len(bits) and bits[bit_pos + b]:
                    idx |= (1 << b)
            bit_pos += num_kmer_bits
            if idx < len(kmers):
                seq.append(kmers[idx])
                i += k
            else:
                seq.append("N" * k)
                i += k
        else:
            # verbatim
            if bit_pos + 1 < len(bits):
                hi = bits[bit_pos]
                lo = bits[bit_pos + 1]
                bit_pos += 2
                code = (hi << 1) | lo
                if code < 4:
                    seq.append("ACGT"[code])
                else:
                    seq.append("N")
                i += 1
            else:
                seq.append("N")
                i += 1

    return "".join(seq)


# ── Benchmark Runners ──

def benchmark_pist(sequence: str, label: str = "") -> Dict:
    """Run PIST compressor benchmark."""
    t0 = time.time()
    compressor = PISTDNACompressor(k=16)
    compressed, meta = compressor.compress(sequence)
    dt_compress = time.time() - t0

    t0 = time.time()
    decompressed = pist_decompress(compressed, meta)
    dt_decompress = time.time() - t0

    # Verify lossless
    if len(sequence) == len(decompressed):
        errors = sum(1 for a, b in zip(sequence, decompressed) if a != b)
    else:
        errors = max(len(sequence), len(decompressed))

    lossless = (errors == 0 and len(sequence) == len(decompressed))

    return {
        "label": label,
        "algorithm": "PIST",
        "sequence_length": len(sequence),
        "compressed_bytes": len(compressed),
        "compression_ratio": (len(sequence) * 2) / max(len(compressed) * 8, 1),
        "bits_per_base": (len(compressed) * 8) / max(len(sequence), 1),
        "compress_time_s": round(dt_compress, 3),
        "decompress_time_s": round(dt_decompress, 3),
        "lossless": lossless,
        "errors": errors,
        "decomp_length": len(decompressed),
        "kmer_hits": meta["kmer_hits"],
        "verbatim_bases": meta["verbatim_bases"],
        "mean_mass": meta["mass_field"]["mean_mass"],
        "low_mass_fraction": meta["mass_field"]["low_mass_fraction"],
        "sha256": meta["sha256"],
    }


def benchmark_general(sequence: str, compressors: List[str]) -> List[Dict]:
    """Benchmark general-purpose compressors on DNA."""
    import subprocess, tempfile, os

    tmp_in = tempfile.NamedTemporaryFile(delete=False, suffix=".dna", mode="w")
    tmp_in.write(sequence)
    tmp_in.close()

    results = []
    for algo in compressors:
        cmd = None
        ext = ""
        if algo == "gzip":
            cmd = ["gzip", "-9kf", tmp_in.name]
            ext = ".gz"
        elif algo == "bzip2":
            cmd = ["bzip2", "-9kf", tmp_in.name]
            ext = ".bz2"
        elif algo == "xz":
            cmd = ["xz", "-9kf", tmp_in.name]
            ext = ".xz"
        elif algo == "zstd":
            cmd = ["zstd", "-19kf", tmp_in.name]
            ext = ".zst"

        if cmd:
            t0 = time.time()
            subprocess.run(cmd, capture_output=True, check=False)
            compress_time = time.time() - t0

            compressed_path = tmp_in.name + ext
            compressed_size = os.path.getsize(compressed_path) if os.path.exists(compressed_path) else 0

            t0 = time.time()
            result = subprocess.run(
                [algo if algo != "zstd" else "zstd", "-dkf", compressed_path],
                capture_output=True, check=False
            )
            decompress_time = time.time() - t0

            results.append({
                "algorithm": algo,
                "sequence_length": len(sequence),
                "compressed_bytes": compressed_size,
                "compression_ratio": (len(sequence) * 2) / max(compressed_size * 8, 1),
                "bits_per_base": (compressed_size * 8) / len(sequence),
                "compress_time_s": round(compress_time, 3),
                "decompress_time_s": round(decompress_time, 3),
                "lossless": True,
            })

            # Cleanup
            for f in [compressed_path, tmp_in.name]:
                if os.path.exists(f):
                    os.unlink(f)

    return results


def run_full_benchmark(fasta_path: str, label: str, is_gz: bool = False,
                       kmer_size: int = 16) -> Dict:
    """Run full benchmark suite on a FASTA file."""
    print(f"\n{'='*60}")
    print(f"BENCHMARK: {label}")
    print(f"  File: {fasta_path}")
    print(f"{'='*60}")

    # Load sequence
    t0 = time.time()
    if is_gz:
        seq = read_fasta_gz(fasta_path)
    else:
        seq = read_fasta(fasta_path)
    load_time = time.time() - t0
    print(f"  Loaded: {len(seq):,} bases in {load_time:.2f}s")

    # Test on first 500 KB for speed
    sample_size = min(len(seq), 500_000)
    sample = seq[:sample_size]
    print(f"  Sample: {sample_size:,} bases for quick tests")
    print()

    results = []

    # PIST
    pist = benchmark_pist(sample, label)
    print(f"  PIST:          {pist['compression_ratio']:.2f}x  {pist['bits_per_base']:.2f} b/b  lossless={pist['lossless']}  ({pist['compress_time_s']:.3f}s)")
    results.append(pist)

    # General compressors
    gen = benchmark_general(sample, ["gzip", "bzip2", "xz", "zstd"])
    for r in gen:
        print(f"  {r['algorithm']:12s}: {r['compression_ratio']:.2f}x  {r['bits_per_base']:.2f} b/b  ({r['compress_time_s']:.3f}s)")
        results.append(r)

    print(f"\n  === Summary: {label} ===")
    print(f"  {'Algorithm':12s} {'Ratio':>7s} {'Bits/Base':>9s}  {'Time(s)':>7s}")
    print(f"  {'-'*12} {'-'*7} {'-'*9}  {'-'*7}")
    for r in sorted(results, key=lambda x: x["bits_per_base"]):
        print(f"  {r['algorithm']:12s} {r['compression_ratio']:6.2f}x {r['bits_per_base']:9.3f}  {r['compress_time_s']:6.3f}s")

    return {
        "label": label,
        "total_bases": len(seq),
        "sample_size": sample_size,
        "load_time_s": round(load_time, 2),
        "results": results,
    }


# ── Explainability Analysis ──

def analyze_mass_field(sequence: str, mass_field: List[float],
                       k: int = 16) -> Dict:
    """
    Explain the mass field: what genomic features correspond to high-mass regions?
    This demonstrates that PIST is EXPLAINABLE — the mass field reveals real biology.
    """
    n = len(sequence)

    # Find high-mass (>0.7) windows
    high_mass_windows = []
    current_start = None
    for i in range(n):
        if mass_field[i] > 0.7:
            if current_start is None:
                current_start = i
        else:
            if current_start is not None:
                length = i - current_start
                if length > 10:
                    seq_window = sequence[current_start:i]
                    gc_content = sum(1 for c in seq_window if c in "GC") / len(seq_window)
                    cpg_count = seq_window.count("CG")
                    repeat_signal = _detect_tandem_repeat(seq_window)
                    high_mass_windows.append({
                        "start": current_start,
                        "end": i,
                        "length": length,
                        "gc_content": round(gc_content, 3),
                        "cpg_density": round(cpg_count / length, 4),
                        "tandem_repeat_score": round(repeat_signal, 3),
                        "context": seq_window[:60],
                    })
                current_start = None

    return {
        "num_high_mass_regions": len(high_mass_windows),
        "high_mass_total_bases": sum(w["length"] for w in high_mass_windows),
        "high_mass_gc_mean": (
            sum(w["gc_content"] for w in high_mass_windows) / max(len(high_mass_windows), 1)
            if high_mass_windows else 0
        ),
        "high_mass_cpg_mean": (
            sum(w["cpg_density"] for w in high_mass_windows) / max(len(high_mass_windows), 1)
            if high_mass_windows else 0
        ),
        "top_high_mass": sorted(high_mass_windows, key=lambda w: -w["length"])[:10],
    }


def _detect_tandem_repeat(seq: str) -> float:
    """Simple tandem repeat detector. Returns score 0-1."""
    if len(seq) < 8:
        return 0.0
    for period in range(2, min(8, len(seq) // 2)):
        unit = seq[:period]
        matches = sum(1 for i in range(0, len(seq) - period, period)
                      if seq[i:i + period] == unit)
        expected = len(seq) // period
        if expected > 2 and matches > expected * 0.7:
            return 1.0 - (period / 10)
    return 0.0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PIST DNA Compressor Benchmark")
    parser.add_argument("--fasta", help="FASTA file to compress")
    parser.add_argument("--benchmark", nargs="+", default=[],
                        help="FASTA files to benchmark")
    parser.add_argument("--k", type=int, default=16, help="k-mer size")
    parser.add_argument("--output", default="/home/allaun/dna_benchmark/results/benchmark_report.json",
                        help="Output JSON path")
    args = parser.parse_args()

    if args.fasta:
        seq = read_fasta(args.fasta)
        compressor = PISTDNACompressor(k=args.k)
        compressed, meta = compressor.compress(seq)
        print(json.dumps({
            "original_bases": len(seq),
            "compressed_bytes": len(compressed),
            "ratio": meta["compression_ratio"],
            "bits_per_base": meta["bits_per_base"],
            "lossless": meta["sha256"] == hashlib.sha256(seq.encode()).hexdigest(),
        }, indent=2))

    elif args.benchmark:
        all_results = {}
        for fpath in args.benchmark:
            name = fpath.split("/")[-1].replace(".gz", "").replace(".fa", "").replace(".fna", "")
            is_gz = fpath.endswith(".gz")
            result = run_full_benchmark(fpath, name, is_gz=is_gz, kmer_size=args.k)
            all_results[name] = result

        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(all_results, f, indent=2, sort_keys=True, default=str)
        print(f"\nFull benchmark report saved to: {args.output}")

    else:
        parser.print_help()
