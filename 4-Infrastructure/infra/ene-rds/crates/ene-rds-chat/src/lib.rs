use anyhow::{Context, Result};
use ene_rds_core::{vec_to_pgtext, RdsClient};
use tracing::info;

pub mod models;
pub use models::*;

/// Chat log RDS surface — replaces Python ENERDSChatLog.
pub struct ChatLogSurface {
    client: RdsClient,
}

impl ChatLogSurface {
    pub fn new(client: RdsClient) -> Self {
        Self { client }
    }

    /// Initialize tables and indexes if they do not exist.
    pub async fn init_tables(&self) -> Result<()> {
        let ddl = r#"
CREATE TABLE IF NOT EXISTS ene.chat_sessions (
    session_id TEXT PRIMARY KEY,
    workspace_fingerprint TEXT,
    workspace_root TEXT,
    fork_parent_session_id TEXT,
    compaction_count INTEGER NOT NULL DEFAULT 0,
    compaction_summary TEXT,
    message_count INTEGER NOT NULL DEFAULT 0,
    token_input_total BIGINT NOT NULL DEFAULT 0,
    token_output_total BIGINT NOT NULL DEFAULT 0,
    created_at_ms BIGINT NOT NULL,
    updated_at_ms BIGINT NOT NULL,
    first_message_at_ms BIGINT,
    last_message_at_ms BIGINT,
    embedding vector(768),
    meta JSONB NOT NULL DEFAULT '{}',
    receipt TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ene.chat_messages (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES ene.chat_sessions(session_id) ON DELETE CASCADE,
    message_index INTEGER NOT NULL,
    role TEXT NOT NULL,
    blocks JSONB NOT NULL,
    text_content TEXT,
    token_input BIGINT NOT NULL DEFAULT 0,
    token_output BIGINT NOT NULL DEFAULT 0,
    token_cache_creation BIGINT NOT NULL DEFAULT 0,
    token_cache_read BIGINT NOT NULL DEFAULT 0,
    tool_calls JSONB NOT NULL DEFAULT '[]',
    embedding vector(768),
    receipt_hash TEXT,
    created_at_ms BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(session_id, message_index)
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated ON ene.chat_sessions(updated_at_ms DESC);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_order ON ene.chat_messages(session_id, message_index);
CREATE INDEX IF NOT EXISTS idx_chat_messages_receipt ON ene.chat_messages(receipt_hash);
CREATE INDEX IF NOT EXISTS idx_chat_messages_text_search ON ene.chat_messages USING GIN(to_tsvector('english', text_content));
CREATE INDEX IF NOT EXISTS idx_chat_messages_tool_search ON ene.chat_messages USING GIN(tool_calls jsonb_path_ops);
        "#;
        self.client
            .inner()
            .batch_execute(ddl)
            .await
            .context("init chat DDL")?;
        info!("chat log schema initialized");
        Ok(())
    }

    pub async fn upsert_session(&self, s: &ChatSession) -> Result<()> {
        let embedding_str = s.embedding.as_ref().map(|v| vec_to_pgtext(v));
        self.client.inner()
            .execute(
                "INSERT INTO ene.chat_sessions \
                 (session_id, workspace_fingerprint, workspace_root, fork_parent_session_id, \
                  compaction_count, compaction_summary, message_count, token_input_total, \
                  token_output_total, created_at_ms, updated_at_ms, first_message_at_ms, \
                  last_message_at_ms, embedding, meta, receipt, updated_at) \
                 VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14::vector, $15, $16, now()) \
                 ON CONFLICT (session_id) DO UPDATE SET \
                  workspace_fingerprint = EXCLUDED.workspace_fingerprint, \
                  workspace_root = EXCLUDED.workspace_root, \
                  fork_parent_session_id = EXCLUDED.fork_parent_session_id, \
                  compaction_count = EXCLUDED.compaction_count, \
                  compaction_summary = EXCLUDED.compaction_summary, \
                  message_count = EXCLUDED.message_count, \
                  token_input_total = EXCLUDED.token_input_total, \
                  token_output_total = EXCLUDED.token_output_total, \
                  updated_at_ms = EXCLUDED.updated_at_ms, \
                  first_message_at_ms = EXCLUDED.first_message_at_ms, \
                  last_message_at_ms = EXCLUDED.last_message_at_ms, \
                  embedding = EXCLUDED.embedding, \
                  meta = EXCLUDED.meta, \
                  receipt = EXCLUDED.receipt, \
                  updated_at = now()",
                &[
                    &s.session_id,
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
                    &s.meta,
                    &s.receipt,
                ],
            )
            .await
            .context("upsert session")?;
        Ok(())
    }

    pub async fn upsert_messages(&self, session_id: &str, msgs: &[ChatMessage]) -> Result<()> {
        for (idx, msg) in msgs.iter().enumerate() {
            let embedding_str = msg.embedding.as_ref().map(|v| vec_to_pgtext(v));
            self.client.inner()
                .execute(
                    "INSERT INTO ene.chat_messages \
                     (session_id, message_index, role, blocks, text_content, \
                      token_input, token_output, token_cache_creation, token_cache_read, \
                      tool_calls, embedding, receipt_hash, created_at_ms, created_at) \
                     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::vector, $12, $13, now()) \
                     ON CONFLICT (session_id, message_index) DO UPDATE SET \
                      role = EXCLUDED.role, blocks = EXCLUDED.blocks, \
                      text_content = EXCLUDED.text_content, \
                      token_input = EXCLUDED.token_input, token_output = EXCLUDED.token_output, \
                      token_cache_creation = EXCLUDED.token_cache_creation, \
                      token_cache_read = EXCLUDED.token_cache_read, \
                      tool_calls = EXCLUDED.tool_calls, \
                      embedding = EXCLUDED.embedding, receipt_hash = EXCLUDED.receipt_hash",
                    &[
                        &session_id,
                        &(idx as i32),
                        &msg.role,
                        &serde_json::to_value(&msg.blocks)?,
                        &msg.text_content,
                        &msg.token_input,
                        &msg.token_output,
                        &msg.token_cache_creation,
                        &msg.token_cache_read,
                        &serde_json::to_value(&msg.tool_calls)?,
                        &embedding_str,
                        &msg.receipt_hash,
                        &msg.created_at_ms,
                    ],
                )
                .await
                .with_context(|| format!("upsert message {} for {}", idx, session_id))?;
        }
        Ok(())
    }

    pub async fn delete_messages_for_session(&self, session_id: &str) -> Result<u64> {
        let rows = self
            .client
            .inner()
            .execute(
                "DELETE FROM ene.chat_messages WHERE session_id = $1",
                &[&session_id],
            )
            .await
            .context("delete messages")?;
        Ok(rows)
    }

    pub async fn search_keyword(&self, query: &str, limit: i64) -> Result<Vec<serde_json::Value>> {
        let rows = self.client.inner()
            .query(
                "SELECT s.session_id, COALESCE(s.compaction_summary, s.session_id) AS title, \
                 s.meta->>'agent' AS agent, s.meta->>'model' AS model, \
                 COUNT(m.id) AS match_count, \
                 MAX(ts_rank(to_tsvector('english', COALESCE(m.text_content, '')), plainto_tsquery('english', $1))) AS rank \
                 FROM ene.chat_sessions s \
                 JOIN ene.chat_messages m ON m.session_id = s.session_id \
                 WHERE to_tsvector('english', COALESCE(m.text_content, '')) @@ plainto_tsquery('english', $1) \
                 GROUP BY s.session_id, 2, 3, 4 \
                 ORDER BY rank DESC LIMIT $2",
                &[&query, &limit],
            )
            .await
            .context("keyword search")?;
        Ok(rows
            .iter()
            .map(|r| {
                serde_json::json!({
                    "session_id": r.get::<_, String>(0),
                    "title": r.get::<_, String>(1),
                    "agent": r.get::<_, Option<String>>(2),
                    "model": r.get::<_, Option<String>>(3),
                    "match_count": r.get::<_, i64>(4),
                    "rank": r.get::<_, f32>(5),
                })
            })
            .collect())
    }

    pub async fn search_similar(
        &self,
        embedding: &[f32],
        limit: i64,
    ) -> Result<Vec<serde_json::Value>> {
        let vec_str = vec_to_pgtext(embedding);
        let rows = self
            .client
            .inner()
            .query(
                "SELECT session_id, COALESCE(compaction_summary, session_id) AS title, \
                 meta->>'agent' AS agent, meta->>'model' AS model, \
                 1 - (embedding <=> $1::vector) AS similarity \
                 FROM ene.chat_sessions WHERE embedding IS NOT NULL \
                 ORDER BY embedding <=> $1::vector LIMIT $2",
                &[&vec_str, &limit],
            )
            .await
            .context("similarity search")?;
        Ok(rows
            .iter()
            .map(|r| {
                serde_json::json!({
                    "session_id": r.get::<_, String>(0),
                    "title": r.get::<_, String>(1),
                    "agent": r.get::<_, Option<String>>(2),
                    "model": r.get::<_, Option<String>>(3),
                    "similarity": r.get::<_, f32>(4),
                })
            })
            .collect())
    }

    pub async fn list_sessions(&self, limit: i64) -> Result<Vec<serde_json::Value>> {
        let rows = self
            .client
            .inner()
            .query(
                "SELECT session_id, COALESCE(compaction_summary, session_id) AS title, \
                 meta->>'agent' AS agent, meta->>'model' AS model, message_count, \
                 token_input_total, token_output_total, created_at_ms, updated_at_ms \
                 FROM ene.chat_sessions ORDER BY updated_at_ms DESC LIMIT $1",
                &[&limit],
            )
            .await
            .context("list sessions")?;
        Ok(rows
            .iter()
            .map(|r| {
                serde_json::json!({
                    "session_id": r.get::<_, String>(0),
                    "title": r.get::<_, String>(1),
                    "agent": r.get::<_, Option<String>>(2),
                    "model": r.get::<_, Option<String>>(3),
                    "message_count": r.get::<_, i32>(4),
                    "token_input_total": r.get::<_, i64>(5),
                    "token_output_total": r.get::<_, i64>(6),
                    "created_at_ms": r.get::<_, i64>(7),
                    "updated_at_ms": r.get::<_, i64>(8),
                })
            })
            .collect())
    }

    pub async fn get_session(&self, session_id: &str) -> Result<Option<serde_json::Value>> {
        let sess = self
            .client
            .inner()
            .query_opt(
                "SELECT session_id, COALESCE(compaction_summary, session_id) AS title, \
                 meta->>'agent' AS agent, meta->>'model' AS model, message_count, \
                 token_input_total, token_output_total, created_at_ms, updated_at_ms, meta \
                 FROM ene.chat_sessions WHERE session_id = $1",
                &[&session_id],
            )
            .await
            .context("get session")?;
        let Some(sess) = sess else { return Ok(None) };
        let msgs = self
            .client
            .inner()
            .query(
                "SELECT message_index, role, blocks, text_content, token_input, \
                 token_output, tool_calls, created_at_ms \
                 FROM ene.chat_messages WHERE session_id = $1 ORDER BY message_index",
                &[&session_id],
            )
            .await
            .context("get messages")?;
        let messages: Vec<_> = msgs
            .iter()
            .map(|r| {
                serde_json::json!({
                    "message_index": r.get::<_, i32>(0),
                    "role": r.get::<_, String>(1),
                    "blocks": r.get::<_, serde_json::Value>(2),
                    "text_content": r.get::<_, String>(3),
                    "token_input": r.get::<_, i64>(4),
                    "token_output": r.get::<_, i64>(5),
                    "tool_calls": r.get::<_, serde_json::Value>(6),
                    "created_at_ms": r.get::<_, i64>(7),
                })
            })
            .collect();
        Ok(Some(serde_json::json!({
            "session_id": sess.get::<_, String>(0),
            "title": sess.get::<_, String>(1),
            "agent": sess.get::<_, Option<String>>(2),
            "model": sess.get::<_, Option<String>>(3),
            "message_count": sess.get::<_, i32>(4),
            "token_input_total": sess.get::<_, i64>(5),
            "token_output_total": sess.get::<_, i64>(6),
            "created_at_ms": sess.get::<_, i64>(7),
            "updated_at_ms": sess.get::<_, i64>(8),
            "meta": sess.get::<_, serde_json::Value>(9),
            "messages": messages,
        })))
    }
}
