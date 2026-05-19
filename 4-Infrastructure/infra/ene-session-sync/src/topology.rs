#![allow(dead_code)]
//! topology.rs — Topology node runtime, controller, and topological storage.
//!
//! Port of topology_node.py, topology_controller.py,
//! topological_storage_delta_gcl.py, and topological_engine_client.py.

use anyhow::{anyhow, Result};
use rusqlite::{params, Connection};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};
use tracing::{debug, info, warn};

// ═══════════════════════════════════════════════════════════════════════════
// §1  Q16.16 Fixed-Point
// ═══════════════════════════════════════════════════════════════════════════

/// Q16.16 fixed-point integer (u32 backing).
///
/// Integer part occupies the high 16 bits; fractional part the low 16 bits.
/// Arithmetic uses wrapping semantics so overflow is deterministic across all
/// substrates (AGENTS.md §Compression First Principles).
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub struct Q16_16(pub u32);

impl Q16_16 {
    /// Additive identity.
    pub const ZERO: Self = Q16_16(0);
    /// Multiplicative identity (1.0 in Q16.16).
    pub const ONE: Self = Q16_16(0x0001_0000);

    /// Construct from a natural number n (maps n → n.0 in Q16.16).
    pub fn from_nat(n: u32) -> Self {
        Q16_16(n.wrapping_mul(65536))
    }

    /// Construct from a rational num/denom (rounded toward zero).
    /// Returns ZERO when denom == 0.
    pub fn from_frac(num: u32, denom: u32) -> Self {
        if denom == 0 {
            Self::ZERO
        } else {
            Q16_16(num.wrapping_mul(65536) / denom)
        }
    }

    /// Lossless conversion to f64 (boundary-only, never used in compute paths).
    pub fn to_f64(self) -> f64 {
        (self.0 as f64) / 65536.0
    }

    /// Wrapping addition.
    pub fn wrapping_add(self, other: Self) -> Self {
        Q16_16(self.0.wrapping_add(other.0))
    }

    /// Wrapping subtraction.
    pub fn wrapping_sub(self, other: Self) -> Self {
        Q16_16(self.0.wrapping_sub(other.0))
    }

    /// Saturating addition — caps at u32::MAX rather than wrapping.
    pub fn saturating_add(self, other: Self) -> Self {
        Q16_16(self.0.saturating_add(other.0))
    }

    /// Returns true if self < other (unsigned comparison).
    pub fn is_less_than(self, other: Self) -> bool {
        self.0 < other.0
    }
}

impl std::fmt::Display for Q16_16 {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{:.4}", self.to_f64())
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// §2  Enums
// ═══════════════════════════════════════════════════════════════════════════

/// Role of a topology node in the research stack mesh.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub enum NodeRole {
    /// Build, verify, synthesize — architect node.
    Core,
    /// Arbitrate, attest, verify — BFT partner.
    Judge,
    /// Store, relay, backup — git mirror.
    Mirror,
    /// Filter, compress, route, attest — minimal resource.
    Edge,
    /// Experimental, unindexed.
    FoxTop,
}

impl NodeRole {
    pub fn as_str(self) -> &'static str {
        match self {
            NodeRole::Core => "core",
            NodeRole::Judge => "judge",
            NodeRole::Mirror => "mirror",
            NodeRole::Edge => "edge",
            NodeRole::FoxTop => "foxTop",
        }
    }
}

impl std::fmt::Display for NodeRole {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(self.as_str())
    }
}

/// State in the node lifecycle state machine.
///
/// Allowed transitions:
/// ```text
/// Boot → Selftest → Announce → Active → Degraded → Active
///                                      ↘ Failed  ↗
///                             ↘ Failed ↗
///            ↘ Failed ↗
/// Failed → Boot
/// ```
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub enum NodeStateEnum {
    Boot,
    Selftest,
    Announce,
    Active,
    Degraded,
    Failed,
}

impl NodeStateEnum {
    pub fn as_str(self) -> &'static str {
        match self {
            NodeStateEnum::Boot => "boot",
            NodeStateEnum::Selftest => "selftest",
            NodeStateEnum::Announce => "announce",
            NodeStateEnum::Active => "active",
            NodeStateEnum::Degraded => "degraded",
            NodeStateEnum::Failed => "failed",
        }
    }
}

impl std::fmt::Display for NodeStateEnum {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(self.as_str())
    }
}

/// Capability that a node can advertise and exercise.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub enum NodeCapability {
    LeanBuild,
    FpgaSynth,
    EquationForest,
    FullGit,
    BftArbitrate,
    MmrVerify,
    Attestation,
    GitMirror,
    ObjectStore,
    Relay,
    Backup,
    Compress,
    RgflowFilter,
    Route,
    Storage,
    Compute,
    Experimental,
}

impl NodeCapability {
    pub fn as_str(self) -> &'static str {
        match self {
            NodeCapability::LeanBuild => "leanBuild",
            NodeCapability::FpgaSynth => "fpgaSynth",
            NodeCapability::EquationForest => "equationForest",
            NodeCapability::FullGit => "fullGit",
            NodeCapability::BftArbitrate => "bftArbitrate",
            NodeCapability::MmrVerify => "mmrVerify",
            NodeCapability::Attestation => "attestation",
            NodeCapability::GitMirror => "gitMirror",
            NodeCapability::ObjectStore => "objectStore",
            NodeCapability::Relay => "relay",
            NodeCapability::Backup => "backup",
            NodeCapability::Compress => "compress",
            NodeCapability::RgflowFilter => "rgflowFilter",
            NodeCapability::Route => "route",
            NodeCapability::Storage => "storage",
            NodeCapability::Compute => "compute",
            NodeCapability::Experimental => "experimental",
        }
    }
}

/// Bind class — category of binding a node can accept.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub enum BindClass {
    Informational,
    Geometric,
    Thermodynamic,
    Physical,
    Control,
}

