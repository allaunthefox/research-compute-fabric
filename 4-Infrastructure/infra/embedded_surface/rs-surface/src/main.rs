/// rs-surface — Rust port of embedded_surface/server.py
///
/// Implements the embedded node surface contract:
/// - HTTP endpoints: /health /status /metrics /primitives /credentials /ws
/// - POST /surface — JSON-framed op dispatch
/// - WebSocket /ws — binary surface-frame protocol (same wire format as Python)
///
/// Surface frame wire format (same as Python server):
///   [version:u8][flags:u8][codec:u8][op:u8][request_id:u32le][payload_len:u32le][crc32:u32le][payload...]
///
/// Op codes (mirror OP_* constants in server.py):
///   0=HEALTH 1=STATUS 2=METRICS 3=ATTEST 4=COMPRESS 5=RGFLOW 6=ROUTE
///   7=MOUNT_STATUS 8=SNAPSHOT 9=ENTER_RECOVERY 10=PRIMITIVES 11=PLAN_ROUTE
///   12=WIKI 13=FRACTAL_FOLD 14=META_AUTOTYPE 15=CREDENTIALS
use anyhow::{anyhow, Result};
use axum::extract::ws::{Message, WebSocket, WebSocketUpgrade};
use axum::extract::State;
use axum::http::StatusCode;
use axum::response::{IntoResponse, Json, Response};
use axum::routing::{get, post};
use axum::Router;
use base64::Engine as _;
use flate2::{read::ZlibDecoder, write::ZlibEncoder, Compression};
use serde_json::{json, Value};
use sha2::Digest as _;
use std::collections::BTreeMap;
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::sync::Arc;
use std::time::{SystemTime, UNIX_EPOCH};
use tokio::net::TcpListener;
use tracing::{info, warn};

// ──────────────────────────────────────────────
// Op codes
// ──────────────────────────────────────────────

const OP_HEALTH: u8 = 0;
const OP_STATUS: u8 = 1;
const OP_METRICS: u8 = 2;
const OP_ATTEST: u8 = 3;
const OP_COMPRESS: u8 = 4;
const OP_RGFLOW: u8 = 5;
const OP_ROUTE: u8 = 6;
const OP_MOUNT_STATUS: u8 = 7;
const OP_SNAPSHOT: u8 = 8;
const OP_ENTER_RECOVERY: u8 = 9;
const OP_PRIMITIVES: u8 = 10;
const OP_PLAN_ROUTE: u8 = 11;
const OP_WIKI: u8 = 12;
const OP_FRACTAL_FOLD: u8 = 13;
const OP_META_AUTOTYPE: u8 = 14;
const OP_CREDENTIALS: u8 = 15;

const CODEC_NONE: u8 = 0;
const CODEC_ZLIB_TEST: u8 = 1;

// ──────────────────────────────────────────────
// Shared state
// ──────────────────────────────────────────────

#[derive(Clone)]
struct AppState {
    profile: Arc<Value>,
    state_dir: PathBuf,
    mount_dir: PathBuf,
    started_at: u64, // unix seconds
}

// ──────────────────────────────────────────────
// Helpers
// ──────────────────────────────────────────────

fn now_secs() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs()
}

fn now_float() -> f64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs_f64()
}

