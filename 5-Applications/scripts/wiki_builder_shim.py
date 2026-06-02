#!/usr/bin/env python3
"""Wiki Builder Shim — Accelerates the raw→wiki→maintenance research loop.

Mirrors the Wiki Builder pattern (dair.ai academy) adapted to the Research Stack's
existing ingestion + tiddlywiki infrastructure. Does three things:

  1. SCAN   — maps raw source material to existing wiki coverage
  2. BUILD  — compiles raw sources into draft .tid files with provenance
  3. LINT   — finds thin pages, missing backlinks, and uncompiled raw notes

Source directories scanned by default:
  - /home/allaun/Documents/ingest/          (Kimi JSONs, chat dumps, papers)
  - shared-data/data/germane/research/      (ingested research articles)
  - 6-Documentation/chat-log-dumps/         (raw conversation logs)

Existing .tid files are checked for provenance markers ([[Durable Source]])
and cross-linked back to source material.

Usage:
  python wiki_builder_shim.py scan          # show coverage gaps
  python wiki_builder_shim.py build --dry   # preview what would be generated
  python wiki_builder_shim.py build         # compile new tiddlers from sources
  python wiki_builder_shim.py lint          # find thin pages, orphans, missing links
  python wiki_builder_shim.py sources       # (re)build sources.md provenance spine
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent
from typing import Any

from shim.utils.hashing import sha256_text


REPO_ROOT = Path(__file__).resolve().parents[2]
TIDDLER_DIR = REPO_ROOT / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers"
SOURCES_MD = TIDDLER_DIR.parent / "sources.md"
PROMPTS_DIR = TIDDLER_DIR.parent / "prompts"
SKIP_FILE = TIDDLER_DIR.parent / "wbs_skip.txt"

SOURCE_DIRS = [
    Path("/home/allaun/Documents/ingest"),
    REPO_ROOT / "shared-data" / "data" / "germane" / "research",
    REPO_ROOT / "6-Documentation" / "chat-log-dumps",
    REPO_ROOT / "6-Documentation" / "articles",
]

LINK_RE = re.compile(r"\[\[([^\[\]\n|#]+)(?:[#|][^\[\]\n]*)?\]\]")
SOURCE_RE = re.compile(r"`([^`]+)`", re.MULTILINE)
TITLE_RE = re.compile(r"^title:\s*(.+)$", re.MULTILINE)
TAGS_RE = re.compile(r"^tags:\s*(.+)$", re.MULTILINE)

AXIS_KEYWORDS: dict[str, list[str]] = {
    "compression": ["compression", "hutter", "gcl", "delta", "metafoam", "codec", "shifter", "decompressor"],
    "physics": ["physics", "pde", "navier", "stokes", "burgers", "yang", "mills", "rg flow", "renormalization"],
    "neural": ["neural", "semantic", "manifold", "embedding", "concept vector", "eigenvector"],
    "lean": ["lean", "proof", "theorem", "formal", "lake", "q16_16", "fixed point"],
    "market": ["market", "hutter prize", "compression prize", "benchmark", "record"],
    "safety": ["safety", "invariant", "security", "audit", "warden", "extremophile"],
    "hardware": ["fpga", "asic", "hdmi", "gpu", "webgpu", "wgsl", "verilog", "tapeout"],
    "signal": ["signal", "dsp", "morphic", "waveprobe", "famm", "spectral"],
    "bio": ["biology", "genetic", "codon", "dna", "rna", "peptide", "hachimoji", "genome"],
    "decision": ["routing", "decision", "sigma gate", "admissibility", "mass number", "sluq"],
    "archive": ["archive", "wiki", "tiddler", "documentation", "index"],
    "sovereign": ["sovereign", "attestation", "receipt", "provenance"],
}

NOW_TS = "20260507000000000"


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9._ -]+", "", s)
    s = re.sub(r"\s+", "_", s).strip("_")
    return s[:60] if s else "untitled"





def concept_vector_14(title: str, body: str, tags: list[str]) -> list[float]:
    """14D vector from keyword axis activation (mirrors tiddlywiki_ene_bridge pattern)."""
    combined = f"{title}\n{body}\n{' '.join(tags)}".lower()
    axes = [0.0] * 14
    for i, (_, keywords) in enumerate(AXIS_KEYWORDS.items()):
        score = sum(combined.count(kw.lower()) for kw in keywords)
        axes[i] = min(1.0, score / max(1, len(keywords)))
    if not any(axes):
        axes[7] = 1.0
    norm = sum(x * x for x in axes) ** 0.5
    return [round(x / norm, 6) if norm else 0.0 for x in axes]


@dataclass
class SourceEntry:
    path: Path
    basename: str
    kind: str       # "kimi_json" | "chatgpt_md" | "article" | "research_article" | "unknown"
    title: str
    url: str
    size_kb: int
    msg_count: int
    sha256: str
    matched_tiddlers: list[str]


@dataclass
class TiddlerInfo:
    path: Path
    title: str
    tags: list[str]
    links: list[str]
    sources: list[str]
    body_bytes: int
    link_count: int
    backlink_count: int


@dataclass
class LintResult:
    orphans: list[str]           # tiddlers with zero backlinks
    stubs: list[str]             # tiddlers with <200 bytes body
    no_sources: list[str]        # tiddlers without [[Durable Source]] references
    uncompiled_sources: list[str]  # source files with zero matched tiddlers
    dead_links: list[tuple[str, str]]  # (tiddler, linked_title) — link targets no page


def scan_sources(limit: int = 200) -> list[SourceEntry]:
    """Scan source directories and match against existing tiddlers."""
    existing_tiddlers = _load_existing_tiddlers()
    entries: list[SourceEntry] = []

    for src_dir in SOURCE_DIRS:
        if not src_dir.exists():
            continue
        for fpath in sorted(src_dir.rglob("*"), key=lambda p: p.stat().st_size, reverse=True)[:limit]:
            if fpath.is_dir() or fpath.name.startswith("."):
                continue
            try:
                entry = _classify_source(fpath, existing_tiddlers)
                if entry:
                    entries.append(entry)
            except Exception:
                continue

    return sorted(entries, key=lambda e: e.size_kb, reverse=True)


def _load_skip_patterns() -> set[str]:
    """Load source basenames to skip from wbs_skip.txt."""
    patterns: set[str] = set()
    if not SKIP_FILE.exists():
        return patterns
    for line in SKIP_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        patterns.add(line)
    return patterns


def _classify_source(fpath: Path, tiddlers: dict[str, TiddlerInfo]) -> SourceEntry | None:
    basename = fpath.name
    suffix = fpath.suffix.lower()

    SKIP_EXTS = {".zip", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".pyc", ".pkl",
                 ".parquet", ".csv", ".tsv", ".log", ".bin", ".o", ".so", ".dll",
                 ".ipynb", ".tgz", ".gz", ".bz2", ".xz", ".lock", ".toml", ".cfg",
                 ".ini", ".cff", ".lean", ".scad", ".asm", ".v", ".c", ".rs",
                 ".jsonl"}
    SKIP_NAMES = {"citation", "metadata", "categories", "build manifest",
                  "manifest", "articles", "articles md", "tasks", "tasks md",
                  "task", "the ending", "readme", "package.json", ".gitignore"}
    if suffix in SKIP_EXTS or basename in SKIP_NAMES or basename.startswith("."):
        return None
    lower_base = basename.lower().rstrip(suffix).strip()
    # Also check basename without extension against SKIP_NAMES
    if suffix and lower_base in SKIP_NAMES:
        return None

    skip_patterns = _load_skip_patterns()
    normalized = basename.lower().replace("_", " ").replace("-", " ").replace("%20", " ")
    if any(p.lower().replace("_", " ").replace("-", " ") in normalized for p in skip_patterns):
        return None

    size_kb = fpath.stat().st_size // 1024
    body = ""
    title = ""
    url = ""
    msg_count = 0

    if fpath.suffix == ".json" and basename.startswith("Kimi-"):
        try:
            d = json.loads(fpath.read_text(encoding="utf-8", errors="replace"))
            title = d.get("title", basename)
            url = d.get("url", "")
            msgs = d.get("messages", [])
            msg_count = len(msgs)
            for m in msgs:
                if m.get("role") == "user" and not body:
                    body = str(m.get("content", ""))[:2000]
        except (json.JSONDecodeError, KeyError):
            body = fpath.read_text(encoding="utf-8", errors="replace")[:2000]
        kind = "kimi_json"
    elif fpath.suffix == ".md" or fpath.suffix == ".txt":
        text = fpath.read_text(encoding="utf-8", errors="replace")
        body = text[:2000]
        for line in text.split("\n")[:20]:
            if line.startswith("# ") and not title:
                title = line[2:].strip()
        kind = "chatgpt_md"
    elif fpath.suffix == ".json":
        text = fpath.read_text(encoding="utf-8", errors="replace")
        body = text[:2000]
        kind = "research_article"
    elif fpath.suffix == ".pdf":
        kind = "article"
        title = fpath.stem
    else:
        kind = "unknown"

    if not title and basename:
        title = basename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ")

    sha = sha256_text(body) if body else sha256_text(basename)

    matched = []
    title_words: set[str] = set(re.findall(r"[a-z0-9]{3,}", slugify(title)))

    def _overlap(a: str, b: str) -> float:
        wa = set(re.findall(r"[a-z0-9]{3,}", slugify(a)))
        wb = set(re.findall(r"[a-z0-9]{3,}", slugify(b)))
        if not wa or not wb:
            return 0.0
        return len(wa & wb) / min(len(wa), len(wb))

    for tid_title, info in tiddlers.items():
        score = _overlap(title, tid_title)
        if score >= 0.25:
            matched.append(tid_title)
        elif score >= 0.15:
            tag_text = " ".join(info.tags)
            if _overlap(title, tag_text) >= 0.15 or _overlap(basename, tag_text) >= 0.15:
                matched.append(tid_title)

    return SourceEntry(fpath, basename, kind, title, url, size_kb, msg_count, sha, matched)


def _load_existing_tiddlers() -> dict[str, TiddlerInfo]:
    tiddlers: dict[str, TiddlerInfo] = {}
    if not TIDDLER_DIR.exists():
        return tiddlers
    for tp in TIDDLER_DIR.glob("*.tid"):
        text = tp.read_text(encoding="utf-8", errors="replace")
        tmatch = TITLE_RE.search(text)
        title = tmatch.group(1).strip() if tmatch else tp.stem
        tags = []
        tmatch2 = TAGS_RE.search(text)
        if tmatch2:
            tags = [t.strip() for t in tmatch2.group(1).split()]
        links = LINK_RE.findall(text)
        sources = SOURCE_RE.findall(text)
        body = text.split("\n\n", 1)[-1] if "\n\n" in text else text
        tiddlers[title] = TiddlerInfo(tp, title, tags, links, sources, len(body.encode()), len(links), 0)

    for title, info in list(tiddlers.items()):
        backlinks = sum(1 for t, i in tiddlers.items() if title in i.links)
        tiddlers[title] = TiddlerInfo(info.path, title, info.tags, info.links, info.sources, info.body_bytes, info.link_count, backlinks)

    return tiddlers


def preview_build(sources: list[SourceEntry]) -> list[dict]:
    """Show what tiddlers would be created for uncovered sources."""
    tiddlers = _load_existing_tiddlers()
    plans: list[dict] = []

    for src in sources:
        if src.matched_tiddlers:
            continue
        plans.append(_draft_tiddler_plan(src, tiddlers))

    return plans


def execute_build(sources: list[SourceEntry], dry_run: bool = False) -> int:
    """Compile new tiddlers from uncovered sources."""
    tiddlers = _load_existing_tiddlers()
    created = 0

    for src in sources:
        if src.matched_tiddlers:
            continue
        plan = _draft_tiddler_plan(src, tiddlers)
        if not plan:
            continue

        fname = f"{plan['title']}.tid"
        fpath = TIDDLER_DIR / fname

        content = plan["content"]

        if dry_run:
            print(f"[DRY] would create: {fname} ({plan['size_kb']}KB source, {plan['msg_count']} msgs)")
            continue

        fpath.write_text(content, encoding="utf-8")
        created += 1

    if dry_run:
        print(f"\nWould create {created} new tiddlers from {len(sources)} sources (dry run)")
    else:
        print(f"Created {created} new tiddlers from {len(sources)} sources")
    return created


def _draft_tiddler_plan(src: SourceEntry, tiddlers: dict[str, TiddlerInfo]) -> dict | None:
    if src.kind == "unknown" or not src.title:
        return None

    tags = _infer_tags(src.title, src.kind)
    vector = concept_vector_14(src.title, "", tags)

    related = [t for t in tiddlers if any(
        kw.lower() in (t + " ".join(tiddlers[t].tags)).lower()
        for kw in src.title.lower().split()[:3]
    )][:5]

    content = f"""\
