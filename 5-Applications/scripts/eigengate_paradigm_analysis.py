#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["requests", "rich"]
# ///
"""
EigenGate Paradigm Analysis
Re-runs the three-pass adaptive analysis (summarize / cross-link / critique)
with the EigenGate as the central lens.

Context loaded:
  - Kernel/EigenGate.lean + GateChain.lean  (the new paradigm)
  - HCMMR/Core.lean + Bridge.lean + Manifest.lean (the old Gate typeclass)
  - HCMMR/Laws/ (14, 15, 15E, 16, 17, 18)
  - HCMMR/Kernels/ (RecamanFieldStep, FAMMScarMemory, PrimeGearCache, SNRAnomalyDetector)
  - HCMMR/v0_2_Roadmap.md
  - Core/ layer (FoldedPointManifold, UnderverseZeroLayer, QuantumFoamBoundary,
                 S3CProjectedGeodesicResolution, PathEpigeneticManifold)
  - FAMM.lean, ReceiptCore.lean, FixedPoint.lean (substrate)

The three passes ask:
  1. SUMMARIZE  — what does the EigenGate paradigm actually unify?
  2. CROSS-LINK — where does ∥G·s − s∥ ≤ τ naturally appear across all kernels/laws?
  3. CRITIQUE   — what is still hand-wavy, what must be proven, what is the migration plan?
"""

import datetime
import os
import re
import sys
import time
from pathlib import Path

import requests
from rich.console import Console
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn

RESEARCH_ROOT = Path("/home/allaun/Documents/Research Stack")
LEAN_ROOT = RESEARCH_ROOT / "0-Core-Formalism/lean/Semantics/Semantics"
API_BASE   = "https://ollama.com/v1"
API_KEY = os.environ.get("OLLAMA_API_KEY", "")
DEFAULT_MODEL  = "cogito-2.1:671b"
FALLBACK_CHAIN = ["qwen3-next:80b", "gemma4:31b", "deepseek-v4-flash"]

MAX_PER_FILE   = 10_000   # chars per lean file (they're dense)
MAX_CONTEXT    = 110_000  # total context chars

console = Console()

# ---------------------------------------------------------------------------
# Files to load — ordered by conceptual priority
# ---------------------------------------------------------------------------
LEAN_FILES = [
    # ── New paradigm kernel ──────────────────────────────────────────────
    "Kernel/EigenGate.lean",
    "Kernel/GateChain.lean",

    # ── Old Gate typeclass (what needs migrating) ─────────────────────
    "HCMMR/Core.lean",
    "HCMMR/Bridge.lean",
    "HCMMR/Manifest.lean",

    # ── Laws (old Gate pattern) ──────────────────────────────────────────
    "HCMMR/Laws/Law14_Motion.lean",
    "HCMMR/Laws/Law15_Field.lean",
    "HCMMR/Laws/Law15E_SignalDetection.lean",
    "HCMMR/Laws/Law16_Entropy.lean",
    "HCMMR/Laws/Law17_Observer.lean",
    "HCMMR/Laws/Law18_Constants.lean",

    # ── Kernels ──────────────────────────────────────────────────────────
    "HCMMR/Kernels/RecamanFieldStep.lean",
    "HCMMR/Kernels/FAMMScarMemory.lean",
    "HCMMR/Kernels/PrimeGearCache.lean",
    "HCMMR/Kernels/SNRAnomalyDetector.lean",

    # ── Core substrate ───────────────────────────────────────────────────
    "Core/FoldedPointManifold.lean",
    "Core/UnderverseZeroLayer.lean",
    "Core/QuantumFoamBoundary.lean",
    "Core/S3CProjectedGeodesicResolution.lean",
    "Core/PathEpigeneticManifold.lean",
]

