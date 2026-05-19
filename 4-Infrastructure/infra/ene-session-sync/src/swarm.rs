//! swarm.rs — Port of:
//!   swarm_ene_middleware.py  (query caching + audit logging)
//!   swarm_execution_layer.py (task execution)
//!   cloud_runtime.py         (session/agent/tool orchestration)
//!   research_engine.py       (search + fetch orchestration)
#![allow(dead_code)]

use anyhow::{Context, Result};
use rusqlite::{params, Connection};
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::collections::HashMap;
use std::path::{Path, PathBuf};

// ─────────────────────────────────────────────────────────────────
// FNV-1a helpers (consistent with main.rs style — not cryptographic)
// ─────────────────────────────────────────────────────────────────

const FNV_OFFSET: u64 = 0xcbf2_9ce4_8422_2325;
const FNV_PRIME: u64 = 0x0000_0001_0000_01b3;

fn fnv1a(data: &[u8]) -> u64 {
    let mut hash = FNV_OFFSET;
    for &byte in data {
        hash ^= u64::from(byte);
        hash = hash.wrapping_mul(FNV_PRIME);
    }
    hash
}

fn fnv1a_hex(data: &[u8]) -> String {
    format!("{:016x}", fnv1a(data))
}

// ─────────────────────────────────────────────────────────────────
// SwarmQueryCache
// ─────────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SwarmQueryCache {
    pub query_hash: String,
    pub subjects: Vec<String>,
    pub keywords: Option<String>,
    pub results: Vec<serde_json::Value>,
    pub count: usize,
    pub confidence: f64,
    pub timestamp: i64,
    pub ttl: i64,
}

// ─────────────────────────────────────────────────────────────────
// SwarmMiddleware — SQLite-backed cache + audit log
// ─────────────────────────────────────────────────────────────────

pub struct SwarmMiddleware {
    pub db_path: PathBuf,
}

impl SwarmMiddleware {
    pub fn new(db_path: impl AsRef<Path>) -> Result<Self> {
        let m = Self {
            db_path: db_path.as_ref().to_path_buf(),
        };
        m.init_tables()?;
        Ok(m)
    }

    fn open(&self) -> Result<Connection> {
        Connection::open(&self.db_path)
            .with_context(|| format!("open swarm db {:?}", self.db_path))
    }

    fn init_tables(&self) -> Result<()> {
        let conn = self.open()?;
        conn.execute_batch(
            "CREATE TABLE IF NOT EXISTS swarm_query_cache (
                query_hash  TEXT PRIMARY KEY,
                subjects    TEXT NOT NULL,
                keywords    TEXT,
                results     TEXT NOT NULL,
                count       INTEGER NOT NULL,
                confidence  REAL NOT NULL,
                timestamp   INTEGER NOT NULL,
                ttl         INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS swarm_api_audit (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                operation   TEXT NOT NULL,
                params      TEXT NOT NULL,
                cached      INTEGER NOT NULL,
                count       INTEGER,
                elapsed_ms  REAL NOT NULL,
                recorded_at INTEGER NOT NULL
            );",
        )
        .context("init swarm tables")
    }

    /// FNV-1a hash of sorted subjects JSON + optional keywords.
    fn compute_query_hash(&self, subjects: &[String], keywords: Option<&str>) -> String {
        let mut sorted = subjects.to_vec();
        sorted.sort();
        let subjects_json = serde_json::to_string(&sorted).unwrap_or_default();
        let raw = format!("{}|{}", subjects_json, keywords.unwrap_or(""));
        fnv1a_hex(raw.as_bytes())
    }

    pub fn check_cache(
        &self,
        subjects: &[String],
        keywords: Option<&str>,
    ) -> Result<Option<SwarmQueryCache>> {
        let hash = self.compute_query_hash(subjects, keywords);
        let now = chrono::Utc::now().timestamp();
        let conn = self.open()?;
        let result = conn.query_row(
            "SELECT query_hash, subjects, keywords, results, count, confidence, timestamp, ttl
             FROM swarm_query_cache
             WHERE query_hash = ?1 AND (timestamp + ttl) > ?2",
            params![hash, now],
            |row| {
                let subjects_str: String = row.get(1)?;
                let results_str: String = row.get(3)?;
                Ok((
                    row.get::<_, String>(0)?,
                    subjects_str,
                    row.get::<_, Option<String>>(2)?,
                    results_str,
                    row.get::<_, i64>(4)? as usize,
                    row.get::<_, f64>(5)?,
                    row.get::<_, i64>(6)?,
                    row.get::<_, i64>(7)?,
                ))
            },
        );

        match result {
            Ok((qhash, subjects_str, kw, results_str, count, confidence, timestamp, ttl)) => {
                let subjects: Vec<String> =
                    serde_json::from_str(&subjects_str).unwrap_or_default();
                let results: Vec<serde_json::Value> =
                    serde_json::from_str(&results_str).unwrap_or_default();
                Ok(Some(SwarmQueryCache {
                    query_hash: qhash,
                    subjects,
                    keywords: kw,
                    results,
                    count,
                    confidence,
                    timestamp,
                    ttl,
                }))
            }
            Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
            Err(e) => Err(e).context("check swarm cache"),
        }
    }

