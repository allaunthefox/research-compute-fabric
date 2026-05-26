#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "boto3",
#   "psycopg2-binary",
# ]
# ///
"""
ENE Wiki Body Re-ingestion Shim.

All 278 ene.wiki_revisions rows currently have text = "" or "[object Promise]"
(a JavaScript async bug from the original ingestion pipeline).

This shim finds real content for each wiki page slug from the following
sources, in priority order:

  1. knowledge.tiddlywiki_pages  — exact title match (body field)
  2. Local filesystem             — for "X → Y" title pattern, read the
                                    actual file or directory listing from
                                    /home/allaun/Research Stack/X/Y
  3. knowledge.documents          — Notion content match by title (if content != '')
  4. ene.packages description     — description field (fallback)
  5. Synthesized stub             — title + slug as minimal placeholder

Updates ene.wiki_revisions.text in-place (only rows where text is empty or
"[object Promise]") and writes a receipt to ingestion.receipts.

Run with:
  cd "/home/allaun/Research Stack"
  uv run 4-Infrastructure/shim/ene_wiki_body_reingest.py
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import uuid
from pathlib import Path
from typing import Optional

import psycopg2
import psycopg2.extras
from rds_connect import connect_rds

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ene_wiki_body_reingest")

# ---------------------------------------------------------------------------
# RDS connection
# ---------------------------------------------------------------------------
RESEARCH_STACK = Path(os.environ.get("RESEARCH_STACK", "/home/allaun/Research Stack"))

# Maximum bytes to read from a single local file (avoid ingesting huge blobs)
MAX_FILE_BYTES = 64 * 1024  # 64 KB


def connect() -> psycopg2.extensions.connection:
    return connect_rds()


# ---------------------------------------------------------------------------
# Source 1: TiddlyWiki pages (knowledge.tiddlywiki_pages)
# ---------------------------------------------------------------------------
def load_tiddlywiki_index(conn) -> dict[str, str]:
    """Return {lower(title): body} for all tiddlywiki pages with non-empty body."""
    idx: dict[str, str] = {}
    with conn.cursor() as cur:
        cur.execute(
            "SELECT title, body FROM knowledge.tiddlywiki_pages WHERE body IS NOT NULL AND body != ''"
        )
        for title, body in cur.fetchall():
            idx[title.lower().strip()] = body
    log.info("TiddlyWiki index loaded: %d pages", len(idx))
    return idx


# ---------------------------------------------------------------------------
# Source 2: Local filesystem
# ---------------------------------------------------------------------------
def title_to_fs_path(title: str) -> Optional[Path]:
    """'A → B' wiki title → /home/allaun/Research Stack/A/B."""
    if " → " not in title:
        return None
    parent, child = title.split(" → ", 1)
    return RESEARCH_STACK / parent.strip() / child.strip()


def read_fs_content(path: Path) -> Optional[str]:
    """
    Read content from a filesystem path:
    - If it's a file, return its text (truncated to MAX_FILE_BYTES).
    - If it's a directory, return a compact directory listing with file sizes.
    - If it doesn't exist, return None.
    """
    if not path.exists():
        return None

    if path.is_file():
        try:
            raw = path.read_bytes()[:MAX_FILE_BYTES]
            text = raw.decode("utf-8", errors="replace")
            suffix = f"\n\n[truncated at {MAX_FILE_BYTES // 1024} KB]" if len(raw) == MAX_FILE_BYTES else ""
            return text + suffix
        except Exception as exc:
            log.debug("Could not read file %s: %s", path, exc)
            return None

    if path.is_dir():
        lines = [f"# {path.name}/\n"]
        try:
            entries = sorted(path.iterdir())
        except PermissionError:
            return None
        files = [e for e in entries if e.is_file()]
        dirs  = [e for e in entries if e.is_dir()]
        if dirs:
            lines.append("## Subdirectories")
            for d in dirs[:50]:
                lines.append(f"- `{d.name}/`")
        if files:
            lines.append("\n## Files")
            for f in files[:100]:
                try:
                    sz = f.stat().st_size
                    lines.append(f"- `{f.name}` ({sz:,} bytes)")
                except OSError:
                    lines.append(f"- `{f.name}`")
        return "\n".join(lines)

    return None


# ---------------------------------------------------------------------------
# Source 3: Notion documents (knowledge.documents)
# ---------------------------------------------------------------------------
def load_notion_index(conn) -> dict[str, str]:
    """Return {lower(title): content} for Notion docs with non-empty content."""
    idx: dict[str, str] = {}
    with conn.cursor() as cur:
        cur.execute(
            "SELECT title, content FROM knowledge.documents "
            "WHERE source='notion' AND content IS NOT NULL AND content != ''"
        )
        for title, content in cur.fetchall():
            key = title.lower().strip()
            # Keep the longest content if there are duplicates
            if key not in idx or len(content) > len(idx[key]):
                idx[key] = content
    log.info("Notion document index loaded: %d entries", len(idx))
    return idx


# ---------------------------------------------------------------------------
# Source 4: ENE packages description
# ---------------------------------------------------------------------------
def load_packages_index(conn) -> dict[str, str]:
    """Return {slug: description} from ene.packages for wiki/* packages."""
    idx: dict[str, str] = {}
    with conn.cursor() as cur:
        cur.execute(
            "SELECT pkg, description FROM ene.packages "
            "WHERE pkg LIKE 'ene/wiki/%' AND description IS NOT NULL AND description != ''"
        )
        for pkg, description in cur.fetchall():
            slug = pkg.removeprefix("ene/wiki/")
            idx[slug] = description
    log.info("ENE packages index loaded: %d wiki entries", len(idx))
    return idx


# ---------------------------------------------------------------------------
# Content resolution
# ---------------------------------------------------------------------------
def resolve_content(
    slug: str,
    title: str,
    tiddly_idx: dict[str, str],
    notion_idx: dict[str, str],
    pkg_idx: dict[str, str],
) -> tuple[str, str]:
    """
    Return (content, source_tag) for the given wiki revision.
    source_tag is one of: tiddlywiki, filesystem, notion, package, generated
    """
    title_lower = title.lower().strip()

    # --- Source 1: TiddlyWiki exact match ---
    if title_lower in tiddly_idx:
        return tiddly_idx[title_lower], "tiddlywiki"

    # --- Source 2: Filesystem (for "X → Y" titles) ---
    fs_path = title_to_fs_path(title)
    if fs_path is not None:
        fs_content = read_fs_content(fs_path)
        if fs_content:
            return fs_content, "filesystem"

    # --- Source 3: Notion documents ---
    if title_lower in notion_idx:
        return notion_idx[title_lower], "notion"

    # --- Source 4: ENE packages description ---
    if slug in pkg_idx:
        desc = pkg_idx[slug]
        return f"# {title}\n\n{desc}", "package"

    # --- Source 5: Generated stub ---
    stub = (
        f"# {title}\n\n"
        f"*Stub page — no source content found during re-ingestion.*\n\n"
        f"**Slug:** `{slug}`\n"
    )
    return stub, "generated"


# ---------------------------------------------------------------------------
# Receipt helper
# ---------------------------------------------------------------------------
def record_receipt(conn, status: str, metadata: dict, error: str | None = None) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO ingestion.receipts
                (receipt_id, shim_name, status, metadata, error_detail, ran_at)
            VALUES (%s, %s, %s, %s, %s, now())
            """,
            (
                str(uuid.uuid4()),
                "ene_wiki_body_reingest",
                status,
                json.dumps(metadata),
                error,
            ),
        )
    conn.commit()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    log.info("Connecting to RDS…")
    conn = connect()
    conn.autocommit = False

    # Build source indexes (read-only queries, no transaction needed)
    log.info("Building source indexes…")
    tiddly_idx  = load_tiddlywiki_index(conn)
    notion_idx  = load_notion_index(conn)
    pkg_idx     = load_packages_index(conn)

    # Fetch all wiki revisions (we update ALL of them to fix the [object Promise] bug too)
    log.info("Fetching all wiki revisions…")
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT slug, revision, title, text FROM ene.wiki_revisions ORDER BY slug, revision"
        )
        revisions = cur.fetchall()

    log.info("Total revisions to process: %d", len(revisions))

    # Stats counters
    stats: dict[str, int] = {
        "total": len(revisions),
        "updated": 0,
        "skipped_already_good": 0,
        "tiddlywiki": 0,
        "filesystem": 0,
        "notion": 0,
        "package": 0,
        "generated": 0,
    }

    BATCH = 50
    batch_count = 0

    for rev in revisions:
        slug     = rev["slug"]
        revision = rev["revision"]
        title    = rev["title"]
        current  = rev["text"] or ""

        # Decide whether this row needs updating:
        # Bad if it's empty string OR the literal "[object Promise]" (including repeated newlines of it)
        is_bad = (
            current.strip() == ""
            or current.strip() == "[object Promise]"
            or (current.replace("[object Promise]", "").replace("\n", "").strip() == "")
        )

        if not is_bad:
            stats["skipped_already_good"] += 1
            continue

        # Resolve content from sources
        content, source_tag = resolve_content(slug, title, tiddly_idx, notion_idx, pkg_idx)

        stats[source_tag] += 1
        stats["updated"] += 1

        with conn.cursor() as cur:
            cur.execute(
                "UPDATE ene.wiki_revisions SET text = %s WHERE slug = %s AND revision = %s",
                (content, slug, revision),
            )

        batch_count += 1
        if batch_count % BATCH == 0:
            conn.commit()
            log.info(
                "  Committed %d/%d revisions updated so far…",
                stats["updated"],
                stats["total"],
            )

    conn.commit()
    log.info("Final commit done.")

    log.info(
        "Summary: total=%d updated=%d skipped=%d | "
        "tiddlywiki=%d filesystem=%d notion=%d package=%d generated=%d",
        stats["total"],
        stats["updated"],
        stats["skipped_already_good"],
        stats["tiddlywiki"],
        stats["filesystem"],
        stats["notion"],
        stats["package"],
        stats["generated"],
    )

    record_receipt(conn, "success", {
        "pages_updated": stats["updated"],
        "skipped_already_good": stats["skipped_already_good"],
        "sources": {
            "tiddlywiki": stats["tiddlywiki"],
            "filesystem": stats["filesystem"],
            "notion": stats["notion"],
            "package": stats["package"],
            "generated": stats["generated"],
        },
        "total_revisions": stats["total"],
    })

    conn.close()
    log.info("Done.")


if __name__ == "__main__":
    main()
