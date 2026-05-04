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
"""Download full daily close history for every available global market instrument
from Yahoo Finance v8 and save as log-return fixture files for the
surprise-determinism and event cross-index test suites.

Instruments covered (56 total)
────────────────────────────────────────────────────────────────────────────────
  US Equities & Rates
    ^GSPC  S&P 500          1927  ^IXIC  NASDAQ           1971
    ^DJI   DJIA             1992  ^RUT   Russell 2000     1987
    ^VIX   VIX (fear index) 1990  ^TNX   US 10Y yield     1962
    ^TYX   US 30Y yield     1977  ^IRX   US 3M T-bill     1960

  Europe
    ^FTSE  UK FTSE 100      1984  ^GDAXI DE DAX           1987
    ^FCHI  FR CAC 40        1990  ^AEX   NL AEX           1992
    ^IBEX  ES IBEX 35       1993  ^SSMI  CH SMI           1990
    ^STOXX50E EU STOXX 50   2007  ^BFX   BE BEL 20        1991
    ^ATX   AT ATX           1992  ^OMX   SE OMX           2008
    IMOEX.ME  RU MOEX       1997  ^RTSI  RU RTS (USD)     1995

  Asia-Pacific
    ^N225  JP Nikkei 225    1965  ^HSI   HK Hang Seng     1986
    000001.SS CN Shanghai   1997  ^BSESN IN BSE Sensex    1997
    ^NSEI  IN NIFTY 50      2007  ^KS11  KR KOSPI         1996
    ^TWII  TW TAIEX         1997  ^STI   SG STI           1987
    ^AORD  AU ASX All Ords  1984  ^NZ50  NZ NZX 50        2003
    ^KLSE  MY KLCI          1993  ^JKSE  ID IDX           1990

  Latin America
    ^BVSP  BR Bovespa       1993  ^MXX   MX IPC           1991
    ^IPSA  CL IPSA          2002  ^MERV  AR Merval        1996

  Middle East
    ^TA125.TA  IL TA-125    1992

  Commodities
    GC=F   Gold futures     2000  SI=F   Silver futures   2000
    CL=F   WTI Crude        2000  BZ=F   Brent Crude      2007
    NG=F   Natural Gas      2000  HG=F   Copper           2000
    ZC=F   Corn             2000  ZW=F   Wheat            2000
    ZS=F   Soybeans         2000  PL=F   Platinum         1997
    PA=F   Palladium        1998

  Currencies
    EURUSD=X  EUR/USD       2003  JPY=X     USD/JPY       1996
    GBPUSD=X  GBP/USD       2003  CNY=X     USD/CNY       2001
    INRUSD=X  INR/USD       2003  BRL=X     USD/BRL       2003
    AUDUSD=X  AUD/USD       2006  DX-Y.NYB  US Dollar Idx 1971

Note on FRED
────────────
FRED supplies extended history (Gold 1968, WTI 1986, US yields 1954) but
requires a separate network session.  The YF coverage above is sufficient
for all event cross-indexing from 1965 onward.  See 6-Documentation/docs/ for the FRED
extension procedure when the host network permits it.

Output
──────
  5-Applications/tests/fixtures/global_markets/{SLUG}_returns.json

  Each file:
  {
    "ticker":      "^N225",
    "slug":        "N225",
    "label":       "JP Nikkei 225",
    "asset_class": "equity",
    "region":      "asia",
    "date_start":  "YYYY-MM-DD",
    "date_end":    "YYYY-MM-DD",
    "n_days":      N,
    "log_returns": [...],
    "dates":       [...]          # parallel to log_returns, for event lookup
  }

Usage:
  python 5-Applications/scripts/fetch_global_market_fixtures.py
  python 5-Applications/scripts/fetch_global_market_fixtures.py --out-dir 5-Applications/tests/fixtures/global_markets
  python 5-Applications/scripts/fetch_global_market_fixtures.py --workers 8
"""


import argparse
import json
import math
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_YF_URL = (
    "https://query1.finance.yahoo.com/v8/finance/chart/"
    "{encoded}?period1={p1}&period2={p2}&interval=1d"
)
_PERIOD1 = -2208988800    # 1900-01-01 UTC — YF clips to actual earliest
_PERIOD2 = 4070908800     # 2099-01-01 UTC — YF clips to actual latest
_REQUEST_TIMEOUT = 20     # seconds per request
_RETRY_PAUSE     = 2.0    # seconds before retry on network error


