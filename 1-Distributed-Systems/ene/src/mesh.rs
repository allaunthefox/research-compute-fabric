//! Mesh Topology
use crate::{EneResult, NodeId};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MeshTopology {
    pub nodes: Vec<NodeId>,
    pub adjacency: Vec<(NodeId, NodeId)>,
}

/// Track heartbeat misses per node for self-healing
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct HeartbeatTracker {
    pub missed: HashMap<NodeId, usize>,
    pub max_misses: usize,
}

impl HeartbeatTracker {
    pub fn new(max_misses: usize) -> Self {
        Self {
            missed: HashMap::new(),
            max_misses,
        }
    }

    /// Record a missed heartbeat for a peer
    pub fn record_miss(&mut self, node: NodeId) {
        *self.missed.entry(node).or_insert(0) += 1;
    }

    /// Record a successful heartbeat (reset miss count)
    pub fn record_beat(&mut self, node: NodeId) {
        self.missed.remove(&node);
    }

    /// Return nodes that have exceeded the max miss threshold
    pub fn stale_nodes(&self) -> Vec<NodeId> {
        self.missed
            .iter()
            .filter(|(_, &count)| count >= self.max_misses)
            .map(|(&node, _)| node)
            .collect()
    }
}

/// Self-healing: remove peers that have missed 3+ heartbeats
pub fn heal_topology(mesh: &mut MeshTopology) -> EneResult<()> {
    let mut tracker = HeartbeatTracker::new(3);
    for &(a, b) in &mesh.adjacency {
        tracker.record_miss(a);
        tracker.record_miss(b);
    }
    let stale = tracker.stale_nodes();
    if stale.is_empty() {
        return Ok(());
    }
    mesh.nodes.retain(|n| !stale.contains(n));
    mesh.adjacency
        .retain(|(a, b)| !stale.contains(a) && !stale.contains(b));
    tracing::info!("Healed topology: removed {} stale nodes", stale.len());
    Ok(())
}
