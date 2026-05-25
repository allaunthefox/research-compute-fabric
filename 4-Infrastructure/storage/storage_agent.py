#!/usr/bin/env python3
# PTOS: LAYER=STORE / DOMAIN=OBSERVE / CONDITION=ACTIVE / STAGE=ACTIVE / SOURCE=CODE
"""
storage_agent.py — Full-loop storage/backup observer, optimizer, and actor.

Shim boundary (per AGENTS.md §7.1):
  ALLOWED:  subprocess calls to existing CLI tools, JSON I/O, log/receipt
            emission, threshold comparisons on Q16_16-encoded integers
            read back from existing receipts.
  FORBIDDEN: reimplementing restic/Garage/rclone logic, Float arithmetic,
             cost functions (those belong in Lean), new external dependencies.

Observe → Decide → Act → Emit Receipt (JSON, hash-chained, sharded to S3).

Receipt schema: storage_agent_receipt_v1

Usage:
    python3 4-Infrastructure/storage/storage_agent.py [options]

Options:
    --probe-only      Observe and emit receipt but take no corrective actions.
    --dry-run         Show what actions would be taken, do not execute them.
    --no-s3           Skip uploading receipt to Garage S3 (local JSONL only).
    --once            Run exactly one cycle and exit (default when called from
                      systemd or a hook; loop mode requires --loop).
    --loop            Run in a polling loop (INTERVAL_SECONDS between ticks).
    --interval N      Seconds between loop ticks (default: 900 = 15 min).

Environment (all read from /etc/garage/garage.env or environment):
    GARAGE_ACCESS_KEY_ID, GARAGE_SECRET_ACCESS_KEY,
    RESTIC_REPOSITORY, RESTIC_PASSWORD_FILE,
    AWS_ENDPOINT_URL (default: http://localhost:3900)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── constants ─────────────────────────────────────────────────────────────────

SCHEMA = "storage_agent_receipt_v1"
VERSION = "1.0.0"

REPO_ROOT = Path(__file__).resolve().parents[3]
STORAGE_DIR = Path(__file__).resolve().parent
RESTIC_DIR = STORAGE_DIR / "restic"
GARAGE_DIR = STORAGE_DIR / "garage"

BACKUP_SH = RESTIC_DIR / "backup.sh"
CONSOLIDATE_SH = GARAGE_DIR / "db-consolidate.sh"

LOG_PATH = Path.home() / ".cache" / "storage-agent.jsonl"
GARAGE_ENDPOINT = os.environ.get("AWS_ENDPOINT_URL", "http://localhost:3900")
GARAGE_BUCKET = "research-stack"
RECEIPT_PREFIX = "agent-receipts"

# ── Q16_16 constants ────────────────────────────────────────────────────────
# All thresholds stored as Q16_16 (UInt32: one = 0x00010000 = 65536).
# See 6-Documentation/docs/AGENTS.md §1.4 for encoding rules.
Q16_ONE: int = 0x00010000           # 1.0
Q16_HALF: int = 0x00008000          # 0.5
Q16_POINT_9: int = 58982            # ≈ 0.9  (58982 / 65536)
Q16_TWO: int = 0x00020000           # 2.0
Q16_FIVE: int = 0x00050000          # 5.0

# Dedup-ratio threshold: act on cold-copy if dedup ratio < 30% (poor dedup)
Q16_DEDUP_LOW: int = 19661          # 0.3


# ── credential loading ────────────────────────────────────────────────────────

def _load_garage_env() -> dict[str, str]:
    """
    Load Garage credentials from /etc/garage/garage.env into a dict.
    Fallback to environment variables already set by caller.
    """
    env: dict[str, str] = {}
    garage_env = Path("/etc/garage/garage.env")
    if garage_env.exists():
        try:
            raw_lines = garage_env.read_text().splitlines()
        except PermissionError:
            raw_lines = []
        for line in raw_lines:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                env[key.strip()] = val.strip()

    # Map GARAGE_* → AWS_* so aws cli + restic can use them
    cred_map = {
        "AWS_ACCESS_KEY_ID":     env.get("GARAGE_ACCESS_KEY_ID",     os.environ.get("AWS_ACCESS_KEY_ID",     "")),
        "AWS_SECRET_ACCESS_KEY": env.get("GARAGE_SECRET_ACCESS_KEY",  os.environ.get("AWS_SECRET_ACCESS_KEY", "")),
        "AWS_DEFAULT_REGION":    env.get("AWS_DEFAULT_REGION",        os.environ.get("AWS_DEFAULT_REGION",    "garage")),
        "AWS_ENDPOINT_URL":      env.get("AWS_ENDPOINT_URL",          GARAGE_ENDPOINT),
        "RESTIC_REPOSITORY":     os.environ.get("RESTIC_REPOSITORY",  "s3:http://localhost:3900/research-stack"),
        "RESTIC_PASSWORD_FILE":  os.environ.get("RESTIC_PASSWORD_FILE", "/etc/garage/restic-password"),
    }
    return cred_map


# ── subprocess helpers ────────────────────────────────────────────────────────

def _run(
    args: list[str],
    env_extra: dict[str, str] | None = None,
    timeout: int = 120,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run a command, merge env_extra into environment, return CompletedProcess."""
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=check,
        env=env,
    )


