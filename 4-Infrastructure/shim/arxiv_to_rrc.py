#!/usr/bin/env python3
"""
arxiv_to_rrc.py — Bridge arXiv papers → RRC predictions JSON.

Reads papers from:
  1) Kaggle arXiv metadata JSON snapshot (--json)
  2) Neon PostgreSQL (--pg-dsn)
  3) Local SQLite database (--sqlite)

Maps each paper's arXiv categories to an RRC shape, computes 16D feature
hashes, and outputs the predictions JSON that build_corpus278.py consumes.

Usage:
    # Bootstrap Neon DB from Kaggle snapshot
    python3 arxiv_to_rrc.py --bootstrap --json metadata.json --pg-dsn postgresql://user@neon/db

    # Classify from Neon DB
    python3 arxiv_to_rrc.py --pg-dsn postgresql://user@neon/db

    # Direct from Kaggle snapshot (no DB)
    python3 arxiv_to_rrc.py --json metadata.json --limit 50000
"""

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

# ── 16D RRC shape mapping: arXiv category → RRC shape ──────────────────────
CAT_TO_SHAPE = {
    # LogogramProjection: categorical/logical/structural
    'math.CT': 'logogramProjection', 'math.RA': 'logogramProjection',
    'math.LO': 'logogramProjection', 'math.PL': 'logogramProjection',
    # ProjectableGeometryTopology: geometry/topology
    'math.AT': 'projectableGeometryTopology', 'math.DG': 'projectableGeometryTopology',
    'math.GT': 'projectableGeometryTopology', 'math.MG': 'projectableGeometryTopology',
    'math.SG': 'projectableGeometryTopology', 'math.AG': 'projectableGeometryTopology',
    'math.GN': 'projectableGeometryTopology', 'math.DS': 'projectableGeometryTopology',
    # CognitiveLoadField: quantum/field theory/high energy
    'quant-ph': 'cognitiveLoadField', 'hep-th': 'cognitiveLoadField',
    'hep-ph': 'cognitiveLoadField', 'math.QA': 'cognitiveLoadField',
    'math.KT': 'cognitiveLoadField', 'math.MP': 'cognitiveLoadField',
    'math-ph': 'cognitiveLoadField',
    # SignalShapedRouteCompiler: optimization/signal
    'math.OC': 'signalShapedRouteCompiler', 'cs.SY': 'signalShapedRouteCompiler',
    'eess.SP': 'signalShapedRouteCompiler',
    # CadForceProbeReceipt: numerical/physical computation
    'math.NA': 'cadForceProbeReceipt', 'cs.NA': 'cadForceProbeReceipt',
    'physics.comp-ph': 'cadForceProbeReceipt',
}

DEFAULT_SHAPE = 'holdForUnlawfulOrUnderspecifiedShape'

SHAPE_TO_STRING = {
    'logogramProjection': 'LogogramProjection',
    'projectableGeometryTopology': 'ProjectableGeometryTopology',
    'cognitiveLoadField': 'CognitiveLoadField',
    'signalShapedRouteCompiler': 'SignalShapedRouteCompiler',
    'cadForceProbeReceipt': 'CadForceProbeReceipt',
    'holdForUnlawfulOrUnderspecifiedShape': 'HoldForUnlawfulOrUnderspecifiedShape',
}


def rrc_shape(categories: str) -> str:
    """Map arXiv category string to RRC shape."""
    identity = 'holdForUnlawfulOrUnderspecifiedShape'
    for cat in categories.split():
        for prefix, shape in CAT_TO_SHAPE.items():
            if cat.startswith(prefix):
                identity = shape
    return identity


def sixteen_d_hash(title: str, abstract: str, categories: str, authors: str) -> int:
    """16D feature hash from paper metadata."""
    sig = f"{title}|{abstract[:300]}|{categories}|{authors[:100]}"
    return int(hashlib.sha256(sig.encode()).hexdigest()[:16], 16)


def process_json(src: Path, limit: int = 0):
    """Process arXiv metadata JSON snapshot (Kaggle format)."""
    predictions = []
    shape_counts = Counter()
    count = 0
    with open(src) as f:
        for line in f:
            if limit and count >= limit:
                break
            d = json.loads(line)
            cats = d.get('categories', '')
            shape_id = rrc_shape(cats)
            shape_str = SHAPE_TO_STRING[shape_id]
            h16 = sixteen_d_hash(
                d.get('title', ''), d.get('abstract', ''),
                cats, str(d.get('authors_parsed', []))
            )
            predictions.append({
                'equation_id': f"arxiv_{d['id'].replace('.','_')}",
                'title': d.get('title', '')[:120],
                'categories': cats,
                'proxy_pred': shape_str,
                'exact_pred': shape_str,
                'notes': f"16d_sha256:{h16:x}",
            })
            shape_counts[shape_id] += 1
            count += 1
    return predictions, shape_counts


