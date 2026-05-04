#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
# PTOS: LAYER=CORE / DOMAIN=COMPUTE / CONDITION=EXPERIMENTAL / STAGE=ACTIVE / SOURCE=CODE
"""
ISO Cross-Product Residual Analyser
=====================================
**concept_anchor:** domain=compression / concept=cross_product_residual_axis /
                    resolution=FORMING

THE THIRD AXIS
--------------
Pass 1 (ISO prepass) operates as the binary thinker: match or no-match.
It finds discrete known symbols and substitutes them.

Pass 2 (bits-back / frequency prior) operates as the laminar flow thinker:
smooth probability distribution over the matched tokens.  It models how
*common* each match is within its domain.

Neither pass looks at CONTEXT between domains.  A geo token appearing next
to a chem token, a bio token following a math token — these cross-domain
positional relationships are invisible to both passes.

The cross-product residual is everything above the expected independence:

  residual(A, B) = observed_cooccurrence(domain_A, domain_B)
                 - expected_cooccurrence(domain_A) * expected_cooccurrence(domain_B)

If residual is positive and recurring: a new compression primitive is hiding
there.  Encoding the pair jointly rather than independently would save bits.
If the residual distribution is heavy-tailed (power law): the structure is
scale-free — the same principle recurs across different specific tokens.

This is the "third impossible axis": it requires both passes to exist (you
need to have matched the symbols before you can measure their positional
relationship) but is orthogonal to what either pass alone can represent.

WHAT THIS PRODUCES
------------------
  1. Co-occurrence matrix: P(domain_A near domain_B) for all domain pairs
  2. Expected matrix:      P(domain_A) * P(domain_B)  (independence baseline)
  3. Residual matrix:      observed - expected
  4. Surprise distribution for the residual (is it heavy-tailed?)
  5. Top cross-domain bigrams: token_A in domain_A followed by token_B in domain_B
     within a configurable window — these are new symbol table candidates

COMPRESSION IMPLICATION
-----------------------
If domain pair (A, B) shows strong positive residual AND the top bigrams
are consistent across documents, then:
  - Add a new iso_cross domain to iso_symbol_table
  - Each bigram becomes a cross-domain compound symbol
  - Pass 1.5 (between ISO prepass and entropy coder) encodes these pairs

HOW TO USE
----------
  # Analyse 1MB of enwik8
  python3 5-Applications/scripts/iso_cross.py shared-data/data/enwik8 --bytes 1000000

  # Show top N cross-domain bigrams
  python3 5-Applications/scripts/iso_cross.py shared-data/data/enwik8 --bytes 1000000 --top 20

  # Write a candidate domain entry to stdout
  python3 5-Applications/scripts/iso_cross.py shared-data/data/enwik8 --bytes 1000000 --emit-candidates
"""

from __future__ import annotations

import argparse
import math
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    from iso_symbol_table import prepass as iso_prepass, EXTENDED_DOMAINS, PTOS_DOMAINS
    _ISO_AVAILABLE = True
except ImportError:
    _ISO_AVAILABLE = False
    print("[error] iso_symbol_table not available", file=sys.stderr)
    sys.exit(1)

try:
    from bits_back_iso import _surprise_bits
    _BB_AVAILABLE = True
except ImportError:
    _BB_AVAILABLE = False

from iso_pipeline import run_windowed_pass, PipelineResult, corpus_adaptive_thresholds, run_chunked_pass


# ─── configuration ────────────────────────────────────────────────────────────

WINDOW_BYTES    = 200    # co-occurrence window: tokens within this many chars are "near"
CHUNK_SIZE      = 65_536
DOMAINS_TO_USE  = EXTENDED_DOMAINS

# Big Bang phase thresholds (bits of surprise).
# Calibrated against enwik8 500KB: surprise distribution is bimodal —
# common tokens cluster at 3–6 bits; floor-probability tokens (not in prior
# table) all land at 16.6 bits.  Setting thresholds at 10 / 5.5 splits:
#   Phase 1: rare tokens + floor-prob tokens (highest energy)
#   Phase 2: mid-frequency tokens in prior table (7–13 bits range in practice)
#   Phase 3: common tokens well-predicted by prior (lang codes, top geo)
PHASE1_THRESHOLD = 10.0   # > this → Phase 1 (high-energy / inflationary)
PHASE3_THRESHOLD  = 5.5   # < this → Phase 3 (low-energy / structure formation)
# Between thresholds → Phase 2 (matter-dominated)


