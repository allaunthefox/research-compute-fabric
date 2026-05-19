#!/usr/bin/env python3
"""
Aggressive cross-source concept tagging and relationship discovery against RDS.

1. Extracts normalized terms from all ingested sources
2. Cross-references across equation ↔ tiddlywiki ↔ reference ↔ link ↔ dataset
3. Builds a concept lattice: concept_tags, source_mentions, cross_triples
4. Runs clustering queries to surface unexpected groupings

Run in dev container:
  podman exec -e AWS_ACCESS_KEY_ID=... -e AWS_SECRET_ACCESS_KEY=... -e AWS_REGION=us-east-1 -e RDS_IAM=1 \
    research-stack python3 /home/researcher/stack/4-Infrastructure/shim/concept_cross_reference.py
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
from typing import Iterable

import boto3
import psycopg2
import psycopg2.extras

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("concept_xref")

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


def ensure_schema(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS knowledge.concept_tags (
            concept_id      uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
            term            text        NOT NULL,
            normalized      text        NOT NULL,
            term_type       text        NOT NULL,  -- 'math_symbol', 'technical_term', 'named_entity', 'domain_label'
            frequency       integer     NOT NULL DEFAULT 0,
            sources         text[]      NOT NULL DEFAULT '{}',  -- which tables it appears in
            created_at      timestamptz NOT NULL DEFAULT now()
        );
        CREATE UNIQUE INDEX IF NOT EXISTS concept_norm_idx ON knowledge.concept_tags (normalized);

        CREATE TABLE IF NOT EXISTS knowledge.source_mentions (
            mention_id      uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
            concept_id      uuid        NOT NULL REFERENCES knowledge.concept_tags(concept_id) ON DELETE CASCADE,
            source_table    text        NOT NULL,  -- 'equations','tiddlywiki_pages','references','dois','links','article_sources'
            source_id       uuid        NOT NULL,
            term_raw        text        NOT NULL,
            context_snippet text,
            position        integer,
            ingested_at     timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS sm_concept_idx ON knowledge.source_mentions (concept_id);
        CREATE INDEX IF NOT EXISTS sm_source_idx ON knowledge.source_mentions (source_table, source_id);

        CREATE TABLE IF NOT EXISTS knowledge.cross_triples (
            triple_id       uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
            concept_id       uuid        NOT NULL REFERENCES knowledge.concept_tags(concept_id),
            source_a_table  text        NOT NULL,
            source_a_id     uuid        NOT NULL,
            source_b_table  text        NOT NULL,
            source_b_id     uuid        NOT NULL,
            cooccurrence    integer     NOT NULL DEFAULT 1,
            discovered_at   timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS ct_concept_idx ON knowledge.cross_triples (concept_id);
        CREATE INDEX IF NOT EXISTS ct_pair_idx ON knowledge.cross_triples (source_a_table, source_a_id, source_b_table, source_b_id);

        CREATE TABLE IF NOT EXISTS knowledge.concept_clusters (
            cluster_id      uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
            cluster_label   text        NOT NULL,
            concept_ids     uuid[]      NOT NULL,
            dominant_terms  text[]      NOT NULL,
            size            integer     NOT NULL,
            cohesion_score  float8      NOT NULL DEFAULT 0,
            cross_sources   text[]      NOT NULL,
            created_at      timestamptz NOT NULL DEFAULT now()
        );
    """)
    conn.commit()
    log.info("Schema ready")


