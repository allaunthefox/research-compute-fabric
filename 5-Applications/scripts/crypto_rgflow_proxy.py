#!/usr/bin/env python3
"""
Crypto RGFlow Proxy — Unified Compression Pipeline

Lightweight proxy that fetches crypto market data from public APIs
(CoinGecko, Yahoo Finance fallback) and routes it through the RGFlow
compression pipeline. No full nodes required.

Feeds per-asset genome compression ratios into the unified shim for
batch lawfulness evaluation.
"""

import json
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

# ═══════════════════════════════════════════════════════════════════════════
# Asset registry with CoinGecko IDs
# ═══════════════════════════════════════════════════════════════════════════

ASSETS = [
    ("BTC", "bitcoin", "BTC-USD"),
    ("ETH", "ethereum", "ETH-USD"),
    ("SOL", "solana", "SOL-USD"),
    ("ADA", "cardano", "ADA-USD"),
    ("XRP", "ripple", "XRP-USD"),
    ("DOT", "polkadot", "DOT-USD"),
    ("LINK", "chainlink", "LINK-USD"),
    ("LTC", "litecoin", "LTC-USD"),
    ("BCH", "bitcoin-cash", "BCH-USD"),
    ("AVAX", "avalanche-2", "AVAX-USD"),
    ("MATIC", "matic-network", "MATIC-USD"),
    ("UNI", "uniswap", "UNI-USD"),
    ("AAVE", "aave", "AAVE-USD"),
    ("ATOM", "cosmos", "ATOM-USD"),
    ("NEAR", "near", "NEAR-USD"),
    ("ALGO", "algorand", "ALGO-USD"),
    ("XTZ", "tezos", "XTZ-USD"),
    ("XLM", "stellar", "XLM-USD"),
    ("XMR", "monero", "XMR-USD"),
    ("DOGE", "dogecoin", "DOGE-USD"),
]

OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "crypto_rgflow"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Q16.16 constants
Q16_ONE = 65536
Q16_HALF = 32768
Q16_ZERO35 = 22937
Q16_EIGHT = 524288
Q16_LAMBDA = 32768

# ═══════════════════════════════════════════════════════════════════════════
# Lightweight API fetchers
# ═══════════════════════════════════════════════════════════════════════════

def coingecko_history(cg_id: str) -> Optional[List[float]]:
    """Fetch full history from CoinGecko public API."""
    url = f"https://api.coingecko.com/api/v3/coins/{cg_id}/market_chart?vs_currency=usd&days=max"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read())
            prices = data.get("prices", [])
            return [p[1] for p in prices if isinstance(p, list) and len(p) == 2]
    except Exception as e:
        print(f"    CoinGecko fail: {e}")
        return None

def yahoo_history(symbol: str) -> Optional[List[float]]:
    """Fallback to Yahoo Finance daily closes."""
    from datetime import datetime
    import subprocess
    start_ts = int(datetime(2010, 1, 1).timestamp())
    end_ts = int(datetime.now().timestamp())
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        f"?interval=1d&period1={start_ts}&period2={end_ts}"
    )
    try:
        out = subprocess.check_output(
            ["curl", "-s", "-H", "User-Agent: Mozilla/5.0", "--max-time", "30", url],
            stderr=subprocess.DEVNULL
        )
        data = json.loads(out)
        result = data.get("chart", {}).get("result", [None])[0]
        if result is None:
            return None
        prices = result["indicators"]["quote"][0]["close"]
        return [p for p in prices if p is not None]
    except Exception as e:
        print(f"    Yahoo fail: {e}")
        return None

def fetch_prices(ticker: str, cg_id: str, yahoo_sym: str) -> List[float]:
    """Try CoinGecko first, fallback to Yahoo."""
    prices = coingecko_history(cg_id)
    if prices and len(prices) > 100:
        return prices
    prices = yahoo_history(yahoo_sym)
    if prices and len(prices) > 100:
        return prices
    return []

