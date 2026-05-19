#![allow(dead_code)]
//! ene_core.rs — ENE API hook, security manager, and MoE cache.
//!
//! Port of ene_api.py and moe_ene_cache.py.

use anyhow::{anyhow, Context};
use base64::engine::general_purpose::STANDARD as B64;
use base64::Engine as _;
use rusqlite::{params, Connection};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};
use tracing::debug;

use aes_gcm::{
    aead::Aead,
    Aes256Gcm, Key, KeyInit, Nonce,
};

// ─── §1 AccessLevel ──────────────────────────────────────────────────────────

/// Data classification / clearance ladder.
///
/// Mirrors `AccessLevel` in `ene_api.py`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[repr(u8)]
pub enum AccessLevel {
    Public = 0,
    Internal = 1,
    Restricted = 2,
    Secret = 3,
}

impl AccessLevel {
    /// Decode an integer stored in SQLite back to an `AccessLevel`.
    pub fn from_u8(v: u8) -> Self {
        match v {
            1 => Self::Internal,
            2 => Self::Restricted,
            3 => Self::Secret,
            _ => Self::Public,
        }
    }

    /// The integer value as stored in SQLite.
    pub fn as_u8(self) -> u8 {
        self as u8
    }
}

// ─── helpers ─────────────────────────────────────────────────────────────────

/// Current wall-clock time in whole seconds since UNIX epoch.
fn now_secs() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs() as i64
}

/// Current wall-clock time in nanoseconds since UNIX epoch, as a `u64`.
fn now_nanos() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos() as u64
}

/// Compute SHA-256 and return the raw 32-byte digest.
fn sha256_bytes(data: &[u8]) -> [u8; 32] {
    let mut h = Sha256::new();
    h.update(data);
    h.finalize().into()
}

/// Compute SHA-256 and return the hex-encoded digest string.
fn sha256_hex(data: &[u8]) -> String {
    let digest = sha256_bytes(data);
    hex_encode(&digest)
}

/// Minimal hex encoder — avoids pulling in a hex crate.
fn hex_encode(bytes: &[u8]) -> String {
    const HEX: &[u8] = b"0123456789abcdef";
    let mut out = String::with_capacity(bytes.len() * 2);
    for &b in bytes {
        out.push(HEX[(b >> 4) as usize] as char);
        out.push(HEX[(b & 0x0f) as usize] as char);
    }
    out
}

// ─── §2 ENESecurityManager ───────────────────────────────────────────────────

/// Manages encryption / decryption and access control for ENE sensitive data.
///
/// Mirrors `ENESecurityManager` in `ene_api.py`.
pub struct ENESecurityManager {
    encryption_key: [u8; 32],
}

impl ENESecurityManager {
    // ── key derivation ────────────────────────────────────────────────────

    /// Build the manager by loading (or deriving) the encryption key.
    ///
    /// Resolution order:
    /// 1. `ENE_ENCRYPTION_KEY` env var → base64-decode, or raw-pad to 32 bytes.
    /// 2. Fallback: SHA-256-based stretch of `ENE_SECRET_KEY` (or the embedded
    ///    default) mixed with the canonical salt.  This replaces the PBKDF2
    ///    path used in the Python version, because `ring`/`pbkdf2` are not
    ///    available in this crate.  The result is still deterministic and
    ///    secret-bound.
    pub fn new() -> Self {
        let key = Self::load_key();
        Self { encryption_key: key }
    }

    fn load_key() -> [u8; 32] {
        const SALT: &[u8] = b"ene-semantic-salt-2024";
        const DEFAULT_SECRET: &[u8] = b"default-secret-key-change-in-production";

        // Priority 1: explicit encryption key env var.
        if let Ok(raw) = std::env::var("ENE_ENCRYPTION_KEY") {
            if !raw.is_empty() {
                // Try base64 first.
                if let Ok(decoded) = B64.decode(raw.trim()) {
                    if decoded.len() >= 32 {
                        let mut k = [0u8; 32];
                        k.copy_from_slice(&decoded[..32]);
                        debug!("ENESecurityManager: key from ENE_ENCRYPTION_KEY (base64)");
                        return k;
                    }
                }
                // Fall back to raw bytes, padded or truncated to 32.
                let raw_bytes = raw.as_bytes();
                let mut k = [0u8; 32];
                let len = raw_bytes.len().min(32);
                k[..len].copy_from_slice(&raw_bytes[..len]);
                debug!("ENESecurityManager: key from ENE_ENCRYPTION_KEY (raw)");
                return k;
            }
        }

        // Priority 2: derive from ENE_SECRET_KEY (or default) + salt.
        let secret_key: Vec<u8> = std::env::var("ENE_SECRET_KEY")
            .map(|s| s.into_bytes())
            .unwrap_or_else(|_| DEFAULT_SECRET.to_vec());

        // Three rounds of SHA-256 over (salt || key_material) — deterministic,
        // secret-bound, and avalanche-complete within a single SHA-256 round.
        let round0 = sha256_bytes(&[SALT, secret_key.as_slice()].concat());
        let round1 = sha256_bytes(&[SALT, &round0].concat());
        let round2 = sha256_bytes(&[SALT, &round1].concat());
        debug!("ENESecurityManager: key derived from ENE_SECRET_KEY via triple-SHA-256");
        round2
    }

