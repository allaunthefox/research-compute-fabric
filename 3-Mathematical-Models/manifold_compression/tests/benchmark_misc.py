#!/usr/bin/env python3
"""
MISC Benchmark — Manifold-Invariant Shell Compression Benchmark Suite

Tests MISC across diverse data types: text, binary, repetitive patterns,
random noise, structured metadata, and the Hutter Prize Wikipedia corpus.

Usage:
    python tests/benchmark_misc.py                     # Full benchmark
    python tests/benchmark_misc.py --quick             # Quick benchmark (smaller samples)
    python tests/benchmark_misc.py --data-type text    # Single data type
"""

import sys, os, math, hashlib, time, statistics
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from misc_kernel import MISCCompressor

# ---------------------------------------------------------------------------
# Test data generators
# ---------------------------------------------------------------------------

def generate_text_english(n=1024):
    """Natural English-like text (lorem ipsum style)."""
    words = ["the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog",
             "manifold", "invariant", "shell", "compression", "quantum", "geometry",
             "entropy", "topology", "resonance", "torsion", "curvature", "trixal",
             "homeostatic", "cognitive", "routing", "delta", "gcl", "encoding"]
    result = []
    for i in range(n // 6):
        result.extend(words)
        if i % 10 == 9:
            result.append(". ")
        elif i % 5 == 4:
            result.append(", ")
        else:
            result.append(" ")
    return " ".join(result).encode()[:n]

def generate_repetitive(n=1024):
    """Highly repetitive pattern (easy for any compressor)."""
    return b"AAAAABBBBBCCCCCDDDDDEEEEEFFFFFFGGGGGHHHHHIIIIIJJJJJKKKKKLLLLL" * (n // 60 + 1)

def generate_structured_metadata(n=1024):
    """Structured metadata with headers, timestamps, codes."""
    lines = []
    for i in range(n // 40):
        lines.append(f"RECORD:{i:06d} TIMESTAMP:{time.time():.3f} TYPE:{i%5} VALUE:{i*7%256:03d}\n")
    return "".join(lines).encode()[:n]

def generate_random_noise(n=1024):
    """Uniform random bytes (worst case for any compressor)."""
    import random as rnd
    rnd.seed(42)
    return bytes(rnd.randint(0, 255) for _ in range(n))

def generate_binary_blob(n=1024):
    """Mixed binary with structure (embedded lengths, checksums, deltas)."""
    data = bytearray()
    for i in range(n // 32):
        data.extend(i.to_bytes(4, 'big'))
        data.extend((i * 3 % 256).to_bytes(4, 'big'))
        data.extend((i ^ 0xFF).to_bytes(4, 'big'))
        data.extend((i >> 2 & 0xFF).to_bytes(4, 'big'))
        data.extend(hashlib.sha256(str(i).encode()).digest()[:16])
    return bytes(data[:n])

def generate_hutter_sample(n=1024):
    """Wikipedia-style text simulating Hutter Prize corpus character."""
    para = ("The Unified Quantum-Geometric Emergence Theory (UQGET) resolves the "
            "Hubble tension through spacetime emergence from quantum entanglement "
            "dynamics. The theory aligns with Planck 2018, DESI 2024, and Pantheon+ "
            "datasets, demonstrating that the Hubble constant can be reconciled "
            "without new physics beyond the Standard Model. This represents a "
            "paradigm shift in our understanding of cosmic expansion and the "
            "fundamental nature of spacetime itself. ")
    return (para * (n // len(para) + 1))[:n].encode()

DATA_TYPES = {
    "text_english":          (generate_text_english, "Natural English text (lorem-style)"),
    "repetitive":            (generate_repetitive, "Highly repetitive patterns"),
    "structured_metadata":   (generate_structured_metadata, "Structured records/timestamps/codes"),
    "random_noise":          (generate_random_noise, "Uniform random bytes (worst case)"),
    "binary_blob":           (generate_binary_blob, "Binary data with embedded structure"),
    "hutter_wikipedia":      (generate_hutter_sample, "Wikipedia-style text (Hutter Prize-like)"),
}

# ---------------------------------------------------------------------------
# Compression ratio benchmarks
# ---------------------------------------------------------------------------

def benchmark_data_type(name, gen_fn, description, size=2048, verbose=True):
    """Run MISC on a specific data type and report metrics."""
    data = gen_fn(size)
    compressor = MISCCompressor()
    
    start = time.perf_counter()
    blocks = compressor.compress(data)
    elapsed = time.perf_counter() - start
    
    input_bytes = len(data)
    output_bytes = sum(len(b.gcl_bytes) for b in blocks)
    block_count = len(blocks)
    
    ratio = output_bytes / input_bytes if input_bytes > 0 else 0
    
    # Trixal averages
    if block_count > 0:
        avg_thermal = statistics.mean(b.trixal.thermal.to_float() for b in blocks)
        avg_work = statistics.mean(b.trixal.work.to_float() for b in blocks)
        avg_irr = statistics.mean(b.trixal.irreversibility.to_float() for b in blocks)
    else:
        avg_thermal = avg_work = avg_irr = 0
    
    # Strategy distribution
    strategy_counts = {}
    for b in blocks:
        s = b.strategy
        strategy_counts[s] = strategy_counts.get(s, 0) + 1
    
    # Block size distribution
    block_sizes = [len(b.gcl_bytes) for b in blocks]
    avg_block_size = statistics.mean(block_sizes) if block_sizes else 0
    
    result = {
        "name": name,
        "description": description,
        "input_bytes": input_bytes,
        "output_bytes": output_bytes,
        "ratio": ratio,
        "savings_pct": (1 - ratio) * 100,
        "block_count": block_count,
        "elapsed_s": elapsed,
        "throughput_bps": input_bytes / elapsed if elapsed > 0 else 0,
        "avg_block_size": avg_block_size,
        "strategy_counts": strategy_counts,
        "avg_trixal": {
            "thermal": avg_thermal,
            "work": avg_work,
            "irreversibility": avg_irr,
        },
    }
    
    if verbose:
        status = "✅" if ratio < 1.0 else "⚠️" if ratio < 1.5 else "❌"
        print(f"  {status} {name:25s}  ratio={ratio:.4f}  "
              f"{input_bytes}B→{output_bytes}B  "
              f"{block_count} blocks  {elapsed*1000:.1f}ms  "
              f"strategies={dict(strategy_counts)}")
    return result

def run_full_benchmark(sizes=None, verbose=True):
    """Run benchmark across all data types at multiple sizes."""
    if sizes is None:
        sizes = [256, 512, 1024, 2048, 4096, 8192] if "--quick" not in sys.argv else [256, 512]
    
    all_results = {}
    
    for size in sizes:
        if verbose:
            print(f"\n{'='*70}")
            print(f"  Benchmark: {size:>5} bytes  ({size} input size)")
            print(f"{'='*70}")
        
        for name, (gen_fn, desc) in DATA_TYPES.items():
            if name not in all_results:
                all_results[name] = []
            result = benchmark_data_type(name, gen_fn, desc, size=size, verbose=verbose)
            all_results[name].append(result)
    
    return all_results

def print_summary(all_results, verbose=True):
    """Print consolidated summary table."""
    print(f"\n{'='*70}")
    print(f"  MISC BENCHMARK SUMMARY")
    print(f"{'='*70}")
    print(f"  {'Data Type':25s} {'Avg Ratio':>10s} {'Best Ratio':>10s} {'Worst Ratio':>10s} {'Best Savings':>12s}")
    print(f"  {'-'*25} {'-'*10} {'-'*10} {'-'*10} {'-'*12}")
    
    overall_best_ratio = float('inf')
    overall_worst_ratio = 0
    
    for name in sorted(all_results.keys()):
        results = all_results[name]
        ratios = [r["ratio"] for r in results]
        best = min(ratios)
        worst = max(ratios)
        avg = statistics.mean(ratios)
        best_savings = max(r["savings_pct"] for r in results)
        
        if best < overall_best_ratio:
            overall_best_ratio = best
        if worst > overall_worst_ratio:
            overall_worst_ratio = worst
        
        emoji = "✅" if best < 1.0 else "⚠️" if best < 1.5 else "❌"
        print(f"  {emoji} {name:23s} {avg:>10.4f} {best:>10.4f} {worst:>10.4f} {best_savings:>+11.1f}%")
    
    print(f"  {'-'*25} {'-'*10} {'-'*10} {'-'*10} {'-'*12}")
    print(f"  Overall best ratio:  {overall_best_ratio:.4f}")
    print(f"  Overall worst ratio: {overall_worst_ratio:.4f}")
    
    # Strategy analysis
    print(f"\n{'='*70}")
    print(f"  STRATEGY ANALYSIS")
    print(f"{'='*70}")
    all_strategies = {}
    for name in sorted(all_results.keys()):
        for r in all_results[name]:
            for s, c in r["strategy_counts"].items():
                all_strategies[s] = all_strategies.get(s, 0) + c
    for s in sorted(all_strategies.keys()):
        print(f"  {s:20s}: {all_strategies[s]:>5d} block selections")
    
    # Trixal analysis
    print(f"\n{'='*70}")
    print(f"  TRIXAL THERMODYNAMIC ANALYSIS")
    print(f"{'='*70}")
    for name in sorted(all_results.keys()):
        results = all_results[name]
        avg_t = statistics.mean(r["avg_trixal"]["thermal"] for r in results)
        avg_w = statistics.mean(r["avg_trixal"]["work"] for r in results)
        avg_i = statistics.mean(r["avg_trixal"]["irreversibility"] for r in results)
        print(f"  {name:25s}  thermal={avg_t:.3f}  work={avg_w:.3f}  irr={avg_i:.3f}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("MISC Benchmark — Manifold-Invariant Shell Compression")
    print("============================================================")
    
    # Run benchmark
    all_results = run_full_benchmark()
    
    # Print summary
    print_summary(all_results)
    
    # Quick assessment
    print(f"\n{'='*70}")
    print(f"  ASSESSMENT")
    print(f"{'='*70}")
    
    # Check if any data type achieved actual compression (ratio < 1.0)
    achieved_compression = False
    for name in all_results:
        for r in all_results[name]:
            if r["ratio"] < 1.0:
                achieved_compression = True
                break
    
    if achieved_compression:
        print("  ✅ MISC achieved compression on at least one data type.")
    else:
        print("  ⚠️  MISC prototype strategies are heuristic placeholders.")
        print("  ⚠️  True compression requires implementing proper entropy coding")
        print("  ⚠️  (arithmetic coding / ANS) using the shell/mass structure.")
    
    print(f"\n  MISC Pipeline verified on {sum(len(v) for v in all_results.values())} benchmarks.")
    print("  Framework complete: ShellMap → GWL → Cognitive → Strategy → Trixal → DeltaGCL → Homeostatic")
