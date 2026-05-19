use anyhow::{Context, Result};
use chrono::Utc;
use clap::Parser;
use ene_storage::{
    build_receipt, decide, load_garage_env, observe, resume_chain, ActionResult, Decision,
    Observation, GARAGE_BUCKET, GARAGE_ENDPOINT, RECEIPT_PREFIX,
};
use serde_json::json;
use std::collections::HashMap;
use std::path::PathBuf;
use tokio::process::Command;
use tracing::{info, warn};

// ── subprocess helpers ─────────────────────────────────────────────────────

async fn run_cmd(
    args: &[&str],
    env_extra: &HashMap<String, String>,
    timeout_secs: u64,
) -> Result<(i32, String, String)> {
    let mut cmd = Command::new(args.first().context("empty command")?);
    for a in &args[1..] {
        cmd.arg(a);
    }
    for (k, v) in env_extra {
        cmd.env(k, v);
    }
    let output = tokio::time::timeout(
        std::time::Duration::from_secs(timeout_secs),
        cmd.output(),
    )
    .await
    .context("command timed out")?
    .context("command failed to run")?;
    let rc = output.status.code().unwrap_or(-1);
    let stdout = String::from_utf8_lossy(&output.stdout).into_owned();
    let stderr = String::from_utf8_lossy(&output.stderr).into_owned();
    Ok((rc, stdout, stderr))
}

// ── Action ─────────────────────────────────────────────────────────────────

async fn act_one(
    label: &str,
    args: &[&str],
    ar: &mut ActionResult,
    env_extra: &HashMap<String, String>,
    timeout_secs: u64,
) {
    ar.actions_attempted.push(label.to_string());
    match run_cmd(args, env_extra, timeout_secs).await {
        Ok((0, stdout, _)) => {
            ar.actions_succeeded.push(label.to_string());
            let tail = stdout.chars().rev().take(500).collect::<Vec<_>>().into_iter().rev().collect::<String>();
            ar.details.insert(label.to_string(), json!({"rc": 0, "stdout_tail": tail.trim() }));
        }
        Ok((rc, stdout, stderr)) => {
            ar.actions_failed.push(label.to_string());
            ar.details.insert(
                label.to_string(),
                json!({
                    "rc": rc,
                    "stderr": stderr.chars().rev().take(500).collect::<Vec<_>>().into_iter().rev().collect::<String>().trim(),
                    "stdout": stdout.chars().rev().take(200).collect::<Vec<_>>().into_iter().rev().collect::<String>().trim(),
                }),
            );
        }
        Err(e) => {
            ar.actions_failed.push(label.to_string());
            ar.details.insert(label.to_string(), json!({"rc": -1, "error": e.to_string() }));
        }
    }
}

async fn act(
    d: &Decision,
    creds: &HashMap<String, String>,
    probe_only: bool,
    dry_run: bool,
) -> ActionResult {
    let mut ar = ActionResult::default();

    if probe_only || dry_run {
        ar.details.insert("mode".into(), json!(if probe_only { "probe_only" } else { "dry_run" }));
        return ar;
    }

    let repo_root = std::env::current_dir()
        .ok()
        .and_then(|p| p.parent().map(|p| p.to_path_buf()))
        .unwrap_or_else(|| PathBuf::from("/home/allaun"));
    let storage_dir = repo_root.join("4-Infrastructure/storage");
    let backup_sh = storage_dir.join("restic/backup.sh");
    let consolidate_sh = storage_dir.join("garage/db-consolidate.sh");

    if d.trigger_garage_restart {
        act_one("garage_restart", &["systemctl", "--user", "restart", "garage.service"], &mut ar, creds, 30).await;
        if ar.actions_failed.contains(&"garage_restart".to_string()) {
            act_one("garage_restart_system", &["sudo", "systemctl", "restart", "garage.service"], &mut ar, creds, 30).await;
        }
    }

    if d.trigger_snap {
        act_one(
            "restic_snap",
            &["bash", &backup_sh.to_string_lossy(), "snap", "agent-triggered"],
            &mut ar,
            creds,
            3600,
        )
        .await;
    }

    if d.trigger_cold_copy {
        act_one(
            "restic_cold_copy",
            &["bash", &backup_sh.to_string_lossy(), "cold-copy"],
            &mut ar,
            creds,
            3600,
        )
        .await;
    }

    if d.trigger_verify {
        act_one(
            "restic_verify",
            &["bash", &backup_sh.to_string_lossy(), "verify"],
            &mut ar,
            creds,
            600,
        )
        .await;
    }

    if d.trigger_forget {
        act_one(
            "restic_forget",
            &["bash", &backup_sh.to_string_lossy(), "forget"],
            &mut ar,
            creds,
            600,
        )
        .await;
    }

    if d.trigger_offload {
        act_one(
            "db_offload",
            &["bash", &consolidate_sh.to_string_lossy(), "offload"],
            &mut ar,
            creds,
            300,
        )
        .await;
    }

    ar
}