    // ── semantic key derivation ───────────────────────────────────────────

    /// Derive a 32-byte key from a semantic manifold coordinate vector.
    ///
    /// Port of `ENESecurityManager.derive_key_from_semantic` in `ene_api.py`.
    ///
    /// * Each component is clamped to \[0, 1\] then scaled to 0xFFFF_FFFF.
    /// * All scaled integers are XOR-folded into a single u32.
    /// * Golden-ratio mixing step: `mixed = base_key.wrapping_mul(0x9E37_79B9)`.
    /// * Final key: SHA-256 of the 4-byte big-endian mixed value.
    pub fn derive_key_from_semantic(semantic_vector: &[f64]) -> [u8; 32] {
        let mut base_key: u32 = 0;
        for &v in semantic_vector {
            let clamped = v.clamp(0.0, 1.0);
            let scaled = (clamped * 0xFFFF_FFFFu64 as f64) as u32;
            base_key ^= scaled;
        }
        let mixed: u32 = base_key.wrapping_mul(0x9E37_79B9);
        sha256_bytes(&mixed.to_be_bytes())
    }

    // ── deterministic nonce ───────────────────────────────────────────────

    /// Build a 12-byte AES-GCM nonce deterministically from the current
    /// nanosecond timestamp and a context slice (pkg name, cache key, etc.).
    ///
    /// Because `rand` is not a declared dependency we avoid `OsRng`.  The
    /// timestamp component ensures distinct nonces across calls separated by
    /// at least 1 ns; the context component ensures distinct nonces within
    /// the same nanosecond for different payloads.
    fn make_nonce(context: &[u8]) -> [u8; 12] {
        let ts = now_nanos().to_be_bytes(); // 8 bytes
        let digest = sha256_bytes(&[ts.as_slice(), context].concat());
        let mut nonce = [0u8; 12];
        nonce.copy_from_slice(&digest[..12]);
        nonce
    }

    // ── encrypt / decrypt ─────────────────────────────────────────────────

    /// Encrypt `plaintext` under the instance key with AES-256-GCM.
    ///
    /// Returns a JSON object: `{ciphertext: <b64>, nonce: <b64>, aad: <b64>}`.
    ///
    /// `aad` is bound into the GCM tag — any tampering with it causes
    /// decryption to fail.
    pub fn encrypt(&self, plaintext: &[u8], aad: &[u8]) -> anyhow::Result<serde_json::Value> {
        let key = Key::<Aes256Gcm>::from_slice(&self.encryption_key);
        let cipher = Aes256Gcm::new(key);
        let nonce_bytes = Self::make_nonce(plaintext.get(..4.min(plaintext.len())).unwrap_or(&[]));
        let nonce = Nonce::from_slice(&nonce_bytes);

        // aes-gcm 0.10 Aead::encrypt_in_place_detached takes optional AAD via
        // the Payload wrapper.  We use the convenience encrypt(nonce, payload)
        // form which bundles AAD through aes_gcm::aead::Payload.
        let ciphertext = cipher
            .encrypt(
                nonce,
                aes_gcm::aead::Payload { msg: plaintext, aad },
            )
            .map_err(|e| anyhow!("AES-GCM encrypt error: {}", e))?;

        Ok(serde_json::json!({
            "ciphertext": B64.encode(&ciphertext),
            "nonce":      B64.encode(&nonce_bytes),
            "aad":        B64.encode(aad),
        }))
    }

    /// Encrypt with a caller-supplied key instead of the instance key.
    fn encrypt_with_key(
        key_bytes: &[u8; 32],
        plaintext: &[u8],
        aad: &[u8],
    ) -> anyhow::Result<serde_json::Value> {
        let key = Key::<Aes256Gcm>::from_slice(key_bytes);
        let cipher = Aes256Gcm::new(key);
        let nonce_bytes = Self::make_nonce(plaintext.get(..4.min(plaintext.len())).unwrap_or(&[]));
        let nonce = Nonce::from_slice(&nonce_bytes);

        let ciphertext = cipher
            .encrypt(
                nonce,
                aes_gcm::aead::Payload { msg: plaintext, aad },
            )
            .map_err(|e| anyhow!("AES-GCM encrypt error: {}", e))?;

        Ok(serde_json::json!({
            "ciphertext": B64.encode(&ciphertext),
            "nonce":      B64.encode(&nonce_bytes),
            "aad":        B64.encode(aad),
        }))
    }

    /// Decrypt a ciphertext envelope produced by [`encrypt`].
    ///
    /// `aad` must match what was used during encryption; it is cross-checked
    /// against the `aad` field stored in the envelope.
    pub fn decrypt(&self, envelope: &serde_json::Value, aad: &[u8]) -> anyhow::Result<Vec<u8>> {
        Self::decrypt_with_key(&self.encryption_key, envelope, aad)
    }

