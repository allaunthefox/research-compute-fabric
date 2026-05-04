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
"""Fetch a non-PDF web source, extract readable text, and scaffold a session capsule.

This helper is the generic sibling to `fetch_web_pdf.py`. It is meant for
web-native sources such as:

- articles and blog posts
- Reddit threads and comments
- Mastodon posts
- X/Twitter posts
- other HTML/text pages worth preserving as durable research artifacts
"""

import argparse
import json
import re
import shutil
# import subprocess (REMOVED BY WARDEN)
import sys
import tempfile
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from literature_probe import build_user_agent, normalize_ws, slugify  # noqa: E402
from fetch_web_pdf import (  # noqa: E402
    IntentSpec,
    PIPELINE_FLAT,
    STAGE_INGEST,
    STAGE_BREAKUP,
    STAGE_CLASSIFY,
    STAGE_LIBERATE,
    STAGE_HANDOFF,
    build_external_boundary,
    build_followup_commands,
    build_intent_spec,
    ensure_dir,
    infer_platform_context,
    pipeline_report_json_ready,
    print_followup_commands,
    print_pipeline_summary,
    repo_rel,
    run_followup_commands,
    sentence_text,
    stage_record,
    tagify_label,
    unique_preserve,
    write_json,
    write_text,
)


DEFAULT_ARCHIVE_ROOT = REPO / "archive" / "WEB_SOURCE"
DEFAULT_SESSIONS_ROOT = REPO / "sessions"

_KNOWN_SOURCE_SUFFIXES = {
    ".html",
    ".htm",
    ".xml",
    ".rss",
    ".atom",
    ".json",
    ".jsonl",
    ".txt",
    ".text",
    ".md",
    ".markdown",
    ".rst",
    ".tex",
    ".bib",
    ".bibtex",
    ".dot",
    ".gv",
    ".graphml",
    ".csv",
    ".tsv",
    ".yaml",
    ".yml",
    ".toml",
}


@dataclass
class WebFetchResult:
    original_url: str
    final_url: str
    content_type: str
    charset: str
    text: str
    headers: Dict[str, str]
    snapshot_suffix: str
    snapshot_format: str


@dataclass
class ExtractedMetadata:
    title: str = ""
    author: str = ""
    publication: str = ""
    date: str = ""
    canonical_url: str = ""
    description: str = ""


class MetadataHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_title = False
        self.title_parts: List[str] = []
        self.meta: Dict[str, str] = {}
        self.link_rel: Dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        attr = {k.lower(): (v or "") for k, v in attrs}
        if tag.lower() == "title":
            self.in_title = True
        if tag.lower() == "meta":
            key = normalize_ws(attr.get("property") or attr.get("name") or attr.get("http-equiv") or "").lower()
            value = normalize_ws(attr.get("content", ""))
            if key and value and key not in self.meta:
                self.meta[key] = value
        if tag.lower() == "link":
            rel = normalize_ws(attr.get("rel", "")).lower()
            href = normalize_ws(attr.get("href", ""))
            if rel and href and rel not in self.link_rel:
                self.link_rel[rel] = href

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            text = normalize_ws(data)
            if text:
                self.title_parts.append(text)


