#!/usr/bin/env python3
"""
Bitcoin RGFlow Data Fetcher (AGENTS.md §6.1 Compliant)

Fetches Bitcoin price data and calls Lean bindserver for RGFlow analysis.
Python shim responsibilities: JSON serialization, subprocess spawn, result wrapping.
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "4-Infrastructure"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "0-Core-Formalism"))

from infra.lean_unified_shim import LeanUnifiedShim

def get_bitcoin_historical_data() -> List[float]:
    """Fetch full historical Bitcoin price data since 2009.
    
    Allowed per AGENTS.md §6.1: Subprocess spawn for data fetching.
    """
    start_date = "2009-09-01"
    end_date = datetime.now().strftime("%Y-%m-%d")
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/BTC-USD?interval=1d&period1={int(datetime(2009, 9, 1).timestamp())}&period2={int(datetime.now().timestamp())}"
    cmd = ["curl", "-s", "-H", "User-Agent: Mozilla/5.0", url]
    out = subprocess.check_output(cmd)
    data = json.loads(out)
    prices = data['chart']['result'][0]['indicators']['quote'][0]['close']
    # Filter out None values
    return [p for p in prices if p is not None]

def prices_to_q1616(prices: List[float]) -> List[int]:
    """Convert Bitcoin prices to Q16.16 format for Lean.
    
    Allowed per AGENTS.md §6.1: Data transformation for Lean input.
    """
    import numpy as np
    prices_np = np.array(prices)
    log_prices = np.log(prices_np)
    min_log = np.min(log_prices)
    max_log = np.max(log_prices)
    if max_log - min_log > 0:
        scaled = ((log_prices - min_log) / (max_log - min_log) * 65535).astype(int)
    else:
        scaled = np.zeros_like(log_prices, dtype=int)
    return scaled.tolist()

def main():
    print("=" * 70)
    print("BITCOIN RGFLOW ANALYSIS (LEAN BINDSERVER)")
    print("=" * 70)
    
    # Fetch full historical Bitcoin data
    print("\nFetching full historical Bitcoin price data since 2009...")
    prices = get_bitcoin_historical_data()
    print(f"Acquired {len(prices)} price points")
    print(f"Price range: ${min(prices):,.2f} - ${max(prices):,.2f}")
    print(f"Latest price: ${prices[-1]:,.2f}")
    
    # Convert to Q16.16 for Lean
    print("\nConverting prices to Q16.16 format for Lean...")
    prices_q1616 = prices_to_q1616(prices)
    print(f"Generated {len(prices_q1616)} Q16.16 values")
    
    # Initialize Lean bindserver shim
    shim = LeanUnifiedShim()
    
    # Call Lean for RGFlow analysis
    print("\nCalling Lean bindserver for RGFlow analysis...")
    lean_code = f"""
import Semantics.BitcoinRGFlow
let prices := {prices_q1616}
let results := Semantics.batchBitcoinRGFlowQ16 prices 30
results
"""
    result = shim.query(lean_code)
    
    if "error" in result:
        print(f"\nError from Lean bindserver: {result['error']}")
        return
    
    # Process Lean results
    print("\n" + "=" * 70)
    print("RGFLOW ANALYSIS RESULTS (FROM LEAN)")
    print("=" * 70)
    
    if isinstance(result, list):
        print(f"\nTotal positions analyzed: {len(result)}")
        
        # Extract metrics from Lean results
        sigma_values = []
        lawful_count = 0
        for r in result:
            if isinstance(r, tuple) and len(r) == 3:
                sigma_q, mu_q, lawful = r
                # Convert Q16.16 raw values to float for display
                sigma_float = sigma_q / 65536.0 if isinstance(sigma_q, int) else 0.0
                sigma_values.append(sigma_float)
                if lawful:
                    lawful_count += 1
        
        if sigma_values:
            import numpy as np
            print(f"Lawful states: {lawful_count} ({lawful_count/len(result)*100:.1f}%)")
            print(f"Average sigma_q: {np.mean(sigma_values):.4f}")
            print(f"Sigma range: {min(sigma_values):.4f} - {max(sigma_values):.4f}")
            
            # Detect informatic collapse
            low_sigma_count = sum(1 for s in sigma_values if s < 1.0)
            if low_sigma_count > 0:
                print(f"\n⚠️  INFORMATIC COLLAPSE DETECTED")
                print(f"   {low_sigma_count} states have sigma_q < 1.0")
                print(f"   This indicates structural instability in the price sequence")
            else:
                print(f"\n✓ MANIFOLD STABLE")
                print(f"   All states maintain scale stability (sigma_q ≥ 1.0)")
        
        # Save results
        output_file = "/home/allaun/Documents/Research Stack/data/bitcoin_rgflow_results.json"
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "data_points": len(prices),
            "price_range": {"min": min(prices), "max": max(prices)},
            "latest_price": prices[-1],
            "rgflow_results": result,
            "statistics": {
                "total_positions": len(result),
                "lawful_count": lawful_count,
                "average_sigma": float(np.mean(sigma_values)) if sigma_values else 0.0,
                "min_sigma": float(min(sigma_values)) if sigma_values else 0.0,
                "max_sigma": float(max(sigma_values)) if sigma_values else 0.0
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        print(f"\nResults saved to: {output_file}")
        
    else:
        print("\nUnexpected result format from Lean")
        print(f"Result type: {type(result)}")

if __name__ == "__main__":
    main()
