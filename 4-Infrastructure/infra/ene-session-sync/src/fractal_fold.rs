// fractal_fold.rs — Fractal Merkle tree encoding with SQLite and PostgreSQL backends.
//
// Port of ene_fractal_fold.py (895 lines) and ene_rds_fractal_fold.py (592 lines).
//
// requires sha2 = "0.10", hex = "0.4" in Cargo.toml
// requires base64 = "0.22" in Cargo.toml
#![allow(dead_code)]

use anyhow::{Context, Result};
use base64::engine::general_purpose::STANDARD as B64;
use base64::Engine as _;
use rusqlite::{params, Connection};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::path::Path;
use std::sync::Arc;
use std::time::{SystemTime, UNIX_EPOCH};

// ─────────────────────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────────────────────

/// Golden angle in radians: π * (3 - √5)
const GOLDEN_ANGLE: f64 = std::f64::consts::PI * (3.0 - 2.2360679774997896);

// ─────────────────────────────────────────────────────────────
// Gray-code helpers
// ─────────────────────────────────────────────────────────────

/// Standard binary-reflected Gray code.
pub fn gray_code(index: u64) -> u64 {
    index ^ (index >> 1)
}

/// Inverse Gray code — recover the original index from a Gray code word.
pub fn inverse_gray_code(mut code: u64) -> u64 {
    let mut mask = code >> 1;
    while mask != 0 {
        code ^= mask;
        mask >>= 1;
    }
    code
}

// ─────────────────────────────────────────────────────────────
// Golden-spiral geometry
// ─────────────────────────────────────────────────────────────

/// A point on the golden spiral associated with a leaf address.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GoldenSpiralPoint {
    pub address: u64,
    pub x: f64,
    pub y: f64,
    pub radius: f64,
    pub theta: f64,
    pub shell: f64,
}

/// Map a leaf address to its canonical point on the golden spiral.
pub fn golden_spiral_point(address: u64, level: u32) -> GoldenSpiralPoint {
    let n = (address as f64) + 1.0;
    let radius = n.sqrt();
    let theta = n * GOLDEN_ANGLE;
    let x = radius * theta.cos();
    let y = radius * theta.sin();
    let shell = (level as f64) * radius;
    GoldenSpiralPoint { address, x, y, radius, theta, shell }
}

/// Euclidean distance in the (x, y, shell) embedding space.
pub fn manifold_distance(a: &GoldenSpiralPoint, b: &GoldenSpiralPoint) -> f64 {
    let dx = a.x - b.x;
    let dy = a.y - b.y;
    let ds = a.shell - b.shell;
    (dx * dx + dy * dy + ds * ds).sqrt()
}

// ─────────────────────────────────────────────────────────────
// Hashing helpers
// ─────────────────────────────────────────────────────────────

/// SHA-256 of a UTF-8 string, returned as a lower-hex string.
pub fn sha256_text(s: &str) -> String {
    sha256_bytes(s.as_bytes())
}

/// SHA-256 of a byte slice, returned as a lower-hex string.
pub fn sha256_bytes(b: &[u8]) -> String {
    let mut h = Sha256::new();
    h.update(b);
    hex::encode(h.finalize())
}

// ─────────────────────────────────────────────────────────────
// Canonical JSON
// ─────────────────────────────────────────────────────────────

/// Recursively convert a `serde_json::Value` to one where every Object is
/// replaced by a BTreeMap so that keys are sorted before serialization.
fn sort_value(v: &Value) -> Value {
    match v {
        Value::Object(map) => {
            let sorted: BTreeMap<String, Value> =
                map.iter().map(|(k, val)| (k.clone(), sort_value(val))).collect();
            serde_json::to_value(sorted).unwrap_or(Value::Null)
        }
        Value::Array(arr) => Value::Array(arr.iter().map(sort_value).collect()),
        other => other.clone(),
    }
}

/// Produce a canonical (sorted-key) JSON string from any `serde_json::Value`.
pub fn canonical_json_value(v: &Value) -> String {
    serde_json::to_string(&sort_value(v)).unwrap_or_else(|_| "null".into())
}

/// Produce a canonical JSON string from a reference to a `serde_json::Value`.
pub fn canonical_json(v: &Value) -> String {
    canonical_json_value(v)
}

// ─────────────────────────────────────────────────────────────
// Data structures
// ─────────────────────────────────────────────────────────────

