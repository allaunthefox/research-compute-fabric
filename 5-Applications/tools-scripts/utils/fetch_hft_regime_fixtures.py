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
"""Download the full ^GSPC (S&P 500 Composite) history from Yahoo Finance v8 API
and slice it into macro-regime era fixtures for the surprise-determinism test suite.

Full available range: 1927-12-30 → today  (~24,680 trading days as of 2026)

Pre-1928 note
─────────────
Data before 1927-12-30 is not available from Yahoo Finance.  The NYSE was
organized in 1792; the DJIA was first published in 1896; systematic daily
S&P Composite data was only reconstructed back to 1928.  Pre-1928 monthly
data (Shiller, 1871–1927) requires Yale's ie_data.xls, which is not
accessible from automated scripts via this network.

Eras saved
──────────
  roaring_twenties : 1927-12-30 → 1929-10-28  (YF start → pre-crash)
  great_depression : 1929-10-29 → 1941-12-31  (Black Tuesday → Pearl Harbor)
  wwii_recovery    : 1942-01-01 → 1952-12-31  (WWII + postwar reconstruction)
  bretton_woods    : 1953-01-01 → 1971-08-14  (stable managed growth)
  stagflation      : 1971-08-15 → 1982-12-31  (Nixon shock → Volcker victory)
  reagan_bull      : 1983-01-01 → 1994-12-31  (80s/90s expansion)
  pre_hft          : 1995-01-03 → 2006-12-29  (human microstructure)
  gfc_transition   : 2007-01-01 → 2011-12-31  (Reg NMS / Flash Crash dirty zone)
  post_hft         : 2012-01-03 → 2023-12-29  (algorithmic-dominant)
  post_pandemic    : 2024-01-01 → latest       (current)
  full_history     : 1927-12-30 → latest       (full corpus)

Data source: Yahoo Finance v8 chart API (https://query1.finance.yahoo.com).
No API key required.  Full history is fetched in a single request and sliced
in memory — avoids per-era network calls and YF rate limiting.

Usage:
  python 5-Applications/scripts/fetch_hft_regime_fixtures.py
  python 5-Applications/scripts/fetch_hft_regime_fixtures.py --out-dir 5-Applications/tests/fixtures/hft_regime
"""


import argparse
import json
import math
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

_YF_URL = (
    "https://query1.finance.yahoo.com/v8/finance/chart/"
    "%5EGSPC?period1={p1}&period2={p2}&interval=1d"
)

# Macro-regime era definitions.
# "2099-12-31" as end date is intentionally far-future; YF clips to latest available.
# Eras are non-overlapping except gfc_transition, which covers the deliberate gap
# between pre_hft and post_hft.
_ERAS = {
    # ── Historical regimes ────────────────────────────────────────────────────
    "roaring_twenties": ("1927-12-30", "1929-10-28"),  # YF start → day before Black Tuesday
    "great_depression": ("1929-10-29", "1941-12-31"),  # Black Tuesday → Pearl Harbor
    "wwii_recovery":    ("1942-01-01", "1952-12-31"),  # Wartime boom → Eisenhower
    "bretton_woods":    ("1953-01-01", "1971-08-14"),  # Gold-peg era → day before Nixon shock
    "stagflation":      ("1971-08-15", "1982-12-31"),  # Nixon shock → year of Volcker victory
    "reagan_bull":      ("1983-01-01", "1994-12-31"),  # 80s/90s expansion
    # ── HFT-era split (backward-compatible, used by existing tests) ───────────
    "pre_hft":          ("1995-01-03", "2006-12-29"),  # Human-only microstructure
    "gfc_transition":   ("2007-01-01", "2011-12-31"),  # Dirty zone (Reg NMS, Bear, Flash Crash)
    "post_hft":         ("2012-01-03", "2023-12-29"),  # Algorithmic-dominant
    # ── Current era ──────────────────────────────────────────────────────────
    "post_pandemic":    ("2024-01-01", "2099-12-31"),
    # ── Full corpus ──────────────────────────────────────────────────────────
    "full_history":     ("1900-01-01", "2099-12-31"),  # YF clips to earliest/latest available
}

_REQUEST_TIMEOUT = 30  # seconds


def _date_to_ts(date_str: str) -> int:
    """Convert YYYY-MM-DD to a UTC Unix timestamp (midnight)."""
    return int(
        datetime.strptime(date_str, "%Y-%m-%d")
        .replace(tzinfo=timezone.utc)
        .timestamp()
    )


def _fetch_all_closes() -> List[Tuple[str, float]]:
    """Fetch the complete ^GSPC history in a single Yahoo Finance v8 request.

    Returns [(date_str, close), ...] oldest-first.
    Uses adjclose (split/dividend-adjusted).
    """
    # Use a wide window — YF returns the actual earliest/latest available.
    p1 = _date_to_ts("1900-01-01")
    p2 = _date_to_ts("2099-12-31")
    url = _YF_URL.format(p1=p1, p2=p2)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; research-stack/1.0)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=_REQUEST_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.URLError as exc:
        print(f"[fetch_hft_regime_fixtures] network error: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        result     = data["chart"]["result"][0]
        timestamps = result["timestamp"]
        indicators = result["indicators"]
        closes_raw = (
            indicators.get("adjclose", [{}])[0].get("adjclose")
            or indicators["quote"][0]["close"]
        )
    except (KeyError, IndexError, TypeError) as exc:
        print(f"[fetch_hft_regime_fixtures] unexpected JSON shape: {exc}", file=sys.stderr)
        sys.exit(1)

    rows: List[Tuple[str, float]] = []
    for ts, px in zip(timestamps, closes_raw):
        if px is None or px <= 0:
            continue
        date_s = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        rows.append((date_s, float(px)))

    rows.sort(key=lambda r: r[0])
    return rows


def _log_returns(closes: List[float]) -> List[float]:
    """Compute ln(p_t / p_{t-1}) for consecutive close prices."""
    return [
        math.log(closes[i] / closes[i - 1])
        for i in range(1, len(closes))
        if closes[i] > 0 and closes[i - 1] > 0
    ]


def main(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    # Single network request for the full history; slice all eras from memory.
    print("Fetching ^GSPC full history from Yahoo Finance v8...", end=" ", flush=True)
    all_rows = _fetch_all_closes()
    if len(all_rows) < 1000:
        print(f"\nERROR: only {len(all_rows)} rows — network or API issue")
        sys.exit(1)
    print(f"{len(all_rows)} days  ({all_rows[0][0]} → {all_rows[-1][0]})")

    for era, (d1, d2) in _ERAS.items():
        rows = [(d, px) for d, px in all_rows if d1 <= d <= d2]
        if len(rows) < 5:
            print(f"  SKIP {era}: {len(rows)} rows in [{d1}, {d2}]")
            continue

        dates   = [r[0] for r in rows]
        closes  = [r[1] for r in rows]
        log_ret = _log_returns(closes)

        payload = {
            "symbol":      "^GSPC via Yahoo Finance v8",
            "era":         era,
            "date_start":  dates[0],
            "date_end":    dates[-1],
            "n_days":      len(rows),
            "log_returns": [round(r, 10) for r in log_ret],
        }
        out_path = out_dir / f"{era}_returns.json"
        out_path.write_text(json.dumps(payload, indent=2))
        print(f"  {era:20s}  {len(rows):5d} days  {dates[0]} → {dates[-1]}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--out-dir",
        default="5-Applications/tests/fixtures/hft_regime",
        help="Directory to write fixture files (created if absent)",
    )
    args = p.parse_args()


    root = Path(__file__).resolve().parent.parent
    main(root / args.out_dir)