fn iso_utc_now() -> String {
    let secs = now_secs();
    // Minimal ISO-8601 without chrono (same approach as meta_autotype.rs)
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
    let dim: [u64; 12] = [31, if leap { 29 } else { 28 }, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    let mut month = 12u64;
    let mut day_rem = rem;
    for (i, &days) in dim.iter().enumerate() {
        if day_rem < days {
            month = i as u64 + 1;
            break;
        }
        day_rem -= days;
    }
    format!("{:04}-{:02}-{:02}T{:02}:{:02}:{:02}", year, month, day_rem + 1, h, m, sec)
}

fn sha256_hex(data: &[u8]) -> String {
    let mut h = sha2::Sha256::new();
    h.update(data);
    hex::encode(h.finalize())
}

fn crc32_of(data: &[u8]) -> u32 {
    // CRC-32 (IEEE 802.3 polynomial) — matches Python's zlib.crc32
    let mut crc: u32 = 0xFFFF_FFFF;
    for &byte in data {
        crc ^= u32::from(byte);
        for _ in 0..8 {
            crc = if crc & 1 == 1 {
                (crc >> 1) ^ 0xEDB8_8320
            } else {
                crc >> 1
            };
        }
    }
    crc ^ 0xFFFF_FFFF
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

fn zlib_compress(data: &[u8]) -> Vec<u8> {
    let mut encoder = ZlibEncoder::new(Vec::new(), Compression::new(6));
    encoder.write_all(data).ok();
    encoder.finish().unwrap_or_default()
}

fn zlib_decompress(data: &[u8]) -> Result<Vec<u8>> {
    let mut decoder = ZlibDecoder::new(data);
    let mut out = Vec::new();
    decoder.read_to_end(&mut out)?;
    Ok(out)
}

// ──────────────────────────────────────────────
// Profile & state
// ──────────────────────────────────────────────

fn load_profile() -> Result<Value> {
    let path = std::env::var("RS_SURFACE_PROFILE")
        .unwrap_or_else(|_| "/etc/rs-surface/node.json".to_string());
    let content = std::fs::read_to_string(&path)
        .map_err(|e| anyhow!("cannot read profile {}: {}", path, e))?;
    Ok(serde_json::from_str(&content)?)
}

fn ensure_state(state_dir: &Path, mount_dir: &Path, profile: &Value) -> Result<()> {
    std::fs::create_dir_all(state_dir)?;
    std::fs::create_dir_all(mount_dir)?;
    let node_id_path = state_dir.join("node-id");
    if !node_id_path.exists() {
        let node_id = profile["node_id"].as_str().unwrap_or("unknown");
        std::fs::write(&node_id_path, format!("{}\n", node_id))?;
    }
    let last_good_path = state_dir.join("last-good.json");
    if !last_good_path.exists() {
        std::fs::write(
            &last_good_path,
            format!("{{\"ok\":true,\"created_at\":{}}}\n", now_float()),
        )?;
    }
    Ok(())
}

fn resolve_bind_host(profile: &Value) -> String {
    if let Ok(host) = std::env::var("RS_SURFACE_HOST") {
        return host;
    }
    let api = &profile["api"];
    match api.get("bind").and_then(|v| v.as_str()) {
        Some("localhost") => "127.0.0.1".to_string(),
        Some("tailscale") => api
            .get("tailscale_ip")
            .and_then(|v| v.as_str())
            .or_else(|| profile.get("tailscale_ip").and_then(|v| v.as_str()))
            .unwrap_or("127.0.0.1")
            .to_string(),
        _ => "0.0.0.0".to_string(), // "public" or missing
    }
}

// ──────────────────────────────────────────────
// Storage status
// ──────────────────────────────────────────────

fn storage_status(mount_dir: &Path) -> &'static str {
    if mount_dir.join(".rs-surface-mounted").exists() {
        "mounted"
    } else if mount_dir.exists() {
        "degraded"
    } else {
        "absent"
    }
}

// ──────────────────────────────────────────────
// Payload builders (mirror Python functions)
// ──────────────────────────────────────────────

fn health_payload(state: &AppState) -> Value {
    json!({
        "ok": true,
        "node": state.profile["node_id"],
        "role": state.profile["role"],
        "mode": state.profile.get("mode_default").unwrap_or(&json!("normal")),
        "surface_version": state.profile["surface_version"],
        "storage": storage_status(&state.mount_dir),
        "last_good": state.state_dir.join("last-good.json").exists(),
        "uptime_seconds": (now_secs() - state.started_at) as f64,
    })
}

fn status_payload(state: &AppState) -> Value {
    json!({
        "profile": *state.profile,
        "state_dir": state.state_dir.display().to_string(),
        "mount_dir": state.mount_dir.display().to_string(),
        "hostname": gethostname(),
    })
}

fn gethostname() -> String {
    std::fs::read_to_string("/etc/hostname")
        .unwrap_or_else(|_| "unknown".to_string())
        .trim()
        .to_string()
}

fn metrics_payload(state: &AppState) -> Value {
    let mut state_bytes: u64 = 0;
    if let Ok(entries) = std::fs::read_dir(&state.state_dir) {
        for entry in entries.flatten() {
            if let Ok(meta) = entry.metadata() {
                if meta.is_file() {
                    state_bytes += meta.len();
                }
            }
        }
    }
    json!({
        "uptime_seconds": (now_secs() - state.started_at) as f64,
        "state_bytes": state_bytes,
        "state_budget_mb": state.profile.get("local_state_budget_mb"),
    })
}

fn primitive_payload(state: &AppState) -> Value {
    let substrate = state.profile.get("topological_substrate").cloned().unwrap_or(json!({}));
    let primitives = substrate.get("primitives").cloned().unwrap_or_else(|| {
        json!([
            "health", "status", "metrics", "attest", "compress", "rgflow",
            "route", "mount_status", "snapshot", "recovery", "plan_route",
            "wiki", "fractal_fold", "meta_autotype", "credentials",
        ])
    });
    json!({
        "node": state.profile["node_id"],
        "role": state.profile["role"],
        "substrate": substrate,
        "primitives": primitives,
    })
}

// ──────────────────────────────────────────────
// RGFlow heuristic
// ──────────────────────────────────────────────

fn rgflow_score(data: &[u8]) -> Value {
    if data.is_empty() {
        return json!({
            "lawful": true,
            "score": 1.0,
            "reason": "empty-control-frame",
        });
    }
    let unique = {
        let mut seen = [false; 256];
        for &b in data {
            seen[b as usize] = true;
        }
        seen.iter().filter(|&&v| v).count()
    };
    let density = unique as f64 / 256.0;
    let compressed = zlib_compress(data);
    let ratio = compressed.len() as f64 / data.len().max(1) as f64;
    let lawful = ratio < 0.98 || data.len() < 512;
    json!({
        "lawful": lawful,
        "score": (1.0_f64 - ratio + density).max(0.0).round_to(6),
        "compression_ratio": ratio.round_to(6),
        "byte_diversity": density.round_to(6),
        "reason": "test-rgflow-heuristic",
    })
}

trait RoundTo {
    fn round_to(self, places: u32) -> Self;
}
impl RoundTo for f64 {
    fn round_to(self, places: u32) -> Self {
        let factor = 10f64.powi(places as i32);
        (self * factor).round() / factor
    }
}

// ──────────────────────────────────────────────
// Plan-route (omni_lut/unified_compression_route) — self-contained Rust port
// ──────────────────────────────────────────────

fn shannon_entropy(data: &[u8]) -> f64 {
    if data.is_empty() {
        return 0.0;
    }
    let mut counts = [0u64; 256];
    for &b in data {
        counts[b as usize] += 1;
    }
    let total = data.len() as f64;
    -counts
        .iter()
        .filter(|&&c| c > 0)
        .map(|&c| {
            let p = c as f64 / total;
            p * p.log2()
        })
        .sum::<f64>()
}

fn detect_sequence_surface(data: &[u8]) -> Option<&'static str> {
    let text: String = data
        .iter()
        .filter(|&&b| !b.is_ascii_whitespace())
        .map(|&b| b.to_ascii_uppercase() as char)
        .collect();
    if text.is_empty() {
        return None;
    }
    if text.chars().all(|c| matches!(c, 'A' | 'C' | 'G' | 'T')) {
        return Some("dna");
    }
    if text.chars().all(|c| matches!(c, 'A' | 'C' | 'G' | 'U')) {
        return Some("rna");
    }
    if text.chars().all(|c| matches!(c, 'A' | 'C' | 'G' | 'T' | 'U')) {
        return Some("mrna");
    }
    None
}

