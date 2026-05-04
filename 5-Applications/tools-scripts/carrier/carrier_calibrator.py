#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Carrier state Calibrator — Establishes structural 'ground truth' baseline vectors.

This utility fetches a 'Gold Standard' contract via RPC, runs the waveprobe,
and computes the aggregate mean response direction (8-dimensional Phi-space)
to serve as the Carrier state Baseline for Torsion measurements.

Example:
    python3 5-Applications/scripts/carrier state_calibrator.py 0x7a2d0d5... --chain ethereum --output 4-Infrastructure/config/carrier state_baseline.json
"""

import argparse
import json
import os
import sys
from typing import List

try:
    from scripts.rpc_bytecode_fetcher import RPCBytecodeFetcher
    from scripts.evm_bytecode_waveprobe import EVMBytecodeWaveprobe, EVMWaveprobeResult
except ModuleNotFoundError:
    # Handle direct execution from 5-Applications/scripts/ directory
    from pathlib import Path
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from rpc_bytecode_fetcher import RPCBytecodeFetcher  # type: ignore
    from evm_bytecode_waveprobe import EVMBytecodeWaveprobe, EVMWaveprobeResult  # type: ignore

def calibrate(address: str, chain: str = "ethereum", config_path: str = "4-Infrastructure/config/rpc_endpoints.json") -> List[float]:
    """Fetch bytecode and compute the aggregate mean response vector."""
    fetcher = RPCBytecodeFetcher(config_path=config_path)
    
    print(f"[*] Fetching bytecode for {address} on {chain}...")
    bytecode = fetcher.fetch_bytecode(address, chain)
    
    if not bytecode or bytecode == "0x":
        print(f"[!] Error: Could not retrieve bytecode for {address}. Ensure RPC is up and address is a contract.")
        sys.exit(1)
        
    print(f"[*] Analyzing structural grain (GraphVM Waveprobe)...")
    probe = EVMBytecodeWaveprobe(bytecode_hex=bytecode)
    result: EVMWaveprobeResult = probe.analyze()
    
    # Feature dimension is 8 (Phi-space)
    dim = 8
    aggregate_vec = [0.0] * dim
    
    # We compute the average mean_response_direction across all significant chunks
    # Significant chunks = those with non-zero heat (actual code, not padding)
    valid_chunks = [c for c in result.chunks if c.heat > 0.05]
    
    if not valid_chunks:
        print("[!] Warning: No high-heat chunks found. Falling back to all chunks.")
        valid_chunks = result.chunks
        
    for chunk in valid_chunks:
        for i in range(dim):
            aggregate_vec[i] += chunk.base_features[i]
            
    # Normalize the average vector
    m = len(valid_chunks)
    if m > 0:
        aggregate_vec = [v / m for v in aggregate_vec]
        
    return aggregate_vec

def main():
    parser = argparse.ArgumentParser(description="Carrier state Drift Calibrator")
    parser.add_argument("address", help="Contract address to calibrate against (e.g. Uniswap V2 Router)")
    parser.add_argument("--chain", default="ethereum", help="Chain handle (ethereum, base, etc.)")
    parser.add_argument("--output", default="4-Infrastructure/config/carrier state_baseline.json", help="Path to save result")
    parser.add_argument("--rpc-config", default="4-Infrastructure/config/rpc_endpoints.json", help="Path to rpc_endpoints.json")
    
    args = parser.parse_args()
    
    baseline_vec = calibrate(args.address, chain=args.chain, config_path=args.rpc_config)
    
    result_data = {
        "calibration_anchor": args.address,
        "chain": args.chain,
        "feature_dim": len(baseline_vec),
        "carrier state_baseline_vector": baseline_vec,
        "metadata": {
            "version": "1.0.0",
            "algorithm": "GraphVM Phi-space Mean Response Direction",
            "canonical_role": "Carrier state Ground Truth"
        }
    }
    
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2)
        
    print(f"[+] Calibration complete. Baseline saved to {args.output}")
    print(f"Baseline Vector: {['{:.4f}'.format(v) for v in baseline_vec]}")

if __name__ == "__main__":
    main()