# ---------------------------------------------------------------------------
# Term extraction
# ---------------------------------------------------------------------------
MATH_SYMBOL_RE = re.compile(
    r'\\(?:alpha|beta|gamma|Gamma|delta|Delta|epsilon|varepsilon|zeta|eta|theta|Theta|'
    r'iota|kappa|lambda|Lambda|mu|nu|xi|Xi|pi|Pi|rho|sigma|Sigma|tau|upsilon|phi|Phi|'
    r'varphi|chi|psi|Psi|omega|Omega|partial|nabla|infty|int|sum|prod|otimes|oplus|'
    r'rightarrow|leftarrow|Rightarrow|Leftarrow|mapsto|approx|equiv|sim|propto|'
    r'leq|geq|neq|times|cdot|circ|pm|mp|sqrt|frac|operatorname|mathbf|mathrm|mathcal|'
    r'mathfrak|mathbb|text|hat|tilde|bar|vec|dot|ddot|widehat|widetilde|'
    r'emptyset|forall|exists|nexists|in|notin|subset|subseteq|supset|supseteq|'
    r'cup|cap|setminus|wedge|vee|neg|implies|iff|top|bot|land|lor|'
    r'langle|rangle|lVert|rVert|vert|Vert|mid|'
    r'underbrace|overbrace|stackrel|limits|nolimits|'
    r'textup|textrm|textsf|texttt|textnormal|'
    r'begin|end|item|label|ref|cite|'
    r'left|right|big|Big|bigg|Bigg)'
)
TECHNICAL_WORD_RE = re.compile(
    r'\b(?:'
    r'manifold|field|shear|packet|spectral|braid|gossip|'
    r'residual|invariant|receipt|scar|warden|collapse|compression|'
    r'entropy|eigen|eigenvalue|eigenvector|coboundary|cochain|'
    r'diffusion|transport|boundary|kernel|operator|'
    r'tensor|metric|geodesic|curvature|torsion|'
    r'quantum|classical|hamiltonian|lagrangian|'
    r'reduction|projection|embedding|immersion|'
    r'chirality|helicity|handedness|logogram|'
    r'sidon|goxel|famm|nuvmap|otom|pist|'
    r'erdos|szekeres|selfridge|gyarfas|'
    r'biocompression|biocompress|organoid|'
    r'chaos|fractal|attractor|basin|'
    r'thermal|thermodynamic|landauer|'
    r'witness|shadow|adversarial|'
    r'morph|morphic|morphism|'
    r'radix|codec|codec|semantic|'
    r'markov|cognitive|attention|'
    r'lattice|algebra|topology|topos|'
    r'proof|theorem|lemma|corollary|'
    r'neural|network|transformer|'
    r'hutter|compression|prize|'
    r'bio|dna|rna|protein|'
    r'feynman|navier|stokes|'
    r'plasma|mhd|alfven|'
    r'betti|homology|cohomology|'
    r'riccati|noise|mfg|'
    r'hessian|jacobian|'
    r'seam|tomography|sandwich|'
    r'pruning|rope|scar|'
    r'eigensolid|eigenspace|'
    r'underverse|geocognition|'
    r'smallcode|constrained|'
    r'\bN\s*space\b|key.value|'
    r'shortcut|ontology|'
    r'hyperbolic|riemannian|poincare'
    r')\b',
    re.IGNORECASE,
)
TOKEN_RE = re.compile(r'[a-zA-Z_\\][a-zA-Z0-9_\\]*|\b(?:N-space|key-value|CP-SAT|Anti-FAMM|Anti-Braid)\b', re.IGNORECASE)