impl BindClass {
    pub fn as_str(self) -> &'static str {
        match self {
            BindClass::Informational => "informational",
            BindClass::Geometric => "geometric",
            BindClass::Thermodynamic => "thermodynamic",
            BindClass::Physical => "physical",
            BindClass::Control => "control",
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// §3  Capability cost table and role defaults
//     (extracted from Lean, mirrored verbatim from topology_node.py §2)
// ═══════════════════════════════════════════════════════════════════════════

/// Q16.16 energy cost of activating each capability.
///
/// Ported from `CAPABILITY_COST` in topology_node.py.
pub fn capability_cost(cap: NodeCapability) -> Q16_16 {
    match cap {
        NodeCapability::LeanBuild => Q16_16::from_nat(10),
        NodeCapability::FpgaSynth => Q16_16::from_nat(50),
        NodeCapability::EquationForest => Q16_16::from_nat(20),
        NodeCapability::FullGit => Q16_16::from_nat(5),
        NodeCapability::BftArbitrate => Q16_16::from_nat(3),
        NodeCapability::MmrVerify => Q16_16::from_nat(2),
        NodeCapability::Attestation => Q16_16::from_nat(2),
        NodeCapability::GitMirror => Q16_16::from_nat(2),
        NodeCapability::ObjectStore => Q16_16::from_nat(1),
        NodeCapability::Relay => Q16_16::from_nat(1),
        NodeCapability::Backup => Q16_16::from_nat(1),
        NodeCapability::Compress => Q16_16::from_nat(4),
        NodeCapability::RgflowFilter => Q16_16::from_nat(3),
        NodeCapability::Route => Q16_16::from_nat(1),
        NodeCapability::Storage => Q16_16::from_nat(1),
        NodeCapability::Compute => Q16_16::from_nat(2),
        NodeCapability::Experimental => Q16_16::from_nat(8),
    }
}

/// Default capability set for each role.
///
/// Ported from `DEFAULT_CAPABILITIES` in topology_node.py.
pub fn default_capabilities(role: NodeRole) -> Vec<NodeCapability> {
    match role {
        NodeRole::Core => vec![
            NodeCapability::LeanBuild,
            NodeCapability::FpgaSynth,
            NodeCapability::EquationForest,
            NodeCapability::FullGit,
            NodeCapability::Storage,
            NodeCapability::Compute,
        ],
        NodeRole::Judge => vec![
            NodeCapability::BftArbitrate,
            NodeCapability::MmrVerify,
            NodeCapability::Attestation,
            NodeCapability::Compute,
        ],
        NodeRole::Mirror => vec![
            NodeCapability::GitMirror,
            NodeCapability::ObjectStore,
            NodeCapability::Relay,
            NodeCapability::Backup,
            NodeCapability::Storage,
        ],
        NodeRole::Edge => vec![
            NodeCapability::Compress,
            NodeCapability::RgflowFilter,
            NodeCapability::Attestation,
            NodeCapability::Route,
            NodeCapability::Storage,
            NodeCapability::Compute,
        ],
        NodeRole::FoxTop => vec![
            NodeCapability::Experimental,
            NodeCapability::Compute,
            NodeCapability::Storage,
            NodeCapability::Route,
        ],
    }
}

/// Default bind-class set for each role.
///
/// Ported from `DEFAULT_BIND_CLASSES` in topology_node.py.
pub fn default_bind_classes(role: NodeRole) -> Vec<BindClass> {
    match role {
        NodeRole::Core => vec![
            BindClass::Informational,
            BindClass::Geometric,
            BindClass::Thermodynamic,
            BindClass::Physical,
            BindClass::Control,
        ],
        NodeRole::Judge => vec![BindClass::Informational, BindClass::Control],
        NodeRole::Mirror => vec![BindClass::Informational, BindClass::Geometric],
        NodeRole::Edge => vec![
            BindClass::Physical,
            BindClass::Thermodynamic,
            BindClass::Control,
        ],
        NodeRole::FoxTop => vec![
            BindClass::Informational,
            BindClass::Physical,
            BindClass::Control,
        ],
    }
}

/// Maximum energy budget (Q16.16) for each role.
///
/// Ported from `MAX_ENERGY` in topology_node.py.
pub fn max_energy(role: NodeRole) -> Q16_16 {
    match role {
        NodeRole::Core => Q16_16::from_nat(100),
        NodeRole::Judge => Q16_16::from_nat(50),
        NodeRole::Mirror => Q16_16::from_nat(50),
        NodeRole::Edge => Q16_16::from_nat(25),
        NodeRole::FoxTop => Q16_16::from_nat(40),
    }
}

/// Per-tick energy recovery rate (Q16.16) for each role.
///
/// Ported from `RECOVERY_RATE` in topology_node.py.
pub fn recovery_rate(role: NodeRole) -> Q16_16 {
    match role {
        NodeRole::Core => Q16_16::from_frac(1, 2),
        NodeRole::Judge => Q16_16::from_frac(1, 4),
        NodeRole::Mirror => Q16_16::from_frac(1, 4),
        NodeRole::Edge => Q16_16::from_frac(1, 8),
        NodeRole::FoxTop => Q16_16::from_frac(1, 4),
    }
}

/// Energy cost of a state transition (Q16.16).
///
/// Returns `None` if the transition is not defined (implying it is also not
/// allowed).  Ported from `STATE_TRANSITION_COST` in topology_node.py.
pub fn state_transition_cost(from: NodeStateEnum, to: NodeStateEnum) -> Option<Q16_16> {
    use NodeStateEnum::*;
    match (from, to) {
        (Boot, Selftest) => Some(Q16_16::from_nat(1)),
        (Selftest, Announce) => Some(Q16_16::from_nat(1)),
        (Announce, Active) => Some(Q16_16::from_nat(2)),
        (Active, Degraded) => Some(Q16_16::from_nat(1)),
        (Degraded, Active) => Some(Q16_16::from_nat(3)),
        (Active, Failed) => Some(Q16_16::ZERO),
        (Degraded, Failed) => Some(Q16_16::ZERO),
        (Failed, Boot) => Some(Q16_16::from_nat(5)),
        (Selftest, Failed) => Some(Q16_16::from_nat(1)),
        (Announce, Failed) => Some(Q16_16::from_nat(1)),
        _ => None,
    }
}

/// Returns `true` when the transition `from → to` is in the allowed set.
///
/// Ported from `ALLOWED_TRANSITIONS` in topology_node.py.
pub fn is_allowed_transition(from: NodeStateEnum, to: NodeStateEnum) -> bool {
    state_transition_cost(from, to).is_some()
}

// ═══════════════════════════════════════════════════════════════════════════
// §4  NodeConfig and NodeRuntime
// ═══════════════════════════════════════════════════════════════════════════

/// Static configuration for a topology node.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NodeConfig {
    /// Unique node identifier (e.g. "qfox-1").
    pub node_id: String,
    /// Role in the mesh.
    pub role: NodeRole,
    /// Memory budget in megabytes.
    pub memory_budget_mb: u32,
    /// Disk budget in gigabytes.
    pub disk_budget_gb: u32,
    /// Jurisdiction tag (e.g. "us-east-2").
    pub jurisdiction: String,
    /// Advertised capabilities.  Defaults to `default_capabilities(role)` when
    /// the `NodeRuntime` is constructed with an empty vec.
    pub capabilities: Vec<NodeCapability>,
    /// Bind classes the node will accept.  Defaults similarly.
    pub bind_classes: Vec<BindClass>,
    /// Tailscale IP address for direct mesh communication.
    pub tailscale_ip: String,
}

impl NodeConfig {
    /// Build a `NodeConfig` with role-derived capability and bind-class
    /// defaults, overriding only the specified fields.
    pub fn with_defaults(
        node_id: impl Into<String>,
        role: NodeRole,
        memory_budget_mb: u32,
        disk_budget_gb: u32,
        jurisdiction: impl Into<String>,
        tailscale_ip: impl Into<String>,
    ) -> Self {
        Self {
            node_id: node_id.into(),
            role,
            memory_budget_mb,
            disk_budget_gb,
            jurisdiction: jurisdiction.into(),
            capabilities: default_capabilities(role),
            bind_classes: default_bind_classes(role),
            tailscale_ip: tailscale_ip.into(),
        }
    }
}

/// Live runtime state of a topology node.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NodeRuntime {
    /// Immutable configuration.
    pub config: NodeConfig,
    /// Current state-machine position.
    pub state: NodeStateEnum,
    /// Current energy budget in Q16.16.
    pub energy: Q16_16,
    /// Monotonically increasing tick counter.
    pub step: u64,
    /// Wall-clock timestamp of the last heartbeat (ms since UNIX epoch).
    pub last_heartbeat_ms: i64,
    /// Known peer node IDs.
    pub peer_ids: Vec<String>,
}