def pg_connect(dsn: str):
    """Connect to PostgreSQL (Neon server or local)."""
    import psycopg2
    return psycopg2.connect(dsn)


def bootstrap_pg(dsn: str, json_snapshot: Path, limit: int = 0):
    """Create arXiv schema on Neon PostgreSQL and ingest from Kaggle snapshot."""
    import hashlib
    conn = pg_connect(dsn)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS domains (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        );
        CREATE TABLE IF NOT EXISTS equations (
            id SERIAL PRIMARY KEY,
            domain_id INTEGER NOT NULL REFERENCES domains(id),
            name TEXT,
            latex TEXT,
            category TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_eq_domain ON equations(domain_id);
    """)
    conn.commit()
    
    count = 0
    domains_cache = {}
    with open(json_snapshot) as f:
        for line in f:
            if limit and count >= limit:
                break
            d = json.loads(line)
            cats = d.get('categories', '')
            primary = cats.split()[0] if cats else 'unknown'
            if primary not in domains_cache:
                cur.execute("INSERT INTO domains (name) VALUES (%s) ON CONFLICT DO NOTHING RETURNING id", (primary,))
                row = cur.fetchone()
                if row:
                    domains_cache[primary] = row[0]
                else:
                    cur.execute("SELECT id FROM domains WHERE name=%s", (primary,))
                    domains_cache[primary] = cur.fetchone()[0]
            dom_id = domains_cache[primary]
            cur.execute("INSERT INTO equations (domain_id, name, latex, category) VALUES (%s, %s, %s, %s)",
                       (dom_id, d.get('title','')[:200], d.get('abstract','')[:1000], cats))
            count += 1
            if count % 50000 == 0:
                conn.commit()
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"Bootstrapped {count} papers into Neon PostgreSQL ({dsn[:50]}...)", file=sys.stderr)


def process_pg(dsn: str):
    """Read from Neon PostgreSQL, classify, output predictions."""
    conn = pg_connect(dsn)
    cur = conn.cursor()
    predictions = []
    shape_counts = Counter()
    
    cur.execute("SELECT id, name FROM domains")
    for dom_id, dom_name in cur.fetchall():
        cur.execute("SELECT id, name, latex, category FROM equations WHERE domain_id=%s", (dom_id,))
        for eq_id, eq_name, eq_latex, cats in cur.fetchall():
            shape_id = rrc_shape(cats or dom_name)
            shape_str = SHAPE_TO_STRING[shape_id]
            h16 = sixteen_d_hash(eq_name or '', eq_latex or '', cats or dom_name, '')
            predictions.append({
                'equation_id': f"dom_{dom_id}_eq_{eq_id}",
                'title': (eq_name or '')[:120],
                'categories': cats or dom_name,
                'proxy_pred': shape_str,
                'exact_pred': shape_str,
                'notes': f"16d_sha256:{h16:x}",
            })
            shape_counts[shape_id] += 1
    
    cur.close()
    conn.close()
    return predictions, shape_counts


def bootstrap_sqlite(db_path: Path, json_snapshot: Path, limit: int = 0):
    """Create SQLite database from Kaggle arXiv metadata snapshot."""
    import sqlite3
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS domains (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );
        CREATE TABLE IF NOT EXISTS equations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain_id INTEGER NOT NULL,
            name TEXT,
            latex TEXT,
            category TEXT,
            FOREIGN KEY (domain_id) REFERENCES domains(id)
        );
        CREATE INDEX IF NOT EXISTS idx_eq_domain ON equations(domain_id);
    """)
    
    count = 0
    domains_cache = {}
    with open(json_snapshot) as f:
        for line in f:
            if limit and count >= limit:
                break
            d = json.loads(line)
            cats = d.get('categories', '')
            primary = cats.split()[0] if cats else 'unknown'
            if primary not in domains_cache:
                cur.execute("INSERT OR IGNORE INTO domains (name) VALUES (?)", (primary,))
                row = cur.execute("SELECT id FROM domains WHERE name=?", (primary,)).fetchone()
                domains_cache[primary] = row[0] if row else 1
            dom_id = domains_cache[primary]
            cur.execute("INSERT INTO equations (domain_id, name, latex, category) VALUES (?, ?, ?, ?)",
                       (dom_id, d.get('title','')[:200], d.get('abstract','')[:1000], cats))
            count += 1
            if count % 50000 == 0:
                conn.commit()
                print(f"  Ingested {count}...", file=sys.stderr)
    
    conn.commit()
    conn.close()
    print(f"Bootstrapped {count} papers into {db_path}", file=sys.stderr)


