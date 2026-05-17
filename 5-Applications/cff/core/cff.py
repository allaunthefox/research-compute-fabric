# PROPRIETARY -- ALL RIGHTS RESERVED
# Copyright (c) 2026 Allaun Holdings
# This source file is proprietary and confidential.
# See THIRD_PARTY_NOTICES.txt for third-party attributions.

"""
Citation Fingerprint Framework -- Core Classes

The CFF is the defensive backbone against LLM hallucination.
Every citation resolves to a Merkle leaf hash. Equations chain these into
a root fingerprint. Hallucinated DOIs fail at three levels:
  1. DOI resolution failure (DOI doesn't exist)
  2. Consistency failure (DOI exists but metadata conflicts)
  3. Topology failure (DOI is real but doesn't fit the constraint graph)
"""

import hashlib
import json
import sqlite3
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .fingerprint import (
    CFF_HASH_ALGO, CFF_ENCODING,
    hash_leaf, hash_node, hash_equation, hash_domain, hash_root,
    normalize_doi, compute_cff_from_db,
    compute_equation_fingerprint_incremental
)


class VerificationStatus(Enum):
    VERIFIED = "verified"
    UNRESOLVED = "unresolved"
    CONFLICTING = "conflicting"
    PENDING = "pending"
    REJECTED = "rejected"


class HallucinationSignal(Enum):
    DOI_NOT_FOUND = "DOI not found"
    AUTHOR_MISMATCH = "Author mismatch"
    YEAR_MISMATCH = "Year mismatch"
    JOURNAL_MISMATCH = "Journal mismatch"
    TITLE_MISMATCH = "Title mismatch"
    TOPOLOGY_BREAK = "Topology break"
    DUPLICATE_DOI = "Duplicate DOI"
    SUSPICIOUS_BATCH = "Suspicious batch"
    NO_ACADEMIC_PRESENCE = "No academic presence"


@dataclass
class CFFVerificationLeaf:
    doi: str
    title: str = ""
    authors: str = ""
    year: str = ""
    journal: str = ""
    equation_id: int = 0
    fingerprint: str = ""
    status: VerificationStatus = VerificationStatus.PENDING
    hallucination_signals: List[HallucinationSignal] = field(default_factory=list)
    resolution_source: str = ""
    resolution_timestamp: str = ""

    def compute_fingerprint(self) -> str:
        self.fingerprint = hash_leaf(
            normalize_doi(self.doi),
            self.title, self.authors, self.year, self.journal
        )
        return self.fingerprint

    @property
    def is_hallucinated(self) -> bool:
        return len(self.hallucination_signals) > 0

    @property
    def is_clean(self) -> bool:
        return self.status == VerificationStatus.VERIFIED and not self.hallucination_signals


@dataclass
class CFFEquationFingerprint:
    eq_id: int
    title: str
    domain: str
    fingerprint: str = ""
    leaf_fingerprints: List[str] = field(default_factory=list)
    dependency_fingerprints: List[str] = field(default_factory=list)
    verification_count: int = 0
    is_armor_plated: bool = False

    def compute_fingerprint(self) -> str:
        self.fingerprint = hash_equation(
            self.eq_id, self.title, self.domain,
            self.leaf_fingerprints, self.dependency_fingerprints
        )
        return self.fingerprint

    @property
    def strength(self) -> float:
        return min(1.0, self.verification_count / 15.0)


@dataclass
class CFFDomainFingerprint:
    name: str
    fingerprint: str = ""
    equation_fingerprints: Dict[int, str] = field(default_factory=dict)

    def compute_fingerprint(self) -> str:
        self.fingerprint = hash_domain(self.name, list(self.equation_fingerprints.values()))
        return self.fingerprint