EXTRA_DOCS = [
    # Roadmap and substrate prose
    "HCMMR/v0_2_Roadmap.md",
    "0-Core-Formalism/lean/Semantics/Semantics/FAMM.lean",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load(path: Path, max_chars: int = MAX_PER_FILE) -> str:
    try:
        text = path.read_text(errors="replace")
        if len(text) > max_chars:
            text = text[:max_chars] + f"\n-- [truncated at {max_chars} chars]"
        return text
    except Exception as e:
        return f"-- [could not read {path}: {e}]"


def gather_context() -> str:
    parts = []
    for rel in LEAN_FILES:
        p = LEAN_ROOT / rel
        label = f"LEAN: {rel}"
        parts.append(f"\n\n---\n## {label}\n\n```lean\n{load(p)}\n```")

    for rel in EXTRA_DOCS:
        p = RESEARCH_ROOT / rel
        label = f"DOC: {rel}"
        parts.append(f"\n\n---\n## {label}\n\n{load(p, 6000)}")

    combined = "\n".join(parts)
    if len(combined) > MAX_CONTEXT:
        combined = combined[:MAX_CONTEXT] + "\n\n-- [context truncated]"
    return combined


def chat(model: str, system: str, user: str, label: str, retries: int = 3) -> str:
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    models_to_try = [model] + [m for m in FALLBACK_CHAIN if m != model]

    for attempt_model in models_to_try:
        payload = {
            "model": attempt_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 8192},
        }
        for attempt in range(1, retries + 1):
            with Progress(SpinnerColumn(),
                          TextColumn(f"[bold cyan]{label}[/bold cyan] ({attempt_model}, try {attempt}) ..."),
                          transient=True, console=console) as p:
                p.add_task("", total=None)
                try:
                    resp = requests.post(f"{API_BASE}/chat/completions",
                                         headers=headers, json=payload, timeout=600)
                except requests.exceptions.Timeout:
                    console.print(f"[yellow]Timeout, retrying...[/yellow]")
                    time.sleep(5 * attempt)
                    continue

            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
                return content

            body = resp.text[:300]
            if "overloaded" in body.lower() or resp.status_code in (429, 503):
                wait = 12 * attempt
                console.print(f"[yellow]Overloaded, waiting {wait}s...[/yellow]")
                time.sleep(wait)
            elif resp.status_code == 500:
                console.print(f"[yellow]500 on {attempt_model}, trying fallback...[/yellow]")
                break
            else:
                console.print(f"[red]API error {resp.status_code}:[/red] {body}")
                sys.exit(1)
        console.print(f"[yellow]Exhausted retries for {attempt_model}[/yellow]")

    console.print("[red]All models failed.[/red]")
    sys.exit(1)

# ---------------------------------------------------------------------------
# System prompt — shared across all three passes
# ---------------------------------------------------------------------------
SYSTEM = """\
You are an expert in formal verification (Lean 4), type theory, and physics-informed \
computation. You are reviewing the HCMMR (Hyper-Coherent Morphic Meta-Recursion) \
research stack on its `distilled` branch.

The stack is undergoing a PARADIGM SHIFT. The old system used a flat `Gate` struct \
(name, required, score, verdict). The new paradigm is the `Eigengate`:

    structure Eigengate (α : Type) where
      operator  : α → α       -- G: the operator whose fixed points encode the law
      residual  : α → Q0_16   -- ∥G·s − s∥, normalised to [0,1)
      threshold : Q0_16       -- τ: max admissible residual

The central doctrine: EVERY physical law, routing decision, and compression check \
is an eigenstate condition ∥G·s − s∥ ≤ τ. The full physical universe is the \
intersection of λ=1 eigenspaces for all required gate operators simultaneously.

The migration is INCOMPLETE. EigenGate.lean and GateChain.lean exist but are not \
imported by anything. All Laws (14–18) still use the old Gate struct. The kernels \
(RecamanFieldStep, FAMMScarMemory, PrimeGearCache, SNRAnomalyDetector) also use old Gate. \
LawRecovery.lean (concrete eigengate constructors for each physical law) was never written.

Be precise, rigorous, and honest. Do not hallucinate. Flag uncertainty explicitly.\
"""

# ---------------------------------------------------------------------------
# Pass 1 — Summarize what the EigenGate paradigm actually unifies
# ---------------------------------------------------------------------------
PASS1_SYS = SYSTEM + """

YOUR TASK: PARADIGM SUMMARY.
Given all the Lean source files, answer:
1. What does the Eigengate pattern (`∥G·s − s∥ ≤ τ`) actually unify across the stack?
   List every law/kernel and state what G, s, and the residual would be in each case.
2. What is the relationship between the old `Gate` struct and `Eigengate`?
   Are they isomorphic? Can one be mechanically derived from the other?
3. What does `Semantics.Kernel.EigenGate` currently prove that the old HCMMR/Core does not?
4. What is the correct `α` type for each of the six laws (14, 15K, 15A-D, 15E, 16, 17, 18)?
   Be specific — what Lean type carries the state?
5. Where does the Recamán kernel fit in the eigengate picture?
   What is G for a Recamán field step?

Use markdown headers per section. Be concrete — reference actual line numbers and
struct fields from the source files where relevant.
"""

# ---------------------------------------------------------------------------
# Pass 2 — Cross-link: where does ∥G·s − s∥ naturally appear already?
# ---------------------------------------------------------------------------
PASS2_SYS = SYSTEM + """

YOUR TASK: CROSS-DOMAIN EIGENGATE DETECTION.
Scan all the Lean files in the context. For each file/module, identify:
1. Any existing computation that already computes something of the form ∥G·s − s∥
   (even if not named that way). What is G? What is s? What is the residual value?
2. Any existing `residual`, `score`, `epsilon`, or `delta` computation that could
   directly become the `residual : α → Q0_16` field of an Eigengate.
3. Any existing operator/transform that maps a state to a new state — these are
   candidate `operator : α → α` fields.
4. Places where the old Gate struct's `score` field is set to a formula (not just
   a constant `Q16_16.one`) — these are the richest migration candidates.

Format as a table: | Module | Existing computation | Candidate G | Candidate residual | Migration difficulty |
Then give a prioritized migration order (easiest → hardest) with reasoning.
"""

