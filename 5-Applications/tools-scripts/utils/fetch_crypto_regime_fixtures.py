# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================

from __future__ import annotations

# [WARDEN BOUNDARY ENFORCEMENT INJECTED]
import sys
import os
try:
    from io_harness_compat import spawn_isolated_process, fetch_network_resource
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from io_harness_compat import spawn_isolated_process, fetch_network_resource

#!/usr/bin/env python3
"""Download full Bitcoin and Ethereum daily close history from CryptoCompare
and slice into macro-regime era fixtures for the surprise-determinism test suite.

Data source: CryptoCompare histoday API (https://min-api.cryptocompare.com).
No API key required for free-tier historical access.
Paginated in 2000-day batches, walking backward from today.

Full available range
────────────────────
  BTC : 2010-07-17 → today  (~5742 days as of 2026-04)  low=$0.05  high=$124K
  ETH : 2015-08-07 → today  (~3895 days as of 2026-04)  low=$0.44  high=$4831

BTC era definitions
────────────────────
  btc_genesis         2010-07-17 → 2013-03-31  Early adopter, sub-dollar → $30 → $2
  btc_first_bubble    2013-04-01 → 2013-12-31  First Mt. Gox peak ($1,000+)
  btc_mtgox_era       2014-01-01 → 2016-07-08  Mt. Gox collapse → first halving
  btc_halving_2017    2016-07-09 → 2017-12-31  Second halving bull run → $20K
  btc_crypto_winter   2018-01-01 → 2020-03-31  -84% bear market
  btc_institutional   2020-04-01 → 2021-11-09  MicroStrategy + Tesla + ATH $69K
  btc_ftx_era         2021-11-10 → 2022-12-31  Luna collapse, FTX bankruptcy
  btc_etf_era         2023-01-01 → 2099-12-31  Recovery, spot ETF Jan 2024, $100K+
  btc_full            2010-07-17 → 2099-12-31  Complete BTC history

ETH era definitions
────────────────────
  eth_genesis         2015-08-07 → 2016-12-31  Early trading, pre-ICO
  eth_ico_bubble      2017-01-01 → 2018-01-31  ICO mania → $1,400 peak
  eth_bear_2018       2018-02-01 → 2020-07-31  -94% multi-year bear
  eth_defi_nft        2020-08-01 → 2021-11-09  DeFi/NFT boom, EIP-1559
  eth_post_merge      2022-09-15 → 2099-12-31  Proof-of-Stake era
  eth_full            2015-08-07 → 2099-12-31  Complete ETH history

Usage:
  python 5-Applications/scripts/fetch_crypto_regime_fixtures.py
  python 5-Applications/scripts/fetch_crypto_regime_fixtures.py --out-dir 5-Applications/tests/fixtures/crypto_regime
"""


import argparse
import json
import math
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

_CC_URL = "https://min-api.cryptocompare.com/data/v2/histoday?fsym={sym}&tsym=USD&limit=2000"
_REQUEST_TIMEOUT = 25  # seconds
_PAGE_PAUSE = 0.5       # seconds between pages; free-tier rate limit is ~30 req/min

_BTC_ERAS: Dict[str, Tuple[str, str]] = {
    "btc_genesis":      ("2010-07-17", "2013-03-31"),
    "btc_first_bubble": ("2013-04-01", "2013-12-31"),
    "btc_mtgox_era":    ("2014-01-01", "2016-07-08"),
    "btc_halving_2017": ("2016-07-09", "2017-12-31"),
    "btc_crypto_winter":("2018-01-01", "2020-03-31"),
    "btc_institutional":("2020-04-01", "2021-11-09"),
    "btc_ftx_era":      ("2021-11-10", "2022-12-31"),
    "btc_etf_era":      ("2023-01-01", "2099-12-31"),
    "btc_full":         ("2010-07-17", "2099-12-31"),
}

_ETH_ERAS: Dict[str, Tuple[str, str]] = {
    "eth_genesis":      ("2015-08-07", "2016-12-31"),
    "eth_ico_bubble":   ("2017-01-01", "2018-01-31"),
    "eth_bear_2018":    ("2018-02-01", "2020-07-31"),
    "eth_defi_nft":     ("2020-08-01", "2021-11-09"),
    "eth_post_merge":   ("2022-09-15", "2099-12-31"),
    "eth_full":         ("2015-08-07", "2099-12-31"),
}


