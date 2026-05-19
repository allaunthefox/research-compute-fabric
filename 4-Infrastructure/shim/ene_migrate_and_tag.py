#!/usr/bin/env python3
"""
Migrate knowledge.* tables → ENE substrate with aggressive concept tagging.

1. Apply ENE schema (ene.packages + 9 support tables)
2. Migrate all sources into ene.packages with typed provenance
3. Extract concepts, build relations, score N-space KV retention
4. Run cross-source discovery queries

Run in dev container:
  podman exec -e AWS_ACCESS_KEY_ID=... -e AWS_SECRET_ACCESS_KEY=... -e AWS_REGION=us-east-1 -e RDS_IAM=1 \
    research-stack python3 /home/researcher/stack/4-Infrastructure/shim/ene_migrate_and_tag.py
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import sys
import uuid
from collections import Counter
from pathlib import Path

import boto3
import psycopg2
import psycopg2.extras

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ene_migrate")

RDS_HOST = os.environ.get("RDS_HOST", "database-1-instance-1.cghu8yqogqwo.us-east-1.rds.amazonaws.com")
RDS_PORT = int(os.environ.get("RDS_PORT", "5432"))
RDS_USER = os.environ.get("RDS_USER", "postgres")
RDS_DBNAME = os.environ.get("RDS_DBNAME", "postgres")
RDS_IAM = os.environ.get("RDS_IAM", "1") == "1"
RDS_PW = os.environ.get("RDS_PASSWORD", "")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")


def connect():
    if RDS_IAM:
        client = boto3.client("rds", region_name=AWS_REGION)
        pw = client.generate_db_auth_token(DBHostname=RDS_HOST, Port=RDS_PORT, DBUsername=RDS_USER, Region=AWS_REGION)
    else:
        pw = RDS_PW
    return psycopg2.connect(host=RDS_HOST, port=RDS_PORT, user=RDS_USER, password=pw, dbname=RDS_DBNAME, sslmode="require")


def apply_schema(conn):
    """Apply the full ENE substrate schema."""
    schema_path = Path("/home/researcher/stack/4-Infrastructure/shim/ene_substrate_schema.sql")
    if schema_path.exists():
        sql = schema_path.read_text()
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        log.info("ENE substrate schema applied")
    else:
        log.warning("Schema file not found, creating inline")
        # Fallback: create minimal schema inline
        with conn.cursor() as cur:
            cur.execute("CREATE SCHEMA IF NOT EXISTS ene")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ene.packages (
                    pkg TEXT PRIMARY KEY, package_type TEXT, title TEXT, content TEXT,
                    content_hash TEXT, concept_vector JSONB DEFAULT '[]',
                    concept_anchor JSONB DEFAULT '{}', tags JSONB DEFAULT '[]',
                    source TEXT, provenance JSONB DEFAULT '{}', domain TEXT,
                    archetype TEXT, promotion_state TEXT DEFAULT 'held',
                    scar_class TEXT, ingested_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                CREATE TABLE IF NOT EXISTS ene.relations (
                    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
                    source_id TEXT NOT NULL, target_id TEXT NOT NULL,
                    relation_type TEXT NOT NULL, weight REAL DEFAULT 1.0,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                CREATE TABLE IF NOT EXISTS ene.nspace_kv (
                    key_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
                    value_package_id TEXT NOT NULL,
                    reduction_reward REAL DEFAULT 0, sparsity_score REAL DEFAULT 0,
                    scar_pressure REAL DEFAULT 0, retention_score REAL DEFAULT 0
                );
            """)
        conn.commit()
        log.info("ENE minimal schema applied")


