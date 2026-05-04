#!/usr/bin/env python3
"""
deepseek_review_adapter.py
==========================

Wraps `4-Infrastructure/infra/deepseek_adapter.py` with three additions for the
"verifier-of-the-verifier / fluent-bullshit defence" workflow:

  (a) prefer remote `deepseek-v4-flash` by default
  (b) escalate to `deepseek-v4-pro` on demand (`tier="pro"`)
  (c) always include the cached project context (verifier code, findings,
      MEMORY.md, etc.) using the Anthropic-compat endpoint's prompt-caching
      so that re-using the context across queries costs ~50× less

Pricing (USD per 1M tokens, per https://api-docs.deepseek.com/quick_start/pricing,
fetched 2026-05-03):

    deepseek-v4-flash : input cache hit $0.0028 | miss $0.14 | output $0.28
    deepseek-v4-pro   : input cache hit $0.003625 | miss $0.435 | output $0.87
                        (75 % discount through 2026/05/31)

A single review of the entire Burgers-verifier project (~20k input tokens of
context + 1k prompt + 3k response) costs ~$0.012 on first query (cache miss)
and ~$0.003 per cached re-use on v4-pro.

Each query emits a JSON receipt with token counts, model, cost, response-text
hash, and the SHA-256 of every cached file at query-time. The receipt is the
DeepSeek-side analogue of the Burgers-verifier's per-run DAG.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import sys
import uuid
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional

import requests

REPO = Path(__file__).resolve().parents[3]
RECEIPTS_DIR = REPO / "shared-data" / "artifacts" / "deepseek_review"
ENV_FILE = REPO / ".env"

# --- Pricing constants (mirrored to DeepSeekBudgetCalculator.lean) ---
PRICING_USD_PER_1M = {
    "deepseek-v4-flash": {"input_cache_hit": 0.0028, "input_cache_miss": 0.14, "output": 0.28},
    "deepseek-v4-pro":   {"input_cache_hit": 0.003625, "input_cache_miss": 0.435, "output": 0.87},
}

ANTHROPIC_COMPAT_BASE = "https://api.deepseek.com/anthropic"
ANTHROPIC_API_VERSION = "2023-06-01"


# =============================================================================
# Result type + cost calculation (mirror of the Lean module)
# =============================================================================

@dataclass
class ReviewResult:
    model: str
    tier: str
    response_text: str
    input_tokens: int
    output_tokens: int
    cache_creation_input_tokens: int
    cache_read_input_tokens: int
    cost_usd: float
    cost_breakdown: dict
    cached_context_files: list
    receipt_path: str | None = None
    receipt_id: str = ""


def cost_for_query(model: str, fresh_input: int, cached_input: int, output: int) -> dict:
    """Compute USD cost given token counts. Mirrors Semantics.DeepSeek.queryCost."""
    if model not in PRICING_USD_PER_1M:
        raise ValueError(f"unknown model {model!r}; known: {list(PRICING_USD_PER_1M)}")
    p = PRICING_USD_PER_1M[model]
    cached_cost = (cached_input / 1_000_000.0) * p["input_cache_hit"]
    fresh_cost = (fresh_input / 1_000_000.0) * p["input_cache_miss"]
    output_cost = (output / 1_000_000.0) * p["output"]
    return {
        "cached_input_cost": cached_cost,
        "fresh_input_cost": fresh_cost,
        "output_cost": output_cost,
        "total_usd": cached_cost + fresh_cost + output_cost,
    }


def estimate_cost(model: str, fresh_input: int, cached_input: int, output: int) -> float:
    return cost_for_query(model, fresh_input, cached_input, output)["total_usd"]


# =============================================================================
# .env loader  (just for DEEPSEEK_API_KEY — no python-dotenv required)
# =============================================================================

def _load_api_key_from_env_file() -> Optional[str]:
    if not ENV_FILE.exists():
        return None
    for line in ENV_FILE.read_text().splitlines():
        if line.startswith("DEEPSEEK_API_KEY="):
            return line.split("=", 1)[1].strip()
    return None


# =============================================================================
# Project-context bundle
# =============================================================================

@dataclass
class ContextFile:
    path: str
    sha256: str
    bytes: int
    snippet_head: str  # first 80 chars for human-readable receipts


def gather_project_context(paths: list[Path]) -> tuple[str, list[ContextFile]]:
    """Concatenate file contents for cache-prefix; return (context_text, file_metadata)."""
    parts: list[str] = []
    metadata: list[ContextFile] = []
    for p in paths:
        if not p.exists():
            sys.stderr.write(f"WARN: cached-context file missing: {p}\n")
            continue
        body = p.read_bytes()
        text = body.decode("utf-8", errors="replace")
        rel = str(p.relative_to(REPO)) if p.is_relative_to(REPO) else str(p)
        parts.append(f"\n\n===== FILE: {rel} =====\n{text}")
        metadata.append(ContextFile(
            path=rel,
            sha256="sha256:" + hashlib.sha256(body).hexdigest(),
            bytes=len(body),
            snippet_head=text[:80].replace("\n", "\\n"),
        ))
    return "".join(parts), metadata


# Default project context for Burgers-verifier work.
# Edit this list per evening to focus DeepSeek on what you want reviewed.
DEFAULT_CONTEXT_PATHS = [
    REPO / "5-Applications" / "tools-scripts" / "verifier" / "burgers_verifier.py",
    REPO / "5-Applications" / "tools-scripts" / "verifier" / "audit_gsp_variants.py",
    REPO / "5-Applications" / "tools-scripts" / "verifier" / "run_dag.py",
    REPO / "shared-data" / "artifacts" / "burgers_verifier" / "findings_2026-05-03.md",
    REPO / "shared-data" / "artifacts" / "burgers_verifier" / "perceval_repro_analysis.md",
]


# =============================================================================
# Adapter
# =============================================================================

class DeepSeekReviewer:
    """
    Tier-aware DeepSeek client with project-context caching and per-query receipts.

    Tiers:
      "flash" → deepseek-v4-flash (default; cheap)
      "pro"   → deepseek-v4-pro   (escalate; ~3× cost)
      "local" → local Ollama via existing infra/deepseek_adapter.py (free)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        cached_context_paths: Optional[list[Path]] = None,
        receipts_dir: Path = RECEIPTS_DIR,
    ):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY") or _load_api_key_from_env_file()
        self.cached_context_paths = cached_context_paths or DEFAULT_CONTEXT_PATHS
        self.receipts_dir = receipts_dir
        self.receipts_dir.mkdir(parents=True, exist_ok=True)

        # Materialise context once at construction; the same prefix string is sent
        # every query so DeepSeek can cache-hit on it.
        self.context_text, self.context_files = gather_project_context(self.cached_context_paths)

    # ------------------------------------------------------------------
    # Cost-only path (no API call) — useful for dry-run and budget planning
    # ------------------------------------------------------------------

    def estimate_review_cost(self, prompt: str, tier: str = "flash",
                              expected_output_tokens: int = 3000,
                              first_query: bool = True) -> dict:
        """Estimate USD cost for a hypothetical review without calling the API.

        Token counts use the conservative ~4-chars-per-token rule of thumb.
        Use `first_query=True` for cache-miss (entire context billed at miss rate),
        `False` for cache-hit (re-use within the cache TTL).
        """
        model = self._tier_to_model(tier)
        if model == "local":
            return {"model": "local", "cost_usd": 0.0,
                    "note": "local Ollama; free at the margin"}
        ctx_tokens = self._tokens_estimate(self.context_text)
        prompt_tokens = self._tokens_estimate(prompt)
        if first_query:
            return cost_for_query(model, fresh_input=ctx_tokens + prompt_tokens,
                                  cached_input=0, output=expected_output_tokens) | {"model": model}
        return cost_for_query(model, fresh_input=prompt_tokens,
                              cached_input=ctx_tokens, output=expected_output_tokens) | {"model": model}

    # ------------------------------------------------------------------
    # Live review path
    # ------------------------------------------------------------------

    def review(
        self,
        prompt: str,
        tier: str = "flash",
        max_output_tokens: int = 4000,
        receipt_label: str = "review",
    ) -> ReviewResult:
        """Submit a review query. Always includes the cached project context."""
        model = self._tier_to_model(tier)
        if model == "local":
            return self._review_local(prompt, max_output_tokens, receipt_label)

        if not self.api_key:
            raise RuntimeError("DEEPSEEK_API_KEY missing; populate .env or pass api_key=")

        # Anthropic-compat payload with prompt caching on the system block.
        body = {
            "model": model,
            "max_tokens": max_output_tokens,
            "system": [
                {
                    "type": "text",
                    "text": (
                        "You are an adversarial reviewer for a research-stack project. "
                        "The cached context that follows is the project state. Read it "
                        "thoroughly. Then answer the user's prompt as a sceptical "
                        "second set of eyes — point out errors, weak claims, missing "
                        "evidence, fluent-but-wrong reasoning, unstated assumptions. "
                        "Be specific and cite file paths or line numbers when possible."
                    ),
                },
                {
                    "type": "text",
                    "text": self.context_text,
                    "cache_control": {"type": "ephemeral"},
                },
            ],
            "messages": [{"role": "user", "content": prompt}],
        }
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": ANTHROPIC_API_VERSION,
            "Content-Type": "application/json",
        }
        url = f"{ANTHROPIC_COMPAT_BASE}/v1/messages"
        resp = requests.post(url, headers=headers, json=body, timeout=120)
        resp.raise_for_status()
        data = resp.json()

        # Anthropic-shaped response: {"content": [{"type": "text", "text": "..."}], "usage": {...}}
        text_blocks = [b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"]
        response_text = "\n".join(text_blocks)
        usage = data.get("usage", {})
        in_tokens = usage.get("input_tokens", 0)
        out_tokens = usage.get("output_tokens", 0)
        cache_creation = usage.get("cache_creation_input_tokens", 0)
        cache_read = usage.get("cache_read_input_tokens", 0)

        breakdown = cost_for_query(
            model,
            fresh_input=in_tokens + cache_creation,  # cache_creation tokens billed at miss rate
            cached_input=cache_read,
            output=out_tokens,
        )
        result = ReviewResult(
            model=model, tier=tier, response_text=response_text,
            input_tokens=in_tokens, output_tokens=out_tokens,
            cache_creation_input_tokens=cache_creation,
            cache_read_input_tokens=cache_read,
            cost_usd=breakdown["total_usd"],
            cost_breakdown=breakdown,
            cached_context_files=[asdict(f) for f in self.context_files],
        )
        self._write_receipt(result, prompt, receipt_label)
        return result

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _tier_to_model(tier: str) -> str:
        tier = tier.lower()
        if tier == "flash":
            return "deepseek-v4-flash"
        if tier == "pro":
            return "deepseek-v4-pro"
        if tier == "local":
            return "local"
        raise ValueError(f"unknown tier {tier!r}; choose 'flash', 'pro', or 'local'")

    @staticmethod
    def _tokens_estimate(text: str) -> int:
        # Conservative: ~4 chars per token (English text + code averages 3-5).
        return max(1, len(text) // 4)

    def _review_local(self, prompt: str, max_output_tokens: int, receipt_label: str) -> ReviewResult:
        """Falls through to the existing infra/deepseek_adapter.py path."""
        sys.path.insert(0, str(REPO / "4-Infrastructure"))
        from infra.deepseek_adapter import DeepSeekV4  # type: ignore[import-not-found]

        client = DeepSeekV4(use_local=True)
        # Same context-prefix pattern in the user message; local has no caching.
        user_msg = f"{self.context_text}\n\n=== REVIEW REQUEST ===\n{prompt}"
        res = client.chat([{"role": "user", "content": user_msg}], model="deepseek-r1:8b")
        text = res.get("message", {}).get("content", "") if isinstance(res, dict) else ""
        result = ReviewResult(
            model="local:deepseek-r1:8b", tier="local", response_text=text,
            input_tokens=self._tokens_estimate(user_msg),
            output_tokens=self._tokens_estimate(text),
            cache_creation_input_tokens=0, cache_read_input_tokens=0,
            cost_usd=0.0,
            cost_breakdown={"note": "local Ollama; free at the margin"},
            cached_context_files=[asdict(f) for f in self.context_files],
        )
        self._write_receipt(result, prompt, receipt_label)
        return result

    def _write_receipt(self, result: ReviewResult, prompt: str, label: str) -> None:
        receipt_id = f"{label}-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
        receipt = {
            "schema_version": "1.0",
            "receipt_id": receipt_id,
            "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "model": result.model,
            "tier": result.tier,
            "prompt_sha256": "sha256:" + hashlib.sha256(prompt.encode()).hexdigest(),
            "prompt_head": prompt[:200],
            "response_sha256": "sha256:" + hashlib.sha256(result.response_text.encode()).hexdigest(),
            "response_head": result.response_text[:200],
            "tokens": {
                "input": result.input_tokens,
                "output": result.output_tokens,
                "cache_creation": result.cache_creation_input_tokens,
                "cache_read": result.cache_read_input_tokens,
            },
            "cost_usd": result.cost_usd,
            "cost_breakdown": result.cost_breakdown,
            "cached_context_files": result.cached_context_files,
        }
        path = self.receipts_dir / f"{receipt_id}.receipt.json"
        path.write_text(json.dumps(receipt, indent=2, default=str))
        result.receipt_path = str(path.relative_to(REPO))
        result.receipt_id = receipt_id


# =============================================================================
# CLI
# =============================================================================

def _cli():
    import argparse
    ap = argparse.ArgumentParser(description="DeepSeek review wrapper with project-context caching")
    ap.add_argument("prompt", nargs="?", help="review prompt (read from stdin if omitted)")
    ap.add_argument("--tier", default="flash", choices=["flash", "pro", "local"])
    ap.add_argument("--max-tokens", type=int, default=4000)
    ap.add_argument("--label", default="review")
    ap.add_argument("--dry-run", action="store_true",
                    help="estimate cost only; do not call API")
    ap.add_argument("--first-query", action="store_true",
                    help="(dry-run) treat as cache-miss")
    args = ap.parse_args()

    prompt = args.prompt or sys.stdin.read()
    reviewer = DeepSeekReviewer()

    if args.dry_run:
        est = reviewer.estimate_review_cost(prompt, tier=args.tier,
                                            expected_output_tokens=args.max_tokens,
                                            first_query=args.first_query)
        print(json.dumps({"dry_run": True, "estimate": est,
                          "context_files": [f.path for f in reviewer.context_files]}, indent=2))
        return

    result = reviewer.review(prompt, tier=args.tier, max_output_tokens=args.max_tokens,
                             receipt_label=args.label)
    print(f"\n=== model={result.model} cost=${result.cost_usd:.4f} ===\n")
    print(result.response_text)
    print(f"\n=== receipt: {result.receipt_path} ===")


if __name__ == "__main__":
    _cli()
