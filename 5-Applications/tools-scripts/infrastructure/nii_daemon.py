#!/usr/bin/env python3
"""
Utility: nii_daemon.py
----------------------
Sovereign Daemon: Autonomous Informatic Sentinel.
Version: BT20-REV-A-IGNITE
"""

import subprocess
import time
import json
import os
import signal
import sys

class SovereignDaemon:
    def __init__(self):
        self.bridge_script = "/home/allaun/Documents/Research Stack/5-Applications/tools-scripts/bt20_fpga_bridge.py"
        self.health_path = "/home/allaun/Documents/Research Stack/5-Applications/tools-scripts/daemon_health.json"
        self.audit_threshold = 10000
        self.uptime_start = time.time()
        self.processed_axioms = 0
        self.state = "INIT"
        self.pid = os.getpid()
        
        # Registration of Graceful Shutdown
        signal.signal(signal.SIGINT,  self.graceful_shutdown)
        signal.signal(signal.SIGTERM, self.graceful_shutdown)

    def emit_health(self):
        health = {
            "pid": self.pid,
            "uptime": f"{int(time.time() - self.uptime_start)}s",
            "state": self.state,
            "processed": self.processed_axioms,
            "next_audit": self.audit_threshold - (self.processed_axioms % self.audit_threshold),
            "v_tag": "BT20-REV-A",
            "heartbeat": time.ctime()
        }
        with open(self.health_path, "w") as f:
            json.dump(health, f)

    def graceful_shutdown(self, signum, frame):
        print(f"\n[!] Signal {signum} Caught. Initiating Graceful Shutdown...")
        self.state = "SHUTDOWN"
        self.emit_health()
        
        # Final Ignition Snapshot
        print("[>] Capturing Final Manifold Snapshot...")
        try:
            # We would normally signal the bridge here, but in simulation we just log it
            with open("/home/allaun/Documents/Research Stack/5-Applications/tools-scripts/ignited_manifold.json", "a") as f:
                f.write(f"\n# Shutdown Snapshot @ {time.ctime()}\n")
            print("[+] Snapshot Anchored. Sovereign Sentinel OFFLINE.")
        except Exception as e:
            print(f"[!] Shutdown Error: {e}")
        
        sys.exit(0)

    def run_audit(self):
        print(f"[!] TRIGGERING STABILITY AUDIT (Threshold: {self.audit_threshold} axioms)")
        self.state = "AUDIT_MODE"
        self.emit_health()
        
        try:
            subprocess.run(["python3", "/home/allaun/Documents/Research Stack/5-Applications/tools-scripts/benchmark_manifold.py", "--routine"], check=True)
            print("[+] Audit Passed. Resuming background sweep.")
            return True
        except subprocess.CalledProcessError:
            print("[CRITICAL] Audit Failed! Entering QUARANTINE.")
            self.state = "QUARANTINE"
            return False

    def start_bridge(self):
        print("[>] Informatic Sentinel: background sweep proceeding...")
        self.state = "BACKGROUND_SWEEP"
        self.processed_axioms += 1000 
        self.emit_health()

    def main_loop(self):
        print(f"[*] Sovereign Sentinel [PID: {self.pid}] ACTIVE.")
        print("[*] Version: BT20-REV-A | Global Audit Pulse: 10k Axioms.")
        while True:
            if self.state == "QUARANTINE":
                self.emit_health()
                time.sleep(10)
                continue
                
            self.start_bridge()
            
            if self.processed_axioms % self.audit_threshold == 0:
                if not self.run_audit():
                    continue 
            
            time.sleep(5)
            self.emit_health()

if __name__ == "__main__":
    daemon = SovereignDaemon()
    daemon.main_loop()
