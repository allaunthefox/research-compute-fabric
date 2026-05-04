#!/usr/bin/env python3
"""
Crypto RGFlow Bulk Analyzer — Major Commodities

Fetches historical price data for 20+ major cryptocurrencies and runs
RGFlow analysis (sigma_q, mu_q, lawfulness) on each. Produces a
comparative report of manifold stability across the crypto ecosystem.

Suitable for MEV bot regime classification and cross-asset arbitrage
detection.
"""

import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

# ═══════════════════════════════════════════════════════════════════════════
# Asset registry: (ticker, yahoo_symbol, approx_launch_year, launch_month)
# ═══════════════════════════════════════════════════════════════════════════

ASSETS = [
    ("BTC", "BTC-USD", 2009, 1),
    ("ETH", "ETH-USD", 2015, 7),
    ("SOL", "SOL-USD", 2020, 4),
    ("ADA", "ADA-USD", 2017, 10),
    ("XRP", "XRP-USD", 2013, 8),
    ("DOT", "DOT-USD", 2020, 8),
    ("LINK", "LINK-USD", 2017, 9),
    ("LTC", "LTC-USD", 2011, 10),
    ("BCH", "BCH-USD", 2017, 8),
    ("AVAX", "AVAX-USD", 2020, 7),
    ("MATIC", "MATIC-USD", 2019, 4),
    ("UNI", "UNI-USD", 2020, 9),
    ("AAVE", "AAVE-USD", 2020, 10),
    ("ATOM", "ATOM-USD", 2019, 3),
    ("NEAR", "NEAR-USD", 2020, 10),
    ("ALGO", "ALGO-USD", 2019, 6),
    ("XTZ", "XTZ-USD", 2018, 6),
    ("XLM", "XLM-USD", 2014, 8),
    ("XMR", "XMR-USD", 2014, 4),
    ("DOGE", "DOGE-USD", 2013, 12),
]

# Q16.16 constants
Q16_ONE = 65536
Q16_HALF = 32768
Q16_ZERO35 = 22937
Q16_EIGHT = 524288
Q16_LAMBDA = 32768

OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "crypto_rgflow"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════
# Data fetching
# ═══════════════════════════════════════════════════════════════════════════

def fetch_prices(symbol: str, start_year: int, start_month: int) -> List[float]:
    """Fetch daily close prices from Yahoo Finance."""
    start_ts = int(datetime(start_year, start_month, 1).timestamp())
    end_ts = int(datetime.now().timestamp())
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        f"?interval=1d&period1={start_ts}&period2={end_ts}"
    )
    cmd = ["curl", "-s", "-H", "User-Agent: Mozilla/5.0", "--max-time", "30", url]
    try:
        out = subprocess.check_output(cmd)
        data = json.loads(out)
        result = data.get("chart", {}).get("result", [None])[0]
        if result is None:
            return []
        prices = result["indicators"]["quote"][0]["close"]
        return [p for p in prices if p is not None]
    except Exception as e:
        print(f"  [WARN] Failed to fetch {symbol}: {e}")
        return []

# ═══════════════════════════════════════════════════════════════════════════
# Q16.16 + RGFlow (same logic as ethereum_rgflow_fetch.py)
# ═══════════════════════════════════════════════════════════════════════════

def prices_to_q1616(prices: List[float]) -> np.ndarray:
    arr = np.array(prices, dtype=np.float64)
    log_prices = np.log(arr)
    min_log, max_log = np.min(log_prices), np.max(log_prices)
    if max_log - min_log > 0:
        scaled = ((log_prices - min_log) / (max_log - min_log) * 65535).astype(np.int64)
    else:
        scaled = np.zeros_like(log_prices, dtype=np.int64)
    return scaled

def q16_div(a: int, b: int) -> int:
    return (a << 16) // b if b != 0 else 0

def q16_mul(a: int, b: int) -> int:
    return (a * b) >> 16

def q16_sqrt_approx(x: int) -> int:
    norm = q16_div(x, Q16_ONE)
    return q16_mul(norm, (49152 - q16_mul(Q16_HALF, norm)))

def log_returns_q16(prices: np.ndarray) -> np.ndarray:
    if len(prices) < 2:
        return np.array([], dtype=np.int64)
    returns = []
    for i in range(len(prices) - 1):
        p0, p1 = prices[i], prices[i + 1]
        if p0 > 0 and p1 > 0:
            ratio = q16_div(p1, p0)
            diff = ratio - Q16_ONE
            log_approx = diff - q16_mul(Q16_HALF, q16_mul(diff, diff))
            returns.append(log_approx)
    return np.array(returns, dtype=np.int64)

def safe_std_q16(xs: np.ndarray) -> int:
    if len(xs) <= 1:
        return 0
    mean = int(np.mean(xs))
    diffs = xs - mean
    var = int(np.mean(diffs * diffs))
    return q16_sqrt_approx(var)

