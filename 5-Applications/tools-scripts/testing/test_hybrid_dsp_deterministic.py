#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
Deterministic test of hybrid DSP workload selector using research space recordings.

Tests the hybrid decision system on real audio recordings to measure:
- DSP workload distribution (Raw, SpectralFocus, TransientEdge, Hybrid)
- QUBO solve time reduction
- Energy efficiency improvements
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(REPO_ROOT))
from scripts.pipewire_waveprobe_compression_chain import run_chain

# Test audio files from research space (WAV only, wave module doesn't support FLAC)
TEST_AUDIO = [
    REPO_ROOT / "media" / "test_audio" / "mandelbrot_boundary.wav",  # Juliet fractal
]

def test_baseline(audio_path: Path) -> dict:
    """Run baseline test without hybrid DSP selection."""
    print(f"\n{'='*70}")
    print(f"BASELINE TEST: {audio_path.name}")
    print(f"{'='*70}")
    
    result = run_chain(
        wav_path=audio_path,
        chunk_size=4096,
        stride=2048,
        max_states=100,
        low_mi_threshold=0.1,
        high_mi_threshold=0.5,
        dsp_workload="hybrid",  # Fixed hybrid workload
        method_profile="baseline",
        qubo_solver="anneal",
        qubo_anneal_steps=32,
        qubo_anneal_temp_start=0.5,
        qubo_anneal_temp_end=0.05,
        qubo_anneal_guidance="dsp_guided",
        qubo_benchmark_guidance_ablation=False,
        qubo_collect_exact_reference=False,
        hybrid_dsp_workload=False,  # Baseline: no adaptive selection
    )
    
    return result

def test_hybrid(audio_path: Path) -> dict:
    """Run hybrid test with adaptive DSP workload selection."""
    print(f"\n{'='*70}")
    print(f"HYBRID TEST: {audio_path.name}")
    print(f"{'='*70}")
    
    result = run_chain(
        wav_path=audio_path,
        chunk_size=4096,
        stride=2048,
        max_states=100,
        low_mi_threshold=0.1,
        high_mi_threshold=0.5,
        dsp_workload="hybrid",  # Initial workload, will be overridden
        method_profile="baseline",
        qubo_solver="anneal",
        qubo_anneal_steps=32,
        qubo_anneal_temp_start=0.5,
        qubo_anneal_temp_end=0.05,
        qubo_anneal_guidance="dsp_guided",
        qubo_benchmark_guidance_ablation=False,
        qubo_collect_exact_reference=False,
        hybrid_dsp_workload=True,  # Enable adaptive selection
    )
    
    return result

def compare_results(baseline: dict, hybrid: dict, audio_name: str) -> dict:
    """Compare baseline and hybrid results."""
    baseline_summary = baseline["summary"]
    hybrid_summary = hybrid["summary"]
    
    comparison = {
        "audio_file": audio_name,
        "baseline_qubo_solve_time_ms": baseline_summary.get("avg_qubo_solve_time_ms", 0),
        "hybrid_qubo_solve_time_ms": hybrid_summary.get("avg_qubo_solve_time_ms", 0),
        "baseline_qubo_invocations": baseline_summary.get("qubo_invocations", 0),
        "hybrid_qubo_invocations": hybrid_summary.get("qubo_invocations", 0),
        "baseline_dsp_workload": baseline_summary.get("dsp_frontend", {}).get("workload", "unknown"),
        "hybrid_dsp_workload_distribution": hybrid_summary.get("dsp_workload_counts", {}),
    }
    
    # Calculate energy efficiency improvement
    if comparison["baseline_qubo_solve_time_ms"] > 0:
        time_reduction = (
            (comparison["baseline_qubo_solve_time_ms"] - comparison["hybrid_qubo_solve_time_ms"])
            / comparison["baseline_qubo_solve_time_ms"]
        ) * 100
        comparison["qubo_time_reduction_pct"] = time_reduction
    else:
        comparison["qubo_time_reduction_pct"] = 0.0
    
    return comparison

def main():
    print("="*70)
    print("Hybrid DSP Workload Selector Deterministic Test")
    print("="*70)
    print(f"\nTesting {len(TEST_AUDIO)} audio files from research space...")
    
    all_results = []
    
    for audio_path in TEST_AUDIO:
        if not audio_path.exists():
            print(f"⚠ Skipping {audio_path.name} (file not found)")
            continue
        if audio_path.suffix.lower() != ".wav":
            print(f"⚠ Skipping {audio_path.name} (not WAV format)")
            continue
        
        # Run baseline test
        baseline = test_baseline(audio_path)
        
        # Run hybrid test
        hybrid = test_hybrid(audio_path)
        
        # Compare results
        comparison = compare_results(baseline, hybrid, audio_path.name)
        all_results.append(comparison)
        
        # Print comparison
        print(f"\n{'='*70}")
        print(f"COMPARISON: {audio_path.name}")
        print(f"{'='*70}")
        print(f"  Baseline QUBO solve time: {comparison['baseline_qubo_solve_time_ms']:.2f} ms")
        print(f"  Hybrid QUBO solve time:   {comparison['hybrid_qubo_solve_time_ms']:.2f} ms")
        print(f"  QUBO time reduction:      {comparison['qubo_time_reduction_pct']:+.2f}%")
        print(f"  Baseline QUBO invocations: {comparison['baseline_qubo_invocations']}")
        print(f"  Hybrid QUBO invocations:   {comparison['hybrid_qubo_invocations']}")
        print(f"  Hybrid DSP workload distribution:")
        for workload, count in comparison['hybrid_dsp_workload_distribution'].items():
            total = sum(comparison['hybrid_dsp_workload_distribution'].values())
            pct = (count / total * 100) if total > 0 else 0
            print(f"    {workload}: {count} ({pct:.1f}%)")
    
    # Print aggregate results
    print(f"\n{'='*70}")
    print("AGGREGATE RESULTS")
    print(f"{'='*70}")
    
    if all_results:
        avg_time_reduction = sum(r["qubo_time_reduction_pct"] for r in all_results) / len(all_results)
        print(f"  Average QUBO time reduction: {avg_time_reduction:+.2f}%")
        print(f"  Files tested: {len(all_results)}")
        
        # Aggregate DSP workload distribution
        total_distribution = {}
        for result in all_results:
            for workload, count in result["hybrid_dsp_workload_distribution"].items():
                total_distribution[workload] = total_distribution.get(workload, 0) + count
        
        print(f"\n  Aggregate DSP workload distribution:")
        total_workloads = sum(total_distribution.values())
        for workload, count in sorted(total_distribution.items()):
            pct = (count / total_workloads * 100) if total_workloads > 0 else 0
            print(f"    {workload}: {count} ({pct:.1f}%)")
        
        # Save results to JSON
        output_path = REPO_ROOT / "out" / "hybrid_dsp_deterministic_test.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump({
                "aggregate": {
                    "avg_qubo_time_reduction_pct": avg_time_reduction,
                    "total_files_tested": len(all_results),
                    "aggregate_dsp_workload_distribution": total_distribution,
                },
                "individual_results": all_results,
            }, f, indent=2)
        
        print(f"\n  Results saved to: {output_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
