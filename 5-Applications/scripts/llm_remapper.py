#!/usr/bin/env python3
"""
LLM-assisted re-mapping of arXiv findings to unified equation symbols.

Supports:
  - OpenAI API (GPT-4o-mini is cheap and fast)
  - Anthropic API (Claude 3 Haiku)
  - Local Ollama (free, no API key)

Usage:
  export OPENAI_API_KEY="sk-..."
  python llm_remapper.py --provider openai --input arxiv_findings_500.md --output arxiv_llm_mapped.md

  # Or local Ollama (free)
  python llm_remapper.py --provider ollama --model llama3.2 --input arxiv_findings_500.md
"""

import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Optional

import requests


@dataclass
class Entry:
    number: int
    title: str
    url: str
    year: str
    summary: str


def parse_entries(text: str) -> list[Entry]:
    entries = []
    pattern = re.compile(
        r"## (\d+)\. (.+?)\n\n"
        r"\*\*Source:\*\* \[([^\]]+)\]\([^)]+\)\s+\((\d{4})\)\n\n"
        r"\*\*Summary:\*\* (.+?)\n\n"
        r"\| Symbol \| Mapping \|\n\|--------\|---------\|\n"
        r"\| Ω \| .+? \|\n"
        r"\| Ψ \| .+? \|\n"
        r"\| B \| .+? \|\n"
        r"\| C \| .+? \|\n"
        r"\| Δ \| .+? \|\n",
        re.DOTALL,
    )
    for m in pattern.finditer(text):
        entries.append(
            Entry(
                number=int(m.group(1)),
                title=m.group(2).strip(),
                url=m.group(3).strip(),
                year=m.group(4).strip(),
                summary=m.group(5).strip()[:600],
            )
        )
    return entries


PROMPT_TEMPLATE = """You are a precise scientific classifier. Map the following paper to five symbols from this universal equation:

  Ω = Ψ [ B(θ) ⊗ C(n, α) ] ⊕ Δ(n, θ, α)

Definitions:
- Ω (Omega): The observable output, the measured phenomenon, the result.
- Ψ (Psi): The operator, mechanism, or theory that combines basis and context.
- B (Basis): The conserved, reusable, fundamental component (basis vectors, genes, spacetime metric, etc.).
- C (Context): The dynamic, adaptive, variable parameter (environment, initial conditions, input data).
- Δ (Delta): The irreducible residual — noise, uncertainty, error, fundamental limit.

Paper:
Title: {title}
Abstract: {summary}

Respond ONLY in valid JSON with exactly these five keys and short (≤15 words) values:
{{"Ω": "...", "Ψ": "...", "B": "...", "C": "...", "Δ": "..."}}
"""


def call_openai(title: str, summary: str, api_key: str, model: str = "gpt-4o-mini") -> Optional[dict]:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a scientific classifier."},
            {"role": "user", "content": PROMPT_TEMPLATE.format(title=title, summary=summary)},
        ],
        "temperature": 0.1,
        "max_tokens": 150,
    }
    try:
        r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        # Extract JSON
        match = re.search(r'\{[^}]+\}', content)
        if match:
            return json.loads(match.group(0))
    except Exception as e:
        print(f"  OpenAI error: {e}", file=sys.stderr)
    return None


def call_anthropic(title: str, summary: str, api_key: str, model: str = "claude-3-haiku-20240307") -> Optional[dict]:
    headers = {"x-api-key": api_key, "Content-Type": "application/json", "anthropic-version": "2023-06-01"}
    payload = {
        "model": model,
        "max_tokens": 150,
        "temperature": 0.1,
        "messages": [{"role": "user", "content": PROMPT_TEMPLATE.format(title=title, summary=summary)}],
    }
    try:
        r = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        content = r.json()["content"][0]["text"]
        match = re.search(r'\{[^}]+\}', content)
        if match:
            return json.loads(match.group(0))
    except Exception as e:
        print(f"  Anthropic error: {e}", file=sys.stderr)
    return None


