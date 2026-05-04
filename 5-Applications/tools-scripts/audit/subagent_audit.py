#!/usr/bin/env python3
"""
Utility: subagent_audit.py
--------------------------
Differential Divergence Sentinel.
"""

import json
import time
import os

class SubagentAuditor:
    def __init__(self):
        self.primary_telemetry = "/home/allaun/Documents/Research Stack/core/ui/telemetry.json"
        self.shadow_telemetry = "/home/allaun/Documents/Research Stack/5-Applications/tools-scripts/shadow_telemetry.json"
        self.audit_report = "/home/allaun/Documents/Research Stack/SHADOW_AUDIT.json"
        self.divergence_threshold = 0.05

    def monitor(self):
        print("[*] Subagent Audit: Monitoring Primary vs Shadow Divergence...")
        while True:
            try:
                with open(self.primary_telemetry, "r") as pf, open(self.shadow_telemetry, "r") as sf:
                    p_data = json.load(pf)
                    s_data = json.load(sf)
                    
                    p_phi = p_data.get("phi", 1.0)
                    s_phi = s_data.get("phi", 1.0)
                    
                    divergence = abs(p_phi - s_phi)
                    
                    report = {
                        "primary_phi": p_phi,
                        "shadow_phi": s_phi,
                        "divergence": divergence,
                        "status": "STABLE" if divergence < self.divergence_threshold else "DIVERGED",
                        "timestamp": time.ctime()
                    }
                    
                    with open(self.audit_report, "w") as f:
                        json.dump(report, f)
                    
                    if report["status"] == "DIVERGED":
                        print(f"[!] ALERT: Informatic Divergence detected! Δ: {divergence:.4f}")
                        
            except Exception as e:
                pass
            
            time.sleep(2)

if __name__ == "__main__":
    auditor = SubagentAuditor()
    auditor.monitor()
