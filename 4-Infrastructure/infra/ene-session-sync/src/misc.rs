#![allow(dead_code)]
//! misc.rs — Miscellaneous infrastructure modules.
//!
//! Ports:
//!   tiddlywiki_ene_bridge.py   — TiddlyWiki .tid scanner and ENE bridge
//!   servo_fetch_adapter.py     — Servo-Fetch web surface adapter
//!   web_interaction_surface.py — Web task dispatch
//!   ascii_art_competition.py / ascii_art_store.py — ASCII art generation stubs
//!   s3c_iterative_improvement.py — S3C iterative improvement loop

use anyhow::{Context, Result};
use rusqlite::{params, Connection};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};
use crate::s3c;

// ═════════════════════════════════════════════════════════════════════════════
// §1  TiddlyWiki ENE Bridge
//     Port of tiddlywiki_ene_bridge.py
// ═════════════════════════════════════════════════════════════════════════════

/// Maximum size of a .tid file that will be parsed.
pub const MAX_TIDDLER_BYTES: usize = 512_000;

/// One parsed TiddlyWiki tiddler.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TiddlerRecord {
    /// Absolute path of the .tid file.
    pub path: String,
    pub title: String,
    pub fields: HashMap<String, String>,
    pub text: String,
    /// Tag list extracted from the `tags` field.
    pub tags: Vec<String>,
    /// `[[...]]` link targets found in the body text.
    pub links: Vec<String>,
    /// SHA-256 hex of the raw file bytes.
    pub source_sha256: String,
    pub size_bytes: usize,
}

/// ENE package plan derived from a tiddler.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ENEPackagePlan {
    pub pkg: String,
    pub version: String,
    pub tier: String,
    pub domain: String,
    pub description: String,
    pub tags: Vec<String>,
    pub sha256: String,
}

// ── Internal helpers ──────────────────────────────────────────────────────────

/// SHA-256 of a byte slice, returned as a lowercase hex string.
pub fn sha256_hex(data: &[u8]) -> String {
    let mut h = Sha256::new();
    h.update(data);
    hex::encode(h.finalize())
}

/// Parse a TiddlyWiki `.tid` file.
///
/// The format is:
/// ```text
/// key: value
/// key: value
///
/// body text
/// ```
/// A blank line separates the header section from the body.  The `title`
/// field is extracted from the header; everything after the first blank line
/// is returned as the body string.
pub fn parse_tid_fields(content: &str) -> (HashMap<String, String>, String) {
    let mut fields: HashMap<String, String> = HashMap::new();
    let mut lines = content.lines();
    let mut in_header = true;
    let mut body_lines: Vec<&str> = Vec::new();

    for line in &mut lines {
        if in_header {
            if line.trim().is_empty() {
                // Blank line marks the end of the header block.
                in_header = false;
                continue;
            }
            // Look for the first `: ` separator.
            if let Some(colon_pos) = line.find(": ") {
                let key = line[..colon_pos].trim().to_ascii_lowercase();
                let value = line[colon_pos + 2..].trim().to_string();
                fields.insert(key, value);
            } else {
                // No separator — treat the rest of this file as body.
                in_header = false;
                body_lines.push(line);
            }
        } else {
            body_lines.push(line);
        }
    }

    let text = body_lines.join("\n");
    (fields, text)
}

/// Parse a TiddlyWiki tag string such as `"[[My Tag]] [[Other]] plain"` into
/// individual tag strings.
///
/// Tags wrapped in `[[...]]` may contain spaces; bare words are single tags.
fn parse_tags(tag_str: &str) -> Vec<String> {
    let mut tags: Vec<String> = Vec::new();
    let chars: Vec<char> = tag_str.chars().collect();
    let mut i = 0;
    while i < chars.len() {
        // Skip leading whitespace.
        if chars[i].is_whitespace() {
            i += 1;
            continue;
        }
        if i + 1 < chars.len() && chars[i] == '[' && chars[i + 1] == '[' {
            // Bracketed tag — find the closing `]]`.
            i += 2;
            let start = i;
            while i + 1 < chars.len() && !(chars[i] == ']' && chars[i + 1] == ']') {
                i += 1;
            }
            let tag: String = chars[start..i].iter().collect();
            if !tag.is_empty() {
                tags.push(tag);
            }
            i += 2; // skip `]]`
        } else {
            // Bare word tag — advance until whitespace.
            let start = i;
            while i < chars.len() && !chars[i].is_whitespace() {
                i += 1;
            }
            let tag: String = chars[start..i].iter().collect();
            if !tag.is_empty() {
                tags.push(tag);
            }
        }
    }
    tags
}