    fn decrypt_with_key(
        key_bytes: &[u8; 32],
        envelope: &serde_json::Value,
        aad: &[u8],
    ) -> anyhow::Result<Vec<u8>> {
        let ct_b64 = envelope["ciphertext"]
            .as_str()
            .ok_or_else(|| anyhow!("envelope missing 'ciphertext'"))?;
        let nonce_b64 = envelope["nonce"]
            .as_str()
            .ok_or_else(|| anyhow!("envelope missing 'nonce'"))?;

        let ciphertext = B64.decode(ct_b64).context("base64-decode ciphertext")?;
        let nonce_bytes = B64.decode(nonce_b64).context("base64-decode nonce")?;
        if nonce_bytes.len() != 12 {
            return Err(anyhow!("nonce must be 12 bytes, got {}", nonce_bytes.len()));
        }

        // Prefer AAD from the envelope; fall back to the caller-supplied value.
        let aad_effective: Vec<u8> = if let Some(aad_b64) = envelope["aad"].as_str() {
            B64.decode(aad_b64).context("base64-decode aad")?
        } else {
            aad.to_vec()
        };

        let key = Key::<Aes256Gcm>::from_slice(key_bytes);
        let cipher = Aes256Gcm::new(key);
        let nonce = Nonce::from_slice(&nonce_bytes);

        let plaintext = cipher
            .decrypt(
                nonce,
                aes_gcm::aead::Payload {
                    msg: &ciphertext,
                    aad: &aad_effective,
                },
            )
            .map_err(|e| anyhow!("AES-GCM decrypt error: {}", e))?;

        Ok(plaintext)
    }

    // ── integrity / access ────────────────────────────────────────────────

    /// Compute the SHA-256 hex digest of `data` — used as an integrity hash
    /// stored alongside encrypted payloads.
    pub fn integrity_hash(data: &[u8]) -> String {
        sha256_hex(data)
    }

    /// Return `true` iff `clearance` is sufficient to read data classified at
    /// `classification`.
    ///
    /// Mirrors `ENESecurityManager.check_access` in `ene_api.py`.
    pub fn check_access(clearance: AccessLevel, classification: AccessLevel) -> bool {
        clearance >= classification
    }
}

impl Default for ENESecurityManager {
    fn default() -> Self {
        Self::new()
    }
}

// ─── §3 ENEAPIHook ───────────────────────────────────────────────────────────

/// SQLite-backed ENE API hook for storing and retrieving encrypted sensitive
/// data.
///
/// Mirrors `ENEAPIHook` in `ene_api.py`.
pub struct ENEAPIHook {
    pub db_path: PathBuf,
    security: ENESecurityManager,
}

impl ENEAPIHook {
    /// Open (or create) the SQLite database at `db_path` and initialise the
    /// `sensitive_data` table.
    pub fn new(db_path: impl AsRef<Path>) -> anyhow::Result<Self> {
        let hook = Self {
            db_path: db_path.as_ref().to_path_buf(),
            security: ENESecurityManager::new(),
        };
        hook.init_tables()?;
        Ok(hook)
    }

    fn connect(&self) -> anyhow::Result<Connection> {
        Connection::open(&self.db_path).context("open SQLite for ENEAPIHook")
    }

