#!/usr/bin/env python3
"""ENE substrate migration + concept tagging (legacy shim).

NOTE (ontology migration):

This file is a **legacy shim** used to keep ENE substrate bootstrapping and
migration workflows running while the AVM / Lean-only ISA rewrite is underway.

**Target architecture:** Lean-only AVM ISA + backend shims.
- Lean defines all semantics.
- Shims perform I/O and orchestration only.

This script currently performs:
- schema application
- migration SQL
- tokenizer-based tagging
- relation building
- retention scoring

Several of those operations are semantic decisions and include float-based scoring.
They must be ported into Lean/AVM.

Rules until ported:
- Treat all outputs as **not promoted**.
- Never silently apply a different schema. If the schema file is missing: **reject**.

TODO(lean-port): Port tagging/relations/retention scoring into Lean/AVM.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import sys
from collections import Counter
from pathlib import Path

import psycopg2
import psycopg2.extras

from rds_connect import connect_rds

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ene_migrate")

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA_PATH = REPO_ROOT / "4-Infrastructure/shim/ene_substrate_schema.sql"
ONTOLOGY_VERSION = "shim-ontology-migration-v1"


def connect():
    return connect_rds()


def apply_schema(conn, schema_path: Path) -> None:
    """Apply the ENE substrate schema.

    Policy: never silently substitute an inline schema. If the schema file is
    missing, reject.
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"ENE schema file not found: {schema_path}")

    sql = schema_path.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    log.info("ENE substrate schema applied (%s)", schema_path)


# ---------------------------------------------------------------------------
# Term extraction (legacy tokenizer)
# ---------------------------------------------------------------------------
MATH_SYMBOL_RE = re.compile(
    r"\\\\(?:alpha|beta|gamma|Gamma|delta|Delta|epsilon|varepsilon|zeta|eta|theta|Theta|"
    r"iota|kappa|lambda|Lambda|mu|nu|xi|Xi|pi|Pi|rho|sigma|Sigma|tau|upsilon|phi|Phi|"
    r"varphi|chi|psi|Psi|omega|Omega|partial|nabla|infty|int|sum|prod|otimes|oplus|"
    r"rightarrow|leftarrow|Rightarrow|Leftarrow|mapsto|approx|equiv|sim|propto|"
    r"leq|geq|neq|times|cdot|circ|pm|mp|sqrt|frac|operatorname|mathbf|mathrm|mathcal|"
    r"mathfrak|mathbb|text|hat|tilde|bar|vec|dot|ddot|widehat|widetilde|"
    r"langle|rangle|lVert|rVert|vert|mid|"
    r"begin|end|left|right|big|Big|bigg|Bigg)"
)

TECHNICAL_RE = re.compile(
    r"\\b(?:"
    r"manifold|field|shear|packet|spectral|braid|gossip|"
    r"residual|invariant|receipt|scar|warden|collapse|compression|"
    r"entropy|eigen(?:value|vector)?|coboundary|cochain|"
    r"diffusion|transport|boundary|kernel|operator|"
    r"tensor|metric|geodesic|curvature|torsion|"
    r"hamiltonian|lagrangian|reduction|projection|embedding|"
    r"chirality|helicity|handedness|logogram|"
    r"sidon|goxel|famm|nuvmap|otom|pist|"
    r"erdos|szekeres|selfridge|gyarfas|"
    r"biocompression|organoid|chaos|fractal|attractor|basin|"
    r"thermal|thermodynamic|landauer|witness|shadow|adversarial|"
    r"morph(?:ic|ism)?|radix|codec|semantic|"
    r"markov|cognitive|attention|neural|network|transformer|"
    r"hutter|prize|betti|homology|cohomology|"
    r"riccati|noise|mfg|hessian|jacobian|"
    r"seam|tomography|sandwich|pruning|rope|scar|"
    r"eigensolid|eigenspace|underverse|geocognition|"
    r"smallcode|constrained|key.value|shortcut|ontology|"
    r"hyperbolic|riemannian|poincare|"
    r"bio|dna|rna|protein|feynman|navier|stokes|"
    r"plasma|mhd|alfven|"
    r"q16|fixed.point|subleq|oisc|kv|cache"
    r")\\b",
    re.IGNORECASE,
)

