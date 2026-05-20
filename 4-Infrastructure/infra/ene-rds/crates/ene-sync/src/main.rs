use anyhow::{Context, Result};
use clap::{Parser, Subcommand};
use ene_rds_chat::{ChatLogSurface, ChatMessage, ChatSession, MessageBlock, ToolCall};
use ene_rds_core::RdsClient;
use rusqlite::{Connection, OptionalExtension};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::time::Duration;
use tracing::{info, warn};

#[derive(Parser, Debug)]
#[command(name = "ene-sync")]
#[command(about = "Sync OpenCode sessions to ENE RDS")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
    #[arg(long, global = true)]
    db: Option<PathBuf>,
    #[arg(long, global = true)]
    dsn: Option<String>,
    #[arg(long, global = true)]
    embed: bool,
}

#[derive(Subcommand, Debug)]
enum Commands {
    Sync {
        #[arg(long)]
        since: Option<i64>,
    },
    Watch {
        #[arg(long, default_value = "60")]
        interval: u64,
    },
    InitSchema,
}

fn default_db_path() -> PathBuf {
    dirs::home_dir()
        .unwrap_or_else(|| PathBuf::from("/home/allaun"))
        .join(".local/share/opencode/opencode.db")
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .init();

    let cli = Cli::parse();
    let db_path = cli.db.unwrap_or_else(default_db_path);
    let dsn = cli.dsn.unwrap_or_else(RdsClient::dsn_from_env);

    match cli.command {
        Commands::Sync { since } => cmd_sync(&db_path, &dsn, cli.embed, since).await,
        Commands::Watch { interval } => cmd_watch(&db_path, &dsn, cli.embed, interval).await,
        Commands::InitSchema => cmd_init_schema(&dsn).await,
    }
}

async fn cmd_sync(
    db_path: &PathBuf,
    dsn: &str,
    enable_embed: bool,
    since: Option<i64>,
) -> Result<()> {
    info!("opening opencode.db at {:?}", db_path);
    let sqlite = Connection::open(db_path)?;
    sqlite.busy_timeout(Duration::from_secs(5))?;

    info!("connecting to RDS");
    let client = RdsClient::connect(dsn).await?;
    client.init_schema().await?;
    let chat = ChatLogSurface::new(client);
    chat.init_tables().await?;

    let embedder = if enable_embed {
        Some(Embedder::new())
    } else {
        None
    };

    let sessions = if let Some(ts) = since {
        sessions_since(&sqlite, ts)?
    } else {
        load_sessions(&sqlite)?
    };

    let total = sessions.len();
    let mut synced = 0;
    for (i, sess) in sessions.iter().enumerate() {
        info!("[{}/{}] syncing {}", i + 1, total, sess.id);

        let raw_msgs = messages_for_session(&sqlite, &sess.id)?;
        let mut chat_msgs = Vec::with_capacity(raw_msgs.len());
        for (idx, raw) in raw_msgs.iter().enumerate() {
            let parts = parts_for_message(&sqlite, &raw.id)?;
            let cm = normalize_message(raw, &parts, idx as i32)?;
            chat_msgs.push(cm);
        }

        let mut chat_session = normalize_session(sess, &chat_msgs, None);

        if let Some(ref emb) = embedder {
            let text = format!(
                "{} {} {}",
                sess.title,
                sess.agent.as_deref().unwrap_or(""),
                sess.model.as_deref().unwrap_or("")
            );
            if let Ok(v) = emb.embed(&text).await {
                chat_session.embedding = Some(v);
            }
            for cm in &mut chat_msgs {
                if !cm.text_content.is_empty() {
                    if let Ok(v) = emb.embed(&cm.text_content).await {
                        cm.embedding = Some(v);
                    }
                }
            }
        }

        chat.delete_messages_for_session(&sess.id).await?;
        chat.upsert_session(&chat_session).await?;
        chat.upsert_messages(&sess.id, &chat_msgs).await?;
        synced += 1;
    }

    info!("sync complete: {} sessions", synced);
    Ok(())
}

async fn cmd_watch(db_path: &PathBuf, dsn: &str, enable_embed: bool, interval: u64) -> Result<()> {
    let state_path = dirs::cache_dir()
        .unwrap_or_else(|| PathBuf::from("/tmp"))
        .join("ene-sync/state.json");
    if let Some(p) = state_path.parent() {
        let _ = std::fs::create_dir_all(p);
    }

    let mut last: i64 = std::fs::read_to_string(&state_path)
        .ok()
        .and_then(|s| s.trim().parse().ok())
        .unwrap_or(0);

    info!("watch mode, last_synced={}", last);
    loop {
        if let Err(e) = cmd_sync(db_path, dsn, enable_embed, Some(last)).await {
            warn!("sync failed: {}", e);
        }
        let sqlite = Connection::open(db_path)?;
        if let Ok(Some(max)) = max_session_updated(&sqlite) {
            last = max;
            let _ = std::fs::write(&state_path, last.to_string());
        }
        tokio::time::sleep(Duration::from_secs(interval)).await;
    }
}