def _sh(
    script: Path,
    subcmd: str,
    env_extra: dict[str, str] | None = None,
    timeout: int = 300,
) -> tuple[int, str, str]:
    """Run bash <script> <subcmd>, return (returncode, stdout, stderr)."""
    result = _run(["bash", str(script), subcmd], env_extra=env_extra, timeout=timeout)
    return result.returncode, result.stdout, result.stderr


# ── hoxel recording ───────────────────────────────────────────────────────────

def _record_hoxel(
    action: str,
    outcome: str,
    details: dict[str, Any] | None = None,
) -> None:
    """Record a hoxel transition to the rs-surface API."""
    import urllib.request
    endpoint = os.environ.get(
        "RS_HOXEL_ENDPOINT",
        "http://100.101.247.127:8444/v1/hoxels/record",
    )
    payload = json.dumps({
        "obj_key": f"storage-agent/{action}",
        "bucket": "research-stack",
        "to_tier": "storage",
        "spectral_mode": "backup",
        "thermal_score": 0.0,
        "residual": 0.0,
        "payload_bytes": 0,
        "density": 1.0,
        "confidence": 1.0,
        "semantic_load": 0.0,
    }).encode()
    try:
        req = urllib.request.Request(
            endpoint, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp.read()
    except Exception:
        pass  # hoxel recording is advisory, never block the backup loop


# ── hashing helpers ───────────────────────────────────────────────────────────

def _sha256(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha256(data).hexdigest()


# ── 1. OBSERVE ────────────────────────────────────────────────────────────────

class Observation:
    """
    Immutable snapshot of storage stack state at one point in time.
    All numeric measurements stored as Q16_16 (UInt32) where meaningful.
    """

    def __init__(self) -> None:
        self.ts = datetime.now(timezone.utc).isoformat()
        self.garage_up: bool = False
        self.garage_nodes_total: int = 0
        self.garage_nodes_ok: int = 0
        self.garage_buckets: list[str] = []

        self.restic_snapshot_count: int = 0
        self.restic_latest_ts: str | None = None
        self.restic_latest_size_bytes: int = 0
        self.restic_stored_bytes: int = 0
        # dedup_ratio_q16: (1 - stored/total) * 65536, Q16_16
        self.dedup_ratio_q16: int = 0

        self.backup_log_last_ok: bool = False
        self.backup_log_last_ts: str | None = None

        self.cold_copy_needed: bool = False

        self.errors: list[str] = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "ts": self.ts,
            "garage": {
                "up":          self.garage_up,
                "nodes_total": self.garage_nodes_total,
                "nodes_ok":    self.garage_nodes_ok,
                "buckets":     self.garage_buckets,
            },
            "restic": {
                "snapshot_count":    self.restic_snapshot_count,
                "latest_ts":         self.restic_latest_ts,
                "latest_size_bytes": self.restic_latest_size_bytes,
                "stored_bytes":      self.restic_stored_bytes,
                "dedup_ratio_q16":   self.dedup_ratio_q16,
            },
            "backup_log": {
                "last_ok": self.backup_log_last_ok,
                "last_ts": self.backup_log_last_ts,
            },
            "cold_copy_needed": self.cold_copy_needed,
            "errors": self.errors,
        }


def _probe_garage(obs: Observation, creds: dict[str, str]) -> None:
    """Probe Garage: HTTP health check + bucket list."""
    import urllib.request
    import urllib.error
    try:
        req = urllib.request.Request(f"{creds['AWS_ENDPOINT_URL']}/", method="HEAD")
        urllib.request.urlopen(req, timeout=5)
        obs.garage_up = True
    except Exception:
        # A 403 from Garage means it IS up but rejects our unsigned HEAD —
        # that still counts as the service being reachable.
        try:
            urllib.request.urlopen(creds["AWS_ENDPOINT_URL"], timeout=5)
            obs.garage_up = True
        except urllib.error.HTTPError as e:
            if e.code in (403, 400):
                obs.garage_up = True
            else:
                obs.errors.append(f"garage_probe: HTTP {e.code}")
        except Exception as exc:
            obs.errors.append(f"garage_probe: {exc}")
            return

    if not obs.garage_up:
        return

    # Bucket list via aws cli
    rc, out, err = _run(
        ["aws", "s3", "ls", "--endpoint-url", creds["AWS_ENDPOINT_URL"]],
        env_extra=creds,
        timeout=30,
    ).returncode, "", ""
    result = _run(
        ["aws", "s3", "ls", "--endpoint-url", creds["AWS_ENDPOINT_URL"]],
        env_extra=creds,
        timeout=30,
    )
    if result.returncode == 0:
        obs.garage_buckets = [
            line.split()[-1] for line in result.stdout.splitlines() if line.strip()
        ]
    else:
        obs.errors.append(f"garage_ls: {result.stderr.strip()[:200]}")


def _probe_restic(obs: Observation, creds: dict[str, str]) -> None:
    """
    Probe restic: list snapshots in JSON mode, extract count, latest ts,
    and compute dedup ratio from the stats output.
    """
    if not obs.garage_up:
        obs.errors.append("restic_probe: skipped (Garage unreachable)")
        return

    # restic snapshots --json
    result = _run(
        ["restic", "snapshots", "--json"],
        env_extra=creds,
        timeout=60,
    )
    if result.returncode != 0:
        obs.errors.append(f"restic_snapshots: {result.stderr.strip()[:300]}")
        return

    try:
        snapshots = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        obs.errors.append(f"restic_snapshots_parse: {exc}")
        return

    if not isinstance(snapshots, list):
        obs.errors.append("restic_snapshots: unexpected JSON (not a list)")
        return

    obs.restic_snapshot_count = len(snapshots)

    if snapshots:
        # Sort by time, take most recent
        def _snap_ts(s: dict[str, Any]) -> str:
            return s.get("time", "")
        latest = sorted(snapshots, key=_snap_ts, reverse=True)[0]
        obs.restic_latest_ts = latest.get("time")
        # `paths` gives us the backup roots; we read the summary from a
        # separate stats call rather than parse the non-JSON snapshot size.

    # restic stats --json (whole-repo stats: blob count, total/unique sizes)
    result_stats = _run(
        ["restic", "stats", "--json"],
        env_extra=creds,
        timeout=120,
    )
    if result_stats.returncode == 0:
        try:
            stats = json.loads(result_stats.stdout)
            total = stats.get("total_size", 0)
            stored = stats.get("total_uncompressed_size", 0) or stats.get("total_size", 0)
            # Prefer blob_count and raw sizes when available.
            # restic ≥0.14 exposes "total_file_size" (pre-dedup) and
            # "total_size" (post-dedup stored).  Older versions only give
            # total_size; in that case dedup_ratio stays 0.
            pre_dedup = stats.get("total_file_size", 0)
            post_dedup = stats.get("total_size", 0)
            obs.restic_latest_size_bytes = pre_dedup
            obs.restic_stored_bytes = post_dedup

            if pre_dedup > 0:
                # dedup_ratio ∈ [0, 1]: fraction of data NOT stored (saved by dedup)
                # Q16_16: multiply by 65536 and truncate
                ratio_f = 1.0 - (post_dedup / pre_dedup)
                if ratio_f < 0:
                    ratio_f = 0.0
                obs.dedup_ratio_q16 = int(ratio_f * Q16_ONE)
        except (json.JSONDecodeError, KeyError, ZeroDivisionError) as exc:
            obs.errors.append(f"restic_stats_parse: {exc}")


def _probe_backup_log(obs: Observation) -> None:
    """
    Scan ~/.cache/restic-backup.log for the most recent run outcome.
    We look for the last occurrence of 'snapshot .* saved' or an error line.
    """
    log_path = Path.home() / ".cache" / "restic-backup.log"
    if not log_path.exists():
        obs.backup_log_last_ok = False
        return

    last_ok_ts: str | None = None
    last_err_ts: str | None = None
    try:
        text = log_path.read_text(errors="replace")
        for line in text.splitlines():
            if "snapshot" in line and "saved" in line:
                # Extract timestamp from log prefix [backup] HH:MM:SS
                parts = line.split()
                last_ok_ts = parts[1] if len(parts) > 1 else line[:20]
            elif "error" in line.lower() or "fatal" in line.lower():
                parts = line.split()
                last_err_ts = parts[1] if len(parts) > 1 else line[:20]
        # If most recent outcome after any error is a successful save, mark ok
        if last_ok_ts is not None:
            # Simple heuristic: ok if log ends with a saved line (not an error after it)
            obs.backup_log_last_ok = True
            obs.backup_log_last_ts = last_ok_ts
        else:
            obs.backup_log_last_ok = False
            obs.backup_log_last_ts = last_err_ts
    except OSError as exc:
        obs.errors.append(f"backup_log: {exc}")


def _probe_cold_copy_staleness(obs: Observation) -> None:
    """
    Determine whether a cold copy to gdrive is needed.
    Heuristic: if there are restic snapshots but the most recent one is
    more than 26 hours old AND no cold copy has run since then, flag it.
    This is intentionally conservative — rclone to gdrive is rate-limited.
    """
    if obs.restic_snapshot_count == 0:
        return

    if obs.restic_latest_ts is None:
        return

    try:
        from datetime import datetime as _dt
        latest = _dt.fromisoformat(obs.restic_latest_ts.rstrip("Z").split("+")[0])
        now_utc = _dt.now(timezone.utc).replace(tzinfo=None)
        age_hours = (now_utc - latest).total_seconds() / 3600.0
        # Flag for cold copy if newest snapshot is > 26 h old (daily timer
        # should have run, but may have been missed)
        if age_hours > 26:
            obs.cold_copy_needed = True
    except Exception as exc:
        obs.errors.append(f"cold_copy_staleness: {exc}")


def observe(creds: dict[str, str]) -> Observation:
    obs = Observation()
    _probe_garage(obs, creds)
    _probe_restic(obs, creds)
    _probe_backup_log(obs)
    _probe_cold_copy_staleness(obs)
    return obs


# ── 2. DECIDE ─────────────────────────────────────────────────────────────────

class Decision:
    """
    Threshold-based decision derived from an Observation.
    All thresholds are Q16_16 integers or plain integer counts.
    No logic in this class — pure data carrier.
    """

    def __init__(self) -> None:
        self.trigger_snap: bool = False          # run backup.sh snap
        self.trigger_cold_copy: bool = False     # run backup.sh cold-copy
        self.trigger_verify: bool = False        # run backup.sh verify
        self.trigger_forget: bool = False        # run backup.sh forget (prune)
        self.trigger_offload: bool = False       # run db-consolidate.sh offload
        self.trigger_garage_restart: bool = False

        self.alerts: list[str] = []
        self.rationale: list[str] = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "trigger_snap":            self.trigger_snap,
            "trigger_cold_copy":       self.trigger_cold_copy,
            "trigger_verify":          self.trigger_verify,
            "trigger_forget":          self.trigger_forget,
            "trigger_offload":         self.trigger_offload,
            "trigger_garage_restart":  self.trigger_garage_restart,
            "alerts":                  self.alerts,
            "rationale":               self.rationale,
        }


