#!/usr/bin/env python3
"""
Map physics equations from sqlite DB to unified equation symbols using local LLM.
V2: Fixed duplicate issue, writes incrementally, can resume.
"""

import csv
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

OUTPUT_FILE = "/home/allaun/Documents/Research Stack/3-Mathematical-Models/physics_eqs_mapped.md"
PROMPT_TEMPLATE = """Map this physics equation to five symbols from:
  Ω = Ψ [ B(θ) ⊗ C(n, α) ] ⊕ Δ(n, θ, α)

Equation: {title}
Domain: {domain}
Description: {description}

Definitions:
- Ω: Observable output, measured quantity, what the equation predicts
- Ψ: The operator, mechanism, or theory
- B: Conserved basis, fundamental component, the fixed structure
- C: Dynamic context, variable parameter, external condition
- Δ: Residual error, noise, uncertainty, fundamental limit

Respond ONLY in valid JSON with exactly these five keys and short (≤15 words) values:
{{"Ω": "...", "Ψ": "...", "B": "...", "C": "...", "Δ": "..."}}
"""


def call_ollama(title, domain, description, model="llama3.1:8b"):
    prompt = PROMPT_TEMPLATE.format(title=title, domain=domain, description=description[:300])
    try:
        r = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0.1, "num_predict": 150}},
            timeout=60,
        )
        r.raise_for_status()
        content = r.json()["response"]
        match = re.search(r'\{[^}]+\}', content)
        if match:
            return json.loads(match.group(0))
    except Exception as e:
        print(f"  ERROR: {e}", file=sys.stderr)
    return None


def load_progress():
    """Load already-mapped equation numbers from output file."""
    done = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                m = re.match(r"## Eq (\d+)\. ", line)
                if m:
                    done.add(m.group(1))
    return done


def append_entry(eq_num, title, domain, description, mapping):
    """Append a single entry to the output file."""
    m = mapping
    lines = [
        f"## Eq {eq_num}. {title}",
        "",
        f"**Domain:** {domain}",
        f"**Description:** {description[:200]}",
        "",
        "| Symbol | Mapping |",
        "|--------|---------|",
        f"| Ω | {m.get('Ω', 'N/A')} |",
        f"| Ψ | {m.get('Ψ', 'N/A')} |",
        f"| B | {m.get('B', 'N/A')} |",
        f"| C | {m.get('C', 'N/A')} |",
        f"| Δ | {m.get('Δ', 'N/A')} |",
        "",
        "---",
        "",
    ]
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    import sqlite3
    conn = sqlite3.connect("/home/allaun/physics_equations.db")
    cursor = conn.cursor()
    cursor.execute("SELECT eq_number, title, domain_id, significance FROM equations ORDER BY eq_number")
    rows = cursor.fetchall()

    # Get domain names
    cursor.execute("SELECT id, name FROM domains")
    domains = {str(r[0]): r[1] for r in cursor.fetchall()}
    conn.close()

    # Load progress
    done = load_progress()
    print(f"Total equations: {len(rows)} | Already mapped: {len(done)}")

    # Write header if new file
    if not done:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("# Physics Equations Database — Mapped to Unified Equation\n\n")
            f.write("**Equations:** {}\n".format(len(rows)))
            f.write("**Equation:** Ω = Ψ [ B(θ) ⊗ C(n, α) ] ⊕ Δ(n, θ, α)\n\n")
            f.write("---\n\n")

    # Process remaining
    remaining = [(eq_num, title, domains.get(str(domain_id), "Unknown"), desc or "")
                 for eq_num, title, domain_id, desc in rows
                 if str(eq_num) not in done]

    print(f"Remaining: {len(remaining)}")

    success = 0
    fail = 0
    for eq_num, title, domain, desc in remaining:
        mapping = call_ollama(title, domain, desc)
        if mapping:
            append_entry(eq_num, title, domain, desc, mapping)
            success += 1
            print(f"  ✓ #{eq_num}: {title[:50]}...")
        else:
            fail += 1
            print(f"  ✗ #{eq_num}: FAILED")
        time.sleep(0.2)

    print(f"\nDone. Success: {success}, Failed: {fail}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
