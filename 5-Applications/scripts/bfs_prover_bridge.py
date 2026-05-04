#!/usr/bin/env python3
"""
bfs_prover_bridge.py
====================

Bridge to the local 'bfs-prover-v2-32b' model for Lean 4 formal verification.
Sends current Burgers formalization for audit.
"""

import json
import requests
from pathlib import Path

OLLAMA_HOST = "http://localhost:11435"
MODEL_NAME = "llama3.1:8b"

def query_prover(prompt: str):
    url = f"{OLLAMA_HOST}/api/generate"
    payload = {
        "model": MODEL_NAME,
        "system": "You are a Lean 4 formalization expert and PDE auditor. Your goal is to verify the mathematical integrity of Lean code and its AVM (Adaptive Virtual Machine) implementations.",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_ctx": 8192
        }
    }
    
    print(f"Connecting to {MODEL_NAME} at {OLLAMA_HOST} (Timeout: 600s)...")
    resp = requests.post(url, json=payload, timeout=600)
    resp.raise_for_status()
    return resp.json()["response"]

def main():
    root = Path("/home/allaun/Documents/Research Stack")
    trace_file = root / "shared-data/burgers_avm_gold_traces.json"
    manifest_file = root / "shared-data/burgers_avm_trace_manifest.json"
    
    trace_content = trace_file.read_text()
    manifest_content = manifest_file.read_text()

    prompt = f"""
You are auditing a formal hardware loopback manifest and golden trace set for Burgers AVM Q16.16 kernels.

### Manifest
{manifest_content}

### Golden Traces
{trace_content}

**Task:**
Audit the AVM golden trace JSON for deterministic replay on FPGA. 
1. Check stack shape, PC monotonicity, instruction/result consistency, and Q16.16 representation.
2. Verify whether any float value is being used as an authority rather than debug metadata.
3. Check whether the manifest contains enough provenance to connect Lean theorem targets, Python trace generation, Q16.16 arithmetic policy, and UART hardware replay.

Return a list of pass/fail checks, missing metadata fields, ambiguous claims, or claim-boundary problems.
Do not validate the mathematics.
"""

    print("Querying Auditor (deepseek-r1:8b)...")
    response = query_prover(prompt)
    
    print("\n" + "="*80)
    print("AVM TRACE AUDIT REPORT")
    print("="*80)
    print(response)
    print("="*80)

    # Save to artifact
    out_dir = root / "shared-data/artifacts/audit"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "burgers_avm_trace_audit.md"
    out_file.write_text(response)
    print(f"\nAudit saved to: {out_file}")

if __name__ == "__main__":
    main()
