use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

/// Raw session row from opencode.db.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OpenCodeSession {
    pub id: String,
    pub project_id: String,
    pub parent_id: Option<String>,
    pub slug: String,
    pub directory: String,
    pub title: String,
    pub version: String,
    pub share_url: Option<String>,
    pub summary_additions: Option<i64>,
    pub summary_deletions: Option<i64>,
    pub summary_files: Option<i64>,
    pub summary_diffs: Option<String>,
    pub revert: Option<String>,
    pub permission: Option<String>,
    pub time_created: i64,
    pub time_updated: i64,
    pub time_compacting: Option<i64>,
    pub time_archived: Option<i64>,
    pub workspace_id: Option<String>,
    pub path: Option<String>,
    pub agent: Option<String>,
    pub model: Option<String>,
    pub cost: f64,
    pub tokens_input: i64,
    pub tokens_output: i64,
    pub tokens_reasoning: i64,
    pub tokens_cache_read: i64,
    pub tokens_cache_write: i64,
}

/// Raw message row from opencode.db.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OpenCodeMessage {
    pub id: String,
    pub session_id: String,
    pub time_created: i64,
    pub time_updated: i64,
    pub data: MessageData,
}

/// The JSON blob inside message.data.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MessageData {
    pub role: String,
    #[serde(default)]
    pub time: Option<MessageTime>,
    #[serde(default)]
    pub tokens: Option<MessageTokens>,
    #[serde(default)]
    pub cost: Option<f64>,
    #[serde(default)]
    pub model_id: Option<String>,
    #[serde(default)]
    pub provider_id: Option<String>,
    #[serde(default)]
    pub agent: Option<String>,
    #[serde(default)]
    pub mode: Option<String>,
    #[serde(default)]
    pub path: Option<String>,
    #[serde(default)]
    pub finish: Option<String>,
    #[serde(default)]
    pub summary: Option<MessageSummary>,
    #[serde(default)]
    pub parent_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MessageTime {
    pub created: Option<i64>,
    pub completed: Option<i64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MessageTokens {
    pub input: Option<i64>,
    pub output: Option<i64>,
    pub reasoning: Option<i64>,
    pub cache: Option<MessageCache>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MessageCache {
    pub creation: Option<i64>,
    pub read: Option<i64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MessageSummary {
    #[serde(default)]
    pub diffs: Option<Vec<String>>,
}

/// Raw part row from opencode.db.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OpenCodePart {
    pub id: String,
    pub message_id: String,
    pub session_id: String,
    pub time_created: i64,
    pub time_updated: i64,
    pub data: PartData,
}

/// The JSON blob inside part.data.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PartData {
    pub r#type: String,
    #[serde(default)]
    pub text: Option<String>,
    #[serde(default)]
    pub tool: Option<String>,
    #[serde(default)]
    pub call_id: Option<String>,
    #[serde(default, rename = "callID")]
    pub call_id_alt: Option<String>,
    #[serde(default)]
    pub state: Option<String>,
    #[serde(default)]
    pub input: Option<serde_json::Value>,
    #[serde(default)]
    pub output: Option<serde_json::Value>,
    #[serde(default)]
    pub is_error: Option<bool>,
}

impl PartData {
    pub fn call_id(&self) -> Option<String> {
        self.call_id.clone().or_else(|| self.call_id_alt.clone())
    }
}

/// Raw session_message row from opencode.db.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OpenCodeSessionMessage {
    pub id: String,
    pub session_id: String,
    pub r#type: String,
    pub time_created: i64,
    pub time_updated: i64,
    pub data: serde_json::Value,
}

/// Normalized chat session ready for RDS.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatSession {
    pub session_id: String,
    pub workspace_fingerprint: Option<String>,
    pub workspace_root: Option<String>,
    pub fork_parent_session_id: Option<String>,
    pub compaction_count: i32,
    pub compaction_summary: Option<String>,
    pub message_count: i32,
    pub token_input_total: i64,
    pub token_output_total: i64,
    pub created_at_ms: i64,
    pub updated_at_ms: i64,
    pub first_message_at_ms: Option<i64>,
    pub last_message_at_ms: Option<i64>,
    pub meta: serde_json::Value,
    pub embedding: Option<Vec<f32>>,
    pub receipt: Option<String>,
}

/// Normalized chat message ready for RDS.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatMessage {
    pub session_id: String,
    pub message_index: i32,
    pub role: String,
    pub blocks: Vec<MessageBlock>,
    pub text_content: String,
    pub token_input: i64,
    pub token_output: i64,
    pub token_cache_creation: i64,
    pub token_cache_read: i64,
    pub tool_calls: Vec<ToolCall>,
    pub embedding: Option<Vec<f32>>,
    pub receipt_hash: Option<String>,
    pub created_at_ms: i64,
}

/// A content block within a message (text, reasoning, tool-use, tool-result).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MessageBlock {
    pub block_type: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub text: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tool_name: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tool_input: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tool_output: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub is_error: Option<bool>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolCall {
    pub call_id: String,
    pub tool_name: String,
    pub input: serde_json::Value,
}

/// Bridge request to a Python surface.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BridgeRequest {
    pub module: String,
    pub operation: String,
    #[serde(default)]
    pub payload: serde_json::Value,
}

/// Bridge response from a Python surface.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BridgeResponse {
    pub ok: bool,
    #[serde(default)]
    pub data: serde_json::Value,
    #[serde(default)]
    pub error: Option<String>,
}

/// Ollama embedding request.
#[derive(Debug, Clone, Serialize)]
pub struct OllamaEmbedRequest {
    pub model: String,
    pub prompt: String,
}

/// Ollama embedding response.
#[derive(Debug, Clone, Deserialize)]
pub struct OllamaEmbedResponse {
    pub embedding: Vec<f32>,
}

/// Ingestion receipt written to ene.ingestion_receipts.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IngestionReceipt {
    pub shim_name: String,
    pub status: String,
    pub sha256: String,
    pub record_count: i64,
    pub source_path: String,
    pub meta: serde_json::Value,
}