/// Find all `[[target]]` or `[[display|target]]` wikilink targets in `text`.
///
/// Returns a deduplicated, stable-order `Vec<String>`.
pub fn extract_links_from_text(text: &str) -> Vec<String> {
    let mut targets: Vec<String> = Vec::new();
    let chars: Vec<char> = text.chars().collect();
    let len = chars.len();
    let mut i = 0;

    while i + 1 < len {
        // Look for `[[`.
        if chars[i] != '[' || chars[i + 1] != '[' {
            i += 1;
            continue;
        }
        i += 2; // skip opening `[[`
        let start = i;

        // Advance until `]]` or end.
        while i + 1 < len && !(chars[i] == ']' && chars[i + 1] == ']') {
            i += 1;
        }
        if i + 1 >= len {
            break;
        }

        let inner: String = chars[start..i].iter().collect();
        i += 2; // skip closing `]]`

        // `[[display|target]]` — take the part after `|`.
        let target = if let Some(pipe) = inner.find('|') {
            inner[pipe + 1..].trim().to_string()
        } else {
            inner.trim().to_string()
        };

        if target.is_empty() {
            continue;
        }
        // Deduplicate while preserving first-seen order.
        if !targets.contains(&target) {
            targets.push(target);
        }
    }

    targets
}

/// Walk `dir` recursively, parse every `.tid` file found, and return a
/// `Vec<TiddlerRecord>`.  Files larger than `MAX_TIDDLER_BYTES` are skipped
/// with a warning printed to stderr.
pub fn scan_tiddlers(dir: impl AsRef<Path>) -> Result<Vec<TiddlerRecord>> {
    let mut records: Vec<TiddlerRecord> = Vec::new();
    scan_tiddlers_inner(dir.as_ref(), &mut records)?;
    Ok(records)
}

fn scan_tiddlers_inner(dir: &Path, out: &mut Vec<TiddlerRecord>) -> Result<()> {
    for entry in std::fs::read_dir(dir).with_context(|| format!("read_dir {:?}", dir))? {
        let entry = entry?;
        let path = entry.path();
        let meta = entry.metadata()?;

        if meta.is_dir() {
            scan_tiddlers_inner(&path, out)?;
            continue;
        }

        if path.extension().and_then(|e| e.to_str()) != Some("tid") {
            continue;
        }

        let size_bytes = meta.len() as usize;
        if size_bytes > MAX_TIDDLER_BYTES {
            eprintln!(
                "misc::scan_tiddlers: skipping {:?} ({} bytes > MAX_TIDDLER_BYTES)",
                path, size_bytes
            );
            continue;
        }

        let raw = std::fs::read(&path)
            .with_context(|| format!("read {:?}", path))?;
        let source_sha256 = sha256_hex(&raw);
        let content = String::from_utf8_lossy(&raw).into_owned();

        let (mut fields, text) = parse_tid_fields(&content);

        let title = fields
            .remove("title")
            .unwrap_or_else(|| {
                path.file_stem()
                    .and_then(|s| s.to_str())
                    .unwrap_or("untitled")
                    .to_string()
            });

        let tags = fields
            .get("tags")
            .map(|s| parse_tags(s))
            .unwrap_or_default();

        let links = extract_links_from_text(&text);

        out.push(TiddlerRecord {
            path: path.to_string_lossy().into_owned(),
            title,
            fields,
            text,
            tags,
            links,
            source_sha256,
            size_bytes,
        });
    }
    Ok(())
}