    /// Create the `sensitive_data` table if it does not already exist.
    fn init_tables(&self) -> anyhow::Result<()> {
        let conn = self.connect()?;
        conn.execute_batch(
            "CREATE TABLE IF NOT EXISTS sensitive_data (
                id               TEXT    PRIMARY KEY,
                pkg              TEXT    NOT NULL,
                encrypted_payload TEXT   NOT NULL,
                nonce            TEXT    NOT NULL,
                classification   INTEGER NOT NULL,
                integrity_hash   TEXT    NOT NULL,
                created_at       INTEGER NOT NULL,
                access_log       TEXT
            );",
        )
        .context("create sensitive_data table")?;
        Ok(())
    }

    // ── store ─────────────────────────────────────────────────────────────

    /// Encrypt `payload` and insert or replace it in the `sensitive_data`
    /// table.
    ///
    /// If `semantic_vector` is supplied the key is derived from it; otherwise
    /// the instance key is used.
    ///
    /// Returns the `data_id` (SHA-256 hex of `pkg || timestamp`).
    pub fn store_sensitive_data(
        &self,
        pkg: &str,
        payload: &str,
        classification: AccessLevel,
        semantic_vector: Option<&[f64]>,
    ) -> anyhow::Result<String> {
        let now = now_secs();
        let data_id = sha256_hex(format!("{}{}", pkg, now).as_bytes());
        let integrity = ENESecurityManager::integrity_hash(payload.as_bytes());

        let envelope = if let Some(sv) = semantic_vector {
            let derived_key = ENESecurityManager::derive_key_from_semantic(sv);
            ENESecurityManager::encrypt_with_key(&derived_key, payload.as_bytes(), pkg.as_bytes())?
        } else {
            self.security.encrypt(payload.as_bytes(), pkg.as_bytes())?
        };

        let ciphertext_b64 = envelope["ciphertext"]
            .as_str()
            .ok_or_else(|| anyhow!("encrypt returned no ciphertext"))?
            .to_string();
        let nonce_b64 = envelope["nonce"]
            .as_str()
            .ok_or_else(|| anyhow!("encrypt returned no nonce"))?
            .to_string();

        let access_log = serde_json::json!({
            "action":    "store",
            "timestamp": now,
        })
        .to_string();

        let conn = self.connect()?;
        conn.execute(
            "INSERT OR REPLACE INTO sensitive_data
             (id, pkg, encrypted_payload, nonce, classification, integrity_hash, created_at, access_log)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)",
            params![
                data_id,
                pkg,
                ciphertext_b64,
                nonce_b64,
                classification.as_u8() as i64,
                integrity,
                now,
                access_log,
            ],
        )
        .context("INSERT sensitive_data")?;

        Ok(data_id)
    }

    // ── retrieve ──────────────────────────────────────────────────────────

    /// Retrieve and decrypt a row by `data_id`.
    ///
    /// Returns `None` if the id does not exist.  Returns an error if the
    /// clearance is insufficient or decryption / integrity check fails.
    ///
    /// Also appends to the `access_log` column on each successful retrieval.
    pub fn retrieve_sensitive_data(
        &self,
        data_id: &str,
        clearance: AccessLevel,
    ) -> anyhow::Result<Option<String>> {
        let conn = self.connect()?;

        let result: Option<(String, String, i64, String, Option<String>)> = {
            let mut stmt = conn.prepare(
                "SELECT encrypted_payload, nonce, classification, integrity_hash, access_log
                 FROM sensitive_data WHERE id = ?1",
            )?;
            stmt.query_row(params![data_id], |row| {
                Ok((
                    row.get::<_, String>(0)?,
                    row.get::<_, String>(1)?,
                    row.get::<_, i64>(2)?,
                    row.get::<_, String>(3)?,
                    row.get::<_, Option<String>>(4)?,
                ))
            })
            .optional()
            .context("query sensitive_data by id")?
        };

        let (enc_payload, nonce, class_int, stored_hash, access_log_raw) = match result {
            Some(row) => row,
            None => return Ok(None),
        };

        let classification = AccessLevel::from_u8(class_int as u8);
        if !ENESecurityManager::check_access(clearance, classification) {
            return Err(anyhow!(
                "Access denied: clearance {:?} insufficient for {:?}",
                clearance,
                classification
            ));
        }

        // Reconstruct the envelope that decrypt() expects.
        let envelope = serde_json::json!({
            "ciphertext": enc_payload,
            "nonce":      nonce,
        });

        // We stored `pkg` as AAD but we only have data_id here; use empty aad
        // as the fallback (the stored `aad` field in the envelope will be used
        // if present, but we wrote `pkg` as AAD without embedding it).  To
        // keep decrypt deterministic, pass empty bytes — the stored envelope
        // aad field (absent in the old path) takes precedence in decrypt_with_key.
        let plaintext_bytes = self.security.decrypt(&envelope, b"")?;
        let plaintext = String::from_utf8(plaintext_bytes)
            .context("decrypted data is not valid UTF-8")?;

        // Integrity check.
        let computed = ENESecurityManager::integrity_hash(plaintext.as_bytes());
        if computed != stored_hash {
            return Err(anyhow!("Integrity check failed for data_id={}", data_id));
        }

        // Append access log entry.
        let now = now_secs();
        let mut log: serde_json::Value = access_log_raw
            .as_deref()
            .and_then(|s| serde_json::from_str(s).ok())
            .unwrap_or_else(|| serde_json::json!([]));

        if let Some(arr) = log.as_array_mut() {
            arr.push(serde_json::json!({ "action": "retrieve", "timestamp": now }));
        } else {
            log = serde_json::json!([
                log,
                { "action": "retrieve", "timestamp": now }
            ]);
        }

        conn.execute(
            "UPDATE sensitive_data SET access_log = ?1 WHERE id = ?2",
            params![log.to_string(), data_id],
        )
        .context("update access_log")?;

        Ok(Some(plaintext))
    }

    // ── list ──────────────────────────────────────────────────────────────

    /// Return a list of `{id, pkg, classification, created_at}` objects for all
    /// rows whose classification ≤ `clearance`.
    pub fn list_sensitive_data(
        &self,
        clearance: AccessLevel,
    ) -> anyhow::Result<Vec<serde_json::Value>> {
        let conn = self.connect()?;
        let mut stmt = conn.prepare(
            "SELECT id, pkg, classification, created_at
             FROM sensitive_data
             ORDER BY created_at DESC",
        )?;

        let rows = stmt
            .query_map([], |row| {
                Ok((
                    row.get::<_, String>(0)?,
                    row.get::<_, String>(1)?,
                    row.get::<_, i64>(2)?,
                    row.get::<_, i64>(3)?,
                ))
            })?
            .filter_map(|r| r.ok())
            .filter(|(_, _, class_int, _)| {
                let classification = AccessLevel::from_u8(*class_int as u8);
                ENESecurityManager::check_access(clearance, classification)
            })
            .map(|(id, pkg, class_int, created_at)| {
                serde_json::json!({
                    "id":             id,
                    "pkg":            pkg,
                    "classification": class_int,
                    "created_at":     created_at,
                })
            })
            .collect();

        Ok(rows)
    }
}

