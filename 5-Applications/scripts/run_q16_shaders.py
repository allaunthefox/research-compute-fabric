#!/usr/bin/env python3
"""Run all Q16_16 GPU verification shaders in parallel."""
import subprocess
import sys
import os
import json
from pathlib import Path

# Note: WGSL shaders require a WebGPU runtime (wgpu, wgpu-native, etc.)
# This script is a placeholder for the actual shader execution infrastructure
# For now, we'll use the existing PyTorch-based verification

def main():
    print("Running Q16_16 GPU verification in parallel...")
    
    # Run the existing PyTorch-based verification
    result = subprocess.run(
        [sys.executable, "5-Applications/scripts/gpu_q16_verification.py"],
        cwd="/home/allaun/Research Stack",
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    # Load and display results
    try:
        with open('/home/allaun/Documents/Research Stack/out/q16_gpu_verification.json', 'r') as f:
            results = json.load(f)
        print("\n=== GPU Verification Results ===")
        for name, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{name}: {status}")
        
        all_passed = all(results.values())
        print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
        
        # Note: WGSL shaders are ready but require WebGPU runtime setup
        print("\n=== WGSL Shaders Status ===")
        print("4 WGSL compute shaders created:")
        print("  - q16_bitlevel_verify.wgsl (shift & toInt/val)")
        print("  - q16_comparison_verify.wgsl (monotonicity)")
        print("  - q16_arithmetic_verify.wgsl (mul/div/neg/abs)")
        print("  - q16_minmax_verify.wgsl (min/max theorems)")
        print("\nWGSL shaders require WebGPU runtime (wgpu-native) for execution.")
        print("Current verification uses PyTorch CUDA backend.")
        
        return 0 if all_passed else 1
    except Exception as e:
        print(f"Error loading results: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
