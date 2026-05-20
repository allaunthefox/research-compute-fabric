//! Swarm Probing
//!
//! Replaces: direct_swarm_probe.py

use crate::{EneResult, NodeId, Q16_16Timestamp};
use serde::{Deserialize, Serialize};
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SwarmProbe {
    pub probe_id: String,
    pub nodes: Vec<NodeId>,
}

impl SwarmProbe {
    pub fn new() -> Self {
        Self {
            probe_id: format!("swarm_{}", uuid::Uuid::new_v4()),
            nodes: Vec::new(),
        }
    }

    pub fn execute(&self) -> EneResult<SwarmReceipt> {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_micros() as Q16_16Timestamp;

        Ok(SwarmReceipt {
            probe_id: self.probe_id.clone(),
            node_count: self.nodes.len(),
            consensus_reached: self.nodes.len() >= 3,
            timestamp: now,
        })
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SwarmReceipt {
    pub probe_id: String,
    pub node_count: usize,
    pub consensus_reached: bool,
    pub timestamp: Q16_16Timestamp,
}