def _date_to_ts(date_str: str) -> int:
    return int(
        datetime.strptime(date_str, "%Y-%m-%d")
        .replace(tzinfo=timezone.utc)
        .timestamp()
    )


def _fetch_all_cc(sym: str) -> List[Tuple[str, float]]:
    """Fetch complete daily close history for `sym` from CryptoCompare.

    Paginates backward from today in 2000-day batches until no more valid data.
    Filters rows where close=0 (pre-listing padding CryptoCompare sometimes emits).
    Returns [(date_str, close), ...] oldest-first.
    """
    base = _CC_URL.format(sym=sym)
    to_ts: int | None = None
    all_rows: List[Tuple[str, float]] = []
    seen_dates: set[str] = set()

    for page in range(20):  # 20 pages × 2000 days = 40,000 days max (safety limit)
        url = base if to_ts is None else f"{base}&toTs={to_ts}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=_REQUEST_TIMEOUT) as r:
                d = json.loads(r.read().decode("utf-8", errors="replace"))
        except urllib.error.URLError as exc:
            print(f"\n[fetch_crypto] page {page}: network error: {exc}", file=sys.stderr)
            break

        rows = d.get("Data", {}).get("Data", [])
        if not rows:
            break

        valid_this_page = 0
        for row in rows:
            ts   = row.get("time", 0)
            px   = row.get("close", 0.0)
            if not ts or not px or px <= 0:
                continue
            date_s = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
            if date_s in seen_dates:
                continue
            seen_dates.add(date_s)
            all_rows.append((date_s, float(px)))
            valid_this_page += 1

        if valid_this_page == 0:
            break  # Hit the pre-listing zero-price region

        to_ts = rows[0]["time"] - 1
        if rows[0]["time"] == 0:
            break

        if page < 19:  # Don't pause after the last page
            time.sleep(_PAGE_PAUSE)

    all_rows.sort(key=lambda r: r[0])
    return all_rows


def _log_returns(closes: List[float]) -> List[float]:
    return [
        math.log(closes[i] / closes[i - 1])
        for i in range(1, len(closes))
        if closes[i] > 0 and closes[i - 1] > 0
    ]


def _save_eras(
    all_rows: List[Tuple[str, float]],
    eras: Dict[str, Tuple[str, str]],
    asset: str,
    out_dir: Path,
) -> None:
    for era, (d1, d2) in eras.items():
        rows = [(d, px) for d, px in all_rows if d1 <= d <= d2]
        if len(rows) < 5:
            print(f"  SKIP {era}: {len(rows)} rows in [{d1}, {d2}]")
            continue

        dates   = [r[0] for r in rows]
        closes  = [r[1] for r in rows]
        log_ret = _log_returns(closes)

        payload = {
            "symbol":      f"{asset}/USD via CryptoCompare",
            "era":         era,
            "date_start":  dates[0],
            "date_end":    dates[-1],
            "n_days":      len(rows),
            "log_returns": [round(r, 10) for r in log_ret],
        }
        out_path = out_dir / f"{era}_returns.json"
        out_path.write_text(json.dumps(payload, indent=2))
        print(f"  {era:<22}  {len(rows):5d} days  {dates[0]} → {dates[-1]}")


def main(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    for sym, eras, label in (
        ("BTC", _BTC_ERAS, "Bitcoin"),
        ("ETH", _ETH_ERAS, "Ethereum"),
    ):
        print(f"\nFetching {label} ({sym}) from CryptoCompare...", flush=True)
        all_rows = _fetch_all_cc(sym)
        if len(all_rows) < 100:
            print(f"ERROR: only {len(all_rows)} rows — network or API issue")
            sys.exit(1)
        print(f"  {len(all_rows)} days  ({all_rows[0][0]} → {all_rows[-1][0]})")
        _save_eras(all_rows, eras, sym, out_dir)



if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--out-dir",
        default="5-Applications/tests/fixtures/crypto_regime",
        help="Directory to write fixture files (created if absent)",
    )
    args = p.parse_args()
    root = Path(__file__).resolve().parent.parent
    main(root / args.out_dir)
