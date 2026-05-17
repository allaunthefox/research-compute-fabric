#!/usr/bin/env python3
"""
Zotero Corpus Pipeline
======================
Reads your Zotero SQLite library, scans local PDF directories for arXiv IDs,
fetches missing metadata from arXiv API, and reconciles everything into a
unified local index.

Usage:
    python zotero_corpus_pipeline.py --scan /home/allaun/Downloads/data
    python zotero_corpus_pipeline.py --report
    python zotero_corpus_pipeline.py --reconcile
"""
import argparse
import json
import os
import re
import sqlite3
import sys
import time
import urllib.request
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

# ── Configuration ────────────────────────────────────────────────────────────
ZOTERO_DB = Path.home() / "Zotero" / "zotero.sqlite"
DEFAULT_SCAN_ROOTS = [
    Path.home() / "Downloads" / "data" / "Downloads_from_internet",
    Path.home() / "Downloads" / "data" / "literature",
    Path.home() / "Zotero" / "storage",
]
INDEX_DB = Path.home() / "Research Stack" / "data" / "substrate_index.db"

# ── Data Classes ─────────────────────────────────────────────────────────────
@dataclass
class ZoteroItem:
    item_id: int
    key: str
    item_type: str
    title: Optional[str] = None
    date: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    extra: Optional[str] = None
    creators: List[str] = field(default_factory=list)
    collections: List[str] = field(default_factory=list)

@dataclass
class LocalPDF:
    path: Path
    arxiv_id: Optional[str] = None
    title_guess: Optional[str] = None
    doi_guess: Optional[str] = None
    file_size: int = 0

@dataclass
class ArxivMeta:
    arxiv_id: str
    title: str
    authors: List[str]
    summary: str
    published: str
    updated: str
    primary_category: str
    categories: List[str]
    pdf_url: str

# ── Zotero Reader ────────────────────────────────────────────────────────────
class ZoteroReader:
    def __init__(self, db_path: Path = ZOTERO_DB):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> "ZoteroReader":
        if not self.db_path.exists():
            raise FileNotFoundError(f"Zotero DB not found: {self.db_path}")
        self.conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
        return self

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def _get_field_map(self) -> Dict[int, str]:
        assert self.conn
        cur = self.conn.execute("SELECT fieldID, fieldName FROM fields")
        return {row[0]: row[1] for row in cur.fetchall()}

    def _get_collection_map(self) -> Dict[int, str]:
        assert self.conn
        cur = self.conn.execute("SELECT collectionID, collectionName FROM collections")
        return {row[0]: row[1] for row in cur.fetchall()}

    def get_items(self, limit: Optional[int] = None) -> List[ZoteroItem]:
        assert self.conn
        field_map = self._get_field_map()
        collection_map = self._get_collection_map()

        # Pull all item metadata in one go
        query = """
            SELECT i.itemID, it.typeName, i.key, i.itemTypeID
            FROM items i
            JOIN itemTypes it ON i.itemTypeID = it.itemTypeID
            WHERE i.itemTypeID NOT IN (1, 14)
            ORDER BY i.dateAdded DESC
        """
        if limit:
            query += f" LIMIT {limit}"

        cur = self.conn.execute(query)
        items: Dict[int, ZoteroItem] = {}
        for row in cur.fetchall():
            item_id, type_name, key, _ = row
            items[item_id] = ZoteroItem(
                item_id=item_id, key=key, item_type=type_name
            )

        # Metadata values
        meta_cur = self.conn.execute(
            """
            SELECT id.itemID, id.fieldID, v.value
            FROM itemData id
            JOIN itemDataValues v ON id.valueID = v.valueID
            WHERE id.itemID IN ({})
            """.format(",".join(map(str, items.keys())))
        )
        for item_id, field_id, value in meta_cur.fetchall():
            field_name = field_map.get(field_id, "")
            item = items[item_id]
            if field_name == "title":
                item.title = value
            elif field_name == "date":
                item.date = value
            elif field_name == "DOI":
                item.doi = value
            elif field_name == "url":
                item.url = value
            elif field_name == "extra":
                item.extra = value

        # Creators
        creator_cur = self.conn.execute(
            """
            SELECT ic.itemID, c.firstName, c.lastName
            FROM itemCreators ic
            JOIN creators c ON ic.creatorID = c.creatorID
            WHERE ic.itemID IN ({})
            ORDER BY ic.orderIndex
            """.format(",".join(map(str, items.keys())))
        )
        for item_id, first, last in creator_cur.fetchall():
            name = f"{first or ''} {last or ''}".strip()
            if name:
                items[item_id].creators.append(name)

        # Collections
        col_cur = self.conn.execute(
            """
            SELECT ci.itemID, ci.collectionID
            FROM collectionItems ci
            WHERE ci.itemID IN ({})
            """.format(",".join(map(str, items.keys())))
        )
        for item_id, col_id in col_cur.fetchall():
            col_name = collection_map.get(col_id)
            if col_name:
                items[item_id].collections.append(col_name)

        return list(items.values())

    def get_stats(self) -> Dict:
        assert self.conn
        stats = {}
        cur = self.conn.execute("SELECT COUNT(*) FROM items WHERE itemTypeID NOT IN (1, 14)")
        stats["total_items"] = cur.fetchone()[0]
        cur = self.conn.execute(
            """SELECT it.typeName, COUNT(*) FROM items i
               JOIN itemTypes it ON i.itemTypeID = it.itemTypeID
               WHERE i.itemTypeID NOT IN (1, 14)
               GROUP BY it.typeName"""
        )
        stats["by_type"] = {row[0]: row[1] for row in cur.fetchall()}
        cur = self.conn.execute("SELECT COUNT(*) FROM itemAttachments")
        stats["attachments"] = cur.fetchone()[0]
        cur = self.conn.execute("SELECT COUNT(*) FROM collections")
        stats["collections"] = cur.fetchone()[0]
        return stats

