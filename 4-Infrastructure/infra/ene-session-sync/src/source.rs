use crate::models::{
    ChatMessage, ChatSession, MessageBlock, OpenCodeMessage, OpenCodePart, OpenCodeSession,
    OpenCodeSessionMessage, PartData, ToolCall,
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

// ---------------------------------------------------------------------------
// Claw JSONL source
// ---------------------------------------------------------------------------

/// Source adapter for Claw JSONL session files (`.claw/sessions/*.jsonl`).
///
/// Each file is either:
///   - A single-line JSON object `{"version":1,"session_id":"...","messages":[...]}`, or
///   - A newline-delimited JSONL stream where each line is a message record.
///
/// This adapter reads the files, parses whatever format it finds, and converts
/// them into the same [`ChatSession`] + [`ChatMessage`] types that the RDS sink
/// expects.  This makes the sync pipeline source-agnostic.
pub struct ClawSource {
    sessions_dir: std::path::PathBuf,
}

impl ClawSource {
    /// Create a source pointed at a `.claw/sessions/` directory.
    pub fn new(sessions_dir: impl AsRef<std::path::Path>) -> Self {
        Self {
            sessions_dir: sessions_dir.as_ref().to_path_buf(),
        }
    }

    /// Discover all `.jsonl` files under the sessions directory.
    fn find_files(&self) -> anyhow::Result<Vec<std::path::PathBuf>> {
        if !self.sessions_dir.exists() {
            info!(
                "Claw sessions dir not found, skipping: {:?}",
                self.sessions_dir
            );
            return Ok(Vec::new());
        }
        let mut files = Vec::new();
        for entry in std::fs::read_dir(&self.sessions_dir)
            .with_context(|| format!("read dir {:?}", self.sessions_dir))?
        {
            let entry = entry?;
            let path = entry.path();
            if path.extension().and_then(|e| e.to_str()) == Some("jsonl") {
                files.push(path);
            }
        }
        files.sort();
        Ok(files)
    }

    /// Parse a single JSONL session file into a `(ChatSession, Vec<ChatMessage>)`.
    ///
    /// The file is either a single full-session JSON object, or a stream of
    /// per-message JSONL lines.  Both formats are tried.
    pub fn load_file(
        path: &std::path::Path,
    ) -> anyhow::Result<Option<(ChatSession, Vec<ChatMessage>)>> {
        let raw = std::fs::read_to_string(path)
            .with_context(|| format!("read {:?}", path))?;

        // Skip Git LFS stub files.
        if raw.starts_with("version https://git-lfs.github.com") {
            debug!("skipping LFS stub: {:?}", path);
            return Ok(None);
        }

        // Derive a session ID from the file name: session-<ts>-<n>.jsonl
        let stem = path
            .file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("unknown");

        // Try full-JSON format first.
        if let Ok(obj) = serde_json::from_str::<serde_json::Value>(raw.trim()) {
            if obj.is_object() {
                return Self::from_full_json(&obj, stem).map(Some);
            }
        }

        // Fall back to JSONL stream.
        Self::from_jsonl_stream(&raw, stem).map(Some)
    }

    fn from_full_json(
        obj: &serde_json::Value,
        stem: &str,
    ) -> anyhow::Result<(ChatSession, Vec<ChatMessage>)> {
        let session_id = obj
            .get("session_id")
            .and_then(|v| v.as_str())
            .unwrap_or(stem)
            .to_string();
        let created_at_ms = obj
            .get("created_at_ms")
            .and_then(|v| v.as_i64())
            .unwrap_or(0);
        let updated_at_ms = obj
            .get("updated_at_ms")
            .and_then(|v| v.as_i64())
            .unwrap_or(created_at_ms);
        let workspace_root = obj
            .get("workspace_root")
            .and_then(|v| v.as_str())
            .map(String::from);
        let fork_parent = obj
            .get("fork")
            .and_then(|f| f.get("parent_session_id"))
            .and_then(|v| v.as_str())
            .map(String::from);
        let compaction_count = obj
            .get("compaction")
            .and_then(|c| c.get("count"))
            .and_then(|v| v.as_i64())
            .unwrap_or(0) as i32;
        let compaction_summary = obj
            .get("compaction")
            .and_then(|c| c.get("summary"))
            .and_then(|v| v.as_str())
            .map(String::from);

        let messages_raw = obj
            .get("messages")
            .and_then(|v| v.as_array())
            .cloned()
            .unwrap_or_default();

        let mut chat_messages = Vec::new();
        let mut first_at: Option<i64> = None;
        let mut last_at: Option<i64> = None;

        for (idx, msg) in messages_raw.iter().enumerate() {
            let cm = Self::parse_message(msg, &session_id, idx as i32)?;
            first_at = first_at.or(Some(cm.created_at_ms));
            last_at = Some(cm.created_at_ms);
            chat_messages.push(cm);
        }

        let fingerprint = workspace_root
            .as_deref()
            .map(crate::normalize::workspace_fingerprint);
        let session = ChatSession {
            session_id: session_id.clone(),
            title: None, // Claw sessions have no title field
            agent: Some("claw".into()),
            model: None,
            workspace_fingerprint: fingerprint,
            workspace_root,
            fork_parent_session_id: fork_parent,
            compaction_count,
            compaction_summary,
            message_count: chat_messages.len() as i32,
            token_input_total: 0,
            token_output_total: 0,
            created_at_ms,
            updated_at_ms,
            first_message_at_ms: first_at,
            last_message_at_ms: last_at,
            meta: serde_json::json!({"source": "claw"}),
            embedding: None,
            receipt: None,
        };
        Ok((session, chat_messages))
    }

    fn from_jsonl_stream(
        raw: &str,
        stem: &str,
    ) -> anyhow::Result<(ChatSession, Vec<ChatMessage>)> {
        // A JSONL stream has one JSON object per line; the first line may be a
        // session header or the first message.
        let mut session_id = stem.to_string();
        let mut created_at_ms: i64 = 0;
        let mut workspace_root: Option<String> = None;
        let mut chat_messages = Vec::new();
        let mut first_at: Option<i64> = None;

        for (line_idx, line) in raw.lines().enumerate() {
            let trimmed = line.trim();
            if trimmed.is_empty() {
                continue;
            }
            let Ok(obj) = serde_json::from_str::<serde_json::Value>(trimmed) else {
                warn!("non-JSON line {} in {}", line_idx + 1, stem);
                continue;
            };

            // If the first object has a "session_id" key treat it as a header.
            if line_idx == 0 {
                if let Some(id) = obj.get("session_id").and_then(|v| v.as_str()) {
                    session_id = id.to_string();
                    created_at_ms = obj
                        .get("created_at_ms")
                        .and_then(|v| v.as_i64())
                        .unwrap_or(0);
                    workspace_root = obj
                        .get("workspace_root")
                        .and_then(|v| v.as_str())
                        .map(String::from);
                    continue;
                }
            }

            // Otherwise treat each line as a message.
            let cm =
                Self::parse_message(&obj, &session_id, chat_messages.len() as i32)?;
            first_at = first_at.or(Some(cm.created_at_ms));
            chat_messages.push(cm);
        }

        let last_at = chat_messages.last().map(|m| m.created_at_ms);
        let fingerprint = workspace_root
            .as_deref()
            .map(crate::normalize::workspace_fingerprint);
        let session = ChatSession {
            session_id: session_id.clone(),
            title: None,
            agent: Some("claw".into()),
            model: None,
            workspace_fingerprint: fingerprint,
            workspace_root,
            fork_parent_session_id: None,
            compaction_count: 0,
            compaction_summary: None,
            message_count: chat_messages.len() as i32,
            token_input_total: 0,
            token_output_total: 0,
            created_at_ms,
            updated_at_ms: last_at.unwrap_or(created_at_ms),
            first_message_at_ms: first_at,
            last_message_at_ms: last_at,
            meta: serde_json::json!({"source": "claw"}),
            embedding: None,
            receipt: None,
        };
        Ok((session, chat_messages))
    }

    /// Parse a single message object (from either format) into a [`ChatMessage`].
    fn parse_message(
        msg: &serde_json::Value,
        session_id: &str,
        index: i32,
    ) -> anyhow::Result<ChatMessage> {
        let role = msg
            .get("role")
            .and_then(|v| v.as_str())
            .unwrap_or("unknown")
            .to_string();
        let created_at_ms = msg
            .get("timestamp_ms")
            .or_else(|| msg.get("created_at_ms"))
            .and_then(|v| v.as_i64())
            .unwrap_or(0);
        let usage = msg.get("usage");
        let token_input = usage
            .and_then(|u| u.get("input_tokens"))
            .and_then(|v| v.as_i64())
            .unwrap_or(0);
        let token_output = usage
            .and_then(|u| u.get("output_tokens"))
            .and_then(|v| v.as_i64())
            .unwrap_or(0);
        let cache_creation = usage
            .and_then(|u| u.get("cache_creation_input_tokens"))
            .and_then(|v| v.as_i64())
            .unwrap_or(0);
        let cache_read = usage
            .and_then(|u| u.get("cache_read_input_tokens"))
            .and_then(|v| v.as_i64())
            .unwrap_or(0);

        let mut blocks: Vec<MessageBlock> = Vec::new();
        let mut text_parts: Vec<String> = Vec::new();
        let mut tool_calls: Vec<ToolCall> = Vec::new();

        // Blocks are either in msg["blocks"] or msg["content"].
        let blocks_raw = msg
            .get("blocks")
            .or_else(|| msg.get("content"))
            .and_then(|v| v.as_array())
            .cloned()
            .unwrap_or_default();

        for block in &blocks_raw {
            let btype = block
                .get("type")
                .and_then(|v| v.as_str())
                .unwrap_or("unknown");
            match btype {
                "text" => {
                    let text = block
                        .get("text")
                        .and_then(|v| v.as_str())
                        .unwrap_or("")
                        .to_string();
                    text_parts.push(text.clone());
                    blocks.push(MessageBlock {
                        block_type: "text".into(),
                        text: Some(text),
                        tool_name: None,
                        tool_input: None,
                        tool_output: None,
                        is_error: None,
                    });
                }
                "tool_use" => {
                    let tool_name = block
                        .get("name")
                        .and_then(|v| v.as_str())
                        .unwrap_or("")
                        .to_string();
                    let call_id = block
                        .get("id")
                        .and_then(|v| v.as_str())
                        .unwrap_or("")
                        .to_string();
                    let input = block.get("input").cloned().unwrap_or(serde_json::json!({}));
                    blocks.push(MessageBlock {
                        block_type: "tool_use".into(),
                        text: None,
                        tool_name: Some(tool_name.clone()),
                        tool_input: Some(input.clone()),
                        tool_output: None,
                        is_error: None,
                    });
                    tool_calls.push(ToolCall {
                        call_id,
                        tool_name,
                        input,
                    });
                }
                "tool_result" => {
                    let content = block.get("content").cloned();
                    let text = content
                        .as_ref()
                        .and_then(|v| v.as_str())
                        .map(String::from);
                    let is_error = block
                        .get("is_error")
                        .and_then(|v| v.as_bool());
                    blocks.push(MessageBlock {
                        block_type: "tool_result".into(),
                        text,
                        tool_name: None,
                        tool_input: None,
                        tool_output: content,
                        is_error,
                    });
                }
                other => {
                    blocks.push(MessageBlock {
                        block_type: other.to_string(),
                        text: block.get("text").and_then(|v| v.as_str()).map(String::from),
                        tool_name: None,
                        tool_input: None,
                        tool_output: None,
                        is_error: None,
                    });
                }
            }
        }

        Ok(ChatMessage {
            session_id: session_id.to_string(),
            message_index: index,
            role,
            blocks,
            text_content: text_parts.join("\n"),
            token_input,
            token_output,
            token_cache_creation: cache_creation,
            token_cache_read: cache_read,
            tool_calls,
            embedding: None,
            receipt_hash: None,
            created_at_ms,
        })
    }

    /// Walk the sessions directory and return all valid (session, messages) pairs.
    pub fn load_all(&self) -> anyhow::Result<Vec<(ChatSession, Vec<ChatMessage>)>> {
        let files = self.find_files()?;
        let mut out = Vec::new();
        for path in &files {
            match Self::load_file(path) {
                Ok(Some(pair)) => out.push(pair),
                Ok(None) => {} // LFS stub or empty, skipped
                Err(e) => warn!("error loading Claw session {:?}: {}", path.display(), e),
            }
        }
        info!("loaded {} Claw sessions from {:?}", out.len(), self.sessions_dir);
        Ok(out)
    }
}
