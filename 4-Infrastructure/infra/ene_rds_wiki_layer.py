"""RDS-backed ENEWikiLayer — drop-in replacement for SQLite ENEWikiLayer.

API-compatible with ene_wiki_layer.ENEWikiLayer: same dataclasses, same
handle_request() protocol, but backed by PostgreSQL via psycopg2.

Constructor:
  ENERDSWikiLayer(dsn="postgresql://user:pass@host:5432/dbname")

The DSN defaults to the RDS_HOST / RDS_PORT / RDS_USER / RDS_PASSWORD / RDS_DB
environment variables (or postgres as dbname, research_stack as fallback).
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extras
import psycopg2.pool

from infra.ene_wiki_layer import (
    WikiPage,
    WikiRevision,
    normalize_title,
    title_slug,
    extract_links,
    extract_categories,
    write_receipt,
    canonical_json,
    sha256_text,
    iso_utc,
    concept_vector_for_wiki,
    genome_from_vector,
    make_archive_record,
    make_jsonl_event,
)


DEFAULT_DSN = None


def _default_dsn() -> str:
    host = os.environ.get("RDS_HOST", "database-1-instance-1.cghu8yqogqwo.us-east-1.rds.amazonaws.com")
    port = os.environ.get("RDS_PORT", "5432")
    user = os.environ.get("RDS_USER", "postgres")
    password = os.environ.get("RDS_PASSWORD") or os.environ.get("RDS_IAM_TOKEN", "")
    dbname = os.environ.get("RDS_DB", "postgres")
    return f"host={host} port={port} dbname={dbname} user={user} password={password} sslmode=require"


import os


class ENERDSWikiLayer:
    def __init__(self, dsn: str | None = None):
        self.dsn = dsn or _default_dsn()
        self._pool: psycopg2.pool.ThreadedConnectionPool | None = None
        self._init_tables()

    def _get_conn(self):
        return psycopg2.connect(self.dsn)

    def _init_tables(self) -> None:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE SCHEMA IF NOT EXISTS ene")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS ene.wiki_pages (
                        slug TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        latest_revision INTEGER NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                        receipt TEXT NOT NULL
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS ene.wiki_revisions (
                        slug TEXT NOT NULL,
                        revision INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        text TEXT NOT NULL,
                        author TEXT NOT NULL DEFAULT 'ene',
                        summary TEXT NOT NULL DEFAULT '',
                        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                        receipt TEXT NOT NULL,
                        archive_id TEXT,
                        content_hash TEXT,
                        archive_record JSONB DEFAULT '{}',
                        jsonl_event JSONB DEFAULT '{}',
                        PRIMARY KEY (slug, revision)
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS ene.wiki_links (
                        slug TEXT NOT NULL,
                        target_slug TEXT NOT NULL,
                        target_title TEXT NOT NULL,
                        PRIMARY KEY (slug, target_slug)
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS ene.wiki_categories (
                        slug TEXT NOT NULL,
                        category TEXT NOT NULL,
                        PRIMARY KEY (slug, category)
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS ene.packages (
                        pkg TEXT PRIMARY KEY,
                        version TEXT NOT NULL,
                        tier TEXT,
                        domain TEXT,
                        archetype TEXT,
                        description TEXT,
                        tags JSONB DEFAULT '[]',
                        source TEXT,
                        sha256 TEXT,
                        indexed_utc TEXT,
                        concept_anchor JSONB DEFAULT '{}',
                        concept_vector JSONB DEFAULT '[]',
                        idea_weights JSONB DEFAULT '{}',
                        analog_map JSONB DEFAULT '{}'
                    )
                """)
                self._ensure_columns(conn, "ene.wiki_revisions", cur)
            conn.commit()

    def _ensure_columns(self, conn, table: str, cur) -> None:
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = 'ene' AND table_name = %s
        """, (table.split('.')[1],))
        existing = {r[0] for r in cur.fetchall()}
        additions = {
            "archive_id": "TEXT",
            "content_hash": "TEXT",
            "archive_record": "JSONB DEFAULT '{}'",
            "jsonl_event": "JSONB DEFAULT '{}'",
        }
        for name, decl in additions.items():
            if name not in existing:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {name} {decl}")

    def _upsert_package(self, conn, cur, event: dict[str, Any]) -> None:
        data = event["data"]
        cur.execute("""
            INSERT INTO ene.packages (
                pkg, version, tier, domain, archetype, description,
                tags, source, sha256, indexed_utc,
                concept_anchor, concept_vector, idea_weights, analog_map
            ) VALUES (
                %(pkg)s, %(version)s, %(tier)s, %(domain)s, %(archetype)s, %(description)s,
                %(tags)s, %(source)s, %(sha256)s, %(indexed_utc)s,
                %(concept_anchor)s, %(concept_vector)s, %(idea_weights)s, %(analog_map)s
            ) ON CONFLICT (pkg) DO UPDATE SET
                version = EXCLUDED.version,
                tier = EXCLUDED.tier,
                domain = EXCLUDED.domain,
                archetype = EXCLUDED.archetype,
                description = EXCLUDED.description,
                tags = EXCLUDED.tags,
                source = EXCLUDED.source,
                sha256 = EXCLUDED.sha256,
                indexed_utc = EXCLUDED.indexed_utc,
                concept_anchor = EXCLUDED.concept_anchor,
                concept_vector = EXCLUDED.concept_vector,
                idea_weights = EXCLUDED.idea_weights,
                analog_map = EXCLUDED.analog_map
        """, {
            "pkg": data["pkg"],
            "version": data["version"],
            "tier": data["tier"],
            "domain": data["domain"],
            "archetype": data["archetype"],
            "description": data["description"],
            "tags": json.dumps(data["tags"], sort_keys=True),
            "source": data["source"],
            "sha256": data["sha256"],
            "indexed_utc": data["indexed_utc"],
            "concept_anchor": json.dumps(data["concept_anchor"], sort_keys=True),
            "concept_vector": json.dumps(data["concept_vector"], sort_keys=True),
            "idea_weights": json.dumps(data["idea_weights"], sort_keys=True),
            "analog_map": json.dumps(data["analog_map"], sort_keys=True),
        })

    def admit_write(self, title: str, text: str) -> tuple[bool, str]:
        try:
            normalize_title(title)
        except ValueError as exc:
            return False, str(exc)
        if len(text.encode("utf-8")) > 256_000:
            return False, "wiki text too large"
        lowered = text.lower()
        if "<script" in lowered or "javascript:" in lowered:
            return False, "active script content refused"
        return True, "wiki_write_admitted"

    def put_page(self, title: str, text: str, author: str = "ene", summary: str = "") -> WikiRevision:
        admitted, reason = self.admit_write(title, text)
        if not admitted:
            raise ValueError(reason)

        normalized = normalize_title(title)
        slug = title_slug(normalized)
        now_ts = int(time.time())
        now_dt = datetime.fromtimestamp(now_ts, tz=timezone.utc)
        links = extract_links(text)
        categories = extract_categories(text)

        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT latest_revision FROM ene.wiki_pages WHERE slug = %s",
                    (slug,),
                )
                row = cur.fetchone()
                revision = int(row[0]) + 1 if row else 1
                receipt = write_receipt(slug, revision, text, author, now_ts)
                archive_record = make_archive_record(
                    normalized, slug, revision, text, author, summary, now_ts, links, categories
                )
                concept_vector = concept_vector_for_wiki(normalized, text, links, categories)
                jsonl_event = make_jsonl_event(archive_record, concept_vector, receipt)

                cur.execute("""
                    INSERT INTO ene.wiki_revisions
                    (slug, revision, title, text, author, summary, created_at, receipt,
                     archive_id, content_hash, archive_record, jsonl_event)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    slug, revision, normalized, text, author, summary, now_dt, receipt,
                    archive_record["archive_id"], archive_record["content_hash"],
                    json.dumps(archive_record, sort_keys=True),
                    json.dumps(jsonl_event, sort_keys=True),
                ))

                cur.execute("""
                    INSERT INTO ene.wiki_pages (slug, title, latest_revision, updated_at, receipt)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (slug) DO UPDATE SET
                        title = EXCLUDED.title,
                        latest_revision = EXCLUDED.latest_revision,
                        updated_at = EXCLUDED.updated_at,
                        receipt = EXCLUDED.receipt
                """, (slug, normalized, revision, now_dt, receipt))

                cur.execute("DELETE FROM ene.wiki_links WHERE slug = %s", (slug,))
                cur.execute("DELETE FROM ene.wiki_categories WHERE slug = %s", (slug,))

                if links:
                    psycopg2.extras.execute_values(
                        cur,
                        "INSERT INTO ene.wiki_links (slug, target_slug, target_title) VALUES %s ON CONFLICT DO NOTHING",
                        [(slug, title_slug(link), link) for link in links],
                    )
                if categories:
                    psycopg2.extras.execute_values(
                        cur,
                        "INSERT INTO ene.wiki_categories (slug, category) VALUES %s ON CONFLICT DO NOTHING",
                        [(slug, cat) for cat in categories],
                    )

                self._upsert_package(conn, cur, jsonl_event)
            conn.commit()

        return WikiRevision(
            normalized, slug, revision, text, author, summary, now_ts, receipt,
            links, categories, archive_record, jsonl_event,
        )

    def get_page(self, title: str, revision: int | None = None) -> WikiRevision | None:
        slug = title_slug(title)
        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if revision is None:
                    cur.execute(
                        "SELECT latest_revision FROM ene.wiki_pages WHERE slug = %s",
                        (slug,),
                    )
                    page = cur.fetchone()
                    if not page:
                        return None
                    revision = int(page["latest_revision"])
                else:
                    revision = int(revision)

                cur.execute("""
                    SELECT title, slug, revision, text, author, summary, created_at, receipt,
                           archive_record, jsonl_event
                    FROM ene.wiki_revisions
                    WHERE slug = %s AND revision = %s
                """, (slug, revision))
                row = cur.fetchone()
                if not row:
                    return None

                cur.execute(
                    "SELECT target_title FROM ene.wiki_links WHERE slug = %s ORDER BY lower(target_title)",
                    (slug,),
                )
                links = [r["target_title"] for r in cur.fetchall()]

                cur.execute(
                    "SELECT category FROM ene.wiki_categories WHERE slug = %s ORDER BY lower(category)",
                    (slug,),
                )
                categories = [r["category"] for r in cur.fetchall()]

                archive_record = row["archive_record"] if isinstance(row["archive_record"], dict) else json.loads(row["archive_record"] or "{}")
                jsonl_event = row["jsonl_event"] if isinstance(row["jsonl_event"], dict) else json.loads(row["jsonl_event"] or "{}")
                created_ts = int(row["created_at"].timestamp()) if hasattr(row["created_at"], "timestamp") else 0

        return WikiRevision(
            row["title"], row["slug"], int(row["revision"]), row["text"],
            row["author"], row["summary"], created_ts, row["receipt"],
            links, categories, archive_record, jsonl_event,
        )

    def search(self, query: str, limit: int = 20) -> list[WikiPage]:
        term = f"%{query.strip()}%"
        limit = max(1, min(limit, 100))
        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT p.title, p.slug, p.latest_revision, p.updated_at, p.receipt
                    FROM ene.wiki_pages p
                    JOIN ene.wiki_revisions r
                      ON r.slug = p.slug AND r.revision = p.latest_revision
                    WHERE p.title ILIKE %s OR r.text ILIKE %s
                    ORDER BY p.updated_at DESC
                    LIMIT %s
                """, (term, term, limit))
                rows = cur.fetchall()
        return [
            WikiPage(
                r["title"], r["slug"], int(r["latest_revision"]),
                int(r["updated_at"].timestamp()) if hasattr(r["updated_at"], "timestamp") else 0,
                r["receipt"],
            )
            for r in rows
        ]

    def backlinks(self, title: str) -> list[WikiPage]:
        target = title_slug(title)
        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT p.title, p.slug, p.latest_revision, p.updated_at, p.receipt
                    FROM ene.wiki_links l
                    JOIN ene.wiki_pages p ON p.slug = l.slug
                    WHERE l.target_slug = %s
                    ORDER BY lower(p.title)
                """, (target,))
                rows = cur.fetchall()
        return [
            WikiPage(
                r["title"], r["slug"], int(r["latest_revision"]),
                int(r["updated_at"].timestamp()) if hasattr(r["updated_at"], "timestamp") else 0,
                r["receipt"],
            )
            for r in rows
        ]

    def recent_changes(self, limit: int = 20) -> list[WikiPage]:
        limit = max(1, min(limit, 100))
        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT title, slug, latest_revision, updated_at, receipt
                    FROM ene.wiki_pages
                    ORDER BY updated_at DESC
                    LIMIT %s
                """, (limit,))
                rows = cur.fetchall()
        return [
            WikiPage(
                r["title"], r["slug"], int(r["latest_revision"]),
                int(r["updated_at"].timestamp()) if hasattr(r["updated_at"], "timestamp") else 0,
                r["receipt"],
            )
            for r in rows
        ]

    def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        op = str(request.get("op", "recent"))
        if op in {"put", "edit"}:
            revision = self.put_page(
                title=str(request.get("title", "")),
                text=str(request.get("text", "")),
                author=str(request.get("author", "ene")),
                summary=str(request.get("summary", "")),
            )
            return {"ok": True, "op": op, "revision": asdict(revision)}
        if op == "get":
            page = self.get_page(str(request.get("title", "")), request.get("revision"))
            return {"ok": page is not None, "op": op, "page": asdict(page) if page else None}
        if op == "search":
            pages = self.search(str(request.get("query", "")), int(request.get("limit", 20)))
            return {"ok": True, "op": op, "pages": [asdict(page) for page in pages]}
        if op == "backlinks":
            pages = self.backlinks(str(request.get("title", "")))
            return {"ok": True, "op": op, "pages": [asdict(page) for page in pages]}
        if op == "recent":
            pages = self.recent_changes(int(request.get("limit", 20)))
            return {"ok": True, "op": op, "pages": [asdict(page) for page in pages]}
        raise ValueError(f"unsupported wiki op {op!r}")


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="ENE RDS wiki layer")
    parser.add_argument("--dsn", help="PostgreSQL DSN")
    parser.add_argument("--op", choices=["put", "get", "search", "backlinks", "recent"], default="recent")
    parser.add_argument("--title", default="")
    parser.add_argument("--text", default="")
    parser.add_argument("--query", default="")
    parser.add_argument("--author", default="ene")
    args = parser.parse_args()

    wiki = ENERDSWikiLayer(args.dsn)
    request: dict[str, Any] = {
        "op": args.op, "title": args.title, "text": args.text,
        "query": args.query, "author": args.author,
    }
    print(json.dumps(wiki.handle_request(request), sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
