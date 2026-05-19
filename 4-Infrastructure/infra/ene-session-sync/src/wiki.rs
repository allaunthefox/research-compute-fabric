#![allow(dead_code)]
//! wiki.rs — ENE MediaWiki-like layer (SQLite + PostgreSQL backends).
//!
//! Port of ene_wiki_layer.py (607 lines) and ene_rds_wiki_layer.py.

use anyhow::{anyhow, Context, Result};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

// ── Constants ──────────────────────────────────────────────────────────────────

/// Maximum allowed title length in characters.
pub const MAX_TITLE_LEN: usize = 160;

/// Maximum allowed content size in bytes (256 KB).
pub const MAX_CONTENT_BYTES: usize = 262_144;

// ── Structs ────────────────────────────────────────────────────────────────────

/// A wiki page header (latest-revision summary, no body text).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WikiPage {
    pub slug: String,
    pub title: String,
    pub latest_revision: i64,
    pub updated_at_ms: i64,
    pub receipt: String,
}

/// A full wiki revision including body text, links, and categories.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WikiRevision {
    pub slug: String,
    pub title: String,
    pub revision: i64,
    pub text: String,
    pub author: String,
    pub summary: String,
    pub created_at_ms: i64,
    pub receipt: String,
    pub links: Vec<String>,
    pub categories: Vec<String>,
}

// ── Pure helper functions ──────────────────────────────────────────────────────

/// Trim and collapse whitespace in a wiki title; reject empty or oversized titles.
pub fn normalize_title(title: &str) -> Result<String> {
    let cleaned: String = title
        .split_whitespace()
        .collect::<Vec<_>>()
        .join(" ");
    if cleaned.is_empty() {
        return Err(anyhow!("wiki title is required"));
    }
    if cleaned.len() > MAX_TITLE_LEN {
        return Err(anyhow!("wiki title too long"));
    }
    Ok(cleaned)
}

/// Derive a URL-safe slug from a title.
///
/// Process: normalize → lowercase → strip non-`[a-z0-9._ -]` → spaces→`_` →
/// strip leading/trailing `_`.  If the result is empty, fall back to the first
/// 16 hex chars of the SHA-256 of the normalized title.
pub fn title_slug(title: &str) -> Result<String> {
    let normalized = normalize_title(title)?;
    let lowered = normalized.to_lowercase();
    // Keep only allowed characters.
    let filtered: String = lowered
        .chars()
        .filter(|c| c.is_ascii_alphanumeric() || *c == '.' || *c == '_' || *c == ' ' || *c == '-')
        .collect();
    // Replace whitespace runs with a single underscore.
    let mut slug = String::with_capacity(filtered.len());
    let mut in_space = false;
    for ch in filtered.chars() {
        if ch == ' ' {
            if !in_space {
                slug.push('_');
                in_space = true;
            }
        } else {
            slug.push(ch);
            in_space = false;
        }
    }
    // Strip leading/trailing underscores.
    let slug = slug.trim_matches('_').to_string();
    if slug.is_empty() {
        let hash = sha256_hex(normalized.as_bytes());
        return Ok(hash[..16].to_string());
    }
    Ok(slug)
}

/// SHA-256 of arbitrary bytes, returned as a lowercase hex string.
pub fn sha256_hex(data: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(data);
    hex::encode(hasher.finalize())
}

/// Unix milliseconds → RFC-3339 string with Z suffix, second precision.
///
/// `ms` is milliseconds since the Unix epoch.
pub fn iso_utc_ms(ms: i64) -> String {
    let secs = ms / 1_000;
    // Use chrono for a clean RFC-3339 rendering.
    use chrono::{TimeZone, Utc};
    let dt = Utc.timestamp_opt(secs, 0).single().unwrap_or_else(|| {
        Utc.timestamp_opt(0, 0).single().expect("epoch is valid")
    });
    dt.format("%Y-%m-%dT%H:%M:%SZ").to_string()
}

/// Serialize a `serde_json::Value` to a compact, deterministic JSON string.
///
/// `serde_json::Value` uses `IndexMap` internally for objects (insertion order).
/// To obtain sorted keys we re-serialize through a `BTreeMap`.
pub fn canonical_json(v: &Value) -> String {
    fn to_sorted(v: &Value) -> Value {
        match v {
            Value::Object(map) => {
                // Collect into a BTreeMap so keys are sorted lexicographically.
                let sorted: std::collections::BTreeMap<_, _> = map
                    .iter()
                    .map(|(k, vv)| (k.clone(), to_sorted(vv)))
                    .collect();
                Value::Object(
                    sorted
                        .into_iter()
                        .collect::<serde_json::Map<String, Value>>(),
                )
            }
            Value::Array(arr) => Value::Array(arr.iter().map(to_sorted).collect()),
            other => other.clone(),
        }
    }
    let sorted = to_sorted(v);
    serde_json::to_string(&sorted).unwrap_or_else(|_| "null".to_string())
}

/// Manual `[[...]]` span parser — returns `(inner_text, start_byte)` for each span.
fn wiki_spans(text: &str) -> Vec<&str> {
    let bytes = text.as_bytes();
    let len = bytes.len();
    let mut spans = Vec::new();
    let mut i = 0;
    while i + 1 < len {
        if bytes[i] == b'[' && bytes[i + 1] == b'[' {
            // Find the matching `]]`.
            let start = i + 2;
            let mut j = start;
            while j + 1 < len {
                if bytes[j] == b']' && bytes[j + 1] == b']' {
                    // Reject spans that contain newlines or nested brackets.
                    let inner = &text[start..j];
                    if !inner.contains('\n') && !inner.contains('[') && !inner.contains(']') {
                        spans.push(inner);
                    }
                    i = j + 2;
                    break;
                }
                j += 1;
            }
            if j + 1 >= len {
                // Unclosed span — advance past the opening `[[`.
                i += 2;
            }
        } else {
            i += 1;
        }
    }
    spans
}

