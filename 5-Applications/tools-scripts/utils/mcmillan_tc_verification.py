# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from math_harness_compat import xp, AnyArray
import scipy.constants as const

def mcmillan_allen_dynes(omega_log, lambd, mu_star):
    """
    McMillan-Allen-Dynes formula for Tc.
    omega_log: Logarithmic average phonon frequency (K)
    lambd: Electron-phonon coupling strength
    mu_star: Coulomb pseudopotential
    """
    num = -1.04 * (1 + lambd)
    den = lambd - mu_star * (1 + 0.62 * lambd)
    tc = (omega_log / 1.2) * xp.exp(num / den)
    return tc

# Target: Tc = 494K
# Hydrogen frequency (~250-300 meV) -> K
omega_h = 280 * 11.604  # ~3249 K
mu_star = 0.13

# Solve for lambda
print(f"Target Tc: 494 K")
print(f"Phonon freq (omega_log): {omega_h:.2f} K")
print(f"Coulomb mu*: {mu_star}")

for l in xp.linspace(1.5, 3.5, 20):
    tc = mcmillan_allen_dynes(omega_h, l, mu_star)
    if tc > 490:
        print(f"LAMBDA FOUND: {l:.4f} -> Tc: {tc:.2f} K")
        break
