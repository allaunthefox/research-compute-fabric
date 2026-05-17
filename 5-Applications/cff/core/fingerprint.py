# PROPRIETARY -- ALL RIGHTS RESERVED
# Copyright (c) 2026 Allaun Holdings
# This source file is proprietary and confidential.
# See THIRD_PARTY_NOTICES.txt for third-party attributions.

"""
Citation Fingerprint Framework -- Core Fingerprint Computation
"""

import hashlib
import json
import sqlite3
from typing import Dict, List, Optional
from datetime import datetime

CFF_HASH_ALGO = "sha256"
CFF_ENCODING = "utf-8"


def hash_leaf(identifier: str, title: str = "", authors: str = "",
              year: str = "", journal: str = "") -> str:
    payload = f"{identifier}\x00{title}\x00{authors}\x00{year}\x00{journal}"
    return hashlib.new(CFF_HASH_ALGO, payload.encode(CFF_ENCODING)).hexdigest()


def hash_verification_leaf(test_name: str, experiment: str, year: str = "",
                           precision: str = "", status: str = "Confirmed") -> str:
    payload = f"{test_name}\x00{experiment}\x00{year}\x00{precision}\x00{status}"
    return hashlib.new(CFF_HASH_ALGO, payload.encode(CFF_ENCODING)).hexdigest()


def hash_node(*components: str) -> str:
    payload = "\x00".join(components)
    return hashlib.new(CFF_HASH_ALGO, payload.encode(CFF_ENCODING)).hexdigest()


def hash_equation(eq_id: int, eq_name: str, domain_name: str,
                  leaf_hashes: List[str], dependent_eq_fingerprints: List[str]) -> str:
    sorted_leaves = sorted(leaf_hashes)
    sorted_deps = sorted(dependent_eq_fingerprints)
    return hash_node(str(eq_id), eq_name, domain_name, *sorted_leaves, *sorted_deps)


def hash_domain(domain_name: str, eq_fingerprints: List[str]) -> str:
    return hash_node(domain_name, *sorted(eq_fingerprints))


def hash_root(domain_fingerprints: List[str]) -> str:
    return hash_node(*sorted(domain_fingerprints))


def normalize_doi(doi: str) -> str:
    doi = doi.strip().lower()
    if doi.startswith("https://doi.org/"):
        doi = doi[16:]
    elif doi.startswith("http://doi.org/"):
        doi = doi[15:]
    elif doi.startswith("doi:"):
        doi = doi[4:]
    elif doi.startswith("doi.org/"):
        doi = doi[8:]
    return doi