/// Derive an `ENEPackagePlan` from a `TiddlerRecord`.
///
/// Mapping heuristic mirrors the Python bridge:
/// - `pkg`         → title (snake_case-ified)
/// - `version`     → `fields["version"]` or `"0.1.0"`
/// - `tier`        → first matching tag from `["FOAM","RESEARCH","CORE","STORAGE"]`,
///                   or `"FOAM"` as default
/// - `domain`      → `fields["domain"]` or inferred from tags, default `"compute"`
/// - `description` → first 256 chars of body text
/// - `tags`        → tiddler tags
/// - `sha256`      → source_sha256
pub fn tiddler_to_ene_package(t: &TiddlerRecord) -> ENEPackagePlan {
    let pkg = t.title
        .to_ascii_lowercase()
        .chars()
        .map(|c| if c.is_alphanumeric() { c } else { '_' })
        .collect::<String>();

    let version = t
        .fields
        .get("version")
        .cloned()
        .unwrap_or_else(|| "0.1.0".into());

    const TIER_TAGS: &[&str] = &["FOAM", "RESEARCH", "CORE", "STORAGE", "COMPUTE"];
    let tier = t
        .tags
        .iter()
        .find(|tag| TIER_TAGS.contains(&tag.to_ascii_uppercase().as_str()))
        .cloned()
        .unwrap_or_else(|| "FOAM".into());

    let domain = t
        .fields
        .get("domain")
        .cloned()
        .unwrap_or_else(|| {
            // Infer from tags: look for known domain words.
            for tag in &t.tags {
                let lc = tag.to_ascii_lowercase();
                match lc.as_str() {
                    "compute" | "semantic" | "topology" | "storage" => return lc,
                    _ => {}
                }
            }
            "compute".into()
        });

    let description = t
        .fields
        .get("description")
        .cloned()
        .unwrap_or_else(|| {
            let trimmed = t.text.trim();
            if trimmed.len() > 256 {
                trimmed[..256].to_string()
            } else {
                trimmed.to_string()
            }
        });

    ENEPackagePlan {
        pkg,
        version,
        tier,
        domain,
        description,
        tags: t.tags.clone(),
        sha256: t.source_sha256.clone(),
    }
}

/// Upsert a slice of `TiddlerRecord`s into the `packages` table of an SQLite
/// database at `db_path`.
///
/// The table is created if it does not already exist.  Returns the number of
/// rows successfully upserted.
pub fn upsert_tiddlers_to_db(
    records: &[TiddlerRecord],
    db_path: impl AsRef<Path>,
) -> Result<usize> {
    let conn = Connection::open(db_path.as_ref())
        .with_context(|| format!("open db {:?}", db_path.as_ref()))?;

    conn.execute_batch(
        "CREATE TABLE IF NOT EXISTS packages (
            pkg          TEXT PRIMARY KEY,
            version      TEXT,
            tier         TEXT,
            domain       TEXT,
            description  TEXT,
            tags         TEXT,
            sha256       TEXT,
            source       TEXT,
            indexed_utc  TEXT
        );",
    )?;

    let now_utc = utc_iso8601_now();
    let mut upserted: usize = 0;

    for record in records {
        let plan = tiddler_to_ene_package(record);
        let tags_json = serde_json::to_string(&plan.tags).unwrap_or_else(|_| "[]".into());

        conn.execute(
            "INSERT INTO packages (pkg, version, tier, domain, description, tags, sha256, source, indexed_utc)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9)
             ON CONFLICT(pkg) DO UPDATE SET
                version     = excluded.version,
                tier        = excluded.tier,
                domain      = excluded.domain,
                description = excluded.description,
                tags        = excluded.tags,
                sha256      = excluded.sha256,
                source      = excluded.source,
                indexed_utc = excluded.indexed_utc",
            params![
                plan.pkg,
                plan.version,
                plan.tier,
                plan.domain,
                plan.description,
                tags_json,
                plan.sha256,
                record.path,
                now_utc,
            ],
        )?;
        upserted += 1;
    }

    Ok(upserted)
}

// ═════════════════════════════════════════════════════════════════════════════
// §2  Web Interaction Surface
//     Port of web_interaction_surface.py + servo_fetch_adapter.py
// ═════════════════════════════════════════════════════════════════════════════

/// The kind of web operation to perform.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum DutyType {
    Fetch,
    Search,
    Extract,
    Screenshot,
}

/// A web task dispatched to the Servo-Fetch adapter.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WebTask {
    pub task_id: String,
    pub duty: DutyType,
    pub url: Option<String>,
    pub query: Option<String>,
    pub timeout_secs: u64,
}