# ── Instrument registry ───────────────────────────────────────────────────────
# (ticker, human_label, asset_class, region)
_INSTRUMENTS: List[Tuple[str, str, str, str]] = [
    # US equities & rates
    ("^GSPC",      "S&P 500",           "equity",    "us"),
    ("^DJI",       "DJIA",              "equity",    "us"),
    ("^IXIC",      "NASDAQ Composite",  "equity",    "us"),
    ("^RUT",       "Russell 2000",      "equity",    "us"),
    ("^VIX",       "VIX",               "volatility","us"),
    ("^TNX",       "US 10Y Yield",      "rate",      "us"),
    ("^TYX",       "US 30Y Yield",      "rate",      "us"),
    ("^IRX",       "US 3M T-bill",      "rate",      "us"),
    # Europe
    ("^FTSE",      "UK FTSE 100",       "equity",    "europe"),
    ("^GDAXI",     "DE DAX",            "equity",    "europe"),
    ("^FCHI",      "FR CAC 40",         "equity",    "europe"),
    ("^AEX",       "NL AEX",            "equity",    "europe"),
    ("^IBEX",      "ES IBEX 35",        "equity",    "europe"),
    ("^SSMI",      "CH SMI",            "equity",    "europe"),
    ("^STOXX50E",  "EU STOXX 50",       "equity",    "europe"),
    ("^BFX",       "BE BEL 20",         "equity",    "europe"),
    ("^ATX",       "AT ATX",            "equity",    "europe"),
    ("^OMX",       "SE OMX",            "equity",    "europe"),
    ("IMOEX.ME",   "RU MOEX Index",     "equity",    "europe"),
    ("^RTSI",      "RU RTS Index (USD)","equity",    "europe"),
    # Asia-Pacific
    ("^N225",      "JP Nikkei 225",     "equity",    "asia"),
    ("^HSI",       "HK Hang Seng",      "equity",    "asia"),
    ("000001.SS",  "CN Shanghai Comp",  "equity",    "asia"),
    ("^BSESN",     "IN BSE Sensex",     "equity",    "asia"),
    ("^NSEI",      "IN NIFTY 50",       "equity",    "asia"),
    ("^KS11",      "KR KOSPI",          "equity",    "asia"),
    ("^TWII",      "TW TAIEX",          "equity",    "asia"),
    ("^STI",       "SG STI",            "equity",    "asia"),
    ("^AORD",      "AU ASX All Ords",   "equity",    "asia"),
    ("^NZ50",      "NZ NZX 50",         "equity",    "asia"),
    ("^KLSE",      "MY KLCI",           "equity",    "asia"),
    ("^JKSE",      "ID IDX Composite",  "equity",    "asia"),
    # Latin America
    ("^BVSP",      "BR Bovespa",        "equity",    "latam"),
    ("^MXX",       "MX IPC",            "equity",    "latam"),
    ("^IPSA",      "CL IPSA",           "equity",    "latam"),
    ("^MERV",      "AR Merval",         "equity",    "latam"),
    # Middle East
    ("^TA125.TA",  "IL TA-125",         "equity",    "mideast"),
    # Commodities
    ("GC=F",       "Gold",              "commodity", "global"),
    ("SI=F",       "Silver",            "commodity", "global"),
    ("CL=F",       "WTI Crude Oil",     "commodity", "global"),
    ("BZ=F",       "Brent Crude",       "commodity", "global"),
    ("NG=F",       "Natural Gas",       "commodity", "global"),
    ("HG=F",       "Copper",            "commodity", "global"),
    ("ZC=F",       "Corn",              "commodity", "global"),
    ("ZW=F",       "Wheat",             "commodity", "global"),
    ("ZS=F",       "Soybeans",          "commodity", "global"),
    ("PL=F",       "Platinum",          "commodity", "global"),
    ("PA=F",       "Palladium",         "commodity", "global"),
    # Currencies
    ("EURUSD=X",   "EUR/USD",           "fx",        "global"),
    ("JPY=X",      "USD/JPY",           "fx",        "global"),
    ("GBPUSD=X",   "GBP/USD",           "fx",        "global"),
    ("CNY=X",      "USD/CNY",           "fx",        "global"),
    ("INRUSD=X",   "INR/USD",           "fx",        "global"),
    ("BRL=X",      "USD/BRL",           "fx",        "global"),
    ("AUDUSD=X",   "AUD/USD",           "fx",        "global"),
    ("DX-Y.NYB",   "US Dollar Index",   "fx",        "global"),
]


def _ticker_slug(ticker: str) -> str:
    """Convert ticker to a safe filename slug.  ^GSPC → GSPC, BZ=F → BZ_F"""
    return re.sub(r"[^A-Za-z0-9]", "_", ticker).strip("_")


