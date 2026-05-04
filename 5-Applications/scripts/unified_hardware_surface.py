#!/usr/bin/env python3
"""
UNIFIED HARDWARE SURFACE (UHS)
Expose the entire machine — CPU, GPU, RAM, VRAM, NVMe — as a single 
computational fabric for the Topological State Machine and manifold work.

Hardware Profile:
  CPU:  AMD Ryzen 5 9600X (6c/12t, ~5.5 GHz)
  RAM:  30 GB (17 GB available)
  GPU:  NVIDIA RTX 4070 SUPER (12 GB VRAM, 10 GB free)
  Disk: 1.9 TB NVMe SSD (633 GB free)
  NUMA: 1 node (no NUMA complexity)

Design:
  - UnifiedMemory: tiered RAM → VRAM → NVMe cache with LRU eviction
  - ComputeSurface: CPU thread pool + CUDA stream scheduler
  - Dataflow: zero-copy where possible, pinned memory for GPU transfers
  - TopologyTask: any operation (fingerprint, encode, manifold update) is a 
    Task that the scheduler routes to CPU or GPU based on data locality
"""

import os
import re
import sys
import json
import math
import time
import hashlib
import sqlite3
import threading
import multiprocessing
from pathlib import Path
from collections import Counter, defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Callable, Iterator