# ── PDF Scanner ──────────────────────────────────────────────────────────────
class PDFScanner:
    ARXIV_RE = re.compile(r"(\d{4}\.\d{4,5}(?:v\d+)?)")
    ARXIV_FN_RE = re.compile(r"(?:ar[xX]iv[_-]?)?(\d{4}\.\d{4,5}(?:v\d+)?)")
    DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9a-z]+")

    def __init__(self, roots: List[Path]):
        self.roots = roots

    def scan(self) -> List[LocalPDF]:
        pdfs: List[LocalPDF] = []
        for root in self.roots:
            if not root.exists():
                print(f"[skip] Missing root: {root}")
                continue
            for path in root.rglob("*.pdf"):
                if not path.is_file():
                    continue
                pdf = self._analyze(path)
                pdfs.append(pdf)
        return pdfs

    def _analyze(self, path: Path) -> LocalPDF:
        name = path.stem
        # Try filename patterns first
        arxiv_match = self.ARXIV_FN_RE.search(name)
        arxiv_id = arxiv_match.group(1) if arxiv_match else None

        # Fallback: scan first 8KB of PDF for DOI/arXiv
        doi_guess = None
        if not arxiv_id:
            try:
                with open(path, "rb") as f:
                    header = f.read(8192).decode("utf-8", errors="ignore")
                    doi_match = self.DOI_RE.search(header)
                    if doi_match:
                        doi_guess = doi_match.group(0)
                    am = self.ARXIV_RE.search(header)
                    if am:
                        arxiv_id = am.group(1)
            except Exception:
                pass

        title_guess = self._clean_title(name)
        return LocalPDF(
            path=path,
            arxiv_id=arxiv_id,
            title_guess=title_guess,
            doi_guess=doi_guess,
            file_size=path.stat().st_size,
        )

    @staticmethod
    def _clean_title(filename: str) -> str:
        t = filename.replace("_", " ").replace("-", " ")
        t = re.sub(r"\b\d{4}\.\d{4,5}v?\d*\b", "", t)  # strip arxiv ids
        t = re.sub(r"\s+", " ", t).strip()
        return t

# ── arXiv API ────────────────────────────────────────────────────────────────
class ArxivClient:
    BASE = "http://export.arxiv.org/api/query"

    def fetch(self, arxiv_id: str) -> Optional[ArxivMeta]:
        # strip vN suffix for API query
        clean_id = re.sub(r"v\d+$", "", arxiv_id)
        url = f"{self.BASE}?id_list={clean_id}&max_results=1"
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                xml = resp.read().decode("utf-8")
            return self._parse(xml, arxiv_id)
        except Exception as e:
            print(f"[arxiv] Failed to fetch {arxiv_id}: {e}")
            return None

    def _parse(self, xml: str, original_id: str) -> Optional[ArxivMeta]:
        import xml.etree.ElementTree as ET
        ns = {"atom": "http://www.w3.org/2005/Atom",
              "arxiv": "http://arxiv.org/schemas/atom"}
        root = ET.fromstring(xml)
        entry = root.find("atom:entry", ns)
        if entry is None:
            return None
        def tag(t): return entry.find(f"atom:{t}", ns)
        title = (tag("title") or entry.find("title")).text.strip()
        summary = (tag("summary") or entry.find("summary")).text.strip()
        published = (tag("published") or entry.find("published")).text.strip()
        updated_el = tag("updated") or entry.find("updated")
        updated = updated_el.text.strip() if updated_el is not None else published
        authors = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)]
        cat_el = entry.find("arxiv:primary_category", ns)
        primary = cat_el.attrib.get("term", "") if cat_el is not None else ""
        cats = [c.attrib.get("term", "") for c in entry.findall("atom:category", ns)]
        pdf_url = f"https://arxiv.org/pdf/{original_id}.pdf"
        return ArxivMeta(
            arxiv_id=original_id,
            title=title,
            authors=authors,
            summary=summary,
            published=published,
            updated=updated,
            primary_category=primary,
            categories=cats,
            pdf_url=pdf_url,
        )

