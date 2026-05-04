# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================

# [WARDEN BOUNDARY ENFORCEMENT INJECTED]
import sys
import os
try:
    from io_harness_compat import spawn_isolated_process, fetch_network_resource
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from io_harness_compat import spawn_isolated_process, fetch_network_resource

#!/usr/bin/env python3
import json
# import subprocess (REMOVED BY WARDEN)
from pathlib import Path
from datetime import datetime, timezone
import math

# UNIVERSE CONSTANTS
AETHER_FLOOR = 0.5
AXES = ['content_hash', 'tier', 'kind', 'meta', 'omega', 'primitive']

def fnv32(s: str) -> int:
    h = 0x811c9dc5
    for char in s:
        h ^= ord(char)
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h

def get_nd_metrics(text: str, identifier: str):
    all_spins = []
    for axis in AXES:
        seed = fnv32(f"{axis}:{identifier}:{text[:500]}")
        s_val = seed
        for _ in range(64):
            s_val = ((s_val << 13) ^ s_val) & 0xFFFFFFFF
            s_val = ((s_val >> 17) ^ s_val) & 0xFFFFFFFF
            s_val = ((s_val << 5) ^ s_val) & 0xFFFFFFFF
            all_spins.append(1 if (s_val & 1) else -1)
    
    p_up = len([s for s in all_spins if s == 1]) / len(all_spins)
    p_dn = 1.0 - p_up
    entropy = -(p_up * math.log2(p_up) + p_dn * math.log2(p_dn)) if 0 < p_up < 1 else 0.0
    return entropy

def get_git_anomalies(repo_path: str):
    cmd = ["git", "-C", repo_path, "log", "--pretty=format:%H|%ai|%ci|%ae|%ce|%s", "--all"]
    output = subprocess.check_output(cmd, encoding='utf-8')
    anomalies = []
    for line in output.splitlines():
        parts = line.split('|')
        if len(parts) < 6: continue
        sha, ad, cd, ae, ce, sub = parts
        
        # Parse dates
        adt = datetime.fromisoformat(ad)
        cdt = datetime.fromisoformat(cd)
        delta = abs((cdt - adt).total_seconds())
        
        if delta > 3600: # 1 hour threshold
            anomalies.append({
                "sha": sha,
                "author": ae,
                "committer": ce,
                "delta": delta,
                "subject": sub
            })
    return anomalies

def reverse_provenance(repo_path: str):
    anomalies = get_git_anomalies(repo_path)
    report = []
    
    for anom in anomalies:
        # Get files changed in this commit
        cmd = ["git", "-C", repo_path, "show", "--name-only", "--pretty=format:", anom['sha']]
        files = subprocess.check_output(cmd, encoding='utf-8').splitlines()
        
        for f in files:
            if not f.strip(): continue
            f_path = Path(repo_path) / f
            if not f_path.exists(): continue
            
            try:
                content = f_path.read_text(encoding='utf-8', errors='ignore')
                entropy = get_nd_metrics(content, f)
                aether_err = abs(entropy - AETHER_FLOOR)
                
                # Reverse Provenance Signature: High Temporal Delta + High Aether Error
                rp_signature = aether_err * math.log10(max(10, anom['delta']))
                
                report.append({
                    "sha": anom['sha'],
                    "file": f,
                    "author": anom['author'],
                    "committer": anom['committer'],
                    "delta": anom['delta'],
                    "entropy": entropy,
                    "aether_error": aether_err,
                    "rp_signature": round(rp_signature, 6)
                })
            except Exception:
                continue
                
    report.sort(key=lambda x: x['rp_signature'], reverse=True)
    return report

if __name__ == "__main__":
    target = "/tmp/proofmode-android"
    print(f"[*] Running Reverse Provenance Audit on {target}...")
    findings = reverse_provenance(target)
    
    print(f"\n[+] Reverse Provenance Top Hits (Thermal-Semantic Displacement):")
    print("-" * 100)
    print(f"{'File':<40} | {'Author':<25} | {'Delta(s)':<10} | {'RP_Sig':<10}")
    print("-" * 100)
    for f in findings[:15]:
        print(f"{f['file'][:40]:<40} | {f['author'][:25]:<25} | {int(f['delta']):<10} | {f['rp_signature']:.6f}")
    
    out_path = Path("5-Applications/out/reverse_provenance_report.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(findings, indent=2), encoding='utf-8')
    print(f"\n[+] Full report written to {out_path}")