/// A single node in the fractal Merkle tree.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FractalNode {
    /// SHA-256 of the node's canonical content.
    pub node_hash: String,
    /// `"leaf"` or `"parent"`.
    pub kind: String,
    /// Tree level (0 = leaf).
    pub level: u32,
    /// Ordinal index within this level.
    pub ordinal: u64,
    /// Gray-coded fold address.
    pub fold_address: u64,
    /// Index of the first leaf covered by this node.
    pub start_leaf: u64,
    /// Index of the last leaf covered by this node (inclusive).
    pub end_leaf: u64,
    /// Byte size of the payload for leaf nodes.
    pub size_bytes: usize,
    /// Hashes of child nodes (parent nodes only).
    pub children: Vec<String>,
    /// Base-64-encoded chunk payload (leaf nodes only).
    pub payload_b64: Option<String>,
}

/// Top-level descriptor for a fractal-encoded object.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FractalManifest {
    /// Root node hash.
    pub root_hash: String,
    /// Human-readable name (e.g. filename).
    pub name: String,
    /// Total byte length of the original data.
    pub byte_len: usize,
    /// Number of leaf chunks.
    pub leaves_count: usize,
    /// Tree depth (0 means a single leaf).
    pub depth: u32,
    /// Chunk size used when splitting the data.
    pub chunk_size: usize,
    /// Fan-out factor at each internal node.
    pub branching_factor: usize,
    /// ISO-8601 UTC creation timestamp.
    pub created_at: String,
    /// SHA-256 receipt over the manifest's canonical JSON.
    pub receipt: String,
}

// ─────────────────────────────────────────────────────────────
// Tree-building helpers
// ─────────────────────────────────────────────────────────────

/// Build a leaf node from a data chunk.
pub fn make_leaf(chunk: &[u8], ordinal: u64) -> FractalNode {
    let payload_b64 = B64.encode(chunk);
    let fold_address = gray_code(ordinal);
    // Hash = SHA-256(canonical JSON of {kind, ordinal, payload_b64})
    let content = json!({
        "kind": "leaf",
        "ordinal": ordinal,
        "payload_b64": payload_b64,
    });
    let node_hash = sha256_text(&canonical_json_value(&content));
    FractalNode {
        node_hash,
        kind: "leaf".into(),
        level: 0,
        ordinal,
        fold_address,
        start_leaf: ordinal,
        end_leaf: ordinal,
        size_bytes: chunk.len(),
        children: Vec::new(),
        payload_b64: Some(payload_b64),
    }
}

/// Build a parent node from a slice of child nodes.
pub fn make_parent(children: &[FractalNode], level: u32, ordinal: u64) -> FractalNode {
    let child_hashes: Vec<String> = children.iter().map(|c| c.node_hash.clone()).collect();
    let start_leaf = children.first().map(|c| c.start_leaf).unwrap_or(ordinal);
    let end_leaf = children.last().map(|c| c.end_leaf).unwrap_or(ordinal);
    let size_bytes: usize = children.iter().map(|c| c.size_bytes).sum();
    let fold_address = gray_code(ordinal);
    let content = json!({
        "kind": "parent",
        "level": level,
        "ordinal": ordinal,
        "children": child_hashes,
    });
    let node_hash = sha256_text(&canonical_json_value(&content));
    FractalNode {
        node_hash,
        kind: "parent".into(),
        level,
        ordinal,
        fold_address,
        start_leaf,
        end_leaf,
        size_bytes,
        children: child_hashes,
        payload_b64: None,
    }
}

// ─────────────────────────────────────────────────────────────
// Core encoding
// ─────────────────────────────────────────────────────────────

