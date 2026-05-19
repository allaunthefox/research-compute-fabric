#![allow(dead_code)]
//! ene_cloud_credential_manager.rs — ENE node balancer and cloud credential
//! manager with SQLite persistence.
//!
//! Port of ene_cloud_credential_manager.py (656 lines).

use anyhow::{Context, Result};
use rusqlite::{params, Connection};
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};

// ─────────────────────────────────────────────────────────────────────────────
// §0  Shared helpers
// ─────────────────────────────────────────────────────────────────────────────

/// Current wall-clock time in whole seconds since the UNIX epoch.
fn now_secs() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs() as i64
}

/// SHA-256 of `data`; returns the first 16 lowercase hex characters.
fn sha256_hex16(data: &[u8]) -> String {
    let mut h = Sha256::new();
    h.update(data);
    hex::encode(&h.finalize()[..8]) // 8 bytes → 16 hex chars
}

// ─────────────────────────────────────────────────────────────────────────────
// §1  NodeStats / NodeConnection
// ─────────────────────────────────────────────────────────────────────────────

/// Aggregated statistics for a registered ENE node.
#[derive(Debug, Clone)]
pub struct NodeStats {
    pub node_id: String,
    pub total_connections: i64,
    pub total_bytes: i64,
    pub avg_latency: f64,
    pub error_rate: f64,
    /// In [0.0, 1.0].  Higher is healthier.
    pub health_score: f64,
}

impl NodeStats {
    fn new(node_id: &str) -> Self {
        Self {
            node_id: node_id.to_owned(),
            total_connections: 0,
            total_bytes: 0,
            avg_latency: 0.0,
            error_rate: 0.0,
            health_score: 1.0,
        }
    }
}

/// A live (or recently closed) connection to an ENE node.
#[derive(Debug, Clone)]
pub struct NodeConnection {
    pub node_id: String,
    pub credential_id: String,
    pub connected_at: f64,
    pub last_activity: f64,
    pub bytes_transferred: i64,
    pub error_count: i64,
    pub latency_ms: f64,
    pub status: String,
}

// ─────────────────────────────────────────────────────────────────────────────
// §2  ENENodeBalancer
// ─────────────────────────────────────────────────────────────────────────────

/// Load-balancing dispatcher for ENE nodes with SQLite-backed statistics.
pub struct ENENodeBalancer {
    db_path: String,
    /// In-memory shadow of the `nodes` table (node_id → stats).
    pub nodes: HashMap<String, NodeStats>,
    /// Connections that have been recorded but not yet closed.
    pub active_connections: HashMap<String, NodeConnection>,
}

impl ENENodeBalancer {
    // ── §2.1  Constructor ────────────────────────────────────────────────────

    /// Open (or create) the SQLite database at `db_path`, ensure the schema
    /// exists, and load all previously-registered nodes into memory.
    pub fn new(db_path: &str) -> Result<Self> {
        let mut balancer = Self {
            db_path: db_path.to_owned(),
            nodes: HashMap::new(),
            active_connections: HashMap::new(),
        };
        balancer.init_tables()?;
        balancer.load_nodes()?;
        Ok(balancer)
    }

    fn open(&self) -> Result<Connection> {
        Connection::open(&self.db_path)
            .with_context(|| format!("ENENodeBalancer: open db {:?}", self.db_path))
    }

    fn init_tables(&self) -> Result<()> {
        let conn = self.open()?;
        conn.execute_batch(
            "CREATE TABLE IF NOT EXISTS nodes (
                node_id           TEXT PRIMARY KEY,
                credential_id     TEXT NOT NULL,
                total_connections INTEGER NOT NULL DEFAULT 0,
                total_bytes       INTEGER NOT NULL DEFAULT 0,
                avg_latency       REAL    NOT NULL DEFAULT 0.0,
                error_rate        REAL    NOT NULL DEFAULT 0.0,
                health_score      REAL    NOT NULL DEFAULT 1.0,
                registered_at     INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS connections (
                connection_id     TEXT PRIMARY KEY,
                node_id           TEXT NOT NULL,
                credential_id     TEXT NOT NULL,
                connected_at      REAL NOT NULL,
                last_activity     REAL NOT NULL,
                bytes_transferred INTEGER NOT NULL DEFAULT 0,
                error_count       INTEGER NOT NULL DEFAULT 0,
                latency_ms        REAL    NOT NULL DEFAULT 0.0,
                status            TEXT    NOT NULL DEFAULT 'active'
            );",
        )
        .context("ENENodeBalancer: init_tables")?;
        Ok(())
    }

