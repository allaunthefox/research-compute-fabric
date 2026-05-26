#!/usr/bin/env python3
"""
Bulk dataset ingestion → Aurora PostgreSQL.

Sources:
  1. consolidated equations bundle (equations/refs/links/dois/articles)
  2. consolidated dataset inventory (161-file artifact manifest)
  3. TiddlyWiki tiddlers (263 .tid files)
  4. Γ-packet seed data

Each run recorded in ingestion.receipts.

Run inside the dev container:
  podman exec -i research-stack python3 /home/researcher/stack/4-Infrastructure/shim/dataset_ingest_rds.py
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
import psycopg2.extras
from rds_connect import connect_rds

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("dataset_ingest_rds")

# Config
RDS_HOST = os.environ.get("RDS_HOST", "database-1-instance-1.cghu8yqogqwo.us-east-1.rds.amazonaws.com")

STACK_ROOT = Path(os.environ.get("STACK_ROOT", "/home/researcher/stack"))
DATA_DIR = STACK_ROOT / "shared-data" / "data" / "ingested_datasets" / "2026-05-18"

BUNDLE_EQS = DATA_DIR / "consolidated_links_bibtex_latex_articles_equations_2026_05_18"
BUNDLE_INV = DATA_DIR / "consolidated_ingested_datasets_2026_05_18"
TIDDLYWIKI_DIR = STACK_ROOT / "6-Documentation" / "tiddlywiki-local" / "wiki" / "tiddlers"

# ---------------------------------------------------------------------------
# DB
# ---------------------------------------------------------------------------
def connect():
    return connect_rds()


def ensure_schema(conn):
    cur = conn.cursor()
    # Equations and references
    cur.execute("""
        CREATE TABLE IF NOT EXISTS knowledge.equations (
            eq_id           uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
            latex           text        NOT NULL,
            kind            text        NOT NULL DEFAULT 'display',
            source_file     text        NOT NULL,
            source_offset   integer,
            content_hash    text        NOT NULL,
            ingested_at     timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS eq_source_idx ON knowledge.equations (source_file);
        CREATE INDEX IF NOT EXISTS eq_hash_idx ON knowledge.equations (content_hash);

        CREATE TABLE IF NOT EXISTS knowledge.references (
            ref_id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
            bibtex          text        NOT NULL,
            source_file     text        NOT NULL,
            source_offset   integer,
            content_hash    text        NOT NULL,
            ingested_at     timestamptz NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS knowledge.links (
            link_id         uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
            url             text        NOT NULL,
            source_file     text        NOT NULL,
            source_offset   integer,
            ingested_at     timestamptz NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS knowledge.dois (
            doi_id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
            doi             text        NOT NULL UNIQUE,
            source_file     text        NOT NULL,
            source_offset   integer,
            ingested_at     timestamptz NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS knowledge.article_sources (
            article_id      uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
            url             text        NOT NULL,
            label           text,
            category        text,
            ingested_at     timestamptz NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS knowledge.tiddlywiki_pages (
            tiddler_id      uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
            title           text        NOT NULL,
            tags            text,
            created         text,
            modified        text,
            body            text,
            source_path     text        NOT NULL,
            content_hash    text        NOT NULL,
            ingested_at     timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS tw_title_idx ON knowledge.tiddlywiki_pages (title);

        CREATE TABLE IF NOT EXISTS knowledge.dataset_inventory (
            inv_id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
            asset_id        text        NOT NULL,
            name            text,
            kind            text,
            status          text,
            evidence        text,
            local_paths     text,
            notes           text,
            ingested_at     timestamptz NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS knowledge.ingestion_runs (
            run_id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
            source_name     text        NOT NULL,
            total_items     integer     NOT NULL DEFAULT 0,
            items_ingested  integer     NOT NULL DEFAULT 0,
            items_skipped   integer     NOT NULL DEFAULT 0,
            error_detail    text,
            ran_at          timestamptz NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS knowledge.gamma_packets (
            component_id     text        PRIMARY KEY,
            component_label  text        NOT NULL,
            category         text        NOT NULL,
            X_input_name     text,
            pi_projection_name text,
            W_result_name    text,
            R_receipt_name   text,
            I_constraints_name text,
            G_guards_name    text,
            K_cost_name      text,
            epsilon_residual_name text,
            source_doc       text,
            source_url       text,
            citation_bibtex  text,
            parent_component text,
            family           text,
            doc_section      text,
            famm_object      text,
            famm_residual_formula text,
            receipt          text NOT NULL,
            tags             jsonb NOT NULL DEFAULT '[]',
            created_at       timestamptz NOT NULL DEFAULT now(),
            updated_at       timestamptz NOT NULL DEFAULT now(),
            allowed_claim    text,
            disallowed_claim text,
            hard_rules       jsonb NOT NULL DEFAULT '[]',
            project_sentence text
        );

        CREATE TABLE IF NOT EXISTS knowledge.gamma_components (
            component_id     text NOT NULL REFERENCES knowledge.gamma_packets(component_id) ON DELETE CASCADE,
            slot_name        text NOT NULL,
            slot_index       smallint NOT NULL CHECK (slot_index BETWEEN 1 AND 8),
            local_symbol     text,
            field_name       text,
            meaning          text,
            json_schema      jsonb DEFAULT '{}',
            example_value    jsonb DEFAULT '{}',
            per_key_slot     boolean NOT NULL DEFAULT false,
            retention_rule   text,
            PRIMARY KEY (component_id, slot_name)
        );

        CREATE TABLE IF NOT EXISTS knowledge.implementation_tiers (
            component_id     text NOT NULL REFERENCES knowledge.gamma_packets(component_id) ON DELETE CASCADE,
            tier_number      smallint NOT NULL CHECK (tier_number BETWEEN 0 AND 6),
            tier_label       text NOT NULL,
            tier_description text,
            status           text NOT NULL DEFAULT 'planned',
            prerequisite     text,
            depended_on_by   text[],
            receipt_sha256   text,
            verified_at      timestamptz,
            created_at       timestamptz NOT NULL DEFAULT now(),
            updated_at       timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (component_id, tier_number)
        );

        CREATE TABLE IF NOT EXISTS ingestion.receipts (
            receipt_id      uuid        PRIMARY KEY,
            shim_name       text        NOT NULL,
            status          text        NOT NULL,
            metadata        jsonb       NOT NULL DEFAULT '{}',
            error_detail    text,
            ran_at          timestamptz NOT NULL DEFAULT now()
        );
    """)
    conn.commit()
    log.info("Schema ready")


def record_run(conn, source_name: str, total: int, ingested: int, skipped: int, error: str | None = None):
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO knowledge.ingestion_runs
               (source_name, total_items, items_ingested, items_skipped, error_detail)
               VALUES (%s,%s,%s,%s,%s)""",
            (source_name, total, ingested, skipped, error),
        )
    conn.commit()


def record_receipt(conn, shim: str, status: str, metadata: dict, error: str | None = None):
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO ingestion.receipts
               (receipt_id, shim_name, status, metadata, error_detail, ran_at)
               VALUES (%s,%s,%s,%s,%s,now())""",
            (str(uuid.uuid4()), shim, status, json.dumps(metadata), error),
        )
    conn.commit()


# ---------------------------------------------------------------------------
# Ingestion functions
# ---------------------------------------------------------------------------
def load_jsonl(path: Path) -> list:
    """Load json or jsonl file."""
    with open(path, "r") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def ingest_equations(conn) -> tuple[int, int]:
    """Ingest equations.json → knowledge.equations"""
    fpath = BUNDLE_EQS / "equations.json"
    if not fpath.exists():
        return 0, 0
    items = load_jsonl(fpath)
    if not items:
        return 0, 0
    ingested = 0
    skipped = 0
    with conn.cursor() as cur:
        for eq in items:
            latex = eq.get("latex", "").strip()
            if not latex:
                skipped += 1
                continue
            chash = hashlib.sha256(latex.encode()).hexdigest()
            cur.execute(
                """INSERT INTO knowledge.equations (latex, kind, source_file, source_offset, content_hash)
                   VALUES (%s,%s,%s,%s,%s)
                   ON CONFLICT DO NOTHING""",
                (latex, eq.get("kind", "display"), eq.get("source_file", ""),
                 eq.get("offset"), chash),
            )
            if cur.rowcount > 0:
                ingested += 1
            else:
                skipped += 1
    conn.commit()
    log.info("Equations: %d ingested, %d skipped", ingested, skipped)
    return ingested, skipped


def ingest_references(conn) -> tuple[int, int]:
    """Ingest references.json → knowledge.references"""
    fpath = BUNDLE_EQS / "references.json"
    if not fpath.exists():
        return 0, 0
    items = load_jsonl(fpath)
    if not items:
        return 0, 0
    ingested = 0
    skipped = 0
    with conn.cursor() as cur:
        for r in items:
            bibtex = r.get("bibtex", "").strip()
            if not bibtex:
                skipped += 1
                continue
            chash = hashlib.sha256(bibtex.encode()).hexdigest()
            cur.execute(
                """INSERT INTO knowledge.references (bibtex, source_file, source_offset, content_hash)
                   VALUES (%s,%s,%s,%s)
                   ON CONFLICT DO NOTHING""",
                (bibtex, r.get("source_file", ""), r.get("offset"), chash),
            )
            if cur.rowcount > 0:
                ingested += 1
            else:
                skipped += 1
    conn.commit()
    log.info("References: %d ingested, %d skipped", ingested, skipped)
    return ingested, skipped


def ingest_links(conn) -> tuple[int, int]:
    """Ingest links.json → knowledge.links"""
    fpath = BUNDLE_EQS / "links.json"
    if not fpath.exists():
        return 0, 0
    items = load_jsonl(fpath)
    if not items:
        return 0, 0
    ingested = 0
    skipped = 0
    with conn.cursor() as cur:
        for r in items:
            url = r.get("url", "").strip()
            if not url:
                skipped += 1
                continue
            cur.execute(
                """INSERT INTO knowledge.links (url, source_file, source_offset)
                   VALUES (%s,%s,%s)
                   ON CONFLICT DO NOTHING""",
                (url, r.get("source_file", ""), r.get("offset")),
            )
            if cur.rowcount > 0:
                ingested += 1
            else:
                skipped += 1
    conn.commit()
    log.info("Links: %d ingested, %d skipped", ingested, skipped)
    return ingested, skipped


def ingest_dois(conn) -> tuple[int, int]:
    """Ingest dois.json → knowledge.dois"""
    fpath = BUNDLE_EQS / "dois.json"
    if not fpath.exists():
        return 0, 0
    items = load_jsonl(fpath)
    if not items:
        return 0, 0
    ingested = 0
    skipped = 0
    with conn.cursor() as cur:
        for r in items:
            doi = r.get("doi", "").strip()
            if not doi:
                skipped += 1
                continue
            cur.execute(
                """INSERT INTO knowledge.dois (doi, source_file, source_offset)
                   VALUES (%s,%s,%s)
                   ON CONFLICT (doi) DO NOTHING""",
                (doi, r.get("source_file", ""), r.get("offset")),
            )
            if cur.rowcount > 0:
                ingested += 1
            else:
                skipped += 1
    conn.commit()
    log.info("DOIs: %d ingested, %d skipped", ingested, skipped)
    return ingested, skipped


def ingest_article_sources(conn) -> tuple[int, int]:
    """Ingest articles_sources.json → knowledge.article_sources"""
    fpath = BUNDLE_EQS / "articles_sources.json"
    if not fpath.exists():
        return 0, 0
    items = load_jsonl(fpath)
    if not items:
        return 0, 0
    ingested = 0
    skipped = 0
    with conn.cursor() as cur:
        for r in items:
            url = r.get("url", "").strip()
            if not url:
                skipped += 1
                continue
            cur.execute(
                """INSERT INTO knowledge.article_sources (url, label, category)
                   VALUES (%s,%s,%s)
                   ON CONFLICT DO NOTHING""",
                (url, r.get("label", ""), r.get("category", "")),
            )
            if cur.rowcount > 0:
                ingested += 1
            else:
                skipped += 1
    conn.commit()
    log.info("Article sources: %d ingested, %d skipped", ingested, skipped)
    return ingested, skipped


def ingest_dataset_inventory(conn) -> tuple[int, int]:
    """Ingest dataset_inventory.json → knowledge.dataset_inventory"""
    fpath = BUNDLE_INV / "manifest" / "dataset_inventory.json"
    if not fpath.exists():
        return 0, 0
    items = load_jsonl(fpath)
    if not items:
        return 0, 0
    ingested = 0
    skipped = 0
    with conn.cursor() as cur:
        for r in items:
            asset_id = r.get("id", "").strip()
            if not asset_id:
                skipped += 1
                continue
            cur.execute(
                """INSERT INTO knowledge.dataset_inventory
                   (asset_id, name, kind, status, evidence, local_paths, notes)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT DO NOTHING""",
                (asset_id, r.get("name", ""), r.get("kind", ""),
                 r.get("status", ""), r.get("evidence", ""),
                 r.get("local_paths_observed", ""), r.get("notes", "")),
            )
            if cur.rowcount > 0:
                ingested += 1
            else:
                skipped += 1
    conn.commit()
    log.info("Dataset inventory: %d ingested, %d skipped", ingested, skipped)
    return ingested, skipped


def ingest_tiddlywiki(conn) -> tuple[int, int]:
    """Ingest 263 .tid files → knowledge.tiddlywiki_pages"""
    if not TIDDLYWIKI_DIR.exists():
        log.warning("TiddlyWiki dir not found: %s", TIDDLYWIKI_DIR)
        return 0, 0
    ingested = 0
    skipped = 0
    with conn.cursor() as cur:
        for fpath in sorted(TIDDLYWIKI_DIR.glob("*.tid")):
            try:
                text = fpath.read_text(encoding="utf-8", errors="replace")
            except Exception:
                skipped += 1
                continue

            # Parse TiddlyWiki fields
            metadata: dict[str, str] = {}
            body_lines: list[str] = []
            in_body = False
            for line in text.split("\n"):
                if not in_body:
                    if line.strip() == "":
                        in_body = True
                        continue
                    if ":" in line:
                        key, _, val = line.partition(":")
                        metadata[key.strip().lower()] = val.strip()
                else:
                    body_lines.append(line)
            body = "\n".join(body_lines).strip()
            title = metadata.get("title", fpath.stem)
            chash = hashlib.sha256(body.encode()).hexdigest()

            # Skip system tiddlers ($:/)
            if title.startswith("$:"):
                skipped += 1
                continue

            cur.execute(
                """INSERT INTO knowledge.tiddlywiki_pages
                   (title, tags, created, modified, body, source_path, content_hash)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT DO NOTHING""",
                (title, metadata.get("tags", ""), metadata.get("created", ""),
                 metadata.get("modified", ""), body, str(fpath), chash),
            )
            if cur.rowcount > 0:
                ingested += 1
            else:
                skipped += 1
            if ingested % 50 == 0:
                conn.commit()
    conn.commit()
    log.info("TiddlyWiki: %d ingested, %d skipped (system)", ingested, skipped)
    return ingested, skipped


def seed_gamma_packets(conn) -> tuple[int, int]:
    """Seed the 14 known Gamma packets. Existing rows are left alone."""
    packets = [
        ("ORToolsWASM", "OR-Tools WASM Constraint Solver Gate", "execution",
         "OR_TOOLS_WASM_CONSTRAINT_SOLVER_GATE.md", "constraint-solver,wasm,cp-sat"),
        ("GliaMemory", "GLIA Persistent Memory Substrate", "memory",
         "POSSIBLE_CONSTRAINED_AGENT_APPROACHES.md", "memory,local-first"),
        ("SmallCode", "SmallCode Constrained Execution Substrate", "execution",
         "POSSIBLE_CONSTRAINED_AGENT_APPROACHES.md", "coding,constrained,patch-first"),
        ("NSpaceKV", "N-Space Key-Value Reward Memory", "memory",
         "POSSIBLE_CONSTRAINED_AGENT_APPROACHES_DEEP_DIVE.md", "key-value,reward,sparsity"),
        ("Collapse", "Field Collapse / Compression Gate", "routing",
         "OR_TOOLS_WASM_CONSTRAINT_SOLVER_GATE.md", "compression,collapse,field-reduction"),
        ("MMRGossip", "N-Folded MMR Gossip KV-Cache Surface", "memory",
         "POSSIBLE_CONSTRAINED_AGENT_APPROACHES_DEEP_DIVE.md", "mmr,gossip,kv-cache"),
        ("Hermes", "Hermes Agent Field Operator Bridge", "governance",
         "POSSIBLE_CONSTRAINED_AGENT_APPROACHES_DEEP_DIVE.md", "governance,authority,bridge"),
        ("AntiFAMM", "Anti-FAMM Witness Blind-Spot Adversary", "adversarial",
         "POSSIBLE_CONSTRAINED_AGENT_APPROACHES.md", "adversarial,famm,blind-spot"),
        ("AntiBraidStorm", "Anti-BraidStorm Hostile Crossing Adversary", "adversarial",
         "POSSIBLE_CONSTRAINED_AGENT_APPROACHES.md", "adversarial,braidstorm,alias"),
        ("BridgeModel", "BridgeModel Global Gate and Linter", "governance",
         "POSSIBLE_CONSTRAINED_AGENT_APPROACHES_DEEP_DIVE.md", "governance,gate,linter"),
        ("FastPatchCheck", "FastPatchCheck — Local Viability", "verification",
         "POSSIBLE_CONSTRAINED_AGENT_APPROACHES_DEEP_DIVE.md", "verification,patch,smoke-test"),
        ("StructuralAdmissibilityCheck", "StructuralAdmissibility — Invariant Legitimacy", "verification",
         "POSSIBLE_CONSTRAINED_AGENT_APPROACHES_DEEP_DIVE.md", "verification,admissibility,invariant"),
        ("GCLCombined", "GCL Combined Coding Surface", "coding",
         "POSSIBLE_CONSTRAINED_AGENT_APPROACHES_DEEP_DIVE.md", "coding,surface,gcl"),
        ("LogogramChirality", "Logogram Chirality Route Gate", "routing",
         "POSSIBLE_CONSTRAINED_AGENT_APPROACHES_DEEP_DIVE.md", "logogram,chirality,route"),
    ]
    ingested = 0
    with conn.cursor() as cur:
        for cid, label, cat, src, tagstr in packets:
            cur.execute(
                """INSERT INTO knowledge.gamma_packets
                   (component_id, component_label, category, source_doc, tags, receipt)
                   VALUES (%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (component_id) DO NOTHING""",
                (cid, label, cat, src, json.dumps(tagstr.split(",")),
                 f"sha256:{cid}_seed_2026-05-18"),
            )
            if cur.rowcount > 0:
                ingested += 1
    conn.commit()
    log.info("Gamma packets: %d seeded", ingested)
    return ingested, 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    log.info("Connecting to RDS (host=%s)…", RDS_HOST)
    conn = connect()
    conn.autocommit = False
    ensure_schema(conn)

    total_ingested = 0
    total_skipped = 0
    errors: list[str] = []

    sources = [
        ("equations", ingest_equations),
        ("references", ingest_references),
        ("links", ingest_links),
        ("dois", ingest_dois),
        ("article_sources", ingest_article_sources),
        ("dataset_inventory", ingest_dataset_inventory),
        ("tiddlywiki", ingest_tiddlywiki),
        ("gamma_packets", seed_gamma_packets),
    ]

    for name, fn in sources:
        try:
            ing, skp = fn(conn)
            total_ingested += ing
            total_skipped += skp
            record_run(conn, name, ing + skp, ing, skp)
            record_receipt(conn, f"dataset_ingest/{name}", "success" if ing > 0 else "empty",
                           {"ingested": ing, "skipped": skp})
        except Exception as e:
            msg = str(e)
            log.error("%s ingestion failed: %s", name, msg)
            errors.append(f"{name}: {msg}")
            conn.rollback()
            record_receipt(conn, f"dataset_ingest/{name}", "error", {}, error=msg)
            record_run(conn, name, 0, 0, 0, msg)

    conn.close()
    log.info("Done. Total ingested=%d skipped=%d errors=%d", total_ingested, total_skipped, len(errors))
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
