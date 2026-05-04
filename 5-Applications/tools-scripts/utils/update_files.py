# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import os

# Update KDA_CONTROL.py
with open("KDA_CONTROL.py", "r") as f:
    text = f.read()

text = text.replace("ANCDemon", "ANCController")
text = text.replace("Entropy Sink", "Array")
text = text.replace("Functions as a Maxwell's Demon: measures", "Measures")
text = text.replace("entropy_sink_active", "anc_active")
text = text.replace("Information-to-Energy conversion: Calculate", "Calculate")
text = text.replace("# H(X) = -sum(P(x) * log2(P(x))) - Information Entropy\n", "")
text = text.replace("anc_demon", "anc_system")
text = text.replace("Pentagram entropy sink", "Pentagonal acoustic dampening")
text = text.replace("Maxwell's Demon routine to sink", "ANC routine to mitigate")

with open("KDA_CONTROL.py", "w") as f:
    f.write(text)

# Update KDA_DOC.tex
with open("KDA_DOC.tex", "r") as f:
    tex = f.read()

tex = tex.replace("Acoustic Containment: Information-to-Energy Entropy Sink", "Acoustic Containment: Harmonic Mitigation")
tex = tex.replace("This subsystem functions strictly on the thermodynamic definition of a \\textbf{Maxwell's Demon}. By", "By")
tex = tex.replace("The information gained by the sensors is converted directly into an entropy sink, stabilizing the chaotic kinetic drift:\n\n\\begin{equation}\n\\Delta S_{system} + \\Delta S_{demon} \\ge 0\n\\end{equation}\n\n", "The acoustic counter-pulse stabilizes the chaotic kinetic drift over the operational cycle.\n\n")

with open("KDA_DOC.tex", "w") as f:
    f.write(tex)

# Update KDA_CORE.scad
with open("KDA_CORE.scad", "r") as f:
    scad = f.read()

scad = scad.replace("KDA_CORE_V1.5 - KINETIC DIFFERENTIAL ARRAY WITH ANC (MAXWELL DEMON)", "KDA_CORE_V1.5 - KINETIC DIFFERENTIAL ARRAY WITH ANC COMPENSATOR")
scad = scad.replace("Maxwell's Demon 5-point outer array", "5-point outer acoustic array")
scad = scad.replace("=== 5-POINT ANC MAXIMUM ENTROPY SINK (MAXWELL'S DEMON) ===", "=== 5-POINT ANC HARMONIC MITIGATION ARRAY ===")

with open("KDA_CORE.scad", "w") as f:
    f.write(scad)

print("Scrubbed Maxwell's Demon terminology.")
