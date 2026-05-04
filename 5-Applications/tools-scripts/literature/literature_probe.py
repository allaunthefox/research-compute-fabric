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
"""Question-focused literature probe using official scholarly APIs.

This script is intentionally tuned for "boundary mapping" rather than broad
harvesting. It takes one research question, queries several official scholarly
APIs, deduplicates results, scores them against the actual question, extracts
recurring nearby vocabulary, and labels the likely kind of wall you are
running into.

Default sources:
- OpenAlex
- Crossref
- Semantic Scholar Graph API
- arXiv API

No third-party dependencies are required.
"""

import argparse
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = PROJECT_ROOT / "out" / "literature_probe"
BASE_USER_AGENT = "research-stack-literature-probe/1.0"

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "because", "by", "can", "could",
    "do", "does", "for", "from", "how", "if", "in", "into", "is", "it", "its",
    "more", "not", "of", "on", "or", "our", "same", "should", "so", "than",
    "that", "the", "their", "them", "there", "these", "they", "this", "to",
    "under", "use", "using", "various", "we", "what", "when", "where", "which",
    "while", "who", "why", "with", "would", "you", "your",
}

LOW_SIGNAL_TERMS = {
    "analysis", "approach", "approaches", "based", "compare", "compares",
    "comparison", "effect", "effects", "framework", "general", "including",
    "method", "methods", "model", "models", "moving", "preserve",
    "preserves", "preserving", "problem", "problems", "process", "results",
    "same", "structure", "study", "system", "systems", "transition",
    "transitions", "various",
}

WALL_KEYWORDS = {
    "theoretical": {
        "theorem", "proof", "relaxation", "formulation", "branch", "bound",
        "semidefinite", "optimization", "manifold", "algorithm", "convergence",
        "objective", "quadratic", "mixed-integer", "qubo", "ising",
    },
    "experimental": {
        "experiment", "experimental", "measurement", "empirical", "benchmark",
        "prototype", "study", "observed", "measured", "dataset", "validation",
        "trial", "evaluation", "performance",
    },
    "fabrication": {
        "fabrication", "synthesis", "material", "materials", "device", "thin",
        "film", "mxene", "nanoscroll", "electrode", "deposition", "etching",
        "semiconductor", "substrate", "sensor",
    },
    "scaling": {
        "scale", "scaling", "runtime", "complexity", "large-scale", "embedding",
        "memory", "qubits", "hardware", "rate-limit", "bottleneck",
        "throughput", "latency", "benchmarking",
    },
    "terminology": {
        "survey", "review", "introduction", "overview", "taxonomy", "framework",
        "perspective", "tutorial", "terminology", "glossary",
    },
}

SOURCE_PRIORITY = {
    "semantic_scholar": 4.0,
    "google_scholar": 3.0,   # scholarly (pip install scholarly); blocked = silent skip
    "openalex": 2.5,
    "crossref": 1.5,
    "arxiv": 1.0,
}

PIPELINE_FLAT = "flat"
PIPELINE_STAGED = "staged"
PIPELINE_COMPARE = "compare"

STAGE_INGEST = "ingest_sieve"
STAGE_BREAKUP = "breakup_normalization"
STAGE_CLASSIFY = "classification_sieve"
STAGE_LIBERATE = "liberation_aggregation"
STAGE_HANDOFF = "recovery_handoff"

DEFAULT_CLASSIFY_WINDOW = 24
DEFAULT_MIN_RELEVANCE = 3.5


@dataclass
class Paper:
    title: str
    abstract: str
    authors: List[str]
    year: Optional[int]
    venue: str
    doi: str
    url: str
    sources: List[str] = field(default_factory=list)
    source_ids: List[str] = field(default_factory=list)
    queries: List[str] = field(default_factory=list)
    citations: int = 0
    fields_of_study: List[str] = field(default_factory=list)
    relevance_score: float = 0.0
    matched_terms: List[str] = field(default_factory=list)


class ApiFetchError(RuntimeError):
    pass


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def normalize_title(text: str) -> str:
    text = normalize_ws(text).lower()
    return re.sub(r"[^a-z0-9 ]+", "", text)


def safe_int(value: object) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def slugify(text: str, max_len: int = 80) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len] or "probe"


