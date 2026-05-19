use axum::{
    extract::{Path, Query, State},
    response::Json,
    routing::get,
    Router,
};
use ene_rds_chat::ChatLogSurface;
use ene_rds_core::RdsClient;
use ene_rds_ephemeral::EphemeralSurface;
use ene_rds_wiki::WikiSurface;
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::Mutex;

struct AppState {
    chat: ChatLogSurface,
    wiki: WikiSurface,
    ephemeral: EphemeralSurface,
}

#[derive(Deserialize)]
struct SearchQuery {
    q: String,
    #[serde(default = "default_limit")]
    limit: i64,
    #[serde(default)]
    semantic: bool,
}

fn default_limit() -> i64 { 10 }

#[derive(Serialize)]
struct HealthResponse {
    ok: bool,
    services: Vec<String>,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .init();

    let dsn = ene_rds_core::RdsClient::dsn_from_env();
    let client = RdsClient::connect(&dsn).await?;
    client.init_schema().await?;

    let chat = ChatLogSurface::new(client);
    chat.init_tables().await?;

    let wiki_client = RdsClient::connect(&dsn).await?;
    let wiki = WikiSurface::new(wiki_client);
    wiki.init_tables().await?;

    let ephemeral_client = RdsClient::connect(&dsn).await?;
    let ephemeral = EphemeralSurface::new(ephemeral_client);
    ephemeral.init_tables().await?;

    let state = Arc::new(Mutex::new(AppState { chat, wiki, ephemeral }));

    let app = Router::new()
        .route("/health", get(health_handler))
        .route("/sessions", get(list_sessions))
        .route("/sessions/:id", get(get_session))
        .route("/search", get(search_handler))
        .route("/wiki/search", get(wiki_search))
        .route("/wiki/:slug", get(get_wiki_page))
        .route("/ephemeral/nodes", get(list_ephemeral_nodes))
        .route("/ephemeral/nodes/:id", get(get_ephemeral_node))
        .with_state(state);

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await?;
    tracing::info!("ENE API listening on http://0.0.0.0:3000");
    axum::serve(listener, app).await?;
    Ok(())
}

async fn health_handler(State(_state): State<Arc<Mutex<AppState>>>) -> Json<HealthResponse> {
    Json(HealthResponse {
        ok: true,
        services: vec!["chat".into(), "wiki".into(), "ephemeral".into()],
    })
}

async fn list_sessions(
    State(state): State<Arc<Mutex<AppState>>>,
    Query(params): Query<HashMap<String, String>>,
) -> Result<Json<serde_json::Value>, String> {
    let limit = params.get("limit").and_then(|s| s.parse().ok()).unwrap_or(10i64);
    let guard = state.lock().await;
    match guard.chat.list_sessions(limit).await {
        Ok(v) => Ok(Json(json!({"ok": true, "data": v}))),
        Err(e) => Err(e.to_string()),
    }
}

async fn get_session(
    State(state): State<Arc<Mutex<AppState>>>,
    Path(id): Path<String>,
) -> Result<Json<serde_json::Value>, String> {
    let guard = state.lock().await;
    match guard.chat.get_session(&id).await {
        Ok(Some(v)) => Ok(Json(json!({"ok": true, "data": v}))),
        Ok(None) => Ok(Json(json!({"ok": false, "error": "not found"}))),
        Err(e) => Err(e.to_string()),
    }
}

async fn search_handler(
    State(state): State<Arc<Mutex<AppState>>>,
    Query(q): Query<SearchQuery>,
) -> Result<Json<serde_json::Value>, String> {
    let guard = state.lock().await;
    if q.semantic {
        Err("semantic search requires embedding provider — not yet wired".into())
    } else {
        match guard.chat.search_keyword(&q.q, q.limit).await {
            Ok(v) => Ok(Json(json!({"ok": true, "data": v}))),
            Err(e) => Err(e.to_string()),
        }
    }
}

async fn wiki_search(
    State(state): State<Arc<Mutex<AppState>>>,
    Query(params): Query<HashMap<String, String>>,
) -> Result<Json<serde_json::Value>, String> {
    let query = params.get("q").cloned().unwrap_or_default();
    let limit = params.get("limit").and_then(|s| s.parse().ok()).unwrap_or(10i64);
    let guard = state.lock().await;
    match guard.wiki.search(&query, limit).await {
        Ok(v) => Ok(Json(json!({"ok": true, "data": v}))),
        Err(e) => Err(e.to_string()),
    }
}

async fn get_wiki_page(
    State(state): State<Arc<Mutex<AppState>>>,
    Path(slug): Path<String>,
) -> Result<Json<serde_json::Value>, String> {
    let guard = state.lock().await;
    match guard.wiki.get_page(&slug).await {
        Ok(Some(v)) => Ok(Json(json!({"ok": true, "data": v}))),
        Ok(None) => Ok(Json(json!({"ok": false, "error": "not found"}))),
        Err(e) => Err(e.to_string()),
    }
}

async fn list_ephemeral_nodes(
    State(state): State<Arc<Mutex<AppState>>>,
    Query(params): Query<HashMap<String, String>>,
) -> Result<Json<serde_json::Value>, String> {
    let zone = params.get("zone").cloned().unwrap_or_else(|| "cold".into());
    let limit = params.get("limit").and_then(|s| s.parse().ok()).unwrap_or(100i64);
    let guard = state.lock().await;
    match guard.ephemeral.list_nodes_by_zone(&zone, limit).await {
        Ok(v) => Ok(Json(json!({"ok": true, "data": v}))),
        Err(e) => Err(e.to_string()),
    }
}

async fn get_ephemeral_node(
    State(state): State<Arc<Mutex<AppState>>>,
    Path(id): Path<String>,
) -> Result<Json<serde_json::Value>, String> {
    let guard = state.lock().await;
    match guard.ephemeral.get_node(&id).await {
        Ok(Some(v)) => Ok(Json(json!({"ok": true, "data": v}))),
        Ok(None) => Ok(Json(json!({"ok": false, "error": "not found"}))),
        Err(e) => Err(e.to_string()),
    }
}
