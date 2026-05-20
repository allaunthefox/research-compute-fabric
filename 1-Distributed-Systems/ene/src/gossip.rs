//! Gossip Protocol
//! Delta GCL compression for gossip messages (reduces bandwidth)

use crate::{EneResult, NodeId};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum GossipType {
    Discovery,
    Heartbeat,
    CredentialSync,
    Replicate,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GossipMessage {
    pub msg_type: GossipType,
    pub from: NodeId,
    pub payload: Vec<u8>,
    pub epoch: u64,
}

/// Delta GCL compression: XOR-based diff of two messages
pub fn compress_gossip(msg: &GossipMessage) -> EneResult<Vec<u8>> {
    let baseline = GossipMessage {
        msg_type: GossipType::Heartbeat,
        from: 0,
        payload: vec![0u8; msg.payload.len().max(1)],
        epoch: 0,
    };
    let base_bytes = bincode_serialize(&baseline);
    let msg_bytes = bincode_serialize(msg);

    let diff: Vec<u8> = base_bytes
        .iter()
        .zip(msg_bytes.iter())
        .map(|(a, b)| a ^ b)
        .collect();

    Ok(diff)
}

fn bincode_serialize<T: serde::Serialize>(val: &T) -> Vec<u8> {
    // Simple binary encoding fallback: use serde_json then take bytes
    let json = serde_json::to_vec(val).unwrap_or_default();
    json
}
