#![allow(dead_code)]

//! Credential provider and minimal HTTP credential server.
//!
//! Ports `credential_provider.py` and `credential_server.py`.
//!
//! # Loading order
//! 1. Remote credential server (`CREDENTIAL_SERVER_URL` env var, skipped if localhost)
//! 2. Config JSON file (`~/.config/ene/credentials.json` or `CREDENTIAL_CONFIG_PATH`)
//! 3. Environment variables (fallback)
//!
//! # HTTP server
//! `run_credential_server(bind)` opens a raw `tokio::net::TcpListener`, speaks a
//! minimal HTTP/1.1 subset (request-line + headers only), and serves JSON
//! responses over the credentials loaded at startup.  No external HTTP framework
//! is required.

use serde::{Deserialize, Serialize};
use std::path::Path;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tracing::{debug, info, warn};

// ─── Provider → env-var manifest ─────────────────────────────────────────────

/// Static mapping from provider name to the environment variable that holds its
/// API key / secret.  Ordered so that the most commonly used providers appear
/// first for fast linear scans.
const PROVIDER_ENV_MAP: &[(&str, &str)] = &[
    ("deepseek", "DEEPSEEK_API_KEY"),
    ("quandela", "QUANDELA_API_KEY"),
    ("wolfram_alpha", "WOLFRAM_ALPHA_APPID"),
    ("notion", "NOTION_API_KEY"),
    ("linear", "LINEAR_API_KEY"),
    ("gemini", "GEMINI_API_KEY"),
    ("ollama", "OLLAMA_API_KEY"),
    ("brave_search", "BRAVE_API_KEY"),
    ("neural_endeavor", "ENE_ENCRYPTION_KEY"),
    ("bedrock", "AWS_BEARER_TOKEN_BEDROCK"),
    ("venice", "VENICE_API_KEY"),
];

// ─── Core data type ───────────────────────────────────────────────────────────

/// A resolved credential for a single provider.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Credential {
    /// Canonical provider identifier, e.g. `"deepseek"`.
    pub provider: String,
    /// The name of the key within the provider's namespace, e.g. `"api_key"`.
    pub key_name: String,
    /// The resolved secret value.
    pub value: String,
    /// Arbitrary provider-specific metadata (source, expiry, …).
    pub metadata: serde_json::Value,
}

// ─── Remote response shapes ───────────────────────────────────────────────────

/// `/credentials` list response item.
#[derive(Debug, Deserialize)]
struct RemoteCredentialEntry {
    name: String,
}

/// `/credentials/{name}` detail response.
#[derive(Debug, Deserialize)]
struct RemoteCredentialDetail {
    #[serde(default)]
    provider: Option<String>,
    #[serde(default)]
    key_name: Option<String>,
    value: String,
    #[serde(default)]
    metadata: Option<serde_json::Value>,
}

// ─── Loading functions ────────────────────────────────────────────────────────

/// Scan `PROVIDER_ENV_MAP` and return a `Credential` for each env var that is
/// currently set and non-empty.
pub fn load_from_env() -> Vec<Credential> {
    let mut out = Vec::new();
    for &(provider, env_var) in PROVIDER_ENV_MAP {
        match std::env::var(env_var) {
            Ok(val) if !val.is_empty() => {
                debug!("credential from env: provider={} var={}", provider, env_var);
                out.push(Credential {
                    provider: provider.to_string(),
                    key_name: env_var.to_string(),
                    value: val,
                    metadata: serde_json::json!({ "source": "env", "env_var": env_var }),
                });
            }
            _ => {}
        }
    }
    info!("load_from_env: {} credentials found", out.len());
    out
}

