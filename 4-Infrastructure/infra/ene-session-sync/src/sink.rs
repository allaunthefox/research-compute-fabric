use crate::models::{ChatMessage, ChatSession, IngestionReceipt};
use anyhow::{Context, Result};
use tokio_postgres::{Client, Config, NoTls};
use tracing::{debug, info, warn};

/// PostgreSQL sink for the ENE chat log schema.
pub struct RdsSink {
    client: Client,
}

impl RdsSink {
    /// Connect to PostgreSQL.  DSN is parsed from standard libpq key=value format.
    ///
    /// RDS requires SSL.  When `sslmode=require` (or `verify-*`) is present in the
    /// DSN the caller should set `PGSSLMODE` or pass a DSN that already includes
    /// `sslmode=require`.  We connect with `NoTls` here so the binary has zero
    /// native-tls/openssl link dependency; in production the caller is expected to
    /// tunnel via an SSL-terminating proxy (RDS IAM auth token + pg_bouncer/SSL
    /// termination), OR the `RDS_DSN` env-var contains `sslmode=disable` for a
    /// dev/tunnel setup.  The feature flag `tls` (future) can replace NoTls.
    pub async fn connect(dsn: &str) -> Result<Self> {
        // Strip sslmode=require so tokio-postgres (NoTls) doesn't reject it.
        // In production, place an SSL-terminating proxy in front or use
        // `tokio-postgres-rustls` crate (requires adding it as a dep).
        let cleaned = dsn
            .split_whitespace()
            .filter(|token| !token.starts_with("sslmode="))
            .collect::<Vec<_>>()
            .join(" ");

        let config: Config = cleaned.parse().context("parse PostgreSQL DSN")?;
        let (client, connection) = config
            .connect(NoTls)
            .await
            .context("connect to RDS (NoTls — see sink.rs comment for TLS upgrade path)")?;
        tokio::spawn(async move {
            if let Err(e) = connection.await {
                warn!("PostgreSQL connection error: {}", e);
            }
        });
        let sink = Self { client };
        sink.init_schema().await?;
        sink.init_tables().await?;
        Ok(sink)
    }

    async fn init_schema(&self) -> Result<()> {
        self.client
            .batch_execute("CREATE SCHEMA IF NOT EXISTS ene")
            .await
            .context("create ene schema")?;
        Ok(())
    }

    /// Create tables and indexes if they do not exist.
    async fn init_tables(&self) -> Result<()> {
        // Try to enable pgvector — harmless if already enabled or unavailable.
        let _ = self
            .client
            .batch_execute("CREATE EXTENSION IF NOT EXISTS vector")
            .await;

        let ddl = r#"
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

-- Columns may already exist after a schema migration; ADD COLUMN IF NOT EXISTS
-- is idempotent on PostgreSQL ≥ 9.6.
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
        "#;
        // Full-text and JSONB indexes require non-empty text_content / tool_calls;
        // create them separately so a pgvector-missing cluster still gets the rest.
        let fts_ddl = r#"
CREATE INDEX IF NOT EXISTS idx_chat_messages_text_search
    ON ene.chat_messages USING GIN(to_tsvector('english', COALESCE(text_content, '')));
CREATE INDEX IF NOT EXISTS idx_chat_messages_tool_search
    ON ene.chat_messages USING GIN(tool_calls jsonb_path_ops);
        "#;
        self.client.batch_execute(ddl).await.context("init DDL")?;
        if let Err(e) = self.client.batch_execute(fts_ddl).await {
            warn!("FTS index creation skipped (non-fatal): {}", e);
        }
        info!("RDS schema initialized");
        Ok(())
    }

