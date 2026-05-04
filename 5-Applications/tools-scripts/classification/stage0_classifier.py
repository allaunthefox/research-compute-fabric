#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
# PTOS: LAYER=CORE / DOMAIN=COMPUTE / CONDITION=EXPERIMENTAL / STAGE=ACTIVE / SOURCE=CODE
"""
Stage 0: Document Type Classifier
===================================
**concept_anchor:** domain=compression / concept=stage0_document_classifier /
                    resolution=FORMING

PURPOSE
-------
Before the ISO prepass (Pass 1), classify the document type so the right
domain set and prior tables are applied.  A single symbol table tuned for
Wikipedia performs poorly on Python code, JSON sessions, or TSM files.

The classifier works from the cross-domain residual profile of a short
sample of the document.  Different document types have fundamentally
different residual fingerprints:

  Wikipedia article:  iso_geo × iso_lang dominant (country + language bias)
  Python source:      iso_code × iso_ptos dominant (keyword + operator bias)
  JSON session:       iso_ptos × iso_abbrev dominant (schema + abbreviation)
  TSM/ISA file:       iso_isa × iso_math dominant (opcode + physics)
  Scientific paper:   iso_chem × iso_math × iso_unit dominant

ARCHITECTURE
------------
  raw input
      ↓
  stage0_classifier.py   ← THIS FILE: probe a 4KB sample, emit doc_type
      ↓
  iso_symbol_table.py    use PTOS_DOMAINS / EXTENDED_DOMAINS / DEFAULT_DOMAINS
      ↓
  iso_pipeline.py        run_windowed_pass with corpus-adaptive thresholds
      ↓
  schema_encoder.py      structural Pass 1.5 for matching doc types

DOC TYPES
---------
  "wikipedia"    — encyclopedic text, heavy geo + lang
  "python"       — Python source code
  "json_session" — Research Stack session JSON
  "markdown"     — docs / PTOS schema markdown
  "tsm"          — TSM/metafoam opcode files
  "scientific"   — academic papers (chem + math + unit heavy)
  "mixed"        — cannot classify (use EXTENDED_DOMAINS)

USAGE
-----
  from stage0_classifier import classify, DOMAIN_SET_FOR

  doc_type = classify(text)
  domains  = DOMAIN_SET_FOR[doc_type]
  result   = run_windowed_pass(text, domains=domains)
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from iso_symbol_table import (
    prepass as iso_prepass,
    EXTENDED_DOMAINS,
    PTOS_DOMAINS,
    DEFAULT_DOMAINS,
    normalize_latex_math,
)

# ─── domain sets per document type ────────────────────────────────────────────

DOMAIN_SET_FOR: dict[str, list[str]] = {
    "wikipedia":    EXTENDED_DOMAINS,
    "python":       PTOS_DOMAINS,
    "json_session": PTOS_DOMAINS,
    "markdown":     PTOS_DOMAINS,
    "tsm":          PTOS_DOMAINS,
    "scientific":   EXTENDED_DOMAINS,
    "mixed":        EXTENDED_DOMAINS,
}

# ─── heuristic probes ─────────────────────────────────────────────────────────
# These run before the domain analysis and catch obvious structural markers.

_PY_PATTERN   = re.compile(r"^(#!/|import |from \w+ import|def |class |    def )",
                            re.MULTILINE)
_JSON_PATTERN = re.compile(r'"concept_anchor"\s*:|"idea_weights"\s*:|"session_id"\s*:')
_TSM_PATTERN  = re.compile(r'(0x[0-9A-Fa-f]{2}|INGEST_STATE|WAVE_FOLD|PHASE_LOCK'
                            r'|FOAM_SPRAY|WELD_SURFACE|tsm_metafoam)', re.IGNORECASE)
_MD_PATTERN   = re.compile(r'^#{1,6} |\*\*concept_anchor\*\*|^PTOS: LAYER=',
                            re.MULTILINE)
_SCI_PATTERN  = re.compile(r'(abstract|doi:|arxiv|journal of|proceedings of'
                            r'|et al\.|fig\.|eq\.|theorem)', re.IGNORECASE)


def _structural_classify(sample: str) -> str | None:
    """Fast structural pre-check — return doc_type or None if ambiguous."""
    if _JSON_PATTERN.search(sample):
        return "json_session"
    if _TSM_PATTERN.search(sample):
        return "tsm"
    if _PY_PATTERN.search(sample):
        return "python"
    if _MD_PATTERN.search(sample):
        return "markdown"
    if _SCI_PATTERN.search(sample):
        return "scientific"
    return None


# ─── domain-hit classifier ────────────────────────────────────────────────────

# Signature: (dominant_domain, secondary_domain) → doc_type
# Ordered by specificity — first match wins.
_DOMAIN_SIGNATURES: list[tuple[str, str | None, str]] = [
    ("iso_isa",   "iso_math",   "tsm"),
    ("iso_isa",   None,         "tsm"),
    ("iso_ptos",  "iso_abbrev", "json_session"),
    ("iso_ptos",  "iso_isa",    "tsm"),
    ("iso_ptos",  "iso_code",   "python"),
    ("iso_ptos",  None,         "markdown"),
    ("iso_code",  "iso_ptos",   "python"),
    ("iso_code",  None,         "python"),
    ("iso_chem",  "iso_math",   "scientific"),
    ("iso_unit",  "iso_math",   "scientific"),
    ("iso_geo",   "iso_lang",   "wikipedia"),
    ("iso_geo",   None,         "wikipedia"),
]


def classify(text: str, sample_bytes: int = 4096) -> str:
    """Classify document type from the first `sample_bytes` of text.

    Returns one of: "wikipedia", "python", "json_session", "markdown",
                    "tsm", "scientific", "mixed"
    """
    sample = text[:sample_bytes]

    # Fast path: structural markers are unambiguous
    structural = _structural_classify(sample)
    if structural is not None:
        return structural

    # Domain-hit analysis on the sample
    _, log = iso_prepass(normalize_latex_math(sample), domains=list(PTOS_DOMAINS))
    if not log:
        return "mixed"

    hit_counts = {domain: len(tokens) for domain, tokens in log.items()}
    ranked = sorted(hit_counts.items(), key=lambda x: -x[1])
    if not ranked:
        return "mixed"

    top_domain  = ranked[0][0]
    second_domain = ranked[1][0] if len(ranked) > 1 else None

    for sig_top, sig_second, doc_type in _DOMAIN_SIGNATURES:
        if top_domain == sig_top:
            if sig_second is None or sig_second == second_domain:
                return doc_type

    return "mixed"


def classify_path(path: Path, sample_bytes: int = 4096) -> str:
    """Classify a file on disk by path + content sample."""
    # Extension pre-check
    suffix = path.suffix.lower()
    if suffix == ".py":
        return "python"
    if suffix in (".tsm", ".metafoam"):
        return "tsm"

    try:
        raw = path.read_bytes()[:sample_bytes]
        text = raw.decode("utf-8", errors="replace")
    except (OSError, PermissionError):
        return "mixed"

    return classify(text, sample_bytes=sample_bytes)


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(
        description="Stage 0 document type classifier"
    )
    parser.add_argument("paths", nargs="+", type=Path,
                        help="files to classify")
    parser.add_argument("--sample", type=int, default=4096,
                        help="bytes to sample per file (default 4096)")
    args = parser.parse_args()

    for p in args.paths:
        doc_type = classify_path(p, sample_bytes=args.sample)
        domains  = DOMAIN_SET_FOR[doc_type]
        print(f"{doc_type:<14}  {p.name}")
        if "--verbose" in sys.argv:
            print(f"               domains: {domains}")


if __name__ == "__main__":
    main()
