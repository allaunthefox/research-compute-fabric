# PROPRIETARY -- ALL RIGHTS RESERVED
# Copyright (c) 2026 Allaun Holdings
# This source file is proprietary and confidential.
# See THIRD_PARTY_NOTICES.txt for third-party attributions.

"""
CFF Schema Extensions for physics_equations.db
"""

CFF_SCHEMA_EXTENSIONS = """
CREATE TABLE IF NOT EXISTS cff_root (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    root_hash TEXT NOT NULL,
    hash_algo TEXT DEFAULT 'sha256',
    num_equations INTEGER, num_verifications INTEGER, num_domains INTEGER,
    version INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')), updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS cff_domains (
    domain_name TEXT PRIMARY KEY,
    domain_hash TEXT NOT NULL, num_equations INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS cff_equations (
    equation_id INTEGER PRIMARY KEY,
    equation_hash TEXT NOT NULL, num_leaves INTEGER DEFAULT 0,
    armor_plated INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (equation_id) REFERENCES equations(id)
);

CREATE TABLE IF NOT EXISTS cff_leaves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doi TEXT UNIQUE NOT NULL, doi_normalized TEXT UNIQUE NOT NULL,
    leaf_hash TEXT NOT NULL, equation_id INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',
    hallucination_signals TEXT DEFAULT '[]',
    resolution_source TEXT, resolved_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (equation_id) REFERENCES equations(id)
);

CREATE TABLE IF NOT EXISTS cff_blacklist (
    doi TEXT PRIMARY KEY,
    rejection_reason TEXT NOT NULL, source_batch TEXT,
    blacklisted_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS cff_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL, computed_root TEXT, expected_root TEXT,
    match INTEGER, num_equations INTEGER, num_verifications INTEGER,
    details TEXT, audited_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_cff_leaves_eq ON cff_leaves(equation_id);
CREATE INDEX IF NOT EXISTS idx_cff_leaves_status ON cff_leaves(status);
CREATE INDEX IF NOT EXISTS idx_cff_audit_at ON cff_audit_log(audited_at);
"""


def apply_cff_schema(conn):
    conn.executescript(CFF_SCHEMA_EXTENSIONS)
    conn.commit()


def apply_cff_schema_to_db(db_path: str):
    import sqlite3
    conn = sqlite3.connect(db_path)
    try:
        apply_cff_schema(conn)
    finally:
        conn.close()
