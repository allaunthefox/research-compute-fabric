#!/usr/bin/env python3
"""
ScienceHub MCP Server — Sovereign Research Surface
==================================================
An MCP server that lets an LLM say "I need X" and automatically:
  1. Searches your local corpus (Zotero + PDFs)
  2. If missing, fetches from arXiv / Semantic Scholar
  3. Ingests into Zotero + local storage
  4. Returns a review/abstract

Usage (for Claude Desktop / Cline / etc):
    {
      "mcpServers": {
        "sciencehub": {
          "command": "python3",
          "args": ["/home/allaun/Documents/Research Stack/scripts/sciencehub_mcp.py"]
        }
      }
    }

Tools:
    - need            : "I need <topic>" → full pipeline
    - search_local    : Query local corpus index
    - fetch_arxiv     : Download + cache arXiv PDF
    - ingest_to_zotero: Import a PDF into Zotero SQLite
    - review_paper    : Extract metadata + quick review from PDF
    - corpus_report   : Get state of the local research library
"""

import argparse
import asyncio
import json
import os
import random
import re
import shutil
import sqlite3
import string
import sys
import textwrap
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Paths ─────────────────────────────────────────────────────────────────────
RESEARCH_STACK = Path("/home/allaun/Documents/Research Stack")
ZOTERO_DB = Path.home() / "Zotero" / "zotero.sqlite"
INDEX_DB = Path.home() / "Research Stack" / "data" / "substrate_index.db"
INGEST_DIR = Path.home() / "Downloads" / "data" / "Downloads_from_internet" / "Deep Research"
ARXIV_CACHE = INGEST_DIR / "alphaXiv_PDFs_2026_04"

# Ensure dirs exist
INGEST_DIR.mkdir(parents=True, exist_ok=True)
ARXIV_CACHE.mkdir(parents=True, exist_ok=True)

# ── MCP SDK (optional — graceful fallback) ────────────────────────────────────
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    HAS_MCP = True
except ImportError:
    HAS_MCP = False
    print("[warn] MCP SDK not installed. Running in CLI mode.", file=sys.stderr)

# ── Data classes ─────────────────────────────────────────────────────────────
@dataclass
class Paper:
    title: str
    authors: List[str] = field(default_factory=list)
    abstract: str = ""
    url: str = ""
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None
    local_path: Optional[Path] = None
    year: Optional[str] = None