# ─── core analysis ────────────────────────────────────────────────────────────

def _coupling_stats(result: PipelineResult) -> dict:
    """Extract Big Bang coupling statistics from a completed PipelineResult.

    Returns the same shape as the old _coupling_strength() but derived from
    the single run_windowed_pass() result — no second traversal needed.
    """
    if not _BB_AVAILABLE:
        return {"error": "bits_back_iso not available — cannot compute surprise"}

    p3_total    = result.phase_counts[3]
    p3_coupled  = result.phase3_coupled
    cf          = p3_coupled / max(p3_total, 1)

    top_couplings = sorted(
        [(t1, d1, t3, d3, cnt)
         for (t1, d1, t3, d3), cnt in result.coupling_pairs.items()],
        key=lambda x: -x[4],
    )

    return {
        "phase_counts":      dict(result.phase_counts),
        "phase3_total":      p3_total,
        "phase3_coupled":    p3_coupled,
        "coupling_fraction": round(cf, 4),
        "top_couplings":     top_couplings[:20],
        "inflationary_size": round(cf, 4),
    }


def _residual_matrix(
    domain_counts: Counter,
    pair_counts: Counter,
    total_tokens: int,
) -> dict[tuple[str, str], float]:
    """Compute observed - expected co-occurrence for each domain pair.

    Expected under independence: P(A) * P(B) * total_pairs
    where P(domain) = domain_counts[domain] / total_tokens
    """
    total_pairs = sum(pair_counts.values()) or 1
    residuals: dict[tuple[str, str], float] = {}

    for (da, db), observed in pair_counts.items():
        pa = domain_counts[da] / total_tokens
        pb = domain_counts[db] / total_tokens
        expected = pa * pb * total_pairs
        residuals[(da, db)] = observed - expected

    return residuals


def _surprise_distribution(
    bigram_counts: Counter,
    residuals: dict[tuple[str, str], float],
) -> list[tuple[float, str, str, str, str, int]]:
    """Score each cross-domain bigram by its residual contribution.

    Returns list of (score, tok_a, dom_a, tok_b, dom_b, count) sorted descending.
    Score = residual(dom_a, dom_b) * count  — how much of the pair residual this
    bigram contributes.
    """
    pair_total: Counter = Counter()
    for (ta, da, tb, db), cnt in bigram_counts.items():
        pair_total[(da, db)] += cnt

    scored = []
    for (ta, da, tb, db), cnt in bigram_counts.items():
        res = residuals.get((da, db), 0.0)
        if res <= 0:
            continue
        # weight by fraction of this bigram in the pair's total
        frac = cnt / max(pair_total[(da, db)], 1)
        score = res * frac * cnt
        # also factor in bits-back surprise if available
        if _BB_AVAILABLE:
            sa = _surprise_bits(ta, da)
            sb = _surprise_bits(tb, db)
            # high surprise in both passes = most orthogonal to both world views
            cross_surprise = (sa + sb) / 2.0
        else:
            cross_surprise = 1.0
        scored.append((score * cross_surprise, ta, da, tb, db, cnt))

    scored.sort(reverse=True)
    return scored


def _is_power_law(counts: list[int]) -> tuple[bool, float]:
    """Rough power-law check on count distribution.

    Fits log(count) ~ alpha * log(rank) via least-squares.
    Returns (is_heavy_tailed, alpha) where alpha < -0.7 is heavy-tailed.
    """
    if len(counts) < 4:
        return False, 0.0
    sorted_counts = sorted(counts, reverse=True)
    log_ranks  = [math.log(i + 1) for i in range(len(sorted_counts))]
    log_counts = [math.log(max(c, 1)) for c in sorted_counts]
    n = len(log_ranks)
    sx = sum(log_ranks)
    sy = sum(log_counts)
    sxy = sum(log_ranks[i] * log_counts[i] for i in range(n))
    sxx = sum(x ** 2 for x in log_ranks)
    denom = n * sxx - sx * sx
    if abs(denom) < 1e-12:
        return False, 0.0
    alpha = (n * sxy - sx * sy) / denom
    return alpha < -0.7, round(alpha, 3)


