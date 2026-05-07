#!/usr/bin/env python3
"""
PIST-S3C-FAMM Accelerated Gdrive Offload Pipeline
===================================================
Compresses, streams, and offloads 530G of corpora/archives to Gdrive
using every aspect of the Research Stack math.

Pipeline:
  S3C shell batching → PIST compress → FAMM rate-shaping → rclone stream → OAC manifest
"""

import os, sys, json, time, hashlib, subprocess, zlib, struct
from pathlib import Path
from dataclasses import dataclass, field
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple
import threading

RESEARCH_STACK = Path("/home/allaun/Documents/Research Stack")
GD_REMOTE = "Gdrive:research-stack-offload"

# ── S3C Shell Coordinates ──────────────────────────────────────────
def s3c_split(n: int) -> Dict:
    """n = k² + a, with mirror b⁰, tension b⁺, mass, delta"""
    k = int(n ** 0.5)
    a = n - k * k
    b0 = (k + 1) ** 2 - 1 - n
    b_plus = (k + 1) ** 2 - n
    mass = a * b0
    delta = a - b0
    throat = "throat" if abs(delta) <= 1 else ("lower" if delta < 0 else "upper")
    return {"k": k, "a": a, "b0": b0, "b_plus": b_plus,
            "mass": mass, "delta": delta, "throat": throat}

# ── PIST Compression ───────────────────────────────────────────────
def pist_compress(data: bytes, level: int = 6) -> bytes:
    """PIST-inspired: zlib with shell-aware dictionary preset"""
    compressor = zlib.compressobj(level, zlib.DEFLATED, -zlib.MAX_WBITS, 9, zlib.Z_DEFAULT_STRATEGY)
    # Shell header: [k:u16][a:u16][method:u8]
    n = len(data)
    s = s3c_split(n)
    header = struct.pack(">HHB", s["k"] & 0xFFFF, s["a"] & 0xFFFF, 0x01)
    compressed = compressor.compress(data) + compressor.flush()
    return header + compressed

def pist_decompress(data: bytes) -> bytes:
    header = data[:5]
    k, a, method = struct.unpack(">HHB", header)
    decompressor = zlib.decompressobj(-zlib.MAX_WBITS)
    return decompressor.decompress(data[5:]) + decompressor.flush()

# ── FAMM Rate Shaping ──────────────────────────────────────────────
class FAMMRateShaper:
    """FAMM preshaped delay line for upload rate control"""
    def __init__(self, base_delay_ms: float = 50, max_parallel: int = 4):
        self.base_delay = base_delay_ms / 1000.0
        self.max_parallel = max_parallel
        self.semaphore = threading.Semaphore(max_parallel)
        self.latencies = deque(maxlen=100)
        self.eigenvalues = [1.77, 2.51, 3.07, 3.54]  # from topology
    
    def delay_for_shell(self, k: int) -> float:
        """Preshape delay based on shell index — larger shells get more time"""
        ev = self.eigenvalues[min(k, len(self.eigenvalues) - 1) % len(self.eigenvalues)]
        return self.base_delay * (ev ** 0.5)
    
    def acquire(self, size_bytes: int):
        self.semaphore.acquire()
        k = int(size_bytes ** 0.5)
        time.sleep(self.delay_for_shell(k) * 0.01)  # scale down for practical use
    
    def release(self, latency_ms: float):
        self.latencies.append(latency_ms)
        self.semaphore.release()

# ── OAC Manifest ────────────────────────────────────────────────────
@dataclass
class OACManifest:
    """Observer-Admissible Cavity: tracks what was offloaded"""
    entries: List[Dict] = field(default_factory=list)
    total_bytes: int = 0
    compressed_bytes: int = 0
    
    def record(self, path: str, size: int, csize: int, gd_path: str, shell: Dict):
        self.entries.append({
            "local": path, "size": size, "compressed": csize,
            "remote": gd_path, "shell": shell,
            "hash": hashlib.sha256(path.encode()).hexdigest()[:16],
            "ts": time.time()
        })
        self.total_bytes += size
        self.compressed_bytes += csize
    
    def save(self, path: Path):
        with open(path, 'w') as f:
            json.dump({
                "entries": self.entries,
                "total_bytes": self.total_bytes,
                "compressed_bytes": self.compressed_bytes,
                "ratio": self.compressed_bytes / max(self.total_bytes, 1),
                "saved_bytes": self.total_bytes - self.compressed_bytes
            }, f, indent=2)

