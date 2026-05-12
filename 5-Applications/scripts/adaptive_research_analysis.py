#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["requests", "rich"]
# ///
"""
Adaptive Research Stack Analyzer
Uses Ollama Cloud API to run a three-pass analysis:
  1. Summarize  - distill key ideas from core documents
  2. Cross-link - find connections across domains
  3. Critique   - identify gaps, weak claims, missing proofs

Usage:
    uv run scripts/adaptive_research_analysis.py
    uv run scripts/adaptive_research_analysis.py --model gemma3:12b --out /tmp/analysis.md
"""

import argparse
import datetime
import json
import os
import sys
import textwrap
from pathlib import Path

import requests
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
RESEARCH_ROOT = Path("/home/allaun/Documents/Research Stack")
API_BASE = "https://ollama.com/v1"
API_KEY = os.environ.get("OLLAMA_API_KEY", "")
# Model priority: cogito (Cognition 671B) → qwen3-next (80B) → gemma4 (31B) → deepseek-v4-flash
DEFAULT_MODEL = "cogito-2.1:671b"
FALLBACK_CHAIN = ["qwen3-next:80b", "gemma4:31b", "deepseek-v4-flash"]

# Key documents to feed into the analysis (relative to RESEARCH_ROOT)
CORE_DOCS = [
    "README.md",
    "CONCEPTS.md",
    "ARCHITECTURE.md",
    "SIGNAL_THEORY_COMPENDIUM.md",
    "6-Documentation/EXPLANATION_FOR_HUMANS.md",
    "6-Documentation/MATH_CORE.md",
    "6-Documentation/VISION_NORTH_STAR.md",
    "6-Documentation/GLOSSARY.md",
    "6-Documentation/FIRST_PRINCIPLES_DAG.md",
    "6-Documentation/FIELD_EQUATION_COMPARISON.md",
    "6-Documentation/docs/SKEPTICISM_GRADIENT_REASSESSMENT_2026-04-29.md",
    "6-Documentation/docs/CLAIM_STATE_AUDIT_2026-05-05.md",
    "6-Documentation/docs/IMPLEMENTATION_ATTACK_ANALYSIS.md",
    "6-Documentation/docs/ENE_RESEARCH_TOPIC_CANDIDATES.md",
    "6-Documentation/docs/OTOM_V1_PAPER_STRUCTURE_AND_NEXT_GEN_SIMULATOR.md",
    "6-Documentation/docs/stack_solidification_staging_manifest_2026-05-10.md",
    "6-Documentation/docs/cross_domain_adaptation_numeric_review.md",
    "6-Documentation/docs/BAD_MATH_CLEANUP_REPORT.md",
]

DOMAIN_DIRS = {
    "Core Formalism (Lean)":   "0-Core-Formalism",
    "Distributed Systems":     "1-Distributed-Systems",
    "Search Space":            "2-Search-Space",
    "Mathematical Models":     "3-Mathematical-Models",
    "Infrastructure / FPGA":  "4-Infrastructure",
    "Applications":            "5-Applications",
    "Documentation":           "6-Documentation/docs",
}

MAX_CHARS_PER_DOC = 8_000    # truncate individual docs (DeepSeek handles large context)
MAX_CONTEXT_CHARS = 120_000  # total context fed per LLM call

console = Console()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_doc(path: Path, max_chars: int = MAX_CHARS_PER_DOC) -> str:
    try:
        text = path.read_text(errors="replace")
        if len(text) > max_chars:
            text = text[:max_chars] + f"\n\n[... truncated at {max_chars} chars ...]"
        return text
    except Exception as e:
        return f"[Could not read {path}: {e}]"


def gather_context() -> str:
    """Load core docs and first-file samples from each domain directory."""
    parts = []

    # Core documents
    for rel in CORE_DOCS:
        p = RESEARCH_ROOT / rel
        if p.exists():
            parts.append(f"\n\n---\n## FILE: {rel}\n\n{load_doc(p)}")

    # Domain directory samples — grab up to 3 .md files per domain
    for domain, rel_dir in DOMAIN_DIRS.items():
        d = RESEARCH_ROOT / rel_dir
        if not d.is_dir():
            continue
        md_files = sorted(d.glob("*.md"))[:3]
        for mdf in md_files:
            rel_path = mdf.relative_to(RESEARCH_ROOT)
            parts.append(f"\n\n---\n## FILE [{domain}]: {rel_path}\n\n{load_doc(mdf, 3000)}")

    combined = "\n".join(parts)
    if len(combined) > MAX_CONTEXT_CHARS:
        combined = combined[:MAX_CONTEXT_CHARS] + "\n\n[... context truncated ...]"
    return combined


def chat(model: str, system: str, user: str, label: str, retries: int = 3) -> str:
    """Call Ollama Cloud chat completions endpoint with retry + fallback."""
    import time

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    models_to_try = [model] + [m for m in FALLBACK_CHAIN if m != model]

    for attempt_model in models_to_try:
        payload = {
            "model": attempt_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 8192},
        }
        for attempt in range(1, retries + 1):
            with Progress(
                SpinnerColumn(),
                TextColumn(f"[bold cyan]{label}[/bold cyan] (model: {attempt_model}, attempt {attempt}/{retries}) ..."),
                transient=True,
                console=console,
            ) as progress:
                progress.add_task("", total=None)
                try:
                    resp = requests.post(
                        f"{API_BASE}/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=600,
                    )
                except requests.exceptions.Timeout:
                    console.print(f"[yellow]Timeout on attempt {attempt}, retrying...[/yellow]")
                    time.sleep(5 * attempt)
                    continue

            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                # Strip <think>...</think> reasoning blocks if present
                import re
                content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
                return content

            error_body = resp.text[:300]
            if "overloaded" in error_body.lower() or resp.status_code in (503, 429):
                wait = 10 * attempt
                console.print(f"[yellow]Server overloaded (attempt {attempt}), waiting {wait}s...[/yellow]")
                time.sleep(wait)
            elif resp.status_code == 500:
                console.print(f"[yellow]500 error with {attempt_model}, trying next model...[/yellow]")
                break  # try fallback model
            else:
                console.print(f"[red]API error {resp.status_code}:[/red] {error_body}")
                sys.exit(1)

        console.print(f"[yellow]Exhausted retries for {attempt_model}, trying fallback...[/yellow]")

    console.print("[red]All models failed. Aborting.[/red]")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Analysis passes
