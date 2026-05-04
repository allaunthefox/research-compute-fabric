#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
# PTOS: LAYER=CORE / DOMAIN=COMPUTE / CONDITION=EXPERIMENTAL / STAGE=ACTIVE / SOURCE=CODE
"""
ISO Pipeline — Shared Single-Pass Windowed Analysis
=====================================================
**concept_anchor:** domain=compression / concept=iso_pipeline_shared_pass /
                    resolution=STABLE

PURPOSE
-------
Three modules were each implementing their own version of the same operation:

  "slide a window over text → run prepass per chunk → aggregate results"

  iso_cross._cooccurrence_from_chunks  — co-occurrence + bigrams
  iso_cross._coupling_strength         — phase-sorted coupling (second pass!)
  ingest_large_file.process_file       — semantic fingerprint for indexing

This module is the single implementation that all three call.  One traversal
of the text produces everything all three need:

  - substitution log (iso_prepass output)
  - per-token surprise scores (bits-back prior)
  - domain counts
  - cross-domain co-occurrence pairs
  - cross-domain bigrams
  - phase-classified token lists (Phase 1 / 2 / 3 by surprise)

ARCHITECTURE
------------
iso_symbol_table.py   symbols + EXTENDED_DOMAINS
        ↓
iso_pipeline.py       ← THIS FILE: shared windowed pass
        ↓
bits_back_iso.py      encode_log / decode_log (log encoding only)
iso_cross.py          residual analysis  (calls run_windowed_pass)
ingest_large_file.py  ingestion          (calls run_windowed_pass or run_chunked_pass)

USAGE
-----
  from iso_pipeline import run_windowed_pass, run_chunked_pass, PipelineResult

  # Cross-product residual / coupling analysis (overlapping windows)
  result = run_windowed_pass(text, window=200)

  # Large-file ingestion (non-overlapping uniform samples)
  result = run_chunked_pass(text, chunk_size=65536, max_chunks=256)

  # Access everything from one result
  result.domain_counts        # Counter: domain → total token count
  result.pair_counts          # Counter: (dom_A, dom_B) → co-occurrence count
  result.bigram_counts        # Counter: (tok_a, dom_a, tok_b, dom_b) → count
  result.all_tokens           # list of TokenRecord
  result.phase_counts         # Counter: 1/2/3 → token count
  result.phase1_tokens        # list of TokenRecord (high-energy)
  result.phase3_tokens        # list of TokenRecord (scaffolding)
"""

from __future__ import annotations

import math
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple

sys.path.insert(0, str(Path(__file__).parent))

from iso_symbol_table import (
    prepass as iso_prepass,
    EXTENDED_DOMAINS,
    normalize_latex_math,
)

try:
    from bits_back_iso import _surprise_bits
    _BB_AVAILABLE = True
except ImportError:
    _BB_AVAILABLE = False


# ─── phase thresholds ─────────────────────────────────────────────────────────
# Calibrated from enwik8 500KB surprise distribution:
#   p25 = 4.3 bits (common tokens, well-predicted)
#   p75 = 16.6 bits (floor-probability tokens, not in prior table)
# Corpus-adaptive override: pass phase1_t / phase3_t to run_*_pass().

PHASE1_DEFAULT = 10.0   # > this → Phase 1 (inflationary / high-energy)
PHASE3_DEFAULT  = 5.5   # < this → Phase 3 (scaffolding / low-energy)


# ─── data types ───────────────────────────────────────────────────────────────

class TokenRecord(NamedTuple):
    """One matched token from the ISO prepass with its surprise score."""
    token:   str
    domain:  str
    surprise: float   # -log₂(p(token|domain)); 0.0 if bits_back_iso unavailable


@dataclass
class PipelineResult:
    """Everything produced by one windowed pass over the text."""
    domain_counts:  Counter = field(default_factory=Counter)
    pair_counts:    Counter = field(default_factory=Counter)
    bigram_counts:  Counter = field(default_factory=Counter)
    all_tokens:     list[TokenRecord] = field(default_factory=list)
    phase_counts:   Counter = field(default_factory=Counter)
    phase1_tokens:  list[TokenRecord] = field(default_factory=list)
    phase3_tokens:  list[TokenRecord] = field(default_factory=list)
    # Phase 1 × Phase 3 coupling: (p1_tok, p1_dom, p3_tok, p3_dom) → count
    coupling_pairs: Counter = field(default_factory=Counter)
    # Phase 3 token appearances in windows that also contain Phase 1 tokens
    phase3_coupled: int = 0
    # Per-domain aggregates
    surprise_sums:  Counter = field(default_factory=Counter)
    windows_seen:   int = 0

    def avg_surprise(self, domain: str) -> float:
        """Mean surprise for a domain (0 if no tokens seen)."""
        n = self.domain_counts[domain]
        return self.surprise_sums[domain] / n if n else 0.0

    def total_tokens(self) -> int:
        """Total matched tokens across all domains."""
        return sum(self.domain_counts.values())


# ─── core window processor ────────────────────────────────────────────────────

