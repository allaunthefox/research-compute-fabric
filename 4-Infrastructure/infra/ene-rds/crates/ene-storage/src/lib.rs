use chrono::Utc;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::path::PathBuf;
use std::time::Duration;

// ── constants ──────────────────────────────────────────────────────────────

pub const SCHEMA: &str = "storage_agent_receipt_v1";
pub const VERSION: &str = "1.0.0";
pub const GARAGE_ENDPOINT: &str = "http://localhost:3900";
pub const GARAGE_BUCKET: &str = "research-stack";
pub const RECEIPT_PREFIX: &str = "agent-receipts";
pub const Q16_ONE: u32 = 0x0001_0000;
pub const Q16_DEDUP_LOW: u32 = 19_661; // 0.3

// ── config / env loading ───────────────────────────────────────────────────

pub fn load_garage_env() -> HashMap<String, String> {
    let mut env: HashMap<String, String> = HashMap::new();
    let garage_env = PathBuf::from("/etc/garage/garage.env");
    if garage_env.exists() {
        if let Ok(text) = std::fs::read_to_string(&garage_env) {
            for line in text.lines() {
                let line = line.trim();
                if line.is_empty() || line.starts_with('#') {
                    continue;
                }
                if let Some((k, v)) = line.split_once('=') {
                    env.insert(k.trim().to_string(), v.trim().to_string());
                }
            }
        }
    }

    let mut creds = HashMap::new();
    creds.insert(
        "AWS_ACCESS_KEY_ID".into(),
        env.get("GARAGE_ACCESS_KEY_ID")
            .cloned()
            .or_else(|| std::env::var("AWS_ACCESS_KEY_ID").ok())
            .unwrap_or_default(),
    );
    creds.insert(
        "AWS_SECRET_ACCESS_KEY".into(),
        env.get("GARAGE_SECRET_ACCESS_KEY")
            .cloned()
            .or_else(|| std::env::var("AWS_SECRET_ACCESS_KEY").ok())
            .unwrap_or_default(),
    );
    creds.insert(
        "AWS_DEFAULT_REGION".into(),
        env.get("AWS_DEFAULT_REGION")
            .cloned()
            .or_else(|| std::env::var("AWS_DEFAULT_REGION").ok())
            .unwrap_or_else(|| "garage".into()),
    );
    creds.insert(
        "AWS_ENDPOINT_URL".into(),
        env.get("AWS_ENDPOINT_URL")
            .cloned()
            .or_else(|| std::env::var("AWS_ENDPOINT_URL").ok())
            .unwrap_or_else(|| GARAGE_ENDPOINT.into()),
    );
    creds.insert(
        "RESTIC_REPOSITORY".into(),
        std::env::var("RESTIC_REPOSITORY")
            .ok()
            .unwrap_or_else(|| "s3:http://localhost:3900/research-stack".into()),
    );
    creds.insert(
        "RESTIC_PASSWORD_FILE".into(),
        std::env::var("RESTIC_PASSWORD_FILE")
            .ok()
            .unwrap_or_else(|| "/etc/garage/restic-password".into()),
    );
    creds
}

// ── Observation ────────────────────────────────────────────────────────────

#[derive(Debug, Default, Clone, Serialize, Deserialize)]
pub struct GarageObs {
    pub up: bool,
    pub nodes_total: i64,
    pub nodes_ok: i64,
    pub buckets: Vec<String>,
}

#[derive(Debug, Default, Clone, Serialize, Deserialize)]
pub struct ResticObs {
    pub snapshot_count: i64,
    pub latest_ts: Option<String>,
    pub latest_size_bytes: i64,
    pub stored_bytes: i64,
    pub dedup_ratio_q16: u32,
}

#[derive(Debug, Default, Clone, Serialize, Deserialize)]
pub struct BackupLogObs {
    pub last_ok: bool,
    pub last_ts: Option<String>,
}

#[derive(Debug, Default, Clone, Serialize, Deserialize)]
pub struct Observation {
    pub ts: String,
    pub garage: GarageObs,
    pub restic: ResticObs,
    pub backup_log: BackupLogObs,
    pub cold_copy_needed: bool,
    pub errors: Vec<String>,
}

impl Observation {
    pub fn new() -> Self {
        Self {
            ts: Utc::now().to_rfc3339(),
            garage: GarageObs::default(),
            restic: ResticObs::default(),
            backup_log: BackupLogObs::default(),
            cold_copy_needed: false,
            errors: vec![],
        }
    }
}

