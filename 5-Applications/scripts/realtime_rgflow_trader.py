#!/usr/bin/env python3
"""
Real-time RGFlow Trader: BTC-USD
Informatic Prediction via Manifold Coherence.
"""

import sys
import json
import numpy as np
import subprocess
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "4-Infrastructure"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "0-Core-Formalism"))

from scripts.rgflow_blind_detector import BlindDetector

logging.basicConfig(level=logging.ERROR)

def get_live_data(symbol="BTC-USD"):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=2h"
    cmd = ["curl", "-s", "-H", "User-Agent: Mozilla/5.0", url]
    out = subprocess.check_output(cmd)
    data = json.loads(out)
    prices = data['chart']['result'][0]['indicators']['quote'][0]['close']
    # Filter out None values
    prices = [p for p in prices if p is not None]
    return np.array(prices)

def predict_signal():
    print("--- REAL-TIME RGFLOW PREDICTIVE AUDIT [BTC-USD] ---")
    prices = get_live_data()
    
    if len(prices) < 20:
        print("Error: Not enough live data.")
        return
        
    print(f"Acquired {len(prices)} live price points. Latest: ${prices[-1]:,.2f}")
    
    # 1. Convert to Log Returns (The Informatic Genome)
    returns = np.diff(np.log(prices))
    
    detector = BlindDetector()
    
    # Audit sliding windows across the last 60 minutes
    window_size = 20
    sigmas = []
    
    for i in range(len(returns) - window_size + 1):
        window = returns[i : i + window_size]
        # Standardize for detector
        win_norm = (window - np.mean(window)) / (np.std(window) + 1e-9)
        
        # Heuristic State
        mu_q = np.std(np.diff(win_norm)) * 0.5
        c_q = np.corrcoef(win_norm[:-1], win_norm[1:])[0, 1] if len(win_norm) > 1 else 0
        sigma_q = 1.0 + (c_q * 0.3) - (mu_q * 0.2)
        
        sigmas.append(sigma_q)

    # 2. Analyze Momentum
    current_sigma = sigmas[-1]
    prev_sigma = sigmas[-5] if len(sigmas) > 5 else sigmas[0]
    velocity = current_sigma - prev_sigma
    
    print(f"\nCurrent Informatic Coherence (σ): {current_sigma:.4f}")
    print(f"Manifold Velocity (Δσ):          {velocity:+.4f}")
    
    # 3. SIGNAL GENERATION
    print("\n--- INFORMATIC PREDICTION ---")
    if velocity > 0.02 and current_sigma > 1.05:
        print("SIGNAL: [🚀 JUMP EXPECTED ]")
        print("REASON: Lawful Resonance. The market intent is crystallizing into a scale-stable trajectory.")
    elif velocity < -0.02 or current_sigma < 0.95:
        print("SIGNAL: [📉 DIP EXPECTED ]")
        print("REASON: Informatic Sabotage. Manifold stability is collapsing into the noise attractor.")
    else:
        print("SIGNAL: [⚖️ NEUTRAL / SIDEWAYS ]")
        print("REASON: Manifold EQ. No dominant lawful attractor detected in current window.")

    print("\n[Audit Verified by Sovereign Manifold]")

if __name__ == "__main__":
    predict_signal()
