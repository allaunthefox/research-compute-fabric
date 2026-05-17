#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
# PTOS: LAYER=STORE / DOMAIN=DATA / CONDITION=EXPERIMENTAL / STAGE=ACTIVE / SOURCE=CODE
"""
Large-File Ingestor — Chunked adapter for multi-GB research documents.
=======================================================================
**concept_anchor:** domain=substrate / concept=large_file_chunked_ingest / resolution=STABLE

PROBLEM
-------
ingest_archive.py reads only the first 8 KB of each file.  That is fine for
most research artifacts (specs, code, session JSON) but completely wrong for:

  - Exported AI conversation logs  (100 KB – 10 MB of markdown)
  - Connectome datasets            (CSV/JSON, hundreds of MB)
  - Literature harvests            (many MB of plain text)
  - Bulk export dumps              (multi-GB XML / JSON)

For these files the first 8 KB is boilerplate/scaffolding — the actual signal
is buried hundreds of kilobytes in.

APPROACH
--------
This adapter borrows the ISO prepass compression tech to solve the indexing
problem.  The key insight:

  iso_symbol_table.prepass(chunk) → (compressed_text, substitution_log)

  The substitution_log is a domain-tagged semantic fingerprint of the chunk.
  If the chunk contains "neuron", "synapse", "axon" we get iso_bio hits.
  If it contains "compression", "entropy", "codec" we get iso_unit/iso_abbrev
  hits.  The log tells us WHAT IS IN THE TEXT without us doing NLP.

  Aggregating substitution counts across all chunks gives us a document-level
  semantic profile even for files we cannot hold in RAM.

SAMPLING STRATEGY (for multi-GB files)
---------------------------------------
  full      : read every chunk (slow, accurate — use for files < ~100 MB)
  uniform   : evenly-spaced samples across the file (fast, approximate)
  head_tail : first N + last N chunks (catches headers and conclusions)

  Default: uniform with up to 256 sample windows of 64 KB each (~16 MB
  coverage regardless of file size).

SCAFFOLDING STRIPPER
--------------------
AI conversation exports (Qwen, Gemini, GPT, Claude) are dominated by
assistant-side metadata: "Thinking", "Search", "Web Fetch", line counts,
URLs.  These words poison the keyword extractor.  The stripper removes lines
matching known scaffolding patterns before the ISO prepass sees them.

  Recognises: Qwen, Gemini, ChatGPT, Claude Code conversation exports.

USAGE
-----
  # Ingest a single large file
  python3 5-Applications/scripts/ingest_large_file.py sessions/conversations_qwen.md

  # Ingest with full bundle attachment sweep (default)
  python3 5-Applications/scripts/ingest_large_file.py extraneous/media/ChatExport_2026-03-29/messages.html

  # Force re-index, show verbose per-chunk stats
  python3 5-Applications/scripts/ingest_large_file.py sessions/big_dump.md --force --verbose

  # Use full read for smaller files (no sampling)
  python3 5-Applications/scripts/ingest_large_file.py shared-data/data/connectome.csv --strategy full

  # Ingest a multi-GB file with custom chunk count
  python3 5-Applications/scripts/ingest_large_file.py shared-data/data/huge.json --max-chunks 512

  # Dry run — show what would be ingested without writing
  python3 5-Applications/scripts/ingest_large_file.py 6-Documentation/archive/giant.md --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


# ─── repo root ────────────────────────────────────────────────────────────────
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "scripts"))

try:
    from substrate_git_index import (
        DB_PATH, _open_db, _concept_vector_from_weights, _upsert_package, _PHI,
    )
except ImportError as e:
    print(f"[error] cannot import substrate_git_index: {e}", file=sys.stderr)
    sys.exit(1)

try:
    from ingest_attachments import collect_auto_attachments
except ImportError as e:
    print(f"[error] cannot import ingest_attachments: {e}", file=sys.stderr)
    sys.exit(1)

try:
    from ingest_text_hygiene import derive_safe_description
except ImportError as e:
    print(f"[error] cannot import ingest_text_hygiene: {e}", file=sys.stderr)
    sys.exit(1)

try:
    from iso_symbol_table import (
        prepass as iso_prepass,
        DOMAINS as ISO_DOMAINS,
        normalize_latex_math,
    )
    _ISO_AVAILABLE = True
except ImportError:
    _ISO_AVAILABLE = False
    def normalize_latex_math(text: str) -> str:
        return text

# ─── defaults ─────────────────────────────────────────────────────────────────

CHUNK_SIZE    = 65_536       # 64 KB per chunk
MAX_CHUNKS    = 256          # max sampled chunks (uniform strategy)
STRATEGY      = "uniform"    # full | uniform | head_tail
ATTACH_MODE   = "resonant"   # full | resonant | source-only

# ISO domains to run on each chunk — all standard ones
_ISO_DOMAINS_TO_USE = ["iso_geo", "iso_chem", "iso_bio", "iso_unit",
                       "iso_lang", "iso_abbrev", "iso_math"]

# ─── scaffolding strip patterns ───────────────────────────────────────────────
# Lines matching any of these are noise from AI conversation exports.
# Applied BEFORE the ISO prepass and keyword extractor.

_SCAFFOLD_LINE_PATTERNS: list[re.Pattern] = [p for p in (re.compile(x) for x in [
    r"^Thinking$",
    r"^Search$",
    r"^Web Fetch$",
    r"^Read$",
    r"^Write$",
    r"^Edit$",
    r"^Bash$",
    r"^ListFiles[:\s]",
    r"^Glob[:\s]",
    r"^OUT$",
    r"^\(Searching the web",
    r"^Fetching content from https?://",
    r"^Error during fetch",
    r"^\d+ lines of output$",
    r"^Interrupted$",
    r"^▼ Show more$",
    r"^▲ Collapse$",
    r"^⎿",
    r"^\[connect\]",
    r"^\[ingest\]",
    r"^Co-Authored-By:",
    # Claude Code tool call scaffolding
    r"^<tool_use>",
    r"^</tool_use>",
    r"^<tool_result>",
    r"^</tool_result>",
    # Qwen-specific
    r"^\*\*Approach\*\*:",
    r"^User has provided the following answers",
    # Generic "N lines of output" variants
    r"^\d+ lines? of output",
])]


def _strip_scaffolding(text: str) -> str:
    """Remove AI conversation export boilerplate, line by line."""
    clean: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not any(p.match(stripped) for p in _SCAFFOLD_LINE_PATTERNS):
            clean.append(line)
    return "\n".join(clean)


# ─── extended cluster vocabulary ─────────────────────────────────────────────
# 14-axis vocabulary matching substrate_git_index / ingest_archive.
# Extended here with neuro/connectome and large-file-relevant terms.

_CLUSTER_KEYWORDS: dict[int, set[str]] = {
    0:  {"substrate", "foam", "voxel", "node", "fabric", "manifold", "register",
         "soliton", "tsm", "metafoam", "capsule"},
    1:  {"compress", "compression", "codec", "encode", "decode", "entropy",
         "huffman", "soliton", "symbol", "iso", "lut", "lookup", "prepass",
         "dictionary", "alphabet", "phoneme", "substitution", "bandwidth"},
    2:  {"graph", "dag", "node", "edge", "tree", "merkle", "hash", "pointer",
         "traversal", "topology", "manifold", "fractal", "connectome",
         "synapse", "axon", "dendrite", "circuit"},
    3:  {"hardware", "risc", "fpga", "hdl", "asic", "pcb", "circuit", "chip",
         "kda", "rad", "trace", "silicon", "lithography", "nanowire"},
    4:  {"time", "planck", "clock", "tick", "timing", "synchron", "latency",
         "quantum", "temporal", "duration", "schedule", "spike", "latency",
         "interspike", "interval", "phase"},
    5:  {"crypto", "hash", "sha256", "merkle", "zk", "stark", "proof",
         "signature", "seal", "attest", "verify", "provenance"},
    6:  {"database", "sql", "sqlite", "index", "query", "schema", "table",
         "row", "column", "fts", "search", "source", "git"},
    7:  {"semantic", "language", "concept", "meaning", "vector", "embed",
         "nlp", "token", "word", "text", "notation", "symbol", "translate",
         "analog", "idea", "weight", "research", "coding", "decode",
         "encode", "representation", "population", "hypervector",
         "patamathematics", "pataphysics", "patamathematical"},
    8:  {"physics", "entropy", "energy", "wave", "frequency", "field",
         "quantum", "particle", "force", "mass", "density", "pressure",
         "temperature", "superconductor", "photon", "electron", "orbital",
         # neuro/biology extended
         "neuron", "neural", "synaptic", "cortex", "hippocampus", "thalamus",
         "neuroscience", "electrophysiology", "potential", "firing",
         "receptor", "protein", "molecular", "genome", "chromosome",
         "membrane", "voltage", "depolarize", "channel",
         "geometry", "topology", "polytope", "torsion", "mobius", "equation",
         "proof", "theorem", "invariant", "patamathematics"},
    9:  {"security", "attack", "exploit", "vuln", "threat", "encrypt",
         "defense", "audit", "taint", "isolat", "sandbox", "secret"},
    10: {"os", "kernel", "process", "memory", "virtual", "vm", "hypervisor",
         "syscall", "opcode", "instruction", "runtime", "executor"},
    11: {"research", "discover", "hypothes", "theory", "experiment", "paper",
         "result", "finding", "analysis", "study", "novel", "specul",
         # neuro research terms
         "vertebrate", "mammal", "primate", "mouse", "human", "species",
         "connectome", "atlas", "resolution", "scan", "imaging", "mri",
         "electrode", "recording", "calcium", "optogenetics", "behavior",
         "locomotion", "spatial", "navigation", "place", "grid"},
    12: {"omnitoken", "token", "bridge", "surface", "bus", "ipc", "transport",
         "protocol", "route", "mesh", "omni"},
    13: {"identity", "sovereign", "manifest", "provenance", "attestation",
         "ownership", "claim", "ptos", "tag", "classify"},
}

_ALL_CLUSTER_WORDS: dict[str, int] = {
    word: axis
    for axis, words in _CLUSTER_KEYWORDS.items()
    for word in words
}

_STOP = frozenset({
    "the", "and", "for", "that", "this", "with", "from", "are", "was",
    "were", "have", "been", "will", "would", "could", "should", "which",
    "their", "there", "these", "those", "what", "when", "where", "how",
    "all", "any", "can", "not", "but", "also", "more", "some", "into",
    "they", "has", "its", "than", "each", "only", "about", "such",
})


# ─── ISO domain → concept axis mapping ───────────────────────────────────────
# When the ISO prepass fires on a domain, boost these axes.

_ISO_DOMAIN_AXIS: dict[str, list[int]] = {
    "iso_chem":   [8],          # chemistry → physics/entropy
    "iso_bio":    [8, 11],      # biology → physics + research
    "iso_unit":   [8, 4],       # SI units → physics + time
    "iso_math":   [8, 7],       # math → physics + semantic
    "iso_lang":   [7],          # language codes → semantic
    "iso_geo":    [13],         # geography → identity/sovereign
    "iso_abbrev": [7, 11],      # abbreviations → semantic + research
    "iso_music":  [7],          # music → semantic
    "iso_qchem":  [8],          # quantum chem → physics
}


# ─── chunk reader with sampling ───────────────────────────────────────────────

def _chunk_offsets(
    file_size: int,
    chunk_size: int,
    max_chunks: int,
    strategy: str,
) -> list[int]:
    """Return list of byte offsets to read chunks from."""
    total_chunks = math.ceil(file_size / chunk_size)

    if strategy == "full" or total_chunks <= max_chunks:
        return list(range(0, file_size, chunk_size))

    if strategy == "head_tail":
        half = max_chunks // 2
        head = [i * chunk_size for i in range(half)]
        tail_start = max(half, total_chunks - half)
        tail = [i * chunk_size for i in range(tail_start, total_chunks)]
        return sorted(set(head + tail))

    # uniform (default)
    step = max(1, total_chunks // max_chunks)
    return [i * chunk_size for i in range(0, total_chunks, step)][:max_chunks]


def _read_chunk(path: Path, offset: int, chunk_size: int) -> str:
    """Read one chunk from offset, decode leniently."""
    try:
        with open(path, "rb") as f:
            f.seek(offset)
            raw = f.read(chunk_size)
        return raw.decode("utf-8", errors="replace")
    except Exception:
        return ""


# ─── keyword extractor ────────────────────────────────────────────────────────

def _extract_keywords(text: str) -> dict[str, float]:
    """TF-IDF-like scorer identical to ingest_archive, with extended vocab."""
    tokens = re.findall(r"\b[a-zA-Z][a-zA-Z_]{3,}\b", text.lower())
    counts = Counter(t for t in tokens if t not in _STOP)
    if not counts:
        return {}

    max_c = counts.most_common(1)[0][1]
    weights: dict[str, float] = {}
    for word, count in counts.most_common(50):
        boost = 2.0 if word in _ALL_CLUSTER_WORDS else 1.0
        score = min(1.0, (count / max_c) * boost * 0.85)
        if score >= 0.08:
            weights[word] = round(score, 3)
    return weights


# ─── main processor ───────────────────────────────────────────────────────────

def process_file(
    path: Path,
    chunk_size: int = CHUNK_SIZE,
    max_chunks: int = MAX_CHUNKS,
    strategy: str = STRATEGY,
    strip_scaffolding: bool = True,
    verbose: bool = False,
) -> dict:
    """Read a large file in chunks, return merged concept profile.

    Returns dict with keys:
      idea_weights   : merged keyword → score
      iso_hit_counts : iso_domain → total substitution count
      concept_vector : list[float] (14 axes)
      foam_score     : float
      description    : str (first meaningful line found)
      file_size      : int
      chunks_read    : int
      chunks_total   : int
    """
    file_size = path.stat().st_size
    offsets = _chunk_offsets(file_size, chunk_size, max_chunks, strategy)
    total_chunks = math.ceil(file_size / chunk_size)

    # Accumulators
    merged_counts: Counter = Counter()
    iso_hit_counts: Counter = Counter()
    description_probe: list[str] = []
    chunks_read = 0

    for i, offset in enumerate(offsets):
        raw_chunk = _read_chunk(path, offset, chunk_size)
        if not raw_chunk.strip():
            continue

        probe_budget = 65536 if path.suffix.lower() == ".json" else 16384
        if sum(len(part) for part in description_probe) < probe_budget:
            description_probe.append(raw_chunk[:probe_budget])

        chunk = _strip_scaffolding(raw_chunk) if strip_scaffolding else raw_chunk
        analysis_chunk = normalize_latex_math(chunk)

        # ISO prepass — substitution log is the semantic fingerprint
        if _ISO_AVAILABLE:
            try:
                compressed, sub_log = iso_prepass(analysis_chunk, domains=_ISO_DOMAINS_TO_USE)
                for domain, hits in sub_log.items():
                    iso_hit_counts[domain] += len(hits)
                # Run keyword extraction on COMPRESSED text (lower entropy = cleaner signal)
                kw = _extract_keywords(compressed)
            except Exception:
                kw = _extract_keywords(analysis_chunk)
        else:
            kw = _extract_keywords(analysis_chunk)

        for word, score in kw.items():
            # Weighted merge: later chunks don't overwrite earlier signal
            merged_counts[word] += score

        chunks_read += 1
        if verbose:
            iso_note = ""
            if _ISO_AVAILABLE:
                top = sorted(iso_hit_counts.items(), key=lambda x: -x[1])[:3]
                iso_note = f"  iso={dict(top)}"
            print(f"  chunk {i+1}/{len(offsets)} offset={offset//1024}KB"
                  f"  kw={len(kw)}{iso_note}")

    description = derive_safe_description(path, "\n".join(description_probe), max_len=200)

    # Normalise merged keyword scores to [0, 1]
    if merged_counts:
        max_score = max(merged_counts.values())
        idea_weights = {
            w: round(min(1.0, s / max_score), 3)
            for w, s in merged_counts.most_common(40)
            if s / max_score >= 0.08
        }
    else:
        idea_weights = {}

    # Boost idea_weights using ISO domain hit counts
    # Each ISO hit translates to a synthetic keyword signal on the relevant axes
    for domain, count in iso_hit_counts.items():
        if count == 0:
            continue
        norm_count = min(1.0, count / 500.0)  # saturate at 500 hits
        axes = _ISO_DOMAIN_AXIS.get(domain, [])
        # Inject synthetic signal words for dominant ISO domains
        _ISO_DOMAIN_SIGNAL_WORDS = {
            "iso_bio":    "biology",
            "iso_chem":   "chemistry",
            "iso_unit":   "physics",
            "iso_math":   "mathematics",
            "iso_lang":   "language",
            "iso_geo":    "geography",
            "iso_abbrev": "abbreviation",
            "iso_music":  "music",
            "iso_qchem":  "quantum",
        }
        signal_word = _ISO_DOMAIN_SIGNAL_WORDS.get(domain)
        if signal_word and norm_count >= 0.05:
            # Only add if it doesn't already outrank this
            existing = idea_weights.get(signal_word, 0.0)
            idea_weights[signal_word] = max(existing, round(norm_count * 0.9, 3))

    concept_vec = _concept_vector_from_weights(idea_weights)
    foam_score = round(
        sum(idea_weights.values()) / max(len(idea_weights), 1) * _PHI, 4
    )

    return {
        "idea_weights":   idea_weights,
        "iso_hit_counts": dict(iso_hit_counts),
        "concept_vector": concept_vec,
        "foam_score":     foam_score,
        "description":    description,
        "file_size":      file_size,
        "chunks_read":    chunks_read,
        "chunks_total":   total_chunks,
    }


# ─── domain detector ──────────────────────────────────────────────────────────

def _detect_domain(path: Path, iso_hits: dict[str, int], idea_weights: dict[str, float]) -> str:
    """Infer concept_anchor domain from ISO hit profile and path."""
    path_str = str(path).lower()

    # Path-based overrides
    if any(k in path_str for k in ("connectome", "neuro", "synapse", "brain", "cortex")):
        return "neuroscience"
    if any(k in path_str for k in ("hutter", "compress", "codec", "iso", "lut")):
        return "compression"
    if any(k in path_str for k in ("tsm", "soliton", "metafoam", "substrate")):
        return "substrate"
    if any(k in path_str for k in ("govern", "legal", "patent", "ethic")):
        return "governance"
    if any(k in path_str for k in ("kda", "hardware", "pcb", "hdl")):
        return "hardware"

    # ISO hit profile: dominant domain wins
    if iso_hits:
        top_iso = max(iso_hits, key=lambda k: iso_hits[k])
        iso_to_domain = {
            "iso_bio":    "neuroscience",
            "iso_chem":   "chemistry",
            "iso_unit":   "physics",
            "iso_math":   "mathematics",
            "iso_lang":   "linguistics",
            "iso_geo":    "geography",
        }
        if iso_to_domain.get(top_iso):
            return iso_to_domain[top_iso]

    # Keyword profile fallback
    top_words = set(list(idea_weights.keys())[:10])
    if top_words & {"neuron", "synapse", "cortex", "connectome", "neural", "spike"}:
        return "neuroscience"
    if top_words & {"compress", "entropy", "codec", "symbol", "iso"}:
        return "compression"
    if top_words & {
        "geometry", "topology", "polytope", "torsion", "mobius",
        "equation", "proof", "theorem", "invariant", "patamathematics",
        "pataphysics",
    }:
        return "mathematics"

    return "research"


def _ptos_domain_for_large_file(path: Path, concept_domain: str) -> str:
    """Map a concept-domain inference onto the PTOS operational domain axis."""
    path_str = str(path).lower()
    if any(k in path_str for k in ("validation", "verification", "test", "tests", "benchmark", "rigor")):
        return "TEST"
    mapping = {
        "compression": "COMPUTE",
        "substrate": "COMPUTE",
        "mathematics": "COMPUTE",
        "computation": "COMPUTE",
        "governance": "RULE",
        "containment": "RULE",
        "cryptography": "RULE",
        "hardware": "MATERIAL",
        "physics": "MATERIAL",
        "chemistry": "MATERIAL",
        "biology": "MATERIAL",
        "linguistics": "COMMS",
        "neuroscience": "DATA",
        "geography": "DATA",
        "research": "DATA",
    }
    return mapping.get(concept_domain, "DATA")


# ─── pkg name ─────────────────────────────────────────────────────────────────

def _pkg_name(path: Path) -> str:
    """Derive stable pkg identifier. Same rules as ingest_archive."""
    try:
        rel = path.relative_to(REPO)
        parts = [p.lower()[:8] for p in rel.parts[:-1]
                 if p.lower() not in ("archive", "sort this", "category",
                                      "research documents")]
        stem = re.sub(r"[^a-z0-9]+", "_", path.stem.lower())[:40]
        prefix = "-".join(p for p in parts if p)[:20]
        tag = f"arc-{prefix}-{stem}" if prefix else f"arc-{stem}"
    except ValueError:
        # Path outside repo — use filename only
        stem = re.sub(r"[^a-z0-9]+", "_", path.stem.lower())[:40]
        tag = f"arc-ext-{stem}"
    return tag[:80]


# ─── ingest ───────────────────────────────────────────────────────────────────

def ingest(
    path: Path,
    pkg_override: str | None = None,
    chunk_size: int = CHUNK_SIZE,
    max_chunks: int = MAX_CHUNKS,
    strategy: str = STRATEGY,
    attach_mode: str = ATTACH_MODE,
    strip_scaffolding: bool = True,
    force: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> str:
    """Ingest a large file into the substrate index. Returns status string."""
    if not path.exists():
        print(f"[error] file not found: {path}", file=sys.stderr)
        return "error"

    pkg = pkg_override or _pkg_name(path)
    version = "1.0.0"

    conn = _open_db()

    if not force and not dry_run:
        row = conn.execute(
            "SELECT pkg FROM packages WHERE pkg=? AND version=?", (pkg, version)
        ).fetchone()
        if row:
            print(f"[skip] {pkg} already indexed (use --force to re-index)")
            return "exists"

    print(f"[large-file] {path.name}  ({path.stat().st_size // 1024} KB)")
    print(f"             strategy={strategy}  max_chunks={max_chunks}"
          f"  chunk={chunk_size // 1024}KB  strip_scaffolding={strip_scaffolding}"
          f"  attachments={attach_mode}")

    profile = process_file(
        path,
        chunk_size=chunk_size,
        max_chunks=max_chunks,
        strategy=strategy,
        strip_scaffolding=strip_scaffolding,
        verbose=verbose,
    )

    idea_weights = profile["idea_weights"]
    iso_hits     = profile["iso_hit_counts"]
    concept_vec  = profile["concept_vector"]
    foam_score   = profile["foam_score"]
    description  = profile["description"]

    domain = _detect_domain(path, iso_hits, idea_weights)
    ptos_domain = _ptos_domain_for_large_file(path, domain)
    stem   = re.sub(r"[^a-z0-9]+", "_", path.stem.lower())[:60]
    concept_anchor = {
        "domain":     domain,
        "concept":    stem,
        "resolution": "FORMING",
    }

    axes_lit = sum(1 for x in concept_vec if x > 0.01)
    print(f"             pkg={pkg}")
    print(f"             domain={domain}  axes={axes_lit}/14  foam={foam_score}")
    print(f"             chunks={profile['chunks_read']}/{profile['chunks_total']}"
          f"  iso_hits={sum(iso_hits.values())}  keywords={len(idea_weights)}")
    if iso_hits:
        top_iso = sorted(iso_hits.items(), key=lambda x: -x[1])[:4]
        print(f"             top_iso={dict(top_iso)}")

    # Use resonant mode if requested, passing top keywords for search-driven discovery
    kw_list = list(idea_weights.keys())[:5] if idea_weights else None
    attached_files, attachment_meta = collect_auto_attachments(
        path, repo=REPO, mode=attach_mode, keywords=kw_list
    )
    print(f"             attachments={attachment_meta['attachment_count']}"
          f"  policies={','.join(attachment_meta['attachment_policies'])}")

    if dry_run:
        print(f"  [dry-run] would write {pkg}")
        return "dry"

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    tags    = [domain, "large-file", path.suffix.lstrip(".")]

    _upsert_package(conn, {
        "pkg": pkg,
        "version": version,
        "layer": "RULE",
        "domain": ptos_domain,
        "condition": "EXPERIMENTAL",
        "stage": "ACTIVE",
        "source": "NOTE",
        "description": description[:500] if description else f"Large file: {path.name}",
        "tags": json.dumps(tags),
        "files": json.dumps(attached_files),
        "sealed_utc": now_utc,
        "foam_score": foam_score,
        "concept_vector": json.dumps(concept_vec),
        "concept_anchor": json.dumps(concept_anchor),
        "idea_weights": json.dumps(idea_weights),
        "module": "LARGE_FILE_INGEST",
        "archetype": "CHUNKED_ISO_PREPASS",
        "analog_map": json.dumps({}),
        "attachment_meta": json.dumps(attachment_meta),
        "ingest_profile": json.dumps({
            "file_size_kb": path.stat().st_size // 1024,
            "chunks_read": profile["chunks_read"],
            "chunks_total": profile["chunks_total"],
            "iso_hit_counts": iso_hits,
            "strategy": strategy,
        }),
        "extension_points": json.dumps([]),
        "tier": "RESEARCH",
        "visibility": "PRIVATE",
        "model_status": "REFERENCE_ONLY",
        "taint_status": "CLEAN",
        "session_id": attached_files[0],
        "indexed_utc": now_utc,
    })
    conn.commit()
    print(f"  [ok] indexed {pkg}")
    return "indexed"


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Ingest a large file into the substrate index using ISO prepass chunking."
    )
    ap.add_argument("file", help="Path to the file to ingest")
    ap.add_argument("--pkg",          help="Override generated pkg name")
    ap.add_argument("--chunk-size",   type=int, default=CHUNK_SIZE,
                    help=f"Bytes per chunk (default {CHUNK_SIZE})")
    ap.add_argument("--max-chunks",   type=int, default=MAX_CHUNKS,
                    help=f"Max sample windows (default {MAX_CHUNKS})")
    ap.add_argument("--strategy",     choices=["full", "uniform", "head_tail"],
                    default=STRATEGY,
                    help=f"Sampling strategy (default {STRATEGY})")
    ap.add_argument("--attachments", choices=["full", "resonant", "source-only"],
                    default=ATTACH_MODE,
                    help=f"Attachment collection mode (default {ATTACH_MODE})")
    ap.add_argument("--no-strip",     action="store_true",
                    help="Disable AI conversation scaffolding stripper")
    ap.add_argument("--force",        action="store_true",
                    help="Re-index if already exists")
    ap.add_argument("--dry-run",      action="store_true",
                    help="Show what would be indexed without writing")
    ap.add_argument("--verbose",      action="store_true",
                    help="Print per-chunk stats")
    args = ap.parse_args()

    path = Path(args.file).expanduser().resolve()
    ingest(
        path,
        pkg_override=args.pkg,
        chunk_size=args.chunk_size,
        max_chunks=args.max_chunks,
        strategy=args.strategy,
        attach_mode=args.attachments,
        strip_scaffolding=not args.no_strip,
        force=args.force,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
