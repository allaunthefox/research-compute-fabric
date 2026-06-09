#!/usr/bin/env python3
"""
verify_all_shims.py - Master coordination script for the verification suite.
Copies all shims to the EPYC cupfox node, executes them sequentially in the venv,
downloads their receipts, and outputs a summary report.
"""

import subprocess
import sys
import os
import time

SHIMS = [
    ("erdos_discrepancy_probe.py", "--output /root/erdos_discrepancy_receipt.json"),
    ("entropic_collision_prober.py", "--output /root/entropic_collision_receipt.json"),
    ("quandela_erdos_search.py", "--output /root/quandela_erdos_search_receipt.json"),
    ("openai_unit_distance_verifier.py", "--output /root/openai_unit_distance_receipt.json"),
    ("galois_orbit_trimmer.py", "--output /root/galois_orbit_trim_receipt.json"),
    ("burgers_2d_simplification.py", "--output /root/burgers_2d_simplification_receipt_128.json --grid 128"),
    ("braid_shock_16d.py", "--output /root/braid_shock_receipt.json")
]

CUPFOX_IP = "46.232.249.226"
CUPFOX_USER = "root"
CUPFOX_VENV = "/root/venv/bin/python3"
LOCAL_RECEIPT_DIR = "shared-data/data/stack_solidification"

def run_local(cmd):
    print(f"Local exec: {cmd}")
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error: {res.stderr}")
        sys.exit(res.returncode)
    return res.stdout

def run_remote(cmd):
    ssh_cmd = f"ssh {CUPFOX_USER}@{CUPFOX_IP} \"{cmd}\""
    print(f"Remote exec: {ssh_cmd}")
    res = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Remote error: {res.stderr}")
        sys.exit(res.returncode)
    return res.stdout

def main():
    print("=== Step 1: Copying all shims to EPYC node (cupfox) ===")
    os.makedirs(LOCAL_RECEIPT_DIR, exist_ok=True)
    
    for shim, _ in SHIMS:
        local_path = os.path.join("4-Infrastructure/shim", shim)
        if not os.path.exists(local_path):
            print(f"Error: Local path {local_path} does not exist.")
            sys.exit(1)
        run_local(f"scp {local_path} {CUPFOX_USER}@{CUPFOX_IP}:/root/")
        
    print("\n=== Step 2: Executing shims sequentially on EPYC node ===")
    start_time = time.time()
    
    for shim, args in SHIMS:
        print(f"\n---> Running {shim}...")
        remote_cmd = f"{CUPFOX_VENV} /root/{shim} {args}"
        stdout = run_remote(remote_cmd)
        print(stdout.strip())
        
    print(f"\nExecution finished in {time.time() - start_time:.2f} seconds.")
    
    print("\n=== Step 3: Downloading receipts to local stack repository ===")
    for shim, args in SHIMS:
        # Extract output filename from args
        output_file = ""
        parts = args.split()
        for idx, part in enumerate(parts):
            if part == "--output":
                output_file = parts[idx + 1]
                break
        if not output_file:
            continue
            
        receipt_name = os.path.basename(output_file)
        run_local(f"scp {CUPFOX_USER}@{CUPFOX_IP}:{output_file} {LOCAL_RECEIPT_DIR}/")
        print(f"Downloaded: {receipt_name}")
        
    print("\n=== Verification Suite Summary ===")
    print("Status: SUCCESS")
    print(f"All {len(SHIMS)} shims executed sequentially. Receipts stored in {LOCAL_RECEIPT_DIR}/")

if __name__ == "__main__":
    main()