/// Encode pre-split chunks into a fractal Merkle tree.
///
/// Returns `(manifest, all_nodes_in_level_order)`.
pub fn encode_fractal_chunks(
    chunks: Vec<Vec<u8>>,
    name: &str,
    chunk_size: usize,
    branching_factor: usize,
) -> Result<(FractalManifest, Vec<FractalNode>)> {
    anyhow::ensure!(branching_factor >= 2, "branching_factor must be >= 2");
    anyhow::ensure!(!chunks.is_empty(), "chunks must not be empty");

    let byte_len: usize = chunks.iter().map(|c| c.len()).sum();
    let leaves_count = chunks.len();

    // Level 0 — leaf nodes
    let mut level_nodes: Vec<FractalNode> =
        chunks.iter().enumerate().map(|(i, c)| make_leaf(c, i as u64)).collect();
    let mut all_nodes: Vec<FractalNode> = level_nodes.clone();

    let mut depth: u32 = 0;
    let mut level_ordinal: u64 = 0;

    // Build parent levels until one root node remains.
    while level_nodes.len() > 1 {
        depth += 1;
        let mut parents: Vec<FractalNode> = Vec::new();
        for chunk_start in (0..level_nodes.len()).step_by(branching_factor) {
            let chunk_end = (chunk_start + branching_factor).min(level_nodes.len());
            let child_slice = &level_nodes[chunk_start..chunk_end];
            parents.push(make_parent(child_slice, depth, level_ordinal));
            level_ordinal += 1;
        }
        all_nodes.extend(parents.clone());
        level_nodes = parents;
    }

    let root = level_nodes.into_iter().next().context("tree has no root")?;
    let root_hash = root.node_hash.clone();
    let created_at = chrono::Utc::now().format("%Y-%m-%dT%H:%M:%S").to_string();

    // Build manifest (receipt = sha256 of canonical JSON of the manifest sans receipt field)
    let pre_receipt = json!({
        "root_hash": root_hash,
        "name": name,
        "byte_len": byte_len,
        "leaves_count": leaves_count,
        "depth": depth,
        "chunk_size": chunk_size,
        "branching_factor": branching_factor,
        "created_at": created_at,
    });
    let receipt = sha256_text(&canonical_json_value(&pre_receipt));

    let manifest = FractalManifest {
        root_hash,
        name: name.to_string(),
        byte_len,
        leaves_count,
        depth,
        chunk_size,
        branching_factor,
        created_at,
        receipt,
    };

    Ok((manifest, all_nodes))
}

/// Split `data` into `chunk_size`-byte chunks and encode as a fractal tree.
pub fn encode_fractal(
    data: &[u8],
    name: &str,
    chunk_size: usize,
    branching_factor: usize,
) -> Result<(FractalManifest, Vec<FractalNode>)> {
    anyhow::ensure!(chunk_size > 0, "chunk_size must be > 0");
    let chunks: Vec<Vec<u8>> = if data.is_empty() {
        vec![Vec::new()]
    } else {
        data.chunks(chunk_size).map(|c| c.to_vec()).collect()
    };
    encode_fractal_chunks(chunks, name, chunk_size, branching_factor)
}

// ─────────────────────────────────────────────────────────────
// Archive record / JSONL event helpers
// ─────────────────────────────────────────────────────────────

/// Build a JSON archive record from a manifest.
pub fn archive_record(manifest: &FractalManifest) -> Value {
    json!({
        "schema": "fractal_fold_v1",
        "root_hash": manifest.root_hash,
        "name": manifest.name,
        "byte_len": manifest.byte_len,
        "leaves_count": manifest.leaves_count,
        "depth": manifest.depth,
        "chunk_size": manifest.chunk_size,
        "branching_factor": manifest.branching_factor,
        "created_at": manifest.created_at,
        "receipt": manifest.receipt,
    })
}

/// Build a JSONL event envelope from an archive record and manifest.
pub fn jsonl_event(record: &Value, manifest: &FractalManifest) -> Value {
    let now_secs = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs() as i64;
    json!({
        "event": "fractal_fold_put",
        "root_hash": manifest.root_hash,
        "name": manifest.name,
        "timestamp": now_secs,
        "record": record,
    })
}

// ─────────────────────────────────────────────────────────────
// Utility — current Unix timestamp
// ─────────────────────────────────────────────────────────────

fn now_secs() -> i64 {
    SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs() as i64
}

fn now_iso() -> String {
    chrono::Utc::now().format("%Y-%m-%dT%H:%M:%S").to_string()
}

// ─────────────────────────────────────────────────────────────
// ENEFractalFold — SQLite backend
// ─────────────────────────────────────────────────────────────

/// Fractal-fold store backed by a SQLite database.
pub struct ENEFractalFold {
    conn: Connection,
}

impl ENEFractalFold {
    /// Open (or create) the SQLite database at `db_path`.
    pub fn new(db_path: impl AsRef<Path>) -> Result<Self> {
        let conn = Connection::open(db_path).context("open fractal_fold SQLite db")?;
        // Enable WAL for concurrent readers.
        conn.execute_batch("PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;")
            .context("set SQLite pragmas")?;
        let me = Self { conn };
        me.init_db()?;
        Ok(me)
    }