def decide(obs: Observation) -> Decision:
    d = Decision()

    # ── Garage health ──────────────────────────────────────────────────────
    if not obs.garage_up:
        d.alerts.append("ALERT: Garage S3 is unreachable at http://localhost:3900")
        d.trigger_garage_restart = True
        d.rationale.append("garage_up=False → trigger_garage_restart")

    # ── Restic snapshot health ─────────────────────────────────────────────
    if obs.restic_snapshot_count == 0 and obs.garage_up:
        d.alerts.append("ALERT: restic repo has zero snapshots — initial backup needed")
        d.trigger_snap = True
        d.rationale.append("snapshot_count=0 → trigger_snap")

    if not obs.backup_log_last_ok and obs.garage_up:
        d.alerts.append("WARN: No successful restic snapshot found in backup log")
        d.trigger_snap = True
        d.rationale.append("backup_log_last_ok=False → trigger_snap")

    # ── Dedup ratio: if very poor (<30%), a verify pass may find orphan blobs ──
    if (
        obs.dedup_ratio_q16 > 0
        and obs.dedup_ratio_q16 < Q16_DEDUP_LOW
        and obs.restic_snapshot_count > 5
    ):
        d.trigger_verify = True
        d.rationale.append(
            f"dedup_ratio_q16={obs.dedup_ratio_q16} < Q16_DEDUP_LOW={Q16_DEDUP_LOW} "
            f"and snapshot_count={obs.restic_snapshot_count} > 5 → trigger_verify"
        )

    # ── Prune: if snapshot count grows without retention policy running ────
    if obs.restic_snapshot_count > 30:
        d.trigger_forget = True
        d.rationale.append(
            f"snapshot_count={obs.restic_snapshot_count} > 30 → trigger_forget (prune)"
        )

    # ── Cold copy ─────────────────────────────────────────────────────────
    if obs.cold_copy_needed:
        d.alerts.append(
            "WARN: Newest restic snapshot is >26 h old but cold copy to gdrive appears stale"
        )
        d.trigger_cold_copy = True
        d.rationale.append("cold_copy_needed=True → trigger_cold_copy")

    # ── DB offload: always worth running if Garage is up ──────────────────
    # (offload is idempotent; no-op if no .db files changed)
    if obs.garage_up:
        d.trigger_offload = True
        d.rationale.append("garage_up=True → trigger_offload (idempotent)")

    return d