STOP_WORDS = {
    "the","a","an","is","are","was","were","be","been","being","have","has","had",
    "do","does","did","will","would","shall","should","may","might","must","can","could",
    "of","in","to","for","with","on","at","by","from","as","into","through","during",
    "and","but","or","not","no","nor","so","if","then","else","when","where",
    "this","that","these","those","it","its","we","they","he","she",
    "which","who","whom","whose","what","how","why",
    "also","very","more","most","some","any","all","each","every","both","few",
    "new","other","such","only","own","same","just","about","over",
    "text","bf","rm","sf","tt","em","sc","it","up",
    "use","using","used","can","one","two","also",
    "etc","via","per","e.g","i.e","figure","table","section",
    "non","doi","url","http","https","www",
    "paper","result","method","approach","model","data","set",
    "page","pages","vol","pp","et","al",
    "note","notes","example","see","shown","fig","eq","ref",
    "abstract","introduction","conclusion","reference","references",
    "arxiv","org","github","com","html","pdf",
    "first","second","third","following","followed",
    "based","given","found","obtained","described","proposed",
    "well","within","without","between","among","under","above","below",
    "since","however","therefore","thus","still","yet",
    "does","don","doesn","did","didn","has","haven","hadn",
    "here","there","where","now","then","than",
    "get","got","getting","make","made","making",
    "take","taken","taking","give","given","giving",
    "let","lets","case","cases","term","terms","form","forms",
    "number","numbers","value","values","point","points",
    "part","parts","type","types","kind","kinds","way","ways",
    "much","many","long","short","high","low","large","small",
    "different","similar","same","total","whole","full",
    "work","works","working","need","needs","needed",
    "help","helps","helped","like","likes","liked",
    "know","known","unknown","think","thought","believe",
    "want","wants","wanted","try","tries","tried",
}


def tokenize(text: str) -> Iterable[str]:
    """Split text into normalized tokens, filtering stop words."""
    for m in TOKEN_RE.finditer(text):
        t = m.group(0).strip().lower().rstrip(".,;:!?\"'()[]{}")
        if not t or t in STOP_WORDS or len(t) < 2:
            continue
        # Clean LaTeX residue
        t = t.lstrip("\\").rstrip("{}")
        if not t or t in STOP_WORDS or len(t) < 2:
            continue
        yield t


def classify_term(term: str, text: str) -> str:
    """Classify term as math_symbol, technical_term, named_entity, or domain_label."""
    if MATH_SYMBOL_RE.fullmatch(term):
        return "math_symbol"
    if TECHNICAL_WORD_RE.search(term):
        return "technical_term"
    # Capitalized word or LaTeX \command suggests math symbol
    if term.startswith("\\") or (term[0].isupper() and len(term) <= 3 and term.isalpha()):
        return "math_symbol"
    return "technical_term"


def extract_terms(text: str) -> list[tuple[str, str]]:
    """Return list of (raw_term, term_type) tuples."""
    results: list[tuple[str, str]] = []
    seen: set[str] = set()
    for tok in tokenize(text):
        if tok in seen:
            continue
        seen.add(tok)
        ttype = classify_term(tok, text)
        results.append((tok, ttype))
    return results


