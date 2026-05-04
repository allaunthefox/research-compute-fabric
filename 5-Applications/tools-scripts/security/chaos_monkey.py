#!/usr/bin/env python3
import json
import os
import sys
import argparse

CHAOS_FILE = "chaos_injection.json"

def write_chaos(data):
    with open(CHAOS_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"[🐵 CHAOS MONKEY] Injection committed: {json.dumps(data)}")

def cmd_torsion():
    write_chaos({"torsion": 5.0, "label": "TORSION_OVERLOAD_ATTACK"})

def cmd_clog():
    write_chaos({"accumulation": 2.0, "label": "CLOG_SATURATION_ATTACK"})

def cmd_dmt():
    # DMT triggers when chi is high and torsion is moderate
    write_chaos({
        "chi": 0.8,
        "torsion": 0.5,
        "label": "DMT_LURE_INJECTION"
    })

def cmd_reset():
    if os.path.exists(CHAOS_FILE):
        os.remove(CHAOS_FILE)
    print("[🐵 CHAOS MONKEY] Injections cleared. System returning to baseline.")

def main():
    parser = argparse.ArgumentParser(description="Sovereign Chaos Monkey - Adversarial Stress Testing")
    parser.add_argument("mode", choices=["torsion", "clog", "dmt", "reset"], help="Chaos mode to inject")
    
    args = parser.parse_args()
    
    if args.mode == "torsion":
        cmd_torsion()
    elif args.mode == "clog":
        cmd_clog()
    elif args.mode == "dmt":
        cmd_dmt()
    elif args.mode == "reset":
        cmd_reset()

if __name__ == "__main__":
    main()
