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
"""Fetch a web PDF, extract text, and scaffold a session capsule.

This helper is the practical bridge between scholarly search APIs and the
repo's local ingestion workflow.

Supported inputs:
- `--query` with `--source` = `auto|semantic_scholar|openalex|crossref|arxiv`
- `--doi`
- `--url`
- `--pdf-url`

Artifacts created by default:
- `6-Documentation/archive/PRIOR_ART/<slug>/<slug>.pdf`
- `6-Documentation/archive/PRIOR_ART/<slug>/<slug>.pdfinfo.txt`
- `6-Documentation/archive/PRIOR_ART/<slug>/<slug>.txt`
- `6-Documentation/archive/PRIOR_ART/<slug>/<slug>.source.json`
- `sessions/<slug>.json`
- `sessions/<slug>.md`
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from literature_probe import ApiFetchError, build_user_agent, fetch_json, fetch_text, normalize_ws, safe_int, slugify  # noqa: E402


DEFAULT_ARCHIVE_ROOT = REPO / "archive" / "PRIOR_ART"
DEFAULT_SESSIONS_ROOT = REPO / "sessions"
DEFAULT_LIMIT = 5

SOURCE_PRIORITY = {
    "semantic_scholar": 4.0,
    "openalex": 3.0,
    "crossref": 2.0,
    "arxiv": 1.5,
    "crossref_doi": 3.5,
    "openalex_doi": 3.25,
    "direct": 0.5,
}

PIPELINE_FLAT = "flat"
PIPELINE_STAGED = "staged"
PIPELINE_COMPARE = "compare"

STAGE_INGEST = "ingest_sieve"
STAGE_BREAKUP = "breakup_normalization"
STAGE_CLASSIFY = "classification_sieve"
STAGE_LIBERATE = "liberation_aggregation"
STAGE_HANDOFF = "recovery_handoff"

DEFAULT_CLASSIFY_WINDOW = 8
DEFAULT_MIN_CANDIDATE_SCORE = 8.0


@dataclass
class SearchHit:
    title: str = ""
    authors: List[str] = field(default_factory=list)
    year: Optional[int] = None
    venue: str = ""
    doi: str = ""
    url: str = ""
    pdf_url: str = ""
    publication: str = ""
    institution: str = ""
    source_type: str = ""
    citations: int = 0
    query: str = ""
    sources: List[str] = field(default_factory=list)
    source_ids: List[str] = field(default_factory=list)


@dataclass
class IntentSpec:
    story: str = "REFERENCE"
    source_role: str = ""
    capture_reason: str = ""
    expected_use: str = ""
    research_questions: List[str] = field(default_factory=list)
    project_threads: List[str] = field(default_factory=list)
    intent_tags: List[str] = field(default_factory=list)
    prior_art_distinction: str = ""


@dataclass
class PlatformContext:
    platform: str = ""
    kind: str = ""
    handle: str = ""
    community: str = ""
    post_id: str = ""
    thread_id: str = ""
    canonical_url: str = ""


def stage_record(
    name: str,
    input_count: int,
    output_count: int,
    note: str,
    metrics: Optional[Dict[str, object]] = None,
) -> Dict[str, object]:
    row: Dict[str, object] = {
        "stage": name,
        "input_count": input_count,
        "output_count": output_count,
        "note": note,
    }
    if metrics:
        row["metrics"] = metrics
    return row


def parse_external_inspirations(values: Sequence[str]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for raw in values:
        text = normalize_ws(raw)
        if not text:
            continue
        parts = [normalize_ws(part) for part in text.split("|", 2)]
        while len(parts) < 3:
            parts.append("")
        title, url, note = parts
        row: Dict[str, str] = {"relationship": "conceptual_inspiration"}
        if title:
            row["title"] = title
        if url:
            row["url"] = url
        if note:
            row["note"] = note
        rows.append(row)
    return rows


def build_external_boundary(args: argparse.Namespace) -> Dict[str, object]:
    inspirations = parse_external_inspirations(getattr(args, "external_inspiration", []) or [])
    code_sources = unique_preserve(getattr(args, "external_code_source", []) or [])
    code_used = bool(getattr(args, "external_code_used", False))
    code_note = normalize_ws(getattr(args, "external_code_note", ""))
    if not code_note:
        if code_used:
            code_note = "External code or code snippets were used and should be traced to the recorded sources."
        else:
            code_note = "No external code or code snippets were recorded for this artifact."
    return {
        "external_inspiration": inspirations,
        "external_code_use": {
            "used": code_used,
            "sources": code_sources,
            "note": code_note,
        },
    }


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def repo_rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def normalize_doi(value: str) -> str:
    text = normalize_ws(value)
    text = re.sub(r"^https?://(dx\.)?doi\.org/", "", text, flags=re.IGNORECASE)
    return text


def family_name(author: str) -> str:
    tokens = [tok for tok in normalize_ws(author).split(" ") if tok]
    return tokens[-1] if tokens else ""


def derive_arxiv_pdf_url(value: str) -> str:
    text = normalize_ws(value)
    if not text:
        return ""
    if re.match(r"^[a-z\-]+/\d{7}$", text) or re.match(r"^\d{4}\.\d{4,5}(v\d+)?$", text):
        return f"https://arxiv.org/pdf/{text}.pdf"
    if "arxiv.org/pdf/" in text:
        return text if text.lower().endswith(".pdf") else f"{text}.pdf"
    if "arxiv.org/abs/" in text:
        return re.sub(r"/abs/", "/pdf/", text) + ".pdf"
    return ""


def extract_doi_from_text(value: str) -> str:
    text = normalize_ws(value)
    if not text:
        return ""
    match = re.search(r"(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)", text)
    if not match:
        return ""
    doi = match.group(1).rstrip(").,;]")
    return normalize_doi(doi)


def extract_arxiv_id(value: str) -> str:
    text = normalize_ws(value)
    if not text:
        return ""
    patterns = [
        r"arxiv\.org/(?:abs|pdf)/([a-z\-]+/\d{7}|\d{4}\.\d{4,5}(?:v\d+)?)",
        r"^([a-z\-]+/\d{7}|\d{4}\.\d{4,5}(?:v\d+)?)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            arxiv_id = normalize_ws(match.group(1))
            return arxiv_id.removesuffix(".pdf")
    return ""


def same_text(value: str) -> str:
    return normalize_ws(value).lower()


def hit_key(hit: SearchHit) -> str:
    if hit.doi:
        return f"doi:{hit.doi.lower()}"
    return f"title:{slugify(hit.title or hit.url or 'hit', max_len=120)}"


def merge_hits(existing: SearchHit, incoming: SearchHit) -> SearchHit:
    if len(incoming.title) > len(existing.title):
        existing.title = incoming.title
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
    if not existing.pdf_url and incoming.pdf_url:
        existing.pdf_url = incoming.pdf_url
    if not existing.publication and incoming.publication:
        existing.publication = incoming.publication
    if not existing.institution and incoming.institution:
        existing.institution = incoming.institution
    if not existing.source_type and incoming.source_type:
        existing.source_type = incoming.source_type
    existing.citations = max(existing.citations, incoming.citations)
    existing.sources = unique_preserve(existing.sources + incoming.sources)
    existing.source_ids = unique_preserve(existing.source_ids + incoming.source_ids)
    return existing


def unique_preserve(items: Iterable[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for item in items:
        norm = same_text(item)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        out.append(normalize_ws(item))
    return out


def normalize_story(value: str) -> str:
    text = normalize_ws(value)
    if not text:
        return "REFERENCE"
    text = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
    return text.upper() or "REFERENCE"


def normalize_label_list(items: Iterable[str]) -> List[str]:
    return unique_preserve(normalize_ws(item) for item in items if normalize_ws(item))


def default_source_role(story: str) -> str:
    return normalize_story(story).lower().replace("_", "-")


def tagify_label(value: str) -> str:
    text = normalize_ws(value).replace("_", "-")
    return slugify(text, max_len=64)


def sentence_text(value: str) -> str:
    return normalize_ws(value).rstrip(".!?")


def clean_host(host: str) -> str:
    host = normalize_ws(host).lower()
    if host.startswith("www."):
        return host[4:]
    return host


def infer_platform_context(url: str) -> PlatformContext:
    text = normalize_ws(url)
    if not text:
        return PlatformContext()
    parsed = urllib.parse.urlparse(text)
    host = clean_host(parsed.netloc)
    parts = [part for part in parsed.path.split("/") if part]

    if host in {"x.com", "twitter.com", "mobile.twitter.com"}:
        if len(parts) >= 3 and parts[1] == "status":
            handle = f"@{parts[0]}"
            post_id = parts[2]
            return PlatformContext(
                platform="twitter",
                kind="post",
                handle=handle,
                post_id=post_id,
                thread_id=post_id,
                canonical_url=f"https://x.com/{parts[0]}/status/{post_id}",
            )
        if parts:
            return PlatformContext(
                platform="twitter",
                kind="profile",
                handle=f"@{parts[0]}",
                canonical_url=f"https://x.com/{parts[0]}",
            )

    if host == "redd.it" and parts:
        post_id = parts[0]
        return PlatformContext(
            platform="reddit",
            kind="thread",
            post_id=post_id,
            thread_id=post_id,
            canonical_url=f"https://www.reddit.com/comments/{post_id}",
        )

    if host.endswith("reddit.com"):
        if len(parts) >= 4 and parts[0] == "r" and parts[2] == "comments":
            community = f"r/{parts[1]}"
            thread_id = parts[3]
            post_id = parts[5] if len(parts) >= 6 else thread_id
            return PlatformContext(
                platform="reddit",
                kind="thread" if post_id == thread_id else "comment",
                community=community,
                post_id=post_id,
                thread_id=thread_id,
                canonical_url=f"https://www.reddit.com/r/{parts[1]}/comments/{thread_id}/",
            )
        if len(parts) >= 2 and parts[0] in {"u", "user"}:
            handle = f"u/{parts[1]}"
            if len(parts) >= 4 and parts[2] == "comments":
                thread_id = parts[3]
                post_id = parts[5] if len(parts) >= 6 else thread_id
                return PlatformContext(
                    platform="reddit",
                    kind="thread" if post_id == thread_id else "comment",
                    handle=handle,
                    post_id=post_id,
                    thread_id=thread_id,
                    canonical_url=f"https://www.reddit.com/{parts[0]}/{parts[1]}/comments/{thread_id}/",
                )
            return PlatformContext(
                platform="reddit",
                kind="profile",
                handle=handle,
                canonical_url=f"https://www.reddit.com/{parts[0]}/{parts[1]}/",
            )

    if len(parts) >= 1 and parts[0].startswith("@"):
        user = parts[0][1:]
        handle = f"@{user}@{host}" if host else f"@{user}"
        if len(parts) >= 2 and parts[1].isdigit():
            post_id = parts[1]
            return PlatformContext(
                platform="mastodon",
                kind="post",
                handle=handle,
                post_id=post_id,
                thread_id=post_id,
                canonical_url=f"{parsed.scheme or 'https'}://{host}/@{user}/{post_id}",
            )
        return PlatformContext(
            platform="mastodon",
            kind="profile",
            handle=handle,
            canonical_url=f"{parsed.scheme or 'https'}://{host}/@{user}",
        )

    if len(parts) >= 4 and parts[0] == "users" and parts[2] == "statuses":
        user = parts[1]
        post_id = parts[3]
        return PlatformContext(
            platform="mastodon",
            kind="post",
            handle=f"@{user}@{host}" if host else f"@{user}",
            post_id=post_id,
            thread_id=post_id,
            canonical_url=f"{parsed.scheme or 'https'}://{host}/users/{user}/statuses/{post_id}",
        )

    return PlatformContext()


def choose_openalex_pdf(item: dict) -> str:
    locations: List[dict] = []
    best = item.get("best_oa_location")
    if isinstance(best, dict):
        locations.append(best)
    for loc in item.get("locations", []) or []:
        if isinstance(loc, dict):
            locations.append(loc)
    primary = item.get("primary_location")
    if isinstance(primary, dict):
        locations.append(primary)

    for loc in locations:
        pdf_url = normalize_ws(loc.get("pdf_url", ""))
        if pdf_url:
            return pdf_url
        for key in ("oa_url", "landing_page_url"):
            url = normalize_ws(loc.get(key, ""))
            if url.lower().endswith(".pdf"):
                return url
    return ""


def choose_crossref_pdf(item: dict) -> str:
    for link in item.get("link", []) or []:
        if not isinstance(link, dict):
            continue
        content_type = same_text(str(link.get("content-type", "")))
        intent = same_text(str(link.get("intended-application", "")))
        url = normalize_ws(link.get("URL", ""))
        if not url:
            continue
        if "pdf" in content_type or url.lower().endswith(".pdf") or "text-mining" in intent:
            return url
    url = normalize_ws(item.get("URL", ""))
    if url.lower().endswith(".pdf"):
        return url
    return ""


def choose_semantic_scholar_pdf(item: dict) -> str:
    pdf = (item.get("openAccessPdf") or {}).get("url", "")
    return normalize_ws(pdf)


def hit_score_components(hit: SearchHit) -> Dict[str, float]:
    source_score = max((SOURCE_PRIORITY.get(source, 0.0) for source in hit.sources), default=0.0)
    pdf_bonus = 8.0 if hit.pdf_url else 0.0
    doi_bonus = 1.5 if hit.doi else 0.0
    cite_bonus = min(5.0, (hit.citations or 0) / 100.0)
    total = round(pdf_bonus + doi_bonus + source_score + cite_bonus, 3)
    return {
        "source_score": round(source_score, 3),
        "pdf_bonus": round(pdf_bonus, 3),
        "doi_bonus": round(doi_bonus, 3),
        "citation_bonus": round(cite_bonus, 3),
        "total": total,
    }


def hit_total_score(hit: SearchHit) -> float:
    return hit_score_components(hit)["total"]


def rank_hits(hits: Sequence[SearchHit]) -> List[SearchHit]:
    def score(hit: SearchHit) -> Tuple[float, int, int, str]:
        year_val = hit.year or 0
        return (hit_total_score(hit), year_val, hit.citations or 0, (hit.title or "").lower())

    return sorted(hits, key=score, reverse=True)


def select_staged_hits(
    ranked: Sequence[SearchHit],
    classify_window: int,
    min_candidate_score: float,
) -> List[SearchHit]:
    capped = max(1, classify_window)
    kept = [hit for hit in ranked if hit_total_score(hit) >= min_candidate_score]
    if kept:
        return kept[:capped]
    return list(ranked[:capped])


def stage_candidate_view(
    hits: Sequence[SearchHit],
    pick: int,
    display_limit: int,
) -> List[SearchHit]:
    return list(hits[: max(pick, min(len(hits), display_limit))])


def dedupe_hits(hits: Sequence[SearchHit]) -> List[SearchHit]:
    merged: Dict[str, SearchHit] = {}
    for hit in hits:
        key = hit_key(hit)
        if key in merged:
            merged[key] = merge_hits(merged[key], hit)
        else:
            merged[key] = hit
    return rank_hits(list(merged.values()))


def search_semantic_scholar(query: str, limit: int) -> List[SearchHit]:
    params = {
        "query": query,
        "limit": str(limit),
        "fields": ",".join(
            [
                "title",
                "year",
                "venue",
                "url",
                "authors",
                "externalIds",
                "citationCount",
                "openAccessPdf",
                "publicationTypes",
                "paperId",
            ]
        ),
    }
    headers: Dict[str, str] = {}
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    if api_key:
        headers["x-api-key"] = api_key
    url = "https://api.semanticscholar.org/graph/v1/paper/search?" + urllib.parse.urlencode(params)
    data = fetch_json(url, headers=headers)
    hits: List[SearchHit] = []
    for item in data.get("data", []) or []:
        title = normalize_ws(item.get("title", ""))
        if not title:
            continue
        external_ids = item.get("externalIds") or {}
        venue = normalize_ws(item.get("venue", ""))
        pub_types = item.get("publicationTypes") or []
        hits.append(
            SearchHit(
                title=title,
                authors=[normalize_ws(author.get("name", "")) for author in (item.get("authors") or []) if normalize_ws(author.get("name", ""))],
                year=safe_int(item.get("year")),
                venue=venue,
                publication=venue,
                doi=normalize_doi(external_ids.get("DOI", "")),
                url=normalize_ws(item.get("url", "")),
                pdf_url=choose_semantic_scholar_pdf(item),
                source_type=normalize_ws(", ".join(pub_types)) or "paper",
                citations=safe_int(item.get("citationCount")) or 0,
                query=query,
                sources=["semantic_scholar"],
                source_ids=[normalize_ws(item.get("paperId", ""))],
            )
        )
    return hits


def search_openalex(query: str, limit: int) -> List[SearchHit]:
    params = {"search": query, "per-page": str(limit)}
    mailto = os.getenv("LITERATURE_PROBE_MAILTO")
    if mailto:
        params["mailto"] = mailto
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    data = fetch_json(url)
    hits: List[SearchHit] = []
    for item in data.get("results", []) or []:
        title = normalize_ws(item.get("display_name", ""))
        if not title:
            continue
        venue = normalize_ws((((item.get("primary_location") or {}).get("source") or {}).get("display_name", "")))
        best = item.get("best_oa_location") or {}
        landing = normalize_ws(best.get("landing_page_url", "")) or normalize_ws(best.get("oa_url", "")) or normalize_ws(item.get("id", ""))
        institution = normalize_ws((((best.get("source") or {}).get("host_organization_name", ""))))
        hits.append(
            SearchHit(
                title=title,
                authors=[
                    normalize_ws(((auth.get("author") or {}).get("display_name", "")))
                    for auth in (item.get("authorships") or [])
                    if normalize_ws(((auth.get("author") or {}).get("display_name", "")))
                ],
                year=safe_int(item.get("publication_year")),
                venue=venue,
                publication=venue,
                institution=institution,
                doi=normalize_doi(item.get("doi", "")),
                url=landing,
                pdf_url=choose_openalex_pdf(item),
                source_type="work",
                citations=safe_int(item.get("cited_by_count")) or 0,
                query=query,
                sources=["openalex"],
                source_ids=[normalize_ws(item.get("id", ""))],
            )
        )
    return hits


def search_crossref(query: str, limit: int) -> List[SearchHit]:
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
                "link",
                "publisher",
                "type",
                "is-referenced-by-count",
            ]
        ),
    }
    mailto = os.getenv("LITERATURE_PROBE_MAILTO") or os.getenv("CROSSREF_MAILTO")
    if mailto:
        params["mailto"] = mailto
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
    data = fetch_json(url)
    hits: List[SearchHit] = []
    for item in data.get("message", {}).get("items", []) or []:
        title_bits = item.get("title", []) if isinstance(item.get("title", []), list) else [str(item.get("title", ""))]
        title = normalize_ws(" ".join(title_bits))
        if not title:
            continue
        year = None
        for field_name in ("published-print", "published-online", "issued"):
            date_parts = (((item.get(field_name) or {}).get("date-parts") or [[None]])[0] or [None])
            year = safe_int(date_parts[0])
            if year is not None:
                break
        venue_bits = item.get("container-title", []) if isinstance(item.get("container-title", []), list) else [str(item.get("container-title", ""))]
        hits.append(
            SearchHit(
                title=title,
                authors=[
                    normalize_ws(f"{author.get('given', '')} {author.get('family', '')}")
                    for author in (item.get("author") or [])
                    if normalize_ws(f"{author.get('given', '')} {author.get('family', '')}")
                ],
                year=year,
                venue=normalize_ws(" ".join(venue_bits)),
                publication=normalize_ws(" ".join(venue_bits)),
                institution=normalize_ws(item.get("publisher", "")),
                doi=normalize_doi(item.get("DOI", "")),
                url=normalize_ws(item.get("URL", "")),
                pdf_url=choose_crossref_pdf(item),
                source_type=normalize_ws(item.get("type", "")),
                citations=safe_int(item.get("is-referenced-by-count")) or 0,
                query=query,
                sources=["crossref"],
                source_ids=[normalize_ws(item.get("DOI", "") or item.get("URL", ""))],
            )
        )
    return hits


def search_arxiv(query: str, limit: int) -> List[SearchHit]:
    q = urllib.parse.quote(query)
    url = f"https://export.arxiv.org/api/query?search_query=all:{q}&start=0&max_results={limit}"
    text = fetch_text(url)
    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    root = ET.fromstring(text)
    hits: List[SearchHit] = []
    for entry in root.findall("atom:entry", ns):
        landing = normalize_ws(entry.findtext("atom:id", default="", namespaces=ns) or "")
        if not landing:
            continue
        title = normalize_ws(entry.findtext("atom:title", default="", namespaces=ns) or "")
        doi_node = entry.find("arxiv:doi", ns)
        doi = normalize_doi(doi_node.text if doi_node is not None and doi_node.text else "")
        hits.append(
            SearchHit(
                title=title,
                authors=[
                    normalize_ws(author.findtext("atom:name", default="", namespaces=ns) or "")
                    for author in entry.findall("atom:author", ns)
                    if normalize_ws(author.findtext("atom:name", default="", namespaces=ns) or "")
                ],
                year=safe_int((entry.findtext("atom:published", default="", namespaces=ns) or "")[:4]),
                venue="arXiv",
                publication="arXiv",
                doi=doi,
                url=landing,
                pdf_url=derive_arxiv_pdf_url(landing),
                source_type="preprint",
                citations=0,
                query=query,
                sources=["arxiv"],
                source_ids=[landing],
            )
        )
    return hits


def lookup_arxiv_id(arxiv_id: str) -> Optional[SearchHit]:
    arxiv_id = extract_arxiv_id(arxiv_id)
    if not arxiv_id:
        return None
    url = f"https://export.arxiv.org/api/query?id_list={urllib.parse.quote(arxiv_id)}"
    text = fetch_text(url)
    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    root = ET.fromstring(text)
    entry = root.find("atom:entry", ns)
    if entry is None:
        return None
    landing = normalize_ws(entry.findtext("atom:id", default="", namespaces=ns) or "")
    doi_node = entry.find("arxiv:doi", ns)
    doi = normalize_doi(doi_node.text if doi_node is not None and doi_node.text else "")
    return SearchHit(
        title=normalize_ws(entry.findtext("atom:title", default="", namespaces=ns) or ""),
        authors=[
            normalize_ws(author.findtext("atom:name", default="", namespaces=ns) or "")
            for author in entry.findall("atom:author", ns)
            if normalize_ws(author.findtext("atom:name", default="", namespaces=ns) or "")
        ],
        year=safe_int((entry.findtext("atom:published", default="", namespaces=ns) or "")[:4]),
        venue="arXiv",
        publication="arXiv",
        doi=doi,
        url=landing,
        pdf_url=derive_arxiv_pdf_url(landing or arxiv_id),
        source_type="preprint",
        citations=0,
        sources=["arxiv"],
        source_ids=[landing or arxiv_id],
    )


def lookup_crossref_doi(doi: str) -> Optional[SearchHit]:
    doi = normalize_doi(doi)
    if not doi:
        return None
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='')}"
    data = fetch_json(url)
    item = (data.get("message") or {})
    title_bits = item.get("title", []) if isinstance(item.get("title", []), list) else [str(item.get("title", ""))]
    title = normalize_ws(" ".join(title_bits))
    if not title:
        return None
    year = None
    for field_name in ("published-print", "published-online", "issued"):
        date_parts = (((item.get(field_name) or {}).get("date-parts") or [[None]])[0] or [None])
        year = safe_int(date_parts[0])
        if year is not None:
            break
    venue_bits = item.get("container-title", []) if isinstance(item.get("container-title", []), list) else [str(item.get("container-title", ""))]
    return SearchHit(
        title=title,
        authors=[
            normalize_ws(f"{author.get('given', '')} {author.get('family', '')}")
            for author in (item.get("author") or [])
            if normalize_ws(f"{author.get('given', '')} {author.get('family', '')}")
        ],
        year=year,
        venue=normalize_ws(" ".join(venue_bits)),
        publication=normalize_ws(" ".join(venue_bits)),
        institution=normalize_ws(item.get("publisher", "")),
        doi=normalize_doi(item.get("DOI", "")),
        url=normalize_ws(item.get("URL", "")),
        pdf_url=choose_crossref_pdf(item),
        source_type=normalize_ws(item.get("type", "")),
        citations=safe_int(item.get("is-referenced-by-count")) or 0,
        sources=["crossref_doi"],
        source_ids=[normalize_ws(item.get("DOI", ""))],
    )


def lookup_openalex_doi(doi: str) -> Optional[SearchHit]:
    doi = normalize_doi(doi)
    if not doi:
        return None
    mailto = os.getenv("LITERATURE_PROBE_MAILTO")
    attempts = [doi, f"https://doi.org/{doi}"]
    for attempt in attempts:
        params = {"filter": f"doi:{attempt}", "per-page": "1"}
        if mailto:
            params["mailto"] = mailto
        url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
        data = fetch_json(url)
        results = data.get("results", []) or []
        if not results:
            continue
        item = results[0]
        title = normalize_ws(item.get("display_name", ""))
        if not title:
            continue
        venue = normalize_ws((((item.get("primary_location") or {}).get("source") or {}).get("display_name", "")))
        best = item.get("best_oa_location") or {}
        landing = normalize_ws(best.get("landing_page_url", "")) or normalize_ws(best.get("oa_url", "")) or normalize_ws(item.get("id", ""))
        institution = normalize_ws((((best.get("source") or {}).get("host_organization_name", ""))))
        return SearchHit(
            title=title,
            authors=[
                normalize_ws(((auth.get("author") or {}).get("display_name", "")))
                for auth in (item.get("authorships") or [])
                if normalize_ws(((auth.get("author") or {}).get("display_name", "")))
            ],
            year=safe_int(item.get("publication_year")),
            venue=venue,
            publication=venue,
            institution=institution,
            doi=normalize_doi(item.get("doi", "")),
            url=landing,
            pdf_url=choose_openalex_pdf(item),
            source_type="work",
            citations=safe_int(item.get("cited_by_count")) or 0,
            sources=["openalex_doi"],
            source_ids=[normalize_ws(item.get("id", ""))],
        )
    return None


def search_hits(query: str, source: str, limit: int) -> List[SearchHit]:
    source = source.lower()
    fetchers = {
        "semantic_scholar": search_semantic_scholar,
        "openalex": search_openalex,
        "crossref": search_crossref,
        "arxiv": search_arxiv,
    }
    if source == "auto":
        hits: List[SearchHit] = []
        for name in ("semantic_scholar", "openalex", "crossref", "arxiv"):
            try:
                hits.extend(fetchers[name](query, limit))
            except ApiFetchError as exc:
                print(f"[warn] {name} search failed: {exc}", file=sys.stderr)
        return dedupe_hits(hits)
    if source not in fetchers:
        raise ValueError(f"unknown source: {source}")
    return dedupe_hits(fetchers[source](query, limit))


def fetch_raw_hits(query: str, source: str, limit: int) -> Tuple[List[SearchHit], Dict[str, object]]:
    source = source.lower()
    fetchers = {
        "semantic_scholar": search_semantic_scholar,
        "openalex": search_openalex,
        "crossref": search_crossref,
        "arxiv": search_arxiv,
    }
    source_stats: Dict[str, object] = {}
    raw_hits: List[SearchHit] = []

    if source == "auto":
        source_names = ["semantic_scholar", "openalex", "crossref", "arxiv"]
    else:
        if source not in fetchers:
            raise ValueError(f"unknown source: {source}")
        source_names = [source]

    for name in source_names:
        try:
            results = fetchers[name](query, limit)
        except ApiFetchError as exc:
            message = str(exc)
            print(f"[warn] {name} search failed: {message}", file=sys.stderr)
            source_stats[name] = {"count": 0, "status": "error", "error": message}
            continue
        raw_hits.extend(results)
        source_stats[name] = {"count": len(results), "status": "ok", "error": ""}

    return raw_hits, source_stats


def build_query_pipeline(
    query: str,
    source: str,
    limit: int,
    pick: int,
    pipeline_mode: str,
    classify_window: int,
    min_candidate_score: float,
) -> Dict[str, object]:
    raw_hits, source_stats = fetch_raw_hits(query, source, limit)
    ranked = dedupe_hits(raw_hits)
    staged = select_staged_hits(ranked, classify_window, min_candidate_score)
    flat_view = stage_candidate_view(ranked, pick, limit)
    staged_view = stage_candidate_view(staged, pick, limit)

    flat_trace = [
        stage_record(
            STAGE_INGEST,
            1,
            len(raw_hits),
            "Fetched raw candidate hits from the configured scholarly source family.",
            {"query": query, "requested_source": source, "per_source_limit": limit},
        ),
        stage_record(
            STAGE_BREAKUP,
            len(raw_hits),
            len(ranked),
            "Normalized and deduplicated candidate records into one ranked comparison surface.",
        ),
        stage_record(
            STAGE_CLASSIFY,
            len(ranked),
            len(ranked),
            "Kept the full ranked candidate set as the flat baseline.",
            {"selection_mode": "flat_full_rank"},
        ),
        stage_record(
            STAGE_LIBERATE,
            len(ranked),
            len(flat_view),
            "Reduced the visible candidate surface to the top ranked records needed for review/pick.",
        ),
        stage_record(
            STAGE_HANDOFF,
            len(flat_view),
            1 if flat_view else 0,
            "Handed one selected candidate to the fetch lane.",
            {"selected_pick": pick},
        ),
    ]

    staged_trace = [
        stage_record(
            STAGE_INGEST,
            1,
            len(raw_hits),
            "Fetched raw candidate hits from the configured scholarly source family.",
            {"query": query, "requested_source": source, "per_source_limit": limit},
        ),
        stage_record(
            STAGE_BREAKUP,
            len(raw_hits),
            len(ranked),
            "Normalized and deduplicated candidate records into one ranked comparison surface.",
        ),
        stage_record(
            STAGE_CLASSIFY,
            len(ranked),
            len(staged),
            "Applied the classification sieve to keep only a bounded relevance window.",
            {"classify_window": max(1, classify_window), "min_candidate_score": min_candidate_score},
        ),
        stage_record(
            STAGE_LIBERATE,
            len(staged),
            len(staged_view),
            "Reduced the visible staged surface to the shortlist needed for review/pick.",
        ),
        stage_record(
            STAGE_HANDOFF,
            len(staged_view),
            1 if staged_view else 0,
            "Handed one selected candidate from the staged shortlist to the fetch lane.",
            {"selected_pick": pick},
        ),
    ]

    comparison = {
        "flat_final_candidate_count": len(ranked),
        "staged_final_candidate_count": len(staged),
        "staged_burden_reduction_ratio": round((len(staged) / max(1, len(ranked))), 3),
        "flat_top_visible_titles": [hit.title for hit in flat_view[:5]],
        "staged_top_visible_titles": [hit.title for hit in staged_view[:5]],
    }

    if pipeline_mode == PIPELINE_STAGED:
        operative = staged
        operative_trace = staged_trace
    elif pipeline_mode == PIPELINE_COMPARE:
        operative = staged
        operative_trace = staged_trace
    else:
        operative = ranked
        operative_trace = flat_trace

    if not operative:
        raise RuntimeError(f"no candidate papers found for query: {query}")

    selected = select_hit(operative, pick)
    operative_view = stage_candidate_view(operative, pick, limit)

    return {
        "pipeline_mode": pipeline_mode,
        "operative_pipeline": PIPELINE_STAGED if pipeline_mode == PIPELINE_COMPARE else pipeline_mode,
        "selected": selected,
        "display_candidates": operative_view,
        "raw_hits": raw_hits,
        "source_stats": source_stats,
        "stage_trace": operative_trace,
        "flat": {
            "candidate_count": len(ranked),
            "display_candidates": flat_view,
            "stage_trace": flat_trace,
        },
        "staged": {
            "candidate_count": len(staged),
            "display_candidates": staged_view,
            "stage_trace": staged_trace,
        },
        "comparison": comparison if pipeline_mode == PIPELINE_COMPARE else {},
    }


def resolve_from_doi(doi: str) -> SearchHit:
    hits: List[SearchHit] = []
    crossref_hit = lookup_crossref_doi(doi)
    if crossref_hit:
        hits.append(crossref_hit)
    try:
        openalex_hit = lookup_openalex_doi(doi)
    except ApiFetchError as exc:
        print(f"[warn] openalex DOI lookup failed: {exc}", file=sys.stderr)
        openalex_hit = None
    if openalex_hit:
        hits.append(openalex_hit)
    if not hits:
        raise RuntimeError(f"could not resolve DOI: {doi}")
    return dedupe_hits(hits)[0]


def resolve_direct(url: str = "", pdf_url: str = "", doi: str = "", title: str = "") -> SearchHit:
    normalized_url = normalize_ws(url)
    normalized_pdf = normalize_ws(pdf_url)
    if not normalized_pdf and normalized_url:
        if normalized_url.lower().endswith(".pdf"):
            normalized_pdf = normalized_url
        elif "arxiv.org/" in normalized_url:
            normalized_pdf = derive_arxiv_pdf_url(normalized_url)
    resolved_title = normalize_ws(title)
    if not resolved_title:
        stem = Path(urllib.parse.urlparse(normalized_pdf or normalized_url).path).stem
        resolved_title = normalize_ws(stem.replace("-", " ").replace("_", " "))
    return SearchHit(
        title=resolved_title,
        doi=normalize_doi(doi),
        url=normalized_url or normalized_pdf,
        pdf_url=normalized_pdf,
        source_type="direct_url",
        sources=["direct"],
        source_ids=[normalized_url or normalized_pdf],
    )


def enrich_direct_hit(hit: SearchHit) -> SearchHit:
    doi = hit.doi or extract_doi_from_text(hit.url) or extract_doi_from_text(hit.pdf_url)
    if doi:
        try:
            doi_hit = resolve_from_doi(doi)
        except Exception as exc:
            print(f"[warn] DOI enrichment failed for {doi}: {exc}", file=sys.stderr)
        else:
            hit.doi = doi
            hit = merge_hits(hit, doi_hit)

    arxiv_id = extract_arxiv_id(hit.url) or extract_arxiv_id(hit.pdf_url)
    if arxiv_id:
        try:
            arxiv_hit = lookup_arxiv_id(arxiv_id)
        except Exception as exc:
            print(f"[warn] arXiv enrichment failed for {arxiv_id}: {exc}", file=sys.stderr)
            arxiv_hit = None
        if arxiv_hit:
            hit = merge_hits(hit, arxiv_hit)

    return hit


def resolve_pdf_url(hit: SearchHit) -> SearchHit:
    if hit.pdf_url:
        return hit
    if hit.url.lower().endswith(".pdf"):
        hit.pdf_url = hit.url
        return hit
    arxiv_pdf = derive_arxiv_pdf_url(hit.url)
    if arxiv_pdf:
        hit.pdf_url = arxiv_pdf
        return hit
    if hit.doi:
        try:
            openalex_hit = lookup_openalex_doi(hit.doi)
        except ApiFetchError as exc:
            print(f"[warn] openalex DOI lookup failed while resolving pdf: {exc}", file=sys.stderr)
            openalex_hit = None
        if openalex_hit and openalex_hit.pdf_url:
            hit = merge_hits(hit, openalex_hit)
            return hit
    return hit


def default_slug(hit: SearchHit) -> str:
    author = family_name(hit.authors[0]) if hit.authors else ""
    year = str(hit.year) if hit.year else ""
    title = hit.title or hit.doi or hit.url or "paper"
    parts = [part for part in [author, title, year] if part]
    return slugify("-".join(parts), max_len=96)


def hit_citation_string(hit: SearchHit) -> str:
    author_part = ", ".join(hit.authors[:4]) if hit.authors else "Unknown author"
    year_part = str(hit.year) if hit.year else "n.d."
    venue = hit.publication or hit.venue or ""
    bits = [f"{author_part} ({year_part})", hit.title]
    if venue:
        bits.append(venue)
    if hit.doi:
        bits.append(f"DOI: {hit.doi}")
    if hit.url:
        bits.append(hit.url)
    return ". ".join(bit for bit in bits if bit).strip()


def build_session_json(
    hit: SearchHit,
    slug: str,
    session_md: Path,
    artifact_dir: Path,
    accessed_utc: str,
    query: str,
    intent: IntentSpec,
    discovery_url: str = "",
    pipeline_report: Optional[Dict[str, object]] = None,
    external_boundary: Optional[Dict[str, object]] = None,
) -> Dict[str, object]:
    pdf_path = artifact_dir / f"{slug}.pdf"
    txt_path = artifact_dir / f"{slug}.txt"
    pdfinfo_path = artifact_dir / f"{slug}.pdfinfo.txt"
    source_path = artifact_dir / f"{slug}.source.json"

    attachments = [
        repo_rel(session_md),
        repo_rel(pdf_path),
        repo_rel(txt_path),
        repo_rel(pdfinfo_path),
        repo_rel(source_path),
    ]
    description_bits = [
        normalize_ws(
            f"Scaffold capsule for {hit.title or slug}. Preserves the local PDF snapshot, "
            f"extracted text, and citation metadata for later semantic distillation."
        )
    ]
    if intent.story or intent.source_role:
        description_bits.append(
            normalize_ws(
                f"Captured under story {intent.story} as {intent.source_role or default_source_role(intent.story)}."
            )
        )
    if intent.capture_reason:
        description_bits.append(f"Reason: {sentence_text(intent.capture_reason)}.")
    if intent.expected_use:
        description_bits.append(f"Expected use: {sentence_text(intent.expected_use)}.")
    if intent.prior_art_distinction:
        description_bits.append(f"Prior-art distinction: {sentence_text(intent.prior_art_distinction)}.")
    description = normalize_ws(" ".join(description_bits))
    title_claim = normalize_ws(hit.title or slug.replace("-", " "))
    source_context = infer_platform_context(hit.url)
    discovery_url = normalize_ws(discovery_url)
    discovery_context = infer_platform_context(discovery_url)
    external_boundary = external_boundary or {
        "external_inspiration": [],
        "external_code_use": {
            "used": False,
            "sources": [],
            "note": "No external code or code snippets were recorded for this artifact.",
        },
    }
    idea_weights = {
        "preserve citation-bearing web PDFs as local source plus extracted text plus session capsule": 0.62,
        f"{title_claim} is preserved locally for later semantic digestion rather than live-url dependence": 0.58,
    }
    extension_points = [
        "Replace scaffold idea_weights with source-specific semantic claims after reading the paper",
        "Link this source to any active research note or theory anchor that depends on it",
        "Promote stable interpretations into a dedicated literature or prior-art session cluster",
    ]
    for question in intent.research_questions:
        extension_points.append(f"Check whether this source materially constrains: {question}")
    for thread in intent.project_threads:
        extension_points.append(f"Cross-link this source into the `{thread}` research thread after reading")
    if intent.prior_art_distinction:
        extension_points.append("Preserve the prior-art distinction when citing or comparing this source")

    story_tag = tagify_label(intent.story)
    role_tag = f"role-{tagify_label(intent.source_role)}" if intent.source_role else ""
    intent_tags = [tagify_label(tag) for tag in intent.intent_tags]
    project_thread_tags = [tagify_label(thread) for thread in intent.project_threads]
    source_platform_tag = f"platform-{tagify_label(source_context.platform)}" if source_context.platform else ""
    discovery_platform_tag = f"discovery-{tagify_label(discovery_context.platform)}" if discovery_context.platform else ""
    payload: Dict[str, object] = {
        "session_id": slug,
        "pkg": slug,
        "version": "1.0.0",
        "layer": "RULE",
        "domain": "DATA",
        "condition": "EXPERIMENTAL",
        "stage": "ACTIVE",
        "source": "NOTE",
        "tier": "RESEARCH",
        "module": "WEB_PDF_SOURCE",
        "archetype": "LITERATURE_SOURCE_SCAFFOLD",
        "description": description,
        "tags": unique_preserve(
            [
                "literature",
                "pdf",
                "web-source",
                story_tag,
                role_tag,
                *intent_tags,
                *project_thread_tags,
                source_platform_tag,
                discovery_platform_tag,
                *(hit.sources or []),
                (hit.source_type or ""),
            ]
        ),
        "visibility": "PRIVATE",
        "concept_anchor": {
            "domain": "research",
            "concept": slug.replace("-", "_"),
            "resolution": "FORMING",
            "story": intent.story,
        },
        "idea_weights": idea_weights,
        "extension_points": extension_points,
        "attachments": attachments,
        "source_role": intent.source_role,
        "capture_reason": intent.capture_reason,
        "expected_use": intent.expected_use,
        "research_questions": intent.research_questions,
        "project_threads": intent.project_threads,
        "intent_tags": intent.intent_tags,
        "source_title": hit.title,
        "source_author": ", ".join(hit.authors),
        "source_publication": hit.publication or hit.venue,
        "source_institution": hit.institution,
        "source_date": str(hit.year) if hit.year else "",
        "source_url": hit.url,
        "source_pdf_url": hit.pdf_url,
        "source_doi": hit.doi,
        "source_type": hit.source_type,
        "source_accessed_utc": accessed_utc,
        "source_query": query,
        "source_search_apis": hit.sources,
        "retrieval_pipeline_mode": (pipeline_report or {}).get("pipeline_mode", PIPELINE_FLAT),
        "retrieval_stage_trace": (pipeline_report or {}).get("stage_trace", []),
        "retrieval_pipeline_comparison": (pipeline_report or {}).get("comparison", {}),
        "external_inspiration": external_boundary["external_inspiration"],
        "external_code_use": external_boundary["external_code_use"],
    }
    if source_context.platform:
        payload["source_platform"] = source_context.platform
    if source_context.kind:
        payload["source_kind"] = source_context.kind
    if source_context.handle:
        payload["source_handle"] = source_context.handle
    if source_context.community:
        payload["source_community"] = source_context.community
    if source_context.post_id:
        payload["source_post_id"] = source_context.post_id
    if source_context.thread_id:
        payload["source_thread_id"] = source_context.thread_id
    if source_context.canonical_url:
        payload["source_canonical_url"] = source_context.canonical_url
    if discovery_url:
        payload["discovery_url"] = discovery_url
    if discovery_context.platform:
        payload["discovery_platform"] = discovery_context.platform
    if discovery_context.kind:
        payload["discovery_kind"] = discovery_context.kind
    if discovery_context.handle:
        payload["discovery_handle"] = discovery_context.handle
    if discovery_context.community:
        payload["discovery_community"] = discovery_context.community
    if discovery_context.post_id:
        payload["discovery_post_id"] = discovery_context.post_id
    if discovery_context.thread_id:
        payload["discovery_thread_id"] = discovery_context.thread_id
    if discovery_context.canonical_url:
        payload["discovery_canonical_url"] = discovery_context.canonical_url
    if intent.prior_art_distinction:
        payload["prior_art_distinction"] = intent.prior_art_distinction
    return payload


def build_session_md(
    hit: SearchHit,
    slug: str,
    artifact_dir: Path,
    accessed_utc: str,
    query: str,
    intent: IntentSpec,
    discovery_url: str = "",
    pipeline_report: Optional[Dict[str, object]] = None,
    external_boundary: Optional[Dict[str, object]] = None,
) -> str:
    pdf_path = artifact_dir / f"{slug}.pdf"
    txt_path = artifact_dir / f"{slug}.txt"
    pdfinfo_path = artifact_dir / f"{slug}.pdfinfo.txt"
    source_path = artifact_dir / f"{slug}.source.json"
    source_context = infer_platform_context(hit.url)
    discovery_url = normalize_ws(discovery_url)
    discovery_context = infer_platform_context(discovery_url)
    external_boundary = external_boundary or {
        "external_inspiration": [],
        "external_code_use": {
            "used": False,
            "sources": [],
            "note": "No external code or code snippets were recorded for this artifact.",
        },
    }

    lines = [
        f"# {hit.title or slug}",
        "",
        "## Provenance",
        "",
        f"- Retrieved: `{accessed_utc}`",
        f"- Search query: `{query}`" if query else "- Search query: `(not recorded)`",
        f"- Search APIs: `{', '.join(hit.sources)}`" if hit.sources else "- Search APIs: `direct`",
        f"- Retrieval pipeline: `{(pipeline_report or {}).get('pipeline_mode', PIPELINE_FLAT)}`",
        f"- Source URL: `{hit.url}`" if hit.url else "- Source URL: `(not recorded)`",
        f"- Source platform: `{source_context.platform}`" if source_context.platform else "- Source platform: `(not inferred)`",
        f"- Source handle/community: `{source_context.handle or source_context.community}`" if (source_context.handle or source_context.community) else "- Source handle/community: `(not inferred)`",
        f"- PDF URL: `{hit.pdf_url}`" if hit.pdf_url else "- PDF URL: `(not resolved)`",
        f"- DOI: `{hit.doi}`" if hit.doi else "- DOI: `(not recorded)`",
        f"- Discovery URL: `{discovery_url}`" if discovery_url else "- Discovery URL: `(not recorded)`",
        f"- Discovery platform: `{discovery_context.platform}`" if discovery_context.platform else "- Discovery platform: `(not inferred)`",
        "",
        "## Citation",
        "",
        hit_citation_string(hit),
        "",
        "## Retrieval Stage Trace",
        "",
    ]
    for stage in (pipeline_report or {}).get("stage_trace", []):
        lines.append(
            f"- `{stage.get('stage', '')}`: {stage.get('input_count', 0)} -> {stage.get('output_count', 0)}"
            + (f" | {normalize_ws(str(stage.get('note', '')))}" if normalize_ws(str(stage.get("note", ""))) else "")
        )
    if not (pipeline_report or {}).get("stage_trace"):
        lines.append("- `(not recorded)`")
    comparison = (pipeline_report or {}).get("comparison") or {}
    if comparison:
        lines.extend([
            "",
            "## Retrieval Comparison",
            "",
            f"- Flat final candidate count: `{comparison.get('flat_final_candidate_count', 0)}`",
            f"- Staged final candidate count: `{comparison.get('staged_final_candidate_count', 0)}`",
            f"- Staged burden reduction ratio: `{comparison.get('staged_burden_reduction_ratio', 0)}`",
        ])
        for title in comparison.get("staged_top_visible_titles", [])[:5]:
            lines.append(f"- staged top: {title}")
    lines.extend([
        "",
        "## External Inspiration Boundary",
        "",
    ])
    inspirations = external_boundary.get("external_inspiration", [])
    if inspirations:
        for row in inspirations:
            title = normalize_ws(str(row.get("title", "")))
            url = normalize_ws(str(row.get("url", "")))
            note = normalize_ws(str(row.get("note", "")))
            parts = [part for part in [title, url, note] if part]
            lines.append(f"- {' | '.join(parts)}")
    else:
        lines.append("- External inspiration: `(not recorded)`")
    code_use = external_boundary.get("external_code_use", {})
    lines.append(
        f"- External code used: `{'yes' if code_use.get('used') else 'no'}`"
    )
    code_sources = code_use.get("sources", []) or []
    if code_sources:
        lines.append(f"- External code sources: `{', '.join(code_sources)}`")
    code_note = normalize_ws(str(code_use.get("note", "")))
    if code_note:
        lines.append(f"- External code note: {code_note}")
    lines.extend([
        "",
        "## Intent",
        "",
        f"- Story: `{intent.story}`",
        f"- Source role: `{intent.source_role}`" if intent.source_role else "- Source role: `(not recorded)`",
        f"- Capture reason: {intent.capture_reason}" if intent.capture_reason else "- Capture reason: `(not recorded)`",
        f"- Expected use: {intent.expected_use}" if intent.expected_use else "- Expected use: `(not recorded)`",
        f"- Intent tags: `{', '.join(intent.intent_tags)}`" if intent.intent_tags else "- Intent tags: `(not recorded)`",
        f"- Project threads: `{', '.join(intent.project_threads)}`" if intent.project_threads else "- Project threads: `(not recorded)`",
        "",
        "## Active Questions",
        "",
        *([f"- {question}" for question in intent.research_questions] or ["- TODO: record the specific question this source was pulled to answer"]),
        "",
        "## Prior-Art Distinction",
        "",
        intent.prior_art_distinction or "- TODO: record the distinction if this source becomes prior art rather than general reference",
        "",
        "## Local Artifacts",
        "",
        f"- `{repo_rel(pdf_path)}`",
        f"- `{repo_rel(txt_path)}`",
        f"- `{repo_rel(pdfinfo_path)}`",
        f"- `{repo_rel(source_path)}`",
        "",
        "## Reading Notes",
        "",
        "- TODO: summarize the source in project language",
        "- TODO: extract the claims that actually constrain the search space",
        "- TODO: connect this paper to active sessions, specs, or experiment notes",
        "",
        "## Attribution Boundary",
        "",
        "- The source metadata and local snapshot are preserved here for attribution and reproducibility.",
        "- Any project-specific interpretation should be stated explicitly rather than implied by the citation alone.",
        "",
    ])
    return "\n".join(lines)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Dict[str, object], *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"refusing to overwrite existing file without --force: {path}")
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"refusing to overwrite existing file without --force: {path}")
    path.write_text(text, encoding="utf-8")


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"required tool not found in PATH: {name}")
    return path


def run_command(args: Sequence[str], *, stdout_path: Optional[Path] = None) -> None:
    if stdout_path is None:
        proc = subprocess.run(args, check=False, capture_output=True, text=True)
        if proc.returncode != 0:
            stderr = normalize_ws(proc.stderr or proc.stdout)
            raise RuntimeError(f"command failed ({' '.join(args)}): {stderr}")
        return

    with stdout_path.open("w", encoding="utf-8") as handle:
        proc = subprocess.run(args, check=False, stdout=handle, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        stderr = normalize_ws(proc.stderr)
        raise RuntimeError(f"command failed ({' '.join(args)}): {stderr}")


def download_pdf(pdf_url: str, dest: Path) -> None:
    curl = shutil.which("curl")
    if curl:
        run_command(
            [
                curl,
                "-fL",
                "--retry",
                "2",
                "--retry-delay",
                "1",
                "--user-agent",
                build_user_agent(),
                pdf_url,
                "-o",
                str(dest),
            ]
        )
        return

    req = urllib.request.Request(pdf_url, headers={"User-Agent": build_user_agent()})
    with urllib.request.urlopen(req, timeout=60.0) as resp:
        dest.write_bytes(resp.read())


def create_pdf_sidecars(pdf_path: Path, slug: str, *, force: bool) -> Tuple[Path, Path]:
    pdfinfo = require_tool("pdfinfo")
    pdftotext = require_tool("pdftotext")
    pdfinfo_path = pdf_path.with_suffix(".pdfinfo.txt")
    text_path = pdf_path.with_suffix(".txt")
    if (pdfinfo_path.exists() or text_path.exists()) and not force:
        raise FileExistsError("refusing to overwrite pdf sidecars without --force")
    run_command([pdfinfo, str(pdf_path)], stdout_path=pdfinfo_path)
    run_command([pdftotext, "-layout", "-nopgbrk", str(pdf_path), str(text_path)])
    return pdfinfo_path, text_path


def select_hit(hits: Sequence[SearchHit], pick: int) -> SearchHit:
    if not hits:
        raise RuntimeError("no hits found")
    index = max(1, pick) - 1
    if index >= len(hits):
        raise RuntimeError(f"--pick={pick} out of range for {len(hits)} hit(s)")
    return hits[index]


def print_hits(hits: Sequence[SearchHit]) -> None:
    for idx, hit in enumerate(hits, start=1):
        year = hit.year if hit.year is not None else "?"
        authors = ", ".join(hit.authors[:3]) if hit.authors else "Unknown author"
        venue = hit.publication or hit.venue or ""
        pdf = "yes" if hit.pdf_url else "no"
        score = hit_total_score(hit)
        print(f"[{idx}] {year} | pdf={pdf} | {', '.join(hit.sources) or 'direct'}")
        print(f"    {hit.title}")
        print(f"    {authors}")
        print(f"    score={score}")
        if venue:
            print(f"    {venue}")
        if hit.doi:
            print(f"    DOI: {hit.doi}")
        if hit.url:
            print(f"    URL: {hit.url}")


def print_pipeline_summary(report: Dict[str, object]) -> None:
    print(f"pipeline mode: {report.get('pipeline_mode', PIPELINE_FLAT)}")
    print(f"operative pipeline: {report.get('operative_pipeline', PIPELINE_FLAT)}")
    for stage in report.get("stage_trace", []):
        print(
            f"  {stage.get('stage', '')}: "
            f"{stage.get('input_count', 0)} -> {stage.get('output_count', 0)}"
        )
    comparison = report.get("comparison") or {}
    if comparison:
        print("comparison:")
        print(
            f"  flat candidates={comparison.get('flat_final_candidate_count', 0)} | "
            f"staged candidates={comparison.get('staged_final_candidate_count', 0)} | "
            f"ratio={comparison.get('staged_burden_reduction_ratio', 0)}"
        )


def hit_to_json_ready(hit: SearchHit) -> Dict[str, object]:
    return asdict(hit)


def pipeline_report_json_ready(report: Optional[Dict[str, object]]) -> Dict[str, object]:
    if not report:
        return {}
    selected = report.get("selected")
    flat = report.get("flat") or {}
    staged = report.get("staged") or {}
    return {
        "pipeline_mode": report.get("pipeline_mode", PIPELINE_FLAT),
        "operative_pipeline": report.get("operative_pipeline", PIPELINE_FLAT),
        "selected": hit_to_json_ready(selected) if isinstance(selected, SearchHit) else selected,
        "source_stats": report.get("source_stats", {}),
        "stage_trace": report.get("stage_trace", []),
        "comparison": report.get("comparison", {}),
        "flat": {
            "candidate_count": flat.get("candidate_count", 0),
            "display_candidates": [
                hit_to_json_ready(hit) if isinstance(hit, SearchHit) else hit
                for hit in flat.get("display_candidates", [])
            ],
            "stage_trace": flat.get("stage_trace", []),
        },
        "staged": {
            "candidate_count": staged.get("candidate_count", 0),
            "display_candidates": [
                hit_to_json_ready(hit) if isinstance(hit, SearchHit) else hit
                for hit in staged.get("display_candidates", [])
            ],
            "stage_trace": staged.get("stage_trace", []),
        },
    }


def build_source_snapshot(
    hit: SearchHit,
    candidates: Sequence[SearchHit],
    query: str,
    accessed_utc: str,
    args: argparse.Namespace,
    intent: IntentSpec,
    pipeline_report: Optional[Dict[str, object]] = None,
) -> Dict[str, object]:
    source_context = infer_platform_context(hit.url)
    discovery_context = infer_platform_context(getattr(args, "discovery_url", ""))
    external_boundary = build_external_boundary(args)
    return {
        "retrieved_utc": accessed_utc,
        "query": query,
        "requested_source": args.source,
        "retrieval_pipeline_mode": getattr(args, "pipeline", PIPELINE_FLAT),
        "retrieval_pipeline": pipeline_report_json_ready(pipeline_report),
        "external_inspiration": external_boundary["external_inspiration"],
        "external_code_use": external_boundary["external_code_use"],
        "intent": asdict(intent),
        "source_context": asdict(source_context),
        "discovery_url": normalize_ws(getattr(args, "discovery_url", "")),
        "discovery_context": asdict(discovery_context),
        "selected": asdict(hit),
        "candidates": [asdict(candidate) for candidate in candidates],
        "argv": sys.argv,
    }


def build_followup_commands(text_path: Path, session_json_path: Path, *, include_session: bool) -> List[List[str]]:
    commands: List[List[str]] = [
        [
            sys.executable,
            str(REPO / "scripts" / "ingest_large_file.py"),
            str(text_path),
        ]
    ]
    if include_session:
        commands.append(
            [
                sys.executable,
                str(REPO / "scripts" / "substrate_git_index.py"),
                "ingest-session",
                str(session_json_path),
            ]
        )
    return commands


def print_followup_commands(commands: Sequence[Sequence[str]]) -> None:
    print("next commands:")
    for cmd in commands:
        rendered = " ".join(repo_rel(Path(part)) if part.startswith(str(REPO)) else part for part in cmd)
        print(f"  {rendered}")


def run_followup_commands(commands: Sequence[Sequence[str]]) -> None:
    for cmd in commands:
        print(f"[ingest] {' '.join(cmd)}")
        run_command(cmd)


def build_intent_spec(args: argparse.Namespace) -> IntentSpec:
    story = normalize_story(getattr(args, "story", "REFERENCE"))
    source_role = normalize_ws(getattr(args, "source_role", "")) or default_source_role(story)
    return IntentSpec(
        story=story,
        source_role=source_role,
        capture_reason=normalize_ws(getattr(args, "capture_reason", "")),
        expected_use=normalize_ws(getattr(args, "expected_use", "")),
        research_questions=normalize_label_list(getattr(args, "research_question", []) or []),
        project_threads=normalize_label_list(getattr(args, "project_thread", []) or []),
        intent_tags=normalize_label_list(getattr(args, "intent_tag", []) or []),
        prior_art_distinction=normalize_ws(getattr(args, "prior_art_distinction", "")),
    )


def direct_pipeline_report(hit: SearchHit, query: str, pick: int) -> Dict[str, object]:
    trace = [
        stage_record(
            STAGE_INGEST,
            1,
            1,
            "Accepted the direct URL / PDF / DOI input as the initial candidate surface.",
        ),
        stage_record(
            STAGE_BREAKUP,
            1,
            1,
            "Enriched and normalized the direct candidate metadata where possible.",
        ),
        stage_record(
            STAGE_CLASSIFY,
            1,
            1,
            "No candidate narrowing was needed because the input already specified one direct target.",
        ),
        stage_record(
            STAGE_LIBERATE,
            1,
            1,
            "Prepared the direct target for the fetch handoff.",
        ),
        stage_record(
            STAGE_HANDOFF,
            1,
            1,
            "Handed the direct target into the fetch lane.",
            {"selected_pick": pick},
        ),
    ]
    return {
        "pipeline_mode": PIPELINE_FLAT,
        "operative_pipeline": PIPELINE_FLAT,
        "selected": hit,
        "display_candidates": [hit],
        "raw_hits": [hit],
        "source_stats": {"direct": {"count": 1, "status": "ok", "error": ""}},
        "stage_trace": trace,
        "flat": {"candidate_count": 1, "display_candidates": [hit], "stage_trace": trace},
        "staged": {"candidate_count": 1, "display_candidates": [hit], "stage_trace": trace},
        "comparison": {},
    }


def resolve_input(args: argparse.Namespace) -> Tuple[SearchHit, List[SearchHit], str, Dict[str, object]]:
    query = normalize_ws(args.query or "")
    if args.pdf_url or args.url:
        hit = resolve_direct(url=args.url or "", pdf_url=args.pdf_url or "", doi=args.doi or "", title=args.title or "")
        hit = enrich_direct_hit(hit)
        hit = resolve_pdf_url(hit)
        report = direct_pipeline_report(hit, query, args.pick)
        return hit, [hit], query, report
    if args.doi:
        hit = resolve_from_doi(args.doi)
        hit = resolve_pdf_url(hit)
        report = direct_pipeline_report(hit, query or hit.title, args.pick)
        return hit, [hit], query or hit.title, report
    if not query:
        raise RuntimeError("one of --query, --doi, --url, or --pdf-url is required")
    report = build_query_pipeline(
        query=query,
        source=args.source,
        limit=args.limit,
        pick=args.pick,
        pipeline_mode=args.pipeline,
        classify_window=args.classify_window,
        min_candidate_score=args.min_candidate_score,
    )
    hit = resolve_pdf_url(report["selected"])
    candidates = report["display_candidates"]
    report["selected"] = hit
    return hit, candidates, query, report


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch a scholarly PDF and scaffold local ingestion artifacts.")
    parser.add_argument("--query", help="Paper search query.")
    parser.add_argument("--source", choices=["auto", "semantic_scholar", "openalex", "crossref", "arxiv"], default="auto")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help=f"Candidates per source (default {DEFAULT_LIMIT}).")
    parser.add_argument("--pick", type=int, default=1, help="1-based candidate index to select after search (default 1).")
    parser.add_argument(
        "--pipeline",
        choices=[PIPELINE_FLAT, PIPELINE_STAGED, PIPELINE_COMPARE],
        default=PIPELINE_FLAT,
        help="Choose the retrieval/candidate-selection posture.",
    )
    parser.add_argument(
        "--classify-window",
        type=int,
        default=DEFAULT_CLASSIFY_WINDOW,
        help="Maximum candidates retained by the classification sieve in staged mode.",
    )
    parser.add_argument(
        "--min-candidate-score",
        type=float,
        default=DEFAULT_MIN_CANDIDATE_SCORE,
        help="Minimum candidate score retained by the classification sieve in staged mode.",
    )
    parser.add_argument("--doi", help="Direct DOI to resolve.")
    parser.add_argument("--url", help="Direct landing URL or direct PDF URL.")
    parser.add_argument("--pdf-url", help="Direct PDF URL.")
    parser.add_argument("--title", help="Manual title when using direct URLs.")
    parser.add_argument("--slug", help="Override generated slug.")
    parser.add_argument("--story", default="REFERENCE", help="Intent / narrative story for concept_anchor.story, for example REFERENCE, PRIOR_ART, BRIDGE, DISCOVERY, or AUDIT.")
    parser.add_argument("--source-role", help="Human-readable role this source plays, for example theory anchor, contrast case, or search-space reduction.")
    parser.add_argument("--capture-reason", help="Short note explaining why this source was captured now.")
    parser.add_argument("--expected-use", help="Short note explaining how you expect to use this source later.")
    parser.add_argument("--discovery-url", help="Optional URL where the source was discovered, for example a Reddit thread, Mastodon post, or X/Twitter post.")
    parser.add_argument("--research-question", action="append", default=[], help="Repeatable active research question this source should help answer.")
    parser.add_argument("--project-thread", action="append", default=[], help="Repeatable project thread tag such as torsion, quantum-eraser, or mxene.")
    parser.add_argument("--intent-tag", action="append", default=[], help="Repeatable extra intent tag to preserve why this source matters.")
    parser.add_argument("--prior-art-distinction", help="If this is prior art, record the project distinction you do not want to forget later.")
    parser.add_argument(
        "--external-inspiration",
        action="append",
        default=[],
        help="Repeatable conceptual grounding source recorded as 'title|url|note'.",
    )
    parser.add_argument(
        "--external-code-used",
        action="store_true",
        help="Record that external code or code snippets were used for this artifact.",
    )
    parser.add_argument(
        "--external-code-source",
        action="append",
        default=[],
        help="Repeatable source reference for any external code that was used.",
    )
    parser.add_argument(
        "--external-code-note",
        help="Short note about external code use or non-use boundary.",
    )
    parser.add_argument("--archive-root", default=str(DEFAULT_ARCHIVE_ROOT), help="Root directory for durable PDF artifacts.")
    parser.add_argument("--sessions-root", default=str(DEFAULT_SESSIONS_ROOT), help="Root directory for session scaffolds.")
    parser.add_argument("--list-only", action="store_true", help="List candidates and exit without downloading.")
    parser.add_argument("--no-session", action="store_true", help="Skip writing session scaffold files.")
    parser.add_argument("--ingest-text", action="store_true", help="After fetch/extract, run ingest_large_file.py on the extracted text.")
    parser.add_argument("--ingest-session", action="store_true", help="After scaffold creation, run substrate_git_index.py ingest-session on the session JSON.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing artifacts.")
    parser.add_argument("--dry-run", action="store_true", help="Resolve metadata and print planned outputs without writing.")
    args = parser.parse_args()
    intent = build_intent_spec(args)
    external_boundary = build_external_boundary(args)

    if args.ingest_session and args.no_session:
        parser.error("--ingest-session requires session scaffolds; remove --no-session")

    try:
        hit, candidates, query, pipeline_report = resolve_input(args)
    except Exception as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)

    print_hits(candidates[: max(args.pick, min(len(candidates), args.limit))])
    print_pipeline_summary(pipeline_report)
    if args.list_only:
        return

    if not hit.pdf_url:
        print("[error] selected record has no resolvable PDF URL", file=sys.stderr)
        sys.exit(2)

    slug = slugify(args.slug or default_slug(hit), max_len=96)
    accessed_utc = now_utc_iso()
    archive_root = Path(args.archive_root).expanduser().resolve()
    sessions_root = Path(args.sessions_root).expanduser().resolve()
    artifact_dir = archive_root / slug
    pdf_path = artifact_dir / f"{slug}.pdf"
    source_path = artifact_dir / f"{slug}.source.json"
    session_json_path = sessions_root / f"{slug}.json"
    session_md_path = sessions_root / f"{slug}.md"

    print("")
    print(f"selected slug: {slug}")
    print(f"pdf url: {hit.pdf_url}")
    print(f"artifact dir: {artifact_dir}")
    if not args.no_session:
        print(f"session scaffold: {session_json_path} + {session_md_path}")
    print(f"story / role: {intent.story} / {intent.source_role}")
    if external_boundary.get("external_inspiration"):
        print(f"external inspiration entries: {len(external_boundary['external_inspiration'])}")
    print(f"external code used: {'yes' if external_boundary['external_code_use'].get('used') else 'no'}")
    if args.discovery_url:
        discovery_context = infer_platform_context(args.discovery_url)
        label = discovery_context.platform or "web"
        print(f"discovered via: {label} / {args.discovery_url}")

    followup_commands = build_followup_commands(
        text_path=pdf_path.with_suffix(".txt"),
        session_json_path=session_json_path,
        include_session=not args.no_session,
    )

    if args.dry_run:
        print("")
        print_followup_commands(followup_commands)
        return

    ensure_dir(artifact_dir)
    ensure_dir(sessions_root)

    if pdf_path.exists() and not args.force:
        raise SystemExit(f"[error] refusing to overwrite existing file without --force: {pdf_path}")

    print("[fetch] downloading pdf …")
    download_pdf(hit.pdf_url, pdf_path)

    print("[extract] running pdfinfo + pdftotext …")
    pdfinfo_path, text_path = create_pdf_sidecars(pdf_path, slug, force=args.force)

    print("[write] recording source snapshot …")
    write_json(
        source_path,
        build_source_snapshot(
            hit,
            candidates[: args.limit],
            query,
            accessed_utc,
            args,
            intent,
            pipeline_report=pipeline_report,
        ),
        force=args.force,
    )

    if not args.no_session:
        print("[write] creating session scaffold …")
        session_payload = build_session_json(
            hit,
            slug,
            session_md_path,
            artifact_dir,
            accessed_utc,
            query,
            intent,
            discovery_url=args.discovery_url or "",
            pipeline_report=pipeline_report,
            external_boundary=external_boundary,
        )
        write_json(session_json_path, session_payload, force=args.force)
        write_text(
            session_md_path,
            build_session_md(
                hit,
                slug,
                artifact_dir,
                accessed_utc,
                query,
                intent,
                discovery_url=args.discovery_url or "",
                pipeline_report=pipeline_report,
                external_boundary=external_boundary,
            ),
            force=args.force,
        )

    print("")
    print("[ok] created:")
    print(f"  {repo_rel(pdf_path)}")
    print(f"  {repo_rel(pdfinfo_path)}")
    print(f"  {repo_rel(text_path)}")
    print(f"  {repo_rel(source_path)}")
    if not args.no_session:
        print(f"  {repo_rel(session_json_path)}")
        print(f"  {repo_rel(session_md_path)}")
    print("")
    print_followup_commands(followup_commands)

    commands_to_run: List[List[str]] = []
    if args.ingest_text:
        commands_to_run.append(followup_commands[0])
    if args.ingest_session and not args.no_session:
        commands_to_run.append(followup_commands[1])

    if commands_to_run:
        print("")
        run_followup_commands(commands_to_run)


if __name__ == "__main__":
    main()