/// The result returned by the Servo-Fetch adapter after executing a task.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WebResult {
    pub task_id: String,
    pub success: bool,
    pub content: Option<String>,
    pub error: Option<String>,
    pub elapsed_ms: u64,
}

/// Wraps the `servo-fetch` binary as a web-surface adapter.
///
/// Spawns the binary via `tokio::process::Command`, captures stdout as the
/// result content, and enforces a per-task timeout.
pub struct ServoFetchAdapter {
    pub binary_path: PathBuf,
}

impl ServoFetchAdapter {
    /// Construct a new adapter.
    ///
    /// `binary_path` defaults to the value of the `SERVO_FETCH_PATH`
    /// environment variable, or `"servo-fetch"` if the variable is unset.
    pub fn new(binary_path: Option<PathBuf>) -> Self {
        let path = binary_path.unwrap_or_else(|| {
            std::env::var("SERVO_FETCH_PATH")
                .map(PathBuf::from)
                .unwrap_or_else(|_| PathBuf::from("servo-fetch"))
        });
        Self { binary_path: path }
    }

    /// Execute a `WebTask` and return a `WebResult`.
    ///
    /// Spawns `self.binary_path` with `--json` plus URL or query arguments.
    /// The process is given `task.timeout_secs` seconds before it is killed.
    pub async fn execute(&self, task: &WebTask) -> WebResult {
        let start = std::time::Instant::now();

        let mut cmd = tokio::process::Command::new(&self.binary_path);
        cmd.arg("--json");

        match task.duty {
            DutyType::Fetch | DutyType::Extract | DutyType::Screenshot => {
                if let Some(ref url) = task.url {
                    cmd.args(["--url", url]);
                }
            }
            DutyType::Search => {
                if let Some(ref q) = task.query {
                    cmd.args(["--query", q]);
                } else if let Some(ref url) = task.url {
                    cmd.args(["--url", url]);
                }
            }
        }

        // Add duty-specific flag where relevant.
        match task.duty {
            DutyType::Extract => {
                cmd.arg("--extract");
            }
            DutyType::Screenshot => {
                cmd.arg("--screenshot");
            }
            _ => {}
        }

        cmd.stdout(std::process::Stdio::piped())
            .stderr(std::process::Stdio::piped());

        let spawn_result = cmd.spawn();
        let mut child = match spawn_result {
            Ok(c) => c,
            Err(e) => {
                return WebResult {
                    task_id: task.task_id.clone(),
                    success: false,
                    content: None,
                    error: Some(format!("spawn failed: {}", e)),
                    elapsed_ms: start.elapsed().as_millis() as u64,
                };
            }
        };

        let timeout = tokio::time::Duration::from_secs(task.timeout_secs.max(1));
        // `wait_with_output` consumes child; capture id first for timeout handling.
        let child_id = child.id();
        let output = tokio::time::timeout(timeout, child.wait_with_output()).await;

        let elapsed_ms = start.elapsed().as_millis() as u64;

        match output {
            Ok(Ok(out)) => {
                if out.status.success() {
                    let content = String::from_utf8_lossy(&out.stdout).trim().to_string();
                    WebResult {
                        task_id: task.task_id.clone(),
                        success: true,
                        content: if content.is_empty() { None } else { Some(content) },
                        error: None,
                        elapsed_ms,
                    }
                } else {
                    let stderr = String::from_utf8_lossy(&out.stderr).trim().to_string();
                    WebResult {
                        task_id: task.task_id.clone(),
                        success: false,
                        content: None,
                        error: Some(format!(
                            "exit code {}: {}",
                            out.status.code().unwrap_or(-1),
                            stderr
                        )),
                        elapsed_ms,
                    }
                }
            }
            Ok(Err(e)) => WebResult {
                task_id: task.task_id.clone(),
                success: false,
                content: None,
                error: Some(format!("wait_with_output error: {}", e)),
                elapsed_ms,
            },
            Err(_) => {
                // Timeout — best-effort kill via process id.
                if let Some(pid) = child_id {
                    let _ = std::process::Command::new("kill")
                        .arg(pid.to_string())
                        .status();
                }
                WebResult {
                    task_id: task.task_id.clone(),
                    success: false,
                    content: None,
                    error: Some(format!(
                        "timeout after {} s",
                        task.timeout_secs
                    )),
                    elapsed_ms,
                }
            }
        }
    }

