#!/usr/bin/env python3
"""
Bidirectional Lean 4 Shim for GCL Compression & Metaprobe Evaluation.
Ingests JSONL preprocessed topology, compresses via Delta GCL,
and interfaces with the Lean 4 unified shim for formal validation and metaprobe signatures.
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "4-Infrastructure"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "0-Core-Formalism"))

from infra.delta_gcl_compression_service import compress_metadata, get_compression_service
from infra.lean_unified_shim import LeanUnifiedShim

def run_pipeline(input_path: str, output_path: str):
    print("Initializing Bidirectional Lean 4 Shim...")
    if not os.path.exists(input_path):
        print(f"[ERROR] Input file {input_path} not found.")
        return

    shim = LeanUnifiedShim()
    service = get_compression_service()
    
    with open(input_path, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    print(f"Loaded {len(lines)} preprocessed equations.")
    results = []

    for idx, line in enumerate(lines):
        try:
            data = json.loads(line)
            eq_name = data.get("Model_Name", f"Eq_{idx}")
            family = data.get("Family", "General")
            connections = data.get("connections", {})

            # 1. Delta GCL Compression
            # Formulate manifest
            manifest = {
                "layer": "CORE",
                "domain": family,
                "tier": "FOAM",
                "condition": "STABLE",
                "metadata": connections
            }

            # Compress using Delta GCL
            comp_result = compress_metadata(manifest, manifest_id=eq_name, use_delta=True, verify=True)
            
            # 2. Metaprobe & Lean 4 Bidirectional Routing
            # We route the compressed state into the Swarm / Domain for formal checks
            try:
                # Querying the DomainModelIntegration via Lean unified shim to validate structural consistency
                query_payload = f"METAPROBE_VALIDATE: {eq_name} | {comp_result.delta_gcl}"
                lean_response = shim.query_domain(domain=family, query=query_payload)
                metaprobe_verdict = lean_response.get("status", "admit")
            except Exception as e:
                # Fallback if specific domain isn't fully registered in Lean yet
                metaprobe_verdict = "holdReview (Shim Exception)"

            print(f"[{idx+1}/{len(lines)}] {eq_name}")
            print(f"  -> GCL Reduction: {comp_result.stats['reduction_percent']:.1f}%")
            print(f"  -> Metaprobe Verdict: {metaprobe_verdict}")

            results.append({
                "Model_Name": eq_name,
                "Family": family,
                "Delta_GCL": comp_result.delta_gcl,
                "Compression_Stats": comp_result.stats,
                "Metaprobe_Verdict": metaprobe_verdict,
                "Timestamp": data.get("timestamp")
            })

        except json.JSONDecodeError:
            print(f"Skipping invalid JSON at line {idx+1}")

    # Output compressed results
    with open(output_path, 'w') as f:
        for res in results:
            f.write(json.dumps(res) + "\n")

    # Overall stats
    stats = service.get_stats()
    print("="*60)
    print("SHIM PIPELINE COMPLETE")
    print(f"Total Equations Processed: {stats.total_compressions}")
    print(f"Average GCL Reduction: {stats.avg_reduction_percent:.2f}%")
    print(f"Output saved to: {output_path}")
    print("="*60)

if __name__ == "__main__":
    input_jsonl = "/home/allaun/Documents/Research Stack/artifacts/preprocessed_equation_connections.jsonl"
    output_jsonl = "/home/allaun/Documents/Research Stack/artifacts/gcl_compressed_metaprobe.jsonl"
    run_pipeline(input_jsonl, output_jsonl)