impl NodeRuntime {
    /// Construct a new runtime in the `Boot` state with full initial energy.
    ///
    /// If `config.capabilities` or `config.bind_classes` are empty they are
    /// filled from the role defaults before the runtime is created.
    pub fn new(mut config: NodeConfig) -> Self {
        if config.capabilities.is_empty() {
            config.capabilities = default_capabilities(config.role);
        }
        if config.bind_classes.is_empty() {
            config.bind_classes = default_bind_classes(config.role);
        }
        let energy = max_energy(config.role);
        Self {
            config,
            state: NodeStateEnum::Boot,
            energy,
            step: 0,
            last_heartbeat_ms: now_ms(),
            peer_ids: Vec::new(),
        }
    }

    /// Attempt a state-machine transition.
    ///
    /// Validates the edge against `ALLOWED_TRANSITIONS`, deducts the
    /// transition energy cost, and fails with an error if either the
    /// transition is illegal or there is insufficient energy.
    pub fn transition(&mut self, next: NodeStateEnum) -> Result<()> {
        if !is_allowed_transition(self.state, next) {
            return Err(anyhow!(
                "illegal transition {} → {} for node {}",
                self.state,
                next,
                self.config.node_id
            ));
        }
        // SAFETY: is_allowed_transition guarantees the pair exists.
        let cost = state_transition_cost(self.state, next).unwrap_or(Q16_16::ZERO);
        if cost.0 > self.energy.0 {
            return Err(anyhow!(
                "insufficient energy for {} → {}: need {} have {}",
                self.state,
                next,
                cost,
                self.energy
            ));
        }
        let old = self.state;
        self.energy = self.energy.wrapping_sub(cost);
        self.state = next;
        info!(
            node = %self.config.node_id,
            from = %old,
            to = %next,
            energy = %self.energy,
            "state transition"
        );
        Ok(())
    }

    /// Advance one simulation tick.
    ///
    /// Increments `step`, applies the role's `RECOVERY_RATE` to `energy`
    /// (capped at `MAX_ENERGY`), and updates `last_heartbeat_ms`.
    pub fn tick(&mut self) {
        self.step = self.step.wrapping_add(1);
        let rate = recovery_rate(self.config.role);
        let cap = max_energy(self.config.role);
        let new_energy = self.energy.saturating_add(rate);
        self.energy = if new_energy.0 > cap.0 { cap } else { new_energy };
        self.last_heartbeat_ms = now_ms();
        debug!(
            node = %self.config.node_id,
            step = self.step,
            energy = %self.energy,
            "tick"
        );
    }

    /// Build a JSON heartbeat/announce payload for this node.
    ///
    /// The payload mirrors `TopologyNodeState.to_dict()` from topology_node.py.
    pub fn heartbeat_json(&self) -> serde_json::Value {
        serde_json::json!({
            "node_id": self.config.node_id,
            "role": self.config.role.as_str(),
            "state": self.state.as_str(),
            "capabilities": self.config.capabilities.iter()
                .map(|c| c.as_str())
                .collect::<Vec<_>>(),
            "bind_classes": self.config.bind_classes.iter()
                .map(|b| b.as_str())
                .collect::<Vec<_>>(),
            "energy": {
                "val": self.energy.0,
                "float": self.energy.to_f64()
            },
            "memory_budget_mb": self.config.memory_budget_mb,
            "disk_budget_gb": self.config.disk_budget_gb,
            "jurisdiction": self.config.jurisdiction,
            "tailscale_ip": self.config.tailscale_ip,
            "step": self.step,
            "last_heartbeat_ms": self.last_heartbeat_ms,
            "peer_ids": self.peer_ids,
        })
    }

    /// Returns true when the node is in the `Active` state.
    pub fn is_active(&self) -> bool {
        self.state == NodeStateEnum::Active
    }

    /// Returns the total Q16.16 cost of all advertised capabilities.
    pub fn total_capability_cost(&self) -> Q16_16 {
        self.config
            .capabilities
            .iter()
            .fold(Q16_16::ZERO, |acc, &cap| {
                acc.saturating_add(capability_cost(cap))
            })
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// §5  TopologicalManifest
// ═══════════════════════════════════════════════════════════════════════════

/// A topological manifest: a versioned, content-addressed record emitted by
/// topology nodes.  Ported from `TopologicalManifest` in both
/// topological_storage_delta_gcl.py and topological_engine_client.py.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TopologicalManifest {
    /// Globally unique manifest identifier (typically a UUID or
    /// `node_id::kind::timestamp` composite).
    pub manifest_id: String,
    /// Node that emitted this manifest.
    pub node_id: String,
    /// Manifest kind / topology type (e.g. "announce", "manifold", "resource").
    pub kind: String,
    /// Arbitrary JSON payload — the manifest body.
    pub payload: serde_json::Value,
    /// Creation timestamp (ms since UNIX epoch).
    pub created_at_ms: i64,
    /// SHA-256 hex digest of the canonical JSON serialisation of `payload`.
    pub content_hash: String,
    /// Optional compression statistics (original_size, compressed_size, …).
    pub compression_stats: Option<serde_json::Value>,
}

impl TopologicalManifest {
    /// Compute the SHA-256 content hash of a JSON payload.
    ///
    /// The payload is canonically serialised (compact, no trailing newline)
    /// before hashing.
    pub fn compute_hash(payload: &serde_json::Value) -> String {
        let canonical = serde_json::to_string(payload)
            .unwrap_or_else(|_| "null".to_string());
        let mut hasher = Sha256::new();
        hasher.update(canonical.as_bytes());
        format!("{:x}", hasher.finalize())
    }

