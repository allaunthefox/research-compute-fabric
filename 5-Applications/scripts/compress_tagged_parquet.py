#!/usr/bin/env python3
"""
Compress tagged Parquet equation databases using the PIST Biological
Polymorphic Shifter pipeline for maximum ingestibility.

Pipeline:
  1. Read tagged Parquet files
  2. Apply optimal shifter chain (BWT+MTF+LZW = 1.2885x on TSV)
  3. Write compact compressed Parquet + GCL delta manifest
"""

import os, sys, json, math, struct, time
from pathlib import Path
from collections import Counter, defaultdict

# ── Imports ────────────────────────────────────────────────────────────────
BASE_RS = Path("/home/allaun/Documents/Research Stack")
sys.path.insert(0, str(BASE_RS / "3-Mathematical-Models"))

try:
    from pist_biological_polymorphic_shifter_v3_complete import (
        ManifoldState, Compressor, Optimizer, NExponent,
        BWTShifter, MTFShifter, LZWShifter, RunLengthShifter,
        PISTShifter, PISTMirrorShifter, DeltaGCLShifter,
        HuffmanShifter, SBoxShifter,
        intrinsic_load, ALL_SHIFTERS, SHIFTER_MAP
    )
    SHIFTERS_AVAILABLE = True
except ImportError as e:
    print(f"  [!] Shifter import failed: {e}")
    SHIFTERS_AVAILABLE = False

import pyarrow.parquet as pq
import pyarrow as pa

# ── Config ─────────────────────────────────────────────────────────────────
PARQUET_DIR = BASE_RS / "3-Mathematical-Models" / "equations_parquet_tagged"
OUTPUT_DIR = BASE_RS / "3-Mathematical-Models" / "equations_compressed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Optimal compression chains (benchmarked on MATH_MODEL_MAP.tsv)
CHAINS = {
    "best_general": {
        "name": "BWT+MTF+LZW",
        "shifter_list": "BWTShifter, MTFShifter, LZWShifter",
    },
    "fast_text": {
        "name": "BWT+RLE",
        "shifter_list": "BWTShifter, RunLengthShifter",
    },
    "high_entropy": {
        "name": "BWT+MTF+Huffman",
        "shifter_list": "BWTShifter, MTFShifter, HuffmanShifter",
    },
    "delta_gcl": {
        "name": "DeltaGCL",
        "shifter_list": "DeltaGCLShifter",
    },
}

def chain_from_name(name):
    """Resolve shifter name to actual class."""
    name_map = {
        "BWTShifter": BWTShifter,
        "MTFShifter": MTFShifter,
        "LZWShifter": LZWShifter,
        "RunLengthShifter": RunLengthShifter,
        "HuffmanShifter": HuffmanShifter,
        "DeltaGCLShifter": DeltaGCLShifter,
    }
    parts = [n.strip() for n in name.split(",")]
    return [name_map[p] for p in parts if p in name_map]


def serialize_parquet_to_bytes(filepath: str) -> bytes:
    """Read a Parquet file and serialize to compact bytes."""
    table = pq.read_table(filepath)
    # Convert to compact JSONL for compression
    records = table.to_pylist()
    lines = []
    for rec in records:
        # Compact form: only essential fields
        compact = {
            "e": rec.get("equation", ""),
            "p": rec.get("pattern", ""),
            "d": rec.get("domain", ""),
            "c": rec.get("confidence", 0.0),
        }
        lines.append(json.dumps(compact, separators=(",", ":")))
    return "\n".join(lines).encode("utf-8")


def compress_with_chain(data: bytes, chain_name: str) -> tuple:
    """Compress data using a named shifter chain."""
    parts = chain_name.split(",")
    chain = chain_from_name(chain_name)
    if not chain:
        return data, 1.0, "identity"

    try:
        compressed = Compressor.compress(data, chain)
        ratio = len(data) / max(len(compressed), 1)
        return bytes(compressed), ratio, chain_name
    except Exception as e:
        print(f"    [!] Chain {chain_name} failed: {e}")
        return data, 1.0, "identity"