/// Extract the link target from a raw `[[...]]` inner string.
///
/// Strip everything from the first `|` or `#` onward.
fn link_target(inner: &str) -> &str {
    let cut = inner
        .find(|c| c == '|' || c == '#')
        .unwrap_or(inner.len());
    &inner[..cut]
}

/// Extract all wiki links from `text`.
///
/// Returns deduplicated, case-insensitively sorted normalized titles.
/// Skips spans whose target (after normalization) starts with `category:`.
pub fn extract_links(text: &str) -> Vec<String> {
    let mut links: Vec<String> = Vec::new();
    for inner in wiki_spans(text) {
        let target = link_target(inner).trim();
        if target.is_empty() {
            continue;
        }
        if let Ok(norm) = normalize_title(target) {
            if !norm.to_lowercase().starts_with("category:") {
                links.push(norm);
            }
        }
    }
    // Deduplicate.
    links.sort_by(|a, b| a.to_lowercase().cmp(&b.to_lowercase()));
    links.dedup_by(|a, b| a.to_lowercase() == b.to_lowercase());
    links
}

/// Extract all `[[Category:...]]` entries from `text`.
///
/// Returns deduplicated, case-insensitively sorted category names (prefix stripped).
pub fn extract_categories(text: &str) -> Vec<String> {
    let mut cats: Vec<String> = Vec::new();
    for inner in wiki_spans(text) {
        let target = link_target(inner).trim();
        // Accept `Category:Foo` or `category:foo` (case-insensitive prefix).
        let lower = target.to_lowercase();
        // The Python CATEGORY_RE also allows whitespace: `Category : Foo`.
        // We replicate that by checking the prefix after collapsing whitespace.
        let condensed: String = target.split_whitespace().collect::<Vec<_>>().join(" ");
        let cond_lower = condensed.to_lowercase();
        // Match `category :` or `category:` prefix.
        let remainder = if cond_lower.starts_with("category :") {
            Some(condensed["category :".len()..].trim().to_string())
        } else if lower.starts_with("category:") {
            Some(target["category:".len()..].trim().to_string())
        } else {
            None
        };
        if let Some(rem) = remainder {
            if let Ok(norm) = normalize_title(&rem) {
                cats.push(norm);
            }
        }
    }
    cats.sort_by(|a, b| a.to_lowercase().cmp(&b.to_lowercase()));
    cats.dedup_by(|a, b| a.to_lowercase() == b.to_lowercase());
    cats
}

/// Compute the deterministic write receipt for a revision.
///
/// Receipt = SHA-256 hex of canonical JSON of
/// `{"author":…,"created_at":…,"revision":…,"slug":…,"text_sha256":…}`.
pub fn write_receipt(
    slug: &str,
    revision: i64,
    text: &str,
    author: &str,
    created_at_ms: i64,
) -> String {
    let text_sha256 = sha256_hex(text.as_bytes());
    // Build a BTreeMap so keys are sorted identically to Python's sort_keys=True.
    let mut map = std::collections::BTreeMap::new();
    map.insert("author", serde_json::Value::String(author.to_string()));
    map.insert(
        "created_at",
        serde_json::Value::Number(serde_json::Number::from(created_at_ms)),
    );
    map.insert(
        "revision",
        serde_json::Value::Number(serde_json::Number::from(revision)),
    );
    map.insert("slug", serde_json::Value::String(slug.to_string()));
    map.insert("text_sha256", serde_json::Value::String(text_sha256));
    let payload = serde_json::to_string(&map).unwrap_or_default();
    sha256_hex(payload.as_bytes())
}

/// Count occurrences of `needle` (as a plain substring) in `haystack`.
#[inline]
fn count_substr(haystack: &str, needle: &str) -> usize {
    if needle.is_empty() {
        return 0;
    }
    let mut count = 0;
    let mut start = 0;
    while let Some(pos) = haystack[start..].find(needle) {
        count += 1;
        start += pos + needle.len();
    }
    count
}

/// Count distinct "word-like" tokens matching `[a-zA-Z][a-zA-Z0-9_]{2,}`.
///
/// This replicates `len(set(re.findall(r"[a-zA-Z][a-zA-Z0-9_]{2,}", lowered)))`.
fn distinct_word_tokens(text: &str) -> usize {
    let bytes = text.as_bytes();
    let len = bytes.len();
    let mut tokens: std::collections::HashSet<String> = std::collections::HashSet::new();
    let mut i = 0;
    while i < len {
        let b = bytes[i];
        // Must start with a letter (a-z after lowering).
        if b.is_ascii_alphabetic() {
            let start = i;
            i += 1;
            while i < len && (bytes[i].is_ascii_alphanumeric() || bytes[i] == b'_') {
                i += 1;
            }
            let word = &text[start..i];
            // Must be at least 3 characters (1 leading + at least 2 more).
            if word.len() >= 3 {
                tokens.insert(word.to_string());
            }
        } else {
            i += 1;
        }
    }
    tokens.len()
}