fn s3c_shear(seed: u64) -> u64 {
    // Minimal MS3C shear heuristic (mirrors matroska_s3c_reduction_gear.py)
    let k = (seed as f64).sqrt() as u64;
    let a = seed.saturating_sub(k * k);
    let b0 = (k + 1) * (k + 1) - 1 - seed.min((k + 1) * (k + 1) - 1);
    // shear = |b+ - mirror_delta| bounded to u8 range
    let mass = a + b0;
    ((mass ^ (seed >> 3)) & 0xFF) as u64
}

fn choose_route(data: &[u8]) -> Value {
    let compressed = zlib_compress(data);
    let unique = {
        let mut seen = [false; 256];
        for &b in data {
            seen[b as usize] = true;
        }
        seen.iter().filter(|&&v| v).count()
    };
    let zlib_ratio = compressed.len() as f64 / data.len().max(1) as f64;
    let byte_diversity = unique as f64 / 256.0;
    let entropy = shannon_entropy(data);
    let seed = if data.len() >= 8 {
        u64::from_be_bytes(data[..8].try_into().unwrap_or([0; 8]))
    } else {
        let mut buf = [0u8; 8];
        buf[..data.len()].copy_from_slice(data);
        u64::from_be_bytes(buf)
    };
    let shear = s3c_shear(seed);
    let sequence_surface = detect_sequence_surface(data);

    let probe = json!({
        "raw_bytes": data.len(),
        "zlib_bytes": compressed.len(),
        "zlib_ratio": zlib_ratio.round_to(6),
        "byte_diversity": byte_diversity.round_to(6),
        "entropy": entropy.round_to(6),
        "integer_seed": seed,
        "sequence_surface": sequence_surface,
    });
    let ms3c_codon = json!({
        "shear": shear,
        "claim_status": "route_prior_geometry_not_physical_brane_claim",
    });

    let (surface, motif, witness, compressor, rg_lawful, score, reason) = if data.len() <= 4 {
        ("binary_control_lane", "gcl_recovery", "informaton_bind", "none", true, 0.95f64, "tiny recovery/control payload")
    } else if let Some(seq) = sequence_surface {
        let motif = if compressed.len() < data.len() { "gcl_compression" } else { "gcl_admission" };
        (seq, motif, "informaton_bind", "sequence_bitpack", true, 0.8f64, "sequence surface detected by finite alphabet")
    } else if zlib_ratio < 0.8 {
        ("byte_payload", "gcl_compression", "informaton_bind", "zlib_test_then_delta_gcl", true, 0.75f64, "payload has ordinary compression structure")
    } else if shear >= 144 {
        ("ms3c_shell_codon", "ms3c_reduction_gear", "informaton_genome", "ms3c_route_prior_then_delta_gcl", true, 0.65f64, "high shell shear route-prior")
    } else {
        ("byte_payload", "gcl_admission", "informaton_bind", "delta_gcl", true, 0.5f64, "default admission before expansion")
    };

    json!({
        "v": "unified-compression-route-0.1",
        "claim_status": "route_selection_not_execution_authority",
        "workload": "auto",
        "probe": probe,
        "ms3c_codon": ms3c_codon,
        "decision": {
            "surface": surface,
            "motif": motif,
            "witness": witness,
            "compressor": compressor,
            "rg_lawful": rg_lawful,
            "score": score,
            "reason": reason,
        },
        "nanokernel_tuple": {
            "surface": surface,
            "motif": motif,
            "witness": witness,
            "compressor": compressor,
        },
        "gcl_required_gate": [
            "OBSERVE", "BIND", "ROUTE", "SIGMA_CHECK",
            "POLICY_CHECK", "DAG_CHECK", "VERIFY", "RECEIPT",
        ],
    })
}

