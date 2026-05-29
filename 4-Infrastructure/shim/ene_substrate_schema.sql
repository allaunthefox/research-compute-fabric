-- ============================================================================
-- ENE Memory Substrate Schema — the project's receipted substrate-memory
--
-- Elemental ENV schema:
--   GROUND  — stable, receipt-bearing, reusable
--   WATER   — fluid, exploratory, not yet fixed
--   FLAME   — high-energy transformation, Warden-watched
--   SEISMIC — deep structural stress, FAMM audit required
--   SAND    — granular fragments, compressible
--   CRYSTAL — settled, hardened, compression-ready invariant
--   AIR     — abstract hypothesis, not grounded
--   VOID    — missing, rejected, negative evidence
--   METAL   — hardened invariant, tool, gate, kernel
--
-- Artifact lifecycle (MEMORY.md):
--   SEED → FORMING → STABLE → CRYSTALLIZED → COMPRESSED
-- ============================================================================
-- Design: every ingested object becomes an addressed package with semantic
-- coordinates, graph relations, source provenance, hashes, scars, receipts,
-- and route history.
--
-- Split:
--   packages = memory content
--   relations = graph edges
--   receipts = verification layer
--   scars = FAMM failure memory
--   vectors = embeddings
--   ingest_events = provenance
--   sessions = workflow lineage
--   routes = traversal history
--   nspace_kv = key-value retention scoring
--   gossip_surface = folded KV-cache compression

CREATE SCHEMA IF NOT EXISTS ene;