# ---------------------------------------------------------------------------
# Term extraction (same aggressive tokenizer from concept_cross_reference.py)
# ---------------------------------------------------------------------------
MATH_SYMBOL_RE = re.compile(
    r'\\(?:alpha|beta|gamma|Gamma|delta|Delta|epsilon|varepsilon|zeta|eta|theta|Theta|'
    r'iota|kappa|lambda|Lambda|mu|nu|xi|Xi|pi|Pi|rho|sigma|Sigma|tau|upsilon|phi|Phi|'
    r'varphi|chi|psi|Psi|omega|Omega|partial|nabla|infty|int|sum|prod|otimes|oplus|'
    r'rightarrow|leftarrow|Rightarrow|Leftarrow|mapsto|approx|equiv|sim|propto|'
    r'leq|geq|neq|times|cdot|circ|pm|mp|sqrt|frac|operatorname|mathbf|mathrm|mathcal|'
    r'mathfrak|mathbb|text|hat|tilde|bar|vec|dot|ddot|widehat|widetilde|'
    r'langle|rangle|lVert|rVert|vert|mid|'
    r'begin|end|left|right|big|Big|bigg|Bigg)'
)

TECHNICAL_RE = re.compile(
    r'\b(?:'
    r'manifold|field|shear|packet|spectral|braid|gossip|'
    r'residual|invariant|receipt|scar|warden|collapse|compression|'
    r'entropy|eigen(?:value|vector)?|coboundary|cochain|'
    r'diffusion|transport|boundary|kernel|operator|'
    r'tensor|metric|geodesic|curvature|torsion|'
    r'hamiltonian|lagrangian|reduction|projection|embedding|'
    r'chirality|helicity|handedness|logogram|'
    r'sidon|goxel|famm|nuvmap|otom|pist|'
    r'erdos|szekeres|selfridge|gyarfas|'
    r'biocompression|organoid|chaos|fractal|attractor|basin|'
    r'thermal|thermodynamic|landauer|witness|shadow|adversarial|'
    r'morph(?:ic|ism)?|radix|codec|semantic|'
    r'markov|cognitive|attention|neural|network|transformer|'
    r'hutter|prize|betti|homology|cohomology|'
    r'riccati|noise|mfg|hessian|jacobian|'
    r'seam|tomography|sandwich|pruning|rope|scar|'
    r'eigensolid|eigenspace|underverse|geocognition|'
    r'smallcode|constrained|key.value|shortcut|ontology|'
    r'hyperbolic|riemannian|poincare|'
    r'bio|dna|rna|protein|feynman|navier|stokes|'
    r'plasma|mhd|alfven|'
    r'q16|fixed.point|subleq|oisc|kv|cache'
    r')\b', re.IGNORECASE
)

TOKEN_RE = re.compile(r'[a-zA-Z_\\][a-zA-Z0-9_\\]*|\b(?:N-space|key-value|CP-SAT|Anti-FAMM|Anti-Braid)\b', re.IGNORECASE)
STOP_WORDS = set("the a an is are was were be been being have has had do does did will would shall should may might must can could of in to for with on at by from as into through during and but or not no nor so if then else when where this that these those it its we they he she which who whom whose what how why also very more most some any all each every both few new other such only own same just about over text bf rm sf tt em sc it up use using used can one two also etc via per e.g i.e figure table section non doi url http https www paper result method approach model data set page pages vol pp et al note notes example see shown fig eq ref abstract introduction conclusion reference references arxiv org github com html pdf first second third following based given found obtained described proposed well within without between among under above below since however therefore thus still yet here there where now then than get got getting make made making take taken taking give given giving let lets case cases term terms form forms number numbers value values point points part parts type types kind kinds way ways much many long short high low large small different similar same total whole full work works working need needs needed help helps helped like likes liked know known unknown think thought believe want wants wanted try tries tried".split())


def tokenize(text: str) -> list[str]:
    if not text:
        return []
    seen: set[str] = set()
    results: list[str] = []
    for m in TOKEN_RE.finditer(text):
        t = m.group(0).strip().lower().rstrip(".,;:!?\"'()[]{}").lstrip("\\").rstrip("{}")
        if not t or t in STOP_WORDS or len(t) < 2 or t in seen:
            continue
        seen.add(t)
        results.append(t)
    return results