// ──────────────────────────────────────────────
// Meta-autotype (inline port of ene_meta_autotype.py)
// ──────────────────────────────────────────────

fn meta_autotype_handle(request: &Value) -> Value {
    let data: Vec<u8> = if let Some(b64) = request.get("data_b64").and_then(|v| v.as_str()) {
        base64::engine::general_purpose::STANDARD
            .decode(b64)
            .unwrap_or_default()
    } else {
        request
            .get("text")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .as_bytes()
            .to_vec()
    };
    let name = request
        .get("name")
        .and_then(|v| v.as_str())
        .unwrap_or("payload");
    meta_autotype_payload(&data, name)
}

fn meta_autotype_payload(data: &[u8], name: &str) -> Value {
    const VERSION: &str = "ene_meta_autotype_v1";
    let text = String::from_utf8_lossy(data).into_owned();
    let parsed: Option<Value> = serde_json::from_str(&text).ok();

    // Build contingent fields
    let fields: Vec<Value> = match &parsed {
        Some(Value::Object(map)) => {
            let mut keys: Vec<_> = map.keys().cloned().collect();
            keys.sort();
            keys.iter()
                .map(|k| {
                    let v = &map[k];
                    let inf = scalar_type_str(v);
                    let bc = bind_class_for_str(k, inf);
                    json!({
                        "name": k, "inferred_type": inf, "confidence": 0.85,
                        "extraction_rule": format!("json_pointer:/{}", k),
                        "bind_class": bc, "status": "contingent",
                    })
                })
                .collect()
        }
        Some(Value::Array(_)) => vec![json!({
            "name": "items", "inferred_type": "array", "confidence": 0.8,
            "extraction_rule": "json_root_array", "bind_class": "informational_bind",
            "status": "contingent",
        })],
        _ => {
            let mut tokens: Vec<String> = text
                .split(|c: char| !c.is_alphanumeric() && c != '_')
                .filter(|s| s.len() >= 3 && s.starts_with(|c: char| c.is_alphabetic() || c == '_'))
                .map(|s| s.to_string())
                .collect::<std::collections::BTreeSet<_>>()
                .into_iter()
                .take(64)
                .collect();
            tokens.sort();
            tokens.truncate(16);
            tokens
                .iter()
                .map(|token| {
                    let bc = bind_class_for_str(token, "string");
                    json!({
                        "name": token, "inferred_type": "token", "confidence": 0.45,
                        "extraction_rule": "regex_identifier_token",
                        "bind_class": bc, "status": "contingent",
                    })
                })
                .collect()
        }
    };

    let hint = surface_hint_str(&text, parsed.as_ref());

    let raw_content = json!({
        "kind": "ene_meta_autotype",
        "version": VERSION,
        "name": name,
        "surface_hint": hint,
        "byte_len": data.len(),
        "contingent_fields": fields,
        "policy": {
            "defined_ingestion_surface": hint != "unknown_surface",
            "authority": "contingent_until_bound_by_ingestion_surface",
            "required_gate": ["OBSERVE","BIND","ROUTE","POLICY_CHECK","VERIFY","RECEIPT"],
        },
    });

    let content_hash = sha256_hex(canonical_json(&raw_content).as_bytes());
    let receipt_pre = json!({ "v": VERSION, "content_hash": content_hash, "name": name });
    let receipt = sha256_hex(canonical_json(&receipt_pre).as_bytes());

    json!({
        "ok": true,
        "op": "meta_autotype",
        "surface_hint": hint,
        "field_count": fields.len(),
        "archive_record": {
            "archive_id": format!("json_catalog_ene_meta_autotype_{}", &content_hash[..16]),
            "source_type": "json_catalog",
            "source_file": format!("ene-meta-autotype://{}", &content_hash[..16]),
            "raw_content": raw_content,
            "extracted_text": &text[..text.len().min(10000)],
            "extracted_at": iso_utc_now(),
            "content_hash": content_hash,
            "extraction_version": VERSION,
        },
        "jsonl_event": {
            "src": "ene", "op": "upsert",
            "data": {
                "pkg": format!("ene/meta-autotype/{}", &receipt[..16]),
                "version": VERSION, "tier": "RESEARCH", "domain": "semantic",
                "archetype": "contingent_schema",
                "tags": ["ene", "meta_autotype", hint],
                "sha256": &content_hash,
            },
            "bind": {
                "lawful": true, "class": "informational_bind",
                "invariant": "contingent_fields_are_not_authoritative",
            },
            "provenance": { "attestation_hash": format!("sha256:{}", receipt) },
        },
        "receipt": receipt,
    })
}

