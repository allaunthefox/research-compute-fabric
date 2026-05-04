#!/usr/bin/env python3
"""
plot_nuvmap_projection.py
=========================

Plots the Non-Uniform Virtual Memory Address Projection (NUVMAP) 
of the Burgers Witness-Grammar results.

Projection: (u, v, intensity)
- u: Spectral Mode Index (nu)
- v: Empirical Probabilities (p_hat)
- Intensity: Contribution to Complexity Metric (Omega_nu)
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def plot_nuvmap(bundle_path: Path):
    if not bundle_path.exists():
        print(f"Error: {bundle_path} not found.")
        return

    with open(bundle_path, 'r') as f:
        data = json.load(f)

    local_slos = data.get("local_slos", {})
    p_hat = local_slos.get("empirical_probabilities", {})
    witness_amps = data.get("witness_amps", {})

    # NUVMAP coordinates
    u = [] # Mode indices
    v = [] # Probabilities
    intensity = [] # Omega contributions

    for mode_str, prob in p_hat.items():
        mode = int(mode_str) + 1 # Convert 0-indexed circuit mode to 1-indexed witness mode
        u.append(mode)
        v.append(prob)
        # Omega_n = 0.5 * n^2 * a_n^2
        # In the empirical case, we use the probability as the amplitude square (a_n^2)
        omega_n = 0.5 * (mode**2) * prob
        intensity.append(omega_n)

    u = np.array(u)
    v = np.array(v)
    intensity = np.array(intensity)

    # Plotting
    plt.figure(figsize=(10, 6))
    plt.style.use('dark_background')
    
    # Increase x-limit padding to prevent Mode 3 label clipping
    plt.xlim(0.5, 3.8)
    plt.ylim(-0.05, 1.1)

    # Scatter plot with size/color based on Omega intensity
    sc = plt.scatter(u, v, s=intensity*2000, c=intensity, cmap='viridis', alpha=0.7, edgecolors='white', label=r'Complexity Intensity ($\Omega$)')
    
    # Colorbar with proper label and padding
    cbar = plt.colorbar(sc, label=r'$\Omega_n$ Contribution / Intensity', pad=0.02)
    cbar.ax.tick_params(labelsize=10)
    
    # Title with reduced size and padding
    plt.title('NUVMAP Projection: Burgers Witness-Grammar', fontsize=16, color='cyan', pad=20)
    
    # User-requested axis labels
    plt.xlabel(r'Process/Time/Albedo ($u = \nu$)', fontsize=12, labelpad=10)
    plt.ylabel(r'Spectral Mode ($v = \hat{p}_n$)', fontsize=12, labelpad=10)
    
    plt.grid(True, linestyle='--', alpha=0.3)
    
    # Add labels to points with better offsets
    for i, txt in enumerate(u):
        # Mode 1 label offset further right/down to avoid overlap
        offset = (10, -15) if txt == 1 else (10, 10)
        plt.annotate(fr"Mode {txt}" + "\n" + fr"($\Omega={intensity[i]:.4f}$)", 
                     (u[i], v[i]), 
                     xytext=offset, 
                     textcoords='offset points', 
                     color='white',
                     fontsize=9,
                     bbox=dict(boxstyle="round,pad=0.3", fc="black", alpha=0.5, ec="cyan"))

    # Add numeric legend/annotation for the source signal
    plt.text(0.6, 0.95, r"$S(x) = \sin(x) + 0.3\sin(2x) + 0.1\sin(3x)$", 
             color='yellow', fontsize=12, bbox=dict(facecolor='black', alpha=0.5))

    out_dir = bundle_path.parent
    out_img = out_dir / "nuvmap_projection.png"
    plt.savefig(out_img, dpi=300, bbox_inches='tight')
    print(f"NUVMAP projection saved to {out_img}")
    plt.close()

if __name__ == "__main__":
    bundle_path = Path("/home/allaun/Documents/Research Stack/shared-data/artifacts/quandela_witness_grammar/witness_grammar_photonic_bundle.json")
    plot_nuvmap(bundle_path)