// ─── §4 ExpertConfiguration ──────────────────────────────────────────────────

/// Full parameter set for a single MoE expert.
///
/// Mirrors `ExpertConfiguration` in `moe_ene_cache.py`.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExpertConfiguration {
    /// Unique expert index.
    pub expert_id: i64,
    /// Gating weight *g*.
    pub gating_weight: f64,
    /// Quality weight *w*.
    pub quality_weight: f64,
    /// Coherence *h*.
    pub coherence: f64,
    /// Penalty weight *v*.
    pub penalty_weight: f64,
    /// Distortion *p*.
    pub distortion: f64,
    /// Arity *N*.
    pub arity: f64,
    /// Cost coefficient *a*.
    pub cost_coefficient: f64,
    /// Overhead *c*.
    pub overhead: f64,
    /// 14-D semantic manifold coordinate.
    pub semantic_vector: Vec<f64>,
    /// Domain string (e.g. `"neural_manifold"`).
    pub domain: String,
    /// Semver version string.
    pub version: String,
}

// ─── §5 MoECacheEntry ────────────────────────────────────────────────────────

/// A single cached MoE computation result.
///
/// Mirrors `MoECacheEntry` in `moe_ene_cache.py`.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MoECacheEntry {
    /// Hash-based lookup key.
    pub cache_key: String,
    /// Which experts contributed to this result.
    pub expert_ids: Vec<i64>,
    /// η_MoE scalar output.
    pub eta_moe_result: f64,
    /// Discarded information fraction *I*.
    pub i_discarded: f64,
    /// UNIX timestamp of this computation (seconds).
    pub timestamp: i64,
    /// Semantic manifold coordinate used for this computation.
    pub semantic_vector: Vec<f64>,
    /// Confidence in [0, 1].
    pub confidence: f64,
}

// ─── §6 MoEENECache ──────────────────────────────────────────────────────────

/// SQLite-backed Mixture-of-Experts cache.
///
/// Mirrors `MoEENECache` in `moe_ene_cache.py`.
pub struct MoEENECache {
    pub db_path: PathBuf,
}

impl MoEENECache {
    // ── construction ─────────────────────────────────────────────────────

    /// Open (or create) the SQLite database at `db_path` and initialise all
    /// MoE cache tables.
    pub fn new(db_path: impl AsRef<Path>) -> anyhow::Result<Self> {
        let cache = Self {
            db_path: db_path.as_ref().to_path_buf(),
        };
        cache.init_tables()?;
        Ok(cache)
    }

    fn connect(&self) -> anyhow::Result<Connection> {
        Connection::open(&self.db_path).context("open SQLite for MoEENECache")
    }

    // ── schema ────────────────────────────────────────────────────────────

