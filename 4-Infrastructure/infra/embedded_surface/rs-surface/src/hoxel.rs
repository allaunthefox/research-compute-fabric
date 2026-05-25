/// Spatiotemporal RAM hoxel registry — RDS-backed memory manifold surface.
///
/// Every transition of data between (node, tier) pairs is recorded as a
/// memory hoxel.  Each hoxel carries:
///   - thermal score     (compute_thermal_signature() — 0..1)
///   - residual          (reconstruction error from the transition)
///   - witness hash      (SHA-256 of prior witness | canonical record)
///   - tx_seq            (globally monotonic IDENTITY from RDS)
///
/// The hoxel IS the computation unit.  Spinning up more nodes adds spatial
/// coordinates, increasing the total compute-in-flight capacity across the
/// memory manifold.
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::Digest as _;
use std::collections::BTreeMap;
use std::path::PathBuf;
use std::sync::Arc;
use tokio::fs::OpenOptions;
use tokio::io::AsyncWriteExt;
use tokio::sync::{Mutex, mpsc};

use tracing::{error, info, warn};

// ──────────────────────────────────────────────
// Types
// ──────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HoxelTransition {
    pub obj_key: String,
    pub bucket: String,
    pub from_node: Option<String>,
    pub from_tier: Option<String>,
    pub to_node: Option<String>,
    pub to_tier: String,
    pub spectral_mode: String,
    pub thermal_score: f64,
    pub residual: f64,
    pub payload_bytes: i64,
    pub density: Option<f64>,
    pub confidence: Option<f64>,
    pub semantic_load: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HoxelResponse {
    pub hoxel_id: String,
    pub tx_seq: i64,
    pub witness_hash: String,
    pub chain_prev: Option<String>,
    pub obj_key: String,
    pub bucket: String,
    pub from_node: Option<String>,
    pub from_tier: Option<String>,
    pub to_node: Option<String>,
    pub to_tier: String,
    pub spectral_mode: String,
    pub density: f64,
    pub confidence: f64,
    pub semantic_load: f64,
    pub thermal_score: f64,
    pub residual: f64,
    pub payload_bytes: i64,
    pub access_count: i32,
    pub created_ts: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HoxelQuery {
    pub node: Option<String>,
    pub tier: Option<String>,
    pub obj_key: Option<String>,
    pub thermal_min: Option<f64>,
    pub thermal_max: Option<f64>,
    pub semantic_min: Option<f64>,
    pub semantic_max: Option<f64>,
    pub since: Option<String>,
    pub limit: Option<i64>,
    pub offset: Option<i64>,
}

impl Default for HoxelQuery {
    fn default() -> Self {
        Self {
            node: None,
            tier: None,
            obj_key: None,
            thermal_min: None,
            thermal_max: None,
            semantic_min: None,
            semantic_max: None,
            since: None,
            limit: Some(100),
            offset: Some(0),
        }
    }
}

// ──────────────────────────────────────────────
// Witness chain computation
// ──────────────────────────────────────────────

fn sha256_hex(data: &[u8]) -> String {
    let mut h = sha2::Sha256::new();
    h.update(data);
    hex::encode(h.finalize())
}

fn canonical_json(v: &Value) -> String {
    fn sort_value(v: &Value) -> Value {
        match v {
            Value::Object(map) => {
                let sorted: BTreeMap<_, _> =
                    map.iter().map(|(k, v)| (k.clone(), sort_value(v))).collect();
                let mut out = serde_json::Map::new();
                for (k, v) in sorted {
                    out.insert(k, v);
                }
                Value::Object(out)
            }
            Value::Array(arr) => Value::Array(arr.iter().map(sort_value).collect()),
            other => other.clone(),
        }
    }
    serde_json::to_string(&sort_value(v)).unwrap_or_default()
}

fn compute_witness(record: &HoxelTransition, prev_witness: Option<&str>) -> String {
    let preimage = json!({
        "obj_key": record.obj_key,
        "bucket": record.bucket,
        "from_node": record.from_node,
        "from_tier": record.from_tier,
        "to_node": record.to_node,
        "to_tier": record.to_tier,
        "spectral_mode": record.spectral_mode,
        "thermal_score": record.thermal_score,
        "residual": record.residual,
        "payload_bytes": record.payload_bytes,
        "prev_witness": prev_witness,
    });
    let canonical = canonical_json(&preimage);
    sha256_hex(canonical.as_bytes())
}

fn iso_utc_now() -> String {
    let secs = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();
    let s = secs % 86400;
    let d = secs / 86400;
    let h = s / 3600;
    let m = (s % 3600) / 60;
    let sec = s % 60;
    let days_400 = d / 146097;
    let rem = d % 146097;
    let days_100 = rem.min(3 * 36524) / 36524;
    let rem = rem - days_100 * 36524;
    let days_4 = rem / 1461;
    let rem = rem % 1461;
    let days_1 = rem.min(3 * 365) / 365;
    let rem = rem - days_1 * 365;
    let year = days_400 * 400 + days_100 * 100 + days_4 * 4 + days_1 + 1970;
    let leap = (days_1 == 3) && (days_4 != 24 || days_100 == 3);
    let dim: [u64; 12] = [
        31,
        if leap { 29 } else { 28 },
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    ];
    let mut month = 12u64;
    let mut day_rem = rem;
    for (i, &days) in dim.iter().enumerate() {
        if day_rem < days {
            month = i as u64 + 1;
            break;
        }
        day_rem -= days;
    }
    format!("{:04}-{:02}-{:02}T{:02}:{:02}:{:02}Z", year, month, day_rem + 1, h, m, sec)
}

// ──────────────────────────────────────────────
// HoxelStore — dual-backend: RDS + local JSONL
// ──────────────────────────────────────────────

#[derive(Clone)]
pub struct HoxelStore {
    pg: Option<Arc<Mutex<tokio_postgres::Client>>>,
    jsonl_tx: mpsc::UnboundedSender<String>,
}

impl HoxelStore {
    /// Create a new HoxelStore with optional PostgreSQL backend.
    ///
    /// When `pg_client` is Some, all reads/writes go through RDS.
    /// Regardless, every recorded transition is also written to a local
    /// JSONL file for offline resilience.
    pub fn new(pg_client: Option<tokio_postgres::Client>) -> Self {
        let (jsonl_tx, mut receiver) = mpsc::unbounded_channel::<String>();

        let log_path = std::env::var("RS_HOXEL_LOG_PATH")
            .map(PathBuf::from)
            .unwrap_or_else(|_| PathBuf::from("/var/log/rs-surface/hoxel.jsonl"));

        tokio::spawn(async move {
            if let Some(parent) = log_path.parent() {
                if let Err(e) = tokio::fs::create_dir_all(parent).await {
                    warn!("hoxel jsonl mkdir failed: {}", e);
                }
            }
            let mut file = match OpenOptions::new()
                .create(true)
                .append(true)
                .open(&log_path)
                .await
            {
                Ok(f) => f,
                Err(e) => {
                    warn!("hoxel jsonl open failed: {} — logging to stderr only", e);
                    while let Some(line) = receiver.recv().await {
                        eprintln!("[HOXEL] {}", line.trim_end());
                    }
                    return;
                }
            };
            while let Some(line) = receiver.recv().await {
                if let Err(e) = file.write_all(line.as_bytes()).await {
                    error!("hoxel jsonl write failed: {}", e);
                }
                let _ = file.sync_all().await;
            }
        });

        let store = Self {
            pg: pg_client.map(|c| Arc::new(Mutex::new(c))),
            jsonl_tx,
        };

        if store.pg.is_some() {
            info!("hoxel store: connected to PostgreSQL (RDS)");
        } else {
            warn!("hoxel store: no PostgreSQL — local JSONL only (no global ordering)");
        }

        store
    }

    /// Record a hoxel transition and return the witness envelope.
    pub async fn record_transition(&self, record: &HoxelTransition) -> Result<HoxelResponse, String> {
        let density = record.density.unwrap_or(1.0);
        let confidence = record.confidence.unwrap_or(1.0);
        let semantic_load = record.semantic_load.unwrap_or(0.0);

        // Look up previous witness for this obj_key to build the chain.
        let prev_witness = self
            .get_latest_witness(&record.obj_key)
            .await
            .unwrap_or(None);

        let witness_hash = compute_witness(record, prev_witness.as_deref());

        if let Some(ref pg_arc) = self.pg {
            let pg = pg_arc.lock().await;
            let rows = pg
                .query_one(
                    "INSERT INTO hoxel_store.memory_hoxels \
                     (obj_key, bucket, from_node, from_tier, to_node, to_tier, \
                      spectral_mode, density, confidence, semantic_load, \
                      thermal_score, residual, payload_bytes, witness_hash) \
                     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14) \
                     RETURNING hoxel_id::TEXT, tx_seq, witness_hash, created_ts::TEXT",
                    &[
                        &record.obj_key,
                        &record.bucket,
                        &record.from_node,
                        &record.from_tier,
                        &record.to_node,
                        &record.to_tier,
                        &record.spectral_mode,
                        &density,
                        &confidence,
                        &semantic_load,
                        &record.thermal_score,
                        &record.residual,
                        &record.payload_bytes,
                        &witness_hash,
                    ],
                )
                .await
                .map_err(|e| format!("hoxel insert failed: {}", e))?;

            let hoxel_id: String = rows.get(0);
            let tx_seq: i64 = rows.get(1);
            let witness_hash_out: String = rows.get(2);
            let created_ts: String = rows.get(3);

            let response = HoxelResponse {
                hoxel_id: hoxel_id.clone(),
                tx_seq,
                witness_hash: witness_hash_out.clone(),
                chain_prev: prev_witness,
                obj_key: record.obj_key.clone(),
                bucket: record.bucket.clone(),
                from_node: record.from_node.clone(),
                from_tier: record.from_tier.clone(),
                to_node: record.to_node.clone(),
                to_tier: record.to_tier.clone(),
                spectral_mode: record.spectral_mode.clone(),
                density,
                confidence,
                semantic_load,
                thermal_score: record.thermal_score,
                residual: record.residual,
                payload_bytes: record.payload_bytes,
                access_count: 1,
                created_ts: created_ts.clone(),
            };

            // Also write to JSONL for offline backup.
            let line = serde_json::to_string(&response).unwrap_or_default() + "\n";
            let _ = self.jsonl_tx.send(line);

            return Ok(response);
        }

        // No RDS: generate a local-only response.
        let response = HoxelResponse {
            hoxel_id: format!("local-{}", &witness_hash[..16]),
            tx_seq: 0,
            witness_hash: witness_hash.clone(),
            chain_prev: prev_witness,
            obj_key: record.obj_key.clone(),
            bucket: record.bucket.clone(),
            from_node: record.from_node.clone(),
            from_tier: record.from_tier.clone(),
            to_node: record.to_node.clone(),
            to_tier: record.to_tier.clone(),
            spectral_mode: record.spectral_mode.clone(),
            density,
            confidence,
            semantic_load,
            thermal_score: record.thermal_score,
            residual: record.residual,
            payload_bytes: record.payload_bytes,
            access_count: 1,
            created_ts: iso_utc_now(),
        };

        let line = serde_json::to_string(&response).unwrap_or_default() + "\n";
        let _ = self.jsonl_tx.send(line);

        Ok(response)
    }

    /// Retrieve a single hoxel by its witness hash.
    pub async fn get_hoxel(&self, hoxel_id: &str) -> Result<HoxelResponse, String> {
        match self.pg {
            Some(ref pg_arc) => {
                let pg = pg_arc.lock().await;
                let rows = pg
                    .query_one(
                        "SELECT hoxel_id::TEXT, tx_seq, obj_key, bucket, \
                                from_node, from_tier, to_node, to_tier, \
                                spectral_mode, density, confidence, semantic_load, \
                                thermal_score, residual, payload_bytes, \
                                access_count, witness_hash, \
                                COALESCE(witness_prev::TEXT, NULL) as chain_prev, \
                                created_ts::TEXT \
                         FROM hoxel_store.memory_hoxels \
                         WHERE hoxel_id::TEXT = $1 OR witness_hash = $1",
                        &[&hoxel_id],
                    )
                    .await
                    .map_err(|e| format!("hoxel query failed: {}", e))?;

                Ok(map_row_to_response(&rows))
            }
            None => Err("no RDS connection — cannot query hoxels by ID".to_string()),
        }
    }

    /// Query hoxels with filters.
    ///
    /// Uses fixed SQL with NULL-coalescing parameters so no dynamic
    /// boxed-trait dispatch is needed.  Each filter becomes a
    /// "IS NULL OR match" clause at the SQL level.
    pub async fn query_hoxels(&self, query: &HoxelQuery) -> Result<Vec<HoxelResponse>, String> {
        match self.pg {
            Some(ref pg_arc) => {
                let pg = pg_arc.lock().await;

                // All parameters are Option<T> — NULL means "no filter".
                let node: Option<&str> = query.node.as_deref();
                let tier: Option<&str> = query.tier.as_deref();
                let obj_key: Option<&str> = query.obj_key.as_deref();
                let thermal_min: Option<f64> = query.thermal_min;
                let thermal_max: Option<f64> = query.thermal_max;
                let semantic_min: Option<f64> = query.semantic_min;
                let semantic_max: Option<f64> = query.semantic_max;
                let since: Option<&str> = query.since.as_deref();
                let limit: i64 = query.limit.unwrap_or(100);
                let offset: i64 = query.offset.unwrap_or(0);

                let rows = pg
                    .query(
                        "SELECT hoxel_id::TEXT, tx_seq, obj_key, bucket, \
                                from_node, from_tier, to_node, to_tier, \
                                spectral_mode, density, confidence, semantic_load, \
                                thermal_score, residual, payload_bytes, \
                                access_count, witness_hash, \
                                COALESCE(witness_prev::TEXT, NULL) as chain_prev, \
                                created_ts::TEXT \
                         FROM hoxel_store.memory_hoxels \
                          WHERE ($1::TEXT IS NULL OR to_node = $1 OR from_node = $1) \
                           AND ($2::TEXT IS NULL OR to_tier = $2) \
                           AND ($3::TEXT IS NULL OR obj_key = $3) \
                           AND ($4::DOUBLE PRECISION IS NULL OR thermal_score >= $4) \
                           AND ($5::DOUBLE PRECISION IS NULL OR thermal_score <= $5) \
                           AND ($6::DOUBLE PRECISION IS NULL OR semantic_load >= $6) \
                           AND ($7::DOUBLE PRECISION IS NULL OR semantic_load <= $7) \
                           AND ($8::TEXT IS NULL OR created_ts >= $8::TIMESTAMPTZ) \
                          ORDER BY created_ts DESC \
                          LIMIT $9 OFFSET $10",
                        &[
                            &node,
                            &tier,
                            &obj_key,
                            &thermal_min,
                            &thermal_max,
                            &semantic_min,
                            &semantic_max,
                            &since,
                            &limit,
                            &offset,
                        ],
                    )
                    .await
                    .map_err(|e| format!("hoxel query failed: {}", e))?;

                Ok(rows.iter().map(|row| map_row_to_response(row)).collect())
            }
            None => Err("no RDS connection — cannot query hoxels".to_string()),
        }
    }

    /// Get the latest witness hash for an obj_key (to chain the next transition).
    async fn get_latest_witness(&self, obj_key: &str) -> Option<Option<String>> {
        match self.pg {
            Some(ref pg_arc) => {
                let pg = pg_arc.lock().await;
                let result = pg
                    .query_opt(
                        "SELECT witness_hash FROM hoxel_store.memory_hoxels \
                         WHERE obj_key = $1 ORDER BY created_ts DESC LIMIT 1",
                        &[&obj_key],
                    )
                    .await;
                match result {
                    Ok(Some(row)) => {
                        let hash: String = row.get(0);
                        Some(Some(hash))
                    }
                    Ok(None) => Some(None),
                    Err(_) => None,
                }
            }
            None => None,
        }
    }

    /// Get inflight compute summary for the last N minutes.
    pub async fn inflight_summary(&self, window_minutes: i64) -> Result<Value, String> {
        match self.pg {
            Some(ref pg_arc) => {
                let pg = pg_arc.lock().await;

                // Main inflight stats
                let stats = pg
                    .query_one(
                        "SELECT COUNT(*)::BIGINT as inflight_count, \
                                COALESCE(SUM(payload_bytes), 0)::BIGINT as total_bytes, \
                                COUNT(DISTINCT COALESCE(to_node, 'unknown')) as node_count, \
                                COUNT(DISTINCT to_tier) as tier_count \
                         FROM hoxel_store.memory_hoxels \
                         WHERE created_ts > NOW() - ($1 || ' minutes')::INTERVAL",
                        &[&window_minutes.to_string()],
                    )
                    .await
                    .map_err(|e| format!("inflight query failed: {}", e))?;

                let inflight_count: i64 = stats.get(0);
                let total_bytes: i64 = stats.get(1);
                let node_count: i64 = stats.get(2);
                let tier_count: i64 = stats.get(3);

                // Active nodes
                let node_rows = pg
                    .query(
                        "SELECT DISTINCT to_node FROM hoxel_store.memory_hoxels \
                         WHERE created_ts > NOW() - ($1 || ' minutes')::INTERVAL \
                         AND to_node IS NOT NULL",
                        &[&window_minutes.to_string()],
                    )
                    .await
                    .map_err(|e| format!("inflight nodes query failed: {}", e))?;

                let active_nodes: Vec<String> = node_rows
                    .iter()
                    .filter_map(|r| r.get::<_, Option<String>>(0))
                    .collect();

                // Breakdown by tier
                let tier_rows = pg
                    .query(
                        "SELECT to_tier, COUNT(*)::BIGINT, COALESCE(SUM(payload_bytes), 0)::BIGINT \
                         FROM hoxel_store.memory_hoxels \
                         WHERE created_ts > NOW() - ($1 || ' minutes')::INTERVAL \
                         GROUP BY to_tier ORDER BY to_tier",
                        &[&window_minutes.to_string()],
                    )
                    .await
                    .map_err(|e| format!("inflight tier query failed: {}", e))?;

                let by_tier: Vec<Value> = tier_rows
                    .iter()
                    .map(|r| {
                        let tier: String = r.get(0);
                        let count: i64 = r.get(1);
                        let bytes: i64 = r.get(2);
                        json!({"tier": tier, "count": count, "bytes": bytes})
                    })
                    .collect();

                // Breakdown by spectral mode
                let mode_rows = pg
                    .query(
                        "SELECT spectral_mode, COUNT(*)::BIGINT, COALESCE(SUM(payload_bytes), 0)::BIGINT \
                         FROM hoxel_store.memory_hoxels \
                         WHERE created_ts > NOW() - ($1 || ' minutes')::INTERVAL \
                         GROUP BY spectral_mode ORDER BY spectral_mode",
                        &[&window_minutes.to_string()],
                    )
                    .await
                    .map_err(|e| format!("inflight mode query failed: {}", e))?;

                let by_mode: Vec<Value> = mode_rows
                    .iter()
                    .map(|r| {
                        let mode: String = r.get(0);
                        let count: i64 = r.get(1);
                        let bytes: i64 = r.get(2);
                        json!({"mode": mode, "count": count, "bytes": bytes})
                    })
                    .collect();

                Ok(json!({
                    "inflight_count": inflight_count,
                    "total_compute_bytes": total_bytes,
                    "active_nodes": active_nodes,
                    "active_node_count": node_count,
                    "tier_count": tier_count,
                    "window_minutes": window_minutes,
                    "by_tier": by_tier,
                    "by_spectral_mode": by_mode,
                }))
            }
            None => Err("no RDS connection — cannot query inflight compute".to_string()),
        }
    }

    /// Defragment cold hoxels — merge old, low-thermal records into aggregates.
    ///
    /// Selects hoxels with thermal_score < cold_threshold AND older than the
    /// specified window, groups them by (obj_key, bucket, to_tier), and creates
    /// aggregate records that preserve total causal cost.
    pub async fn defrag_hoxels(
        &self,
        cold_threshold: f64,
        window_hours: i64,
    ) -> Result<Value, String> {
        match self.pg {
            Some(ref pg_arc) => {
                let pg = pg_arc.lock().await;

                // Count eligible cold hoxels first
                let count_row = pg
                    .query_one(
                        "SELECT COUNT(*)::BIGINT \
                         FROM hoxel_store.memory_hoxels \
                         WHERE thermal_score < $1::DOUBLE PRECISION \
                           AND created_ts < NOW() - ($2 || ' hours')::INTERVAL",
                        &[&cold_threshold, &window_hours.to_string()],
                    )
                    .await
                    .map_err(|e| format!("defrag count query failed: {}", e))?;
                let cold_count: i64 = count_row.get(0);

                if cold_count == 0 {
                    return Ok(json!({
                        "cold_hoxels": 0,
                        "aggregates_created": 0,
                        "causal_cost_preserved": true,
                    }));
                }

                // Create aggregates grouped by (obj_key, bucket, to_tier)
                let agg_rows = pg
                    .query(
                        "INSERT INTO hoxel_store.memory_hoxels \
                         (obj_key, bucket, to_tier, spectral_mode, \
                          density, confidence, semantic_load, \
                          thermal_score, residual, payload_bytes, witness_hash) \
                         SELECT \
                           obj_key, bucket, to_tier, 'defrag_aggregate', \
                           AVG(density), AVG(confidence), AVG(semantic_load), \
                           SUM(thermal_score), AVG(residual), SUM(payload_bytes), \
                           md5(CONCAT_WS('|', obj_key, bucket, to_tier, 'defrag', NOW()::TEXT)) \
                         FROM hoxel_store.memory_hoxels \
                         WHERE thermal_score < $1::DOUBLE PRECISION \
                           AND created_ts < NOW() - ($2 || ' hours')::INTERVAL \
                         GROUP BY obj_key, bucket, to_tier \
                         RETURNING hoxel_id::TEXT",
                        &[&cold_threshold, &window_hours.to_string()],
                    )
                    .await
                    .map_err(|e| format!("defrag aggregate insert failed: {}", e))?;

                let aggregates_created = agg_rows.len() as i64;

                Ok(json!({
                    "cold_hoxels": cold_count,
                    "aggregates_created": aggregates_created,
                    "causal_cost_preserved": true,
                }))
            }
            None => Err("no RDS connection — cannot defrag hoxels".to_string()),
        }
    }

    /// Get the latest tx_seq (global clock reading).
    pub async fn current_tx_seq(&self) -> Result<i64, String> {
        match self.pg {
            Some(ref pg_arc) => {
                let pg = pg_arc.lock().await;
                let row = pg
                    .query_one(
                        "SELECT COALESCE(MAX(tx_seq), 0) FROM hoxel_store.memory_hoxels",
                        &[],
                    )
                    .await
                    .map_err(|e| format!("tx_seq query failed: {}", e))?;
                Ok(row.get(0))
            }
            None => Err("no RDS connection".to_string()),
        }
    }
}

// ──────────────────────────────────────────────
// Helpers
// ──────────────────────────────────────────────

fn map_row_to_response(row: &tokio_postgres::Row) -> HoxelResponse {
    HoxelResponse {
        hoxel_id: row.get(0),
        tx_seq: row.get(1),
        obj_key: row.get(2),
        bucket: row.get(3),
        from_node: row.get(4),
        from_tier: row.get(5),
        to_node: row.get(6),
        to_tier: row.get(7),
        spectral_mode: row.get(8),
        density: row.get(9),
        confidence: row.get(10),
        semantic_load: row.get(11),
        thermal_score: row.get(12),
        residual: row.get(13),
        payload_bytes: row.get(14),
        access_count: row.get(15),
        witness_hash: row.get(16),
        chain_prev: row.get(17),
        created_ts: row.get(18),
    }
}
