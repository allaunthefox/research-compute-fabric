# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================

from __future__ import annotations

# [WARDEN BOUNDARY ENFORCEMENT INJECTED]
import sys
import os
try:
    from io_harness_compat import spawn_isolated_process, fetch_network_resource
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from io_harness_compat import spawn_isolated_process, fetch_network_resource

#!/usr/bin/env python3
"""High-coverage literature harvesting pipeline with compact archival.

This script is a practical stand-in for "fetch everything": it queries multiple
open sources, deduplicates, ranks relevance, and writes an append-only
"DeepCompression" archive plus a nibble-style compact index.

Sources:
- Crossref
- OpenAlex
- arXiv

No third-party dependencies are required.
"""

import argparse
import csv
import hashlib
import json
import os
import re
import statistics
import time
from collections import Counter
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zlib
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Tuple

try:
    from scripts.logic_signal_substrate_translation import (
        assert_surface_write_safe,
        logic_signal_substrate_from_archive_domain,
        logic_signal_substrate_from_surface,
        surface_from_logic_signal_substrate,
    )
except ImportError:
    try:
        from logic_signal_substrate_translation import (
            assert_surface_write_safe,
            logic_signal_substrate_from_archive_domain,
            logic_signal_substrate_from_surface,
            surface_from_logic_signal_substrate,
        )
    except ImportError:
        # Module not available — substrate surface writes disabled.
        # find_low_coverage_sources and other pure functions remain usable.
        assert_surface_write_safe = lambda *a, **kw: None
        logic_signal_substrate_from_archive_domain = lambda *a, **kw: None
        logic_signal_substrate_from_surface = lambda *a, **kw: None
        surface_from_logic_signal_substrate = lambda *a, **kw: {}


USER_AGENT = "graph_os-literature-harvest/1.0 (+local-script)"
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OMNITOKEN_DIR = os.path.join(PROJECT_ROOT, "out", "omnitoken_bridge")
OMNITOKEN_SURFACE_PATH = os.path.join(OMNITOKEN_DIR, "egress_surface.json")


DEFAULT_QUERIES = [
    "human interaction safety ultra-fast computation",
    "real-time AI systems human factors safety",
    "algorithmic decision support cognitive overload",
    "human-in-the-loop control systems safety",
    "AI alignment human-computer interaction",
    "autonomy override governance AI systems",
    "model latency human trust calibration",
    "psychological effects of conversational AI",
    "adaptive systems intervention threshold",
    "safety-critical machine learning human oversight",
]


SAFETY_KEYWORDS = [
    "human",
    "interaction",
    "safety",
    "oversight",
    "alignment",
    "trust",
    "cognitive",
    "entrainment",
    "autonomy",
    "handover",
    "intervention",
    "governance",
    "risk",
    "control",
    "error",
    "failsafe",
    "fail-safe",
]


@dataclass
class Paper:
    source: str
    source_id: str
    title: str
    abstract: str
    authors: List[str]
    year: Optional[int]
    venue: str
    doi: str
    url: str
    query: str
    relevance_score: int = 0
    relevance_bucket_4bit: int = 0
    nibble_fingerprint_hex: str = ""


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def normalize_title(text: str) -> str:
    text = normalize_ws(text).lower()
    text = re.sub(r"[^a-z0-9 ]+", "", text)
    return text


def safe_int(x: object) -> Optional[int]:
    try:
        return int(x)
    except (TypeError, ValueError):
        return None


def fetch_json(url: str, timeout: float = 25.0, retries: int = 3) -> dict:
    last_exc: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8", errors="replace"))
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:  # pragma: no cover
            last_exc = exc
            if attempt < retries:
                time.sleep(1.2 * attempt)
    raise RuntimeError(f"Failed to fetch JSON from {url}: {last_exc}")


def fetch_text(url: str, timeout: float = 25.0, retries: int = 3) -> str:
    last_exc: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except (OSError, urllib.error.URLError) as exc:  # pragma: no cover
            last_exc = exc
            if attempt < retries:
                time.sleep(1.2 * attempt)
    raise RuntimeError(f"Failed to fetch text from {url}: {last_exc}")


def score_relevance(title: str, abstract: str) -> int:
    text = f"{title} {abstract}".lower()
    score = 0
    for kw in SAFETY_KEYWORDS:
        if kw in text:
            score += 1
    return score


def bucket_4bit(score: int, max_score: int = 16) -> int:
    score = max(0, score)
    if max_score <= 0:
        return 0
    b = round((min(score, max_score) / max_score) * 15)
    return int(max(0, min(15, b)))


def nibble_fingerprint(title: str, abstract: str) -> str:
    digest = hashlib.sha256((title + "\n" + abstract).encode("utf-8", errors="ignore")).hexdigest()
    # 16 nibbles = compact 64-bit-style fingerprint (hex chars are already nibbles)
    return digest[:16]