# ═══════════════════════════════════════════════════════════════════════════
# Genome compression (6D quantization)
# ═══════════════════════════════════════════════════════════════════════════

def prices_to_q1616(prices: List[float]) -> np.ndarray:
    arr = np.array(prices, dtype=np.float64)
    log_p = np.log(arr)
    mn, mx = np.min(log_p), np.max(log_p)
    if mx - mn > 0:
        return ((log_p - mn) / (mx - mn) * 65535).astype(np.int64)
    return np.zeros_like(log_p, dtype=np.int64)

def q16_div(a: int, b: int) -> int:
    return (a << 16) // b if b != 0 else 0

def q16_mul(a: int, b: int) -> int:
    return (a * b) >> 16

def log_returns_q16(prices: np.ndarray) -> np.ndarray:
    if len(prices) < 2:
        return np.array([], dtype=np.int64)
    out = []
    for i in range(len(prices) - 1):
        p0, p1 = prices[i], prices[i + 1]
        if p0 > 0 and p1 > 0:
            ratio = q16_div(p1, p0)
            diff = ratio - Q16_ONE
            out.append(diff - q16_mul(Q16_HALF, q16_mul(diff, diff)))
    return np.array(out, dtype=np.int64)

def safe_std_q16(xs: np.ndarray) -> int:
    if len(xs) <= 1:
        return 0
    mean = int(np.mean(xs))
    diffs = xs - mean
    var = int(np.mean(diffs * diffs))
    norm = q16_div(var, Q16_ONE)
    return q16_mul(norm, 49152 - q16_mul(Q16_HALF, norm))

def compute_sigma_mu(returns: np.ndarray, i: int, window: int = 30) -> Tuple[int, int]:
    if len(returns) < 2:
        return Q16_ONE, 0
    ri = max(0, i - 1)
    start = max(0, ri - window + 1)
    wd = returns[start:ri + 1]
    if len(wd) < 2:
        return Q16_ONE, 0
    vol = safe_std_q16(wd)
    mean = int(np.mean(wd))
    abs_mean = abs(mean)
    coherence = q16_div(abs_mean, vol + 1)
    raw = Q16_ONE + q16_mul(Q16_ZERO35, coherence) - q16_mul(Q16_EIGHT, vol)
    sigma = max(16384, min(196608, raw))
    mu = mean
    return sigma, mu

def is_lawful(sigma: int, mu: int) -> bool:
    return sigma > (Q16_ONE + q16_mul(Q16_LAMBDA, mu))

def analyze(prices: List[float], window: int = 30) -> Dict:
    if len(prices) < window + 2:
        return {"error": "insufficient data", "count": len(prices)}
    pq = prices_to_q1616(prices)
    returns = log_returns_q16(pq)
    sigmas, mus, lawfuls = [], [], []
    for i in range(len(pq)):
        s, m = compute_sigma_mu(returns, i, window)
        sigmas.append(s)
        mus.append(m)
        lawfuls.append(is_lawful(s, m))
    sigmas_f = [s / Q16_ONE for s in sigmas]
    return {
        "positions": len(prices),
        "lawful_count": sum(lawfuls),
        "lawful_pct": round(sum(lawfuls) / len(prices) * 100, 2),
        "collapse_count": sum(1 for s in sigmas_f if s < 1.0),
        "avg_sigma": round(float(np.mean(sigmas_f)), 4),
        "min_sigma": round(float(min(sigmas_f)), 4),
        "max_sigma": round(float(max(sigmas_f)), 4),
        "price_min": round(min(prices), 2),
        "price_max": round(max(prices), 2),
        "latest_price": round(prices[-1], 2),
    }

# ═══════════════════════════════════════════════════════════════════════════
# Genome → 18-bit address encoding (for LUT lookup)
# ═══════════════════════════════════════════════════════════════════════════