# ── Index Manager ────────────────────────────────────────────────────────────
class IndexManager:
    SCHEMA = """
    CREATE TABLE IF NOT EXISTS zotero_items (
        zotero_key TEXT PRIMARY KEY,
        item_id INTEGER,
        item_type TEXT,
        title TEXT,
        date TEXT,
        doi TEXT,
        url TEXT,
        extra TEXT,
        creators TEXT,   -- JSON list
        collections TEXT -- JSON list
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
        authors TEXT, -- JSON list
        summary TEXT,
        published TEXT,
        updated TEXT,
        primary_category TEXT,
        categories TEXT, -- JSON list
        pdf_url TEXT
    );

    CREATE TABLE IF NOT EXISTS reconciler_log (
        run_time TEXT,
        zotero_count INTEGER,
        pdf_count INTEGER,
        matched_count INTEGER,
        unmatched_pdf_count INTEGER,
        notes TEXT
    );
    """

    def __init__(self, db_path: Path = INDEX_DB):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.executescript(self.SCHEMA)
        self.conn.commit()

    def close(self):
        self.conn.close()

    def sync_zotero(self, items: List[ZoteroItem]):
        with self.conn:
            self.conn.execute("DELETE FROM zotero_items")
            for it in items:
                self.conn.execute(
                    """INSERT INTO zotero_items VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (
                        it.key,
                        it.item_id,
                        it.item_type,
                        it.title,
                        it.date,
                        it.doi,
                        it.url,
                        it.extra,
                        json.dumps(it.creators),
                        json.dumps(it.collections),
                    ),
                )

    def sync_pdfs(self, pdfs: List[LocalPDF]):
        seen: Set[str] = set()
        with self.conn:
            self.conn.execute("DELETE FROM local_pdfs")
            for p in pdfs:
                path_str = str(p.path)
                if path_str in seen:
                    continue
                seen.add(path_str)
                self.conn.execute(
                    """INSERT INTO local_pdfs (path, arxiv_id, title_guess, doi_guess, file_size)
                       VALUES (?,?,?,?,?)""",
                    (path_str, p.arxiv_id, p.title_guess, p.doi_guess, p.file_size),
                )

    def store_arxiv_meta(self, meta: ArxivMeta):
        with self.conn:
            self.conn.execute(
                """INSERT OR REPLACE INTO arxiv_meta VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    meta.arxiv_id,
                    meta.title,
                    json.dumps(meta.authors),
                    meta.summary,
                    meta.published,
                    meta.updated,
                    meta.primary_category,
                    json.dumps(meta.categories),
                    meta.pdf_url,
                ),
            )

    def reconcile(self) -> Dict:
        """Match local PDFs to Zotero items by DOI or arXiv ID."""
        with self.conn:
            # Match by DOI
            self.conn.execute(
                """UPDATE local_pdfs
                   SET zotero_key = (
                       SELECT zotero_key FROM zotero_items
                       WHERE zotero_items.doi = local_pdfs.doi_guess
                       LIMIT 1
                   )
                   WHERE doi_guess IS NOT NULL"""
            )
            # Match by arXiv ID in URL or extra
            self.conn.execute(
                """UPDATE local_pdfs
                   SET zotero_key = (
                       SELECT z.zotero_key FROM zotero_items z
                       WHERE (z.url LIKE '%' || local_pdfs.arxiv_id || '%'
                              OR z.extra LIKE '%' || local_pdfs.arxiv_id || '%')
                       LIMIT 1
                   )
                   WHERE arxiv_id IS NOT NULL AND zotero_key IS NULL"""
            )
            # Match by title similarity (naive)
            self.conn.execute(
                """UPDATE local_pdfs
                   SET zotero_key = (
                       SELECT z.zotero_key FROM zotero_items z
                       WHERE z.title IS NOT NULL
                         AND local_pdfs.title_guess IS NOT NULL
                         AND lower(trim(z.title)) = lower(trim(local_pdfs.title_guess))
                       LIMIT 1
                   )
                   WHERE zotero_key IS NULL"""
            )

        cur = self.conn.execute("SELECT COUNT(*) FROM zotero_items")
        z_count = cur.fetchone()[0]
        cur = self.conn.execute("SELECT COUNT(*) FROM local_pdfs")
        p_count = cur.fetchone()[0]
        cur = self.conn.execute(
            "SELECT COUNT(DISTINCT zotero_key) FROM local_pdfs WHERE zotero_key IS NOT NULL"
        )
        matched = cur.fetchone()[0]
        cur = self.conn.execute(
            "SELECT COUNT(*) FROM local_pdfs WHERE zotero_key IS NULL"
        )
        unmatched = cur.fetchone()[0]
        return {
            "zotero_items": z_count,
            "local_pdfs": p_count,
            "matched_pdfs": matched,
            "unmatched_pdfs": unmatched,
        }

    def report(self) -> str:
        lines = []
        cur = self.conn.execute("SELECT * FROM zotero_items LIMIT 10")
        lines.append("== Sample Zotero Items ==")
        for row in cur.fetchall():
            lines.append(f"  {row[0]} | {row[3]} | {row[8]}")

        cur = self.conn.execute(
            "SELECT path, arxiv_id, zotero_key FROM local_pdfs LIMIT 10"
        )
        lines.append("\n== Sample Local PDFs ==")
        for row in cur.fetchall():
            lines.append(f"  {Path(row[0]).name} | arXiv:{row[1]} | Zotero:{row[2]}")

        cur = self.conn.execute(
            "SELECT arxiv_id, title FROM arxiv_meta LIMIT 10"
        )
        lines.append("\n== Cached arXiv Metadata ==")
        for row in cur.fetchall():
            lines.append(f"  {row[0]} | {row[1][:60]}")

        cur = self.conn.execute(
            """SELECT zotero_key, COUNT(*) FROM local_pdfs
               WHERE zotero_key IS NOT NULL GROUP BY zotero_key ORDER BY COUNT(*) DESC LIMIT 5"""
        )
        lines.append("\n== PDFs per Zotero Item (top 5) ==")
        for row in cur.fetchall():
            lines.append(f"  {row[0]}: {row[1]} PDFs")

        return "\n".join(lines)

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Zotero Corpus Pipeline")
    parser.add_argument("--scan", nargs="*", help="Extra directories to scan for PDFs")
    parser.add_argument("--report", action="store_true", help="Print index report")
    parser.add_argument("--reconcile", action="store_true", help="Run reconciler")
    parser.add_argument("--fetch-arxiv", action="store_true", help="Fetch arXiv metadata for unmatched PDFs")
    parser.add_argument("--stats", action="store_true", help="Print Zotero stats")
    args = parser.parse_args()

    # 1. Read Zotero
    print("[1/4] Connecting to Zotero...")
    zr = ZoteroReader().connect()
    if args.stats:
        stats = zr.get_stats()
        print(json.dumps(stats, indent=2))
        zr.close()
        return

    items = zr.get_items()
    print(f"  -> {len(items)} Zotero items loaded")

    # 2. Scan PDFs
    print("[2/4] Scanning local PDF corpus...")
    roots = list(DEFAULT_SCAN_ROOTS)
    if args.scan:
        roots += [Path(p) for p in args.scan]
    scanner = PDFScanner(roots)
    pdfs = scanner.scan()
    print(f"  -> {len(pdfs)} PDFs found")

    # 3. Update index
    print("[3/4] Writing index...")
    idx = IndexManager()
    idx.sync_zotero(items)
    idx.sync_pdfs(pdfs)

    # 4. Reconcile
    if args.reconcile:
        print("[4/4] Reconciling...")
        rec = idx.reconcile()
        print(f"  -> {rec['matched_pdfs']} matched, {rec['unmatched_pdfs']} unmatched")

    # 5. Fetch arXiv metadata for unmatched PDFs with arxiv_id
    if args.fetch_arxiv:
        print("[5/5] Fetching arXiv metadata...")
        client = ArxivClient()
        cur = idx.conn.execute(
            """SELECT arxiv_id FROM local_pdfs
               WHERE arxiv_id IS NOT NULL
                 AND zotero_key IS NULL
                 AND arxiv_id NOT IN (SELECT arxiv_id FROM arxiv_meta)"""
        )
        missing = [row[0] for row in cur.fetchall()]
        print(f"  -> {len(missing)} missing metadata records")
        for i, aid in enumerate(missing, 1):
            meta = client.fetch(aid)
            if meta:
                idx.store_arxiv_meta(meta)
            if i % 10 == 0:
                print(f"      ...{i}/{len(missing)} fetched")
            time.sleep(3)  # be polite to arXiv

    if args.report:
        print(idx.report())

    idx.close()
    zr.close()
    print("Done.")

if __name__ == "__main__":
    main()