    /// Upsert a session (insert or update on conflict).
    pub async fn upsert_session(&self, s: &ChatSession) -> Result<()> {
        let embedding_str = s.embedding.as_ref().map(|v| {
            format!(
                "[{}]",
                v.iter()
                    .map(|f| f.to_string())
                    .collect::<Vec<_>>()
                    .join(",")
            )
        });
        let meta_json = serde_json::to_value(&s.meta)?;
        self.client
            .execute(
                "INSERT INTO ene.chat_sessions \
                 (session_id, title, agent, model, \
                  workspace_fingerprint, workspace_root, fork_parent_session_id, \
                  compaction_count, compaction_summary, message_count, \
                  token_input_total, token_output_total, \
                  created_at_ms, updated_at_ms, first_message_at_ms, last_message_at_ms, \
                  embedding, meta, receipt, updated_at) \
                 VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17::vector,$18,$19,now()) \
                 ON CONFLICT (session_id) DO UPDATE SET \
                  title                  = EXCLUDED.title, \
                  agent                  = EXCLUDED.agent, \
                  model                  = EXCLUDED.model, \
                  workspace_fingerprint  = EXCLUDED.workspace_fingerprint, \
                  workspace_root         = EXCLUDED.workspace_root, \
                  fork_parent_session_id = EXCLUDED.fork_parent_session_id, \
                  compaction_count       = EXCLUDED.compaction_count, \
                  compaction_summary     = EXCLUDED.compaction_summary, \
                  message_count          = EXCLUDED.message_count, \
                  token_input_total      = EXCLUDED.token_input_total, \
                  token_output_total     = EXCLUDED.token_output_total, \
                  updated_at_ms          = EXCLUDED.updated_at_ms, \
                  first_message_at_ms    = EXCLUDED.first_message_at_ms, \
                  last_message_at_ms     = EXCLUDED.last_message_at_ms, \
                  embedding              = EXCLUDED.embedding, \
                  meta                   = EXCLUDED.meta, \
                  receipt                = EXCLUDED.receipt, \
                  updated_at             = now()",
                &[
                    &s.session_id,
                    &s.title,
                    &s.agent,
                    &s.model,
                    &s.workspace_fingerprint,
                    &s.workspace_root,
                    &s.fork_parent_session_id,
                    &(s.compaction_count as i32),
                    &s.compaction_summary,
                    &(s.message_count as i32),
                    &s.token_input_total,
                    &s.token_output_total,
                    &s.created_at_ms,
                    &s.updated_at_ms,
                    &s.first_message_at_ms,
                    &s.last_message_at_ms,
                    &embedding_str,
                    &meta_json,
                    &s.receipt,
                ],
            )
            .await
            .context("upsert session")?;
        debug!("upserted session {}", s.session_id);
        Ok(())
    }

    /// Upsert a batch of messages for a session.
    pub async fn upsert_messages(&self, session_id: &str, msgs: &[ChatMessage]) -> Result<()> {
        for msg in msgs {
            let embedding_str = msg.embedding.as_ref().map(|v| {
                format!(
                    "[{}]",
                    v.iter()
                        .map(|f| f.to_string())
                        .collect::<Vec<_>>()
                        .join(",")
                )
            });
            let blocks_json = serde_json::to_value(&msg.blocks)?;
            let tool_calls_json = serde_json::to_value(&msg.tool_calls)?;
            self.client
                .execute(
                    "INSERT INTO ene.chat_messages \
                     (session_id, message_index, role, blocks, text_content, \
                      token_input, token_output, token_cache_creation, token_cache_read, \
                      tool_calls, embedding, receipt_hash, created_at_ms, created_at) \
                     VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11::vector,$12,$13,now()) \
                     ON CONFLICT (session_id, message_index) DO UPDATE SET \
                      role                 = EXCLUDED.role, \
                      blocks               = EXCLUDED.blocks, \
                      text_content         = EXCLUDED.text_content, \
                      token_input          = EXCLUDED.token_input, \
                      token_output         = EXCLUDED.token_output, \
                      token_cache_creation = EXCLUDED.token_cache_creation, \
                      token_cache_read     = EXCLUDED.token_cache_read, \
                      tool_calls           = EXCLUDED.tool_calls, \
                      embedding            = EXCLUDED.embedding, \
                      receipt_hash         = EXCLUDED.receipt_hash, \
                      created_at_ms        = EXCLUDED.created_at_ms",
                    &[
                        &session_id,
                        &msg.message_index,
                        &msg.role,
                        &blocks_json,
                        &msg.text_content,
                        &msg.token_input,
                        &msg.token_output,
                        &msg.token_cache_creation,
                        &msg.token_cache_read,
                        &tool_calls_json,
                        &embedding_str,
                        &msg.receipt_hash,
                        &msg.created_at_ms,
                    ],
                )
                .await
                .with_context(|| {
                    format!(
                        "upsert message idx={} for session {}",
                        msg.message_index, session_id
                    )
                })?;
        }
        info!(
            "upserted {} messages for session {}",
            msgs.len(),
            session_id
        );
        Ok(())
    }