def dedupe_key(p: Paper) -> str:
    if p.doi:
        return f"doi:{p.doi.lower()}"
    return f"title:{normalize_title(p.title)}"


def from_crossref(query: str, rows: int) -> Iterable[Paper]:
    q = urllib.parse.quote(query)
    url = (
        "https://api.crossref.org/works"
        f"?query={q}&rows={rows}&select=DOI,title,author,container-title,URL,published-print,published-online,issued"
    )
    data = fetch_json(url)
    items = data.get("message", {}).get("items", [])
    for it in items:
        title = normalize_ws(" ".join(it.get("title", []) if isinstance(it.get("title", []), list) else [str(it.get("title", ""))]))
        venue = normalize_ws(" ".join(it.get("container-title", []) if isinstance(it.get("container-title", []), list) else [str(it.get("container-title", ""))]))
        doi = normalize_ws(it.get("DOI", ""))
        url_out = normalize_ws(it.get("URL", ""))

        authors = []
        for a in it.get("author", []) or []:
            given = normalize_ws(a.get("given", ""))
            family = normalize_ws(a.get("family", ""))
            full = normalize_ws(f"{given} {family}")
            if full:
                authors.append(full)

        year = None
        for fld in ("published-print", "published-online", "issued"):
            parts = (((it.get(fld) or {}).get("date-parts") or [[None]])[0] or [None])
            y = safe_int(parts[0])
            if y:
                year = y
                break

        if title:
            yield Paper(
                source="crossref",
                source_id=doi or url_out or hashlib.md5(title.encode()).hexdigest(),
                title=title,
                abstract="",
                authors=authors,
                year=year,
                venue=venue,
                doi=doi,
                url=url_out,
                query=query,
            )


def from_openalex(query: str, rows: int) -> Iterable[Paper]:
    q = urllib.parse.quote(query)
    url = f"https://api.openalex.org/works?search={q}&per-page={rows}"
    data = fetch_json(url)
    items = data.get("results", [])
    for it in items:
        title = normalize_ws(it.get("display_name", ""))
        abstract_idx = it.get("abstract_inverted_index") or {}
        if abstract_idx:
            max_pos = 0
            for positions in abstract_idx.values():
                for pos in positions:
                    if pos > max_pos:
                        max_pos = pos
            tokens = [""] * (max_pos + 1)
            for token, positions in abstract_idx.items():
                for pos in positions:
                    if 0 <= pos < len(tokens):
                        tokens[pos] = token
            abstract = normalize_ws(" ".join(tokens))
        else:
            abstract = ""

        venue = normalize_ws(((it.get("primary_location") or {}).get("source") or {}).get("display_name", ""))
        year = safe_int(it.get("publication_year"))
        doi = normalize_ws((it.get("doi") or "").replace("https://doi.org/", ""))
        url_out = normalize_ws(it.get("id", ""))
        authors = [
            normalize_ws(((a.get("author") or {}).get("display_name", "")))
            for a in (it.get("authorships") or [])
        ]
        authors = [a for a in authors if a]

        if title:
            yield Paper(
                source="openalex",
                source_id=url_out or doi or hashlib.md5(title.encode()).hexdigest(),
                title=title,
                abstract=abstract,
                authors=authors,
                year=year,
                venue=venue,
                doi=doi,
                url=url_out,
                query=query,
            )


def from_arxiv(query: str, rows: int) -> Iterable[Paper]:
    q = urllib.parse.quote(query)
    url = f"https://export.arxiv.org/api/query?search_query=all:{q}&start=0&max_results={rows}"
    xml_text = fetch_text(url)

    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }
    root = ET.fromstring(xml_text)
    for entry in root.findall("atom:entry", ns):
        title = normalize_ws((entry.findtext("atom:title", default="", namespaces=ns) or ""))
        abstract = normalize_ws((entry.findtext("atom:summary", default="", namespaces=ns) or ""))
        url_out = normalize_ws((entry.findtext("atom:id", default="", namespaces=ns) or ""))
        year = safe_int((entry.findtext("atom:published", default="", namespaces=ns) or "")[:4])
        authors = [
            normalize_ws((a.findtext("atom:name", default="", namespaces=ns) or ""))
            for a in entry.findall("atom:author", ns)
        ]
        authors = [a for a in authors if a]
        doi = ""
        for cat in entry.findall("arxiv:doi", ns):
            if cat is not None and (cat.text or "").strip():
                doi = normalize_ws(cat.text)
                break

        if title:
            yield Paper(
                source="arxiv",
                source_id=url_out or hashlib.md5(title.encode()).hexdigest(),
                title=title,
                abstract=abstract,
                authors=authors,
                year=year,
                venue="arXiv",
                doi=doi,
                url=url_out,
                query=query,
            )