TOKEN_RE = re.compile(
    r"[a-zA-Z_\\\\][a-zA-Z0-9_\\\\]*|\\b(?:N-space|key-value|CP-SAT|Anti-FAMM|Anti-Braid)\\b",
    re.IGNORECASE,
)
STOP_WORDS = set(
    "the a an is are was were be been being have has had do does did will would shall should may might must can could of in to for with on at by from as into through during and but or not no nor so if then else when where this that these those it its we they which who what how why also more most some any all each every both few new other such only own same just about over text rm sf tt em sc up use using used one two etc via per eg ie figure table section doi url http https www paper result method approach model data set page pages vol pp et al note notes example see shown fig eq ref abstract introduction conclusion reference references arxiv org github com html pdf first second third following based given found obtained described proposed well within without between among under above below since however therefore thus still yet here there now then than"
    .split()
)


def tokenize(text: str) -> list[str]:
    if not text:
        return []
    seen: set[str] = set()
    results: list[str] = []
    for m in TOKEN_RE.finditer(text):
        t = (
            m.group(0)
            .strip()
            .lower()
            .rstrip(".,;:!?\"'()[]{}")
            .lstrip("\\\\")
            .rstrip("{}")
        )
        if not t or t in STOP_WORDS or len(t) < 2 or t in seen:
            continue
        seen.add(t)
        results.append(t)
    return results


# ---------------------------------------------------------------------------
# Migration
# ---------------------------------------------------------------------------
def migrate_all_sources(conn) -> int:
    """Migrate knowledge.* tables into ene.packages with typed provenance."""
    cur = conn.cursor()
    total = 0

    migrations = [
        (
            "equations",
            """
            INSERT INTO ene.packages (pkg, package_type, title, content, content_hash, tags, source, domain, provenance, promotion_state)
            SELECT eq_id::text, 'equation', latex, latex, content_hash, '[]'::jsonb, source_file, 'equation_corpus',
                   jsonb_build_object('kind', kind, 'source_file', source_file, 'source_offset', source_offset),
                   'held'
            FROM knowledge.equations
            ON CONFLICT (pkg) DO UPDATE SET
                title = EXCLUDED.title, content = EXCLUDED.content,
                content_hash = EXCLUDED.content_hash, tags = EXCLUDED.tags
            """,
        ),
        (
            "tiddlywiki_pages",
            """
            INSERT INTO ene.packages (pkg, package_type, title, content, content_hash, tags, source, domain, provenance, promotion_state)
            SELECT tiddler_id::text, 'tiddler', title, coalesce(body,''),
                   content_hash, '[]'::jsonb, source_path, 'tiddlywiki',
                   jsonb_build_object('tags', tags, 'created', created, 'modified', modified, 'source_path', source_path),
                   'held'
            FROM knowledge.tiddlywiki_pages
            ON CONFLICT (pkg) DO UPDATE SET
                title = EXCLUDED.title, content = EXCLUDED.content,
                content_hash = EXCLUDED.content_hash, tags = EXCLUDED.tags
            """,
        ),
        (
            "references",
            """
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
            """,
        ),
        (
            "links",
            """
            INSERT INTO ene.packages (pkg, package_type, title, content, content_hash, tags, source, domain, provenance, promotion_state)
            SELECT link_id::text, 'link', url, url, encode(sha256(url::bytea),'hex'), '[]'::jsonb, source_file,
                   'external_reference',
                   jsonb_build_object('url', url, 'source_file', source_file),
                   'held'
            FROM knowledge.links
            ON CONFLICT (pkg) DO UPDATE SET
                title = EXCLUDED.title, content = EXCLUDED.content
            """,
        ),
        (
            "article_sources",
            """
            INSERT INTO ene.packages (pkg, package_type, title, content, content_hash, tags, source, domain, provenance, promotion_state)
            SELECT article_id::text, 'article', coalesce(label, url), coalesce(label,'') || ' ' || url,
                   encode(sha256(url::bytea),'hex'), '[]'::jsonb, url, 'article_source',
                   jsonb_build_object('url', url, 'label', label, 'category', category),
                   'held'
            FROM knowledge.article_sources
            ON CONFLICT (pkg) DO UPDATE SET
                title = EXCLUDED.title, content = EXCLUDED.content
            """,
        ),
        (
            "dois",
            """
            INSERT INTO ene.packages (pkg, package_type, title, content, content_hash, tags, source, domain, provenance, promotion_state)
            SELECT doi_id::text, 'doi', doi, doi, encode(sha256(doi::bytea),'hex'), '[]'::jsonb, source_file, 'doi_identifier',
                   jsonb_build_object('doi', doi, 'source_file', source_file),
                   'held'
            FROM knowledge.dois
            ON CONFLICT (pkg) DO UPDATE SET
                title = EXCLUDED.title, content = EXCLUDED.content
            """,
        ),
        (
            "dataset_inventory",
            """
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
            """,
        ),
    ]

    for src_table, insert_sql in migrations:
        cur.execute(f"SELECT COUNT(*) FROM knowledge.{src_table}")
        count = int(cur.fetchone()[0])
        cur.execute(insert_sql)
        total += count
        log.info("Migrated %s → ene.packages (%d rows)", src_table, count)

    conn.commit()
    log.info("Total packages migrated: %d", total)
    return total