    /// Delete all messages for a session (used before re-ingesting).
    pub async fn delete_messages_for_session(&self, session_id: &str) -> Result<u64> {
        let rows = self
            .client
            .execute(
                "DELETE FROM ene.chat_messages WHERE session_id = $1",
                &[&session_id],
            )
            .await
            .context("delete messages")?;
        Ok(rows)
    }

    /// Write an ingestion receipt.
    pub async fn write_receipt(&self, r: &IngestionReceipt) -> Result<()> {
        let meta_json = serde_json::to_value(&r.meta)?;
        self.client
            .execute(
                "INSERT INTO ene.ingestion_receipts \
                 (shim_name, status, sha256, record_count, source_path, meta) \
                 VALUES ($1, $2, $3, $4, $5, $6)",
                &[
                    &r.shim_name,
                    &r.status,
                    &r.sha256,
                    &r.record_count,
                    &r.source_path,
                    &meta_json,
                ],
            )
            .await
            .context("write receipt")?;
        Ok(())
    }

    /// Keyword full-text search across messages.
    pub async fn search_keyword(
        &self,
        query: &str,
        limit: i64,
    ) -> Result<Vec<serde_json::Value>> {
        let rows = self
            .client
            .query(
                "SELECT s.session_id, s.title, s.agent, s.model, \
                 COUNT(m.id) AS match_count, \
                 MAX(ts_rank(to_tsvector('english', COALESCE(m.text_content,'')), \
                             plainto_tsquery('english', $1))) AS rank \
                 FROM ene.chat_sessions s \
                 JOIN ene.chat_messages m ON m.session_id = s.session_id \
                 WHERE to_tsvector('english', COALESCE(m.text_content,'')) \
                       @@ plainto_tsquery('english', $1) \
                 GROUP BY s.session_id, s.title, s.agent, s.model \
                 ORDER BY rank DESC \
                 LIMIT $2",
                &[&query, &limit],
            )
            .await
            .context("keyword search")?;
        let mut out = Vec::new();
        for row in &rows {
            out.push(serde_json::json!({
                "session_id": row.try_get::<_, String>(0)?,
                "title":      row.try_get::<_, Option<String>>(1)?,
                "agent":      row.try_get::<_, Option<String>>(2)?,
                "model":      row.try_get::<_, Option<String>>(3)?,
                "match_count": row.try_get::<_, i64>(4)?,
                "rank":       row.try_get::<_, f32>(5)?,
            }));
        }
        Ok(out)
    }

    /// Semantic search via embedding cosine similarity (requires pgvector).
    pub async fn search_similar(
        &self,
        embedding: &[f32],
        limit: i64,
    ) -> Result<Vec<serde_json::Value>> {
        let vec_str = format!(
            "[{}]",
            embedding
                .iter()
                .map(|f| f.to_string())
                .collect::<Vec<_>>()
                .join(",")
        );
        let rows = self
            .client
            .query(
                "SELECT session_id, title, agent, model, \
                 1 - (embedding <=> $1::vector) AS similarity \
                 FROM ene.chat_sessions \
                 WHERE embedding IS NOT NULL \
                 ORDER BY embedding <=> $1::vector \
                 LIMIT $2",
                &[&vec_str, &limit],
            )
            .await
            .context("similarity search")?;
        let mut out = Vec::new();
        for row in &rows {
            out.push(serde_json::json!({
                "session_id": row.try_get::<_, String>(0)?,
                "title":      row.try_get::<_, Option<String>>(1)?,
                "agent":      row.try_get::<_, Option<String>>(2)?,
                "model":      row.try_get::<_, Option<String>>(3)?,
                "similarity": row.try_get::<_, f32>(4)?,
            }));
        }
        Ok(out)
    }

