#!/usr/bin/env python3
# PTOS: LAYER=INFRA / DOMAIN=ORCHESTRATOR / CONDITION=ALPHA
"""
unified_orchestrator.py — Unified Observe → Decide → Act → Emit loop.

Merges:
  - infra_controller.py   (node health probes via SSH)
  - storage_agent.py      (Garage/restic backup stack probes)

Both run in the same cycle. Decisions and actions are dispatched separately
but emitted as a single unified receipt. Hoxels recorded for every action.

Usage:
    python3 4-Infrastructure/auto/orchestrator.py [options]

Options:
    --once          Run one cycle and exit (default)
    --probe-only    Observe only, emit receipt, no actions
    --dry-run       Show what would happen, don't execute
    --loop          Run in polling loop
    --interval N    Seconds between ticks (default: 300)
    --dump          Print receipt to stdout
"""
from __future__ import annotations

import sys
import os
import time
import json
import hashlib
import argparse
import shlex
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AUTO_DIR = Path(__file__).resolve().parent
INFRA_DIR = AUTO_DIR.parent
sys.path.insert(0, str(INFRA_DIR))

from auto.lib.config import load_config
from auto.lib.receipt import read_chain, write_receipt, sha256
from auto.lib.probe import run_probe
from auto.lib.alerting import Alerter
from auto.lib.q16 import Q16_ONE

SCHEMA = "unified_orchestrator_receipt_v1"
VERSION = "1.0.0"
LOG_PATH = Path.home() / ".cache" / "orchestrator.jsonl"

BACKUP_SH = INFRA_DIR / "storage" / "restic" / "backup.sh"
CONSOLIDATE_SH = INFRA_DIR / "storage" / "garage" / "db-consolidate.sh"


# ── helpers ─────────────────────────────────────────────────────────────────────

def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def _log(msg: str) -> None:
    print(f"[{_ts()}] {msg}", file=sys.stderr, flush=True)


def _run(
    args: list[str],
    env_extra: dict[str, str] | None = None,
    timeout: int = 120,
) -> tuple[int, str, str]:
    import subprocess
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout, env=env)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except Exception as e:
        return -1, "", str(e)


def _send_alert(subject: str, body: str) -> None:
    """Send an alert email via the microvm-racknerd msmtp relay."""
    import subprocess
    target = os.environ.get("RS_ALERT_RELAY_SSH_TARGET", "root@100.101.247.127")
    remote = (
        "send-alert "
        f"{shlex.quote(subject)} "
        f"{shlex.quote(body)}"
    )
    cmd = [
        "ssh", "-o", "StrictHostKeyChecking=no",
        target,
        remote,
    ]
    try:
        subprocess.run(cmd, capture_output=True, timeout=30)
    except Exception:
        pass


