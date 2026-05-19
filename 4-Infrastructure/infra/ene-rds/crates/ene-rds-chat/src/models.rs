use serde::{Deserialize, Serialize};

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