# ---------------------------------------------------------------------------

SYSTEM_BASE = """\
You are an expert research analyst reviewing a cutting-edge research stack called OTOM \
(One-Time Operations on Manifolds / Ultra-low-power zero-decimal data routing). \
The stack spans Lean 4 formal proofs, FPGA hardware, distributed systems, genomics, \
astrophysics, signal theory, and compression mathematics. \
Be precise, technical, and honest. Do NOT hallucinate citations. \
When you are uncertain, say so explicitly.\
"""


def pass_summarize(model: str, context: str) -> str:
    system = SYSTEM_BASE + """

Your task: SUMMARIZE.
Produce a structured executive summary of this research stack covering:
1. Core thesis and central claims
2. Mathematical foundations (key equations, structures, proof techniques)
3. Hardware targets and implementation status
4. Applied domains (compression, genomics, astrophysics, etc.)
5. Current maturity level — what is proven vs speculative
Keep each section under 250 words. Use markdown headers.
"""
    user = f"Here is the research stack content:\n\n{context}\n\nProduce the structured summary now."
    return chat(model, system, user, "Pass 1: Summarize")


def pass_crosslink(model: str, context: str, summary: str) -> str:
    system = SYSTEM_BASE + """

Your task: CROSS-DOMAIN LINKING.
Given the research content and the summary already produced, identify:
1. Non-obvious connections between domains (e.g. genomics ↔ topology, signal theory ↔ FPGA routing)
2. Concepts that appear in multiple domains under different names (unification opportunities)
3. Mathematical structures that bridge multiple layers of the stack
4. Any surprising overlaps with known external research (mention without fabricating citations)
Format as a markdown table + narrative explanation for each link found.
"""
    user = f"Summary:\n{summary}\n\n---\nFull context:\n{context}\n\nIdentify cross-domain links now."
    return chat(model, system, user, "Pass 2: Cross-link")


def pass_critique(model: str, context: str, summary: str) -> str:
    system = SYSTEM_BASE + """

Your task: CRITIQUE AND GAP ANALYSIS.
Be rigorous and honest. Identify:
1. Claims that lack formal proof or empirical validation — flag each clearly
2. Mathematical steps that appear hand-wavy or unjustified
3. Research gaps: important questions the stack does not yet address
4. Risks: places where the stack's assumptions could break down
5. Recommended next experiments or proof targets
Be constructive but unflinching. A weak critique is useless.
Format with severity tags: [CRITICAL], [MODERATE], [MINOR].
"""
    user = f"Summary:\n{summary}\n\n---\nFull context:\n{context}\n\nDeliver the critique now."
    return chat(model, system, user, "Pass 3: Critique")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Adaptive Research Stack Analyzer")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"Ollama Cloud model to use (default: {DEFAULT_MODEL}, fallback chain: {FALLBACK_CHAIN})")
    parser.add_argument("--out", default=None,
                        help="Output markdown file path (default: auto-named in Research Stack)")
    parser.add_argument("--list-models", action="store_true",
                        help="List available Ollama Cloud models and exit")
    args = parser.parse_args()

    if not API_KEY:
        console.print("[red]Set OLLAMA_API_KEY before calling the Ollama Cloud API.[/red]")
        sys.exit(1)

    if args.list_models:
        resp = requests.get(
            "https://ollama.com/api/tags",
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=30,
        )
        models = [m["name"] for m in resp.json().get("models", [])]
        console.print("\n".join(sorted(models)))
        return

    console.rule("[bold green]Adaptive Research Stack Analyzer[/bold green]")
    console.print(f"Model: [bold]{args.model}[/bold]   Root: {RESEARCH_ROOT}\n")

    # --- Gather context
    console.print("[dim]Gathering research documents...[/dim]")
    context = gather_context()
    char_count = len(context)
    console.print(f"[dim]Context: {char_count:,} chars across core docs + domain samples[/dim]\n")

    # --- Three passes
    summary   = pass_summarize(args.model, context)
    crosslink = pass_crosslink(args.model, context, summary)
    critique  = pass_critique(args.model, context, summary)

    # --- Assemble report
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    report = f"""# Adaptive Research Analysis Report
*Generated: {timestamp} | Model: {args.model}*

---

## Pass 1 — Executive Summary

{summary}

---

## Pass 2 — Cross-Domain Links

{crosslink}

---

## Pass 3 — Critique & Gap Analysis

{critique}

---
*Analysis performed by `scripts/adaptive_research_analysis.py` using Ollama Cloud API.*
"""

    # --- Output
    if args.out:
        out_path = Path(args.out)
    else:
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        out_path = RESEARCH_ROOT / "6-Documentation" / "docs" / "reports" / f"adaptive_analysis_{date_str}.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)

    out_path.write_text(report)

    console.rule("[bold green]Analysis Complete[/bold green]")
    console.print(f"\nReport saved to: [bold]{out_path}[/bold]\n")
    console.print(Markdown(report[:6000] + ("\n\n*[report truncated for display — see file for full output]*" if len(report) > 6000 else "")))


if __name__ == "__main__":
    main()
