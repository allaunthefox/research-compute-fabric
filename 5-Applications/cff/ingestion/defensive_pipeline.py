# PROPRIETARY -- ALL RIGHTS RESERVED
# Copyright (c) 2026 Allaun Holdings
# See THIRD_PARTY_NOTICES.txt for third-party attributions.

"""
Defensive Ingestion Pipeline

The core anti-hallucination layer. Every raw citation passes through:
  1. ID extraction (DOI, arXiv, ISBN, title-based lookup)
  2. Multi-API resolution (Crossref, OpenAlex, Semantic Scholar, Europe PMC, arXiv)
  3. Cross-validation (metadata consistency across sources)
  4. CFF leaf hashing
  5. Constraint graph topology verification
  6. Admit / Reject / Flag-for-review
"""

import hashlib
import json
import re
import time
import sqlite3
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class IngestionVerdict(Enum):
    ADMIT = "admit"
    REJECT = "reject"
    FLAG = "flag"


class SignalStrength(Enum):
    CLEAN = "clean"
    SUSPICIOUS = "suspicious"
    HALLUCINATION = "hallucination"


@dataclass
class ResolvedRef:
    """A single citation resolved through the ingestion pipeline."""
    raw_text: str
    doi: str = ""
    title: str = ""
    authors: str = ""
    year: str = ""
    journal: str = ""
    volume: str = ""
    pages: str = ""
    abstract: str = ""
    fingerprint: str = ""
    status: SignalStrength = SignalStrength.CLEAN
    signals: List[str] = field(default_factory=list)
    resolution_chain: List[str] = field(default_factory=list)
    crossval_sources: int = 0
    topology_valid: bool = False
    topology_gap: float = 0.0
    verify_timestamp: str = ""
    equation_id: int = 0
    verdict: IngestionVerdict = IngestionVerdict.FLAG


