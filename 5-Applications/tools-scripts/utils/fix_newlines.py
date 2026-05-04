# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import re

with open("TSM_COMPILER.py", "r") as f:
    text = f.read()

# Fix all stray raw newlines inside strings that caused the syntax error
text = text.replace('print("\n', 'print("\\n')
text = text.replace('ants.\\n")\n', 'ants.")\n')

with open("TSM_COMPILER.py", "w") as f:
    f.write(text)