    fn load_nodes(&mut self) -> Result<()> {
        let conn = self.open()?;
        let mut stmt = conn.prepare(
            "SELECT node_id, total_connections, total_bytes, avg_latency, error_rate, health_score
               FROM nodes",
        )?;
        let rows = stmt.query_map([], |row| {
            Ok(NodeStats {
                node_id: row.get(0)?,
                total_connections: row.get(1)?,
                total_bytes: row.get(2)?,
                avg_latency: row.get(3)?,
                error_rate: row.get(4)?,
                health_score: row.get(5)?,
            })
        })?;
        for row in rows {
            let stats = row?;
            self.nodes.insert(stats.node_id.clone(), stats);
        }
        Ok(())
    }

    // ── §2.2  Node management ────────────────────────────────────────────────

    /// Register a new node; returns `true` if inserted, `false` if it already
    /// existed.
    pub fn register_node(&mut self, node_id: &str, credential_id: &str) -> Result<bool> {
        if self.nodes.contains_key(node_id) {
            return Ok(false);
        }
        let conn = self.open()?;
        conn.execute(
            "INSERT OR IGNORE INTO nodes
                (node_id, credential_id, registered_at)
             VALUES (?1, ?2, ?3)",
            params![node_id, credential_id, now_secs()],
        )
        .context("ENENodeBalancer: register_node")?;
        self.nodes.insert(node_id.to_owned(), NodeStats::new(node_id));
        Ok(true)
    }

    // ── §2.3  Node selection ─────────────────────────────────────────────────

    /// Pick a node according to the named strategy.
    ///
    /// | Strategy           | Description                                  |
    /// |--------------------|----------------------------------------------|
    /// | `health_weighted`  | Probabilistic, weighted by `health_score`.   |
    /// | `round_robin`      | First node in sorted order.                  |
    /// | `latency`          | Node with the lowest `avg_latency`.          |
    /// | `least_connections`| Node with the fewest `total_connections`.    |
    ///
    /// Returns `None` when no nodes are registered.
    pub fn select_node(&self, strategy: &str) -> Option<String> {
        if self.nodes.is_empty() {
            return None;
        }

        // Collect a stable-ordered snapshot.
        let mut nodes_vec: Vec<&NodeStats> = self.nodes.values().collect();
        nodes_vec.sort_by(|a, b| a.node_id.cmp(&b.node_id));

        match strategy {
            "health_weighted" => self.select_health_weighted(&nodes_vec),
            "round_robin" => nodes_vec.first().map(|n| n.node_id.clone()),
            "latency" => nodes_vec
                .iter()
                .min_by(|a, b| {
                    a.avg_latency
                        .partial_cmp(&b.avg_latency)
                        .unwrap_or(std::cmp::Ordering::Equal)
                })
                .map(|n| n.node_id.clone()),
            "least_connections" => nodes_vec
                .iter()
                .min_by_key(|n| n.total_connections)
                .map(|n| n.node_id.clone()),
            _ => nodes_vec.first().map(|n| n.node_id.clone()),
        }
    }

    /// Health-weighted selection using a hash-based pseudo-random threshold.
    ///
    /// 1. Sort nodes by health_score descending.
    /// 2. Scale health scores to integers (×1000) to get total_weight.
    /// 3. Hash `(sorted_ids joined by "+") + now_secs` → u64 seed.
    /// 4. `threshold = seed % total_weight`.
    /// 5. Walk cumulative sums; return first node where cumulative ≥ threshold.
    fn select_health_weighted(&self, nodes: &[&NodeStats]) -> Option<String> {
        // Sort descending by health so healthiest nodes are visited first.
        let mut sorted: Vec<&NodeStats> = nodes.to_vec();
        sorted.sort_by(|a, b| {
            b.health_score
                .partial_cmp(&a.health_score)
                .unwrap_or(std::cmp::Ordering::Equal)
        });

        let weights: Vec<u64> = sorted
            .iter()
            .map(|n| (n.health_score.max(0.0) * 1000.0) as u64 + 1)
            .collect();
        let total_weight: u64 = weights.iter().sum();
        if total_weight == 0 {
            return sorted.first().map(|n| n.node_id.clone());
        }

        // Derive a pseudo-random threshold from the node IDs + current time.
        let ids_str = sorted
            .iter()
            .map(|n| n.node_id.as_str())
            .collect::<Vec<_>>()
            .join("+");
        let seed_input = format!("{}{}", ids_str, now_secs());
        let mut h = Sha256::new();
        h.update(seed_input.as_bytes());
        let digest = h.finalize();
        let seed_bytes: [u8; 8] = digest[..8].try_into().unwrap_or([0u8; 8]);
        let seed = u64::from_le_bytes(seed_bytes);
        let threshold = seed % total_weight;

        let mut cumulative = 0u64;
        for (node, &w) in sorted.iter().zip(weights.iter()) {
            cumulative += w;
            if cumulative >= threshold {
                return Some(node.node_id.clone());
            }
        }
        // Fallback (should not be reached).
        sorted.first().map(|n| n.node_id.clone())
    }

