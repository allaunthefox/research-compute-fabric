//! Model Context Protocol (MCP) server for Authentik.
//!
//! Wraps the existing Rust Authentik shim (`authentik_agent_manager` crate)
//! and exposes Authentik operations as MCP "tools" over JSON-RPC 2.0 on stdio.
//!
//! # Environment
//!
//! - `AUTHENTIK_TOKEN` — required. Authentik API bearer token.
//! - `AUTHENTIK_BASE_URL` — optional. Defaults to `https://researchstack.info`.
//!
//! # Run
//!
//! ```bash
//! export AUTHENTIK_TOKEN="..."
//! cargo run --bin mcp_server
//! ```
//!
//! # MCP protocol
//!
//! The server reads JSON-RPC requests from stdin and writes responses to stdout.
//! All tracing / debug output goes to stderr so stdout stays pure JSON-RPC.
//!
//! Supported methods:
//! - `initialize` — handshake, returns server info and capabilities.
//! - `tools/list` — returns available tools with JSON schemas.
//! - `tools/call` — executes a named tool with arguments.

use authentik_agent_manager::{authentik, dag, execute_dag};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use tokio::io::{AsyncBufReadExt, AsyncWriteExt};
use tracing::{debug, info};

// ─── JSON-RPC types ─────────────────────────────────────────────────────────

#[derive(Debug, Deserialize)]
struct JsonRpcRequest {
    jsonrpc: String,
    id: Option<u64>,
    method: String,
    #[serde(default)]
    params: Value,
}

#[derive(Debug, Serialize)]
struct JsonRpcResponse {
    jsonrpc: String,
    id: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    result: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<JsonRpcError>,
}

#[derive(Debug, Serialize)]
struct JsonRpcError {
    code: i32,
    message: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    data: Option<Value>,
}

impl JsonRpcResponse {
    fn success(id: Option<u64>, result: Value) -> Self {
        Self {
            jsonrpc: "2.0".to_string(),
            id,
            result: Some(result),
            error: None,
        }
    }

    fn error(id: Option<u64>, code: i32, message: String, data: Option<Value>) -> Self {
        Self {
            jsonrpc: "2.0".to_string(),
            id,
            result: None,
            error: Some(JsonRpcError {
                code,
                message,
                data,
            }),
        }
    }
}

// ─── MCP types ─────────────────────────────────────────────────────────────

#[derive(Debug, Serialize)]
struct InitializeResult {
    protocol_version: String,
    capabilities: Value,
    server_info: ServerInfo,
}

#[derive(Debug, Serialize)]
struct ServerInfo {
    name: String,
    version: String,
}

#[derive(Debug, Serialize)]
struct ToolsListResult {
    tools: Vec<Tool>,
}

#[derive(Debug, Serialize)]
struct Tool {
    name: String,
    description: String,
    input_schema: Value,
}

#[derive(Debug, Deserialize)]
struct ToolCallParams {
    name: String,
    #[serde(default)]
    arguments: Value,
}

#[derive(Debug, Serialize)]
struct ToolCallResult {
    content: Vec<ToolContent>,
    #[serde(skip_serializing_if = "Option::is_none")]
    is_error: Option<bool>,
}

#[derive(Debug, Serialize)]
struct ToolContent {
    #[serde(rename = "type")]
    ty: String,
    text: String,
}

// ─── Server state ───────────────────────────────────────────────────────────

struct Server {
    client: authentik::Client,
}

// ─── Main loop ─────────────────────────────────────────────────────────────

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Log to stderr only; stdout is reserved for JSON-RPC.
    tracing_subscriber::fmt()
        .with_writer(std::io::stderr)
        .init();

    let token = std::env::var("AUTHENTIK_TOKEN")
        .map_err(|_| anyhow::anyhow!("AUTHENTIK_TOKEN environment variable not set"))?;
    let base_url = std::env::var("AUTHENTIK_BASE_URL")
        .unwrap_or_else(|_| "https://researchstack.info".to_string());

    let client = authentik::Client::new(&base_url, &token);
    let server = Server { client };

    let stdin = tokio::io::stdin();
    let stdout = tokio::io::stdout();
    let mut reader = tokio::io::BufReader::new(stdin);
    let stdout = tokio::sync::Mutex::new(stdout);

    let mut line = String::new();
    loop {
        line.clear();
        let n = reader.read_line(&mut line).await?;
        if n == 0 {
            info!("stdin closed — shutting down");
            break;
        }
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }

        let req: JsonRpcRequest = match serde_json::from_str(trimmed) {
            Ok(r) => r,
            Err(e) => {
                write_response(
                    &stdout,
                    JsonRpcResponse::error(None, -32700, format!("parse error: {}", e), None),
                )
                .await?;
                continue;
            }
        };

        // Notifications (no id) don't get a response, except we still
        // process internal state changes if needed.
        let is_notification = req.id.is_none();

        let response = match handle_request(&server, req).await {
            Ok(Some(resp)) => Some(resp),
            Ok(None) => None,
            Err(e) => Some(JsonRpcResponse::error(
                None,
                -32603,
                format!("internal error: {}", e),
                None,
            )),
        };

        if let Some(resp) = response {
            if !is_notification {
                write_response(&stdout, resp).await?;
            }
        }
    }

    Ok(())
}