    pub fn store_cache(
        &self,
        subjects: &[String],
        keywords: Option<&str>,
        results: Vec<serde_json::Value>,
        confidence: f64,
        ttl_secs: i64,
    ) -> Result<()> {
        let hash = self.compute_query_hash(subjects, keywords);
        let now = chrono::Utc::now().timestamp();
        let count = results.len();
        let mut sorted = subjects.to_vec();
        sorted.sort();
        let subjects_json = serde_json::to_string(&sorted)?;
        let results_json = serde_json::to_string(&results)?;

        let conn = self.open()?;
        conn.execute(
            "INSERT OR REPLACE INTO swarm_query_cache
                (query_hash, subjects, keywords, results, count, confidence, timestamp, ttl)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)",
            params![
                hash,
                subjects_json,
                keywords,
                results_json,
                count as i64,
                confidence,
                now,
                ttl_secs
            ],
        )
        .context("store swarm cache")?;
        Ok(())
    }

    pub fn log_operation(
        &self,
        operation: &str,
        params_val: &serde_json::Value,
        cached: bool,
        count: Option<usize>,
        elapsed_ms: f64,
    ) -> Result<()> {
        let now = chrono::Utc::now().timestamp();
        let params_str = serde_json::to_string(params_val)?;
        let conn = self.open()?;
        conn.execute(
            "INSERT INTO swarm_api_audit
                (operation, params, cached, count, elapsed_ms, recorded_at)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
            params![
                operation,
                params_str,
                cached as i64,
                count.map(|c| c as i64),
                elapsed_ms,
                now
            ],
        )
        .context("log swarm operation")?;
        Ok(())
    }

    /// Remove expired cache entries; returns count of removed rows.
    pub fn invalidate_expired(&self) -> Result<usize> {
        let now = chrono::Utc::now().timestamp();
        let conn = self.open()?;
        let n = conn
            .execute(
                "DELETE FROM swarm_query_cache WHERE (timestamp + ttl) <= ?1",
                params![now],
            )
            .context("invalidate expired")?;
        Ok(n)
    }

    pub fn cache_stats(&self) -> Result<serde_json::Value> {
        let now = chrono::Utc::now().timestamp();
        let conn = self.open()?;
        let total: i64 = conn
            .query_row("SELECT COUNT(*) FROM swarm_query_cache", [], |r| r.get(0))
            .unwrap_or(0);
        let live: i64 = conn
            .query_row(
                "SELECT COUNT(*) FROM swarm_query_cache WHERE (timestamp + ttl) > ?1",
                params![now],
                |r| r.get(0),
            )
            .unwrap_or(0);
        let audit_rows: i64 = conn
            .query_row("SELECT COUNT(*) FROM swarm_api_audit", [], |r| r.get(0))
            .unwrap_or(0);
        Ok(json!({
            "total_cache_entries": total,
            "live_cache_entries":  live,
            "expired_entries":     total - live,
            "audit_log_rows":      audit_rows,
        }))
    }
}

// ─────────────────────────────────────────────────────────────────
// SwarmExecutionLayer — task execution
// ─────────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum TaskStatus {
    Pending,
    InProgress,
    Completed,
    Failed,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Task {
    pub id: String,
    pub description: String,
    pub priority: f64,
    pub status: TaskStatus,
    pub gpu_accelerated: bool,
    pub estimated_cycles: u32,
    pub actual_cycles: u32,
    pub result: Option<serde_json::Value>,
    pub error: Option<String>,
}

pub struct SwarmExecutionLayer {
    pub tasks: Vec<Task>,
    pub current_cycle: u32,
    pub gpu_available: bool,
    pub execution_log: Vec<serde_json::Value>,
}

impl SwarmExecutionLayer {
    pub fn new() -> Self {
        // GPU detection is platform-specific — default to false per spec.
        Self {
            tasks: Vec::new(),
            current_cycle: 0,
            gpu_available: false,
            execution_log: Vec::new(),
        }
    }

