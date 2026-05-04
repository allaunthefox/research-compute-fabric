#!/usr/bin/env python3
"""
Ethereum RGFlow Data Fetcher — Python-native implementation.

Fetches full historical ETH-USD price data and performs RGFlow analysis
using the same invariant logic as the Lean formalization, but without
the unified shim build dependency (avoids pre-existing failing modules).

Outputs Q16.16-encoded price series with sigma_q, mu_q, and lawfulness
flags for each position. Suitable for MEV bot integration.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import numpy as np

# ═══════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════

REPO_ROOT = Path(__file__).parent.parent.parent
OUTPUT_FILE = REPO_ROOT / "data" / "ethereum_rgflow_results.json"

# Q16.16 constants
Q16_ONE = 65536
Q16_HALF = 32768
Q16_ZERO35 = 22937   # 0.35 * 65536
Q16_EIGHT = 524288   # 8.0 * 65536
Q16_LAMBDA = 32768   # 0.5 * 65536

# ═══════════════════════════════════════════════════════════════════════════
# Data fetching
# ═══════════════════════════════════════════════════════════════════════════

def fetch_eth_prices() -> List[float]:
    """Fetch full historical ETH-USD daily prices from Yahoo Finance."""
    start_ts = int(datetime(2015, 7, 30).timestamp())
    end_ts = int(datetime.now().timestamp())
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/ETH-USD"
        f"?interval=1d&period1={start_ts}&period2={end_ts}"
    )
    cmd = ["curl", "-s", "-H", "User-Agent: Mozilla/5.0", url]
    out = subprocess.check_output(cmd)
    data = json.loads(out)
    prices = data['chart']['result'][0]['indicators']['quote'][0]['close']
    return [p for p in prices if p is not None]

# ═══════════════════════════════════════════════════════════════════════════
# Q16.16 helpers
# ═══════════════════════════════════════════════════════════════════════════

def prices_to_q1616(prices: List[float]) -> np.ndarray:
    """Convert float prices to Q16.16 fixed-point integers."""
    arr = np.array(prices, dtype=np.float64)
    log_prices = np.log(arr)
    min_log, max_log = np.min(log_prices), np.max(log_prices)
    if max_log - min_log > 0:
        scaled = ((log_prices - min_log) / (max_log - min_log) * 65535).astype(np.int64)
    else:
        scaled = np.zeros_like(log_prices, dtype=np.int64)
    return scaled

def q16_add(a: int, b: int) -> int:
    return a + b

def q16_sub(a: int, b: int) -> int:
    return a - b

def q16_mul(a: int, b: int) -> int:
    return (a * b) >> 16

def q16_div(a: int, b: int) -> int:
    return (a << 16) // b if b != 0 else 0

def q16_sqrt_approx(x: int) -> int:
    """sqrt(x) ≈ x * (1.5 - 0.5*x) for x near 1.0 in Q16.16"""
    one = Q16_ONE
    one_half = Q16_HALF
    three_half = 49152
    norm = q16_div(x, one)
    return q16_mul(norm, q16_sub(three_half, q16_mul(one_half, norm)))

# ═══════════════════════════════════════════════════════════════════════════
# RGFlow analysis (mirrors Lean BitcoinRGFlow logic)
# ═══════════════════════════════════════════════════════════════════════════

def log_returns_q16(prices: np.ndarray) -> np.ndarray:
    """Compute approximate log returns in Q16.16."""
    if len(prices) < 2:
        return np.array([], dtype=np.int64)
    returns = []
    for i in range(len(prices) - 1):
        p0, p1 = prices[i], prices[i + 1]
        if p0 > 0 and p1 > 0:
            ratio = q16_div(p1, p0)
            diff = q16_sub(ratio, Q16_ONE)
            diff_sq = q16_mul(diff, diff)
            log_approx = q16_sub(diff, q16_mul(Q16_HALF, diff_sq))
            returns.append(log_approx)
    return np.array(returns, dtype=np.int64)

def safe_std_q16(xs: np.ndarray) -> int:
    """Standard deviation in Q16.16."""
    if len(xs) <= 1:
        return 0
    mean = int(np.mean(xs))
    diffs = xs - mean
    var = int(np.mean(diffs * diffs))
    return q16_sqrt_approx(var)

def compute_mu_q16(returns: np.ndarray, i: int, window: int = 30) -> int:
    """Rolling mean log return (drift rate)."""
    if len(returns) < 2:
        return 0
    ri = max(0, i - 1)
    start = max(0, ri - window + 1)
    window_data = returns[start:ri + 1]
    if len(window_data) < 2:
        return 0
    return int(np.mean(window_data))

def compute_sigma_q16(returns: np.ndarray, i: int, window: int = 30) -> int:
    """Scale stability: σ_q = 1.0 + 0.35*coherence - 8.0*volatility."""
    if len(returns) < 2:
        return Q16_ONE
    ri = max(0, i - 1)
    start = max(0, ri - window + 1)
    window_data = returns[start:ri + 1]
    if len(window_data) < 2:
        return Q16_ONE
    vol = safe_std_q16(window_data)
    mean = int(np.mean(window_data))
    abs_mean = abs(mean)
    epsilon = 1
    vol_plus_eps = vol + epsilon
    coherence = q16_div(abs_mean, vol_plus_eps)
    coherence_term = q16_mul(Q16_ZERO35, coherence)
    vol_term = q16_mul(Q16_EIGHT, vol)
    raw = Q16_ONE + coherence_term - vol_term
    # Clamp to [0.25, 3.0]
    min_val, max_val = 16384, 196608
    return max(min_val, min(max_val, raw))

def is_lawful_rgflow(sigma_q: int, mu_q: int) -> bool:
    """RGFlow invariant: σ_q > 1 + λ·μ_q."""
    threshold = Q16_ONE + q16_mul(Q16_LAMBDA, mu_q)
    return sigma_q > threshold

def batch_eth_rgflow(prices_q16: np.ndarray, window: int = 30) -> List[Tuple[int, int, bool]]:
    """Run RGFlow analysis on all positions."""
    returns = log_returns_q16(prices_q16)
    results = []
    for i in range(len(prices_q16)):
        sigma_q = compute_sigma_q16(returns, i, window)
        mu_q = compute_mu_q16(returns, i, window)
        lawful = is_lawful_rgflow(sigma_q, mu_q)
        results.append((sigma_q, mu_q, lawful))
    return results

# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("ETHEREUM RGFLOW ANALYSIS (PYTHON-NATIVE)")
    print("=" * 70)

    print("\nFetching full historical ETH-USD price data since 2015...")
    prices = fetch_eth_prices()
    print(f"Acquired {len(prices)} daily price points")
    print(f"Price range: ${min(prices):,.2f} - ${max(prices):,.2f}")
    print(f"Latest price: ${prices[-1]:,.2f}")

    print("\nConverting prices to Q16.16 format...")
    prices_q16 = prices_to_q1616(prices)
    print(f"Generated {len(prices_q16)} Q16.16 values")

    print("\nRunning RGFlow analysis (rolling window=30)...")
    results = batch_eth_rgflow(prices_q16, window=30)

    sigma_values = [r[0] / Q16_ONE for r in results]
    lawful_count = sum(1 for r in results if r[2])

    print("\n" + "=" * 70)
    print("RGFLOW ANALYSIS RESULTS")
    print("=" * 70)
    print(f"Total positions analyzed: {len(results)}")
    print(f"Lawful states: {lawful_count} ({lawful_count/len(results)*100:.1f}%)")
    print(f"Average sigma_q: {np.mean(sigma_values):.4f}")
    print(f"Sigma range: {min(sigma_values):.4f} - {max(sigma_values):.4f}")

    low_sigma = sum(1 for s in sigma_values if s < 1.0)
    if low_sigma > 0:
        print(f"\n⚠️  INFORMATIC COLLAPSE DETECTED")
        print(f"   {low_sigma} states have sigma_q < 1.0")
    else:
        print(f"\n✓ MANIFOLD STABLE")
        print(f"   All states maintain sigma_q ≥ 1.0")

    # Save results
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    results_data = {
        "timestamp": datetime.now().isoformat(),
        "asset": "ETH-USD",
        "data_points": len(prices),
        "price_range": {"min": min(prices), "max": max(prices)},
        "latest_price": prices[-1],
        "rgflow_results": [
            {"position": i, "sigma_q": r[0], "mu_q": r[1], "lawful": r[2]}
            for i, r in enumerate(results)
        ],
        "statistics": {
            "total_positions": len(results),
            "lawful_count": lawful_count,
            "average_sigma": float(np.mean(sigma_values)),
            "min_sigma": float(min(sigma_values)),
            "max_sigma": float(max(sigma_values)),
        }
    }
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results_data, f, indent=2)
    print(f"\nResults saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
