#![allow(dead_code)]
//! gemma_integration.rs — Gemma-4 task dispatcher with SQLite persistence.
//!
//! Port of gemma_4_integration.py (397 lines).  A per-operation SQLite
//! connection is opened for each method call, mirroring the Python pattern of
//! constructing a new connection per operation.

use anyhow::{Context, Result};
use rusqlite::{params, Connection, OptionalExtension};
use serde_json::{json, Value};
use std::time::{SystemTime, UNIX_EPOCH};

// ─────────────────────────────────────────────────────────────────────────────
// §0  Shared helpers
// ─────────────────────────────────────────────────────────────────────────────

/// Current wall-clock seconds since the UNIX epoch.
fn now_secs() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs() as i64
}

// ─────────────────────────────────────────────────────────────────────────────
// §1  Variant and task-type enumerations
// ─────────────────────────────────────────────────────────────────────────────

/// Supported Gemma-4 model variants.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum GemmaVariant {
    /// `google/gemma-4-2b-it` — 2B instruction-tuned.
    E2B,
    /// `google/gemma-4-4b-it` — 4B instruction-tuned (default).
    E4B,
    /// `google/gemma-4-31b-it` — 31B instruction-tuned.
    E31B,
    /// `google/gemma-4-26b-a4b-it` — 26B MoE (active 4B) instruction-tuned.
    E26BA4B,
}

impl GemmaVariant {
    /// Hugging Face model identifier string.
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::E2B => "google/gemma-4-2b-it",
            Self::E4B => "google/gemma-4-4b-it",
            Self::E31B => "google/gemma-4-31b-it",
            Self::E26BA4B => "google/gemma-4-26b-a4b-it",
        }
    }

    /// Parse a model-identifier string; falls back to `E4B` on unknown input.
    pub fn from_str(s: &str) -> Self {
        match s {
            "google/gemma-4-2b-it" => Self::E2B,
            "google/gemma-4-4b-it" => Self::E4B,
            "google/gemma-4-31b-it" => Self::E31B,
            "google/gemma-4-26b-a4b-it" => Self::E26BA4B,
            _ => Self::E4B,
        }
    }
}

/// High-level task categories supported by this integration.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum GemmaTask {
    TextGeneration,
    MultimodalProcessing,
    AudioTranscription,
    ImageUnderstanding,
    Reasoning,
    CodeGeneration,
    FunctionCalling,
}

