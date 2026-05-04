#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
# PTOS: LAYER=CORE / DOMAIN=COMPUTE / CONDITION=EXPERIMENTAL / STAGE=ACTIVE / SOURCE=CODE
"""
Schema Encoder — Structural Pass 1.8 (Single-Pass Unified Matcher)
==================================================================

Replaces structural patterns with compact tokens in a single, coordinate-stable
pass. Supports Half-Möbius closures (Inverse Sisyphus) and other structural schemas.
"""

from __future__ import annotations

import os
import sys
import re
import json
from pathlib import Path
from dataclasses import dataclass
from typing import NamedTuple, List, Tuple, Optional

REPO_ROOT = Path(os.getenv("RESEARCH_STACK_ROOT") or Path(__file__).resolve().parents[1])
TOOLS_DIR = REPO_ROOT / "tools"

# Add local tools directory to path
sys.path.insert(0, str(TOOLS_DIR))
try:
    from topological_encoder import TopologicalEncoder, detect_seismic_shell, SisyphusInverseError
except ImportError:
    # Retry with an explicit repo-root-based tools path for remote environments.
    sys.path.insert(0, str(TOOLS_DIR.resolve()))
    from topological_encoder import TopologicalEncoder, detect_seismic_shell, SisyphusInverseError


# ─── schema tokens (compact placeholders) ─────────────────────────────────────

_TOK_PTOS_HEADER     = "§H"
_TOK_CONCEPT_ANCHOR  = "§CA"
_TOK_SESSION_ENV     = "§SE"
_TOK_IDEA_WEIGHT     = "§IW"
_TOK_TOPOLOGICAL     = "§TM"


# ─── data types ───────────────────────────────────────────────────────────────

class SchemaMatch(NamedTuple):
    """Record of one structural substitution."""
    token:    str    # compact placeholder inserted into text
    original: str    # full original text that was replaced
    position: int    # character position in ORIGINAL text


# ─── pattern definitions ──────────────────────────────────────────────────────

# PTOS header: entire comment line with variable LAYER/DOMAIN/CONDITION/STAGE/SOURCE
_RE_PTOS_HEADER = re.compile(
    r"#\s*PTOS:\s*LAYER=(?P<layer>\w+)\s*/\s*DOMAIN=(?P<domain>\w+)\s*"
    r"/\s*CONDITION=(?P<condition>\w+)\s*/\s*STAGE=(?P<stage>\w+)\s*"
    r"/\s*SOURCE=(?P<source>\w+)"
)

# concept_anchor block in docstrings (inline format)
_RE_CONCEPT_ANCHOR = re.compile(
    r"\*\*concept_anchor:\*\*\s*domain=(?P<domain>\S+)\s*/\s*"
    r"concept=(?P<concept>\S+)\s*/\s*"
    r"resolution=(?P<resolution>\w+)"
    r"(?:\s*/\s*story=(?P<story>\w+))?"
)

# Session JSON envelope keys (first few keys of a session file)
_RE_SESSION_ENV = re.compile(
    r'"session_id"\s*:\s*"(?P<sid>[^"]+)"\s*,\s*\n\s*'
    r'"pkg"\s*:\s*"(?P<pkg>[^"]+)"\s*,\s*\n\s*'
    r'"version"\s*:\s*"(?P<ver>[^"]+)"\s*,\s*\n\s*'
    r'"module"\s*:\s*"(?P<module>[^"]+)"'
)

# idea_weights key-value pair (JSON string → float)
_RE_IDEA_WEIGHT = re.compile(
    r'"(?P<key>[^"]{8,120})"\s*:\s*(?P<weight>0\.\d+)'
)

# SEISMIC Signal Manifold (loose format)
_RE_SIGNAL_MANIFOLD = re.compile(
    r'\{[^{}]*?"phi_corr"\s*:\s*(?P<phi>0\.\d+).*?"torsion_gradient"\s*:\s*\[(?P<tau>[^\]]+)\].*?\}',
    re.DOTALL
)


# ─── Matching Logic ─────────────────────────────────────────────────────────