# ---------------------------------------------------------------------------
# Migration
# ---------------------------------------------------------------------------
def migrate_all_sources(conn):
    """Migrate knowledge.* tables into ene.packages with typed provenance."""
    cur = conn.cursor()
    total = 0

    migrations = [
        ("equations", "eq_id", "equation", """
            INSERT INTO ene.packages (pkg, package_type, title, content, content_hash, tags, source, domain, provenance, promotion_state)
            SELECT eq_id::text, 'equation', latex, latex, content_hash, '[]'::jsonb, source_file, 'equation_corpus',
                   jsonb_build_object('kind', kind, 'source_file', source_file, 'source_offset', source_offset),
                   'held'
            FROM knowledge.equations
            ON CONFLICT (pkg) DO UPDATE SET
                title = EXCLUDED.title, content = EXCLUDED.content,
                content_hash = EXCLUDED.content_hash, tags = EXCLUDED.tags
        """),
        ("tiddlywiki_pages", "tiddler_id", "tiddler", """
            INSERT INTO ene.packages (pkg, package_type, title, content, content_hash, tags, source, domain, provenance, promotion_state)
            SELECT tiddler_id::text, 'tiddler', title, coalesce(body,''),
                   content_hash, '[]'::jsonb, source_path, 'tiddlywiki',
                   jsonb_build_object('tags', tags, 'created', created, 'modified', modified, 'source_path', source_path),
                   'held'
            FROM knowledge.tiddlywiki_pages
            ON CONFLICT (pkg) DO UPDATE SET
                title = EXCLUDED.title, content = EXCLUDED.content,
                content_hash = EXCLUDED.content_hash, tags = EXCLUDED.tags
        """),
        ("references", "ref_id", "reference", """
            INSERT INTO ene.packages (pkg, package_type, title, content, content_hash, tags, source, domain, provenance, promotion_state)
            SELECT ref_id::text, 'reference', 
                   substring(coalesce(bibtex,'') from 1 for 200),
                   bibtex, content_hash, '[]'::jsonb, source_file, 'bibliography',
                   jsonb_build_object('source_file', source_file, 'bibtex', coalesce(bibtex,'')),
                   'held'
            FROM knowledge.references
            ON CONFLICT (pkg) DO UPDATE SET
                title = EXCLUDED.title, content = EXCLUDED.content,
                content_hash = EXCLUDED.content_hash, tags = EXCLUDED.tags
        """),
        ("links", "link_id", "link", """
            INSERT INTO ene.packages (pkg, package_type, title, content, content_hash, tags, source, domain, provenance, promotion_state)
            SELECT link_id::text, 'link', url, url, encode(sha256(url::bytea),'hex'), '[]'::jsonb, source_file,
                   'external_reference',
                   jsonb_build_object('url', url, 'source_file', source_file),
                   'held'
            FROM knowledge.links
            ON CONFLICT (pkg) DO UPDATE SET
                title = EXCLUDED.title, content = EXCLUDED.content
        """),
        ("article_sources", "article_id", "article", """
            INSERT INTO ene.packages (pkg, package_type, title, content, content_hash, tags, source, domain, provenance, promotion_state)
            SELECT article_id::text, 'article', coalesce(label, url), coalesce(label,'') || ' ' || url,
                   encode(sha256(url::bytea),'hex'), '[]'::jsonb, url, 'article_source',
                   jsonb_build_object('url', url, 'label', label, 'category', category),
                   'held'
            FROM knowledge.article_sources
            ON CONFLICT (pkg) DO UPDATE SET
                title = EXCLUDED.title, content = EXCLUDED.content
        """),
        ("dois", "doi_id", "doi", """
            INSERT INTO ene.packages (pkg, package_type, title, content, content_hash, tags, source, domain, provenance, promotion_state)
            SELECT doi_id::text, 'doi', doi, doi, encode(sha256(doi::bytea),'hex'), '[]'::jsonb, source_file, 'doi_identifier',
                   jsonb_build_object('doi', doi, 'source_file', source_file),
                   'held'
            FROM knowledge.dois
            ON CONFLICT (pkg) DO UPDATE SET
                title = EXCLUDED.title, content = EXCLUDED.content
        """),
        ("dataset_inventory", "inv_id", "dataset", """
            INSERT INTO ene.packages (pkg, package_type, title, content, content_hash, tags, source, domain, provenance, promotion_state)
            SELECT inv_id::text, 'dataset', coalesce(name, asset_id),
                   coalesce(name,'') || ' ' || coalesce(evidence,'') || ' ' || coalesce(notes,''),
                   encode(sha256(coalesce(name,'')::bytea),'hex'), '[]'::jsonb, coalesce(name,''),
                   'dataset_manifest',
                   jsonb_build_object('asset_id', asset_id, 'name', name, 'kind', kind, 'status', status, 'evidence', evidence),
                   'held'
            FROM knowledge.dataset_inventory
            ON CONFLICT (pkg) DO UPDATE SET
                title = EXCLUDED.title, content = EXCLUDED.content
        """),
    ]

    for src_table, id_col, pkg_type, insert_sql in migrations:
        cur.execute(f"SELECT COUNT(*) FROM knowledge.{src_table}")
        count = cur.fetchone()[0]
        cur.execute(insert_sql)
        total += count
        log.info("Migrated %s → ene.packages (%d rows)", src_table, count)

    conn.commit()
    log.info("Total packages migrated: %d", total)
    return total