def delta_encode_pack(data: bytes, chunk_size: int = 4096) -> bytes:
    """
    Delta GCL — chunk-level delta encoding with variable-length prefix.
    Stores first chunk raw, then deltas.
    """
    result = bytearray()
    chunks = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]

    # Store n_chunks and reference
    n_chunks = len(chunks)
    result.extend(struct.pack(">I", n_chunks))

    # First chunk: raw
    prev = chunks[0]
    result.extend(struct.pack(">I", len(prev)))
    result.extend(prev)

    # Subsequent chunks: delta
    for i in range(1, n_chunks):
        curr = chunks[i]
        # Pad shorter chunks with zeros
        max_len = max(len(prev), len(curr))
        curr_padded = curr.ljust(max_len, b'\x00')
        prev_padded = prev.ljust(max_len, b'\x00')

        # XOR delta
        delta = bytes(a ^ b for a, b in zip(curr_padded, prev_padded))
        # Run-length encode the delta
        rle_result = bytearray()
        j = 0
        while j < len(delta):
            b = delta[j]
            count = 1
            while j + count < len(delta) and delta[j + count] == b and count < 255:
                count += 1
            rle_result.append(count)
            rle_result.append(b)
            j += count

        result.extend(struct.pack(">I", len(rle_result)))
        result.extend(rle_result)
        prev = curr

    return bytes(result)


def build_manifest(all_stats: dict) -> dict:
    """Build a GCL-style manifest for the compressed dataset."""
    return {
        "version": 3,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_equations": all_stats.get("total", 0),
        "total_size_raw_mb": all_stats.get("raw_size", 0),
        "total_size_compressed_mb": all_stats.get("compressed_size", 0),
        "compression_ratio": all_stats.get("ratio", 1.0),
        "best_chain": all_stats.get("best_chain", "none"),
        "shifter_bases": all_stats.get("shifter_bases", {}),
        "files": all_stats.get("files", []),
        "pattern_counts": all_stats.get("pattern_counts", {}),
        "domain_counts": all_stats.get("domain_counts", {}),
        "n_factor_total": all_stats.get("n_factor_total", 1.0),
    }