def call_ollama(title: str, summary: str, model: str = "llama3.2", host: str = "http://localhost:11434") -> Optional[dict]:
    payload = {
        "model": model,
        "prompt": PROMPT_TEMPLATE.format(title=title, summary=summary),
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 150},
    }
    try:
        r = requests.post(f"{host}/api/generate", json=payload, timeout=60)
        r.raise_for_status()
        content = r.json()["response"]
        match = re.search(r'\{[^}]+\}', content)
        if match:
            return json.loads(match.group(0))
    except Exception as e:
        print(f"  Ollama error: {e}", file=sys.stderr)
    return None


def map_entry(entry: Entry, provider: str, model: str, api_key: Optional[str]) -> Optional[dict]:
    if provider == "openai":
        if not api_key:
            print("ERROR: OPENAI_API_KEY not set", file=sys.stderr)
            return None
        return call_openai(entry.title, entry.summary, api_key, model)
    elif provider == "anthropic":
        if not api_key:
            print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
            return None
        return call_anthropic(entry.title, entry.summary, api_key, model)
    elif provider == "ollama":
        return call_ollama(entry.title, entry.summary, model)
    else:
        print(f"ERROR: Unknown provider {provider}", file=sys.stderr)
        return None


def render_entry(e: Entry, mapping: dict) -> str:
    return (
        f"## {e.number}. {e.title}\n\n"
        f"**Source:** [{e.url}]({e.url})  ({e.year})\n\n"
        f"**Summary:** {e.summary[:500]}\n\n"
        f"| Symbol | Mapping |\n"
        f"|--------|---------|\n"
        f"| Ω | {mapping.get('Ω', 'N/A')} |\n"
        f"| Ψ | {mapping.get('Ψ', 'N/A')} |\n"
        f"| B | {mapping.get('B', 'N/A')} |\n"
        f"| C | {mapping.get('C', 'N/A')} |\n"
        f"| Δ | {mapping.get('Δ', 'N/A')} |\n\n"
        f"---\n\n"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input markdown file")
    parser.add_argument("--output", required=True, help="Output markdown file")
    parser.add_argument("--provider", choices=["openai", "anthropic", "ollama"], default="ollama")
    parser.add_argument("--model", default="llama3.2", help="Model name")
    parser.add_argument("--workers", type=int, default=4, help="Parallel workers")
    parser.add_argument("--max", type=int, default=0, help="Max entries (0 = all)")
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY") if args.provider == "openai" else os.getenv("ANTHROPIC_API_KEY")

    with open(args.input, "r", encoding="utf-8") as f:
        text = f.read()

    entries = parse_entries(text)
    if args.max:
        entries = entries[:args.max]

    print(f"Entries: {len(entries)} | Provider: {args.provider} | Model: {args.model}")
    print("=" * 60)

    results = {}

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(map_entry, e, args.provider, args.model, api_key): e for e in entries}
        for future in as_completed(futures):
            e = futures[future]
            mapping = future.result()
            if mapping:
                results[e.number] = mapping
                print(f"  ✓ #{e.number}: {e.title[:50]}...")
            else:
                print(f"  ✗ #{e.number}: FAILED")
            time.sleep(0.5)  # rate limit politeness

    # Build output
    lines = [
        f"# ArXiv Findings — LLM-Mapped ({args.provider}/{args.model})",
        "",
        f"**Papers:** {len(entries)}",
        f"**Successfully mapped:** {len(results)}",
        f"**Equation:** Ω = Ψ [ B(θ) ⊗ C(n, α) ] ⊕ Δ(n, θ, α)",
        "",
        "---",
        "",
    ]

    for e in entries:
        mapping = results.get(e.number, {
            "Ω": "N/A", "Ψ": "N/A", "B": "N/A", "C": "N/A", "Δ": "N/A"
        })
        lines.append(render_entry(e, mapping))

    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\nWrote {args.output}")
    print(f"Success rate: {len(results)}/{len(entries)} ({100*len(results)//len(entries)}%)")


if __name__ == "__main__":
    main()