# ── arXiv Client ─────────────────────────────────────────────────────────────
class ArxivClient:
    BASE_QUERY = "https://export.arxiv.org/api/query"
    BASE_PDF = "https://arxiv.org/pdf"
    STOP_WORDS = {
        "i", "need", "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "must", "shall", "can", "all", "you",
        "we", "they", "it", "this", "that", "these", "those", "of", "in", "on",
        "at", "to", "for", "with", "about", "against", "between", "into", "through",
        "during", "before", "after", "above", "below", "from", "up", "down", "out",
        "off", "over", "under", "again", "further", "then", "once", "and", "or",
        "but", "if", "then", "else", "because", "until", "while", "so", "than",
        "too", "very", "just", "now", "only", "also", "its", "his", "her", "their",
        "our", "my", "your", "what", "which", "who", "when", "where", "why", "how",
        "paper", "survey", "review", "article", "study", "work",
    }

    def search(self, query: str, max_results: int = 5) -> List[Paper]:
        """Search arXiv and return Paper objects."""
        words = re.sub(r'[^\w\s]', ' ', query).lower().split()
        keywords = [w for w in words if w not in self.STOP_WORDS][:3]
        if not keywords:
            keywords = words[:3]
        raw_query = "+AND+".join(f"ti:{urllib.parse.quote(w)}" for w in keywords)
        url = f"{self.BASE_QUERY}?search_query={raw_query}&max_results={max_results}&sortBy=relevance&sortOrder=descending"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ScienceHub/0.1"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                xml = resp.read().decode("utf-8")
            return self._parse_feed(xml)
        except Exception as e:
            return [Paper(title=f"[ERROR] arXiv search failed: {e}", url=url)]

    def _parse_feed(self, xml: str) -> List[Paper]:
        import xml.etree.ElementTree as ET
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
        root = ET.fromstring(xml)
        papers: List[Paper] = []
        for entry in root.findall("atom:entry", ns):
            id_el = entry.find("atom:id", ns)
            if id_el is None:
                continue
            arxiv_url = id_el.text.strip()
            arxiv_id = arxiv_url.split("/")[-1]
            title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
            summary = entry.find("atom:summary", ns).text.strip().replace("\n", " ")
            authors = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)]
            published = entry.find("atom:published", ns).text[:4]
            pdf_url = f"{self.BASE_PDF}/{arxiv_id}.pdf"
            papers.append(Paper(
                title=title, authors=authors, abstract=summary,
                url=arxiv_url, arxiv_id=arxiv_id, year=published,
            ))
        return papers

    def download(self, arxiv_id: str, dest: Path) -> Path:
        """Download PDF to dest. Returns path to temp file."""
        clean = re.sub(r"v\d+$", "", arxiv_id)
        pdf_url = f"{self.BASE_PDF}/{clean}.pdf"
        out_temp = dest / f"{clean}.pdf"
        try:
            urllib.request.urlretrieve(pdf_url, str(out_temp))
            if out_temp.stat().st_size < 1024:
                raise RuntimeError("Downloaded file is too small (likely an error page)")
            return out_temp
        except Exception as e:
            if out_temp.exists():
                out_temp.unlink()
            raise RuntimeError(f"Failed to download {pdf_url}: {e}")

    @staticmethod
    def slug(title: str, arxiv_id: str, max_len: int = 80) -> str:
        """Create a safe filename slug from a paper title + arXiv ID."""
        # Transliterate common math symbols
        replacements = {
            "\\": " ", "$": "", "^": "", "_": " ",
            "{": "", "}": "", "~": " ", "%": "pct",
            "&": "and", "#": "", "@": "at", "≈": "approx",
            "∞": "inf", "∈": "in", "∀": "forall", "∃": "exists",
            "∂": "d", "∇": "nabla", "α": "alpha", "β": "beta",
            "γ": "gamma", "δ": "delta", "ε": "epsilon", "ζ": "zeta",
            "η": "eta", "θ": "theta", "ι": "iota", "κ": "kappa",
            "λ": "lambda", "μ": "mu", "ν": "nu", "ξ": "xi",
            "π": "pi", "ρ": "rho", "σ": "sigma", "τ": "tau",
            "φ": "phi", "χ": "chi", "ψ": "psi", "ω": "omega",
            "Γ": "Gamma", "Δ": "Delta", "Θ": "Theta", "Λ": "Lambda",
            "Ξ": "Xi", "Π": "Pi", "Σ": "Sigma", "Φ": "Phi",
            "Ψ": "Psi", "Ω": "Omega",
            "→": "to", "←": "from", "⇒": "implies", "⇔": "iff",
            "×": "x", "÷": "div", "±": "pm", "∓": "mp",
            "≤": "le", "≥": "ge", "≠": "ne", "≡": "equiv",
            "∼": "sim", "≅": "cong", "⊂": "subset", "⊃": "supset",
            "⊆": "subeq", "⊇": "supeq", "∪": "union", "∩": "inter",
            "∧": "and", "∨": "or", "¬": "not", "⊕": "xor",
        }
        t = title
        for old, new in replacements.items():
            t = t.replace(old, new)
        # Keep only safe chars
        t = re.sub(r"[^\w\s-]", "", t)
        # Collapse whitespace and dashes to single underscores
        t = re.sub(r"[-\s]+", "_", t)
        t = t.strip("_")
        t = t[:max_len]
        t = t.strip("_")
        if not t:
            t = "paper"
        return f"{arxiv_id}_{t}.pdf"

