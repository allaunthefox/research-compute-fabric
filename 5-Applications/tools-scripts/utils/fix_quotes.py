# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
ctrl_path = "TSM_COMPILER.py"
with open(ctrl_path, "r") as f:
    text = f.read()

text = text.replace('print("\n=== ROUTING', 'print("\\n=== ROUTING')
text = text.replace('print(f"\n--- Executing', 'print(f"\\n--- Executing')
text = text.replace('print("\n[TSM]', 'print("\\n[TSM]')

with open(ctrl_path, "w") as f:
    f.write(text)