/// Derive a deterministic 14-axis concept vector for a wiki page.
///
/// Axes 0,1,3,4,8,9,10 are always 0.0.  Active axes:
/// - axis 2  : topology / manifold / links
/// - axis 5  : hash / receipt / verify
/// - axis 6  : sqlite / schema / index
/// - axis 7  : lexical richness (distinct tokens / 500)
/// - axis 11 : proof / lean / theorem
/// - axis 12 : categories / archive / history
/// - axis 13 : author / provenance / attest
///
/// The vector is L2-normalised then rounded to 6 decimal places.
pub fn concept_vector_for_wiki(
    title: &str,
    text: &str,
    links: &[String],
    categories: &[String],
) -> Vec<f64> {
    let combined = format!("{}\n{}", title, text).to_lowercase();
    let mut axes = vec![0.0f64; 14];

    axes[2] = f64::min(
        1.0,
        (count_substr(&combined, "topology") as f64
            + count_substr(&combined, "manifold") as f64
            + links.len() as f64)
            / 12.0,
    );
    axes[5] = f64::min(
        1.0,
        (count_substr(&combined, "hash") as f64
            + count_substr(&combined, "receipt") as f64
            + count_substr(&combined, "verify") as f64)
            / 8.0,
    );
    axes[6] = f64::min(
        1.0,
        (count_substr(&combined, "sqlite") as f64
            + count_substr(&combined, "schema") as f64
            + count_substr(&combined, "index") as f64)
            / 8.0,
    );
    axes[7] = f64::min(1.0, distinct_word_tokens(&combined) as f64 / 500.0);
    axes[11] = f64::min(
        1.0,
        (count_substr(&combined, "proof") as f64
            + count_substr(&combined, "lean") as f64
            + count_substr(&combined, "theorem") as f64)
            / 8.0,
    );
    axes[12] = f64::min(
        1.0,
        (categories.len() as f64
            + count_substr(&combined, "archive") as f64
            + count_substr(&combined, "history") as f64)
            / 8.0,
    );
    axes[13] = f64::min(
        1.0,
        (count_substr(&combined, "author") as f64
            + count_substr(&combined, "provenance") as f64
            + count_substr(&combined, "attest") as f64)
            / 8.0,
    );

    // If all axes are zero, set the lexical richness axis to 1.
    if axes.iter().all(|&x| x == 0.0) {
        axes[7] = 1.0;
    }

    // L2 normalise.
    let norm = axes.iter().map(|x| x * x).sum::<f64>().sqrt();
    axes.iter()
        .map(|&x| {
            if norm > 0.0 {
                // Round to 6 decimal places.
                (x / norm * 1_000_000.0).round() / 1_000_000.0
            } else {
                0.0
            }
        })
        .collect()
}

/// Bin a concept vector into 0–7 genome integers and return the six named axes.
pub fn genome_from_vector(v: &[f64]) -> Value {
    let bins: Vec<u8> = v
        .iter()
        .map(|&x| u8::min(7, (x * 8.0) as u8))
        .collect();
    let get = |idx: usize| -> i64 { bins.get(idx).copied().unwrap_or(0) as i64 };
    json!({
        "mu":  get(1),
        "rho": get(7),
        "c":   get(6),
        "m":   get(2),
        "ne":  get(12),
        "sig": get(13),
    })
}

/// Build the archive_id string for a slug + content_hash pair.
fn archive_id_for(slug: &str, content_hash: &str) -> String {
    format!(
        "json_catalog_ene_wiki_{}_{}",
        slug,
        &content_hash[..content_hash.len().min(16)]
    )
}

/// Build the full archive record dict matching the Python `make_archive_record()`.
pub fn make_archive_record(
    title: &str,
    slug: &str,
    revision: i64,
    text: &str,
    author: &str,
    summary: &str,
    created_at_ms: i64,
    links: &[String],
    categories: &[String],
) -> Value {
    let raw_content = json!({
        "kind":       "ene_wiki_page",
        "title":      title,
        "slug":       slug,
        "revision":   revision,
        "text":       text,
        "author":     author,
        "summary":    summary,
        "links":      links,
        "categories": categories,
    });
    let content_hash = sha256_hex(canonical_json(&raw_content).as_bytes());
    let archive_id = archive_id_for(slug, &content_hash);
    let extracted_text: String = text.chars().take(10_000).collect();
    let extracted_at = iso_utc_ms(created_at_ms);
    json!({
        "archive_id":          archive_id,
        "source_type":         "json_catalog",
        "source_file":         format!("ene-wiki://{}/{}", slug, revision),
        "raw_content":         raw_content,
        "extracted_text":      extracted_text,
        "extracted_at":        extracted_at,
        "content_hash":        content_hash,
        "extraction_version":  "ene_wiki_layer_v1",
    })
}

/// Build the JSONL event dict matching the Python `make_jsonl_event()`.
pub fn make_jsonl_event(record: &Value, concept_vector: &[f64], receipt: &str) -> Value {
    let now_ms = now_unix_ms() as f64 / 1_000.0;
    let raw = &record["raw_content"];
    let slug = raw["slug"].as_str().unwrap_or("");
    let title = raw["title"].as_str().unwrap_or("");
    let links_len = raw["links"]
        .as_array()
        .map(|a| a.len())
        .unwrap_or(0);
    let categories_arr: Vec<Value> = raw["categories"]
        .as_array()
        .cloned()
        .unwrap_or_default();
    let content_hash = record["content_hash"].as_str().unwrap_or("");
    let extracted_at = record["extracted_at"].as_str().unwrap_or("");
    let archive_id = record["archive_id"].as_str().unwrap_or("");
    let extracted_text = record["extracted_text"].as_str().unwrap_or("");

    let pkg = format!("ene/wiki/{}", slug);
    let event_id = format!("ene:{}", archive_id);

    // bind.cost = max(1, len(extracted_text.encode("utf-8"))) << 16
    let text_bytes = extracted_text.len().max(1);
    let cost: i64 = (text_bytes as i64) << 16;

    let mut tags = vec![
        Value::String("ene".to_string()),
        Value::String("wiki".to_string()),
    ];
    for cat in &categories_arr {
        tags.push(cat.clone());
    }

    let data = json!({
        "pkg":          pkg,
        "version":      extracted_at,
        "tier":         "RESEARCH",
        "domain":       "semantic",
        "archetype":    "wiki_page",
        "description":  title,
        "tags":         tags,
        "source":       "ene_wiki_layer",
        "sha256":       content_hash,
        "indexed_utc":  extracted_at,
        "concept_anchor": {
            "domain":     "semantic",
            "concept":    slug,
            "resolution": "FORMING",
        },
        "concept_vector": concept_vector,
        "idea_weights": {
            "wiki_link_count": f64::min(1.0, links_len as f64 / 16.0),
        },
        "analog_map": {
            "mediawiki":  "ene_wiki_layer",
            "archive_id": archive_id,
        },
    });

    json!({
        "t":   now_ms,
        "src": "ene",
        "id":  event_id,
        "op":  "upsert",
        "data": data,
        "genome": genome_from_vector(concept_vector),
        "bind": {
            "lawful":    true,
            "cost":      cost,
            "invariant": "ene_wiki_revision_is_append_only",
            "class":     "informational_bind",
        },
        "provenance": {
            "node":             "ene-wiki-layer",
            "lake_seed":        "local",
            "tailscale_ip":     "",
            "attestation_hash": format!("sha256:{}", receipt),
            "prev_id":          Value::Null,
        },
    })
}