@dataclass
class CFFRootFingerprint:
    fingerprint: str = ""
    hash_algo: str = CFF_HASH_ALGO
    timestamp: str = ""
    num_equations: int = 0
    num_verifications: int = 0
    num_domains: int = 0
    domain_fingerprints: Dict[str, str] = field(default_factory=dict)
    version: int = 1

    def compute_fingerprint(self) -> str:
        self.fingerprint = hash_root(list(self.domain_fingerprints.values()))
        return self.fingerprint

    def to_dict(self) -> Dict:
        return {
            "root": self.fingerprint, "hash_algo": self.hash_algo,
            "timestamp": self.timestamp, "num_equations": self.num_equations,
            "num_verifications": self.num_verifications, "num_domains": self.num_domains,
            "domains": self.domain_fingerprints, "version": self.version
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


class CitationFingerprintFramework:
    """
    Main CFF class -- manages the entire citation fingerprint lifecycle.

    This is the 'feel the virtual mass' framework: every DOI resolves
    to a weighted presence in the constraint graph. The Merkle root becomes
    the verifiable proof that the entire structure is academically sound.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.leaves: Dict[str, CFFVerificationLeaf] = {}
        self.equations: Dict[int, CFFEquationFingerprint] = {}
        self.domains: Dict[str, CFFDomainFingerprint] = {}
        self.root = CFFRootFingerprint()
        self._hallucination_blacklist: Set[str] = set()

    def build_from_database(self) -> CFFRootFingerprint:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='verifications'")
        if not cursor.fetchone():
            conn.close()
            return self.root

        cursor.execute("PRAGMA table_info(verifications)")
        cols = {r[1] for r in cursor.fetchall()}
        has_test = "test_name" in cols
        has_exp = "experiment" in cols

        if has_test and has_exp:
            cursor.execute("""
                SELECT equation_id, test_name, experiment, year, precision_level, status
                FROM verifications ORDER BY equation_id
            """)
            for row in cursor.fetchall():
                doi_key = f"{row['test_name']}|{row['experiment']}|{row['year']}"
                doi_key = normalize_doi(doi_key)
                if not doi_key:
                    continue
                if doi_key not in self.leaves:
                    self.leaves[doi_key] = CFFVerificationLeaf(
                        doi=doi_key,
                        title=row["test_name"] or "",
                        year=str(row["year"] or ""),
                        equation_id=row["equation_id"]
                    )
                    self.leaves[doi_key].compute_fingerprint()

        cursor.execute("""
            SELECT e.id, e.title, d.name as domain
            FROM equations e JOIN domains d ON e.domain_id = d.id ORDER BY e.id
        """)
        for row in cursor.fetchall():
            self.equations[row["id"]] = CFFEquationFingerprint(
                eq_id=row["id"],
                title=row["title"] or f"Eq_{row['id']}",
                domain=row["domain"] or "Unknown"
            )

        for doi, leaf in self.leaves.items():
            eq = self.equations.get(leaf.equation_id)
            if eq:
                eq.leaf_fingerprints.append(leaf.fingerprint)
                eq.verification_count += 1

        domain_eqs: Dict[str, Dict[int, str]] = {}
        for eq in self.equations.values():
            eq.compute_fingerprint()
            eq.is_armor_plated = eq.verification_count >= 15
            domain_eqs.setdefault(eq.domain, {})[eq.eq_id] = eq.fingerprint

        for name, eqs in domain_eqs.items():
            self.domains[name] = CFFDomainFingerprint(name=name, equation_fingerprints=eqs)
            self.domains[name].compute_fingerprint()

        self.root = CFFRootFingerprint(
            hash_algo=CFF_HASH_ALGO,
            timestamp=datetime.utcnow().isoformat(),
            num_equations=len(self.equations),
            num_verifications=len(self.leaves),
            num_domains=len(self.domains),
            domain_fingerprints={n: d.fingerprint for n, d in self.domains.items()}
        )
        self.root.compute_fingerprint()

        conn.close()
        return self.root

    def verify_integrity(self, stored_root: Optional[str] = None) -> Tuple[bool, Dict]:
        current_root = self.build_from_database()
        report = {
            "computed_root": current_root.fingerprint,
            "stored_root": stored_root,
            "match": current_root.fingerprint == stored_root if stored_root else None,
            "num_equations": current_root.num_equations,
            "num_verifications": current_root.num_verifications,
            "num_domains": current_root.num_domains,
            "timestamp": datetime.utcnow().isoformat(),
            "armor_plated_count": sum(1 for e in self.equations.values() if e.is_armor_plated),
            "hallucination_blacklist_size": len(self._hallucination_blacklist)
        }
        is_valid = report.get("match") is not False
        return is_valid, report

    def get_equation_fingerprint(self, eq_id: int) -> Optional[str]:
        eq = self.equations.get(eq_id)
        return eq.fingerprint if eq else None

    def get_virtual_mass(self, eq_id: int) -> float:
        eq = self.equations.get(eq_id)
        if not eq:
            return 0.0
        max_vcount = max((e.verification_count for e in self.equations.values()), default=1)
        base_mass = eq.verification_count / max_vcount
        armor_bonus = 1.0 if eq.is_armor_plated else 0.5
        density_factor = max(0.1, (len(self.leaves) / max(len(self.equations), 1)) / 15.0)
        return base_mass * armor_bonus * density_factor

    @property
    def verification_density(self) -> float:
        if not self.equations:
            return 0.0
        return len(self.leaves) / len(self.equations)

    def save_root(self, output_path: str):
        with open(output_path, "w") as f:
            f.write(self.root.to_json())

    def load_root(self, input_path: str) -> bool:
        with open(input_path, "r") as f:
            data = json.load(f)
        self.root.fingerprint = data.get("root", "")
        return bool(self.root.fingerprint)