# ─── analysis entry point ─────────────────────────────────────────────────────

def _print_pass1(log: dict, text: str, compressed: str) -> None:
    """Print Pass 1 (ISO prepass) stats."""
    total_matches = sum(len(v) for v in log.values())
    print("\nPass 1 (ISO prepass):")
    print(f"  Domains fired  : {list(log.keys())}")
    print(f"  Total matches  : {total_matches:,}")
    print(f"  Input bytes    : {len(text.encode('utf-8')):,}")
    print(f"  After prepass  : {len(compressed.encode('utf-8')):,}")


def _print_pass2(log: dict) -> None:
    """Print Pass 2 (bits-back surprise) stats if available."""
    if not _BB_AVAILABLE:
        return
    avg_surprise = {}
    for domain, tokens in log.items():
        surprises = [_surprise_bits(t, domain) for t in tokens]
        if surprises:
            avg_surprise[domain] = sum(surprises) / len(surprises)
    print("\nPass 2 (bits-back surprise per domain):")
    for d, s in sorted(avg_surprise.items(), key=lambda x: -x[1]):
        print(f"  {d:<14}  avg_surprise={s:.2f} bits")


def _print_residual_matrix(
    residuals: dict,
    pair_counts: Counter,
    domain_counts: Counter,
    total_tokens: int,
) -> None:
    """Print the observed-minus-expected co-occurrence matrix."""
    print("\nResidual matrix (observed - expected co-occurrence):")
    total_pairs = sum(pair_counts.values())
    for (da, db), res in sorted(residuals.items(), key=lambda x: -x[1])[:8]:
        obs = pair_counts[(da, db)]
        pa  = domain_counts[da] / total_tokens
        pb  = domain_counts[db] / total_tokens
        exp = pa * pb * total_pairs
        sign = "▲" if res > 0 else "▼"
        print(
            f"  {sign} {da:<12} × {db:<12}  "
            f"obs={obs:4d}  exp={exp:5.1f}  Δ={res:+6.1f}"
        )


def _print_bigrams(bigram_scored: list, top_n: int, emit_candidates: bool) -> None:
    """Print top cross-domain bigrams and optional candidate entries."""
    counts_only = [c for _, _, _, _, _, c in bigram_scored]
    is_heavy, alpha = _is_power_law(counts_only)

    label = "HEAVY-TAILED" if is_heavy else "not heavy-tailed"
    print("\nResidual distribution:")
    print(f"  Unique positive-residual bigrams: {len(bigram_scored)}")
    print(f"  Power-law fit alpha: {alpha}  ({label})")
    if is_heavy:
        print("  *** Heavy tail detected — recurring cross-domain structure present ***")
        print("      This is the signature of a compressible third axis.")

    hdr = f"  {'score':>8}  {'token_A':<20} {'dom_A':<13} → {'token_B':<20} {'dom_B':<13} cnt"
    sep = f"  {'-'*8}  {'-'*20} {'-'*13}   {'-'*20} {'-'*13} ---"
    print(f"\nTop {top_n} cross-domain bigrams (new symbol candidates):")
    print(hdr)
    print(sep)
    for score, ta, da, tb, db, cnt in bigram_scored[:top_n]:
        print(f"  {score:8.2f}  {ta:<20} {da:<13} → {tb:<20} {db:<13} {cnt}")

    if emit_candidates and bigram_scored:
        print("\n--- CANDIDATE ISO_CROSS DOMAIN ENTRIES ---")
        print("# Add these to iso_symbol_table.py as a new 'iso_cross' domain")
        print("# Each entry is a cross-domain compound that co-occurs above expectation")
        print()
        seen: set[str] = set()
        for score, ta, da, tb, db, cnt in bigram_scored[:top_n]:
            compound = f"{ta} {tb}"
            if compound in seen:
                continue
            seen.add(compound)
            domains_str = f'["{da}", "{db}"]'
            print(
                f'    "{compound}": {{'
                f'"domains": {domains_str}, "score": {score:.2f}, "count": {cnt}'
                f'}},'
            )