    /// Convenience: fetch a single URL.
    pub async fn fetch(&self, url: &str, timeout_secs: u64) -> WebResult {
        let task = WebTask {
            task_id: sha256_hex(url.as_bytes())[..16].to_string(),
            duty: DutyType::Fetch,
            url: Some(url.to_string()),
            query: None,
            timeout_secs,
        };
        self.execute(&task).await
    }

    /// Convenience: run a search query.
    pub async fn search(&self, query: &str, timeout_secs: u64) -> WebResult {
        let task = WebTask {
            task_id: sha256_hex(query.as_bytes())[..16].to_string(),
            duty: DutyType::Search,
            url: None,
            query: Some(query.to_string()),
            timeout_secs,
        };
        self.execute(&task).await
    }
}

// ═════════════════════════════════════════════════════════════════════════════
// §3  ASCII Art Store
//     Port of ascii_art_competition.py / ascii_art_store.py
// ═════════════════════════════════════════════════════════════════════════════

/// A single ASCII art entry in the competition store.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AsciiArtEntry {
    pub entry_id: String,
    pub title: String,
    pub art: String,
    pub author: String,
    pub score: f64,
    pub created_at_ms: i64,
}

/// SQLite-backed store for ASCII art entries.
pub struct AsciiArtStore {
    pub db_path: PathBuf,
}

impl AsciiArtStore {
    /// Open (or create) the store at `db_path`, initialising tables as needed.
    pub fn new(db_path: impl AsRef<Path>) -> Result<Self> {
        let store = Self {
            db_path: db_path.as_ref().to_path_buf(),
        };
        store.init_tables()?;
        Ok(store)
    }

    /// Create the `ascii_art_entries` table if it does not already exist.
    fn init_tables(&self) -> Result<()> {
        let conn = self.open_conn()?;
        conn.execute_batch(
            "CREATE TABLE IF NOT EXISTS ascii_art_entries (
                entry_id      TEXT PRIMARY KEY,
                title         TEXT,
                art           TEXT,
                author        TEXT,
                score         REAL,
                created_at_ms INTEGER
            );",
        )?;
        Ok(())
    }

    /// Open a connection to the store database.
    fn open_conn(&self) -> Result<Connection> {
        Connection::open(&self.db_path)
            .with_context(|| format!("open ascii_art db {:?}", self.db_path))
    }

    /// Submit a new ASCII art entry.
    ///
    /// The `entry_id` is derived from the SHA-256 of `"<author>:<title>:<ms>"`.
    /// The initial score is `0.0`.
    pub fn submit(&self, title: &str, art: &str, author: &str) -> Result<AsciiArtEntry> {
        let now_ms = now_ms();
        let id_input = format!("{}:{}:{}", author, title, now_ms);
        let entry_id = sha256_hex(id_input.as_bytes())[..32].to_string();

        let entry = AsciiArtEntry {
            entry_id: entry_id.clone(),
            title: title.to_string(),
            art: art.to_string(),
            author: author.to_string(),
            score: 0.0,
            created_at_ms: now_ms,
        };

        let conn = self.open_conn()?;
        conn.execute(
            "INSERT OR REPLACE INTO ascii_art_entries
                (entry_id, title, art, author, score, created_at_ms)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
            params![
                entry.entry_id,
                entry.title,
                entry.art,
                entry.author,
                entry.score,
                entry.created_at_ms,
            ],
        )?;

        Ok(entry)
    }

    /// List entries in insertion order, up to `limit` rows.
    pub fn list_entries(&self, limit: i64) -> Result<Vec<AsciiArtEntry>> {
        let conn = self.open_conn()?;
        let mut stmt = conn.prepare(
            "SELECT entry_id, title, art, author, score, created_at_ms
             FROM ascii_art_entries
             ORDER BY created_at_ms ASC
             LIMIT ?1",
        )?;
        collect_entries(&mut stmt, [limit])
    }

    /// List entries ordered by score descending, up to `limit` rows.
    pub fn top_entries(&self, limit: i64) -> Result<Vec<AsciiArtEntry>> {
        let conn = self.open_conn()?;
        let mut stmt = conn.prepare(
            "SELECT entry_id, title, art, author, score, created_at_ms
             FROM ascii_art_entries
             ORDER BY score DESC
             LIMIT ?1",
        )?;
        collect_entries(&mut stmt, [limit])
    }

    /// Update the score of an existing entry.
    pub fn score_entry(&self, entry_id: &str, score: f64) -> Result<()> {
        let conn = self.open_conn()?;
        conn.execute(
            "UPDATE ascii_art_entries SET score = ?1 WHERE entry_id = ?2",
            params![score, entry_id],
        )?;
        Ok(())
    }
}