fn scalar_type_str(v: &Value) -> &'static str {
    match v {
        Value::Bool(_) => "boolean",
        Value::Number(n) => if n.is_f64() { "float" } else { "integer" },
        Value::Array(_) => "array",
        Value::Object(_) => "object",
        Value::Null => "null",
        Value::String(s) => {
            if s.len() == 64 && s.chars().all(|c| c.is_ascii_hexdigit()) { return "sha256_hex"; }
            if s.parse::<i64>().is_ok() { return "integer_string"; }
            if s.parse::<f64>().is_ok() && s.contains('.') { return "float_string"; }
            if s.starts_with("http://") || s.starts_with("https://") { return "url"; }
            "string"
        }
    }
}

fn bind_class_for_str(name: &str, inferred_type: &str) -> &'static str {
    let lower = name.to_lowercase();
    if inferred_type == "sha256_hex" || lower.contains("hash") || lower.contains("receipt") {
        return "attestation_bind";
    }
    if ["x", "y", "z", "coord", "manifold", "topology", "graph"].iter().any(|t| lower.contains(t)) {
        return "geometric_bind";
    }
    if ["policy", "allow", "deny", "risk", "security"].iter().any(|t| lower.contains(t)) {
        return "control_bind";
    }
    "informational_bind"
}

