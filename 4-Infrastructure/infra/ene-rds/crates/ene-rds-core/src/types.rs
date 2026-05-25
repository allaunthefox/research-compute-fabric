use serde::{Deserialize, Serialize};

/// Generic API request envelope matching the Python handle_request protocol.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApiRequest {
    pub op: String,
    #[serde(flatten)]
    pub extra: serde_json::Map<String, serde_json::Value>,
}

/// Generic API response envelope.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApiResponse {
    pub ok: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub data: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
}

impl ApiResponse {
    pub fn success(data: serde_json::Value) -> Self {
        Self { ok: true, data: Some(data), error: None }
    }
    pub fn fail(msg: impl Into<String>) -> Self {
        Self { ok: false, data: None, error: Some(msg.into()) }
    }
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
