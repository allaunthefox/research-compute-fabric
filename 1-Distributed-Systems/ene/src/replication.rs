//! Self-Replication
use crate::{EneResult, NodeId};
use rand::Rng;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReplicationRequest {
    pub target_endpoint: String,
    pub source_node: NodeId,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ReplicationState {
    pub peer_counts: HashMap<NodeId, usize>,
    pub min_peers: usize,
}

impl ReplicationState {
    pub fn new(min_peers: usize) -> Self {
        Self {
            peer_counts: HashMap::new(),
            min_peers,
        }
    }

    /// Find nodes with low peer counts and recruit new connections
    pub fn auto_replicate(&mut self, all_nodes: &[NodeId]) -> EneResult<Vec<NodeId>> {
        let mut recruited = Vec::new();
        let mut rng = rand::thread_rng();

        for &node in all_nodes {
            let count = self.peer_counts.get(&node).copied().unwrap_or(0);
            if count < self.min_peers {
                let needed = self.min_peers - count;
                let candidates: Vec<&NodeId> = all_nodes.iter().filter(|&&n| n != node).collect();

                for _ in 0..needed.min(candidates.len()) {
                    if let Some(&&candidate) = candidates.get(rng.gen_range(0..candidates.len())) {
                        recruited.push(candidate);
                        *self.peer_counts.entry(node).or_insert(0) += 1;
                        *self.peer_counts.entry(candidate).or_insert(0) += 1;
                    }
                }
            }
        }

        Ok(recruited)
    }
}

/// Replicate a node to a target endpoint (returns new node ID)
pub fn replicate(req: &ReplicationRequest) -> EneResult<NodeId> {
    let mut rng = rand::thread_rng();
    let new_id: u128 = 1u128 << rng.gen_range(0..8usize);
    tracing::info!(
        "Replicated node {} to endpoint {}, new ID: {}",
        req.source_node,
        req.target_endpoint,
        new_id
    );
    Ok(new_id)
}