def compute_sigma_q16(returns: np.ndarray, i: int, window: int = 30) -> int:
    if len(returns) < 2:
        return Q16_ONE
    ri = max(0, i - 1)
    start = max(0, ri - window + 1)
    wd = returns[start:ri + 1]
    if len(wd) < 2:
        return Q16_ONE
    vol = safe_std_q16(wd)
    mean = int(np.mean(wd))
    abs_mean = abs(mean)
    coherence = q16_div(abs_mean, vol + 1)
    raw = Q16_ONE + q16_mul(Q16_ZERO35, coherence) - q16_mul(Q16_EIGHT, vol)
    return max(16384, min(196608, raw))

def compute_mu_q16(returns: np.ndarray, i: int, window: int = 30) -> int:
    if len(returns) < 2:
        return 0
    ri = max(0, i - 1)
    start = max(0, ri - window + 1)
    wd = returns[start:ri + 1]
    if len(wd) < 2:
        return 0
    return int(np.mean(wd))

def is_lawful(sigma_q: int, mu_q: int) -> bool:
    return sigma_q > (Q16_ONE + q16_mul(Q16_LAMBDA, mu_q))

def analyze_asset(prices: List[float], window: int = 30) -> Dict:
    if len(prices) < window + 2:
        return {"error": "insufficient data", "count": len(prices)}
    prices_q16 = prices_to_q1616(prices)
    returns = log_returns_q16(prices_q16)
    results = []
    for i in range(len(prices_q16)):
        sigma_q = compute_sigma_q16(returns, i, window)
        mu_q = compute_mu_q16(returns, i, window)
        results.append((sigma_q, mu_q, is_lawful(sigma_q, mu_q)))

    sigmas = [r[0] / Q16_ONE for r in results]
    lawful = sum(1 for r in results if r[2])
    collapse = sum(1 for s in sigmas if s < 1.0)

    return {
        "positions": len(results),
        "lawful_count": lawful,
        "lawful_pct": round(lawful / len(results) * 100, 2),
        "collapse_count": collapse,
        "avg_sigma": round(float(np.mean(sigmas)), 4),
        "min_sigma": round(float(min(sigmas)), 4),
        "max_sigma": round(float(max(sigmas)), 4),
        "price_min": round(min(prices), 2),
        "price_max": round(max(prices), 2),
        "latest_price": round(prices[-1], 2),
    }

# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def process_asset(ticker: str, symbol: str, year: int, month: int) -> Tuple[str, Dict]:
    print(f"\n[{ticker}] Fetching {symbol}...")
    prices = fetch_prices(symbol, year, month)
    if not prices:
        return ticker, {"error": "no data fetched"}
    print(f"  → {len(prices)} price points | ${prices[0]:.2f} → ${prices[-1]:.2f}")
    stats = analyze_asset(prices)
    # Save per-asset detail
    detail = {
        "ticker": ticker,
        "symbol": symbol,
        "timestamp": datetime.now().isoformat(),
        "prices": prices,
        "statistics": stats,
    }
    with open(OUTPUT_DIR / f"{ticker.lower()}_rgflow.json", "w") as f:
        json.dump(detail, f, indent=2)
    return ticker, stats

def main():
    print("=" * 70)
    print("CRYPTO RGFLOW BULK ANALYZER")
    print("=" * 70)
    print(f"\nAnalyzing {len(ASSETS)} major crypto commodities...")
    print(f"Output directory: {OUTPUT_DIR}")

    all_results = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(process_asset, t, s, y, m): t
            for t, s, y, m in ASSETS
        }
        for future in as_completed(futures):
            ticker, stats = future.result()
            all_results[ticker] = stats

    # Comparative summary
    summary = []
    for ticker in sorted(all_results.keys()):
        s = all_results[ticker]
        if "error" in s:
            summary.append((ticker, 0.0, 0, 0, "ERROR"))
        else:
            summary.append((
                ticker,
                s["avg_sigma"],
                s["lawful_pct"],
                s["collapse_count"],
                f"${s['latest_price']:,.2f}"
            ))

    print("\n" + "=" * 70)
    print("COMPARATIVE RGFLOW SUMMARY")
    print("=" * 70)
    print(f"{'Asset':>6s} {'Avg σ_q':>10s} {'Lawful%':>8s} {'Collapse':>9s} {'Price':>14s}")
    print("-" * 55)
    for ticker, avg_sigma, lawful_pct, collapse, price in sorted(summary, key=lambda x: -x[1]):
        print(f"{ticker:>6s} {avg_sigma:>10.4f} {lawful_pct:>7.1f}% {collapse:>8d} {price:>14s}")

    # Save master summary
    master = {
        "timestamp": datetime.now().isoformat(),
        "assets_analyzed": len(ASSETS),
        "results": all_results,
    }
    with open(OUTPUT_DIR / "master_summary.json", "w") as f:
        json.dump(master, f, indent=2)

    print(f"\n[OK] All results saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
