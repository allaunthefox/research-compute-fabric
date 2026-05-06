#!/usr/bin/env python3
"""
Map physics equations from sqlite DB to unified equation symbols using local LLM.
"""

import csv
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

PROMPT_TEMPLATE = """Map this physics equation to five symbols from:
  Ω = Ψ [ B(θ) ⊗ C(n, α) ] ⊕ Δ(n, θ, α)

Equation: {title}
Domain: {domain}
Formula/Description: {formula}

Definitions:
- Ω: Observable output, measured quantity, what the equation predicts
- Ψ: The operator, mechanism, or theory
- B: Conserved basis, fundamental component, the fixed structure
- C: Dynamic context, variable parameter, external condition
- Δ: Residual error, noise, uncertainty, fundamental limit

Respond ONLY in valid JSON with exactly these five keys and short (≤15 words) values:
{{"Ω": "...", "Ψ": "...", "B": "...", "C": "...", "Δ": "..."}}
"""


def call_ollama(title, domain, formula, model="llama3.1:8b"):
    prompt = PROMPT_TEMPLATE.format(title=title, domain=domain, formula=formula[:300])
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
        print(f"  ERROR #{title}: {e}", file=sys.stderr)
    return None


def main():
    input_file = "/tmp/physics_eqs_export.tsv"
    output_file = "/home/allaun/Documents/Research Stack/3-Mathematical-Models/physics_eqs_mapped.md"

    rows = list(csv.DictReader(open(input_file), delimiter='|', fieldnames=['eq_number', 'title', 'domain', 'formula', 'description']))
    # Skip header if present
    if rows and rows[0]['eq_number'].strip() == 'eq_number':
        rows = rows[1:]

    print(f"Mapping {len(rows)} physics equations...")

    results = {}

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {}
        for row in rows:
            eq_num = row['eq_number'].strip()
            title = row['title'].strip()
            domain = row['domain'].strip()
            formula = row['formula'].strip() + " " + row['description'].strip()
            future = executor.submit(call_ollama, title, domain, formula)
            futures[future] = (eq_num, title)

        for future in as_completed(futures):
            eq_num, title = futures[future]
            mapping = future.result()
            if mapping:
                results[eq_num] = mapping
                print(f"  ✓ #{eq_num}: {title[:50]}...")
            else:
                print(f"  ✗ #{eq_num}: FAILED")
            time.sleep(0.3)

    print(f"\nSuccess: {len(results)}/{len(rows)}")

    lines = [
        "# Physics Equations Database — Mapped to Unified Equation",
        "",
        f"**Equations:** {len(rows)}",
        f"**Successfully mapped:** {len(results)}",
        f"**Equation:** Ω = Ψ [ B(θ) ⊗ C(n, α) ] ⊕ Δ(n, θ, α)",
        "",
        "---",
        "",
    ]

    for row in rows:
        eq_num = row['eq_number'].strip()
        title = row['title'].strip()
        domain = row['domain'].strip()
        formula = row['formula'].strip()
        desc = row['description'].strip()
        m = results.get(eq_num, {"Ω": "N/A", "Ψ": "N/A", "B": "N/A", "C": "N/A", "Δ": "N/A"})

        lines.append(f"## Eq {eq_num}. {title}")
        lines.append(f"")
        lines.append(f"**Domain:** {domain}")
        lines.append(f"**Formula:** {formula[:200] if formula else desc[:200]}")
        lines.append(f"")
        lines.append(f"| Symbol | Mapping |")
        lines.append(f"|--------|---------|")
        lines.append(f"| Ω | {m['Ω']} |")
        lines.append(f"| Ψ | {m['Ψ']} |")
        lines.append(f"| B | {m['B']} |")
        lines.append(f"| C | {m['C']} |")
        lines.append(f"| Δ | {m['Δ']} |")
        lines.append(f"")
        lines.append(f"---")
        lines.append(f"")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\nWrote {output_file}")


if __name__ == "__main__":
    main()