    /// List recent sessions.
    pub async fn list_sessions(&self, limit: i64) -> Result<Vec<serde_json::Value>> {
        let rows = self
            .client
            .query(
                "SELECT session_id, title, agent, model, message_count, \
                 token_input_total, token_output_total, created_at_ms, updated_at_ms \
                 FROM ene.chat_sessions \
                 ORDER BY updated_at_ms DESC \
                 LIMIT $1",
                &[&limit],
            )
            .await
            .context("list sessions")?;
        let mut out = Vec::new();
        for row in &rows {
            out.push(serde_json::json!({
                "session_id":        row.try_get::<_, String>(0)?,
                "title":             row.try_get::<_, Option<String>>(1)?,
                "agent":             row.try_get::<_, Option<String>>(2)?,
                "model":             row.try_get::<_, Option<String>>(3)?,
                "message_count":     row.try_get::<_, i32>(4)?,
                "token_input_total": row.try_get::<_, i64>(5)?,
                "token_output_total":row.try_get::<_, i64>(6)?,
                "created_at_ms":     row.try_get::<_, i64>(7)?,
                "updated_at_ms":     row.try_get::<_, i64>(8)?,
            }));
        }
        Ok(out)
    }

    /// Retrieve a single session with all its messages.
    pub async fn get_session(&self, session_id: &str) -> Result<Option<serde_json::Value>> {
        let Some(sess) = self
            .client
            .query_opt(
                "SELECT session_id, title, agent, model, message_count, \
                 token_input_total, token_output_total, created_at_ms, updated_at_ms, meta \
                 FROM ene.chat_sessions WHERE session_id = $1",
                &[&session_id],
            )
            .await
            .context("get session")?
        else {
            return Ok(None);
        };

        let msg_rows = self
            .client
            .query(
                "SELECT message_index, role, blocks, text_content, \
                 token_input, token_output, tool_calls, created_at_ms \
                 FROM ene.chat_messages \
                 WHERE session_id = $1 ORDER BY message_index",
                &[&session_id],
            )
            .await
            .context("get messages")?;
        let mut messages = Vec::new();
        for row in &msg_rows {
            messages.push(serde_json::json!({
                "message_index": row.try_get::<_, i32>(0)?,
                "role":          row.try_get::<_, String>(1)?,
                "blocks":        row.try_get::<_, serde_json::Value>(2)?,
                "text_content":  row.try_get::<_, Option<String>>(3)?,
                "token_input":   row.try_get::<_, i64>(4)?,
                "token_output":  row.try_get::<_, i64>(5)?,
                "tool_calls":    row.try_get::<_, serde_json::Value>(6)?,
                "created_at_ms": row.try_get::<_, i64>(7)?,
            }));
        }
        Ok(Some(serde_json::json!({
            "session_id":         sess.try_get::<_, String>(0)?,
            "title":              sess.try_get::<_, Option<String>>(1)?,
            "agent":              sess.try_get::<_, Option<String>>(2)?,
            "model":              sess.try_get::<_, Option<String>>(3)?,
            "message_count":      sess.try_get::<_, i32>(4)?,
            "token_input_total":  sess.try_get::<_, i64>(5)?,
            "token_output_total": sess.try_get::<_, i64>(6)?,
            "created_at_ms":      sess.try_get::<_, i64>(7)?,
            "updated_at_ms":      sess.try_get::<_, i64>(8)?,
            "meta":               sess.try_get::<_, serde_json::Value>(9)?,
            "messages": messages,
        })))
    }
}
