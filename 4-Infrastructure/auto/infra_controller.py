#!/usr/bin/env python3
# PTOS: LAYER=INFRA / DOMAIN=AUTOMATION / CONDITION=ALPHA
"""
infra_controller.py — Full-loop infrastructure health orchestration.

Runs on 361395-1 (Netcup VPS) as the control plane. Probes all nodes via SSH,
collects health status, makes decisions, dispatches alerts. qfox-1 is treated
as opportunistic — its absence is logged but not alerted.

Observe → Decide → Act → Emit receipt cycle. Systemd timer fires every 5 min.

Usage:
    python3 4-Infrastructure/auto/infra_controller.py [options]

Options:
    --once        Run one cycle and exit (default)
    --probe-only  Observe only, emit receipt, no actions
    --dry-run     Show what would happen, don't execute
    --loop N      Run every N seconds (default: 300)
    --dump        Print full receipt to stdout instead of JSONL
"""
from __future__ import annotations

import sys
import os
import time
from pathlib import Path
from typing import Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse

# Set up paths so we can import from auto.lib regardless of cwd
AUTO_DIR = Path(__file__).resolve().parent         # 4-Infrastructure/auto/
INFRA_DIR = AUTO_DIR.parent                         # 4-Infrastructure/
sys.path.insert(0, str(INFRA_DIR))

from auto.lib.config import load_config