def main():
    if not SHIFTERS_AVAILABLE:
        print("  [!] Shifters not available. Install from 3-Mathematical-Models/")
        sys.exit(1)

    print(f"═" * 60)
    print(f"  PIST Compression Pipeline for Tagged Equations")
    print(f"═" * 60)

    # Find input parquet files
    parquet_files = sorted(PARQUET_DIR.glob("*_equations_*.parquet"))
    print(f"\n  Found {len(parquet_files)} tagged Parquet files")

    all_stats = {
        "total": 0,
        "raw_size": 0,
        "compressed_size": 0,
        "ratio": 1.0,
        "best_chain": "",
        "shifter_bases": {},
        "files": [],
        "pattern_counts": {},
        "domain_counts": {},
    }

    total_raw = 0
    total_comp = 0
    total_n = 1.0

    for i, pf in enumerate(parquet_files):
        if "tagging_summary" in pf.name:
            continue

        fname = pf.stem
        fsize = pf.stat().st_size / (1024 * 1024)
        print(f"\n  [{i+1}/{len(parquet_files)}] {fname}.parquet ({fsize:.1f} MB)")

        # Read and serialize
        raw_data = serialize_parquet_to_bytes(str(pf))
        raw_mb = len(raw_data) / (1024 * 1024)
        print(f"    Serialized: {raw_mb:.1f} MB, entropy: {intrinsic_load(raw_data):.2f} bits/byte")

        # Try each compression chain
        best_data = raw_data
        best_ratio = 1.0
        best_chain_name = "none"
        best_n_factor = 1.0

        for ckey, cinfo in CHAINS.items():
            try:
                chain = chain_from_name(cinfo["shifter_list"])
                compressed = Compressor.compress(raw_data, chain)
                ratio = len(raw_data) / max(len(compressed), 1)
                print(f"    Chain {cinfo['name']:20s}: {len(compressed)/1024:.0f} KB  ratio={ratio:.4f}x")

                if ratio > best_ratio:
                    best_data = compressed
                    best_ratio = ratio
                    best_chain_name = ckey
            except Exception as e:
                print(f"    Chain {cinfo['name']:20s}: ERROR — {e}")

        # Apply delta GCL encoding on top
        if best_ratio < 2.0 and len(best_data) > 100000:
            delta_packed = delta_encode_pack(best_data)
            delta_ratio = len(best_data) / max(len(delta_packed), 1)
            if delta_ratio > 1.05:
                print(f"    DeltaGCL boost: {len(best_data)/1024:.0f} → {len(delta_packed)/1024:.0f} KB  ratio={delta_ratio:.3f}x")
                best_data = delta_packed
                best_ratio = best_ratio * delta_ratio

        # Write compressed output
        output_path = OUTPUT_DIR / f"{fname}.compressed"
        with open(output_path, "wb") as f:
            f.write(best_data)

        comp_mb = len(best_data) / (1024 * 1024)
        print(f"    → {output_path.name}: {comp_mb:.1f} MB  ({best_ratio:.3f}x)")

        total_raw += len(raw_data)
        total_comp += len(best_data)

        # Track pattern/domain counts from the data
        table = pq.read_table(str(pf))
        records = table.to_pylist()
        for rec in records:
            p = rec.get("pattern", "unknown")
            d = rec.get("domain", "unknown")
            all_stats["pattern_counts"][p] = all_stats["pattern_counts"].get(p, 0) + 1
            all_stats["domain_counts"][d] = all_stats["domain_counts"].get(d, 0) + 1
        all_stats["total"] += len(records)

        all_stats["files"].append({
            "name": fname,
            "raw_bytes": len(raw_data),
            "compressed_bytes": len(best_data),
            "ratio": best_ratio,
            "chain": best_chain_name,
        })

        # Track best global chain
        if best_ratio > all_stats.get("ratio", 1.0):
            all_stats["ratio"] = best_ratio
            all_stats["best_chain"] = best_chain_name

    # Calculate aggregate stats
    all_stats["raw_size"] = round(total_raw / (1024*1024), 1)
    all_stats["compressed_size"] = round(total_comp / (1024*1024), 1)
    if total_comp > 0:
        all_stats["ratio"] = round(total_raw / total_comp, 3)

    # Build and write manifest
    manifest = build_manifest(all_stats)
    manifest_path = OUTPUT_DIR / "compression_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\n  Manifest: {manifest_path}")

    # Build index for ingestibility
    index = {
        "manifest": "compression_manifest.json",
        "files": {},
        "chains_used": list(CHAINS.keys()),
    }
    for f_info in all_stats["files"]:
        index["files"][f_info["name"]] = {
            "compressed": f"{f_info['name']}.compressed",
            "raw_mb": round(f_info["raw_bytes"] / (1024*1024), 2),
            "compressed_mb": round(f_info["compressed_bytes"] / (1024*1024), 2),
            "ratio": round(f_info["ratio"], 3),
            "chain": f_info["chain"],
        }
    index_path = OUTPUT_DIR / "index.json"
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)

    print(f"\n" + "═" * 60)
    print(f"  COMPRESSION COMPLETE")
    print(f"  Total raw:      {all_stats['raw_size']} MB")
    print(f"  Total compressed: {all_stats['compressed_size']} MB")
    print(f"  Global ratio:   {all_stats['ratio']}x")
    print(f"  Best chain:     {all_stats['best_chain']}")
    print(f"  Output:         {OUTPUT_DIR}/")
    print(f"═" * 60)

    # Copy index to parquet dir for discoverability
    import shutil
    shutil.copy(str(index_path), str(PARQUET_DIR / ".." / "equations_NUVMAP_index.json"))


if __name__ == "__main__":
    main()