    // ── §2.4  Connection lifecycle ───────────────────────────────────────────

    /// Record a new connection to `node_id`, returning a unique `connection_id`.
    ///
    /// The `connection_id` is the first 16 hex chars of `SHA-256(node_id +
    /// timestamp_secs_as_str)`.
    pub fn record_connection(
        &mut self,
        node_id: &str,
        credential_id: &str,
    ) -> Result<String> {
        let now = now_secs() as f64;
        let connection_id =
            sha256_hex16(format!("{}{}", node_id, now as i64).as_bytes());

        let conn_rec = NodeConnection {
            node_id: node_id.to_owned(),
            credential_id: credential_id.to_owned(),
            connected_at: now,
            last_activity: now,
            bytes_transferred: 0,
            error_count: 0,
            latency_ms: 0.0,
            status: "active".to_owned(),
        };

        let db = self.open()?;
        db.execute(
            "INSERT OR REPLACE INTO connections
                (connection_id, node_id, credential_id, connected_at, last_activity, status)
             VALUES (?1, ?2, ?3, ?4, ?5, 'active')",
            params![connection_id, node_id, credential_id, now, now],
        )
        .context("ENENodeBalancer: record_connection")?;

        // Update in-memory node stats.
        if let Some(stats) = self.nodes.get_mut(node_id) {
            stats.total_connections += 1;
        }

        self.active_connections
            .insert(connection_id.clone(), conn_rec);
        Ok(connection_id)
    }

    /// Update bytes-transferred and latency for an active connection.
    pub fn update_connection_stats(
        &mut self,
        connection_id: &str,
        bytes_delta: i64,
        latency_ms: f64,
        error: bool,
    ) {
        let now = now_secs() as f64;
        if let Some(c) = self.active_connections.get_mut(connection_id) {
            c.bytes_transferred += bytes_delta;
            c.last_activity = now;
            // Rolling average latency (simple mean).
            c.latency_ms = (c.latency_ms + latency_ms) / 2.0;
            if error {
                c.error_count += 1;
            }

            // Mirror to node stats.
            if let Some(stats) = self.nodes.get_mut(&c.node_id.clone()) {
                stats.total_bytes += bytes_delta;
                stats.avg_latency = (stats.avg_latency + latency_ms) / 2.0;
                if error && c.error_count > 0 {
                    stats.error_rate = c.error_count as f64
                        / (c.error_count + stats.total_connections) as f64;
                }
            }
        }
    }

    /// Mark a connection as closed and persist final statistics.
    pub fn close_connection(&mut self, connection_id: &str) -> Result<()> {
        let db = self.open()?;
        db.execute(
            "UPDATE connections SET status = 'closed' WHERE connection_id = ?1",
            params![connection_id],
        )
        .context("ENENodeBalancer: close_connection")?;
        self.active_connections.remove(connection_id);
        Ok(())
    }

    // ── §2.5  Health check ───────────────────────────────────────────────────