def enrich_scores(papers: Iterable[Paper]) -> List[Paper]:
    out: List[Paper] = []
    for p in papers:
        p.relevance_score = score_relevance(p.title, p.abstract)
        p.relevance_bucket_4bit = bucket_4bit(p.relevance_score)
        p.nibble_fingerprint_hex = nibble_fingerprint(p.title, p.abstract)
        out.append(p)
    return out


def dedupe(papers: Iterable[Paper]) -> List[Paper]:
    best: Dict[str, Paper] = {}
    for p in papers:
        k = dedupe_key(p)
        old = best.get(k)
        if old is None or p.relevance_score > old.relevance_score:
            best[k] = p
    return list(best.values())


def find_low_coverage_sources(source_totals: Dict[str, int], min_total_per_source: int) -> Dict[str, int]:
    return {name: total for name, total in source_totals.items() if total < min_total_per_source}


def write_jsonl(path: str, papers: Iterable[Paper]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for p in papers:
            f.write(json.dumps(asdict(p), ensure_ascii=False) + "\n")


def write_csv(path: str, papers: Iterable[Paper]) -> None:
    rows = [asdict(p) for p in papers]
    if not rows:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def write_blackhole_vault(vault_dir: str, papers: List[Paper], run_id: str) -> str:
    return write_blackhole_vault_with_mode(
        vault_dir=vault_dir,
        papers=papers,
        run_id=run_id,
        archive_mode="legacy",
        benchmark_against_legacy=False,
    )


def canonical_archive_row(p: Paper) -> Dict[str, object]:
    """Return a stable, compact record used for partitioned archive encoding."""
    return {
        "k": dedupe_key(p),
        "b": int(p.relevance_bucket_4bit),
        "f": p.nibble_fingerprint_hex,
        "src": normalize_ws(p.source),
        "t": normalize_ws(p.title),
        "a": normalize_ws(p.abstract),
        "y": p.year if p.year is not None else 0,
        "v": normalize_ws(p.venue),
        "d": normalize_ws(p.doi),
        "u": normalize_ws(p.url),
        "q": normalize_ws(p.query),
        "s": int(p.relevance_score),
        "au": [normalize_ws(author) for author in (p.authors or [])],
    }


def build_legacy_payload_bytes(papers: List[Paper]) -> bytes:
    """Build legacy JSONL payload bytes for compression."""
    lines = [json.dumps(asdict(p), ensure_ascii=False) for p in papers]
    return ("\n".join(lines) + "\n").encode("utf-8")


def build_partitioned_payload_bytes(papers: List[Paper]) -> bytes:
    """Build a bucketed, field-partitioned payload that improves locality for zlib."""
    canonical_rows = [canonical_archive_row(p) for p in papers]
    canonical_rows.sort(key=lambda row: (int(row["b"]), str(row["f"]), str(row["k"])))

    buckets: Dict[int, List[Dict[str, object]]] = {}
    for row in canonical_rows:
        bucket = int(row["b"])
        buckets.setdefault(bucket, []).append(row)

    bucket_payloads: List[Dict[str, object]] = []
    for bucket in sorted(buckets.keys()):
        rows = buckets[bucket]
        bucket_payloads.append(
            {
                "bucket": bucket,
                "k": [row["k"] for row in rows],
                "f": [row["f"] for row in rows],
                "src": [row["src"] for row in rows],
                "t": [row["t"] for row in rows],
                "a": [row["a"] for row in rows],
                "y": [row["y"] for row in rows],
                "v": [row["v"] for row in rows],
                "d": [row["d"] for row in rows],
                "u": [row["u"] for row in rows],
                "q": [row["q"] for row in rows],
                "s": [row["s"] for row in rows],
                "au": [row["au"] for row in rows],
            }
        )

    payload = {
        "schema": "deepcompression/partitioned/v1",
        "paper_count": len(papers),
        "bucket_count": len(bucket_payloads),
        "buckets": bucket_payloads,
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def build_context_spray_payload_bytes(papers: List[Paper]) -> bytes:
    """Build context-sensitive payload with local context cells and per-cell delta emissions.

    Foam strategy:
    - Adaptive merge for tiny cells to avoid over-fragmented context groups
    - Deterministic rotation in each cell to alter adjacency and expose repeated patterns
    - Shared lexicon carry-over so repeated long strings are stored once
    """
    rows = [canonical_archive_row(p) for p in papers]
    rows.sort(
        key=lambda row: (
            str(row["q"]),
            str(row["src"]),
            int(row["b"]),
            str(row["v"]),
            int(row["y"]),
            str(row["f"]),
        )
    )

    base_cells: Dict[Tuple[str, str, int, str], List[Dict[str, object]]] = {}
    for row in rows:
        key = (
            str(row["q"]),
            str(row["src"]),
            int(row["b"]),
            str(row["v"]),
        )
        base_cells.setdefault(key, []).append(row)

    # Merge tiny cells into broader context bins to avoid sparse overhead.
    min_cell_size = 3
    cells: Dict[Tuple[str, str, int, str], List[Dict[str, object]]] = {}
    for key, cell_rows in base_cells.items():
        if len(cell_rows) >= min_cell_size:
            cells[key] = cell_rows
            continue

        query, _source, bucket, _venue = key
        merged_key = (query, "*", bucket, "*")
        cells.setdefault(merged_key, []).extend(cell_rows)

    lexicon: List[str] = []
    lexicon_index: Dict[str, int] = {}

    def lex(value: str) -> int:
        value = normalize_ws(value)
        existing = lexicon_index.get(value)
        if existing is not None:
            return existing
        idx = len(lexicon)
        lexicon.append(value)
        lexicon_index[value] = idx
        return idx

    def lex_authors(authors: List[object]) -> List[int]:
        return [lex(str(a)) for a in authors]

    emitted_cells: List[Dict[str, object]] = []

    def top_ngrams(texts: List[str], min_n: int = 2, max_n: int = 3, top_k: int = 16) -> List[str]:
        counts: Counter[str] = Counter()
        for text in texts:
            words = [w for w in re.split(r"\W+", normalize_ws(text).lower()) if len(w) >= 3]
            for n in range(min_n, max_n + 1):
                if len(words) < n:
                    continue
                for i in range(0, len(words) - n + 1):
                    phrase = " ".join(words[i : i + n])
                    if len(phrase) >= 8:
                        counts[phrase] += 1
        ranked = [phrase for phrase, c in counts.most_common(top_k * 3) if c >= 3]
        # Keep longest phrases first so replacement is stable and deterministic.
        ranked.sort(key=lambda x: (-len(x), x))
        return ranked[:top_k]

    def apply_ngrams(text: str, ngrams: List[str]) -> str:
        out = normalize_ws(text)
        if not out or not ngrams:
            return out
        lowered = out.lower()
        for i, phrase in enumerate(ngrams):
            marker = f"~g{i}~"
            # Case-insensitive, deterministic whole-phrase replacement.
            pattern = re.compile(re.escape(phrase), flags=re.IGNORECASE)
            lowered = pattern.sub(marker, lowered)
        return lowered
    for key in sorted(cells.keys()):
        query, source, bucket, venue = key
        cell_rows = cells[key]
        if not cell_rows:
            continue

        # Deterministic rotation for context-sensitive adjacency shifts.
        if len(cell_rows) > 1:
            seed = hashlib.sha256(f"{query}|{source}|{bucket}|{venue}".encode("utf-8")).hexdigest()
            offset = int(seed[:4], 16) % len(cell_rows)
            if offset:
                cell_rows = cell_rows[offset:] + cell_rows[:offset]

        cell_ngrams = top_ngrams(
            [str(r["t"]) for r in cell_rows] + [str(r["a"]) for r in cell_rows],
            min_n=2,
            max_n=3,
            top_k=16,
        )

        first = cell_rows[0]
        first_full = {
            "k": first["k"],
            "f": first["f"],
            "src": lex(str(first["src"])),
            "t": lex(apply_ngrams(str(first["t"]), cell_ngrams)),
            "a": lex(apply_ngrams(str(first["a"]), cell_ngrams)),
            "y": first["y"],
            "v": lex(str(first["v"])),
            "d": lex(str(first["d"])),
            "u": lex(str(first["u"])),
            "q": lex(str(first["q"])),
            "s": first["s"],
            "au": lex_authors(list(first["au"])),
        }

        deltas: List[Dict[str, object]] = []
        prev = first
        for row in cell_rows[1:]:
            delta: Dict[str, object] = {
                "k": row["k"],
                "f": row["f"],
                "s": row["s"],
            }
            for field in ("t", "a", "y", "d", "u", "au"):
                if row[field] != prev[field]:
                    if field == "au":
                        delta[field] = lex_authors(list(row[field]))
                    elif field in ("t", "a", "d", "u"):
                        if field in ("t", "a"):
                            delta[field] = lex(apply_ngrams(str(row[field]), cell_ngrams))
                        else:
                            delta[field] = lex(str(row[field]))
                    else:
                        delta[field] = row[field]
            deltas.append(delta)
            prev = row

        emitted_cells.append(
            {
                "ctx": {
                    "q": lex(query),
                    "src": lex(source),
                    "b": bucket,
                    "v": lex(venue),
                },
                "local_ngrams": cell_ngrams,
                "seed": first_full,
                "spray": deltas,
            }
        )

    payload = {
        "schema": "deepcompression/context-spray/v2",
        "paper_count": len(papers),
        "cell_count": len(emitted_cells),
        "lexicon": lexicon,
        "cells": emitted_cells,
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def build_hybrid_payload_bytes(papers: List[Paper]) -> bytes:
    """Build a hybrid payload:
    - high-entropy fields in partitioned blocks
    - low-entropy repeated fields in context-spray cells
    """
    rows = [canonical_archive_row(p) for p in papers]
    rows.sort(key=lambda row: (int(row["b"]), str(row["f"]), str(row["k"])))

    # High-entropy partition: titles/abstracts/urls/dois/authors tend to vary heavily.
    high_partition_buckets: Dict[int, List[Dict[str, object]]] = {}
    for row in rows:
        bucket = int(row["b"])
        high_partition_buckets.setdefault(bucket, []).append(
            {
                "k": row["k"],
                "f": row["f"],
                "t": row["t"],
                "a": row["a"],
                "d": row["d"],
                "u": row["u"],
                "au": row["au"],
            }
        )

    high_blocks: List[Dict[str, object]] = []
    for bucket in sorted(high_partition_buckets.keys()):
        block_rows = high_partition_buckets[bucket]
        high_blocks.append(
            {
                "bucket": bucket,
                "k": [r["k"] for r in block_rows],
                "f": [r["f"] for r in block_rows],
                "t": [r["t"] for r in block_rows],
                "a": [r["a"] for r in block_rows],
                "d": [r["d"] for r in block_rows],
                "u": [r["u"] for r in block_rows],
                "au": [r["au"] for r in block_rows],
            }
        )

    # Low-entropy context spray: source/query/venue/year/score are more repeatable.
    low_rows = [
        {
            "k": row["k"],
            "f": row["f"],
            "src": row["src"],
            "q": row["q"],
            "v": row["v"],
            "b": row["b"],
            "y": row["y"],
            "s": row["s"],
        }
        for row in rows
    ]

    low_rows.sort(key=lambda row: (str(row["q"]), str(row["src"]), int(row["b"]), str(row["v"]), int(row["y"]), str(row["f"])))
    low_cells: Dict[Tuple[str, str, int, str], List[Dict[str, object]]] = {}
    for row in low_rows:
        key = (str(row["q"]), str(row["src"]), int(row["b"]), str(row["v"]))
        low_cells.setdefault(key, []).append(row)

    low_emitted: List[Dict[str, object]] = []
    for key in sorted(low_cells.keys()):
        query, source, bucket, venue = key
        cell_rows = low_cells[key]
        first = cell_rows[0]
        deltas: List[Dict[str, object]] = []
        prev = first
        for row in cell_rows[1:]:
            delta: Dict[str, object] = {"k": row["k"], "f": row["f"]}
            for field in ("y", "s"):
                if row[field] != prev[field]:
                    delta[field] = row[field]
            deltas.append(delta)
            prev = row

        low_emitted.append(
            {
                "ctx": {"q": query, "src": source, "b": bucket, "v": venue},
                "seed": first,
                "spray": deltas,
            }
        )

    payload = {
        "schema": "deepcompression/hybrid/v1",
        "paper_count": len(papers),
        "high_entropy_partitioned": {
            "bucket_count": len(high_blocks),
            "blocks": high_blocks,
        },
        "low_entropy_context_spray": {
            "cell_count": len(low_emitted),
            "cells": low_emitted,
        },
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def compress_payload(raw_bytes: bytes) -> Dict[str, object]:
    compressed = zlib.compress(raw_bytes, level=9)
    return {
        "raw_bytes": len(raw_bytes),
        "compressed_bytes": len(compressed),
        "compression_ratio": round(len(compressed) / max(1, len(raw_bytes)), 6),
        "blob": compressed,
    }


def compare_archive_modes(papers: List[Paper]) -> Dict[str, object]:
    """Compute direct legacy versus partitioned compression metrics on identical inputs."""
    legacy_raw = build_legacy_payload_bytes(papers)
    partitioned_raw = build_partitioned_payload_bytes(papers)
    context_spray_raw = build_context_spray_payload_bytes(papers)
    hybrid_raw = build_hybrid_payload_bytes(papers)

    legacy_stats = compress_payload(legacy_raw)
    partitioned_stats = compress_payload(partitioned_raw)
    context_spray_stats = compress_payload(context_spray_raw)
    hybrid_stats = compress_payload(hybrid_raw)

    legacy_ratio = float(legacy_stats["compression_ratio"])
    partitioned_ratio = float(partitioned_stats["compression_ratio"])
    context_spray_ratio = float(context_spray_stats["compression_ratio"])
    hybrid_ratio = float(hybrid_stats["compression_ratio"])

    candidates = {
        "legacy": int(legacy_stats["compressed_bytes"]),
        "partitioned": int(partitioned_stats["compressed_bytes"]),
        "context_spray": int(context_spray_stats["compressed_bytes"]),
        "hybrid": int(hybrid_stats["compressed_bytes"]),
    }
    auto_winner_mode = min(candidates.keys(), key=lambda m: candidates[m])

    return {
        "legacy": {
            "raw_bytes": legacy_stats["raw_bytes"],
            "compressed_bytes": legacy_stats["compressed_bytes"],
            "compression_ratio": legacy_ratio,
        },
        "partitioned": {
            "raw_bytes": partitioned_stats["raw_bytes"],
            "compressed_bytes": partitioned_stats["compressed_bytes"],
            "compression_ratio": partitioned_ratio,
        },
        "context_spray": {
            "raw_bytes": context_spray_stats["raw_bytes"],
            "compressed_bytes": context_spray_stats["compressed_bytes"],
            "compression_ratio": context_spray_ratio,
        },
        "hybrid": {
            "raw_bytes": hybrid_stats["raw_bytes"],
            "compressed_bytes": hybrid_stats["compressed_bytes"],
            "compression_ratio": hybrid_ratio,
        },
        "auto_winner": {
            "mode": auto_winner_mode,
            "compressed_bytes": candidates[auto_winner_mode],
        },
        "delta": {
            "partitioned_compressed_bytes_saved": int(legacy_stats["compressed_bytes"]) - int(partitioned_stats["compressed_bytes"]),
            "context_spray_compressed_bytes_saved": int(legacy_stats["compressed_bytes"]) - int(context_spray_stats["compressed_bytes"]),
            "hybrid_compressed_bytes_saved": int(legacy_stats["compressed_bytes"]) - int(hybrid_stats["compressed_bytes"]),
            "compression_ratio_improvement": round(legacy_ratio - partitioned_ratio, 6),
            "improved": partitioned_ratio < legacy_ratio,
            "context_spray_ratio_improvement": round(legacy_ratio - context_spray_ratio, 6),
            "context_spray_improved": context_spray_ratio < legacy_ratio,
            "hybrid_ratio_improvement": round(legacy_ratio - hybrid_ratio, 6),
            "hybrid_improved": hybrid_ratio < legacy_ratio,
        },
    }


def read_archive_domain_from_omnitoken_surface() -> Dict[str, object]:
    if not os.path.exists(OMNITOKEN_SURFACE_PATH):
        return {
            "status": "unavailable",
            "reason": "omnitoken_surface_not_found",
            "surface_path": OMNITOKEN_SURFACE_PATH,
        }

    try:
        with open(OMNITOKEN_SURFACE_PATH, "r", encoding="utf-8") as f:
            surface = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {
            "status": "unreadable",
            "reason": "invalid_surface_json",
            "surface_path": OMNITOKEN_SURFACE_PATH,
        }

    if not isinstance(surface, dict):
        return {
            "status": "unreadable",
            "reason": "surface_not_object",
            "surface_path": OMNITOKEN_SURFACE_PATH,
        }

    surface_bus = surface.get("surface_bus") if isinstance(surface.get("surface_bus"), dict) else {}
    domains = surface_bus.get("domains") if isinstance(surface_bus.get("domains"), dict) else {}
    archive_domain = domains.get("archive_compression") if isinstance(domains.get("archive_compression"), dict) else {}

    if archive_domain:
        _ = logic_signal_substrate_from_surface(archive_domain)
        return {
            "status": "ok",
            "source": "surface_bus.domains.archive_compression",
            "domain": archive_domain,
            "translation_runtime": {
                "mode": "pure_logic_signal_substrate_internal",
                "logic_signal_substrate_exposed": False,
            },
        }

    legacy_domain = surface.get("archive_surface") if isinstance(surface.get("archive_surface"), dict) else {}
    if legacy_domain:
        _ = logic_signal_substrate_from_surface(legacy_domain)
        return {
            "status": "ok",
            "source": "archive_surface",
            "domain": legacy_domain,
            "translation_runtime": {
                "mode": "pure_logic_signal_substrate_internal",
                "logic_signal_substrate_exposed": False,
            },
        }

    return {
        "status": "unavailable",
        "reason": "archive_domain_missing",
        "surface_path": OMNITOKEN_SURFACE_PATH,
    }


def publish_archive_domain_to_omnitoken_surface(archive_domain: Dict[str, object], manifest_path: str) -> None:
    os.makedirs(OMNITOKEN_DIR, exist_ok=True)

    logic_signal_substrate_state = logic_signal_substrate_from_archive_domain(archive_domain)
    translated_surface_domain = surface_from_logic_signal_substrate(logic_signal_substrate_state)

    surface: Dict[str, object] = {}
    if os.path.exists(OMNITOKEN_SURFACE_PATH):
        try:
            with open(OMNITOKEN_SURFACE_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                surface = loaded
        except (OSError, json.JSONDecodeError):
            surface = {}

    surface_bus = dict(surface.get("surface_bus") or {})
    domains = dict(surface_bus.get("domains") or {})
    domains["archive_compression"] = translated_surface_domain
    surface_bus["schema"] = str(surface_bus.get("schema") or "omnitoken-surface-bus/v1")
    surface_bus["agnostic"] = True
    surface_bus["domains"] = domains
    surface["surface_bus"] = surface_bus
    surface["archive_surface"] = translated_surface_domain
    surface["updated_utc"] = datetime.now(timezone.utc).isoformat()
    surface["archive_manifest_path"] = manifest_path

    assert_surface_write_safe(surface, scope="omnitoken_surface")
    with open(OMNITOKEN_SURFACE_PATH, "w", encoding="utf-8") as f:
        json.dump(surface, f, indent=2)

    profile_path_obj = surface.get("profile")
    if isinstance(profile_path_obj, str) and os.path.exists(profile_path_obj):
        try:
            with open(profile_path_obj, "r", encoding="utf-8") as f:
                profile = json.load(f)
            if isinstance(profile, dict):
                p_surface_bus = dict(profile.get("surface_bus") or {})
                p_domains = dict(p_surface_bus.get("domains") or {})
                p_domains["archive_compression"] = translated_surface_domain
                p_surface_bus["schema"] = str(p_surface_bus.get("schema") or "omnitoken-surface-bus/v1")
                p_surface_bus["agnostic"] = True
                p_surface_bus["domains"] = p_domains
                profile["surface_bus"] = p_surface_bus
                profile["archive_surface"] = translated_surface_domain
                profile["updated_utc"] = datetime.now(timezone.utc).isoformat()
                assert_surface_write_safe(profile, scope="omnitoken_profile")
                with open(profile_path_obj, "w", encoding="utf-8") as f:
                    json.dump(profile, f, indent=2)
        except (OSError, json.JSONDecodeError):
            pass


def write_blackhole_vault_with_mode(
    vault_dir: str,
    papers: List[Paper],
    run_id: str,
    archive_mode: str,
    benchmark_against_legacy: bool,
) -> str:
    os.makedirs(vault_dir, exist_ok=True)
    raw_jsonl = os.path.join(vault_dir, f"papers_{run_id}.jsonl")
    write_jsonl(raw_jsonl, papers)

    benchmark = compare_archive_modes(papers)
    inbound_surface = read_archive_domain_from_omnitoken_surface()

    if archive_mode == "auto":
        archive_mode = str(benchmark["auto_winner"]["mode"])

    if archive_mode == "partitioned":
        raw_bytes = build_partitioned_payload_bytes(papers)
        payload_format = "partitioned_bucket_streams"
    elif archive_mode == "context-spray":
        raw_bytes = build_context_spray_payload_bytes(papers)
        payload_format = "context_sensitive_spray_cells"
    elif archive_mode == "hybrid":
        raw_bytes = build_hybrid_payload_bytes(papers)
        payload_format = "hybrid_partitioned_context"
    else:
        raw_bytes = build_legacy_payload_bytes(papers)
        payload_format = "legacy_jsonl"

    compressed = zlib.compress(raw_bytes, level=9)
    blob_path = os.path.join(vault_dir, f"blackhole_{run_id}.zlib")
    with open(blob_path, "wb") as f:
        f.write(compressed)

    manifest = {
        "run_id": run_id,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "paper_count": len(papers),
        "raw_jsonl": raw_jsonl,
        "compressed_blob": blob_path,
        "archive_mode": archive_mode,
        "payload_format": payload_format,
        "raw_bytes": len(raw_bytes),
        "compressed_bytes": len(compressed),
        "compression_ratio": round(len(compressed) / max(1, len(raw_bytes)), 4),
        "nibble_bucket_mean": round(
            statistics.mean((p.relevance_bucket_4bit for p in papers)) if papers else 0.0,
            4,
        ),
        "nibble_index": [
            {
                "key": dedupe_key(p),
                "bucket4": p.relevance_bucket_4bit,
                "fingerprint16": p.nibble_fingerprint_hex,
            }
            for p in papers
        ],
        "omnitoken_surface_input": inbound_surface,
    }

    if benchmark_against_legacy:
        manifest["archive_mode_benchmark"] = benchmark

    manifest_path = os.path.join(vault_dir, f"manifest_{run_id}.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    archive_domain = {
        "domain": "archive_compression",
        "selection_policy": "auto_smallest_compressed_bytes",
        "selected_mode": archive_mode,
        "payload_format": payload_format,
        "raw_bytes": int(len(raw_bytes)),
        "compressed_bytes": int(len(compressed)),
        "manifest_path": manifest_path,
        "benchmark": benchmark,
        "updated_utc": datetime.now(timezone.utc).isoformat(),
    }
    publish_archive_domain_to_omnitoken_surface(archive_domain, manifest_path)

    return manifest_path


def gather_all(queries: List[str], rows_per_source: int, dry_run: bool) -> Tuple[List[Paper], Dict[str, int], Dict[str, int]]:
    papers: List[Paper] = []
    source_totals = {"crossref": 0, "openalex": 0, "arxiv": 0}
    source_failures = {"crossref": 0, "openalex": 0, "arxiv": 0}

    if dry_run:
        for q in queries[:3]:
            papers.append(
                Paper(
                    source="dry-run",
                    source_id=hashlib.md5(q.encode()).hexdigest(),
                    title=f"Synthetic result for: {q}",
                    abstract="Human safety oversight and intervention threshold under low latency.",
                    authors=["Dry Runner"],
                    year=2026,
                    venue="Simulation",
                    doi="",
                    url="",
                    query=q,
                )
            )
        return papers, source_totals, source_failures

    for q in queries:
        try:
            got = list(from_crossref(q, rows_per_source))
            papers.extend(got)
            source_totals["crossref"] += len(got)
        except RuntimeError as exc:
            source_failures["crossref"] += 1
            print(f"[warn] crossref failed for query={q!r}: {exc}")

        try:
            got = list(from_openalex(q, rows_per_source))
            papers.extend(got)
            source_totals["openalex"] += len(got)
        except RuntimeError as exc:
            source_failures["openalex"] += 1
            print(f"[warn] openalex failed for query={q!r}: {exc}")

        try:
            got = list(from_arxiv(q, rows_per_source))
            papers.extend(got)
            source_totals["arxiv"] += len(got)
        except (RuntimeError, ET.ParseError) as exc:
            source_failures["arxiv"] += 1
            print(f"[warn] arxiv failed for query={q!r}: {exc}")

    return papers, source_totals, source_failures


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="High-coverage literature harvesting with DeepCompression vault output.")
    p.add_argument("--query", action="append", default=[], help="Query string (repeatable).")
    p.add_argument("--rows-per-source", type=int, default=35, help="Rows per source per query.")
    p.add_argument("--out-dir", default=os.path.join(PROJECT_ROOT, "literature_blackhole"), help="Output directory.")
    p.add_argument("--min-total-per-source", type=int, default=1, help="Fail run if any source returns fewer total records than this.")
    p.add_argument(
        "--archive-mode",
        choices=["legacy", "partitioned", "context-spray", "hybrid", "auto"],
        default="auto",
        help="Archive payload encoding mode.",
    )
    p.add_argument(
        "--benchmark-against-legacy",
        action="store_true",
        help="Include direct legacy-versus-selected-mode compression comparison in manifest.",
    )
    p.add_argument("--dry-run", action="store_true", help="Use synthetic records and skip network calls.")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    queries = args.query if args.query else DEFAULT_QUERIES

    run_id = now_utc()
    all_papers, source_totals, source_failures = gather_all(queries, args.rows_per_source, args.dry_run)

    if not args.dry_run:
        low_sources = find_low_coverage_sources(source_totals, args.min_total_per_source)
        if low_sources:
            print(json.dumps({
                "error": "insufficient_source_coverage",
                "min_total_per_source": int(args.min_total_per_source),
                "source_totals": source_totals,
                "source_failures": source_failures,
                "low_sources": low_sources,
            }, indent=2))
            return 3

    scored = enrich_scores(all_papers)
    deduped = dedupe(scored)

    deduped.sort(key=lambda p: (p.relevance_score, p.year or 0), reverse=True)

    out_dir = args.out_dir
    os.makedirs(out_dir, exist_ok=True)
    dedup_jsonl = os.path.join(out_dir, f"deduped_{run_id}.jsonl")
    dedup_csv = os.path.join(out_dir, f"deduped_{run_id}.csv")
    write_jsonl(dedup_jsonl, deduped)
    write_csv(dedup_csv, deduped)

    manifest = write_blackhole_vault_with_mode(
        vault_dir=os.path.join(out_dir, "vault"),
        papers=deduped,
        run_id=run_id,
        archive_mode=args.archive_mode,
        benchmark_against_legacy=bool(args.benchmark_against_legacy),
    )

    summary = {
        "run_id": run_id,
        "dry_run": bool(args.dry_run),
        "queries": len(queries),
        "raw_records": len(scored),
        "deduped_records": len(deduped),
        "source_totals": source_totals,
        "source_failures": source_failures,
        "top_titles": [p.title for p in deduped[:5]],
        "outputs": {
            "dedup_jsonl": dedup_jsonl,
            "dedup_csv": dedup_csv,
            "manifest": manifest,
        },
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