def _print_summary(
    pair_counts: Counter,
    domain_counts: Counter,
    residuals: dict,
    total_tokens: int,
) -> None:
    """Print cross-product residual summary and next-step guidance."""
    total_cross_pairs = sum(pair_counts.values())
    total_expected = sum(
        (domain_counts[da] / total_tokens)
        * (domain_counts[db] / total_tokens)
        * total_cross_pairs
        for (da, db) in pair_counts
    )
    total_residual    = sum(r for r in residuals.values() if r > 0)
    residual_fraction = total_residual / max(total_cross_pairs, 1)

    print("\n" + "=" * 60)
    print("CROSS-PRODUCT RESIDUAL SUMMARY")
    print(f"  Total cross-domain co-occurrences: {total_cross_pairs:,}")
    print(f"  Expected under independence:        {total_expected:.1f}")
    print(f"  Positive residual (above expected): {total_residual:.1f}")
    print(f"  Residual fraction:                  {residual_fraction:.3f}")
    if residual_fraction > 0.15:
        print(f"  *** {residual_fraction*100:.1f}% above independence baseline ***")
        print("      The two passes are leaving significant structure on the table.")
        print("      A Pass 1.5 encoding these cross-domain pairs would recover it.")
    elif residual_fraction > 0.05:
        print(f"  Moderate cross-domain structure ({residual_fraction*100:.1f}%). Worth monitoring.")
    else:
        print("  Low residual. Passes are nearly independent on this corpus.")

    print("\nNext step: if heavy-tailed and residual_fraction > 0.15,")
    print("  add top bigrams to iso_symbol_table as 'iso_cross' domain.")
    print("  That becomes Pass 1.5 — the third axis encoded as a symbol table.")


def _print_coupling_strength(
    result: PipelineResult,
    window: int,
    p1_t: float = PHASE1_THRESHOLD,
    p3_t: float = PHASE3_THRESHOLD,
) -> None:
    """Print Big Bang phase coupling strength — inflationary epoch size."""
    cs = _coupling_stats(result)
    if "error" in cs:
        print(f"\n[coupling strength: {cs['error']}]")
        return

    phases  = cs["phase_counts"]
    p1      = phases.get(1, 0)
    p2      = phases.get(2, 0)
    p3      = phases.get(3, 0)
    total   = p1 + p2 + p3 or 1
    cf      = cs["coupling_fraction"]
    p3t     = cs["phase3_total"]
    p3c     = cs["phase3_coupled"]

    print("\nBig Bang decompression profile:")
    print(f"  Phase 1 (inflationary,  >{p1_t:.2f} bits): "
          f"{p1:4d} tokens  ({p1/total*100:4.1f}%)")
    print(f"  Phase 2 (matter,   {p3_t:.2f}–{p1_t:.2f} bits): "
          f"{p2:4d} tokens  ({p2/total*100:4.1f}%)")
    print(f"  Phase 3 (scaffolding,   <{p3_t:.2f} bits): "
          f"{p3:4d} tokens  ({p3/total*100:4.1f}%)")
    print(f"\n  Phase 3 tokens coupled to Phase 1: {p3c}/{p3t}")
    print(f"  Inflationary epoch size: {cf*100:.1f}%  "
          f"({'STRONG' if cf > 0.5 else 'MODERATE' if cf > 0.25 else 'WEAK'} coupling)")

    if cf > 0.25 and cs["top_couplings"]:
        print("\n  Top Phase1→Phase3 couplings (skeleton predicts scaffolding):")
        hdr = "    {:<20} {:<13} → {:<20} {:<13} {}"
        print(hdr.format("phase1_token", "dom1", "phase3_token", "dom3", "cnt"))
        print("    " + "-" * 74)
        for t1, d1, t3, d3, cnt in cs["top_couplings"][:8]:
            print(f"    {t1:<20} {d1:<13} → {t3:<20} {d3:<13} {cnt}")

    if cf > 0.5:
        print(
            f"\n  *** {cf*100:.1f}% of low-energy tokens are predicted by the"
            " high-energy skeleton ***"
        )
        print("      Encoder can omit them; decoder reconstructs by attraction.")
        print("      Minimum induced energy to decompress = Phase 1 tokens only.")


