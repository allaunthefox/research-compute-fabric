use anyhow::{Context, Result};
use ene_rds_core::RdsClient;
use serde::{Deserialize, Serialize};
use tracing::info;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EphemeralNode {
    pub node_id: String,
    pub thermal_zone: String,
    pub reliability_raw: i64,
    pub latency_p95_ms: i64,
    pub scar_count: i32,
    pub last_seen_ms: i64,
    pub reputation_raw: i64,
    pub quarantine_until_ms: Option<i64>,
    pub meta: serde_json::Value,
    pub created_at_ms: i64,
    pub updated_at_ms: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EphemeralTask {
    pub task_id: String,
    pub session_id: String,
    pub node_id: String,
    pub task_state: String,
    pub priority_raw: i64,
    pub ttl_ms: i64,
    pub dispatched_at_ms: Option<i64>,
    pub completed_at_ms: Option<i64>,
    pub result_hash: Option<String>,
    pub meta: serde_json::Value,
    pub created_at_ms: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EphemeralReceipt {
    pub receipt_id: String,
    pub task_id: String,
    pub node_id: String,
    pub cross_matrix: serde_json::Value,
    pub sidon_slack: i32,
    pub step_count: i32,
    pub residual_series: Vec<i64>,
    pub write_timing_ms: i64,
    pub scar_absent: bool,
    pub created_at_ms: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EphemeralScarEvent {
    pub scar_id: String,
    pub node_id: String,
    pub task_id: String,
    pub scar_pressure: i64,
    pub failure_mode: String,
    pub coarsening_agent: Option<String>,
    pub created_at_ms: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EphemeralMetric {
    pub metric_id: String,
    pub node_id: String,
    pub metric_name: String,
    pub metric_value_raw: i64,
    pub metric_scale: i32,
    pub recorded_at_ms: i64,
}

/// EphemeralNode thermal zone RDS surface — replaces Python ENERDSEphemeralNode.
pub struct EphemeralSurface {
    client: RdsClient,
}

impl EphemeralSurface {
    pub fn new(client: RdsClient) -> Self {
        Self { client }
    }

    pub async fn init_tables(&self) -> Result<()> {
        let ddl = r#"
CREATE TABLE IF NOT EXISTS ene.ephemeral_nodes (
    node_id TEXT PRIMARY KEY,
    thermal_zone TEXT NOT NULL DEFAULT 'cold',
    reliability_raw BIGINT NOT NULL DEFAULT 0,
    latency_p95_ms BIGINT NOT NULL DEFAULT 0,
    scar_count INTEGER NOT NULL DEFAULT 0,
    last_seen_ms BIGINT NOT NULL DEFAULT 0,
    reputation_raw BIGINT NOT NULL DEFAULT 0,
    quarantine_until_ms BIGINT,
    meta JSONB NOT NULL DEFAULT '{}',
    created_at_ms BIGINT NOT NULL,
    updated_at_ms BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS ene.ephemeral_tasks (
    task_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    node_id TEXT NOT NULL REFERENCES ene.ephemeral_nodes(node_id),
    task_state TEXT NOT NULL DEFAULT 'pending',
    priority_raw BIGINT NOT NULL DEFAULT 0,
    ttl_ms BIGINT NOT NULL DEFAULT 0,
    dispatched_at_ms BIGINT,
    completed_at_ms BIGINT,
    result_hash TEXT,
    meta JSONB NOT NULL DEFAULT '{}',
    created_at_ms BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS ene.ephemeral_receipts (
    receipt_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES ene.ephemeral_tasks(task_id),
    node_id TEXT NOT NULL REFERENCES ene.ephemeral_nodes(node_id),
    cross_matrix JSONB NOT NULL DEFAULT '{}',
    sidon_slack INTEGER NOT NULL DEFAULT 0,
    step_count INTEGER NOT NULL DEFAULT 0,
    residual_series BIGINT[] NOT NULL DEFAULT '{}',
    write_timing_ms BIGINT NOT NULL DEFAULT 0,
    scar_absent BOOLEAN NOT NULL DEFAULT true,
    created_at_ms BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS ene.ephemeral_scar_events (
    scar_id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL REFERENCES ene.ephemeral_nodes(node_id),
    task_id TEXT REFERENCES ene.ephemeral_tasks(task_id),
    scar_pressure BIGINT NOT NULL DEFAULT 0,
    failure_mode TEXT NOT NULL DEFAULT '',
    coarsening_agent TEXT,
    created_at_ms BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS ene.ephemeral_metrics (
    metric_id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL REFERENCES ene.ephemeral_nodes(node_id),
    metric_name TEXT NOT NULL,
    metric_value_raw BIGINT NOT NULL DEFAULT 0,
    metric_scale INTEGER NOT NULL DEFAULT 65536,
    recorded_at_ms BIGINT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ephemeral_nodes_zone ON ene.ephemeral_nodes(thermal_zone);
CREATE INDEX IF NOT EXISTS idx_ephemeral_nodes_quarantine ON ene.ephemeral_nodes(quarantine_until_ms);
CREATE INDEX IF NOT EXISTS idx_ephemeral_tasks_state ON ene.ephemeral_tasks(task_state);
CREATE INDEX IF NOT EXISTS idx_ephemeral_tasks_session ON ene.ephemeral_tasks(session_id);
CREATE INDEX IF NOT EXISTS idx_ephemeral_scar_node ON ene.ephemeral_scar_events(node_id, created_at_ms DESC);
        "#;
        self.client.inner().batch_execute(ddl).await.context("init ephemeral DDL")?;
        info!("ephemeral node schema initialized");
        Ok(())
    }

    pub async fn upsert_node(&self, node: &EphemeralNode) -> Result<()> {
        self.client.inner()
            .execute(
                "INSERT INTO ene.ephemeral_nodes \
                 (node_id, thermal_zone, reliability_raw, latency_p95_ms, scar_count, \
                  last_seen_ms, reputation_raw, quarantine_until_ms, meta, created_at_ms, updated_at_ms) \
                 VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11) \
                 ON CONFLICT (node_id) DO UPDATE SET \
                  thermal_zone = EXCLUDED.thermal_zone, \
                  reliability_raw = EXCLUDED.reliability_raw, \
                  latency_p95_ms = EXCLUDED.latency_p95_ms, \
                  scar_count = EXCLUDED.scar_count, \
                  last_seen_ms = EXCLUDED.last_seen_ms, \
                  reputation_raw = EXCLUDED.reputation_raw, \
                  quarantine_until_ms = EXCLUDED.quarantine_until_ms, \
                  meta = EXCLUDED.meta, \
                  updated_at_ms = EXCLUDED.updated_at_ms",
                &[
                    &node.node_id, &node.thermal_zone, &node.reliability_raw,
                    &node.latency_p95_ms, &node.scar_count, &node.last_seen_ms,
                    &node.reputation_raw, &node.quarantine_until_ms, &node.meta,
                    &node.created_at_ms, &node.updated_at_ms,
                ],
            )
            .await
            .context("upsert ephemeral node")?;
        Ok(())
    }

    pub async fn get_node(&self, node_id: &str) -> Result<Option<EphemeralNode>> {
        let row = self.client.inner()
            .query_opt(
                "SELECT node_id, thermal_zone, reliability_raw, latency_p95_ms, scar_count, \
                 last_seen_ms, reputation_raw, quarantine_until_ms, meta, created_at_ms, updated_at_ms \
                 FROM ene.ephemeral_nodes WHERE node_id = $1",
                &[&node_id],
            )
            .await
            .context("get ephemeral node")?;
        Ok(row.map(|r| EphemeralNode {
            node_id: r.get(0),
            thermal_zone: r.get(1),
            reliability_raw: r.get(2),
            latency_p95_ms: r.get(3),
            scar_count: r.get(4),
            last_seen_ms: r.get(5),
            reputation_raw: r.get(6),
            quarantine_until_ms: r.get(7),
            meta: r.get(8),
            created_at_ms: r.get(9),
            updated_at_ms: r.get(10),
        }))
    }

    pub async fn list_nodes_by_zone(&self, zone: &str, limit: i64) -> Result<Vec<EphemeralNode>> {
        let rows = self.client.inner()
            .query(
                "SELECT node_id, thermal_zone, reliability_raw, latency_p95_ms, scar_count, \
                 last_seen_ms, reputation_raw, quarantine_until_ms, meta, created_at_ms, updated_at_ms \
                 FROM ene.ephemeral_nodes WHERE thermal_zone = $1 ORDER BY updated_at_ms DESC LIMIT $2",
                &[&zone, &limit],
            )
            .await
            .context("list ephemeral nodes")?;
        Ok(rows.iter().map(|r| EphemeralNode {
            node_id: r.get(0),
            thermal_zone: r.get(1),
            reliability_raw: r.get(2),
            latency_p95_ms: r.get(3),
            scar_count: r.get(4),
            last_seen_ms: r.get(5),
            reputation_raw: r.get(6),
            quarantine_until_ms: r.get(7),
            meta: r.get(8),
            created_at_ms: r.get(9),
            updated_at_ms: r.get(10),
        }).collect())
    }

    pub async fn insert_task(&self, task: &EphemeralTask) -> Result<()> {
        self.client.inner()
            .execute(
                "INSERT INTO ene.ephemeral_tasks \
                 (task_id, session_id, node_id, task_state, priority_raw, ttl_ms, \
                  dispatched_at_ms, completed_at_ms, result_hash, meta, created_at_ms) \
                 VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11) \
                 ON CONFLICT (task_id) DO UPDATE SET \
                  task_state = EXCLUDED.task_state, \
                  dispatched_at_ms = EXCLUDED.dispatched_at_ms, \
                  completed_at_ms = EXCLUDED.completed_at_ms, \
                  result_hash = EXCLUDED.result_hash, \
                  meta = EXCLUDED.meta",
                &[
                    &task.task_id, &task.session_id, &task.node_id, &task.task_state,
                    &task.priority_raw, &task.ttl_ms, &task.dispatched_at_ms,
                    &task.completed_at_ms, &task.result_hash, &task.meta, &task.created_at_ms,
                ],
            )
            .await
            .context("insert ephemeral task")?;
        Ok(())
    }

    pub async fn record_scar(&self, scar: &EphemeralScarEvent) -> Result<()> {
        self.client.inner()
            .execute(
                "INSERT INTO ene.ephemeral_scar_events \
                 (scar_id, node_id, task_id, scar_pressure, failure_mode, coarsening_agent, created_at_ms) \
                 VALUES ($1, $2, $3, $4, $5, $6, $7) \
                 ON CONFLICT (scar_id) DO UPDATE SET \
                  scar_pressure = EXCLUDED.scar_pressure, \
                  failure_mode = EXCLUDED.failure_mode, \
                  coarsening_agent = EXCLUDED.coarsening_agent",
                &[
                    &scar.scar_id, &scar.node_id, &scar.task_id, &scar.scar_pressure,
                    &scar.failure_mode, &scar.coarsening_agent, &scar.created_at_ms,
                ],
            )
            .await
            .context("record scar")?;
        Ok(())
    }

    pub async fn insert_metric(&self, metric: &EphemeralMetric) -> Result<()> {
        self.client.inner()
            .execute(
                "INSERT INTO ene.ephemeral_metrics \
                 (metric_id, node_id, metric_name, metric_value_raw, metric_scale, recorded_at_ms) \
                 VALUES ($1, $2, $3, $4, $5, $6) \
                 ON CONFLICT (metric_id) DO UPDATE SET \
                  metric_value_raw = EXCLUDED.metric_value_raw, \
                  metric_scale = EXCLUDED.metric_scale, \
                  recorded_at_ms = EXCLUDED.recorded_at_ms",
                &[
                    &metric.metric_id, &metric.node_id, &metric.metric_name,
                    &metric.metric_value_raw, &metric.metric_scale, &metric.recorded_at_ms,
                ],
            )
            .await
            .context("insert metric")?;
        Ok(())
    }

    pub async fn get_node_scars(&self, node_id: &str, limit: i64) -> Result<Vec<EphemeralScarEvent>> {
        let rows = self.client.inner()
            .query(
                "SELECT scar_id, node_id, task_id, scar_pressure, failure_mode, coarsening_agent, created_at_ms \
                 FROM ene.ephemeral_scar_events WHERE node_id = $1 ORDER BY created_at_ms DESC LIMIT $2",
                &[&node_id, &limit],
            )
            .await
            .context("get node scars")?;
        Ok(rows.iter().map(|r| EphemeralScarEvent {
            scar_id: r.get(0),
            node_id: r.get(1),
            task_id: r.get(2),
            scar_pressure: r.get(3),
            failure_mode: r.get(4),
            coarsening_agent: r.get(5),
            created_at_ms: r.get(6),
        }).collect())
    }

    pub async fn get_task_receipt(&self, task_id: &str) -> Result<Option<EphemeralReceipt>> {
        let row = self.client.inner()
            .query_opt(
                "SELECT receipt_id, task_id, node_id, cross_matrix, sidon_slack, \
                 step_count, residual_series, write_timing_ms, scar_absent, created_at_ms \
                 FROM ene.ephemeral_receipts WHERE task_id = $1",
                &[&task_id],
            )
            .await
            .context("get task receipt")?;
        Ok(row.map(|r| EphemeralReceipt {
            receipt_id: r.get(0),
            task_id: r.get(1),
            node_id: r.get(2),
            cross_matrix: r.get(3),
            sidon_slack: r.get(4),
            step_count: r.get(5),
            residual_series: r.get(6),
            write_timing_ms: r.get(7),
            scar_absent: r.get(8),
            created_at_ms: r.get(9),
        }))
    }
}