# ---------------------------------------------------------------------------
# Cross-referencing
# ---------------------------------------------------------------------------
def fetch_and_tag(conn):
    """Extract terms from all sources and populate concept_tags + source_mentions."""
    cur = conn.cursor()

    # Clear previous run (idempotent for re-runs)
    cur.execute("TRUNCATE knowledge.source_mentions, knowledge.cross_triples CASCADE")
    cur.execute("DELETE FROM knowledge.concept_tags")

    # Map: normalized_term -> concept_id
    concept_map: dict[str, uuid.UUID] = {}

    sources = [
        ("equations", "SELECT eq_id, latex, source_file FROM knowledge.equations"),
        ("tiddlywiki_pages", "SELECT tiddler_id, body || ' ' || tags, title FROM knowledge.tiddlywiki_pages"),
        ("references", "SELECT ref_id, bibtex, source_file FROM knowledge.references"),
        ("links", "SELECT link_id, url, source_file FROM knowledge.links"),
        ("article_sources", "SELECT article_id, url || ' ' || coalesce(label,''), coalesce(label,'') FROM knowledge.article_sources"),
        ("dois", "SELECT doi_id, doi, source_file FROM knowledge.dois"),
        ("dataset_inventory", "SELECT inv_id, coalesce(name,'') || ' ' || coalesce(evidence,'') || ' ' || coalesce(notes,''), coalesce(name,'') FROM knowledge.dataset_inventory"),
    ]

    total_mentions = 0

    for src_table, query in sources:
        cur.execute(query)
        rows = cur.fetchall()
        log.info("Processing %s: %d rows", src_table, len(rows))

        for row in rows:
            source_id = row[0]
            text = row[1] if row[1] else ""
            label = row[2] if len(row) > 2 and row[2] else ""

            terms = extract_terms(text)
            for raw_term, ttype in terms:
                norm = raw_term.lower().strip("\\{}")

                # Get or create concept
                if norm not in concept_map:
                    cur.execute(
                        """INSERT INTO knowledge.concept_tags (term, normalized, term_type, frequency, sources)
                           VALUES (%s,%s,%s,1,ARRAY[%s])
                           ON CONFLICT (normalized) DO UPDATE SET
                               frequency = concept_tags.frequency + 1,
                               sources = array_append(concept_tags.sources, %s)
                           RETURNING concept_id""",
                        (raw_term, norm, ttype, src_table, src_table),
                    )
                    cid = cur.fetchone()[0]
                    concept_map[norm] = cid
                else:
                    cid = concept_map[norm]
                    cur.execute(
                        """UPDATE knowledge.concept_tags
                           SET frequency = frequency + 1,
                               sources = CASE WHEN NOT (%s = ANY(sources)) THEN array_append(sources, %s) ELSE sources END
                           WHERE concept_id = %s""",
                        (src_table, src_table, cid),
                    )

                # Record mention
                snippet = text[max(0, text.lower().find(raw_term.lower()) - 60):
                              min(len(text), text.lower().find(raw_term.lower()) + 60)]
                cur.execute(
                    """INSERT INTO knowledge.source_mentions (concept_id, source_table, source_id, term_raw, context_snippet)
                       VALUES (%s,%s,%s,%s,%s)""",
                    (cid, src_table, source_id, raw_term, snippet),
                )
                total_mentions += 1

            if total_mentions % 5000 == 0:
                conn.commit()
                log.info("  %d mentions processed…", total_mentions)

    conn.commit()
    log.info("Total concepts: %d, total mentions: %d", len(concept_map), total_mentions)
    return total_mentions


def build_cross_triples(conn):
    """For each concept that appears in 2+ sources, create cross triples between every pair of source items."""
    cur = conn.cursor()

    cur.execute("""
        SELECT concept_id, array_agg(DISTINCT source_table) AS src_tables,
               array_agg(DISTINCT source_id) AS src_ids
        FROM knowledge.source_mentions
        GROUP BY concept_id
        HAVING count(DISTINCT source_table) >= 2
    """)
    concepts = cur.fetchall()
    log.info("Cross-referencing %d multi-source concepts…", len(concepts))

    triple_count = 0
    for cid, src_tables, src_ids in concepts:
        # Build cross triples: for each concept, link every source item pair
        # that shares this concept but comes from different source tables
        cur.execute("""
            SELECT DISTINCT sm1.source_table, sm1.source_id,
                            sm2.source_table, sm2.source_id
            FROM knowledge.source_mentions sm1
            JOIN knowledge.source_mentions sm2
              ON sm1.concept_id = sm2.concept_id
             AND sm1.source_table < sm2.source_table
             AND sm1.source_id != sm2.source_id
            WHERE sm1.concept_id = %s
        """, (cid,))
        pairs = cur.fetchall()
        for sa_table, sa_id, sb_table, sb_id in pairs:
            cur.execute(
                """INSERT INTO knowledge.cross_triples (concept_id, source_a_table, source_a_id, source_b_table, source_b_id)
                   VALUES (%s,%s,%s,%s,%s)
                   ON CONFLICT DO NOTHING""",
                (cid, sa_table, sa_id, sb_table, sb_id),
            )
            triple_count += 1

        if triple_count % 2000 == 0:
            conn.commit()
            log.info("  %d triples…", triple_count)

    conn.commit()
    log.info("Cross triples: %d", triple_count)
    return triple_count


