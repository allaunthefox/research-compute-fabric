#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
Interference Eraser Cache Simulator — Tick 694

Test interference eraser principles on CPU cache optimization.
Run on your actual CPU to measure erasure vs. tracking trade-offs.

Usage:
    python3 interference_eraser_cache_sim.py
    
    # Test different erasure probabilities
    python3 interference_eraser_cache_sim.py --erase_probs 0.0 0.5 0.7 0.9 1.0
    
    # Run specific workload
    python3 interference_eraser_cache_sim.py --workload spatial
"""

import numpy as np
import argparse
import time
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

# Optional imports for visualization
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# ============================================================================
# Cache Models
# ============================================================================

@dataclass
class CacheLine:
    """Standard cache line with full tracking."""
    tag: int
    data: Optional[bytes] = None
    state: str = 'I'  # MESI: M/E/S/I
    lru_counter: int = 0
    owner_core: int = -1
    access_history: List[int] = field(default_factory=list)


@dataclass
class ErasedCacheLine:
    """Interference eraser cache line with aggregate metrics only."""
    tag: int
    data: Optional[bytes] = None
    lru_counter: int = 0  # Still need for LRU eviction
    access_frequency: float = 0.0
    temporal_decay: float = 0.0
    spatial_cluster: int = -1
    # Erased: specific core_id, specific access order


@dataclass
class CacheStats:
    """Cache performance statistics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    coherence_updates: int = 0
    metadata_updates: int = 0
    total_accesses: int = 0
    
    @property
    def hit_rate(self) -> float:
        if self.total_accesses == 0:
            return 0.0
        return self.hits / self.total_accesses
    
    @property
    def miss_rate(self) -> float:
        return 1.0 - self.hit_rate