def tag_packages(conn) -> int:
    """Extract terms from package content and store concept_vector + tags JSONB.

    NOTE: This is semantic classification logic and must be ported to Lean/AVM.
    """
    cur = conn.cursor()

    cur.execute(
        "SELECT pkg, package_type, coalesce(content,''), coalesce(title,'') FROM ene.packages WHERE content IS NOT NULL AND content != ''"
    )
    packages = cur.fetchall()

    updated = 0
    for pkg, pkg_type, content, title in packages:
        terms = tokenize(content + " " + title)
        if not terms:
            continue

        math_terms = [t for t in terms if MATH_SYMBOL_RE.fullmatch(t)]
        tech_terms = [t for t in terms if TECHNICAL_RE.search(t)]
        all_terms = list(dict.fromkeys(terms))

        concept_vector = [
            {
                "term": t,
                "type": "math_symbol" if t in math_terms else "technical_term" if t in tech_terms else "keyword",
            }
            for t in all_terms[:50]
        ]
        tags = all_terms[:20]

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


def build_relations(conn) -> int:
    """Build ene.relations between packages that share concepts across domains.

    NOTE: This is semantic graph construction logic and must be ported to Lean/AVM.
    """
    cur = conn.cursor()

    cur.execute(
        "SELECT pkg, concept_vector, domain FROM ene.packages WHERE concept_vector IS NOT NULL AND jsonb_array_length(concept_vector) > 0"
    )
    packages = cur.fetchall()
    log.info("Building relations from %d tagged packages…", len(packages))

    term_index: dict[str, list[tuple[str, str]]] = {}
    for pkg, cv, domain in packages:
        if cv is None:
            continue
        concepts = json.loads(cv) if isinstance(cv, str) else cv
        for c in concepts:
            term = c["term"].lower()
            term_index.setdefault(term, []).append((pkg, domain or "unknown"))

    relation_count = 0
    for term, pkgs in term_index.items():
        if len(pkgs) < 2:
            continue
        for i, (p1, d1) in enumerate(pkgs):
            for j in range(i + 1, len(pkgs)):
                p2, d2 = pkgs[j]
                if d1 == d2:
                    continue
                rel_type = "shares_concept"
                cur.execute(
                    """INSERT INTO ene.relations (source_id, target_id, relation_type, weight)
                       VALUES (%s,%s,%s,1.0)
                       ON CONFLICT DO NOTHING""",
                    (p1, p2, rel_type),
                )
                if cur.rowcount > 0:
                    relation_count += 1
        if relation_count and relation_count % 2000 == 0:
            conn.commit()
            log.info("  %d relations…", relation_count)

    conn.commit()
    log.info("Built %d cross-domain relations", relation_count)
    return relation_count