fn surface_hint_str(text: &str, parsed: Option<&Value>) -> &'static str {
    let lower = text.to_lowercase();
    if let Some(Value::Object(map)) = parsed {
        let keys: std::collections::HashSet<&str> = map.keys().map(|k| k.as_str()).collect();
        if keys.contains("nodes") || keys.contains("edges") || lower.contains("graphml") {
            return "graph_concept_surface";
        }
        if keys.contains("archive_id") && keys.contains("source_type") && keys.contains("raw_content") {
            return "ene_archive_surface";
        }
        if keys.contains("pkg") && keys.contains("tier") && keys.contains("domain") {
            return "ene_package_surface";
        }
    }
    if lower.contains("<graphml") { return "graphml_surface"; }
    if lower.contains("[[") && lower.contains("]]") { return "wiki_surface"; }
    "unknown_surface"
}

// ──────────────────────────────────────────────
// Credential helpers (stub — production reads from env/profile)
// ──────────────────────────────────────────────

fn credential_status() -> Value {
    json!({
        "ok": true,
        "providers": ["env"],
        "source": "rs-surface-credential-provider",
        "version": "1.0.0",
    })
}

fn provider_manifest() -> Value {
    json!({
        "providers": [
            { "name": "env", "available": true, "description": "environment variable credential provider" }
        ]
    })
}

fn resolve_credential(provider: &str) -> Option<Value> {
    // Resolve from env: CREDENTIAL_<PROVIDER_UPPER>
    let key = format!("CREDENTIAL_{}", provider.to_uppercase().replace('-', "_"));
    std::env::var(&key).ok().map(|val| json!({ "provider": provider, "value": val }))
}

// ──────────────────────────────────────────────
// Surface op dispatch (mirrors handle_surface_op in Python)
// ──────────────────────────────────────────────

fn handle_surface_op(op: u8, payload: &[u8], state: &AppState) -> Value {
    match op {
        OP_HEALTH => health_payload(state),
        OP_STATUS => status_payload(state),
        OP_METRICS => metrics_payload(state),
        OP_ATTEST => json!({
            "sha256": sha256_hex(payload),
            "bytes": payload.len(),
            "node": state.profile["node_id"],
        }),
        OP_COMPRESS => {
            let compressed = zlib_compress(payload);
            json!({
                "codec": "zlib-test",
                "raw_bytes": payload.len(),
                "compressed_bytes": compressed.len(),
                "ratio": (compressed.len() as f64 / payload.len().max(1) as f64).round_to(6),
                "payload_b64": base64::engine::general_purpose::STANDARD.encode(&compressed),
            })
        }
        OP_RGFLOW => rgflow_score(payload),
        OP_ROUTE => {
            let lawful = rgflow_score(payload)["lawful"].as_bool().unwrap_or(true);
            json!({
                "accepted": lawful,
                "route": if payload.len() < 4096 { "local" } else { "atlas" },
            })
        }
        OP_MOUNT_STATUS => json!({
            "storage": storage_status(&state.mount_dir),
            "mount_point": state.mount_dir.display().to_string(),
            "provider": state.profile["storage"]["provider"],
            "required_for_boot": state.profile["storage"]["required_for_boot"],
        }),
        OP_SNAPSHOT => {
            let digest = sha256_hex(payload);
            let snapshot_path = state.state_dir.join("snapshot-last.json");
            let snap_content = format!(
                "{{\"sha256\":\"{}\",\"bytes\":{},\"t\":{}}}\n",
                digest,
                payload.len(),
                now_float()
            );
            std::fs::write(&snapshot_path, snap_content).ok();
            json!({ "snapshotted": true, "sha256": digest })
        }
        OP_ENTER_RECOVERY => json!({
            "accepted": false,
            "reason": "recovery transition disabled in test image",
        }),
        OP_PRIMITIVES => primitive_payload(state),
        OP_PLAN_ROUTE => choose_route(payload),
        OP_WIKI => {
            let request: Value = if payload.is_empty() {
                json!({"op": "recent"})
            } else {
                serde_json::from_slice(payload).unwrap_or(json!({"op": "recent"}))
            };
            // Wiki stub — returns manifest if no DB configured
            json!({
                "ok": true,
                "op": request.get("op").and_then(|v| v.as_str()).unwrap_or("recent"),
                "entries": [],
                "source": "rs-surface-wiki-stub",
                "note": "configure RS_WIKI_DB env var for persistent wiki",
            })
        }
        OP_FRACTAL_FOLD => {
            let request: Value = if payload.is_empty() {
                json!({"op": "manifest"})
            } else {
                serde_json::from_slice(payload).unwrap_or(json!({"op": "manifest"}))
            };
            json!({
                "ok": true,
                "op": request.get("op").and_then(|v| v.as_str()).unwrap_or("manifest"),
                "entries": [],
                "source": "rs-surface-fractal-fold-stub",
                "note": "configure RS_FRACTAL_FOLD_DB env var for persistent fractal fold",
            })
        }
        OP_META_AUTOTYPE => {
            let request: Value = if payload.is_empty() {
                json!({"text": ""})
            } else {
                serde_json::from_slice(payload).unwrap_or(json!({"text": ""}))
            };
            meta_autotype_handle(&request)
        }
        OP_CREDENTIALS => {
            let request: Value = if payload.is_empty() {
                json!({})
            } else {
                serde_json::from_slice(payload).unwrap_or(json!({}))
            };
            let action = request.get("action").and_then(|v| v.as_str()).unwrap_or("status");
            match action {
                "status" => credential_status(),
                "manifest" => provider_manifest(),
                "resolve" => {
                    let provider = request.get("provider").and_then(|v| v.as_str()).unwrap_or("");
                    if provider.is_empty() {
                        return json!({"ok": false, "error": "missing provider name"});
                    }
                    match resolve_credential(provider) {
                        Some(cred) => json!({"ok": true, "provider": cred["provider"], "value": cred["value"]}),
                        None => json!({"ok": false, "error": format!("provider {:?} not available", provider)}),
                    }
                }
                other => json!({"ok": false, "error": format!("unknown credentials action {:?}", other)}),
            }
        }
        _ => json!({"error": "unknown-op", "op": op}),
    }
}

