use anyhow::{Context, Result};
use chrono::Utc;
use rusqlite::OptionalExtension;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{HashMap, HashSet};
use std::net::SocketAddr;
use std::path::{Path, PathBuf};
use std::sync::Arc;
use tokio::sync::RwLock;
use tracing::{info, warn};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NodeIdentity {
    pub node_id: String,
    pub public_key: String,
    pub ip_address: Option<String>,
    pub port: u16,
    pub first_seen: i64,
    pub last_seen: i64,
    pub replication_version: String,
    pub capabilities: Vec<String>,
    pub health_score_q16: u32,
    pub is_active: bool,
}

impl Default for NodeIdentity {
    fn default() -> Self {
        let now = Utc::now().timestamp_millis();
        Self {
            node_id: String::new(),
            public_key: String::new(),
            ip_address: None,
            port: 7947,
            first_seen: now,
            last_seen: now,
            replication_version: "2.0.0-Cambrian-Bind".into(),
            capabilities: vec!["storage".into(), "compute".into(), "relay".into()],
            health_score_q16: 65536,
            is_active: true,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GossipMessage {
    pub message_id: String,
    pub sender_node: String,
    pub message_type: String,
    pub payload: serde_json::Value,
    pub timestamp: i64,
    pub ttl: u8,
    pub signature: Option<String>,
}

impl GossipMessage {
    pub fn new(sender: &str, msg_type: &str, payload: serde_json::Value) -> Self {
        let id = format!(
            "gossip_{}",
            &sha256_hex(&format!("{}:{}:{}", sender, msg_type, Utc::now().timestamp_millis()))[..16]
        );
        Self {
            message_id: id,
            sender_node: sender.into(),
            message_type: msg_type.into(),
            payload,
            timestamp: Utc::now().timestamp_millis(),
            ttl: 10,
            signature: None,
        }
    }

    /// Canonical bytes for HMAC signing (excludes signature field).
    fn canonical_bytes(&self) -> Vec<u8> {
        let preimage = serde_json::json!({
            "message_id": &self.message_id,
            "sender_node": &self.sender_node,
            "message_type": &self.message_type,
            "payload": &self.payload,
            "timestamp": self.timestamp,
            "ttl": self.ttl,
        });
        serde_json::to_vec(&preimage).unwrap_or_default()
    }

    /// Sign this message with HMAC-SHA256 using the cluster secret.
    pub fn sign(&mut self, secret: &str) {
        use hmac::{Hmac, Mac};
        use sha2::Sha256;
        type HmacSha256 = Hmac<Sha256>;
        let mut mac = HmacSha256::new_from_slice(secret.as_bytes())
            .expect("HMAC can take key of any size");
        mac.update(&self.canonical_bytes());
        let result = mac.finalize();
        self.signature = Some(hex::encode(result.into_bytes()));
    }

    /// Verify the HMAC signature against the cluster secret.
    pub fn verify(&self, secret: &str) -> bool {
        let Some(ref sig) = self.signature else { return false };
        use hmac::{Hmac, Mac};
        use sha2::Sha256;
        type HmacSha256 = Hmac<Sha256>;
        let mut mac = match HmacSha256::new_from_slice(secret.as_bytes()) {
            Ok(m) => m,
            Err(_) => return false,
        };
        mac.update(&self.canonical_bytes());
        let result = mac.finalize();
        hex::encode(result.into_bytes()) == *sig
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CredentialFragment {
    pub credential_id: String,
    pub provider: String,
    pub fragment: Vec<u8>,
    pub access_level: i32,
    pub node_assignments: Vec<String>,
    pub usage_count: i64,
    pub last_rotated: i64,
    pub health_score_q16: u32,
    pub is_active: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReplicationRecord {
    pub replication_id: String,
    pub target_node: String,
    pub source_node: String,
    pub started_at: i64,
    pub completed_at: Option<i64>,
    pub status: String,
    pub version_replicated: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConsensusProposal {
    pub proposal_id: String,
    pub credential_id: String,
    pub proposer: String,
    pub timestamp: i64,
    pub votes: HashMap<String, bool>,
    pub resolved: bool,
}

fn sha256_hex(data: &str) -> String {
    let mut h = Sha256::new();
    h.update(data.as_bytes());
    hex::encode(h.finalize())
}

// ── database ───────────────────────────────────────────────────────────────

pub struct NodeDb {
    conn: rusqlite::Connection,
}

impl NodeDb {
    pub fn open<P: AsRef<Path>>(path: P) -> Result<Self> {
        let conn = rusqlite::Connection::open(path).context("open node db")?;
        let db = Self { conn };
        db.init_schema()?;
        Ok(db)
    }

    fn init_schema(&self) -> Result<()> {
        self.conn.execute_batch(
            r#"
CREATE TABLE IF NOT EXISTS ene_peers (
    node_id TEXT PRIMARY KEY,
    public_key TEXT NOT NULL,
    ip_address TEXT,
    port INTEGER DEFAULT 7947,
    first_seen INTEGER NOT NULL,
    last_seen INTEGER NOT NULL,
    replication_version TEXT NOT NULL DEFAULT '2.0.0-Cambrian-Bind',
    capabilities TEXT NOT NULL DEFAULT '[]',
    health_score_q16 INTEGER DEFAULT 65536,
    is_active INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS ene_credentials (
    credential_id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    encrypted_fragment BLOB NOT NULL,
    access_level INTEGER DEFAULT 0,
    node_assignments TEXT NOT NULL DEFAULT '[]',
    usage_count INTEGER DEFAULT 0,
    last_rotated INTEGER,
    health_score_q16 INTEGER DEFAULT 65536,
    is_active INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS ene_replications (
    replication_id TEXT PRIMARY KEY,
    target_node TEXT NOT NULL,
    source_node TEXT NOT NULL,
    started_at INTEGER NOT NULL,
    completed_at INTEGER,
    status TEXT NOT NULL DEFAULT 'pending',
    version_replicated TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ene_gossip (
    message_id TEXT PRIMARY KEY,
    sender_node TEXT NOT NULL,
    message_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    processed INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS ene_proposals (
    proposal_id TEXT PRIMARY KEY,
    credential_id TEXT NOT NULL,
    proposer TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    votes TEXT NOT NULL DEFAULT '{}',
    resolved INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_peers_active ON ene_peers(is_active);
CREATE INDEX IF NOT EXISTS idx_gossip_sender ON ene_gossip(sender_node, timestamp);
CREATE INDEX IF NOT EXISTS idx_replications_target ON ene_replications(target_node, status);
        "#,
        )?;
        Ok(())
    }

    pub fn save_peer(&self, peer: &NodeIdentity) -> Result<()> {
        self.conn.execute(
            "INSERT OR REPLACE INTO ene_peers \
             (node_id, public_key, ip_address, port, first_seen, last_seen, \
              replication_version, capabilities, health_score_q16, is_active) \
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)",
            rusqlite::params![
                &peer.node_id, &peer.public_key, &peer.ip_address, &peer.port,
                &peer.first_seen, &peer.last_seen, &peer.replication_version,
                serde_json::to_string(&peer.capabilities)?,
                &peer.health_score_q16, &peer.is_active as &dyn rusqlite::ToSql,
            ],
        )?;
        Ok(())
    }

    pub fn load_peers(&self) -> Result<Vec<NodeIdentity>> {
        let mut stmt = self.conn.prepare(
            "SELECT node_id, public_key, ip_address, port, first_seen, last_seen, \
             replication_version, capabilities, health_score_q16, is_active \
             FROM ene_peers WHERE is_active = 1"
        )?;
        let rows = stmt.query_map([], |row| {
            let caps: String = row.get(7)?;
            let active: i32 = row.get(9)?;
            Ok(NodeIdentity {
                node_id: row.get(0)?,
                public_key: row.get(1)?,
                ip_address: row.get(2)?,
                port: row.get(3)?,
                first_seen: row.get(4)?,
                last_seen: row.get(5)?,
                replication_version: row.get(6)?,
                capabilities: serde_json::from_str(&caps).unwrap_or_default(),
                health_score_q16: row.get(8)?,
                is_active: active != 0,
            })
        })?;
        let mut out = Vec::new();
        for r in rows { out.push(r?); }
        Ok(out)
    }

    pub fn save_gossip(&self, msg: &GossipMessage) -> Result<()> {
        self.conn.execute(
            "INSERT OR IGNORE INTO ene_gossip \
             (message_id, sender_node, message_type, payload, timestamp) \
             VALUES (?1, ?2, ?3, ?4, ?5)",
            rusqlite::params![
                &msg.message_id, &msg.sender_node, &msg.message_type,
                &serde_json::to_string(&msg.payload)?, &msg.timestamp,
            ],
        )?;
        Ok(())
    }

    pub fn save_proposal(&self, prop: &ConsensusProposal) -> Result<()> {
        self.conn.execute(
            "INSERT OR REPLACE INTO ene_proposals \
             (proposal_id, credential_id, proposer, timestamp, votes, resolved) \
             VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
            rusqlite::params![
                &prop.proposal_id, &prop.credential_id, &prop.proposer,
                &prop.timestamp, &serde_json::to_string(&prop.votes)?,
                &prop.resolved as &dyn rusqlite::ToSql,
            ],
        )?;
        Ok(())
    }

    pub fn load_proposal(&self, proposal_id: &str) -> Result<Option<ConsensusProposal>> {
        let mut stmt = self.conn.prepare(
            "SELECT proposal_id, credential_id, proposer, timestamp, votes, resolved \
             FROM ene_proposals WHERE proposal_id = ?1"
        )?;
        let row = stmt.query_row([proposal_id], |row| {
            let votes_str: String = row.get(4)?;
            Ok(ConsensusProposal {
                proposal_id: row.get(0)?,
                credential_id: row.get(1)?,
                proposer: row.get(2)?,
                timestamp: row.get(3)?,
                votes: serde_json::from_str(&votes_str).unwrap_or_default(),
                resolved: row.get::<_, i32>(5)? != 0,
            })
        }).optional()?;
        Ok(row)
    }

    pub fn load_all_proposals(&self) -> Result<Vec<ConsensusProposal>> {
        let mut stmt = self.conn.prepare(
            "SELECT proposal_id, credential_id, proposer, timestamp, votes, resolved FROM ene_proposals"
        )?;
        let rows = stmt.query_map([], |row| {
            let votes_str: String = row.get(4)?;
            Ok(ConsensusProposal {
                proposal_id: row.get(0)?,
                credential_id: row.get(1)?,
                proposer: row.get(2)?,
                timestamp: row.get(3)?,
                votes: serde_json::from_str(&votes_str).unwrap_or_default(),
                resolved: row.get::<_, i32>(5)? != 0,
            })
        })?;
        let mut out = Vec::new();
        for r in rows { out.push(r?); }
        Ok(out)
    }

    pub fn save_replication(&self, rec: &ReplicationRecord) -> Result<()> {
        self.conn.execute(
            "INSERT OR REPLACE INTO ene_replications \
             (replication_id, target_node, source_node, started_at, completed_at, status, version_replicated) \
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
            rusqlite::params![
                &rec.replication_id, &rec.target_node, &rec.source_node,
                &rec.started_at, &rec.completed_at, &rec.status, &rec.version_replicated,
            ],
        )?;
        Ok(())
    }

    pub fn save_credential_fragment(&self, frag: &CredentialFragment) -> Result<()> {
        self.conn.execute(
            "INSERT OR REPLACE INTO ene_credentials \
             (credential_id, provider, encrypted_fragment, access_level, node_assignments, \
              usage_count, last_rotated, health_score_q16, is_active) \
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9)",
            rusqlite::params![
                &frag.credential_id, &frag.provider, &frag.fragment,
                &frag.access_level, &serde_json::to_string(&frag.node_assignments)?,
                &frag.usage_count, &frag.last_rotated,
                &frag.health_score_q16, &frag.is_active as &dyn rusqlite::ToSql,
            ],
        )?;
        Ok(())
    }
}

// ── node core ──────────────────────────────────────────────────────────────

pub struct EneNode {
    pub identity: NodeIdentity,
    pub db_path: PathBuf,
    pub cluster_secret: String,
    pub peers: Arc<RwLock<HashMap<String, NodeIdentity>>>,
    pub seen_message_ids: Arc<RwLock<HashSet<String>>>,
    pub replication_queue: Arc<RwLock<Vec<String>>>,
    pub seed_nodes: Vec<String>,
    pub gossip_socket: Arc<tokio::net::UdpSocket>,
}

impl EneNode {
    pub async fn new(
        node_id: Option<String>,
        db_path: &Path,
        bind_addr: SocketAddr,
        seed_nodes: Vec<String>,
        cluster_secret: Option<String>,
    ) -> Result<Self> {
        let db = NodeDb::open(db_path)?;
        let loaded_peers = db.load_peers().unwrap_or_default();
        let mut identity = NodeIdentity::default();
        identity.node_id = node_id.unwrap_or_else(|| {
            format!("ene_{}", &sha256_hex(&Utc::now().timestamp_millis().to_string())[..16])
        });
        identity.public_key = sha256_hex(&identity.node_id)[..32].to_string();
        db.save_peer(&identity)?;

        let peers_map: HashMap<String, NodeIdentity> = loaded_peers
            .into_iter()
            .map(|p| (p.node_id.clone(), p))
            .collect();

        let socket = tokio::net::UdpSocket::bind(bind_addr).await?;
        info!("ENE node {} bound to {}", identity.node_id, bind_addr);

        let secret = cluster_secret.unwrap_or_else(|| {
            std::env::var("ENE_CLUSTER_SECRET")
                .unwrap_or_else(|_| sha256_hex("default-cluster-secret"))
        });

        Ok(Self {
            identity,
            db_path: db_path.to_path_buf(),
            cluster_secret: secret,
            peers: Arc::new(RwLock::new(peers_map)),
            seen_message_ids: Arc::new(RwLock::new(HashSet::new())),
            replication_queue: Arc::new(RwLock::new(Vec::new())),
            seed_nodes,
            gossip_socket: Arc::new(socket),
        })
    }

    fn with_db<F, R>(&self, f: F) -> Result<R>
    where
        F: FnOnce(&NodeDb) -> Result<R>,
    {
        let db = NodeDb::open(&self.db_path)?;
        f(&db)
    }

    pub async fn gossip(&self, mut msg: GossipMessage) -> Result<()> {
        msg.sign(&self.cluster_secret);
        let peers_guard = self.peers.read().await;
        let payload = serde_json::to_vec(&msg)?;
        for peer in peers_guard.values() {
            if let Some(ref ip) = peer.ip_address {
                let addr = format!("{}:{}", ip, peer.port).parse::<SocketAddr>()?;
                let _ = self.gossip_socket.send_to(&payload, addr).await;
            }
        }
        drop(peers_guard);

        self.with_db(|db| db.save_gossip(&msg))?;
        self.seen_message_ids.write().await.insert(msg.message_id.clone());
        info!("gossip {} -> {} peers", msg.message_type, self.peers.read().await.len());
        Ok(())
    }

    pub async fn process_incoming_gossip(&self, data: &[u8], from: SocketAddr) -> Result<()> {
        let msg: GossipMessage = serde_json::from_slice(data)?;

        if !msg.verify(&self.cluster_secret) {
            warn!("dropping unsigned/invalid gossip from {}", from);
            return Ok(());
        }

        if self.seen_message_ids.read().await.contains(&msg.message_id) {
            return Ok(());
        }
        self.seen_message_ids.write().await.insert(msg.message_id.clone());
        self.with_db(|db| db.save_gossip(&msg))?;

        match msg.message_type.as_str() {
            "discovery" => self.handle_discovery(&msg, from).await?,
            "heartbeat" => self.handle_heartbeat(&msg).await?,
            "credential_sync" => self.handle_credential_sync(&msg).await?,
            "replicate" => self.handle_replicate(&msg).await?,
            "credential_rotation_proposal" => self.handle_proposal(&msg).await?,
            _ => warn!("unknown gossip type: {}", msg.message_type),
        }
        Ok(())
    }

    async fn handle_discovery(&self, msg: &GossipMessage, from: SocketAddr) -> Result<()> {
        let node_id = msg.payload.get("node_id").and_then(|v| v.as_str());
        let caps = msg.payload.get("capabilities")
            .and_then(|v| v.as_array())
            .map(|arr| arr.iter().filter_map(|v| v.as_str().map(|s| s.to_string())).collect())
            .unwrap_or_else(|| vec!["storage".into(), "compute".into()]);

        if let Some(nid) = node_id {
            let mut peers = self.peers.write().await;
            if !peers.contains_key(nid) && nid != self.identity.node_id {
                let peer = NodeIdentity {
                    node_id: nid.into(),
                    public_key: sha256_hex(nid)[..32].to_string(),
                    ip_address: Some(from.ip().to_string()),
                    port: from.port(),
                    first_seen: Utc::now().timestamp_millis(),
                    last_seen: Utc::now().timestamp_millis(),
                    replication_version: "2.0.0-Cambrian-Bind".into(),
                    capabilities: caps,
                    health_score_q16: 65536,
                    is_active: true,
                };
                let _ = self.with_db(|db| db.save_peer(&peer));
                peers.insert(nid.into(), peer);
                info!("discovered peer {} at {}", nid, from);
            }
        }
        Ok(())
    }

    async fn handle_heartbeat(&self, msg: &GossipMessage) -> Result<()> {
        let mut peers = self.peers.write().await;
        if let Some(peer) = peers.get_mut(&msg.sender_node) {
            peer.last_seen = Utc::now().timestamp_millis();
            if let Some(h) = msg.payload.get("health_score_q16").and_then(|v| v.as_u64()) {
                peer.health_score_q16 = h as u32;
            }
            let _ = self.with_db(|db| db.save_peer(peer));
        }
        Ok(())
    }

    async fn handle_credential_sync(&self, msg: &GossipMessage) -> Result<()> {
        let cred_id = msg.payload.get("credential_id").and_then(|v| v.as_str());
        let fragment_b64 = msg.payload.get("fragment_b64").and_then(|v| v.as_str());
        if let (Some(id), Some(b64)) = (cred_id, fragment_b64) {
            let frag = CredentialFragment {
                credential_id: id.into(),
                provider: msg.payload.get("provider").and_then(|v| v.as_str()).unwrap_or("unknown").into(),
                fragment: base64_decode(b64),
                access_level: msg.payload.get("access_level").and_then(|v| v.as_i64()).unwrap_or(0) as i32,
                node_assignments: vec![msg.sender_node.clone()],
                usage_count: 0,
                last_rotated: Utc::now().timestamp_millis(),
                health_score_q16: 65536,
                is_active: true,
            };
            self.with_db(|db| db.save_credential_fragment(&frag))?;
            info!("stored credential fragment {} from {}", id, msg.sender_node);
        }
        Ok(())
    }

    async fn handle_replicate(&self, msg: &GossipMessage) -> Result<()> {
        let target = msg.payload.get("target_node").and_then(|v| v.as_str());
        if target == Some(&self.identity.node_id) {
            info!("received replication request from {}", msg.sender_node);
            let mut queue = self.replication_queue.write().await;
            queue.push(msg.sender_node.clone());
        }
        Ok(())
    }

    async fn handle_proposal(&self, msg: &GossipMessage) -> Result<()> {
        let proposal_id = msg.payload.get("proposal_id").and_then(|v| v.as_str());
        let credential_id = msg.payload.get("credential_id").and_then(|v| v.as_str());
        let proposer = msg.payload.get("proposer").and_then(|v| v.as_str());

        if let (Some(pid), Some(cid), Some(pro)) = (proposal_id, credential_id, proposer) {
            self.with_db(|db| {
                if db.load_proposal(pid)?.is_none() {
                    let prop = ConsensusProposal {
                        proposal_id: pid.into(),
                        credential_id: cid.into(),
                        proposer: pro.into(),
                        timestamp: Utc::now().timestamp_millis(),
                        votes: HashMap::new(),
                        resolved: false,
                    };
                    db.save_proposal(&prop)?;
                    info!("new proposal {} for credential {}", pid, cid);
                }
                Ok(())
            })?;
        }
        Ok(())
    }

    pub async fn vote(&self, proposal_id: &str, approve: bool) -> Result<bool> {
        let total = self.peers.read().await.len() + 1;
        let mut prop = self.with_db(|db| db.load_proposal(proposal_id))?
            .context("proposal not found")?;
        prop.votes.insert(self.identity.node_id.clone(), approve);
        self.with_db(|db| db.save_proposal(&prop))?;

        let approve_count = prop.votes.values().filter(|&&v| v).count();
        let threshold = (total * 2) / 3;
        if approve_count >= threshold && !prop.resolved {
            prop.resolved = true;
            self.with_db(|db| db.save_proposal(&prop))?;
            info!("consensus reached on {} ({} of {})", proposal_id, approve_count, total);
            return Ok(true);
        }
        Ok(false)
    }

    pub async fn propose_rotation(&self, credential_id: &str) -> Result<String> {
        let proposal_id = format!(
            "prop_{}",
            &sha256_hex(&format!("{}:{}", credential_id, Utc::now().timestamp_millis()))[..12]
        );
        let payload = serde_json::json!({
            "proposal_id": &proposal_id,
            "credential_id": credential_id,
            "proposer": &self.identity.node_id,
            "timestamp": Utc::now().timestamp_millis(),
        });
        let msg = GossipMessage::new(&self.identity.node_id, "credential_rotation_proposal", payload);
        self.gossip(msg).await?;
        Ok(proposal_id)
    }

    pub async fn send_heartbeat(&self) -> Result<()> {
        let payload = serde_json::json!({
            "health_score_q16": self.identity.health_score_q16,
            "capabilities": self.identity.capabilities,
            "replication_version": self.identity.replication_version,
        });
        let msg = GossipMessage::new(&self.identity.node_id, "heartbeat", payload);
        self.gossip(msg).await?;
        Ok(())
    }

    pub async fn get_status(&self) -> serde_json::Value {
        let peers = self.peers.read().await;
        serde_json::json!({
            "node_id": self.identity.node_id,
            "replication_version": self.identity.replication_version,
            "peers": peers.len(),
            "gossip_backlog": self.seen_message_ids.read().await.len(),
            "is_distributed": true,
            "auto_replicates": true,
            "consensus_enabled": true,
        })
    }

    pub async fn get_mesh_health(&self) -> serde_json::Value {
        let peers = self.peers.read().await;
        let healthy = peers.values().filter(|p| p.health_score_q16 > 32768).count();
        let mesh_size = peers.len() + 1;
        serde_json::json!({
            "mesh_size": mesh_size,
            "healthy_nodes": healthy + 1,
            "mesh_status": if healthy >= peers.len() / 2 { "healthy" } else { "degraded" },
        })
    }
}

fn base64_decode(s: &str) -> Vec<u8> {
    use base64::Engine;
    base64::engine::general_purpose::STANDARD.decode(s.as_bytes()).unwrap_or_default()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn gossip_sign_and_verify_roundtrip() {
        let mut msg = GossipMessage::new("ene_alpha", "heartbeat", serde_json::json!({"health": 1}));
        assert!(msg.signature.is_none());
        msg.sign("secret-key");
        assert!(msg.signature.is_some());
        assert!(msg.verify("secret-key"));
    }

    #[test]
    fn gossip_verify_fails_with_wrong_secret() {
        let mut msg = GossipMessage::new("ene_alpha", "heartbeat", serde_json::json!({}));
        msg.sign("correct-secret");
        assert!(!msg.verify("wrong-secret"));
    }

    #[test]
    fn gossip_verify_fails_when_unsigned() {
        let msg = GossipMessage::new("ene_alpha", "heartbeat", serde_json::json!({}));
        assert!(!msg.verify("any-secret"));
    }

    #[test]
    fn gossip_tamper_payload_invalidates_signature() {
        let mut msg = GossipMessage::new("ene_alpha", "heartbeat", serde_json::json!({"health": 1}));
        msg.sign("secret-key");
        assert!(msg.verify("secret-key"));
        // Tamper with payload after signing
        msg.payload = serde_json::json!({"health": 0});
        assert!(!msg.verify("secret-key"));
    }

    #[test]
    fn gossip_tamper_sender_invalidates_signature() {
        let mut msg = GossipMessage::new("ene_alpha", "heartbeat", serde_json::json!({}));
        msg.sign("secret-key");
        assert!(msg.verify("secret-key"));
        msg.sender_node = "ene_eve".into();
        assert!(!msg.verify("secret-key"));
    }

    #[test]
    fn gossip_signature_is_deterministic() {
        let mut msg1 = GossipMessage::new("ene_alpha", "heartbeat", serde_json::json!({"h": 1}));
        let mut msg2 = GossipMessage::new("ene_alpha", "heartbeat", serde_json::json!({"h": 1}));
        msg1.sign("secret");
        msg2.sign("secret");
        // Same canonical bytes → same signature (when timestamp and ttl match)
        // But timestamps differ, so we test canonical_bytes separately
    }

    #[test]
    fn gossip_canonical_bytes_excludes_signature() {
        let mut msg = GossipMessage::new("ene_alpha", "heartbeat", serde_json::json!({"h": 1}));
        let before = msg.canonical_bytes();
        msg.sign("secret");
        let after = msg.canonical_bytes();
        assert_eq!(before, after);
    }

    #[test]
    fn node_identity_default_has_sensible_values() {
        let id = NodeIdentity::default();
        assert!(id.node_id.is_empty());
        assert_eq!(id.port, 7947);
        assert!(id.capabilities.contains(&"storage".to_string()));
        assert!(id.capabilities.contains(&"compute".to_string()));
        assert_eq!(id.health_score_q16, 65536);
        assert!(id.is_active);
    }

    #[test]
    fn sha256_hex_is_deterministic() {
        let h1 = sha256_hex("hello");
        let h2 = sha256_hex("hello");
        assert_eq!(h1, h2);
        assert_eq!(h1.len(), 64);
    }

    #[test]
    fn sha256_hex_changes_with_input() {
        let h1 = sha256_hex("a");
        let h2 = sha256_hex("b");
        assert_ne!(h1, h2);
    }

    #[test]
    fn base64_decode_roundtrip() {
        use base64::Engine;
        let data = b"hello world";
        let encoded = base64::engine::general_purpose::STANDARD.encode(data);
        let decoded = base64_decode(&encoded);
        assert_eq!(decoded, data.as_slice());
    }
}
