//! ENE Distributed Node Adapter
//!
//! Replaces: ene_distributed_node_adapter.py

use crate::{ProbeReceipt, WaveprobeError, WaveprobeResult};
use ene_distributed_node::node::{EneNode, ProbeConfig};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ENEDistributedNodeAdapter {
    pub probe_id: String,
    pub node: EneNode,
}

impl ENEDistributedNodeAdapter {
    pub fn new(initial_peers: usize) -> Self {
        Self {
            probe_id: format!(
                "wave_{}",
                Uuid::new_v4().to_string().replace("-", "")[..12].to_string()
            ),
            node: EneNode::new(initial_peers),
        }
    }

    pub fn execute_probe(&mut self, config: ProbeConfig) -> WaveprobeResult<ProbeReceipt> {
        let receipt = self
            .node
            .execute_probe(config)
            .map_err(|e| WaveprobeError::Adapter(format!("ENE probe failed: {}", e)))?;

        Ok(ProbeReceipt {
            probe_id: self.probe_id.clone(),
            adapter_type: "ene_distributed_node".to_string(),
            timestamp: receipt.timestamp,
            metrics: serde_json::to_value(&receipt.metrics)?,
            receipt_hash: receipt.receipt_hash,
        })
    }
}