// ──────────────────────────────────────────────
// Surface frame codec
// ──────────────────────────────────────────────

struct SurfaceFrame {
    request_id: u32,
    codec: u8,
    op: u8,
    payload: Vec<u8>,
}

fn parse_surface_frame(data: &[u8]) -> Result<SurfaceFrame> {
    if data.len() < 16 {
        return Err(anyhow!("surface frame too short"));
    }
    let version = data[0];
    let _flags = data[1];
    let codec = data[2];
    let op = data[3];
    if version != 1 {
        return Err(anyhow!("unsupported version {}", version));
    }
    let request_id = u32::from_le_bytes(data[4..8].try_into()?);
    let payload_len = u32::from_le_bytes(data[8..12].try_into()?) as usize;
    let crc_expected = u32::from_le_bytes(data[12..16].try_into()?);
    if data.len() < 16 + payload_len {
        return Err(anyhow!("payload length mismatch"));
    }
    let encoded_payload = &data[16..16 + payload_len];
    let crc_actual = crc32_of(encoded_payload);
    if crc_actual != crc_expected {
        return Err(anyhow!("payload crc mismatch: got {:08x}, expected {:08x}", crc_actual, crc_expected));
    }
    let payload = match codec {
        CODEC_NONE => encoded_payload.to_vec(),
        CODEC_ZLIB_TEST => zlib_decompress(encoded_payload)?,
        other => return Err(anyhow!("unsupported codec {}", other)),
    };
    Ok(SurfaceFrame { request_id, codec, op, payload })
}

fn build_surface_frame(request_id: u32, op: u8, payload_obj: &Value, codec: u8) -> Vec<u8> {
    let raw = canonical_json(payload_obj).into_bytes();
    let payload = match codec {
        CODEC_ZLIB_TEST => zlib_compress(&raw),
        _ => raw,
    };
    let crc = crc32_of(&payload);
    let mut frame = Vec::with_capacity(16 + payload.len());
    frame.push(1u8); // version
    frame.push(0u8); // flags
    frame.push(codec);
    frame.push(op);
    frame.extend_from_slice(&request_id.to_le_bytes());
    frame.extend_from_slice(&(payload.len() as u32).to_le_bytes());
    frame.extend_from_slice(&crc.to_le_bytes());
    frame.extend_from_slice(&payload);
    frame
}

// ──────────────────────────────────────────────
// Axum HTTP handlers
// ──────────────────────────────────────────────

async fn get_health(State(state): State<AppState>) -> Json<Value> {
    Json(health_payload(&state))
}

async fn get_status(State(state): State<AppState>) -> Json<Value> {
    Json(status_payload(&state))
}

async fn get_metrics(State(state): State<AppState>) -> Json<Value> {
    Json(metrics_payload(&state))
}

async fn get_primitives(State(state): State<AppState>) -> Json<Value> {
    Json(primitive_payload(&state))
}

async fn get_credentials(State(_state): State<AppState>) -> Json<Value> {
    Json(credential_status())
}

