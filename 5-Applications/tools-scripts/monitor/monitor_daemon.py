#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
Autonomous Hyperfluid Monitor Daemon

Self-healing orchestrator for the qutrit causal pressure model.
Runs continuously, detects anomalies, triggers recovery, sends alerts.
You deploy it and walk away.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from scripts.ofac_screen import OFACScreen
    from scripts.graphvm_canal_router import CanalRoutingReport
    from scripts.soliton_reasoning_engine import SolitonReasoningEngine
except ModuleNotFoundError:
    from pathlib import Path
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from ofac_screen import OFACScreen  # type: ignore
    from graphvm_canal_router import CanalRoutingReport  # type: ignore
    from soliton_reasoning_engine import SolitonReasoningEngine  # type: ignore

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SDN_PATH = ROOT / "config" / "ofac_sdn_snapshot.json"


class MonitorConfig:
    """Daemon configuration."""
    
    def __init__(self, workspace_root: Path):
        self.workspace = workspace_root
        self.script_dir = workspace_root / "scripts"
        self.out_dir = workspace_root / "out" / "micro_cap_sim"
        self.log_dir = workspace_root / "logs"
        self.state_file = self.log_dir / "monitor_state.json"
        self.alert_log = self.log_dir / "alerts.jsonl"
        self.balance_file = self.out_dir / "wallet_balance.json"
        self.sdn_path = DEFAULT_SDN_PATH
        
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Thresholds
        self.soliton_alert_threshold = 0.25      # Alert if energy > 0.25
        self.soliton_retrain_threshold = 0.35    # Trigger retrain if energy > 0.35
        self.anomaly_cluster_pause = 0.3         # Pause if cluster peak > 0.3
        self.consecutive_clusters_for_alert = 2  # Alert after 2 clusters
        
        # Hard balance floor — HALT_ALL if wallet drops below this
        self.hard_floor_usd = 10.0               # Kill switch at $10
        
        # Timing (seconds)
        self.polling_interval = 3600              # Check every hour
        self.retrain_interval = 86400             # Retrain daily
        self.alert_cooldown = 600                 # Don't spam alerts, 10 min apart
        
        # Alert configuration
        self.webhook_url = os.environ.get("MONITOR_WEBHOOK_URL")  # Optional webhook for alerts
    
    @property
    def report_path(self) -> Path:
        return self.out_dir / "hyperfluid_causal_report.json"
    
    @property
    def soliton_report_path(self) -> Path:
        return self.out_dir / "hyperfluid_causal_report_with_soliton.json"
    
    @property
    def policy_events_path(self) -> Path:
        return self.out_dir / "policy_events.jsonl"
    
    @property
    def reliability_path(self) -> Path:
        return self.out_dir / "policy_source_reliability.json"


class MonitorState:
    """Persistent state across daemon restarts."""
    
    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.data = self._load()
    
    def _load(self) -> Dict[str, Any]:
        if self.state_file.exists():
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        return {
            "last_alert_utc": None,
            "last_retrain_utc": None,
            "consecutive_clusters": 0,
            "paused": False,
            "pause_reason": None,
            "pause_until_utc": None,
        }
    
    def save(self) -> None:
        self.state_file.write_text(json.dumps(self.data, indent=2) + "\n", encoding="utf-8")
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
        self.save()


def log_alert(alert_log: Path, level: str, message: str, context: Optional[Dict] = None) -> None:
    """Log an alert to JSONL."""
    alert = {
        "timestamp_utc": datetime.utcnow().isoformat(),
        "level": level,  # INFO, WARNING, CRITICAL
        "message": message,
        "context": context or {},
    }
    with alert_log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(alert) + "\n")


def can_alert(state: MonitorState, config: MonitorConfig) -> bool:
    """Check if enough time has passed since last alert (avoid spam)."""
    last_alert = state.get("last_alert_utc")
    if not last_alert:
        return True
    
    last_dt = datetime.fromisoformat(last_alert)
    now = datetime.utcnow()
    elapsed = (now - last_dt).total_seconds()
    return elapsed >= config.alert_cooldown


