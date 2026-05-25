//! Receipt (audit log) emission for DAG executions.
//!
//! Every completed node writes a JSON line to `~/.cache/authentik-dag-receipts.jsonl`.
//! The receipt schema is intentionally simple and machine-readable.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::io::Write;
use std::path::PathBuf;


#[derive(Debug, Serialize, Deserialize)]
pub struct NodeReceipt {
    pub ts: u64,
    pub dag_id: String,
    pub node_id: String,
    pub op: String,
    pub success: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub outputs: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub extracted: Option<HashMap<String, serde_json::Value>>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DagReceipt {
    pub ts: u64,
    pub dag_id: String,
    pub success: bool,
    pub nodes_completed: usize,
    pub nodes_failed: usize,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
}

fn receipt_path() -> PathBuf {
    dirs::cache_dir()
        .unwrap_or_else(|| std::env::temp_dir())
        .join("authentik-dag-receipts.jsonl")
}

pub fn emit_node(r: &NodeReceipt) {
    let path = receipt_path();
    if let Some(parent) = path.parent() {
        let _ = std::fs::create_dir_all(parent);
    }
    let mut file = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(&path)
        .unwrap_or_else(|_| panic!("cannot open receipt file {:?}", path));
    let line = serde_json::to_string(r).expect("serialize receipt");
    writeln!(file, "{}", line).expect("write receipt");
}

pub fn emit_dag(r: &DagReceipt) {
    let path = receipt_path();
    if let Some(parent) = path.parent() {
        let _ = std::fs::create_dir_all(parent);
    }
    let mut file = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(&path)
        .unwrap_or_else(|_| panic!("cannot open receipt file {:?}", path));
    let line = serde_json::to_string(r).expect("serialize receipt");
    writeln!(file, "{}", line).expect("write receipt");
}