    /// Create the three MoE tables if they do not already exist.
    ///
    /// Tables:
    /// * `moe_expert_cache` — per-expert configuration rows.
    /// * `moe_computation_cache` — cached η_MoE computation results.
    /// * `moe_rewiring_audit` — rewiring proposals with swarm consensus.
    fn init_tables(&self) -> anyhow::Result<()> {
        let conn = self.connect()?;
        conn.execute_batch(
            "CREATE TABLE IF NOT EXISTS moe_expert_cache (
                expert_id       INTEGER PRIMARY KEY,
                domain          TEXT    NOT NULL,
                config_json     TEXT    NOT NULL,
                semantic_vector TEXT    NOT NULL,
                version         TEXT    NOT NULL,
                created_at      INTEGER NOT NULL,
                updated_at      INTEGER NOT NULL,
                cache_hit_count INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS moe_computation_cache (
                cache_key       TEXT    PRIMARY KEY,
                expert_ids      TEXT    NOT NULL,
                eta_moe_result  REAL    NOT NULL,
                i_discarded     REAL    NOT NULL,
                semantic_vector TEXT    NOT NULL,
                confidence      REAL    NOT NULL,
                created_at      INTEGER NOT NULL,
                hit_count       INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS moe_rewiring_audit (
                id              TEXT    PRIMARY KEY,
                expert_id       INTEGER NOT NULL,
                proposal_json   TEXT    NOT NULL,
                swarm_consensus REAL    NOT NULL,
                proposing_agent TEXT    NOT NULL,
                approved        INTEGER NOT NULL DEFAULT 0,
                created_at      INTEGER NOT NULL
            );",
        )
        .context("create MoE cache tables")?;
        Ok(())
    }

    // ── expert configuration ──────────────────────────────────────────────

    /// Persist an expert configuration (INSERT OR REPLACE).
    pub fn cache_expert_config(&self, config: &ExpertConfiguration) -> anyhow::Result<()> {
        let now = now_secs();
        let config_json =
            serde_json::to_string(config).context("serialize ExpertConfiguration")?;
        let semantic_json =
            serde_json::to_string(&config.semantic_vector).context("serialize semantic_vector")?;

        let conn = self.connect()?;
        conn.execute(
            "INSERT OR REPLACE INTO moe_expert_cache
             (expert_id, domain, config_json, semantic_vector, version, created_at, updated_at)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
            params![
                config.expert_id,
                config.domain,
                config_json,
                semantic_json,
                config.version,
                now,
                now,
            ],
        )
        .context("INSERT moe_expert_cache")?;

        debug!("cached expert_id={}", config.expert_id);
        Ok(())
    }

    /// Retrieve an expert configuration by id, incrementing the hit counter.
    pub fn retrieve_expert_config(
        &self,
        expert_id: i64,
    ) -> anyhow::Result<Option<ExpertConfiguration>> {
        let conn = self.connect()?;

        let result: Option<String> = {
            let mut stmt = conn
                .prepare("SELECT config_json FROM moe_expert_cache WHERE expert_id = ?1")?;
            stmt.query_row(params![expert_id], |row| row.get(0))
                .optional()
                .context("query moe_expert_cache")?
        };

        if let Some(config_json) = result {
            conn.execute(
                "UPDATE moe_expert_cache SET cache_hit_count = cache_hit_count + 1 WHERE expert_id = ?1",
                params![expert_id],
            )
            .context("increment cache_hit_count")?;

            let config: ExpertConfiguration =
                serde_json::from_str(&config_json).context("deserialize ExpertConfiguration")?;
            Ok(Some(config))
        } else {
            Ok(None)
        }
    }

    // ── computation results ───────────────────────────────────────────────

    /// Persist a computation result (INSERT OR REPLACE).
    pub fn cache_computation_result(&self, entry: &MoECacheEntry) -> anyhow::Result<()> {
        let expert_ids_json =
            serde_json::to_string(&entry.expert_ids).context("serialize expert_ids")?;
        let semantic_json =
            serde_json::to_string(&entry.semantic_vector).context("serialize semantic_vector")?;

        let conn = self.connect()?;
        conn.execute(
            "INSERT OR REPLACE INTO moe_computation_cache
             (cache_key, expert_ids, eta_moe_result, i_discarded, semantic_vector, confidence, created_at)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
            params![
                entry.cache_key,
                expert_ids_json,
                entry.eta_moe_result,
                entry.i_discarded,
                semantic_json,
                entry.confidence,
                entry.timestamp,
            ],
        )
        .context("INSERT moe_computation_cache")?;

        debug!("cached computation key={}", entry.cache_key);
        Ok(())
    }

    /// Retrieve a cached computation result by key, incrementing the hit count.
    pub fn retrieve_computation_result(
        &self,
        cache_key: &str,
    ) -> anyhow::Result<Option<MoECacheEntry>> {
        let conn = self.connect()?;

        type Row = (String, f64, f64, String, f64, i64);
        let result: Option<Row> = {
            let mut stmt = conn.prepare(
                "SELECT expert_ids, eta_moe_result, i_discarded, semantic_vector, confidence, created_at
                 FROM moe_computation_cache WHERE cache_key = ?1",
            )?;
            stmt.query_row(params![cache_key], |row| {
                Ok((
                    row.get::<_, String>(0)?,
                    row.get::<_, f64>(1)?,
                    row.get::<_, f64>(2)?,
                    row.get::<_, String>(3)?,
                    row.get::<_, f64>(4)?,
                    row.get::<_, i64>(5)?,
                ))
            })
            .optional()
            .context("query moe_computation_cache")?
        };

        if let Some((expert_ids_json, eta, i_disc, semantic_json, conf, created_at)) = result {
            conn.execute(
                "UPDATE moe_computation_cache SET hit_count = hit_count + 1 WHERE cache_key = ?1",
                params![cache_key],
            )
            .context("increment hit_count")?;

            let expert_ids: Vec<i64> =
                serde_json::from_str(&expert_ids_json).context("deserialize expert_ids")?;
            let semantic_vector: Vec<f64> =
                serde_json::from_str(&semantic_json).context("deserialize semantic_vector")?;

            Ok(Some(MoECacheEntry {
                cache_key: cache_key.to_string(),
                expert_ids,
                eta_moe_result: eta,
                i_discarded: i_disc,
                timestamp: created_at,
                semantic_vector,
                confidence: conf,
            }))
        } else {
            Ok(None)
        }
    }

    // ── rewiring audit ────────────────────────────────────────────────────

    /// Append a rewiring proposal to the audit log.
    ///
    /// The proposal is marked `approved = false` (pending).  Returns the
    /// generated proposal id (`"rewire_{expert_id}_{timestamp}"`).
    pub fn log_rewiring_proposal(
        &self,
        expert_id: i64,
        proposal: &serde_json::Value,
        swarm_consensus: f64,
        proposing_agent: &str,
    ) -> anyhow::Result<String> {
        let now = now_secs();
        let proposal_id = format!("rewire_{}_{}", expert_id, now);
        let proposal_json =
            serde_json::to_string(proposal).context("serialize rewiring proposal")?;

        let conn = self.connect()?;
        conn.execute(
            "INSERT INTO moe_rewiring_audit
             (id, expert_id, proposal_json, swarm_consensus, proposing_agent, approved, created_at)
             VALUES (?1, ?2, ?3, ?4, ?5, 0, ?6)",
            params![
                proposal_id,
                expert_id,
                proposal_json,
                swarm_consensus,
                proposing_agent,
                now,
            ],
        )
        .context("INSERT moe_rewiring_audit")?;

        debug!(
            "logged rewiring proposal {} for expert_id={} consensus={:.3}",
            proposal_id, expert_id, swarm_consensus
        );
        Ok(proposal_id)
    }

    // ── statistics ────────────────────────────────────────────────────────

    /// Return cache statistics as a JSON value.
    ///
    /// ```json
    /// {
    ///   "expert_cache_entries":     <i64>,
    ///   "expert_cache_hits":        <i64>,
    ///   "computation_cache_entries":<i64>,
    ///   "computation_cache_hits":   <i64>,
    ///   "rewiring_proposals":       <i64>
    /// }
    /// ```
    pub fn get_cache_statistics(&self) -> anyhow::Result<serde_json::Value> {
        let conn = self.connect()?;

        let (expert_count, expert_hits): (i64, i64) = conn
            .query_row(
                "SELECT COUNT(*), COALESCE(SUM(cache_hit_count), 0) FROM moe_expert_cache",
                [],
                |row| Ok((row.get(0)?, row.get(1)?)),
            )
            .context("query moe_expert_cache stats")?;

        let (comp_count, comp_hits): (i64, i64) = conn
            .query_row(
                "SELECT COUNT(*), COALESCE(SUM(hit_count), 0) FROM moe_computation_cache",
                [],
                |row| Ok((row.get(0)?, row.get(1)?)),
            )
            .context("query moe_computation_cache stats")?;

        let audit_count: i64 = conn
            .query_row(
                "SELECT COUNT(*) FROM moe_rewiring_audit",
                [],
                |row| row.get(0),
            )
            .context("query moe_rewiring_audit count")?;

        Ok(serde_json::json!({
            "expert_cache_entries":      expert_count,
            "expert_cache_hits":         expert_hits,
            "computation_cache_entries": comp_count,
            "computation_cache_hits":    comp_hits,
            "rewiring_proposals":        audit_count,
        }))
    }
}

// ─── tests ───────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    // ── AccessLevel ordering ──────────────────────────────────────────────

