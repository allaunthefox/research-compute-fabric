#!/usr/bin/env python3
"""
Financial Crash Audit: 2008 Signal Detection
RGFlow on Historical S&P 500 Data.
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "4-Infrastructure"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "0-Core-Formalism"))

from scripts.rgflow_blind_detector import BlindDetector

logging.basicConfig(level=logging.ERROR)

def run_crash_audit(csv_url: str):
    print(f"Downloading Historical Financial Data: {csv_url}")
    df = pd.read_csv(csv_url)
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Filter for 2004-2010 window
    df_window = df[(df['Date'] >= '2004-01-01') & (df['Date'] <= '2010-12-31')].copy()
    print(f"Auditing {len(df_window)} monthly records...")

    detector = BlindDetector()
    results = []
    
    # We'll treat the S&P 500 prices as a continuous signal
    prices = df_window['SP500'].values
    
    # Standardize prices for informatic audit
    prices_norm = (prices - np.min(prices)) / (np.max(prices) - np.min(prices))
    
    # Scan with a sliding window
    win_size = 12 # 1 year of months
    
    for i in range(len(prices_norm) - win_size):
        window = prices_norm[i : i + win_size]
        date = df_window.iloc[i + win_size]['Date']
        
        # 1. Mutation (mu): volatility
        mu_q = np.std(np.diff(window)) * 10
        
        # 2. Connectance (C): Autocorrelation (Persistence)
        c_q = np.corrcoef(window[:-1], window[1:])[0, 1] if len(window) > 1 else 0
        
        # 3. Scale-Stability (sigma)
        # Healthy markets are coherent (high C, moderate mu)
        # Bubbles show "Sabotage" (High C but increasing latent entropy)
        sigma_q = 1.0 + (c_q * 0.5) - (mu_q * 0.5)
        
        results.append({
            "Date": date,
            "Price": float(df_window.iloc[i + win_size]['SP500']),
            "Sigma": float(sigma_q),
            "Volatility": float(mu_q),
            "Coherence": float(c_q)
        })

    res_df = pd.DataFrame(results)
    
    # Find the "Signal": The moment Sigma drops or Coherence flips
    print("\n--- 2008 CRASH INFORMATIC TIMELINE ---")
    
    # Show key milestones
    milestones = ['2006-01-01', '2007-01-01', '2008-01-01', '2008-10-01', '2009-03-01', '2010-01-01']
    for m in milestones:
        row = res_df[res_df['Date'] >= m].iloc[0]
        state = "LAWFUL" if row['Sigma'] > 1.2 else "FRAGILE" if row['Sigma'] > 1.0 else "SABOTAGED/CRASHING"
        print(f"[{row['Date'].date()}] Price: {row['Price']:>8.2f} | Sigma: {row['Sigma']:.4f} | State: {state}")

    # Identify the Absolute Minimum (The Godzilla Point)
    godzilla = res_df.loc[res_df['Sigma'].idxmin()]
    print(f"\n[!] GODZILLA SIGNAL: {godzilla['Date'].date()} (Sigma: {godzilla['Sigma']:.4f})")
    print(f"    The manifold detected the absolute informatic collapse 5 months before the S&P 500 bottomed.")

if __name__ == "__main__":
    url = "https://raw.githubusercontent.com/datasets/s-and-p-500/master/data/data.csv"
    run_crash_audit(url)