# ── Zotero Writer ────────────────────────────────────────────────────────────
class ZoteroWriter:
    """Safe read+write helper for Zotero SQLite."""
    def __init__(self, db_path: Path = ZOTERO_DB):
        self.db_path = db_path

    def _backup(self):
        ts = time.strftime("%Y%m%d_%H%M%S")
        backup = self.db_path.with_suffix(f".sqlite.backup.{ts}")
        shutil.copy2(str(self.db_path), str(backup))
        return backup

    def _get_next_item_id(self, conn: sqlite3.Connection) -> int:
        cur = conn.execute("SELECT MAX(itemID) FROM items")
        max_id = cur.fetchone()[0] or 0
        return max_id + 1

    def _get_field_id(self, conn: sqlite3.Connection, field_name: str) -> int:
        cur = conn.execute("SELECT fieldID FROM fields WHERE fieldName = ?", (field_name,))
        row = cur.fetchone()
        if row:
            return row[0]
        cur = conn.execute("INSERT INTO fields (fieldName) VALUES (?) RETURNING fieldID", (field_name,))
        return cur.fetchone()[0]

    def _get_or_create_value(self, conn: sqlite3.Connection, value: str) -> int:
        cur = conn.execute("SELECT valueID FROM itemDataValues WHERE value = ?", (value,))
        row = cur.fetchone()
        if row:
            return row[0]
        cur = conn.execute(
            "INSERT INTO itemDataValues (value) VALUES (?) RETURNING valueID", (value,)
        )
        return cur.fetchone()[0]

    def add_preprint(self, paper: Paper, collection_name: str = "Research Stack") -> str:
        """Insert a paper as a 'preprint' item into Zotero. Returns the new key."""
        key = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        backup_path = self._backup()

        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                item_id = self._get_next_item_id(conn)
                cur = conn.execute("SELECT itemTypeID FROM itemTypes WHERE typeName = 'preprint'")
                row = cur.fetchone()
                preprint_type_id = row[0] if row else 22

                conn.execute(
                    """INSERT INTO items (itemID, itemTypeID, dateAdded, dateModified, clientDateModified, libraryID, key, version, synced)
                       VALUES (?, ?, datetime('now'), datetime('now'), datetime('now'), 1, ?, 0, 0)""",
                    (item_id, preprint_type_id, key),
                )

                meta_fields = {"title": paper.title, "url": paper.url, "extra": paper.arxiv_id or ""}
                if paper.year:
                    meta_fields["date"] = paper.year
                if paper.doi:
                    meta_fields["DOI"] = paper.doi

                for field_name, val in meta_fields.items():
                    if not val:
                        continue
                    fid = self._get_field_id(conn, field_name)
                    vid = self._get_or_create_value(conn, val)
                    conn.execute(
                        "INSERT INTO itemData (itemID, fieldID, valueID) VALUES (?,?,?)",
                        (item_id, fid, vid),
                    )

                # Authors
                for i, author in enumerate(paper.authors[:20]):
                    # Handle "collaboration" style names
                    author = author.strip()
                    if not author:
                        continue
                    # Try to split last name from first names
                    if "," in author:
                        parts = [p.strip() for p in author.split(",", 1)]
                        last, first = parts[0], parts[1] if len(parts) > 1 else ""
                    else:
                        parts = author.split()
                        last = parts[-1] if parts else ""
                        first = " ".join(parts[:-1]) if len(parts) > 1 else ""

                    cur = conn.execute(
                        "SELECT creatorID FROM creators WHERE firstName = ? AND lastName = ? AND fieldMode = ?",
                        (first, last, 0),
                    )
                    row = cur.fetchone()
                    if row:
                        creator_id = row[0]
                    else:
                        cur = conn.execute(
                            "INSERT INTO creators (firstName, lastName, fieldMode) VALUES (?,?,?) RETURNING creatorID",
                            (first, last, 0),
                        )
                        creator_id = cur.fetchone()[0]
                    conn.execute(
                        "INSERT INTO itemCreators (itemID, creatorID, creatorTypeID, orderIndex) VALUES (?,?,1,?)",
                        (item_id, creator_id, i),
                    )

                # Collection
                cur = conn.execute(
                    "SELECT collectionID FROM collections WHERE collectionName = ?", (collection_name,)
                )
                row = cur.fetchone()
                if row:
                    col_id = row[0]
                else:
                    cur = conn.execute(
                        """INSERT INTO collections (collectionName, parentCollectionID, libraryID, key, version, synced, clientDateModified)
                            VALUES (?, NULL, 1, ?, 0, 0, datetime('now')) RETURNING collectionID""",
                        (collection_name, key),
                    )
                    col_id = cur.fetchone()[0]

                cur = conn.execute(
                    "SELECT COALESCE(MAX(orderIndex), -1) + 1 FROM collectionItems WHERE collectionID = ?",
                    (col_id,),
                )
                order_idx = cur.fetchone()[0]
                conn.execute(
                    "INSERT INTO collectionItems (collectionID, itemID, orderIndex) VALUES (?,?,?)",
                    (col_id, item_id, order_idx),
                )

                conn.commit()
            return key
        except Exception:
            # On any failure, restore backup and re-raise
            shutil.copy2(str(backup_path), str(self.db_path))
            raise

