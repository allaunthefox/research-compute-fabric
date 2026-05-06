#!/usr/bin/env python3
"""
bfs_bulk_verify.py
==================

General-purpose verification script for Lean 4 files using the BFS-Prover model.
Iterates through specified Lean files and queries the local Ollama instance for formal audit.
"""

import json
import requests
import argparse
from pathlib import Path
import sys

OLLAMA_HOST = "http://localhost:11434"
MODEL_NAME = "zeyu-zheng/BFS-Prover-V2-7B:q8_0"

def query_prover(prompt: str):
    url = f"{OLLAMA_HOST}/api/generate"
    payload = {
        "model": MODEL_NAME,
        "system": "You are a Lean 4 formalization expert. Your goal is to verify the mathematical integrity and formal correctness of Lean code. Check for logic errors, type mismatches, and 'sorry' obligations.",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_ctx": 16384
        }
    }

    resp = requests.post(url, json=payload, timeout=900)
    resp.raise_for_status()
    return resp.json()["response"]

def verify_file(file_path: Path):
    if not file_path.exists():
        print(f"Error: File {file_path} not found.")
        return None

    print(f"Verifying {file_path}...")
    content = file_path.read_text()

    prompt = f"""
Please verify the following Lean 4 file.
Perform a deep audit of the formal logic, type safety, and mathematical correctness.

### File: {file_path.name}
```lean
{content}
```

**Task:**
1. Identify any 'sorry' markers or incomplete proofs.
2. Check for potential logic errors or unsound axioms.
3. Verify that the fixed-point arithmetic (if present) handles overflow/underflow correctly.
4. Provide a pass/fail assessment and a list of specific improvements.

Return the audit as a markdown report.
"""
    try:
        response = query_prover(prompt)
        return response
    except Exception as e:
        print(f"Error querying prover for {file_path}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Verify Lean 4 files using BFS-Prover.")
    parser.add_argument("files", nargs="*", help="Lean files to verify. If empty, searches current directory.")
    args = parser.parse_args()

    root = Path("/home/allaun/Documents/Research Stack")
    files_to_verify = []

    if args.files:
        for f in args.files:
            files_to_verify.append(Path(f))
    else:
        # Default: verify the most recent semantic core files
        base_path = root / "0-Core-Formalism/lean/Semantics/Semantics"
        targets = [
            "FixedPoint.lean",
            "GeneticGroundUp.lean",
            "Testing/FixedPointTest.lean",
            "Testing/GeneticGroundUpTest.lean"
        ]
        for t in targets:
            files_to_verify.append(base_path / t)

    audit_dir = root / "shared-data/artifacts/audit/bulk"
    audit_dir.mkdir(parents=True, exist_ok=True)

    for f in files_to_verify:
        report = verify_file(f)
        if report:
            out_file = audit_dir / f"{f.stem}_audit.md"
            out_file.write_text(report)
            print(f"Audit report saved to: {out_file}")
            print("-" * 40)
            # Print a snippet of the report
            first_lines = "\n".join(report.splitlines()[:5])
            print(f"Snippet:\n{first_lines}\n...")
            print("-" * 40)

if __name__ == "__main__":
    main()