def compute_cff_from_db(db_path: str) -> Dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cff_data = {
        "root": "", "timestamp": datetime.utcnow().isoformat(),
        "hash_algo": CFF_HASH_ALGO,
        "num_equations": 0, "num_verifications": 0, "num_domains": 0,
        "domains": {}, "equations": {}, "verification_leaves": {}, "dependency_edges": []
    }

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='verifications'")
    if not cursor.fetchone():
        conn.close()
        return cff_data

    cursor.execute("PRAGMA table_info(verifications)")
    col_names = {r["name"] for r in cursor.fetchall()}
    has_test = "test_name" in col_names
    has_exp = "experiment" in col_names

    if has_test and has_exp:
        cursor.execute("SELECT equation_id, test_name, experiment, year, precision_level, status FROM verifications ORDER BY equation_id, test_name")
    else:
        conn.close()
        return cff_data

    leaf_hashes_by_eq = {}
    leaf_details = {}

    for row in cursor.fetchall():
        eq_id = row["equation_id"]
        test_name = row["test_name"] or ""
        experiment = row["experiment"] or ""
        year = str(row["year"] or "")
        precision = row["precision_level"] or ""
        status = row["status"] or "Confirmed"
        if not test_name and not experiment:
            continue
        leaf = hash_verification_leaf(test_name, experiment, year, precision, status)
        leaf_details[leaf] = {"equation_id": eq_id, "test_name": test_name, "experiment": experiment, "year": year}
        leaf_hashes_by_eq.setdefault(eq_id, []).append(leaf)

    cff_data["num_verifications"] = sum(len(v) for v in leaf_hashes_by_eq.values())
    cff_data["verification_leaves"] = leaf_details

    dep_edges = {}
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='invariant_chains'")
    if cursor.fetchone():
        for layer_pair in [
            ("layer1_eq_id", "layer2_eq_id"),
            ("layer2_eq_id", "layer3_eq_id"),
            ("layer3_eq_id", "layer4_eq_id"),
        ]:
            cursor.execute(f"SELECT {layer_pair[0]} as src, {layer_pair[1]} as dst FROM invariant_chains WHERE {layer_pair[0]} IS NOT NULL AND {layer_pair[1]} IS NOT NULL")
            for r in cursor.fetchall():
                src, dst = r["src"], r["dst"]
                if src and dst:
                    dep_edges.setdefault(dst, []).append(src)
                    cff_data["dependency_edges"].append([src, dst])

    cursor.execute("SELECT e.id, e.title, d.name FROM equations e JOIN domains d ON e.domain_id=d.id ORDER BY e.id")
    eq_info = {}
    domain_eqs = {}
    eq_fp = {}
    for row in cursor.fetchall():
        eid, title, dom = row["id"], row["title"] or f"Eq_{row['id']}", row["name"] or "Unknown"
        eq_info[eid] = (title, dom)
        domain_eqs.setdefault(dom, []).append(eid)

    remaining = set(eq_info.keys())
    for _ in range(len(remaining) * 2):
        resolved = set()
        for eid in list(remaining):
            deps = dep_edges.get(eid, [])
            if all(d not in remaining for d in deps):
                leaves = leaf_hashes_by_eq.get(eid, [])
                dep_fps = [eq_fp[d] for d in deps if d in eq_fp]
                eq_fp[eid] = hash_equation(eid, eq_info[eid][0], eq_info[eid][1], leaves, dep_fps)
                resolved.add(eid)
        remaining -= resolved
        if not resolved:
            break

    for eid in remaining:
        leaves = leaf_hashes_by_eq.get(eid, [])
        eq_fp[eid] = hash_equation(eid, eq_info[eid][0], eq_info[eid][1], leaves, [])

    cff_data["equations"] = {str(k): v for k, v in eq_fp.items()}
    cff_data["num_equations"] = len(eq_fp)

    domain_fps = {}
    for dom, eids in domain_eqs.items():
        fp = hash_domain(dom, [eq_fp[e] for e in eids])
        domain_fps[dom] = fp
        cff_data["domains"][dom] = {"fingerprint": fp, "num_equations": len(eids),
            "equation_fingerprints": {str(e): eq_fp[e] for e in eids}}
    cff_data["num_domains"] = len(domain_fps)
    cff_data["root"] = hash_root(list(domain_fps.values()))

    conn.close()
    return cff_data


def compute_equation_fingerprint_incremental(db_path: str, eq_id: int) -> str:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT e.title, d.name FROM equations e JOIN domains d ON e.domain_id=d.id WHERE e.id=?", (eq_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return ""
    title, domain = row[0], row[1]

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='verifications'")
    if not cursor.fetchone():
        conn.close()
        return hash_equation(eq_id, title or f"Eq_{eq_id}", domain or "Unknown", [], [])

    cursor.execute("PRAGMA table_info(verifications)")
    cols = {r[1] for r in cursor.fetchall()}

    if "test_name" in cols and "experiment" in cols:
        cursor.execute("SELECT test_name, experiment, year, precision_level, status FROM verifications WHERE equation_id=?", (eq_id,))
        leaves = [hash_verification_leaf(r["test_name"] or "", r["experiment"] or "",
            str(r["year"] or ""), r["precision_level"] or "", r["status"] or "Confirmed")
            for r in cursor.fetchall()]
    else:
        leaves = []

    conn.close()
    return hash_equation(eq_id, title or f"Eq_{eq_id}", domain or "Unknown", leaves, [])
