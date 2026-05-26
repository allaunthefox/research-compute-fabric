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
use std::net::SocketAddr;
use std::sync::Arc;
use tokio::sync::Mutex;

struct AppState {
    dsn: String,
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

fn default_limit() -> i64 {
    10
}

fn error_json(context: &str, error: impl std::fmt::Display) -> Json<serde_json::Value> {
    Json(json!({
        "ok": false,
        "error": context,
        "detail": format!("{:#}", error),
    }))
}

fn should_reconnect(error: &anyhow::Error) -> bool {
    let detail = format!("{:#}", error);
    detail.contains("connection closed")
        || detail.contains("closed connection")
        || detail.contains("connection was closed")
}

async fn connect_state(dsn: &str) -> anyhow::Result<AppState> {
    let client = RdsClient::connect(dsn).await?;
    client.init_schema().await?;

    let chat = ChatLogSurface::new(client);
    chat.init_tables().await?;

    let wiki_client = RdsClient::connect(dsn).await?;
    let wiki = WikiSurface::new(wiki_client);
    wiki.init_tables().await?;

    let ephemeral_client = RdsClient::connect(dsn).await?;
    let ephemeral = EphemeralSurface::new(ephemeral_client);
    ephemeral.init_tables().await?;

    Ok(AppState {
        dsn: dsn.to_string(),
        chat,
        wiki,
        ephemeral,
    })
}

async fn refresh_state(state: &Arc<Mutex<AppState>>) -> anyhow::Result<()> {
    let dsn = {
        let guard = state.lock().await;
        guard.dsn.clone()
    };
    let next = connect_state(&dsn).await?;
    let mut guard = state.lock().await;
    *guard = next;
    Ok(())
}

async fn maybe_refresh_state(
    state: &Arc<Mutex<AppState>>,
    context: &str,
    error: &anyhow::Error,
) -> Option<Json<serde_json::Value>> {
    if !should_reconnect(error) {
        return Some(error_json(context, error));
    }
    tracing::warn!("refreshing ENE RDS clients after stale connection: {context}");
    if let Err(refresh_error) = refresh_state(state).await {
        return Some(Json(json!({
            "ok": false,
            "error": context,
            "detail": format!("{:#}", error),
            "refresh_error": format!("{:#}", refresh_error),
        })));
    }
    None
}

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
    let state = Arc::new(Mutex::new(connect_state(&dsn).await?));

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

    let bind_addr: SocketAddr = std::env::var("ENE_API_BIND")
        .unwrap_or_else(|_| "0.0.0.0:3000".into())
        .parse()?;
    let listener = tokio::net::TcpListener::bind(bind_addr).await?;
    tracing::info!("ENE API listening on http://{bind_addr}");
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
) -> Json<serde_json::Value> {
    let limit = params
        .get("limit")
        .and_then(|s| s.parse().ok())
        .unwrap_or(10i64);
    let guard = state.lock().await;
    match guard.chat.list_sessions(limit).await {
        Ok(v) => Json(json!({"ok": true, "data": v})),
        Err(e) => {
            drop(guard);
            if let Some(response) = maybe_refresh_state(&state, "list sessions", &e).await {
                return response;
            }
            let guard = state.lock().await;
            match guard.chat.list_sessions(limit).await {
                Ok(v) => Json(json!({"ok": true, "data": v})),
                Err(e) => error_json("list sessions", e),
            }
        }
    }
}

async fn get_session(
    State(state): State<Arc<Mutex<AppState>>>,
    Path(id): Path<String>,
) -> Json<serde_json::Value> {
    let guard = state.lock().await;
    match guard.chat.get_session(&id).await {
        Ok(Some(v)) => Json(json!({"ok": true, "data": v})),
        Ok(None) => Json(json!({"ok": false, "error": "not found"})),
        Err(e) => {
            drop(guard);
            if let Some(response) = maybe_refresh_state(&state, "get session", &e).await {
                return response;
            }
            let guard = state.lock().await;
            match guard.chat.get_session(&id).await {
                Ok(Some(v)) => Json(json!({"ok": true, "data": v})),
                Ok(None) => Json(json!({"ok": false, "error": "not found"})),
                Err(e) => error_json("get session", e),
            }
        }
    }
}