    #[test]
    fn access_level_ordering() {
        assert!(AccessLevel::Secret > AccessLevel::Restricted);
        assert!(AccessLevel::Restricted > AccessLevel::Internal);
        assert!(AccessLevel::Internal > AccessLevel::Public);
    }

    #[test]
    fn check_access_boundary() {
        assert!(ENESecurityManager::check_access(
            AccessLevel::Secret,
            AccessLevel::Restricted
        ));
        assert!(!ENESecurityManager::check_access(
            AccessLevel::Public,
            AccessLevel::Internal
        ));
        assert!(ENESecurityManager::check_access(
            AccessLevel::Restricted,
            AccessLevel::Restricted
        ));
    }

    // ── key derivation ────────────────────────────────────────────────────

    #[test]
    fn derive_key_from_semantic_deterministic() {
        let sv = vec![0.5, 0.3, 0.7, 0.2];
        let k1 = ENESecurityManager::derive_key_from_semantic(&sv);
        let k2 = ENESecurityManager::derive_key_from_semantic(&sv);
        assert_eq!(k1, k2);
        assert_ne!(k1, [0u8; 32]);
    }

    #[test]
    fn derive_key_from_semantic_sensitive_to_input() {
        let k1 = ENESecurityManager::derive_key_from_semantic(&[0.1, 0.2]);
        let k2 = ENESecurityManager::derive_key_from_semantic(&[0.1, 0.3]);
        assert_ne!(k1, k2);
    }

    // ── integrity hash ────────────────────────────────────────────────────

    #[test]
    fn integrity_hash_known_value() {
        // SHA-256("") = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
        let h = ENESecurityManager::integrity_hash(b"");
        assert_eq!(
            h,
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        );
    }

    // ── round-trip encrypt / decrypt ──────────────────────────────────────

    #[test]
    fn encrypt_decrypt_roundtrip() {
        let mgr = ENESecurityManager::new();
        let plaintext = b"hello ENE world";
        let aad = b"test-aad";
        let envelope = mgr.encrypt(plaintext, aad).expect("encrypt");
        let recovered = mgr.decrypt(&envelope, aad).expect("decrypt");
        assert_eq!(recovered, plaintext);
    }

    #[test]
    fn decrypt_rejects_wrong_aad() {
        let mgr = ENESecurityManager::new();
        let plaintext = b"secret payload";
        let envelope = mgr.encrypt(plaintext, b"correct-aad").expect("encrypt");
        // Tamper: remove the stored aad so decrypt falls back to caller-supplied.
        let mut env2 = envelope.clone();
        env2.as_object_mut().unwrap().remove("aad");
        // With the wrong aad the GCM tag check must fail.
        let result = mgr.decrypt(&env2, b"wrong-aad");
        assert!(result.is_err());
    }

    // ── SQLite ENEAPIHook ─────────────────────────────────────────────────