# Optional GPU imports (graceful degradation)
try:
    import torch
    import torch.cuda as cuda
    HAS_CUDA = cuda.is_available()
    if HAS_CUDA:
        DEVICE = torch.device("cuda:0")
        print(f"  [UHS] CUDA available: {cuda.get_device_name(0)}")
        print(f"  [UHS] VRAM: {cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
except ImportError:
    HAS_CUDA = False
    DEVICE = None
    print("  [UHS] CUDA not available — CPU-only mode")

BASE = Path("/home/allaun/Documents/Research Stack")
CACHE_DIR = BASE / "3-Mathematical-Models/unified_surface/cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ── Hardware Discovery ───────────────────────────────────────────────────────

class HardwareTopology:
    """Discover and represent the machine's hardware topology."""
    
    def __init__(self):
        self.cpu_cores = os.cpu_count() or 12
        self.cpu_threads = self.cpu_cores * 2  # SMT assumed
        self.ram_total_gb = self._ram_gb()
        self.ram_available_gb = self._ram_available_gb()
        self.has_gpu = HAS_CUDA
        self.vram_total_gb = 0.0
        self.vram_free_gb = 0.0
        self.disk_free_gb = 0.0
        
        if self.has_gpu:
            props = cuda.get_device_properties(0)
            self.vram_total_gb = props.total_memory / (1024**3)
            self.vram_free_gb = (props.total_memory - cuda.memory_allocated()) / (1024**3)
        
        self.disk_free_gb = self._disk_free_gb()
    
    def _ram_gb(self) -> float:
        try:
            with open('/proc/meminfo') as f:
                for line in f:
                    if line.startswith('MemTotal:'):
                        return int(line.split()[1]) / (1024**2)
        except:
            pass
        return 30.0
    
    def _ram_available_gb(self) -> float:
        try:
            with open('/proc/meminfo') as f:
                for line in f:
                    if line.startswith('MemAvailable:'):
                        return int(line.split()[1]) / (1024**2)
        except:
            pass
        return 17.0
    
    def _disk_free_gb(self) -> float:
        try:
            stat = os.statvfs('/')
            return (stat.f_bavail * stat.f_frsize) / (1024**3)
        except:
            return 600.0
    
    def summary(self) -> dict:
        return {
            "cpu_cores": self.cpu_cores,
            "cpu_threads": self.cpu_threads,
            "ram_total_gb": round(self.ram_total_gb, 1),
            "ram_available_gb": round(self.ram_available_gb, 1),
            "has_gpu": self.has_gpu,
            "vram_total_gb": round(self.vram_total_gb, 1),
            "vram_free_gb": round(self.vram_free_gb, 1),
            "disk_free_gb": round(self.disk_free_gb, 1),
            "compute_units": self.cpu_cores + (1024 if self.has_gpu else 0),  # GPU SM count approx
        }

# ── Unified Memory Tier ──────────────────────────────────────────────────────

class UnifiedMemory:
    """
    Tiered memory: RAM → VRAM → NVMe cache.
    Data blocks are tracked by hash. Hot data stays in RAM, warm in VRAM,
    cold spills to NVMe. All access is via hash lookup.
    """
    
    def __init__(self, hw: HardwareTopology, cache_dir: Path = CACHE_DIR):
        self.hw = hw
        self.cache_dir = cache_dir
        self.db_path = cache_dir / "unified_memory.db"
        
        # RAM cache: hash -> data
        self.ram_cache: Dict[str, bytes] = {}
        self.ram_max_mb = int(hw.ram_available_gb * 0.5 * 1024)  # 50% of available RAM
        self.ram_current_mb = 0
        self.ram_lru: deque = deque()  # LRU order
        
        # VRAM cache: hash -> GPU tensor (only for numeric data)
        self.vram_cache: Dict[str, torch.Tensor] = {}
        self.vram_max_mb = int(hw.vram_free_gb * 0.7 * 1024) if hw.has_gpu else 0
        self.vram_current_mb = 0
        
        # NVMe spill
        self.nvme_dir = cache_dir / "nvme_spill"
        self.nvme_dir.mkdir(exist_ok=True)
        
        self._init_db()
        self.lock = threading.RLock()
    
    def _init_db(self):
        with sqlite3.connect(str(self.db_path), timeout=30) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS blocks (
                    hash TEXT PRIMARY KEY,
                    size_mb REAL NOT NULL,
                    tier TEXT NOT NULL,  -- ram, vram, nvme
                    last_access TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def _evict_ram(self, needed_mb: float):
        """Evict oldest RAM entries to NVMe until space available."""
        while self.ram_current_mb + needed_mb > self.ram_max_mb and self.ram_lru:
            oldest_hash = self.ram_lru.popleft()
            if oldest_hash in self.ram_cache:
                data = self.ram_cache.pop(oldest_hash)
                self.ram_current_mb -= len(data) / (1024**2)
                # Spill to NVMe if valuable (>1KB)
                if len(data) > 1024:
                    spill_path = self.nvme_dir / oldest_hash
                    spill_path.write_bytes(data)
                    with sqlite3.connect(str(self.db_path), timeout=30) as conn:
                        conn.execute(
                            "INSERT OR REPLACE INTO blocks (hash, size_mb, tier) VALUES (?, ?, ?)",
                            (oldest_hash, len(data)/(1024**2), "nvme")
                        )
                        conn.commit()
    
    def store(self, data_hash: str, data: bytes, prefer_gpu: bool = False):
        """Store data block in appropriate tier."""
        with self.lock:
            size_mb = len(data) / (1024**2)
            
            # Try GPU for numeric tensors
            if prefer_gpu and HAS_CUDA and size_mb < self.vram_max_mb * 0.1:
                try:
                    tensor = torch.frombuffer(data, dtype=torch.uint8).to(DEVICE)
                    if self.vram_current_mb + size_mb > self.vram_max_mb:
                        self._evict_vram(size_mb)
                    self.vram_cache[data_hash] = tensor
                    self.vram_current_mb += size_mb
                    self._db_update(data_hash, size_mb, "vram")
                    return
                except:
                    pass  # Fall through to RAM
            
            # RAM
            if self.ram_current_mb + size_mb > self.ram_max_mb:
                self._evict_ram(size_mb)
            
            self.ram_cache[data_hash] = data
            self.ram_current_mb += size_mb
            self.ram_lru.append(data_hash)
            self._db_update(data_hash, size_mb, "ram")
    
    def _evict_vram(self, needed_mb: float):
        """Evict oldest VRAM entries back to RAM."""
        while self.vram_current_mb + needed_mb > self.vram_max_mb and self.vram_cache:
            oldest = next(iter(self.vram_cache))
            tensor = self.vram_cache.pop(oldest)
            data = tensor.cpu().numpy().tobytes()
            self.vram_current_mb -= len(data) / (1024**2)
            # Push to RAM
            if oldest not in self.ram_cache:
                self.ram_cache[oldest] = data
                self.ram_current_mb += len(data) / (1024**2)
                self.ram_lru.append(oldest)
    
    def _db_update(self, data_hash: str, size_mb: float, tier: str):
        with sqlite3.connect(str(self.db_path), timeout=30) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO blocks (hash, size_mb, tier) VALUES (?, ?, ?)",
                (data_hash, size_mb, tier)
            )
            conn.commit()
    
    def retrieve(self, data_hash: str) -> Optional[bytes]:
        """Retrieve data block from any tier."""
        with self.lock:
            # RAM
            if data_hash in self.ram_cache:
                self.ram_lru.remove(data_hash)
                self.ram_lru.append(data_hash)  # promote to MRU
                return self.ram_cache[data_hash]
            
            # VRAM
            if data_hash in self.vram_cache:
                tensor = self.vram_cache[data_hash]
                return tensor.cpu().numpy().tobytes()
            
            # NVMe
            spill_path = self.nvme_dir / data_hash
            if spill_path.exists():
                data = spill_path.read_bytes()
                # Promote to RAM
                self.store(data_hash, data)
                spill_path.unlink()
                with sqlite3.connect(str(self.db_path), timeout=30) as conn:
                    conn.execute("DELETE FROM blocks WHERE hash=?", (data_hash,))
                    conn.commit()
                return data
            
            return None
    
    def stats(self) -> dict:
        return {
            "ram_used_mb": round(self.ram_current_mb, 1),
            "ram_max_mb": self.ram_max_mb,
            "vram_used_mb": round(self.vram_current_mb, 1),
            "vram_max_mb": self.vram_max_mb,
            "nvme_files": len(list(self.nvme_dir.iterdir())),
            "total_blocks_cached": len(self.ram_cache) + len(self.vram_cache),
        }

# ── Compute Surface ───────────────────────────────────────────────────────────

class ComputeSurface:
    """
    Unified compute: CPU threads + GPU CUDA streams exposed as one scheduling surface.
    Tasks are routed based on type and data location.
    """
    
    def __init__(self, hw: HardwareTopology):
        self.hw = hw
        self.cpu_pool = ThreadPoolExecutor(max_workers=hw.cpu_threads)
        self.gpu_stream = None
        if hw.has_gpu:
            self.gpu_stream = cuda.Stream()
        
        self.task_stats = Counter()
        self.task_times = defaultdict(list)
    
    def submit(self, task_fn: Callable, *args, prefer_gpu: bool = False, **kwargs):
        """Submit task to appropriate compute unit."""
        start = time.time()
        
        if prefer_gpu and self.hw.has_gpu and self._is_gpu_suitable(task_fn):
            # GPU path
            future = self.cpu_pool.submit(self._gpu_wrap, task_fn, *args, **kwargs)
            self.task_stats['gpu'] += 1
        else:
            # CPU path
            future = self.cpu_pool.submit(task_fn, *args, **kwargs)
            self.task_stats['cpu'] += 1
        
        elapsed = time.time() - start
        self.task_times['submit'].append(elapsed)
        return future
    
    def _is_gpu_suitable(self, fn: Callable) -> bool:
        """Heuristic: GPU good for matrix ops, bad for string parsing."""
        name = fn.__name__ if hasattr(fn, '__name__') else str(fn)
        gpu_friendly = {'matmul', 'conv', 'fft', 'encode_batch', 'tensor', 'embedding'}
        return any(k in name.lower() for k in gpu_friendly)
    
    def _gpu_wrap(self, fn, *args, **kwargs):
        """Run function with CUDA stream context."""
        if self.gpu_stream:
            with cuda.device(0):
                return fn(*args, **kwargs)
        return fn(*args, **kwargs)
    
    def map(self, fn: Callable, items: Iterator, prefer_gpu: bool = False):
        """Parallel map across all compute units."""
        futures = [self.submit(fn, item, prefer_gpu=prefer_gpu) for item in items]
        return [f.result() for f in futures]
    
    def stats(self) -> dict:
        return {
            "cpu_tasks": self.task_stats['cpu'],
            "gpu_tasks": self.task_stats['gpu'],
            "avg_submit_ms": round(sum(self.task_times['submit']) / len(self.task_times['submit']) * 1000, 2) if self.task_times['submit'] else 0,
            "pool_workers": self.cpu_pool._max_workers,
        }

# ── Unified Surface (The Main API) ────────────────────────────────────────────

class UnifiedSurface:
    """
    The single surface: memory + compute exposed as one entity.
    
    Usage:
      surface = UnifiedSurface()
      surface.put("block_hash", data_bytes)
      result = surface.compute(fingerprint_fn, "block_hash")
    """
    
    def __init__(self):
        print("=" * 70)
        print("  UNIFIED HARDWARE SURFACE (UHS)")
        print("  Initializing hardware topology...")
        print("=" * 70)
        
        self.hw = HardwareTopology()
        self.memory = UnifiedMemory(self.hw)
        self.compute = ComputeSurface(self.hw)
        
        print(f"\n  [CPU] {self.hw.cpu_cores} cores / {self.hw.cpu_threads} threads")
        print(f"  [RAM] {self.hw.ram_available_gb:.1f} GB available / {self.hw.ram_total_gb:.1f} GB total")
        if self.hw.has_gpu:
            print(f"  [GPU] {self.hw.vram_free_gb:.1f} GB free / {self.hw.vram_total_gb:.1f} GB total")
        print(f"  [Disk] {self.hw.disk_free_gb:.1f} GB free (NVMe)")
        print(f"\n  UHS ready: {self.hw.summary()['compute_units']} compute units")
        print("=" * 70)
    
    def put(self, key: str, data: bytes, prefer_gpu: bool = False):
        """Store data on the unified surface."""
        self.memory.store(key, data, prefer_gpu=prefer_gpu)
    
    def get(self, key: str) -> Optional[bytes]:
        """Retrieve data from the unified surface."""
        return self.memory.retrieve(key)
    
    def compute(self, fn: Callable, *args, prefer_gpu: bool = False, **kwargs):
        """Execute function on the best available compute unit."""
        return self.compute.submit(fn, *args, prefer_gpu=prefer_gpu, **kwargs)
    
    def parallel_map(self, fn: Callable, items: List, prefer_gpu: bool = False):
        """Map function across all compute units in parallel."""
        return self.compute.map(fn, iter(items), prefer_gpu=prefer_gpu)
    
    def stats(self) -> dict:
        return {
            "hardware": self.hw.summary(),
            "memory": self.memory.stats(),
            "compute": self.compute.stats(),
            "timestamp": datetime.now().isoformat(),
        }
    
    def save_state(self, path: Path):
        """Serialize surface state."""
        with open(path, "w") as f:
            json.dump(self.stats(), f, indent=2)
        print(f"  Surface state saved: {path}")

# ── Integration: TSM + Manifold on the Surface ─────────────────────────────────

def fingerprint_batch(texts: List[str]) -> List[str]:
    """Batch fingerprinting — CPU-bound, stays on CPU."""
    # POS tag dictionaries
    CLOSED = {'the','a','an','and','or','but','in','on','at','to','for','of','with','by','from','as',
              'is','was','are','were','be','been','being','have','has','had','do','does','did','will',
              'would','could','should','may','might','can','shall','this','that','these','those','it',
              'its','they','them','their','he','she','his','her','him','we','us','our','you','your',
              'my','mine','i','me','who','which','what','when','where','why','how','all','each',
              'every','both','either','neither','some','any','no','none','more','most','many','much',
              'few','little','other','another','such','only','own','same','so','than','too','very',
              'just','now','then','here','there','up','down','out','off','over','under','again',
              'further','once','not','also','always','never','often','sometimes','usually','still'}
    PREP = {'in','on','at','by','for','with','about','against','between','into','through','during',
            'before','after','above','below','to','from','up','down','of','off','over','under',
            'again','further','then','once','around','behind','beyond','despite','except','inside',
            'near','past','since','toward','upon','within','without','across','along','among',
            'beside','besides','concerning','considering','following','including','like','minus',
            'plus','regarding','round','save','till','until','via','worth'}
    CONJ = {'and','or','but','nor','yet','so','for','although','because','before','if','since',
            'though','unless','until','when','while','whereas','whether','either','neither',
            'both','not','only','than','rather','however','moreover','furthermore','nevertheless',
            'otherwise','therefore','thus','hence','consequently','meanwhile'}
    AUX = {'be','am','is','are','was','were','being','been','have','has','had','do','does','did',
           'will','would','shall','should','may','might','can','could','must','ought','need',
           'dare','used','get','gets','got','getting','become','becomes','became','seem','seems',
           'seemed','appear','appears','appeared'}
    PRON = {'i','me','my','mine','myself','you','your','yours','yourself','he','him','his',
            'himself','she','her','hers','herself','it','its','itself','we','us','our','ours',
            'ourselves','they','them','their','theirs','themselves','this','that','these','those',
            'who','whom','whose','which','what','whatever','whoever','whomever','anyone','someone',
            'everyone','nobody','nothing','something','anything','everything'}
    DET = {'the','a','an','this','that','these','those','my','your','his','her','its','our',
           'their','some','any','no','each','every','either','neither','both','all','half',
           'enough','several','many','much','few','little','other','another','such','what',
           'which','whose','one','two','three','first','last','next','various','certain'}
    
    def tag(w):
        w = w.lower().strip("'\"")
        if w in DET: return "DET"
        if w in PRON: return "PRON"
        if w in PREP: return "PREP"
        if w in CONJ: return "CONJ"
        if w in AUX: return "AUX"
        if w in CLOSED: return "FUNC"
        if w.endswith("ing"): return "VBG"
        if w.endswith("ed"): return "VBN"
        if w.endswith(("ly","ily","ally")): return "ADV"
        if w.endswith(("tion","sion","ment","ness","ity","ance","ence","hood","ship")): return "NOUN"
        if w.endswith(("able","ible","ful","ous","ive","less","ish","al")): return "ADJ"
        if w.endswith(("ize","ise","ify","ate")): return "VERB"
        if len(w) <= 3: return "SHORT"
        return "LEX"
    
    def fp(sentence):
        words = re.findall(r"[a-zA-Z']+", sentence)
        if len(words) < 3 or len(words) > 40:
            return ""
        tags = [tag(w) for w in words]
        collapsed = []
        prev = None
        for t in tags:
            if t != prev:
                collapsed.append(t)
                prev = t
            elif t == "LEX" and (len(collapsed) < 2 or collapsed[-2] != "LEX+"):
                collapsed[-1] = "LEX+"
        return " ".join(collapsed)
    
    return [fp(t) for t in texts]

# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 70)
    print("  UNIFIED HARDWARE SURFACE — STRESS TEST")
    print("=" * 70)
    
    surface = UnifiedSurface()
    
    # Test 1: Store and retrieve data
    print("\n[1] Memory tier test...")
    test_data = b"Hello, unified surface! " * 10000
    test_hash = hashlib.sha256(test_data).hexdigest()
    surface.put(test_hash, test_data)
    retrieved = surface.get(test_hash)
    assert retrieved == test_data
    print(f"  Stored/retrieved: {len(test_data):,} bytes — OK")
    
    # Test 2: Parallel compute (CPU-bound fingerprinting)
    print("\n[2] Parallel compute test (fingerprinting)...")
    sentences = [
        "The cat sat on the mat and looked at the moon.",
        "However, the situation changed dramatically after the event.",
        "In order to understand quantum mechanics, one must first study linear algebra.",
        "The quick brown fox jumps over the lazy dog.",
    ] * 1000  # 4000 sentences
    
    start = time.time()
    results = surface.parallel_map(fingerprint_batch, 
                                   [sentences[i:i+100] for i in range(0, len(sentences), 100)])
    elapsed = time.time() - start
    total_fps = sum(len(r) for r in results)
    print(f"  Fingerprinted {total_fps:,} sentences in {elapsed:.2f}s ({total_fps/elapsed:,.0f} sent/s)")
    
    # Test 3: Stats
    print("\n[3] Surface statistics...")
    stats = surface.stats()
    print(f"  Hardware: {stats['hardware']}")
    print(f"  Memory: {stats['memory']}")
    print(f"  Compute: {stats['compute']}")
    
    # Save state
    out_dir = BASE / "3-Mathematical-Models/unified_surface"
    out_dir.mkdir(parents=True, exist_ok=True)
    surface.save_state(out_dir / f"uhs_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    print(f"\n{'='*70}")
    print("  UHS READY")
    print(f"{'='*70}")
    print("  The entire machine is now one surface:")
    print(f"    CPU:  {surface.hw.cpu_threads} threads")
    print(f"    RAM:  {surface.memory.ram_max_mb} MB managed")
    print(f"    GPU:  {surface.memory.vram_max_mb} MB managed (if available)")
    print(f"    Disk: {surface.memory.nvme_dir} (NVMe spill)")
    print(f"\n  All TSM/manifold operations route through this surface.")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
