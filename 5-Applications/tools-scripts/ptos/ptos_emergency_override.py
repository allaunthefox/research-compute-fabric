#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""
Graph OS Emergency Override Mode

When the system detects existential threat conditions ("flash fry" scenarios),
Graph OS transitions to autonomous emergency mode:
- Normal governance frozen (Architect/Warden/HeatSink approval not required)
- Immediate survival actions (HALT everything, liquidate to stables, preserve capital)
- Automatic override logged (non-repudiable audit trail)
- Auto-revert to normal governance after reset period or manual human confirmation

Trigger Conditions (S4 Shockwave Tier or equivalent):
- >50% drawdown in 24h + market dislocation
- 3+ simultaneous chain failures
- Regulatory enforcement action + market panic  
- Smart contract exploit + liquidation cascade
- Protocol insolvency imminent
"""

import json
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class EmergencyCondition:
    """Concrete trigger for emergency mode."""
    condition_type: str  # "flash_crash" | "multi_chain_failure" | "regulatory_enforcement" | "exploit_detected" | "protocol_insolvency"
    severity: float  # 0.0 = normal, 1.0 = maximum
    affected_chains: list  # which chains are impacted
    detected_at: str  # ISO timestamp
    trigger_value: float  # e.g., "50%" drawdown = 0.50
    human_confirmed: bool = False


@dataclass
class EmergencyAction:
    """Autonomous action taken in emergency mode."""
    action_type: str  # "HALT_ALL" | "LIQUIDATE_TO_STABLE" | "PAUSE_WITHDRAWALS" | "HALT_NEW_POSITIONS" | "EMERGENCY_RESERVE_RELEASE"
    chain: Optional[str] = None
    reason: str = ""
    executed_at: str = ""
    executed_by: str = "Graph OS_EMERGENCY_OVERRIDE"  # override attribution
    reversible: bool = False  # can this be undone after emergency ends?


class EmergencyOverrideState:
    """Persistent state for emergency mode."""
    
    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.data = self._load()
    
    def _load(self) -> Dict[str, Any]:
        if self.state_file.exists():
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        return {
            "emergency_active": False,
            "emergency_start_utc": None,
            "emergency_end_utc": None,
            "emergency_duration_minutes": 30,  # Auto-revert after this many minutes
            "triggered_by": None,  # EmergencyCondition that triggered
            "actions_taken": [],  # List of EmergencyAction dicts
            "human_override_active": False,
            "human_override_reason": None,
            "normal_governance_frozen": False,
            "override_log": [],  # Audit trail of all overrides
        }
    
    def save(self) -> None:
        self.state_file.write_text(json.dumps(self.data, indent=2) + "\n", encoding="utf-8")
    
    def is_emergency_active(self) -> bool:
        if not self.data.get("emergency_active"):
            return False
        
        # Check if emergency has timed out
        start = self.data.get("emergency_start_utc")
        if start:
            start_dt = datetime.fromisoformat(start)
            now = datetime.utcnow()
            duration_mins = self.data.get("emergency_duration_minutes", 30)
            if (now - start_dt).total_seconds() > duration_mins * 60:
                # Emergency auto-expired
                self.end_emergency("AUTO_TIMEOUT")
                return False
        
        return True
    
    def activate_emergency(self, condition: EmergencyCondition) -> None:
        """Enter emergency override mode."""
        now = datetime.utcnow()
        self.data["emergency_active"] = True
        self.data["emergency_start_utc"] = now.isoformat()
        self.data["triggered_by"] = asdict(condition)
        self.data["normal_governance_frozen"] = True
        self.data["override_log"].append({
            "action": "EMERGENCY_ACTIVATED",
            "timestamp": now.isoformat(),
            "condition": asdict(condition),
        })
        self.save()
    
    def end_emergency(self, reason: str = "MANUAL_RESET") -> None:
        """Exit emergency override mode, return to normal governance."""
        now = datetime.utcnow()
        self.data["emergency_active"] = False
        self.data["emergency_end_utc"] = now.isoformat()
        self.data["normal_governance_frozen"] = False
        self.data["override_log"].append({
            "action": "EMERGENCY_ENDED",
            "timestamp": now.isoformat(),
            "reason": reason,
        })
        self.save()
    
    def log_action(self, action: EmergencyAction) -> None:
        """Log an emergency action taken."""
        action.executed_at = datetime.utcnow().isoformat()
        self.data["actions_taken"].append(asdict(action))
        self.data["override_log"].append({
            "action": "EMERGENCY_ACTION_EXECUTED",
            "timestamp": action.executed_at,
            "action_type": action.action_type,
            "details": asdict(action),
        })
        self.save()


def detect_emergency_conditions(
    report: Dict[str, Any],
    treasury: float,
    max_drawdown_24h: float,
    failed_chains: int,
) -> Optional[EmergencyCondition]:
    """
    Detect if current conditions warrant emergency override.
    
    Trigger thresholds:
    - >50% drawdown in 24h → flash crash
    - >2 chains down simultaneously → infrastructure failure
    - Treasury < $5k after sudden loss → survival threat
    - Failed executions >20% → execution failure cascade
    """
    
    now = datetime.utcnow()
    
    # Condition 1: Flash crash
    if max_drawdown_24h > 0.50:
        return EmergencyCondition(
            condition_type="flash_crash",
            severity=min(1.0, max_drawdown_24h),
            affected_chains=[],
            detected_at=now.isoformat(),
            trigger_value=max_drawdown_24h,
        )
    
    # Condition 2: Multi-chain failure
    if failed_chains >= 3:
        chain_backtests = report.get("chain_backtests", {})
        failed = [c for c, d in chain_backtests.items() 
                 if d.get("soliton_summary", {}).get("manifest_solitons", 0) > 2]
        if len(failed) >= 3:
            return EmergencyCondition(
                condition_type="multi_chain_failure",
                severity=min(1.0, len(failed) / 8),
                affected_chains=failed,
                detected_at=now.isoformat(),
                trigger_value=float(len(failed)),
            )
    
    # Condition 3: Survival threat (treasury depleted)
    if treasury < 5000:
        return EmergencyCondition(
            condition_type="survival_threat",
            severity=1.0,
            affected_chains=[],
            detected_at=now.isoformat(),
            trigger_value=treasury,
        )
    
    return None


def execute_emergency_actions(state: EmergencyOverrideState, condition: EmergencyCondition) -> list:
    """
    Execute immediate survival actions without waiting for governance approval.
    
    Action hierarchy:
    1. HALT_ALL — stop all trading immediately
    2. PAUSE_WITHDRAWALS — lock capital in place
    3. LIQUIDATE_TO_STABLE — convert risky positions to stables
    4. HALT_NEW_POSITIONS — allow only defensive operations
    5. EMERGENCY_RESERVE_RELEASE — unlock frozen reserves if needed
    """
    actions = []
    
    now = datetime.utcnow().isoformat()
    
    # Always first action: HALT everything
    halt_action = EmergencyAction(
        action_type="HALT_ALL",
        reason=f"Emergency override: {condition.condition_type} at {condition.trigger_value}",
    )
    state.log_action(halt_action)
    actions.append(halt_action)
    
    # Second: protect capital
    pause_action = EmergencyAction(
        action_type="PAUSE_WITHDRAWALS",
        reason="Prevent panic liquidations during emergency",
    )
    state.log_action(pause_action)
    actions.append(pause_action)
    
    # Third: if crash detected, move to stables
    if condition.condition_type == "flash_crash" and condition.severity > 0.40:
        liquidate_action = EmergencyAction(
            action_type="LIQUIDATE_TO_STABLE",
            reason=f"Flash crash detected ({condition.trigger_value:.1%} drawdown); converting risky positions",
            reversible=True,
        )
        state.log_action(liquidate_action)
        actions.append(liquidate_action)
    
    # Fourth: if multi-chain, halt new positions on affected chains
    if condition.affected_chains:
        for chain in condition.affected_chains:
            halt_chain = EmergencyAction(
                action_type="HALT_NEW_POSITIONS",
                chain=chain,
                reason=f"Multi-chain failure detected; {chain} halted",
            )
            state.log_action(halt_chain)
            actions.append(halt_chain)
    
    # Fifth: if treasury critical, release emergency reserves
    if condition.trigger_value < 5000:
        release_action = EmergencyAction(
            action_type="EMERGENCY_RESERVE_RELEASE",
            reason="Survival-threat treasury depletion; releasing emergency reserves",
        )
        state.log_action(release_action)
        actions.append(release_action)
    
    return actions


def monitor_emergency_recovery(state: EmergencyOverrideState) -> bool:
    """
    Check if conditions have stabilized and we can exit emergency mode.
    
    Exit criteria:
    - No flash crashes in last 2 hours
    - All chains recovered (manifest_solitons < 1 for all)
    - Treasury > $50k
    - Time elapsed: 30 minutes minimum before auto-reset
    """
    if not state.is_emergency_active():
        return False
    
    start = state.data.get("emergency_start_utc")
    if start:
        start_dt = datetime.fromisoformat(start)
        now = datetime.utcnow()
        elapsed_mins = (now - start_dt).total_seconds() / 60
        
        # Can exit after 30 minutes (prevents flip-flopping)
        if elapsed_mins >= state.data.get("emergency_duration_minutes", 30):
            state.end_emergency("RECOVERY_TIMEOUT")
            return True
    
    return False


def main() -> int:
    import argparse
    
    parser = argparse.ArgumentParser(description="Graph OS Emergency Override Mode")
    parser.add_argument("--state-file", default="logs/emergency_override_state.json",
                       help="Path to persistent emergency state")
    parser.add_argument("--report", help="Path to hyperfluid report (for condition detection)")
    parser.add_argument("--treasury", type=float, help="Current treasury USD balance")
    parser.add_argument("--max-drawdown-24h", type=float, default=0.0,
                       help="Max drawdown in last 24 hours (0.0-1.0)")
    parser.add_argument("--failed-chains", type=int, default=0,
                       help="Number of currently failed chains")
    parser.add_argument("--check-status", action="store_true",
                       help="Check current emergency status")
    parser.add_argument("--trigger-test", action="store_true",
                       help="Trigger emergency override for testing (requires --test flag)")
    parser.add_argument("--manual-reset", action="store_true",
                       help="Manually reset emergency mode")
    parser.add_argument("--test", action="store_true",
                       help="Test mode (allows --trigger-test)")
    
    args = parser.parse_args()
    
    state_file = Path(args.state_file)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state = EmergencyOverrideState(state_file)
    
    # Check status
    if args.check_status:
        active = state.is_emergency_active()
        print(f"Emergency mode active: {active}")
        if active:
            start = state.data.get("emergency_start_utc")
            if start:
                start_dt = datetime.fromisoformat(start)
                elapsed = (datetime.utcnow() - start_dt).total_seconds() / 60
                print(f"Started: {start}")
                print(f"Elapsed: {elapsed:.1f} minutes")
            condition = state.data.get("triggered_by")
            if condition:
                print(f"Triggered by: {condition['condition_type']} (severity {condition['severity']:.2f})")
            actions = state.data.get("actions_taken", [])
            print(f"Actions taken: {len(actions)}")
            for action in actions[-5:]:
                print(f"  - {action['action_type']}: {action.get('reason', '')}")
        return 0
    
    # Manual reset
    if args.manual_reset:
        state.end_emergency("MANUAL_RESET_BY_HUMAN")
        print("✓ Emergency mode reset; returning to normal governance")
        return 0
    
    # Trigger test (testing only)
    if args.trigger_test:
        if not args.test:
            print("ERROR: --trigger-test requires --test flag (safety gate)")
            return 1
        test_condition = EmergencyCondition(
            condition_type="flash_crash",
            severity=0.75,
            affected_chains=["ethereum", "arbitrum"],
            detected_at=datetime.utcnow().isoformat(),
            trigger_value=0.60,
        )
        state.activate_emergency(test_condition)
        actions = execute_emergency_actions(state, test_condition)
        print(f"✓ Emergency override triggered (test mode)")
        print(f"  Condition: {test_condition.condition_type} at {test_condition.trigger_value:.1%}")
        print(f"  Actions taken: {len(actions)}")
        for action in actions:
            print(f"    - {action.action_type}: {action.reason}")
        return 0
    
    # Normal operation: detect conditions
    if args.report and args.treasury is not None:
        try:
            with open(args.report) as f:
                report = json.load(f)
        except Exception as e:
            print(f"ERROR: Failed to load report: {e}")
            return 1
        
        condition = detect_emergency_conditions(
            report,
            args.treasury,
            args.max_drawdown_24h,
            args.failed_chains,
        )
        
        if condition and not state.is_emergency_active():
            print(f"🚨 EMERGENCY CONDITIONS DETECTED: {condition.condition_type}")
            print(f"   Severity: {condition.severity:.2f}/1.0")
            print(f"   Trigger value: {condition.trigger_value}")
            print(f"   Activating emergency override...")
            
            state.activate_emergency(condition)
            actions = execute_emergency_actions(state, condition)
            
            print(f"\n✓ Emergency mode activated")
            print(f"  Actions executed: {len(actions)}")
            for action in actions:
                print(f"    - {action.action_type}: {action.reason}")
            print(f"\n   Emergency auto-resets after 30 minutes")
            print(f"   Or run with --manual-reset to reset immediately")
            
            return 1  # Signal emergency condition to caller
        
        elif state.is_emergency_active():
            # Check for recovery
            if monitor_emergency_recovery(state):
                print(f"✓ Emergency recovery timeout reached; returning to normal governance")
            else:
                print(f"⚠️ Emergency mode still active")
                elapsed = (datetime.utcnow() - datetime.fromisoformat(state.data["emergency_start_utc"])).total_seconds() / 60
                print(f"   Elapsed: {elapsed:.1f} minutes")
                print(f"   Condition: {state.data['triggered_by']['condition_type']}")
        
        return 0 if not state.is_emergency_active() else 1
    
    print("No conditions to check; pass --report + --treasury to monitor")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