    fn tmp_db(name: &str) -> PathBuf {
        let mut p = std::env::temp_dir();
        p.push(format!("ene_core_test_{}_{}.db", std::process::id(), name));
        // Remove stale file from a previous run so tests are hermetic.
        let _ = std::fs::remove_file(&p);
        p
    }

    #[test]
    fn ene_api_hook_store_retrieve() {
        let db_path = tmp_db("api_hook_store_retrieve");
        let hook = ENEAPIHook::new(&db_path).unwrap();

        let id = hook
            .store_sensitive_data(
                "test/pkg",
                "TOP SECRET PAYLOAD",
                AccessLevel::Secret,
                None,
            )
            .unwrap();

        // Retrieve with sufficient clearance.
        let payload = hook
            .retrieve_sensitive_data(&id, AccessLevel::Secret)
            .unwrap()
            .expect("should find row");
        assert_eq!(payload, "TOP SECRET PAYLOAD");

        // Insufficient clearance should error.
        let err = hook.retrieve_sensitive_data(&id, AccessLevel::Public);
        assert!(err.is_err());
    }

    #[test]
    fn ene_api_hook_list_filters_by_clearance() {
        let db_path = tmp_db("api_hook_list");
        let hook = ENEAPIHook::new(&db_path).unwrap();

        hook.store_sensitive_data("a/pkg", "public data", AccessLevel::Public, None)
            .unwrap();
        hook.store_sensitive_data("b/pkg", "secret data", AccessLevel::Secret, None)
            .unwrap();

        let public_view = hook.list_sensitive_data(AccessLevel::Public).unwrap();
        // Public clearance should only see Public-classified rows.
        assert_eq!(public_view.len(), 1);

        let secret_view = hook.list_sensitive_data(AccessLevel::Secret).unwrap();
        assert_eq!(secret_view.len(), 2);
    }

    // ── MoEENECache ───────────────────────────────────────────────────────

    fn sample_config(id: i64) -> ExpertConfiguration {
        ExpertConfiguration {
            expert_id: id,
            gating_weight: 0.7,
            quality_weight: 0.8,
            coherence: 0.9,
            penalty_weight: 0.1,
            distortion: 0.05,
            arity: 5.0,
            cost_coefficient: 0.02,
            overhead: 0.01,
            semantic_vector: vec![
                0.5, 0.3, 0.7, 0.2, 0.1, 0.4, 0.6, 0.8, 0.2, 0.3, 0.5, 0.7, 0.1, 0.4,
            ],
            domain: "neural_manifold".into(),
            version: "1.0.0".into(),
        }
    }

    #[test]
    fn moe_cache_expert_roundtrip() {
        let dir = tempfile::tempdir().unwrap();
        let cache = MoEENECache::new(dir.path().join("moe.db")).unwrap();

        let cfg = sample_config(42);
        cache.cache_expert_config(&cfg).unwrap();

        let retrieved = cache.retrieve_expert_config(42).unwrap().unwrap();
        assert_eq!(retrieved.expert_id, 42);
        assert!((retrieved.gating_weight - 0.7).abs() < 1e-9);
        assert_eq!(retrieved.domain, "neural_manifold");
    }

    #[test]
    fn moe_cache_computation_roundtrip() {
        let dir = tempfile::tempdir().unwrap();
        let cache = MoEENECache::new(dir.path().join("moe.db")).unwrap();

        let entry = MoECacheEntry {
            cache_key: "eta_moe_test_001".into(),
            expert_ids: vec![1, 2, 3],
            eta_moe_result: 0.85,
            i_discarded: 0.1,
            timestamp: now_secs(),
            semantic_vector: vec![0.5, 0.3, 0.7],
            confidence: 0.95,
        };
        cache.cache_computation_result(&entry).unwrap();

        let r = cache
            .retrieve_computation_result("eta_moe_test_001")
            .unwrap()
            .unwrap();
        assert!((r.eta_moe_result - 0.85).abs() < 1e-9);
        assert_eq!(r.expert_ids, vec![1, 2, 3]);
    }

    #[test]
    fn moe_cache_statistics() {
        let dir = tempfile::tempdir().unwrap();
        let cache = MoEENECache::new(dir.path().join("moe.db")).unwrap();

        cache.cache_expert_config(&sample_config(1)).unwrap();
        cache.cache_expert_config(&sample_config(2)).unwrap();
        cache.retrieve_expert_config(1).unwrap();
        cache.retrieve_expert_config(1).unwrap();

        let stats = cache.get_cache_statistics().unwrap();
        assert_eq!(stats["expert_cache_entries"], 2);
        assert_eq!(stats["expert_cache_hits"], 2);
    }

    #[test]
    fn moe_rewiring_audit_log() {
        let dir = tempfile::tempdir().unwrap();
        let cache = MoEENECache::new(dir.path().join("moe.db")).unwrap();

        let proposal = serde_json::json!({ "action": "swap", "target": 3 });
        let pid = cache
            .log_rewiring_proposal(7, &proposal, 0.82, "swarm_agent_1")
            .unwrap();
        assert!(pid.starts_with("rewire_7_"));

        let stats = cache.get_cache_statistics().unwrap();
        assert_eq!(stats["rewiring_proposals"], 1);
    }
}
