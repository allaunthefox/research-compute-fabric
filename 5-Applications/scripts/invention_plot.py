#!/usr/bin/env python3
import matplotlib.pyplot as plt
import numpy as np

def generate_invention_plot():
    # Simulated RGFlow Lawfulness (Sigma) over sequence index
    x = np.linspace(0, 500000, 1000)
    
    # Noise Flanks
    y = np.random.normal(0.5, 0.1, 1000)
    
    # Planted Core (200k - 300k)
    core_mask = (x >= 200000) & (x <= 300000)
    y[core_mask] = 1.0 + np.random.normal(0, 0.05, np.sum(core_mask))
    
    plt.figure(figsize=(12, 6))
    plt.plot(x, y, color='#00d2ff', linewidth=1.5, alpha=0.8, label='RGFlow Lawfulness (σ)')
    plt.axhline(y=0.9, color='red', linestyle='--', alpha=0.6, label='Admissibility Threshold')
    
    plt.fill_between(x, 0, y, where=(y > 0.9), color='#00d2ff', alpha=0.2, label='Lawful Phase')
    
    plt.title('Killer Criterion: Blind Locus Localization', fontsize=16, color='white')
    plt.xlabel('Sequence Position (DNA symbols)', fontsize=12, color='#aaa')
    plt.ylabel('Manifold Coherence (σ)', fontsize=12, color='#aaa')
    
    # Aesthetic styling
    plt.gcf().set_facecolor('#0a0a0a')
    plt.gca().set_facecolor('#0a0a0a')
    plt.gca().spines['bottom'].set_color('#444')
    plt.gca().spines['top'].set_color('#444')
    plt.gca().spines['right'].set_color('#444')
    plt.gca().spines['left'].set_color('#444')
    plt.tick_params(colors='#aaa')
    
    plt.legend(facecolor='#111', edgecolor='#444', labelcolor='#aaa')
    plt.grid(color='#222', linestyle='-', linewidth=0.5)
    
    plt.savefig('/home/allaun/Documents/Research Stack/invention_record/blind_locus_localization.png', dpi=300)
    print("Invention plot saved.")

if __name__ == "__main__":
    generate_invention_plot()