/// Return `true` if the text passes the content admission gate.
///
/// Rejects: oversized text, `<script` tags, `javascript:` URLs.
pub fn admit_write(text: &str) -> bool {
    if text.len() >= MAX_CONTENT_BYTES {
        return false;
    }
    if text.contains("<script") {
        return false;
    }
    if text.to_lowercase().contains("javascript:") {
        return false;
    }
    true
}

/// Current Unix time as milliseconds.
fn now_unix_ms() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as i64
}

// ── ENEWikiLayer (SQLite) ──────────────────────────────────────────────────────

/// SQLite-backed wiki layer.  Drop-in equivalent of `ene_wiki_layer.ENEWikiLayer`.
pub struct ENEWikiLayer {
    pub db_path: PathBuf,
}

impl ENEWikiLayer {
    /// Open (or create) a wiki backed by the SQLite database at `db_path`.
    pub fn new(db_path: impl AsRef<Path>) -> Result<Self> {
        let db_path = db_path.as_ref().to_path_buf();
        if let Some(parent) = db_path.parent() {
            std::fs::create_dir_all(parent)
                .with_context(|| format!("creating db directory {:?}", parent))?;
        }
        let layer = Self { db_path };
        layer.init_tables()?;
        Ok(layer)
    }

    /// Open a raw SQLite connection to the backing database.
    fn open(&self) -> Result<rusqlite::Connection> {
        let conn = rusqlite::Connection::open(&self.db_path)
            .with_context(|| format!("opening sqlite db {:?}", self.db_path))?;
        conn.execute_batch("PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;")?;
        Ok(conn)
    }

    /// Create all tables if they do not exist.
    pub fn init_tables(&self) -> Result<()> {
        let conn = self.open()?;
        conn.execute_batch(
            r#"
            CREATE TABLE IF NOT EXISTS ene_wiki_pages (
                slug             TEXT PRIMARY KEY,
                title            TEXT NOT NULL,
                latest_revision  INTEGER NOT NULL,
                updated_at       INTEGER NOT NULL,
                receipt          TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS ene_wiki_revisions (
                slug             TEXT NOT NULL,
                revision         INTEGER NOT NULL,
                title            TEXT NOT NULL,
                text             TEXT NOT NULL,
                author           TEXT NOT NULL,
                summary          TEXT NOT NULL,
                created_at       INTEGER NOT NULL,
                receipt          TEXT NOT NULL,
                archive_id       TEXT,
                content_hash     TEXT,
                archive_record   TEXT,
                jsonl_event      TEXT,
                PRIMARY KEY (slug, revision)
            );

            CREATE TABLE IF NOT EXISTS ene_wiki_links (
                slug             TEXT NOT NULL,
                target_slug      TEXT NOT NULL,
                target_title     TEXT NOT NULL,
                PRIMARY KEY (slug, target_slug)
            );

            CREATE TABLE IF NOT EXISTS ene_wiki_categories (
                slug             TEXT NOT NULL,
                category         TEXT NOT NULL,
                PRIMARY KEY (slug, category)
            );

            CREATE TABLE IF NOT EXISTS packages (
                pkg              TEXT PRIMARY KEY,
                version          TEXT NOT NULL,
                tier             TEXT,
                domain           TEXT,
                archetype        TEXT,
                description      TEXT,
                tags             TEXT,
                source           TEXT,
                sha256           TEXT,
                indexed_utc      TEXT,
                concept_anchor   TEXT,
                concept_vector   TEXT,
                idea_weights     TEXT,
                analog_map       TEXT
            );
            "#,
        )
        .context("creating wiki tables")?;

        // Ensure optional columns exist on ene_wiki_revisions (schema migration).
        let extra_cols = [
            ("archive_id", "TEXT"),
            ("content_hash", "TEXT"),
            ("archive_record", "TEXT"),
            ("jsonl_event", "TEXT"),
        ];
        let existing: Vec<String> = {
            let mut stmt = conn
                .prepare("PRAGMA table_info(ene_wiki_revisions)")?;
            stmt.query_map([], |row| row.get::<_, String>(1))?
                .filter_map(|r| r.ok())
                .collect()
        };
        for (col, decl) in &extra_cols {
            if !existing.contains(&col.to_string()) {
                conn.execute_batch(&format!(
                    "ALTER TABLE ene_wiki_revisions ADD COLUMN {} {}",
                    col, decl
                ))?;
            }
        }
        Ok(())
    }

    /// Upsert a packages row from a JSONL event.
    fn upsert_package(conn: &rusqlite::Connection, event: &Value) -> Result<()> {
        let data = &event["data"];
        let pkg = data["pkg"].as_str().unwrap_or("");
        let version = data["version"].as_str().unwrap_or("");
        let tier = data["tier"].as_str().unwrap_or("");
        let domain = data["domain"].as_str().unwrap_or("");
        let archetype = data["archetype"].as_str().unwrap_or("");
        let description = data["description"].as_str().unwrap_or("");
        let tags = serde_json::to_string(&data["tags"]).unwrap_or_default();
        let source = data["source"].as_str().unwrap_or("");
        let sha256 = data["sha256"].as_str().unwrap_or("");
        let indexed_utc = data["indexed_utc"].as_str().unwrap_or("");
        let concept_anchor = serde_json::to_string(&data["concept_anchor"]).unwrap_or_default();
        let concept_vector = serde_json::to_string(&data["concept_vector"]).unwrap_or_default();
        let idea_weights = serde_json::to_string(&data["idea_weights"]).unwrap_or_default();
        let analog_map = serde_json::to_string(&data["analog_map"]).unwrap_or_default();

        conn.execute(
            r#"
            INSERT INTO packages (
                pkg, version, tier, domain, archetype, description,
                tags, source, sha256, indexed_utc,
                concept_anchor, concept_vector, idea_weights, analog_map
            ) VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11,?12,?13,?14)
            ON CONFLICT(pkg) DO UPDATE SET
                version        = excluded.version,
                tier           = excluded.tier,
                domain         = excluded.domain,
                archetype      = excluded.archetype,
                description    = excluded.description,
                tags           = excluded.tags,
                source         = excluded.source,
                sha256         = excluded.sha256,
                indexed_utc    = excluded.indexed_utc,
                concept_anchor = excluded.concept_anchor,
                concept_vector = excluded.concept_vector,
                idea_weights   = excluded.idea_weights,
                analog_map     = excluded.analog_map
            "#,
            rusqlite::params![
                pkg, version, tier, domain, archetype, description,
                tags, source, sha256, indexed_utc,
                concept_anchor, concept_vector, idea_weights, analog_map,
            ],
        )
        .context("upserting package")?;
        Ok(())
    }