pub async fn observe(creds: &HashMap<String, String>) -> Observation {
    let mut obs = Observation::new();
    let endpoint = creds
        .get("AWS_ENDPOINT_URL")
        .cloned()
        .unwrap_or_else(|| GARAGE_ENDPOINT.to_string());

    match tokio::time::timeout(Duration::from_secs(2), reqwest::get(&endpoint)).await {
        Ok(Ok(response)) => {
            obs.garage.up = true;
            obs.garage.buckets.push(GARAGE_BUCKET.to_string());
            if !response.status().is_success() {
                obs.errors.push(format!(
                    "garage endpoint responded with non-success status {}",
                    response.status()
                ));
            }
        }
        Ok(Err(err)) => {
            obs.errors
                .push(format!("garage endpoint probe failed: {err}"));
        }
        Err(_) => {
            obs.errors
                .push("garage endpoint probe timed out after 2s".to_string());
        }
    }

    let backup_log = dirs::cache_dir()
        .unwrap_or_else(|| PathBuf::from("/tmp"))
        .join("garage-post-commit.log");
    if let Ok(text) = std::fs::read_to_string(&backup_log) {
        obs.backup_log.last_ts = std::fs::metadata(&backup_log)
            .and_then(|metadata| metadata.modified())
            .ok()
            .map(|modified| chrono::DateTime::<Utc>::from(modified).to_rfc3339());
        obs.backup_log.last_ok =
            text.contains("completed") || text.contains("success") || text.contains("succeeded");
    }

    obs
}

// ── Decision ───────────────────────────────────────────────────────────────

#[derive(Debug, Default, Clone, Serialize, Deserialize)]
pub struct Decision {
    pub trigger_snap: bool,
    pub trigger_cold_copy: bool,
    pub trigger_verify: bool,
    pub trigger_forget: bool,
    pub trigger_offload: bool,
    pub trigger_garage_restart: bool,
    pub alerts: Vec<String>,
    pub rationale: Vec<String>,
}

pub fn decide(obs: &Observation) -> Decision {
    let mut d = Decision::default();

    if !obs.garage.up {
        d.alerts.push("ALERT: Garage S3 is unreachable".into());
        d.trigger_garage_restart = true;
        d.rationale
            .push("garage_up=false → trigger_garage_restart".into());
    }

    if obs.restic.snapshot_count == 0 && obs.garage.up {
        d.alerts
            .push("ALERT: restic repo has zero snapshots — initial backup needed".into());
        d.trigger_snap = true;
        d.rationale.push("snapshot_count=0 → trigger_snap".into());
    }

    if !obs.backup_log.last_ok && obs.garage.up {
        d.alerts
            .push("WARN: No successful restic snapshot found in backup log".into());
        d.trigger_snap = true;
        d.rationale
            .push("backup_log_last_ok=false → trigger_snap".into());
    }

    if obs.restic.dedup_ratio_q16 > 0
        && obs.restic.dedup_ratio_q16 < Q16_DEDUP_LOW
        && obs.restic.snapshot_count > 5
    {
        d.trigger_verify = true;
        d.rationale.push(format!(
            "dedup_ratio_q16={} < Q16_DEDUP_LOW={} and snapshot_count={} > 5 → trigger_verify",
            obs.restic.dedup_ratio_q16, Q16_DEDUP_LOW, obs.restic.snapshot_count
        ));
    }

    if obs.restic.snapshot_count > 30 {
        d.trigger_forget = true;
        d.rationale.push(format!(
            "snapshot_count={} > 30 → trigger_forget (prune)",
            obs.restic.snapshot_count
        ));
    }

    if obs.cold_copy_needed {
        d.alerts.push(
            "WARN: Newest restic snapshot is >26 h old — cold copy to gdrive appears stale".into(),
        );
        d.trigger_cold_copy = true;
        d.rationale
            .push("cold_copy_needed=true → trigger_cold_copy".into());
    }

    if obs.garage.up {
        d.trigger_offload = true;
        d.rationale
            .push("garage_up=true → trigger_offload (idempotent)".into());
    }

    d
}

// ── Action Result ────────────────────────────────────────────────────────────

#[derive(Debug, Default, Clone, Serialize, Deserialize)]
pub struct ActionResult {
    pub actions_attempted: Vec<String>,
    pub actions_succeeded: Vec<String>,
    pub actions_failed: Vec<String>,
    pub details: HashMap<String, serde_json::Value>,
}

// ── Receipt ────────────────────────────────────────────────────────────────

pub fn build_receipt(
    tick: i64,
    parent_hash: &str,
    obs: &Observation,
    dec: &Decision,
    ar: &ActionResult,
) -> serde_json::Value {
    let mut receipt = serde_json::json!({
        "schema": SCHEMA,
        "version": VERSION,
        "generated_at_utc": Utc::now().to_rfc3339(),
        "tick": tick,
        "parent_hash": parent_hash,
        "observation": obs,
        "decision": dec,
        "action_result": ar,
        "claim_boundary": "storage-agent-observe-decide-act-only",
    });

    // Hash the preimage (excluding generated_at_utc and receipt_hash)
    let preimage = serde_json::json!({
        "schema": SCHEMA,
        "version": VERSION,
        "tick": tick,
        "parent_hash": parent_hash,
        "observation": obs,
        "decision": dec,
        "action_result": ar,
        "claim_boundary": "storage-agent-observe-decide-act-only",
    });
    let hash = sha256_text(&serde_json::to_string(&preimage).unwrap_or_default());
    receipt["receipt_hash"] = serde_json::json!(hash);
    receipt
}

pub fn sha256_text(data: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(data.as_bytes());
    hex::encode(hasher.finalize())
}