def _log_returns(closes: List[float]) -> List[float]:
    return [
        math.log(closes[i] / closes[i - 1])
        for i in range(1, len(closes))
        if closes[i] > 0 and closes[i - 1] > 0
    ]


def _fetch_one(
    ticker: str, label: str, asset_class: str, region: str
) -> Optional[dict]:
    """Fetch full history for one ticker from YF.  Returns fixture dict or None on error."""
    encoded = urllib.request.quote(ticker, safe="")
    url = _YF_URL.format(encoded=encoded, p1=_PERIOD1, p2=_PERIOD2)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=_REQUEST_TIMEOUT) as r:
                data = json.loads(r.read().decode("utf-8", errors="replace"))
            break
        except urllib.error.HTTPError as exc:
            return {"_error": f"HTTP {exc.code}", "ticker": ticker}
        except Exception as exc:
            if attempt == 0:
                time.sleep(_RETRY_PAUSE)
                continue
            return {"_error": str(exc)[:80], "ticker": ticker}

    try:
        result     = data["chart"]["result"][0]
        timestamps = result["timestamp"]
        indicators = result["indicators"]
        closes_raw = (
            indicators.get("adjclose", [{}])[0].get("adjclose")
            or indicators["quote"][0]["close"]
        )
    except (KeyError, IndexError, TypeError) as exc:
        return {"_error": f"parse: {exc}", "ticker": ticker}

    # Build (date, close) pairs, dropping nulls
    rows: List[Tuple[str, float]] = []
    for ts, px in zip(timestamps, closes_raw):
        if px is None or px <= 0:
            continue
        date_s = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        rows.append((date_s, float(px)))

    rows.sort(key=lambda r: r[0])
    if len(rows) < 5:
        return {"_error": "too few rows", "ticker": ticker}

    dates   = [r[0] for r in rows]
    closes  = [r[1] for r in rows]

    # log_returns has len(rows)-1 entries; dates_lr is aligned to the "current" day
    log_ret    = _log_returns(closes)
    dates_lr   = dates[1:]   # date[i] corresponds to log_ret[i] = ln(p[i]/p[i-1])

    return {
        "ticker":      ticker,
        "slug":        _ticker_slug(ticker),
        "label":       label,
        "asset_class": asset_class,
        "region":      region,
        "date_start":  dates_lr[0]  if dates_lr else dates[0],
        "date_end":    dates_lr[-1] if dates_lr else dates[-1],
        "n_days":      len(rows),
        "log_returns": [round(r, 10) for r in log_ret],
        "dates":       dates_lr,
    }


def main(out_dir: Path, workers: int) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fetching {len(_INSTRUMENTS)} instruments from Yahoo Finance "
          f"(workers={workers})...\n")

    results: Dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_fetch_one, ticker, label, cls, region): ticker
            for ticker, label, cls, region in _INSTRUMENTS
        }
        for fut in as_completed(futures):
            ticker = futures[fut]
            r = fut.result()
            results[ticker] = r

    # Print summary sorted by start date
    ordered = sorted(
        [(t, r) for t, r in results.items() if "_error" not in r],
        key=lambda x: x[1]["date_start"],
    )
    errors = [(t, r) for t, r in results.items() if "_error" in r]

    print(f"{'ticker':<18} {'label':<28} {'class':<10} {'n':>6}  "
          f"{'start':>10}  {'end':>10}")
    print("─" * 88)
    for ticker, r in ordered:
        print(f"{ticker:<18} {r['label']:<28} {r['asset_class']:<10} "
              f"{r['n_days']:>6}  {r['date_start']}  {r['date_end']}")
        slug = _ticker_slug(ticker)
        out_path = out_dir / f"{slug}_returns.json"
        out_path.write_text(json.dumps(r, indent=2))

    if errors:
        print(f"\nFailed ({len(errors)}):")
        for ticker, r in errors:
            print(f"  {ticker:<18} {r.get('_error','?')}")

    print(f"\n{len(ordered)} fixtures written to {out_dir}/")

    # Write an index manifest
    manifest = {
        "generated": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "instruments": [
            {k: r[k] for k in ("ticker","slug","label","asset_class","region",
                                "date_start","date_end","n_days")}
            for _, r in ordered
        ],
    }
    (out_dir / "_manifest.json").write_text(json.dumps(manifest, indent=2))
    print("_manifest.json written.")



if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir", default="5-Applications/tests/fixtures/global_markets",
                   help="Output directory")
    p.add_argument("--workers", type=int, default=10,
                   help="Parallel download threads")
    args = p.parse_args()
    root = Path(__file__).resolve().parent.parent
    main(root / args.out_dir, args.workers)
