use crate::models::{
    OpenCodeMessage, OpenCodePart, OpenCodeSession, OpenCodeSessionMessage, PartData,
};
use anyhow::{Context, Result};
use rusqlite::{Connection, OptionalExtension};
use std::path::Path;
use tracing::{debug, info, warn};

/// Source adapter for the OpenCode SQLite database.
pub struct OpenCodeSource {
    conn: Connection,
}

impl OpenCodeSource {
    /// Open the opencode.db at the given path.
    pub fn open<P: AsRef<Path>>(path: P) -> Result<Self> {
        let conn = Connection::open(path)?;
        conn.busy_timeout(std::time::Duration::from_secs(5))?;
        Ok(Self { conn })
    }

    /// Return every session row.
    pub fn sessions(&self) -> Result<Vec<OpenCodeSession>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, project_id, parent_id, slug, directory, title, version, \
             share_url, summary_additions, summary_deletions, summary_files, summary_diffs, \
             revert, permission, time_created, time_updated, time_compacting, time_archived, \
             workspace_id, path, agent, model, cost, tokens_input, tokens_output, \
             tokens_reasoning, tokens_cache_read, tokens_cache_write \
             FROM session ORDER BY time_created"
        )?;
        let rows = stmt.query_map([], |row| {
            Ok(OpenCodeSession {
                id: row.get(0)?,
                project_id: row.get(1)?,
                parent_id: row.get(2)?,
                slug: row.get(3)?,
                directory: row.get(4)?,
                title: row.get(5)?,
                version: row.get(6)?,
                share_url: row.get(7)?,
                summary_additions: row.get(8)?,
                summary_deletions: row.get(9)?,
                summary_files: row.get(10)?,
                summary_diffs: row.get(11)?,
                revert: row.get(12)?,
                permission: row.get(13)?,
                time_created: row.get(14)?,
                time_updated: row.get(15)?,
                time_compacting: row.get(16)?,
                time_archived: row.get(17)?,
                workspace_id: row.get(18)?,
                path: row.get(19)?,
                agent: row.get(20)?,
                model: row.get(21)?,
                cost: row.get(22)?,
                tokens_input: row.get(23)?,
                tokens_output: row.get(24)?,
                tokens_reasoning: row.get(25)?,
                tokens_cache_read: row.get(26)?,
                tokens_cache_write: row.get(27)?,
            })
        })?;
        let mut out = Vec::new();
        for r in rows {
            out.push(r?);
        }
        info!("loaded {} sessions from opencode.db", out.len());
        Ok(out)
    }

    /// Return every message row for a given session.
    pub fn messages_for_session(&self, session_id: &str) -> Result<Vec<OpenCodeMessage>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, session_id, time_created, time_updated, data \
             FROM message WHERE session_id = ?1 ORDER BY time_created, id"
        )?;
        let rows = stmt.query_map([session_id], |row| {
            let data_str: String = row.get(4)?;
            let data: crate::models::MessageData = serde_json::from_str(&data_str).unwrap_or_else(|e| {
                warn!("failed to parse message data for {}: {}", row.get::<usize, String>(0).unwrap_or_default(), e);
                crate::models::MessageData {
                    role: "unknown".into(),
                    time: None,
                    tokens: None,
                    cost: None,
                    model_id: None,
                    provider_id: None,
                    agent: None,
                    mode: None,
                    path: None,
                    finish: None,
                    summary: None,
                    parent_id: None,
                }
            });
            Ok(crate::models::OpenCodeMessage {
                id: row.get(0)?,
                session_id: row.get(1)?,
                time_created: row.get(2)?,
                time_updated: row.get(3)?,
                data,
            })
        })?;
        let mut out = Vec::new();
        for r in rows {
            out.push(r?);
        }
        Ok(out)
    }

    /// Return every part row for a given message.
    pub fn parts_for_message(&self, message_id: &str) -> Result<Vec<OpenCodePart>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, message_id, session_id, time_created, time_updated, data \
             FROM part WHERE message_id = ?1 ORDER BY time_created, id"
        )?;
        let rows = stmt.query_map([message_id], |row| {
            let data_str: String = row.get(5)?;
            let data: PartData = serde_json::from_str(&data_str).unwrap_or_else(|e| {
                warn!("failed to parse part data for {}: {}", row.get::<usize, String>(0).unwrap_or_default(), e);
                PartData {
                    r#type: "unknown".into(),
                    text: None,
                    tool: None,
                    call_id: None,
                    call_id_alt: None,
                    state: None,
                    input: None,
                    output: None,
                    is_error: None,
                }
            });
            Ok(OpenCodePart {
                id: row.get(0)?,
                message_id: row.get(1)?,
                session_id: row.get(2)?,
                time_created: row.get(3)?,
                time_updated: row.get(4)?,
                data,
            })
        })?;
        let mut out = Vec::new();
        for r in rows {
            out.push(r?);
        }
        Ok(out)
    }

    /// Return session_messages (lifecycle events) for a session.
    pub fn session_messages(&self, session_id: &str) -> Result<Vec<OpenCodeSessionMessage>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, session_id, type, time_created, time_updated, data \
             FROM session_message WHERE session_id = ?1 ORDER BY time_created"
        )?;
        let rows = stmt.query_map([session_id], |row| {
            let data_str: String = row.get(5)?;
            let data = serde_json::from_str(&data_str).unwrap_or(serde_json::Value::Null);
            Ok(OpenCodeSessionMessage {
                id: row.get(0)?,
                session_id: row.get(1)?,
                r#type: row.get(2)?,
                time_created: row.get(3)?,
                time_updated: row.get(4)?,
                data,
            })
        })?;
        let mut out = Vec::new();
        for r in rows {
            out.push(r?);
        }
        Ok(out)
    }

    /// Get the max time_updated among all sessions (for incremental sync).
    pub fn max_session_updated(&self) -> Result<Option<i64>> {
        self.conn
            .query_row(
                "SELECT MAX(time_updated) FROM session",
                [],
                |row| row.get(0),
            )
            .optional()
            .context("query max session updated")
    }

    /// Get sessions updated since a given timestamp.
    pub fn sessions_since(&self, since_ms: i64) -> Result<Vec<OpenCodeSession>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, project_id, parent_id, slug, directory, title, version, \
             share_url, summary_additions, summary_deletions, summary_files, summary_diffs, \
             revert, permission, time_created, time_updated, time_compacting, time_archived, \
             workspace_id, path, agent, model, cost, tokens_input, tokens_output, \
             tokens_reasoning, tokens_cache_read, tokens_cache_write \
             FROM session WHERE time_updated > ?1 ORDER BY time_created"
        )?;
        let rows = stmt.query_map([since_ms], |row| {
            Ok(OpenCodeSession {
                id: row.get(0)?,
                project_id: row.get(1)?,
                parent_id: row.get(2)?,
                slug: row.get(3)?,
                directory: row.get(4)?,
                title: row.get(5)?,
                version: row.get(6)?,
                share_url: row.get(7)?,
                summary_additions: row.get(8)?,
                summary_deletions: row.get(9)?,
                summary_files: row.get(10)?,
                summary_diffs: row.get(11)?,
                revert: row.get(12)?,
                permission: row.get(13)?,
                time_created: row.get(14)?,
                time_updated: row.get(15)?,
                time_compacting: row.get(16)?,
                time_archived: row.get(17)?,
                workspace_id: row.get(18)?,
                path: row.get(19)?,
                agent: row.get(20)?,
                model: row.get(21)?,
                cost: row.get(22)?,
                tokens_input: row.get(23)?,
                tokens_output: row.get(24)?,
                tokens_reasoning: row.get(25)?,
                tokens_cache_read: row.get(26)?,
                tokens_cache_write: row.get(27)?,
            })
        })?;
        let mut out = Vec::new();
        for r in rows {
            out.push(r?);
        }
        Ok(out)
    }
}