def find_all_matches(text: str) -> List[Tuple[int, int, str, str, int]]:
    """
    Find all structural matches in the original text.
    Returns list of (start, end, token, original, priority).
    """
    matches = []
    topo_encoder = TopologicalEncoder()

    # Priority 0: Topological Closures (Highest)
    for m in _RE_SIGNAL_MANIFOLD.finditer(text):
        try:
            raw = m.group(0)
            manifold_data = json.loads(raw)
            shell = topo_encoder.process_manifold(manifold_data)
            if shell:
                token = f"{_TOK_TOPOLOGICAL}:{shell.sha256[:16]}"
                matches.append((m.start(), m.end(), token, raw, 0))
            elif detect_seismic_shell(manifold_data.get("phi_corr", 0.0)):
                # HEATSINK_HALT: SEISMIC signal failed to close.
                sys.stderr.write(f"[!] Sisyphus Inverse Failure: Annnihilated Vortex at pos {m.start()}\n")
                # We tag it for stats by adding a non-substituting match type if we wanted, 
                # but for now we just log it.
        except Exception as e:
            sys.stderr.write(f"[-] Topological Parse Error: {e}\n")

    # Priority 1: Headers
    for m in _RE_PTOS_HEADER.finditer(text):
        matches.append((m.start(), m.end(), _TOK_PTOS_HEADER, m.group(0), 1))

    # Priority 2: Concept Anchors
    for m in _RE_CONCEPT_ANCHOR.finditer(text):
        matches.append((m.start(), m.end(), _TOK_CONCEPT_ANCHOR, m.group(0), 2))

    # Priority 3: Session Envelopes
    for m in _RE_SESSION_ENV.finditer(text):
        matches.append((m.start(), m.end(), _TOK_SESSION_ENV, m.group(0), 3))

    # Priority 4: Idea Weights
    for m in _RE_IDEA_WEIGHT.finditer(text):
        matches.append((m.start(), m.end(), _TOK_IDEA_WEIGHT, m.group(0), 4))

    return matches


def filter_conflicts(matches: List[Tuple[int, int, str, str, int]]) -> List[SchemaMatch]:
    """Resolve overlapping matches based on priority and length."""
    if not matches: return []

    # Sort primarily by start index, secondarily by priority (lower number = higher priority)
    matches.sort(key=lambda x: (x[0], x[4]))

    final_matches: List[SchemaMatch] = []
    last_end = -1

    for start, end, token, original, priority in matches:
        if start >= last_end:
            # No overlap, or starting after last match
            final_matches.append(SchemaMatch(token, original, start))
            last_end = end
        else:
            # Conflict detected. Since we sorted by priority, the earlier one in the list wins.
            # (Matches at same start index: highest priority wins).
            pass

    return final_matches


# ─── encoder ──────────────────────────────────────────────────────────────────

def encode(text: str) -> Tuple[str, List[SchemaMatch]]:
    """
    Unified Single-Pass Encoder.
    Identifies all structural clusters in the original text and performs
    coordinate-stable substitution.
    """
    all_raw = find_all_matches(text)
    filtered = filter_conflicts(all_raw)
    
    # Process from Right-to-Left to avoid shifting pending match positions
    # while building the encoded string.
    # Actually, it's easier to build a new string from left to right:
    filtered.sort(key=lambda x: x.position)
    
    result_parts = []
    last_idx = 0
    for match in filtered:
        # Append literal text before the match
        result_parts.append(text[last_idx:match.position])
        # Append the token
        result_parts.append(match.token)
        # Advance cursor past the original text
        last_idx = match.position + len(match.original)
    
    # Append remaining literal text
    result_parts.append(text[last_idx:])
    
    return "".join(result_parts), filtered


def decode(encoded: str, matches: List[SchemaMatch]) -> str:
    """Restore original text from encoded form + match list."""
    # Build from tokens and original strings
    # Positions are absolute in the original text, so we rebuild it exactly.
    matches.sort(key=lambda x: x.position)
    
    result = encoded
    # We must replace from right-to-left because replacing changes indices in 'encoded'
    # BUT, the 'position' in 'matches' is relative to the ORIGINAL text.
    # The decoder needs to find where each token is in the ENCODED text.
    
    # Wait! If we store ORIGINAL positions, we should rebuild from scratch:
    text_parts = []
    curr_enc_idx = 0
    
    for match in matches:
        # Find token in encoded text
        # Since we processed matches in order, the next token must be at curr_enc_idx
        # But wait! Literal text between tokens is present.
        
        # Identify how much literal text preceded this match in the ORIGINAL
        # and how much was shifted in the ENCODED.
        pass

    # simpler way: use the same logic as before but be VERY careful with index math
    # the old decode worked because it went backwards:
    result = encoded
    
    # To decode, we need the positions in the ENCODED text.
    # Let's calculate them:
    enc_offset = 0
    match_list_with_enc_pos = []
    for m in matches:
        enc_pos = m.position - enc_offset
        match_list_with_enc_pos.append((enc_pos, m))
        enc_offset += len(m.original) - len(m.token)
        
    result = encoded
    for enc_pos, m in reversed(match_list_with_enc_pos):
        result = result[:enc_pos] + m.original + result[enc_pos + len(m.token):]
        
    return result