async fn write_response(
    stdout: &tokio::sync::Mutex<tokio::io::Stdout>,
    resp: JsonRpcResponse,
) -> anyhow::Result<()> {
    let mut guard = stdout.lock().await;
    let line = serde_json::to_string(&resp)?;
    guard.write_all(line.as_bytes()).await?;
    guard.write_all(b"\n").await?;
    guard.flush().await?;
    Ok(())
}

// ─── Request dispatch ────────────────────────────────────────────────────────

async fn handle_request(
    server: &Server,
    req: JsonRpcRequest,
) -> anyhow::Result<Option<JsonRpcResponse>> {
    if req.jsonrpc != "2.0" {
        return Ok(Some(JsonRpcResponse::error(
            req.id,
            -32600,
            "invalid request: jsonrpc must be '2.0'".to_string(),
            None,
        )));
    }

    match req.method.as_str() {
        "initialize" => Ok(Some(handle_initialize(req.id))),
        "initialized" => {
            // Notification; no response.
            debug!("received initialized notification");
            Ok(None)
        }
        "tools/list" => Ok(Some(handle_tools_list(req.id))),
        "tools/call" => Ok(Some(handle_tools_call(server, req.id, req.params).await)),
        _ => Ok(Some(JsonRpcResponse::error(
            req.id,
            -32601,
            format!("method not found: {}", req.method),
            None,
        ))),
    }
}

// ─── Method handlers ─────────────────────────────────────────────────────────

fn handle_initialize(id: Option<u64>) -> JsonRpcResponse {
    JsonRpcResponse::success(
        id,
        json!(InitializeResult {
            protocol_version: "2024-11-05".to_string(),
            capabilities: json!({}),
            server_info: ServerInfo {
                name: "authentik-mcp-server".to_string(),
                version: env!("CARGO_PKG_VERSION").to_string(),
            },
        }),
    )
}

fn handle_tools_list(id: Option<u64>) -> JsonRpcResponse {
    let tools = vec![
        Tool {
            name: "list_users".to_string(),
            description: "List all users in the Authentik directory.".to_string(),
            input_schema: json!({
                "type": "object",
                "properties": {},
                "required": []
            }),
        },
        Tool {
            name: "list_groups".to_string(),
            description: "List all groups in the Authentik directory.".to_string(),
            input_schema: json!({
                "type": "object",
                "properties": {},
                "required": []
            }),
        },
        Tool {
            name: "create_user".to_string(),
            description: "Create a new service-account user in Authentik.".to_string(),
            input_schema: json!({
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "Unique username (login name)"
                    },
                    "name": {
                        "type": "string",
                        "description": "Display name"
                    },
                    "email": {
                        "type": "string",
                        "description": "Email address (optional, defaults to username@researchstack.info)"
                    }
                },
                "required": ["username", "name"]
            }),
        },
        Tool {
            name: "create_application".to_string(),
            description: "Create a new application in Authentik.".to_string(),
            input_schema: json!({
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Human-readable application name"
                    },
                    "slug": {
                        "type": "string",
                        "description": "URL-safe identifier"
                    }
                },
                "required": ["name", "slug"]
            }),
        },
        Tool {
            name: "create_proxy_provider".to_string(),
            description: "Create a new proxy provider in Authentik.".to_string(),
            input_schema: json!({
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Provider name"
                    },
                    "authorization_flow": {
                        "type": "string",
                        "description": "UUID of the authorization flow to use"
                    },
                    "internal_host": {
                        "type": "string",
                        "description": "Internal upstream URL (e.g. http://service:8080)"
                    },
                    "external_host": {
                        "type": "string",
                        "description": "External host exposed to users (e.g. https://app.researchstack.info)"
                    }
                },
                "required": ["name", "authorization_flow", "internal_host", "external_host"]
            }),
        },
        Tool {
            name: "execute_dag".to_string(),
            description: "Execute a DAG plan (JSON object with nodes) against Authentik.".to_string(),
            input_schema: json!({
                "type": "object",
                "properties": {
                    "plan": {
                        "type": "object",
                        "description": "DAG plan object with a 'nodes' array"
                    }
                },
                "required": ["plan"]
            }),
        },
    ];

    JsonRpcResponse::success(id, json!(ToolsListResult { tools }))
}