    /// Write or update a wiki page, appending a new revision.
    pub fn put_page(
        &self,
        title: &str,
        text: &str,
        author: &str,
        summary: &str,
    ) -> Result<WikiRevision> {
        if !admit_write(text) {
            return Err(anyhow!("wiki write rejected: content failed admission gate"));
        }
        let normalized = normalize_title(title)?;
        let slug = title_slug(&normalized)?;
        let created_at_ms = now_unix_ms();

        let conn = self.open()?;

        // Determine next revision number.
        let latest: Option<i64> = conn
            .query_row(
                "SELECT latest_revision FROM ene_wiki_pages WHERE slug = ?1",
                rusqlite::params![&slug],
                |row| row.get(0),
            )
            .optional()
            .context("querying latest revision")?;
        let revision = latest.unwrap_or(0) + 1;

        let links = extract_links(text);
        let categories = extract_categories(text);
        let receipt = write_receipt(&slug, revision, text, author, created_at_ms);
        let archive_record = make_archive_record(
            &normalized,
            &slug,
            revision,
            text,
            author,
            summary,
            created_at_ms,
            &links,
            &categories,
        );
        let concept_vector = concept_vector_for_wiki(&normalized, text, &links, &categories);
        let jsonl_event = make_jsonl_event(&archive_record, &concept_vector, &receipt);

        let archive_id = archive_record["archive_id"].as_str().unwrap_or("").to_string();
        let content_hash = archive_record["content_hash"].as_str().unwrap_or("").to_string();
        let archive_record_json =
            serde_json::to_string(&archive_record).unwrap_or_default();
        let jsonl_event_json = serde_json::to_string(&jsonl_event).unwrap_or_default();

        // Insert revision.
        conn.execute(
            r#"
            INSERT INTO ene_wiki_revisions
                (slug, revision, title, text, author, summary, created_at, receipt,
                 archive_id, content_hash, archive_record, jsonl_event)
            VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11,?12)
            "#,
            rusqlite::params![
                &slug, revision, &normalized, text, author, summary,
                created_at_ms, &receipt,
                &archive_id, &content_hash,
                &archive_record_json, &jsonl_event_json,
            ],
        )
        .context("inserting wiki revision")?;

        // Upsert page header.
        conn.execute(
            r#"
            INSERT INTO ene_wiki_pages (slug, title, latest_revision, updated_at, receipt)
            VALUES (?1,?2,?3,?4,?5)
            ON CONFLICT(slug) DO UPDATE SET
                title           = excluded.title,
                latest_revision = excluded.latest_revision,
                updated_at      = excluded.updated_at,
                receipt         = excluded.receipt
            "#,
            rusqlite::params![&slug, &normalized, revision, created_at_ms, &receipt],
        )
        .context("upserting wiki page")?;

        // Replace links.
        conn.execute(
            "DELETE FROM ene_wiki_links WHERE slug = ?1",
            rusqlite::params![&slug],
        )?;
        for link_title in &links {
            let target_slug = title_slug(link_title).unwrap_or_default();
            conn.execute(
                r#"
                INSERT OR IGNORE INTO ene_wiki_links (slug, target_slug, target_title)
                VALUES (?1,?2,?3)
                "#,
                rusqlite::params![&slug, &target_slug, link_title],
            )
            .context("inserting wiki link")?;
        }

        // Replace categories.
        conn.execute(
            "DELETE FROM ene_wiki_categories WHERE slug = ?1",
            rusqlite::params![&slug],
        )?;
        for cat in &categories {
            conn.execute(
                "INSERT OR IGNORE INTO ene_wiki_categories (slug, category) VALUES (?1,?2)",
                rusqlite::params![&slug, cat],
            )
            .context("inserting wiki category")?;
        }

        Self::upsert_package(&conn, &jsonl_event)?;