# ─── statistics ───────────────────────────────────────────────────────────────

@dataclass
class SchemaStats:
    """Byte savings summary for one encode pass."""
    ptos_headers:     int = 0
    concept_anchors:  int = 0
    session_envs:     int = 0
    idea_weights:     int = 0
    topological_kms:  int = 0
    annihilated_vortices: int = 0
    bytes_before:     int = 0
    bytes_after:      int = 0

    @property
    def total_matches(self) -> int:
        return (self.ptos_headers + self.concept_anchors
                + self.session_envs + self.idea_weights + self.topological_kms)

    @property
    def bytes_saved(self) -> int:
        return self.bytes_before - self.bytes_after

    @property
    def ratio(self) -> float:
        return self.bytes_after / max(self.bytes_before, 1)


def encode_with_stats(text: str) -> tuple[str, list[SchemaMatch], SchemaStats]:
    """encode() with per-schema byte savings breakdown."""
    encoded, matches = encode(text)
    stats = SchemaStats(
        bytes_before = len(text.encode()),
        bytes_after  = len(encoded.encode()),
    )
    for m in matches:
        if m.token == _TOK_PTOS_HEADER:
            stats.ptos_headers += 1
        elif m.token == _TOK_CONCEPT_ANCHOR:
            stats.concept_anchors += 1
        elif m.token == _TOK_SESSION_ENV:
            stats.session_envs += 1
        elif m.token == _TOK_IDEA_WEIGHT:
            stats.idea_weights += 1
        elif m.token.startswith(_TOK_TOPOLOGICAL):
            stats.topological_kms += 1
    
    # Second pass for stats-only analysis of failures
    for m in _RE_SIGNAL_MANIFOLD.finditer(text):
        try:
            phi = float(m.group("phi"))
            if 0.35 <= phi < 0.47: # SEISMIC
                raw = m.group(0)
                manifold_data = json.loads(raw)
                if not TopologicalEncoder().process_manifold(manifold_data):
                    stats.annihilated_vortices += 1
        except: pass

    return encoded, matches, stats


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(
        description="Schema encoder — structural Pass 1.8"
    )
    parser.add_argument("path", help="file to analyse")
    parser.add_argument("--decode", action="store_true",
                        help="verify round-trip losslessness")
    args = parser.parse_args()

    text = open(args.path, encoding="utf-8", errors="replace").read()
    encoded, matches, stats = encode_with_stats(text)

    print(f"Schema encoder: {args.path}")
    print(f"  Topological KMS: {stats.topological_kms}")
    print(f"  PTOS headers:    {stats.ptos_headers}")
    print(f"  concept_anchors: {stats.concept_anchors}")
    print(f"  session envs:    {stats.session_envs}")
    print(f"  idea_weights:    {stats.idea_weights}")
    print(f"  Annihilated Vortices: {stats.annihilated_vortices}")
    print(f"  bytes before:    {stats.bytes_before:,}")
    print(f"  bytes after:     {stats.bytes_after:,}")
    print(f"  bytes saved:     {stats.bytes_saved:,}  ({(1-stats.ratio)*100:.1f}%)")

    if args.decode:
        recovered = decode(encoded, matches)
        if recovered == text:
            print("  round-trip:      OK")
        else:
            print("  round-trip:      FAIL")
            # Find first difference
            for i, (a, b) in enumerate(zip(text, recovered)):
                if a != b:
                    print(f"  first diff at char {i}: {repr(text[i:i+40])}"
                          f" vs {repr(recovered[i:i+40])}")
                    break


if __name__ == "__main__":
    main()