/// POST /surface — JSON envelope: { "op": <int>, "payload_b64": "<base64>" }
async fn post_surface(State(state): State<AppState>, body: axum::body::Bytes) -> Response {
    let req: Value = match serde_json::from_slice(&body) {
        Ok(v) => v,
        Err(e) => {
            return (
                StatusCode::BAD_REQUEST,
                Json(json!({"error": format!("invalid json: {}", e)})),
            )
                .into_response();
        }
    };
    let op = match req.get("op").and_then(|v| v.as_u64()) {
        Some(v) => v as u8,
        None => {
            return (
                StatusCode::BAD_REQUEST,
                Json(json!({"error": "missing op field"})),
            )
                .into_response();
        }
    };
    let payload = req
        .get("payload_b64")
        .and_then(|v| v.as_str())
        .and_then(|s| base64::engine::general_purpose::STANDARD.decode(s).ok())
        .unwrap_or_default();
    let result = handle_surface_op(op, &payload, &state);
    Json(result).into_response()
}

/// GET /ws — WebSocket upgrade (binary surface-frame protocol)
async fn ws_handler(
    ws: WebSocketUpgrade,
    State(state): State<AppState>,
) -> Response {
    ws.on_upgrade(move |socket| handle_socket(socket, state))
}

async fn handle_socket(mut socket: WebSocket, state: AppState) {
    loop {
        match socket.recv().await {
            Some(Ok(Message::Binary(data))) => {
                match parse_surface_frame(&data) {
                    Ok(frame) => {
                        let result = handle_surface_op(frame.op, &frame.payload, &state);
                        let response = build_surface_frame(frame.request_id, frame.op, &result, frame.codec);
                        if socket.send(Message::Binary(response)).await.is_err() {
                            return;
                        }
                    }
                    Err(e) => {
                        warn!("ws frame error: {}", e);
                        let err_frame = build_surface_frame(0, OP_STATUS, &json!({"error": e.to_string()}), CODEC_NONE);
                        let _ = socket.send(Message::Binary(err_frame)).await;
                        return;
                    }
                }
            }
            Some(Ok(Message::Close(_))) | None => return,
            Some(Ok(_)) => {} // ignore text/ping/pong frames
            Some(Err(e)) => {
                warn!("ws recv error: {}", e);
                return;
            }
        }
    }
}

async fn not_found() -> impl IntoResponse {
    (StatusCode::NOT_FOUND, Json(json!({"error": "not-found"})))
}

// ──────────────────────────────────────────────
// Main
// ──────────────────────────────────────────────

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .init();

    let profile = load_profile()?;

    let state_dir = PathBuf::from(
        std::env::var("RS_SURFACE_STATE").unwrap_or_else(|_| "/var/lib/rs-surface".to_string()),
    );
    let mount_dir = PathBuf::from(
        std::env::var("RS_SURFACE_MOUNT").unwrap_or_else(|_| "/mnt/topological-storage".to_string()),
    );

    ensure_state(&state_dir, &mount_dir, &profile)?;

    let host = resolve_bind_host(&profile);
    let port: u16 = std::env::var("RS_SURFACE_PORT")
        .ok()
        .and_then(|s| s.parse().ok())
        .or_else(|| {
            profile
                .get("api")
                .and_then(|a| a.get("plain_health_port"))
                .and_then(|p| p.as_u64())
                .map(|p| p as u16)
        })
        .unwrap_or(8080);

    let started_at = now_secs();
    let app_state = AppState {
        profile: Arc::new(profile.clone()),
        state_dir,
        mount_dir,
        started_at,
    };

    let app = Router::new()
        .route("/health", get(get_health))
        .route("/status", get(get_status))
        .route("/metrics", get(get_metrics))
        .route("/primitives", get(get_primitives))
        .route("/credentials", get(get_credentials))
        .route("/surface", post(post_surface))
        .route("/ws", get(ws_handler))
        .fallback(not_found)
        .with_state(app_state);

    let addr = format!("{}:{}", host, port);
    info!("rs-surface listening on {} node={}", addr, profile["node_id"]);
    println!(
        "rs-surface listening on {}:{} node={}",
        host,
        port,
        profile["node_id"].as_str().unwrap_or("unknown")
    );

    let listener = TcpListener::bind(&addr).await?;
    axum::serve(listener, app).await?;
    Ok(())
}
