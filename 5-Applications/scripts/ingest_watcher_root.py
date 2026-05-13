#!/usr/bin/env python3
"""
Smart Ingest Watcher (Daemon)
=============================
Monitors watched directories for new PDFs. On detection:
  1. Extract arXiv ID / DOI from filename + PDF header
  2. Fetch metadata from arXiv API if arXiv ID found
  3. Ingest into Zotero with proper metadata
  4. Move to the canonical archive directory
  5. Log everything to the index

Usage:
    # Run once (foreground, dry-run)
    python3 ingest_watcher.py --once --dry-run

    # Run as daemon
    python3 ingest_watcher.py --daemon

    # Add a watch directory
    python3 ingest_watcher.py --watch ~/Downloads --daemon
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

# ── Paths ─────────────────────────────────────────────────────────────────────
ZOTERO_DB = Path.home() / "Zotero" / "zotero.sqlite"
INDEX_DB = Path.home() / "Research Stack" / "data" / "substrate_index.db"
CANONICAL_DIR = Path.home() / "Downloads" / "data" / "Downloads_from_internet" / "Deep Research" / "alphaXiv_PDFs_2026_04"
STATE_FILE = Path.home() / "Research Stack" / "data" / "ingest_watcher_state.json"
LOG_FILE = Path.home() / "Research Stack" / "data" / "ingest_watcher.log"

CANONICAL_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

# ── Config ────────────────────────────────────────────────────────────────────
DEFAULT_WATCH_DIRS = [
    str(Path.home() / "Downloads"),
    str(Path.home() / "Downloads" / "data" / "Downloads_from_internet"),
]
CHECK_INTERVAL = 30  # seconds

# ── Data Classes ─────────────────────────────────────────────────────────────
@dataclass
class DiscoveredPDF:
    path: Path
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None
    title_guess: str = ""
    hash: str = ""

# ── arXiv Client (lightweight) ────────────────────────────────────────────────
class ArxivClient:
    BASE_QUERY = "https://export.arxiv.org/api/query"
    BASE_PDF = "https://arxiv.org/pdf"

    def fetch_meta(self, arxiv_id: str) -> Optional[Dict]:
        clean = re.sub(r"v\d+$", "", arxiv_id)
        url = f"{self.BASE_QUERY}?id_list={clean}&max_results=1"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ScienceHub-Watcher/0.1"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                xml = resp.read().decode("utf-8")
            return self._parse(xml, clean)
        except Exception as e:
            self._log(f"[arxiv] Failed to fetch {arxiv_id}: {e}")
            return None

    def _parse(self, xml: str, arxiv_id: str) -> Optional[Dict]:
        import xml.etree.ElementTree as ET
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
        root = ET.fromstring(xml)
        entry = root.find("atom:entry", ns)
        if entry is None:
            return None
        def tag(t):
            el = entry.find(f"atom:{t}", ns)
            return el.text.strip() if el is not None else ""
        authors = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)]
        cat_el = entry.find("arxiv:primary_category", ns)
        primary = cat_el.attrib.get("term", "") if cat_el is not None else ""
        cats = [c.attrib.get("term", "") for c in entry.findall("atom:category", ns)]
        return {
            "arxiv_id": arxiv_id,
            "title": tag("title").replace("\n", " "),
            "authors": authors,
            "summary": tag("summary").replace("\n", " "),
            "published": tag("published")[:4],
            "updated": tag("updated"),
            "primary_category": primary,
            "categories": cats,
            "pdf_url": f"{self.BASE_PDF}/{arxiv_id}.pdf",
        }

    def _log(self, msg: str):
        print(msg, file=sys.stderr)

# ── Zotero Writer (same as sciencehub_mcp but minimal) ──────────────────────
class ZoteroWriter:
    def __init__(self, db_path: Path = ZOTERO_DB):
        self.db_path = db_path

    def _backup(self):
        ts = time.strftime("%Y%m%d_%H%M%S")
        backup = self.db_path.with_suffix(f".sqlite.backup.{ts}")
        shutil.copy2(str(self.db_path), str(backup))
        return backup

    def _get_next_item_id(self, conn: sqlite3.Connection) -> int:
        cur = conn.execute("SELECT MAX(itemID) FROM items")
        return (cur.fetchone()[0] or 0) + 1

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
        cur = conn.execute("INSERT INTO itemDataValues (value) VALUES (?) RETURNING valueID", (value,))
        return cur.fetchone()[0]

    def add_preprint(self, title: str, authors: List[str], url: str,
                     arxiv_id: Optional[str] = None, year: Optional[str] = None,
                     collection_name: str = "Research Stack") -> str:
        import random, string
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
                meta = {"title": title, "url": url, "extra": arxiv_id or ""}
                if year:
                    meta["date"] = year
                for field_name, val in meta.items():
                    if not val:
                        continue
                    fid = self._get_field_id(conn, field_name)
                    vid = self._get_or_create_value(conn, val)
                    conn.execute("INSERT INTO itemData (itemID, fieldID, valueID) VALUES (?,?,?)",
                                 (item_id, fid, vid))
                for i, author in enumerate(authors[:20]):
                    author = author.strip()
                    if not author:
                        continue
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
                cur = conn.execute("SELECT collectionID FROM collections WHERE collectionName = ?", (collection_name,))
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
            shutil.copy2(str(backup_path), str(self.db_path))
            raise

# ── Watcher State ─────────────────────────────────────────────────────────────
class WatcherState:
    def __init__(self, path: Path = STATE_FILE):
        self.path = path
        self.data: Dict = self._load()

    def _load(self) -> Dict:
        if self.path.exists():
            with open(self.path) as f:
                return json.load(f)
        return {"processed_hashes": [], "last_run": None}

    def save(self):
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=2)

    def is_new(self, file_hash: str) -> bool:
        return file_hash not in self.data.get("processed_hashes", [])

    def mark_processed(self, file_hash: str):
        self.data.setdefault("processed_hashes", []).append(file_hash)
        self.data["last_run"] = time.strftime("%Y-%m-%d %H:%M:%S")
        self.save()

# ── PDF Analyzer ────────────────────────────────────────────────────────────
class PDFAnalyzer:
    ARXIV_RE = re.compile(r"(\d{4}\.\d{4,5}(?:v\d+)?)")
    DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9a-z]+")

    def analyze(self, path: Path) -> DiscoveredPDF:
        name = path.stem
        arxiv_match = self.ARXIV_RE.search(name)
        arxiv_id = arxiv_match.group(1) if arxiv_match else None
        doi_guess = None
        if not arxiv_id:
            try:
                with open(path, "rb") as f:
                    header = f.read(8192).decode("utf-8", errors="ignore")
                    dm = self.DOI_RE.search(header)
                    if dm:
                        doi_guess = dm.group(0)
                    am = self.ARXIV_RE.search(header)
                    if am:
                        arxiv_id = am.group(1)
            except Exception:
                pass
        title_guess = self._clean_title(name)
        h = hashlib.sha256(path.read_bytes()).hexdigest()
        return DiscoveredPDF(path=path, arxiv_id=arxiv_id, doi=doi_guess, title_guess=title_guess, hash=h)

    @staticmethod
    def _clean_title(filename: str) -> str:
        t = filename.replace("_", " ").replace("-", " ")
        t = re.sub(r"\b\d{4}\.\d{4,5}v?\d*\b", "", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t

# ── Ingest Pipeline ─────────────────────────────────────────────────────────
class IngestPipeline:
    def __init__(self):
        self.analyzer = PDFAnalyzer()
        self.arxiv = ArxivClient()
        self.zotero = ZoteroWriter()
        self.state = WatcherState()

    def run_once(self, watch_dirs: List[str], dry_run: bool = False) -> List[str]:
        discovered: List[DiscoveredPDF] = []
        for d in watch_dirs:
            root = Path(d)
            if not root.exists():
                continue
            for pdf in root.rglob("*.pdf"):
                # Skip already-archived files
                if CANONICAL_DIR in pdf.parents:
                    continue
                info = self.analyzer.analyze(pdf)
                if self.state.is_new(info.hash):
                    discovered.append(info)

        reports: List[str] = []
        for pdf in discovered:
            report = self._process(pdf, dry_run=dry_run)
            reports.append(report)
            if not dry_run:
                self.state.mark_processed(pdf.hash)
        return reports

    def _process(self, pdf: DiscoveredPDF, dry_run: bool = False) -> str:
        lines = [f"📄  {pdf.path.name}"]
        if pdf.arxiv_id:
            lines.append(f"   arXiv ID: {pdf.arxiv_id}")
        if pdf.doi:
            lines.append(f"   DOI guess: {pdf.doi}")

        title = pdf.title_guess or "Unknown"
        authors: List[str] = []
        year: Optional[str] = None
        url = ""

        if pdf.arxiv_id:
            meta = self.arxiv.fetch_meta(pdf.arxiv_id)
            if meta:
                title = meta["title"]
                authors = meta["authors"]
                year = meta["published"]
                url = meta["pdf_url"]
                lines.append(f"   Fetched title: {title}")
                lines.append(f"   Authors: {', '.join(authors[:3])}")
            else:
                lines.append("   ⚠️  Could not fetch arXiv metadata")

        if dry_run:
            lines.append("   ⏸️  DRY RUN — no changes made")
            return "\n".join(lines)

        # Ingest to Zotero
        try:
            zkey = self.zotero.add_preprint(title, authors, url, arxiv_id=pdf.arxiv_id, year=year)
            lines.append(f"   📥  Zotero key: {zkey}")
        except Exception as e:
            lines.append(f"   ⚠️  Zotero ingest failed: {e}")

        # Move to canonical dir with safe name
        try:
            safe_title = self._safe_slug(title)
            dest_name = f"{pdf.arxiv_id or 'unknown'}_{safe_title}.pdf"
            dest = CANONICAL_DIR / dest_name
            shutil.move(str(pdf.path), str(dest))
            lines.append(f"   💾  Archived to: {dest}")
        except Exception as e:
            lines.append(f"   ⚠️  Move failed: {e}")

        return "\n".join(lines)

    @staticmethod
    def _safe_slug(title: str) -> str:
        replacements = {
            "\\": " ", "$": "", "^": "", "_": " ", "{": "", "}": "",
            "~": " ", "%": "pct", "&": "and", "#": "", "@": "at",
        }
        for old, new in replacements.items():
            title = title.replace(old, new)
        title = re.sub(r"[^\w\s-]", "", title)
        title = re.sub(r"[-\s]+", "_", title).strip("_")
        return title[:80] if title else "paper"

    def run_daemon(self, watch_dirs: List[str], interval: int = CHECK_INTERVAL):
        self._log(f"👁️  Ingest Watcher daemon started")
        self._log(f"   Watching: {', '.join(watch_dirs)}")
        self._log(f"   Archive:  {CANONICAL_DIR}")
        self._log(f"   Interval: {interval}s")
        while True:
            reports = self.run_once(watch_dirs)
            if reports:
                for r in reports:
                    self._log(r)
            time.sleep(interval)

    @staticmethod
    def _log(msg: str):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {msg}"
        print(line)
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Smart Ingest Watcher")
    parser.add_argument("--watch", nargs="*", default=DEFAULT_WATCH_DIRS, help="Directories to watch")
    parser.add_argument("--once", action="store_true", help="Run one scan and exit")
    parser.add_argument("--dry-run", action="store_true", help="Don't modify anything")
    parser.add_argument("--daemon", action="store_true", help="Run forever")
    parser.add_argument("--interval", type=int, default=CHECK_INTERVAL, help="Seconds between scans")
    args = parser.parse_args()

    pipeline = IngestPipeline()
    if args.once:
        reports = pipeline.run_once(args.watch, dry_run=args.dry_run)
        for r in reports:
            print(r)
        print(f"\nProcessed {len(reports)} new PDFs.")
    elif args.daemon:
        pipeline.run_daemon(args.watch, interval=args.interval)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