async fn handle_tools_call(
    server: &Server,
    id: Option<u64>,
    params: Value,
) -> JsonRpcResponse {
    let call: ToolCallParams = match serde_json::from_value(params) {
        Ok(c) => c,
        Err(e) => {
            return JsonRpcResponse::error(
                id,
                -32602,
                format!("invalid params: {}", e),
                None,
            );
        }
    };

    let result = match call.name.as_str() {
        "list_users" => tool_list_users(&server.client).await,
        "list_groups" => tool_list_groups(&server.client).await,
        "create_user" => tool_create_user(&server.client, call.arguments).await,
        "create_application" => tool_create_application(&server.client, call.arguments).await,
        "create_proxy_provider" => {
            tool_create_proxy_provider(&server.client, call.arguments).await
        }
        "execute_dag" => tool_execute_dag(&server.client, call.arguments).await,
        other => Err(anyhow::anyhow!("unknown tool: {}", other)),
    };

    match result {
        Ok(content) => JsonRpcResponse::success(
            id,
            json!(ToolCallResult {
                content,
                is_error: Some(false),
            }),
        ),
        Err(e) => JsonRpcResponse::success(
            id,
            json!(ToolCallResult {
                content: vec![ToolContent {
                    ty: "text".to_string(),
                    text: format!("Error: {}", e),
                }],
                is_error: Some(true),
            }),
        ),
    }
}

// ─── Tool implementations ────────────────────────────────────────────────────

async fn tool_list_users(client: &authentik::Client) -> anyhow::Result<Vec<ToolContent>> {
    let resp = client.list_users().await?;
    let text = serde_json::to_string_pretty(&resp)?;
    Ok(vec![ToolContent {
        ty: "text".to_string(),
        text,
    }])
}

async fn tool_list_groups(client: &authentik::Client) -> anyhow::Result<Vec<ToolContent>> {
    let resp = client.list_groups().await?;
    let text = serde_json::to_string_pretty(&resp)?;
    Ok(vec![ToolContent {
        ty: "text".to_string(),
        text,
    }])
}

async fn tool_create_user(
    client: &authentik::Client,
    args: Value,
) -> anyhow::Result<Vec<ToolContent>> {
    let username = args["username"]
        .as_str()
        .ok_or_else(|| anyhow::anyhow!("missing required argument: username"))?;
    let name = args["name"]
        .as_str()
        .ok_or_else(|| anyhow::anyhow!("missing required argument: name"))?;
    let email = args.get("email").and_then(|v| v.as_str());

    let resp = client.create_user(username, name, email).await?;
    let text = serde_json::to_string_pretty(&resp)?;
    Ok(vec![ToolContent {
        ty: "text".to_string(),
        text,
    }])
}

async fn tool_create_application(
    client: &authentik::Client,
    args: Value,
) -> anyhow::Result<Vec<ToolContent>> {
    let name = args["name"]
        .as_str()
        .ok_or_else(|| anyhow::anyhow!("missing required argument: name"))?;
    let slug = args["slug"]
        .as_str()
        .ok_or_else(|| anyhow::anyhow!("missing required argument: slug"))?;

    let resp = client.create_application(name, slug).await?;
    let text = serde_json::to_string_pretty(&resp)?;
    Ok(vec![ToolContent {
        ty: "text".to_string(),
        text,
    }])
}

async fn tool_create_proxy_provider(
    client: &authentik::Client,
    args: Value,
) -> anyhow::Result<Vec<ToolContent>> {
    let name = args["name"]
        .as_str()
        .ok_or_else(|| anyhow::anyhow!("missing required argument: name"))?;
    let authorization_flow = args["authorization_flow"]
        .as_str()
        .ok_or_else(|| anyhow::anyhow!("missing required argument: authorization_flow"))?;
    let internal_host = args["internal_host"]
        .as_str()
        .ok_or_else(|| anyhow::anyhow!("missing required argument: internal_host"))?;
    let external_host = args["external_host"]
        .as_str()
        .ok_or_else(|| anyhow::anyhow!("missing required argument: external_host"))?;

    let resp = client
        .create_proxy_provider(name, authorization_flow, internal_host, external_host)
        .await?;
    let text = serde_json::to_string_pretty(&resp)?;
    Ok(vec![ToolContent {
        ty: "text".to_string(),
        text,
    }])
}

async fn tool_execute_dag(
    client: &authentik::Client,
    args: Value,
) -> anyhow::Result<Vec<ToolContent>> {
    let plan = args
        .get("plan")
        .cloned()
        .ok_or_else(|| anyhow::anyhow!("missing required argument: plan"))?;
    let dag: dag::Dag = serde_json::from_value(plan)
        .map_err(|e| anyhow::anyhow!("invalid DAG plan: {}", e))?;
    dag.validate()?;

    execute_dag(client, &dag).await?;

    Ok(vec![ToolContent {
        ty: "text".to_string(),
        text: "DAG executed successfully. Receipts written to ~/.cache/authentik-dag-receipts.jsonl".to_string(),
    }])
}