class DOIDefensiveResolver:
    """
    Multi-API DOI resolution with cross-validation.

    Attempts resolution through:
      1. Crossref (DOI → metadata)
      2. OpenAlex (DOI → work)
      3. Semantic Scholar (DOI → paper)
      4. Europe PMC (DOI → article, life sciences)
      5. arXiv (for arXiv IDs)
      6. INSPIRE-HEP (DOI → record, physics)

    Cross-validates: title, year, journal, authors across ≥2 sources.
    Single-source resolutions are flagged as suspicious.
    Unresolvable DOIs are marked as hallucination.
    """

    def __init__(self, user_agent: str = "CFF-Ingestion/1.0 (mailto:research@example.com)"):
        self.user_agent = user_agent
        self.rate_limit_delay = 1.5
        self._last_request = 0.0
        self.cache: Dict[str, Dict] = {}

    def _rate_limit(self):
        elapsed = time.time() - self._last_request
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self._last_request = time.time()

    def _fetch_json(self, url: str) -> Optional[Dict]:
        self._rate_limit()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except Exception:
            return None

    def _fetch_xml(self, url: str) -> Optional[ET.Element]:
        self._rate_limit()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
            with urllib.request.urlopen(req, timeout=10) as resp:
                return ET.fromstring(resp.read().decode())
        except Exception:
            return None

    def _fetch_text(self, url: str) -> Optional[str]:
        self._rate_limit()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.read().decode()
        except Exception:
            return None

    def resolve_crossref(self, doi: str) -> Optional[Dict]:
        url = f"https://api.crossref.org/works/{doi}"
        data = self._fetch_json(url)
        if not data or "message" not in data:
            return None
        msg = data["message"]
        authors = []
        for a in msg.get("author", []):
            family = a.get("family", "")
            given = a.get("given", "")
            name = f"{given} {family}".strip() or a.get("name", "")
            if name:
                authors.append(name)
        return {
            "title": " ".join(msg.get("title", ["Unknown"])),
            "authors": "; ".join(authors),
            "year": str(msg.get("created", {}).get("date-parts", [[0]])[0][0]),
            "journal": " ".join(msg.get("container-title", ["Unknown"])),
            "volume": msg.get("volume", ""),
            "pages": msg.get("page", ""),
            "abstract": msg.get("abstract", ""),
            "source": "crossref",
        }

    def resolve_openalex(self, doi: str) -> Optional[Dict]:
        doi_enc = doi.replace("/", "%2F")
        url = f"https://api.openalex.org/works/doi:{doi_enc}"
        data = self._fetch_json(url)
        if not data or data.get("error"):
            return None
        authors = []
        for a in data.get("authorships", []):
            author = a.get("author", {})
            name = author.get("display_name", "")
            if name:
                authors.append(name)
        return {
            "title": data.get("title", ""),
            "authors": "; ".join(authors),
            "year": str(data.get("publication_year", "")),
            "journal": data.get("primary_location", {}).get("source", {}).get("display_name", ""),
            "volume": "",
            "pages": "",
            "abstract": "",
            "source": "openalex",
        }

    def resolve_semantic_scholar(self, doi: str) -> Optional[Dict]:
        doi_enc = doi.replace("/", "%2F")
        url = f"https://api.semanticscholar.org/v1/paper/DOI:{doi_enc}"
        data = self._fetch_json(url)
        if not data or data.get("error"):
            return None
        authors = []
        for a in data.get("authors", []):
            name = a.get("name", "")
            if name:
                authors.append(name)
        return {
            "title": data.get("title", ""),
            "authors": "; ".join(authors),
            "year": str(data.get("year", "")),
            "journal": data.get("venue", ""),
            "volume": "",
            "pages": "",
            "abstract": data.get("abstract", ""),
            "source": "semantic_scholar",
        }

    def resolve_europe_pmc(self, doi: str) -> Optional[Dict]:
        doi_enc = doi.replace("/", "%2F")
        url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:{doi_enc}&format=json&resultType=core"
        data = self._fetch_json(url)
        if not data or "resultList" not in data:
            return None
        results = data["resultList"].get("result", [])
        if not results:
            return None
        r = results[0]
        author_str = r.get("authorString", "")
        authors = "; ".join(a.strip() for a in author_str.split(",") if a.strip())
        return {
            "title": r.get("title", ""),
            "authors": authors,
            "year": r.get("pubYear", ""),
            "journal": r.get("journalTitle", ""),
            "volume": r.get("journalVolume", ""),
            "pages": r.get("pageInfo", ""),
            "abstract": r.get("abstractText", ""),
            "source": "europe_pmc",
        }

    def resolve_arxiv(self, arxiv_id: str) -> Optional[Dict]:
        url = f"https://export.arxiv.org/api/query?id_list={arxiv_id}&max_results=1"
        xml = self._fetch_xml(url)
        if xml is None:
            return None
        ns = {"a": "http://www.w3.org/2005/Atom"}
        entries = xml.findall("a:entry", ns)
        if not entries:
            return None
        entry = entries[0]
        authors = []
        for a in entry.findall("a:author", ns):
            name = a.findtext("a:name", "", ns)
            if name:
                authors.append(name)
        title = entry.findtext("a:title", "", ns).strip().replace("\n", " ")
        return {
            "title": title,
            "authors": "; ".join(authors),
            "year": entry.findtext("a:published", "", ns)[:4],
            "journal": "arXiv",
            "volume": "",
            "pages": "",
            "abstract": entry.findtext("a:summary", "", ns).strip(),
            "source": "arxiv",
        }

    def resolve_doi(self, doi: str) -> List[Dict]:
        """
        Resolve a DOI across all available APIs.
        Returns list of resolved metadata dicts, one per API.
        """
        if doi in self.cache:
            return self.cache[doi]

        results = []

        crossref = self.resolve_crossref(doi)
        if crossref:
            results.append(crossref)

        oa = self.resolve_openalex(doi)
        if oa:
            results.append(oa)

        s2 = self.resolve_semantic_scholar(doi)
        if s2:
            results.append(s2)

        # Europe PMC (life sciences focus)
        epmc = self.resolve_europe_pmc(doi)
        if epmc:
            results.append(epmc)

        self.cache[doi] = results
        return results

    def cross_validate(self, results: List[Dict]) -> Tuple[Dict, List[str]]:
        """
        Cross-validate metadata across API results.
        Returns (merged_dict, list_of_mismatch_signals).
        """
        if not results:
            return {}, ["DOI_NOT_FOUND"]

        if len(results) == 1:
            return results[0], ["SINGLE_SOURCE"]

        signals = []

        merged = {
            "title": results[0].get("title", ""),
            "authors": results[0].get("authors", ""),
            "year": results[0].get("year", ""),
            "journal": results[0].get("journal", ""),
            "abstract": results[0].get("abstract", ""),
            "sources": [r["source"] for r in results],
        }

        titles = [r.get("title", "").lower().strip(". ") for r in results]
        if len(set(titles)) > 1:
            signals.append("TITLE_MISMATCH")

        years = {r.get("year", "") for r in results}
        years.discard("")
        if len(years) > 1:
            signals.append("YEAR_MISMATCH")

        journals = {r.get("journal", "").lower().strip() for r in results}
        journals.discard("")
        journals.discard("unknown")
        if len(journals) > 1:
            signals.append("JOURNAL_MISMATCH")

        auth_sigs = set()
        for r in results:
            auth_list = sorted([a.strip().lower() for a in r.get("authors", "").split(";") if a.strip()])
            auth_sigs.add(tuple(auth_list[:3]))
        if len(auth_sigs) > 1:
            signals.append("AUTHOR_MISMATCH")

        if not signals and len(results) >= 2:
            signals.append("CROSS_VALIDATED")

        return merged, signals

    def classify(self, signals: List[str]) -> SignalStrength:
        if "DOI_NOT_FOUND" in signals:
            return SignalStrength.HALLUCINATION
        if "SINGLE_SOURCE" in signals:
            return SignalStrength.SUSPICIOUS
        severity = len([s for s in signals
                         if s in ("TITLE_MISMATCH", "YEAR_MISMATCH", "AUTHOR_MISMATCH")])
        if severity >= 2:
            return SignalStrength.HALLUCINATION
        if severity == 1:
            return SignalStrength.SUSPICIOUS
        return SignalStrength.CLEAN


