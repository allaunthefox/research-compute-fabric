mod bridge;
mod compression;
mod credential;
mod deepseek_adapter;
mod embed;
mod ene_cloud_credential_manager;
mod ene_core;
mod enhanced_swarm;
mod fractal_fold;
mod gemma_integration;
mod hyperbolic_encoding;
mod knowledge_ingestion;
mod manifold_perception;
mod math;
mod meta_autotype;
mod misc;
mod models;
mod normalize;
mod s3c;
mod s3c_lean_review;
mod search_adapter;
mod sink;
mod source;
mod swarm;
mod topology;
mod wiki;

use anyhow::Result;
use clap::{Parser, Subcommand};
use std::path::PathBuf;
use std::time::Duration;
use tracing::{info, warn};

/// ENE Session Sync — Rust daemon that syncs opencode.db chat logs to RDS PostgreSQL.
#[derive(Parser, Debug)]
#[command(name = "ene-session-sync")]
#[command(about = "Sync OpenCode sessions to ENE RDS")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
    /// Path to opencode.db (default: ~/.local/share/opencode/opencode.db)
    #[arg(long, global = true)]
    db: Option<PathBuf>,
    /// PostgreSQL DSN (default: from RDS_* env vars)
    #[arg(long, global = true)]
    dsn: Option<String>,
    /// Directory containing Python infra modules (default: ./infra)
    #[arg(long, global = true)]
    infra_dir: Option<PathBuf>,
    /// Enable embedding generation via Ollama
    #[arg(long, global = true)]
    embed: bool,
}

#[derive(Subcommand, Debug)]
enum Commands {
    /// One-shot sync of all sessions (or since last watch checkpoint)
    Sync {
        /// Only sync sessions updated since this timestamp (ms)
        #[arg(long)]
        since: Option<i64>,
    },
    /// Continuous watch mode — poll for new/changed sessions
    Watch {
        /// Poll interval in seconds
        #[arg(long, default_value = "60")]
        interval: u64,
    },
    /// Search sessions by keyword
    Search {
        /// Search query
        query: String,
        /// Limit results
        #[arg(long, default_value = "10")]
        limit: i64,
        /// Semantic search (requires --embed)
        #[arg(long)]
        semantic: bool,
    },
    /// Test the Python bridge
    BridgeTest {
        /// Python module name to call
        #[arg(default_value = "ene_rds_wiki_layer")]
        module: String,
    },
    /// List recent sessions from RDS
    List {
        /// Number of sessions to return
        #[arg(long, default_value = "20")]
        limit: i64,
    },
    /// Retrieve a single session with all messages
    Get {
        /// Session ID
        session_id: String,
    },
    /// Sync Claw JSONL session files from a .claw/sessions/ directory
    ClawSync {
        /// Path to the .claw/sessions/ directory
        #[arg(long)]
        sessions_dir: PathBuf,
    },
    /// Initialize RDS schema only (no data)
    InitSchema,
}

fn default_db_path() -> PathBuf {
    dirs::home_dir()
        .unwrap_or_else(|| PathBuf::from("/home/allaun"))
        .join(".local/share/opencode/opencode.db")
}

fn default_infra_dir() -> PathBuf {
    let exe = std::env::current_exe().unwrap_or_else(|_| PathBuf::from("."));
    exe.parent()
        .unwrap_or_else(|| std::path::Path::new("."))
        .join("infra")
}

fn build_dsn() -> String {
    if let Ok(dsn) = std::env::var("RDS_DSN") {
        return dsn;
    }
    let host = std::env::var("RDS_HOST")
        .unwrap_or_else(|_| "database-1.cluster-c9i0w8eu8fnv.us-east-2.rds.amazonaws.com".into());
    let port = std::env::var("RDS_PORT").unwrap_or_else(|_| "5432".into());
    let user = std::env::var("RDS_USER").unwrap_or_else(|_| "postgres".into());
    let password = std::env::var("RDS_PASSWORD")
        .or_else(|_| std::env::var("RDS_IAM_TOKEN"))
        .unwrap_or_default();
    let dbname = std::env::var("RDS_DB").unwrap_or_else(|_| "postgres".into());
    format!(
        "host={} port={} dbname={} user={} password={} sslmode=require",
        host, port, dbname, user, password
    )
}