def process_sqlite(db_path: Path):
    """Process papers from local SQLite database."""
    if not db_path.exists():
        print(f"Database {db_path} not found.", file=sys.stderr)
        return [], Counter()
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    predictions = []
    shape_counts = Counter()
    
    cur.execute("SELECT id, name FROM domains")
    for dom_id, dom_name in cur.fetchall():
        cur.execute("SELECT id, name, latex, category FROM equations WHERE domain_id=?", (dom_id,))
        for eq_id, eq_name, eq_latex, cats in cur.fetchall():
            shape_id = rrc_shape(cats or dom_name)
            shape_str = SHAPE_TO_STRING[shape_id]
            h16 = sixteen_d_hash(eq_name or '', eq_latex or '', cats or dom_name, '')
            predictions.append({
                'equation_id': f"dom_{dom_id}_eq_{eq_id}",
                'title': (eq_name or '')[:120],
                'categories': cats or dom_name,
                'proxy_pred': shape_str,
                'exact_pred': shape_str,
                'notes': f"16d_sha256:{h16:x}",
            })
            shape_counts[shape_id] += 1
    
    conn.close()
    return predictions, shape_counts


def main():
    ap = argparse.ArgumentParser(description='arXiv → RRC predictions bridge')
    ap.add_argument('--json', type=Path, help='arXiv metadata JSON snapshot (Kaggle)')
    ap.add_argument('--bootstrap', action='store_true', help='Bootstrap DB from JSON snapshot')
    ap.add_argument('--limit', type=int, default=0, help='Max papers (0 = all)')
    ap.add_argument('--output', type=Path, 
                    default=Path('/home/allaun/Research Stack/shared-data/rrc_arxiv_predictions_v1.json'),
                    help='Output predictions JSON')
    
    # Database options (mutually exclusive)
    db_group = ap.add_mutually_exclusive_group()
    db_group.add_argument('--pg-dsn', help='Neon PostgreSQL DSN (postgresql://user:pass@host/db)')
    db_group.add_argument('--sqlite', type=Path, default=Path('/home/allaun/physics_equations.db'),
                         help='Local SQLite database path')
    args = ap.parse_args()

    # Bootstrap mode: ingest Kaggle JSON into database
    if args.bootstrap:
        if not args.json:
            print("--json <path> required with --bootstrap", file=sys.stderr)
            sys.exit(1)
        if args.pg_dsn:
            bootstrap_pg(args.pg_dsn, args.json, args.limit)
        else:
            bootstrap_sqlite(args.sqlite, args.json, args.limit)
        return

    # Classification mode: read from database → classify → write predictions
    if args.pg_dsn:
        preds, shapes = process_pg(args.pg_dsn)
    elif args.json:
        preds, shapes = process_json(args.json, args.limit)
    else:
        preds, shapes = process_sqlite(args.sqlite)

    if not preds:
        print("No predictions generated.", file=sys.stderr)
        sys.exit(1)

    print(f"\nProcessed {len(preds)} papers", file=sys.stderr)
    print(f"Shape distribution:", file=sys.stderr)
    for s, c in shapes.most_common():
        print(f"  {SHAPE_TO_STRING[s]:40s} x{c}", file=sys.stderr)

    with open(args.output, 'w') as f:
        json.dump({
            'schema': 'rrc_arxiv_predictions_v1',
            'source': str(args.json or args.pg_dsn or args.sqlite),
            'total_papers': len(preds),
            'predictions': preds,
        }, f, indent=2)
    
    print(f"\nWritten {len(preds)} predictions to {args.output}", file=sys.stderr)
    print(f"Size: {args.output.stat().st_size / 1024 / 1024:.1f} MB", file=sys.stderr)


if __name__ == '__main__':
    main()