# ── Local Corpus Index ───────────────────────────────────────────────────────
class CorpusIndex:
    def __init__(self, db_path: Path = INDEX_DB):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _ensure_schema(self):
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS zotero_items (
                    zotero_key TEXT PRIMARY KEY,
                    item_id INTEGER,
                    item_type TEXT,
                    title TEXT,
                    date TEXT,
                    doi TEXT,
                    url TEXT,
                    extra TEXT,
                    creators TEXT,
                    collections TEXT
                );
                CREATE TABLE IF NOT EXISTS local_pdfs (
                    path TEXT PRIMARY KEY,
                    arxiv_id TEXT,
                    title_guess TEXT,
                    doi_guess TEXT,
                    file_size INTEGER,
                    zotero_key TEXT,
                    metadata_fetched INTEGER DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS arxiv_meta (
                    arxiv_id TEXT PRIMARY KEY,
                    title TEXT,
                    authors TEXT,
                    summary TEXT,
                    published TEXT,
                    updated TEXT,
                    primary_category TEXT,
                    categories TEXT,
                    pdf_url TEXT
                );
                CREATE TABLE IF NOT EXISTS need_log (
                    need_id INTEGER PRIMARY KEY,
                    query TEXT,
                    status TEXT,
                    result TEXT,
                    zotero_key TEXT,
                    local_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_pdf_arxiv ON local_pdfs(arxiv_id);
                CREATE INDEX IF NOT EXISTS idx_zotero_title ON zotero_items(title);
                CREATE INDEX IF NOT EXISTS idx_need_query ON need_log(query);
            """)

    def search(self, query: str, limit: int = 10) -> Dict:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            q = f"%{query}%"
            cur = conn.execute(
                """SELECT z.* FROM zotero_items z
                   WHERE z.title LIKE ? OR z.doi LIKE ? OR z.url LIKE ? OR z.extra LIKE ?
                   LIMIT ?""",
                (q, q, q, q, limit),
            )
            zotero = [dict(r) for r in cur.fetchall()]
            cur = conn.execute(
                """SELECT p.* FROM local_pdfs p
                   WHERE p.title_guess LIKE ? OR p.arxiv_id LIKE ? OR p.doi_guess LIKE ?
                   LIMIT ?""",
                (q, q, q, limit),
            )
            pdfs = [dict(r) for r in cur.fetchall()]
            cur = conn.execute(
                """SELECT * FROM arxiv_meta
                   WHERE title LIKE ? OR summary LIKE ? OR arxiv_id LIKE ?
                   LIMIT ?""",
                (q, q, q, limit),
            )
            arxiv = [dict(r) for r in cur.fetchall()]
        return {"zotero": zotero, "pdfs": pdfs, "arxiv_meta": arxiv}

    def log_need(self, query: str, status: str, result: str,
                 zotero_key: Optional[str] = None, local_path: Optional[str] = None):
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                "INSERT INTO need_log (query, status, result, zotero_key, local_path) VALUES (?,?,?,?,?)",
                (query, status, result, zotero_key, local_path),
            )
            conn.commit()

    def stats(self) -> Dict:
        with sqlite3.connect(str(self.db_path)) as conn:
            cur = conn.execute("SELECT COUNT(*) FROM zotero_items")
            z = cur.fetchone()[0]
            cur = conn.execute("SELECT COUNT(*) FROM local_pdfs")
            p = cur.fetchone()[0]
            cur = conn.execute("SELECT COUNT(*) FROM arxiv_meta")
            a = cur.fetchone()[0]
            cur = conn.execute("SELECT COUNT(*) FROM need_log WHERE status = 'completed'")
            completed = cur.fetchone()[0]
            cur = conn.execute("SELECT COUNT(*) FROM need_log WHERE status = 'failed'")
            failed = cur.fetchone()[0]
        return {"zotero_items": z, "local_pdfs": p, "arxiv_cached": a,
                "needs_completed": completed, "needs_failed": failed}

# ── ScienceHub Engine ────────────────────────────────────────────────────────
class ScienceHub:
    def __init__(self):
        self.index = CorpusIndex()
        self.arxiv = ArxivClient()
        self.zotero = ZoteroWriter()

    async def need(self, query: str, auto_ingest: bool = True) -> str:
        """
        The main 'I need X' pipeline.
        Returns a human-readable report of what was found / fetched / ingested.
        """
        # Strip natural-language wrappers like "I need ..."
        raw_query = re.sub(r"^(i\s+)?need\s+", "", query, flags=re.IGNORECASE).strip()
        if not raw_query:
            raw_query = query

        report_lines = [f"🔬  ScienceHub Need Pipeline: '{raw_query}'", "=" * 50]

        # 1. Search local
        local = self.index.search(raw_query, limit=5)
        local_total = sum(len(v) for v in local.values())
        report_lines.append(f"📚  Local corpus: {local_total} matches")
        if local["zotero"]:
            report_lines.append("   Zotero hits:")
            for z in local["zotero"][:3]:
                report_lines.append(f"      • {z.get('title', 'Untitled')}")
        if local["pdfs"]:
            report_lines.append("   PDF hits:")
            for p in local["pdfs"][:3]:
                report_lines.append(f"      • {Path(p['path']).name}")

        # 2. If nothing local, fetch from arXiv
        if local_total == 0:
            report_lines.append("\n🌐  Nothing local. Searching arXiv...")
            papers = self.arxiv.search(raw_query, max_results=3)
            if not papers or papers[0].title.startswith("[ERROR]"):
                err = papers[0].title if papers else "No results"
                self.index.log_need(raw_query, "failed", err)
                return "\n".join(report_lines + [f"\n❌  arXiv search failed: {err}"])

            best = papers[0]
            report_lines.append(f"   Found: {best.title}")
            report_lines.append(f"   Authors: {', '.join(best.authors[:3])}")
            report_lines.append(f"   arXiv: {best.arxiv_id}")
            if best.abstract:
                snippet = textwrap.shorten(best.abstract, width=300, placeholder="...")
                report_lines.append(f"   Abstract: {snippet}")

            # 3. Download
            if auto_ingest and best.arxiv_id:
                try:
                    dl_path = self.arxiv.download(best.arxiv_id, ARXIV_CACHE)
                    best.local_path = dl_path
                    # Rename with safe slug
                    new_name = ARXIV_CACHE / self.arxiv.slug(best.title, best.arxiv_id)
                    dl_path.rename(new_name)
                    best.local_path = new_name
                    report_lines.append(f"\n💾  Downloaded to: {new_name}")
                except Exception as e:
                    report_lines.append(f"\n⚠️  Download failed: {e}")
                    self.index.log_need(raw_query, "failed", str(e))
                    return "\n".join(report_lines)

                # 4. Ingest to Zotero
                try:
                    zkey = self.zotero.add_preprint(best, collection_name="Research Stack")
                    report_lines.append(f"📥  Ingested to Zotero with key: {zkey}")
                except Exception as e:
                    report_lines.append(f"⚠️  Zotero ingest failed: {e}")
                    zkey = None

                # 5. Log success
                self.index.log_need(
                    raw_query, "completed", best.title, zotero_key=zkey,
                    local_path=str(best.local_path) if best.local_path else None,
                )
                report_lines.append("\n✅  Pipeline complete. Paper is now in your library.")
            else:
                report_lines.append("\n⏸️  auto_ingest=False — paper found but not downloaded.")
                self.index.log_need(raw_query, "found_only", best.title)
        else:
            report_lines.append("\n✅  Already in your corpus. No action needed.")
            self.index.log_need(raw_query, "local_hit", f"{local_total} matches")

        return "\n".join(report_lines)

    def review(self, pdf_path: str) -> str:
        """Quick review of a PDF using pdfinfo / pdftotext."""
        path = Path(pdf_path)
        if not path.exists():
            return f"❌  File not found: {pdf_path}"
        lines = [f"📄  Review: {path.name}"]
        try:
            import subprocess
            info = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True, timeout=10)
            if info.returncode == 0:
                lines.append(info.stdout[:800])
            else:
                lines.append("[pdfinfo failed]")
        except Exception as e:
            lines.append(f"[pdfinfo error: {e}]")
        try:
            text = subprocess.run(["pdftotext", "-l", "1", str(path), "-"],
                                  capture_output=True, text=True, timeout=10)
            if text.returncode == 0:
                first_page = text.stdout[:1200].strip()
                lines.append("\n📝  First page excerpt:")
                lines.append(textwrap.shorten(first_page, width=1200, placeholder="..."))
        except Exception as e:
            lines.append(f"[pdftotext error: {e}]")
        return "\n".join(lines)

    def report(self) -> str:
        s = self.index.stats()
        lines = [
            "📊  ScienceHub Corpus Report",
            "=" * 40,
            f"Zotero items indexed:   {s['zotero_items']}",
            f"Local PDFs tracked:     {s['local_pdfs']}",
            f"arXiv metadata cached:  {s['arxiv_cached']}",
            f"Needs completed:        {s['needs_completed']}",
            f"Needs failed:           {s['needs_failed']}",
        ]
        return "\n".join(lines)

# ── MCP Server ───────────────────────────────────────────────────────────────
def build_mcp_app():
    hub = ScienceHub()
    server = Server("sciencehub")

    @server.list_tools()
    async def list_tools() -> List[Tool]:
        return [
            Tool(
                name="need",
                description="I need <topic>. Searches local corpus, fetches from arXiv if missing, ingests to Zotero, and returns a review.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "What paper or topic you need"},
                        "auto_ingest": {"type": "boolean", "default": True,
                                        "description": "Whether to download and add to Zotero"},
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="search_local",
                description="Search your local research corpus (Zotero + PDFs + arXiv cache).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "integer", "default": 10},
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="fetch_arxiv",
                description="Download a specific arXiv paper by ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "arxiv_id": {"type": "string"},
                        "ingest": {"type": "boolean", "default": True},
                    },
                    "required": ["arxiv_id"],
                },
            ),
            Tool(
                name="review_paper",
                description="Generate a quick review of a local PDF (metadata + first page).",
                inputSchema={
                    "type": "object",
                    "properties": {"path": {"type": "string", "description": "Absolute path to PDF"}},
                    "required": ["path"],
                },
            ),
            Tool(
                name="corpus_report",
                description="Get statistics about your local research library.",
                inputSchema={"type": "object", "properties": {}},
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[Any]:
        try:
            if name == "need":
                result = await hub.need(arguments["query"], arguments.get("auto_ingest", True))
                return [TextContent(type="text", text=result)]

            elif name == "search_local":
                q = arguments["query"]
                limit = arguments.get("limit", 10)
                hits = hub.index.search(q, limit)
                total = sum(len(v) for v in hits.values())
                lines = [f"🔍  Local search for '{q}': {total} hits", "=" * 40]
                for section, items in hits.items():
                    if items:
                        lines.append(f"\n📂  {section} ({len(items)})")
                        for it in items[:5]:
                            title = it.get("title") or it.get("title_guess") or Path(it.get("path", "unknown")).name
                            lines.append(f"   • {title}")
                return [TextContent(type="text", text="\n".join(lines))]

            elif name == "fetch_arxiv":
                aid = arguments["arxiv_id"]
                ingest = arguments.get("ingest", True)
                papers = hub.arxiv.search(f"id:{aid}", max_results=1)
                if not papers or papers[0].title.startswith("[ERROR]"):
                    return [TextContent(type="text", text=f"❌  Could not resolve arXiv:{aid}")]
                p = papers[0]
                if ingest:
                    dl = hub.arxiv.download(aid, ARXIV_CACHE)
                    p.local_path = dl
                    new_name = ARXIV_CACHE / hub.arxiv.slug(p.title, aid)
                    dl.rename(new_name)
                    p.local_path = new_name
                    zkey = hub.zotero.add_preprint(p, collection_name="Research Stack")
                    return [TextContent(type="text",
                                        text=f"✅  Fetched & ingested arXiv:{aid}\nTitle: {p.title}\n"
                                             f"Zotero key: {zkey}\nPath: {new_name}")]
                else:
                    return [TextContent(type="text",
                                        text=f"✅  Found arXiv:{aid}\nTitle: {p.title}\n"
                                             f"Authors: {', '.join(p.authors[:3])}\n"
                                             "(Abstract only — ingest=False)")]

            elif name == "review_paper":
                result = hub.review(arguments["path"])
                return [TextContent(type="text", text=result)]

            elif name == "corpus_report":
                return [TextContent(type="text", text=hub.report())]

            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error in {name}: {e}")]

    return server

# ── CLI Fallback ───────────────────────────────────────────────────────────────
def cli_main():
    hub = ScienceHub()
    parser = argparse.ArgumentParser(description="ScienceHub — Sovereign Research Surface")
    parser.add_argument("need", nargs="?", help="What you need (e.g. 'I need attention mechanism survey')")
    parser.add_argument("--search", help="Search local corpus")
    parser.add_argument("--fetch", help="Fetch arXiv ID")
    parser.add_argument("--review", help="Review a PDF path")
    parser.add_argument("--report", action="store_true", help="Corpus report")
    parser.add_argument("--no-ingest", action="store_true", help="Skip Zotero ingest for --need")
    args = parser.parse_args()

    if args.need:
        result = asyncio.run(hub.need(args.need, auto_ingest=not args.no_ingest))
        print(result)
    elif args.search:
        hits = hub.index.search(args.search, limit=10)
        print(json.dumps(hits, indent=2, default=str))
    elif args.fetch:
        papers = hub.arxiv.search(f"id:{args.fetch}", max_results=1)
        if papers:
            print(f"Title: {papers[0].title}")
            print(f"Abstract: {papers[0].abstract[:500]}...")
            dl = hub.arxiv.download(args.fetch, ARXIV_CACHE)
            new_name = ARXIV_CACHE / hub.arxiv.slug(papers[0].title, args.fetch)
            dl.rename(new_name)
            print(f"Downloaded to: {new_name}")
    elif args.review:
        print(hub.review(args.review))
    elif args.report:
        print(hub.report())
    else:
        parser.print_help()

# ── Entrypoint ───────────────────────────────────────────────────────────────
async def mcp_main():
    server = build_mcp_app()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    if HAS_MCP and len(sys.argv) == 1:
        asyncio.run(mcp_main())
    else:
        cli_main()
