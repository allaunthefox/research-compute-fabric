# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
with open("Graph OS_DOC.tex", "r") as f:
    text = f.read()

import re
parts = text.split(r'\subsection{Class-X Existential Hazards \& Blacklisted Directives}')
new_text = parts[0] + r'\subsection{Class-X Existential Hazards \& Blacklisted Directives}' + parts[1] + r'\end{document}'

with open("Graph OS_DOC.tex", "w") as f:
    f.write(new_text)