    /// Parse "priority_state_tracking.current_priorities" array from analysis JSON
    /// and create a Task for each entry.
    pub fn load_recommendations(&mut self, analysis: &serde_json::Value) {
        let priorities = analysis
            .get("priority_state_tracking")
            .and_then(|p| p.get("current_priorities"))
            .and_then(|p| p.as_array());

        if let Some(arr) = priorities {
            for (i, item) in arr.iter().enumerate() {
                let description = item
                    .get("description")
                    .or_else(|| item.get("task"))
                    .and_then(|v| v.as_str())
                    .unwrap_or("unnamed task")
                    .to_string();
                let priority = item
                    .get("priority")
                    .and_then(|v| v.as_f64())
                    .unwrap_or(0.5);
                let estimated_cycles = item
                    .get("estimated_cycles")
                    .and_then(|v| v.as_u64())
                    .unwrap_or(1) as u32;

                let task = Task {
                    id: format!("task-{}-{}", self.current_cycle, i),
                    description,
                    priority,
                    status: TaskStatus::Pending,
                    gpu_accelerated: self.gpu_available,
                    estimated_cycles,
                    actual_cycles: 0,
                    result: None,
                    error: None,
                };
                self.tasks.push(task);
            }
        }
    }

    /// Execute a single task by index; returns a result JSON object.
    /// Status transitions: Pending → InProgress → Completed (no actual sleep).
    pub fn execute_task(&mut self, task_idx: usize) -> serde_json::Value {
        if task_idx >= self.tasks.len() {
            return json!({"ok": false, "error": "task index out of range"});
        }
        let task = &mut self.tasks[task_idx];
        task.status = TaskStatus::InProgress;
        self.current_cycle += 1;

        // Simulate execution — record cycles consumed.
        let cycles_used = task.estimated_cycles.max(1);
        task.actual_cycles = cycles_used;

        let result = json!({
            "task_id":       task.id,
            "description":   task.description,
            "cycles_used":   cycles_used,
            "gpu":           task.gpu_accelerated,
            "cycle_number":  self.current_cycle,
        });
        task.result = Some(result.clone());
        task.status = TaskStatus::Completed;

        let log_entry = json!({
            "event":    "task_completed",
            "task_id":  task.id,
            "priority": task.priority,
            "cycle":    self.current_cycle,
        });
        self.execution_log.push(log_entry);

        result
    }

    /// Sort tasks by priority descending, execute each, return summary.
    pub fn execute_all(&mut self) -> serde_json::Value {
        // Collect pending indices sorted by priority descending.
        let mut pending: Vec<usize> = self
            .tasks
            .iter()
            .enumerate()
            .filter(|(_, t)| t.status == TaskStatus::Pending)
            .map(|(i, _)| i)
            .collect();
        // Sort descending by priority; stable ties preserve insertion order.
        pending.sort_by(|&a, &b| {
            self.tasks[b]
                .priority
                .partial_cmp(&self.tasks[a].priority)
                .unwrap_or(std::cmp::Ordering::Equal)
        });

        let mut completed = 0usize;
        let mut failed = 0usize;
        for idx in pending {
            let r = self.execute_task(idx);
            if r.get("ok").and_then(|v| v.as_bool()) == Some(false) {
                failed += 1;
            } else {
                completed += 1;
            }
        }

        json!({
            "total":     self.tasks.len(),
            "completed": completed,
            "failed":    failed,
        })
    }

    pub fn get_status(&self) -> serde_json::Value {
        let pending = self
            .tasks
            .iter()
            .filter(|t| t.status == TaskStatus::Pending)
            .count();
        let in_progress = self
            .tasks
            .iter()
            .filter(|t| t.status == TaskStatus::InProgress)
            .count();
        let completed = self
            .tasks
            .iter()
            .filter(|t| t.status == TaskStatus::Completed)
            .count();
        let failed = self
            .tasks
            .iter()
            .filter(|t| t.status == TaskStatus::Failed)
            .count();
        json!({
            "total_tasks":    self.tasks.len(),
            "pending":        pending,
            "in_progress":    in_progress,
            "completed":      completed,
            "failed":         failed,
            "current_cycle":  self.current_cycle,
            "gpu_available":  self.gpu_available,
            "log_entries":    self.execution_log.len(),
        })
    }
}

impl Default for SwarmExecutionLayer {
    fn default() -> Self {
        Self::new()
    }
}

// ─────────────────────────────────────────────────────────────────
// CloudRuntime — SQLite-backed session/agent orchestration
// ─────────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum SessionState {
    Initializing,
    Active,
    Suspended,
    Completed,
    Failed,
}

