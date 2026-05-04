#!/usr/bin/env python3
"""
Ollama Cloud Manifold Reconfiguration Probe
Send the Hutter Prize manifold report to a gigabyte-scale model and
ask it to reconfigure the manifold for maximum compactness + 1:1 restorability.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from ollama import Client

BASE = Path("/home/allaun/Documents/Research Stack/3-Mathematical-Models")
MANIFOLD_REPORT = BASE / "hutter_manifold/hutter_manifold_report_20260504_160627.json"
SELF_DISCOVERED = BASE / "math_self_discovered.json"
OUTDIR = BASE / "hutter_manifold"
OUTDIR.mkdir(parents=True, exist_ok=True)

def load_manifold_data():
    with open(MANIFOLD_REPORT) as f:
        manifold = json.load(f)
    with open(SELF_DISCOVERED) as f:
        discovered = json.load(f)
    return manifold, discovered

def build_prompt(manifold: dict, discovered: dict) -> str:
    lines = []
    lines.append("You are a compression theorist specializing in Kolmogorov complexity and manifold geometry.")
    lines.append("")
    lines.append("I have built a manifold map of 374,322 unique mathematical equation structures")
    lines.append("derived from 1.51 million stripped equations (no human labels, purely structural).")
    lines.append("")
    lines.append("CURRENT MANIFOLD CONFIGURATION:")
    lines.append(f"  Total equations: {discovered['total_equations']:,}")
    lines.append(f"  Unique structural forms: {discovered['unique_structural_forms']:,}")
    lines.append(f"  Current compression ratio: {manifold['compression']['compression_ratio']:.2f}x")
    lines.append(f"  Current Hutter score: {manifold['compression']['hutter_score']:.4f}")
    lines.append("")
    lines.append("CURRENT CATEGORIES (cogito-2.1:671b taxonomy):")
    for cat, count in manifold['manifold']['categories'].items():
        lines.append(f"  {cat:15s}: {count:>8,}")
    lines.append("")
    lines.append("CURRENT COMPRESSION COMPONENTS (Hutter Prize equation):")
    lines.append(f"  C_comp (grammar compression):  {manifold['compression']['c_comp']}")
    lines.append(f"  C_phys (binding entropy):      {manifold['compression']['c_phys']}")
    lines.append(f"  C_geom (manifold curvature):  {manifold['compression']['c_geom']}")
    lines.append(f"  S (spatial coherence):         {manifold['compression']['s']}")
    lines.append(f"  G (decoder overhead):          {manifold['compression']['g']}")
    lines.append(f"  F (compute field):              {manifold['compression']['f']}")
    lines.append("")
    lines.append("TOP 50 STRUCTURAL MOTIFS (fingerprint → count → %):")
    for m in discovered['top_motifs'][:50]:
        lines.append(f"  {m['count']:>7,}  ({m['percentage']:>5.2f}%)  {m['fingerprint']}")
    lines.append("")
    lines.append("YOUR TASK — MANIFOLD RECONFIGURATION:")
    lines.append("")
    lines.append("1. IDENTIFY WASTE: Where is the current manifold bloated?")
    lines.append("   - Redundant categories? Overlapping templates? Poor clustering?")
    lines.append("   - Which structural forms are 'almost identical' and should merge?")
    lines.append("")
    lines.append("2. PROPOSE A NEW COMPACTIFICATION:")
    lines.append("   - Design a smaller, denser manifold (fewer templates, better clustering)")
    lines.append("   - Suggest new categories if the 6 cogito categories are suboptimal")
    lines.append("   - Define the encoding scheme: how many bits per equation?")
    lines.append("")
    lines.append("3. COMPUTE THEORETICAL LIMITS:")
    lines.append("   - What is the information-theoretic minimum size?")
    lines.append("   - Kolmogorov complexity estimate for this dataset")
    lines.append("   - How close can we get to the Shannon entropy bound?")
    lines.append("")
    lines.append("4. SPECIFY THE 1:1 RESTORABILITY PROOF:")
    lines.append("   - Exact decode procedure from compressed representation")
    lines.append("   - Prove no information is lost (bijective mapping)")
    lines.append("")
    lines.append("Respond in structured JSON with keys:")
    lines.append("  waste_analysis, new_manifold_design, theoretical_limits, reconfig_commands, restorability_proof")
    lines.append("")
    lines.append("Be mathematically rigorous. Target: beat 10.00x compression while maintaining 1:1 restorability.")

    return "\n".join(lines)

def main():
    # Try largest available models
    models_to_try = [
        "deepseek-v3.1:671b",
        "kimi-k2:1t",
        "mistral-large-3:675b",
        "cogito-2.1:671b",
    ]

    api_key = os.getenv("OLLAMA_API_KEY", "your_api_key_here")
    client = Client(
        host="https://ollama.com",
        headers={"Authorization": "Bearer " + api_key}
    )

    # Test which model is available
    model = None
    for m in models_to_try:
        try:
            print(f"Trying {m}...")
            # Quick ping
            client.chat(model=m, messages=[{"role": "user", "content": "ping"}], stream=False)
            model = m
            print(f"  {m} is available!")
            break
        except Exception as e:
            print(f"  {m} unavailable: {e}")
            continue

    if not model:
        print("[!] No large models available. Using cogito-2.1:671b as fallback.")
        model = "cogito-2.1:671b"

    print(f"\n{'='*60}")
    print(f"  MANIFOLD RECONFIGURATION PROBE")
    print(f"  Model: {model}")
    print(f"{'='*60}")

    print("\nLoading manifold data...")
    manifold, discovered = load_manifold_data()

    print("\nBuilding prompt...")
    prompt = build_prompt(manifold, discovered)
    prompt_chars = len(prompt)
    print(f"  Prompt: {prompt_chars:,} chars (~{prompt_chars//4:,} tokens)")

    print(f"\nSending to {model}...")
    print("  (this may take several minutes for 671B+ parameters)")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = OUTDIR / f"manifold_reconfig_{model.replace(':', '_')}_{ts}.json"

    try:
        response = client.chat(
            model=model,
            messages=[
                {"role": "system", "content": "You are a compression theorist and manifold geometer. Respond only in valid JSON. Be rigorous and quantitative."},
                {"role": "user", "content": prompt},
            ],
            stream=False,
            options={"temperature": 0.1, "num_ctx": 128000},
        )

        content = response["message"]["content"]
        print(f"\n  Response: {len(content):,} chars")

        result = {
            "timestamp": ts,
            "model": model,
            "prompt_chars": prompt_chars,
            "response_chars": len(content),
            "response": content,
        }

        with open(out_path, "w") as f:
            json.dump(result, f, indent=2)

        print(f"  Saved to: {out_path}")

        # Try to parse
        try:
            parsed = json.loads(content)
            print("\n  --- RECONFIGURATION PROPOSAL (parsed) ---")
            print(json.dumps(parsed, indent=2)[:5000])
        except json.JSONDecodeError:
            print("\n  --- RAW RESPONSE (first 3000 chars) ---")
            print(content[:3000])

    except Exception as e:
        print(f"\n  [!] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return

    print(f"\n{'='*60}")
    print("  MANIFOLD RECONFIGURATION COMPLETE")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