/// Read a JSON file at `path` with shape `{ "<provider>": "<key>" }` and
/// return a `Credential` per entry.  Missing / unreadable files return an empty
/// `Vec` rather than propagating an error, to keep startup non-fatal.
pub fn load_from_config(path: &Path) -> Vec<Credential> {
    let raw = match std::fs::read_to_string(path) {
        Ok(s) => s,
        Err(e) => {
            debug!("load_from_config: cannot read {:?}: {}", path, e);
            return Vec::new();
        }
    };
    let map: serde_json::Value = match serde_json::from_str(&raw) {
        Ok(v) => v,
        Err(e) => {
            warn!("load_from_config: invalid JSON in {:?}: {}", path, e);
            return Vec::new();
        }
    };
    let obj = match map.as_object() {
        Some(o) => o,
        None => {
            warn!("load_from_config: top-level JSON is not an object");
            return Vec::new();
        }
    };

    let mut out = Vec::new();
    for (provider, value_v) in obj {
        if let Some(value) = value_v.as_str() {
            if !value.is_empty() {
                out.push(Credential {
                    provider: provider.clone(),
                    key_name: "api_key".to_string(),
                    value: value.to_string(),
                    metadata: serde_json::json!({
                        "source": "config",
                        "config_path": path.to_string_lossy()
                    }),
                });
            }
        }
    }
    info!(
        "load_from_config: {} credentials from {:?}",
        out.len(),
        path
    );
    out
}

/// Fetch credentials from a remote credential server.
///
/// 1. `GET {server_url}/credentials` → `[{"name": "<n>"}, …]`
/// 2. For each name: `GET {server_url}/credentials/{name}` → detail
///
/// Returns an empty `Vec` on any network / parse error.  Skipped entirely when
/// `server_url` resolves to localhost (127.0.0.1 / ::1 / `localhost`).
pub async fn load_from_remote(server_url: &str) -> Vec<Credential> {
    // Security guard: never attempt to reach a localhost credential server —
    // this avoids SSRF-style self-loops when the binary is run inside the
    // credential server's own process tree.
    let lower = server_url.to_lowercase();
    if lower.contains("localhost")
        || lower.contains("127.0.0.1")
        || lower.contains("::1")
    {
        debug!("load_from_remote: skipping localhost URL {}", server_url);
        return Vec::new();
    }

    let client = match reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(5))
        .build()
    {
        Ok(c) => c,
        Err(e) => {
            warn!("load_from_remote: could not build HTTP client: {}", e);
            return Vec::new();
        }
    };

    // Step 1 — list available credential names.
    let list_url = format!("{}/credentials", server_url.trim_end_matches('/'));
    let entries: Vec<RemoteCredentialEntry> = match client.get(&list_url).send().await {
        Ok(resp) => match resp.json().await {
            Ok(v) => v,
            Err(e) => {
                warn!("load_from_remote: could not parse /credentials response: {}", e);
                return Vec::new();
            }
        },
        Err(e) => {
            warn!("load_from_remote: GET {} failed: {}", list_url, e);
            return Vec::new();
        }
    };

    // Step 2 — fetch each credential detail.
    let mut out = Vec::new();
    for entry in entries {
        let detail_url = format!(
            "{}/credentials/{}",
            server_url.trim_end_matches('/'),
            entry.name
        );
        match client.get(&detail_url).send().await {
            Ok(resp) => match resp.json::<RemoteCredentialDetail>().await {
                Ok(detail) => {
                    out.push(Credential {
                        provider: detail
                            .provider
                            .unwrap_or_else(|| entry.name.clone()),
                        key_name: detail
                            .key_name
                            .unwrap_or_else(|| entry.name.clone()),
                        value: detail.value,
                        metadata: detail.metadata.unwrap_or_else(|| {
                            serde_json::json!({ "source": "remote", "server": server_url })
                        }),
                    });
                }
                Err(e) => warn!(
                    "load_from_remote: could not parse detail for {}: {}",
                    entry.name, e
                ),
            },
            Err(e) => warn!(
                "load_from_remote: GET {} failed: {}",
                detail_url, e
            ),
        }
    }

    info!(
        "load_from_remote: {} credentials from {}",
        out.len(),
        server_url
    );
    out
}