async fn cmd_init_schema(dsn: &str) -> Result<()> {
    let client = RdsClient::connect(dsn).await?;
    client.init_schema().await?;
    let chat = ChatLogSurface::new(client);
    chat.init_tables().await?;
    println!("RDS chat schema initialized");
    Ok(())
}

// ─── SQLite source helpers ──────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
struct OpenCodeSession {
    id: String,
    project_id: String,
    parent_id: Option<String>,
    slug: String,
    directory: String,
    title: String,
    agent: Option<String>,
    model: Option<String>,
    time_created: i64,
    time_updated: i64,
    tokens_input: i64,
    tokens_output: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct OpenCodeMessage {
    id: String,
    session_id: String,
    time_created: i64,
    #[serde(rename = "role")]
    data_role: String,
    #[serde(default)]
    data: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct OpenCodePart {
    #[serde(rename = "type")]
    part_type: String,
    #[serde(default)]
    text: Option<String>,
    #[serde(default)]
    tool: Option<String>,
    #[serde(default, rename = "callID")]
    call_id: Option<String>,
    #[serde(default)]
    input: Option<serde_json::Value>,
    #[serde(default)]
    output: Option<serde_json::Value>,
    #[serde(default)]
    is_error: Option<bool>,
}

fn load_sessions(conn: &Connection) -> Result<Vec<OpenCodeSession>> {
    let mut stmt = conn.prepare(
        "SELECT id, project_id, parent_id, slug, directory, title, \
         agent, model, time_created, time_updated, tokens_input, tokens_output \
         FROM session ORDER BY time_created",
    )?;
    let rows = stmt.query_map([], |row| {
        Ok(OpenCodeSession {
            id: row.get(0)?,
            project_id: row.get(1)?,
            parent_id: row.get(2)?,
            slug: row.get(3)?,
            directory: row.get(4)?,
            title: row.get(5)?,
            agent: row.get(6)?,
            model: row.get(7)?,
            time_created: row.get(8)?,
            time_updated: row.get(9)?,
            tokens_input: row.get(10)?,
            tokens_output: row.get(11)?,
        })
    })?;
    rows.collect::<Result<Vec<_>, _>>().map_err(|e| e.into())
}

fn sessions_since(conn: &Connection, since_ms: i64) -> Result<Vec<OpenCodeSession>> {
    let mut stmt = conn.prepare(
        "SELECT id, project_id, parent_id, slug, directory, title, \
         agent, model, time_created, time_updated, tokens_input, tokens_output \
         FROM session WHERE time_updated > ?1 ORDER BY time_created",
    )?;
    let rows = stmt.query_map([since_ms], |row| {
        Ok(OpenCodeSession {
            id: row.get(0)?,
            project_id: row.get(1)?,
            parent_id: row.get(2)?,
            slug: row.get(3)?,
            directory: row.get(4)?,
            title: row.get(5)?,
            agent: row.get(6)?,
            model: row.get(7)?,
            time_created: row.get(8)?,
            time_updated: row.get(9)?,
            tokens_input: row.get(10)?,
            tokens_output: row.get(11)?,
        })
    })?;
    rows.collect::<Result<Vec<_>, _>>().map_err(|e| e.into())
}

fn max_session_updated(conn: &Connection) -> Result<Option<i64>> {
    conn.query_row("SELECT MAX(time_updated) FROM session", [], |row| {
        row.get(0)
    })
    .optional()
    .map_err(|e| e.into())
}

fn messages_for_session(conn: &Connection, session_id: &str) -> Result<Vec<OpenCodeMessage>> {
    let mut stmt = conn.prepare(
        "SELECT id, session_id, time_created, data FROM message \
         WHERE session_id = ?1 ORDER BY time_created, id",
    )?;
    let rows = stmt.query_map([session_id], |row| {
        let data_str: String = row.get(3)?;
        let data: serde_json::Value =
            serde_json::from_str(&data_str).unwrap_or(serde_json::Value::Null);
        let role = data
            .get("role")
            .and_then(|v| v.as_str())
            .unwrap_or("unknown")
            .to_string();
        Ok(OpenCodeMessage {
            id: row.get(0)?,
            session_id: row.get(1)?,
            time_created: row.get(2)?,
            data_role: role,
            data,
        })
    })?;
    rows.collect::<Result<Vec<_>, _>>().map_err(|e| e.into())
}

fn parts_for_message(conn: &Connection, message_id: &str) -> Result<Vec<OpenCodePart>> {
    let mut stmt =
        conn.prepare("SELECT data FROM part WHERE message_id = ?1 ORDER BY time_created, id")?;
    let rows = stmt.query_map([message_id], |row| {
        let data_str: String = row.get(0)?;
        let part: OpenCodePart = serde_json::from_str(&data_str).unwrap_or(OpenCodePart {
            part_type: "unknown".into(),
            text: None,
            tool: None,
            call_id: None,
            input: None,
            output: None,
            is_error: None,
        });
        Ok(part)
    })?;
    rows.collect::<Result<Vec<_>, _>>().map_err(|e| e.into())
}

fn normalize_session(
    sess: &OpenCodeSession,
    msgs: &[ChatMessage],
    _compaction: Option<String>,
) -> ChatSession {
    ChatSession {
        session_id: sess.id.clone(),
        workspace_fingerprint: Some(workspace_fingerprint(&sess.directory)),
        workspace_root: Some(sess.directory.clone()),
        fork_parent_session_id: sess.parent_id.clone(),
        compaction_count: 0,
        compaction_summary: None,
        message_count: msgs.len() as i32,
        token_input_total: sess.tokens_input,
        token_output_total: sess.tokens_output,
        created_at_ms: sess.time_created,
        updated_at_ms: sess.time_updated,
        first_message_at_ms: msgs.first().map(|m| m.created_at_ms),
        last_message_at_ms: msgs.last().map(|m| m.created_at_ms),
        meta: serde_json::json!({
            "slug": &sess.slug, "agent": &sess.agent, "model": &sess.model,
            "project_id": &sess.project_id,
        }),
        embedding: None,
        receipt: None,
    }
}

fn normalize_message(
    msg: &OpenCodeMessage,
    parts: &[OpenCodePart],
    index: i32,
) -> Result<ChatMessage> {
    let mut blocks = Vec::new();
    let mut text_parts = Vec::new();
    let mut tool_calls = Vec::new();

    for part in parts {
        match part.part_type.as_str() {
            "text" => {
                if let Some(ref t) = part.text {
                    text_parts.push(t.clone());
                    blocks.push(MessageBlock {
                        block_type: "text".into(),
                        text: Some(t.clone()),
                        tool_name: None,
                        tool_input: None,
                        tool_output: None,
                        is_error: None,
                    });
                }
            }
            "reasoning" => {
                if let Some(ref t) = part.text {
                    text_parts.push(format!("[reasoning] {}", t));
                    blocks.push(MessageBlock {
                        block_type: "reasoning".into(),
                        text: Some(t.clone()),
                        tool_name: None,
                        tool_input: None,
                        tool_output: None,
                        is_error: None,
                    });
                }
            }
            "tool" => {
                let call_id = part.call_id.clone().unwrap_or_default();
                let tool_name = part.tool.clone().unwrap_or_default();
                blocks.push(MessageBlock {
                    block_type: "tool_use".into(),
                    text: None,
                    tool_name: Some(tool_name.clone()),
                    tool_input: part.input.clone(),
                    tool_output: part.output.clone(),
                    is_error: part.is_error,
                });
                tool_calls.push(ToolCall {
                    call_id: call_id.clone(),
                    tool_name,
                    input: part.input.clone().unwrap_or(serde_json::json!({})),
                });
            }
            "tool-result" => {
                blocks.push(MessageBlock {
                    block_type: "tool_result".into(),
                    text: part.text.clone(),
                    tool_name: part.tool.clone(),
                    tool_input: None,
                    tool_output: part.output.clone(),
                    is_error: part.is_error,
                });
            }
            _ => {}
        }
    }

    Ok(ChatMessage {
        session_id: msg.session_id.clone(),
        message_index: index,
        role: msg.data_role.clone(),
        blocks,
        text_content: text_parts.join("\n"),
        token_input: 0,
        token_output: 0,
        token_cache_creation: 0,
        token_cache_read: 0,
        tool_calls,
        embedding: None,
        receipt_hash: None,
        created_at_ms: msg.time_created,
    })
}

fn workspace_fingerprint(path: &str) -> String {
    const FNV_OFFSET: u64 = 0xcbf29ce484222325;
    const FNV_PRIME: u64 = 0x100000001b3;
    let mut hash = FNV_OFFSET;
    for b in path.bytes() {
        hash ^= u64::from(b);
        hash = hash.wrapping_mul(FNV_PRIME);
    }
    format!("{:016x}", hash)
}

// ─── Embedding helper ───────────────────────────────────────────────────

struct Embedder {
    client: reqwest::Client,
    url: String,
    model: String,
}

impl Embedder {
    fn new() -> Self {
        let base = std::env::var("OLLAMA_HOST").unwrap_or_else(|_| "http://localhost:11434".into());
        let model =
            std::env::var("OLLAMA_EMBED_MODEL").unwrap_or_else(|_| "nomic-embed-text".into());
        Self {
            client: reqwest::Client::new(),
            url: format!("{}/api/embeddings", base.trim_end_matches('/')),
            model,
        }
    }

    async fn embed(&self, text: &str) -> Result<Vec<f32>> {
        let resp = self
            .client
            .post(&self.url)
            .json(&serde_json::json!({"model": self.model, "prompt": text}))
            .send()
            .await
            .context("embed POST")?;
        if !resp.status().is_success() {
            anyhow::bail!("embed HTTP {}", resp.status());
        }
        let json: serde_json::Value = resp.json().await.context("embed JSON")?;
        let arr = json
            .get("embedding")
            .and_then(|v| v.as_array())
            .context("missing embedding")?;
        Ok(arr
            .iter()
            .map(|v| v.as_f64().unwrap_or(0.0) as f32)
            .collect())
    }
}
