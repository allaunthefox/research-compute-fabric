//! Waveprobe Adapters — Rust Rewrite
//!
//! Replaces legacy Python adapters:
//! - ene_distributed_node_adapter.py
//! - otom_v4_adapter.py
//! - quantum_manifold_geometry_adapter.py
//! - resonance_adapter.py
//! - wsm_wr_egs_wc_adapter.py

pub mod ene_adapter;
pub mod otom_adapter;

use thiserror::Error;

#[derive(Error, Debug)]
pub enum WaveprobeError {
    #[error("Adapter error: {0}")]
    Adapter(String),
    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),
}

pub type WaveprobeResult<T> = Result<T, WaveprobeError>;

/// Probe execution receipt
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ProbeReceipt {
    pub probe_id: String,
    pub adapter_type: String,
    pub timestamp: u64,
    pub metrics: serde_json::Value,
    pub receipt_hash: [u8; 32],
}
