#!/usr/bin/env python3
"""
Hutter Prize (enwik8) RGFlow Filter
Filtrating the White Whale of compression benchmarks.
"""

import os
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
logger = logging.getLogger(__name__)

def filter_hutter_parquet(input_parquet: Path, output_parquet: Path):
    print(f"Loading Hutter Prize Parquet: {input_parquet.name}...")
    df = pd.read_parquet(input_parquet)
    
    # Sample first 10,000 rows for immediate audit
    df = df.head(10000)
    
    # Assuming the text is in a column named 'text' or similar
    text_col = 'text' if 'text' in df.columns else df.columns[0]
    print(f"Filtering {len(df)} chunks using RGFlow (SAMPLED)...")

    detector = BlindDetector()
    results = []
    
    for i, row in df.iterrows():
        text = str(row[text_col])
        # We need to convert text back to DNA or just use its bits
        # For enwik8, we can use the bits directly or treat as 'DNA' (A=00, C=01, G=10, T=11)
        # But our blind detector expects ACGT. We'll map the text to ACGT.
        # Simple mapping: 2 bits per char -> DNA
        binary = "".join(format(ord(c), '08b') for c in text[:1000]) # Audit first 1k chars
        mapping = {'00': 'A', '01': 'C', '10': 'G', '11': 'T'}
        dna_proxy = "".join(mapping[binary[j:j+2]] for j in range(0, len(binary), 2))
        
        state = detector.calculate_window_state(dna_proxy)
        (lawful_now, lawful_under_flow, reaches_attractor, _, _, _, margin, rg_depth, attractor_id, _) = \
            detector.adaptation_eq.evaluate_state(state)
        
        results.append({
            "idx": i,
            "lawful": lawful_under_flow,
            "margin": float(margin),
            "depth": int(rg_depth),
            "attractor": int(attractor_id),
            "sigma": float(state.sigma_q),
            "mu": float(state.mu_q)
        })
        
        if i % 100 == 0:
            print(f"Processed {i}/{len(df)} chunks...")

    res_df = pd.DataFrame(results)
    final_df = pd.concat([df, res_df], axis=1)
    
    # Filter for ONLY Lawful chunks (The White Whale Signal)
    lawful_df = final_df[final_df['lawful'] == True]
    
    lawful_df.to_parquet(output_parquet)
    print(f"Filtration complete. Saved {len(lawful_df)} lawful chunks to {output_parquet}")
    print(f"Averge Sigma for Lawful Chunks: {lawful_df['sigma'].mean():.4f}")

if __name__ == "__main__":
    input_p = Path("/home/allaun/Documents/Research Stack/data/enwik8_huggingface/context128-stride1/test-00000-of-00002.parquet")
    output_p = Path("/home/allaun/Documents/Research Stack/data/enwik8_huggingface/enwik8_lawful_filtered.parquet")
    
    if input_p.exists():
        filter_hutter_parquet(input_p, output_p)
    else:
        print("Error: Hutter Prize Parquet not found.")