-- 1. packages — central memory packet
CREATE TABLE IF NOT EXISTS ene.packages (
    pkg              TEXT PRIMARY KEY,
    package_type     TEXT,
    title            TEXT,
    content          TEXT,
    content_hash     TEXT,
    element          TEXT DEFAULT 'GROUND',
    concept_vector   JSONB DEFAULT '[]',
    concept_anchor   JSONB DEFAULT '{}',
    idea_weights     JSONB DEFAULT '{}',
    analog_map       JSONB DEFAULT '{}',
    extension_points JSONB DEFAULT '{}',
    tags             JSONB DEFAULT '[]',
    source           TEXT,
    created_at       TEXT,
    updated_at       TEXT,
    session_id       TEXT,
    provenance       JSONB DEFAULT '{}',
    merkle_root      TEXT,
    attachment_meta  JSONB DEFAULT '{}',
    ingest_profile   JSONB DEFAULT '{}',
    verification_status TEXT DEFAULT 'raw',
    promotion_state  TEXT DEFAULT 'held',
    scar_class       TEXT,
    domain           TEXT,
    archetype        TEXT,
    notes            TEXT,
    ingested_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ene_pkg_type_idx ON ene.packages (package_type);
CREATE INDEX IF NOT EXISTS ene_pkg_source_idx ON ene.packages (source);
CREATE INDEX IF NOT EXISTS ene_pkg_promotion_idx ON ene.packages (promotion_state);
CREATE UNIQUE INDEX IF NOT EXISTS ene_pkg_hash_idx ON ene.packages (content_hash) WHERE (content_hash IS NOT NULL);

-- 2. relations — graph layer
CREATE TABLE IF NOT EXISTS ene.relations (
    id              TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    source_id       TEXT NOT NULL REFERENCES ene.packages(pkg) ON DELETE CASCADE,
    target_id       TEXT NOT NULL REFERENCES ene.packages(pkg) ON DELETE CASCADE,
    relation_type   TEXT NOT NULL,
    weight          REAL DEFAULT 1.0,
    evidence_hash   TEXT,
    provenance      JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ene_rel_source_idx ON ene.relations (source_id);
CREATE INDEX IF NOT EXISTS ene_rel_target_idx ON ene.relations (target_id);
CREATE INDEX IF NOT EXISTS ene_rel_type_idx ON ene.relations (relation_type);
CREATE UNIQUE INDEX IF NOT EXISTS ene_rel_unique_idx ON ene.relations (source_id, target_id, relation_type);

-- 3. receipts — verification layer
CREATE TABLE IF NOT EXISTS ene.receipts (
    id              TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    package_id      TEXT NOT NULL REFERENCES ene.packages(pkg) ON DELETE CASCADE,
    receipt_type    TEXT NOT NULL,
    receipt_hash    TEXT,
    input_hash      TEXT,
    output_hash     TEXT,
    toolchain       TEXT,
    verifier        TEXT,
    status          TEXT NOT NULL DEFAULT 'pending',
    residual        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ene_rec_pkg_idx ON ene.receipts (package_id);
CREATE INDEX IF NOT EXISTS ene_rec_type_idx ON ene.receipts (receipt_type);

-- 4. scars — FAMM failure memory
CREATE TABLE IF NOT EXISTS ene.scars (
    id              TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    package_id      TEXT NOT NULL REFERENCES ene.packages(pkg) ON DELETE CASCADE,
    scar_type       TEXT NOT NULL,
    scar_pressure   REAL DEFAULT 0,
    failure_mode    TEXT,
    residual        JSONB DEFAULT '{}',
    coarsening_agent JSONB DEFAULT '{}',
    opened_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at       TIMESTAMPTZ,
    status          TEXT NOT NULL DEFAULT 'open'
);
CREATE INDEX IF NOT EXISTS ene_scar_pkg_idx ON ene.scars (package_id);
CREATE INDEX IF NOT EXISTS ene_scar_pressure_idx ON ene.scars (scar_pressure DESC);

-- 5. vectors — embedding storage
CREATE TABLE IF NOT EXISTS ene.vectors (
    id              TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    package_id      TEXT NOT NULL REFERENCES ene.packages(pkg) ON DELETE CASCADE,
    vector_type     TEXT NOT NULL,
    embedding       FLOAT8[],
    model           TEXT,
    dimensions      INTEGER,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ene_vec_pkg_idx ON ene.vectors (package_id);
CREATE INDEX IF NOT EXISTS ene_vec_type_idx ON ene.vectors (vector_type);

-- 6. ingest_events — provenance
CREATE TABLE IF NOT EXISTS ene.ingest_events (
    id                  TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    package_id          TEXT NOT NULL REFERENCES ene.packages(pkg) ON DELETE CASCADE,
    source_uri          TEXT,
    source_type         TEXT,
    source_hash         TEXT,
    ingest_profile      TEXT,
    parser_version      TEXT,
    extracted_entities  JSONB DEFAULT '{}',
    extracted_equations JSONB DEFAULT '[]',
    extracted_links     JSONB DEFAULT '[]',
    extracted_bibtex    JSONB DEFAULT '[]',
    warnings            JSONB DEFAULT '[]',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ene_ie_pkg_idx ON ene.ingest_events (package_id);

-- 7. sessions — workflow lineage
CREATE TABLE IF NOT EXISTS ene.sessions (
    id              TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    project_id      TEXT,
    title           TEXT,
    started_at      TIMESTAMPTZ,
    ended_at        TIMESTAMPTZ,
    actor           TEXT,
    toolchain       TEXT,
    summary         TEXT,
    memory_hash     TEXT,
    promotion_state TEXT DEFAULT 'held'
);
CREATE INDEX IF NOT EXISTS ene_sess_project_idx ON ene.sessions (project_id);

-- 8. routes — traversal through ENE
CREATE TABLE IF NOT EXISTS ene.routes (
    id              TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    start_package_id TEXT NOT NULL REFERENCES ene.packages(pkg) ON DELETE CASCADE,
    end_package_id  TEXT NOT NULL REFERENCES ene.packages(pkg) ON DELETE CASCADE,
    route_type      TEXT NOT NULL,
    cost            REAL DEFAULT 0,
    residual        REAL DEFAULT 0,
    scar_pressure   REAL DEFAULT 0,
    receipt_hash    TEXT,
    path            JSONB DEFAULT '[]',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ene_route_start_idx ON ene.routes (start_package_id);
CREATE INDEX IF NOT EXISTS ene_route_type_idx ON ene.routes (route_type);

-- 9. nspace_kv — key-value retention scoring
CREATE TABLE IF NOT EXISTS ene.nspace_kv (
    key_id              TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    rounded_coordinate  JSONB DEFAULT '{}',
    coordinate_hash     TEXT,
    value_package_id    TEXT NOT NULL REFERENCES ene.packages(pkg) ON DELETE CASCADE,
    reduction_reward    REAL DEFAULT 0,
    sparsity_score      REAL DEFAULT 0,
    scar_pressure       REAL DEFAULT 0,
    retention_score     REAL DEFAULT 0,
    last_used_at        TIMESTAMPTZ,
    receipt_hash        TEXT
);
CREATE INDEX IF NOT EXISTS ene_nskv_retention_idx ON ene.nspace_kv (retention_score DESC);
CREATE INDEX IF NOT EXISTS ene_nskv_pkg_idx ON ene.nspace_kv (value_package_id);

-- 10. gossip_surface — folded KV-cache compression
CREATE TABLE IF NOT EXISTS ene.gossip_surface_nodes (
    id              TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    package_id      TEXT NOT NULL REFERENCES ene.packages(pkg) ON DELETE CASCADE,
    fold_coordinate JSONB DEFAULT '{}',
    neighborhood_hash TEXT,
    local_summary   TEXT,
    witness_mass    REAL DEFAULT 0,
    gossip_round    INTEGER DEFAULT 0,
    receipt_hash    TEXT
);
CREATE INDEX IF NOT EXISTS ene_gsn_pkg_idx ON ene.gossip_surface_nodes (package_id);
CREATE INDEX IF NOT EXISTS ene_gsn_fold_idx ON ene.gossip_surface_nodes (gossip_round);

CREATE TABLE IF NOT EXISTS ene.gossip_surface_edges (
    id              TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    source_node_id  TEXT NOT NULL REFERENCES ene.gossip_surface_nodes(id) ON DELETE CASCADE,
    target_node_id  TEXT NOT NULL REFERENCES ene.gossip_surface_nodes(id) ON DELETE CASCADE,
    edge_type       TEXT,
    weight          REAL DEFAULT 1.0,
    last_gossip_at  TIMESTAMPTZ,
    receipt_hash    TEXT
);
CREATE INDEX IF NOT EXISTS ene_gse_source_idx ON ene.gossip_surface_edges (source_node_id);

-- 11. dsp_nodes — PipeWire/FLAC DSP compute node capabilities
CREATE TABLE IF NOT EXISTS ene.dsp_nodes (
    node_id          TEXT PRIMARY KEY,
    dsp_available    BOOLEAN NOT NULL DEFAULT true,
    pipewire_available BOOLEAN NOT NULL DEFAULT false,
    virtual_soundcard_supported BOOLEAN NOT NULL DEFAULT false,
    physical_soundcard BOOLEAN NOT NULL DEFAULT false,
    max_sample_rate  INTEGER DEFAULT 48000,
    spectral_bands   INTEGER DEFAULT 1024,
    latency_target_us INTEGER DEFAULT 5120,
    fft_size         INTEGER DEFAULT 2048,
    overlap_factor   REAL DEFAULT 0.5,
    last_seen_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    receipt_hash     TEXT
);
CREATE INDEX IF NOT EXISTS ene_dsp_available_idx ON ene.dsp_nodes (dsp_available) WHERE dsp_available = true;

-- 12. legacy compatibility tables
CREATE TABLE IF NOT EXISTS ene.wiki_pages (
    slug TEXT PRIMARY KEY,
    title TEXT,
    latest_revision INTEGER,
    updated_at TIMESTAMPTZ,
    receipt TEXT
);
CREATE TABLE IF NOT EXISTS ene.wiki_revisions (
    slug TEXT,
    revision INTEGER,
    title TEXT,
    text TEXT,
    author TEXT,
    summary TEXT,
    created_at TIMESTAMPTZ,
    receipt TEXT,
    archive_id TEXT,
    content_hash TEXT,
    archive_record JSONB,
    jsonl_event JSONB,
    PRIMARY KEY (slug, revision)
);
CREATE TABLE IF NOT EXISTS ene.wiki_links (
    slug TEXT,
    target_slug TEXT,
    target_title TEXT,
    PRIMARY KEY (slug, target_slug)
);
CREATE TABLE IF NOT EXISTS ene.wiki_categories (
    slug TEXT,
    category TEXT,
    PRIMARY KEY (slug, category)
);
CREATE TABLE IF NOT EXISTS ene.fractal_manifolds (
    root_hash TEXT PRIMARY KEY,
    name TEXT,
    byte_len INTEGER,
    leaves_count INTEGER,
    depth INTEGER,
    chunk_size INTEGER,
    branching_factor INTEGER,
    created_at TIMESTAMPTZ,
    receipt TEXT,
    archive_record JSONB DEFAULT '{}',
    jsonl_event JSONB DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS ene.fractal_nodes (
    root_hash TEXT,
    node_hash TEXT,
    kind TEXT,
    level INTEGER,
    ordinal INTEGER,
    fold_address INTEGER,
    start_leaf INTEGER,
    end_leaf INTEGER,
    size_bytes INTEGER,
    children TEXT,
    payload_b64 TEXT,
    PRIMARY KEY (root_hash, node_hash)
);
CREATE TABLE IF NOT EXISTS ene.fractal_graph_entities (
    root_hash TEXT,
    graph_node_id TEXT,
    leaf_index INTEGER,
    name TEXT,
    family TEXT,
    domain TEXT,
    neighbors TEXT,
    PRIMARY KEY (root_hash, graph_node_id)
);