// ── Receipt emission ───────────────────────────────────────────────────────

fn emit_local(receipt: &serde_json::Value) -> Result<()> {
    let log_path = dirs::cache_dir()
        .unwrap_or_else(|| PathBuf::from("/tmp"))
        .join("ene-storage/receipts.jsonl");
    if let Some(p) = log_path.parent() {
        let _ = std::fs::create_dir_all(p);
    }
    let line = serde_json::to_string(receipt)?;
    use std::io::Write;
    let mut fh = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(&log_path)?;
    writeln!(fh, "{}", line)?;
    Ok(())
}

async fn emit_s3(receipt: &serde_json::Value, creds: &HashMap<String, String>) -> Result<(bool, String)> {
    let ts = receipt["generated_at_utc"]
        .as_str()
        .unwrap_or("")
        .chars()
        .take(10)
        .collect::<String>();
    let h = receipt["receipt_hash"]
        .as_str()
        .unwrap_or("")
        .chars()
        .take(16)
        .collect::<String>();
    let key = format!("{}/{}/{}.json", RECEIPT_PREFIX, ts, h);
    let payload = serde_json::to_vec_pretty(receipt)?;

    let tmp = tempfile::NamedTempFile::with_suffix(".json")?;
    tokio::fs::write(tmp.path(), &payload).await?;

    let endpoint = creds.get("AWS_ENDPOINT_URL").cloned().unwrap_or_else(|| GARAGE_ENDPOINT.into());
    let (rc, _, _) = run_cmd(
        &[
            "aws",
            "s3",
            "cp",
            "--endpoint-url",
            &endpoint,
            tmp.path().to_str().unwrap_or("/dev/null"),
            &format!("s3://{}/{}", GARAGE_BUCKET, key),
            "--content-type",
            "application/json",
        ],
        creds,
        60,
    )
    .await?;

    Ok((rc == 0, key))
}

// ── Main cycle ─────────────────────────────────────────────────────────────

#[derive(Parser, Debug)]
#[command(name = "ene-storage")]
#[command(about = "Storage stack ODA daemon — replaces storage_agent.py")]
struct Cli {
    #[arg(long)]
    probe_only: bool,
    #[arg(long)]
    dry_run: bool,
    #[arg(long)]
    no_s3: bool,
    #[arg(long)]
    loop_mode: bool,
    #[arg(long, default_value = "900")]
    interval: u64,
}

async fn run_cycle(
    tick: i64,
    parent_hash: &str,
    creds: &HashMap<String, String>,
    probe_only: bool,
    dry_run: bool,
    no_s3: bool,
) -> String {
    let obs = observe(creds).await;
    let dec = decide(&obs);
    let ar = act(&dec, creds, probe_only, dry_run).await;
    let receipt = build_receipt(tick, parent_hash, &obs, &dec, &ar);

    let _ = emit_local(&receipt);

    let (s3_ok, s3_key) = if !no_s3 && obs.garage.up {
        emit_s3(&receipt, creds).await.unwrap_or((false, String::new()))
    } else {
        (false, String::new())
    };

    let mode_tag = if probe_only {
        " [probe-only]"
    } else if dry_run {
        " [dry-run]"
    } else {
        ""
    };
    let hash_str = receipt["receipt_hash"]
        .as_str()
        .unwrap_or("")
        .chars()
        .take(16)
        .collect::<String>();
    info!(
        "tick={}{} garage={} snapshots={} dedup_q16={} alerts={} acted={:?} failed={:?} hash={}... s3={}",
        tick,
        mode_tag,
        if obs.garage.up { "UP" } else { "DOWN" },
        obs.restic.snapshot_count,
        obs.restic.dedup_ratio_q16,
        dec.alerts.len(),
        ar.actions_succeeded,
        ar.actions_failed,
        hash_str,
        if s3_ok { &s3_key } else { "skipped" }
    );
    for alert in &dec.alerts {
        warn!("! {}", alert);
    }

    receipt["receipt_hash"]
        .as_str()
        .unwrap_or("")
        .to_string()
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .init();

    let cli = Cli::parse();
    let creds = load_garage_env();

    let (mut tick, mut parent_hash) = resume_chain();
    tick += 1;

    if cli.loop_mode {
        info!("loop mode, interval={}s, resuming tick={}", cli.interval, tick);
        loop {
            match tokio::time::timeout(
                std::time::Duration::from_secs(cli.interval + 300),
                run_cycle(
                    tick,
                    &parent_hash,
                    &creds,
                    cli.probe_only,
                    cli.dry_run,
                    cli.no_s3,
                ),
            )
            .await
            {
                Ok(new_hash) => parent_hash = new_hash,
                Err(_) => warn!("cycle timed out (tick={})", tick),
            }
            tick += 1;
            tokio::time::sleep(std::time::Duration::from_secs(cli.interval)).await;
        }
    } else {
        run_cycle(tick, &parent_hash, &creds, cli.probe_only, cli.dry_run, cli.no_s3).await;
    }

    Ok(())
}
