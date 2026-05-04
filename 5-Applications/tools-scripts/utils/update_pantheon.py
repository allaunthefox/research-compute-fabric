# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
with open("graph os_moe_pantheon.py", "r") as f:
    text = f.read()

import re

# Remove GPT-4o from the pantheon specs dictionary
text = re.sub(r'\s*"GPT-4o \(Omni-Modal\)": \{"d_model": 12288, "layers": 120, "experts": 128\},', '', text)

# Update the target string at the top of the file
text = text.replace("Target: Full Copilot Chat Model Roster (GPT-4o, Claude 3.5 Sonnet, o3-mini)", "Target: Sanitized Copilot Roster (Claude 3.5 Sonnet, o3-mini)")

with open("graph os_moe_pantheon.py", "w") as f:
    f.write(text)