def encode_genome(sigma_bin: int, mu_bin: int, c_bin: int, m_bin: int, ne_bin: int, sig_bin: int) -> int:
    return (
        (sigma_bin & 7) * 32768 +
        (mu_bin & 7) * 4096 +
        (c_bin & 7) * 512 +
        (m_bin & 7) * 64 +
        (ne_bin & 7) * 8 +
        (sig_bin & 7)
    )

def stats_to_genome(stats: Dict) -> int:
    """Compress asset statistics into 18-bit genome address."""
    sigma_bin = min(7, int(stats.get("avg_sigma", 2.0) / 3.0 * 8))
    mu_bin = min(7, int(abs(stats.get("avg_mu", 0.0)) / 65536.0 * 8))
    c_bin = min(7, int(stats.get("lawful_pct", 50) / 100.0 * 8))
    m_bin = min(7, int((100 - stats.get("collapse_count", 0)) / 100.0 * 8))
    ne_bin = min(7, int(np.log1p(stats.get("positions", 0)) / np.log1p(5000) * 8))
    sig_bin = min(7, int(stats.get("latest_price", 1) / (stats.get("price_max", 1) + 1) * 8))
    return encode_genome(sigma_bin, mu_bin, c_bin, m_bin, ne_bin, sig_bin)

# ═══════════════════════════════════════════════════════════════════════════
# Main pipeline
# ═══════════════════════════════════════════════════════════════════════════

def process_asset(ticker: str, cg_id: str, yahoo_sym: str) -> Tuple[str, Optional[Dict]]:
    print(f"\n[{ticker}] Fetching via proxy...")
    prices = fetch_prices(ticker, cg_id, yahoo_sym)
    if not prices:
        print(f"  → FAILED")
        return ticker, None
    print(f"  → {len(prices)} points | ${prices[0]:.4f} → ${prices[-1]:.4f}")
    stats = analyze(prices)
    stats["genome_addr"] = stats_to_genome(stats)
    # Save per-asset
    with open(OUTPUT_DIR / f"{ticker.lower()}_proxy.json", "w") as f:
        json.dump({"ticker": ticker, "prices": prices, "stats": stats}, f, indent=2)
    return ticker, stats

def main():
    print("=" * 70)
    print("CRYPTO RGFLOW PROXY — UNIFIED COMPRESSION PIPELINE")
    print("=" * 70)
    print(f"\nAssets: {len(ASSETS)}")
    print(f"Output: {OUTPUT_DIR}")

    all_stats = {}
    # Serialize with delay to respect API rate limits
    for ticker, cg_id, yahoo_sym in ASSETS:
        t, stats = process_asset(ticker, cg_id, yahoo_sym)
        if stats:
            all_stats[t] = stats
        time.sleep(1.2)  # CoinGecko rate limit courtesy

    # Comparative summary
    print("\n" + "=" * 70)
    print("COMPARATIVE RGFLOW SUMMARY")
    print("=" * 70)
    print(f"{'Asset':>6s} {'Avg σ_q':>10s} {'Lawful%':>8s} {'Collapse':>9s} {'Genome':>8s} {'Price':>14s}")
    print("-" * 62)
    rows = []
    for t, s in all_stats.items():
        rows.append((
            t, s["avg_sigma"], s["lawful_pct"], s["collapse_count"],
            s["genome_addr"], f"${s['latest_price']:,.2f}"
        ))
    for row in sorted(rows, key=lambda x: -x[1]):
        print(f"{row[0]:>6s} {row[1]:>10.4f} {row[2]:>7.1f}% {row[3]:>8d} {row[4]:>8d} {row[5]:>14s}")

    # Save master
    with open(OUTPUT_DIR / "proxy_master.json", "w") as f:
        json.dump({"timestamp": datetime.now().isoformat(), "assets": all_stats}, f, indent=2)
    print(f"\n[OK] Master saved: {OUTPUT_DIR / 'proxy_master.json'}")

if __name__ == "__main__":
    main()