/// Helper: collect rows from a prepared ASCII-art SELECT statement.
fn collect_entries(
    stmt: &mut rusqlite::Statement<'_>,
    params: impl rusqlite::Params,
) -> Result<Vec<AsciiArtEntry>> {
    let rows = stmt.query_map(params, |row| {
        Ok(AsciiArtEntry {
            entry_id: row.get(0)?,
            title: row.get(1)?,
            art: row.get(2)?,
            author: row.get(3)?,
            score: row.get(4)?,
            created_at_ms: row.get(5)?,
        })
    })?;
    let mut out = Vec::new();
    for r in rows {
        out.push(r?);
    }
    Ok(out)
}

// ═════════════════════════════════════════════════════════════════════════════
// §4  S3C Iterative Improvement
//     Port of s3c_iterative_improvement.py
// ═════════════════════════════════════════════════════════════════════════════

/// Metrics snapshot produced by one improvement cycle.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImprovementCycle {
    pub cycle_id: u64,
    /// Fraction of states that are "emitted" (S3CState::emitted == true).
    pub emission_ratio: f64,
    /// Mean j_total across all states.
    pub avg_j_total: f64,
    /// Fraction of states where `a == b` (the "throat" condition).
    pub throat_ratio: f64,
    /// Multiplicative scale suggestion = target_emission_ratio / emission_ratio,
    /// clamped to [0.5, 2.0].
    pub suggested_scale: f64,
    /// Human-readable diagnostic notes produced by this cycle.
    pub notes: Vec<String>,
}

/// Runs an iterative self-improvement loop over a stream of `S3CState` samples.
pub struct S3CIterativeImprover {
    pub cycles: Vec<ImprovementCycle>,
    /// Target fraction of states that should be emitted (default: 0.3).
    pub target_emission_ratio: f64,
}

impl S3CIterativeImprover {
    /// Create a new improver.
    ///
    /// `target_emission_ratio` is the desired emission fraction; pass `0.3` for
    /// the default.
    pub fn new(target_emission_ratio: f64) -> Self {
        Self {
            cycles: Vec::new(),
            target_emission_ratio,
        }
    }

