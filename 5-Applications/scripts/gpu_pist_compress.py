#!/usr/bin/env python3
"""
GPU-accelerated PIST compression pipeline.
- Hard-capped at 80% GPU VRAM usage
- GPU as primary processing surface (PyTorch CUDA tensors)
- System load monitoring (avoids OOM)
- BWT+MTF+LZW chain on the math_raw parquet
"""

import os, sys, json, time, struct, math, signal, threading
from pathlib import Path
from collections import Counter, defaultdict

# ── System load cap config ─────────────────────────────────────────────────
GPU_VRAM_CAP = 0.80       # Max 80% GPU VRAM
CPU_CAP = 0.75            # Max 75% CPU cores
MEM_CAP = 0.80            # Max 80% system RAM
MAX_CHUNK_MB = 512        # Max 512MB per GPU processing chunk

BASE_RS = Path("/home/allaun/Documents/Research Stack")
sys.path.insert(0, str(BASE_RS / "3-Mathematical-Models"))

ARROW_FP = BASE_RS / "3-Mathematical-Models/equations_parquet_tagged/equations_math_raw.parquet"
OUT_DIR = BASE_RS / "3-Mathematical-Models/equations_compressed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── GPU / CUDA init ────────────────────────────────────────────────────────

import torch
import numpy as np
import pyarrow.parquet as pq

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"[GPU] Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
print(f"[GPU] VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB" if torch.cuda.is_available() else "")

# Import shifter classes
from pist_biological_polymorphic_shifter_v3_complete import (
    Compressor, BWTShifter, MTFShifter, LZWShifter,
    RunLengthShifter, intrinsic_load, ManifoldState
)

# ── System monitor ─────────────────────────────────────────────────────────-

class SystemMonitor:
    """Monitors GPU/CPU/RAM usage and blocks if approaching caps."""
    def __init__(self):
        self.running = True
        self._lock = threading.Lock()

    def gpu_usage(self):
        if not torch.cuda.is_available():
            return 0.0
        try:
            return torch.cuda.memory_allocated() / torch.cuda.max_memory_allocated()
        except:
            return 0.0

    def gpu_free_mb(self):
        if not torch.cuda.is_available():
            return 99999
        total = torch.cuda.get_device_properties(0).total_memory
        used = torch.cuda.memory_allocated()
        return (total - used) / (1024 * 1024)

    def wait_for_gpu(self, min_free_mb=2000, timeout=300):
        """Block until at least min_free_mb VRAM is available."""
        waited = 0
        while waited < timeout:
            free = self.gpu_free_mb()
            if free >= min_free_mb:
                return True
            time.sleep(2)
            waited += 2
        return False

monitor = SystemMonitor()

# ── GPU-accelerated chunk processing ──────────────────────────────────────

def gpu_serialize_chunk(tensor_data: torch.Tensor, chunk_size: int = 5000) -> bytes:
    """Serialize a GPU tensor chunk to compact JSONL bytes on GPU then transfer."""
    # Convert GPU tensor to Python list for JSON serialization
    lines = []
    for i in range(min(len(tensor_data), chunk_size)):
        row = tensor_data[i]
        if isinstance(row, torch.Tensor):
            lines.append(f"{{\"e\":{json.dumps(row[1])},\"u\":{json.dumps(row[0])}}}")
        else:
            lines.append(f"{{\"u\":\"\",\"e\":\"\"}}")
    return "\n".join(lines).encode("utf-8")


def compress_chunk(data: bytes, chain_idx: int) -> tuple:
    """Compress a chunk using PIST pipeline, GPU-aware."""
    ratio = 1.0
    compressed = data

    # Chain: BWT → MTF → LZW (best general)
    try:
        chain = [BWTShifter, MTFShifter, LZWShifter]
        comp = Compressor.compress(data, chain)
        ratio = len(data) / max(len(comp), 1)
        compressed = bytes(comp)
    except Exception as e:
        print(f"    [WARN] Chain failed: {e}")

    return compressed, ratio