async fn search_handler(
    State(state): State<Arc<Mutex<AppState>>>,
    Query(q): Query<SearchQuery>,
) -> Json<serde_json::Value> {
    let guard = state.lock().await;
    if q.semantic {
        Json(json!({
            "ok": false,
            "error": "semantic search requires embedding provider - not yet wired"
        }))
    } else {
        match guard.chat.search_keyword(&q.q, q.limit).await {
            Ok(v) => Json(json!({"ok": true, "data": v})),
            Err(e) => {
                drop(guard);
                if let Some(response) = maybe_refresh_state(&state, "keyword search", &e).await {
                    return response;
                }
                let guard = state.lock().await;
                match guard.chat.search_keyword(&q.q, q.limit).await {
                    Ok(v) => Json(json!({"ok": true, "data": v})),
                    Err(e) => error_json("keyword search", e),
                }
            }
        }
    }
}

async fn wiki_search(
    State(state): State<Arc<Mutex<AppState>>>,
    Query(params): Query<HashMap<String, String>>,
) -> Json<serde_json::Value> {
    let query = params.get("q").cloned().unwrap_or_default();
    let limit = params
        .get("limit")
        .and_then(|s| s.parse().ok())
        .unwrap_or(10i64);
    let guard = state.lock().await;
    match guard.wiki.search(&query, limit).await {
        Ok(v) => Json(json!({"ok": true, "data": v})),
        Err(e) => {
            drop(guard);
            if let Some(response) = maybe_refresh_state(&state, "search wiki", &e).await {
                return response;
            }
            let guard = state.lock().await;
            match guard.wiki.search(&query, limit).await {
                Ok(v) => Json(json!({"ok": true, "data": v})),
                Err(e) => error_json("search wiki", e),
            }
        }
    }
}

async fn get_wiki_page(
    State(state): State<Arc<Mutex<AppState>>>,
    Path(slug): Path<String>,
) -> Json<serde_json::Value> {
    let guard = state.lock().await;
    match guard.wiki.get_page(&slug).await {
        Ok(Some(v)) => Json(json!({"ok": true, "data": v})),
        Ok(None) => Json(json!({"ok": false, "error": "not found"})),
        Err(e) => {
            drop(guard);
            if let Some(response) = maybe_refresh_state(&state, "get wiki page", &e).await {
                return response;
            }
            let guard = state.lock().await;
            match guard.wiki.get_page(&slug).await {
                Ok(Some(v)) => Json(json!({"ok": true, "data": v})),
                Ok(None) => Json(json!({"ok": false, "error": "not found"})),
                Err(e) => error_json("get wiki page", e),
            }
        }
    }
}

async fn list_ephemeral_nodes(
    State(state): State<Arc<Mutex<AppState>>>,
    Query(params): Query<HashMap<String, String>>,
) -> Json<serde_json::Value> {
    let zone = params.get("zone").cloned().unwrap_or_else(|| "cold".into());
    let limit = params
        .get("limit")
        .and_then(|s| s.parse().ok())
        .unwrap_or(100i64);
    let guard = state.lock().await;
    match guard.ephemeral.list_nodes_by_zone(&zone, limit).await {
        Ok(v) => Json(json!({"ok": true, "data": v})),
        Err(e) => {
            drop(guard);
            if let Some(response) = maybe_refresh_state(&state, "list ephemeral nodes", &e).await {
                return response;
            }
            let guard = state.lock().await;
            match guard.ephemeral.list_nodes_by_zone(&zone, limit).await {
                Ok(v) => Json(json!({"ok": true, "data": v})),
                Err(e) => error_json("list ephemeral nodes", e),
            }
        }
    }
}

async fn get_ephemeral_node(
    State(state): State<Arc<Mutex<AppState>>>,
    Path(id): Path<String>,
) -> Json<serde_json::Value> {
    let guard = state.lock().await;
    match guard.ephemeral.get_node(&id).await {
        Ok(Some(v)) => Json(json!({"ok": true, "data": v})),
        Ok(None) => Json(json!({"ok": false, "error": "not found"})),
        Err(e) => {
            drop(guard);
            if let Some(response) = maybe_refresh_state(&state, "get ephemeral node", &e).await {
                return response;
            }
            let guard = state.lock().await;
            match guard.ephemeral.get_node(&id).await {
                Ok(Some(v)) => Json(json!({"ok": true, "data": v})),
                Ok(None) => Json(json!({"ok": false, "error": "not found"})),
                Err(e) => error_json("get ephemeral node", e),
            }
        }
    }
}