# ── 3. ACT ────────────────────────────────────────────────────────────────────

class ActionResult:
    def __init__(self) -> None:
        self.actions_attempted: list[str] = []
        self.actions_succeeded: list[str] = []
        self.actions_failed: list[str] = []
        self.details: dict[str, Any] = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "actions_attempted": self.actions_attempted,
            "actions_succeeded": self.actions_succeeded,
            "actions_failed":    self.actions_failed,
            "details":           self.details,
        }


def _act_one(
    label: str,
    args: list[str],
    ar: ActionResult,
    env_extra: dict[str, str] | None = None,
    timeout: int = 600,
) -> None:
    ar.actions_attempted.append(label)
    try:
        result = _run(args, env_extra=env_extra, timeout=timeout)
        if result.returncode == 0:
            ar.actions_succeeded.append(label)
            ar.details[label] = {
                "rc": 0,
                "stdout_tail": result.stdout[-500:].strip(),
            }
        else:
            ar.actions_failed.append(label)
            ar.details[label] = {
                "rc":     result.returncode,
                "stderr": result.stderr[-500:].strip(),
                "stdout": result.stdout[-200:].strip(),
            }
    except subprocess.TimeoutExpired:
        ar.actions_failed.append(label)
        ar.details[label] = {"rc": -1, "error": "timeout"}
    except Exception as exc:
        ar.actions_failed.append(label)
        ar.details[label] = {"rc": -1, "error": str(exc)}