def analyse(
    path: Path,
    n_bytes: int = 1_000_000,
    window: int = WINDOW_BYTES,
    top_n: int = 15,
    emit_candidates: bool = False,
    domains: list[str] | None = None,
    adaptive: bool = False,
) -> None:
    """Run full cross-product residual analysis on the given file.

    domains  : override DOMAINS_TO_USE (pass PTOS_DOMAINS for Research Stack)
    adaptive : derive phase thresholds from this corpus (p90/p25) instead of
               using the enwik8-calibrated defaults
    """
    if domains is None:
        domains = list(DOMAINS_TO_USE)

    with open(path, "rb") as f:
        raw = f.read(n_bytes)
    try:
        text = raw.decode("utf-8", errors="replace")
    except (UnicodeDecodeError, ValueError):
        text = raw.decode("latin-1", errors="replace")

    print(f"Input: {len(raw):,} bytes from {path.name}")
    print(f"Domains: {domains}")

    compressed, log = iso_prepass(text, domains=domains)
    total_matches = sum(len(v) for v in log.values())
    _print_pass1(log, text, compressed)
    if total_matches == 0:
        print("\n[no matches — cannot compute cross-product residual]")
        return

    _print_pass2(log)

    # Corpus-adaptive thresholds: quick chunked pass to calibrate, then full pass
    p1_t, p3_t = PHASE1_THRESHOLD, PHASE3_THRESHOLD
    if adaptive:
        cal = run_chunked_pass(text, chunk_size=65_536, max_chunks=16,
                               strategy="uniform", domains=domains)
        p1_t, p3_t = corpus_adaptive_thresholds(cal)
        print(f"\nCorpus-adaptive thresholds (p90/p25): "
              f"Phase1 > {p1_t:.2f} bits, Phase3 < {p3_t:.2f} bits")

    result = run_windowed_pass(
        text, window=window, domains=domains,
        phase1_t=p1_t, phase3_t=p3_t,
    )
    total_tokens = result.total_tokens() or 1
    print(f"\nCo-occurrence (window={window} chars):")
    print(f"  Cross-domain pairs observed: {sum(result.pair_counts.values()):,}")
    print(f"  Unique domain pairs        : {len(result.pair_counts)}")
    print(f"  Unique cross-domain bigrams: {len(result.bigram_counts)}")

    residuals     = _residual_matrix(result.domain_counts, result.pair_counts,
                                     total_tokens)
    bigram_scored = _surprise_distribution(result.bigram_counts, residuals)

    _print_residual_matrix(residuals, result.pair_counts, result.domain_counts,
                           total_tokens)
    _print_bigrams(bigram_scored, top_n, emit_candidates)
    _print_summary(result.pair_counts, result.domain_counts, residuals, total_tokens)

    # ── Big Bang coupling strength (from the same pass — no extra traversal) ──
    _print_coupling_strength(result, window, p1_t=p1_t, p3_t=p3_t)


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="ISO cross-product residual analyser — find the third axis"
    )
    parser.add_argument("path", type=Path, help="input file (enwik8 or any text/XML)")
    parser.add_argument("--bytes", type=int, default=1_000_000,
                        help="bytes to read from input (default 1MB)")
    parser.add_argument("--window", type=int, default=WINDOW_BYTES,
                        help=f"co-occurrence window in chars (default {WINDOW_BYTES})")
    parser.add_argument("--top", type=int, default=15,
                        help="top N bigrams to display (default 15)")
    parser.add_argument("--emit-candidates", action="store_true",
                        help="print candidate iso_cross domain entries")
    parser.add_argument("--ptos", action="store_true",
                        help="use PTOS_DOMAINS instead of EXTENDED_DOMAINS")
    parser.add_argument("--adaptive", action="store_true",
                        help="derive phase thresholds from this corpus (p90/p25)")
    args = parser.parse_args()

    if not args.path.exists():
        print(f"[error] file not found: {args.path}", file=sys.stderr)
        sys.exit(1)

    domains = list(PTOS_DOMAINS) if args.ptos else None
    analyse(args.path, n_bytes=args.bytes, window=args.window,
            top_n=args.top, emit_candidates=args.emit_candidates,
            domains=domains, adaptive=args.adaptive)


if __name__ == "__main__":
    main()