    /// Create the required tables if they do not already exist.
    pub fn init_db(&self) -> Result<()> {
        self.conn.execute_batch(r#"
CREATE TABLE IF NOT EXISTS ene_fractal_manifolds (
    root_hash         TEXT    PRIMARY KEY,
    name              TEXT    NOT NULL,
    byte_len          INTEGER NOT NULL,
    leaves_count      INTEGER NOT NULL,
    depth             INTEGER NOT NULL,
    chunk_size        INTEGER NOT NULL,
    branching_factor  INTEGER NOT NULL,
    created_at        TEXT    NOT NULL,
    receipt           TEXT    NOT NULL,
    stored_at         INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS ene_fractal_nodes (
    node_hash    TEXT    PRIMARY KEY,
    root_hash    TEXT    NOT NULL REFERENCES ene_fractal_manifolds(root_hash) ON DELETE CASCADE,
    kind         TEXT    NOT NULL,
    level        INTEGER NOT NULL,
    ordinal      INTEGER NOT NULL,
    fold_address INTEGER NOT NULL,
    start_leaf   INTEGER NOT NULL,
    end_leaf     INTEGER NOT NULL,
    size_bytes   INTEGER NOT NULL,
    children_json TEXT   NOT NULL DEFAULT '[]',
    payload_b64  TEXT
);

CREATE TABLE IF NOT EXISTS ene_fractal_graph_entities (
    entity_id    TEXT    PRIMARY KEY,
    root_hash    TEXT    NOT NULL REFERENCES ene_fractal_manifolds(root_hash) ON DELETE CASCADE,
    kind         TEXT    NOT NULL,
    data_json    TEXT    NOT NULL,
    created_at   INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_fractal_nodes_root
    ON ene_fractal_nodes(root_hash);
CREATE INDEX IF NOT EXISTS idx_fractal_nodes_level
    ON ene_fractal_nodes(root_hash, level);
CREATE INDEX IF NOT EXISTS idx_fractal_graph_root
    ON ene_fractal_graph_entities(root_hash);
        "#).context("init fractal_fold tables")?;
        Ok(())
    }

    // ── persist helpers ──────────────────────────────────────

    fn save_manifest(&self, m: &FractalManifest) -> Result<()> {
        self.conn.execute(
            "INSERT OR REPLACE INTO ene_fractal_manifolds \
             (root_hash, name, byte_len, leaves_count, depth, chunk_size, \
              branching_factor, created_at, receipt, stored_at) \
             VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9,?10)",
            params![
                m.root_hash, m.name, m.byte_len as i64, m.leaves_count as i64,
                m.depth as i64, m.chunk_size as i64, m.branching_factor as i64,
                m.created_at, m.receipt, now_secs(),
            ],
        ).context("insert manifest")?;
        Ok(())
    }

    fn save_node(&self, n: &FractalNode, root_hash: &str) -> Result<()> {
        let children_json = serde_json::to_string(&n.children)?;
        self.conn.execute(
            "INSERT OR IGNORE INTO ene_fractal_nodes \
             (node_hash, root_hash, kind, level, ordinal, fold_address, \
              start_leaf, end_leaf, size_bytes, children_json, payload_b64) \
             VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11)",
            params![
                n.node_hash, root_hash, n.kind, n.level as i64, n.ordinal as i64,
                n.fold_address as i64, n.start_leaf as i64, n.end_leaf as i64,
                n.size_bytes as i64, children_json, n.payload_b64,
            ],
        ).context("insert node")?;
        Ok(())
    }

    // ── row → Value helper ───────────────────────────────────

    fn manifest_row_to_value(
        root_hash: &str, name: &str, byte_len: i64, leaves_count: i64,
        depth: i64, chunk_size: i64, branching_factor: i64,
        created_at: &str, receipt: &str, stored_at: i64,
    ) -> Value {
        json!({
            "root_hash": root_hash,
            "name": name,
            "byte_len": byte_len,
            "leaves_count": leaves_count,
            "depth": depth,
            "chunk_size": chunk_size,
            "branching_factor": branching_factor,
            "created_at": created_at,
            "receipt": receipt,
            "stored_at": stored_at,
        })
    }

    // ── public API ───────────────────────────────────────────

    /// Encode and persist `data`.  Returns a JSONL event JSON value.
    pub fn put(
        &self,
        data: &[u8],
        name: &str,
        chunk_size: usize,
        branching_factor: usize,
    ) -> Result<Value> {
        let (manifest, nodes) = encode_fractal(data, name, chunk_size, branching_factor)
            .context("encode_fractal")?;
        self.save_manifest(&manifest)?;
        for node in &nodes {
            self.save_node(node, &manifest.root_hash)?;
        }
        let rec = archive_record(&manifest);
        let event = jsonl_event(&rec, &manifest);
        Ok(event)
    }

    /// Retrieve manifest metadata by root hash.
    pub fn manifest_get(&self, root_hash: &str) -> Result<Option<Value>> {
        let mut stmt = self.conn.prepare(
            "SELECT root_hash, name, byte_len, leaves_count, depth, \
                    chunk_size, branching_factor, created_at, receipt, stored_at \
             FROM ene_fractal_manifolds WHERE root_hash = ?1",
        )?;
        let mut rows = stmt.query(params![root_hash])?;
        if let Some(row) = rows.next()? {
            let v = Self::manifest_row_to_value(
                &row.get::<_, String>(0)?,
                &row.get::<_, String>(1)?,
                row.get(2)?, row.get(3)?, row.get(4)?,
                row.get(5)?, row.get(6)?,
                &row.get::<_, String>(7)?,
                &row.get::<_, String>(8)?,
                row.get(9)?,
            );
            Ok(Some(v))
        } else {
            Ok(None)
        }
    }

    /// Build a Merkle proof path from the root to a given leaf index.
    pub fn proof(&self, root_hash: &str, leaf_index: u64) -> Result<Value> {
        // Load all nodes for this tree.
        let mut stmt = self.conn.prepare(
            "SELECT node_hash, kind, level, ordinal, fold_address, \
                    start_leaf, end_leaf, size_bytes, children_json, payload_b64 \
             FROM ene_fractal_nodes WHERE root_hash = ?1 ORDER BY level DESC",
        )?;
        let mut rows = stmt.query(params![root_hash])?;
        let mut nodes: Vec<Value> = Vec::new();
        while let Some(row) = rows.next()? {
            let children_json: String = row.get(8)?;
            let children: Vec<String> = serde_json::from_str(&children_json).unwrap_or_default();
            nodes.push(json!({
                "node_hash": row.get::<_,String>(0)?,
                "kind": row.get::<_,String>(1)?,
                "level": row.get::<_,i64>(2)?,
                "ordinal": row.get::<_,i64>(3)?,
                "fold_address": row.get::<_,i64>(4)?,
                "start_leaf": row.get::<_,i64>(5)?,
                "end_leaf": row.get::<_,i64>(6)?,
                "size_bytes": row.get::<_,i64>(7)?,
                "children": children,
                "payload_b64": row.get::<_,Option<String>>(9)?,
            }));
        }

        // Walk from root down, collecting the chain of nodes that contain leaf_index.
        let mut path: Vec<Value> = Vec::new();
        for node in &nodes {
            let start = node["start_leaf"].as_u64().unwrap_or(0);
            let end = node["end_leaf"].as_u64().unwrap_or(0);
            if leaf_index >= start && leaf_index <= end {
                path.push(node.clone());
            }
        }
        // Sort path by level ascending (leaf first).
        path.sort_by_key(|n| n["level"].as_i64().unwrap_or(0));

        Ok(json!({
            "root_hash": root_hash,
            "leaf_index": leaf_index,
            "proof_path": path,
            "length": path.len(),
        }))
    }

    /// Verify hash consistency of the entire tree.
    pub fn verify(&self, root_hash: &str) -> Result<Value> {
        let mut stmt = self.conn.prepare(
            "SELECT node_hash, kind, level, ordinal, children_json, payload_b64 \
             FROM ene_fractal_nodes WHERE root_hash = ?1",
        )?;
        let mut rows = stmt.query(params![root_hash])?;

        let mut ok_count: u64 = 0;
        let mut bad_count: u64 = 0;
        let mut bad_hashes: Vec<String> = Vec::new();

        while let Some(row) = rows.next()? {
            let stored_hash: String = row.get(0)?;
            let kind: String = row.get(1)?;
            let level: i64 = row.get(2)?;
            let ordinal: i64 = row.get(3)?;
            let children_json: String = row.get(4)?;
            let payload_b64: Option<String> = row.get(5)?;
            let children: Vec<String> =
                serde_json::from_str(&children_json).unwrap_or_default();

            // Re-compute expected hash.
            let expected = if kind == "leaf" {
                let pb = payload_b64.as_deref().unwrap_or("");
                let content = json!({
                    "kind": "leaf",
                    "ordinal": ordinal,
                    "payload_b64": pb,
                });
                sha256_text(&canonical_json_value(&content))
            } else {
                let content = json!({
                    "kind": "parent",
                    "level": level,
                    "ordinal": ordinal,
                    "children": children,
                });
                sha256_text(&canonical_json_value(&content))
            };

            if expected == stored_hash {
                ok_count += 1;
            } else {
                bad_count += 1;
                bad_hashes.push(stored_hash.clone());
            }
        }

        Ok(json!({
            "root_hash": root_hash,
            "ok_count": ok_count,
            "bad_count": bad_count,
            "valid": bad_count == 0,
            "bad_hashes": bad_hashes,
        }))
    }

    /// List all stored manifests.
    pub fn list_manifests(&self) -> Result<Vec<Value>> {
        let mut stmt = self.conn.prepare(
            "SELECT root_hash, name, byte_len, leaves_count, depth, \
                    chunk_size, branching_factor, created_at, receipt, stored_at \
             FROM ene_fractal_manifolds ORDER BY stored_at DESC",
        )?;
        let mut rows = stmt.query([])?;
        let mut result = Vec::new();
        while let Some(row) = rows.next()? {
            result.push(Self::manifest_row_to_value(
                &row.get::<_, String>(0)?,
                &row.get::<_, String>(1)?,
                row.get(2)?, row.get(3)?, row.get(4)?,
                row.get(5)?, row.get(6)?,
                &row.get::<_, String>(7)?,
                &row.get::<_, String>(8)?,
                row.get(9)?,
            ));
        }
        Ok(result)
    }

    /// Delete a manifest and all its associated nodes (CASCADE).
    pub fn delete(&self, root_hash: &str) -> Result<Value> {
        let rows_deleted = self.conn.execute(
            "DELETE FROM ene_fractal_manifolds WHERE root_hash = ?1",
            params![root_hash],
        ).context("delete manifest")?;
        Ok(json!({
            "root_hash": root_hash,
            "deleted": rows_deleted > 0,
            "rows_deleted": rows_deleted,
        }))
    }
}

// ─────────────────────────────────────────────────────────────
// ENERdsFractalFold — PostgreSQL (async) backend
// ─────────────────────────────────────────────────────────────

/// Fractal-fold store backed by a PostgreSQL database (async, `tokio-postgres`).
pub struct ENERdsFractalFold {
    pg: Arc<tokio_postgres::Client>,
}

impl ENERdsFractalFold {
    /// Wrap an existing, connected `tokio_postgres::Client`.
    pub fn new(pg_client: Arc<tokio_postgres::Client>) -> Self {
        Self { pg: pg_client }
    }

    /// Create the `ene` schema and required tables if they do not exist.
    pub async fn init_tables(&self) -> Result<()> {
        self.pg
            .batch_execute("CREATE SCHEMA IF NOT EXISTS ene")
            .await
            .context("create ene schema")?;

        self.pg.batch_execute(r#"
CREATE TABLE IF NOT EXISTS ene.fractal_manifolds (
    root_hash         TEXT    PRIMARY KEY,
    name              TEXT    NOT NULL,
    byte_len          BIGINT  NOT NULL,
    leaves_count      BIGINT  NOT NULL,
    depth             INTEGER NOT NULL,
    chunk_size        INTEGER NOT NULL,
    branching_factor  INTEGER NOT NULL,
    created_at        TEXT    NOT NULL,
    receipt           TEXT    NOT NULL,
    stored_at         BIGINT  NOT NULL
);

CREATE TABLE IF NOT EXISTS ene.fractal_nodes (
    node_hash      TEXT    PRIMARY KEY,
    root_hash      TEXT    NOT NULL REFERENCES ene.fractal_manifolds(root_hash) ON DELETE CASCADE,
    kind           TEXT    NOT NULL,
    level          INTEGER NOT NULL,
    ordinal        BIGINT  NOT NULL,
    fold_address   BIGINT  NOT NULL,
    start_leaf     BIGINT  NOT NULL,
    end_leaf       BIGINT  NOT NULL,
    size_bytes     BIGINT  NOT NULL,
    children_json  TEXT    NOT NULL DEFAULT '[]',
    payload_b64    TEXT
);

CREATE TABLE IF NOT EXISTS ene.fractal_graph_entities (
    entity_id   TEXT    PRIMARY KEY,
    root_hash   TEXT    NOT NULL REFERENCES ene.fractal_manifolds(root_hash) ON DELETE CASCADE,
    kind        TEXT    NOT NULL,
    data_json   TEXT    NOT NULL,
    created_at  BIGINT  NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_rds_fractal_nodes_root
    ON ene.fractal_nodes(root_hash);
CREATE INDEX IF NOT EXISTS idx_rds_fractal_nodes_level
    ON ene.fractal_nodes(root_hash, level);
CREATE INDEX IF NOT EXISTS idx_rds_fractal_graph_root
    ON ene.fractal_graph_entities(root_hash);
        "#).await.context("init RDS fractal tables")?;
        Ok(())
    }

    // ── persist helpers ──────────────────────────────────────

    async fn save_manifest(&self, m: &FractalManifest) -> Result<()> {
        self.pg
            .execute(
                "INSERT INTO ene.fractal_manifolds \
                 (root_hash, name, byte_len, leaves_count, depth, chunk_size, \
                  branching_factor, created_at, receipt, stored_at) \
                 VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10) \
                 ON CONFLICT (root_hash) DO NOTHING",
                &[
                    &m.root_hash,
                    &m.name,
                    &(m.byte_len as i64),
                    &(m.leaves_count as i64),
                    &(m.depth as i32),
                    &(m.chunk_size as i32),
                    &(m.branching_factor as i32),
                    &m.created_at,
                    &m.receipt,
                    &now_secs(),
                ],
            )
            .await
            .context("insert RDS manifest")?;
        Ok(())
    }

    async fn save_node(&self, n: &FractalNode, root_hash: &str) -> Result<()> {
        let children_json = serde_json::to_string(&n.children)?;
        self.pg
            .execute(
                "INSERT INTO ene.fractal_nodes \
                 (node_hash, root_hash, kind, level, ordinal, fold_address, \
                  start_leaf, end_leaf, size_bytes, children_json, payload_b64) \
                 VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11) \
                 ON CONFLICT (node_hash) DO NOTHING",
                &[
                    &n.node_hash,
                    &root_hash.to_string(),
                    &n.kind,
                    &(n.level as i32),
                    &(n.ordinal as i64),
                    &(n.fold_address as i64),
                    &(n.start_leaf as i64),
                    &(n.end_leaf as i64),
                    &(n.size_bytes as i64),
                    &children_json,
                    &n.payload_b64,
                ],
            )
            .await
            .context("insert RDS node")?;
        Ok(())
    }

    // ── public async API ─────────────────────────────────────

    /// Encode and persist `data`.  Returns a JSONL event JSON value.
    pub async fn put(
        &self,
        data: &[u8],
        name: &str,
        chunk_size: usize,
        branching_factor: usize,
    ) -> Result<Value> {
        let (manifest, nodes) = encode_fractal(data, name, chunk_size, branching_factor)
            .context("encode_fractal")?;
        self.save_manifest(&manifest).await?;
        for node in &nodes {
            self.save_node(node, &manifest.root_hash).await?;
        }
        let rec = archive_record(&manifest);
        let event = jsonl_event(&rec, &manifest);
        Ok(event)
    }

    /// Retrieve manifest metadata by root hash.
    pub async fn manifest_get(&self, root_hash: &str) -> Result<Option<Value>> {
        let rows = self.pg
            .query(
                "SELECT root_hash, name, byte_len, leaves_count, depth, \
                        chunk_size, branching_factor, created_at, receipt, stored_at \
                 FROM ene.fractal_manifolds WHERE root_hash = $1",
                &[&root_hash.to_string()],
            )
            .await
            .context("manifest_get query")?;
        if let Some(row) = rows.into_iter().next() {
            let v = json!({
                "root_hash":        row.get::<_,String>(0),
                "name":             row.get::<_,String>(1),
                "byte_len":         row.get::<_,i64>(2),
                "leaves_count":     row.get::<_,i64>(3),
                "depth":            row.get::<_,i32>(4),
                "chunk_size":       row.get::<_,i32>(5),
                "branching_factor": row.get::<_,i32>(6),
                "created_at":       row.get::<_,String>(7),
                "receipt":          row.get::<_,String>(8),
                "stored_at":        row.get::<_,i64>(9),
            });
            Ok(Some(v))
        } else {
            Ok(None)
        }
    }

    /// Build a Merkle proof path from the root to a given leaf index.
    pub async fn proof(&self, root_hash: &str, leaf_index: u64) -> Result<Value> {
        let rows = self.pg
            .query(
                "SELECT node_hash, kind, level, ordinal, fold_address, \
                        start_leaf, end_leaf, size_bytes, children_json, payload_b64 \
                 FROM ene.fractal_nodes WHERE root_hash = $1 ORDER BY level DESC",
                &[&root_hash.to_string()],
            )
            .await
            .context("proof query")?;

        let mut path: Vec<Value> = Vec::new();
        for row in &rows {
            let start: i64 = row.get(5);
            let end: i64 = row.get(6);
            if leaf_index >= start as u64 && leaf_index <= end as u64 {
                let children_json: String = row.get(8);
                let children: Vec<String> =
                    serde_json::from_str(&children_json).unwrap_or_default();
                path.push(json!({
                    "node_hash":   row.get::<_,String>(0),
                    "kind":        row.get::<_,String>(1),
                    "level":       row.get::<_,i32>(2),
                    "ordinal":     row.get::<_,i64>(3),
                    "fold_address":row.get::<_,i64>(4),
                    "start_leaf":  start,
                    "end_leaf":    end,
                    "size_bytes":  row.get::<_,i64>(7),
                    "children":    children,
                    "payload_b64": row.get::<_,Option<String>>(9),
                }));
            }
        }
        path.sort_by_key(|n| n["level"].as_i64().unwrap_or(0));

        Ok(json!({
            "root_hash":  root_hash,
            "leaf_index": leaf_index,
            "proof_path": path,
            "length":     path.len(),
        }))
    }

    /// Verify hash consistency of every node in the tree.
    pub async fn verify(&self, root_hash: &str) -> Result<Value> {
        let rows = self.pg
            .query(
                "SELECT node_hash, kind, level, ordinal, children_json, payload_b64 \
                 FROM ene.fractal_nodes WHERE root_hash = $1",
                &[&root_hash.to_string()],
            )
            .await
            .context("verify query")?;

        let mut ok_count: u64 = 0;
        let mut bad_count: u64 = 0;
        let mut bad_hashes: Vec<String> = Vec::new();

        for row in &rows {
            let stored_hash: String = row.get(0);
            let kind: String = row.get(1);
            let level: i32 = row.get(2);
            let ordinal: i64 = row.get(3);
            let children_json: String = row.get(4);
            let payload_b64: Option<String> = row.get(5);
            let children: Vec<String> =
                serde_json::from_str(&children_json).unwrap_or_default();

            let expected = if kind == "leaf" {
                let pb = payload_b64.as_deref().unwrap_or("");
                let content = json!({
                    "kind": "leaf",
                    "ordinal": ordinal,
                    "payload_b64": pb,
                });
                sha256_text(&canonical_json_value(&content))
            } else {
                let content = json!({
                    "kind": "parent",
                    "level": level,
                    "ordinal": ordinal,
                    "children": children,
                });
                sha256_text(&canonical_json_value(&content))
            };

            if expected == stored_hash {
                ok_count += 1;
            } else {
                bad_count += 1;
                bad_hashes.push(stored_hash.clone());
            }
        }

        Ok(json!({
            "root_hash": root_hash,
            "ok_count":  ok_count,
            "bad_count": bad_count,
            "valid":     bad_count == 0,
            "bad_hashes": bad_hashes,
        }))
    }

    /// List all stored manifests, most recent first.
    pub async fn list_manifests(&self) -> Result<Vec<Value>> {
        let rows = self.pg
            .query(
                "SELECT root_hash, name, byte_len, leaves_count, depth, \
                        chunk_size, branching_factor, created_at, receipt, stored_at \
                 FROM ene.fractal_manifolds ORDER BY stored_at DESC",
                &[],
            )
            .await
            .context("list_manifests query")?;
        let result = rows
            .iter()
            .map(|row| json!({
                "root_hash":        row.get::<_,String>(0),
                "name":             row.get::<_,String>(1),
                "byte_len":         row.get::<_,i64>(2),
                "leaves_count":     row.get::<_,i64>(3),
                "depth":            row.get::<_,i32>(4),
                "chunk_size":       row.get::<_,i32>(5),
                "branching_factor": row.get::<_,i32>(6),
                "created_at":       row.get::<_,String>(7),
                "receipt":          row.get::<_,String>(8),
                "stored_at":        row.get::<_,i64>(9),
            }))
            .collect();
        Ok(result)
    }

    /// Delete a manifest and all its nodes (CASCADE).
    pub async fn delete(&self, root_hash: &str) -> Result<Value> {
        let n = self.pg
            .execute(
                "DELETE FROM ene.fractal_manifolds WHERE root_hash = $1",
                &[&root_hash.to_string()],
            )
            .await
            .context("delete RDS manifest")?;
        Ok(json!({
            "root_hash":    root_hash,
            "deleted":      n > 0,
            "rows_deleted": n,
        }))
    }
}
