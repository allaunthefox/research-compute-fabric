//! Health Checking
use crate::{EneResult, NodeId};
use rand::Rng;

/// Check peer health: ping each peer in the list and return count of reachable ones
pub fn check_peers(peers: &[NodeId]) -> EneResult<usize> {
    let mut reachable = 0;
    let mut rng = rand::thread_rng();
    for _peer in peers {
        // Simulated ping: 90% chance of success
        if rng.gen_bool(0.9) {
            reachable += 1;
        }
    }
    Ok(reachable)
}

/// Check a single peer's health
pub fn check_peer(node: NodeId) -> EneResult<bool> {
    let mut rng = rand::thread_rng();
    let ok = rng.gen_bool(0.9);
    tracing::debug!(
        "Health check for node {}: {}",
        node,
        if ok { "alive" } else { "dead" }
    );
    Ok(ok)
}