def act(
    d: Decision,
    creds: dict[str, str],
    probe_only: bool = False,
    dry_run: bool = False,
) -> ActionResult:
    ar = ActionResult()

    if probe_only or dry_run:
        ar.details["mode"] = "probe_only" if probe_only else "dry_run"
        return ar

    # ── Garage restart ─────────────────────────────────────────────────────
    if d.trigger_garage_restart:
        _act_one(
            "garage_restart",
            ["systemctl", "--user", "restart", "garage.service"],
            ar,
            timeout=30,
        )
        # If user-level fails, try system-level (Garage runs as system service)
        if "garage_restart" in ar.actions_failed:
            _act_one(
                "garage_restart_system",
                ["sudo", "systemctl", "restart", "garage.service"],
                ar,
                timeout=30,
            )

    # ── Snap ───────────────────────────────────────────────────────────────
    if d.trigger_snap:
        _act_one(
            "restic_snap",
            ["bash", str(BACKUP_SH), "snap", "agent-triggered"],
            ar,
            env_extra=creds,
            timeout=3600,
        )
        if "restic_snap" not in ar.actions_failed:
            _record_hoxel("snap", "success")

    # ── Cold copy ──────────────────────────────────────────────────────────
    if d.trigger_cold_copy:
        _act_one(
            "restic_cold_copy",
            ["bash", str(BACKUP_SH), "cold-copy"],
            ar,
            env_extra=creds,
            timeout=3600,
        )
        if "restic_cold_copy" not in ar.actions_failed:
            _record_hoxel("cold_copy", "success")

    # ── Verify ─────────────────────────────────────────────────────────────
    if d.trigger_verify:
        _act_one(
            "restic_verify",
            ["bash", str(BACKUP_SH), "verify"],
            ar,
            env_extra=creds,
            timeout=600,
        )
        if "restic_verify" not in ar.actions_failed:
            _record_hoxel("verify", "success")

    # ── Forget / prune ─────────────────────────────────────────────────────
    if d.trigger_forget:
        _act_one(
            "restic_forget",
            ["bash", str(BACKUP_SH), "forget"],
            ar,
            env_extra=creds,
            timeout=600,
        )
        if "restic_forget" not in ar.actions_failed:
            _record_hoxel("forget", "success")

    # ── DB offload ─────────────────────────────────────────────────────────
    if d.trigger_offload:
        _act_one(
            "db_offload",
            ["bash", str(CONSOLIDATE_SH), "offload"],
            ar,
            env_extra=creds,
            timeout=300,
        )
        if "db_offload" not in ar.actions_failed:
            _record_hoxel("offload", "success")

    return ar