impl GemmaTask {
    /// Canonical lowercase identifier used for storage and metrics.
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::TextGeneration => "text_generation",
            Self::MultimodalProcessing => "multimodal_processing",
            Self::AudioTranscription => "audio_transcription",
            Self::ImageUnderstanding => "image_understanding",
            Self::Reasoning => "reasoning",
            Self::CodeGeneration => "code_generation",
            Self::FunctionCalling => "function_calling",
        }
    }

    /// Parse the canonical identifier; falls back to `TextGeneration`.
    pub fn from_str(s: &str) -> Self {
        match s {
            "text_generation" => Self::TextGeneration,
            "multimodal_processing" => Self::MultimodalProcessing,
            "audio_transcription" => Self::AudioTranscription,
            "image_understanding" => Self::ImageUnderstanding,
            "reasoning" => Self::Reasoning,
            "code_generation" => Self::CodeGeneration,
            "function_calling" => Self::FunctionCalling,
            _ => Self::TextGeneration,
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// §2  GemmaTaskRequest
// ─────────────────────────────────────────────────────────────────────────────

/// A fully-specified Gemma-4 task ready for submission.
pub struct GemmaTaskRequest {
    /// Caller-supplied or generated unique identifier.
    pub task_id: String,
    pub task_type: GemmaTask,
    pub variant: GemmaVariant,
    /// Arbitrary input payload (prompt, code, image bytes, …).
    pub input_data: Value,
    /// Whether the "thinking" scratchpad should be enabled in the model.
    pub enable_thinking: bool,
    /// Maximum tokens to generate.
    pub max_tokens: i64,
    /// Scheduling priority; higher is more urgent.
    pub priority: i64,
}

// ─────────────────────────────────────────────────────────────────────────────
// §3  Gemma4Integration
// ─────────────────────────────────────────────────────────────────────────────

/// SQLite-backed dispatcher for Gemma-4 inference tasks.
///
/// Each public method opens its own `rusqlite::Connection` (stateless per-op
/// pattern, matching the Python port).
pub struct Gemma4Integration {
    db_path: String,
    /// Default variant used when no variant is explicitly specified.
    _default_variant: GemmaVariant,
}

impl Gemma4Integration {
    // ── §3.1  Constructor ────────────────────────────────────────────────────

    /// Open (or create) the SQLite database at `db_path` and initialise all
    /// required tables.
    pub fn new(db_path: &str, default_variant: GemmaVariant) -> Result<Self> {
        let integration = Self {
            db_path: db_path.to_owned(),
            _default_variant: default_variant,
        };
        integration.init_tables()?;
        Ok(integration)
    }

    fn open(&self) -> Result<Connection> {
        Connection::open(&self.db_path)
            .with_context(|| format!("Gemma4Integration: open db {:?}", self.db_path))
    }

    fn init_tables(&self) -> Result<()> {
        let conn = self.open()?;
        conn.execute_batch(
            "CREATE TABLE IF NOT EXISTS gemma_task_requests (
                task_id         TEXT    PRIMARY KEY,
                task_type       TEXT    NOT NULL,
                variant         TEXT    NOT NULL,
                input_data      TEXT    NOT NULL,
                enable_thinking INTEGER NOT NULL DEFAULT 0,
                max_tokens      INTEGER NOT NULL DEFAULT 512,
                priority        INTEGER NOT NULL DEFAULT 0,
                status          TEXT    NOT NULL DEFAULT 'pending',
                created_at      INTEGER NOT NULL,
                started_at      INTEGER,
                completed_at    INTEGER,
                result          TEXT,
                error           TEXT
            );
            CREATE TABLE IF NOT EXISTS gemma_performance_metrics (
                variant              TEXT    PRIMARY KEY,
                total_tasks          INTEGER NOT NULL DEFAULT 0,
                avg_latency          REAL    NOT NULL DEFAULT 0.0,
                avg_tokens_per_second REAL   NOT NULL DEFAULT 0.0,
                last_updated         INTEGER NOT NULL
            );",
        )
        .context("Gemma4Integration: init_tables")?;
        Ok(())
    }

    // ── §3.2  Task submission ────────────────────────────────────────────────

    /// Insert a task into the database and bump the per-variant metrics row.
    ///
    /// Returns the `task_id` on success.
    pub fn submit_task(&self, task: &GemmaTaskRequest) -> Result<String> {
        let conn = self.open()?;

        let input_json = task.input_data.to_string();
        let now = now_secs();

        conn.execute(
            "INSERT OR REPLACE INTO gemma_task_requests
                (task_id, task_type, variant, input_data, enable_thinking,
                 max_tokens, priority, status, created_at)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, 'pending', ?8)",
            params![
                task.task_id,
                task.task_type.as_str(),
                task.variant.as_str(),
                input_json,
                task.enable_thinking as i64,
                task.max_tokens,
                task.priority,
                now,
            ],
        )
        .context("Gemma4Integration: submit_task insert")?;

        // Upsert performance-metrics row.
        conn.execute(
            "INSERT INTO gemma_performance_metrics
                (variant, total_tasks, avg_latency, avg_tokens_per_second, last_updated)
             VALUES (?1, 1, 0.0, 0.0, ?2)
             ON CONFLICT(variant) DO UPDATE SET
                 total_tasks  = total_tasks + 1,
                 last_updated = excluded.last_updated",
            params![task.variant.as_str(), now],
        )
        .context("Gemma4Integration: submit_task metrics upsert")?;

        Ok(task.task_id.clone())
    }

    // ── §3.3  Task execution ─────────────────────────────────────────────────

    /// Transition the task from `pending` → `in_progress` → `completed`,
    /// calling the simulated execution kernel in between.
    pub fn execute_task(&self, task_id: &str) -> Result<Value> {
        let conn = self.open()?;
        let now = now_secs();

        // Fetch task metadata.
        let row: Option<(String, String, i64)> = conn
            .query_row(
                "SELECT variant, task_type, max_tokens FROM gemma_task_requests
                  WHERE task_id = ?1",
                params![task_id],
                |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?)),
            )
            .optional()
            .context("Gemma4Integration: execute_task fetch")?;

        let (variant, task_type, max_tokens) = row
            .ok_or_else(|| anyhow::anyhow!("execute_task: unknown task_id '{}'", task_id))?;

        // Mark in-progress.
        conn.execute(
            "UPDATE gemma_task_requests SET status = 'in_progress', started_at = ?1
              WHERE task_id = ?2",
            params![now, task_id],
        )
        .context("Gemma4Integration: execute_task mark in_progress")?;

        // Simulate execution.
        let result = self._simulate_gemma_execution(task_id, &variant, &task_type, max_tokens);
        let result_json = result.to_string();

        let completed_at = now_secs();
        // Mark completed.
        conn.execute(
            "UPDATE gemma_task_requests
                SET status = 'completed', completed_at = ?1, result = ?2
              WHERE task_id = ?3",
            params![completed_at, result_json, task_id],
        )
        .context("Gemma4Integration: execute_task mark completed")?;

        // Update metrics with synthetic latency.
        let latency_ms = ((completed_at - now) * 1000) as f64 + 100.0;
        let tokens_per_sec = if latency_ms > 0.0 {
            (max_tokens as f64 / 2.0) / (latency_ms / 1000.0)
        } else {
            0.0
        };
        conn.execute(
            "UPDATE gemma_performance_metrics
                SET avg_latency           = (avg_latency + ?1) / 2.0,
                    avg_tokens_per_second = (avg_tokens_per_second + ?2) / 2.0,
                    last_updated          = ?3
              WHERE variant = ?4",
            params![latency_ms, tokens_per_sec, completed_at, variant],
        )
        .context("Gemma4Integration: execute_task update metrics")?;

        Ok(result)
    }

    /// Simulate Gemma inference — returns a structured `serde_json::Value`.
    fn _simulate_gemma_execution(
        &self,
        task_id: &str,
        variant: &str,
        task_type: &str,
        max_tokens: i64,
    ) -> Value {
        json!({
            "task_id": task_id,
            "variant": variant,
            "output": format!("Simulated output for {}", task_type),
            "tokens_generated": max_tokens / 2,
            "latency_ms": 100,
        })
    }

    // ── §3.4  Queries ────────────────────────────────────────────────────────

    /// Retrieve the result of a completed task, or `None` when still pending.
    pub fn get_task_result(&self, task_id: &str) -> Result<Option<Value>> {
        let conn = self.open()?;
        let result: Option<Option<String>> = conn
            .query_row(
                "SELECT result FROM gemma_task_requests WHERE task_id = ?1",
                params![task_id],
                |r| r.get(0),
            )
            .optional()
            .context("Gemma4Integration: get_task_result")?;

        match result {
            None => Ok(None), // task_id not found
            Some(None) => Ok(None), // task found but result not yet set
            Some(Some(json_str)) => {
                let v: Value = serde_json::from_str(&json_str)
                    .context("Gemma4Integration: get_task_result parse")?;
                Ok(Some(v))
            }
        }
    }

    /// Retrieve aggregated performance metrics for a specific variant.
    pub fn get_performance_metrics(&self, variant: &str) -> Result<Option<Value>> {
        let conn = self.open()?;
        let row: Option<(i64, f64, f64, i64)> = conn
            .query_row(
                "SELECT total_tasks, avg_latency, avg_tokens_per_second, last_updated
                   FROM gemma_performance_metrics WHERE variant = ?1",
                params![variant],
                |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?, r.get(3)?)),
            )
            .optional()
            .context("Gemma4Integration: get_performance_metrics")?;

        Ok(row.map(|(total, latency, tps, updated)| {
            json!({
                "variant": variant,
                "total_tasks": total,
                "avg_latency_ms": latency,
                "avg_tokens_per_second": tps,
                "last_updated": updated,
            })
        }))
    }

    /// List all tasks, optionally filtered by `status`.
    pub fn list_tasks(&self, status: Option<&str>) -> Result<Vec<Value>> {
        let conn = self.open()?;

        let (sql, filter): (&str, Option<&str>) = match status {
            Some(s) => (
                "SELECT task_id, task_type, variant, status, priority, created_at, completed_at
                   FROM gemma_task_requests WHERE status = ?1 ORDER BY priority DESC, created_at ASC",
                Some(s),
            ),
            None => (
                "SELECT task_id, task_type, variant, status, priority, created_at, completed_at
                   FROM gemma_task_requests ORDER BY priority DESC, created_at ASC",
                None,
            ),
        };

        let mut stmt = conn
            .prepare(sql)
            .context("Gemma4Integration: list_tasks prepare")?;

        let map_row = |r: &rusqlite::Row<'_>| -> rusqlite::Result<Value> {
            let task_id: String = r.get(0)?;
            let task_type: String = r.get(1)?;
            let variant: String = r.get(2)?;
            let row_status: String = r.get(3)?;
            let priority: i64 = r.get(4)?;
            let created_at: i64 = r.get(5)?;
            let completed_at: Option<i64> = r.get(6)?;
            Ok(json!({
                "task_id": task_id,
                "task_type": task_type,
                "variant": variant,
                "status": row_status,
                "priority": priority,
                "created_at": created_at,
                "completed_at": completed_at,
            }))
        };

        let rows: Vec<Value> = if let Some(s) = filter {
            stmt.query_map(params![s], map_row)
                .context("Gemma4Integration: list_tasks query (filtered)")?
                .collect::<rusqlite::Result<Vec<_>>>()
                .context("Gemma4Integration: list_tasks collect (filtered)")?
        } else {
            stmt.query_map([], map_row)
                .context("Gemma4Integration: list_tasks query")?
                .collect::<rusqlite::Result<Vec<_>>>()
                .context("Gemma4Integration: list_tasks collect")?
        };

        Ok(rows)
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// §4  Tests
// ─────────────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::NamedTempFile;

    fn temp_db() -> String {
        NamedTempFile::new().unwrap().path().to_string_lossy().to_string()
    }

    fn make_task(id: &str) -> GemmaTaskRequest {
        GemmaTaskRequest {
            task_id: id.to_owned(),
            task_type: GemmaTask::Reasoning,
            variant: GemmaVariant::E4B,
            input_data: json!({ "prompt": "Explain braid theory." }),
            enable_thinking: true,
            max_tokens: 256,
            priority: 5,
        }
    }

    #[test]
    fn test_submit_and_execute() {
        let db = temp_db();
        let g = Gemma4Integration::new(&db, GemmaVariant::E4B).unwrap();
        let task = make_task("t-001");
        g.submit_task(&task).unwrap();
        let result = g.execute_task("t-001").unwrap();
        assert_eq!(result["task_id"], "t-001");
        assert_eq!(result["variant"], GemmaVariant::E4B.as_str());
        assert!(result["tokens_generated"].as_i64().unwrap() == 128);
    }

    #[test]
    fn test_get_task_result_after_execute() {
        let db = temp_db();
        let g = Gemma4Integration::new(&db, GemmaVariant::E2B).unwrap();
        let task = make_task("t-002");
        g.submit_task(&task).unwrap();
        g.execute_task("t-002").unwrap();
        let result = g.get_task_result("t-002").unwrap();
        assert!(result.is_some());
    }

    #[test]
    fn test_list_tasks_filtered() {
        let db = temp_db();
        let g = Gemma4Integration::new(&db, GemmaVariant::E4B).unwrap();
        g.submit_task(&make_task("t-003")).unwrap();
        g.submit_task(&make_task("t-004")).unwrap();
        g.execute_task("t-003").unwrap();

        let completed = g.list_tasks(Some("completed")).unwrap();
        assert_eq!(completed.len(), 1);
        assert_eq!(completed[0]["task_id"], "t-003");

        let pending = g.list_tasks(Some("pending")).unwrap();
        assert_eq!(pending.len(), 1);
        assert_eq!(pending[0]["task_id"], "t-004");
    }

    #[test]
    fn test_performance_metrics() {
        let db = temp_db();
        let g = Gemma4Integration::new(&db, GemmaVariant::E4B).unwrap();
        g.submit_task(&make_task("t-005")).unwrap();
        g.execute_task("t-005").unwrap();
        let metrics = g
            .get_performance_metrics(GemmaVariant::E4B.as_str())
            .unwrap();
        assert!(metrics.is_some());
        assert!(metrics.unwrap()["total_tasks"].as_i64().unwrap() >= 1);
    }

    #[test]
    fn test_variant_round_trip() {
        assert_eq!(
            GemmaVariant::from_str(GemmaVariant::E26BA4B.as_str()),
            GemmaVariant::E26BA4B
        );
        // Unknown string → default E4B.
        assert_eq!(GemmaVariant::from_str("unknown"), GemmaVariant::E4B);
    }

    #[test]
    fn test_task_type_round_trip() {
        for t in &[
            GemmaTask::TextGeneration,
            GemmaTask::Reasoning,
            GemmaTask::CodeGeneration,
            GemmaTask::FunctionCalling,
        ] {
            assert_eq!(GemmaTask::from_str(t.as_str()).as_str(), t.as_str());
        }
    }
}