/// Return a default config file path: `~/.config/ene/credentials.json` (or the
/// value of `CREDENTIAL_CONFIG_PATH`).
fn default_config_path() -> std::path::PathBuf {
    if let Ok(p) = std::env::var("CREDENTIAL_CONFIG_PATH") {
        return std::path::PathBuf::from(p);
    }
    dirs::config_dir()
        .unwrap_or_else(|| std::path::PathBuf::from("/tmp"))
        .join("ene")
        .join("credentials.json")
}

/// Resolve credentials using the priority chain:
///
/// 1. Remote server (`CREDENTIAL_SERVER_URL`)
/// 2. Config file (`~/.config/ene/credentials.json`)
/// 3. Environment variables
///
/// Each layer is merged in order; earlier layers shadow later ones for the same
/// provider.
pub async fn load_credentials() -> Vec<Credential> {
    // 1. Remote
    if let Ok(url) = std::env::var("CREDENTIAL_SERVER_URL") {
        let remote = load_from_remote(&url).await;
        if !remote.is_empty() {
            return remote;
        }
    }

    // 2. Config file
    let config_path = default_config_path();
    let from_config = load_from_config(&config_path);
    if !from_config.is_empty() {
        return from_config;
    }

    // 3. Env fallback
    load_from_env()
}

// ─── Utility functions ────────────────────────────────────────────────────────

/// Build a JSON status summary for a loaded credential set.
///
/// ```json
/// { "ok": true, "count": 3, "available_providers": ["deepseek", "ollama", …] }
/// ```
pub fn credential_status(creds: &[Credential]) -> serde_json::Value {
    let providers: Vec<&str> = creds.iter().map(|c| c.provider.as_str()).collect();
    serde_json::json!({
        "ok": !creds.is_empty(),
        "count": creds.len(),
        "available_providers": providers,
    })
}

/// Return the first `Credential` whose `provider` matches `provider` (case-
/// insensitive), or `None` if no match is found.
pub fn resolve_credential<'a>(
    creds: &'a [Credential],
    provider: &str,
) -> Option<&'a Credential> {
    let needle = provider.to_lowercase();
    creds
        .iter()
        .find(|c| c.provider.to_lowercase() == needle)
}

// ─── Minimal HTTP credential server ──────────────────────────────────────────

/// Build and send an HTTP/1.1 response with `Content-Type: application/json`.
///
/// `status` is the numeric HTTP status code (e.g. `200`, `404`).
async fn write_json_response(
    stream: &mut tokio::net::TcpStream,
    status: u16,
    body: &[u8],
) {
    let reason = match status {
        200 => "OK",
        400 => "Bad Request",
        404 => "Not Found",
        500 => "Internal Server Error",
        _ => "Unknown",
    };
    let header = format!(
        "HTTP/1.1 {} {}\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n",
        status,
        reason,
        body.len()
    );
    if let Err(e) = stream.write_all(header.as_bytes()).await {
        warn!("credential server: write header error: {}", e);
        return;
    }
    if let Err(e) = stream.write_all(body).await {
        warn!("credential server: write body error: {}", e);
    }
}

/// Parse the first line of an HTTP request (`METHOD /path HTTP/1.x`) and return
/// `(method, path)`.  Returns `None` when the request-line cannot be parsed.
fn parse_request_line(raw: &str) -> Option<(String, String)> {
    let line = raw.lines().next()?;
    let mut parts = line.splitn(3, ' ');
    let method = parts.next()?.to_uppercase();
    let path = parts.next()?.to_string();
    Some((method, path))
}

