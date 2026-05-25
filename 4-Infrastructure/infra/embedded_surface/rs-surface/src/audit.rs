/// Lightweight append-only JSONL audit logger for credential operations.
///
/// Writes to a local file (default `/var/log/rs-surface/access_log.jsonl`)
/// and, when `CREDENTIAL_AUDIT_DSN` or `RDS_DSN` is set, also INSERTs into
/// PostgreSQL `credential_store.access_log`.
///
/// Each line is a self-contained JSON object matching the PostgreSQL schema.
use serde_json::json;
use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};
use tokio::fs::OpenOptions;
use tokio::io::AsyncWriteExt;
use tokio::sync::mpsc;
use tokio_postgres::types::Json;
use tracing::{error, info, warn};

#[derive(Debug, Clone)]
pub struct AuditEvent {
    pub actor: Option<String>,
    pub action: String,
    pub resource: Option<String>,
    pub resource_type: Option<String>,
    pub outcome: String,
    pub ip_address: Option<String>,
    pub user_agent: Option<String>,
    pub request_id: Option<String>,
    pub details: serde_json::Value,
}

impl AuditEvent {
    fn to_jsonl(&self) -> String {
        let ts = iso_utc_now();
        let obj = json!({
            "timestamp": ts,
            "actor": self.actor,
            "action": self.action,
            "resource": self.resource,
            "resource_type": self.resource_type,
            "outcome": self.outcome,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "request_id": self.request_id,
            "details": self.details,
        });
        // Single-line JSON for JSONL format.
        obj.to_string() + "\n"
    }
}

/// ISO-8601 UTC timestamp without chrono (mirrors main.rs helper).
fn iso_utc_now() -> String {
    let secs = SystemTime::now()
        .duration_since(UNIX_EPOCH)
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
    format!(
        "{:04}-{:02}-{:02}T{:02}:{:02}:{:02}Z",
        year,
        month,
        day_rem + 1,
        h,
        m,
        sec
    )
}

/// Async audit logger backed by a Tokio task that appends to a JSONL file
/// and optionally INSERTs into PostgreSQL.
#[derive(Clone)]
pub struct AuditLogger {
    sender: mpsc::UnboundedSender<AuditEvent>,
}

impl AuditLogger {
    /// Start the background writer.  If the file cannot be opened the logger
    /// falls back to stderr warning (no panic) so the server stays up.
    pub fn new(log_path: PathBuf) -> Self {
        let (sender, mut receiver) = mpsc::unbounded_channel::<AuditEvent>();

        tokio::spawn(async move {
            // Ensure parent directory exists.
            if let Some(parent) = log_path.parent() {
                if let Err(e) = tokio::fs::create_dir_all(parent).await {
                    warn!("audit log mkdir failed: {}", e);
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
                    warn!("audit log open failed: {} — logging to stderr only", e);
                    // Fallback: print JSONL to stderr.
                    while let Some(evt) = receiver.recv().await {
                        eprintln!("[AUDIT] {}", evt.to_jsonl().trim_end());
                    }
                    return;
                }
            };

            // Try to open a PostgreSQL connection if DSN is configured.
            let dsn = std::env::var("CREDENTIAL_AUDIT_DSN")
                .or_else(|_| std::env::var("RDS_DSN"))
                .ok();
            let pg_client = if let Some(ref dsn_str) = dsn {
                // Build a Rustls TLS connector using webpki roots.
                let tls = {
                    let mut root_store = rustls::RootCertStore::empty();
                    root_store.extend(webpki_roots::TLS_SERVER_ROOTS.iter().cloned());
                    let config = rustls::ClientConfig::builder()
                        .with_root_certificates(root_store)
                        .with_no_client_auth();
                    tokio_postgres_rustls::MakeRustlsConnect::new(config)
                };
                match tokio_postgres::connect(dsn_str, tls).await {
                    Ok((client, connection)) => {
                        tokio::spawn(async move {
                            if let Err(e) = connection.await {
                                warn!("postgres connection error: {}", e);
                            }
                        });
                        info!("audit log: connected to PostgreSQL");
                        Some(client)
                    }
                    Err(e) => {
                        warn!("audit log: could not connect to postgres: {}", e);
                        None
                    }
                }
            } else {
                None
            };

            while let Some(evt) = receiver.recv().await {
                let line = evt.to_jsonl();
                if let Err(e) = file.write_all(line.as_bytes()).await {
                    error!("audit log write failed: {}", e);
                }
                // Best-effort fsync for durability.
                let _ = file.sync_all().await;

                // Best-effort PostgreSQL insert.
                if let Some(ref client) = pg_client {
                    let actor = evt.actor.as_deref().unwrap_or("");
                    let resource = evt.resource.as_deref().unwrap_or("");
                    let resource_type = evt.resource_type.as_deref();
                    let ip = evt.ip_address.as_deref();
                    let ua = evt.user_agent.as_deref();
                    let req_id = evt.request_id.as_deref();
                    let details = Json(&evt.details);
                    let result = client
                        .execute(
                            "INSERT INTO credential_store.access_log \
                             (actor, action, resource, resource_type, outcome, ip_address, user_agent, request_id, details) \
                             VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)",
                            &[
                                &actor,
                                &evt.action,
                                &resource,
                                &resource_type,
                                &evt.outcome,
                                &ip,
                                &ua,
                                &req_id,
                                &details,
                            ],
                        )
                        .await;
                    if let Err(e) = result {
                        warn!("audit log: postgres insert failed: {}", e);
                    }
                }
            }
        });

        Self { sender }
    }

    /// Fire-and-forget audit event.  Never blocks the caller.
    pub fn log(&self, event: AuditEvent) {
        if let Err(e) = self.sender.send(event) {
            warn!("audit log channel closed: {}", e);
        }
    }
}

/// Convenience constructor that reads `RS_AUDIT_LOG_PATH` or falls back to
/// the default log path.
pub fn default_logger() -> AuditLogger {
    let path = std::env::var("RS_AUDIT_LOG_PATH")
        .map(PathBuf::from)
        .unwrap_or_else(|_| PathBuf::from("/var/log/rs-surface/access_log.jsonl"));
    AuditLogger::new(path)
}