    /// Perform a (synthetic) health check for `node_id`.
    ///
    /// - If `error_rate < 0.1` → `health_score += 0.05` (clamp 1.0).
    /// - Otherwise             → `health_score -= 0.1`  (clamp 0.0).
    ///
    /// Returns `true` when the node is considered healthy after the update.
    pub fn health_check(&mut self, node_id: &str) -> Result<bool> {
        let healthy = {
            if let Some(stats) = self.nodes.get_mut(node_id) {
                if stats.error_rate < 0.1 {
                    stats.health_score = (stats.health_score + 0.05).min(1.0);
                    true
                } else {
                    stats.health_score = (stats.health_score - 0.1).max(0.0);
                    false
                }
            } else {
                anyhow::bail!("health_check: unknown node '{}'", node_id);
            }
        };

        // Persist the updated health score.
        let score = self.nodes[node_id].health_score;
        let db = self.open()?;
        db.execute(
            "UPDATE nodes SET health_score = ?1 WHERE node_id = ?2",
            params![score, node_id],
        )
        .context("ENENodeBalancer: health_check persist")?;

        Ok(healthy)
    }

    // ── §2.6  Introspection ──────────────────────────────────────────────────

    /// Look up current statistics for a single node.
    pub fn get_node_stats(&self, node_id: &str) -> Option<&NodeStats> {
        self.nodes.get(node_id)
    }

