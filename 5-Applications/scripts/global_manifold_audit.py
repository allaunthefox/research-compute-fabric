#!/usr/bin/env python3
"""
Global Sovereign Manifold Audit
RGFlow on Unified Compression Data
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

def run_global_audit(input_parquet: Path, output_summary: Path):
    print(f"Opening Master Sovereign Manifold: {input_parquet.name}")
    df = pd.read_parquet(input_parquet)
    
    detector = BlindDetector()
    results = []
    
    print(f"Auditing {len(df)} records across Unified Compression stack...")

    # We iterate through the records. We need to find the 'data' or 'ids' column.
    data_col = next((c for c in df.columns if c in ['input_ids', 'ids', 'data', 'text']), df.columns[0])
    
    # Audit a representative sample if too large
    sample_size = min(len(df), 20000)
    df_sample = df.sample(sample_size, random_state=42)

    for i, (idx, row) in enumerate(df_sample.iterrows()):
        content = row['content']
        seq = str(content)
        
        # 1. Mutation (mu): high character transitions in code
        transitions = sum(1 for k in range(len(seq)-1) if seq[k] != seq[k+1])
        mu_q = (transitions / len(seq)) * 0.1 if len(seq) > 0 else 0
        
        # 2. Entropy
        counts = np.unique(list(seq), return_counts=True)[1]
        probs = counts / len(seq)
        entropy = -np.sum(probs * np.log2(probs + 1e-9))
        
        # 3. Admissibility
        # Mathlib code is dense. Sigma should be high.
        sigma_q = 1.0 + (entropy / 4.0)
        
        state = detector.calculate_window_state('ACGT'*100)
        state.sigma_q = sigma_q
        state.mu_q = mu_q
        
        (lawful_now, lawful_under_flow, _, _, _, _, _, rg_depth, attractor_id, _) = \
            detector.adaptation_eq.evaluate_state(state)

        if i < 5:
            print(f"Record {idx}: mu={mu_q:.4f}, sigma={sigma_q:.4f}, lawful={lawful_under_flow}")

        results.append({
            "idx": idx,
            "lawful": lawful_under_flow,
            "sigma": sigma_q,
            "depth": rg_depth,
            "path": row.get('path', 'unknown')
        })

        if i % 1000 == 0:
            print(f"Audit Progress: {i}/{sample_size}")

    res_df = pd.DataFrame(results)
    top_lawful = res_df[res_df['lawful'] == True].sort_values(by='sigma', ascending=False)
    
    print("\n--- TOP LAWFUL SIGNALS IN UNIFIED STACK ---")
    print(top_lawful.head(10))
    
    top_lawful.to_csv(output_summary, index=False)
    print(f"\nAudit complete. Summary saved to {output_summary}")

if __name__ == "__main__":
    master_p = Path("/home/allaun/Documents/Research Stack/data/datasets/master_sovereign_manifold.parquet")
    output_s = Path("/home/allaun/Documents/Research Stack/data/datasets/global_audit_summary.csv")
    
    if master_p.exists():
        run_global_audit(master_p, output_s)
    else:
        print("Error: Master Manifold not found.")