def _record_hoxel(obs: Observation, status: str) -> None:
    """Record node health as a hoxel transition to the rs-surface API."""
    import json
    import urllib.request
    endpoint = os.environ.get(
        "RS_HOXEL_ENDPOINT",
        "http://100.101.247.127:8444/v1/hoxels/record",
    )
    payload = json.dumps({
        "obj_key": "infra-controller/cycle",
        "bucket": "research-stack",
        "to_tier": "infra",
        "spectral_mode": "health",
        "thermal_score": len(obs.critical_down) / max(len(obs.probes), 1),
        "residual": len(obs.optional_unavailable) / max(len(obs.probes), 1),
        "payload_bytes": len(obs.probes),
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
        pass  # hoxel recording is advisory, never block the probe loop
from auto.lib.probe import run_probe
from auto.lib.receipt import build_receipt, write_receipt, read_chain
from auto.lib.alerting import Alerter


# ── helpers ────────────────────────────────────────────────────────────────────

def _ts() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def _log(msg: str) -> None:
    print(f"[{_ts()}] {msg}", file=sys.stderr, flush=True)


# ── OBSERVE ────────────────────────────────────────────────────────────────────

class Observation:
    def __init__(self) -> None:
        self.probes: dict[str, Any] = {}       # node_name → list of probe results
        self.backup_status: dict[str, Any] = {}
        self.garage_status: dict[str, Any] = {}
        self.optional_unavailable: list[str] = []
        self.critical_down: list[str] = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "probes": {
                node: [r.to_dict() for r in results]
                for node, results in self.probes.items()
            },
            "backup_status": self.backup_status,
            "garage_status": self.garage_status,
            "optional_unavailable": self.optional_unavailable,
            "critical_down": self.critical_down,
        }


def observe(config: dict) -> tuple[Observation, Alerter]:
    obs = Observation()
    alerter = Alerter(config)
    nodes_cfg = config.get("nodes", {})
    tier_1 = set(config.get("tier_1_required", []))

    # Probe all nodes in parallel
    futures: dict = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        for node_name, node_cfg in nodes_cfg.items():
            ip = node_cfg["ip"]
            ssh_target = node_cfg.get("ssh_target", f"root@{ip}")
            optional = node_cfg.get("optional", False)
            probe_names = node_cfg.get("probes", [])
            for pname in probe_names:
                fut = pool.submit(run_probe, node_name, ip, ssh_target, pname, optional)
                futures[fut] = (node_name, pname, optional)

    for fut in as_completed(futures):
        node_name, pname, optional = futures[fut]
        try:
            result = fut.result()
        except Exception as exc:
            result = type("Pr", (), {})()
            result.__dict__ = {
                "node": node_name, "ip": "",
                "optional": optional, "reachable": False,
                "error": str(exc), "data": {}, "elapsed_ms": 0,
            }
        obs.probes.setdefault(node_name, []).append(result)

        if not result.reachable and not optional:
            obs.critical_down.append(node_name)
            node_role = nodes_cfg[node_name].get("roles", [])
            alerter.alert(f"node DOWN: {node_name} ({', '.join(node_role)}) is unreachable")
        elif not result.reachable and optional:
            obs.optional_unavailable.append(node_name)
            alerter.note(f"optional node unavailable: {node_name}")

        # Parse probe-specific data into structured fields
        _parse_probe_data(obs, node_name, pname, result, alerter, config)

    # Aggregate garage status across all nodes that probed it
    _aggregate_garage_status(obs, alerter, config)

    # Deduplicate unavailable lists (each node may have multiple probes)
    obs.critical_down = sorted(set(obs.critical_down))
    obs.optional_unavailable = sorted(set(obs.optional_unavailable))

    # Aggregate backup status
    _aggregate_backup_status(obs, alerter, config)

    return obs, alerter


def _parse_probe_data(obs, node_name, pname, result, alerter, config):
    thresh = config.get("thresholds", {})
    data = result.data if result.reachable else {}

    if pname == "system":
        disk_pct = int(data.get("disk", {}).get("used_pct", 0) or 0)
        mem_pct = int(data.get("memory", {}).get("used_pct", 0) or 0)
        if disk_pct >= thresh.get("disk_warn_pct", 90):
            alerter.warn(f"high disk usage: {node_name} at {disk_pct}%")
        if mem_pct >= thresh.get("memory_warn_pct", 90):
            alerter.warn(f"high memory usage: {node_name} at {mem_pct}%")

    elif pname == "caddy":
        cert_days = int(data.get("cert_days_remaining", 999) or 999)
        if cert_days < thresh.get("cert_min_days", 30):
            alerter.alert(f"SSL certificate expiring: {node_name} has {cert_days} days remaining")
        if not data.get("caddy_running", True):
            alerter.alert(f"caddy not running on {node_name}")

    elif pname == "restic":
        if data.get("restic_reachable"):
            hours = int(data.get("latest_age_hours", 0) or 0)
            max_age = thresh.get("restic_max_age_hours", 28)
            if hours > max_age:
                alerter.warn(f"restic snapshot age: {node_name} last snap {hours}h ago (limit {max_age}h)")
            if not data.get("backup_log_ok", True):
                alerter.warn(f"restic backup log shows no successful backup on {node_name}")
        elif data.get("restic_installed"):
            alerter.warn(f"restic repository unreachable on {node_name}")

    elif pname == "k3s":
        total = int(data.get("total_pods", 0) or 0)
        running = int(data.get("running_pods", 0) or 0)
        if total > 0 and running < total:
            alerter.warn(f"k3s pods degraded: {node_name} has {running}/{total} running")


def _aggregate_garage_status(obs, alerter, config):
    """Combine garage probe data from all nodes that run the probe."""
    seen_nodes: set = set()
    garage_nodes = []
    total_healthy = 0
    thresh = config.get("thresholds", {})

    for node_name, results in obs.probes.items():
        for r in results:
            if not r.reachable:
                continue
            data = r.data
            if data.get("garage_reachable"):
                total_h = int(data.get("healthy_nodes", 0) or 0)
                nodes = data.get("nodes", [])
                if nodes:
                    for n in nodes:
                        nid = n.get("id", "")
                        if nid and nid not in seen_nodes:
                            seen_nodes.add(nid)
                            garage_nodes.append({"probed_from": node_name, **n})
                    alerter.note(
                        f"garage via {node_name}: {total_h} healthy nodes"
                    )
                total_healthy = max(total_healthy, total_h)

    min_nodes = thresh.get("garage_nodes_min", 3)
    if total_healthy < min_nodes:
        alerter.warn(f"garage cluster degraded: {total_healthy}/{min_nodes} healthy nodes")

    obs.garage_status = {
        "healthy_nodes": total_healthy,
        "nodes_seen": garage_nodes,
    }

    # Bucket probe data
    bucket_list = []
    for node_name, results in obs.probes.items():
        for r in results:
            if r.reachable and "buckets" in r.data:
                buckets = r.data.get("buckets", [])
                if buckets:
                    bucket_list = buckets  # take the first non-empty result
                    break
    obs.garage_status["buckets"] = bucket_list


def _aggregate_backup_status(obs, alerter, config):
    """Aggregate restic + cold copy probe data."""
    backup = {"snapshot_count": 0, "latest_age_hours": 0, "backup_log_ok": False,
              "last_cold_copy_hours": 0, "total_size": 0, "file_size": 0}
    thresh = config.get("thresholds", {})

    for node_name, results in obs.probes.items():
        for r in results:
            if not r.reachable:
                continue
            data = r.data
            if data.get("restic_reachable"):
                backup["snapshot_count"] = int(data.get("snapshot_count", 0) or 0)
                backup["latest_age_hours"] = int(data.get("latest_age_hours", 0) or 0)
                backup["backup_log_ok"] = data.get("backup_log_ok", False)
                backup["total_size"] = int(data.get("total_size", 0) or 0)
                backup["file_size"] = int(data.get("file_size", 0) or 0)
            if "hours_since_copy" in data:
                backup["last_cold_copy_hours"] = int(data.get("hours_since_copy", 0) or 0)

    # Only warn about backup state if at least one restic probe responded
    has_restic_data = False
    for node_name, results in obs.probes.items():
        for r in results:
            if r.reachable and r.data.get("restic_reachable") or r.data.get("restic_installed"):
                has_restic_data = True
                break

    if not has_restic_data:
        if any(n for n in obs.optional_unavailable if "qfox-1" in n):
            alerter.note("restic/backup host (qfox-1) is offline — backup status unknown")
        obs.backup_status = backup
        return

    if backup["snapshot_count"] == 0:
        alerter.warn("no restic snapshots found")
    elif backup["latest_age_hours"] > thresh.get("restic_max_age_hours", 28):
        alerter.warn(
            f"restic snapshots are {backup['latest_age_hours']}h old "
            f"(limit {thresh['restic_max_age_hours']}h)"
        )

    backup["cold_copy_stale"] = backup["last_cold_copy_hours"] > 14 * 24  # 14 days
    if backup["cold_copy_stale"]:
        alerter.warn(
            f"cold copy to gdrive is stale: {backup['last_cold_copy_hours']}h since last copy"
        )

    obs.backup_status = backup


# ── DECIDE ─────────────────────────────────────────────────────────────────────

class Decision:
    def __init__(self) -> None:
        self.actions: list[str] = []

    def to_dict(self) -> dict:
        return {"actions": self.actions}


def decide(obs: Observation) -> Decision:
    d = Decision()
    # Decisions are made in the observe phase via the alerter.
    # The controller is primarily an observer + alerter; actions
    # like restarting services require manual intervention via alerts
    # (or future automation scripts on the target nodes).
    #
    # The decision surface tracks whether any actionable alerts were
    # generated — the act phase handles dispatching them.
    has_alerts = bool(obs.critical_down or obs.backup_status.get("snapshot_count", 0) == 0
                      or obs.garage_status.get("healthy_nodes", 0) < 3)
    if has_alerts:
        d.actions.append("dispatch_alerts")
    return d


# ── ACT ────────────────────────────────────────────────────────────────────────

def act(alerter: Alerter, dry_run: bool = False) -> dict[str, Any]:
    if dry_run:
        return {"alerts": alerter.alerts, "warnings": alerter.warnings, "info": alerter.info}
    return alerter.send()


# ── MAIN CYCLE ─────────────────────────────────────────────────────────────────

def run_cycle(
    config: dict,
    tick: int,
    parent_hash: str,
    probe_only: bool = False,
    dry_run: bool = False,
) -> str:
    _log(f"tick={tick} probing {len(config.get('nodes',{}))} nodes...")
    obs, alerter = observe(config)
    dec = decide(obs)
    result = act(alerter, dry_run=dry_run)

    receipt = build_receipt(
        tick=tick,
        parent_hash=parent_hash,
        observation=obs.to_dict(),
        decision=dec.to_dict(),
        action_result=result,
    )

    write_receipt(receipt)

    status = "OK"
    _record_hoxel(obs, status)
    if obs.critical_down:
        status = "DEGRADED"
    elif alerter.alerts:
        status = "ALERTS"

    _log(
        f"tick={tick} done — status={status} "
        f"critical_down={len(obs.critical_down)} "
        f"optional_unavailable={len(obs.optional_unavailable)} "
        f"alerts={len(alerter.alerts)} warnings={len(alerter.warnings)} "
        f"hash={receipt['receipt_hash'][:16]}..."
    )

    return receipt["receipt_hash"]


def main() -> None:
    p = argparse.ArgumentParser(description="infra_controller.py — infrastructure health daemon")
    p.add_argument("--once", action="store_true", default=True, help="Run one cycle")
    p.add_argument("--probe-only", action="store_true", help="Observe only")
    p.add_argument("--dry-run", action="store_true", help="Show what would happen")
    p.add_argument("--loop", type=float, default=0, help="Run every N seconds")
    p.add_argument("--dump", action="store_true", help="Print receipt to stdout")
    args = p.parse_args()

    # Load config
    config = load_config()

    tick, parent_hash = read_chain()
    tick += 1

    interval = args.loop if args.loop > 0 else config.get("schedule", {}).get("node_probes", 300)

    if args.loop:
        _log(f"daemon mode, interval={interval}s, resuming at tick={tick}")
        while True:
            try:
                parent_hash = run_cycle(config, tick, parent_hash,
                                        probe_only=args.probe_only,
                                        dry_run=args.dry_run)
                tick += 1
            except Exception as exc:
                _log(f"cycle error (tick={tick}): {exc}")
                import traceback
                traceback.print_exc(file=sys.stderr)
            time.sleep(interval)
    else:
        parent_hash = run_cycle(config, tick, parent_hash,
                                probe_only=args.probe_only,
                                dry_run=args.dry_run)
        if args.dump:
            import json
            last_tick, last_hash = read_chain()
            log_path = Path.home() / ".cache" / "infra-controller.jsonl"
            if log_path.exists():
                with open(log_path) as fh:
                    lines = fh.readlines()
                    if lines:
                        print(lines[-1].strip())


if __name__ == "__main__":
    main()