def _process_window(
    chunk: str,
    result: PipelineResult,
    domains: list[str],
    phase1_t: float,
    phase3_t: float,
) -> None:
    """Run prepass on one chunk and accumulate into result (in-place)."""
    normalized_chunk = normalize_latex_math(chunk)
    _, chunk_log = iso_prepass(normalized_chunk, domains=domains)
    if not chunk_log:
        return

    result.windows_seen += 1
    window_tokens: list[tuple[str, str, float]] = []
    p1_window: list[tuple[str, str]] = []  # (token, domain) for Phase 1
    p3_window: list[tuple[str, str]] = []  # (token, domain) for Phase 3

    for domain, tokens in chunk_log.items():
        for tok in tokens:
            s = _surprise_bits(tok, domain) if _BB_AVAILABLE else 0.0
            result.domain_counts[domain] += 1
            result.surprise_sums[domain] += s
            rec = TokenRecord(tok.lower(), domain, s)
            result.all_tokens.append(rec)
            window_tokens.append((tok.lower(), domain, s))

            if s > phase1_t:
                result.phase_counts[1] += 1
                result.phase1_tokens.append(rec)
                p1_window.append((tok.lower(), domain))
            elif s < phase3_t:
                result.phase_counts[3] += 1
                result.phase3_tokens.append(rec)
                p3_window.append((tok.lower(), domain))
            else:
                result.phase_counts[2] += 1

    # Cross-domain pairs and bigrams
    for i, (ta, da, _) in enumerate(window_tokens):
        for j, (tb, db, _) in enumerate(window_tokens):
            if i != j and da != db:
                result.pair_counts[(da, db)] += 1
                result.bigram_counts[(ta, da, tb, db)] += 1

    # Phase 1 × Phase 3 coupling (Coulomb binding field)
    if p1_window and p3_window:
        result.phase3_coupled += len(p3_window)
        for t1, d1 in p1_window:
            for t3, d3 in p3_window:
                result.coupling_pairs[(t1, d1, t3, d3)] += 1


# ─── public API ───────────────────────────────────────────────────────────────

def run_windowed_pass(
    text: str,
    window: int = 200,
    domains: list[str] | None = None,
    phase1_t: float = PHASE1_DEFAULT,
    phase3_t: float = PHASE3_DEFAULT,
) -> PipelineResult:
    """Sliding-window pass with 50% overlap — for co-occurrence / residual analysis.

    Every token appears in approximately 2 windows, giving robust co-occurrence
    counts.  Use for iso_cross residual analysis and coupling strength.
    """
    if domains is None:
        domains = EXTENDED_DOMAINS
    result = PipelineResult()
    step = window // 2
    n = len(text)
    for start in range(0, n, step):
        _process_window(text[start: start + window], result, domains,
                        phase1_t, phase3_t)
    return result


def run_chunked_pass(
    text: str,
    chunk_size: int = 65_536,
    max_chunks: int = 256,
    strategy: str = "uniform",
    domains: list[str] | None = None,
    phase1_t: float = PHASE1_DEFAULT,
    phase3_t: float = PHASE3_DEFAULT,
) -> PipelineResult:
    """Non-overlapping chunk pass — for large-file ingestion.

    Strategies:
      full      — every chunk sequentially (accurate, slow for large files)
      uniform   — evenly-spaced sample of max_chunks chunks
      head_tail — first N/2 + last N/2 chunks (catches header + conclusion)
    """
    if domains is None:
        domains = EXTENDED_DOMAINS
    n = len(text)
    total_chunks = math.ceil(n / chunk_size)

    if strategy == "full" or total_chunks <= max_chunks:
        offsets = list(range(0, n, chunk_size))
    elif strategy == "head_tail":
        half = max_chunks // 2
        head = list(range(0, min(half * chunk_size, n), chunk_size))
        tail_start = max(0, n - half * chunk_size)
        tail = list(range(tail_start, n, chunk_size))
        seen: set[int] = set()
        offsets = []
        for o in head + tail:
            if o not in seen:
                seen.add(o)
                offsets.append(o)
    else:  # uniform
        step = max(1, total_chunks // max_chunks)
        offsets = list(range(0, n, step * chunk_size))[:max_chunks]

    result = PipelineResult()
    for start in offsets:
        _process_window(text[start: start + chunk_size], result, domains,
                        phase1_t, phase3_t)
    return result


_FLOOR_BITS = 16.5   # tokens at -log2(1e-5) ≈ 16.61 are floor-probability;
                     # exclude them so the adaptive percentiles reflect the
                     # real distribution rather than being pulled up by missing priors.

def corpus_adaptive_thresholds(result: PipelineResult) -> tuple[float, float]:
    """Derive corpus-adaptive phase thresholds from observed surprise distribution.

    Returns (phase1_threshold, phase3_threshold) using p90 / p25 quantiles.
    Floor-probability tokens (surprise ≥ _FLOOR_BITS) are excluded so the
    thresholds reflect the real distribution, not the density of missing priors.
    Falls back to defaults if fewer than 10 non-floor tokens observed.
    """
    surprises = sorted(
        t.surprise for t in result.all_tokens
        if t.surprise < _FLOOR_BITS
    )
    n = len(surprises)
    if n < 10:
        return PHASE1_DEFAULT, PHASE3_DEFAULT
    p90 = surprises[int(n * 0.90)]
    p25 = surprises[int(n * 0.25)]
    return p90, p25