# ── Streaming Offload Engine ────────────────────────────────────────
class StreamingOffloadEngine:
    def __init__(self):
        self.shaper = FAMMRateShaper()
        self.manifest = OACManifest()
        self.lock = threading.Lock()
        self.stats = {"files": 0, "bytes": 0, "errors": 0}
    
    def stream_file(self, filepath: Path, gd_base: str) -> Dict:
        """Compress in chunks, stream to Gdrive via rclone rcat"""
        try:
            size = filepath.stat().st_size
            self.shaper.acquire(size)
            
            t0 = time.time()
            rel = filepath.relative_to(RESEARCH_STACK)
            gd_path = f"{gd_base}/{rel}.pist"
            
            # Pre-calculate shell header
            s = s3c_split(size)
            header = struct.pack(">HHB", s["k"] & 0xFFFF, s["a"] & 0xFFFF, 0x01)
            
            # Start rclone rcat process
            proc = subprocess.Popen(
                ["rclone", "rcat", gd_path],
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            compressor = zlib.compressobj(3, zlib.DEFLATED, -zlib.MAX_WBITS, 9, zlib.Z_DEFAULT_STRATEGY)
            compressed_len = 0
            
            # Write header
            proc.stdin.write(header)
            compressed_len += len(header)
            
            # Stream file in 1MB chunks
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(1024 * 1024)
                    if not chunk:
                        break
                    out = compressor.compress(chunk)
                    if out:
                        proc.stdin.write(out)
                        compressed_len += len(out)
                
                final = compressor.flush()
                if final:
                    proc.stdin.write(final)
                    compressed_len += len(final)
            
            proc.stdin.close()
            stdout, stderr = proc.communicate(timeout=3600) # Long timeout for huge files
            
            latency = (time.time() - t0) * 1000
            self.shaper.release(latency)
            
            if proc.returncode != 0:
                raise RuntimeError(stderr.decode())
            
            with self.lock:
                self.manifest.record(str(rel), size, compressed_len, gd_path, s)
                self.stats["files"] += 1
                self.stats["bytes"] += size
            
            return {"path": str(rel), "size": size, "compressed": compressed_len,
                    "latency_ms": latency, "shell": s["k"], "ok": True}
        
        except Exception as e:
            with self.lock:
                self.stats["errors"] += 1
            return {"path": str(filepath), "error": str(e), "ok": False}
    
    def stream_directory(self, dirpath: Path, gd_base: str, workers: int = 4):
        """S3C-batched parallel streaming of entire directory"""
        files = list(dirpath.rglob("*"))
        files = [f for f in files if f.is_file() and not f.name.startswith('.')]
        
        # S3C shell batching: group by shell index k for optimal streaming
        batches = {}
        for f in files:
            k = s3c_split(f.stat().st_size)["k"]
            batches.setdefault(k, []).append(f)
        
        print(f"  {len(files)} files in {len(batches)} S3C shell batches")
        
        total = len(files)
        done = 0
        
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = []
            for k in sorted(batches.keys(), reverse=True):  # largest shells first
                for f in batches[k]:
                    futures.append(pool.submit(self.stream_file, f, gd_base))
            
            for future in as_completed(futures):
                result = future.result()
                done += 1
                
                # Print every 10 files or if the file was large (>1GB)
                if done % 10 == 0 or result.get("size", 0) > 1e9 or done == total:
                    pct = done / total * 100
                    status = f"Done: {result['path']} ({result.get('size', 0)/1e9:.1f}GB)" if result.get("size", 0) > 1e9 else "..."
                    print(f"  [{done}/{total}] {pct:.1f}% — "
                          f"{self.stats['bytes']/1e9:.1f}GB streamed, "
                          f"{self.stats['errors']} errors. {status}")
        
        return self.stats

# ── Main ────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("PIST-S3C-FAMM Accelerated Gdrive Offload")
    print("=" * 60)
    
    engine = StreamingOffloadEngine()
    
    OFFLOAD_TARGETS = [
        ("data/corpora", "corpora"),
        ("6-Documentation/archive", "archive"),
    ]
    
    manifest_path = RESEARCH_STACK / "4-Infrastructure/shim/gdrive_offload_manifest.json"
    t_start = time.time()
    
    for dirname, gd_dir in OFFLOAD_TARGETS:
        local = RESEARCH_STACK / dirname
        if not local.exists():
            print(f"\n⚠ {dirname} not found, skipping")
            continue
        
        gd_path = f"{GD_REMOTE}/{gd_dir}"
        print(f"\n{'─' * 60}")
        print(f"Offloading: {dirname} → {gd_path}")
        print(f"Local size: {sum(f.stat().st_size for f in local.rglob('*') if f.is_file())/1e9:.1f}GB")
        print(f"{'─' * 60}")
        
        stats = engine.stream_directory(local, gd_path, workers=4)
        
        print(f"\n  Complete: {stats['files']} files, {stats['bytes']/1e9:.1f}GB, {stats['errors']} errors")
    
    elapsed = time.time() - t_start
    
    # Save manifest
    engine.manifest.save(manifest_path)
    
    print(f"\n{'=' * 60}")
    print(f"OFFLOAD COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Total files:    {engine.manifest.entries.__len__()}")
    print(f"  Raw bytes:      {engine.manifest.total_bytes / 1e9:.1f} GB")
    print(f"  Compressed:     {engine.manifest.compressed_bytes / 1e9:.1f} GB")
    print(f"  Ratio:          {engine.manifest.compressed_bytes / max(engine.manifest.total_bytes, 1):.2%}")
    print(f"  Time:           {elapsed:.0f}s")
    print(f"  Throughput:     {engine.manifest.total_bytes / elapsed / 1e6:.1f} MB/s")
    print(f"  Manifest:       {manifest_path}")
    
    # Next step: delete local files
    print(f"\n  To free disk space, run:")
    print(f"  rm -rf '{RESEARCH_STACK}/data/corpora' '{RESEARCH_STACK}/6-Documentation/archive'")

if __name__ == "__main__":
    main()