def tag_packages(conn):
    """Extract terms from each package content and store as concept_vector + tags JSONB."""
    cur = conn.cursor()

    cur.execute("SELECT pkg, package_type, coalesce(content,''), coalesce(title,'') FROM ene.packages WHERE content IS NOT NULL AND content != ''")
    packages = cur.fetchall()

    updated = 0
    for pkg, pkg_type, content, title in packages:
        terms = tokenize(content + " " + title)
        if not terms:
            continue

        # Classify terms
        math_terms = [t for t in terms if MATH_SYMBOL_RE.fullmatch(t)]
        tech_terms = [t for t in terms if TECHNICAL_RE.search(t)]
        all_terms = list(dict.fromkeys(terms))  # deduplicate preserving order

        concept_vector = [
            {"term": t, "type": "math_symbol" if t in math_terms else "technical_term" if t in tech_terms else "keyword"}
            for t in all_terms[:50]  # cap at 50 for storage
        ]
        tags = all_terms[:20]  # top 20 as tags

        cur.execute(
            """UPDATE ene.packages
               SET concept_vector = %s, tags = %s
               WHERE pkg = %s""",
            (json.dumps(concept_vector), json.dumps(tags), pkg),
        )
        updated += 1
        if updated % 100 == 0:
            conn.commit()
            log.info("  tagged %d/%d packages…", updated, len(packages))

    conn.commit()
    log.info("Tagged %d packages with concept vectors", updated)
    return updated


def build_relations(conn):
    """Build ene.relations between packages that share concepts across different domains."""
    cur = conn.cursor()

    # Extract all concept terms per package
    cur.execute("SELECT pkg, concept_vector, domain FROM ene.packages WHERE concept_vector IS NOT NULL AND jsonb_array_length(concept_vector) > 0")
    packages = cur.fetchall()
    log.info("Building relations from %d tagged packages…", len(packages))

    # Index: term -> [(pkg, domain), ...]
    term_index: dict[str, list[tuple[str, str]]] = {}
    for pkg, cv, domain in packages:
        if cv is None:
            continue
        concepts = json.loads(cv) if isinstance(cv, str) else cv
        for c in concepts:
            term = c["term"].lower()
            if term not in term_index:
                term_index[term] = []
            term_index[term].append((pkg, domain or "unknown"))

    # Build relations: packages sharing concepts across different domains
    relation_count = 0
    for term, pkgs in term_index.items():
        if len(pkgs) < 2:
            continue
        # Pair packages from different domains sharing this term
        for i, (p1, d1) in enumerate(pkgs):
            for j in range(i + 1, len(pkgs)):
                p2, d2 = pkgs[j]
                if d1 == d2:
                    continue  # skip same-domain (already known)
                # Determine relation type
                rel_type = "shares_concept" if d1 != d2 else "co_occurs"
                try:
                    cur.execute(
                        """INSERT INTO ene.relations (source_id, target_id, relation_type, weight)
                           VALUES (%s,%s,%s,1.0)
                           ON CONFLICT DO NOTHING""",
                        (p1, p2, rel_type),
                    )
                    if cur.rowcount > 0:
                        relation_count += 1
                except Exception:
                    pass
        if relation_count % 2000 == 0:
            conn.commit()
            log.info("  %d relations…", relation_count)

    conn.commit()
    log.info("Built %d cross-domain relations", relation_count)
    return relation_count


