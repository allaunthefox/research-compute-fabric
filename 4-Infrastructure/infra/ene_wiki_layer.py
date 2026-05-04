#!/usr/bin/env python3
"""ENE MediaWiki-like layer.

This is a compact wiki surface for ENE rather than a full MediaWiki install.
It provides page revisions, wiki links, categories, recent changes, backlinks,
and deterministic write receipts using only SQLite and the Python stdlib.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_DB_PATH = Path("/home/allaun/Documents/Research Stack/data/substrate_index.db")
LINK_RE = re.compile(r"\[\[([^\[\]\n|#]+)(?:[#|][^\[\]\n]*)?\]\]")
CATEGORY_RE = re.compile(r"\[\[\s*Category\s*:\s*([^\[\]\n|#]+)(?:[#|][^\[\]\n]*)?\]\]", re.I)


@dataclass(frozen=True)
class WikiPage:
    title: str
    slug: str
    latest_revision: int
    updated_at: int
    receipt: str


@dataclass(frozen=True)
class WikiRevision:
    title: str
    slug: str
    revision: int
    text: str
    author: str
    summary: str
    created_at: int
    receipt: str
    links: list[str]
    categories: list[str]
    archive_record: dict[str, Any]
    jsonl_event: dict[str, Any]


def normalize_title(title: str) -> str:
    cleaned = " ".join(title.strip().split())
    if not cleaned:
        raise ValueError("wiki title is required")
    if len(cleaned) > 160:
        raise ValueError("wiki title too long")
    return cleaned


def title_slug(title: str) -> str:
    normalized = normalize_title(title)
    slug = normalized.lower()
    slug = re.sub(r"[^a-z0-9._ -]+", "", slug)
    slug = re.sub(r"\s+", "_", slug).strip("_")
    if not slug:
        slug = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
    return slug


def extract_links(text: str) -> list[str]:
    links = []
    for match in LINK_RE.finditer(text):
        target = normalize_title(match.group(1))
        if not target.lower().startswith("category:"):
            links.append(target)
    return sorted(set(links), key=str.lower)


def extract_categories(text: str) -> list[str]:
    categories = [normalize_title(match.group(1)) for match in CATEGORY_RE.finditer(text)]
    return sorted(set(categories), key=str.lower)


def write_receipt(slug: str, revision: int, text: str, author: str, created_at: int) -> str:
    payload = json.dumps(
        {
            "author": author,
            "created_at": created_at,
            "revision": revision,
            "slug": slug,
            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def iso_utc(ts: int | None = None) -> str:
    dt = datetime.fromtimestamp(ts or int(time.time()), tz=timezone.utc)
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def concept_vector_for_wiki(title: str, text: str, links: list[str], categories: list[str]) -> list[float]:
    """Derive a deterministic ConceptVector14-ish vector for wiki pages.

    This follows the ENE schema's fixed 14-axis shape without pretending to be
    a learned embedding. It is a bounded route/index vector.
    """
    lowered = f"{title}\n{text}".lower()
    axes = [0.0] * 14
    axes[2] = min(1.0, (lowered.count("topology") + lowered.count("manifold") + len(links)) / 12.0)
    axes[5] = min(1.0, (lowered.count("hash") + lowered.count("receipt") + lowered.count("verify")) / 8.0)
    axes[6] = min(1.0, (lowered.count("sqlite") + lowered.count("schema") + lowered.count("index")) / 8.0)
    axes[7] = min(1.0, (len(set(re.findall(r"[a-zA-Z][a-zA-Z0-9_]{2,}", lowered))) / 500.0))
    axes[11] = min(1.0, (lowered.count("proof") + lowered.count("lean") + lowered.count("theorem")) / 8.0)
    axes[12] = min(1.0, (len(categories) + lowered.count("archive") + lowered.count("history")) / 8.0)
    axes[13] = min(1.0, (lowered.count("author") + lowered.count("provenance") + lowered.count("attest")) / 8.0)
    if not any(axes):
        axes[7] = 1.0
    norm = sum(x * x for x in axes) ** 0.5
    return [round(x / norm, 6) if norm else 0.0 for x in axes]


def genome_from_vector(vector: list[float]) -> dict[str, int]:
    bins = [min(7, max(0, int(v * 8))) for v in vector]
    return {
        "mu": bins[1] if len(bins) > 1 else 0,
        "rho": bins[7] if len(bins) > 7 else 0,
        "c": bins[6] if len(bins) > 6 else 0,
        "m": bins[2] if len(bins) > 2 else 0,
        "ne": bins[12] if len(bins) > 12 else 0,
        "sig": bins[13] if len(bins) > 13 else 0,
    }


def archive_id_for(slug: str, content_hash: str) -> str:
    return f"json_catalog_ene_wiki_{slug}_{content_hash[:16]}"


def make_archive_record(
    title: str,
    slug: str,
    revision: int,
    text: str,
    author: str,
    summary: str,
    created_at: int,
    links: list[str],
    categories: list[str],
) -> dict[str, Any]:
    raw_content = {
        "kind": "ene_wiki_page",
        "title": title,
        "slug": slug,
        "revision": revision,
        "text": text,
        "author": author,
        "summary": summary,
        "links": links,
        "categories": categories,
    }
    content_hash = sha256_text(canonical_json(raw_content))
    return {
        "archive_id": archive_id_for(slug, content_hash),
        "source_type": "json_catalog",
        "source_file": f"ene-wiki://{slug}/{revision}",
        "raw_content": raw_content,
        "extracted_text": text[:10_000],
        "extracted_at": iso_utc(created_at),
        "content_hash": content_hash,
        "extraction_version": "ene_wiki_layer_v1",
    }


def make_jsonl_event(record: dict[str, Any], concept_vector: list[float], receipt: str) -> dict[str, Any]:
    now = time.time()
    pkg = f"ene/wiki/{record['raw_content']['slug']}"
    data = {
        "pkg": pkg,
        "version": record["extracted_at"],
        "tier": "RESEARCH",
        "domain": "semantic",
        "archetype": "wiki_page",
        "description": record["raw_content"]["title"],
        "tags": ["ene", "wiki", *record["raw_content"]["categories"]],
        "source": "ene_wiki_layer",
        "sha256": record["content_hash"],
        "indexed_utc": record["extracted_at"],
        "concept_anchor": {
            "domain": "semantic",
            "concept": record["raw_content"]["slug"],
            "resolution": "FORMING",
        },
        "concept_vector": concept_vector,
        "idea_weights": {"wiki_link_count": min(1.0, len(record["raw_content"]["links"]) / 16.0)},
        "analog_map": {"mediawiki": "ene_wiki_layer", "archive_id": record["archive_id"]},
    }
    event_id = f"ene:{record['archive_id']}"
    event = {
        "t": now,
        "src": "ene",
        "id": event_id,
        "op": "upsert",
        "data": data,
        "genome": genome_from_vector(concept_vector),
        "bind": {
            "lawful": True,
            "cost": max(1, len(record["extracted_text"].encode("utf-8"))) << 16,
            "invariant": "ene_wiki_revision_is_append_only",
            "class": "informational_bind",
        },
        "provenance": {
            "node": "ene-wiki-layer",
            "lake_seed": "local",
            "tailscale_ip": "",
            "attestation_hash": f"sha256:{receipt}",
            "prev_id": None,
        },
    }
    return event


class ENEWikiLayer:
    """Small revisioned wiki surface for ENE."""

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS ene_wiki_pages (
                    slug TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    latest_revision INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    receipt TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS ene_wiki_revisions (
                    slug TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    text TEXT NOT NULL,
                    author TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    receipt TEXT NOT NULL,
                    archive_id TEXT,
                    content_hash TEXT,
                    archive_record TEXT,
                    jsonl_event TEXT,
                    PRIMARY KEY (slug, revision)
                );

                CREATE TABLE IF NOT EXISTS ene_wiki_links (
                    slug TEXT NOT NULL,
                    target_slug TEXT NOT NULL,
                    target_title TEXT NOT NULL,
                    PRIMARY KEY (slug, target_slug)
                );

                CREATE TABLE IF NOT EXISTS ene_wiki_categories (
                    slug TEXT NOT NULL,
                    category TEXT NOT NULL,
                    PRIMARY KEY (slug, category)
                );
                """
            )
            self._ensure_columns(
                conn,
                "ene_wiki_revisions",
                {
                    "archive_id": "TEXT",
                    "content_hash": "TEXT",
                    "archive_record": "TEXT",
                    "jsonl_event": "TEXT",
                },
            )
            self._ensure_packages_table(conn)

    def _ensure_columns(self, conn: sqlite3.Connection, table: str, columns: dict[str, str]) -> None:
        existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
        for name, decl in columns.items():
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")

    def _ensure_packages_table(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS packages (
                pkg TEXT PRIMARY KEY,
                version TEXT NOT NULL,
                tier TEXT,
                domain TEXT,
                archetype TEXT,
                description TEXT,
                tags TEXT,
                source TEXT,
                sha256 TEXT,
                indexed_utc TEXT,
                concept_anchor TEXT,
                concept_vector TEXT,
                idea_weights TEXT,
                analog_map TEXT
            )
            """
        )

    def _upsert_package(self, conn: sqlite3.Connection, event: dict[str, Any]) -> None:
        data = event["data"]
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(packages)")}
        candidate = {
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
        }
        record = {key: value for key, value in candidate.items() if key in columns}
        keys = list(record)
        placeholders = ", ".join(["?"] * len(keys))
        assignments = ", ".join(f"{key}=excluded.{key}" for key in keys if key != "pkg")
        conn.execute(
            f"""
            INSERT INTO packages ({", ".join(keys)})
            VALUES ({placeholders})
            ON CONFLICT(pkg) DO UPDATE SET {assignments}
            """,
            [record[key] for key in keys],
        )

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
        now = int(time.time())
        links = extract_links(text)
        categories = extract_categories(text)

        with self._connect() as conn:
            row = conn.execute(
                "SELECT latest_revision FROM ene_wiki_pages WHERE slug = ?",
                (slug,),
            ).fetchone()
            revision = int(row["latest_revision"]) + 1 if row else 1
            receipt = write_receipt(slug, revision, text, author, now)
            archive_record = make_archive_record(normalized, slug, revision, text, author, summary, now, links, categories)
            concept_vector = concept_vector_for_wiki(normalized, text, links, categories)
            jsonl_event = make_jsonl_event(archive_record, concept_vector, receipt)

            conn.execute(
                """
                INSERT INTO ene_wiki_revisions
                (slug, revision, title, text, author, summary, created_at, receipt,
                 archive_id, content_hash, archive_record, jsonl_event)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    slug,
                    revision,
                    normalized,
                    text,
                    author,
                    summary,
                    now,
                    receipt,
                    archive_record["archive_id"],
                    archive_record["content_hash"],
                    canonical_json(archive_record),
                    canonical_json(jsonl_event),
                ),
            )
            conn.execute(
                """
                INSERT INTO ene_wiki_pages (slug, title, latest_revision, updated_at, receipt)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(slug) DO UPDATE SET
                  title = excluded.title,
                  latest_revision = excluded.latest_revision,
                  updated_at = excluded.updated_at,
                  receipt = excluded.receipt
                """,
                (slug, normalized, revision, now, receipt),
            )
            conn.execute("DELETE FROM ene_wiki_links WHERE slug = ?", (slug,))
            conn.execute("DELETE FROM ene_wiki_categories WHERE slug = ?", (slug,))
            conn.executemany(
                "INSERT OR REPLACE INTO ene_wiki_links (slug, target_slug, target_title) VALUES (?, ?, ?)",
                [(slug, title_slug(link), link) for link in links],
            )
            conn.executemany(
                "INSERT OR REPLACE INTO ene_wiki_categories (slug, category) VALUES (?, ?)",
                [(slug, category) for category in categories],
            )
            self._upsert_package(conn, jsonl_event)

        return WikiRevision(
            normalized,
            slug,
            revision,
            text,
            author,
            summary,
            now,
            receipt,
            links,
            categories,
            archive_record,
            jsonl_event,
        )

    def get_page(self, title: str, revision: int | None = None) -> WikiRevision | None:
        slug = title_slug(title)
        with self._connect() as conn:
            if revision is None:
                page = conn.execute("SELECT latest_revision FROM ene_wiki_pages WHERE slug = ?", (slug,)).fetchone()
                if not page:
                    return None
                revision = int(page["latest_revision"])
            else:
                revision = int(revision)
            row = conn.execute(
                """
                SELECT title, slug, revision, text, author, summary, created_at, receipt,
                       archive_record, jsonl_event
                FROM ene_wiki_revisions
                WHERE slug = ? AND revision = ?
                """,
                (slug, revision),
            ).fetchone()
            if not row:
                return None
            links = [
                link["target_title"]
                for link in conn.execute(
                    "SELECT target_title FROM ene_wiki_links WHERE slug = ? ORDER BY lower(target_title)",
                    (slug,),
                )
            ]
            categories = [
                cat["category"]
                for cat in conn.execute(
                    "SELECT category FROM ene_wiki_categories WHERE slug = ? ORDER BY lower(category)",
                    (slug,),
                )
            ]
            archive_record = json.loads(row["archive_record"]) if row["archive_record"] else {}
            jsonl_event = json.loads(row["jsonl_event"]) if row["jsonl_event"] else {}
        return WikiRevision(
            row["title"],
            row["slug"],
            int(row["revision"]),
            row["text"],
            row["author"],
            row["summary"],
            int(row["created_at"]),
            row["receipt"],
            links,
            categories,
            archive_record,
            jsonl_event,
        )

    def search(self, query: str, limit: int = 20) -> list[WikiPage]:
        term = f"%{query.strip()}%"
        limit = max(1, min(limit, 100))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT p.title, p.slug, p.latest_revision, p.updated_at, p.receipt
                FROM ene_wiki_pages p
                JOIN ene_wiki_revisions r
                  ON r.slug = p.slug AND r.revision = p.latest_revision
                WHERE p.title LIKE ? OR r.text LIKE ?
                ORDER BY p.updated_at DESC
                LIMIT ?
                """,
                (term, term, limit),
            ).fetchall()
        return [
            WikiPage(row["title"], row["slug"], int(row["latest_revision"]), int(row["updated_at"]), row["receipt"])
            for row in rows
        ]

    def backlinks(self, title: str) -> list[WikiPage]:
        target = title_slug(title)
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT p.title, p.slug, p.latest_revision, p.updated_at, p.receipt
                FROM ene_wiki_links l
                JOIN ene_wiki_pages p ON p.slug = l.slug
                WHERE l.target_slug = ?
                ORDER BY lower(p.title)
                """,
                (target,),
            ).fetchall()
        return [
            WikiPage(row["title"], row["slug"], int(row["latest_revision"]), int(row["updated_at"]), row["receipt"])
            for row in rows
        ]

    def recent_changes(self, limit: int = 20) -> list[WikiPage]:
        limit = max(1, min(limit, 100))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT title, slug, latest_revision, updated_at, receipt
                FROM ene_wiki_pages
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            WikiPage(row["title"], row["slug"], int(row["latest_revision"]), int(row["updated_at"]), row["receipt"])
            for row in rows
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

    parser = argparse.ArgumentParser(description="ENE wiki layer")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--op", choices=["put", "get", "search", "backlinks", "recent"], default="recent")
    parser.add_argument("--title", default="")
    parser.add_argument("--text", default="")
    parser.add_argument("--query", default="")
    parser.add_argument("--author", default="ene")
    args = parser.parse_args()

    wiki = ENEWikiLayer(args.db)
    request: dict[str, Any] = {"op": args.op, "title": args.title, "text": args.text, "query": args.query, "author": args.author}
    print(json.dumps(wiki.handle_request(request), sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
