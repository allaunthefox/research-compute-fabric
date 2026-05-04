#!/usr/bin/env python3
"""
Sovereign Daemon - Continuous Background Monitoring
--------------------------------------------------
This daemon drives the Sovereign Pipeline by polling physical hardware 
disturbances from the BitFlipHarvester and injecting them into the 
Warden manifold. It relies on Sovereign Persistence (Phase 10) to 
maintain the manifold state across dispatches.
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path

# Add parent directory to path to find bit_flip_harvester
sys.path.append(str(Path(__file__).parent.parent))
from bit_flip_harvester import BitFlipHarvester
import fcntl

def acquire_singleton_lock():
    lock_file = "/home/allaun/.sovereign.lock"
    # Ensure file exists
    if not os.path.exists(lock_file):
        with open(lock_file, "w") as f:
            f.write("sovereign-daemon")
            
    f = open(lock_file, "r")
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        print(f"[🛡️ DAEMON] Singleton lock acquired: {f.name}")
        return f # Keep file handle open to maintain lock
    except BlockingIOError:
        print("[🔥 DAEMON] FATAL: Another Sovereign Daemon is already running.")
        print("[🛡️ DAEMON] Multi-monitor conflict detected. Aborting dispatch to preserve MMR integrity.")
        sys.exit(1)

def drive_sovereign_machine():
    _lock = acquire_singleton_lock()
    harvester = BitFlipHarvester()
    warden_path = Path(__file__).parent.parent / "target" / "release" / "sovereign_warden"
    
    if not warden_path.exists():
        print(f"[🔥 DAEMON] Error: {warden_path} not found. Please run 'cargo build --release'.")
        sys.exit(1)

    print("[🛡️ DAEMON] Sovereign Background Monitor Online.")
    print(f"[🛡️ DAEMON] Path: {warden_path}")
    
    while True:
        try:
            # 1. Harvest physical entropy (EMI, Solar, Thermal noise via Bit Flips)
            events = harvester.harvest_all()
            stress = len(events) * 0.1  # 0.1 accumulation residue per event
            
            # --- CHAOS MONKEY HOOK ---
            chaos_file = Path(__file__).parent.parent / "chaos_injection.json"
            chaos_data = {}
            if chaos_file.exists():
                try:
                    with open(chaos_file, 'r') as f:
                        chaos_data = json.load(f)
                    print(f"[🛡️ DAEMON] Adversarial Injection Detected: {chaos_data.get('label', 'UNKNOWN')}")
                except Exception:
                    pass

            # 2. Prepare Environment logic
            env = os.environ.copy()
            
            # Base physical stress
            if stress > 0:
                print(f"[🛡️ DAEMON] Detected {len(events)} physical events. Baseline Stress={stress:.2f}")
                env["WARDEN_ACCUMULATION_INJECTION"] = str(stress)
            
            # Chaos overrides
            if "torsion" in chaos_data:
                env["WARDEN_TORSION_OVERRIDE"] = str(chaos_data["torsion"])
            if "accumulation" in chaos_data:
                env["WARDEN_ACCUMULATION_INJECTION"] = str(chaos_data["accumulation"])
            if "chi" in chaos_data:
                env["WARDEN_CHI_OVERRIDE"] = str(chaos_data["chi"])

            # 3. Dispatch the Warden
            result = subprocess.run(
                [str(warden_path)], 
                env=env,
                capture_output=True,
                text=True
            )
            
            # 4. Check for HALT/DMT/BREACH
            output = result.stdout + result.stderr
            if "WARDEN HALT" in output or "WARDEN BREACH" in output:
                reason = "HALT" if "WARDEN HALT" in output else "BREACH"
                print(f"[🔥 DAEMON] EMERGENCY {reason} DETECTED! Manifold stability lost.")
                print(f"[🛡️ DAEMON] Initiating 30s Thermophysical Cooldown...")
                time.sleep(30)
            elif "DMT MODE DETECTED" in output:
                print("[🛡️ DAEMON] SHORTCUT ACTIVE: Navigation established.")
            else:
                print("[🛡️ DAEMON] Dispatch successful. Manifold stable.")

            # 5. Calibration Mode: 60s Dispatches
            # (Allows persistence to emerge and maintains the NR1 slow-wave identity)
            time.sleep(60)

        except KeyboardInterrupt:
            print("\n[🛡️ DAEMON] Shutting down gracefully.")
            break
        except Exception as e:
            print(f"[⚠️ DAEMON] Error in cycle: {e}")
            time.sleep(5)

if __name__ == "__main__":
    drive_sovereign_machine()