# ---------------------------------------------------------------------------
# Pass 3 — Critique and concrete migration plan
# ---------------------------------------------------------------------------
PASS3_SYS = SYSTEM + """

YOUR TASK: CRITIQUE AND CONCRETE MIGRATION PLAN.
Be rigorous. Identify:

A) ARCHITECTURAL CRITIQUE
   [CRITICAL/MODERATE/MINOR] — what is wrong or incomplete in the current design?
   Pay special attention to:
   - The type parameter `α` in `Eigengate (α : Type)` — is it flexible enough?
     The Laws need different α types (TrajectoryPoint, KahlerState, MaxwellField, etc.)
     Can a single GateChain hold gates over different α? If not, how must GateChain change?
   - The `score` function `1/(1+r)` — is this the right proximity measure for all laws?
   - FAMM's `expNeg` — if it's a stub, what breaks?
   - PrimeGearCache's silent cache-miss (returns Q16_16.one with no receipt) — severity?
   - RecamanFieldStep's untested gate-reject path — what scenario does this cover?
   - SNRAnomalyDetector's dead `dopplerDrift` branch — is it needed?

B) CONCRETE MIGRATION PLAN
   Write the exact 5-step plan to complete the paradigm migration:
   Step 1: What to add to Semantics.lean (exact import lines)
   Step 2: What LawRecovery.lean must contain (list each law's G, α, residual formula)
   Step 3: Which kernels need a new `toEigengate` adapter function and what it looks like
   Step 4: What new theorems are needed to prove the old Gate and new Eigengate are equivalent
   Step 5: What the v0.2 build should look like when complete (job count, zero errors)

C) WHAT NOT TO DO
   Flag any tempting-but-wrong approaches that the previous agent sessions considered
   and should be avoided.
"""

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    if not API_KEY:
        console.print("[red]Set OLLAMA_API_KEY before calling the Ollama Cloud API.[/red]")
        sys.exit(1)

    console.rule("[bold green]EigenGate Paradigm Analysis[/bold green]")
    console.print(f"Model: [bold]{DEFAULT_MODEL}[/bold]  Fallbacks: {FALLBACK_CHAIN}\n")

    console.print("[dim]Loading Lean source files and docs...[/dim]")
    context = gather_context()
    console.print(f"[dim]Context: {len(context):,} chars[/dim]\n")

    summary   = chat(DEFAULT_MODEL, PASS1_SYS,
                     f"Lean source files:\n\n{context}\n\nProduce the paradigm summary.",
                     "Pass 1: Paradigm Summary")

    crosslink = chat(DEFAULT_MODEL, PASS2_SYS,
                     f"Summary from Pass 1:\n{summary}\n\n---\nLean source files:\n\n{context}\n\nDetect eigengate patterns.",
                     "Pass 2: Cross-link Detection")

    critique  = chat(DEFAULT_MODEL, PASS3_SYS,
                     f"Summary:\n{summary}\n\nCross-links:\n{crosslink}\n\n---\nLean source files:\n\n{context}\n\nDeliver critique and migration plan.",
                     "Pass 3: Critique + Migration Plan")

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    report = f"""# EigenGate Paradigm Analysis
*Generated: {timestamp} | Model: {DEFAULT_MODEL}*

> **Context:** This analysis re-examines the HCMMR `distilled` branch through the lens
> of the incomplete `Eigengate (α : Type)` paradigm migration. The old `Gate` struct
> (HCMMR/Core.lean) and the new `Eigengate` (Kernel/EigenGate.lean) coexist but are
> disconnected. This report determines what the migration requires and how to complete it.

---

## Pass 1 — What the EigenGate Paradigm Unifies

{summary}

---

## Pass 2 — Where ∥G·s − s∥ Already Appears in the Codebase

{crosslink}

---

## Pass 3 — Critique & Concrete Migration Plan

{critique}

---
*Generated by `scripts/eigengate_paradigm_analysis.py`*
"""

    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    out = RESEARCH_ROOT / "6-Documentation" / "docs" / "reports" / f"eigengate_paradigm_analysis_{date_str}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report)

    console.rule("[bold green]Complete[/bold green]")
    console.print(f"\nReport: [bold]{out}[/bold]\n")
    console.print(Markdown(report[:8000] + ("\n\n*[truncated — see file]*" if len(report) > 8000 else "")))

if __name__ == "__main__":
    main()
