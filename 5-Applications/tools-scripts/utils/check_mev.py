# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import os, json, glob
log_files = glob.glob("5-Applications/out/micro_cap_sim/**/*.jsonl", recursive=True)
if not log_files:
    print("No micro_cap_sim logs.")
else:
    latest = max(log_files, key=os.path.getmtime)
    print(f"File: {latest}")
    for line in open(latest).readlines()[-3:]:
        d = json.loads(line)
        print("Time:", d.get('timestamp'), "Route:", d.get('target_route'), "Expected:", d.get('expected_arb_profit_sol'), "Status:", d.get('status'))