    /// Build a new manifest, computing the `content_hash` automatically.
    pub fn build(
        manifest_id: impl Into<String>,
        node_id: impl Into<String>,
        kind: impl Into<String>,
        payload: serde_json::Value,
    ) -> Self {
        let hash = Self::compute_hash(&payload);
        Self {
            manifest_id: manifest_id.into(),
            node_id: node_id.into(),
            kind: kind.into(),
            payload,
            created_at_ms: now_ms(),
            content_hash: hash,
            compression_stats: None,
        }
    }

    /// Attach compression statistics to the manifest (mutating).
    pub fn with_compression_stats(mut self, stats: serde_json::Value) -> Self {
        self.compression_stats = Some(stats);
        self
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// §6  TopologicalStorage (SQLite-backed)
// ═══════════════════════════════════════════════════════════════════════════

/// SQLite-backed store for `TopologicalManifest` records.
///
/// Ported from `TopologicalStorageDeltaGCL` in
/// topological_storage_delta_gcl.py, adapted to rusqlite.
pub struct TopologicalStorage {
    db_path: PathBuf,
}

impl TopologicalStorage {
    /// Open (or create) a storage database at `db_path`.
    pub fn new(db_path: impl AsRef<Path>) -> Result<Self> {
        let s = Self {
            db_path: db_path.as_ref().to_path_buf(),
        };
        s.init_tables()?;
        Ok(s)
    }

    /// Open a short-lived connection to the SQLite database.
    fn conn(&self) -> Result<Connection> {
        Ok(Connection::open(&self.db_path)?)
    }

    /// Create the `topology_manifests` table if it does not exist.
    fn init_tables(&self) -> Result<()> {
        let conn = self.conn()?;
        conn.execute_batch(
            "CREATE TABLE IF NOT EXISTS topology_manifests (
                manifest_id      TEXT PRIMARY KEY,
                node_id          TEXT NOT NULL,
                kind             TEXT NOT NULL,
                payload          TEXT NOT NULL,
                created_at_ms    INTEGER NOT NULL,
                content_hash     TEXT NOT NULL,
                compression_stats TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_tm_node_id
                ON topology_manifests (node_id);
            CREATE INDEX IF NOT EXISTS idx_tm_kind
                ON topology_manifests (kind);
            CREATE INDEX IF NOT EXISTS idx_tm_created
                ON topology_manifests (created_at_ms);",
        )?;
        debug!(db = %self.db_path.display(), "topology_manifests table ready");
        Ok(())
    }

    /// Persist a manifest (upsert on `manifest_id`).
    pub fn store_manifest(&self, manifest: &TopologicalManifest) -> Result<()> {
        let conn = self.conn()?;
        let payload_str = serde_json::to_string(&manifest.payload)?;
        let stats_str = manifest
            .compression_stats
            .as_ref()
            .map(serde_json::to_string)
            .transpose()?;
        conn.execute(
            "INSERT OR REPLACE INTO topology_manifests
             (manifest_id, node_id, kind, payload, created_at_ms, content_hash, compression_stats)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
            params![
                manifest.manifest_id,
                manifest.node_id,
                manifest.kind,
                payload_str,
                manifest.created_at_ms,
                manifest.content_hash,
                stats_str,
            ],
        )?;
        debug!(manifest_id = %manifest.manifest_id, "manifest stored");
        Ok(())
    }

    /// Retrieve a single manifest by ID.  Returns `None` if not found.
    pub fn get_manifest(&self, manifest_id: &str) -> Result<Option<TopologicalManifest>> {
        let conn = self.conn()?;
        let mut stmt = conn.prepare(
            "SELECT manifest_id, node_id, kind, payload, created_at_ms, content_hash, compression_stats
             FROM topology_manifests WHERE manifest_id = ?1",
        )?;
        let mut rows = stmt.query(params![manifest_id])?;
        if let Some(row) = rows.next()? {
            Ok(Some(row_to_manifest(row)?))
        } else {
            Ok(None)
        }
    }

    /// List manifests, optionally filtered by `node_id` and/or `kind`.
    ///
    /// Results are ordered by `created_at_ms` descending (newest first).
    pub fn list_manifests(
        &self,
        node_id: Option<&str>,
        kind: Option<&str>,
        limit: i64,
    ) -> Result<Vec<TopologicalManifest>> {
        let conn = self.conn()?;

        // Build query dynamically based on provided filters.
        let mut sql = String::from(
            "SELECT manifest_id, node_id, kind, payload, created_at_ms, content_hash, compression_stats
             FROM topology_manifests WHERE 1=1",
        );
        let mut param_strings: Vec<String> = Vec::new();

        if let Some(nid) = node_id {
            sql.push_str(" AND node_id = ?");
            param_strings.push(nid.to_string());
        }
        if let Some(k) = kind {
            sql.push_str(" AND kind = ?");
            param_strings.push(k.to_string());
        }
        sql.push_str(" ORDER BY created_at_ms DESC LIMIT ?");

        // Rebuild with concrete index placeholders for rusqlite.
        let mut indexed_sql = String::from(
            "SELECT manifest_id, node_id, kind, payload, created_at_ms, content_hash, compression_stats
             FROM topology_manifests WHERE 1=1",
        );
        let mut param_idx = 1usize;

        if node_id.is_some() {
            indexed_sql.push_str(&format!(" AND node_id = ?{}", param_idx));
            param_idx += 1;
        }
        if kind.is_some() {
            indexed_sql.push_str(&format!(" AND kind = ?{}", param_idx));
            param_idx += 1;
        }
        indexed_sql.push_str(&format!(" ORDER BY created_at_ms DESC LIMIT ?{}", param_idx));

        let mut stmt = conn.prepare(&indexed_sql)?;

        // Bind parameters positionally.
        let mut manifests = Vec::new();
        let result: rusqlite::Result<Vec<TopologicalManifest>> = match (node_id, kind) {
            (Some(nid), Some(k)) => {
                let mut rows = stmt.query(params![nid, k, limit])?;
                let mut v = Vec::new();
                while let Some(row) = rows.next()? {
                    v.push(row_to_manifest(row)?);
                }
                Ok(v)
            }
            (Some(nid), None) => {
                let mut rows = stmt.query(params![nid, limit])?;
                let mut v = Vec::new();
                while let Some(row) = rows.next()? {
                    v.push(row_to_manifest(row)?);
                }
                Ok(v)
            }
            (None, Some(k)) => {
                let mut rows = stmt.query(params![k, limit])?;
                let mut v = Vec::new();
                while let Some(row) = rows.next()? {
                    v.push(row_to_manifest(row)?);
                }
                Ok(v)
            }
            (None, None) => {
                let mut rows = stmt.query(params![limit])?;
                let mut v = Vec::new();
                while let Some(row) = rows.next()? {
                    v.push(row_to_manifest(row)?);
                }
                Ok(v)
            }
        };
        manifests = result?;
        Ok(manifests)
    }

    /// Aggregate compression statistics across all stored manifests.
    ///
    /// Returns a JSON object with:
    /// - `total_manifests`: count of all records
    /// - `total_original_size`: sum of `compression_stats.original_size`
    /// - `total_compressed_size`: sum of `compression_stats.compressed_size`
    /// - `total_reduction`: total bytes saved
    /// - `average_reduction_percent`: percentage if original > 0
    ///
    /// Ported from `TopologicalStorageDeltaGCL.get_compression_stats()`.
    pub fn get_compression_stats(&self) -> Result<serde_json::Value> {
        let conn = self.conn()?;

        // Row count.
        let total: i64 = conn.query_row(
            "SELECT COUNT(*) FROM topology_manifests",
            [],
            |row| row.get(0),
        )?;

        if total == 0 {
            return Ok(serde_json::json!({ "total_manifests": 0 }));
        }

        // Pull every non-null compression_stats blob and aggregate.
        let mut stmt = conn.prepare(
            "SELECT compression_stats FROM topology_manifests WHERE compression_stats IS NOT NULL",
        )?;
        let mut rows = stmt.query([])?;

        let mut total_original: i64 = 0;
        let mut total_compressed: i64 = 0;
        let mut stats_rows: i64 = 0;

        while let Some(row) = rows.next()? {
            let blob: String = row.get(0)?;
            if let Ok(v) = serde_json::from_str::<serde_json::Value>(&blob) {
                let orig = v
                    .get("original_size")
                    .and_then(|x| x.as_i64())
                    .unwrap_or(0);
                let comp = v
                    .get("compressed_size")
                    .and_then(|x| x.as_i64())
                    .unwrap_or(0);
                total_original += orig;
                total_compressed += comp;
                stats_rows += 1;
            }
        }

        let total_reduction = total_original - total_compressed;
        let avg_reduction_pct = if total_original > 0 {
            (total_reduction as f64 / total_original as f64) * 100.0
        } else {
            0.0
        };

        Ok(serde_json::json!({
            "total_manifests": total,
            "manifests_with_compression_stats": stats_rows,
            "total_original_size": total_original,
            "total_compressed_size": total_compressed,
            "total_reduction": total_reduction,
            "average_reduction_percent": avg_reduction_pct,
        }))
    }
}

/// Deserialise a rusqlite `Row` into a `TopologicalManifest`.
fn row_to_manifest(row: &rusqlite::Row<'_>) -> rusqlite::Result<TopologicalManifest> {
    let payload_str: String = row.get(3)?;
    let stats_str: Option<String> = row.get(6)?;

    let payload: serde_json::Value = serde_json::from_str(&payload_str)
        .unwrap_or(serde_json::Value::Null);
    let compression_stats: Option<serde_json::Value> = stats_str
        .as_deref()
        .and_then(|s| serde_json::from_str(s).ok());

    Ok(TopologicalManifest {
        manifest_id: row.get(0)?,
        node_id: row.get(1)?,
        kind: row.get(2)?,
        payload,
        created_at_ms: row.get(4)?,
        content_hash: row.get(5)?,
        compression_stats,
    })
}

// ═══════════════════════════════════════════════════════════════════════════
// §7  TopologyController
// ═══════════════════════════════════════════════════════════════════════════

/// Orchestrator that owns a peer map and a manifest store.
///
/// Ported from `TopologyController` in topology_controller.py, extended with
/// the manifest-store capability from topology_storage_delta_gcl.py.
pub struct TopologyController {
    /// Persistent manifest storage.
    pub storage: TopologicalStorage,
    /// This controller's own node ID.
    pub node_id: String,
    /// Map of peer node_id → live runtime.
    pub peers: HashMap<String, NodeRuntime>,
}

impl TopologyController {
    /// Create a new controller with the given node ID and database path.
    pub fn new(node_id: &str, db_path: impl AsRef<Path>) -> Result<Self> {
        let storage = TopologicalStorage::new(db_path)?;
        Ok(Self {
            storage,
            node_id: node_id.to_string(),
            peers: HashMap::new(),
        })
    }

    /// Register a peer runtime (or replace an existing one with the same ID).
    pub fn register_peer(&mut self, runtime: NodeRuntime) {
        let id = runtime.config.node_id.clone();
        info!(peer = %id, role = %runtime.config.role, "peer registered");
        self.peers.insert(id, runtime);
    }

    /// Remove a peer by node ID.  No-op if the peer is not known.
    pub fn remove_peer(&mut self, peer_id: &str) {
        if self.peers.remove(peer_id).is_some() {
            info!(peer = %peer_id, "peer removed");
        }
    }

    /// Advance every registered peer by one tick.
    pub fn tick_all(&mut self) {
        for runtime in self.peers.values_mut() {
            runtime.tick();
        }
    }

    /// Return references to all peers currently in the `Active` state.
    pub fn healthy_peers(&self) -> Vec<&NodeRuntime> {
        self.peers
            .values()
            .filter(|r| r.is_active())
            .collect()
    }

    /// Emit a manifest of the given `kind` with `payload`, storing it
    /// durably in SQLite.
    ///
    /// The `manifest_id` is derived as `"<node_id>/<kind>/<created_at_ms>"`.
    /// The `content_hash` is the SHA-256 of the canonical JSON payload.
    ///
    /// Ported from `announce_manifest` concept in topology_controller.py +
    /// `store_manifest` in topological_storage_delta_gcl.py.
    pub fn announce_manifest(
        &self,
        kind: &str,
        payload: serde_json::Value,
    ) -> Result<TopologicalManifest> {
        let ts = now_ms();
        let manifest_id = format!("{}/{}/{}", self.node_id, kind, ts);
        let manifest = TopologicalManifest::build(&manifest_id, &self.node_id, kind, payload);
        self.storage.store_manifest(&manifest)?;
        info!(
            manifest_id = %manifest.manifest_id,
            kind = %kind,
            hash = %manifest.content_hash,
            "manifest announced"
        );
        Ok(manifest)
    }

    /// Retrieve a previously stored manifest by ID.
    pub fn get_manifest(&self, manifest_id: &str) -> Result<Option<TopologicalManifest>> {
        self.storage.get_manifest(manifest_id)
    }

    /// List manifests, forwarding to storage.
    pub fn list_manifests(
        &self,
        node_id: Option<&str>,
        kind: Option<&str>,
        limit: i64,
    ) -> Result<Vec<TopologicalManifest>> {
        self.storage.list_manifests(node_id, kind, limit)
    }

    /// Emit a heartbeat manifest from every healthy peer, storing them all.
    ///
    /// Returns the manifests emitted (one per active peer).
    pub fn broadcast_heartbeats(&self) -> Result<Vec<TopologicalManifest>> {
        let mut out = Vec::new();
        for peer in self.healthy_peers() {
            let ts = now_ms();
            let manifest_id = format!("{}/heartbeat/{}", peer.config.node_id, ts);
            let payload = peer.heartbeat_json();
            let manifest =
                TopologicalManifest::build(&manifest_id, &peer.config.node_id, "heartbeat", payload);
            self.storage.store_manifest(&manifest)?;
            out.push(manifest);
        }
        Ok(out)
    }

    /// Return a JSON status snapshot of this controller.
    pub fn status_json(&self) -> serde_json::Value {
        let healthy = self.healthy_peers().len();
        let total = self.peers.len();
        let peer_states: Vec<serde_json::Value> = self
            .peers
            .values()
            .map(|r| {
                serde_json::json!({
                    "node_id": r.config.node_id,
                    "role": r.config.role.as_str(),
                    "state": r.state.as_str(),
                    "energy": r.energy.to_f64(),
                    "step": r.step,
                })
            })
            .collect();
        serde_json::json!({
            "controller_id": self.node_id,
            "total_peers": total,
            "healthy_peers": healthy,
            "peers": peer_states,
        })
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// §8  TopologicalEngineClient stub
// ═══════════════════════════════════════════════════════════════════════════

/// HTTP client stub for the private topological engine (NoDupeLabs API).
///
/// Ported from `TopologicalEngineClient` in topological_engine_client.py.
/// Uses `reqwest` with JSON support.
pub struct TopologicalEngineClient {
    /// Base URL of the topological engine (e.g. "http://localhost:3000").
    pub base_url: String,
    /// Optional Bearer token from `TOPOLOGICAL_ENGINE_TOKEN`.
    token: Option<String>,
    http: reqwest::Client,
}

impl TopologicalEngineClient {
    /// Construct a client, reading the optional auth token from the
    /// `TOPOLOGICAL_ENGINE_TOKEN` environment variable.
    pub fn new(base_url: &str) -> Self {
        let token = std::env::var("TOPOLOGICAL_ENGINE_TOKEN").ok();
        let http = reqwest::Client::builder()
            .timeout(std::time::Duration::from_secs(30))
            .build()
            .expect("reqwest client construction should not fail");
        Self {
            base_url: base_url.trim_end_matches('/').to_string(),
            token,
            http,
        }
    }

    /// Build a request builder with the Authorization header set if a token
    /// is available.
    fn request(&self, method: reqwest::Method, path: &str) -> reqwest::RequestBuilder {
        let url = format!("{}{}", self.base_url, path);
        let mut builder = self.http.request(method, &url);
        if let Some(ref tok) = self.token {
            builder = builder.bearer_auth(tok);
        }
        builder
    }

    /// Ping the `/health` endpoint.  Returns `true` when the engine responds
    /// with HTTP 2xx.
    pub async fn ping(&self) -> Result<bool> {
        let resp = self
            .request(reqwest::Method::GET, "/health")
            .send()
            .await;
        match resp {
            Ok(r) => Ok(r.status().is_success()),
            Err(e) => {
                warn!(error = %e, "topological engine health check failed");
                Ok(false)
            }
        }
    }

    /// POST a manifest to `/manifests`.
    pub async fn store_manifest(&self, m: &TopologicalManifest) -> Result<()> {
        let resp = self
            .request(reqwest::Method::POST, "/manifests")
            .json(m)
            .send()
            .await?;
        if resp.status().is_success() {
            Ok(())
        } else {
            let status = resp.status();
            let body = resp.text().await.unwrap_or_default();
            Err(anyhow!(
                "store_manifest failed: HTTP {} — {}",
                status,
                body
            ))
        }
    }

    /// GET `/manifests/{id}`.  Returns `None` on HTTP 404, error on other
    /// non-success statuses.
    pub async fn get_manifest(&self, id: &str) -> Result<Option<TopologicalManifest>> {
        let path = format!("/manifests/{}", id);
        let resp = self
            .request(reqwest::Method::GET, &path)
            .send()
            .await?;
        match resp.status() {
            s if s.is_success() => {
                let m: TopologicalManifest = resp.json().await?;
                Ok(Some(m))
            }
            s if s.as_u16() == 404 => Ok(None),
            s => {
                let body = resp.text().await.unwrap_or_default();
                Err(anyhow!("get_manifest({}) failed: HTTP {} — {}", id, s, body))
            }
        }
    }

    /// List manifests via `GET /manifests` with optional query parameters.
    pub async fn list_manifests(
        &self,
        node_id: Option<&str>,
        kind: Option<&str>,
        limit: Option<i64>,
    ) -> Result<Vec<TopologicalManifest>> {
        let mut qp: Vec<(&str, String)> = Vec::new();
        if let Some(nid) = node_id {
            qp.push(("node_id", nid.to_string()));
        }
        if let Some(k) = kind {
            qp.push(("kind", k.to_string()));
        }
        if let Some(l) = limit {
            qp.push(("limit", l.to_string()));
        }
        let resp = self
            .request(reqwest::Method::GET, "/manifests")
            .query(&qp)
            .send()
            .await?;
        if resp.status().is_success() {
            let v: Vec<TopologicalManifest> = resp.json().await?;
            Ok(v)
        } else {
            let status = resp.status();
            let body = resp.text().await.unwrap_or_default();
            Err(anyhow!("list_manifests failed: HTTP {} — {}", status, body))
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// Utilities
// ═══════════════════════════════════════════════════════════════════════════

/// Current time as milliseconds since UNIX epoch.
fn now_ms() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_millis() as i64)
        .unwrap_or(0)
}

// ═══════════════════════════════════════════════════════════════════════════
// Tests
// ═══════════════════════════════════════════════════════════════════════════

#[cfg(test)]
mod tests {
    use super::*;

    // ── Q16_16 ─────────────────────────────────────────────────────────────

    #[test]
    fn q16_16_from_nat_one() {
        assert_eq!(Q16_16::from_nat(1), Q16_16::ONE);
    }

    #[test]
    fn q16_16_from_frac_half() {
        let half = Q16_16::from_frac(1, 2);
        assert_eq!(half.0, 32768);
        let approx = (half.to_f64() - 0.5_f64).abs();
        assert!(approx < 1e-6, "to_f64 of 0.5 = {}", half.to_f64());
    }

    #[test]
    fn q16_16_wrapping_add_sub() {
        let a = Q16_16::from_nat(3);
        let b = Q16_16::from_nat(2);
        assert_eq!(a.wrapping_sub(b), Q16_16::ONE);
        assert_eq!(b.wrapping_add(Q16_16::ONE), a);
    }

    #[test]
    fn q16_16_zero_denom() {
        assert_eq!(Q16_16::from_frac(1, 0), Q16_16::ZERO);
    }

    // ── Capability cost ─────────────────────────────────────────────────────

    #[test]
    fn capability_cost_fpga() {
        assert_eq!(capability_cost(NodeCapability::FpgaSynth), Q16_16::from_nat(50));
    }

    #[test]
    fn capability_cost_relay() {
        assert_eq!(capability_cost(NodeCapability::Relay), Q16_16::from_nat(1));
    }

    // ── Role defaults ───────────────────────────────────────────────────────

    #[test]
    fn default_capabilities_core_includes_lean() {
        let caps = default_capabilities(NodeRole::Core);
        assert!(caps.contains(&NodeCapability::LeanBuild));
    }

    #[test]
    fn default_bind_classes_judge() {
        let bcs = default_bind_classes(NodeRole::Judge);
        assert!(bcs.contains(&BindClass::Informational));
        assert!(bcs.contains(&BindClass::Control));
        assert!(!bcs.contains(&BindClass::Geometric));
    }

    #[test]
    fn max_energy_core() {
        assert_eq!(max_energy(NodeRole::Core), Q16_16::from_nat(100));
    }

    #[test]
    fn recovery_rate_edge() {
        assert_eq!(recovery_rate(NodeRole::Edge), Q16_16::from_frac(1, 8));
    }

    // ── State machine ───────────────────────────────────────────────────────

    #[test]
    fn allowed_transitions_happy_path() {
        assert!(is_allowed_transition(NodeStateEnum::Boot, NodeStateEnum::Selftest));
        assert!(is_allowed_transition(NodeStateEnum::Selftest, NodeStateEnum::Announce));
        assert!(is_allowed_transition(NodeStateEnum::Announce, NodeStateEnum::Active));
        assert!(is_allowed_transition(NodeStateEnum::Active, NodeStateEnum::Degraded));
        assert!(is_allowed_transition(NodeStateEnum::Failed, NodeStateEnum::Boot));
    }

    #[test]
    fn disallowed_transition_boot_active() {
        assert!(!is_allowed_transition(NodeStateEnum::Boot, NodeStateEnum::Active));
    }

    #[test]
    fn node_runtime_full_boot_sequence() {
        let cfg = NodeConfig::with_defaults(
            "test-node",
            NodeRole::Core,
            4096,
            500,
            "us-test-1",
            "100.0.0.1",
        );
        let mut rt = NodeRuntime::new(cfg);
        assert_eq!(rt.state, NodeStateEnum::Boot);
        assert_eq!(rt.energy, max_energy(NodeRole::Core));

        rt.transition(NodeStateEnum::Selftest).unwrap();
        rt.transition(NodeStateEnum::Announce).unwrap();
        rt.transition(NodeStateEnum::Active).unwrap();
        assert_eq!(rt.state, NodeStateEnum::Active);
        assert!(rt.is_active());
    }

    #[test]
    fn node_runtime_transition_bad_edge_errors() {
        let cfg = NodeConfig::with_defaults(
            "bad-node",
            NodeRole::Edge,
            512,
            50,
            "test",
            "10.0.0.1",
        );
        let mut rt = NodeRuntime::new(cfg);
        // Boot → Active is not allowed.
        assert!(rt.transition(NodeStateEnum::Active).is_err());
    }

    #[test]
    fn node_runtime_tick_recovers_energy() {
        let cfg = NodeConfig::with_defaults(
            "tick-node",
            NodeRole::Judge,
            1024,
            100,
            "test",
            "10.0.0.2",
        );
        let mut rt = NodeRuntime::new(cfg);
        // Burn some energy via a transition.
        rt.transition(NodeStateEnum::Selftest).unwrap();
        let after_transition = rt.energy;
        rt.tick();
        // Energy should have increased by recovery_rate(Judge) = 0.25.
        assert!(
            rt.energy.0 >= after_transition.0,
            "tick should recover energy: before={} after={}",
            after_transition.0,
            rt.energy.0
        );
    }

    #[test]
    fn node_runtime_tick_caps_at_max() {
        let cfg = NodeConfig::with_defaults(
            "full-node",
            NodeRole::Mirror,
            2048,
            200,
            "test",
            "10.0.0.3",
        );
        let mut rt = NodeRuntime::new(cfg);
        // Energy starts at max; tick should not overflow.
        for _ in 0..10 {
            rt.tick();
        }
        assert_eq!(
            rt.energy,
            max_energy(NodeRole::Mirror),
            "energy must not exceed max after repeated ticks"
        );
    }

    #[test]
    fn heartbeat_json_structure() {
        let cfg = NodeConfig::with_defaults(
            "hb-node",
            NodeRole::Edge,
            256,
            10,
            "edge-zone",
            "100.1.2.3",
        );
        let rt = NodeRuntime::new(cfg);
        let hb = rt.heartbeat_json();
        assert_eq!(hb["node_id"], "hb-node");
        assert_eq!(hb["role"], "edge");
        assert_eq!(hb["state"], "boot");
        assert!(hb["energy"]["val"].is_number());
    }

    // ── TopologicalManifest ─────────────────────────────────────────────────

    #[test]
    fn manifest_hash_is_deterministic() {
        let payload = serde_json::json!({"vertices": 1000, "edges": 2500});
        let h1 = TopologicalManifest::compute_hash(&payload);
        let h2 = TopologicalManifest::compute_hash(&payload);
        assert_eq!(h1, h2);
        assert_eq!(h1.len(), 64, "SHA-256 hex is 64 chars");
    }

    #[test]
    fn manifest_hash_differs_on_payload_change() {
        let p1 = serde_json::json!({"x": 1});
        let p2 = serde_json::json!({"x": 2});
        assert_ne!(
            TopologicalManifest::compute_hash(&p1),
            TopologicalManifest::compute_hash(&p2)
        );
    }

    // ── TopologicalStorage ──────────────────────────────────────────────────

    fn tmp_db_path(tag: &str) -> PathBuf {
        std::env::temp_dir().join(format!("topology_test_{}.db", tag))
    }

    #[test]
    fn storage_round_trip() {
        let path = tmp_db_path("round_trip");
        let storage = TopologicalStorage::new(&path).unwrap();

        let manifest = TopologicalManifest::build(
            "test/announce/1",
            "test-node",
            "announce",
            serde_json::json!({"hello": "world"}),
        );
        storage.store_manifest(&manifest).unwrap();

        let retrieved = storage.get_manifest("test/announce/1").unwrap().unwrap();
        assert_eq!(retrieved.manifest_id, manifest.manifest_id);
        assert_eq!(retrieved.content_hash, manifest.content_hash);
        assert_eq!(retrieved.payload["hello"], "world");
    }

    #[test]
    fn storage_get_missing_returns_none() {
        let path = tmp_db_path("missing");
        let storage = TopologicalStorage::new(&path).unwrap();
        assert!(storage.get_manifest("does-not-exist").unwrap().is_none());
    }

    #[test]
    fn storage_list_with_filters() {
        let path = tmp_db_path("list_filters");
        let storage = TopologicalStorage::new(&path).unwrap();

        for i in 0..5u32 {
            let m = TopologicalManifest::build(
                format!("node-a/announce/{}", i),
                "node-a",
                "announce",
                serde_json::json!({"i": i}),
            );
            storage.store_manifest(&m).unwrap();
        }
        for i in 0..3u32 {
            let m = TopologicalManifest::build(
                format!("node-b/heartbeat/{}", i),
                "node-b",
                "heartbeat",
                serde_json::json!({"i": i}),
            );
            storage.store_manifest(&m).unwrap();
        }

        let by_node = storage.list_manifests(Some("node-a"), None, 100).unwrap();
        assert_eq!(by_node.len(), 5);

        let by_kind = storage.list_manifests(None, Some("heartbeat"), 100).unwrap();
        assert_eq!(by_kind.len(), 3);

        let limited = storage.list_manifests(None, None, 4).unwrap();
        assert_eq!(limited.len(), 4);
    }

    #[test]
    fn storage_compression_stats_empty() {
        let path = tmp_db_path("stats_empty");
        let storage = TopologicalStorage::new(&path).unwrap();
        let stats = storage.get_compression_stats().unwrap();
        assert_eq!(stats["total_manifests"], 0);
    }

    #[test]
    fn storage_compression_stats_with_data() {
        let path = tmp_db_path("stats_data");
        let storage = TopologicalStorage::new(&path).unwrap();

        let mut m = TopologicalManifest::build(
            "node/kind/1",
            "node",
            "kind",
            serde_json::json!({}),
        );
        m.compression_stats = Some(serde_json::json!({
            "original_size": 1000,
            "compressed_size": 400
        }));
        storage.store_manifest(&m).unwrap();

        let stats = storage.get_compression_stats().unwrap();
        assert_eq!(stats["total_manifests"], 1);
        assert_eq!(stats["total_original_size"], 1000);
        assert_eq!(stats["total_compressed_size"], 400);
        assert_eq!(stats["total_reduction"], 600);
    }

    // ── TopologyController ──────────────────────────────────────────────────

    #[test]
    fn controller_register_and_healthy_peers() {
        let path = tmp_db_path("ctrl_peers");
        let mut ctrl = TopologyController::new("ctrl", &path).unwrap();

        // Add a peer in Boot state — not healthy.
        let cfg_a = NodeConfig::with_defaults("peer-a", NodeRole::Mirror, 1024, 100, "t", "1.2.3.4");
        ctrl.register_peer(NodeRuntime::new(cfg_a));

        // Add a peer and walk to Active.
        let cfg_b = NodeConfig::with_defaults("peer-b", NodeRole::Edge, 512, 50, "t", "1.2.3.5");
        let mut rt_b = NodeRuntime::new(cfg_b);
        rt_b.transition(NodeStateEnum::Selftest).unwrap();
        rt_b.transition(NodeStateEnum::Announce).unwrap();
        rt_b.transition(NodeStateEnum::Active).unwrap();
        ctrl.register_peer(rt_b);

        assert_eq!(ctrl.healthy_peers().len(), 1);
    }

    #[test]
    fn controller_tick_all_advances_steps() {
        let path = tmp_db_path("ctrl_tick");
        let mut ctrl = TopologyController::new("ctrl", &path).unwrap();
        let cfg = NodeConfig::with_defaults("p", NodeRole::FoxTop, 256, 10, "t", "1.0.0.1");
        ctrl.register_peer(NodeRuntime::new(cfg));
        ctrl.tick_all();
        assert_eq!(ctrl.peers["p"].step, 1);
    }

    #[test]
    fn controller_announce_manifest_stores_and_returns() {
        let tmp = tempfile::NamedTempFile::new().expect("tempfile");
        let ctrl = TopologyController::new("ctrl-node", tmp.path()).unwrap();
        let payload = serde_json::json!({"test": true});
        let m = ctrl.announce_manifest("test-kind", payload).unwrap();
        assert_eq!(m.node_id, "ctrl-node");
        assert_eq!(m.kind, "test-kind");
        assert_eq!(m.payload["test"], true);
        // Verify it was persisted.
        let fetched = ctrl.get_manifest(&m.manifest_id).unwrap().unwrap();
        assert_eq!(fetched.content_hash, m.content_hash);
    }
}