# ── 4. EMIT RECEIPT ───────────────────────────────────────────────────────────

def _build_receipt(
    tick: int,
    parent_hash: str,
    obs: Observation,
    dec: Decision,
    ar: ActionResult,
) -> dict[str, Any]:
    """
    Assemble a storage_agent_receipt_v1 object.
    receipt_hash is SHA-256 of the canonical preimage (excluding receipt_hash
    itself and generated_at_utc for stability).
    """
    receipt: dict[str, Any] = {
        "schema":           SCHEMA,
        "version":          VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "tick":             tick,
        "parent_hash":      parent_hash,
        "observation":      obs.to_dict(),
        "decision":         dec.to_dict(),
        "action_result":    ar.to_dict(),
        "claim_boundary":   "storage-agent-observe-decide-act-only",
    }

    preimage = {
        k: v for k, v in receipt.items()
        if k not in ("generated_at_utc", "receipt_hash")
    }
    receipt["receipt_hash"] = _sha256(json.dumps(preimage, sort_keys=True))
    return receipt


def _emit_local(receipt: dict[str, Any]) -> None:
    """Append receipt to the local JSONL hash-chain log."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as fh:
        fh.write(json.dumps(receipt) + "\n")


def _emit_s3(receipt: dict[str, Any], creds: dict[str, str]) -> tuple[bool, str]:
    """
    Upload the receipt JSON to Garage:research-stack/agent-receipts/<date>/<hash>.json
    via the aws cli.  Returns (ok, key).
    """
    ts = receipt.get("generated_at_utc", "")[:10]
    h = receipt["receipt_hash"][:16]
    key = f"{RECEIPT_PREFIX}/{ts}/{h}.json"
    payload = json.dumps(receipt, indent=2).encode()

    # Write to a temp file so aws cp can read it
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        tf.write(payload)
        tmp_path = tf.name

    result = _run(
        [
            "aws", "s3", "cp",
            "--endpoint-url", creds["AWS_ENDPOINT_URL"],
            tmp_path,
            f"s3://{GARAGE_BUCKET}/{key}",
            "--content-type", "application/json",
        ],
        env_extra=creds,
        timeout=60,
    )
    Path(tmp_path).unlink(missing_ok=True)
    return result.returncode == 0, key


# ── 5. MAIN CYCLE ─────────────────────────────────────────────────────────────

def run_cycle(
    tick: int,
    parent_hash: str,
    creds: dict[str, str],
    probe_only: bool = False,
    dry_run: bool = False,
    no_s3: bool = False,
) -> str:
    """
    One full Observe → Decide → Act → Emit cycle.
    Returns the new receipt_hash for hash-chain continuity.
    """
    obs = observe(creds)
    dec = decide(obs)
    ar = act(dec, creds, probe_only=probe_only, dry_run=dry_run)
    receipt = _build_receipt(tick, parent_hash, obs, dec, ar)

    _emit_local(receipt)

    s3_ok = False
    s3_key = ""
    if not no_s3 and obs.garage_up:
        s3_ok, s3_key = _emit_s3(receipt, creds)

    # Human-readable summary to stdout
    alerts = dec.alerts
    successes = ar.actions_succeeded
    failures = ar.actions_failed
    mode_tag = " [probe-only]" if probe_only else (" [dry-run]" if dry_run else "")
    print(
        f"[storage-agent] tick={tick}{mode_tag} "
        f"garage={'UP' if obs.garage_up else 'DOWN'} "
        f"snapshots={obs.restic_snapshot_count} "
        f"dedup_q16={obs.dedup_ratio_q16} "
        f"alerts={len(alerts)} "
        f"acted={successes} "
        f"failed={failures} "
        f"hash={receipt['receipt_hash'][:16]}... "
        + (f"s3={s3_key}" if s3_ok else "s3=skipped")
    )
    for alert in alerts:
        print(f"  ! {alert}", file=sys.stderr)

    return receipt["receipt_hash"]


def _resume_chain() -> tuple[int, str]:
    """Read the last tick and hash from the local JSONL chain."""
    if not LOG_PATH.exists():
        return 0, ""
    last_tick = 0
    last_hash = ""
    try:
        with open(LOG_PATH) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    last_tick = entry.get("tick", last_tick)
                    last_hash = entry.get("receipt_hash", last_hash)
                except json.JSONDecodeError:
                    pass
    except OSError:
        pass
    return last_tick, last_hash


# ── CLI ────────────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="storage_agent.py — Observe / Optimize / Act for the storage stack",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--probe-only", action="store_true",
                   help="Observe and emit receipt; take no actions.")
    p.add_argument("--dry-run", action="store_true",
                   help="Print what would be done, but do nothing.")
    p.add_argument("--no-s3", action="store_true",
                   help="Skip uploading receipt to Garage S3.")
    p.add_argument("--loop", action="store_true",
                   help="Run in polling loop (default: one-shot).")
    p.add_argument("--interval", type=int, default=900,
                   help="Seconds between loop ticks (default: 900).")
    p.add_argument("--once", action="store_true", default=True,
                   help="Run exactly one cycle (default).")
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    creds = _load_garage_env()

    tick, parent_hash = _resume_chain()
    tick += 1

    if args.loop:
        print(f"[storage-agent] loop mode, interval={args.interval}s, resuming tick={tick}")
        while True:
            try:
                parent_hash = run_cycle(
                    tick=tick,
                    parent_hash=parent_hash,
                    creds=creds,
                    probe_only=args.probe_only,
                    dry_run=args.dry_run,
                    no_s3=args.no_s3,
                )
                tick += 1
            except Exception as exc:
                print(f"[storage-agent] cycle error (tick={tick}): {exc}", file=sys.stderr)
            time.sleep(args.interval)
    else:
        run_cycle(
            tick=tick,
            parent_hash=parent_hash,
            creds=creds,
            probe_only=args.probe_only,
            dry_run=args.dry_run,
            no_s3=args.no_s3,
        )


if __name__ == "__main__":
    main()
