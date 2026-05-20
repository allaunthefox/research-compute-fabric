//! ENE Node Core
//!
//! Replaces: ene_distributed_node.py

use crate::{EneResult, NodeId, Q16_16Timestamp, ReceiptHash};
use rand::Rng;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use uuid::Uuid;

/// Canonical Sidon set for 8-strand braid labeling
const SIDON_SET: [u128; 8] = [1, 2, 4, 8, 16, 32, 64, 128];

/// ENE Node state
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EneNode {
    pub node_id: NodeId,
    pub probe_id: String,
    pub created_at: Q16_16Timestamp,
    pub peers: Vec<PeerInfo>,
    pub credentials: CredentialVault,
    pub mesh_state: MeshState,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PeerInfo {
    pub node_id: NodeId,
    pub endpoint: String,
    pub last_heartbeat: Q16_16Timestamp,
    pub gossip_version: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CredentialVault {
    pub encrypted_cache: Vec<u8>,
    pub rotation_epoch: u64,
    pub consensus_threshold: f64, // Q0_64 encoded as f64 at boundary
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MeshState {
    pub time_steps: usize,
    pub dt: f64, // Q16_16 encoded at boundary
    pub gossip_interval: f64,
    pub failure_rate: f64,
    pub convergence_reached: bool,
}

impl EneNode {
    pub fn new(initial_peers: usize) -> Self {
        Self {
            node_id: generate_sidon_label(),
            probe_id: format!("ene_{}", Uuid::new_v4()),
            created_at: 0, // Q16_16: initialized at runtime
            peers: Vec::with_capacity(initial_peers),
            credentials: CredentialVault {
                encrypted_cache: Vec::new(),
                rotation_epoch: 0,
                consensus_threshold: 0.67,
            },
            mesh_state: MeshState {
                time_steps: 100,
                dt: 0.1,
                gossip_interval: 1.0,
                failure_rate: 0.0,
                convergence_reached: false,
            },
        }
    }

    /// Execute probe and return metrics receipt
    pub fn execute_probe(&mut self, config: ProbeConfig) -> EneResult<ProbeReceipt> {
        let history = self.simulate_mesh(&config)?;
        let metrics = self.extract_metrics(&history, &config)?;
        let convergence = self.validate_convergence(&metrics)?;

        let canonical = serde_json::to_string(&ProbeReceipt {
            probe_id: self.probe_id.clone(),
            node_id: self.node_id,
            timestamp: self.created_at,
            metrics: metrics.clone(),
            convergence: convergence.clone(),
            receipt_hash: [0u8; 32],
        })?;
        let hash = Sha256::digest(canonical.as_bytes());

        Ok(ProbeReceipt {
            probe_id: self.probe_id.clone(),
            node_id: self.node_id,
            timestamp: self.created_at,
            metrics,
            convergence,
            receipt_hash: hash.into(),
        })
    }

    fn simulate_mesh(&self, config: &ProbeConfig) -> EneResult<MeshHistory> {
        let time_steps = config.time_steps;
        let dt = config.dt;
        let initial_peers = config.initial_peers;
        let gossip_interval = config.gossip_interval;
        let failure_rate = config.failure_rate;

        let mut peer_counts = Vec::with_capacity(time_steps);
        let mut gossip_counts = Vec::with_capacity(time_steps);
        let mut credential_rotations = Vec::new();

        let max_peers = (initial_peers as f64 * 2.0) as usize;
        let mut current_peers = initial_peers;
        let mut gossip_accum = 0.0;
        let mut rng = rand::thread_rng();

        for step in 0..time_steps {
            // Q16_16 fixed-point: encode rates as Q16_16 and scale
            let _qdt = (dt * 65536.0) as u64;
            let _qfailure = (failure_rate * 65536.0) as u64;

            // Randomly disconnect peers based on failure_rate
            let qdisconnect = ((failure_rate * dt) * 65536.0) as u64;
            let disconnects = ((qdisconnect * current_peers as u64) / 65536) as usize;
            current_peers = current_peers.saturating_sub(disconnects);

            // Randomly reconnect new peers
            let reconnect_prob = (1.0 - failure_rate) * dt * 0.5;
            let qreconnect = (reconnect_prob * 65536.0) as u64;
            let reconnects = ((qreconnect * max_peers as u64) / 65536) as usize;
            current_peers = (current_peers + reconnects).min(max_peers);

            peer_counts.push(current_peers);

            // Gossip events at gossip_interval boundaries
            gossip_accum += dt;
            if gossip_accum >= gossip_interval {
                gossip_accum -= gossip_interval;
                let gossip_count = if current_peers > 0 {
                    rng.gen_range(1..=current_peers)
                } else {
                    0
                };
                gossip_counts.push(gossip_count);
            }

            // Periodic credential rotation
            if step > 0 && step % 25 == 0 {
                credential_rotations.push(step as u64);
            }
        }

        Ok(MeshHistory {
            peer_counts,
            gossip_counts,
            credential_rotations,
        })
    }

    fn extract_metrics(
        &self,
        history: &MeshHistory,
        config: &ProbeConfig,
    ) -> EneResult<MeshMetrics> {
        let total_peers: usize = history.peer_counts.iter().sum();
        let avg_peers = if !history.peer_counts.is_empty() {
            total_peers as f64 / history.peer_counts.len() as f64
        } else {
            0.0
        };

        let dt = config.dt;
        let convergence_time = if history.peer_counts.len() > 1 {
            let max_idx = history
                .peer_counts
                .iter()
                .enumerate()
                .max_by(|a, b| a.1.cmp(b.1))
                .map(|(i, _)| i)
                .unwrap_or(0);
            max_idx as f64 * dt
        } else {
            0.0
        };

        let credential_sync_latency = if history.credential_rotations.is_empty() {
            dt * history.peer_counts.len() as f64
        } else {
            let first = history.credential_rotations[0];
            first as f64 * dt
        };

        let total_gossip: usize = history.gossip_counts.iter().sum();
        let replication_rate = if history.peer_counts.is_empty() {
            0.0
        } else {
            total_gossip as f64 / history.peer_counts.len() as f64
        };

        Ok(MeshMetrics {
            avg_peers,
            convergence_time,
            credential_sync_latency,
            replication_rate,
        })
    }

    fn validate_convergence(&self, metrics: &MeshMetrics) -> EneResult<ConvergenceStatus> {
        let threshold = self.credentials.consensus_threshold;
        let failure_rate_derived = if metrics.avg_peers > 0.0 {
            metrics.avg_peers.recip()
        } else {
            1.0
        };
        let converged = failure_rate_derived < threshold;
        let iterations = self.mesh_state.time_steps;
        let residual = (failure_rate_derived - threshold).abs();

        Ok(ConvergenceStatus {
            converged,
            iterations,
            residual,
        })
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProbeConfig {
    pub time_steps: usize,
    pub dt: f64,
    pub initial_peers: usize,
    pub gossip_interval: f64,
    pub failure_rate: f64,
    pub consensus_threshold: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProbeReceipt {
    pub probe_id: String,
    pub node_id: NodeId,
    pub timestamp: Q16_16Timestamp,
    pub metrics: MeshMetrics,
    pub convergence: ConvergenceStatus,
    pub receipt_hash: ReceiptHash,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MeshHistory {
    pub peer_counts: Vec<usize>,
    pub gossip_counts: Vec<usize>,
    pub credential_rotations: Vec<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MeshMetrics {
    pub avg_peers: f64,
    pub convergence_time: f64,
    pub credential_sync_latency: f64,
    pub replication_rate: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConvergenceStatus {
    pub converged: bool,
    pub iterations: usize,
    pub residual: f64,
}

/// Generate canonical Sidon label (power of 2 for 8-strand braid)
fn generate_sidon_label() -> NodeId {
    let strand = rand::thread_rng().gen_range(0..8usize);
    SIDON_SET[strand]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_node_creation() {
        let node = EneNode::new(3);
        assert!(node.probe_id.starts_with("ene_"));
    }

    #[test]
    fn test_sidon_label() {
        let label = generate_sidon_label();
        // Must be a power of 2
        assert!(label.count_ones() == 1);
    }
}
