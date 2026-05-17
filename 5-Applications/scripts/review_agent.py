#!/usr/bin/env python3
"""
Deep Review Agent
=================
After a paper is ingested, this agent:
  1. Extracts full text (or first N pages)
  2. Runs an LLM (local Ollama) to generate a structured review
  3. Stores the review back in the local index

Usage:
    python3 review_agent.py --paper /path/to/paper.pdf
    python3 review_agent.py --zotero-key B78T16BK
    python3 review_agent.py --batch 10          # Review 10 un-reviewed papers
    python3 review_agent.py --daemon            # Background loop

Review JSON schema:
    {
      "title": str,
      "authors": [str],
      "year": str,
      "venue": str,
      "tl_dr": str,           # 1-sentence elevator pitch
      "methods": str,         # What they actually did
      "key_findings": [str],  # Bullet list of top results
      "limitations": [str],   # Weaknesses / caveats
      "relevance": str,       # Why this matters to your work
      "citations_to_follow": [str],  # Key refs worth chasing
      "confidence": str,      # low / medium / high
      "read_again": bool      # Should you re-read in depth?
    }
"""

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Config ────────────────────────────────────────────────────────────────────
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:14b")
INDEX_DB = Path.home() / "Research Stack" / "data" / "substrate_index.db"
ZOTERO_DB = Path.home() / "Zotero" / "zotero.sqlite"
MAX_PAGES = 12  # pages to feed to LLM
BATCH_SIZE = 5  # papers per batch

# ── Review Storage ──────────────────────────────────────────────────────────
class ReviewStore:
    SCHEMA = """
    CREATE TABLE IF NOT EXISTS paper_reviews (
        paper_key TEXT PRIMARY KEY,
        zotero_key TEXT,
        arxiv_id TEXT,
        local_path TEXT,
        review_json TEXT,
        tl_dr TEXT,
        relevance TEXT,
        confidence TEXT,
        read_again INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_review_arxiv ON paper_reviews(arxiv_id);
    CREATE INDEX IF NOT EXISTS idx_review_relevance ON paper_reviews(relevance);
    """

    def __init__(self, db_path: Path = INDEX_DB):
        self.db_path = db_path
        self._ensure()

    def _ensure(self):
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.executescript(self.SCHEMA)

    def save(self, key: str, review: Dict, zotero_key: Optional[str] = None,
             arxiv_id: Optional[str] = None, local_path: Optional[str] = None):
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO paper_reviews
                   (paper_key, zotero_key, arxiv_id, local_path, review_json, tl_dr, relevance, confidence, read_again)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (
                    key,
                    zotero_key,
                    arxiv_id,
                    local_path,
                    json.dumps(review),
                    review.get("tl_dr", "")[:500],
                    review.get("relevance", "")[:500],
                    review.get("confidence", "medium"),
                    1 if review.get("read_again", False) else 0,
                ),
            )
            conn.commit()

    def get(self, key: str) -> Optional[Dict]:
        with sqlite3.connect(str(self.db_path)) as conn:
            cur = conn.execute("SELECT review_json FROM paper_reviews WHERE paper_key = ?", (key,))
            row = cur.fetchone()
            if row:
                return json.loads(row[0])
        return None

    def list_unreviewed(self, limit: int = 10) -> List[Dict]:
        """Return papers in local_pdfs that have no review yet."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                """SELECT p.* FROM local_pdfs p
                   LEFT JOIN paper_reviews r ON p.path = r.local_path
                   WHERE r.paper_key IS NULL
                   LIMIT ?""", (limit,)
            )
            return [dict(r) for r in cur.fetchall()]

# ── Text Extractor ──────────────────────────────────────────────────────────
class TextExtractor:
    def extract(self, pdf_path: Path, max_pages: int = MAX_PAGES) -> str:
        try:
            result = subprocess.run(
                ["pdftotext", "-l", str(max_pages), str(pdf_path), "-"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                return result.stdout
        except Exception:
            pass
        return ""

    def extract_from_zotero(self, zotero_key: str, max_pages: int = MAX_PAGES) -> str:
        # Find attachment path via Zotero storage
        # For now, fall back to searching local_pdfs by zotero_key
        with sqlite3.connect(str(INDEX_DB)) as conn:
            cur = conn.execute("SELECT path FROM local_pdfs WHERE zotero_key = ?", (zotero_key,))
            row = cur.fetchone()
            if row:
                return self.extract(Path(row[0]), max_pages)
        return ""

# ── LLM Reviewer ─────────────────────────────────────────────────────────────
class LLMReviewer:
    PROMPT_TEMPLATE = """You are a senior research scientist reviewing a preprint for a sovereign research lab focused on AI, topology, compression, and mathematical formalization.