/// Run a minimal credential HTTP server on `bind` (e.g. `"127.0.0.1:8765"`).
///
/// Routes:
/// - `GET /`                  → service info JSON
/// - `GET /health`            → `{"status":"ok"}`
/// - `GET /credentials`       → provider manifest (names only, no values)
/// - `GET /credentials/{name}`→ full credential JSON (or 404)
/// - `GET /status`            → `credential_status()` JSON
/// - everything else          → 404
///
/// Credentials are loaded once at startup via `load_credentials()` and shared
/// across all connections via an `Arc`.
pub async fn run_credential_server(bind: &str) -> anyhow::Result<()> {
    use std::sync::Arc;
    use tokio::net::TcpListener;

    let creds = Arc::new(load_credentials().await);
    info!(
        "credential server: loaded {} credentials",
        creds.len()
    );

    let listener = TcpListener::bind(bind)
        .await
        .map_err(|e| anyhow::anyhow!("bind {}: {}", bind, e))?;
    info!("credential server: listening on {}", bind);

    loop {
        let (mut stream, peer) = match listener.accept().await {
            Ok(pair) => pair,
            Err(e) => {
                warn!("credential server: accept error: {}", e);
                continue;
            }
        };
        debug!("credential server: connection from {}", peer);

        let creds_ref = Arc::clone(&creds);

        tokio::spawn(async move {
            // Read up to 4 KiB — enough for a well-formed HTTP request-line +
            // headers.  We do not need to parse a body for these GET-only routes.
            let mut buf = vec![0u8; 4096];
            let n = match stream.read(&mut buf).await {
                Ok(n) => n,
                Err(e) => {
                    warn!("credential server: read error from {}: {}", peer, e);
                    return;
                }
            };
            if n == 0 {
                return;
            }

            let raw = String::from_utf8_lossy(&buf[..n]);
            let (method, path) = match parse_request_line(&raw) {
                Some(p) => p,
                None => {
                    let body = br#"{"error":"bad request"}"#;
                    write_json_response(&mut stream, 400, body).await;
                    return;
                }
            };

            if method != "GET" {
                let body = br#"{"error":"method not allowed"}"#;
                write_json_response(&mut stream, 400, body).await;
                return;
            }

            // Normalise path: strip query string.
            let path_clean = path.splitn(2, '?').next().unwrap_or(&path);
            // Strip trailing slash for all paths except root.
            let path_norm = if path_clean != "/" {
                path_clean.trim_end_matches('/')
            } else {
                path_clean
            };

            match path_norm {
                "/" => {
                    let body = serde_json::to_vec(&serde_json::json!({
                        "service": "ene-credential-server",
                        "version": "0.1.0",
                        "routes": ["/health", "/credentials", "/credentials/{name}", "/status"],
                    }))
                    .unwrap_or_default();
                    write_json_response(&mut stream, 200, &body).await;
                }

                "/health" => {
                    write_json_response(&mut stream, 200, br#"{"status":"ok"}"#).await;
                }

                "/status" => {
                    let status = credential_status(&creds_ref);
                    let body = serde_json::to_vec(&status).unwrap_or_default();
                    write_json_response(&mut stream, 200, &body).await;
                }

                "/credentials" => {
                    // Return a safe manifest: provider names only, no secret values.
                    let manifest: Vec<serde_json::Value> = creds_ref
                        .iter()
                        .map(|c| serde_json::json!({ "name": c.provider, "key_name": c.key_name }))
                        .collect();
                    let body =
                        serde_json::to_vec(&serde_json::json!(manifest)).unwrap_or_default();
                    write_json_response(&mut stream, 200, &body).await;
                }

                p if p.starts_with("/credentials/") => {
                    // Extract provider name after the prefix.
                    let name = &p["/credentials/".len()..];
                    match resolve_credential(&creds_ref, name) {
                        Some(cred) => {
                            let body = serde_json::to_vec(cred).unwrap_or_default();
                            write_json_response(&mut stream, 200, &body).await;
                        }
                        None => {
                            let body = serde_json::to_vec(&serde_json::json!({
                                "error": "not found",
                                "provider": name,
                            }))
                            .unwrap_or_default();
                            write_json_response(&mut stream, 404, &body).await;
                        }
                    }
                }

                _ => {
                    let body = serde_json::to_vec(&serde_json::json!({
                        "error": "not found",
                        "path": path_norm,
                    }))
                    .unwrap_or_default();
                    write_json_response(&mut stream, 404, &body).await;
                }
            }
        });
    }
}