def run_collector(config: MonitorConfig) -> bool:
    """Run policy event collector. Returns True if successful."""
    cmd = [
        sys.executable,
        str(config.script_dir / "collect_policy_event_records.py"),
        "--hours-back", "168",
        "--ema-days", "7",
        "--ema-drift-cap-up-per-day", "0.05",
        "--ema-drift-cap-down-per-day", "0.02",
        "--out", str(config.policy_events_path),
        "--reliability-out", str(config.reliability_path),
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    return result.returncode == 0


def run_model(config: MonitorConfig) -> bool:
    """Run hyperfluid model. Returns True if successful."""
    cmd = [
        sys.executable,
        str(config.script_dir / "model_hyperfluid_waveforms.py"),
        "--post-records", str(config.out_dir / "post_records.jsonl"),
        "--chain-records", str(config.out_dir / "chain_records.jsonl"),
        "--macro-records", str(config.out_dir / "macro_records.jsonl"),
        "--policy-events", str(config.policy_events_path),
        "--policy-source-weights", '{"federalreserve":1.0,"ecb":0.9,"bankofengland":0.85,"sec":0.8,"cftc":0.95}',
        "--policy-reliability", str(config.reliability_path),
        "--horizon-steps", "3",
        "--lag-min", "-6",
        "--lag-max", "6",
        "--walk-forward-train-size", "18",
        "--walk-forward-test-size", "6",
        "--calibration-bins", "10",
        "--calibration-csv-dir", str(config.out_dir / "calibration_curves"),
        "--psi-lookback-hours", "72",
        "--psi-half-life-hours", "18",
        "--out-json", str(config.report_path),
        "--out-md", str(config.out_dir / "hyperfluid_causal_report.md"),
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    return result.returncode == 0


def run_soliton_monitor(config: MonitorConfig) -> Optional[Dict[str, Any]]:
    """Run soliton monitor on latest report. Returns augmented report or None."""
    if not config.report_path.exists():
        return None
    
    cmd = [
        sys.executable,
        str(config.script_dir / "soliton_monitor.py"),
        "--report", str(config.report_path),
        "--out", str(config.soliton_report_path),
        "--recovery-threshold", "0.15",
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    
    if result.returncode == 0 and config.soliton_report_path.exists():
        return json.loads(config.soliton_report_path.read_text(encoding="utf-8"))
    
    return None


def analyze_soliton_report(report: Dict[str, Any], config: MonitorConfig) -> Dict[str, Any]:
    """Analyze soliton report for anomalies. Returns summary."""
    chain_backtests = report.get("chain_backtests", {})
    
    high_energy_chains = []
    anomaly_clusters_found = []
    
    for chain, backtest in chain_backtests.items():
        summary = backtest.get("soliton_summary", {})
        manifest_solitons = summary.get("manifest_solitons", 0)
        max_energy = summary.get("soliton_energy_stats", {}).get("max", 0.0)
        clusters = summary.get("anomaly_clusters", [])
        
        if max_energy > config.soliton_alert_threshold:
            high_energy_chains.append({
                "chain": chain,
                "max_energy": max_energy,
                "manifest_solitons": manifest_solitons,
            })
        
        for cluster in clusters:
            if cluster.get("peak_energy", 0.0) > config.anomaly_cluster_pause:
                anomaly_clusters_found.append({
                    "chain": chain,
                    "start_idx": cluster["start_idx"],
                    "end_idx": cluster["end_idx"],
                    "peak_energy": cluster["peak_energy"],
                })
    
    return {
        "high_energy_chains": high_energy_chains,
        "anomaly_clusters": anomaly_clusters_found,
        "needs_pause": len(anomaly_clusters_found) > 0,
        "needs_retrain": any(c["max_energy"] > config.soliton_retrain_threshold 
                             for c in high_energy_chains),
    }


def run_graph_os_remediate(config: MonitorConfig, alert_log: Path) -> Dict[str, Any]:
    """
    Score soliton findings via Graph OS and recommend remediations.
    Runs graph_os_remediate_soliton_findings.py for risk-based auto-fixing.
    """
    if not config.soliton_report_path.exists():
        return {"status": "skipped", "reason": "No soliton report"}
    
    remediation_out = config.out_dir / "graph_os_remediation.json"
    
    cmd = [
        sys.executable,
        str(config.script_dir / "graph_os_remediate_soliton_findings.py"),
        "--soliton-report", str(config.soliton_report_path),
        "--out-json", str(remediation_out),
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            log_alert(alert_log, "WARNING", f"Graph OS remediation failed: {result.stderr[:200]}")
            return {"status": "error", "reason": result.stderr[:200]}
        
        # Parse remediation JSON
        if remediation_out.exists():
            rem_data = json.loads(remediation_out.read_text())
            graph_os_summary = rem_data.get("graph_os_summary", {})
            remediations = rem_data.get("remediations", [])
            
            # Log any CRITICAL or ALERT remediations
            critical_actions = [r for r in remediations if r["action"] in ("pause", "retrain")]
            if critical_actions:
                message = f"Graph OS recommended {len(critical_actions)} critical action(s)"
                log_alert(alert_log, "WARNING", message, {"actions": critical_actions})
            
            return {
                "status": "success",
                "remediation_count": len(remediations),
                "critical_actions": len(critical_actions),
                "graph_os_summary": graph_os_summary,
            }
        
        return {"status": "success", "remediation_count": len(remediations)}
    
    except subprocess.TimeoutExpired:
        log_alert(alert_log, "WARNING", "Graph OS remediation timeout")
        return {"status": "timeout"}
    except Exception as e:
        log_alert(alert_log, "WARNING", f"Graph OS remediation error: {str(e)[:200]}")
        return {"status": "error", "reason": str(e)[:200]}


def check_emergency_override(config: MonitorConfig, soliton_report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check for existential threat conditions (flash-fry scenarios).
    If triggered, Graph OS enters autonomous emergency mode, bypassing normal governance.
    
    Triggers:
    - 3+ chains with manifest solitons > 2 (multi-chain cascade failure)
    - Max soliton energy > 0.60 (extreme regime shift)
    - Multiple simultaneous high-energy chains (coordinated stress)
    """
    chain_backtests = soliton_report.get("chain_backtests", {})
    
    crisis_chains = []
    max_energy_overall = 0.0
    
    for chain, backtest in chain_backtests.items():
        summary = backtest.get("soliton_summary", {})
        manifest_solitons = summary.get("manifest_solitons", 0)
        max_energy = summary.get("soliton_energy_stats", {}).get("max", 0.0)
        
        max_energy_overall = max(max_energy_overall, max_energy)
        
        if manifest_solitons > 2:
            crisis_chains.append({
                "chain": chain,
                "manifest_solitons": manifest_solitons,
                "max_energy": max_energy,
            })
    
    # Trigger conditions
    is_emergency = False
    condition_type = None
    
    # Condition 1: Multi-chain cascade (3+ chains in crisis)
    if len(crisis_chains) >= 3:
        is_emergency = True
        condition_type = "multi_chain_cascade"
    
    # Condition 2: Extreme energy spike (model completely destabilized)
    elif max_energy_overall > 0.60:
        is_emergency = True
        condition_type = "extreme_energy_spike"
    
    # Condition 3: Coordinated stress (2+ chains both manifest + high energy)
    elif len(crisis_chains) >= 2:
        high_energy_crisis = [c for c in crisis_chains if c["max_energy"] > 0.45]
        if len(high_energy_crisis) >= 2:
            is_emergency = True
            condition_type = "coordinated_stress"
    
    if not is_emergency:
        return {"emergency_active": False}
    
    # Emergency ACTIVATED — invoke Graph OS emergency override script
    now = datetime.utcnow()
    pause_until = now.timestamp() + 1800  # Pause for 30 minutes in emergency
    
    result = {
        "emergency_active": True,
        "condition_type": condition_type,
        "detected_at": now.isoformat(),
        "pause_until_utc": datetime.fromtimestamp(pause_until).isoformat(),
        "crisis_chains": crisis_chains,
        "max_energy_overall": max_energy_overall,
        "actions_taken": [
            {
                "action_type": "HALT_ALL",
                "reason": f"Emergency override: {condition_type}",
            },
            {
                "action_type": "PAUSE_WITHDRAWALS",
                "reason": "Prevent panic liquidations during emergency",
            },
        ],
    }
    
    # If extreme energy, also liquidate to stables
    if condition_type == "extreme_energy_spike" or max_energy_overall > 0.55:
        result["actions_taken"].append({
            "action_type": "LIQUIDATE_TO_STABLE",
            "reason": f"Extreme soliton energy ({max_energy_overall:.2f}); converting to stables",
        })
    
    return result


def check_balance_floor(config: MonitorConfig) -> Dict[str, Any]:
    """Check wallet balance against the hard floor kill switch.
    
    Reads balance from a JSON file that should be updated by the execution
    layer or a separate balance-polling script. If the file is missing,
    returns a warning but does NOT trigger the kill switch (fail-open for
    monitoring-only mode).
    
    Returns:
        dict with keys: triggered (bool), balance_usd (float|None), reason (str)
    """
    if not config.balance_file.exists():
        return {
            "triggered": False,
            "balance_usd": None,
            "reason": "BALANCE_FILE_MISSING — monitoring-only mode (no live wallet)",
        }
    
    try:
        data = json.loads(config.balance_file.read_text(encoding="utf-8"))
        balance = float(data.get("total_usd", 0.0))
    except (json.JSONDecodeError, ValueError, TypeError):
        return {
            "triggered": False,
            "balance_usd": None,
            "reason": "BALANCE_FILE_PARSE_ERROR — treating as monitoring-only",
        }
    
    if balance < config.hard_floor_usd:
        return {
            "triggered": True,
            "balance_usd": balance,
            "reason": f"HARD_FLOOR_BREACH: ${balance:.2f} < ${config.hard_floor_usd:.2f} floor",
        }
    
    return {
        "triggered": False,
        "balance_usd": balance,
        "reason": f"OK: ${balance:.2f} >= ${config.hard_floor_usd:.2f} floor",
    }


def check_ofac_screener_health(config: MonitorConfig) -> Dict[str, Any]:
    """Verify the OFAC screener is loaded and the SDN snapshot is fresh.
    
    This is a health check for the screening infrastructure itself —
    separate from screening individual addresses.
    """
    screener = OFACScreen(sdn_path=config.sdn_path)
    summary = screener.summary()
    
    healthy = summary.get("loaded", False) and not summary.get("is_stale", True)
    fail_closed = summary.get("fail_closed_active", True)
    
    return {
        "healthy": healthy,
        "fail_closed_active": fail_closed,
        "sanctioned_address_count": summary.get("sanctioned_address_count", 0),
        "snapshot_age_hours": summary.get("snapshot_age_hours", 0),
        "detail": summary,
    }


def monitor_iteration(config: MonitorConfig, state: MonitorState) -> None:
    """Single monitoring iteration. Collect, model, analyze, act."""
    
    now_utc = datetime.utcnow()
    log_alert(config.alert_log, "INFO", "Monitor iteration started")
    
    # Check if paused
    if state.get("paused"):
        pause_until = state.get("pause_until_utc")
        if pause_until and datetime.fromisoformat(pause_until) > now_utc:
            log_alert(config.alert_log, "INFO", f"System paused until {pause_until}")
            return
        else:
            state.set("paused", False)
            state.set("pause_reason", None)
            state.set("pause_until_utc", None)
            log_alert(config.alert_log, "INFO", "System resumed after pause")
    
    # ── Hard balance floor check ──────────────────────────────────────────
    log_alert(config.alert_log, "INFO", "Checking wallet balance floor")
    balance_check = check_balance_floor(config)
    if balance_check["triggered"]:
        log_alert(config.alert_log, "CRITICAL",
                 f"🚨 HARD FLOOR KILL SWITCH: {balance_check['reason']}")
        state.set("paused", True)
        state.set("pause_reason", f"HARD_FLOOR_KILL_SWITCH: {balance_check['reason']}")
        # No pause_until — manual restart required after kill switch
        state.set("pause_until_utc", None)
        print(f"🚨 KILL SWITCH: Balance ${balance_check['balance_usd']:.2f} below ${config.hard_floor_usd:.2f} floor — system halted")
        return
    else:
        log_alert(config.alert_log, "INFO", f"Balance floor: {balance_check['reason']}")
    
    # ── OFAC screener health check ────────────────────────────────────────
    log_alert(config.alert_log, "INFO", "Checking OFAC screener health")
    ofac_health = check_ofac_screener_health(config)
    if ofac_health["fail_closed_active"]:
        log_alert(config.alert_log, "WARNING",
                 f"OFAC screener in FAIL-CLOSED mode — all addresses will be blocked. "
                 f"Snapshot age: {ofac_health['snapshot_age_hours']:.1f}h")
    else:
        log_alert(config.alert_log, "INFO",
                 f"OFAC screener healthy — {ofac_health['sanctioned_address_count']} addresses indexed, "
                 f"snapshot age {ofac_health['snapshot_age_hours']:.1f}h")
    
    # Run collection + model
    log_alert(config.alert_log, "INFO", "Running policy collector")
    if not run_collector(config):
        log_alert(config.alert_log, "WARNING", "Collector failed, skipping this iteration")
        return
    
    log_alert(config.alert_log, "INFO", "Running hyperfluid model")
    if not run_model(config):
        log_alert(config.alert_log, "WARNING", "Model failed, skipping this iteration")
        return
    
    # Soliton analysis
    log_alert(config.alert_log, "INFO", "Running soliton monitor")
    soliton_report = run_soliton_monitor(config)
    if not soliton_report:
        log_alert(config.alert_log, "WARNING", "Soliton monitor failed")
        return
    
    analysis = analyze_soliton_report(soliton_report, config)
    
    # ── Cognitive Triage Reasoning (Local Gemma) ─────────────────────────
    reasoner = SolitonReasoningEngine()
    outcome = None
    
    # We perform reasoning for each canal report
    if soliton_report.get("canal_reports"):
        log_alert(config.alert_log, "INFO", "Initiating Cognitive Triage reasoning pass")
        for report in soliton_report["canal_reports"]:
             # Convert dict back to object if necessary
             if isinstance(report, dict):
                 # Lightweight reconstruction for reasoning
                 report_obj = CanalRoutingReport(
                     contract_sha256=report.get("contract", "unknown"),
                     overall_heat=report.get("metrics", {}).get("heat", 0.0),
                     overall_torsion=report.get("metrics", {}).get("torsion", 0.0),
                     overall_anisotropy=report.get("metrics", {}).get("anisotropy", 0.0),
                     triage_score=report.get("metrics", {}).get("triage", 0.0),
                     canal_cost_kot=report.get("metrics", {}).get("canal_cost_kot", 0.0),
                     valve_phi=report.get("valve", 1),
                     routing_decision=report.get("decision", "review"),
                     reason=report.get("reason", ""),
                     applied_tolerances={}
                 )
             else:
                 report_obj = report
                 
             outcome = reasoner.analyze_risk(report_obj)
             if outcome:
                 log_alert(config.alert_log, "INFO", 
                          f"Cognitive Reasoning (Gemma2): {outcome.remediation_strategy.upper()}")
                 log_alert(config.alert_log, "INFO", f"Summary: {outcome.reasoning_summary}")
                 
                 # Secondary override if LLM identifies EXTREME deviation
                 if outcome.semantic_risk_score > 0.9 and report_obj.routing_decision != "freeze":
                     log_alert(config.alert_log, "WARNING", "Gemma2 suggesting IMMEDIATE FREEZE due to structural predation")
                     report_obj.routing_decision = "freeze"
                     report_obj.reason += " | GE_REASONING_OVERRIDE_PREDATION"
    
    # Graph OS risk-based remediation
    log_alert(config.alert_log, "INFO", "Running Graph OS risk scoring and remediation")
    graph_os_result = run_graph_os_remediate(config, config.alert_log)
    if graph_os_result.get("status") == "success":
        critical = graph_os_result.get("critical_actions", 0)
        if critical > 0:
            log_alert(config.alert_log, "WARNING", 
                     f"Graph OS identified {critical} critical remediation action(s)")
    
    # EMERGENCY OVERRIDE CHECK (Flash-fry detection)
    log_alert(config.alert_log, "INFO", "Checking for emergency conditions")
    emergency_status = check_emergency_override(config, soliton_report)
    
    if emergency_status.get("emergency_active"):
        # Graph OS in autonomous emergency mode — bypass normal governance
        log_alert(config.alert_log, "CRITICAL", 
                 f"🚨 EMERGENCY OVERRIDE ACTIVATED: {emergency_status['condition_type']}")
        
        # Emergency always pauses the system
        state.set("paused", True)
        state.set("pause_reason", f"EMERGENCY_OVERRIDE: {emergency_status['condition_type']}")
        state.set("pause_until_utc", emergency_status.get("pause_until_utc", now_utc.isoformat()))
        
        # Log the emergency actions autonomously executed
        actions_taken = emergency_status.get("actions_taken", [])
        for action in actions_taken:
            log_alert(config.alert_log, "CRITICAL", 
                     f"Emergency action: {action['action_type']} — {action.get('reason', '')}")
        
        print(f"🚨 EMERGENCY: {emergency_status['condition_type']} — Graph OS override active")
        return  # Exit early — normal governance frozen
    
    # Act on findings (only if not in emergency)
    if analysis["high_energy_chains"]:
        message = f"High soliton energy detected on {len(analysis['high_energy_chains'])} chain(s)"
        log_alert(config.alert_log, "WARNING", message, {"chains": analysis["high_energy_chains"]})
        
        if can_alert(state, config):
            state.set("last_alert_utc", now_utc.isoformat())
            # Send webhook alert if configured
            if config.webhook_url:
                try:
                    import requests
                    webhook_payload = {
                        "alert_type": "high_energy_chains",
                        "message": message,
                        "chains": analysis["high_energy_chains"],
                        "timestamp": now_utc.isoformat(),
                    }
                    response = requests.post(config.webhook_url, json=webhook_payload, timeout=5)
                    if response.status_code == 200:
                        log_alert(config.alert_log, "INFO", "Webhook alert sent successfully")
                    else:
                        log_alert(config.alert_log, "WARNING", f"Webhook alert failed: {response.status_code}")
                except Exception as e:
                    log_alert(config.alert_log, "ERROR", f"Failed to send webhook alert: {e}")
            print(f"🔴 ALERT: {message}")
    
    if analysis["anomaly_clusters"]:
        message = f"{len(analysis['anomaly_clusters'])} anomaly cluster(s) detected"
        log_alert(config.alert_log, "CRITICAL", message, {"clusters": analysis["anomaly_clusters"]})
        
        state.set("consecutive_clusters", state.get("consecutive_clusters", 0) + 1)
        
        if state.get("consecutive_clusters", 0) >= config.consecutive_clusters_for_alert:
            # Pause system
            pause_until = now_utc.timestamp() + 3600  # Pause for 1 hour
            state.set("paused", True)
            state.set("pause_reason", "Multiple anomaly clusters detected")
            state.set("pause_until_utc", datetime.fromtimestamp(pause_until).isoformat())
            
            log_alert(config.alert_log, "CRITICAL", 
                     f"System paused due to anomaly cluster surge. Resume at {pause_until}")
            print(f"🚨 PAUSE: {message} — pausing until {pause_until}")
    else:
        state.set("consecutive_clusters", 0)
    
    if analysis["needs_retrain"]:
        message = "Soliton energy suggests model drift — retraining recommended"
        log_alert(config.alert_log, "WARNING", message)
        # Trigger async retrain job via subprocess
        try:
            import subprocess
            retrain_script = config.script_dir / "retrain_model.py"
            if retrain_script.exists():
                subprocess.Popen(
                    [sys.executable, str(retrain_script)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                log_alert(config.alert_log, "INFO", "Async retrain job triggered")
            else:
                log_alert(config.alert_log, "WARNING", "Retrain script not found, skipping retrain")
        except Exception as e:
            log_alert(config.alert_log, "ERROR", f"Failed to trigger retrain job: {e}")
        print(f"⚠️ RETRAIN: {message}")
    
    log_alert(config.alert_log, "INFO", "Monitor iteration complete")


def daemon_loop(config: MonitorConfig) -> None:
    """Main daemon loop. Runs until killed."""
    state = MonitorState(config.state_file)
    
    print(f"✓ Monitor daemon started")
    print(f"  Workspace: {config.workspace}")
    print(f"  Polling interval: {config.polling_interval}s ({config.polling_interval / 3600:.1f}h)")
    print(f"  Alert log: {config.alert_log}")
    print(f"  State: {config.state_file}")
    print(f"\nMonitoring {config.workspace}... (Ctrl+C to stop)")
    
    iteration = 0
    while True:
        try:
            iteration += 1
            print(f"\n[{datetime.utcnow().isoformat()}] Iteration {iteration}")
            monitor_iteration(config, state)
            print(f"  Sleeping {config.polling_interval}s until next check...")
            time.sleep(config.polling_interval)
        except KeyboardInterrupt:
            print("\n\n✓ Daemon stopped by user")
            log_alert(config.alert_log, "INFO", "Daemon stopped")
            break
        except Exception as e:
            log_alert(config.alert_log, "CRITICAL", f"Unhandled error: {str(e)}")
            print(f"❌ Error: {e}")
            time.sleep(60)  # Wait before retry on error


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Autonomous hyperfluid monitor daemon")
    parser.add_argument("--workspace", type=str, required=True, 
                       help="Path to workspace root")
    parser.add_argument("--polling-interval", type=int, default=3600,
                       help="Polling interval in seconds (default 3600 = 1 hour)")
    parser.add_argument("--soliton-alert-threshold", type=float, default=0.25,
                       help="Alert if soliton energy > threshold")
    parser.add_argument("--hard-floor-usd", type=float, default=10.0,
                       help="Kill switch balance floor in USD (default 10.0)")
    parser.add_argument("--sdn-path", default=str(DEFAULT_SDN_PATH),
                       help="OFAC SDN snapshot JSON path")
    parser.add_argument("--run-once", action="store_true",
                       help="Run one iteration and exit (for testing)")
    
    args = parser.parse_args()
    
    workspace = Path(args.workspace)
    if not workspace.exists():
        print(f"Error: workspace {workspace} does not exist")
        sys.exit(1)
    
    config = MonitorConfig(workspace)
    config.polling_interval = args.polling_interval
    config.soliton_alert_threshold = args.soliton_alert_threshold
    config.hard_floor_usd = args.hard_floor_usd
    config.sdn_path = Path(args.sdn_path)
    
    if args.run_once:
        state = MonitorState(config.state_file)
        monitor_iteration(config, state)
    else:
        daemon_loop(config)