pub fn resume_chain() -> (i64, String) {
    let log_path = dirs::cache_dir()
        .unwrap_or_else(|| PathBuf::from("/tmp"))
        .join("ene-storage/receipts.jsonl");
    if !log_path.exists() {
        return (0, String::new());
    }
    let text = match std::fs::read_to_string(&log_path) {
        Ok(t) => t,
        Err(_) => return (0, String::new()),
    };
    let mut last_tick = 0i64;
    let mut last_hash = String::new();
    for line in text.lines() {
        if let Ok(entry) = serde_json::from_str::<serde_json::Value>(line) {
            last_tick = entry
                .get("tick")
                .and_then(|v| v.as_i64())
                .unwrap_or(last_tick);
            last_hash = entry
                .get("receipt_hash")
                .and_then(|v| v.as_str())
                .unwrap_or(&last_hash)
                .to_string();
        }
    }
    (last_tick, last_hash)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn decide_garage_down_triggers_restart() {
        let mut obs = Observation::new();
        obs.garage.up = false;
        let d = decide(&obs);
        assert!(d.trigger_garage_restart);
        assert!(d.alerts.iter().any(|a| a.contains("unreachable")));
    }

    #[test]
    fn decide_zero_snapshots_triggers_snap() {
        let mut obs = Observation::new();
        obs.garage.up = true;
        obs.restic.snapshot_count = 0;
        let d = decide(&obs);
        assert!(d.trigger_snap);
        assert!(d.alerts.iter().any(|a| a.contains("zero snapshots")));
    }

    #[test]
    fn decide_poor_dedup_triggers_verify() {
        let mut obs = Observation::new();
        obs.garage.up = true;
        obs.restic.snapshot_count = 10;
        obs.restic.dedup_ratio_q16 = 10_000; // well below 19_661
        let d = decide(&obs);
        assert!(d.trigger_verify);
    }

    #[test]
    fn decide_good_dedup_no_verify() {
        let mut obs = Observation::new();
        obs.garage.up = true;
        obs.restic.snapshot_count = 10;
        obs.restic.dedup_ratio_q16 = 50_000; // above 19_661
        let d = decide(&obs);
        assert!(!d.trigger_verify);
    }

    #[test]
    fn decide_too_many_snapshots_triggers_forget() {
        let mut obs = Observation::new();
        obs.garage.up = true;
        obs.restic.snapshot_count = 31;
        let d = decide(&obs);
        assert!(d.trigger_forget);
    }

    #[test]
    fn decide_cold_copy_stale() {
        let mut obs = Observation::new();
        obs.garage.up = true;
        obs.cold_copy_needed = true;
        let d = decide(&obs);
        assert!(d.trigger_cold_copy);
    }

    #[test]
    fn decide_garage_up_triggers_offload() {
        let mut obs = Observation::new();
        obs.garage.up = true;
        let d = decide(&obs);
        assert!(d.trigger_offload);
    }

    #[test]
    fn receipt_hash_is_stable() {
        let obs = Observation::new();
        let dec = decide(&obs);
        let ar = ActionResult::default();
        let r1 = build_receipt(1, "", &obs, &dec, &ar);
        let r2 = build_receipt(1, "", &obs, &dec, &ar);
        assert_eq!(r1["receipt_hash"], r2["receipt_hash"]);
    }

    #[test]
    fn receipt_hash_changes_with_tick() {
        let obs = Observation::new();
        let dec = decide(&obs);
        let ar = ActionResult::default();
        let r1 = build_receipt(1, "", &obs, &dec, &ar);
        let r2 = build_receipt(2, "", &obs, &dec, &ar);
        assert_ne!(r1["receipt_hash"], r2["receipt_hash"]);
    }

    #[test]
    fn receipt_hash_changes_with_parent() {
        let obs = Observation::new();
        let dec = decide(&obs);
        let ar = ActionResult::default();
        let r1 = build_receipt(1, "abc", &obs, &dec, &ar);
        let r2 = build_receipt(1, "def", &obs, &dec, &ar);
        assert_ne!(r1["receipt_hash"], r2["receipt_hash"]);
    }

    #[test]
    fn sha256_text_is_deterministic() {
        let h1 = sha256_text("hello");
        let h2 = sha256_text("hello");
        assert_eq!(h1, h2);
        assert_eq!(h1.len(), 64);
    }

    #[test]
    fn sha256_text_changes_with_input() {
        let h1 = sha256_text("a");
        let h2 = sha256_text("b");
        assert_ne!(h1, h2);
    }

    #[test]
    fn observation_new_sets_timestamp() {
        let obs = Observation::new();
        assert!(!obs.ts.is_empty());
        assert!(!obs.garage.up);
        assert_eq!(obs.restic.snapshot_count, 0);
    }

    #[test]
    fn q16_constants_sane() {
        assert_eq!(Q16_ONE, 65536);
        assert!(Q16_DEDUP_LOW < Q16_ONE);
        // 0.3 * 65536 = 19660.8 ≈ 19661
        assert_eq!(Q16_DEDUP_LOW, 19661);
    }
}