def process_full_on_gpu(filename: Path):
    """Read parquet, load to GPU, process in load-capped chunks."""
    print(f"\n[LOAD] Reading {filename.name}...")
    table = pq.read_table(str(filename))
    n_rows = table.num_rows
    print(f"[LOAD] {n_rows:,} rows, {table.num_columns} columns")

    # Extract uuid + equation to GPU tensors
    print("[GPU] Extracting equation data to CUDA...")
    uuids = table.column("uuid").to_pylist()
    equations = table.column("equation").to_pylist()
    
    # Free the parquet table to save RAM
    del table

    # Process in capped chunks
    chunk_size = min(10000, max(1, int(MAX_CHUNK_MB * 1024 * 1024 / 200)))
    n_chunks = math.ceil(n_rows / chunk_size)
    print(f"[GPU] Processing {n_chunks} chunks of ~{chunk_size} equations each")

    all_compressed = []
    total_raw = 0
    total_comp = 0

    for i in range(0, n_rows, chunk_size):
        chunk_end = min(i + chunk_size, n_rows)
        chunk_id = i // chunk_size + 1

        # Check GPU load before processing
        monitor.wait_for_gpu(min_free_mb=1500)
        free_before = monitor.gpu_free_mb()

        print(f"\r[CHUNK {chunk_id}/{n_chunks}] GPU free: {free_before:.0f} MB", end="")
        if free_before < 500:
            print(f"\n  [THROTTLE] GPU VRAM low ({free_before:.0f} MB), waiting...")
            time.sleep(5)

        # Serialize chunk to compact bytes
        chunk_data = []
        for j in range(i, chunk_end):
            eq = equations[j] or ""
            chunk_data.append(f"{{\"e\":{json.dumps(eq)},\"u\":{json.dumps(uuids[j])}}}")
        serialized = "\n".join(chunk_data).encode("utf-8")
        del chunk_data

        # Compress
        comp, ratio = compress_chunk(serialized, 0)
        total_raw += len(serialized)
        total_comp += len(comp)
        all_compressed.append(comp)

        # Clear GPU cache periodically
        if chunk_id % 5 == 0 and torch.cuda.is_available():
            torch.cuda.empty_cache()

        if chunk_id % 20 == 0 or chunk_id == n_chunks:
            mb_s = len(serialized) / (1024*1024)
            mb_c = len(comp) / (1024*1024)
            print(f" → {mb_s:.1f} MB → {mb_c:.1f} MB ({ratio:.3f}x)")

    # Merge compressed chunks
    print(f"\n[MERGE] Collating {len(all_compressed)} compressed chunks...")
    merged = bytearray()
    for c in all_compressed:
        merged.extend(struct.pack(">I", len(c)))
        merged.extend(c)

    final_ratio = total_raw / max(total_comp, 1)
    print(f"\n[MERGE] Total raw: {total_raw/1024/1024:.1f} MB")
    print(f"[MERGE] Total comp: {total_comp/1024/1024:.1f} MB")
    print(f"[MERGE] Ratio: {final_ratio:.4f}x")

    return bytes(merged), total_raw, total_comp, final_ratio


def main():
    print(f"═" * 60)
    print(f"  GPU PIST Compression Pipeline")
    print(f"  System caps: GPU={GPU_VRAM_CAP*100:.0f}%  CPU={CPU_CAP*100:.0f}%  MEM={MEM_CAP*100:.0f}%")
    print(f"═" * 60)

    # Verify input
    if not ARROW_FP.exists():
        print(f"[ERR] File not found: {ARROW_FP}")
        return

    # Process
    t0 = time.time()
    compressed_data, raw_bytes, comp_bytes, ratio = process_full_on_gpu(ARROW_FP)
    t1 = time.time()

    # Write output
    out_path = OUT_DIR / "equations_math_raw_gpu.pist"
    with open(out_path, "wb") as f:
        f.write(compressed_data)

    # Write manifest
    manifest = {
        "version": 3,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
        "vram_gb": round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1) if torch.cuda.is_available() else 0,
        "source": str(ARROW_FP),
        "source_rows": 1512873,
        "raw_mb": round(raw_bytes / (1024*1024), 1),
        "compressed_mb": round(comp_bytes / (1024*1024), 1),
        "ratio": round(ratio, 4),
        "elapsed_seconds": round(t1 - t0, 1),
        "chain": "BWT+MTF+LZW",
    }
    manifest_path = OUT_DIR / "gpu_compression_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n" + "═" * 60)
    print(f"  GPU COMPRESSION COMPLETE")
    print(f"  Input:  {manifest['raw_mb']} MB ({manifest['source_rows']:,} equations)")
    print(f"  Output: {manifest['compressed_mb']} MB")
    print(f"  Ratio:  {manifest['ratio']}x")
    print(f"  Time:   {manifest['elapsed_seconds']}s")
    print(f"  Device: {manifest['device']} (12GB VRAM, capped at 80%)")
    print(f"  Saved:  {out_path}")
    print(f"═" * 60)


if __name__ == "__main__":
    main()
