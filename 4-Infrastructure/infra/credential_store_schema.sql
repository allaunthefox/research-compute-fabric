-- ============================================================================
-- Credential Store Schema — audit trail for Research Stack credential server
--
-- Deploy: psql -f credential_store_schema.sql
--         (or run through 4-Infrastructure/storage/garage/db-consolidate.sh)
--
-- Table: credential_store.access_log
--   Every credential operation (status, manifest, resolve, rotate, revoke)
--   is logged with actor, action, resource, outcome, and network context.
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS credential_store;

-- Primary audit log table for credential access events.
-- Designed to be written by rs-surface (direct PostgreSQL or via sync script)
-- and consumed by compliance / monitoring shims.
CREATE TABLE IF NOT EXISTS credential_store.access_log (
    id              SERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ DEFAULT now(),
    actor           VARCHAR(255) NOT NULL,
    action          VARCHAR(50) NOT NULL,
    resource        VARCHAR(255) NOT NULL,
    resource_type   VARCHAR(50),
    outcome         VARCHAR(20) NOT NULL CHECK (outcome IN ('success', 'failure', 'denied')),
    ip_address      INET,
    user_agent      TEXT,
    request_id      VARCHAR(255),
    details         JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_access_log_timestamp
    ON credential_store.access_log (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_access_log_actor
    ON credential_store.access_log (actor);
CREATE INDEX IF NOT EXISTS idx_access_log_resource
    ON credential_store.access_log (resource);

-- ============================================================================
-- Optional: credential_store.credentials table (normalized credential metadata)
-- ============================================================================
-- This table stores *metadata* about credentials, NOT the secret values.
-- Secret values remain in the JSON file on microvm-racknerd or env vars.
CREATE TABLE IF NOT EXISTS credential_store.credentials (
    credential_id   TEXT PRIMARY KEY,
    provider          TEXT NOT NULL,
    description       TEXT,
    access_level      TEXT NOT NULL DEFAULT 'internal', -- public | internal | restricted | secret
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_accessed_at  TIMESTAMPTZ,
    is_active         BOOLEAN NOT NULL DEFAULT true,
    rotation_due_at   TIMESTAMPTZ,
    metadata          JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_credentials_provider
    ON credential_store.credentials (provider);
CREATE INDEX IF NOT EXISTS idx_credentials_active
    ON credential_store.credentials (is_active)
    WHERE is_active = true;

-- ============================================================================
-- Optional: credential_store.rotation_events table
-- ============================================================================
CREATE TABLE IF NOT EXISTS credential_store.rotation_events (
    event_id          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    credential_id     TEXT NOT NULL REFERENCES credential_store.credentials(credential_id),
    triggered_by      TEXT NOT NULL,
    old_key_digest    TEXT,          -- SHA-256 prefix of old key (never store full key)
    new_key_digest    TEXT,
    rotated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    status            TEXT NOT NULL DEFAULT 'pending', -- pending | completed | failed | rolled_back
    metadata          JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_rotation_events_cred
    ON credential_store.rotation_events (credential_id, rotated_at DESC);

-- ============================================================================
-- ============================================================================
-- Hoxel Store Schema — Spatiotemporal RAM address surface
--
-- Every transition of data between (node, tier) pairs is recorded as a
-- memory hoxel.  Each hoxel carries a thermal score, residual, witness
-- chain, and a globally-monotonic tx_seq — forming a verifiable,
-- ACID-ordered memory manifold across all nodes.
--
-- The hoxel IS the computation: moving data between tiers computes the
-- thermal score, residual, and witness in a single atomic event.
-- Spinning up more nodes adds more spatial coordinates to the manifold,
-- increasing the total compute-in-flight capacity.
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS hoxel_store;

CREATE TABLE IF NOT EXISTS hoxel_store.memory_hoxels (
    hoxel_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    obj_key         TEXT NOT NULL,                  -- sha256: the eigen-address
    bucket          TEXT NOT NULL,                  -- namespace / s3 bucket
    from_node       TEXT,                           -- spatial origin (null = new)
    from_tier       TEXT,                           -- previous tier (null = new)
    to_node         TEXT,                           -- spatial destination
    to_tier         TEXT NOT NULL,                  -- target tier (hot|warm|cold|garage|gdrive|in_flight)
    spectral_mode   TEXT NOT NULL DEFAULT 'migrate', -- read|write|migrate|stream|scan|replicate
    density         DOUBLE PRECISION DEFAULT 1.0,
    confidence      DOUBLE PRECISION DEFAULT 1.0,
    semantic_load   DOUBLE PRECISION DEFAULT 0.0,
    thermal_score   DOUBLE PRECISION NOT NULL,      -- 0..1 from compute_thermal_signature()
    residual        DOUBLE PRECISION DEFAULT 0.0,   -- reconstruction error
    payload_bytes   BIGINT DEFAULT 0,               -- size of the data in motion
    created_ts      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    accessed_ts     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    access_count    INTEGER DEFAULT 0,
    witness_prev    UUID REFERENCES hoxel_store.memory_hoxels(hoxel_id),
    witness_hash    TEXT NOT NULL,                   -- sha256 of canonical (record | prev_witness)
    tx_seq          BIGINT GENERATED ALWAYS AS IDENTITY  -- monotonic global clock
);

CREATE INDEX IF NOT EXISTS idx_hoxels_thermal
    ON hoxel_store.memory_hoxels (thermal_score, created_ts DESC);
CREATE INDEX IF NOT EXISTS idx_hoxels_node
    ON hoxel_store.memory_hoxels (to_node, created_ts DESC);
CREATE INDEX IF NOT EXISTS idx_hoxels_tier
    ON hoxel_store.memory_hoxels (to_tier, created_ts DESC);
CREATE INDEX IF NOT EXISTS idx_hoxels_obj_key
    ON hoxel_store.memory_hoxels (obj_key, created_ts DESC);
CREATE INDEX IF NOT EXISTS idx_hoxels_created
    ON hoxel_store.memory_hoxels (created_ts DESC);
CREATE INDEX IF NOT EXISTS idx_hoxels_witness_prev
    ON hoxel_store.memory_hoxels (witness_prev);

-- Compute currently in-flight across the mesh (transitions in last N minutes)
CREATE OR REPLACE VIEW hoxel_store.inflight_compute AS
SELECT
    COUNT(*)                                          AS inflight_count,
    COALESCE(SUM(payload_bytes), 0)                   AS total_compute_bytes,
    COUNT(DISTINCT COALESCE(to_node, 'unknown'))      AS active_nodes,
    COUNT(DISTINCT to_tier)                           AS tier_count,
    MIN(created_ts)                                   AS oldest_inflight,
    MAX(created_ts)                                   AS newest_inflight
FROM hoxel_store.memory_hoxels
WHERE created_ts > NOW() - INTERVAL '30 minutes';

-- Thermal zone breakdown
CREATE OR REPLACE VIEW hoxel_store.thermal_zones AS
SELECT
    to_tier                                           AS tier,
    COUNT(*)                                          AS hoxel_count,
    COALESCE(AVG(thermal_score), 0)                   AS avg_thermal_score,
    COALESCE(SUM(payload_bytes), 0)                   AS total_bytes,
    COUNT(DISTINCT COALESCE(to_node, 'unknown'))      AS nodes
FROM hoxel_store.memory_hoxels
GROUP BY to_tier
ORDER BY avg_thermal_score;

-- Per-object access chain (braid path reconstruction)
CREATE OR REPLACE VIEW hoxel_store.object_braid AS
SELECT
    obj_key,
    COUNT(*)                                          AS transition_count,
    COUNT(DISTINCT to_tier)                           AS tier_span,
    MIN(created_ts)                                   AS first_seen,
    MAX(created_ts)                                   AS last_seen,
    SUM(payload_bytes)                                AS total_bytes_moved,
    COALESCE(AVG(residual), 0)                        AS avg_residual,
    COALESCE(SUM(CASE WHEN spectral_mode = 'migrate' THEN 1 ELSE 0 END), 0) AS migrations
FROM hoxel_store.memory_hoxels
GROUP BY obj_key
ORDER BY transition_count DESC;

-- ============================================================================
-- Helper views (existing credential access views)
-- ============================================================================

-- Recent access failures for security dashboard
CREATE OR REPLACE VIEW credential_store.recent_access_failures AS
SELECT
    timestamp,
    actor,
    action,
    resource,
    outcome,
    ip_address,
    details
FROM credential_store.access_log
WHERE outcome IN ('failure', 'denied')
  AND timestamp > now() - interval '24 hours'
ORDER BY timestamp DESC;

-- Credential usage summary (last 7 days)
CREATE OR REPLACE VIEW credential_store.weekly_usage_summary AS
SELECT
    resource AS provider,
    action,
    outcome,
    count(*) AS event_count,
    min(timestamp) AS first_seen,
    max(timestamp) AS last_seen
FROM credential_store.access_log
WHERE timestamp > now() - interval '7 days'
GROUP BY resource, action, outcome
ORDER BY event_count DESC;