impl SessionState {
    fn as_str(&self) -> &'static str {
        match self {
            SessionState::Initializing => "Initializing",
            SessionState::Active => "Active",
            SessionState::Suspended => "Suspended",
            SessionState::Completed => "Completed",
            SessionState::Failed => "Failed",
        }
    }

    fn from_str(s: &str) -> Self {
        match s {
            "Active" => SessionState::Active,
            "Suspended" => SessionState::Suspended,
            "Completed" => SessionState::Completed,
            "Failed" => SessionState::Failed,
            _ => SessionState::Initializing,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Session {
    pub session_id: String,
    pub created_at: f64,
    pub updated_at: f64,
    pub state: SessionState,
    pub workspace: String,
    pub agent_id: Option<String>,
    pub context: serde_json::Value,
}

pub struct CloudRuntime {
    pub db_path: PathBuf,
    pub sessions: HashMap<String, Session>,
    /// Monotonic counter for simple UUID generation without the uuid crate.
    session_counter: u64,
}

impl CloudRuntime {
    pub fn new(db_path: impl AsRef<Path>) -> Result<Self> {
        let mut rt = Self {
            db_path: db_path.as_ref().to_path_buf(),
            sessions: HashMap::new(),
            session_counter: 0,
        };
        rt.init_db()?;
        rt.load_sessions()?;
        Ok(rt)
    }

    fn open(&self) -> Result<Connection> {
        Connection::open(&self.db_path)
            .with_context(|| format!("open cloud runtime db {:?}", self.db_path))
    }

    fn init_db(&self) -> Result<()> {
        let conn = self.open()?;
        conn.execute_batch(
            "CREATE TABLE IF NOT EXISTS cloud_sessions (
                session_id  TEXT PRIMARY KEY,
                created_at  REAL NOT NULL,
                updated_at  REAL NOT NULL,
                state       TEXT NOT NULL,
                workspace   TEXT NOT NULL,
                agent_id    TEXT,
                context     TEXT NOT NULL
            );",
        )
        .context("init cloud_sessions table")
    }

    fn load_sessions(&mut self) -> Result<()> {
        let conn = self.open()?;
        let mut stmt = conn.prepare(
            "SELECT session_id, created_at, updated_at, state, workspace, agent_id, context
             FROM cloud_sessions",
        )?;
        let rows = stmt.query_map([], |row| {
            Ok((
                row.get::<_, String>(0)?,
                row.get::<_, f64>(1)?,
                row.get::<_, f64>(2)?,
                row.get::<_, String>(3)?,
                row.get::<_, String>(4)?,
                row.get::<_, Option<String>>(5)?,
                row.get::<_, String>(6)?,
            ))
        })?;
        for row in rows {
            let (sid, created, updated, state_str, workspace, agent_id, context_str) =
                row.context("read cloud session row")?;
            let context: serde_json::Value =
                serde_json::from_str(&context_str).unwrap_or(serde_json::Value::Null);
            let session = Session {
                session_id: sid.clone(),
                created_at: created,
                updated_at: updated,
                state: SessionState::from_str(&state_str),
                workspace,
                agent_id,
                context,
            };
            self.sessions.insert(sid, session);
        }
        Ok(())
    }

    /// Generate a simple unique session ID using a FNV-1a hash of timestamp + counter.
    fn next_session_id(&mut self) -> String {
        self.session_counter += 1;
        let raw = format!(
            "{}-{}",
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap_or_default()
                .as_nanos(),
            self.session_counter
        );
        format!("sess-{}", fnv1a_hex(raw.as_bytes()))
    }

    pub fn create_session(
        &mut self,
        workspace: &str,
        agent_id: Option<&str>,
    ) -> Result<Session> {
        let sid = self.next_session_id();
        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs_f64();

        let session = Session {
            session_id: sid.clone(),
            created_at: now,
            updated_at: now,
            state: SessionState::Initializing,
            workspace: workspace.to_string(),
            agent_id: agent_id.map(str::to_string),
            context: json!({}),
        };

        // Persist
        let conn = self.open()?;
        conn.execute(
            "INSERT INTO cloud_sessions
                (session_id, created_at, updated_at, state, workspace, agent_id, context)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
            params![
                session.session_id,
                session.created_at,
                session.updated_at,
                session.state.as_str(),
                session.workspace,
                session.agent_id,
                serde_json::to_string(&session.context).unwrap_or_else(|_| "{}".into()),
            ],
        )
        .context("persist new session")?;

        self.sessions.insert(sid, session.clone());
        Ok(session)
    }

    pub fn get_session(&self, session_id: &str) -> Option<&Session> {
        self.sessions.get(session_id)
    }

    pub fn update_session_state(
        &mut self,
        session_id: &str,
        new_state: SessionState,
    ) -> Result<()> {
        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs_f64();

        let conn = self.open()?;
        conn.execute(
            "UPDATE cloud_sessions SET state = ?1, updated_at = ?2 WHERE session_id = ?3",
            params![new_state.as_str(), now, session_id],
        )
        .context("update session state")?;

        if let Some(sess) = self.sessions.get_mut(session_id) {
            sess.state = new_state;
            sess.updated_at = now;
        }
        Ok(())
    }

    pub fn get_status(&self) -> serde_json::Value {
        let active = self
            .sessions
            .values()
            .filter(|s| s.state == SessionState::Active)
            .count();
        let initializing = self
            .sessions
            .values()
            .filter(|s| s.state == SessionState::Initializing)
            .count();
        let suspended = self
            .sessions
            .values()
            .filter(|s| s.state == SessionState::Suspended)
            .count();
        let completed = self
            .sessions
            .values()
            .filter(|s| s.state == SessionState::Completed)
            .count();
        let failed = self
            .sessions
            .values()
            .filter(|s| s.state == SessionState::Failed)
            .count();
        json!({
            "sessions":       self.sessions.len(),
            "active_sessions": active,
            "initializing":   initializing,
            "suspended":      suspended,
            "completed":      completed,
            "failed":         failed,
            "db_path":        self.db_path.display().to_string(),
        })
    }
}

// ─────────────────────────────────────────────────────────────────
// ResearchEngine — search + fetch orchestration
// ─────────────────────────────────────────────────────────────────

pub struct ResearchEngine {
    pub search_url: String,
    pub lake_path: PathBuf,
}

impl ResearchEngine {
    pub fn new(search_url: &str, lake_path: impl AsRef<Path>) -> Self {
        Self {
            search_url: search_url.to_string(),
            lake_path: lake_path.as_ref().to_path_buf(),
        }
    }

    /// GET `{search_url}?q={query}&limit={limit}`, return results array or empty on error.
    pub async fn search(
        &self,
        query: &str,
        limit: usize,
    ) -> Result<Vec<serde_json::Value>> {
        let url = format!("{}?q={}&limit={}", self.search_url, query, limit);
        let client = reqwest::Client::new();
        let resp = client
            .get(&url)
            .send()
            .await
            .context("research engine search request")?;
        let body: serde_json::Value = resp.json().await.context("parse search response JSON")?;
        // Accept either a top-level array or {"results": [...]}
        if let Some(arr) = body.as_array() {
            return Ok(arr.clone());
        }
        if let Some(arr) = body.get("results").and_then(|v| v.as_array()) {
            return Ok(arr.clone());
        }
        Ok(Vec::new())
    }

    /// Deep research: search, fetch each result URL, ingest to lake, return consolidated result.
    pub async fn deep_research(
        &self,
        query: &str,
        limit: usize,
    ) -> Result<serde_json::Value> {
        let results = self.search(query, limit).await.unwrap_or_default();
        let client = reqwest::Client::builder()
            .timeout(std::time::Duration::from_secs(15))
            .build()
            .unwrap_or_default();

        let mut fetched = Vec::new();
        for item in &results {
            let url_opt = item
                .get("url")
                .or_else(|| item.get("link"))
                .and_then(|v| v.as_str());
            if let Some(url) = url_opt {
                match client.get(url).send().await {
                    Ok(resp) => {
                        let text = resp.text().await.unwrap_or_default();
                        let record = json!({
                            "source_url": url,
                            "query":      query,
                            "content":    &text[..text.len().min(4096)],
                            "timestamp":  chrono::Utc::now().timestamp(),
                        });
                        let _ = self.ingest_to_lake(&record);
                        fetched.push(record);
                    }
                    Err(_) => {
                        // Skip unreachable URLs silently.
                    }
                }
            }
        }

        Ok(json!({
            "query":          query,
            "search_results": results.len(),
            "fetched_pages":  fetched.len(),
            "records":        fetched,
        }))
    }

    /// Append a JSON record as a JSONL line to the lake file.
    fn ingest_to_lake(&self, data: &serde_json::Value) -> Result<()> {
        use std::io::Write;
        if let Some(parent) = self.lake_path.parent() {
            std::fs::create_dir_all(parent).ok();
        }
        let mut file = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(&self.lake_path)
            .with_context(|| format!("open lake file {:?}", self.lake_path))?;
        let line = serde_json::to_string(data)?;
        writeln!(file, "{}", line).context("write lake JSONL line")?;
        Ok(())
    }
}