    /// Run one improvement cycle over `states` and append the result to
    /// `self.cycles`.
    ///
    /// # Metrics computed
    /// - `emission_ratio`  — count(emitted) / total
    /// - `avg_j_total`     — mean(j_total) across all states
    /// - `throat_ratio`    — count(a == b) / total
    /// - `suggested_scale` — target / emission_ratio, clamped to [0.5, 2.0]
    pub fn run_cycle(&mut self, states: &[s3c::S3CState]) -> ImprovementCycle {
        let cycle_id = self.cycles.len() as u64;
        let total = states.len();

        let (emission_ratio, avg_j_total, throat_ratio) = if total == 0 {
            (0.0_f64, 0.0_f64, 0.0_f64)
        } else {
            let emitted_count = states.iter().filter(|s| s.emit).count();
            let throat_count = states.iter().filter(|s| s.handles.handle_a == s.handles.handle_b).count();
            let j_sum: f64 = states.iter().map(|s| s.j_score.total as f64).sum();

            (
                emitted_count as f64 / total as f64,
                j_sum / total as f64,
                throat_count as f64 / total as f64,
            )
        };

        // Suggested scale: target / actual, clamped to [0.5, 2.0].
        let suggested_scale = if emission_ratio > 0.0 {
            (self.target_emission_ratio / emission_ratio).clamp(0.5, 2.0)
        } else {
            // No emissions at all — push toward max scale.
            2.0_f64
        };

        let mut notes: Vec<String> = Vec::new();

        if total == 0 {
            notes.push("no states provided".into());
        } else {
            notes.push(format!("total_states={}", total));
            notes.push(format!("emission_ratio={:.4}", emission_ratio));
            notes.push(format!("avg_j_total={:.4}", avg_j_total));
            notes.push(format!("throat_ratio={:.4}", throat_ratio));
            notes.push(format!("suggested_scale={:.4}", suggested_scale));

            if emission_ratio < self.target_emission_ratio {
                notes.push(format!(
                    "emission below target ({:.2} < {:.2}): scale up by {:.3}x",
                    emission_ratio, self.target_emission_ratio, suggested_scale
                ));
            } else if emission_ratio > self.target_emission_ratio * 1.5 {
                notes.push(format!(
                    "emission above 1.5× target ({:.2}): scale down by {:.3}x",
                    emission_ratio, suggested_scale
                ));
            } else {
                notes.push("emission within acceptable range".into());
            }

            if throat_ratio > 0.5 {
                notes.push(format!(
                    "high throat ratio ({:.2}): consider widening a/b separation",
                    throat_ratio
                ));
            }
        }

        let cycle = ImprovementCycle {
            cycle_id,
            emission_ratio,
            avg_j_total,
            throat_ratio,
            suggested_scale,
            notes,
        };

        self.cycles.push(cycle.clone());
        cycle
    }

    /// Summarise all completed cycles as a `serde_json::Value`.
    pub fn summary_json(&self) -> serde_json::Value {
        let cycles_json: Vec<serde_json::Value> = self
            .cycles
            .iter()
            .map(|c| {
                serde_json::json!({
                    "cycle_id":        c.cycle_id,
                    "emission_ratio":  c.emission_ratio,
                    "avg_j_total":     c.avg_j_total,
                    "throat_ratio":    c.throat_ratio,
                    "suggested_scale": c.suggested_scale,
                    "notes":           c.notes,
                })
            })
            .collect();

        let last_scale = self
            .cycles
            .last()
            .map(|c| c.suggested_scale)
            .unwrap_or(1.0);

        serde_json::json!({
            "target_emission_ratio": self.target_emission_ratio,
            "total_cycles":          self.cycles.len(),
            "last_suggested_scale":  last_scale,
            "cycles":                cycles_json,
        })
    }
}

// ═════════════════════════════════════════════════════════════════════════════
// Shared time utilities
// ═════════════════════════════════════════════════════════════════════════════

/// Current time as milliseconds since UNIX epoch.
fn now_ms() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as i64
}

/// Current time as an ISO-8601 UTC string (`YYYY-MM-DDTHH:MM:SSZ`).
fn utc_iso8601_now() -> String {
    let secs = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();
    // Manual ISO-8601 formatting to avoid the chrono dep in this module.
    let s = secs % 60;
    let m = (secs / 60) % 60;
    let h = (secs / 3600) % 24;
    let days = secs / 86400;
    // Gregorian calendar: compute year/month/day from epoch days.
    let (year, month, day) = epoch_days_to_ymd(days);
    format!(
        "{:04}-{:02}-{:02}T{:02}:{:02}:{:02}Z",
        year, month, day, h, m, s
    )
}

/// Convert days since the Unix epoch (1970-01-01) to a `(year, month, day)` tuple.
///
/// Uses the proleptic Gregorian calendar algorithm from RFC 5322 / POSIX.
fn epoch_days_to_ymd(days: u64) -> (u64, u64, u64) {
    // Algorithm: civil_from_days (Howard Hinnant)
    let z = days as i64 + 719_468;
    let era = if z >= 0 { z } else { z - 146_096 } / 146_097;
    let doe = (z - era * 146_097) as u64;
    let yoe = (doe - doe / 1460 + doe / 36524 - doe / 146_096) / 365;
    let y = yoe as i64 + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = doy - (153 * mp + 2) / 5 + 1;
    let m = if mp < 10 { mp + 3 } else { mp - 9 };
    let y = if m <= 2 { y + 1 } else { y } as u64;
    (y, m, d)
}