def unique_preserve(items: Iterable[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for item in items:
        key = normalize_ws(item)
        if not key:
            continue
        folded = key.lower()
        if folded in seen:
            continue
        seen.add(folded)
        out.append(key)
    return out


def text_tokens(text: str) -> List[str]:
    return [tok for tok in re.findall(r"[a-z0-9][a-z0-9\-]+", text.lower()) if tok not in STOPWORDS]


def content_terms(text: str, max_terms: int = 8) -> List[str]:
    tokens = [tok for tok in text_tokens(text) if len(tok) > 2 and tok not in LOW_SIGNAL_TERMS]
    ranked = []
    seen = set()
    for tok in tokens:
        if tok in seen:
            continue
        seen.add(tok)
        ranked.append(tok)
    return ranked[:max_terms]


def question_ngrams(question: str) -> List[str]:
    terms = content_terms(question, max_terms=12)
    ngrams: List[str] = []
    for n in (2, 3):
        for i in range(0, len(terms) - n + 1):
            ngrams.append(" ".join(terms[i : i + n]))
    return unique_preserve(ngrams)


def derive_queries(question: str, extra_queries: Sequence[str]) -> List[str]:
    queries = [normalize_ws(question)]
    keywords = content_terms(question, max_terms=8)
    if len(keywords) >= 3:
        queries.append(" ".join(keywords))
    queries.extend(extra_queries)
    return unique_preserve(queries)


def build_user_agent() -> str:
    mailto = os.getenv("LITERATURE_PROBE_MAILTO") or os.getenv("CROSSREF_MAILTO")
    if mailto:
        return f"{BASE_USER_AGENT} (mailto:{mailto})"
    return BASE_USER_AGENT


def classify_source_error(message: str) -> str:
    lowered = (message or "").lower()
    if "429" in lowered or "too many requests" in lowered or "rate limit" in lowered:
        return "rate_limited"
    if "401" in lowered or "403" in lowered:
        return "auth"
    if "timed out" in lowered or "timeout" in lowered:
        return "timeout"
    if lowered:
        return "error"
    return ""


def fetch_json(url: str, headers: Optional[Dict[str, str]] = None, timeout: float = 30.0) -> dict:
    hdrs = {"User-Agent": build_user_agent()}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        raise ApiFetchError(f"{exc.code} from {url}: {body[:240]}") from exc
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
        raise ApiFetchError(f"failed fetching {url}: {exc}") from exc


def fetch_text(url: str, timeout: float = 30.0) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": build_user_agent()})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise ApiFetchError(f"{exc.code} from {url}") from exc
    except (urllib.error.URLError, OSError) as exc:
        raise ApiFetchError(f"failed fetching {url}: {exc}") from exc


def abstract_from_openalex_index(index: dict) -> str:
    if not index:
        return ""
    max_pos = 0
    for positions in index.values():
        for pos in positions:
            if pos > max_pos:
                max_pos = pos
    tokens = [""] * (max_pos + 1)
    for token, positions in index.items():
        for pos in positions:
            if 0 <= pos < len(tokens):
                tokens[pos] = token
    return normalize_ws(" ".join(tokens))


def paper_key(paper: Paper) -> str:
    if paper.doi:
        return f"doi:{paper.doi.lower()}"
    return f"title:{normalize_title(paper.title)}"


def merge_paper(existing: Paper, incoming: Paper) -> Paper:
    if len(incoming.abstract) > len(existing.abstract):
        existing.abstract = incoming.abstract
    if len(incoming.authors) > len(existing.authors):
        existing.authors = incoming.authors
    if existing.year is None and incoming.year is not None:
        existing.year = incoming.year
    if not existing.venue and incoming.venue:
        existing.venue = incoming.venue
    if not existing.doi and incoming.doi:
        existing.doi = incoming.doi
    if not existing.url and incoming.url:
        existing.url = incoming.url
    existing.citations = max(existing.citations, incoming.citations)
    existing.sources = unique_preserve(existing.sources + incoming.sources)
    existing.source_ids = unique_preserve(existing.source_ids + incoming.source_ids)
    existing.queries = unique_preserve(existing.queries + incoming.queries)
    existing.fields_of_study = unique_preserve(existing.fields_of_study + incoming.fields_of_study)
    return existing


def from_openalex(query: str, limit: int) -> List[Paper]:
    params = {"search": query, "per-page": str(limit)}
    mailto = os.getenv("LITERATURE_PROBE_MAILTO")
    if mailto:
        params["mailto"] = mailto
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    data = fetch_json(url)
    papers: List[Paper] = []
    for item in data.get("results", []):
        title = normalize_ws(item.get("display_name", ""))
        if not title:
            continue
        fields = []
        primary_topic = (item.get("primary_topic") or {}).get("display_name")
        if primary_topic:
            fields.append(normalize_ws(primary_topic))
        for concept in item.get("concepts", []) or []:
            name = normalize_ws(concept.get("display_name", ""))
            if name:
                fields.append(name)
        papers.append(
            Paper(
                title=title,
                abstract=abstract_from_openalex_index(item.get("abstract_inverted_index") or {}),
                authors=[
                    normalize_ws(((auth.get("author") or {}).get("display_name", "")))
                    for auth in (item.get("authorships") or [])
                    if normalize_ws(((auth.get("author") or {}).get("display_name", "")))
                ],
                year=safe_int(item.get("publication_year")),
                venue=normalize_ws((((item.get("primary_location") or {}).get("source") or {}).get("display_name", ""))),
                doi=normalize_ws((item.get("doi") or "").replace("https://doi.org/", "")),
                url=normalize_ws(item.get("id", "")),
                sources=["openalex"],
                source_ids=[normalize_ws(item.get("id", ""))],
                queries=[query],
                citations=safe_int(item.get("cited_by_count")) or 0,
                fields_of_study=unique_preserve(fields),
            )
        )
    return papers


def from_crossref(query: str, limit: int) -> List[Paper]:
    params = {
        "query": query,
        "rows": str(limit),
        "select": ",".join(
            [
                "DOI",
                "title",
                "author",
                "container-title",
                "URL",
                "published-print",
                "published-online",
                "issued",
                "abstract",
                "subject",
                "is-referenced-by-count",
            ]
        ),
    }
    mailto = os.getenv("LITERATURE_PROBE_MAILTO") or os.getenv("CROSSREF_MAILTO")
    if mailto:
        params["mailto"] = mailto
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
    data = fetch_json(url)
    papers: List[Paper] = []
    for item in data.get("message", {}).get("items", []):
        title_parts = item.get("title", []) if isinstance(item.get("title", []), list) else [str(item.get("title", ""))]
        title = normalize_ws(" ".join(title_parts))
        if not title:
            continue
        year = None
        for field_name in ("published-print", "published-online", "issued"):
            date_parts = (((item.get(field_name) or {}).get("date-parts") or [[None]])[0] or [None])
            year = safe_int(date_parts[0])
            if year is not None:
                break
        abstract = normalize_ws(re.sub(r"<[^>]+>", " ", item.get("abstract", "") or ""))
        authors = []
        for author in item.get("author", []) or []:
            full = normalize_ws(f"{author.get('given', '')} {author.get('family', '')}")
            if full:
                authors.append(full)
        venue_parts = item.get("container-title", []) if isinstance(item.get("container-title", []), list) else [str(item.get("container-title", ""))]
        fields = [normalize_ws(subject) for subject in (item.get("subject") or []) if normalize_ws(subject)]
        papers.append(
            Paper(
                title=title,
                abstract=abstract,
                authors=authors,
                year=year,
                venue=normalize_ws(" ".join(venue_parts)),
                doi=normalize_ws(item.get("DOI", "")),
                url=normalize_ws(item.get("URL", "")),
                sources=["crossref"],
                source_ids=[normalize_ws(item.get("DOI", "") or item.get("URL", ""))],
                queries=[query],
                citations=safe_int(item.get("is-referenced-by-count")) or 0,
                fields_of_study=unique_preserve(fields),
            )
        )
    return papers


def from_semantic_scholar(query: str, limit: int) -> List[Paper]:
    params = {
        "query": query,
        "limit": str(limit),
        "fields": ",".join(
            [
                "title",
                "abstract",
                "year",
                "venue",
                "url",
                "authors",
                "externalIds",
                "citationCount",
                "fieldsOfStudy",
            ]
        ),
    }
    headers: Dict[str, str] = {}
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    if api_key:
        headers["x-api-key"] = api_key
    url = "https://api.semanticscholar.org/graph/v1/paper/search?" + urllib.parse.urlencode(params)
    data = fetch_json(url, headers=headers)
    papers: List[Paper] = []
    for item in data.get("data", []):
        title = normalize_ws(item.get("title", ""))
        if not title:
            continue
        external_ids = item.get("externalIds") or {}
        doi = normalize_ws(external_ids.get("DOI", ""))
        fields = [normalize_ws(field) for field in (item.get("fieldsOfStudy") or []) if normalize_ws(field)]
        papers.append(
            Paper(
                title=title,
                abstract=normalize_ws(item.get("abstract", "")),
                authors=[normalize_ws(author.get("name", "")) for author in (item.get("authors") or []) if normalize_ws(author.get("name", ""))],
                year=safe_int(item.get("year")),
                venue=normalize_ws(item.get("venue", "")),
                doi=doi,
                url=normalize_ws(item.get("url", "")),
                sources=["semantic_scholar"],
                source_ids=[normalize_ws(item.get("paperId", "") or item.get("url", ""))],
                queries=[query],
                citations=safe_int(item.get("citationCount")) or 0,
                fields_of_study=unique_preserve(fields),
            )
        )
    return papers


def from_arxiv(query: str, limit: int) -> List[Paper]:
    q = urllib.parse.quote(query)
    url = f"https://export.arxiv.org/api/query?search_query=all:{q}&start=0&max_results={limit}"
    text = fetch_text(url)
    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    root = ET.fromstring(text)
    papers: List[Paper] = []
    for entry in root.findall("atom:entry", ns):
        title = normalize_ws(entry.findtext("atom:title", default="", namespaces=ns) or "")
        if not title:
            continue
        doi = ""
        doi_node = entry.find("arxiv:doi", ns)
        if doi_node is not None and (doi_node.text or "").strip():
            doi = normalize_ws(doi_node.text)
        papers.append(
            Paper(
                title=title,
                abstract=normalize_ws(entry.findtext("atom:summary", default="", namespaces=ns) or ""),
                authors=[
                    normalize_ws(author.findtext("atom:name", default="", namespaces=ns) or "")
                    for author in entry.findall("atom:author", ns)
                    if normalize_ws(author.findtext("atom:name", default="", namespaces=ns) or "")
                ],
                year=safe_int((entry.findtext("atom:published", default="", namespaces=ns) or "")[:4]),
                venue="arXiv",
                doi=doi,
                url=normalize_ws(entry.findtext("atom:id", default="", namespaces=ns) or ""),
                sources=["arxiv"],
                source_ids=[normalize_ws(entry.findtext("atom:id", default="", namespaces=ns) or "")],
                queries=[query],
                citations=0,
                fields_of_study=["preprint"],
            )
        )
    return papers


def from_google_scholar(query: str, limit: int) -> List[Paper]:
    """Fetch from Google Scholar via the `scholarly` library (pip install scholarly).

    scholarly is an unofficial scraper — Google blocks with CAPTCHAs under
    heavy load.  This function returns [] silently when:
      - scholarly is not installed
      - Google returns a CAPTCHA / rate-limit
    No proxy is configured; install scholarly and run at low request rates.
    """
    try:
        import itertools
        import scholarly as _scholarly  # type: ignore
    except ImportError:
        return []

    papers: List[Paper] = []
    try:
        iterator = _scholarly.search_pubs(query)
        for result in itertools.islice(iterator, limit):
            bib = result.get("bib") or {}
            title = normalize_ws(bib.get("title", ""))
            if not title:
                continue
            raw_authors = bib.get("author", "")
            if isinstance(raw_authors, list):
                authors = [normalize_ws(a) for a in raw_authors if normalize_ws(a)]
            else:
                authors = [normalize_ws(a) for a in re.split(r"\s+and\s+|,\s*", raw_authors) if normalize_ws(a)]
            year_raw = bib.get("pub_year", "") or bib.get("year", "")
            venue = normalize_ws(bib.get("venue", "") or bib.get("journal", "") or bib.get("booktitle", ""))
            url = normalize_ws(result.get("pub_url", "") or result.get("eprint_url", ""))
            cites = safe_int(result.get("num_citations")) or 0
            papers.append(
                Paper(
                    title=title,
                    abstract=normalize_ws(bib.get("abstract", "")),
                    authors=authors,
                    year=safe_int(str(year_raw)[:4]) if year_raw else None,
                    venue=venue,
                    doi="",
                    url=url,
                    sources=["google_scholar"],
                    source_ids=[url or title[:80]],
                    queries=[query],
                    citations=cites,
                    fields_of_study=[],
                )
            )
    except Exception:
        # CAPTCHA, network error, or scholarly internal error — return what we have
        pass
    return papers


def dedupe_and_merge(papers: Sequence[Paper]) -> List[Paper]:
    merged: Dict[str, Paper] = {}
    for paper in papers:
        key = paper_key(paper)
        if key in merged:
            merged[key] = merge_paper(merged[key], paper)
        else:
            merged[key] = paper
    return list(merged.values())


def score_paper(paper: Paper, question: str) -> Tuple[float, List[str]]:
    question_terms = set(content_terms(question, max_terms=12))
    paper_title_terms = set(text_tokens(paper.title))
    paper_body_terms = set(text_tokens(f"{paper.title} {paper.abstract} {' '.join(paper.fields_of_study)} {paper.venue}"))
    overlaps = sorted(question_terms & paper_body_terms)
    q_ngrams = question_ngrams(question)
    haystack = f"{paper.title} {paper.abstract}".lower()
    phrase_hits = sum(1 for ngram in q_ngrams if ngram and ngram in haystack)
    score = 0.0
    score += 3.0 * len(question_terms & paper_title_terms)
    score += 1.2 * len(overlaps)
    score += 2.5 * phrase_hits
    if paper.abstract:
        score += 1.0
    if paper.citations > 0:
        score += min(4.0, math.log10(paper.citations + 1) * 1.5)
    score += source_preference_score(paper)
    return round(score, 3), overlaps


def source_preference_score(paper: Paper) -> float:
    if not paper.sources:
        return 0.0
    max_source = max(SOURCE_PRIORITY.get(source, 0.0) for source in paper.sources)
    diversity_bonus = min(0.6, 0.15 * max(0, len(paper.sources) - 1))
    return max_source * 0.25 + diversity_bonus


def stage_record(
    name: str,
    input_count: int,
    output_count: int,
    note: str,
    metrics: Optional[Dict[str, object]] = None,
) -> dict:
    row = {
        "stage": name,
        "input_count": input_count,
        "output_count": output_count,
        "note": note,
    }
    if metrics:
        row["metrics"] = metrics
    return row


def average_relevance(papers: Sequence[Paper], top_n: int = 12) -> float:
    window = list(papers[:top_n])
    if not window:
        return 0.0
    return round(sum(p.relevance_score for p in window) / len(window), 3)


def average_matched_terms(papers: Sequence[Paper], top_n: int = 12) -> float:
    window = list(papers[:top_n])
    if not window:
        return 0.0
    return round(sum(len(p.matched_terms) for p in window) / len(window), 3)


def select_candidate_window(
    ranked: Sequence[Paper],
    classify_window: int,
    min_relevance: float,
) -> List[Paper]:
    capped = max(1, classify_window)
    kept = [paper for paper in ranked if paper.relevance_score >= min_relevance]
    if kept:
        return kept[:capped]
    return list(ranked[:capped])


def rank_papers(papers: Sequence[Paper], question: str) -> List[Paper]:
    ranked: List[Paper] = []
    for paper in papers:
        score, overlaps = score_paper(paper, question)
        paper.relevance_score = score
        paper.matched_terms = overlaps
        ranked.append(paper)
    ranked.sort(key=lambda p: (-p.relevance_score, -(p.citations or 0), -(p.year or 0), p.title.lower()))
    return ranked


def recurring_terms(papers: Sequence[Paper], question: str, top_k: int = 12) -> List[str]:
    question_terms = set(content_terms(question, max_terms=12))
    counts: Counter[str] = Counter()
    for paper in papers[:12]:
        tokens = [tok for tok in text_tokens(f"{paper.title} {paper.abstract}") if len(tok) > 2]
        for n in (1, 2, 3):
            for i in range(0, len(tokens) - n + 1):
                phrase = " ".join(tokens[i : i + n])
                parts = phrase.split()
                if all(part in question_terms for part in parts):
                    continue
                if any(part in STOPWORDS for part in parts):
                    continue
                counts[phrase] += 1
    ranked = [term for term, count in counts.most_common(top_k * 4) if count >= 2]
    ranked.sort(key=lambda term: (-len(term.split()), -counts[term], term))
    return ranked[:top_k]


def nearby_fields(papers: Sequence[Paper], top_k: int = 10) -> List[str]:
    counts: Counter[str] = Counter()
    for paper in papers[:20]:
        for field_name in paper.fields_of_study:
            counts[normalize_ws(field_name)] += 1
    return [field_name for field_name, _ in counts.most_common(top_k)]


def source_contribution_summary(papers: Sequence[Paper], top_n: int = 12) -> Dict[str, int]:
    counts: Counter[str] = Counter()
    for paper in papers[:top_n]:
        for source in paper.sources:
            counts[source] += 1
    return dict(counts.most_common())


def wall_signals(papers: Sequence[Paper], question: str) -> Dict[str, float]:
    if not papers:
        return {"evidence_gap": 1.0}

    corpus = " ".join(
        normalize_ws(
            " ".join(
                [
                    paper.title,
                    paper.abstract,
                    paper.venue,
                    " ".join(paper.fields_of_study),
                ]
            )
        ).lower()
        for paper in papers[:12]
    )
    scores: Dict[str, float] = {}
    for wall_type, keywords in WALL_KEYWORDS.items():
        score = 0.0
        for keyword in keywords:
            if keyword in corpus:
                score += 1.0
        scores[wall_type] = score

    avg_relevance = sum(p.relevance_score for p in papers[:8]) / max(1, min(len(papers), 8))
    if len(papers) < 5 or avg_relevance < 4.0:
        scores["evidence_gap"] = scores.get("evidence_gap", 0.0) + 3.0

    question_terms = set(content_terms(question, max_terms=12))
    overlap_total = sum(len(p.matched_terms) for p in papers[:8])
    if papers and overlap_total <= max(2, len(question_terms) // 2):
        scores["terminology"] = scores.get("terminology", 0.0) + 2.0

    return scores


def likely_wall_type(papers: Sequence[Paper], question: str) -> Tuple[str, Dict[str, float]]:
    scores = wall_signals(papers, question)
    if not scores:
        return "evidence_gap", {"evidence_gap": 1.0}
    wall_type = max(scores, key=lambda key: scores[key])
    rounded = {key: round(value, 3) for key, value in sorted(scores.items())}
    return wall_type, rounded


def to_json_ready(papers: Sequence[Paper]) -> List[dict]:
    rows = []
    for paper in papers:
        rows.append(asdict(paper))
    return rows


def markdown_summary(
    question: str,
    queries: Sequence[str],
    wall_type: str,
    wall_scores: Dict[str, float],
    source_stats: Dict[str, dict],
    source_contributions: Dict[str, int],
    recurring: Sequence[str],
    fields: Sequence[str],
    papers: Sequence[Paper],
    pipeline_mode: str = PIPELINE_FLAT,
    stage_trace: Optional[Sequence[dict]] = None,
) -> str:
    lines = [
        f"# Literature Probe",
        "",
        f"**Question:** {question}",
        "",
        f"**Pipeline:** `{pipeline_mode}`",
        "",
        f"**Likely wall type:** `{wall_type}`",
        "",
        "## Queries",
        "",
    ]
    for query in queries:
        lines.append(f"- `{query}`")
    if stage_trace:
        lines.extend(["", "## Stage Trace", ""])
        for stage in stage_trace:
            line = (
                f"- `{stage.get('stage', '')}`: "
                f"{stage.get('input_count', 0)} -> {stage.get('output_count', 0)}"
            )
            note = normalize_ws(str(stage.get("note", "")))
            if note:
                line += f" | {note}"
            lines.append(line)
    lines.extend(["", "## Wall Signals", ""])
    for key, value in sorted(wall_scores.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Source Stats", ""])
    for source_name, stats in source_stats.items():
        line = f"- `{source_name}`: {stats.get('count', 0)} papers"
        if stats.get("status"):
            line += f" | status: {stats['status']}"
        if stats.get("error"):
            line += f" | error: {stats['error']}"
        lines.append(line)
    if source_contributions:
        lines.extend(["", "## Source Contribution In Top Papers", ""])
        for source_name, count in source_contributions.items():
            lines.append(f"- `{source_name}`: {count} of top 12")
    if recurring:
        lines.extend(["", "## Recurring Terms", ""])
        for term in recurring:
            lines.append(f"- `{term}`")
    if fields:
        lines.extend(["", "## Nearby Fields", ""])
        for field_name in fields:
            lines.append(f"- `{field_name}`")
    lines.extend(["", "## Top Papers", ""])
    for index, paper in enumerate(papers[:12], start=1):
        authors = ", ".join(paper.authors[:4])
        details = []
        if paper.year:
            details.append(str(paper.year))
        if paper.venue:
            details.append(paper.venue)
        if paper.sources:
            details.append("sources: " + "/".join(paper.sources))
        if paper.citations:
            details.append(f"citations: {paper.citations}")
        if paper.matched_terms:
            details.append("matched: " + ", ".join(paper.matched_terms[:6]))
        detail_text = " | ".join(details)
        lines.append(f"{index}. [{paper.title}]({paper.url or paper.doi or '#'})")
        if detail_text:
            lines.append(f"   {detail_text}")
        if authors:
            lines.append(f"   {authors}")
    lines.append("")
    return "\n".join(lines)


def markdown_compare_summary(result: dict) -> str:
    comparison = result["comparison"]
    flat = result["flat_result"]
    staged = result["staged_result"]
    lines = [
        "# Literature Probe Pipeline Comparison",
        "",
        f"**Question:** {result['question']}",
        "",
        "## Summary",
        "",
        f"- Flat top-12 average relevance: `{comparison['flat_top12_avg_relevance']}`",
        f"- Staged top-12 average relevance: `{comparison['staged_top12_avg_relevance']}`",
        f"- Flat final paper count: `{comparison['flat_final_paper_count']}`",
        f"- Staged final paper count: `{comparison['staged_final_paper_count']}`",
        f"- Staged burden reduction vs flat: `{comparison['staged_burden_reduction_ratio']}`",
        f"- Top-12 overlap count: `{comparison['top12_overlap_count']}`",
        "",
        "## Flat Stage Trace",
        "",
    ]
    for stage in flat.get("stage_trace", []):
        lines.append(
            f"- `{stage.get('stage', '')}`: {stage.get('input_count', 0)} -> {stage.get('output_count', 0)}"
        )
    lines.extend(["", "## Staged Stage Trace", ""])
    for stage in staged.get("stage_trace", []):
        lines.append(
            f"- `{stage.get('stage', '')}`: {stage.get('input_count', 0)} -> {stage.get('output_count', 0)}"
        )
    lines.extend(["", "## Top-12 Overlap Titles", ""])
    for title in comparison.get("top12_overlap_titles", []):
        lines.append(f"- {title}")
    if not comparison.get("top12_overlap_titles"):
        lines.append("- none")
    lines.extend(["", "## Interpretation", ""])
    lines.append(comparison["interpretation"])
    lines.append("")
    return "\n".join(lines)


def fetch_all_papers(
    queries: Sequence[str],
    per_source: int,
) -> Tuple[List[Paper], Dict[str, dict], List[dict]]:
    all_papers: List[Paper] = []
    source_stats: Dict[str, dict] = {}
    events: List[dict] = []

    fetchers = {
        "semantic_scholar": from_semantic_scholar,
        "openalex": from_openalex,
        "crossref": from_crossref,
        "arxiv": from_arxiv,
    }
    try:
        import scholarly  # noqa: F401
        fetchers["google_scholar"] = from_google_scholar
    except ImportError:
        pass

    for source_name, fetcher in fetchers.items():
        source_total = 0
        error_text = ""
        status = "ok"
        for query in queries:
            try:
                results = fetcher(query, per_source)
            except ApiFetchError as exc:
                error_text = str(exc)
                status = classify_source_error(error_text)
                events.append(
                    {
                        "source": source_name,
                        "query": query,
                        "status": status,
                        "message": error_text,
                    }
                )
                continue
            source_total += len(results)
            all_papers.extend(results)
            time.sleep(0.15)
        source_stats[source_name] = {"count": source_total, "error": error_text, "status": status}

    return all_papers, source_stats, events


def build_probe_result(
    *,
    question: str,
    queries: Sequence[str],
    source_stats: Dict[str, dict],
    events: List[dict],
    wall_type: str,
    wall_scores: Dict[str, float],
    recurring: Sequence[str],
    fields: Sequence[str],
    source_contributions: Dict[str, int],
    papers: Sequence[Paper],
    pipeline_mode: str,
    stage_trace: Sequence[dict],
    raw_hit_count: int,
    deduped_paper_count: int,
    classified_paper_count: int,
    final_paper_count: int,
    classify_window: int,
    min_relevance: float,
    candidate_selection_note: str,
) -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "queries": list(queries),
        "pipeline_mode": pipeline_mode,
        "stage_trace": list(stage_trace),
        "wall_type": wall_type,
        "wall_scores": wall_scores,
        "recurring_terms": list(recurring),
        "nearby_fields": list(fields),
        "source_stats": source_stats,
        "source_contributions_top12": source_contributions,
        "events": events,
        "raw_hit_count": raw_hit_count,
        "deduped_paper_count": deduped_paper_count,
        "classified_paper_count": classified_paper_count,
        "final_paper_count": final_paper_count,
        "top12_avg_relevance": average_relevance(papers),
        "top12_avg_matched_terms": average_matched_terms(papers),
        "classify_window": classify_window,
        "min_relevance": min_relevance,
        "candidate_selection_note": candidate_selection_note,
        "papers": to_json_ready(papers),
    }


def run_probe_flat(
    question: str,
    extra_queries: Sequence[str],
    per_source: int,
    classify_window: int = DEFAULT_CLASSIFY_WINDOW,
    min_relevance: float = DEFAULT_MIN_RELEVANCE,
) -> dict:
    queries = derive_queries(question, extra_queries)
    all_papers, source_stats, events = fetch_all_papers(queries, per_source)
    deduped = dedupe_and_merge(all_papers)
    ranked = rank_papers(deduped, question)
    wall_type, wall_scores = likely_wall_type(ranked, question)
    recurring = recurring_terms(ranked, question)
    fields = nearby_fields(ranked)
    source_contributions = source_contribution_summary(ranked)
    top_window = min(12, len(ranked))
    stage_trace = [
        stage_record(
            STAGE_INGEST,
            len(queries),
            len(all_papers),
            "Fetched raw candidate hits across all configured scholarly sources.",
            {"query_count": len(queries), "per_source": per_source},
        ),
        stage_record(
            STAGE_BREAKUP,
            len(all_papers),
            len(deduped),
            "Normalized and deduplicated records into one comparable candidate set.",
        ),
        stage_record(
            STAGE_CLASSIFY,
            len(deduped),
            len(ranked),
            "Ranked all deduplicated candidates without narrowing the result window.",
            {"selection_mode": "flat_full_rank"},
        ),
        stage_record(
            STAGE_LIBERATE,
            len(ranked),
            top_window,
            "Derived recurring terms, nearby fields, and wall signals from the top-ranked set.",
        ),
        stage_record(
            STAGE_HANDOFF,
            top_window,
            len(ranked),
            "Returned the full ranked list as the flat baseline handoff surface.",
        ),
    ]
    return build_probe_result(
        question=question,
        queries=queries,
        source_stats=source_stats,
        events=events,
        wall_type=wall_type,
        wall_scores=wall_scores,
        recurring=recurring,
        fields=fields,
        source_contributions=source_contributions,
        papers=ranked,
        pipeline_mode=PIPELINE_FLAT,
        stage_trace=stage_trace,
        raw_hit_count=len(all_papers),
        deduped_paper_count=len(deduped),
        classified_paper_count=len(ranked),
        final_paper_count=len(ranked),
        classify_window=classify_window,
        min_relevance=min_relevance,
        candidate_selection_note="Flat baseline keeps the full ranked list after scoring.",
    )


def run_probe_staged(
    question: str,
    extra_queries: Sequence[str],
    per_source: int,
    classify_window: int = DEFAULT_CLASSIFY_WINDOW,
    min_relevance: float = DEFAULT_MIN_RELEVANCE,
) -> dict:
    queries = derive_queries(question, extra_queries)
    all_papers, source_stats, events = fetch_all_papers(queries, per_source)
    deduped = dedupe_and_merge(all_papers)
    ranked = rank_papers(deduped, question)
    candidates = select_candidate_window(ranked, classify_window, min_relevance)
    wall_type, wall_scores = likely_wall_type(candidates, question)
    recurring = recurring_terms(candidates, question)
    fields = nearby_fields(candidates)
    source_contributions = source_contribution_summary(candidates)
    stage_trace = [
        stage_record(
            STAGE_INGEST,
            len(queries),
            len(all_papers),
            "Fetched raw candidate hits across all configured scholarly sources.",
            {"query_count": len(queries), "per_source": per_source},
        ),
        stage_record(
            STAGE_BREAKUP,
            len(all_papers),
            len(deduped),
            "Normalized and deduplicated records into one comparable candidate set.",
        ),
        stage_record(
            STAGE_CLASSIFY,
            len(deduped),
            len(candidates),
            "Scored candidates and kept only the bounded relevance window.",
            {"classify_window": max(1, classify_window), "min_relevance": min_relevance},
        ),
        stage_record(
            STAGE_LIBERATE,
            len(candidates),
            min(12, len(candidates)),
            "Computed recurring terms, nearby fields, and wall signals only from the retained relevance slice.",
        ),
        stage_record(
            STAGE_HANDOFF,
            min(12, len(candidates)),
            len(candidates),
            "Returned the narrowed candidate slice as the staged handoff surface.",
        ),
    ]
    return build_probe_result(
        question=question,
        queries=queries,
        source_stats=source_stats,
        events=events,
        wall_type=wall_type,
        wall_scores=wall_scores,
        recurring=recurring,
        fields=fields,
        source_contributions=source_contributions,
        papers=candidates,
        pipeline_mode=PIPELINE_STAGED,
        stage_trace=stage_trace,
        raw_hit_count=len(all_papers),
        deduped_paper_count=len(deduped),
        classified_paper_count=len(candidates),
        final_paper_count=len(candidates),
        classify_window=classify_window,
        min_relevance=min_relevance,
        candidate_selection_note=(
            "Staged mode keeps only the bounded relevance window after classification "
            "so later aggregation and handoff operate on a smaller, more explainable slice."
        ),
    )


def compare_probe_results(flat_result: dict, staged_result: dict) -> dict:
    flat_papers = [Paper(**paper) for paper in flat_result["papers"]]
    staged_papers = [Paper(**paper) for paper in staged_result["papers"]]
    flat_top = flat_papers[:12]
    staged_top = staged_papers[:12]
    flat_titles = {normalize_title(p.title): p.title for p in flat_top}
    staged_titles = {normalize_title(p.title): p.title for p in staged_top}
    overlap_keys = sorted(set(flat_titles) & set(staged_titles))
    overlap_titles = [flat_titles[key] for key in overlap_keys]
    flat_final = max(1, flat_result.get("final_paper_count", len(flat_papers)))
    staged_final = staged_result.get("final_paper_count", len(staged_papers))
    burden_ratio = round(staged_final / flat_final, 3)
    staged_gain = round(
        staged_result.get("top12_avg_relevance", 0.0) - flat_result.get("top12_avg_relevance", 0.0),
        3,
    )
    if staged_gain > 0:
        interpretation = (
            "The staged path kept a smaller candidate surface while slightly increasing "
            "top-result relevance density."
        )
    elif staged_gain < 0:
        interpretation = (
            "The staged path reduced burden, but it also lowered top-result relevance density "
            "for this query and should be tuned."
        )
    else:
        interpretation = (
            "The staged path reduced burden without materially changing top-result relevance density "
            "for this query."
        )
    return {
        "flat_top12_avg_relevance": flat_result.get("top12_avg_relevance", 0.0),
        "staged_top12_avg_relevance": staged_result.get("top12_avg_relevance", 0.0),
        "flat_top12_avg_matched_terms": flat_result.get("top12_avg_matched_terms", 0.0),
        "staged_top12_avg_matched_terms": staged_result.get("top12_avg_matched_terms", 0.0),
        "flat_final_paper_count": flat_result.get("final_paper_count", len(flat_papers)),
        "staged_final_paper_count": staged_result.get("final_paper_count", len(staged_papers)),
        "staged_burden_reduction_ratio": burden_ratio,
        "top12_overlap_count": len(overlap_titles),
        "top12_overlap_titles": overlap_titles,
        "interpretation": interpretation,
    }


def run_probe(
    question: str,
    extra_queries: Sequence[str],
    per_source: int,
    pipeline_mode: str = PIPELINE_FLAT,
    classify_window: int = DEFAULT_CLASSIFY_WINDOW,
    min_relevance: float = DEFAULT_MIN_RELEVANCE,
) -> dict:
    if pipeline_mode == PIPELINE_STAGED:
        return run_probe_staged(question, extra_queries, per_source, classify_window, min_relevance)
    if pipeline_mode == PIPELINE_COMPARE:
        flat_result = run_probe_flat(question, extra_queries, per_source, classify_window, min_relevance)
        staged_result = run_probe_staged(question, extra_queries, per_source, classify_window, min_relevance)
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "question": question,
            "pipeline_mode": PIPELINE_COMPARE,
            "flat_result": flat_result,
            "staged_result": staged_result,
            "comparison": compare_probe_results(flat_result, staged_result),
        }
    return run_probe_flat(question, extra_queries, per_source, classify_window, min_relevance)


def write_outputs(result: dict, out_dir: Path) -> Tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = now_utc()
    pipeline_mode = result.get("pipeline_mode", PIPELINE_FLAT)
    stem = f"{stamp}_{slugify(result['question'])}_{pipeline_mode}"
    json_path = out_dir / f"{stem}.json"
    md_path = out_dir / f"{stem}.md"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    if pipeline_mode == PIPELINE_COMPARE:
        md_path.write_text(markdown_compare_summary(result), encoding="utf-8")
    else:
        papers = [Paper(**paper) for paper in result["papers"]]
        md_path.write_text(
            markdown_summary(
                question=result["question"],
                queries=result["queries"],
                wall_type=result["wall_type"],
                wall_scores=result["wall_scores"],
                source_stats=result["source_stats"],
                source_contributions=result["source_contributions_top12"],
                recurring=result["recurring_terms"],
                fields=result["nearby_fields"],
                papers=papers,
                pipeline_mode=pipeline_mode,
                stage_trace=result.get("stage_trace"),
            ),
            encoding="utf-8",
        )
    return json_path, md_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Probe scholarly literature around one research question.")
    parser.add_argument("question", help="Research question to probe.")
    parser.add_argument(
        "--extra-query",
        action="append",
        default=[],
        help="Optional extra focused search query. Can be used multiple times.",
    )
    parser.add_argument(
        "--per-source",
        type=int,
        default=8,
        help="Number of results to request from each source for each query.",
    )
    parser.add_argument(
        "--pipeline",
        choices=[PIPELINE_FLAT, PIPELINE_STAGED, PIPELINE_COMPARE],
        default=PIPELINE_FLAT,
        help="Choose the retrieval/compression posture to run.",
    )
    parser.add_argument(
        "--classify-window",
        type=int,
        default=DEFAULT_CLASSIFY_WINDOW,
        help="Maximum number of candidates retained after the classification sieve in staged mode.",
    )
    parser.add_argument(
        "--min-relevance",
        type=float,
        default=DEFAULT_MIN_RELEVANCE,
        help="Minimum relevance score to keep during the classification sieve in staged mode.",
    )
    parser.add_argument(
        "--out-dir",
        default=str(DEFAULT_OUT_DIR),
        help="Directory to write JSON and Markdown outputs.",
    )
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Also print the final JSON result to stdout.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = run_probe(
        args.question,
        args.extra_query,
        max(1, args.per_source),
        pipeline_mode=args.pipeline,
        classify_window=max(1, args.classify_window),
        min_relevance=args.min_relevance,
    )
    json_path, md_path = write_outputs(result, Path(args.out_dir))

    print(f"Question: {result['question']}")
    print(f"Pipeline: {result.get('pipeline_mode', PIPELINE_FLAT)}")
    if result.get("pipeline_mode") == PIPELINE_COMPARE:
        comparison = result["comparison"]
        print(f"Flat top-12 avg relevance: {comparison['flat_top12_avg_relevance']}")
        print(f"Staged top-12 avg relevance: {comparison['staged_top12_avg_relevance']}")
        print(f"Top-12 overlap count: {comparison['top12_overlap_count']}")
        print(f"Staged burden reduction ratio: {comparison['staged_burden_reduction_ratio']}")
    else:
        print(f"Likely wall type: {result['wall_type']}")
        print(f"Final paper count: {result.get('final_paper_count', len(result.get('papers', [])))}")
    print(f"Wrote JSON: {json_path}")
    print(f"Wrote Markdown: {md_path}")
    source_stats = (
        result["flat_result"]["source_stats"]
        if result.get("pipeline_mode") == PIPELINE_COMPARE
        else result["source_stats"]
    )
    if source_stats.get("semantic_scholar", {}).get("status") == "rate_limited":
        print("Semantic Scholar status: rate-limited; using fallback sources for this run")
    else:
        print("Semantic Scholar status:", source_stats.get("semantic_scholar", {}).get("status", "unknown"))
    recurring_terms = (
        result["staged_result"]["recurring_terms"]
        if result.get("pipeline_mode") == PIPELINE_COMPARE
        else result["recurring_terms"]
    )
    nearby_fields_list = (
        result["staged_result"]["nearby_fields"]
        if result.get("pipeline_mode") == PIPELINE_COMPARE
        else result["nearby_fields"]
    )
    print("Top recurring terms:", ", ".join(recurring_terms[:8]) or "none")
    print("Nearby fields:", ", ".join(nearby_fields_list[:8]) or "none")

    if args.print_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
