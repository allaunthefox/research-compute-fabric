#!/usr/bin/env python3
"""
project_general_review.py
=========================

Performs a general architectural and code quality review of the Research Stack
using the 'default' local Ollama model.
"""

import json
import requests
from pathlib import Path

OLLAMA_HOST = "http://localhost:11434"
MODEL_NAME = "default"

def query_model(prompt: str):
    url = f"{OLLAMA_HOST}/api/generate"
    payload = {
        "model": MODEL_NAME,
        "system": "You are a senior software architect and formal methods expert. Your goal is to review the Sovereign Research Stack and provide strategic feedback on architecture, code quality, and alignment with the project's vision of 'One Truth Only'.",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_ctx": 32768
        }
    }

    resp = requests.post(url, json=payload, timeout=1200)
    resp.raise_for_status()
    return resp.json()["response"]

def main():
    root = Path("/home/allaun/Documents/Research Stack")
    project_map = (root / "PROJECT_MAP.md").read_text()

    # Core semantic files
    core_files = [
        "0-Core-Formalism/lean/Semantics/Semantics/FixedPoint.lean",
        "0-Core-Formalism/lean/Semantics/Semantics/GeneticGroundUp.lean",
        "0-Core-Formalism/lean/Semantics/Semantics/Testing/FixedPointTest.lean",
        "0-Core-Formalism/lean/Semantics/Semantics/Testing/GeneticGroundUpTest.lean"
    ]

    file_contents = ""
    for f in core_files:
        p = root / f
        if p.exists():
            file_contents += f"\n--- FILE: {f} ---\n"
            file_contents += p.read_text()
            file_contents += "\n"

    prompt = f"""
You are reviewing the Sovereign Research Stack.
The project aims for a 'One Truth Only' model (OTOM) where Lean 4 is the canonical truth.

### PROJECT MAP
{project_map}

### CORE SEMANTIC MODULES
{file_contents}

**Review Task:**
1. **Architectural Alignment**: Does the Q16.16 arithmetic core and the Genetic Ground Up redesign align with the project goals?
2. **Code Quality**: Evaluate the Lean 4 implementations. Are they idiomatic? Are the proofs robust?
3. **Consistency**: Is there consistency between the arithmetic substrate (FixedPoint) and the higher-level genetic semantics?
4. **Strategic Risks**: Identify any "deceptively simple" areas that might hide future complexity or unsoundness.
5. **Recommendations**: Suggest next steps for formalizing the "Sharded Genome" or the "Metabolic GNN".

Provide a comprehensive review report.
"""

    print(f"Querying {MODEL_NAME} for project review...")
    try:
        response = query_model(prompt)

        print("\n" + "="*80)
        print("SOVEREIGN RESEARCH STACK - ARCHITECTURAL REVIEW")
        print("="*80)
        print(response)
        print("="*80)

        # Save to artifact
        out_dir = root / "shared-data/artifacts/review"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "project_architectural_review.md"
        out_file.write_text(response)
        print(f"\nReview saved to: {out_file}")

    except Exception as e:
        print(f"Error during review: {e}")

if __name__ == "__main__":
    main()