def score_nspace_kv(conn):
    """Compute reduction_reward, sparsity_score, and retention_score for packages."""
    cur = conn.cursor()

    # Score based on: concept count (richness), relation count (connectivity), domain uniqueness
    cur.execute("""
        INSERT INTO ene.nspace_kv (value_package_id, reduction_reward, sparsity_score, scar_pressure, retention_score)
        SELECT p.pkg,
               GREATEST(0.1, LEAST(1.0, jsonb_array_length(p.concept_vector) / 50.0)) AS reduction_reward,
               1.0 / NULLIF(
                   (SELECT COUNT(*) FROM ene.packages p2 WHERE p2.domain = p.domain),
                   1
                )::float AS sparsity_score,
               0.0 AS scar_pressure,
               GREATEST(0.1, LEAST(1.0,
                   (jsonb_array_length(p.concept_vector) / 50.0) * 0.4 +
                   (1.0 / NULLIF((SELECT COUNT(*) FROM ene.packages p2 WHERE p2.domain = p.domain), 1)::float) * 0.3 +
                   ((SELECT COUNT(*) FROM ene.relations r WHERE r.source_id = p.pkg OR r.target_id = p.pkg)::float / NULLIF((SELECT COUNT(*) FROM ene.relations), 1)::float) * 0.3
               )) AS retention_score
        FROM ene.packages p
        WHERE p.concept_vector IS NOT NULL AND jsonb_array_length(p.concept_vector) > 0
        ON CONFLICT (value_package_id) DO UPDATE SET
            reduction_reward = EXCLUDED.reduction_reward,
            sparsity_score = EXCLUDED.sparsity_score,
            retention_score = EXCLUDED.retention_score
    """)
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM ene.nspace_kv")
    nv = cur.fetchone()[0]
    log.info("Scored %d packages with N-space KV retention", nv)
    return nv


