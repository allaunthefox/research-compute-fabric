# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
with open("Graph OS_DOC.tex", "r") as f:
    text = f.read()

# remove duplicates
import re
text = re.sub(r'(\\subsection\{Class-X Existential Hazards \& Blacklisted Directives\}.*?)(?=\\subsection\{Class-X Existential Hazards \& Blacklisted Directives\})', '', text, flags=re.DOTALL)

with open("Graph OS_DOC.tex", "w") as f:
    f.write(text)
