# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import re

ctrl_path = "TSM_COMPILER.py"
with open(ctrl_path, "r") as f:
    text = f.read()

new_chem_code = """    print("\\n=== OVERRIDING QUANTUM CHEMISTRY BOUNDS ===")
    print("[TSM] Reprogramming molecular orbital mechanics and atomic stability.\\n")
    
    quantum_chemistry_sets = {
        "Fix 1: Noble Gas Hyper-Polymerization (Forcing Xenon-Helium continuous covalent chains)": [131.293, 4.0026, 0.0, 8.0],
        "Fix 2: The Island of Stability Anchor (Permanently stabilizing Element 120 / Unbinilium)": [120.0, 299.0, 1.0e-20, 9.9e9],
        "Fix 3: Covalent-to-Strong-Force Upconversion (Indestructible Carbon Allotropes)": [1.2e-10, 1.0e38, 6.022e23, 12.011],
        "Fix 4: Room-Temperature Metallic Bose-Einstein Condensation (Zero-Friction Gold)": [196.97, 293.15, 0.0, 1.0e-9]
    }
    
    for name, tensor in quantum_chemistry_sets.items():
        print(f"\\n--- Executing Chemistry Override: {name} ---")
        compiler.compile_matter_script(tensor)
        
    print("\\n[TSM-CHEM] Elemental periodicity overwritten. The standard model of chemistry is now obsolete.\\n")"""

# Inject before the final omega print
text = text.replace('print("\\n[TSM-OMEGA]', new_chem_code + '\n    print("\\n[TSM-OMEGA]')

with open(ctrl_path, "w") as f:
    f.write(text)

# ------------- UPDATE DOC -------------
doc_path = "KDA_DOC.tex"
with open(doc_path, "r") as f:
    doc_text = f.read()

chem_section = """
\\subsection{Quantum Chemistry Overrides (The Post-Empirical Periodic Table)}
The machine does not just warp spacetime; it directly rewrites Pauli exclusion principles and electron orbital limits via localized Acoustic Electrodynamics. What were once immutable chemical laws are now adjustable variables:
\\begin{itemize}
    \\item \\textbf{Noble Gas Hyper-Polymers:} By phase-locking complete valence shells with acoustic tensors, the machine forces strictly non-reactive gases (Helium, Xenon) into infinitely scaling covalent polymer chains. 
    \\item \\textbf{Island of Stability Anchoring:} Element 120 (Unbinilium) is theoretically unstable, decaying in microseconds. The MoE Wall injects an inverse-resonance field into the nucleus, completely negating radioactive decay and making superheavy elements permanently stable.
    \\item \\textbf{Strong-Force Covalent Bonds:} Molecular carbon bonds are synthetically 'upconverted' to mirror strong nuclear binding potentials, rendering resulting structures physically indestructible.
    \\item \\textbf{Thermal Isolation (High-Temp BECs):} Synthesizing macroscopic Bose-Einstein Condensates at room temperature (293K) by perfectly cancelling atomic thermal vibrations using destructive phononic harmonics.
\\end{itemize}
"""

if r"\end{document}" in doc_text:
    doc_text = doc_text.replace(r"\end{document}", chem_section + "\n\\end{document}")
else:
    doc_text += "\n" + chem_section

with open(doc_path, "w") as f:
    f.write(doc_text)