class ReadableTextHTMLParser(HTMLParser):
    _BLOCK_TAGS = {
        "article",
        "blockquote",
        "br",
        "div",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "li",
        "main",
        "ol",
        "p",
        "pre",
        "section",
        "tr",
        "ul",
    }
    _SKIP_TAGS = {"script", "style", "noscript"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: List[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        lower = tag.lower()
        if lower in self._SKIP_TAGS:
            self.skip_depth += 1
        if lower in self._BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        lower = tag.lower()
        if lower in self._SKIP_TAGS and self.skip_depth:
            self.skip_depth -= 1
        if lower in self._BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        text = normalize_ws(data)
        if text:
            self.parts.append(text)
            self.parts.append(" ")

    def to_text(self) -> str:
        raw = "".join(self.parts)
        lines = [normalize_ws(line) for line in raw.splitlines()]
        lines = [line for line in lines if line]
        return "\n\n".join(lines)


def _filename_extension_from_disposition(header: str) -> str:
    header = normalize_ws(header)
    if not header:
        return ""
    for pattern in (r'filename\*?="?([^";]+)"?', r"filename\*?=([^;]+)"):
        match = re.search(pattern, header, flags=re.IGNORECASE)
        if match:
            candidate = urllib.parse.unquote(normalize_ws(match.group(1)).strip("\"'"))
            suffix = Path(candidate).suffix.lower()
            if suffix in _KNOWN_SOURCE_SUFFIXES:
                return suffix
    return ""


def infer_snapshot_suffix(url: str, content_type: str, headers: Dict[str, str]) -> Tuple[str, str]:
    content_type = normalize_ws(content_type).lower()
    disposition_suffix = _filename_extension_from_disposition(headers.get("Content-Disposition", ""))
    if disposition_suffix:
        suffix = disposition_suffix
    else:
        path_suffix = Path(urllib.parse.urlparse(url).path).suffix.lower()
        suffix = path_suffix if path_suffix in _KNOWN_SOURCE_SUFFIXES else ""

    if not suffix:
        if content_type in {"text/html", "application/xhtml+xml"} or "html" in content_type:
            suffix = ".html"
        elif content_type in {"application/xml", "text/xml"} or content_type.endswith("+xml") or "xml" in content_type:
            suffix = ".xml"
        elif content_type in {"application/json", "text/json"} or content_type.endswith("+json") or "json" in content_type:
            suffix = ".json"
        elif "bibtex" in content_type or "bibliography" in content_type:
            suffix = ".bib"
        elif "graphviz" in content_type or content_type in {"text/vnd.graphviz", "application/vnd.graphviz"}:
            suffix = ".dot"
        elif content_type == "text/csv":
            suffix = ".csv"
        elif content_type in {"text/tab-separated-values", "text/tsv"}:
            suffix = ".tsv"
        elif "markdown" in content_type:
            suffix = ".md"
        elif "tex" in content_type:
            suffix = ".tex"
        elif "yaml" in content_type or content_type in {"application/x-yaml", "text/x-yaml"}:
            suffix = ".yaml"
        elif "toml" in content_type:
            suffix = ".toml"
        else:
            suffix = ".txt"

    format_map = {
        ".html": "html",
        ".htm": "html",
        ".xml": "xml",
        ".rss": "xml",
        ".atom": "xml",
        ".json": "json",
        ".jsonl": "jsonl",
        ".txt": "text",
        ".text": "text",
        ".md": "markdown",
        ".markdown": "markdown",
        ".rst": "text",
        ".tex": "tex",
        ".bib": "bibtex",
        ".bibtex": "bibtex",
        ".dot": "dot",
        ".gv": "dot",
        ".graphml": "xml",
        ".csv": "csv",
        ".tsv": "tsv",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
    }
    return suffix, format_map.get(suffix, "text")


def xml_to_readable_text(text: str) -> str:
    try:
        root = ET.fromstring(text)
    except Exception:
        stripped = re.sub(r"<[^>]+>", " ", text)
        return "\n".join(line for line in (normalize_ws(line) for line in stripped.splitlines()) if line)
    pieces = [normalize_ws(piece) for piece in root.itertext()]
    rendered = "\n".join(piece for piece in pieces if piece)
    return rendered or text


def extract_xml_metadata(text: str, base_url: str) -> ExtractedMetadata:
    try:
        root = ET.fromstring(text)
    except Exception:
        return ExtractedMetadata(canonical_url=normalize_ws(base_url))

    title = ""
    author = ""
    publication = ""
    date = ""
    canonical_url = normalize_ws(base_url)

    for elem in root.iter():
        local = elem.tag.rsplit("}", 1)[-1].lower() if isinstance(elem.tag, str) else ""
        elem_text = normalize_ws("".join(elem.itertext()))
        if not title and local in {"title"} and elem_text:
            title = elem_text
        elif not author and local in {"author", "creator", "name"} and elem_text:
            author = elem_text
        elif not publication and local in {"generator", "subtitle"} and elem_text:
            publication = elem_text
        elif not date and local in {"updated", "published", "pubdate", "issued", "date"} and elem_text:
            date = elem_text
        elif local == "link":
            href = normalize_ws(elem.attrib.get("href", "") or elem.attrib.get("url", ""))
            rel = normalize_ws(elem.attrib.get("rel", "")).lower()
            if href and (not canonical_url or rel in {"canonical", "alternate", ""}):
                canonical_url = href

    return ExtractedMetadata(
        title=title,
        author=author,
        publication=publication,
        date=date,
        canonical_url=canonical_url,
    )


def extract_json_metadata(text: str, base_url: str) -> ExtractedMetadata:
    try:
        data = json.loads(text)
    except Exception:
        return ExtractedMetadata(canonical_url=normalize_ws(base_url))
    if not isinstance(data, dict):
        return ExtractedMetadata(canonical_url=normalize_ws(base_url))
    title = normalize_ws(str(data.get("title", "") or data.get("name", "")))
    author = normalize_ws(str(data.get("author", "") or data.get("creator", "")))
    publication = normalize_ws(str(data.get("publisher", "") or data.get("site_name", "")))
    date = normalize_ws(str(data.get("date", "") or data.get("published", "") or data.get("updated", "")))
    canonical_url = normalize_ws(str(data.get("url", "") or data.get("canonical_url", "") or base_url))
    description = normalize_ws(str(data.get("description", "") or data.get("summary", "")))
    return ExtractedMetadata(
        title=title,
        author=author,
        publication=publication,
        date=date,
        canonical_url=canonical_url,
        description=description,
    )


def extract_bibtex_metadata(text: str, base_url: str) -> ExtractedMetadata:
    fields = {}
    for key in ("title", "author", "year", "journal", "booktitle", "publisher", "url"):
        match = re.search(rf"{key}\s*=\s*[{{\"](.*?)[}}\"]\s*,?", text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            fields[key] = normalize_ws(match.group(1))
    publication = fields.get("journal") or fields.get("booktitle") or fields.get("publisher", "")
    return ExtractedMetadata(
        title=fields.get("title", ""),
        author=fields.get("author", ""),
        publication=publication,
        date=fields.get("year", ""),
        canonical_url=fields.get("url", "") or normalize_ws(base_url),
    )


def extract_dot_metadata(text: str, base_url: str) -> ExtractedMetadata:
    match = re.search(r"\b(?:di)?graph\s+([A-Za-z0-9_]+)\s*\{", text)
    title = normalize_ws(match.group(1).replace("_", " ")) if match else ""
    return ExtractedMetadata(
        title=title,
        canonical_url=normalize_ws(base_url),
    )


def render_structured_text(text: str, snapshot_format: str) -> str:
    if snapshot_format == "html":
        return html_to_readable_text(text)
    if snapshot_format == "xml":
        return xml_to_readable_text(text)
    if snapshot_format == "json":
        try:
            return json.dumps(json.loads(text), indent=2, ensure_ascii=False)
        except Exception:
            return text
    return text


def fetch_web_text(url: str) -> WebFetchResult:
    normalized_url = normalize_ws(url)
    request = urllib.request.Request(
        normalized_url,
        headers={
            "User-Agent": build_user_agent(),
            "Accept": "text/html,application/xhtml+xml,text/plain,application/json;q=0.9,*/*;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60.0) as response:
            body = response.read()
            final_url = normalize_ws(response.geturl())
            info = response.info()
            content_type = normalize_ws(info.get_content_type() or info.get("Content-Type") or "text/html").lower()
            charset = normalize_ws(info.get_content_charset() or "utf-8")
            text = body.decode(charset or "utf-8", errors="replace")
            headers = {str(k): normalize_ws(v) for k, v in info.items()}
    except Exception:
        curl = shutil.which("curl")
        if not curl:
            raise
        with tempfile.TemporaryDirectory() as tmpdir:
            header_path = Path(tmpdir) / "headers.txt"
            body_path = Path(tmpdir) / "body.txt"
            proc = subprocess.run(
                [
                    curl,
                    "-fsSL",
                    "-A",
                    build_user_agent(),
                    "-D",
                    str(header_path),
                    normalized_url,
                    "-o",
                    str(body_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            if proc.returncode != 0:
                raise RuntimeError(normalize_ws(proc.stderr or proc.stdout or f"curl failed for {normalized_url}"))
            raw_headers = header_path.read_text(encoding="utf-8", errors="replace")
            header_blocks = [block for block in raw_headers.split("\r\n\r\n") if block.strip()] or [raw_headers]
            last_block = header_blocks[-1]
            headers = {}
            for line in last_block.splitlines():
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                headers[normalize_ws(key)] = normalize_ws(value)
            content_type_header = headers.get("Content-Type", "text/html")
            content_type = normalize_ws(content_type_header.split(";", 1)[0]).lower()
            charset = "utf-8"
            if "charset=" in content_type_header.lower():
                charset = normalize_ws(content_type_header.split("charset=", 1)[1].split(";", 1)[0]) or "utf-8"
            text = body_path.read_text(encoding=charset or "utf-8", errors="replace")
            final_url = normalized_url

    suffix, snapshot_format = infer_snapshot_suffix(final_url or normalized_url, content_type, headers)

    return WebFetchResult(
        original_url=normalize_ws(url),
        final_url=final_url,
        content_type=content_type,
        charset=charset or "utf-8",
        text=text,
        headers=headers,
        snapshot_suffix=suffix,
        snapshot_format=snapshot_format,
    )


def extract_html_metadata(text: str, base_url: str) -> ExtractedMetadata:
    parser = MetadataHTMLParser()
    parser.feed(text)
    meta = parser.meta
    title = (
        meta.get("og:title")
        or meta.get("twitter:title")
        or normalize_ws(" ".join(parser.title_parts))
    )
    author = (
        meta.get("author")
        or meta.get("article:author")
        or meta.get("parsely-author")
        or meta.get("dc.creator")
    )
    publication = (
        meta.get("og:site_name")
        or meta.get("application-name")
        or meta.get("twitter:site")
    )
    date = (
        meta.get("article:published_time")
        or meta.get("og:published_time")
        or meta.get("pubdate")
        or meta.get("date")
    )
    canonical_url = parser.link_rel.get("canonical") or meta.get("og:url") or normalize_ws(base_url)
    description = meta.get("description") or meta.get("og:description") or meta.get("twitter:description") or ""
    return ExtractedMetadata(
        title=normalize_ws(title),
        author=normalize_ws(author),
        publication=normalize_ws(publication),
        date=normalize_ws(date),
        canonical_url=normalize_ws(canonical_url),
        description=normalize_ws(description),
    )


def html_to_readable_text(text: str) -> str:
    parser = ReadableTextHTMLParser()
    parser.feed(text)
    return parser.to_text()


def resolve_source_metadata(
    fetch: WebFetchResult,
    *,
    title: str = "",
    author: str = "",
    publication: str = "",
    date: str = "",
    source_type: str = "",
    canonical_url: str = "",
) -> Tuple[ExtractedMetadata, str]:
    source_context = infer_platform_context(fetch.final_url or fetch.original_url)
    if fetch.snapshot_format == "html":
        extracted = extract_html_metadata(fetch.text, fetch.final_url or fetch.original_url)
    elif fetch.snapshot_format == "xml":
        extracted = extract_xml_metadata(fetch.text, fetch.final_url or fetch.original_url)
    elif fetch.snapshot_format in {"json", "jsonl"}:
        extracted = extract_json_metadata(fetch.text, fetch.final_url or fetch.original_url)
    elif fetch.snapshot_format == "bibtex":
        extracted = extract_bibtex_metadata(fetch.text, fetch.final_url or fetch.original_url)
    elif fetch.snapshot_format == "dot":
        extracted = extract_dot_metadata(fetch.text, fetch.final_url or fetch.original_url)
    else:
        extracted = ExtractedMetadata()
    readable = render_structured_text(fetch.text, fetch.snapshot_format)

    resolved_title = normalize_ws(title) or extracted.title or source_context.handle or slugify(fetch.final_url or fetch.original_url, max_len=64).replace("-", " ")
    resolved_author = normalize_ws(author) or extracted.author or source_context.handle
    resolved_publication = normalize_ws(publication) or extracted.publication
    if not resolved_publication and source_context.platform:
        resolved_publication = source_context.platform.title()
    if not resolved_publication and fetch.final_url:
        resolved_publication = urllib.parse.urlparse(fetch.final_url).netloc
    resolved_date = normalize_ws(date) or extracted.date
    resolved_canonical = normalize_ws(canonical_url) or extracted.canonical_url or fetch.final_url or fetch.original_url

    extracted.title = resolved_title
    extracted.author = resolved_author
    extracted.publication = resolved_publication
    extracted.date = resolved_date
    extracted.canonical_url = resolved_canonical
    return extracted, readable


def infer_source_type(value: str, context_platform: str, context_kind: str, snapshot_format: str = "") -> str:
    explicit = normalize_ws(value)
    if explicit:
        return explicit
    if context_platform and context_kind:
        return f"{context_platform}_{context_kind}"
    if context_platform:
        return context_platform
    if snapshot_format == "bibtex":
        return "bibliography_record"
    if snapshot_format == "dot":
        return "graphviz_source"
    if snapshot_format == "xml":
        return "xml_document"
    if snapshot_format == "json":
        return "json_document"
    if snapshot_format == "jsonl":
        return "jsonl_document"
    if snapshot_format == "markdown":
        return "markdown_document"
    if snapshot_format == "csv":
        return "csv_document"
    if snapshot_format == "tsv":
        return "tsv_document"
    if snapshot_format == "tex":
        return "tex_document"
    if snapshot_format == "yaml":
        return "yaml_document"
    if snapshot_format == "toml":
        return "toml_document"
    if snapshot_format == "text":
        return "text_document"
    return "web_page"


def default_slug(title: str, url: str) -> str:
    title = normalize_ws(title)
    if title:
        return slugify(title, max_len=96)
    return slugify(url, max_len=96)


def web_source_pipeline_report(
    fetch: "WebFetchResult",
    metadata: "ExtractedMetadata",
    readable_text: str,
) -> Dict[str, object]:
    """Build a 5-stage pipeline trace for a single direct web-source fetch.

    Mirrors fetch_web_pdf.direct_pipeline_report() but uses web-fetch stage notes.
    Always returns pipeline_mode=PIPELINE_FLAT (no multi-candidate narrowing).
    """
    n_chars = len(readable_text)
    trace = [
        stage_record(
            STAGE_INGEST,
            1,
            1,
            f"URL accepted and HTTP fetch dispatched; "
            f"HTTP status {fetch.status_code if hasattr(fetch, 'status_code') else 'OK'}.",
        ),
        stage_record(
            STAGE_BREAKUP,
            1,
            1,
            f"Content-type resolved to '{fetch.content_type or '(unknown)'}'; "
            f"charset decoded; raw text extracted ({fetch.snapshot_format or 'text'} format).",
        ),
        stage_record(
            STAGE_CLASSIFY,
            1,
            1,
            f"Metadata resolved: title='{metadata.title or '(not resolved)'}', "
            f"author='{metadata.author or '(not resolved)'}', "
            f"canonical_url='{metadata.canonical_url or '(not resolved)'}'.",
        ),
        stage_record(
            STAGE_LIBERATE,
            1,
            1,
            f"Readable text rendered from snapshot ({n_chars:,} chars).",
        ),
        stage_record(
            STAGE_HANDOFF,
            1,
            1,
            "Artifact paths resolved; handed to write lane.",
        ),
    ]
    pipeline_block = {
        "candidate_count": 1,
        "stage_trace": trace,
    }
    return {
        "pipeline_mode":      PIPELINE_FLAT,
        "operative_pipeline": PIPELINE_FLAT,
        "stage_trace":        trace,
        "flat":               pipeline_block,
        "staged":             pipeline_block,
        "comparison":         {},
    }


def build_source_snapshot(
    fetch: WebFetchResult,
    metadata: ExtractedMetadata,
    readable_text: str,
    *,
    intent: IntentSpec,
    discovery_url: str,
    source_type: str,
    accessed_utc: str,
    args: argparse.Namespace,
    pipeline_report: Optional[Dict[str, object]] = None,
) -> Dict[str, object]:
    source_context = infer_platform_context(metadata.canonical_url or fetch.final_url or fetch.original_url)
    discovery_context = infer_platform_context(discovery_url)
    external_boundary = build_external_boundary(args)
    return {
        "retrieved_utc": accessed_utc,
        "intent": asdict(intent),
        "external_inspiration": external_boundary["external_inspiration"],
        "external_code_use": external_boundary["external_code_use"],
        "original_url": fetch.original_url,
        "final_url": fetch.final_url,
        "content_type": fetch.content_type,
        "charset": fetch.charset,
        "headers": fetch.headers,
        "snapshot_suffix": fetch.snapshot_suffix,
        "snapshot_format": fetch.snapshot_format,
        "metadata": asdict(metadata),
        "source_type": source_type,
        "source_context": asdict(source_context),
        "discovery_url": discovery_url,
        "discovery_context": asdict(discovery_context),
        "readable_text_chars": len(readable_text),
        "argv": sys.argv,
        "requested_title": normalize_ws(args.title or ""),
        "requested_author": normalize_ws(args.author or ""),
        "requested_publication": normalize_ws(args.publication or ""),
        "requested_date": normalize_ws(args.date or ""),
        "retrieval_pipeline_mode": (pipeline_report or {}).get("pipeline_mode", PIPELINE_FLAT),
        "retrieval_pipeline": pipeline_report_json_ready(pipeline_report),
    }


def build_session_json(
    slug: str,
    session_md: Path,
    artifact_dir: Path,
    snapshot_path: Path,
    text_path: Path,
    source_snapshot_path: Path,
    *,
    metadata: ExtractedMetadata,
    source_url: str,
    original_url: str,
    source_content_type: str,
    source_snapshot_suffix: str,
    source_snapshot_format: str,
    source_type: str,
    intent: IntentSpec,
    accessed_utc: str,
    discovery_url: str,
    external_boundary: Optional[Dict[str, object]] = None,
    pipeline_report: Optional[Dict[str, object]] = None,
) -> Dict[str, object]:
    source_context = infer_platform_context(source_url)
    discovery_context = infer_platform_context(discovery_url)
    external_boundary = external_boundary or {
        "external_inspiration": [],
        "external_code_use": {
            "used": False,
            "sources": [],
            "note": "No external code or code snippets were recorded for this artifact.",
        },
    }
    title_claim = normalize_ws(metadata.title or slug.replace("-", " "))
    description_bits = [
        normalize_ws(
            f"Scaffold capsule for {title_claim}. Preserves the local web snapshot, extracted text, and attribution metadata for later semantic distillation."
        )
    ]
    if intent.story or intent.source_role:
        description_bits.append(
            normalize_ws(
                f"Captured under story {intent.story} as {intent.source_role or intent.story.lower()}."
            )
        )
    if intent.capture_reason:
        description_bits.append(f"Reason: {sentence_text(intent.capture_reason)}.")
    if intent.expected_use:
        description_bits.append(f"Expected use: {sentence_text(intent.expected_use)}.")
    description = normalize_ws(" ".join(description_bits))

    idea_weights = {
        "preserve web-native sources as local snapshot plus extracted text plus session capsule": 0.62,
        f"{title_claim} is preserved locally for later semantic digestion rather than live-url dependence": 0.58,
    }
    if intent.capture_reason:
        idea_weights[f"Capture reason: {sentence_text(intent.capture_reason)}"] = 0.56

    extension_points = [
        "Replace scaffold idea_weights with source-specific semantic claims after reading the source",
        "Link this source to any active research note or theory anchor that depends on it",
        "Promote stable interpretations into a dedicated literature, prior-art, or signal-source session cluster",
    ]
    for question in intent.research_questions:
        extension_points.append(f"Check whether this source materially constrains: {question}")

    tags = unique_preserve(
        [
            "web-source",
            f"format-{tagify_label(source_snapshot_format)}" if source_snapshot_format else "",
            tagify_label(intent.story),
            f"role-{tagify_label(intent.source_role)}" if intent.source_role else "",
            *(tagify_label(tag) for tag in intent.intent_tags),
            *(tagify_label(thread) for thread in intent.project_threads),
            f"platform-{tagify_label(source_context.platform)}" if source_context.platform else "",
            f"discovery-{tagify_label(discovery_context.platform)}" if discovery_context.platform else "",
            tagify_label(source_type),
        ]
    )

    attachments = unique_preserve(
        [
            repo_rel(session_md),
            repo_rel(snapshot_path),
            repo_rel(text_path),
            repo_rel(source_snapshot_path),
        ]
    )

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
        "module": "WEB_SOURCE_CAPTURE",
        "archetype": "WEB_SOURCE_SCAFFOLD",
        "description": description,
        "tags": tags,
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
        "source_title": metadata.title,
        "source_author": metadata.author,
        "source_publication": metadata.publication,
        "source_date": metadata.date,
        "source_url": source_url,
        "source_original_url": original_url,
        "source_canonical_url": metadata.canonical_url,
        "source_content_type": source_content_type,
        "source_snapshot_suffix": source_snapshot_suffix,
        "source_snapshot_format": source_snapshot_format,
        "source_type": source_type,
        "source_accessed_utc": accessed_utc,
        "discovery_url": discovery_url,
        "external_inspiration": external_boundary["external_inspiration"],
        "external_code_use": external_boundary["external_code_use"],
    }
    payload["retrieval_pipeline_mode"] = (pipeline_report or {}).get("pipeline_mode", PIPELINE_FLAT)
    payload["retrieval_stage_trace"] = (pipeline_report or {}).get("stage_trace", [])
    payload["retrieval_pipeline_comparison"] = (pipeline_report or {}).get("comparison", {})
    if intent.prior_art_distinction:
        payload["prior_art_distinction"] = intent.prior_art_distinction
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
    return payload


def build_session_md(
    slug: str,
    snapshot_path: Path,
    text_path: Path,
    source_snapshot_path: Path,
    *,
    metadata: ExtractedMetadata,
    source_url: str,
    source_content_type: str,
    source_snapshot_format: str,
    source_type: str,
    intent: IntentSpec,
    accessed_utc: str,
    discovery_url: str,
    external_boundary: Optional[Dict[str, object]] = None,
    pipeline_report: Optional[Dict[str, object]] = None,
) -> str:
    source_context = infer_platform_context(source_url)
    discovery_context = infer_platform_context(discovery_url)
    external_boundary = external_boundary or {
        "external_inspiration": [],
        "external_code_use": {
            "used": False,
            "sources": [],
            "note": "No external code or code snippets were recorded for this artifact.",
        },
    }
    local_artifacts = unique_preserve(
        [
            repo_rel(snapshot_path),
            repo_rel(text_path),
            repo_rel(source_snapshot_path),
        ]
    )
    lines = [
        f"# {metadata.title or slug}",
        "",
        "## Provenance",
        "",
        f"- Retrieved: `{accessed_utc}`",
        f"- Source URL: `{source_url}`",
        f"- Canonical URL: `{metadata.canonical_url}`" if metadata.canonical_url else "- Canonical URL: `(not recorded)`",
        f"- Source type: `{source_type}`",
        f"- Content type: `{source_content_type}`" if source_content_type else "- Content type: `(not recorded)`",
        f"- Snapshot format: `{source_snapshot_format}`" if source_snapshot_format else "- Snapshot format: `(not recorded)`",
        f"- Source platform: `{source_context.platform}`" if source_context.platform else "- Source platform: `(not inferred)`",
        f"- Source handle/community: `{source_context.handle or source_context.community}`" if (source_context.handle or source_context.community) else "- Source handle/community: `(not inferred)`",
        f"- Discovery URL: `{discovery_url}`" if discovery_url else "- Discovery URL: `(not recorded)`",
        f"- Discovery platform: `{discovery_context.platform}`" if discovery_context.platform else "- Discovery platform: `(not inferred)`",
        f"- Retrieval pipeline: `{(pipeline_report or {}).get('pipeline_mode', PIPELINE_FLAT)}`",
        "",
        "## Citation",
        "",
        f"{metadata.author or 'Unknown author'} ({metadata.date or 'n.d.'}). {metadata.title or slug}. {metadata.publication or ''} {metadata.canonical_url or source_url}".strip(),
        "",
        "## External Inspiration Boundary",
        "",
    ]
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
    lines.append(f"- External code used: `{'yes' if code_use.get('used') else 'no'}`")
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
        *[f"- `{artifact}`" for artifact in local_artifacts],
        "",
        "## Reading Notes",
        "",
        "- TODO: summarize the source in project language",
        "- TODO: separate what the source says from what the project infers from it",
        "- TODO: connect this source to active sessions, specs, or experiment notes",
        "",
        "## Attribution Boundary",
        "",
        "- The source metadata and local snapshot are preserved here for attribution and reproducibility.",
        "- Any project-specific interpretation should be stated explicitly rather than implied by the source alone.",
        "",
    ])
    if pipeline_report:
        stage_trace = pipeline_report.get("stage_trace") or []
        lines.append("## Retrieval Stage Trace")
        lines.append("")
        for rec in stage_trace:
            name = rec.get("stage", "?")
            note = rec.get("note", "")
            kept = rec.get("output_count", "?")
            total = rec.get("input_count", "?")
            lines.append(f"- **{name}** ({kept}/{total}): {note}")
        lines.append("")
        comparison = pipeline_report.get("comparison") or {}
        if comparison:
            lines.append("## Retrieval Comparison")
            lines.append("")
            for k, v in comparison.items():
                lines.append(f"- {k}: {v}")
            lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch a non-PDF web source and scaffold local ingestion artifacts.")
    parser.add_argument("--url", required=True, help="Direct URL for the article, thread, post, or page to snapshot.")
    parser.add_argument("--title", help="Manual source title override.")
    parser.add_argument("--author", help="Manual source author override.")
    parser.add_argument("--publication", help="Manual publication / site / institution override.")
    parser.add_argument("--date", help="Manual source date override.")
    parser.add_argument("--source-type", help="Manual source type override such as reddit_thread, mastodon_post, article, or blog_post.")
    parser.add_argument("--canonical-url", help="Manual canonical URL override.")
    parser.add_argument("--slug", help="Override generated slug.")
    parser.add_argument("--story", default="REFERENCE", help="Intent / narrative story for concept_anchor.story.")
    parser.add_argument("--source-role", help="Human-readable role this source plays.")
    parser.add_argument("--capture-reason", help="Short note explaining why this source was captured now.")
    parser.add_argument("--expected-use", help="Short note explaining how you expect to use this source later.")
    parser.add_argument("--discovery-url", help="Optional URL where the source was discovered, for example Reddit, Mastodon, or X/Twitter.")
    parser.add_argument("--research-question", action="append", default=[], help="Repeatable active research question this source should help answer.")
    parser.add_argument("--project-thread", action="append", default=[], help="Repeatable project thread tag.")
    parser.add_argument("--intent-tag", action="append", default=[], help="Repeatable extra intent tag.")
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
    parser.add_argument("--archive-root", default=str(DEFAULT_ARCHIVE_ROOT), help="Root directory for durable web-source artifacts.")
    parser.add_argument("--sessions-root", default=str(DEFAULT_SESSIONS_ROOT), help="Root directory for session scaffolds.")
    parser.add_argument("--no-session", action="store_true", help="Skip writing session scaffold files.")
    parser.add_argument("--ingest-text", action="store_true", help="After fetch/extract, run ingest_large_file.py on the extracted text.")
    parser.add_argument("--ingest-session", action="store_true", help="After scaffold creation, run substrate_git_index.py ingest-session on the session JSON.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing artifacts.")
    parser.add_argument("--dry-run", action="store_true", help="Fetch metadata and print planned outputs without writing files.")
    parser.add_argument("--pipeline", default=PIPELINE_FLAT, choices=[PIPELINE_FLAT], help="Pipeline mode (currently only 'flat' is supported for web sources).")
    args = parser.parse_args()

    if args.ingest_session and args.no_session:
        parser.error("--ingest-session requires session scaffolds; remove --no-session")

    intent = build_intent_spec(args)
    external_boundary = build_external_boundary(args)
    fetch = fetch_web_text(args.url)
    metadata, readable_text = resolve_source_metadata(
        fetch,
        title=args.title or "",
        author=args.author or "",
        publication=args.publication or "",
        date=args.date or "",
        source_type=args.source_type or "",
        canonical_url=args.canonical_url or "",
    )
    source_url = metadata.canonical_url or fetch.final_url or fetch.original_url
    source_context = infer_platform_context(source_url)
    source_type = infer_source_type(args.source_type or "", source_context.platform, source_context.kind, fetch.snapshot_format)

    pipeline_report = web_source_pipeline_report(fetch, metadata, readable_text)

    slug = slugify(args.slug or default_slug(metadata.title, source_url), max_len=96)
    accessed_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    archive_root = Path(args.archive_root).expanduser().resolve()
    sessions_root = Path(args.sessions_root).expanduser().resolve()
    artifact_dir = archive_root / slug
    snapshot_path = artifact_dir / f"{slug}{fetch.snapshot_suffix}"
    text_path = artifact_dir / f"{slug}.txt"
    source_snapshot_path = artifact_dir / f"{slug}.source.json"
    session_json_path = sessions_root / f"{slug}.json"
    session_md_path = sessions_root / f"{slug}.md"

    print(f"title: {metadata.title or '(not resolved)'}")
    print(f"url: {source_url}")
    print(f"type/platform: {source_type} / {source_context.platform or 'web'}")
    print(f"content/format: {fetch.content_type} / {fetch.snapshot_format}")
    print(f"selected slug: {slug}")
    print(f"artifact dir: {artifact_dir}")
    if external_boundary.get("external_inspiration"):
        print(f"external inspiration entries: {len(external_boundary['external_inspiration'])}")
    print(f"external code used: {'yes' if external_boundary['external_code_use'].get('used') else 'no'}")
    if args.discovery_url:
        discovery_context = infer_platform_context(args.discovery_url)
        print(f"discovered via: {discovery_context.platform or 'web'} / {args.discovery_url}")
    if not args.no_session:
        print(f"session scaffold: {session_json_path} + {session_md_path}")

    followup_commands = build_followup_commands(
        text_path=text_path,
        session_json_path=session_json_path,
        include_session=not args.no_session,
    )

    if args.dry_run:
        print("")
        print_followup_commands(followup_commands)
        return

    ensure_dir(artifact_dir)
    ensure_dir(sessions_root)

    write_text(snapshot_path, fetch.text, force=args.force)
    if text_path != snapshot_path:
        write_text(text_path, readable_text, force=args.force)
    write_json(
        source_snapshot_path,
        build_source_snapshot(
            fetch,
            metadata,
            readable_text,
            intent=intent,
            discovery_url=normalize_ws(args.discovery_url or ""),
            source_type=source_type,
            accessed_utc=accessed_utc,
            args=args,
            pipeline_report=pipeline_report,
        ),
        force=args.force,
    )

    if not args.no_session:
        payload = build_session_json(
            slug,
            session_md_path,
            artifact_dir,
            snapshot_path,
            text_path,
            source_snapshot_path,
            metadata=metadata,
            source_url=source_url,
            original_url=fetch.original_url,
            source_content_type=fetch.content_type,
            source_snapshot_suffix=fetch.snapshot_suffix,
            source_snapshot_format=fetch.snapshot_format,
            source_type=source_type,
            intent=intent,
            accessed_utc=accessed_utc,
            discovery_url=normalize_ws(args.discovery_url or ""),
            external_boundary=external_boundary,
            pipeline_report=pipeline_report,
        )
        write_json(session_json_path, payload, force=args.force)
        write_text(
            session_md_path,
            build_session_md(
                slug,
                snapshot_path,
                text_path,
                source_snapshot_path,
                metadata=metadata,
                source_url=source_url,
                source_content_type=fetch.content_type,
                source_snapshot_format=fetch.snapshot_format,
                source_type=source_type,
                intent=intent,
                accessed_utc=accessed_utc,
                discovery_url=normalize_ws(args.discovery_url or ""),
                external_boundary=external_boundary,
                pipeline_report=pipeline_report,
            ),
            force=args.force,
        )

    print("")
    print("[ok] created:")
    print(f"  {repo_rel(snapshot_path)}")
    print(f"  {repo_rel(text_path)}")
    print(f"  {repo_rel(source_snapshot_path)}")
    if not args.no_session:
        print(f"  {repo_rel(session_json_path)}")
        print(f"  {repo_rel(session_md_path)}")
    print("")
    print_pipeline_summary(pipeline_report)
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