def score_nspace_kv(conn) -> int:
    """Compute retention scoring for packages.

    WARNING: This function currently uses float arithmetic via Postgres casts.
    It must be ported into Lean/AVM fixed-point semantics.
    """
    cur = conn.cursor()

    cur.execute(
        """
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
        """
    )
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM ene.nspace_kv")
    nv = int(cur.fetchone()[0])
    log.info("Scored %d packages with N-space KV retention", nv)
    return nv


def run_discovery_queries(conn) -> dict[str, list[tuple]]:
    """Run cross-source discovery queries and log groupings."""
    cur = conn.cursor()

    queries = [
        (
            "domains_sharing_most_concepts",
            """
            SELECT r.relation_type, p1.domain AS domain_a, p2.domain AS domain_b,
                   COUNT(*) AS pair_count,
                   COUNT(DISTINCT r.source_id) + COUNT(DISTINCT r.target_id) AS packages_involved
            FROM ene.relations r
            JOIN ene.packages p1 ON p1.pkg = r.source_id
            JOIN ene.packages p2 ON p2.pkg = r.target_id
            GROUP BY r.relation_type, p1.domain, p2.domain
            ORDER BY pair_count DESC
            LIMIT 20
            """,
        ),
    ]

    results: dict[str, list[tuple]] = {}
    for key, query in queries:
        cur.execute(query)
        rows = cur.fetchall()
        results[key] = rows
        log.info("Query %s returned %d rows", key, len(rows))

    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Migrate knowledge.* tables → ENE substrate with concept tagging.")
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA_PATH)
    parser.add_argument("--skip-tagging", action="store_true")
    parser.add_argument("--skip-relations", action="store_true")
    parser.add_argument("--skip-retention", action="store_true")
    args = parser.parse_args(argv)

    log.info("Connecting to RDS…")
    conn = connect()
    conn.autocommit = False

    try:
        log.info("Phase 1: Apply ENE substrate schema")
        apply_schema(conn, args.schema)

        log.info("Phase 2: Migrate knowledge.* → ene.packages")
        migrate_all_sources(conn)

        if not args.skip_tagging:
            log.info("Phase 3: Extract concepts and tag packages")
            tag_packages(conn)

        if not args.skip_relations:
            log.info("Phase 4: Build cross-domain relations")
            build_relations(conn)

        if not args.skip_retention:
            log.info("Phase 5: Score N-space KV retention")
            score_nspace_kv(conn)

        log.info("Phase 6: Run discovery queries")
        run_discovery_queries(conn)

        log.info("Done.")
        return 0

    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())


# ---------------------------------------------------------------------------
# Shim strip receipt (non-authoritative conversion surface)
# ---------------------------------------------------------------------------
STRIP_RECEIPT = {
    "ontology_version": ONTOLOGY_VERSION,
    "shim_role": "legacy_ene_migration_and_tagging_pending_avm",
    "computed_in_shim": [
        "tokenize / concept tagging",
        "relation building",
        "retention scoring",
        "schema orchestration",
    ],
    "must_port_to_lean_avm": [
        "tokenization policy (finite types, no open strings)",
        "relation scoring (fixed-point)",
        "retention scoring (fixed-point)",
        "all semantic decisions",
    ],
    "float_policy": {
        "status": "float_present_in_sql_scoring",
        "reason": "ene.nspace_kv scoring uses Postgres float casts; must be ported",
    },
}
