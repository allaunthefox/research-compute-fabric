//! ENE Distributed Node — Rust Rewrite
//!
//! Replaces legacy Python: ene_distributed_node.py, debug_credentials.py,
//! direct_swarm_probe.py, ingest_keys_to_ene.py, migrate_credentials.py,
//! propagate_ssh_keys.py
//!
//! Per AGENTS.md: Lean is the source of truth. Rust is an extraction target
//! for operational I/O components. Python shims are deprecated in favour of Rust,
//! but neither Rust nor Python may contain logic, invariant checks, or decisions.

pub mod config;
pub mod credentials;
pub mod gossip;
pub mod health;
pub mod mesh;
pub mod node;
pub mod replication;
pub mod swarm;

use thiserror::Error;

/// Top-level ENE error type
#[derive(Error, Debug)]
pub enum EneError {
    #[error("Credential error: {0}")]
    Credential(String),
    #[error("Mesh error: {0}")]
    Mesh(String),
    #[error("Replication error: {0}")]
    Replication(String),
    #[error("Gossip error: {0}")]
    Gossip(String),
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),
}

pub type EneResult<T> = Result<T, EneError>;

/// Node identifier using Sidon labels (powers of 2 for 8 strands)
pub type NodeId = u128;

/// Q16_16 fixed-point timestamp for cross-substrate determinism
pub type Q16_16Timestamp = u64;

/// Receipt hash for validation
pub type ReceiptHash = [u8; 32];

// Mesh consensus is delegated to the `mesh` module (self-healing topology),
// `gossip` module (delta GCL gossip diffusion), and `replication` module
// (auto-replication). Full Byzantine consensus (Raft/Paxos-style) is not
// yet implemented — `mesh::heal_topology` provides the minimum viable mesh
// maintenance for current deployment scale.