        Ok(WikiRevision {
            slug,
            title: normalized,
            revision,
            text: text.to_string(),
            author: author.to_string(),
            summary: summary.to_string(),
            created_at_ms,
            receipt,
            links,
            categories,
        })
    }

    /// Retrieve the latest revision of a page by title, or `None` if not found.
    pub fn get_page(&self, title: &str) -> Result<Option<WikiRevision>> {
        let slug = title_slug(title)?;
        let conn = self.open()?;

        // Find latest revision number from the pages table.
        let latest: Option<i64> = conn
            .query_row(
                "SELECT latest_revision FROM ene_wiki_pages WHERE slug = ?1",
                rusqlite::params![&slug],
                |row| row.get(0),
            )
            .optional()
            .context("querying wiki page")?;
        let revision = match latest {
            Some(r) => r,
            None => return Ok(None),
        };

        // Fetch the revision body.
        let row: Option<(String, String, i64, String, String, String, i64, String)> = conn
            .query_row(
                r#"
                SELECT title, slug, revision, text, author, summary, created_at, receipt
                FROM ene_wiki_revisions
                WHERE slug = ?1 AND revision = ?2
                "#,
                rusqlite::params![&slug, revision],
                |r| {
                    Ok((
                        r.get(0)?,
                        r.get(1)?,
                        r.get(2)?,
                        r.get(3)?,
                        r.get(4)?,
                        r.get(5)?,
                        r.get(6)?,
                        r.get(7)?,
                    ))
                },
            )
            .optional()
            .context("fetching wiki revision")?;

        let (title_db, slug_db, rev, text, author, summary, created_at_ms, receipt_db) =
            match row {
                Some(t) => t,
                None => return Ok(None),
            };

        // Fetch links.
        let mut stmt = conn.prepare(
            "SELECT target_title FROM ene_wiki_links WHERE slug = ?1 ORDER BY lower(target_title)",
        )?;
        let links: Vec<String> = stmt
            .query_map(rusqlite::params![&slug_db], |r| r.get(0))?
            .filter_map(|r| r.ok())
            .collect();

        // Fetch categories.
        let mut stmt = conn.prepare(
            "SELECT category FROM ene_wiki_categories WHERE slug = ?1 ORDER BY lower(category)",
        )?;
        let categories: Vec<String> = stmt
            .query_map(rusqlite::params![&slug_db], |r| r.get(0))?
            .filter_map(|r| r.ok())
            .collect();

        Ok(Some(WikiRevision {
            slug: slug_db,
            title: title_db,
            revision: rev,
            text,
            author,
            summary,
            created_at_ms,
            receipt: receipt_db,
            links,
            categories,
        }))
    }

    /// Search pages by title or slug containing `query` (case-insensitive LIKE).
    pub fn search(&self, query: &str, limit: i64) -> Result<Vec<WikiPage>> {
        let limit = limit.max(1).min(100);
        let term = format!("%{}%", query.trim());
        let conn = self.open()?;
        let mut stmt = conn.prepare(
            r#"
            SELECT slug, title, latest_revision, updated_at, receipt
            FROM ene_wiki_pages
            WHERE title LIKE ?1 OR slug LIKE ?1
            ORDER BY updated_at DESC
            LIMIT ?2
            "#,
        )?;
        let pages: Vec<WikiPage> = stmt
            .query_map(rusqlite::params![&term, limit], |r| {
                Ok(WikiPage {
                    slug: r.get(0)?,
                    title: r.get(1)?,
                    latest_revision: r.get(2)?,
                    updated_at_ms: r.get(3)?,
                    receipt: r.get(4)?,
                })
            })?
            .filter_map(|r| r.ok())
            .collect();
        Ok(pages)
    }

    /// Return slugs of all pages that link *to* `title` via `ene_wiki_links`.
    pub fn backlinks(&self, title: &str) -> Result<Vec<String>> {
        let target_slug = title_slug(title)?;
        let conn = self.open()?;
        let mut stmt = conn.prepare(
            r#"
            SELECT l.slug
            FROM ene_wiki_links l
            JOIN ene_wiki_pages p ON p.slug = l.slug
            WHERE l.target_slug = ?1
            ORDER BY lower(p.title)
            "#,
        )?;
        let slugs: Vec<String> = stmt
            .query_map(rusqlite::params![&target_slug], |r| r.get(0))?
            .filter_map(|r| r.ok())
            .collect();
        Ok(slugs)
    }

    /// Return the most recently changed revisions, newest first.
    pub fn recent_changes(&self, limit: i64) -> Result<Vec<WikiRevision>> {
        let limit = limit.max(1).min(100);
        let conn = self.open()?;
        let mut stmt = conn.prepare(
            r#"
            SELECT r.slug, r.title, r.revision, r.text, r.author, r.summary,
                   r.created_at, r.receipt
            FROM ene_wiki_revisions r
            JOIN ene_wiki_pages p ON p.slug = r.slug AND p.latest_revision = r.revision
            ORDER BY r.created_at DESC
            LIMIT ?1
            "#,
        )?;
        let revs: Vec<WikiRevision> = stmt
            .query_map(rusqlite::params![limit], |r| {
                Ok(WikiRevision {
                    slug: r.get(0)?,
                    title: r.get(1)?,
                    revision: r.get(2)?,
                    text: r.get(3)?,
                    author: r.get(4)?,
                    summary: r.get(5)?,
                    created_at_ms: r.get(6)?,
                    receipt: r.get(7)?,
                    links: Vec::new(),
                    categories: Vec::new(),
                })
            })?
            .filter_map(|r| r.ok())
            .collect();
        Ok(revs)
    }
}

// ── RdsWikiLayer (PostgreSQL / tokio-postgres) ─────────────────────────────────

/// PostgreSQL-backed wiki layer.  Drop-in equivalent of `ene_rds_wiki_layer.ENERDSWikiLayer`.
pub struct RdsWikiLayer {
    pub dsn: String,
}