created: {NOW_TS}
modified: {NOW_TS}
tags: ResearchStack {" ".join(tags)}
title: {src.title}
type: text/vnd.tiddlywiki

! {src.title}

[Auto-compiled from source material. Review and expand.]

!! Source Context

* Type: {src.kind.replace('_', ' ')}
* Size: {src.size_kb} KB
* Messages: {src.msg_count}
* Source hash: `{src.sha256[:16]}`
{"* Original URL: " + src.url if src.url else ""}

!! Durable Source

`{src.path}`

!! Related

{chr(10).join(f"* [[{r}]]" for r in related) if related else "* (none yet)"}
"""
    return {
        "title": src.title,
        "content": content,
        "size_kb": src.size_kb,
        "msg_count": src.msg_count,
    }


def _infer_tags(title: str, kind: str) -> list[str]:
    tags: list[str] = []
    lower = title.lower()
    for axis, keywords in AXIS_KEYWORDS.items():
        if any(kw.lower() in lower for kw in keywords):
            tags.append(axis)
    if kind == "kimi_json":
        tags.append("Kimi")
    elif kind == "chatgpt_md":
        tags.append("ChatGPT")
        tags.append("Conversation")
    if not tags:
        tags.append("ResearchStack")
    return sorted(set(tags))


def lint_wiki() -> LintResult:
    tiddlers = _load_existing_tiddlers()

    orphans = [t for t, i in tiddlers.items() if i.backlink_count == 0 and not t.startswith("$__")]
    stubs = [t for t, i in tiddlers.items() if i.body_bytes < 200 and not t.startswith("$__")]
    no_sources = [t for t, i in tiddlers.items() if not i.sources and not t.startswith("$__")]

    uncompiled: list[str] = []
    skip_patterns = _load_skip_patterns()
    for src_dir in SOURCE_DIRS:
        if not src_dir.exists():
            continue
        for fpath in src_dir.rglob("*"):
            if fpath.is_dir() or fpath.name.startswith("."):
                continue
            basename = fpath.name
            suffix = fpath.suffix.lower()
            SKIP_EXTS = {".zip", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".pyc", ".pkl",
                         ".parquet", ".csv", ".tsv", ".log", ".bin", ".o", ".so", ".dll",
                         ".ipynb", ".tgz", ".gz", ".bz2", ".xz", ".lock", ".toml", ".cfg",
                         ".ini", ".cff", ".lean", ".scad", ".asm", ".v", ".c", ".rs",
                         ".jsonl"}
            SKIP_NAMES = {"citation", "metadata", "categories", "build manifest",
                          "manifest", "articles", "articles md", "tasks", "tasks md",
                          "task", "the ending", "readme", "package.json", ".gitignore"}
            if suffix in SKIP_EXTS or basename in SKIP_NAMES or basename.startswith("."):
                continue
            normalized = basename.lower().replace("_", " ").replace("-", " ").replace("%20", " ")
            if any(p.lower().replace("_", " ").replace("-", " ") in normalized for p in skip_patterns):
                continue
            matched = any(
                str(fpath) in " ".join(i.sources) or fpath.name in " ".join(i.sources)
                for i in tiddlers.values()
            )
            if not matched and suffix in (".json", ".md", ".txt", ".pdf"):
                uncompiled.append(str(fpath))

    dead_links: list[tuple[str, str]] = []
    for title, info in tiddlers.items():
        for link in info.links:
            if link not in tiddlers:
                dead_links.append((title, link))

    return LintResult(orphans, stubs, no_sources, uncompiled, dead_links)


def build_sources_md() -> str:
    """Generate the sources.md provenance spine."""
    sources = scan_sources(limit=300)
    tiddlers = _load_existing_tiddlers()

    lines = [
        "# Research Stack — Source Provenance Spine\n",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M')}\n",
        f"Sources scanned: {len(sources)}",
        f"Tiddlers compiled: {len(tiddlers)}\n",
        "## Covered Sources (have matching tiddlers)\n",
    ]

    covered = [s for s in sources if s.matched_tiddlers]
    for s in covered:
        lines.append(f"- **{s.title}** ({s.kind}, {s.size_kb}KB) → {', '.join(f'[[{t}]]' for t in s.matched_tiddlers)}")

    lines.append("\n## Uncovered Sources (no tiddlers yet)\n")
    uncovered = [s for s in sources if not s.matched_tiddlers]
    for s in uncovered:
        lines.append(f"- {s.title} ({s.kind}, {s.size_kb}KB) — `{s.path}`")

    lines.append("\n## Maintenance Log\n")
    lines.append(f"| Date | Action | Detail |")
    lines.append(f"|------|--------|--------|")
    lines.append(f"| {time.strftime('%Y-%m-%d')} | sources.md generated | {len(coverage:=covered)} covered, {len(uncovered)} uncovered |")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Wiki Builder Shim — raw→wiki→maintenance loop")
    parser.add_argument("mode", choices=["scan", "build", "lint", "sources"],
                        help="Operation mode")
    parser.add_argument("--dry", action="store_true", help="Dry run for build mode")
    parser.add_argument("--limit", type=int, default=200, help="Max sources to scan")
    parser.add_argument("--json", action="store_true", help="JSON output (scan/lint modes)")
    args = parser.parse_args()

    if args.mode == "scan":
        sources = scan_sources(limit=args.limit)
        if args.json:
            out = [{"title": s.title, "kind": s.kind, "size_kb": s.size_kb,
                     "msgs": s.msg_count, "matched": s.matched_tiddlers, "path": str(s.path)}
                    for s in sources]
            print(json.dumps(out, indent=2))
        else:
            covered = sum(1 for s in sources if s.matched_tiddlers)
            uncovered = len(sources) - covered
            print(f"Sources scanned: {len(sources)}  |  Covered: {covered}  |  Uncovered: {uncovered}\n")
            for s in sources:
                status = f"→ {', '.join(s.matched_tiddlers[:3])}" if s.matched_tiddlers else "[UNCOVERED]"
                print(f"  {s.size_kb:>5}KB  {s.kind:<16}  {s.title[:60]:60s}  {status}")
        return 0

    if args.mode == "build":
        sources = scan_sources(limit=args.limit)
        count = execute_build(sources, dry_run=args.dry)
        return 0 if count >= 0 else 1

    if args.mode == "lint":
        result = lint_wiki()
        if args.json:
            print(json.dumps({
                "orphans": result.orphans,
                "stubs": result.stubs,
                "no_sources": result.no_sources,
                "uncompiled_sources": result.uncompiled_sources[:50],
                "dead_links": [[a, b] for a, b in result.dead_links[:50]],
            }, indent=2))
        else:
            print(f"=== Wiki Lint Report ===\n")
            print(f"Orphans (zero backlinks): {len(result.orphans)}")
            for t in result.orphans[:20]:
                print(f"  - {t}")
            print(f"\nStubs (<200 bytes): {len(result.stubs)}")
            for t in result.stubs[:20]:
                print(f"  - {t}")
            print(f"\nNo Durable Source refs: {len(result.no_sources)}")
            for t in result.no_sources[:20]:
                print(f"  - {t}")
            print(f"\nUncompiled sources: {len(result.uncompiled_sources)}")
            for s in result.uncompiled_sources[:20]:
                print(f"  - {s}")
            print(f"\nDead links: {len(result.dead_links)}")
            for t, link in result.dead_links[:20]:
                print(f"  - [[{t}]] → [[{link}]] (missing)")
        return 0

    if args.mode == "sources":
        md = build_sources_md()
        SOURCES_MD.parent.mkdir(parents=True, exist_ok=True)
        SOURCES_MD.write_text(md, encoding="utf-8")
        PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
        _write_prompt_files()
        print(f"Wrote: {SOURCES_MD}")
        print(f"Wrote prompt files to: {PROMPTS_DIR}")
        return 0

    return 1


def _write_prompt_files() -> None:
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)

    compile_source = dedent("""\
    # Compile Source Page Prompt

    Given a raw source file (conversation dump, article, paper),
    produce a single tiddlywiki page that:

    1. Summarizes the key claims in 2-3 bullet points
    2. Links to at least 3 existing wiki pages if relevant concepts exist
    3. Includes a [[Durable Source]] reference pointing back to the raw file
    4. Uses appropriate tags from the ResearchStack taxonomy
    5. Marks speculative claims with (?) prefix

    Source file: {path}
    Source type: {kind}
    Source size: {size_kb} KB
    """)

    lint_wiki_prompt = dedent("""\
    # Lint Wiki Prompt

    Review the entire tiddlywiki for quality issues:

    1. Pages with <200 bytes of body text (stubs) — flag for expansion
    2. Pages with zero inbound links (orphans) — suggest link targets
    3. Pages without [[Durable Source]] references — add provenance
    4. Dead links pointing to nonexistent pages — suggest targets or remove
    5. Source files in raw/ that have no compiled wiki page — flag for compilation

    Report format: table of {page, issue type, suggested fix}
    """)

    query_and_file = dedent("""\
    # Query and File Prompt

    When answering a question about the Research Stack:

    1. Search existing wiki pages for relevant information first
    2. If the answer involves a concept not yet in the wiki, draft a new page
    3. File the answer as a wiki/question/ page with the question as context
    4. Link the answer back to at least one existing concept page
    5. Add a maintenance log entry recording the query and its resolution
    """)

    (PROMPTS_DIR / "compile-source.md").write_text(compile_source, encoding="utf-8")
    (PROMPTS_DIR / "lint-wiki.md").write_text(lint_wiki_prompt, encoding="utf-8")
    (PROMPTS_DIR / "query-and-file.md").write_text(query_and_file, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
