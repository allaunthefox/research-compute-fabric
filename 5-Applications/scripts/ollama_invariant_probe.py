#!/usr/bin/env python3
"""
Ollama Cloud Invariant Probe
Feed distilled self-discovered math structures to an LLM and ask it to extract invariants.
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime

import pyarrow.parquet as pq
from ollama import Client

BASE = Path("/home/allaun/Documents/Research Stack/3-Mathematical-Models")
PARQUET = BASE / "equations_parquet_tagged/equations_self_clustered.parquet"
REPORT = BASE / "math_self_discovered.json"
OUTDIR = BASE / "invariant_probes"
OUTDIR.mkdir(parents=True, exist_ok=True)

def load_top_motifs(n=200):
    with open(REPORT) as f:
        data = json.load(f)
    return data['top_motifs'][:n], data['total_equations'], data['unique_structural_forms']

def sample_representatives(fingerprint, n=3):
    """Grab n original equations matching a fingerprint from the parquet."""
    table = pq.read_table(PARQUET, columns=['equation', 'fingerprint'])
    # Filter in Python (parquet doesn't do string equality pushdown well)
    eqs = []
    for eq, fp in zip(table.column('equation').to_pylist(), table.column('fingerprint').to_pylist()):
        if fp == fingerprint:
            eqs.append(eq)
            if len(eqs) >= n:
                break
    return eqs

def build_prompt(motifs, total_eq, unique_forms):
    lines = []
    lines.append("You are a mathematical structural analyst. I have run an unsupervised structural discovery pipeline on 1.51 million mathematical equations stripped of all human categorization.")
    lines.append("")
    lines.append("The pipeline canonicalized each equation to a 'structural fingerprint' by:")
    lines.append("  - Anonymizing variables (single letters → v0, v1...; multi-letter → vN)")
    lines.append("  - Collapsing all numbers to N")
    lines.append("  - Replacing Greek letters with g0, g1...")
    lines.append("  - Preserving math functions (sin, cos, exp, log, etc.)")
    lines.append("  - Normalizing whitespace")
    lines.append("")
    lines.append(f"RESULTS: {total_eq:,} equations → {unique_forms:,} unique structural forms")
    lines.append("Top 50 structural motifs (fingerprint → count → % of total):")
    lines.append("")

    for m in motifs[:50]:
        lines.append(f"  {m['count']:>7,}  ({m['percentage']:>5.2f}%)  {m['fingerprint']}")

    lines.append("")
    lines.append("Here are representative ORIGINAL equations for the top 10 motifs:")
    lines.append("")

    for m in motifs[:10]:
        fp = m['fingerprint']
        reps = sample_representatives(fp, n=3)
        lines.append(f"--- {fp} ({m['count']:,} occurrences) ---")
        for r in reps:
            lines.append(f"  {r}")
        lines.append("")

    lines.append("YOUR TASK:")
    lines.append("1. EXTRACT INVARIANTS: What structural patterns are invariant across this dataset?")
    lines.append("   (e.g., 'binary equality dominates', 'inequalities cluster around ordering relations',")
    lines.append("    'parenthesized expressions indicate function application', etc.)")
    lines.append("")
    lines.append("2. CLASSIFY NATURAL GROUPINGS: If math were drawing its own taxonomy without human labels,")
    lines.append("   what categories would emerge purely from these structural signatures?")
    lines.append("   Name each category and give its defining invariant.")
    lines.append("")
    lines.append("3. PREDICT STRUCTURAL DENSITY: Given the long-tail distribution (top form is only 3.59%),")
    lines.append("   what does this say about the 'information entropy' of mathematical notation across domains?")
    lines.append("")
    lines.append("4. ANOMALY FLAGGING: Which motifs strike you as structurally 'weird' or outliers that")
    lines.append("   break expected patterns? (e.g., v0 = v0, v0 = empty, unusual operator combinations)")
    lines.append("")
    lines.append("Respond in structured JSON with keys: invariants, natural_taxonomy, entropy_analysis, anomalies.")
    lines.append("Be concise but mathematically rigorous.")

    return "\n".join(lines)

def main():
    model = "cogito-2.1:671b"
    print(f"{'='*60}")
    print(f"  OLLAMA CLOUD INVARIANT PROBE")
    print(f"  Model: {model}")
    print(f"{'='*60}")

    api_key = os.getenv("OLLAMA_API_KEY", "your_api_key_here")
    client = Client(
        host="https://ollama.com",
        headers={"Authorization": "Bearer " + api_key}
    )

    print("\nLoading motifs...")
    motifs, total_eq, unique_forms = load_top_motifs(n=200)
    print(f"  Loaded top {len(motifs)} motifs from {total_eq:,} equations")

    print("\nBuilding prompt...")
    prompt = build_prompt(motifs, total_eq, unique_forms)
    prompt_chars = len(prompt)
    prompt_tokens = prompt_chars // 4  # rough estimate
    print(f"  Prompt size: {prompt_chars:,} chars (~{prompt_tokens:,} tokens)")

    print(f"\nSending to {model}...")
    print("  (this may take a while for 671B parameters)")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = OUTDIR / f"invariant_probe_{model.replace(':', '_')}_{ts}.json"

    try:
        response = client.chat(
            model=model,
            messages=[
                {"role": "system", "content": "You are a mathematical structural analyst. Respond only in valid JSON."},
                {"role": "user", "content": prompt},
            ],
            stream=False,
            options={"temperature": 0.2, "num_ctx": 128000},
        )

        content = response["message"]["content"]
        print(f"\n  Response received: {len(content):,} chars")

        # Save raw response
        result = {
            "timestamp": ts,
            "model": model,
            "prompt_tokens_est": prompt_tokens,
            "prompt_chars": prompt_chars,
            "response_chars": len(content),
            "response": content,
        }

        with open(out_path, "w") as f:
            json.dump(result, f, indent=2)

        print(f"  Saved to: {out_path}")

        # Try to pretty-print the JSON response
        try:
            parsed = json.loads(content)
            print("\n  --- PARSED RESPONSE ---")
            print(json.dumps(parsed, indent=2)[:3000])
        except json.JSONDecodeError:
            print("\n  --- RAW RESPONSE (first 2000 chars) ---")
            print(content[:2000])

    except Exception as e:
        print(f"\n  [!] ERROR: {e}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("  INVARIANT PROBE COMPLETE")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