def discover_clusters(conn, min_cohesion: float = 0.3, max_clusters: int = 50):
    """Use cross triples to discover concept clusters via shared-source density."""
    cur = conn.cursor()

    # Approach: find concepts that co-occur with the same source items
    # A cluster forms when multiple concepts share the same cross-source item pairs
    cur.execute("""
        WITH concept_pairs AS (
            SELECT ct1.concept_id AS c1, ct2.concept_id AS c2,
                   ct1.source_a_table, ct1.source_a_id,
                   ct1.source_b_table, ct1.source_b_id,
                   COUNT(*) AS shared_instances
            FROM knowledge.cross_triples ct1
            JOIN knowledge.cross_triples ct2
              ON ct1.source_a_table = ct2.source_a_table
             AND ct1.source_a_id = ct2.source_a_id
             AND ct1.source_b_table = ct2.source_b_table
             AND ct1.source_b_id = ct2.source_b_id
             AND ct1.concept_id < ct2.concept_id
            WHERE ct1.concept_id != ct2.concept_id
            GROUP BY 1,2,3,4,5,6
        ),
        concept_cohesion AS (
            SELECT c1, c2, COUNT(*) AS shared_pairs,
                   ARRAY_AGG(DISTINCT source_a_table || '-' || source_b_table) AS cross_source_pairs
            FROM concept_pairs
            GROUP BY c1, c2
            HAVING COUNT(*) >= 2
            ORDER BY shared_pairs DESC
        )
        SELECT cc.c1, cc.c2, cc.shared_pairs, cc.cross_source_pairs,
               t1.normalized AS term_a, t2.normalized AS term_b,
               t1.sources AS sources_a, t2.sources AS sources_b
        FROM concept_cohesion cc
        JOIN knowledge.concept_tags t1 ON t1.concept_id = cc.c1
        JOIN knowledge.concept_tags t2 ON t2.concept_id = cc.c2
        ORDER BY cc.shared_pairs DESC
        LIMIT %s
    """, (max_clusters * 2,))

    pairs = cur.fetchall()
    log.info("Found %d high-cohesion concept pairs", len(pairs))

    # Greedy cluster assignment
    cluster_map: dict[uuid.UUID, uuid.UUID] = {}
    clusters: dict[uuid.UUID, dict] = {}

    for c1, c2, shared, xsources, term_a, term_b, sources_a, sources_b in pairs:
        c1_cluster = cluster_map.get(c1)
        c2_cluster = cluster_map.get(c2)

        if c1_cluster and c2_cluster:
            if c1_cluster != c2_cluster:
                # Merge: combine smaller into larger
                ca = clusters[c1_cluster]
                cb = clusters[c2_cluster]
                if ca["size"] >= cb["size"]:
                    _merge_cluster(ca, cb, cluster_map)
                    del clusters[c2_cluster]
                else:
                    _merge_cluster(cb, ca, cluster_map)
                    del clusters[c1_cluster]
        elif c1_cluster:
            _add_to_cluster(clusters[c1_cluster], c2, term_b, sources_b, c2_cluster)
            cluster_map[c2] = c1_cluster
        elif c2_cluster:
            _add_to_cluster(clusters[c2_cluster], c1, term_a, sources_a, c1_cluster)
            cluster_map[c1] = c2_cluster
        else:
            # New cluster
            cid = uuid.uuid4()
            sources_set = set(list(sources_a) + list(sources_b) + [xs.split("-")[0] for xs in xsources] + [xs.split("-")[1] if "-" in xs else "" for xs in xsources])
            clusters[cid] = {
                "concept_ids": [c1, c2],
                "terms": [term_a, term_b],
                "cross_sources": list(sources_set - {""}),
                "size": 2,
            }
            cluster_map[c1] = cid
            cluster_map[c2] = cid

    # Persist clusters
    cluster_count = 0
    for cid, cdata in clusters.items():
        if cdata["size"] < 3:
            continue
        # Compute approximate cohesion score
        cohesion = min(1.0, cdata["size"] / 10.0)
        cur.execute(
            """INSERT INTO knowledge.concept_clusters
               (cluster_id, cluster_label, concept_ids, dominant_terms, size, cohesion_score, cross_sources)
               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (cid, cdata["terms"][0], cdata["concept_ids"], cdata["terms"],
             cdata["size"], cohesion, cdata["cross_sources"]),
        )
        cluster_count += 1

    conn.commit()
    log.info("Persisted %d concept clusters", cluster_count)
    return cluster_count


def _merge_cluster(into: dict, other: dict, cluster_map: dict):
    into["concept_ids"].extend(other["concept_ids"])
    into["terms"].extend(other["terms"])
    into["cross_sources"] = list(set(into["cross_sources"] + other["cross_sources"]))
    into["size"] += other["size"]
    for cid in other["concept_ids"]:
        cluster_map[cid] = cluster_map[into["concept_ids"][0]] if into["concept_ids"] else None


def _add_to_cluster(cdata: dict, cid, term, sources, _old_cluster):
    cdata["concept_ids"].append(cid)
    cdata["terms"].append(term)
    cdata["cross_sources"] = list(set(cdata["cross_sources"] + list(sources)))
    cdata["size"] += 1


def run_exploratory_queries(conn):
    """Run and log interesting cross-source discovery queries."""
    cur = conn.cursor()

    queries = [
        ("Top concepts by cross-source span",
         """SELECT ct.normalized, ct.term_type, ct.frequency,
                   array_length(ct.sources, 1) AS source_count,
                   COUNT(DISTINCT sm.source_table) AS actual_sources
            FROM knowledge.concept_tags ct
            JOIN knowledge.source_mentions sm ON sm.concept_id = ct.concept_id
            GROUP BY ct.concept_id, ct.normalized, ct.term_type, ct.frequency, ct.sources
            ORDER BY actual_sources DESC, ct.frequency DESC
            LIMIT 30"""),

        ("Cross-source pairs that share the most concepts",
         """SELECT ct.source_a_table, ct.source_b_table,
                   COUNT(DISTINCT ct.concept_id) AS shared_concepts,
                   COUNT(*) AS total_pairs
            FROM knowledge.cross_triples ct
            GROUP BY ct.source_a_table, ct.source_b_table
            ORDER BY shared_concepts DESC
            LIMIT 20"""),

        ("Equations referencing tiddlywiki concepts",
         """SELECT sm1.source_id AS tw_id, tw.title, sm2.source_id AS eq_id,
                   eq.latex, ct.normalized AS shared_concept
            FROM knowledge.cross_triples ct
            JOIN knowledge.source_mentions sm1 ON sm1.concept_id = ct.concept_id AND sm1.source_table = 'tiddlywiki_pages'
            JOIN knowledge.source_mentions sm2 ON sm2.concept_id = ct.concept_id AND sm2.source_table = 'equations'
            JOIN knowledge.tiddlywiki_pages tw ON tw.tiddler_id = sm1.source_id
            JOIN knowledge.equations eq ON eq.eq_id = sm2.source_id
            LIMIT 30"""),

        ("References linked to datasets via shared concepts",
         """SELECT ct.normalized,
                   r.bibtex AS ref_bibtex,
                   di.name AS dataset_name
            FROM knowledge.cross_triples ct
            JOIN knowledge.source_mentions sm1 ON sm1.concept_id = ct.concept_id AND sm1.source_table = 'references'
            JOIN knowledge.source_mentions sm2 ON sm2.concept_id = ct.concept_id AND sm2.source_table = 'dataset_inventory'
            JOIN knowledge.references r ON r.ref_id = sm1.source_id
            JOIN knowledge.dataset_inventory di ON di.inv_id = sm2.source_id
            LIMIT 30"""),

        ("TiddlyWiki pages bridging multiple datasets via shared concepts",
         """SELECT tw.title,
                   array_agg(DISTINCT di.name) AS linked_datasets,
                   array_agg(DISTINCT ct.normalized) AS shared_concepts,
                   COUNT(DISTINCT di.inv_id) AS dataset_count
            FROM knowledge.source_mentions stw
            JOIN knowledge.source_mentions sdi
              ON stw.concept_id = sdi.concept_id
             AND stw.source_table = 'tiddlywiki_pages'
             AND sdi.source_table = 'dataset_inventory'
            JOIN knowledge.tiddlywiki_pages tw ON tw.tiddler_id = stw.source_id
            JOIN knowledge.dataset_inventory di ON di.inv_id = sdi.source_id
            JOIN knowledge.concept_tags ct ON ct.concept_id = stw.concept_id
            GROUP BY tw.tiddler_id, tw.title
            HAVING COUNT(DISTINCT di.inv_id) >= 2
            ORDER BY dataset_count DESC
            LIMIT 30"""),

        ("Most connected concepts (hub scores)",
         """SELECT ct.normalized, ct.term_type,
                   COUNT(DISTINCT sm.source_table) AS source_types,
                   COUNT(DISTINCT sm.source_id) AS items_linked,
                   COUNT(DISTINCT cl.cluster_id) AS clusters
            FROM knowledge.concept_tags ct
            LEFT JOIN knowledge.source_mentions sm ON sm.concept_id = ct.concept_id
            LEFT JOIN knowledge.concept_clusters cl ON ct.concept_id = ANY(cl.concept_ids)
            GROUP BY ct.concept_id, ct.normalized, ct.term_type
            ORDER BY items_linked DESC
            LIMIT 30"""),

        ("Concept clusters with most diverse cross-source provenance",
         """SELECT cc.cluster_label, cc.size, cc.cohesion_score,
                   cc.dominant_terms[1:5] AS top_terms,
                   cc.cross_sources
            FROM knowledge.concept_clusters cc
            ORDER BY array_length(cc.cross_sources, 1) DESC, cc.size DESC
            LIMIT 20"""),

        ("Unexpected equation-tiddler-DOI triples",
         """SELECT eq.latex, tw.title, d.doi, ct.normalized
            FROM knowledge.source_mentions sm_eq
            JOIN knowledge.source_mentions sm_tw
              ON sm_eq.concept_id = sm_tw.concept_id
             AND sm_eq.source_table = 'equations'
             AND sm_tw.source_table = 'tiddlywiki_pages'
            LEFT JOIN knowledge.source_mentions sm_doi
              ON sm_eq.concept_id = sm_doi.concept_id
             AND sm_doi.source_table = 'dois'
            JOIN knowledge.equations eq ON eq.eq_id = sm_eq.source_id
            JOIN knowledge.tiddlywiki_pages tw ON tw.tiddler_id = sm_tw.source_id
            LEFT JOIN knowledge.dois d ON d.doi_id = sm_doi.source_id
            JOIN knowledge.concept_tags ct ON ct.concept_id = sm_eq.concept_id
            WHERE sm_doi.concept_id IS NOT NULL
            LIMIT 30"""),
    ]

    for title, query in queries:
        cur.execute(query)
        rows = cur.fetchall()
        log.info("\n=== %s (%d results) ===", title, len(rows))
        for i, row in enumerate(rows):
            if i >= 10:
                log.info("  ... + %d more", len(rows) - 10)
                break
            log.info("  %s", " | ".join(str(c) for c in row))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    log.info("Connecting to RDS…")
    conn = connect()
    conn.autocommit = False
    ensure_schema(conn)

    log.info("Phase 1: Extract terms and tag all sources")
    mentions = fetch_and_tag(conn)

    log.info("Phase 2: Build cross-references triples")
    triples = build_cross_triples(conn)

    log.info("Phase 3: Discover concept clusters")
    clusters = discover_clusters(conn, min_cohesion=0.3, max_clusters=50)

    log.info("Phase 4: Exploratory queries")
    run_exploratory_queries(conn)

    conn.close()
    log.info("Done. mentions=%d triples=%d clusters=%d", mentions, triples, clusters)


if __name__ == "__main__":
    main()