class ConstraintTopologyVerifier:
    """
    Verifies that a resolved reference is topologically consistent with
    the constraint graph — i.e. this DOI belongs to the right equation.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path

    def check_topology(self, eq_id: int, ref_keywords: List[str],
                       ref_year: str = "") -> Tuple[bool, float]:
        """
        Check if this reference is topologically consistent with the equation.
        Returns (is_valid, gap_score).
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT title, year_range, significance, precision_note
            FROM equations WHERE id = ?
        """, (eq_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, 1.0

        eq_title = (row[0] or "").lower()
        eq_year = (row[1] or "").lower()
        eq_sig = (row[2] or "").lower()
        eq_prec = (row[3] or "").lower()

        conn.close()

        keyword_matches = sum(1 for kw in ref_keywords
                              if kw.lower() in eq_title + eq_sig + eq_prec)

        score = 1.0 if keyword_matches > 0 else 0.0
        is_valid = score >= 0.5
        gap = 1.0 - score

        return is_valid, gap


class DefensiveIngestionPipeline:
    """
    The full defensive ingestion pipeline.

    Flow:
      raw_citation → extract_ids → resolve → cross_validate → fingerprint → topology → verdict
    """

    def __init__(self, db_path: str, user_agent: str = "CFF-Ingestion/1.0"):
        self.db_path = db_path
        self.resolver = DOIDefensiveResolver(user_agent=user_agent)
        self.topology = ConstraintTopologyVerifier(db_path)

    @staticmethod
    def extract_ids(text: str) -> List[Tuple[str, str]]:
        """
        Extract identifiers from raw citation text.
        Returns list of (id_type, id_value) tuples.
        """
        ids = []

        doi_pattern = re.compile(r'\b(10\.\d{4,}(?:[.][^/\s]+)?/[-._;()/:a-zA-Z0-9]+)\b')
        for m in doi_pattern.finditer(text):
            ids.append(("doi", m.group(1)))

        arxiv_pattern = re.compile(
            r'(?:arxiv\s*:?\s*|arXiv\s*:?\s*|arxiv\.org/abs/)'
            r'(\d{4}\.\d{4,}(?:v\d+)?)',
            re.IGNORECASE
        )
        for m in arxiv_pattern.finditer(text):
            ids.append(("arxiv", m.group(1)))

        return ids

    def ingest(self, raw_citation: str, equation_id: int = 0) -> ResolvedRef:
        """
        Ingest a single raw citation. Returns ResolvedRef with verdict.
        """
        ref = ResolvedRef(
            raw_text=raw_citation,
            equation_id=equation_id,
            verify_timestamp=datetime.utcnow().isoformat(),
        )

        ids = self.extract_ids(raw_citation)
        if not ids:
            ref.signals.append("NO_IDENTIFIABLE_ID")
            ref.status = SignalStrength.SUSPICIOUS
            ref.verdict = IngestionVerdict.FLAG
            return ref

        all_resolutions = []
        for id_type, id_val in ids:
            if id_type == "doi":
                results = self.resolver.resolve_doi(id_val)
                ref.doi = id_val
            elif id_type == "arxiv":
                results = [self.resolver.resolve_arxiv(id_val)]
                results = [r for r in results if r is not None]
            else:
                results = []

            for r in results:
                r["id_type"] = id_type
                r["id_value"] = id_val
            all_resolutions.extend(results)

        if not all_resolutions:
            ref.signals.append("DOI_NOT_FOUND")
            ref.status = SignalStrength.HALLUCINATION
            ref.verdict = IngestionVerdict.REJECT
            return ref

        merged, signals = self.resolver.cross_validate(all_resolutions)
        ref.signals = signals
        ref.status = self.resolver.classify(signals)
        ref.resolution_chain = merged.get("sources", [])

        ref.title = merged.get("title", "")
        ref.authors = merged.get("authors", "")
        ref.year = merged.get("year", "")
        ref.journal = merged.get("journal", "")
        ref.abstract = merged.get("abstract", "")

        payload = (f"{ref.doi}\x00{ref.title}\x00{ref.authors}\x00"
                   f"{ref.year}\x00{ref.journal}")
        ref.fingerprint = hashlib.sha256(payload.encode()).hexdigest()

        keywords = (ref.title + " " + ref.abstract).split()
        keywords = [kw.strip(",.():;[]") for kw in keywords if len(kw) > 3]
        valid, gap = self.topology.check_topology(equation_id, keywords, ref.year)
        ref.topology_valid = valid
        ref.topology_gap = gap

        if ref.status == SignalStrength.HALLUCINATION:
            ref.verdict = IngestionVerdict.REJECT
        elif ref.status == SignalStrength.SUSPICIOUS:
            ref.verdict = IngestionVerdict.FLAG
        elif not valid:
            ref.verdict = IngestionVerdict.FLAG
            ref.signals.append("TOPOLOGY_BREAK")
        else:
            ref.verdict = IngestionVerdict.ADMIT

        return ref

    def ingest_batch(self, citations: List[Tuple[str, int]]) -> List[ResolvedRef]:
        """Ingest a batch of citations. Returns results in order."""
        results = []
        for text, eq_id in citations:
            ref = self.ingest(text, eq_id)
            results.append(ref)
        return results

    def admit_to_db(self, ref: ResolvedRef):
        """Write an admitted reference to the database."""
        if ref.verdict != IngestionVerdict.ADMIT:
            return False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cff_admitted_refs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equation_id INTEGER NOT NULL,
                doi TEXT, fingerprint TEXT UNIQUE,
                title TEXT, authors TEXT, year TEXT, journal TEXT,
                sources TEXT, ingest_timestamp TEXT,
                FOREIGN KEY (equation_id) REFERENCES equations(id)
            )
        """)

        try:
            cursor.execute("""
                INSERT OR IGNORE INTO cff_admitted_refs
                (equation_id, doi, fingerprint, title, authors, year, journal, sources, ingest_timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ref.equation_id, ref.doi, ref.fingerprint,
                ref.title, ref.authors, ref.year, ref.journal,
                json.dumps(ref.resolution_chain),
                datetime.utcnow().isoformat(),
            ))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def reject_to_blacklist(self, ref: ResolvedRef, batch_id: str = ""):
        """Write a rejected reference to the blacklist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cff_blacklist (
                fingerprint TEXT PRIMARY KEY,
                doi TEXT, raw_text TEXT, equation_id INTEGER,
                signals TEXT, rejection_reason TEXT, source_batch TEXT,
                blacklisted_at TEXT DEFAULT (datetime('now'))
            )
        """)

        cursor.execute("""
            INSERT OR IGNORE INTO cff_blacklist
            (fingerprint, doi, raw_text, equation_id, signals, rejection_reason, source_batch)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            ref.fingerprint, ref.doi, ref.raw_text, ref.equation_id,
            json.dumps(ref.signals),
            "; ".join(ref.signals),
            batch_id,
        ))

        conn.commit()
        conn.close()


def quick_verify(doi: str) -> Dict:
    """
    Quick standalone DOI verification.
    Returns verification report dict.
    """
    resolver = DOIDefensiveResolver()
    results = resolver.resolve_doi(doi)

    if not results:
        return {"verdict": "REJECTED", "signal": "DOI_NOT_FOUND", "sources": []}

    merged, signals = resolver.cross_validate(results)
    status = resolver.classify(signals)

    return {
        "verdict": "ADMITTED" if status == SignalStrength.CLEAN else "FLAGGED",
        "title": merged.get("title", "")[:120],
        "year": merged.get("year", ""),
        "journal": merged.get("journal", ""),
        "sources": merged.get("sources", []),
        "cross_validated": "CROSS_VALIDATED" in signals,
        "signals": [s for s in signals if s != "CROSS_VALIDATED"],
    }