TASK: Read the paper text below and produce a JSON review object.

RULES:
- Be concise but specific. No fluff.
- If the text is garbled or too short, note low confidence.
- Focus on: methods, novelty, reproducibility, and relevance to integer-only computing / topological state machines / manifold compression.
- Return ONLY valid JSON. No markdown fences. No prose outside the JSON.

PAPER TEXT (first {pages} pages):
---
{text}
---

REQUIRED JSON SCHEMA:
{{
  "title": "paper title",
  "authors": ["name1", "name2"],
  "year": "YYYY",
  "venue": "arXiv or journal/conference",
  "tl_dr": "One-sentence summary.",
  "methods": "What they did, technically.",
  "key_findings": ["Finding A", "Finding B"],
  "limitations": ["Limitation A", "Limitation B"],
  "relevance": "Why this matters to our work (integer math, topological compression, Lean proofs, etc).",
  "citations_to_follow": ["Author et al. YYYY — Topic"],
  "confidence": "high|medium|low",
  "read_again": true|false
}}
"""

    def __init__(self, model: str = OLLAMA_MODEL, host: str = OLLAMA_HOST):
        self.model = model
        self.host = host

    def review(self, text: str, pages: int = MAX_PAGES, force_stub: bool = False) -> Dict[str, Any]:
        if force_stub or not self._ollama_alive():
            return self.stub_review(text)
        prompt = self.PROMPT_TEMPLATE.format(pages=pages, text=text[:15000])
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.3, "num_ctx": 8192},
        }
        try:
            import urllib.request
            req = urllib.request.Request(
                f"{self.host}/api/generate",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read().decode())
            raw = data.get("response", "")
            raw = raw.strip()
            if raw.startswith("```json"):
                raw = raw[7:]
            if raw.startswith("```"):
                raw = raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()
            if not raw:
                raise ValueError("Empty response from LLM")
            parsed = json.loads(raw)
            for k in ["key_findings", "limitations", "citations_to_follow"]:
                if k not in parsed:
                    parsed[k] = []
                elif isinstance(parsed[k], str):
                    parsed[k] = [parsed[k]]
            return parsed
        except Exception as e:
            return self.stub_review(text, meta={"error": str(e)})

    def _ollama_alive(self) -> bool:
        """Check if the chosen model is loaded and Ollama is responsive."""
        try:
            import urllib.request
            # Check /api/ps for loaded models first
            req = urllib.request.Request(f"{self.host}/api/ps", method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                running = [m.get("name", "") for m in data.get("models", [])]
                if any(self.model in r for r in running):
                    return True
            # Fallback: check if model exists in library
            req = urllib.request.Request(f"{self.host}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                models = [m["name"] for m in data.get("models", [])]
                return self.model in models
        except Exception:
            return False

    def stub_review(self, text: str, meta: Optional[Dict] = None) -> Dict[str, Any]:
        """Generate a metadata-only review without calling the LLM."""
        stub = {
            "title": meta.get("title", "Unknown") if meta else "Unknown",
            "authors": meta.get("authors", []) if meta else [],
            "year": meta.get("year", "") if meta else "",
            "venue": "arXiv" if meta and meta.get("arxiv_id") else "Unknown",
            "tl_dr": "Stub review — LLM not available. Re-run with working Ollama for deep analysis.",
            "methods": "",
            "key_findings": [],
            "limitations": ["No LLM review performed."],
            "relevance": "unknown",
            "citations_to_follow": [],
            "confidence": "low",
            "read_again": False,
        }
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if lines and (not meta or not meta.get("title")):
            stub["title"] = lines[0][:200]
        # Try to grab authors from second line if it starts with "Authors:"
        if len(lines) > 1 and lines[1].lower().startswith("authors"):
            stub["authors"] = [a.strip() for a in lines[1].replace("Authors:", "").split(",") if a.strip()]
        return stub

# ── Review Pipeline ─────────────────────────────────────────────────────────
class ReviewPipeline:
    def __init__(self):
        self.store = ReviewStore()
        self.extractor = TextExtractor()
        self.reviewer = LLMReviewer()

    def review_pdf(self, pdf_path: Path) -> Dict:
        key = f"pdf:{pdf_path}"
        existing = self.store.get(key)
        if existing:
            return {"status": "already_reviewed", "review": existing}

        text = self.extractor.extract(pdf_path)
        if not text.strip():
            return {"status": "no_text", "review": None}

        review = self.reviewer.review(text)
        self.store.save(key, review, local_path=str(pdf_path))
        return {"status": "reviewed", "review": review}

    def review_zotero_key(self, zkey: str) -> Dict:
        key = f"zotero:{zkey}"
        existing = self.store.get(key)
        if existing:
            return {"status": "already_reviewed", "review": existing}

        text = self.extractor.extract_from_zotero(zkey)
        if not text.strip():
            return {"status": "no_text", "review": None}

        review = self.reviewer.review(text)
        self.store.save(key, review, zotero_key=zkey)
        return {"status": "reviewed", "review": review}

    def batch_review(self, limit: int = BATCH_SIZE) -> List[Dict]:
        unreviewed = self.store.list_unreviewed(limit)
        results = []
        for item in unreviewed:
            path = Path(item["path"])
            if not path.exists():
                continue
            res = self.review_pdf(path)
            results.append({"path": str(path), **res})
            time.sleep(2)  # be polite to Ollama
        return results

# ── CLI ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Deep Review Agent")
    parser.add_argument("--paper", help="Path to PDF to review")
    parser.add_argument("--zotero-key", help="Zotero item key to review")
    parser.add_argument("--batch", type=int, help="Review N unreviewed papers")
    parser.add_argument("--daemon", action="store_true", help="Loop forever reviewing new papers")
    parser.add_argument("--interval", type=int, default=300, help="Seconds between daemon scans")
    parser.add_argument("--show", help="Show existing review for a key")
    parser.add_argument("--model", default=OLLAMA_MODEL, help="Ollama model name")
    args = parser.parse_args()

    pipeline = ReviewPipeline()
    pipeline.reviewer.model = args.model

    if args.paper:
        res = pipeline.review_pdf(Path(args.paper))
        print(json.dumps(res, indent=2, default=str))
    elif args.zotero_key:
        res = pipeline.review_zotero_key(args.zotero_key)
        print(json.dumps(res, indent=2, default=str))
    elif args.batch:
        results = pipeline.batch_review(limit=args.batch)
        for r in results:
            print(f"\n{'='*60}")
            print(f"📄  {r['path']}")
            print(f"   Status: {r['status']}")
            if r.get("review"):
                rev = r["review"]
                print(f"   TL;DR: {rev.get('tl_dr')}")
                print(f"   Confidence: {rev.get('confidence')}")
                print(f"   Read again: {rev.get('read_again')}")
    elif args.daemon:
        print(f"👁️  Review daemon started (model={args.model}, interval={args.interval}s)")
        while True:
            results = pipeline.batch_review(limit=3)
            if results:
                for r in results:
                    print(f"[reviewed] {r['path']} → {r['status']}")
            time.sleep(args.interval)
    elif args.show:
        rev = pipeline.store.get(args.show)
        if rev:
            print(json.dumps(rev, indent=2))
        else:
            print("No review found for that key.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