impl RdsWikiLayer {
    /// Create an `RdsWikiLayer` using the given DSN string.
    ///
    /// Does NOT open a persistent connection — each operation creates a short-lived
    /// connection, matching the Python psycopg2 pattern.
    pub async fn new(dsn: &str) -> Result<Self> {
        Ok(Self {
            dsn: dsn.to_string(),
        })
    }

    /// Open a tokio-postgres connection pair (client + connection driver).
    async fn connect(&self) -> Result<tokio_postgres::Client> {
        let (client, connection) = tokio_postgres::connect(&self.dsn, tokio_postgres::NoTls)
            .await
            .context("connecting to PostgreSQL")?;
        // Drive the connection in a detached task.
        tokio::spawn(async move {
            if let Err(e) = connection.await {
                tracing::warn!("postgres connection error: {}", e);
            }
        });
        Ok(client)
    }

    /// Create all tables in the `ene` schema if they do not exist.
    pub async fn init_tables(&self) -> Result<()> {
        let client = self.connect().await?;
        client
            .batch_execute(
                r#"
                CREATE SCHEMA IF NOT EXISTS ene;

                CREATE TABLE IF NOT EXISTS ene.wiki_pages (
                    slug             TEXT PRIMARY KEY,
                    title            TEXT NOT NULL,
                    latest_revision  INTEGER NOT NULL,
                    updated_at_ms    BIGINT NOT NULL,
                    receipt          TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS ene.wiki_revisions (
                    slug             TEXT NOT NULL,
                    revision         INTEGER NOT NULL,
                    title            TEXT NOT NULL,
                    text             TEXT NOT NULL,
                    author           TEXT NOT NULL DEFAULT 'ene',
                    summary          TEXT NOT NULL DEFAULT '',
                    created_at_ms    BIGINT NOT NULL,
                    receipt          TEXT NOT NULL,
                    archive_id       TEXT,
                    content_hash     TEXT,
                    archive_record   JSONB DEFAULT '{}',
                    jsonl_event      JSONB DEFAULT '{}',
                    PRIMARY KEY (slug, revision)
                );

                CREATE TABLE IF NOT EXISTS ene.wiki_links (
                    slug             TEXT NOT NULL,
                    target_slug      TEXT NOT NULL,
                    target_title     TEXT NOT NULL,
                    PRIMARY KEY (slug, target_slug)
                );

                CREATE TABLE IF NOT EXISTS ene.wiki_categories (
                    slug             TEXT NOT NULL,
                    category         TEXT NOT NULL,
                    PRIMARY KEY (slug, category)
                );

                CREATE TABLE IF NOT EXISTS ene.packages (
                    pkg              TEXT PRIMARY KEY,
                    version          TEXT NOT NULL,
                    tier             TEXT,
                    domain           TEXT,
                    archetype        TEXT,
                    description      TEXT,
                    tags             JSONB DEFAULT '[]',
                    source           TEXT,
                    sha256           TEXT,
                    indexed_utc      TEXT,
                    concept_anchor   JSONB DEFAULT '{}',
                    concept_vector   JSONB DEFAULT '[]',
                    idea_weights     JSONB DEFAULT '{}',
                    analog_map       JSONB DEFAULT '{}'
                );
                "#,
            )
            .await
            .context("initialising PostgreSQL wiki tables")?;
        Ok(())
    }

    /// Write or update a wiki page, appending a new revision.
    pub async fn put_page(
        &self,
        title: &str,
        text: &str,
        author: &str,
        summary: &str,
    ) -> Result<WikiRevision> {
        if !admit_write(text) {
            return Err(anyhow!("wiki write rejected: content failed admission gate"));
        }
        let normalized = normalize_title(title)?;
        let slug = title_slug(&normalized)?;
        let created_at_ms = now_unix_ms();

        let client = self.connect().await?;

        // Determine next revision.
        let latest: Option<i64> = {
            let row = client
                .query_opt(
                    "SELECT latest_revision FROM ene.wiki_pages WHERE slug = $1",
                    &[&slug],
                )
                .await
                .context("querying latest revision")?;
            row.map(|r| r.get::<_, i64>(0))
        };
        let revision = latest.unwrap_or(0) + 1;

        let links = extract_links(text);
        let categories = extract_categories(text);
        let receipt = write_receipt(&slug, revision, text, author, created_at_ms);
        let archive_record = make_archive_record(
            &normalized,
            &slug,
            revision,
            text,
            author,
            summary,
            created_at_ms,
            &links,
            &categories,
        );
        let concept_vector = concept_vector_for_wiki(&normalized, text, &links, &categories);
        let jsonl_event = make_jsonl_event(&archive_record, &concept_vector, &receipt);

        let archive_id = archive_record["archive_id"].as_str().unwrap_or("").to_string();
        let content_hash = archive_record["content_hash"].as_str().unwrap_or("").to_string();

        // Insert revision.
        client
            .execute(
                r#"
                INSERT INTO ene.wiki_revisions
                    (slug, revision, title, text, author, summary, created_at_ms, receipt,
                     archive_id, content_hash, archive_record, jsonl_event)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
                "#,
                &[
                    &slug,
                    &revision,
                    &normalized,
                    &text,
                    &author,
                    &summary,
                    &created_at_ms,
                    &receipt,
                    &archive_id,
                    &content_hash,
                    &archive_record,
                    &jsonl_event,
                ],
            )
            .await
            .context("inserting wiki revision")?;

        // Upsert page header.
        client
            .execute(
                r#"
                INSERT INTO ene.wiki_pages (slug, title, latest_revision, updated_at_ms, receipt)
                VALUES ($1,$2,$3,$4,$5)
                ON CONFLICT (slug) DO UPDATE SET
                    title           = EXCLUDED.title,
                    latest_revision = EXCLUDED.latest_revision,
                    updated_at_ms   = EXCLUDED.updated_at_ms,
                    receipt         = EXCLUDED.receipt
                "#,
                &[&slug, &normalized, &revision, &created_at_ms, &receipt],
            )
            .await
            .context("upserting wiki page")?;

        // Replace links.
        client
            .execute(
                "DELETE FROM ene.wiki_links WHERE slug = $1",
                &[&slug],
            )
            .await?;
        for link_title in &links {
            let target_slug = title_slug(link_title).unwrap_or_default();
            client
                .execute(
                    r#"
                    INSERT INTO ene.wiki_links (slug, target_slug, target_title)
                    VALUES ($1,$2,$3)
                    ON CONFLICT DO NOTHING
                    "#,
                    &[&slug, &target_slug, link_title],
                )
                .await
                .context("inserting wiki link")?;
        }

        // Replace categories.
        client
            .execute(
                "DELETE FROM ene.wiki_categories WHERE slug = $1",
                &[&slug],
            )
            .await?;
        for cat in &categories {
            client
                .execute(
                    "INSERT INTO ene.wiki_categories (slug, category) VALUES ($1,$2) ON CONFLICT DO NOTHING",
                    &[&slug, cat],
                )
                .await
                .context("inserting wiki category")?;
        }

        // Upsert packages.
        let data = &jsonl_event["data"];
        let pkg = data["pkg"].as_str().unwrap_or("");
        let version = data["version"].as_str().unwrap_or("");
        let tier = data["tier"].as_str().unwrap_or("");
        let domain = data["domain"].as_str().unwrap_or("");
        let archetype = data["archetype"].as_str().unwrap_or("");
        let description = data["description"].as_str().unwrap_or("");
        let source = data["source"].as_str().unwrap_or("");
        let sha256_val = data["sha256"].as_str().unwrap_or("");
        let indexed_utc = data["indexed_utc"].as_str().unwrap_or("");

        client
            .execute(
                r#"
                INSERT INTO ene.packages (
                    pkg, version, tier, domain, archetype, description,
                    tags, source, sha256, indexed_utc,
                    concept_anchor, concept_vector, idea_weights, analog_map
                ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)
                ON CONFLICT (pkg) DO UPDATE SET
                    version        = EXCLUDED.version,
                    tier           = EXCLUDED.tier,
                    domain         = EXCLUDED.domain,
                    archetype      = EXCLUDED.archetype,
                    description    = EXCLUDED.description,
                    tags           = EXCLUDED.tags,
                    source         = EXCLUDED.source,
                    sha256         = EXCLUDED.sha256,
                    indexed_utc    = EXCLUDED.indexed_utc,
                    concept_anchor = EXCLUDED.concept_anchor,
                    concept_vector = EXCLUDED.concept_vector,
                    idea_weights   = EXCLUDED.idea_weights,
                    analog_map     = EXCLUDED.analog_map
                "#,
                &[
                    &pkg,
                    &version,
                    &tier,
                    &domain,
                    &archetype,
                    &description,
                    &data["tags"],
                    &source,
                    &sha256_val,
                    &indexed_utc,
                    &data["concept_anchor"],
                    &data["concept_vector"],
                    &data["idea_weights"],
                    &data["analog_map"],
                ],
            )
            .await
            .context("upserting package row")?;

        Ok(WikiRevision {
            slug,
            title: normalized,
            revision,
            text: text.to_string(),
            author: author.to_string(),
            summary: summary.to_string(),
            created_at_ms,
            receipt,
            links,
            categories,
        })
    }

    /// Retrieve the latest revision of a page by title, or `None` if not found.
    pub async fn get_page(&self, title: &str) -> Result<Option<WikiRevision>> {
        let slug = title_slug(title)?;
        let client = self.connect().await?;

        // Find latest revision number.
        let latest = client
            .query_opt(
                "SELECT latest_revision FROM ene.wiki_pages WHERE slug = $1",
                &[&slug],
            )
            .await
            .context("querying wiki page")?;
        let revision: i64 = match latest {
            Some(r) => r.get(0),
            None => return Ok(None),
        };

        // Fetch the revision body.
        let row = client
            .query_opt(
                r#"
                SELECT title, slug, revision, text, author, summary, created_at_ms, receipt
                FROM ene.wiki_revisions
                WHERE slug = $1 AND revision = $2
                "#,
                &[&slug, &revision],
            )
            .await
            .context("fetching wiki revision")?;

        let row = match row {
            Some(r) => r,
            None => return Ok(None),
        };

        let slug_db: String = row.get(1);

        // Fetch links.
        let link_rows = client
            .query(
                "SELECT target_title FROM ene.wiki_links WHERE slug = $1 ORDER BY lower(target_title)",
                &[&slug_db],
            )
            .await?;
        let links: Vec<String> = link_rows.iter().map(|r| r.get(0)).collect();

        // Fetch categories.
        let cat_rows = client
            .query(
                "SELECT category FROM ene.wiki_categories WHERE slug = $1 ORDER BY lower(category)",
                &[&slug_db],
            )
            .await?;
        let categories: Vec<String> = cat_rows.iter().map(|r| r.get(0)).collect();

        Ok(Some(WikiRevision {
            slug: slug_db,
            title: row.get(0),
            revision: row.get(2),
            text: row.get(3),
            author: row.get(4),
            summary: row.get(5),
            created_at_ms: row.get(6),
            receipt: row.get(7),
            links,
            categories,
        }))
    }
}

// ── Rusqlite optional helper ───────────────────────────────────────────────────

/// Extension trait to turn "not found" rusqlite errors into `Option::None`.
trait OptionalExt<T> {
    fn optional(self) -> Result<Option<T>>;
}

impl<T> OptionalExt<T> for rusqlite::Result<T> {
    fn optional(self) -> Result<Option<T>> {
        match self {
            Ok(v) => Ok(Some(v)),
            Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
            Err(e) => Err(anyhow::Error::from(e)),
        }
    }
}