def run_discovery_queries(conn):
    """Run cross-source discovery queries and log unexpected groupings."""
    cur = conn.cursor()

    queries = [
        ("=== DOMAINS SHARING THE MOST CONCEPTS ===", """
            SELECT r.relation_type, p1.domain AS domain_a, p2.domain AS domain_b,
                   COUNT(*) AS pair_count,
                   COUNT(DISTINCT r.source_id) + COUNT(DISTINCT r.target_id) AS packages_involved
            FROM ene.relations r
            JOIN ene.packages p1 ON p1.pkg = r.source_id
            JOIN ene.packages p2 ON p2.pkg = r.target_id
            GROUP BY r.relation_type, p1.domain, p2.domain
            ORDER BY pair_count DESC
            LIMIT 20
        """),

        ("=== EQUATIONS BRIDGING TO TIDDLYWIKI PAGES ===", """
            SELECT eq.pkg AS eq_pkg, LEFT(eq.title, 80) AS equation,
                   tw.title AS tiddler_title,
                   r.relation_type
            FROM ene.relations r
            JOIN ene.packages eq ON eq.pkg = r.source_id AND eq.domain = 'equation_corpus'
            JOIN ene.packages tw ON tw.pkg = r.target_id AND tw.domain = 'tiddlywiki'
            ORDER BY r.weight DESC
            LIMIT 30
        """),

        ("=== UNEXPECTED CROSS-SOURCE GROUPINGS ===", """
            WITH shared AS (
                SELECT p1.domain AS d1, p2.domain AS d2, COUNT(*) AS cnt
                FROM ene.relations r
                JOIN ene.packages p1 ON p1.pkg = r.source_id
                JOIN ene.packages p2 ON p2.pkg = r.target_id
                WHERE p1.domain != p2.domain
                GROUP BY p1.domain, p2.domain
            )
            SELECT d1, d2, cnt,
                   CASE WHEN cnt > 10 THEN 'strong'
                        WHEN cnt > 3 THEN 'notable'
                        ELSE 'weak'
                   END AS strength
            FROM shared
            ORDER BY cnt DESC
        """),

        ("=== TOP BRIDGE CONCEPTS (terms spanning most domains) ===", """
            SELECT term, COUNT(DISTINCT p.domain) AS domain_span,
                   ARRAY_AGG(DISTINCT p.domain) AS domains
            FROM (
                SELECT p.domain, (jsonb_array_elements(p.concept_vector)->>'term') AS term
                FROM ene.packages p
                WHERE p.concept_vector IS NOT NULL AND jsonb_array_length(p.concept_vector) > 0
            ) sub
            GROUP BY term
            HAVING COUNT(DISTINCT domain) >= 3
            ORDER BY domain_span DESC, COUNT(*) DESC
            LIMIT 30
        """),

        ("=== HIGHEST RETENTION SCORE PACKAGES ===", """
            SELECT n.value_package_id, p.title, p.domain, n.retention_score,
                   n.reduction_reward, n.sparsity_score
            FROM ene.nspace_kv n
            JOIN ene.packages p ON p.pkg = n.value_package_id
            ORDER BY n.retention_score DESC
            LIMIT 20
        """),

        ("=== DOMAINS BY PACKAGE COUNT ===", """
            SELECT domain, COUNT(*) AS package_count, package_type,
                   COUNT(DISTINCT package_type) AS types
            FROM ene.packages
            GROUP BY domain, package_type
            ORDER BY COUNT(*) DESC
        """),

        ("=== RELATION TYPE DISTRIBUTION ===", """
            SELECT relation_type, COUNT(*) AS total,
                   COUNT(DISTINCT source_id) AS sources,
                   COUNT(DISTINCT target_id) AS targets
            FROM ene.relations
            GROUP BY relation_type
            ORDER BY total DESC
        """),
    ]

    results = {}
    for title, query in queries:
        cur.execute(query)
        rows = cur.fetchall()
        results[title] = rows
        log.info("\n%s", title)
        for row in rows[:12]:
            log.info("  %s", " | ".join(str(c) for c in row))
        if len(rows) > 12:
            log.info("  ... +%d more rows", len(rows) - 12)

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    log.info("Connecting to RDS…")
    conn = connect()
    conn.autocommit = False

    log.info("Phase 1: Apply ENE substrate schema")
    apply_schema(conn)

    log.info("Phase 2: Migrate knowledge.* → ene.packages")
    total = migrate_all_sources(conn)

    log.info("Phase 3: Extract concepts and tag packages")
    tagged = tag_packages(conn)

    log.info("Phase 4: Build cross-domain relations")
    relations = build_relations(conn)

    log.info("Phase 5: Score N-space KV retention")
    nv_scored = score_nspace_kv(conn)

    log.info("Phase 6: Run discovery queries")
    results = run_discovery_queries(conn)

    # Summary
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM ene.packages")
    pkg_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM ene.relations")
    rel_count = cur.fetchone()[0]
    cur.execute("SELECT domain, COUNT(*) FROM ene.packages GROUP BY domain ORDER BY COUNT(*) DESC")
    domains = cur.fetchall()
    conn.close()

    log.info("\n=== SUMMARY ===")
    log.info("Packages: %d", pkg_count)
    log.info("Relations: %d", rel_count)
    log.info("N-space KV scored: %d", nv_scored)
    log.info("Domains:")
    for d, c in domains:
        log.info("  %s: %d", d, c)
    log.info("Done.")


if __name__ == "__main__":
    main()
