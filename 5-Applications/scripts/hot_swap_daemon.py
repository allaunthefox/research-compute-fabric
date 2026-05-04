#!/usr/bin/env python3
"""
hot_swap_daemon.py — Background daemon for automatic model hot-swapping.

Monitors system resources and Ollama state, performing automatic swaps
based on configurable policies. Integrates with ENE gossip for distributed
state sync across the swarm mesh.

Usage:
    python3 hot_swap_daemon.py [start|stop|status|once]

Config: /home/allaun/Documents/Research Stack/config/hot_swap_policy.json
"""

import sys
import time
import signal
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "4-Infrastructure"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "0-Core-Formalism"))

from scripts.hot_swap_manager import HotSwapManager, ModelTier, SwapEvent


class HotSwapDaemon:
    """Background daemon for automatic hot-swapping."""
    
    CONFIG_PATH = Path("/home/allaun/Documents/Research Stack/config/hot_swap_policy.json")
    PID_PATH = Path("/tmp/hot_swap_daemon.pid")
    LOG_PATH = Path("/home/allaun/Documents/Research Stack/logs/hot_swap_daemon.log")
    
    DEFAULT_POLICY = {
        "check_interval_seconds": 10,
        "memory_threshold_gb": 4.0,
        "vram_threshold_gb": 1.0,
        "auto_swap_down": True,
        "auto_swap_up": False,  # Conservative: don't auto-upgrade
        "preferred_tier_default": "balanced",
        "emergency_tier": "fast",
        "quiet_hours": [],  # Hours when auto-swap is suppressed
        "ene_gossip_sync": True,
    }
    
    def __init__(self):
        self.policy = self._load_policy()
        self.manager = HotSwapManager(
            memory_threshold_gb=self.policy["memory_threshold_gb"],
            vram_threshold_gb=self.policy["vram_threshold_gb"]
        )
        self.running = False
        self.last_check: Optional[datetime] = None
        self._register_callbacks()
        
    def _load_policy(self) -> dict:
        """Load swap policy from config or create defaults."""
        if self.CONFIG_PATH.exists():
            try:
                with open(self.CONFIG_PATH) as f:
                    return {**self.DEFAULT_POLICY, **json.load(f)}
            except Exception as e:
                print(f"[WARN] Could not load policy: {e}, using defaults")
        
        self.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(self.CONFIG_PATH, "w") as f:
            json.dump(self.DEFAULT_POLICY, f, indent=2)
        
        return dict(self.DEFAULT_POLICY)
    
    def _register_callbacks(self):
        """Register callbacks for swap events."""
        self.manager.register_callback(self._log_swap_event)
        if self.policy["ene_gossip_sync"]:
            self.manager.register_callback(self._gossip_swap_event)
    
    def _log_swap_event(self, event: SwapEvent):
        """Log swap events to file."""
        self.LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(self.LOG_PATH, "a") as f:
            ts = datetime.fromtimestamp(event.timestamp).isoformat()
            status = "OK" if event.success else "FAIL"
            f.write(f"[{ts}] SWAP {status}: {event.from_model} → {event.to_model} "
                   f"({event.reason}, {event.duration_ms}ms, "
                   f"{event.memory_before_gb:.1f}→{event.memory_after_gb:.1f}GB)\n")
    
    def _gossip_swap_event(self, event: SwapEvent):
        """Sync swap state to ENE mesh via gossip."""
        try:
            # Write to swarm SRAM via local API
            import requests
            gossip = {
                "t": event.timestamp,
                "src": "hot_swap_daemon",
                "id": f"swap:{event.to_model}:{int(event.timestamp * 1000)}",
                "op": "upsert",
                "data": {
                    "from_model": event.from_model,
                    "to_model": event.to_model,
                    "reason": event.reason,
                    "success": event.success,
                    "duration_ms": event.duration_ms,
                    "memory_delta_gb": event.memory_after_gb - event.memory_before_gb,
                },
                "genome": {"mu": 1, "rho": 1, "c": 1, "m": 1, "ne": 1, "sig": 1},
                "provenance": {"node": "hot_swap_daemon", "source": "auto_swap"},
            }
            requests.post(
                "http://localhost:3001/ingest/jsonl",
                json=[gossip],
                timeout=5
            )
        except Exception:
            pass  # Gossip is best-effort
    
    def _is_quiet_hour(self) -> bool:
        """Check if current hour is in quiet hours."""
        if not self.policy["quiet_hours"]:
            return False
        return datetime.now().hour in self.policy["quiet_hours"]
    
    def _check_and_swap(self):
        """Check resources and swap if needed."""
        if self._is_quiet_hour():
            return
        
        status = self.manager.get_status()
        
        if status["should_swap_down"] and self.policy["auto_swap_down"]:
            candidate = self.manager.get_swap_candidate("down")
            if candidate and candidate != status["current_model"]:
                print(f"[AUTO] Swapping down: {status['current_model']} → {candidate}")
                event = self.manager.perform_swap(candidate, "auto_memory_pressure")
                if event.success:
                    print(f"[AUTO] Swap complete in {event.duration_ms}ms")
                else:
                    print(f"[AUTO] Swap failed!")
        
        elif self.policy["auto_swap_up"] and status["current_model"]:
            current = self.manager.MODEL_REGISTRY.get(status["current_model"])
            if current and current.tier == ModelTier.FAST:
                candidate = self.manager.get_swap_candidate("up")
                if candidate and candidate != status["current_model"]:
                    print(f"[AUTO] Swapping up: {status['current_model']} → {candidate}")
                    event = self.manager.perform_swap(candidate, "auto_resources_available")
    
    def run_once(self):
        """Perform a single check-and-swap cycle."""
        self._check_and_swap()
        self.manager.save_state()
    
    def run(self):
        """Run daemon loop."""
        print("[DAEMON] Hot swap daemon starting...")
        print(f"[DAEMON] Policy: {self.policy}")
        print(f"[DAEMON] Check interval: {self.policy['check_interval_seconds']}s")
        
        self.running = True
        self._write_pid()
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        try:
            while self.running:
                self.last_check = datetime.now()
                self._check_and_swap()
                
                # Save state periodically
                self.manager.save_state()
                
                # Sleep with interruptible wait
                for _ in range(self.policy["check_interval_seconds"]):
                    if not self.running:
                        break
                    time.sleep(1)
                    
        except Exception as e:
            print(f"[DAEMON] Error: {e}")
        finally:
            self._remove_pid()
            print("[DAEMON] Shut down")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\n[DAEMON] Received signal {signum}, shutting down...")
        self.running = False
    
    def _write_pid(self):
        """Write PID file."""
        with open(self.PID_PATH, "w") as f:
            f.write(str(sys.argv[0]) + "\n")
            f.write(str(time.time()) + "\n")
    
    def _remove_pid(self):
        """Remove PID file."""
        if self.PID_PATH.exists():
            self.PID_PATH.unlink()
    
    def status(self) -> dict:
        """Get daemon status."""
        manager_status = self.manager.get_status()
        return {
            "running": self.running,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "policy": self.policy,
            "manager": manager_status,
            "pid_file_exists": self.PID_PATH.exists(),
            "log_lines": sum(1 for _ in open(self.LOG_PATH)) if self.LOG_PATH.exists() else 0,
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Hot Swap Daemon for Ollama Models")
    parser.add_argument("command", choices=["start", "stop", "status", "once", "test"],
                       default="status", nargs="?",
                       help="start=run daemon, stop=shutdown, status=show state, once=single check, test=dry-run")
    args = parser.parse_args()
    
    daemon = HotSwapDaemon()
    
    if args.command == "start":
        daemon.run()
    elif args.command == "once":
        daemon.run_once()
        status = daemon.status()
        print(json.dumps(status, indent=2))
    elif args.command == "test":
        print("[TEST] Hot swap manager status:")
        status = daemon.manager.get_status()
        print(json.dumps(status, indent=2))
        print("\n[TEST] Available models:")
        for name, spec in daemon.manager.MODEL_REGISTRY.items():
            print(f"  {name}: {spec.size_gb:.1f}GB ({spec.tier.value})")
    else:  # status
        status = daemon.status()
        print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