    /// All registered nodes.
    pub fn get_all_nodes(&self) -> &HashMap<String, NodeStats> {
        &self.nodes
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// §3  CloudCredential / ENECredentialManager
// ─────────────────────────────────────────────────────────────────────────────

/// A cloud provider credential with an encrypted payload and node assignments.
#[derive(Debug, Clone)]
pub struct CloudCredential {
    pub credential_id: String,
    pub provider: String,
    /// Raw payload bytes (encryption delegated to `ene_core`).
    pub encrypted_payload: Vec<u8>,
    pub access_level: String,
    /// Node IDs to which this credential is assigned.
    pub node_assignments: Vec<String>,
    pub usage_count: i64,
    pub health_score: f64,
    pub is_active: bool,
}

/// In-memory credential store backed by an `ENENodeBalancer`.
pub struct ENECredentialManager {
    credentials: HashMap<String, CloudCredential>,
    pub balancer: ENENodeBalancer,
}

impl ENECredentialManager {
    // ── §3.1  Constructor ────────────────────────────────────────────────────

    pub fn new(db_path: &str) -> Result<Self> {
        Ok(Self {
            credentials: HashMap::new(),
            balancer: ENENodeBalancer::new(db_path)?,
        })
    }

    // ── §3.2  Credential CRUD ─────────────────────────────────────────────────

    /// Create a new `CloudCredential`.
    ///
    /// `credential_id` = first 16 hex chars of SHA-256(canonical JSON of payload).
    /// The `encrypted_payload` field stores the raw JSON bytes; actual encryption
    /// is handled by the `ene_core` module.
    pub fn create_credential(
        &mut self,
        provider: &str,
        payload: &Value,
        access_level: &str,
        node_assignments: Vec<String>,
    ) -> CloudCredential {
        let canonical = payload.to_string();
        let credential_id = sha256_hex16(canonical.as_bytes());

        let cred = CloudCredential {
            credential_id: credential_id.clone(),
            provider: provider.to_owned(),
            encrypted_payload: canonical.into_bytes(),
            access_level: access_level.to_owned(),
            node_assignments,
            usage_count: 0,
            health_score: 1.0,
            is_active: true,
        };
        self.credentials.insert(credential_id, cred.clone());
        cred
    }

    /// Retrieve a credential by ID; returns the payload as a JSON `Value`.
    pub fn get_credential(&self, credential_id: &str) -> Option<Value> {
        let cred = self.credentials.get(credential_id)?;
        if !cred.is_active {
            return None;
        }
        serde_json::from_slice(&cred.encrypted_payload).ok()
    }

    /// All currently active credentials.
    pub fn list_credentials(&self) -> Vec<&CloudCredential> {
        self.credentials
            .values()
            .filter(|c| c.is_active)
            .collect()
    }

    /// Deactivate a credential; returns `true` when it existed and was active.
    pub fn revoke_credential(&mut self, credential_id: &str) -> bool {
        if let Some(cred) = self.credentials.get_mut(credential_id) {
            if cred.is_active {
                cred.is_active = false;
                return true;
            }
        }
        false
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// §4  ENECloudBridge
// ─────────────────────────────────────────────────────────────────────────────

/// High-level bridge: combines credential management with the node balancer to
/// simulate cloud storage connections.
pub struct ENECloudBridge {
    credential_manager: ENECredentialManager,
}

impl ENECloudBridge {
    pub fn new(db_path: &str) -> Result<Self> {
        Ok(Self {
            credential_manager: ENECredentialManager::new(db_path)?,
        })
    }

    /// Select a healthy node and open a connection for `provider`.
    ///
    /// Returns the `connection_id` on success, or `None` if no suitable node
    /// is available.
    pub fn connect_to_storage(&mut self, provider: &str, node_id: &str) -> Option<String> {
        // Register the node if not already known.
        let cred_id = sha256_hex16(provider.as_bytes());
        let _ = self
            .credential_manager
            .balancer
            .register_node(node_id, &cred_id);

        // Use health_weighted selection; fall back to the supplied node_id.
        let selected = self
            .credential_manager
            .balancer
            .select_node("health_weighted")
            .unwrap_or_else(|| node_id.to_owned());

        self.credential_manager
            .balancer
            .record_connection(&selected, &cred_id)
            .ok()
    }

    /// Simulate a data transfer on an open connection.
    ///
    /// Returns `true` when the connection exists and the update succeeds.
    pub fn transfer_data(&mut self, connection_id: &str, data: &[u8]) -> bool {
        if !self
            .credential_manager
            .balancer
            .active_connections
            .contains_key(connection_id)
        {
            return false;
        }
        self.credential_manager.balancer.update_connection_stats(
            connection_id,
            data.len() as i64,
            1.0, // synthetic 1 ms latency per transfer
            false,
        );
        true
    }

    /// Close an open connection.
    pub fn close_connection(&mut self, connection_id: &str) -> Result<()> {
        self.credential_manager
            .balancer
            .close_connection(connection_id)
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// §5  Tests
// ─────────────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::NamedTempFile;

    fn temp_db() -> String {
        NamedTempFile::new().unwrap().path().to_string_lossy().to_string()
    }

    #[test]
    fn test_register_and_select_node() {
        let db = temp_db();
        let mut balancer = ENENodeBalancer::new(&db).unwrap();
        balancer.register_node("node-A", "cred-1").unwrap();
        balancer.register_node("node-B", "cred-2").unwrap();

        // round_robin always returns the first sorted node.
        let selected = balancer.select_node("round_robin").unwrap();
        assert_eq!(selected, "node-A");
    }

    #[test]
    fn test_record_and_close_connection() {
        let db = temp_db();
        let mut balancer = ENENodeBalancer::new(&db).unwrap();
        balancer.register_node("n1", "c1").unwrap();
        let conn_id = balancer.record_connection("n1", "c1").unwrap();
        assert_eq!(conn_id.len(), 16);
        balancer.close_connection(&conn_id).unwrap();
        assert!(!balancer.active_connections.contains_key(&conn_id));
    }

    #[test]
    fn test_health_check_improves_score() {
        let db = temp_db();
        let mut balancer = ENENodeBalancer::new(&db).unwrap();
        balancer.register_node("n2", "c2").unwrap();
        // Initial error_rate is 0.0, so health should improve.
        let healthy = balancer.health_check("n2").unwrap();
        assert!(healthy);
        let score = balancer.get_node_stats("n2").unwrap().health_score;
        assert!(score > 1.0 - 1e-9, "score should be at ceiling 1.0; got {}", score);
    }

    #[test]
    fn test_credential_lifecycle() {
        let db = temp_db();
        let mut mgr = ENECredentialManager::new(&db).unwrap();
        let payload = serde_json::json!({ "key": "secret123", "region": "us-east-1" });
        let cred = mgr.create_credential("aws", &payload, "restricted", vec!["node-1".into()]);

        assert!(!cred.credential_id.is_empty());
        assert_eq!(cred.provider, "aws");

        let retrieved = mgr.get_credential(&cred.credential_id).unwrap();
        assert_eq!(retrieved["key"], "secret123");

        let revoked = mgr.revoke_credential(&cred.credential_id);
        assert!(revoked);
        assert!(mgr.get_credential(&cred.credential_id).is_none());
    }

    #[test]
    fn test_cloud_bridge_connect_transfer_close() {
        let db = temp_db();
        let mut bridge = ENECloudBridge::new(&db).unwrap();
        let conn_id = bridge.connect_to_storage("s3", "node-x").unwrap();
        let ok = bridge.transfer_data(&conn_id, b"hello world");
        assert!(ok);
        bridge.close_connection(&conn_id).unwrap();
    }
}