def _record_hoxel(action: str, outcome: str, domain: str = "infra") -> None:
    import urllib.request
    endpoint = os.environ.get(
        "RS_HOXEL_ENDPOINT",
        "http://100.101.247.127:8444/v1/hoxels/record",
    )
    payload = json.dumps({
        "obj_key": f"orchestrator/{action}",
        "bucket": "research-stack",
        "to_tier": domain,
        "spectral_mode": "orchestration",
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
        with urllib.request.urlopen(req, timeout=10):
            pass
    except Exception:
        pass


# ── Garage/restic credential loading (from storage_agent) ───────────────────────

def _load_garage_env() -> dict[str, str]:
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
    return {
        "AWS_ACCESS_KEY_ID": env.get("GARAGE_ACCESS_KEY_ID", os.environ.get("AWS_ACCESS_KEY_ID", "")),
        "AWS_SECRET_ACCESS_KEY": env.get("GARAGE_SECRET_ACCESS_KEY", os.environ.get("AWS_SECRET_ACCESS_KEY", "")),
        "AWS_DEFAULT_REGION": env.get("AWS_DEFAULT_REGION", os.environ.get("AWS_DEFAULT_REGION", "garage")),
        "AWS_ENDPOINT_URL": env.get("AWS_ENDPOINT_URL", os.environ.get("AWS_ENDPOINT_URL", "http://localhost:3900")),
        "RESTIC_REPOSITORY": os.environ.get("RESTIC_REPOSITORY", "s3:http://localhost:3900/research-stack"),
        "RESTIC_PASSWORD_FILE": os.environ.get("RESTIC_PASSWORD_FILE", "/etc/garage/restic-password"),
    }


# ── 1. OBSERVE ──────────────────────────────────────────────────────────────────

class StorageObservation:
    def __init__(self) -> None:
        self.garage_up: bool = False
        self.garage_nodes_total: int = 0
        self.garage_nodes_ok: int = 0
        self.garage_buckets: list[str] = []
        self.restic_snapshot_count: int = 0
        self.restic_latest_ts: str | None = None
        self.restic_latest_size_bytes: int = 0
        self.restic_stored_bytes: int = 0
        self.dedup_ratio_q16: int = 0
        self.backup_log_last_ok: bool = False
        self.cold_copy_needed: bool = False
        self.errors: list[str] = []

    def to_dict(self) -> dict:
        return {
            "garage_up": self.garage_up,
            "garage_nodes_total": self.garage_nodes_total,
            "garage_nodes_ok": self.garage_nodes_ok,
            "garage_buckets": self.garage_buckets,
            "restic": {
                "snapshot_count": self.restic_snapshot_count,
                "latest_ts": self.restic_latest_ts,
                "latest_size_bytes": self.restic_latest_size_bytes,
                "stored_bytes": self.restic_stored_bytes,
                "dedup_ratio_q16": self.dedup_ratio_q16,
            },
            "backup_log_last_ok": self.backup_log_last_ok,
            "cold_copy_needed": self.cold_copy_needed,
            "errors": self.errors,
        }


class InfraObservation:
    def __init__(self) -> None:
        self.probes: dict[str, Any] = {}
        self.critical_down: list[str] = []
        self.optional_unavailable: list[str] = []
        self.backup_status: dict[str, Any] = {}
        self.garage_status: dict[str, Any] = {}

    def to_dict(self) -> dict:
        return {
            "probes": {
                n: [r.to_dict() if hasattr(r, "to_dict") else r.__dict__ for r in rs]
                for n, rs in self.probes.items()
            },
            "critical_down": self.critical_down,
            "optional_unavailable": self.optional_unavailable,
            "backup_status": self.backup_status,
            "garage_status": self.garage_status,
        }


def _probe_garage(obs: StorageObservation, creds: dict[str, str]) -> None:
    import urllib.request
    import urllib.error
    try:
        urllib.request.urlopen(creds["AWS_ENDPOINT_URL"], timeout=5)
        obs.garage_up = True
    except urllib.error.HTTPError as e:
        if e.code in (403, 400):
            obs.garage_up = True
        else:
            obs.errors.append(f"garage: HTTP {e.code}")
    except Exception as exc:
        obs.errors.append(f"garage: {exc}")
        return

    rc, out, err = _run(
        ["aws", "s3", "ls", "--endpoint-url", creds["AWS_ENDPOINT_URL"]],
        env_extra=creds, timeout=30,
    )
    if rc == 0:
        obs.garage_buckets = [line.split()[-1] for line in out.splitlines() if line.strip()]


def _probe_restic(obs: StorageObservation, creds: dict[str, str]) -> None:
    if not obs.garage_up:
        obs.errors.append("restic: skipped (Garage unreachable)")
        return
    rc, out, err = _run(["restic", "snapshots", "--json"], env_extra=creds, timeout=60)
    if rc != 0:
        obs.errors.append(f"restic snapshots: {err.strip()[:300]}")
        return
    try:
        snapshots = json.loads(out)
    except json.JSONDecodeError as e:
        obs.errors.append(f"restic parse: {e}")
        return
    obs.restic_snapshot_count = len(snapshots)
    if snapshots:
        latest = sorted(snapshots, key=lambda s: s.get("time", ""), reverse=True)[0]
        obs.restic_latest_ts = latest.get("time")

    rc2, out2, err2 = _run(["restic", "stats", "--json"], env_extra=creds, timeout=120)
    if rc2 == 0:
        try:
            stats = json.loads(out2)
            pre = stats.get("total_file_size", 0)
            post = stats.get("total_size", 0)
            obs.restic_latest_size_bytes = pre
            obs.restic_stored_bytes = post
            if pre > 0:
                ratio = max(0.0, 1.0 - (post / pre))
                obs.dedup_ratio_q16 = int(ratio * Q16_ONE)
        except (json.JSONDecodeError, KeyError, ZeroDivisionError) as e:
            obs.errors.append(f"restic stats: {e}")


def _probe_backup_log(obs: StorageObservation) -> None:
    log_path = Path.home() / ".cache" / "restic-backup.log"
    if not log_path.exists():
        return
    try:
        text = log_path.read_text(errors="replace")
        obs.backup_log_last_ok = any("snapshot" in l and "saved" in l for l in text.splitlines())
    except OSError as e:
        obs.errors.append(f"backup log: {e}")


def _probe_cold_copy(obs: StorageObservation) -> None:
    if obs.restic_snapshot_count == 0 or obs.restic_latest_ts is None:
        return
    try:
        latest = datetime.fromisoformat(obs.restic_latest_ts.rstrip("Z").split("+")[0])
        age = (datetime.now(timezone.utc).replace(tzinfo=None) - latest).total_seconds() / 3600
        obs.cold_copy_needed = age > 26
    except Exception as e:
        obs.errors.append(f"cold copy: {e}")


def observe_storage(creds: dict[str, str]) -> StorageObservation:
    obs = StorageObservation()
    _probe_garage(obs, creds)
    _probe_restic(obs, creds)
    _probe_backup_log(obs)
    _probe_cold_copy(obs)
    return obs


def observe_infra(config: dict) -> tuple[InfraObservation, Alerter]:
    obs = InfraObservation()
    alerter = Alerter(config)
    nodes = config.get("nodes", {})
    tier_1 = set(config.get("tier_1_required", []))

    from concurrent.futures import ThreadPoolExecutor, as_completed
    futures = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        for name, cfg in nodes.items():
            ip = cfg["ip"]
            target = cfg.get("ssh_target", f"root@{ip}")
            optional = cfg.get("optional", False)
            for pname in cfg.get("probes", []):
                f = pool.submit(run_probe, name, ip, target, pname, optional)
                futures[f] = (name, pname, optional)

    for f in as_completed(futures):
        name, pname, optional = futures[f]
        try:
            result = f.result()
        except Exception as e:
            result = type("PR", (), {})()
            result.__dict__ = {"node": name, "ip": "", "optional": optional, "reachable": False, "error": str(e), "data": {}, "elapsed_ms": 0}
        obs.probes.setdefault(name, []).append(result)
        if not result.reachable and not optional:
            obs.critical_down.append(name)
            alerter.alert(f"node DOWN: {name} unreachable")
        elif not result.reachable and optional:
            obs.optional_unavailable.append(name)
            alerter.note(f"optional node unavailable: {name}")

    obs.critical_down = sorted(set(obs.critical_down))
    obs.optional_unavailable = sorted(set(obs.optional_unavailable))
    return obs, alerter


# ── 2. DECIDE ───────────────────────────────────────────────────────────────────

class UnifiedDecision:
    def __init__(self) -> None:
        self.storage_actions: list[str] = []
        self.infra_actions: list[str] = []
        self.alerts: list[str] = []

    def to_dict(self) -> dict:
        return {
            "storage_actions": self.storage_actions,
            "infra_actions": self.infra_actions,
            "alerts": self.alerts,
        }


Q16_DEDUP_LOW = 19661


def decide(
    storage: StorageObservation,
    infra: InfraObservation,
    alerter: Alerter,
) -> UnifiedDecision:
    d = UnifiedDecision()

    # ── Storage decisions ───────────────────────────────────────────────────
    if not storage.garage_up:
        d.storage_actions.append("restart_garage")
        d.alerts.append("Garage S3 unreachable")
    if storage.restic_snapshot_count == 0 and storage.garage_up:
        d.storage_actions.append("snap")
    if not storage.backup_log_last_ok and storage.garage_up:
        d.storage_actions.append("snap")
    if (
        storage.dedup_ratio_q16 > 0
        and storage.dedup_ratio_q16 < Q16_DEDUP_LOW
        and storage.restic_snapshot_count > 5
    ):
        d.storage_actions.append("verify")
    if storage.restic_snapshot_count > 30:
        d.storage_actions.append("forget")
    if storage.cold_copy_needed:
        d.storage_actions.append("cold_copy")
    if storage.garage_up:
        d.storage_actions.append("offload")

    # ── Infra decisions ────────────────────────────────────────────────────
    has_infra_issues = bool(
        infra.critical_down
        or infra.backup_status.get("snapshot_count", 0) == 0
        or infra.garage_status.get("healthy_nodes", 0) < 3
    )
    if has_infra_issues:
        d.infra_actions.append("dispatch_alerts")

    d.alerts.extend(alerter.alerts)
    return d


# ── 3. ACT ──────────────────────────────────────────────────────────────────────

class UnifiedActionResult:
    def __init__(self) -> None:
        self.storage_succeeded: list[str] = []
        self.storage_failed: list[str] = []
        self.infra_dispatched: list[str] = []

    def to_dict(self) -> dict:
        return {
            "storage_succeeded": self.storage_succeeded,
            "storage_failed": self.storage_failed,
            "infra_dispatched": self.infra_dispatched,
        }


def _act_one(
    label: str,
    args: list[str],
    succeeded: list[str],
    failed: list[str],
    env_extra: dict[str, str] | None = None,
    timeout: int = 600,
) -> None:
    rc, out, err = _run(args, env_extra=env_extra, timeout=timeout)
    if rc == 0:
        succeeded.append(label)
        _record_hoxel(label, "success", "storage")
    else:
        failed.append(label)


def act_storage(d: UnifiedDecision, creds: dict[str, str], probe_only: bool, dry_run: bool) -> tuple[list[str], list[str]]:
    succeeded: list[str] = []
    failed: list[str] = []

    if probe_only or dry_run:
        return succeeded, failed

    for action in d.storage_actions:
        if action == "restart_garage":
            _act_one("restart_garage", ["systemctl", "--user", "restart", "garage.service"], succeeded, failed, timeout=30)
            if "restart_garage" in failed:
                _act_one("restart_garage_system", ["sudo", "systemctl", "restart", "garage.service"], succeeded, failed, timeout=30)
        elif action == "snap":
            _act_one("snap", ["bash", str(BACKUP_SH), "snap", "orchestrator-triggered"], succeeded, failed, env_extra=creds, timeout=3600)
        elif action == "cold_copy":
            _act_one("cold_copy", ["bash", str(BACKUP_SH), "cold-copy"], succeeded, failed, env_extra=creds, timeout=3600)
        elif action == "verify":
            _act_one("verify", ["bash", str(BACKUP_SH), "verify"], succeeded, failed, env_extra=creds, timeout=600)
        elif action == "forget":
            _act_one("forget", ["bash", str(BACKUP_SH), "forget"], succeeded, failed, env_extra=creds, timeout=600)
        elif action == "offload":
            _act_one("offload", ["bash", str(CONSOLIDATE_SH), "offload"], succeeded, failed, env_extra=creds, timeout=300)

    return succeeded, failed


def act_infra(d: UnifiedDecision, alerter: Alerter, dry_run: bool) -> list[str]:
    if dry_run:
        return []
    if "dispatch_alerts" in d.infra_actions:
        result = alerter.send()
        return list(result.keys())
    return []


# ── 4. EMIT RECEIPT ─────────────────────────────────────────────────────────────

def build_receipt(
    tick: int,
    parent_hash: str,
    storage_obs: StorageObservation,
    infra_obs: InfraObservation,
    decision: UnifiedDecision,
    result: UnifiedActionResult,
) -> dict:
    receipt = {
        "schema": SCHEMA,
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "tick": tick,
        "parent_hash": parent_hash,
        "observation": {
            "storage": storage_obs.to_dict(),
            "infra": infra_obs.to_dict(),
        },
        "decision": decision.to_dict(),
        "action_result": result.to_dict(),
        "claim_boundary": "unified-orchestrator-observe-decide-act",
    }
    preimage = {k: v for k, v in receipt.items() if k not in ("generated_at_utc", "receipt_hash")}
    receipt["receipt_hash"] = sha256(json.dumps(preimage, sort_keys=True))
    return receipt


def emit_local(receipt: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(receipt) + "\n")
    write_receipt(receipt)


# ── 5. MAIN CYCLE ───────────────────────────────────────────────────────────────

def run_cycle(
    config: dict,
    creds: dict[str, str],
    tick: int,
    parent_hash: str,
    probe_only: bool = False,
    dry_run: bool = False,
) -> str:
    _log(f"tick={tick} starting unified cycle...")

    storage_obs = observe_storage(creds)
    infra_obs, alerter = observe_infra(config)

    dec = decide(storage_obs, infra_obs, alerter)

    storage_ok, storage_fail = act_storage(dec, creds, probe_only=probe_only, dry_run=dry_run)
    infra_dispatch = act_infra(dec, alerter, dry_run=dry_run)

    result = UnifiedActionResult()
    result.storage_succeeded = storage_ok
    result.storage_failed = storage_fail
    result.infra_dispatched = infra_dispatch

    receipt = build_receipt(tick, parent_hash, storage_obs, infra_obs, dec, result)
    emit_local(receipt)

    summary = (
        f"tick={tick} "
        f"garage={'UP' if storage_obs.garage_up else 'DOWN'} "
        f"snapshots={storage_obs.restic_snapshot_count} "
        f"nodes_down={len(infra_obs.critical_down)} "
        f"storage_ok={storage_ok} "
        f"storage_fail={storage_fail} "
        f"hash={receipt['receipt_hash'][:16]}..."
    )
    _log(summary)

    for alert in dec.alerts:
        _log(f"  ALERT: {alert}")
        if not dry_run:
            _send_alert("Orchestrator Alert", alert)

    if infra_obs.critical_down and not dry_run:
        _send_alert("Node DOWN", f"Critical nodes unreachable: {', '.join(infra_obs.critical_down)}")

    for h in storage_ok:
        _record_hoxel(h, "success", "storage")
    for h in storage_fail:
        _record_hoxel(h, "failure", "storage")

    return receipt["receipt_hash"]


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(description="unified_orchestrator.py — unified infrastructure daemon")
    p.add_argument("--once", action="store_true", default=True)
    p.add_argument("--probe-only", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--loop", action="store_true")
    p.add_argument("--interval", type=int, default=300)
    p.add_argument("--dump", action="store_true")
    args = p.parse_args()

    config = load_config()
    creds = _load_garage_env()

    tick, parent_hash = read_chain()
    tick += 1

    if args.loop:
        _log(f"loop mode, interval={args.interval}s, resuming tick={tick}")
        while True:
            try:
                parent_hash = run_cycle(config, creds, tick, parent_hash,
                                         probe_only=args.probe_only,
                                         dry_run=args.dry_run)
                tick += 1
            except Exception as e:
                _log(f"cycle error: {e}")
                import traceback
                traceback.print_exc(file=sys.stderr)
            time.sleep(args.interval)
    else:
        run_cycle(config, creds, tick, parent_hash,
                  probe_only=args.probe_only,
                  dry_run=args.dry_run)
        if args.dump:
            if LOG_PATH.exists():
                with open(LOG_PATH) as f:
                    lines = f.readlines()
                    if lines:
                        print(lines[-1].strip())


if __name__ == "__main__":
    main()
