-- Canonical ENE chat/session sync schema
--
-- This schema is consumed by:
-- - 4-Infrastructure/infra/ene-session-sync (Rust)
--
-- Policy:
-- - treat this file as the canonical DDL source for these tables
-- - code should not embed divergent CREATE TABLE strings

CREATE SCHEMA IF NOT EXISTS ene;

-- Optional extension (non-fatal if unavailable).
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS ene.chat_sessions (
    session_id              TEXT PRIMARY KEY,
    title                   TEXT,
    agent                   TEXT,
    model                   TEXT,
    workspace_fingerprint   TEXT,
    workspace_root          TEXT,
    fork_parent_session_id  TEXT,
    compaction_count        INTEGER     NOT NULL DEFAULT 0,
    compaction_summary      TEXT,
    message_count           INTEGER     NOT NULL DEFAULT 0,
    token_input_total       BIGINT      NOT NULL DEFAULT 0,
    token_output_total      BIGINT      NOT NULL DEFAULT 0,
    created_at_ms           BIGINT      NOT NULL,
    updated_at_ms           BIGINT      NOT NULL,
    first_message_at_ms     BIGINT,
    last_message_at_ms      BIGINT,
    embedding               vector(768),
    meta                    JSONB       NOT NULL DEFAULT '{}',
    receipt                 TEXT,
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ene.chat_messages (
    id                    BIGSERIAL   PRIMARY KEY,
    session_id            TEXT        NOT NULL REFERENCES ene.chat_sessions(session_id) ON DELETE CASCADE,
    message_index         INTEGER     NOT NULL,
    role                  TEXT        NOT NULL,
    blocks                JSONB       NOT NULL,
    text_content          TEXT,
    token_input           BIGINT      NOT NULL DEFAULT 0,
    token_output          BIGINT      NOT NULL DEFAULT 0,
    token_cache_creation  BIGINT      NOT NULL DEFAULT 0,
    token_cache_read      BIGINT      NOT NULL DEFAULT 0,
    tool_calls            JSONB       NOT NULL DEFAULT '[]',
    embedding             vector(768),
    receipt_hash          TEXT,
    created_at_ms         BIGINT      NOT NULL,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(session_id, message_index)
);

CREATE TABLE IF NOT EXISTS ene.ingestion_receipts (
    receipt_id    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    shim_name     TEXT        NOT NULL,
    status        TEXT        NOT NULL DEFAULT 'pending',
    sha256        TEXT        NOT NULL,
    record_count  BIGINT      NOT NULL DEFAULT 0,
    source_path   TEXT        NOT NULL,
    meta          JSONB       NOT NULL DEFAULT '{}',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Idempotent migration helpers.
ALTER TABLE ene.chat_sessions ADD COLUMN IF NOT EXISTS title TEXT;
ALTER TABLE ene.chat_sessions ADD COLUMN IF NOT EXISTS agent TEXT;
ALTER TABLE ene.chat_sessions ADD COLUMN IF NOT EXISTS model TEXT;

CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated
    ON ene.chat_sessions(updated_at_ms DESC);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_workspace
    ON ene.chat_sessions(workspace_fingerprint);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_order
    ON ene.chat_messages(session_id, message_index);
CREATE INDEX IF NOT EXISTS idx_chat_messages_receipt
    ON ene.chat_messages(receipt_hash);

-- Optional indexes (non-fatal if missing language config).
CREATE INDEX IF NOT EXISTS idx_chat_messages_text_search
    ON ene.chat_messages USING GIN(to_tsvector('english', COALESCE(text_content, '')));
CREATE INDEX IF NOT EXISTS idx_chat_messages_tool_search
    ON ene.chat_messages USING GIN(tool_calls jsonb_path_ops);