/// FNV-1a 64-bit hash rendered as 16 hex chars — lightweight receipt digest.
/// (Not a cryptographic hash — use only for shim deduplication keys.)
fn sha256_text(text: &str) -> String {
    const FNV_OFFSET: u64 = 0xcbf2_9ce4_8422_2325;
    const FNV_PRIME: u64 = 0x0000_0001_0000_01b3;
    let mut hash = FNV_OFFSET;
    for byte in text.bytes() {
        hash ^= u64::from(byte);
        hash = hash.wrapping_mul(FNV_PRIME);
    }
    format!("{:016x}", hash)
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .init();

    let cli = Cli::parse();
    let db_path = cli.db.unwrap_or_else(default_db_path);
    let dsn = cli.dsn.unwrap_or_else(build_dsn);
    let infra_dir = cli.infra_dir.unwrap_or_else(default_infra_dir);

    match cli.command {
        Commands::Sync { since } => cmd_sync(&db_path, &dsn, cli.embed, since).await,
        Commands::Watch { interval } => cmd_watch(&db_path, &dsn, cli.embed, interval).await,
        Commands::Search {
            query,
            limit,
            semantic,
        } => cmd_search(&dsn, &query, limit, semantic).await,
        Commands::BridgeTest { module } => cmd_bridge_test(&infra_dir, &module),
        Commands::List { limit } => cmd_list(&dsn, limit).await,
        Commands::Get { session_id } => cmd_get(&dsn, &session_id).await,
        Commands::ClawSync { sessions_dir } => {
            cmd_claw_sync(&sessions_dir, &dsn, cli.embed).await
        }
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
    let source = source::OpenCodeSource::open(db_path)?;

    info!("connecting to RDS");
    let sink = sink::RdsSink::connect(dsn).await?;

    let embedder = if enable_embed {
        let e = embed::Embedder::from_env();
        if !e.health_check().await.unwrap_or(false) {
            warn!("Ollama not reachable — embeddings disabled");
            None
        } else {
            info!("Ollama embedding enabled");
            Some(e)
        }
    } else {
        None
    };

    let sessions = if let Some(ts) = since {
        source.sessions_since(ts)?
    } else {
        source.sessions()?
    };

    let total = sessions.len();
    let mut synced = 0;
    for (i, sess) in sessions.iter().enumerate() {
        info!("[{}/{}] syncing session {} — {}", i + 1, total, sess.id, sess.title);

        let raw_messages = source.messages_for_session(&sess.id)?;
        let mut chat_messages = Vec::with_capacity(raw_messages.len());
        for (idx, raw_msg) in raw_messages.iter().enumerate() {
            let parts = source.parts_for_message(&raw_msg.id)?;
            let cm = normalize::normalize_message(raw_msg, &parts, idx as i32)?;
            chat_messages.push(cm);
        }

        let compaction = source
            .session_messages(&sess.id)?
            .into_iter()
            .map(|sm| format!("{}: {}", sm.r#type, sm.data))
            .collect::<Vec<_>>()
            .join("\n");
        let compaction_summary = if compaction.is_empty() {
            None
        } else {
            Some(compaction)
        };

        let mut chat_session = normalize::normalize_session(sess, &chat_messages, compaction_summary);

        if let Some(ref emb) = embedder {
            let session_text = format!(
                "{} {} {}",
                sess.title,
                sess.agent.as_deref().unwrap_or(""),
                sess.model.as_deref().unwrap_or("")
            );
            match emb.embed(&session_text).await {
                Ok(v) => chat_session.embedding = Some(v),
                Err(e) => warn!("session embedding failed: {}", e),
            }

            for cm in &mut chat_messages {
                if !cm.text_content.is_empty() {
                    match emb.embed(&cm.text_content).await {
                        Ok(v) => cm.embedding = Some(v),
                        Err(e) => warn!("message embedding failed: {}", e),
                    }
                }
            }
        }

        sink.delete_messages_for_session(&sess.id).await?;
        sink.upsert_session(&chat_session).await?;
        sink.upsert_messages(&sess.id, &chat_messages).await?;
        synced += 1;
    }

    let receipt = models::IngestionReceipt {
        shim_name: "ene-session-sync".into(),
        status: "ok".into(),
        sha256: sha256_text(&format!("{:?}", db_path)),
        record_count: synced as i64,
        source_path: db_path.to_string_lossy().into(),
        meta: serde_json::json!({"sessions": total}),
    };
    sink.write_receipt(&receipt).await?;

    info!("sync complete: {} sessions written", synced);
    Ok(())
}

async fn cmd_watch(
    db_path: &PathBuf,
    dsn: &str,
    enable_embed: bool,
    interval_secs: u64,
) -> Result<()> {
    let state_path = dirs::cache_dir()
        .unwrap_or_else(|| PathBuf::from("/tmp"))
        .join("ene-session-sync/state.json");
    if let Some(parent) = state_path.parent() {
        let _ = std::fs::create_dir_all(parent);
    }

    let mut last_synced: i64 = std::fs::read_to_string(&state_path)
        .ok()
        .and_then(|s| s.trim().parse().ok())
        .unwrap_or(0);

    info!("watch mode starting, last_synced={}", last_synced);

    loop {
        if let Err(e) = cmd_sync(db_path, dsn, enable_embed, Some(last_synced)).await {
            warn!("sync iteration failed: {}", e);
        }

        let source = source::OpenCodeSource::open(db_path)?;
        if let Ok(Some(max)) = source.max_session_updated() {
            last_synced = max;
            let _ = std::fs::write(&state_path, last_synced.to_string());
        }

        tokio::time::sleep(Duration::from_secs(interval_secs)).await;
    }
}

async fn cmd_search(dsn: &str, query: &str, limit: i64, semantic: bool) -> Result<()> {
    let sink = sink::RdsSink::connect(dsn).await?;

    if semantic {
        let embedder = embed::Embedder::from_env();
        if !embedder.health_check().await.unwrap_or(false) {
            anyhow::bail!("Ollama not available for semantic search");
        }
        let vec = embedder.embed(query).await?;
        let results = sink.search_similar(&vec, limit).await?;
        println!("{}", serde_json::to_string_pretty(&results)?);
    } else {
        let results = sink.search_keyword(query, limit).await?;
        println!("{}", serde_json::to_string_pretty(&results)?);
    }
    Ok(())
}

fn cmd_bridge_test(infra_dir: &PathBuf, module: &str) -> Result<()> {
    let bridge = bridge::PythonBridge::new(infra_dir.clone());
    let req = serde_json::json!({"op": "ping"});
    match bridge.call(module, &req) {
        Ok(resp) => {
            println!("Bridge OK:\n{}", serde_json::to_string_pretty(&resp)?);
            Ok(())
        }
        Err(e) => {
            eprintln!("Bridge test failed: {}", e);
            std::process::exit(1);
        }
    }
}

async fn cmd_list(dsn: &str, limit: i64) -> Result<()> {
    let sink = sink::RdsSink::connect(dsn).await?;
    let sessions = sink.list_sessions(limit).await?;
    println!("{}", serde_json::to_string_pretty(&sessions)?);
    Ok(())
}

async fn cmd_get(dsn: &str, session_id: &str) -> Result<()> {
    let sink = sink::RdsSink::connect(dsn).await?;
    match sink.get_session(session_id).await? {
        Some(v) => println!("{}", serde_json::to_string_pretty(&v)?),
        None => {
            eprintln!("Session not found: {}", session_id);
            std::process::exit(1);
        }
    }
    Ok(())
}

async fn cmd_claw_sync(sessions_dir: &PathBuf, dsn: &str, enable_embed: bool) -> Result<()> {
    info!("loading Claw sessions from {:?}", sessions_dir);
    let claw = source::ClawSource::new(sessions_dir);
    let pairs = claw.load_all()?;

    if pairs.is_empty() {
        info!("no Claw sessions found (all may be LFS stubs)");
        return Ok(());
    }

    info!("connecting to RDS");
    let sink = sink::RdsSink::connect(dsn).await?;

    let embedder = if enable_embed {
        let e = embed::Embedder::from_env();
        if !e.health_check().await.unwrap_or(false) {
            warn!("Ollama not reachable — embeddings disabled");
            None
        } else {
            info!("Ollama embedding enabled");
            Some(e)
        }
    } else {
        None
    };

    let total = pairs.len();
    let mut synced = 0;
    for (i, (mut session, mut messages)) in pairs.into_iter().enumerate() {
        info!(
            "[{}/{}] syncing Claw session {}",
            i + 1,
            total,
            session.session_id
        );

        if let Some(ref emb) = embedder {
            let text = format!(
                "{} {}",
                session.session_id,
                session.workspace_root.as_deref().unwrap_or("")
            );
            if let Ok(v) = emb.embed(&text).await {
                session.embedding = Some(v);
            }
            for cm in &mut messages {
                if !cm.text_content.is_empty() {
                    if let Ok(v) = emb.embed(&cm.text_content).await {
                        cm.embedding = Some(v);
                    }
                }
            }
        }

        sink.delete_messages_for_session(&session.session_id)
            .await?;
        sink.upsert_session(&session).await?;
        sink.upsert_messages(&session.session_id, &messages).await?;
        synced += 1;
    }

    let receipt = models::IngestionReceipt {
        shim_name: "ene-session-sync/claw".into(),
        status: "ok".into(),
        sha256: sha256_text(&sessions_dir.to_string_lossy()),
        record_count: synced as i64,
        source_path: sessions_dir.to_string_lossy().into(),
        meta: serde_json::json!({"sessions": total, "source": "claw"}),
    };
    sink.write_receipt(&receipt).await?;
    info!("Claw sync complete: {} sessions written", synced);
    Ok(())
}

async fn cmd_init_schema(dsn: &str) -> Result<()> {
    let _sink = sink::RdsSink::connect(dsn).await?; // schema init happens in connect()
    println!(
        "RDS schema initialized (ene.chat_sessions, ene.chat_messages, ene.ingestion_receipts)"
    );
    Ok(())
}