class StandardCache:
    """
    Standard CPU cache with full path tracking.
    Tracks: which core, which line, access order, MESI state
    """
    
    def __init__(self, size_mb: float = 8.0, line_size: int = 64, 
                 associativity: int = 16, num_cores: int = 8):
        self.size_bytes = int(size_mb * 1024 * 1024)
        self.line_size = line_size
        self.num_lines = self.size_bytes // line_size
        self.associativity = associativity
        self.num_sets = self.num_lines // associativity
        self.num_cores = num_cores
        
        # Cache structure: sets × ways
        self.sets = [[CacheLine(tag=-1) for _ in range(associativity)] 
                     for _ in range(self.num_sets)]
        
        self.lru_counter = 0
        self.stats = CacheStats()
    
    def _get_set_index(self, addr: int) -> int:
        return (addr // self.line_size) % self.num_sets
    
    def _get_tag(self, addr: int) -> int:
        return addr // (self.line_size * self.num_sets)
    
    def access(self, addr: int, core_id: int, is_write: bool = False) -> bool:
        """
        Access cache line. Returns True if hit, False if miss.
        Tracks full path information.
        """
        self.stats.total_accesses += 1
        self.stats.metadata_updates += 1  # Track every access
        
        set_idx = self._get_set_index(addr)
        tag = self._get_tag(addr)
        
        # Search for tag
        for way in range(self.associativity):
            line = self.sets[set_idx][way]
            if line.tag == tag:
                # HIT
                self.stats.hits += 1
                line.lru_counter = self.lru_counter
                line.owner_core = core_id
                line.access_history.append(core_id)
                if is_write:
                    line.state = 'M'
                    self.stats.coherence_updates += 1
                self.lru_counter += 1
                return True
        
        # MISS
        self.stats.misses += 1
        
        # Find LRU way
        lru_way = min(range(self.associativity), 
                     key=lambda w: self.sets[set_idx][w].lru_counter)
        
        # Evict if necessary
        if self.sets[set_idx][lru_way].tag != -1:
            self.stats.evictions += 1
        
        # Install new line
        self.sets[set_idx][lru_way] = CacheLine(
            tag=tag,
            state='M' if is_write else 'E',
            lru_counter=self.lru_counter,
            owner_core=core_id,
            access_history=[core_id]
        )
        
        self.lru_counter += 1
        return False


class InterferenceEraserCache:
    """
    Interference eraser cache with aggregate metrics.
    Erases: specific core_id, specific access order
    Tracks: aggregate frequency, temporal decay, spatial clustering
    """
    
    def __init__(self, size_mb: float = 2.0, line_size: int = 64,
                 associativity: int = 16, num_cores: int = 8,
                 erase_prob: float = 0.8, tau_decay: float = 0.99):
        self.size_bytes = int(size_mb * 1024 * 1024)
        self.line_size = line_size
        self.num_lines = self.size_bytes // line_size
        self.associativity = associativity
        self.num_sets = self.num_lines // associativity
        self.num_cores = num_cores
        self.erase_prob = erase_prob
        self.tau_decay = tau_decay
        
        # Cache structure: sets × ways
        self.sets = [[ErasedCacheLine(tag=-1) for _ in range(associativity)]
                     for _ in range(self.num_sets)]
        
        self.lru_counter = 0
        self.stats = CacheStats()
        
        # Spatial clustering (simple hash-based)
        self.spatial_clusters = 16
    
    def _get_set_index(self, addr: int) -> int:
        return (addr // self.line_size) % self.num_sets
    
    def _get_tag(self, addr: int) -> int:
        return addr // (self.line_size * self.num_sets)
    
    def _get_spatial_cluster(self, addr: int) -> int:
        return (addr // self.line_size) % self.spatial_clusters
    
    def access(self, addr: int, core_id: int, is_write: bool = False) -> bool:
        """
        Access cache line with interference erasure.
        With probability erase_prob, erase specific path information.
        """
        self.stats.total_accesses += 1
        
        set_idx = self._get_set_index(addr)
        tag = self._get_tag(addr)
        cluster = self._get_spatial_cluster(addr)
        
        # Search for tag
        for way in range(self.associativity):
            line = self.sets[set_idx][way]
            if line.tag == tag:
                # HIT
                self.stats.hits += 1
                
                # Interference erasure decision
                if np.random.random() < self.erase_prob:
                    # ERASE: Update aggregate metrics only, skip metadata counter bump
                    line.access_frequency += 1.0
                    line.temporal_decay *= self.tau_decay
                    line.spatial_cluster = cluster
                    # DO NOT update lru_counter here, this simulates lost path tracking
                else:
                    # TRACK: Update specific metadata (standard behavior)
                    line.lru_counter = self.lru_counter
                    self.stats.metadata_updates += 1  # Heavyweight update
                
                if is_write:
                    self.stats.coherence_updates += 1
                
                self.lru_counter += 1
                return True
        
        # MISS
        self.stats.misses += 1
        
        # Find LRU way
        lru_way = min(range(self.associativity),
                     key=lambda w: self.sets[set_idx][w].lru_counter)
        
        # Evict if necessary
        if self.sets[set_idx][lru_way].tag != -1:
            self.stats.evictions += 1
        
        # Install new line with aggregate metrics
        self.sets[set_idx][lru_way] = ErasedCacheLine(
            tag=tag,
            lru_counter=self.lru_counter,
            access_frequency=1.0,
            temporal_decay=1.0,
            spatial_cluster=cluster
        )
        
        self.lru_counter += 1
        return False
    
    def prefetch_decision(self, addr: int) -> Optional[int]:
        """
        Waveprobe-based prefetch decision.
        Uses aggregate field to decide prefetch region.
        """
        set_idx = self._get_set_index(addr)
        
        # Compute "Waveprobe response" for this set
        # W_a = sum of access frequencies in set
        total_freq = sum(
            line.access_frequency * line.temporal_decay
            for line in self.sets[set_idx]
            if line.tag != -1
        )
        
        # Prefetch if aggregate response is high
        if total_freq > 2.0:  # Threshold
            # Prefetch next spatial cluster
            cluster = self._get_spatial_cluster(addr)
            prefetch_addr = addr + (self.line_size * self.spatial_clusters)
            return prefetch_addr
        
        return None


# ============================================================================
# Workload Generators
# ============================================================================

def generate_spatial_workload(num_accesses: int = 10000, 
                              stride: int = 64,
                              num_cores: int = 8) -> List[Tuple[int, int, bool]]:
    """
    Spatial locality workload (typical array traversal).
    Use limited address range to ensure cache hits.
    """
    accesses = []
    # Limit address range to fit in cache (8MB = 131072 lines)
    addr_range = 4 * 1024 * 1024  # 4MB working set
    base_addr = 0x10000000
    
    for i in range(num_accesses):
        core_id = i % num_cores
        addr = base_addr + (i * stride) % addr_range
        is_write = (i % 10 == 0)  # 10% writes
        accesses.append((addr, core_id, is_write))
    
    return accesses


def generate_random_workload(num_accesses: int = 10000,
                             addr_range: int = 1024 * 1024,
                             num_cores: int = 8) -> List[Tuple[int, int, bool]]:
    """
    Random access workload (using Zipf to ensure temporal locality where LRU matters).
    """
    accesses = []
    base_addr = 0x10000000
    
    # Generate Zipf distribution (alpha=1.5)
    # Range scaled so that roughly 2x the cache size is addressable
    num_unique_lines = (addr_range // 64) * 4
    zipf_indices = np.random.zipf(1.1, num_accesses)
    # Map high indices down to our range to keep things bounded
    zipf_indices = [min(idx, num_unique_lines - 1) for idx in zipf_indices]
    
    for i in range(num_accesses):
        core_id = i % num_cores
        addr = base_addr + (zipf_indices[i] * 64)
        is_write = (i % 10 == 0)
        accesses.append((addr, core_id, is_write))
    
    return accesses


def generate_burst_workload(num_accesses: int = 10000,
                            burst_size: int = 100,
                            num_cores: int = 8) -> List[Tuple[int, int, bool]]:
    """
    Bursty workload (temporal locality).
    """
    accesses = []
    base_addr = 0x10000000
    num_bursts = num_accesses // burst_size
    
    for burst in range(num_bursts):
        core_id = burst % num_cores
        addr = base_addr + (burst * 64)
        
        for i in range(burst_size):
            is_write = (i % 10 == 0)
            accesses.append((addr + (i * 64), core_id, is_write))
    
    return accesses


def generate_multicore_workload(num_accesses: int = 10000,
                                shared_regions: int = 4,
                                num_cores: int = 8) -> List[Tuple[int, int, bool]]:
    """
    Multi-core workload with shared memory regions.
    """
    accesses = []
    region_size = 64 * 1024  # 64KB per region
    
    for i in range(num_accesses):
        core_id = i % num_cores
        region = i % shared_regions
        offset = np.random.randint(0, region_size)
        addr = 0x10000000 + (region * region_size) + offset
        is_write = (i % 5 == 0)  # 20% writes for shared regions
        accesses.append((addr, core_id, is_write))
    
    return accesses


# ============================================================================
# Benchmark Runner
# ============================================================================

@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""
    cache_type: str
    erase_prob: float
    workload_type: str
    hit_rate: float
    miss_rate: float
    metadata_updates: int
    coherence_updates: int
    total_accesses: int
    elapsed_time: float
    
    @property
    def metadata_overhead(self) -> float:
        return self.metadata_updates / self.total_accesses


def run_benchmark(cache, accesses: List[Tuple[int, int, bool]]) -> BenchmarkResult:
    """
    Run benchmark on cache with given workload.
    """
    start_time = time.perf_counter()
    
    for addr, core_id, is_write in accesses:
        cache.access(addr, core_id, is_write)
    
    elapsed_time = time.perf_counter() - start_time
    
    return BenchmarkResult(
        cache_type=type(cache).__name__,
        erase_prob=getattr(cache, 'erase_prob', 0.0),
        workload_type='unknown',
        hit_rate=cache.stats.hit_rate,
        miss_rate=cache.stats.miss_rate,
        metadata_updates=cache.stats.metadata_updates,
        coherence_updates=cache.stats.coherence_updates,
        total_accesses=cache.stats.total_accesses,
        elapsed_time=elapsed_time
    )


def compare_caches(erase_probs: List[float] = None,
                   workload_types: List[str] = None,
                   num_accesses: int = 10000,
                   cache_size_mb: int = 8,
                   num_cores: int = 8) -> List[BenchmarkResult]:
    """
    Compare standard cache vs. interference eraser cache across erasure probabilities.
    """
    if erase_probs is None:
        erase_probs = [0.0, 0.3, 0.5, 0.7, 0.9, 1.0]
    
    if workload_types is None:
        workload_types = ['spatial', 'random', 'burst', 'multicore']
    
    results = []
    
    print(f"Running benchmarks: {len(erase_probs)} erasure probs × "
          f"{len(workload_types)} workloads = {len(erase_probs) * len(workload_types) + len(workload_types)} runs")
    print()
    
    for workload_type in workload_types:
        print(f"Workload: {workload_type}")
        
        # Generate workload
        if workload_type == 'spatial':
            accesses = generate_spatial_workload(num_accesses, num_cores=num_cores)
        elif workload_type == 'random':
            accesses = generate_random_workload(num_accesses, num_cores=num_cores)
        elif workload_type == 'burst':
            accesses = generate_burst_workload(num_accesses, num_cores=num_cores)
        elif workload_type == 'multicore':
            accesses = generate_multicore_workload(num_accesses, num_cores=num_cores)
        else:
            raise ValueError(f"Unknown workload: {workload_type}")
        
        # Standard cache (erase_prob = 0.0)
        print(f"  Standard cache (tracking)...")
        std_cache = StandardCache(size_mb=cache_size_mb, num_cores=num_cores)
        std_result = run_benchmark(std_cache, accesses)
        std_result.workload_type = workload_type
        results.append(std_result)
        print(f"    Hit rate: {std_result.hit_rate:.3f}, "
              f"Metadata overhead: {std_result.metadata_overhead:.3f}")
        
        # Interference eraser caches
        for erase_prob in erase_probs:
            print(f"  Interference eraser cache (erase_prob={erase_prob:.1f})...")
            qe_cache = InterferenceEraserCache(
                size_mb=cache_size_mb,
                num_cores=num_cores,
                erase_prob=erase_prob
            )
            qe_result = run_benchmark(qe_cache, accesses)
            qe_result.workload_type = workload_type
            results.append(qe_result)
            print(f"    Hit rate: {qe_result.hit_rate:.3f}, "
                  f"Metadata overhead: {qe_result.metadata_overhead:.3f}")
        
        print()
    
    return results


# ============================================================================
# Visualization
# ============================================================================

def plot_results(results: List[BenchmarkResult], output_file: str = None):
    """
    Plot benchmark results.
    """
    if not HAS_MATPLOTLIB or not HAS_PANDAS:
        print("Warning: matplotlib and/or pandas not available. Skipping plot.")
        return
    
    df = pd.DataFrame([r.__dict__ for r in results])
    
    # Group by workload
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    for idx, workload in enumerate(df['workload_type'].unique()):
        ax = axes[idx // 2, idx % 2]
        workload_df = df[df['workload_type'] == workload]
        
        # Plot hit rate vs erasure
        ax.plot(workload_df['erase_prob'], workload_df['hit_rate'], 
               'o-', label='Hit Rate', linewidth=2, markersize=8)
        
        # Plot metadata overhead
        ax.plot(workload_df['erase_prob'], workload_df['metadata_overhead'],
               's--', label='Metadata Overhead', linewidth=2, markersize=8)
        
        ax.set_xlabel('Erasure Probability', fontsize=12)
        ax.set_ylabel('Metric', fontsize=12)
        ax.set_title(f'{workload.capitalize()} Workload', fontsize=14)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(-0.05, 1.05)
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Plot saved to {output_file}")
    else:
        plt.show()


def print_summary(results: List[BenchmarkResult]):
    """
    Print summary of key findings.
    """
    if not HAS_PANDAS:
        print("Warning: pandas not available. Using basic summary.")
        # Basic summary without pandas
        for r in results:
            print(f"  {r.cache_type} (erase={r.erase_prob:.1f}): "
                  f"hit_rate={r.hit_rate:.3f}, metadata={r.metadata_overhead:.3f}")
        return
    
    df = pd.DataFrame([r.__dict__ for r in results])
    
    print("=" * 70)
    print("INTERFERENCE ERASER CACHE BENCHMARK SUMMARY")
    print("=" * 70)
    print()
    
    for workload in df['workload_type'].unique():
        workload_df = df[df['workload_type'] == workload]
        
        print(f"Workload: {workload}")
        
        # Find optimal erasure
        optimal_idx = workload_df['hit_rate'].idxmax()
        optimal = workload_df.loc[optimal_idx]
        standard_row = workload_df[workload_df['erase_prob'] == 0.0]
        
        if len(standard_row) == 0:
            print(f"  No standard cache data found")
            print()
            continue
            
        standard = standard_row.iloc[0]
        
        print(f"  Standard cache hit rate: {standard['hit_rate']:.3f}")
        print(f"  Optimal erasure: {optimal['erase_prob']:.1f}")
        print(f"  Optimal hit rate: {optimal['hit_rate']:.3f}")
        print(f"  Improvement: {(optimal['hit_rate'] - standard['hit_rate']) * 100:.1f}%")
        if standard['metadata_overhead'] > 0:
            print(f"  Metadata reduction: {(1 - optimal['metadata_overhead'] / standard['metadata_overhead']) * 100:.1f}%")
        print()
    
    print("=" * 70)


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Interference Eraser Cache Simulator (Tick 694)'
    )
    parser.add_argument('--erase_probs', type=float, nargs='+',
                       default=[0.0, 0.3, 0.5, 0.7, 0.9, 1.0],
                       help='Erasure probabilities to test')
    parser.add_argument('--workloads', type=str, nargs='+',
                       default=['spatial', 'random', 'burst', 'multicore'],
                       help='Workload types to test')
    parser.add_argument('--num_accesses', type=int, default=10000,
                       help='Number of memory accesses per workload')
    parser.add_argument('--cache_size', type=float, default=2.0,
                       help='Cache size in MB (smaller forces evictions)')
    parser.add_argument('--num_cores', type=int, default=8,
                       help='Number of CPU cores')
    parser.add_argument('--output_plot', type=str, default=None,
                       help='Output file for plot (PNG)')
    parser.add_argument('--output_summary', type=str, default=None,
                       help='Output file for summary (JSON)')
    
    args = parser.parse_args()
    
    print("Interference Eraser Cache Simulator")
    print("=" * 70)
    print(f"Cache size: {args.cache_size}MB")
    print(f"Cores: {args.num_cores}")
    print(f"Accesses: {args.num_accesses:,}")
    print(f"Erasure probs: {args.erase_probs}")
    print(f"Workloads: {args.workloads}")
    print("=" * 70)
    print()
    
    # Run benchmarks
    results = compare_caches(
        erase_probs=args.erase_probs,
        workload_types=args.workloads,
        num_accesses=args.num_accesses,
        cache_size_mb=args.cache_size,
        num_cores=args.num_cores
    )
    
    # Print summary
    print_summary(results)
    
    # Plot results
    if args.output_plot:
        plot_results(results, args.output_plot)
    
    # Save summary
    if args.output_summary:
        import json
        summary = [r.__dict__ for r in results]
        with open(args.output_summary, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"Summary saved to {args.output_summary}")


if __name__ == '__main__':
    main()
